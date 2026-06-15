"""Envío de correo transaccional (Resend HTTPS, SMTP o consola según settings)."""

from __future__ import annotations

import logging
from typing import Sequence

import resend
from django.conf import settings
from django.core.mail import send_mail
from resend.exceptions import ResendError

from codas.settings._email import EMAIL_DELIVERY_RESEND

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Fallo de envío con mensaje apto para mostrar al usuario."""

    def __init__(self, user_message: str, *, cause: Exception | None = None) -> None:
        self.user_message = user_message
        super().__init__(user_message)
        if cause is not None:
            self.__cause__ = cause


def effective_email_delivery() -> str:
    return getattr(settings, "EMAIL_DELIVERY_EFFECTIVE", "unknown")


def email_delivery_user_message(exc: Exception) -> str:
    """Traduce excepciones de envío a texto de negocio (sin detalles técnicos)."""
    if isinstance(exc, EmailDeliveryError):
        return exc.user_message

    if isinstance(exc, ResendError):
        detail = (exc.message or "").lower()
        if exc.code in (403, "403") or "only send testing emails" in detail:
            return (
                "Resend en modo prueba solo permite enviar al correo de la cuenta Resend. "
                "Para cualquier usuario, verifique un dominio en resend.com/domains y "
                "configure DEFAULT_FROM_EMAIL con ese dominio en Railway."
            )
        if exc.code in (401, "401") or "api key" in detail:
            return (
                "La clave de API de Resend no es válida. Revise RESEND_API_KEY en Railway."
            )
        if "domain" in detail and "verif" in detail:
            return (
                "El remitente no coincide con un dominio verificado en Resend. "
                "Revise DEFAULT_FROM_EMAIL y el estado del dominio en resend.com/domains."
            )
        return "No se pudo enviar el correo vía Resend. Intente más tarde o contacte al administrador."

    if effective_email_delivery() == EMAIL_DELIVERY_RESEND:
        return "No se pudo enviar el correo vía Resend. Intente más tarde."

    return "No se pudo enviar el correo. Compruebe la configuración SMTP o reintente."


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
        raise EmailDeliveryError(
            "Falta RESEND_API_KEY en la configuración del servidor.",
            cause=ValueError("RESEND_API_KEY no configurada."),
        )

    resend.api_key = api_key
    params: resend.Emails.SendParams = {
        "from": from_email,
        "to": recipients,
        "subject": subject,
        "text": body,
    }
    try:
        resend.Emails.send(params)
    except ResendError as exc:
        logger.exception(
            "Resend rechazó envío from=%s to=%s code=%s type=%s",
            from_email,
            recipients,
            exc.code,
            exc.error_type,
        )
        raise EmailDeliveryError(
            email_delivery_user_message(exc),
            cause=exc,
        ) from exc
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
    except Exception as exc:
        logger.exception("Fallo al enviar correo CODAS a %s", to)
        if not isinstance(exc, EmailDeliveryError):
            raise EmailDeliveryError(
                email_delivery_user_message(exc),
                cause=exc,
            ) from exc
        raise

    logger.info("Correo CODAS enviado (sent=%s) a %s", sent, to)
    return sent
