from __future__ import annotations

from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.sources.forms import SourceTemplateForm
from apps.sources.models import SourceTemplate
from apps.sources.services.access import (
    MSG_UNAUTHORIZED_SOURCES,
    has_sources_company_scope,
    source_queryset_for_user,
    user_can_access_source,
)
from apps.userprofile.models import UserProfile

ALLOWED_PER_PAGE = (5, 10, 15, 20, 25)
DEFAULT_PER_PAGE = 10

ORDERING_MAP = {
    "name": "name",
    "-name": "-name",
    "type": "source_type",
    "-type": "-source_type",
    "status": "status",
    "-status": "-status",
    "version": "version",
    "-version": "-version",
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


def _require_sources_scope(view_func):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not has_sources_company_scope(request.user.profile):
            messages.warning(request, MSG_UNAUTHORIZED_SOURCES)
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def _next_ordering(current: str, column: str) -> str:
    asc, desc = column, f"-{column}"
    if current in (asc, desc):
        return desc if current == asc else asc
    return asc


def _build_sort_url(request: HttpRequest, column: str) -> str:
    current_ord = (request.GET.get("ordering") or "").strip() or "name"
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
        "name": _ordering_column_state(ordering, "name"),
        "type": _ordering_column_state(ordering, "type"),
        "status": _ordering_column_state(ordering, "status"),
        "version": _ordering_column_state(ordering, "version"),
    }


def _filtered_queryset(request: HttpRequest):
    qs = source_queryset_for_user(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(filename__icontains=q))
    st = request.GET.get("source_type", "").strip()
    if st in dict(SourceTemplate.SourceType.choices):
        qs = qs.filter(source_type=st)
    status = request.GET.get("status", "").strip()
    if status in dict(SourceTemplate.Status.choices):
        qs = qs.filter(status=status)
    ordering = (request.GET.get("ordering") or "").strip() or "name"
    if ordering not in ORDERING_MAP:
        ordering = "name"
    qs = qs.order_by(ORDERING_MAP[ordering])
    return qs, ordering


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


@login_required
@_require_profile
@_require_sources_scope
def source_list(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    qs, ordering = _filtered_queryset(request)
    page_obj = _paginate(request, qs)
    return render(
        request,
        "sources/source_list.html",
        {
            "profile": profile,
            "sources": page_obj.object_list,
            "page_obj": page_obj,
            "ordering": ordering,
            "current_per_page": _get_per_page(request),
            "source_type_choices": SourceTemplate.SourceType.choices,
            "status_choices": SourceTemplate.Status.choices,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "pagination_qs": _pagination_qs(request),
            "sort_url_name": _build_sort_url(request, "name"),
            "sort_url_type": _build_sort_url(request, "type"),
            "sort_url_status": _build_sort_url(request, "status"),
            "sort_url_version": _build_sort_url(request, "version"),
            "sort_cols": _ordering_states(ordering),
            "dashboard_nav_active": "sources",
        },
    )


@login_required
@_require_profile
@_require_sources_scope
def source_detail(request: HttpRequest, pk: int) -> HttpResponse:
    profile = request.user.profile
    source = get_object_or_404(SourceTemplate, pk=pk)
    if not user_can_access_source(request.user, source):
        raise Http404()
    return render(
        request,
        "sources/source_detail.html",
        {
            "profile": profile,
            "source": source,
            "dashboard_nav_active": "sources",
        },
    )


@login_required
@_require_profile
@_require_sources_scope
@require_http_methods(["GET", "POST"])
def source_create(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    if request.method == "POST":
        form = SourceTemplateForm(request.POST, company_id=profile.company_id)
        if form.is_valid():
            source = form.save(commit=False)
            source.company_id = profile.company_id
            source.created_by = request.user
            source.updated_by = request.user
            try:
                source.save()
            except IntegrityError:
                form.add_error(
                    None,
                    "Ya existe una plantilla con este nombre y versión para su compañía. "
                    "Cambie el nombre o incremente la versión.",
                )
            else:
                messages.success(request, "Plantilla creada correctamente.")
                return redirect("sources:detail", pk=source.pk)
    else:
        form = SourceTemplateForm(company_id=profile.company_id)
    return render(
        request,
        "sources/source_form.html",
        {
            "profile": profile,
            "form": form,
            "is_edit": False,
            "dashboard_nav_active": "sources",
        },
    )


@login_required
@_require_profile
@_require_sources_scope
@require_http_methods(["GET", "POST"])
def source_update(request: HttpRequest, pk: int) -> HttpResponse:
    profile = request.user.profile
    source = get_object_or_404(SourceTemplate, pk=pk)
    if not user_can_access_source(request.user, source):
        raise Http404()
    if request.method == "POST":
        form = SourceTemplateForm(
            request.POST, instance=source, company_id=profile.company_id
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company_id = profile.company_id
            obj.updated_by = request.user
            try:
                obj.save()
            except IntegrityError:
                form.add_error(
                    None,
                    "Ya existe una plantilla con este nombre y versión para su compañía. "
                    "Cambie el nombre o incremente la versión.",
                )
            else:
                messages.success(request, "Plantilla actualizada correctamente.")
                return redirect("sources:detail", pk=obj.pk)
    else:
        form = SourceTemplateForm(instance=source, company_id=profile.company_id)
    return render(
        request,
        "sources/source_form.html",
        {
            "profile": profile,
            "form": form,
            "source": source,
            "is_edit": True,
            "dashboard_nav_active": "sources",
        },
    )


@login_required
@_require_profile
@_require_sources_scope
@require_http_methods(["GET", "POST"])
def source_delete(request: HttpRequest, pk: int) -> HttpResponse:
    profile = request.user.profile
    source = get_object_or_404(SourceTemplate, pk=pk)
    if not user_can_access_source(request.user, source):
        raise Http404()
    if request.method == "POST":
        source.delete()
        messages.success(request, "Plantilla eliminada correctamente.")
        return redirect("sources:list")
    return render(
        request,
        "sources/source_confirm_delete.html",
        {
            "profile": profile,
            "source": source,
            "dashboard_nav_active": "sources",
        },
    )
