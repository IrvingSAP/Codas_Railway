"""Asistente UPD (UPDATE) — pasos 1–6 (checklist E)."""

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
    suggested_specific_name,
    validate_not_null_with_null_origin,
    validate_source_detail_rule,
    validate_step1_identification,
)
from apps.sp_asistido.services.dlt_validation import definition_has_where_clause, validate_where_row
from apps.sp_asistido.services.generate_insert_script import format_db2_type_for_parameter
from apps.sp_asistido.services.generate_update_script import (
    build_update_procedure_sql,
    persist_generated_upd_script,
)
from apps.sp_asistido.services.upd_validation import (
    normalize_col_flags,
    normalize_where_col_flags,
    ordered_selected_detail_ids,
    validate_concurrency_mode,
    validate_upd_set_column_ids,
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
from apps.sp_asistido.views_add_wizard import (
    ORIGIN_POST_MAP,
    SOURCE_KIND_TO_POST,
)
from apps.table_design.models import DetailTable, HeaderTable
from apps.userprofile.models import UserProfile

SESSION_UPD_STEP1 = "sp_asistido_upd_step1"


def _get_upd_definition(request: HttpRequest, definition_id: int) -> SPDefinition:
    return get_sp_definition_or_404(
        request.user,
        definition_id,
        operation=SPDefinition.Operation.UPD,
    )


def _upd_where_conditions(definition: SPDefinition) -> list[SPCondition]:
    return list(
        definition.conditions.filter(clause_kind=SPCondition.ClauseKind.WHERE)
        .select_related("detail_field")
        .order_by("ordinal", "id")
    )


def _upd_step5_payload(definition: SPDefinition) -> dict:
    st = SPStepState.objects.filter(
        sp_definition=definition, step_number=5
    ).first()
    if not st or not isinstance(st.payload_json, dict):
        return {"mode": "none"}
    m = (st.payload_json.get("mode") or "none").strip().lower()
    if m not in ("none", "exactly_one"):
        m = "none"
    return {"mode": m}


def _details_for_where_header(header_id: int):
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


def _assignments_as_tuples(definition: SPDefinition):
    qs = definition.assignments.select_related("detail_field").order_by(
        "detail_field__order_reg", "id"
    )
    return [(a.detail_field, a.source_kind, a.source_value) for a in qs]


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET", "POST"])
def upd_wizard_step1(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile

    initial, expired = load_wizard_session(request, SESSION_UPD_STEP1)
    initial = initial or {}
    if expired:
        notify_warning(
            request,
            "La sesión previa del asistente UPD expiró y se limpió automáticamente.",
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
                SESSION_UPD_STEP1,
                {
                "schema_name": schema.strip(),
                "procedure_name_short": short.strip(),
                "procedure_name_long": long_.strip(),
                "procedure_comment": comment.strip(),
                },
            )
            return redirect("sp_asistido:upd_step2")

    return render(
        request,
        "sp_asistido/upd_wizard_step1.html",
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
def upd_wizard_step2(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    data, expired = load_wizard_session(request, SESSION_UPD_STEP1)
    if expired:
        notify_warning(
            request,
            "La sesión del asistente UPD expiró. Inicie nuevamente desde el paso 1.",
        )
        return redirect("sp_asistido:upd_step1")
    if not data:
        notify_warning(
            request,
            "Complete primero la identificación del procedimiento.",
        )
        return redirect("sp_asistido:upd_step1")

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
                operation=SPDefinition.Operation.UPD,
                step1_data=data,
                user=request.user,
            )
            if result.ok:
                definition = result.data
                clear_wizard_session(request, SESSION_UPD_STEP1)
                notify_success(request, result.error_message)
                return redirect(
                    "sp_asistido:upd_step",
                    definition_id=definition.pk,
                    step=3,
                )
            notify_error(request, result.error_message)

    return render(
        request,
        "sp_asistido/upd_wizard_step2.html",
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
def upd_wizard_step_detail(
    request: HttpRequest, definition_id: int, step: int
) -> HttpResponse:
    profile = request.user.profile
    if step not in (3, 4, 5, 6):
        notify_error(request, "Paso no válido.")
        return redirect("sp_asistido:list")

    definition = _get_upd_definition(request, definition_id)

    if step == 3:
        return _upd_step3(request, definition, profile)
    if step == 4:
        return _upd_step4(request, definition, profile)
    if step == 5:
        return _upd_step5(request, definition, profile)
    return _upd_step6(request, definition, profile)


def _upd_step3(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    cols = list(insertable_details_for_header(definition.header_table_id))
    col_ids = [c.id for c in cols]
    errors: list[str] = []

    saved = {}
    if definition.assignments.exists():
        saved = {
            a.detail_field_id: (a.source_kind, a.source_value)
            for a in definition.assignments.all()
        }

    if request.method == "POST":
        set_ids = normalize_col_flags(request.POST, col_ids)
        set_ids, verr = validate_upd_set_column_ids(
            set_ids, definition.header_table_id, profile.company_id
        )
        errors.extend(verr)

        details_by_id = {d.id: d for d in cols}
        ordered = [details_by_id[i] for i in set_ids if i in details_by_id]

        if not errors:
            for d in ordered:
                raw_o = (request.POST.get(f"origin_{d.pk}", "in") or "in").lower()
                sk = ORIGIN_POST_MAP.get(raw_o, SPAssignment.SourceKind.IN_PARAM)
                sv = request.POST.get(f"detail_{d.pk}", "")
                if sk == SPAssignment.SourceKind.NULL:
                    sv = ""
                err = validate_source_detail_rule(sk, sv)
                if err:
                    errors.append(f"{d.field_name_short}: {err}")

        if not errors and ordered:
            nn_errors = validate_not_null_with_null_origin(
                {d.id: d for d in ordered},
                [
                    (
                        d.id,
                        ORIGIN_POST_MAP.get(
                            (request.POST.get(f"origin_{d.pk}", "in") or "in").lower(),
                            SPAssignment.SourceKind.IN_PARAM,
                        ),
                        request.POST.get(f"detail_{d.pk}", ""),
                    )
                    for d in ordered
                ],
            )
            errors.extend(nn_errors)

        if not errors and ordered:
            with transaction.atomic():
                definition.assignments.all().delete()
                for d in ordered:
                    raw_o = (request.POST.get(f"origin_{d.pk}", "in") or "in").lower()
                    sk = ORIGIN_POST_MAP.get(raw_o, SPAssignment.SourceKind.IN_PARAM)
                    sv = (request.POST.get(f"detail_{d.pk}", "") or "").strip()
                    if sk == SPAssignment.SourceKind.NULL:
                        sv = ""
                    SPAssignment.objects.create(
                        sp_definition=definition,
                        detail_field=d,
                        source_kind=sk,
                        source_value=sv,
                        created_by=request.user,
                        updated_by=request.user,
                    )
                upsert_step_state(
                    definition,
                    3,
                    {"detail_field_ids": set_ids},
                    request.user,
                )
                definition.current_step = 3
                definition.updated_by = request.user
                definition.save(
                    update_fields=["current_step", "updated_at", "updated_by"]
                )
            return redirect(
                "sp_asistido:upd_step",
                definition_id=definition.pk,
                step=4,
            )

    if request.method == "POST" and errors:
        err_rows = []
        for d in cols:
            checked = request.POST.get(f"col_{d.pk}")
            raw_o = (request.POST.get(f"origin_{d.pk}", "in") or "in").lower()
            if raw_o not in ORIGIN_POST_MAP:
                raw_o = "in"
            val = request.POST.get(f"detail_{d.pk}", "") or ""
            err_rows.append(
                {
                    "detail": d,
                    "checked": bool(checked),
                    "origin": raw_o,
                    "value": val,
                }
            )
        return render(
            request,
            "sp_asistido/upd_wizard_step3.html",
            {
                "profile": profile,
                "definition": definition,
                "dashboard_nav_active": "sp_asistido",
                "current_step": 3,
                "columns": cols,
                "column_rows": err_rows,
                "errors": errors,
            },
        )

    column_rows = []
    for d in cols:
        origin = "in"
        val = ""
        checked = d.id in saved
        if d.id in saved:
            sk, sv = saved[d.id]
            origin = SOURCE_KIND_TO_POST.get(sk, "in")
            val = sv or ""
        else:
            short = (d.field_name_short or "").strip().upper()
            val = f"P_{short}"[:30] if short else "P_COL"
        column_rows.append(
            {
                "detail": d,
                "checked": checked,
                "origin": origin,
                "value": val,
            }
        )

    return render(
        request,
        "sp_asistido/upd_wizard_step3.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 3,
            "columns": cols,
            "column_rows": column_rows,
            "errors": errors,
        },
    )


def _where_rows_for_step4(
    details: list[DetailTable], saved_by_field: dict
) -> list[dict]:
    """Una fila por columna: checkbox + operador/origen/valor (vista edición)."""
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


def _upd_step4(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition.assignments.exists():
        notify_warning(request, "Defina primero columnas SET y orígenes.")
        return redirect(
            "sp_asistido:upd_step",
            definition_id=definition.pk,
            step=3,
        )

    details = list(_details_for_where_header(definition.header_table_id))
    col_ids = [d.id for d in details]
    wqs = _upd_where_conditions(definition)
    saved_by_field = {c.detail_field_id: c for c in wqs if c.detail_field_id}

    errors: list[str] = []
    ordered_ids: list[int] = []

    if request.method == "POST":
        sel = normalize_where_col_flags(request.POST, col_ids)
        if not sel:
            errors.append(
                "Seleccione al menos un campo para el predicado WHERE.",
            )
        if not errors:
            ordered_ids = ordered_selected_detail_ids(details, sel)
            if not ordered_ids:
                errors.append(
                    "Seleccione al menos un campo para el predicado WHERE.",
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
                "sp_asistido:upd_step",
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
                }
            )
        return render(
            request,
            "sp_asistido/upd_wizard_step4.html",
            {
                "profile": profile,
                "definition": definition,
                "dashboard_nav_active": "sp_asistido",
                "current_step": 4,
                "where_rows": err_rows,
                "errors": errors,
            },
        )

    where_rows = _where_rows_for_step4(details, saved_by_field)
    return render(
        request,
        "sp_asistido/upd_wizard_step4.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 4,
            "where_rows": where_rows,
            "errors": errors,
        },
    )


def _upd_step5(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition_has_where_clause(definition):
        notify_warning(request, "Defina primero la condición WHERE obligatoria.")
        return redirect(
            "sp_asistido:upd_step",
            definition_id=definition.pk,
            step=4,
        )

    payload = _upd_step5_payload(definition)
    errors: list[str] = []

    if request.method == "POST":
        mode = (request.POST.get("concurrency_mode") or "none").strip().lower()
        errors = validate_concurrency_mode(mode)
        if not errors:
            upsert_step_state(
                definition,
                5,
                {"mode": mode},
                request.user,
            )
            definition.current_step = 5
            definition.updated_by = request.user
            definition.save(
                update_fields=["current_step", "updated_at", "updated_by"]
            )
            return redirect(
                "sp_asistido:upd_step",
                definition_id=definition.pk,
                step=6,
            )

    return render(
        request,
        "sp_asistido/upd_wizard_step5.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 5,
            "concurrency_mode": payload["mode"],
            "errors": errors,
        },
    )


def _upd_step6(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition.assignments.exists():
        notify_error(request, "No hay columnas SET definidas.")
        return redirect(
            "sp_asistido:upd_step",
            definition_id=definition.pk,
            step=3,
        )
    wcs = _upd_where_conditions(definition)
    if not wcs:
        notify_error(
            request,
            "No se puede generar UPDATE sin condición WHERE.",
        )
        return redirect(
            "sp_asistido:upd_step",
            definition_id=definition.pk,
            step=4,
        )

    tuples = _assignments_as_tuples(definition)
    mode_payload = _upd_step5_payload(definition)
    conc = mode_payload["mode"]

    review_rows = []
    for a in definition.assignments.select_related("detail_field").order_by(
        "detail_field__order_reg", "id"
    ):
        d = a.detail_field
        ok = True
        if not d.nullable and a.source_kind == SPAssignment.SourceKind.NULL:
            ok = False
        review_rows.append({"assignment": a, "detail": d, "ok": ok})

    preview_sql = build_update_procedure_sql(
        definition,
        tuples,
        wcs,
        concurrency_mode=conc,
        generated_by=request.user,
    )

    in_parts = []
    seen: set[str] = set()
    for d, sk, sv in tuples:
        if sk == SPAssignment.SourceKind.IN_PARAM:
            name = (sv or "").strip().upper()
            if name and name not in seen:
                seen.add(name)
                in_parts.append(f"{name} {format_db2_type_for_parameter(d)}")
    for wc in wcs:
        if wc.value_origin == SPCondition.ValueOrigin.IN_PARAM and wc.detail_field_id:
            name = (wc.value_text or "").strip().upper()
            if name and name not in seen:
                seen.add(name)
                in_parts.append(
                    f"{name} {format_db2_type_for_parameter(wc.detail_field)}"
                )
    in_line = ", ".join(in_parts)

    if request.method == "POST":
        action = request.POST.get("action") or ""
        if not all(r["ok"] for r in review_rows):
            notify_error(
                request,
                "Corrija columnas obligatorias con origen NULL antes de generar.",
            )
            return redirect(
                "sp_asistido:upd_step",
                definition_id=definition.pk,
                step=6,
            )
        if action == "save_draft":
            definition.current_step = 6
            definition.updated_by = request.user
            definition.save(
                update_fields=["current_step", "updated_at", "updated_by"]
            )
            notify_success(request, "Borrador guardado.")
            return redirect("sp_asistido:list")
        if action == "confirm":
            result = confirm_generated_script(
                definition,
                preview_sql,
                user=request.user,
                persist_fn=persist_generated_upd_script,
                persist_kwargs={
                    "assignments": tuples,
                    "where_conditions": wcs,
                },
            )
            if result.ok:
                notify_success(request, result.error_message)
                return redirect("sp_asistido:list")
            notify_error(request, result.error_message)
            return redirect(
                "sp_asistido:upd_step",
                definition_id=definition.pk,
                step=6,
            )

    all_review_ok = all(r["ok"] for r in review_rows)

    return render(
        request,
        "sp_asistido/upd_wizard_step6.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 6,
            "preview_sql": preview_sql,
            "review_rows": review_rows,
            "all_review_ok": all_review_ok,
            "where_conditions": wcs,
            "concurrency_mode": conc,
            "in_signature_line": in_line,
            "specific_name": suggested_specific_name(
                definition.procedure_name_short
            ),
        },
    )
