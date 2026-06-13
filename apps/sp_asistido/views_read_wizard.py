"""Asistente READ (SELECT) — pasos 1–7 (checklist F)."""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.sp_asistido.models import SPAssignment, SPCondition, SPDefinition, SPStepState
from apps.sp_asistido.services.access import get_sp_definition_or_404
from apps.sp_asistido.services.add_validation import (
    header_belongs_to_company,
    insertable_details_for_header,
    normalize_selected_field_ids,
    suggested_specific_name,
    validate_step1_identification,
)
from apps.sp_asistido.services.dlt_validation import (
    definition_has_where_clause,
    validate_where_row,
)
from apps.sp_asistido.services.generate_read_script import (
    READ_PROJECTION_MARKER,
    build_read_procedure_sql,
    is_read_projection_assignment,
    persist_generated_read_script,
)
from apps.sp_asistido.services.read_validation import (
    validate_read_order_and_fetch,
    validate_read_column_selection,
)
from apps.sp_asistido.services.generate_insert_script import format_db2_type_for_parameter
from apps.sp_asistido.services.upd_validation import (
    normalize_where_col_flags,
    ordered_selected_detail_ids,
)
from apps.sp_asistido.services.ui_messages import (
    notify_error,
    notify_success,
    notify_warning,
)
from apps.sp_asistido.services.wizard_session import (
    clear_wizard_session,
    load_wizard_session,
    save_wizard_session,
)
from apps.sp_asistido.views import _require_profile, _require_sp_asistido_list_access
from apps.sp_asistido.services.sp_persistence import (
    confirm_generated_script,
    create_wizard_definition_draft,
    upsert_step_state,
)
from apps.table_design.models import DetailTable, HeaderTable
from apps.userprofile.models import UserProfile

SESSION_READ_STEP1 = "sp_asistido_read_step1"


def _get_read_definition(request: HttpRequest, definition_id: int) -> SPDefinition:
    return get_sp_definition_or_404(
        request.user,
        definition_id,
        operation=SPDefinition.Operation.READ,
    )


def _details_for_read_header(header_id: int):
    return (
        DetailTable.objects.filter(
            header_id=header_id, status=DetailTable.Status.ACTIVE
        )
        .order_by(
            Case(
                When(is_key=True, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            "order_reg",
            "id",
        )
    )


def _read_where_conditions(definition: SPDefinition) -> list[SPCondition]:
    return list(
        definition.conditions.filter(
            clause_kind=SPCondition.ClauseKind.WHERE
        )
        .select_related("detail_field")
        .order_by("ordinal", "id")
    )


def _read_order_conditions(definition: SPDefinition) -> list[SPCondition]:
    return list(
        definition.conditions.filter(clause_kind=SPCondition.ClauseKind.ORDER)
        .select_related("detail_field")
        .order_by("ordinal", "id")
    )


def _read_fetch_condition(definition: SPDefinition) -> SPCondition | None:
    return (
        definition.conditions.filter(clause_kind=SPCondition.ClauseKind.FETCH)
        .order_by("id")
        .first()
    )


def _read_order_dir_map(
    proj_fields: list, order_rows: list[SPCondition]
) -> dict[int, str]:
    """Dirección guardada (ASC|DESC) por `detail_id` a partir de condiciones ORDER (ordinal)."""
    m: dict[int, str] = {}
    for c in order_rows:
        if c.detail_field_id:
            o = (c.operator or "ASC").strip().upper()
            m[int(c.detail_field_id)] = o if o in ("ASC", "DESC") else ""
    return {f.pk: m.get(f.pk, "") for f in proj_fields}


def _read_step3_selected_ids(definition: SPDefinition) -> list[int]:
    ids: list[int] = []
    for a in definition.assignments.select_related("detail_field").all():
        if is_read_projection_assignment(a) and a.detail_field_id:
            ids.append(int(a.detail_field_id))
    if ids:
        return ids
    st = SPStepState.objects.filter(
        sp_definition=definition, step_number=3
    ).first()
    if st and isinstance(st.payload_json, dict):
        return normalize_selected_field_ids(
            st.payload_json.get("detail_field_ids") or []
        )
    return []


def _dlt_like_where_rows_for_read(details, saved_by_field: dict) -> list[dict]:
    """Misma estructura que DLT/UPD paso WHERE (columnas: checked, value_preserve)."""
    rows: list[dict] = []
    for d in details:
        c = saved_by_field.get(d.id)
        if c:
            origin = (
                "literal"
                if c.value_origin == SPCondition.ValueOrigin.LITERAL
                else "in"
            )
            rows.append(
                {
                    "detail": d,
                    "checked": True,
                    "operator": (c.operator or "=")[:12],
                    "value_origin": origin,
                    "value_text": c.value_text or "",
                    "value_preserve": True,
                }
            )
        else:
            short = (d.field_name_short or "").strip().upper()
            suggest = f"P_{short}"[:30] if short else "P_COL"
            rows.append(
                {
                    "detail": d,
                    "checked": False,
                    "operator": "=",
                    "value_origin": "in",
                    "value_text": suggest,
                    "value_preserve": False,
                }
            )
    return rows


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET", "POST"])
def read_wizard_step1(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile

    initial, expired = load_wizard_session(request, SESSION_READ_STEP1)
    initial = initial or {}
    if expired:
        notify_warning(
            request,
            "La sesión previa del asistente READ expiró y se limpió automáticamente.",
        )
    errors: list[str] = []
    display = {
        "schema_name": initial.get("schema_name", ""),
        "procedure_name_short": initial.get("procedure_name_short", ""),
        "procedure_name_long": initial.get("procedure_name_long", ""),
        "procedure_comment": initial.get("procedure_comment", ""),
    }

    if request.method == "POST":
        schema = request.POST.get("schema_name", "")
        short = request.POST.get("procedure_name_short", "")
        long_ = request.POST.get("procedure_name_long", "")
        comment = request.POST.get("procedure_comment", "")
        display = {
            "schema_name": schema,
            "procedure_name_short": short,
            "procedure_name_long": long_,
            "procedure_comment": comment,
        }
        errors = validate_step1_identification(
            schema, short, long_, comment, company_id=profile.company_id
        )
        if any("ya está registrado" in e.lower() for e in errors):
            notify_error(
                request, "El procedimiento ya está registrado para su compañía."
            )
        if not errors:
            save_wizard_session(
                request,
                SESSION_READ_STEP1,
                {
                "schema_name": schema.strip(),
                "procedure_name_short": short.strip(),
                "procedure_name_long": long_.strip(),
                "procedure_comment": comment.strip(),
                },
            )
            return redirect("sp_asistido:read_step2")

    return render(
        request,
        "sp_asistido/read_wizard_step1.html",
        {
            "profile": profile,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 1,
            "errors": errors,
            **display,
        },
    )


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET", "POST"])
def read_wizard_step2(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    data, expired = load_wizard_session(request, SESSION_READ_STEP1)
    if expired:
        notify_warning(
            request,
            "La sesión del asistente READ expiró. Inicie nuevamente desde el paso 1.",
        )
        return redirect("sp_asistido:read_step1")
    if not data:
        notify_warning(
            request,
            "Complete primero la identificación del procedimiento.",
        )
        return redirect("sp_asistido:read_step1")

    errors: list[str] = []
    q = (request.GET.get("q") or request.POST.get("q") or "").strip()

    qs = HeaderTable.objects.filter(
        company_id=profile.company_id,
        status=HeaderTable.Status.ACTIVE,
    ).order_by("-created_at")
    if q:
        qs = qs.filter(
            Q(table_name_short__icontains=q)
            | Q(table_name_long__icontains=q)
            | Q(schema__icontains=q)
        )
    tables = list(qs[:25])

    if request.method == "POST":
        raw_id = request.POST.get("header_table_id", "").strip()
        try:
            ht_id = int(raw_id)
        except ValueError:
            ht_id = 0
        if not header_belongs_to_company(ht_id, profile.company_id):
            errors.append("Seleccione una tabla de diseño válida para su compañía.")
        if not errors:
            result = create_wizard_definition_draft(
                company_id=profile.company_id,
                header_table_id=ht_id,
                operation=SPDefinition.Operation.READ,
                step1_data=data,
                user=request.user,
            )
            if result.ok:
                definition = result.data
                clear_wizard_session(request, SESSION_READ_STEP1)
                notify_success(request, result.error_message)
                return redirect(
                    "sp_asistido:read_step",
                    definition_id=definition.pk,
                    step=3,
                )
            notify_error(request, result.error_message)

    return render(
        request,
        "sp_asistido/read_wizard_step2.html",
        {
            "profile": profile,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 2,
            "tables": tables,
            "search_q": q,
            "errors": errors,
            "step1_summary": data,
        },
    )


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET", "POST"])
def read_wizard_step_detail(
    request: HttpRequest, definition_id: int, step: int
) -> HttpResponse:
    if step not in (3, 4, 5, 6, 7):
        notify_error(request, "Paso no válido.")
        return redirect("sp_asistido:list")

    definition = _get_read_definition(request, definition_id)
    profile = request.user.profile

    if step == 3:
        return _read_step3(request, definition, profile)
    if step == 4:
        return _read_step4(request, definition, profile)
    if step == 5:
        return _read_step5(request, definition, profile)
    if step == 6:
        return _read_step6(request, definition, profile)
    return _read_step7(request, definition, profile)


def _read_step3(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    columns = list(insertable_details_for_header(definition.header_table_id))
    selected = set(_read_step3_selected_ids(definition))
    errors: list[str] = []

    if request.method == "POST":
        raw = request.POST.getlist("columns")
        ids = normalize_selected_field_ids(raw)
        errors = validate_read_column_selection(
            ids, definition.header_table_id, profile.company_id
        )
        if not errors and ids:
            details_by_id = {d.id: d for d in columns}
            with transaction.atomic():
                definition.assignments.all().delete()
                for did in ids:
                    d = details_by_id.get(did)
                    if d:
                        SPAssignment.objects.create(
                            sp_definition=definition,
                            detail_field=d,
                            source_kind=SPAssignment.SourceKind.LITERAL,
                            source_value=READ_PROJECTION_MARKER,
                            created_by=request.user,
                            updated_by=request.user,
                        )
                upsert_step_state(
                    definition,
                    3,
                    {"detail_field_ids": ids},
                    request.user,
                )
                definition.current_step = 3
                definition.updated_by = request.user
                definition.save(
                    update_fields=["current_step", "updated_at", "updated_by"]
                )
            return redirect(
                "sp_asistido:read_step",
                definition_id=definition.pk,
                step=4,
            )

    return render(
        request,
        "sp_asistido/read_wizard_step3.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 3,
            "columns": columns,
            "selected_ids": selected,
            "errors": errors,
        },
    )


def _read_step4(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition.assignments.filter(
        source_kind=SPAssignment.SourceKind.LITERAL,
        source_value=READ_PROJECTION_MARKER,
    ).exists():
        notify_warning(
            request, "Defina columnas de resultado en el paso anterior."
        )
        return redirect("sp_asistido:read_step", definition_id=definition.pk, step=3)

    details = list(_details_for_read_header(definition.header_table_id))
    wqs = _read_where_conditions(definition)
    saved_by_field = {c.detail_field_id: c for c in wqs if c.detail_field_id}

    col_ids = [d.id for d in details]
    errors: list[str] = []
    ordered_ids: list[int] = []

    if request.method == "POST":
        sel = normalize_where_col_flags(request.POST, col_ids)
        if not sel:
            errors.append(
                "Seleccione al menos un campo para el predicado WHERE (F.4).",
            )
        if not errors:
            ordered_ids = ordered_selected_detail_ids(details, sel)
            if not ordered_ids:
                errors.append(
                    "Seleccione al menos un campo para el predicado WHERE (F.4).",
                )

        if not errors:
            details_by_id = {d.id: d for d in details}
            for did in ordered_ids:
                d = details_by_id[did]
                op = (request.POST.get(f"where_op_{did}", "=") or "=").strip()
                raw_o = (
                    request.POST.get(f"where_origin_{did}", "in") or "in"
                ).lower()
                if raw_o not in ("in", "literal"):
                    raw_o = "in"
                v_origin = "IN" if raw_o == "in" else "LITERAL"
                vtext = request.POST.get(f"where_val_{did}", "") or ""
                row_errs = validate_where_row(
                    did,
                    op,
                    v_origin,
                    vtext,
                    header_id=definition.header_table_id,
                )
                for msg in row_errs:
                    errors.append(f"{d.field_name_short}: {msg}")

        if not errors and ordered_ids:
            details_by_id = {x.id: x for x in details}
            with transaction.atomic():
                definition.conditions.filter(
                    clause_kind=SPCondition.ClauseKind.WHERE
                ).delete()
                n = len(ordered_ids)
                for i, did in enumerate(ordered_ids):
                    d = details_by_id[did]
                    op = (request.POST.get(f"where_op_{did}", "=") or "=").strip()
                    raw_o = (
                        request.POST.get(f"where_origin_{did}", "in") or "in"
                    ).lower()
                    v_origin = "IN" if raw_o == "in" else "LITERAL"
                    vtext = (request.POST.get(f"where_val_{did}", "") or "").strip()
                    join = (
                        SPCondition.LogicalJoin.AND
                        if i < n - 1
                        else ""
                    )
                    SPCondition.objects.create(
                        sp_definition=definition,
                        clause_kind=SPCondition.ClauseKind.WHERE,
                        detail_field_id=d.id,
                        operator=op,
                        value_origin=(
                            SPCondition.ValueOrigin.IN_PARAM
                            if v_origin == "IN"
                            else SPCondition.ValueOrigin.LITERAL
                        ),
                        value_text=vtext,
                        logical_join=join,
                        ordinal=i,
                        created_by=request.user,
                        updated_by=request.user,
                    )
                definition.current_step = 4
                definition.updated_by = request.user
                definition.save(
                    update_fields=["current_step", "updated_at", "updated_by"]
                )
            return redirect(
                "sp_asistido:read_step",
                definition_id=definition.pk,
                step=5,
            )

    if request.method == "POST" and errors:
        err_rows: list[dict] = []
        for d in details:
            did = d.pk
            checked = bool(request.POST.get(f"where_col_{did}"))
            op = (request.POST.get(f"where_op_{did}", "=") or "=").strip()
            raw_o = (request.POST.get(f"where_origin_{did}", "in") or "in").lower()
            if raw_o not in ("in", "literal"):
                raw_o = "in"
            vtext = request.POST.get(f"where_val_{did}", "") or ""
            err_rows.append(
                {
                    "detail": d,
                    "checked": checked,
                    "operator": op,
                    "value_origin": raw_o,
                    "value_text": vtext,
                    "value_preserve": False,
                    "value_mark_touched": bool(errors) and checked,
                }
            )
        return render(
            request,
            "sp_asistido/read_wizard_step4.html",
            {
                "profile": profile,
                "definition": definition,
                "dashboard_nav_active": "sp_asistido",
                "current_step": 4,
                "where_rows": err_rows,
                "errors": errors,
            },
        )

    where_rows = _dlt_like_where_rows_for_read(details, saved_by_field)
    return render(
        request,
        "sp_asistido/read_wizard_step4.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 4,
            "where_rows": where_rows,
            "errors": errors,
        },
    )


def _read_step5(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition_has_where_clause(definition):
        notify_warning(request, "Defina primero el criterio WHERE (F.4).")
        return redirect("sp_asistido:read_step", definition_id=definition.pk, step=4)

    proj_ids = {
        a.detail_field_id
        for a in definition.assignments.all()
        if is_read_projection_assignment(a) and a.detail_field_id
    }
    proj_fields = list(
        DetailTable.objects.filter(pk__in=proj_ids).order_by("order_reg", "id")
    )
    olist = _read_order_conditions(definition)
    fcond = _read_fetch_condition(definition)
    order_dir_map = _read_order_dir_map(proj_fields, olist)
    ftxt = (fcond.value_text or "").strip() if fcond else ""
    if ftxt and ftxt.isdigit() and int(ftxt) > 0:
        fetch_unlimited = False
        fetch_limit_str = ftxt
    else:
        fetch_unlimited = True
        fetch_limit_str = "100"
    errors: list[str] = []
    read_mode = (definition.read_mode or SPDefinition.ReadMode.CURSOR).upper()
    if read_mode not in (
        SPDefinition.ReadMode.CURSOR,
        SPDefinition.ReadMode.ROW,
    ):
        read_mode = SPDefinition.ReadMode.CURSOR
    read_row_policy = (
        definition.read_row_policy or SPDefinition.ReadRowPolicy.ERROR
    ).upper()
    if read_row_policy not in (
        SPDefinition.ReadRowPolicy.ERROR,
        SPDefinition.ReadRowPolicy.FIRST,
    ):
        read_row_policy = SPDefinition.ReadRowPolicy.ERROR

    if request.method == "POST":
        read_mode = (
            request.POST.get("read_mode", SPDefinition.ReadMode.CURSOR) or ""
        ).strip().upper()
        if read_mode not in (
            SPDefinition.ReadMode.CURSOR,
            SPDefinition.ReadMode.ROW,
        ):
            read_mode = SPDefinition.ReadMode.CURSOR
        read_row_policy = (
            request.POST.get("read_row_policy", SPDefinition.ReadRowPolicy.ERROR) or ""
        ).strip().upper()
        if read_row_policy not in (
            SPDefinition.ReadRowPolicy.ERROR,
            SPDefinition.ReadRowPolicy.FIRST,
        ):
            read_row_policy = SPDefinition.ReadRowPolicy.ERROR
        order_by: list[tuple[int, str]] = []
        post_order_map: dict[int, str] = {}
        for f in proj_fields:
            u = (request.POST.get(f"order_dir_{f.pk}", "") or "").strip().upper()
            if read_mode == SPDefinition.ReadMode.CURSOR and u in ("ASC", "DESC"):
                order_by.append((f.pk, u))
                post_order_map[f.pk] = u
            else:
                post_order_map[f.pk] = ""
        order_dir_map = post_order_map
        is_unl = (
            request.POST.get("fetch_mode", "unlimited") or ""
        ).strip() == "unlimited"
        raw_fetch = (request.POST.get("fetch_limit", "") or "").strip()
        if read_mode == SPDefinition.ReadMode.ROW:
            fetch_unlimited = True
            fetch_limit_str = "1"
        elif is_unl:
            fetch_unlimited = True
        else:
            fetch_unlimited = False
            fetch_limit_str = raw_fetch
        if read_mode == SPDefinition.ReadMode.CURSOR:
            errors = validate_read_order_and_fetch(
                order_by,
                fetch_unlimited=fetch_unlimited,
                fetch_limit_text=raw_fetch if not is_unl else "1",
                allowed_detail_ids=proj_ids,
            )
        if not errors:
            with transaction.atomic():
                definition.conditions.filter(
                    clause_kind__in=[
                        SPCondition.ClauseKind.ORDER,
                        SPCondition.ClauseKind.FETCH,
                    ]
                ).delete()
                if read_mode == SPDefinition.ReadMode.CURSOR:
                    for i, (did, odr) in enumerate(order_by):
                        odir = (odr or "ASC").strip().upper()
                        if odir not in ("ASC", "DESC"):
                            odir = "ASC"
                        SPCondition.objects.create(
                            sp_definition=definition,
                            clause_kind=SPCondition.ClauseKind.ORDER,
                            detail_field_id=did,
                            operator=odir,
                            value_origin=SPCondition.ValueOrigin.LITERAL,
                            value_text="",
                            logical_join="",
                            ordinal=i,
                            created_by=request.user,
                            updated_by=request.user,
                        )
                    fval = ""
                    if not is_unl and raw_fetch.strip().isdigit():
                        fval = str(max(1, min(int(raw_fetch.strip()), 99_999)))
                    SPCondition.objects.create(
                        sp_definition=definition,
                        clause_kind=SPCondition.ClauseKind.FETCH,
                        detail_field_id=None,
                        operator="",
                        value_origin=SPCondition.ValueOrigin.LITERAL,
                        value_text=fval,
                        logical_join="",
                        ordinal=0,
                        created_by=request.user,
                        updated_by=request.user,
                    )
                definition.current_step = 5
                definition.read_mode = read_mode
                definition.read_row_policy = read_row_policy
                definition.updated_by = request.user
                definition.save(
                    update_fields=[
                        "current_step",
                        "read_mode",
                        "read_row_policy",
                        "updated_at",
                        "updated_by",
                    ]
                )
            return redirect(
                "sp_asistido:read_step",
                definition_id=definition.pk,
                step=6,
            )

    odm = order_dir_map or {}
    order_field_rows: list[dict] = [
        {
            "field": f,
            "order_dir": odm.get(f.pk, odm.get(str(f.pk), "")) or "",
        }
        for f in proj_fields
    ]

    return render(
        request,
        "sp_asistido/read_wizard_step5.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 5,
            "order_field_rows": order_field_rows,
            "fetch_unlimited": fetch_unlimited,
            "fetch_limit": fetch_limit_str,
            "read_mode": read_mode,
            "read_mode_cursor": SPDefinition.ReadMode.CURSOR,
            "read_mode_row": SPDefinition.ReadMode.ROW,
            "read_row_policy": read_row_policy,
            "read_row_policy_error": SPDefinition.ReadRowPolicy.ERROR,
            "read_row_policy_first": SPDefinition.ReadRowPolicy.FIRST,
            "errors": errors,
        },
    )


def _read_step6(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition_has_where_clause(definition):
        return redirect("sp_asistido:read_step", definition_id=definition.pk, step=4)
    wcs = _read_where_conditions(definition)

    if request.method == "POST" and request.POST.get("action") == "save_draft":
        definition.current_step = 6
        definition.updated_by = request.user
        definition.save(update_fields=["current_step", "updated_at", "updated_by"])
        notify_success(request, "Borrador guardado.")
        return redirect("sp_asistido:list")
    in_sig: list[str] = []
    seen: set[str] = set()
    for wc in wcs:
        if wc.value_origin == SPCondition.ValueOrigin.IN_PARAM and wc.detail_field_id:
            n = (wc.value_text or "").strip().upper()
            if n and n not in seen:
                seen.add(n)
                in_sig.append(
                    f"{n} {format_db2_type_for_parameter(wc.detail_field)}"
                )
    olist = _read_order_conditions(definition)
    fcond = _read_fetch_condition(definition)
    read_mode = (definition.read_mode or SPDefinition.ReadMode.CURSOR).upper()
    is_cursor_mode = read_mode == SPDefinition.ReadMode.CURSOR
    ftxt = (fcond.value_text or "").strip() if fcond else ""
    if is_cursor_mode and ftxt and ftxt.isdigit() and int(ftxt) > 0:
        fetch_unlimited = False
        fetch_n = int(ftxt)
    else:
        fetch_unlimited = True
        fetch_n = None

    return render(
        request,
        "sp_asistido/read_wizard_step6.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 6,
            "projection_assignments": list(
                definition.assignments.filter(
                    source_value=READ_PROJECTION_MARKER
                ).select_related("detail_field")
            ),
            "where_conditions": wcs,
            "order_conditions": olist if is_cursor_mode else [],
            "fetch_unlimited": fetch_unlimited,
            "fetch_n": fetch_n,
            "in_signature_parts": in_sig,
            "in_line": ", ".join(in_sig),
            "read_mode": read_mode,
            "is_cursor_mode": is_cursor_mode,
            "read_row_policy": definition.read_row_policy,
            "specific_name": suggested_specific_name(
                definition.procedure_name_short
            ),
        },
    )


def _read_step7(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    asg = list(
        definition.assignments.filter(
            source_value=READ_PROJECTION_MARKER
        ).select_related("detail_field")
    )
    wcs = _read_where_conditions(definition)
    if not asg or not wcs:
        notify_error(
            request,
            "Complete columnas, WHERE y orden/paginación (F.4 / F.5).",
        )
        return redirect("sp_asistido:read_step", definition_id=definition.pk, step=3)

    olist = _read_order_conditions(definition)
    fcond = _read_fetch_condition(definition)

    preview_sql = build_read_procedure_sql(
        definition,
        asg,
        wcs,
        olist,
        fcond,
        generated_by=request.user,
    )

    if request.method == "POST" and request.POST.get("action") == "confirm":
        result = confirm_generated_script(
            definition,
            preview_sql,
            user=request.user,
            persist_fn=persist_generated_read_script,
            persist_kwargs={
                "where_conditions": wcs,
                "assignments": asg,
            },
        )
        if result.ok:
            notify_success(request, result.error_message)
            return redirect("sp_asistido:list")
        notify_error(request, result.error_message)
        return redirect(
            "sp_asistido:read_step",
            definition_id=definition.pk,
            step=7,
        )

    if request.method == "POST" and request.POST.get("action") == "save_draft":
        definition.current_step = 7
        definition.updated_by = request.user
        definition.save(update_fields=["current_step", "updated_at", "updated_by"])
        notify_success(request, "Borrador guardado.")
        return redirect("sp_asistido:list")

    in_parts: list[str] = []
    seen: set[str] = set()
    for wc in wcs:
        if (
            wc.value_origin == SPCondition.ValueOrigin.IN_PARAM
            and wc.detail_field_id
        ):
            name = (wc.value_text or "").strip().upper()
            if name and name not in seen:
                seen.add(name)
                in_parts.append(
                    f"{name} {format_db2_type_for_parameter(wc.detail_field)}"
                )

    return render(
        request,
        "sp_asistido/read_wizard_step7.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 7,
            "preview_sql": preview_sql,
            "in_line": ", ".join(in_parts),
        },
    )
