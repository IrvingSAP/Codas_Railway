"""
Clasificación de ruta tras contraseña correcta (CODAS_SECURITY §2, §8.1, §2.1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from apps.userprofile.models import UserProfile

if TYPE_CHECKING:
    from django.contrib.auth.models import User

RouteName = Literal[
    "security_totp",
    "security_email_code",
    "security_totp_setup",
    "error_no_email",
]


def user_email_filled(user: User) -> bool:
    return bool((user.email or "").strip())


def totp_secret_filled(profile: UserProfile) -> bool:
    return bool((profile.totp_secret or "").strip())


def is_active_for_totp_login(user: User, profile: UserProfile) -> bool:
    """Criterio recomendado §8.1: secreto, correo y ambos flags en True."""
    return (
        totp_secret_filled(profile)
        and user_email_filled(user)
        and profile.email_confirmed
        and profile.tfa_verified
    )


def is_eligible_for_actualizar_2fa(user: User, profile: UserProfile) -> bool:
    """§9.1 + criterio recomendado: usuario que ya era plenamente activo."""
    return is_active_for_totp_login(user, profile)


def route_after_valid_password(user: User, profile: UserProfile) -> RouteName:
    if not user_email_filled(user):
        return "error_no_email"
    if is_active_for_totp_login(user, profile):
        return "security_totp"
    if profile.email_confirmed and not profile.tfa_verified:
        return "security_totp_setup"
    if not profile.email_confirmed:
        return "security_email_code"
    if not totp_secret_filled(profile):
        return "security_totp_setup"
    return "security_totp_setup"
