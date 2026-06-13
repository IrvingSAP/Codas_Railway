from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.company.forms import CompanyForm
from apps.company.models import Company
from apps.company.services.access import (
    MSG_UNAUTHORIZED_COMPANY,
    company_queryset_for_user,
    is_company_maintainer,
    is_superuser_profile,
    user_can_view_company,
)
from apps.company.services.company_persistence import (
    create_company,
    delete_company_if_allowed,
    update_company,
)
from apps.company.services.deletion import get_company_delete_context
from apps.core.services.operation_messages import MSG_FORM_INVALID
from apps.core.services.operation_result import OperationResult
from apps.userprofile.models import UserProfile


def _require_profile(view_func):
    """Exige perfil; si no existe, error y redirect al login."""

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


def require_company_maintainer(view_func):
    """Solo SU o AC (regla a/b); otros reciben advertencia y vuelta al panel."""

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        profile = request.user.profile
        if not is_company_maintainer(profile):
            messages.warning(request, MSG_UNAUTHORIZED_COMPANY)
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def require_superuser_company(view_func):
    """Solo SU para CRUD de escritura (crear/editar/eliminar)."""

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        profile = request.user.profile
        if not is_superuser_profile(profile):
            messages.warning(request, MSG_UNAUTHORIZED_COMPANY)
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def _apply_operation_field_errors(form: CompanyForm, result: OperationResult) -> None:
    """Mapea ``field_errors`` del servicio al formulario Django."""
    if not result.field_errors:
        return
    for field_name, error_list in result.field_errors.items():
        for message in error_list:
            if field_name == "__all__":
                form.add_error(None, message)
            else:
                form.add_error(field_name, message)


@login_required
@_require_profile
@require_company_maintainer
def company_list(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    companies = company_queryset_for_user(request.user).order_by("name_short")
    return render(
        request,
        "company/company_list.html",
        {
            "profile": profile,
            "companies": companies,
            "can_crud": is_superuser_profile(profile),
            "dashboard_nav_active": "companies",
        },
    )


@login_required
@_require_profile
@require_company_maintainer
def company_detail(request: HttpRequest, pk: int) -> HttpResponse:
    profile = request.user.profile
    company = get_object_or_404(Company, pk=pk)
    if not user_can_view_company(request.user, company):
        raise Http404()
    return render(
        request,
        "company/company_detail.html",
        {
            "profile": profile,
            "company": company,
            "can_crud": is_superuser_profile(profile),
            "dashboard_nav_active": "companies",
        },
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def company_create(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            result = create_company(company, user=request.user)
            if result.ok:
                messages.success(request, result.error_message)
                return redirect("company:detail", pk=result.data.pk)
            messages.error(request, result.error_message)
            _apply_operation_field_errors(form, result)
        else:
            messages.error(request, MSG_FORM_INVALID)
    else:
        form = CompanyForm()
    return render(
        request,
        "company/company_form.html",
        {
            "profile": profile,
            "form": form,
            "is_edit": False,
            "dashboard_nav_active": "companies",
        },
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def company_update(request: HttpRequest, pk: int) -> HttpResponse:
    profile = request.user.profile
    company = get_object_or_404(Company, pk=pk)
    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            obj = form.save(commit=False)
            result = update_company(obj, user=request.user)
            if result.ok:
                messages.success(request, result.error_message)
                return redirect("company:detail", pk=result.data.pk)
            messages.error(request, result.error_message)
            _apply_operation_field_errors(form, result)
        else:
            messages.error(request, MSG_FORM_INVALID)
    else:
        form = CompanyForm(instance=company)
    return render(
        request,
        "company/company_form.html",
        {
            "profile": profile,
            "form": form,
            "company": company,
            "is_edit": True,
            "dashboard_nav_active": "companies",
        },
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def company_delete(request: HttpRequest, pk: int) -> HttpResponse:
    profile = request.user.profile
    company = get_object_or_404(Company, pk=pk)
    delete_ctx = get_company_delete_context(company)
    if request.method == "POST":
        result = delete_company_if_allowed(company)
        if result.ok:
            messages.success(request, result.error_message)
            return redirect("company:list")
        messages.error(request, result.error_message)
        return redirect("company:detail", pk=company.pk)
    return render(
        request,
        "company/company_confirm_delete.html",
        {
            "profile": profile,
            "company": company,
            "dashboard_nav_active": "companies",
            **delete_ctx,
        },
    )
