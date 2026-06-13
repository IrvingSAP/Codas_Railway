from __future__ import annotations

from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.services.operation_messages import MSG_FORM_INVALID
from apps.userprofile.forms import UserProfileCreateForm, UserProfileMaintainerForm
from apps.userprofile.models import UserProfile
from apps.userprofile.services.access import (
    MSG_UNAUTHORIZED_USERPROFILE,
    company_readonly_for_connection,
    is_superuser_connection,
    is_userprofile_maintainer,
    resolve_new_profile_user_type,
    resolve_company_for_save,
    user_can_access_target_profile,
    userprofile_queryset_for_user,
)
from apps.userprofile.services.operation_ui import apply_operation_field_errors
from apps.userprofile.services.userprofile_persistence import (
    create_user_profile,
    delete_user_profile,
    update_user_profile,
)

ALLOWED_PER_PAGE = (5, 10, 15, 20, 25)
DEFAULT_PER_PAGE = 10

ORDERING_MAP = {
    "username": "user__username",
    "-username": "-user__username",
    "tipo": "user_type",
    "-tipo": "-user_type",
    "estado": "status",
    "-estado": "-status",
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


def require_userprofile_maintainer(view_func):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        profile = request.user.profile
        if not is_userprofile_maintainer(profile):
            messages.warning(request, MSG_UNAUTHORIZED_USERPROFILE)
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def _next_ordering(current: str, column: str) -> str:
    asc, desc = column, f"-{column}"
    if current in (asc, desc):
        return desc if current == asc else asc
    return asc


def _build_sort_url(request: HttpRequest, column: str) -> str:
    """Preserva filtros GET y fija ordering + page=1 (evita rarezas con QueryDict)."""
    current_ord = (request.GET.get("ordering") or "").strip() or "username"
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
    """
    Estado visual por columna ordenable.
    Activa: ▲ o ▼ (azul en plantilla). Inactiva: ⇅ en gris para indicar que también ordena.
    """
    asc, desc = col, f"-{col}"
    if ordering == asc:
        return {"glyph": "▲", "active": True}
    if ordering == desc:
        return {"glyph": "▼", "active": True}
    return {"glyph": "⇅", "active": False}


def _ordering_states(ordering: str) -> dict[str, dict[str, object]]:
    return {
        "username": _ordering_column_state(ordering, "username"),
        "tipo": _ordering_column_state(ordering, "tipo"),
        "estado": _ordering_column_state(ordering, "estado"),
    }


def _filtered_queryset(request: HttpRequest):
    qs = userprofile_queryset_for_user(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(user__username__icontains=q)
    ut = request.GET.get("user_type", "").strip()
    if ut in dict(UserProfile.UserType.choices):
        qs = qs.filter(user_type=ut)
    st = request.GET.get("status", "").strip()
    if st in dict(UserProfile.Status.choices):
        qs = qs.filter(status=st)
    ordering = (request.GET.get("ordering") or "").strip() or "username"
    if ordering not in ORDERING_MAP:
        ordering = "username"
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
@require_userprofile_maintainer
def userprofile_list(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    qs, ordering = _filtered_queryset(request)
    page_obj = _paginate(request, qs)
    return render(
        request,
        "userprofile/userprofile_list.html",
        {
            "profile": profile,
            "page_obj": page_obj,
            "profiles": page_obj.object_list,
            "ordering": ordering,
            "current_per_page": _get_per_page(request),
            "user_type_choices": UserProfile.UserType.choices,
            "status_choices": UserProfile.Status.choices,
            "allowed_per_page": ALLOWED_PER_PAGE,
            "pagination_qs": _pagination_qs(request),
            "sort_url_username": _build_sort_url(request, "username"),
            "sort_url_tipo": _build_sort_url(request, "tipo"),
            "sort_url_estado": _build_sort_url(request, "estado"),
            "sort_cols": _ordering_states(ordering),
            "dashboard_nav_active": "userprofiles",
        },
    )


@login_required
@_require_profile
@require_userprofile_maintainer
def userprofile_detail(request: HttpRequest, pk: int) -> HttpResponse:
    profile = request.user.profile
    target = get_object_or_404(
        UserProfile.objects.select_related("user", "company"),
        pk=pk,
    )
    if not user_can_access_target_profile(request.user, target):
        raise Http404()
    return render(
        request,
        "userprofile/userprofile_detail.html",
        {
            "profile": profile,
            "target_profile": target,
            "dashboard_nav_active": "userprofiles",
        },
    )


@login_required
@_require_profile
@require_userprofile_maintainer
@require_http_methods(["GET", "POST"])
def userprofile_create(request: HttpRequest) -> HttpResponse:
    connection_profile = request.user.profile
    show_company = is_superuser_connection(connection_profile)

    if request.method == "POST":
        form = UserProfileCreateForm(
            request.POST,
            connection_profile=connection_profile,
            show_company_select=show_company,
        )
        if form.is_valid():
            posted_company = form.cleaned_data.get("company")
            cid = posted_company.pk if posted_company else None
            company_id = resolve_company_for_save(connection_profile, cid)
            profile = form.save(commit=False)
            result = create_user_profile(
                profile,
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email", ""),
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
                password=form.cleaned_data["password1"],
                company_id=company_id,
                user_type=resolve_new_profile_user_type(connection_profile),
                actor=request.user,
            )
            if result.ok:
                messages.success(request, result.error_message)
                return redirect("userprofile:detail", pk=result.data.pk)
            messages.error(request, result.error_message)
            apply_operation_field_errors(form, result)
        else:
            messages.error(request, MSG_FORM_INVALID)
    else:
        form = UserProfileCreateForm(
            connection_profile=connection_profile,
            show_company_select=show_company,
        )
    return render(
        request,
        "userprofile/userprofile_form.html",
        {
            "profile": connection_profile,
            "form": form,
            "is_edit": False,
            "company_readonly": company_readonly_for_connection(connection_profile),
            "connection_company": connection_profile.company,
            "dashboard_nav_active": "userprofiles",
        },
    )


@login_required
@_require_profile
@require_userprofile_maintainer
@require_http_methods(["GET", "POST"])
def userprofile_update(request: HttpRequest, pk: int) -> HttpResponse:
    connection_profile = request.user.profile
    target = get_object_or_404(UserProfile.objects.select_related("user", "company"), pk=pk)
    if not user_can_access_target_profile(request.user, target):
        raise Http404()
    show_company = is_superuser_connection(connection_profile)

    if request.method == "POST":
        form = UserProfileMaintainerForm(
            request.POST,
            instance=target,
            connection_profile=connection_profile,
            show_company_select=show_company,
        )
        if form.is_valid():
            posted_company = form.cleaned_data.get("company")
            cid = posted_company.pk if posted_company else None
            company_id = resolve_company_for_save(connection_profile, cid)
            obj = form.save(commit=False)
            new_password = form.cleaned_data.get("password1") or None
            result = update_user_profile(
                obj,
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
                email=form.cleaned_data.get("email", ""),
                password=new_password,
                company_id=company_id,
                actor=request.user,
            )
            if result.ok:
                messages.success(request, result.error_message)
                return redirect("userprofile:detail", pk=result.data.pk)
            messages.error(request, result.error_message)
            apply_operation_field_errors(form, result)
        else:
            messages.error(request, MSG_FORM_INVALID)
    else:
        form = UserProfileMaintainerForm(
            instance=target,
            connection_profile=connection_profile,
            show_company_select=show_company,
        )
    return render(
        request,
        "userprofile/userprofile_form.html",
        {
            "profile": connection_profile,
            "form": form,
            "is_edit": True,
            "target_profile": target,
            "company_readonly": company_readonly_for_connection(connection_profile),
            "connection_company": connection_profile.company,
            "dashboard_nav_active": "userprofiles",
        },
    )


@login_required
@_require_profile
@require_userprofile_maintainer
@require_http_methods(["GET", "POST"])
def userprofile_delete(request: HttpRequest, pk: int) -> HttpResponse:
    connection_profile = request.user.profile
    target = get_object_or_404(UserProfile, pk=pk)
    if not user_can_access_target_profile(request.user, target):
        raise Http404()
    if request.method == "POST":
        result = delete_user_profile(target)
        if result.ok:
            messages.success(request, result.error_message)
            return redirect("userprofile:list")
        messages.error(request, result.error_message)
        return redirect("userprofile:detail", pk=target.pk)
    return render(
        request,
        "userprofile/userprofile_confirm_delete.html",
        {
            "profile": connection_profile,
            "target_profile": target,
            "dashboard_nav_active": "userprofiles",
        },
    )
