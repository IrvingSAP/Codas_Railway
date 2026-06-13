"""
Código de confirmación por correo (CODAS_SECURITY §2, caducidad 5 minutos).
"""

from __future__ import annotations

import logging
import random
from datetime import timedelta
from typing import TYPE_CHECKING

from apps.core.services.email_delivery import send_codas_mail
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import User

    from apps.userprofile.models import UserProfile

logger = logging.getLogger(__name__)


def issue_new_email_code(profile: UserProfile) -> str:
    code = f"{random.randint(0, 999999):06d}"
    profile.email_confirm_code = code
    profile.email_confirm_exp = timezone.now() + timedelta(minutes=5)
    profile.save(update_fields=["email_confirm_code", "email_confirm_exp", "updated_at"])
    return code


def send_email_confirmation(*, user: User, code: str) -> None:
    subject = "CODAS — Código de validación"
    body = (
        f"Su código de validación es: {code}\n\n"
        "Vence en 5 minutos. Si no solicitó este acceso, ignore este mensaje."
    )
    try:
        send_codas_mail(
            subject=subject,
            body=body,
            recipients=[user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Fallo al enviar correo de confirmación a %s", user.email)
        raise


def confirm_email_on_profile(profile: UserProfile) -> None:
    profile.email_confirmed = True
    profile.email_confirm_code = None
    profile.email_confirm_exp = None
    profile.save(
        update_fields=["email_confirmed", "email_confirm_code", "email_confirm_exp", "updated_at"]
    )


def should_issue_fresh_email_code(profile: UserProfile) -> bool:
    """True si no hay código o ya caducó."""
    if not (profile.email_confirm_code or "").strip():
        return True
    exp = profile.email_confirm_exp
    if exp is None:
        return True
    return timezone.now() > exp


def verify_submitted_email_code(profile: UserProfile, submitted: str) -> tuple[bool, str | None]:
    """
    Retorna (éxito, código_corto_error: ``wrong``, ``expired``, ``missing``, ``empty``).
    """
    if not (submitted or "").strip():
        return False, "empty"
    expected = (profile.email_confirm_code or "").strip()
    if not expected:
        return False, "missing"
    exp = profile.email_confirm_exp
    if exp is None or timezone.now() > exp:
        return False, "expired"
    if submitted.strip() != expected:
        return False, "wrong"
    return True, None
