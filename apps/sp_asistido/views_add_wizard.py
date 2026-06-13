"""Asistente ADD (INSERT) — pasos 1–7 (checklist C)."""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.sp_asistido.models import SPAssignment, SPDefinition, SPStepState
from apps.sp_asistido.services.access import get_sp_definition_or_404
from apps.sp_asistido.services.add_validation import (
    header_belongs_to_company,
    insertable_details_for_header,
    normalize_selected_field_ids,
    suggested_specific_name,
    validate_not_null_with_null_origin,
    validate_source_detail_rule,
    validate_step1_identification,
    validate_step3_columns,
)
from apps.sp_asistido.services.generate_insert_script import (
    build_insert_procedure_sql,
    format_db2_type_for_parameter,
    persist_generated_script,
)
from apps.sp_asistido.services.ui_messages import (
    notify_error,
    notify_success,
    notify_warning,
)
from apps.sp_asistido.services.sp_persistence import (
    confirm_generated_script,
    create_wizard_definition_draft,
    upsert_step_state,
)
from apps.sp_asistido.services.wizard_session import (
    clear_wizard_session,
    load_wizard_session,
    save_wizard_session,
)
from apps.sp_asistido.views import _require_profile, _require_sp_asistido_list_access
from apps.table_design.models import DetailTable, HeaderTable
from apps.userprofile.models import UserProfile

SESSION_ADD_STEP1 = "sp_asistido_add_step1"

ORIGIN_POST_MAP = {
    "in": SPAssignment.SourceKind.IN_PARAM,
    "literal": SPAssignment.SourceKind.LITERAL,
    "null": SPAssignment.SourceKind.NULL,
    "expr": SPAssignment.SourceKind.EXPR,
}

SOURCE_KIND_TO_POST = {v: k for k, v in ORIGIN_POST_MAP.items()}


def _get_add_definition(request: HttpRequest, definition_id: int) -> SPDefinition:
    return get_sp_definition_or_404(
        request.user,
        definition_id,
        operation=SPDefinition.Operation.ADD,
    )


def _step3_payload(definition: SPDefinition) -> list[int]:
    st = SPStepState.objects.filter(
        sp_definition=definition, step_number=3
    ).first()
    if not st or not isinstance(st.payload_json, dict):
        return []
    return normalize_selected_field_ids(st.payload_json.get("detail_field_ids") or [])


def _ordered_details(definition: SPDefinition, selected_ids: list[int]) -> list[DetailTable]:
    if not selected_ids:
        return []
    rows = (
        DetailTable.objects.filter(
            id__in=selected_ids,
            header_id=definition.header_table_id,
        )
        .select_related("header")
        .order_by("order_reg", "id")
    )
    return list(rows)


def _assignments_as_tuples(definition: SPDefinition):
    qs = definition.assignments.select_related("detail_field").order_by(
        "detail_field__order_reg", "id"
    )
    return [(a.detail_field, a.source_kind, a.source_value) for a in qs]


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET", "POST"])
def add_wizard_step1(request: HttpRequest) -> HttpResponse:
    """C.1 Identificación (sesión hasta elegir tabla)."""
    profile = request.user.profile

    initial, expired = load_wizard_session(request, SESSION_ADD_STEP1)
    initial = initial or {}
    if expired:
        notify_warning(
            request,
            "La sesión previa del asistente ADD expiró y se limpió automáticamente.",
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
                SESSION_ADD_STEP1,
                {
                "schema_name": schema.strip(),
                "procedure_name_short": short.strip(),
                "procedure_name_long": long_.strip(),
                "procedure_comment": comment.strip(),
                },
            )
            return redirect("sp_asistido:add_step2")

    return render(
        request,
        "sp_asistido/add_wizard_step1.html",
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
def add_wizard_step2(request: HttpRequest) -> HttpResponse:
    """C.2 Tabla destino (últimas 25 + búsqueda); crea SPDefinition en POST."""
    profile = request.user.profile
    data, expired = load_wizard_session(request, SESSION_ADD_STEP1)
    if expired:
        notify_warning(
            request,
            "La sesión del asistente ADD expiró. Inicie nuevamente desde el paso 1.",
        )
        return redirect("sp_asistido:add_step1")
    if not data:
        notify_warning(
            request,
            "Complete primero la identificación del procedimiento.",
        )
        return redirect("sp_asistido:add_step1")

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
                operation=SPDefinition.Operation.ADD,
                step1_data=data,
                user=request.user,
            )
            if result.ok:
                definition = result.data
                clear_wizard_session(request, SESSION_ADD_STEP1)
                notify_success(request, result.error_message)
                return redirect(
                    "sp_asistido:add_step",
                    definition_id=definition.pk,
                    step=3,
                )
            notify_error(request, result.error_message)

    return render(
        request,
        "sp_asistido/add_wizard_step2.html",
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
def add_wizard_step_detail(
    request: HttpRequest, definition_id: int, step: int
) -> HttpResponse:
    """Pasos 3–7 sobre una SPDefinition ADD en borrador."""
    profile = request.user.profile
    if step not in (3, 4, 5, 6, 7):
        notify_error(request, "Paso no válido.")
        return redirect("sp_asistido:list")

    definition = _get_add_definition(request, definition_id)

    if step == 3:
        return _add_step3(request, definition, profile)
    if step == 4:
        return _add_step4(request, definition, profile)
    if step == 5:
        return _add_step5(request, definition, profile)
    if step == 6:
        return _add_step6(request, definition, profile)
    return _add_step7(request, definition, profile)


def _add_step3(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    cols = insertable_details_for_header(definition.header_table_id)
    selected = set(_step3_payload(definition))
    errors: list[str] = []

    if request.method == "POST":
        raw = request.POST.getlist("columns")
        ids = normalize_selected_field_ids(raw)
        ids, verr = validate_step3_columns(
            ids, definition.header_table_id, profile.company_id
        )
        errors.extend(verr)
        if not errors:
            upsert_step_state(
                definition,
                3,
                {"detail_field_ids": ids},
                request.user,
            )
            definition.current_step = 3
            definition.updated_by = request.user
            definition.save(update_fields=["current_step", "updated_at", "updated_by"])
            return redirect(
                "sp_asistido:add_step",
                definition_id=definition.pk,
                step=4,
            )

    return render(
        request,
        "sp_asistido/add_wizard_step3.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 3,
            "columns": cols,
            "selected_ids": selected,
            "errors": errors,
        },
    )


def _add_step4(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    selected_ids = _step3_payload(definition)
    if not selected_ids:
        notify_warning(request, "Seleccione columnas en el paso anterior.")
        return redirect(
            "sp_asistido:add_step",
            definition_id=definition.pk,
            step=3,
        )

    details = _ordered_details(definition, selected_ids)
    errors: list[str] = []

    if request.method == "POST":
        for d in details:
            raw_o = (request.POST.get(f"origin_{d.pk}", "in") or "in").lower()
            sk = ORIGIN_POST_MAP.get(raw_o, SPAssignment.SourceKind.IN_PARAM)
            sv = request.POST.get(f"detail_{d.pk}", "")
            if sk == SPAssignment.SourceKind.NULL:
                sv = ""
            err = validate_source_detail_rule(sk, sv)
            if err:
                errors.append(f"{d.field_name_short}: {err}")
        if not errors:
            nn_errors = validate_not_null_with_null_origin(
                {d.id: d for d in details},
                [
                    (
                        d.id,
                        ORIGIN_POST_MAP.get(
                            (request.POST.get(f"origin_{d.pk}", "in") or "in").lower(),
                            SPAssignment.SourceKind.IN_PARAM,
                        ),
                        request.POST.get(f"detail_{d.pk}", ""),
                    )
                    for d in details
                ],
            )
            errors.extend(nn_errors)

        if not errors:
            with transaction.atomic():
                definition.assignments.all().delete()
                for d in details:
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
                definition.current_step = 4
                definition.updated_by = request.user
                definition.save(
                    update_fields=["current_step", "updated_at", "updated_by"]
                )
                upsert_step_state(
                    definition,
                    4,
                    {"saved": True},
                    request.user,
                )
            return redirect(
                "sp_asistido:add_step",
                definition_id=definition.pk,
                step=5,
            )

    if request.method == "POST" and errors:
        err_rows = []
        for d in details:
            raw_o = (request.POST.get(f"origin_{d.pk}", "in") or "in").lower()
            if raw_o not in ORIGIN_POST_MAP:
                raw_o = "in"
            val = request.POST.get(f"detail_{d.pk}", "") or ""
            err_rows.append({"detail": d, "origin": raw_o, "value": val})
        return render(
            request,
            "sp_asistido/add_wizard_step4.html",
            {
                "profile": profile,
                "definition": definition,
                "dashboard_nav_active": "sp_asistido",
                "current_step": 4,
                "column_rows": err_rows,
                "errors": errors,
            },
        )

    saved = {}
    if definition.assignments.exists() and request.method == "GET":
        saved = {
            a.detail_field_id: (a.source_kind, a.source_value)
            for a in definition.assignments.all()
        }

    column_rows = []
    for d in details:
        origin = "in"
        short = (d.field_name_short or "").strip().upper()
        val = f"P_{short}"[:30] if short else "P_COL"
        if d.id in saved:
            sk, sv = saved[d.id]
            origin = SOURCE_KIND_TO_POST.get(sk, "in")
            val = sv or ("" if sk == SPAssignment.SourceKind.NULL else val)
        column_rows.append({"detail": d, "origin": origin, "value": val})

    return render(
        request,
        "sp_asistido/add_wizard_step4.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 4,
            "column_rows": column_rows,
            "errors": errors,
        },
    )


def _add_step5(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition.assignments.exists():
        notify_warning(request, "Defina orígenes de valor antes de revisar.")
        return redirect(
            "sp_asistido:add_step",
            definition_id=definition.pk,
            step=4,
        )

    rows = []
    for a in definition.assignments.select_related("detail_field").order_by(
        "detail_field__order_reg",
        "id",
    ):
        d = a.detail_field
        ok = True
        if not d.nullable and a.source_kind == SPAssignment.SourceKind.NULL:
            ok = False
        rows.append(
            {
                "assignment": a,
                "detail": d,
                "ok": ok,
            }
        )

    if request.method == "POST":
        if not all(r["ok"] for r in rows):
            notify_error(
                request,
                "Corrija columnas obligatorias con origen NULL antes de continuar.",
            )
            return redirect(
                "sp_asistido:add_step",
                definition_id=definition.pk,
                step=4,
            )
        definition.current_step = 5
        definition.updated_by = request.user
        definition.save(update_fields=["current_step", "updated_at", "updated_by"])
        return redirect(
            "sp_asistido:add_step",
            definition_id=definition.pk,
            step=6,
        )

    return render(
        request,
        "sp_asistido/add_wizard_step5.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 5,
            "review_rows": rows,
        },
    )


def _add_step6(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition.assignments.exists():
        return redirect(
            "sp_asistido:add_step",
            definition_id=definition.pk,
            step=4,
        )

    in_params: list[str] = []
    for a in definition.assignments.order_by("detail_field__order_reg", "id"):
        if a.source_kind == SPAssignment.SourceKind.IN_PARAM and (
            a.source_value or ""
        ).strip():
            name = a.source_value.strip().upper()
            if name not in in_params:
                in_params.append(name)

    in_signature_parts = []
    for a in definition.assignments.select_related("detail_field").order_by(
        "detail_field__order_reg", "id"
    ):
        if a.source_kind != SPAssignment.SourceKind.IN_PARAM:
            continue
        name = (a.source_value or "").strip().upper()
        if not name:
            continue
        in_signature_parts.append(
            f"{name} {format_db2_type_for_parameter(a.detail_field)}"
        )

    in_line = ", ".join(in_signature_parts)

    if request.method == "POST" and request.POST.get("action") == "save_draft":
        definition.current_step = 6
        definition.updated_by = request.user
        definition.save(update_fields=["current_step", "updated_at", "updated_by"])
        notify_success(request, "Borrador guardado.")
        return redirect("sp_asistido:list")

    return render(
        request,
        "sp_asistido/add_wizard_step6.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 6,
            "in_param_names": in_params,
            "in_signature_line": in_line,
            "specific_name": suggested_specific_name(definition.procedure_name_short),
        },
    )


def _add_step7(
    request: HttpRequest, definition: SPDefinition, profile: UserProfile
) -> HttpResponse:
    if not definition.assignments.exists():
        return redirect(
            "sp_asistido:add_step",
            definition_id=definition.pk,
            step=4,
        )

    tuples = _assignments_as_tuples(definition)
    preview_sql = build_insert_procedure_sql(
        definition, tuples, generated_by=request.user
    )

    if request.method == "POST" and request.POST.get("action") == "confirm":
        result = confirm_generated_script(
            definition,
            preview_sql,
            user=request.user,
            persist_fn=persist_generated_script,
        )
        if result.ok:
            notify_success(request, result.error_message)
            return redirect("sp_asistido:list")
        notify_error(request, result.error_message)
        return redirect(
            "sp_asistido:add_step",
            definition_id=definition.pk,
            step=7,
        )

    return render(
        request,
        "sp_asistido/add_wizard_step7.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "current_step": 7,
            "preview_sql": preview_sql,
        },
    )
