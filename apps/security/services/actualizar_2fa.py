"""
Entrada «Actualizar 2FA» (CODAS_SECURITY §9): credenciales y reset sin TOTP previo.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse

from apps.security.services.profile_routing import is_eligible_for_actualizar_2fa
from apps.security.services.security_session import set_pending_user
from apps.security.services.totp_reset import apply_profile_2fa_reset
from apps.userprofile.models import UserProfile

User = get_user_model()

MSG_BAD_PASSWORD = (
    "Error en contraseña, si requiere solicitar un cambio contacte al administrador de sistemas"
)
MSG_USER_NOT_FOUND = "Error usuario no Existe en sistema"
MSG_NOT_ELIGIBLE = (
    "Esta opción solo está disponible para usuarios que ya tenían el segundo factor "
    "completamente activado. Use el inicio de sesión habitual."
)
MSG_NO_PROFILE = "Su cuenta no tiene perfil configurado. Contacte al administrador de sistemas."


def process_security_actualizar_2fa_step(request: Any) -> dict[str, Any]:
    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""

    errors: list[str] = []
    if not username:
        errors.append("Ingrese el usuario.")
    if not password:
        errors.append("Ingrese la contraseña.")
    if errors:
        return {"errors": errors, "redirect_url": None}

    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        return {"errors": [MSG_USER_NOT_FOUND], "redirect_url": None}

    auth_user = authenticate(request, username=username, password=password)
    if auth_user is None:
        return {"errors": [MSG_BAD_PASSWORD], "redirect_url": None}

    if not auth_user.is_active:
        return {"errors": ["Su cuenta está desactivada."], "redirect_url": None}

    try:
        profile = auth_user.profile
    except UserProfile.DoesNotExist:
        return {"errors": [MSG_NO_PROFILE], "redirect_url": None}

    if not is_eligible_for_actualizar_2fa(auth_user, profile):
        return {"errors": [MSG_NOT_ELIGIBLE], "redirect_url": None}

    apply_profile_2fa_reset(profile)
    set_pending_user(request, auth_user.pk)
    return {
        "errors": [],
        "redirect_url": reverse("security:security_email_code"),
    }
