from __future__ import annotations

import hashlib
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.maintenance_builder.models import (
    MaintenanceDefinition,
    MaintenanceProcessLog,
    MaintenanceScriptVersion,
    MaintenanceSourceSelection,
    MaintenanceSpSelection,
)
from apps.sources.models import SourceTemplate
from apps.sp_asistido.models import SPDefinition
from apps.table_design.models import HeaderTable
from apps.userprofile.models import UserProfile

ALLOWED_PER_PAGE = (10, 20, 30, 50)
DEFAULT_PER_PAGE = 10

ORDERING_MAP = {
    "-updated_at": ("-updated_at",),
    "name_asc": ("name_short",),
    "name_desc": ("-name_short",),
    "status": ("status", "name_short"),
}


def _require_profile(view_func):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        try:
            request.user.profile
        except UserProfile.DoesNotExist:
            return render(request, "dashboard/home_user.html", status=403)
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
    query = request.GET.copy()
    query.pop("page", None)
    return query.urlencode()


def _paginate(request: HttpRequest, qs):
    paginator = Paginator(qs, _get_per_page(request))
    page = request.GET.get("page", "1")
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def _queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return MaintenanceDefinition.objects.none()
    return (
        MaintenanceDefinition.objects.filter(company_id=profile.company_id)
        .select_related("header_table")
        .prefetch_related("sp_selections__sp_definition", "script_versions")
    )


def _apply_filters(request: HttpRequest, qs):
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(name_short__icontains=q)
            | Q(name_long__icontains=q)
            | Q(comment__icontains=q)
            | Q(header_table__schema__icontains=q)
            | Q(header_table__table_name_short__icontains=q)
            | Q(header_table__table_name_long__icontains=q)
            | Q(sp_selections__sp_definition__procedure_name_short__icontains=q)
        )

    status_filter = request.GET.get("status", "").strip()
    if status_filter in dict(MaintenanceDefinition.Status.choices):
        qs = qs.filter(status=status_filter)

    table_filter = request.GET.get("table", "").strip()
    if table_filter.isdigit():
        qs = qs.filter(header_table_id=int(table_filter))

    ordering = request.GET.get("ordering", "").strip() or "-updated_at"
    if ordering not in ORDERING_MAP:
        ordering = "-updated_at"
    qs = qs.order_by(*ORDERING_MAP[ordering]).distinct()
    return qs, ordering, status_filter, table_filter, q


def _list_stats(qs):
    return {
        "total": qs.count(),
        "generated": qs.filter(status=MaintenanceDefinition.Status.GENERATED).count(),
        "drafts": qs.filter(status=MaintenanceDefinition.Status.DRAFT).count(),
        "inactive": qs.filter(status=MaintenanceDefinition.Status.INACTIVE).count(),
    }


def _table_filter_choices(profile: UserProfile):
    if not profile.company_id:
        return []
    return (
        HeaderTable.objects.filter(company_id=profile.company_id)
        .order_by("table_name_short")
        .values_list("id", "schema", "table_name_short")
    )


def _header_table_queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return HeaderTable.objects.none()
    return HeaderTable.objects.filter(company_id=profile.company_id)


def _apply_header_table_filters(request: HttpRequest, qs):
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(table_name_short__icontains=q)
            | Q(table_name_long__icontains=q)
            | Q(schema__icontains=q)
        )

    schema_filter = request.GET.get("schema", "").strip()
    if schema_filter:
        qs = qs.filter(schema=schema_filter)

    status_filter = request.GET.get("status", "").strip()
    if status_filter in dict(HeaderTable.Status.choices):
        qs = qs.filter(status=status_filter)

    table_type_filter = request.GET.get("table_type", "").strip()
    if table_type_filter in dict(HeaderTable.TableKind.choices):
        qs = qs.filter(table_type=table_type_filter)

    return (
        qs.order_by("schema", "table_name_short"),
        q,
        schema_filter,
        status_filter,
        table_type_filter,
    )


def _schema_filter_choices(qs):
    return list(qs.order_by("schema").values_list("schema", flat=True).distinct())


def _readc_queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return SPDefinition.objects.none()
    return (
        SPDefinition.objects.filter(
            company_id=profile.company_id,
            operation=SPDefinition.Operation.READ,
            read_mode=SPDefinition.ReadMode.CURSOR,
        )
        .select_related("header_table")
        .order_by("-updated_at")
    )


def _apply_readc_filters(request: HttpRequest, qs):
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(procedure_name_short__icontains=q)
            | Q(procedure_name_long__icontains=q)
            | Q(schema_name__icontains=q)
            | Q(header_table__table_name_short__icontains=q)
            | Q(header_table__table_name_long__icontains=q)
        )
    schema_filter = request.GET.get("schema", "").strip()
    if schema_filter:
        qs = qs.filter(schema_name=schema_filter)
    status_filter = request.GET.get("status", "").strip()
    if status_filter in dict(SPDefinition.Status.choices):
        qs = qs.filter(status=status_filter)
    script_filter = request.GET.get("script", "").strip()
    if script_filter == "1":
        qs = qs.filter(script_generated=True)
    elif script_filter == "0":
        qs = qs.filter(script_generated=False)
    return qs, q, schema_filter, status_filter, script_filter


def _sp_schema_filter_choices(qs):
    return list(qs.order_by("schema_name").values_list("schema_name", flat=True).distinct())


def _add_queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return SPDefinition.objects.none()
    return (
        SPDefinition.objects.filter(
            company_id=profile.company_id,
            operation=SPDefinition.Operation.ADD,
        )
        .select_related("header_table")
        .order_by("-updated_at")
    )


def _readr_queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return SPDefinition.objects.none()
    return (
        SPDefinition.objects.filter(
            company_id=profile.company_id,
            operation=SPDefinition.Operation.READ,
            read_mode=SPDefinition.ReadMode.ROW,
        )
        .select_related("header_table")
        .order_by("-updated_at")
    )


def _upd_queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return SPDefinition.objects.none()
    return (
        SPDefinition.objects.filter(
            company_id=profile.company_id,
            operation=SPDefinition.Operation.UPD,
        )
        .select_related("header_table")
        .order_by("-updated_at")
    )


def _dlt_queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return SPDefinition.objects.none()
    return (
        SPDefinition.objects.filter(
            company_id=profile.company_id,
            operation=SPDefinition.Operation.DLT,
        )
        .select_related("header_table")
        .order_by("-updated_at")
    )


def _dspf_queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return SourceTemplate.objects.none()
    return (
        SourceTemplate.objects.filter(
            source_type=SourceTemplate.SourceType.DSPF,
        )
        .filter(Q(company_id=profile.company_id) | Q(company__isnull=True))
        .order_by("-updated_at")
    )


def _sqlrpgle_queryset_for_user(request: HttpRequest):
    profile = request.user.profile
    if not profile.company_id:
        return SourceTemplate.objects.none()
    return (
        SourceTemplate.objects.filter(
            source_type=SourceTemplate.SourceType.SQLRPGLE,
        )
        .filter(Q(company_id=profile.company_id) | Q(company__isnull=True))
        .order_by("-updated_at")
    )


def _apply_source_filters(request: HttpRequest, qs):
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(filename__icontains=q)
        )
    scope_filter = request.GET.get("scope", "").strip()
    if scope_filter == "G":
        qs = qs.filter(company__isnull=True)
    elif scope_filter == "C":
        qs = qs.filter(company__isnull=False)
    status_filter = request.GET.get("status", "").strip()
    if status_filter in dict(SourceTemplate.Status.choices):
        qs = qs.filter(status=status_filter)
    version_filter = request.GET.get("version", "").strip()
    if version_filter.isdigit():
        qs = qs.filter(version=int(version_filter))
    return qs, q, scope_filter, status_filter, version_filter


def _source_versions(qs):
    return list(qs.order_by("version").values_list("version", flat=True).distinct())


def _selection_map(maintenance: MaintenanceDefinition):
    by_operation = {
        sel.operation: sel
        for sel in maintenance.sp_selections.select_related("sp_definition").all()
    }
    by_role = {
        sel.role_code: sel
        for sel in maintenance.source_selections.select_related("source_template").all()
    }
    return by_operation, by_role


def _generate_sqlrpgle_script(maintenance: MaintenanceDefinition, sp_map, source_map, username: str) -> str:
    now = timezone.localtime()
    table_ref = f"{maintenance.header_table.schema}.{maintenance.header_table.table_name_short}"
    readc = sp_map.get(MaintenanceSpSelection.OperationRole.READ_C)
    add = sp_map.get(MaintenanceSpSelection.OperationRole.ADD)
    readr = sp_map.get(MaintenanceSpSelection.OperationRole.READ_R)
    upd = sp_map.get(MaintenanceSpSelection.OperationRole.UPD)
    dlt = sp_map.get(MaintenanceSpSelection.OperationRole.DLT)
    dspf = source_map.get(MaintenanceSourceSelection.RoleCode.BASE_DSPF)
    sqlrpgle = source_map.get(MaintenanceSourceSelection.RoleCode.BASE_SQLRPGLE)
    return "\n".join(
        [
            f"-- CODAS SQLRPGLE generado: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Usuario: {username}",
            f"-- Tabla: {table_ref}",
            "-- Operacion: MANTENIMIENTO",
            f"-- Mantenimiento: {maintenance.name_short}",
            f"-- READ-C: {readc.sp_definition.procedure_name_short if readc and readc.sp_definition_id else 'N/A'}",
            f"-- ADD: {add.sp_definition.procedure_name_short if add and add.sp_definition_id else 'N/A'}",
            f"-- READ-R: {readr.sp_definition.procedure_name_short if readr and readr.sp_definition_id else 'N/A'}",
            f"-- UPD: {upd.sp_definition.procedure_name_short if upd and upd.sp_definition_id else 'N/A'}",
            f"-- DLT: {dlt.sp_definition.procedure_name_short if dlt and dlt.sp_definition_id else 'N/A'}",
            f"-- DSPF: {dspf.source_template.name if dspf else 'N/A'}",
            f"-- SQLRPGLE: {sqlrpgle.source_template.name if sqlrpgle else 'N/A'}",
            "",
            f"-- TODO: ensamblar plantilla SQLRPGLE base para {maintenance.name_short}",
        ]
    )


def _next_script_version(maintenance: MaintenanceDefinition) -> int:
    current = maintenance.script_versions.order_by("-version").values_list("version", flat=True).first()
    return 1 if not current else current + 1


@login_required
@_require_profile
@require_http_methods(["GET"])
def list_view(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    base_qs = _queryset_for_user(request)
    qs, ordering, status_filter, table_filter, q_filter = _apply_filters(request, base_qs)
    page_obj = _paginate(request, qs)
    current_scripts = {
        script.maintenance_id: script
        for script in MaintenanceScriptVersion.objects.filter(
            maintenance_id__in=[m.id for m in page_obj.object_list],
            is_current=True,
        )
    }
    for maintenance in page_obj.object_list:
        maintenance.current_script_version = current_scripts.get(maintenance.id)
    stats = _list_stats(qs)
    return render(
        request,
        "maintenance_builder/list.html",
        {
            "dashboard_nav_active": "maintenance_builder",
            "profile": profile,
            "maintenances": page_obj.object_list,
            "page_obj": page_obj,
            "stats": stats,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "ordering": ordering,
            "ordering_options": [
                ("-updated_at", "Actualizado (más reciente)"),
                ("name_asc", "Nombre (A-Z)"),
                ("name_desc", "Nombre (Z-A)"),
                ("status", "Estado"),
            ],
            "q_filter": q_filter,
            "status_filter": status_filter,
            "table_filter": table_filter,
            "status_choices": MaintenanceDefinition.Status.choices,
            "table_filter_rows": list(_table_filter_choices(profile)),
            "pagination_qs": _pagination_qs(request),
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET"])
def detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    return render(
        request,
        "maintenance_builder/detail_stub.html",
        {"maintenance": maintenance, "dashboard_nav_active": "maintenance_builder"},
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def create_view(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    header_base_qs = _header_table_queryset_for_user(request)
    filtered_header_qs, q_filter, schema_filter, status_filter, table_type_filter = _apply_header_table_filters(
        request, header_base_qs
    )
    page_obj = _paginate(request, filtered_header_qs)
    selected_header_table_id = request.POST.get("header_table_id", "").strip()
    name_short_value = request.POST.get("name_short", "").strip()

    if request.method == "POST":
        has_error = False
        normalized_name = name_short_value.upper()
        if not normalized_name:
            messages.error(request, "El nombre del mantenimiento es obligatorio.")
            has_error = True
        elif len(normalized_name) > 10:
            messages.error(request, "El nombre del mantenimiento no puede exceder 10 caracteres.")
            has_error = True
        elif not normalized_name.replace("_", "").isalnum():
            messages.error(request, "El nombre del mantenimiento solo permite A-Z, 0-9 y _.")
            has_error = True
        elif MaintenanceDefinition.objects.filter(company_id=profile.company_id, name_short=normalized_name).exists():
            messages.error(request, "Ya existe un mantenimiento con ese identificador.")
            has_error = True

        if not selected_header_table_id.isdigit():
            messages.error(request, "Debe seleccionar una tabla base.")
            has_error = True
            selected_header_table = None
        else:
            selected_header_table = (
                HeaderTable.objects.filter(company_id=profile.company_id, pk=int(selected_header_table_id)).first()
            )
            if not selected_header_table:
                messages.error(request, "La tabla seleccionada no pertenece a su compañía.")
                has_error = True

        if not has_error and selected_header_table:
            maintenance = MaintenanceDefinition.objects.create(
                company_id=profile.company_id,
                name_short=normalized_name,
                name_long=normalized_name,
                header_table=selected_header_table,
                current_step=2,
                created_by=request.user,
                updated_by=request.user,
            )
            messages.success(request, "Paso 1 guardado correctamente.")
            return redirect("maintenance_builder:wizard_step2", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step1.html",
        {
            "dashboard_nav_active": "maintenance_builder",
            "page_obj": page_obj,
            "header_tables": page_obj.object_list,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "q_filter": q_filter,
            "schema_filter": schema_filter,
            "status_filter": status_filter,
            "table_type_filter": table_type_filter,
            "status_choices": HeaderTable.Status.choices,
            "table_type_choices": HeaderTable.TableKind.choices,
            "schema_choices": _schema_filter_choices(header_base_qs),
            "name_short_value": name_short_value,
            "selected_header_table_id": selected_header_table_id,
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET"])
def update_view(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    return render(
        request,
        "maintenance_builder/update_stub.html",
        {"maintenance": maintenance, "dashboard_nav_active": "maintenance_builder"},
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def wizard_step2(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    readc_base_qs = _readc_queryset_for_user(request)
    filtered_qs, q_filter, schema_filter, status_filter, script_filter = _apply_readc_filters(request, readc_base_qs)
    page_obj = _paginate(request, filtered_qs)
    selected_sp_id = request.POST.get("sp_definition_id", "").strip()
    current_selection = maintenance.sp_selections.filter(
        operation=MaintenanceSpSelection.OperationRole.READ_C
    ).select_related("sp_definition").first()

    if request.method == "POST":
        if not selected_sp_id.isdigit():
            messages.error(request, "Debe seleccionar un SP READ-C.")
        else:
            selected_sp = readc_base_qs.filter(pk=int(selected_sp_id)).first()
            if not selected_sp:
                messages.error(request, "El SP seleccionado no pertenece a su compañía o no es READ-C.")
            else:
                MaintenanceSpSelection.objects.update_or_create(
                    maintenance=maintenance,
                    operation=MaintenanceSpSelection.OperationRole.READ_C,
                    defaults={
                        "sp_definition": selected_sp,
                        "is_required": True,
                        "selection_status": MaintenanceSpSelection.SelectionStatus.SELECTED,
                        "created_by": request.user if not current_selection else current_selection.created_by,
                        "updated_by": request.user,
                    },
                )
                maintenance.current_step = max(maintenance.current_step, 3)
                maintenance.updated_by = request.user
                maintenance.save(update_fields=["current_step", "updated_by", "updated_at"])
                messages.success(request, "Paso 2 guardado correctamente.")
                return redirect("maintenance_builder:wizard_step3", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step2.html",
        {
            "maintenance": maintenance,
            "dashboard_nav_active": "maintenance_builder",
            "sp_definitions": page_obj.object_list,
            "page_obj": page_obj,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "q_filter": q_filter,
            "schema_filter": schema_filter,
            "status_filter": status_filter,
            "script_filter": script_filter,
            "schema_choices": _sp_schema_filter_choices(readc_base_qs),
            "status_choices": SPDefinition.Status.choices,
            "selected_sp_id": selected_sp_id or (str(current_selection.sp_definition_id) if current_selection else ""),
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def wizard_step3(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    add_base_qs = _add_queryset_for_user(request)
    filtered_qs, q_filter, schema_filter, status_filter, script_filter = _apply_readc_filters(request, add_base_qs)
    page_obj = _paginate(request, filtered_qs)
    selected_sp_id = request.POST.get("sp_definition_id", "").strip()
    clear_selection = request.POST.get("clear_selection", "").strip() == "1"
    current_selection = maintenance.sp_selections.filter(
        operation=MaintenanceSpSelection.OperationRole.ADD
    ).select_related("sp_definition").first()

    if request.method == "POST":
        selected_sp = None
        if selected_sp_id.isdigit():
            selected_sp = add_base_qs.filter(pk=int(selected_sp_id)).first()
            if not selected_sp:
                messages.error(request, "El SP ADD seleccionado no pertenece a su compañía.")
                return redirect("maintenance_builder:wizard_step3", pk=maintenance.pk)

        if clear_selection:
            selected_sp = None

        if selected_sp:
            MaintenanceSpSelection.objects.update_or_create(
                maintenance=maintenance,
                operation=MaintenanceSpSelection.OperationRole.ADD,
                defaults={
                    "sp_definition": selected_sp,
                    "is_required": False,
                    "selection_status": MaintenanceSpSelection.SelectionStatus.SELECTED,
                    "created_by": request.user if not current_selection else current_selection.created_by,
                    "updated_by": request.user,
                },
            )
        else:
            if current_selection:
                current_selection.sp_definition = None
                current_selection.is_required = False
                current_selection.selection_status = MaintenanceSpSelection.SelectionStatus.NOT_SELECTED
                current_selection.updated_by = request.user
                current_selection.save(
                    update_fields=[
                        "sp_definition",
                        "is_required",
                        "selection_status",
                        "updated_by",
                        "updated_at",
                    ]
                )
            else:
                MaintenanceSpSelection.objects.create(
                    maintenance=maintenance,
                    operation=MaintenanceSpSelection.OperationRole.ADD,
                    sp_definition=None,
                    is_required=False,
                    selection_status=MaintenanceSpSelection.SelectionStatus.NOT_SELECTED,
                    created_by=request.user,
                    updated_by=request.user,
                )

        maintenance.current_step = max(maintenance.current_step, 4)
        maintenance.updated_by = request.user
        maintenance.save(update_fields=["current_step", "updated_by", "updated_at"])
        messages.success(request, "Paso 3 guardado correctamente.")
        return redirect("maintenance_builder:wizard_step4", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step3.html",
        {
            "maintenance": maintenance,
            "dashboard_nav_active": "maintenance_builder",
            "sp_definitions": page_obj.object_list,
            "page_obj": page_obj,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "q_filter": q_filter,
            "schema_filter": schema_filter,
            "status_filter": status_filter,
            "script_filter": script_filter,
            "schema_choices": _sp_schema_filter_choices(add_base_qs),
            "status_choices": SPDefinition.Status.choices,
            "selected_sp_id": selected_sp_id or (str(current_selection.sp_definition_id) if current_selection and current_selection.sp_definition_id else ""),
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def wizard_step4(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    readr_base_qs = _readr_queryset_for_user(request)
    filtered_qs, q_filter, schema_filter, status_filter, script_filter = _apply_readc_filters(request, readr_base_qs)
    page_obj = _paginate(request, filtered_qs)
    selected_sp_id = request.POST.get("sp_definition_id", "").strip()
    clear_selection = request.POST.get("clear_selection", "").strip() == "1"
    current_selection = maintenance.sp_selections.filter(
        operation=MaintenanceSpSelection.OperationRole.READ_R
    ).select_related("sp_definition").first()

    if request.method == "POST":
        selected_sp = None
        if selected_sp_id.isdigit():
            selected_sp = readr_base_qs.filter(pk=int(selected_sp_id)).first()
            if not selected_sp:
                messages.error(request, "El SP READ-R seleccionado no pertenece a su compañía.")
                return redirect("maintenance_builder:wizard_step4", pk=maintenance.pk)

        if clear_selection:
            selected_sp = None

        if selected_sp:
            MaintenanceSpSelection.objects.update_or_create(
                maintenance=maintenance,
                operation=MaintenanceSpSelection.OperationRole.READ_R,
                defaults={
                    "sp_definition": selected_sp,
                    "is_required": False,
                    "selection_status": MaintenanceSpSelection.SelectionStatus.SELECTED,
                    "created_by": request.user if not current_selection else current_selection.created_by,
                    "updated_by": request.user,
                },
            )
        else:
            if current_selection:
                current_selection.sp_definition = None
                current_selection.is_required = False
                current_selection.selection_status = MaintenanceSpSelection.SelectionStatus.NOT_SELECTED
                current_selection.updated_by = request.user
                current_selection.save(
                    update_fields=[
                        "sp_definition",
                        "is_required",
                        "selection_status",
                        "updated_by",
                        "updated_at",
                    ]
                )
            else:
                MaintenanceSpSelection.objects.create(
                    maintenance=maintenance,
                    operation=MaintenanceSpSelection.OperationRole.READ_R,
                    sp_definition=None,
                    is_required=False,
                    selection_status=MaintenanceSpSelection.SelectionStatus.NOT_SELECTED,
                    created_by=request.user,
                    updated_by=request.user,
                )

        maintenance.current_step = max(maintenance.current_step, 5)
        maintenance.updated_by = request.user
        maintenance.save(update_fields=["current_step", "updated_by", "updated_at"])
        messages.success(request, "Paso 4 guardado correctamente.")
        return redirect("maintenance_builder:wizard_step5", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step4.html",
        {
            "maintenance": maintenance,
            "dashboard_nav_active": "maintenance_builder",
            "sp_definitions": page_obj.object_list,
            "page_obj": page_obj,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "q_filter": q_filter,
            "schema_filter": schema_filter,
            "status_filter": status_filter,
            "script_filter": script_filter,
            "schema_choices": _sp_schema_filter_choices(readr_base_qs),
            "status_choices": SPDefinition.Status.choices,
            "selected_sp_id": selected_sp_id
            or (str(current_selection.sp_definition_id) if current_selection and current_selection.sp_definition_id else ""),
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def wizard_step5(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    upd_base_qs = _upd_queryset_for_user(request)
    filtered_qs, q_filter, schema_filter, status_filter, script_filter = _apply_readc_filters(request, upd_base_qs)
    page_obj = _paginate(request, filtered_qs)
    selected_sp_id = request.POST.get("sp_definition_id", "").strip()
    clear_selection = request.POST.get("clear_selection", "").strip() == "1"
    current_selection = maintenance.sp_selections.filter(
        operation=MaintenanceSpSelection.OperationRole.UPD
    ).select_related("sp_definition").first()

    if request.method == "POST":
        selected_sp = None
        if selected_sp_id.isdigit():
            selected_sp = upd_base_qs.filter(pk=int(selected_sp_id)).first()
            if not selected_sp:
                messages.error(request, "El SP UPD seleccionado no pertenece a su compañía.")
                return redirect("maintenance_builder:wizard_step5", pk=maintenance.pk)

        if clear_selection:
            selected_sp = None

        if selected_sp:
            MaintenanceSpSelection.objects.update_or_create(
                maintenance=maintenance,
                operation=MaintenanceSpSelection.OperationRole.UPD,
                defaults={
                    "sp_definition": selected_sp,
                    "is_required": False,
                    "selection_status": MaintenanceSpSelection.SelectionStatus.SELECTED,
                    "created_by": request.user if not current_selection else current_selection.created_by,
                    "updated_by": request.user,
                },
            )
        else:
            if current_selection:
                current_selection.sp_definition = None
                current_selection.is_required = False
                current_selection.selection_status = MaintenanceSpSelection.SelectionStatus.NOT_SELECTED
                current_selection.updated_by = request.user
                current_selection.save(
                    update_fields=[
                        "sp_definition",
                        "is_required",
                        "selection_status",
                        "updated_by",
                        "updated_at",
                    ]
                )
            else:
                MaintenanceSpSelection.objects.create(
                    maintenance=maintenance,
                    operation=MaintenanceSpSelection.OperationRole.UPD,
                    sp_definition=None,
                    is_required=False,
                    selection_status=MaintenanceSpSelection.SelectionStatus.NOT_SELECTED,
                    created_by=request.user,
                    updated_by=request.user,
                )

        maintenance.current_step = max(maintenance.current_step, 6)
        maintenance.updated_by = request.user
        maintenance.save(update_fields=["current_step", "updated_by", "updated_at"])
        messages.success(request, "Paso 5 guardado correctamente.")
        return redirect("maintenance_builder:wizard_step6", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step5.html",
        {
            "maintenance": maintenance,
            "dashboard_nav_active": "maintenance_builder",
            "sp_definitions": page_obj.object_list,
            "page_obj": page_obj,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "q_filter": q_filter,
            "schema_filter": schema_filter,
            "status_filter": status_filter,
            "script_filter": script_filter,
            "schema_choices": _sp_schema_filter_choices(upd_base_qs),
            "status_choices": SPDefinition.Status.choices,
            "selected_sp_id": selected_sp_id
            or (str(current_selection.sp_definition_id) if current_selection and current_selection.sp_definition_id else ""),
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def wizard_step6(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    dlt_base_qs = _dlt_queryset_for_user(request)
    filtered_qs, q_filter, schema_filter, status_filter, script_filter = _apply_readc_filters(request, dlt_base_qs)
    page_obj = _paginate(request, filtered_qs)
    selected_sp_id = request.POST.get("sp_definition_id", "").strip()
    clear_selection = request.POST.get("clear_selection", "").strip() == "1"
    current_selection = maintenance.sp_selections.filter(
        operation=MaintenanceSpSelection.OperationRole.DLT
    ).select_related("sp_definition").first()

    if request.method == "POST":
        selected_sp = None
        if selected_sp_id.isdigit():
            selected_sp = dlt_base_qs.filter(pk=int(selected_sp_id)).first()
            if not selected_sp:
                messages.error(request, "El SP DLT seleccionado no pertenece a su compañía.")
                return redirect("maintenance_builder:wizard_step6", pk=maintenance.pk)

        if clear_selection:
            selected_sp = None

        if selected_sp:
            MaintenanceSpSelection.objects.update_or_create(
                maintenance=maintenance,
                operation=MaintenanceSpSelection.OperationRole.DLT,
                defaults={
                    "sp_definition": selected_sp,
                    "is_required": False,
                    "selection_status": MaintenanceSpSelection.SelectionStatus.SELECTED,
                    "created_by": request.user if not current_selection else current_selection.created_by,
                    "updated_by": request.user,
                },
            )
        else:
            if current_selection:
                current_selection.sp_definition = None
                current_selection.is_required = False
                current_selection.selection_status = MaintenanceSpSelection.SelectionStatus.NOT_SELECTED
                current_selection.updated_by = request.user
                current_selection.save(
                    update_fields=[
                        "sp_definition",
                        "is_required",
                        "selection_status",
                        "updated_by",
                        "updated_at",
                    ]
                )
            else:
                MaintenanceSpSelection.objects.create(
                    maintenance=maintenance,
                    operation=MaintenanceSpSelection.OperationRole.DLT,
                    sp_definition=None,
                    is_required=False,
                    selection_status=MaintenanceSpSelection.SelectionStatus.NOT_SELECTED,
                    created_by=request.user,
                    updated_by=request.user,
                )

        maintenance.current_step = max(maintenance.current_step, 7)
        maintenance.updated_by = request.user
        maintenance.save(update_fields=["current_step", "updated_by", "updated_at"])
        messages.success(request, "Paso 6 guardado correctamente.")
        return redirect("maintenance_builder:wizard_step7", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step6.html",
        {
            "maintenance": maintenance,
            "dashboard_nav_active": "maintenance_builder",
            "sp_definitions": page_obj.object_list,
            "page_obj": page_obj,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "q_filter": q_filter,
            "schema_filter": schema_filter,
            "status_filter": status_filter,
            "script_filter": script_filter,
            "schema_choices": _sp_schema_filter_choices(dlt_base_qs),
            "status_choices": SPDefinition.Status.choices,
            "selected_sp_id": selected_sp_id
            or (str(current_selection.sp_definition_id) if current_selection and current_selection.sp_definition_id else ""),
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def wizard_step7(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    dspf_base_qs = _dspf_queryset_for_user(request)
    filtered_qs, q_filter, scope_filter, status_filter, version_filter = _apply_source_filters(
        request, dspf_base_qs
    )
    page_obj = _paginate(request, filtered_qs)
    selected_template_id = request.POST.get("source_template_id", "").strip()
    current_selection = maintenance.source_selections.filter(
        role_code=MaintenanceSourceSelection.RoleCode.BASE_DSPF
    ).select_related("source_template").first()

    if request.method == "POST":
        if not selected_template_id.isdigit():
            messages.error(request, "Debe seleccionar una plantilla DSPF.")
            return redirect("maintenance_builder:wizard_step7", pk=maintenance.pk)

        selected_template = dspf_base_qs.filter(pk=int(selected_template_id)).first()
        if not selected_template:
            messages.error(request, "La plantilla DSPF seleccionada no pertenece a su ámbito.")
            return redirect("maintenance_builder:wizard_step7", pk=maintenance.pk)

        MaintenanceSourceSelection.objects.update_or_create(
            maintenance=maintenance,
            role_code=MaintenanceSourceSelection.RoleCode.BASE_DSPF,
            defaults={
                "source_template": selected_template,
                "source_type_expected": SourceTemplate.SourceType.DSPF,
                "created_by": request.user if not current_selection else current_selection.created_by,
                "updated_by": request.user,
            },
        )
        maintenance.current_step = max(maintenance.current_step, 8)
        maintenance.updated_by = request.user
        maintenance.save(update_fields=["current_step", "updated_by", "updated_at"])
        messages.success(request, "Paso 7 guardado correctamente.")
        return redirect("maintenance_builder:wizard_step8", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step7.html",
        {
            "maintenance": maintenance,
            "dashboard_nav_active": "maintenance_builder",
            "source_templates": page_obj.object_list,
            "page_obj": page_obj,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "q_filter": q_filter,
            "scope_filter": scope_filter,
            "status_filter": status_filter,
            "version_filter": version_filter,
            "status_choices": SourceTemplate.Status.choices,
            "versions": _source_versions(dspf_base_qs),
            "selected_template_id": selected_template_id
            or (str(current_selection.source_template_id) if current_selection and current_selection.source_template_id else ""),
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def wizard_step8(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    sqlrpgle_base_qs = _sqlrpgle_queryset_for_user(request)
    filtered_qs, q_filter, scope_filter, status_filter, version_filter = _apply_source_filters(
        request, sqlrpgle_base_qs
    )
    page_obj = _paginate(request, filtered_qs)
    selected_template_id = request.POST.get("source_template_id", "").strip()
    current_selection = maintenance.source_selections.filter(
        role_code=MaintenanceSourceSelection.RoleCode.BASE_SQLRPGLE
    ).select_related("source_template").first()

    if request.method == "POST":
        if not selected_template_id.isdigit():
            messages.error(request, "Debe seleccionar una plantilla SQLRPGLE.")
            return redirect("maintenance_builder:wizard_step8", pk=maintenance.pk)

        selected_template = sqlrpgle_base_qs.filter(pk=int(selected_template_id)).first()
        if not selected_template:
            messages.error(request, "La plantilla SQLRPGLE seleccionada no pertenece a su ámbito.")
            return redirect("maintenance_builder:wizard_step8", pk=maintenance.pk)

        MaintenanceSourceSelection.objects.update_or_create(
            maintenance=maintenance,
            role_code=MaintenanceSourceSelection.RoleCode.BASE_SQLRPGLE,
            defaults={
                "source_template": selected_template,
                "source_type_expected": SourceTemplate.SourceType.SQLRPGLE,
                "created_by": request.user if not current_selection else current_selection.created_by,
                "updated_by": request.user,
            },
        )
        maintenance.current_step = max(maintenance.current_step, 9)
        maintenance.updated_by = request.user
        maintenance.save(update_fields=["current_step", "updated_by", "updated_at"])
        messages.success(request, "Paso 8 guardado correctamente.")
        return redirect("maintenance_builder:wizard_step9", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step8.html",
        {
            "maintenance": maintenance,
            "dashboard_nav_active": "maintenance_builder",
            "source_templates": page_obj.object_list,
            "page_obj": page_obj,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "current_per_page": _get_per_page(request),
            "pagination_qs": _pagination_qs(request),
            "q_filter": q_filter,
            "scope_filter": scope_filter,
            "status_filter": status_filter,
            "version_filter": version_filter,
            "status_choices": SourceTemplate.Status.choices,
            "versions": _source_versions(sqlrpgle_base_qs),
            "selected_template_id": selected_template_id
            or (str(current_selection.source_template_id) if current_selection and current_selection.source_template_id else ""),
        },
    )


@login_required
@_require_profile
@require_http_methods(["GET", "POST"])
def wizard_step9(request: HttpRequest, pk: int) -> HttpResponse:
    maintenance = get_object_or_404(_queryset_for_user(request), pk=pk)
    sp_map, source_map = _selection_map(maintenance)
    dspf_selection = source_map.get(MaintenanceSourceSelection.RoleCode.BASE_DSPF)
    sqlrpgle_selection = source_map.get(MaintenanceSourceSelection.RoleCode.BASE_SQLRPGLE)
    readc_selection = sp_map.get(MaintenanceSpSelection.OperationRole.READ_C)
    can_generate = bool(
        readc_selection
        and readc_selection.sp_definition_id
        and dspf_selection
        and dspf_selection.source_template_id
        and sqlrpgle_selection
        and sqlrpgle_selection.source_template_id
    )

    if request.method == "POST":
        if not can_generate:
            messages.error(request, "Faltan selecciones obligatorias para generar el script.")
            return redirect("maintenance_builder:wizard_step9", pk=maintenance.pk)
        try:
            with transaction.atomic():
                maintenance.dspf_template = dspf_selection.source_template
                maintenance.sqlrpgle_template = sqlrpgle_selection.source_template
                maintenance.is_generation_pending = False
                maintenance.last_generation_at = timezone.now()
                maintenance.status = MaintenanceDefinition.Status.GENERATED
                maintenance.last_generation_result = MaintenanceDefinition.GenerationResult.SUCCESS
                maintenance.last_error_message = ""
                maintenance.updated_by = request.user
                maintenance.save(
                    update_fields=[
                        "dspf_template",
                        "sqlrpgle_template",
                        "is_generation_pending",
                        "last_generation_at",
                        "status",
                        "last_generation_result",
                        "last_error_message",
                        "updated_by",
                        "updated_at",
                    ]
                )

                script_text = _generate_sqlrpgle_script(
                    maintenance=maintenance,
                    sp_map=sp_map,
                    source_map=source_map,
                    username=request.user.get_username() or "system",
                )
                script_hash = hashlib.sha256(script_text.encode("utf-8")).hexdigest()
                maintenance.script_versions.filter(is_current=True).update(is_current=False, updated_by=request.user)
                MaintenanceScriptVersion.objects.create(
                    maintenance=maintenance,
                    version=_next_script_version(maintenance),
                    script_sqlrpgle=script_text,
                    script_hash=script_hash,
                    generation_status=MaintenanceScriptVersion.GenerationStatus.SUCCESS,
                    is_current=True,
                    created_by=request.user,
                    updated_by=request.user,
                )
                MaintenanceProcessLog.objects.create(
                    maintenance=maintenance,
                    event_type=MaintenanceProcessLog.EventType.SAVE,
                    event_status=MaintenanceProcessLog.EventStatus.SUCCESS,
                    event_message="Resumen confirmado y persistido para generación.",
                    event_detail_json={"step": 9},
                    created_by=request.user,
                    updated_by=request.user,
                )
                MaintenanceProcessLog.objects.create(
                    maintenance=maintenance,
                    event_type=MaintenanceProcessLog.EventType.GENERATE,
                    event_status=MaintenanceProcessLog.EventStatus.SUCCESS,
                    event_message="Script SQLRPGLE generado correctamente.",
                    event_detail_json={"version": maintenance.script_versions.order_by("-version").first().version},
                    created_by=request.user,
                    updated_by=request.user,
                )
            messages.success(request, "El registro se guardó correctamente y el script fue generado.")
            return redirect("maintenance_builder:list_view")
        except Exception:
            maintenance.last_generation_at = timezone.now()
            maintenance.status = MaintenanceDefinition.Status.ERROR
            maintenance.last_generation_result = MaintenanceDefinition.GenerationResult.ERROR
            maintenance.last_error_message = "Se produjo un error en el proceso."
            maintenance.updated_by = request.user
            maintenance.save(
                update_fields=[
                    "last_generation_at",
                    "status",
                    "last_generation_result",
                    "last_error_message",
                    "updated_by",
                    "updated_at",
                ]
            )
            MaintenanceProcessLog.objects.create(
                maintenance=maintenance,
                event_type=MaintenanceProcessLog.EventType.ERROR,
                event_status=MaintenanceProcessLog.EventStatus.ERROR,
                event_message="Se produjo un error en el proceso.",
                event_detail_json={"step": 9},
                created_by=request.user,
                updated_by=request.user,
            )
            messages.error(request, "Se produjo un error en el proceso.")
            return redirect("maintenance_builder:wizard_step9", pk=maintenance.pk)

    return render(
        request,
        "maintenance_builder/wizard_step9.html",
        {
            "maintenance": maintenance,
            "dashboard_nav_active": "maintenance_builder",
            "can_generate": can_generate,
            "readc_selection": readc_selection,
            "add_selection": sp_map.get(MaintenanceSpSelection.OperationRole.ADD),
            "readr_selection": sp_map.get(MaintenanceSpSelection.OperationRole.READ_R),
            "upd_selection": sp_map.get(MaintenanceSpSelection.OperationRole.UPD),
            "dlt_selection": sp_map.get(MaintenanceSpSelection.OperationRole.DLT),
            "dspf_selection": dspf_selection,
            "sqlrpgle_selection": sqlrpgle_selection,
        },
    )
