"""
Paso 1 — Credenciales (CODAS_SECURITY: §3 usuario nuevo, §8 usuario activo).
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.security.services.profile_routing import route_after_valid_password
from apps.security.services.security_session import set_pending_user
from apps.userprofile.models import UserProfile

User = get_user_model()

MSG_USER_NOT_FOUND = "Error usuario no Existe en sistema"
MSG_BAD_PASSWORD = (
    "Error en contraseña, si requiere solicitar un cambio contacte al administrador de sistemas"
)
MSG_NO_PROFILE = "Su cuenta no tiene perfil configurado. Contacte al administrador de sistemas."
MSG_NO_EMAIL = (
    "Su usuario no tiene correo electrónico registrado. "
    "Contacte al administrador de sistemas para completar el registro."
)
MSG_INACTIVE = "Su cuenta está desactivada. Contacte al administrador de sistemas."
MSG_LOCKED = "Su cuenta está temporalmente bloqueada. Intente más tarde."


def process_security_login_step(request: Any) -> dict[str, Any]:
    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""

    errors: list[str] = []
    if not username:
        errors.append("Ingrese el usuario.")
    if not password:
        errors.append("Ingrese la contraseña.")
    if errors:
        return {"errors": errors, "redirect_url": None, "info_message": None}

    try:
        candidate = User.objects.get(username=username)
        print('candidate', candidate)
    except User.DoesNotExist:
        return {"errors": [MSG_USER_NOT_FOUND], "redirect_url": None, "info_message": None}

    auth_user = authenticate(request, username=username, password=password)
    print('auth_user', auth_user)
    if auth_user is None:
        return {"errors": [MSG_BAD_PASSWORD], "redirect_url": None, "info_message": None}

    if not auth_user.is_active:
        return {"errors": [MSG_INACTIVE], "redirect_url": None, "info_message": None}

    try:
        profile = auth_user.profile
        print('profile', profile)
    except UserProfile.DoesNotExist:
        print('profile no existe')
        return {"errors": [MSG_NO_PROFILE], "redirect_url": None, "info_message": None}

    if profile.status == profile.Status.INACTIVE:
        return {"errors": [MSG_INACTIVE], "redirect_url": None, "info_message": None}

    if profile.locked_until and profile.locked_until > timezone.now():
        return {"errors": [MSG_LOCKED], "redirect_url": None, "info_message": None}

    route = route_after_valid_password(auth_user, profile)
    if route == "error_no_email":
        return {"errors": [MSG_NO_EMAIL], "redirect_url": None, "info_message": None}
    if route == "error_no_profile":
        return {"errors": [MSG_NO_PROFILE], "redirect_url": None, "info_message": None}

    set_pending_user(request, auth_user.pk)
    return {
        "errors": [],
        "redirect_url": reverse(f"security:{route}"),
        "info_message": None,
    }
