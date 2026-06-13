"""Envío de correo transaccional (SMTP o consola según settings)."""

from __future__ import annotations

import logging
from typing import Sequence

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def effective_email_delivery() -> str:
    return getattr(settings, "EMAIL_DELIVERY_EFFECTIVE", "unknown")


def send_codas_mail(
    *,
    subject: str,
    body: str,
    recipients: Sequence[str],
    fail_silently: bool = False,
) -> int:
    """
    Envía un correo usando la configuración Django del entorno activo.

    Retorna el número de mensajes enviados (0 o 1 en envío simple).
    """
    to = [addr.strip() for addr in recipients if (addr or "").strip()]
    if not to:
        raise ValueError("Debe indicar al menos un destinatario.")

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@codas.local"
    backend = getattr(settings, "EMAIL_BACKEND", "")

    logger.info(
        "Envío correo CODAS backend=%s delivery=%s from=%s to=%s subject=%r",
        backend,
        effective_email_delivery(),
        from_email,
        to,
        subject,
    )

    try:
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
