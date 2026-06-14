"""Envío de correo transaccional (Resend HTTPS, SMTP o consola según settings)."""

from __future__ import annotations

import logging
from typing import Sequence

import resend
from django.conf import settings
from django.core.mail import send_mail

from codas.settings._email import EMAIL_DELIVERY_RESEND

logger = logging.getLogger(__name__)


def effective_email_delivery() -> str:
    return getattr(settings, "EMAIL_DELIVERY_EFFECTIVE", "unknown")


def _send_via_resend(
    *,
    subject: str,
    body: str,
    from_email: str,
    recipients: list[str],
) -> int:
    """Envía correo con el SDK oficial de Resend (https://resend.com/docs/send-with-python)."""
    api_key = (getattr(settings, "RESEND_API_KEY", None) or "").strip()
    if not api_key:
        raise ValueError("RESEND_API_KEY no configurada.")

    resend.api_key = api_key
    params: resend.Emails.SendParams = {
        "from": from_email,
        "to": recipients,
        "subject": subject,
        "text": body,
    }
    resend.Emails.send(params)
    return 1


def send_codas_mail(
    *,
    subject: str,
    body: str,
    recipients: Sequence[str],
    fail_silently: bool = False,
) -> int:
    """
    Envía un correo según EMAIL_DELIVERY_EFFECTIVE:
    resend → SDK Resend; smtp/console → django.core.mail.send_mail.
    """
    to = [addr.strip() for addr in recipients if (addr or "").strip()]
    if not to:
        raise ValueError("Debe indicar al menos un destinatario.")

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@codas.local"
    delivery = effective_email_delivery()
    backend = getattr(settings, "EMAIL_BACKEND", "")

    logger.info(
        "Envío correo CODAS backend=%s delivery=%s from=%s to=%s subject=%r",
        backend,
        delivery,
        from_email,
        to,
        subject,
    )

    try:
        if delivery == EMAIL_DELIVERY_RESEND:
            sent = _send_via_resend(
                subject=subject,
                body=body,
                from_email=from_email,
                recipients=to,
            )
        else:
            sent = send_mail(
                subject,
                body,
                from_email,
                to,
                fail_silently=fail_silently,
            )
    except Exception:
        logger.exception("Fallo al enviar correo CODAS a %s", to)
        raise

    logger.info("Correo CODAS enviado (sent=%s) a %s", sent, to)
    return sent
