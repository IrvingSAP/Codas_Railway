"""Context processors del panel CODAS."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from apps.userprofile.models import UserProfile

_DEFAULT_SIDEBAR = "dashboard/includes/sidebar_user.html"

# Claves = valor en BD (`user_type`), no el miembro del enum.
_SIDEBAR_BY_TYPE: dict[str, str] = {
    UserProfile.UserType.SUPERUSER.value: "dashboard/includes/sidebar_superuser.html",
    UserProfile.UserType.ADMIN_COMPANY.value: "dashboard/includes/sidebar_admin_company.html",
    UserProfile.UserType.ADMIN_SYSTEM.value: "dashboard/includes/sidebar_admin_system.html",
    UserProfile.UserType.USER.value: "dashboard/includes/sidebar_user.html",
}


def dashboard_sidebar(request: HttpRequest) -> dict[str, Any]:
    """
    Plantilla del menú lateral según ``UserProfile.user_type``.
    Sin usuario autenticado o sin perfil: menú de usuario final (placeholder).
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"dashboard_sidebar_include": _DEFAULT_SIDEBAR}
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return {"dashboard_sidebar_include": _DEFAULT_SIDEBAR}
    path = _SIDEBAR_BY_TYPE.get(profile.user_type, _DEFAULT_SIDEBAR)
    return {"dashboard_sidebar_include": path}
