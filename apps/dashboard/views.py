from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.company.models import Company
from apps.userprofile.models import UserProfile
from apps.dashboard.services.admin_system_metrics import get_admin_system_dashboard_metrics
from apps.dashboard.services.profile_company import get_dashboard_company_id
from apps.userprofile.services.company_user_metrics import get_company_user_metrics

User = get_user_model()


def _dashboard_template_by_user_type(profile: UserProfile) -> str:
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return "dashboard/home_superuser.html"
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY:
        return "dashboard/home_admin_company.html"
    if profile.user_type == UserProfile.UserType.ADMIN_SYSTEM:
        return "dashboard/home_admin_system.html"
    if profile.user_type == UserProfile.UserType.USER:
        return "dashboard/home_user.html"
    return "dashboard/dashboard.html"


@login_required
def dashboard_home(request: HttpRequest) -> HttpResponse:
    """Entrada tras login: menú y panel según tipo de usuario (CODAS UserProfile)."""
    try:
        profile = UserProfile.objects.select_related("company").get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(
            request,
            "Su cuenta no tiene perfil configurado. Contacte al administrador de sistemas.",
        )
        return redirect("security:security_login")

    if profile.user_type == UserProfile.UserType.SUPERUSER:
        context = {
            "profile": profile,
            "dashboard_nav_active": "home",
            "total_companies": Company.objects.count(),
            "total_users": User.objects.count(),
            "total_admin_company": UserProfile.objects.filter(
                user_type=UserProfile.UserType.ADMIN_COMPANY
            ).count(),
        }
        return render(request, _dashboard_template_by_user_type(profile), context)

    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY:
        metrics = get_company_user_metrics(get_dashboard_company_id(profile))
        context = {
            "profile": profile,
            "dashboard_nav_active": "home",
            "total_users": metrics.total_users,
            "total_admin_system": metrics.total_admin_system,
        }
        return render(request, _dashboard_template_by_user_type(profile), context)

    if profile.user_type == UserProfile.UserType.ADMIN_SYSTEM:
        company_id = get_dashboard_company_id(profile)
        metrics = get_admin_system_dashboard_metrics(company_id)
        context = {
            "profile": profile,
            "dashboard_nav_active": "home",
            "metrics": metrics,
            "total_users": metrics.total_users,
        }
        return render(request, _dashboard_template_by_user_type(profile), context)

    context = {"profile": profile, "dashboard_nav_active": "home"}
    return render(request, _dashboard_template_by_user_type(profile), context)
