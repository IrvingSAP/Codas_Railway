"""
Reset de 2FA según CODAS_SECURITY §9.3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from apps.userprofile.models import UserProfile


def apply_profile_2fa_reset(profile: UserProfile) -> None:
    """Vacía TOTP y fuerza ciclo completo (correo + 2FA de nuevo)."""
    profile.totp_secret = None
    profile.tfa_verified = False
    profile.email_confirmed = False
    profile.email_confirm_code = None
    profile.email_confirm_exp = None
    profile.last_totp_reset = timezone.now()
    profile.save(
        update_fields=[
            "totp_secret",
            "tfa_verified",
            "email_confirmed",
            "email_confirm_code",
            "email_confirm_exp",
            "last_totp_reset",
            "updated_at",
        ]
    )
