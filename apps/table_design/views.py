from __future__ import annotations

from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.table_design.forms import (
    DetailTableForm,
    HeaderTableCreateForm,
    HeaderTableUpdateForm,
)
from apps.table_design.models import (
    DetailTable,
    DetailTableDb2Attributes,
    HeaderTable,
)
from apps.table_design.services.access import (
    MSG_TABLE_DESIGN_NO_COMPANY,
    MSG_UNAUTHORIZED_TABLE_DESIGN,
    header_table_queryset_for_user,
)
from apps.core.services.operation_messages import MSG_FORM_INVALID
from apps.table_design.services.field_persistence import (
    create_detail_field,
    delete_detail_field,
    update_detail_field,
)
from apps.table_design.services.header_persistence import (
    create_header_table,
    update_header_table,
)
from apps.table_design.services.operation_ui import apply_operation_field_errors
from apps.table_design.forms_db2_attributes import (
    DetailTableDb2AttributesForm,
    build_db2_attributes_form_context,
)
from apps.table_design.services.field_db2_attributes import (
    persist_field_db2_attributes_from_form,
)
from apps.table_design.services.field_order import (
    get_next_order_reg,
    move_field_down,
    move_field_up,
)
from apps.table_design.services.field_validation import (
    ALLOCATE_REQUIRED_TYPES,
    CCSID_FIELD_TYPES,
    FIXED_LENGTH_BY_TYPE,
    IDENTITY_FIELD_TYPES,
    LENGTH_REQUIRED_TYPES,
    MAX_COLUMN_LABEL_LEN,
    MAX_COLUMN_TEXT_LEN,
    NO_LENGTH_TYPES,
    MAX_FIELD_NAME_LONG_LEN,
    MAX_FIELD_NAME_SHORT_LEN,
    MIN_FIELD_NAME_LONG_LEN,
    MIN_FIELD_NAME_SHORT_LEN,
)
from apps.table_design.services.sql_script import build_simple_sql_script
from apps.table_design.services.validation import (
    MAX_SCHEMA_LEN,
    MAX_TABLE_NAME_LONG_LEN,
    MAX_TABLE_NAME_SHORT_LEN,
    MIN_TABLE_NAME_LONG_LEN,
    MIN_TABLE_NAME_SHORT_LEN,
)
from apps.userprofile.models import UserProfile

ALLOWED_PER_PAGE = (10, 15, 25, 50)
DEFAULT_PER_PAGE = 15
SCRIPT_QUALIFICATION_STYLE_CHOICES = ("mixed", "dot", "slash")

ORDERING_MAP = {
    "table_name_short": "table_name_short",
    "-table_name_short": "-table_name_short",
    "table_type": "table_type",
    "-table_type": "-table_type",
    "status": "status",
    "-status": "-status",
    "updated_at": "updated_at",
    "-updated_at": "-updated_at",
}


def _header_identity_rules_context() -> dict[str, int]:
    """Rangos de nombre de cabecera (alineados con services/validation.py)."""
    return {
        "long_min": MIN_TABLE_NAME_LONG_LEN,
        "long_max": MAX_TABLE_NAME_LONG_LEN,
        "short_min": MIN_TABLE_NAME_SHORT_LEN,
        "short_max": MAX_TABLE_NAME_SHORT_LEN,
        "schema_max": MAX_SCHEMA_LEN,
    }


def _detail_field_rules_context() -> dict[str, int]:
    """Rangos de nombres de campo (services/field_validation.py)."""
    return {
        "min_short": MIN_FIELD_NAME_SHORT_LEN,
        "max_short": MAX_FIELD_NAME_SHORT_LEN,
        "min_long": MIN_FIELD_NAME_LONG_LEN,
        "max_long": MAX_FIELD_NAME_LONG_LEN,
        "column_label_max": MAX_COLUMN_LABEL_LEN,
        "column_text_max": MAX_COLUMN_TEXT_LEN,
    }


def _detail_field_form_js_config() -> dict[str, object]:
    """Config para static/js/table_design/detail_field_form.js (tipos DB2)."""
    T = DetailTable.FieldDB2Type
    return {
        "DECIMAL": T.DECIMAL,
        "NUMERIC": T.NUMERIC,
        "fixedLengths": dict(FIXED_LENGTH_BY_TYPE),
        "lengthRequired": sorted(LENGTH_REQUIRED_TYPES),
        "noLengthTypes": sorted(NO_LENGTH_TYPES),
        "allocateForTypes": sorted(ALLOCATE_REQUIRED_TYPES),
        "ccsidForTypes": sorted(CCSID_FIELD_TYPES),
        "identityForTypes": sorted(IDENTITY_FIELD_TYPES),
    }


def _require_profile(view_func):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        try:
            request.user.profile
        except UserProfile.DoesNotExist:
            messages.error(
                request,
                "Su cuenta no tiene perfil configurado. Contacte al administrador de sistemas.",
            )
            return redirect("security:security_login")
        return view_func(request, *args, **kwargs)

    return wrapper


def _require_table_design_list_access(view_func):
    """AS o US con compañía; si no, mensaje de error y vuelta al panel (modal en base)."""

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        profile = request.user.profile
        if profile.user_type not in (
            UserProfile.UserType.ADMIN_SYSTEM,
            UserProfile.UserType.USER,
        ):
            messages.error(request, MSG_UNAUTHORIZED_TABLE_DESIGN)
            return redirect("dashboard:home")
        if not profile.company_id:
            messages.error(request, MSG_TABLE_DESIGN_NO_COMPANY)
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def _next_ordering(current: str, column: str) -> str:
    asc, desc = column, f"-{column}"
    if current in (asc, desc):
        return desc if current == asc else asc
    return asc


def _build_sort_url(request: HttpRequest, column: str) -> str:
    current_ord = (request.GET.get("ordering") or "").strip() or "table_name_short"
    next_ord = _next_ordering(current_ord, column)
    params: list[tuple[str, str]] = []
    for key in request.GET:
        if key in ("page", "ordering"):
            continue
        for val in request.GET.getlist(key):
            params.append((key, val))
    params.append(("ordering", next_ord))
    params.append(("page", "1"))
    return "?" + urlencode(params)


def _ordering_column_state(ordering: str, col: str) -> dict[str, object]:
    asc, desc = col, f"-{col}"
    if ordering == asc:
        return {"glyph": "▲", "active": True}
    if ordering == desc:
        return {"glyph": "▼", "active": True}
    return {"glyph": "⇅", "active": False}


def _ordering_states(ordering: str) -> dict[str, dict[str, object]]:
    return {
        "table_name_short": _ordering_column_state(ordering, "table_name_short"),
        "table_type": _ordering_column_state(ordering, "table_type"),
        "status": _ordering_column_state(ordering, "status"),
        "updated_at": _ordering_column_state(ordering, "updated_at"),
    }


def _filtered_header_queryset(request: HttpRequest):
    qs = header_table_queryset_for_user(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(table_name_short__icontains=q)
            | Q(table_name_long__icontains=q)
            | Q(schema__icontains=q)
        )

    tm = request.GET.get("table_model", "").strip()
    if tm in dict(HeaderTable.TableModel.choices):
        qs = qs.filter(table_model=tm)

    tt = request.GET.get("table_type", "").strip()
    if tt in dict(HeaderTable.TableKind.choices):
        qs = qs.filter(table_type=tt)

    st = request.GET.get("status", "").strip()
    if st in dict(HeaderTable.Status.choices):
        qs = qs.filter(status=st)

    sg = request.GET.get("script_generated", "").strip()
    if sg == "1":
        qs = qs.filter(script_generated=True)
    elif sg == "0":
        qs = qs.filter(script_generated=False)

    hk = request.GET.get("is_field_key", "").strip()
    if hk == "1":
        qs = qs.filter(is_field_key=True)
    elif hk == "0":
        qs = qs.filter(is_field_key=False)

    ordering = (request.GET.get("ordering") or "").strip() or "table_name_short"
    if ordering not in ORDERING_MAP:
        ordering = "table_name_short"
    qs = qs.order_by(ORDERING_MAP[ordering])
    return qs, ordering


def _list_stats(qs):
    return {
        "total": qs.count(),
        "active": qs.filter(status=HeaderTable.Status.ACTIVE).count(),
        "process": qs.filter(status=HeaderTable.Status.PROCESS).count(),
        "no_script": qs.filter(script_generated=False).count(),
    }


def _pagination_qs(request: HttpRequest) -> str:
    q = request.GET.copy()
    q.pop("page", None)
    return q.urlencode()


def _get_per_page(request: HttpRequest) -> int:
    try:
        per_page = int(request.GET.get("per_page", DEFAULT_PER_PAGE))
    except ValueError:
        per_page = DEFAULT_PER_PAGE
    if per_page not in ALLOWED_PER_PAGE:
        per_page = DEFAULT_PER_PAGE
    return per_page


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


def _script_bool_from_payload(payload: dict, key: str, default: bool = False) -> bool:
    raw = str(payload.get(key, "")).strip().lower()
    if raw in {"1", "true", "on", "yes"}:
        return True
    if raw in {"0", "false", "off", "no"}:
        return False
    return default


def _script_format_options_from_request(request: HttpRequest) -> tuple[dict[str, object], list[str]]:
    """
    Lee opciones de formato de script desde GET/POST y valida valores permitidos.
    """
    source = request.POST if request.method == "POST" else request.GET
    warnings: list[str] = []

    style_raw = str(source.get("qualification_style", "mixed")).strip().lower()
    if style_raw not in SCRIPT_QUALIFICATION_STYLE_CHOICES:
        warnings.append(
            "qualification_style inválido; se usa «mixed». Valores permitidos: mixed, dot, slash."
        )
        style_raw = "mixed"

    emit_schema = _script_bool_from_payload(source, "emit_set_current_schema", False)
    emit_default_null = _script_bool_from_payload(
        source, "emit_default_null_for_nullable", False
    )

    return (
        {
            "qualification_style": style_raw,
            "emit_set_current_schema": emit_schema,
            "emit_default_null_for_nullable": emit_default_null,
        },
        warnings,
    )


def _script_format_querystring(opts: dict[str, object]) -> str:
    return urlencode(
        {
            "qualification_style": str(opts["qualification_style"]),
            "emit_set_current_schema": "1" if bool(opts["emit_set_current_schema"]) else "0",
            "emit_default_null_for_nullable": "1"
            if bool(opts["emit_default_null_for_nullable"])
            else "0",
        }
    )


def _redirect_header_script_with_options(header_pk: int, opts: dict[str, object]) -> HttpResponse:
    base_url = redirect("table_design:header_script", header_pk=header_pk).url
    return redirect(f"{base_url}?{_script_format_querystring(opts)}")


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET"])
def header_table_list(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    qs, ordering = _filtered_header_queryset(request)
    stats = _list_stats(qs)
    page_obj = _paginate(request, qs)
    return render(
        request,
        "table_design/header_table_list.html",
        {
            "profile": profile,
            "headers": page_obj.object_list,
            "page_obj": page_obj,
            "ordering": ordering,
            "stats": stats,
            "current_per_page": _get_per_page(request),
            "table_model_choices": HeaderTable.TableModel.choices,
            "table_type_choices": HeaderTable.TableKind.choices,
            "status_choices": HeaderTable.Status.choices,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "pagination_qs": _pagination_qs(request),
            "sort_url_table_name_short": _build_sort_url(request, "table_name_short"),
            "sort_url_table_type": _build_sort_url(request, "table_type"),
            "sort_url_status": _build_sort_url(request, "status"),
            "sort_url_updated_at": _build_sort_url(request, "updated_at"),
            "sort_cols": _ordering_states(ordering),
            "dashboard_nav_active": "table_design",
        },
    )


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET"])
def header_table_detail(request: HttpRequest, pk: int) -> HttpResponse:
    profile = request.user.profile
    qs = header_table_queryset_for_user(request.user).select_related("auto_key_config")
    header = get_object_or_404(qs, pk=pk)
    return render(
        request,
        "table_design/header_table_detail.html",
        {
            "profile": profile,
            "header": header,
            "dashboard_nav_active": "table_design",
            "header_rules": _header_identity_rules_context(),
        },
    )


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET", "POST"])
def header_script(request: HttpRequest, header_pk: int) -> HttpResponse:
    """Vista previa / descarga de DDL SIMPLE y confirmación de emisión (§9 CODAS)."""
    profile = request.user.profile
    qs = header_table_queryset_for_user(request.user)
    header = get_object_or_404(qs, pk=header_pk)
    header.refresh_from_db()
    script_opts, format_warnings = _script_format_options_from_request(request)
    ok, sql, errors = build_simple_sql_script(
        header,
        emit_set_current_schema=bool(script_opts["emit_set_current_schema"]),
        qualification_style=str(script_opts["qualification_style"]),
        emit_default_null_for_nullable=bool(
            script_opts["emit_default_null_for_nullable"]
        ),
    )
    if format_warnings:
        for w in format_warnings:
            messages.warning(request, w)

    if (request.GET.get("download") or "").strip() == "1":
        if not ok:
            for msg in errors:
                messages.error(request, msg)
            return _redirect_header_script_with_options(header.pk, script_opts)
        filename = f"{header.table_name_short.strip()}_ddl.sql"
        resp = HttpResponse(sql, content_type="text/plain; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    if request.method == "POST":
        if header.status == HeaderTable.Status.INACTIVE:
            messages.error(
                request,
                "No puede confirmar la emisión del script: la cabecera está en estado Inactivo.",
            )
            return _redirect_header_script_with_options(header.pk, script_opts)
        if header.script_generated:
            messages.info(
                request,
                "El script para esta tabla ya fue confirmado anteriormente.",
            )
            return _redirect_header_script_with_options(header.pk, script_opts)
        if not ok:
            for msg in errors:
                messages.error(request, msg)
            return _redirect_header_script_with_options(header.pk, script_opts)
        header.script_generated = True
        header.script_date = timezone.now().date()
        header.updated_by = request.user
        header.status = HeaderTable.Status.ACTIVE
        header.save(
            update_fields=["script_generated", "script_date", "updated_by", "updated_at", "status"]
        )
        messages.success(
            request,
            "Emisión del script DDL registrada. La cabecera y los campos quedan bloqueados "
            "para edición estructural.",
        )
        return _redirect_header_script_with_options(header.pk, script_opts)

    can_confirm = (
        ok
        and not header.script_generated
        and header.status != HeaderTable.Status.INACTIVE
    )
    return render(
        request,
        "table_design/header_script.html",
        {
            "profile": profile,
            "header": header,
            "sql_ok": ok,
            "sql_text": sql,
            "sql_errors": errors,
            "script_format_options": script_opts,
            "script_format_querystring": _script_format_querystring(script_opts),
            "script_qualification_styles": SCRIPT_QUALIFICATION_STYLE_CHOICES,
            "can_confirm": can_confirm,
            "dashboard_nav_active": "table_design",
        },
    )


def _header_update_allowed(header: HeaderTable) -> bool:
    """True si la cabecera admite edición (inactiva no)."""
    return header.status != HeaderTable.Status.INACTIVE


def _respond_header_edit_blocked(
    request: HttpRequest, header: HeaderTable
) -> HttpResponse:
    """Cabecera inactiva: mensaje y vuelta al listado (§ 8 CODAS_TABLE_DESIGN)."""
    messages.error(
        request,
        "No puede editar esta cabecera: está en estado Inactivo. "
        "La reactivación no está disponible en esta pantalla.",
    )
    return redirect("table_design:header_list")


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET", "POST"])
def header_table_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Edición de cabecera: mismos campos que en alta, con validación DDL y unicidad de PK."""
    profile = request.user.profile
    qs = header_table_queryset_for_user(request.user)
    header = get_object_or_404(
        qs.select_related(
            "auto_key_config",
            "auto_key_config__created_by",
            "auto_key_config__updated_by",
        ),
        pk=pk,
    )

    if not _header_update_allowed(header):
        return _respond_header_edit_blocked(request, header)

    if request.method == "POST":
        header = get_object_or_404(
            qs.select_related(
                "auto_key_config",
                "auto_key_config__created_by",
                "auto_key_config__updated_by",
            ),
            pk=pk,
        )
        if not _header_update_allowed(header):
            return _respond_header_edit_blocked(request, header)
        had_script_generated = header.script_generated
        form = HeaderTableUpdateForm(
            request.POST,
            instance=header,
            company_id=profile.company_id,
            can_edit_identity=True,
        )
        if form.is_valid():
            updated = form.save(commit=False)
            result = update_header_table(
                updated,
                cleaned_data=form.cleaned_data,
                user=request.user,
                had_script_generated=had_script_generated,
            )
            if result.ok:
                messages.success(request, result.error_message)
                return redirect("table_design:header_list")
            messages.error(request, result.error_message)
            apply_operation_field_errors(form, result)
        else:
            messages.error(request, MSG_FORM_INVALID)
    else:
        form = HeaderTableUpdateForm(
            instance=header,
            company_id=profile.company_id,
            can_edit_identity=True,
        )

    return render(
        request,
        "table_design/header_table_form.html",
        {
            "profile": profile,
            "form": form,
            "header": header,
            "form_mode": "edit",
            "can_edit_identity": True,
            "dashboard_nav_active": "table_design",
            "header_rules": _header_identity_rules_context(),
        },
    )


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET", "POST"])
def header_table_create(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    if request.method == "POST":
        form = HeaderTableCreateForm(request.POST, company_id=profile.company_id)
        if form.is_valid():
            header = form.save(commit=False)
            header.company_id = profile.company_id
            header.created_by = request.user
            header.updated_by = request.user
            result = create_header_table(
                header,
                cleaned_data=form.cleaned_data,
                user=request.user,
            )
            if result.ok:
                messages.success(request, result.error_message)
                return redirect("table_design:header_list")
            messages.error(request, result.error_message)
            apply_operation_field_errors(form, result)
        else:
            messages.error(request, MSG_FORM_INVALID)
    else:
        form = HeaderTableCreateForm(
            company_id=profile.company_id,
            initial={
                "table_model": HeaderTable.TableModel.SIMPLE,
                "table_type": HeaderTable.TableKind.PHYSICAL,
            },
        )
    return render(
        request,
        "table_design/header_table_form.html",
        {
            "profile": profile,
            "form": form,
            "form_mode": "create",
            "can_edit_identity": True,
            "dashboard_nav_active": "table_design",
            "header_rules": _header_identity_rules_context(),
        },
    )


def _header_fields_mutations_blocked(header: HeaderTable) -> bool:
    return bool(header.script_generated) or (
        header.status == HeaderTable.Status.INACTIVE
    )


def _respond_field_mutations_blocked(
    request: HttpRequest, header: HeaderTable
) -> HttpResponse:
    """No se permiten altas/bajas/cambios de campos (§ 9 CODAS_TABLE_DESIGN)."""
    script = header.script_generated
    inactive = header.status == HeaderTable.Status.INACTIVE
    if script and inactive:
        messages.warning(
            request,
            "No puede modificar campos: el script ya fue generado y la cabecera está "
            "en estado Inactivo.",
        )
    elif script:
        messages.error(
            request,
            "No puede modificar campos: el script para esta tabla ya fue generado.",
        )
    else:
        messages.error(
            request,
            "No puede modificar campos: la cabecera está en estado Inactivo.",
        )
    return redirect("table_design:field_list", header_pk=header.pk)


def _field_list_context(
    request: HttpRequest,
    header: HeaderTable,
) -> dict[str, object]:
    profile = request.user.profile
    mutations_blocked = _header_fields_mutations_blocked(header)
    fields = header.fields.select_related("db2_attributes").order_by(
        "order_reg", "pk"
    )
    return {
        "profile": profile,
        "header": header,
        "fields": fields,
        "mutations_blocked": mutations_blocked,
        "dashboard_nav_active": "table_design",
    }


def _field_form_context(
    request: HttpRequest,
    header: HeaderTable,
    *,
    form: DetailTableForm,
    field: DetailTable | None,
    step_title: str,
) -> dict[str, object]:
    ctx = _field_list_context(request, header)
    ctx.update(
        {
            "form": form,
            "field": field,
            "step_title": step_title,
            "field_rules": _detail_field_rules_context(),
            "detail_field_js_config": _detail_field_form_js_config(),
        }
    )
    return ctx


def _get_field_db2_attrs(field: DetailTable):
    try:
        return field.db2_attributes
    except DetailTableDb2Attributes.DoesNotExist:
        return None


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET"])
def field_list(request: HttpRequest, header_pk: int) -> HttpResponse:
    header = get_object_or_404(
        header_table_queryset_for_user(request.user), pk=header_pk
    )
    return render(
        request,
        "table_design/field_list.html",
        _field_list_context(request, header),
    )


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET", "POST"])
def field_create(request: HttpRequest, header_pk: int) -> HttpResponse:
    header = get_object_or_404(
        header_table_queryset_for_user(request.user), pk=header_pk
    )
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)

    if request.method == "GET":
        form = DetailTableForm(header=header, exclude_field_id=None)
        return render(
            request,
            "table_design/field_form.html",
            _field_form_context(
                request,
                header,
                form=form,
                field=None,
                step_title="Nuevo campo",
            ),
        )

    form = DetailTableForm(request.POST, header=header, exclude_field_id=None)
    if form.is_valid():
        header.refresh_from_db()
        if _header_fields_mutations_blocked(header):
            return _respond_field_mutations_blocked(request, header)
        obj = form.save(commit=False)
        obj.header = header
        obj.order_reg = get_next_order_reg(header)
        obj.status = DetailTable.Status.ACTIVE
        obj.created_by = request.user
        obj.updated_by = request.user
        result = create_detail_field(obj, header=header)
        if result.ok:
            messages.success(request, result.error_message)
            return redirect("table_design:field_list", header_pk=header.pk)
        messages.error(request, result.error_message)
        apply_operation_field_errors(form, result)
    else:
        messages.error(request, MSG_FORM_INVALID)

    return render(
        request,
        "table_design/field_form.html",
        _field_form_context(
            request,
            header,
            form=form,
            field=None,
            step_title="Nuevo campo",
        ),
    )


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET", "POST"])
def field_update(request: HttpRequest, header_pk: int, field_pk: int) -> HttpResponse:
    header = get_object_or_404(
        header_table_queryset_for_user(request.user), pk=header_pk
    )
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)

    field = get_object_or_404(header.fields, pk=field_pk)
    if request.method == "GET":
        form = DetailTableForm(
            instance=field,
            header=header,
            exclude_field_id=field.pk,
        )
        return render(
            request,
            "table_design/field_form.html",
            _field_form_context(
                request,
                header,
                form=form,
                field=field,
                step_title="Editar campo",
            ),
        )

    form = DetailTableForm(
        request.POST,
        instance=field,
        header=header,
        exclude_field_id=field.pk,
    )
    if form.is_valid():
        header.refresh_from_db()
        if _header_fields_mutations_blocked(header):
            return _respond_field_mutations_blocked(request, header)
        updated = form.save(commit=False)
        updated.updated_by = request.user
        result = update_detail_field(updated, header=header)
        if result.ok:
            messages.success(request, result.error_message)
            return redirect("table_design:field_list", header_pk=header.pk)
        messages.error(request, result.error_message)
        apply_operation_field_errors(form, result)
    else:
        messages.error(request, MSG_FORM_INVALID)

    return render(
        request,
        "table_design/field_form.html",
        _field_form_context(
            request,
            header,
            form=form,
            field=field,
            step_title="Editar campo",
        ),
    )


@login_required
@_require_profile
@_require_table_design_list_access
@require_http_methods(["GET", "POST"])
def field_db2_attributes(
    request: HttpRequest, header_pk: int, field_pk: int
) -> HttpResponse:
    header = get_object_or_404(
        header_table_queryset_for_user(request.user), pk=header_pk
    )
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)

    field = get_object_or_404(header.fields, pk=field_pk)
    attrs = _get_field_db2_attrs(field)

    if request.method == "GET":
        form = DetailTableDb2AttributesForm(
            detail=field,
            attrs_instance=attrs,
        )
        ctx = _field_list_context(request, header)
        ctx.update(
            {
                "field": field,
                "step_title": "Atributos DB2",
                **build_db2_attributes_form_context(form),
            }
        )
        return render(request, "table_design/field_db2_attributes.html", ctx)

    form = DetailTableDb2AttributesForm(
        request.POST,
        detail=field,
        attrs_instance=attrs,
    )
    if form.is_valid():
        header.refresh_from_db()
        if _header_fields_mutations_blocked(header):
            return _respond_field_mutations_blocked(request, header)
        selected = form.selected_field_keys()
        try:
            with transaction.atomic():
                persist_field_db2_attributes_from_form(
                    field,
                    cleaned_data=form.cleaned_data,
                    selected=selected,
                    user=request.user,
                    user_defined_only=form.user_defined_only(),
                )
        except ValidationError as exc:
            if hasattr(exc, "error_dict"):
                for fname, errs in exc.error_dict.items():
                    for err in errs:
                        form.add_error(
                            fname if fname in form.fields else None, err
                        )
            else:
                form.add_error(None, exc.messages)
        else:
            messages.success(request, "Atributos DB2 guardados correctamente.")
            return redirect("table_design:field_list", header_pk=header.pk)

    ctx = _field_list_context(request, header)
    ctx.update(
        {
            "field": field,
            "step_title": "Atributos DB2",
            **build_db2_attributes_form_context(form),
        }
    )
    return render(request, "table_design/field_db2_attributes.html", ctx)


@login_required
@_require_profile
@_require_table_design_list_access
@require_POST
def field_delete(request: HttpRequest, header_pk: int, field_pk: int) -> HttpResponse:
    header = get_object_or_404(
        header_table_queryset_for_user(request.user), pk=header_pk
    )
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)

    field = get_object_or_404(header.fields, pk=field_pk)
    header.refresh_from_db()
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)
    result = delete_detail_field(field, header=header)
    if result.ok:
        messages.success(request, result.error_message)
    else:
        messages.error(request, result.error_message)
    return redirect("table_design:field_list", header_pk=header.pk)


@login_required
@_require_profile
@_require_table_design_list_access
@require_POST
def field_move_up(request: HttpRequest, header_pk: int, field_pk: int) -> HttpResponse:
    header = get_object_or_404(
        header_table_queryset_for_user(request.user), pk=header_pk
    )
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)

    field = get_object_or_404(header.fields, pk=field_pk)
    header.refresh_from_db()
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)
    if move_field_up(header, field):
        messages.success(request, "Orden del campo actualizado.")
    else:
        messages.info(request, "El campo ya está en la primera posición.")
    return redirect("table_design:field_list", header_pk=header.pk)


@login_required
@_require_profile
@_require_table_design_list_access
@require_POST
def field_move_down(request: HttpRequest, header_pk: int, field_pk: int) -> HttpResponse:
    header = get_object_or_404(
        header_table_queryset_for_user(request.user), pk=header_pk
    )
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)

    field = get_object_or_404(header.fields, pk=field_pk)
    header.refresh_from_db()
    if _header_fields_mutations_blocked(header):
        return _respond_field_mutations_blocked(request, header)
    if move_field_down(header, field):
        messages.success(request, "Orden del campo actualizado.")
    else:
        messages.info(request, "El campo ya está en la última posición.")
    return redirect("table_design:field_list", header_pk=header.pk)
