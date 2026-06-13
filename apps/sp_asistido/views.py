"""Vistas del módulo SP Asistido (panel)."""

from __future__ import annotations

import csv
from datetime import date
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.sp_asistido.models import SPDefinition, SPStepState
from apps.sp_asistido.services.add_validation import validate_step1_identification
from apps.sp_asistido.services.access import (
    MSG_SP_ASISTIDO_NO_COMPANY,
    MSG_UNAUTHORIZED_SP_ASISTIDO,
    get_sp_definition_or_404,
    has_sp_asistido_list_access,
    sp_definition_queryset_for_user,
)
from apps.sp_asistido.services.operation_ui import extend_errors_from_result
from apps.sp_asistido.services.sp_persistence import (
    reopen_definition_wizard,
    update_definition_identification,
    upsert_step_state,
)
from apps.sp_asistido.services.ui_messages import (
    notify_error,
    notify_info,
    notify_success,
    notify_warning,
)
from apps.sp_asistido.services.wizard_session import clear_wizard_session
from apps.table_design.models import HeaderTable
from apps.userprofile.models import UserProfile

ALLOWED_PER_PAGE = (10, 15, 25, 50)
DEFAULT_PER_PAGE = 15

ORDERING_MAP = {
    "-updated_at": ("-updated_at",),
    "updated_at": ("updated_at",),
    "procedure_name_short": ("procedure_name_short",),
    "-procedure_name_short": ("-procedure_name_short",),
    "operation_name": ("operation", "procedure_name_short"),
    "header_then_name": ("header_table__table_name_short", "procedure_name_short"),
    "status_draft_first": None,
}

WIZARD_STEP1_SESSION_KEYS = {
    "add": "sp_asistido_add_step1",
    "dlt": "sp_asistido_dlt_step1",
    "upd": "sp_asistido_upd_step1",
    "read": "sp_asistido_read_step1",
}


def _require_profile(view_func):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        try:
            request.user.profile
        except UserProfile.DoesNotExist:
            notify_error(
                request,
                "Su cuenta no tiene perfil configurado. Contacte al administrador de sistemas.",
            )
            return redirect("security:security_login")
        return view_func(request, *args, **kwargs)

    return wrapper


def _require_sp_asistido_list_access(view_func):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        profile = request.user.profile
        if not has_sp_asistido_list_access(profile):
            if not profile.company_id:
                notify_error(request, MSG_SP_ASISTIDO_NO_COMPANY)
            else:
                notify_error(request, MSG_UNAUTHORIZED_SP_ASISTIDO)
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def _get_per_page(request: HttpRequest) -> int:
    try:
        per_page = int(request.GET.get("per_page", DEFAULT_PER_PAGE))
    except ValueError:
        per_page = DEFAULT_PER_PAGE
    if per_page not in ALLOWED_PER_PAGE:
        per_page = DEFAULT_PER_PAGE
    return per_page


def _pagination_qs(request: HttpRequest) -> str:
    q = request.GET.copy()
    q.pop("page", None)
    return q.urlencode()


def _export_csv_querystring(request: HttpRequest) -> str:
    """Mismos filtros que el listado, sin paginación (para enlace export CSV)."""
    q = request.GET.copy()
    q.pop("page", None)
    q.pop("per_page", None)
    return q.urlencode()


def _paginate(request: HttpRequest, qs):
    per_page = _get_per_page(request)
    paginator = Paginator(qs, per_page)
    page = request.GET.get("page", "1")
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def _apply_ordering(qs, ordering: str):
    if ordering == "status_draft_first":
        return qs.annotate(
            _status_sort=Case(
                When(status=SPDefinition.Status.DRAFT, then=Value(0)),
                When(status=SPDefinition.Status.ACTIVE, then=Value(1)),
                When(status=SPDefinition.Status.INACTIVE, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by("_status_sort", "procedure_name_short")
    fields = ORDERING_MAP.get(ordering)
    if not fields:
        return qs.order_by("-updated_at")
    return qs.order_by(*fields)


def _filtered_definitions(request: HttpRequest):
    qs = sp_definition_queryset_for_user(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(procedure_name_short__icontains=q)
            | Q(procedure_name_long__icontains=q)
            | Q(schema_name__icontains=q)
            | Q(procedure_comment__icontains=q)
            | Q(header_table__table_name_short__icontains=q)
            | Q(header_table__table_name_long__icontains=q)
        )

    op = request.GET.get("operation", "").strip()
    if op in dict(SPDefinition.Operation.choices):
        qs = qs.filter(operation=op)

    ht = request.GET.get("header_table", "").strip()
    if ht.isdigit():
        qs = qs.filter(header_table_id=int(ht))

    ordering = (request.GET.get("ordering") or "").strip() or "-updated_at"
    if ordering not in ORDERING_MAP:
        ordering = "-updated_at"
    qs = _apply_ordering(qs, ordering)
    return qs, ordering


def _list_stats(qs):
    return {
        "total": qs.count(),
        "read": qs.filter(operation=SPDefinition.Operation.READ).count(),
        "add": qs.filter(operation=SPDefinition.Operation.ADD).count(),
        "upd": qs.filter(operation=SPDefinition.Operation.UPD).count(),
        "dlt": qs.filter(operation=SPDefinition.Operation.DLT).count(),
        "script_ok": qs.filter(script_generated=True).count(),
        "drafts": qs.filter(status=SPDefinition.Status.DRAFT).count(),
    }


def _header_filter_choices(profile: UserProfile):
    return (
        HeaderTable.objects.filter(company_id=profile.company_id)
        .order_by("-created_at")[:200]
        .values_list("id", "schema", "table_name_short", "table_name_long")
    )


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET"])
def definition_list(request: HttpRequest) -> HttpResponse:
    """Listado principal de definiciones SP (B.1–B.6)."""
    profile = request.user.profile
    base_qs = sp_definition_queryset_for_user(request.user)
    if not base_qs.exists():
        return render(
            request,
            "sp_asistido/definition_list_empty.html",
            {
                "profile": profile,
                "dashboard_nav_active": "sp_asistido",
            },
        )

    qs, ordering = _filtered_definitions(request)
    stats = _list_stats(qs)
    page_obj = _paginate(request, qs)
    header_rows = list(_header_filter_choices(profile))
    header_table_filter = request.GET.get("header_table", "").strip()
    operation_filter = request.GET.get("operation", "").strip()
    q_filter = request.GET.get("q", "").strip()

    return render(
        request,
        "sp_asistido/definition_list.html",
        {
            "profile": profile,
            "definitions": page_obj.object_list,
            "page_obj": page_obj,
            "ordering": ordering,
            "stats": stats,
            "header_filter_rows": header_rows,
            "header_table_filter": header_table_filter,
            "operation_filter": operation_filter,
            "q_filter": q_filter,
            "operation_choices": SPDefinition.Operation.choices,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "dashboard_nav_active": "sp_asistido",
            "ordering_options": [
                ("-updated_at", "Actualizado (más reciente)"),
                ("procedure_name_short", "Nombre del SP (A→Z)"),
                ("operation_name", "Operación · nombre"),
                ("header_then_name", "Tabla de diseño · nombre"),
                ("status_draft_first", "Estado (borrador primero)"),
            ],
            "export_csv_qs": _export_csv_querystring(request),
        },
    )


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET"])
def definition_list_export_csv(request: HttpRequest) -> HttpResponse:
    """Exporta a CSV todas las definiciones que cumplen los filtros del listado (sin paginar)."""
    qs, _ordering = _filtered_definitions(request)
    qs = qs.select_related("header_table", "company")

    filename = f"codas_sp_definitions_{date.today().isoformat()}.csv"
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow(
        [
            "id",
            "esquema_sp",
            "nombre_corto_sp",
            "nombre_largo_sp",
            "comentario",
            "operacion",
            "read_mode",
            "read_row_policy",
            "estado",
            "company_id",
            "company_nombre_corto",
            "tabla_esquema",
            "tabla_nombre_corto",
            "tabla_nombre_largo",
            "script_generado",
            "fecha_script",
            "paso_wizard",
            "creado_el",
            "actualizado_el",
            "creado_por",
            "actualizado_por",
        ]
    )
    for d in qs:
        ht = d.header_table
        writer.writerow(
            [
                d.pk,
                d.schema_name,
                d.procedure_name_short,
                d.procedure_name_long,
                d.procedure_comment or "",
                d.get_operation_display(),
                (
                    "READ-R"
                    if d.operation == SPDefinition.Operation.READ and d.read_mode == SPDefinition.ReadMode.ROW
                    else (
                        "READ-C"
                        if d.operation == SPDefinition.Operation.READ
                        else ""
                    )
                ),
                (
                    "first"
                    if d.operation == SPDefinition.Operation.READ and d.read_row_policy == SPDefinition.ReadRowPolicy.FIRST
                    else (
                        "error"
                        if d.operation == SPDefinition.Operation.READ
                        else ""
                    )
                ),
                d.get_status_display(),
                d.company_id,
                d.company.name_short if d.company_id else "",
                ht.schema,
                ht.table_name_short,
                ht.table_name_long,
                "Sí" if d.script_generated else "No",
                d.script_date.isoformat() if d.script_date else "",
                d.current_step,
                d.created_at.isoformat(timespec="seconds") if d.created_at else "",
                d.updated_at.isoformat(timespec="seconds") if d.updated_at else "",
                d.created_by.get_username() if d.created_by_id else "",
                d.updated_by.get_username() if d.updated_by_id else "",
            ]
        )
    return response


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET"])
def definition_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Ficha de una definición SP en el ámbito del listado (B — detalle)."""
    profile = request.user.profile
    definition = get_sp_definition_or_404(
        request.user,
        pk,
    )
    counts = {
        "assignments": definition.assignments.count(),
        "parameters": definition.parameters.count(),
        "conditions": definition.conditions.count(),
        "step_states": definition.step_states.count(),
        "artifacts": definition.artifact_versions.count(),
    }
    current_artifact = definition.artifact_versions.filter(
        is_current=True
    ).first()

    continue_add_step = None
    if (
        definition.operation == SPDefinition.Operation.ADD
        and not definition.script_generated
    ):
        step = definition.current_step or 1
        continue_add_step = max(3, min(max(step, 3), 7))

    continue_dlt_step = None
    if (
        definition.operation == SPDefinition.Operation.DLT
        and not definition.script_generated
    ):
        step_d = definition.current_step or 1
        continue_dlt_step = max(3, min(max(step_d, 3), 6))

    continue_upd_step = None
    if (
        definition.operation == SPDefinition.Operation.UPD
        and not definition.script_generated
    ):
        step_u = definition.current_step or 1
        continue_upd_step = max(3, min(max(step_u, 3), 6))

    continue_read_step = None
    if (
        definition.operation == SPDefinition.Operation.READ
        and not definition.script_generated
    ):
        step_r = definition.current_step or 1
        continue_read_step = max(3, min(max(step_r, 3), 7))

    return render(
        request,
        "sp_asistido/definition_detail.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "counts": counts,
            "current_artifact": current_artifact,
            "continue_add_step": continue_add_step,
            "continue_dlt_step": continue_dlt_step,
            "continue_upd_step": continue_upd_step,
            "continue_read_step": continue_read_step,
        },
    )


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET", "POST"])
def definition_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edición de identificación y estado (metadatos de cabecera)."""
    profile = request.user.profile
    definition = get_sp_definition_or_404(
        request.user,
        pk,
    )
    status_choices = list(SPDefinition.Status.choices)
    errors: list[str] = []
    display = {
        "schema_name": definition.schema_name,
        "procedure_name_short": definition.procedure_name_short,
        "procedure_name_long": definition.procedure_name_long,
        "procedure_comment": definition.procedure_comment or "",
        "status": definition.status,
    }
    if request.method == "POST":
        schema = request.POST.get("schema_name", "")
        short = request.POST.get("procedure_name_short", "")
        long_ = request.POST.get("procedure_name_long", "")
        comment = request.POST.get("procedure_comment", "")
        raw_st = (request.POST.get("status", "") or "").strip()
        display = {
            "schema_name": schema,
            "procedure_name_short": short,
            "procedure_name_long": long_,
            "procedure_comment": comment,
            "status": raw_st,
        }
        valid_status = {c[0] for c in status_choices}
        if raw_st not in valid_status:
            errors.append("Estado de la definición no válido.")
        errors += validate_step1_identification(
            schema,
            short,
            long_,
            comment,
            company_id=definition.company_id,
            exclude_definition_pk=definition.pk,
        )
        if not errors:
            st_val = (
                raw_st
                if raw_st in valid_status
                else definition.status
            )
            result = update_definition_identification(
                definition,
                schema_name=schema,
                procedure_name_short=short,
                procedure_name_long=long_,
                procedure_comment=comment,
                status=st_val,
                user=request.user,
            )
            if not result.ok:
                notify_error(request, result.error_message)
                extend_errors_from_result(errors, result)
            else:
                payload: dict
                st_row = SPStepState.objects.filter(
                    sp_definition=definition, step_number=1
                ).first()
                if st_row and isinstance(st_row.payload_json, dict):
                    payload = dict(st_row.payload_json)
                else:
                    payload = {}
                payload.update(
                    {
                        "schema_name": definition.schema_name,
                        "procedure_name_short": definition.procedure_name_short,
                        "procedure_name_long": definition.procedure_name_long,
                        "procedure_comment": definition.procedure_comment,
                    }
                )
                upsert_step_state(definition, 1, payload, request.user)
                if definition.script_generated:
                    notify_info(
                        request,
                        "Si cambió esquema o nombre del SP, revise o regenere el script para que coincida con la definición.",
                    )
                else:
                    notify_success(request, result.error_message)
                return redirect("sp_asistido:detail", pk=definition.pk)

        if errors and raw_st not in valid_status:
            display["status"] = definition.status

    return render(
        request,
        "sp_asistido/definition_edit.html",
        {
            "profile": profile,
            "definition": definition,
            "dashboard_nav_active": "sp_asistido",
            "status_choices": status_choices,
            "operation_display": definition.get_operation_display(),
            "table_label": f"{definition.header_table.schema}.{definition.header_table.table_name_short}",
            "errors": errors,
            **display,
        },
    )


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["POST"])
def definition_reopen_wizard(request: HttpRequest, pk: int) -> HttpResponse:
    """Reabre el asistente de la definición para ajustar lógica y regenerar script."""
    definition = get_sp_definition_or_404(request.user, pk)
    route_name = {
        SPDefinition.Operation.ADD: "sp_asistido:add_step",
        SPDefinition.Operation.DLT: "sp_asistido:dlt_step",
        SPDefinition.Operation.UPD: "sp_asistido:upd_step",
        SPDefinition.Operation.READ: "sp_asistido:read_step",
    }.get(definition.operation)
    if not route_name:
        notify_error(request, "La operación de la definición no es válida.")
        return redirect("sp_asistido:detail", pk=definition.pk)

    if definition.script_generated:
        result = reopen_definition_wizard(definition, user=request.user)
        if result.ok:
            notify_warning(request, result.error_message)
        else:
            notify_error(request, result.error_message)
            return redirect("sp_asistido:detail", pk=definition.pk)
    return redirect(route_name, definition_id=definition.pk, step=3)


def _wizard_start_url(operation: str) -> str:
    """URL estática del prototipo HTML según operación (hasta existir wizard Django)."""
    base = "/static/prototypes/sp-asistido/"
    mapping = {
        "READ": "sp-asistido-read-01-name-sp.html",
        "ADD": "sp-asistido-add-01-name-sp.html",
        "UPD": "sp-asistido-upd-01-name-sp.html",
        "DLT": "sp-asistido-dlt-01-name-sp.html",
    }
    return base + mapping.get(operation, "sp-asistido-list-demo.html")


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["GET"])
def wizard_redirect(request: HttpRequest, operation: str) -> HttpResponse:
    """ADD, READ, DLT, UPD → asistente en panel; otras operaciones → prototipo estático si aplica."""
    operation = operation.strip().upper()
    valid = {c[0] for c in SPDefinition.Operation.choices}
    if operation not in valid:
        notify_warning(request, "Operación no reconocida.")
        return redirect("sp_asistido:list")
    if operation == SPDefinition.Operation.ADD:
        return redirect("sp_asistido:add_step1")
    if operation == SPDefinition.Operation.READ:
        return redirect("sp_asistido:read_step1")
    if operation == SPDefinition.Operation.DLT:
        return redirect("sp_asistido:dlt_step1")
    if operation == SPDefinition.Operation.UPD:
        return redirect("sp_asistido:upd_step1")
    target = _wizard_start_url(operation)
    return redirect(target)


@login_required
@_require_profile
@_require_sp_asistido_list_access
@require_http_methods(["POST"])
def wizard_cancel(request: HttpRequest, flow: str) -> HttpResponse:
    """Limpia sesión temporal del asistente y vuelve al listado."""
    key = WIZARD_STEP1_SESSION_KEYS.get((flow or "").strip().lower())
    if not key:
        notify_warning(request, "Flujo de asistente no reconocido para cancelar.")
        return redirect("sp_asistido:list")
    clear_wizard_session(request, key)
    notify_info(request, "Asistente cancelado. Se limpió la sesión temporal.")
    return redirect("sp_asistido:list")
