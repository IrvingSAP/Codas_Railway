"""Configuración de correo compartida (local, prueba/staging y producción)."""

from __future__ import annotations

import os
from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .base import env_bool

CONSOLE_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SMTP_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Modos admitidos en EMAIL_DELIVERY: resend | smtp | console | auto
EMAIL_DELIVERY_RESEND = "resend"
EMAIL_DELIVERY_SMTP = "smtp"
EMAIL_DELIVERY_CONSOLE = "console"
EMAIL_DELIVERY_AUTO = "auto"


def _resend_configured() -> bool:
    return bool((os.environ.get("RESEND_API_KEY") or "").strip())


def _smtp_credentials_configured() -> bool:
    return bool(
        (os.environ.get("EMAIL_HOST_USER") or "").strip()
        and (os.environ.get("EMAIL_HOST_PASSWORD") or "").strip()
    )


def _default_from_email() -> str:
    host_user = (os.environ.get("EMAIL_HOST_USER") or "").strip()
    return (
        (os.environ.get("DEFAULT_FROM_EMAIL") or "").strip()
        or host_user
        or "noreply@codas.local"
    )


def _resolve_delivery_mode(*, require_smtp: bool) -> str:
    """
    Elige backend efectivo.

    - EMAIL_DELIVERY=resend|smtp|console: fuerza el modo.
    - EMAIL_DELIVERY=auto o vacío:
      - producción: Resend si hay RESEND_API_KEY; si no SMTP si hay credenciales.
      - local: Resend si hay RESEND_API_KEY; si no SMTP si hay credenciales; si no consola.
    """
    raw = (os.environ.get("EMAIL_DELIVERY") or EMAIL_DELIVERY_AUTO).strip().lower()
    if raw == EMAIL_DELIVERY_CONSOLE:
        return EMAIL_DELIVERY_CONSOLE
    if raw == EMAIL_DELIVERY_RESEND:
        return EMAIL_DELIVERY_RESEND
    if raw == EMAIL_DELIVERY_SMTP:
        return EMAIL_DELIVERY_SMTP
    if raw not in (EMAIL_DELIVERY_AUTO, ""):
        raise ImproperlyConfigured(
            f"EMAIL_DELIVERY inválido: {raw!r}. Use resend, smtp, console o auto."
        )
    if require_smtp:
        if _resend_configured():
            return EMAIL_DELIVERY_RESEND
        return EMAIL_DELIVERY_SMTP
    if _resend_configured():
        return EMAIL_DELIVERY_RESEND
    if _smtp_credentials_configured():
        return EMAIL_DELIVERY_SMTP
    return EMAIL_DELIVERY_CONSOLE


def _build_smtp_email_settings(*, default_from: str) -> dict[str, Any]:
    """
    SMTP clásico (Gmail, PythonAnywhere, Railway Pro).

    Railway Free/Hobby bloquea puertos SMTP salientes (25/465/587); en esos
    planes use EMAIL_DELIVERY=resend con RESEND_API_KEY.
    """
    host_user = (os.environ.get("EMAIL_HOST_USER") or "").strip()
    if not _smtp_credentials_configured():
        raise ImproperlyConfigured(
            "EMAIL_DELIVERY=smtp pero faltan EMAIL_HOST_USER o EMAIL_HOST_PASSWORD."
        )
    return {
        "EMAIL_DELIVERY_EFFECTIVE": EMAIL_DELIVERY_SMTP,
        "EMAIL_BACKEND": SMTP_EMAIL_BACKEND,
        "EMAIL_HOST": os.environ.get("EMAIL_HOST", "smtp.gmail.com"),
        "EMAIL_PORT": int(os.environ.get("EMAIL_PORT", "587")),
        "EMAIL_USE_TLS": env_bool("EMAIL_USE_TLS", True),
        "EMAIL_USE_SSL": env_bool("EMAIL_USE_SSL", False),
        "EMAIL_HOST_USER": host_user,
        "EMAIL_HOST_PASSWORD": os.environ.get("EMAIL_HOST_PASSWORD", ""),
        "DEFAULT_FROM_EMAIL": default_from,
        "EMAIL_TIMEOUT": int(os.environ.get("EMAIL_TIMEOUT", "30")),
    }


def _build_resend_email_settings(*, default_from: str) -> dict[str, Any]:
    """Resend SDK oficial (API HTTPS; compatible Railway Free/Hobby)."""
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not api_key:
        raise ImproperlyConfigured(
            "EMAIL_DELIVERY=resend pero falta RESEND_API_KEY "
            "(https://resend.com/docs/introduction)."
        )
    return {
        "EMAIL_DELIVERY_EFFECTIVE": EMAIL_DELIVERY_RESEND,
        "RESEND_API_KEY": api_key,
        "DEFAULT_FROM_EMAIL": default_from,
    }


def build_email_settings(*, require_smtp: bool) -> dict[str, Any]:
    """Construye EMAIL_* para inyectar en local.py / production.py."""
    mode = _resolve_delivery_mode(require_smtp=require_smtp)
    default_from = _default_from_email()

    if mode == EMAIL_DELIVERY_CONSOLE:
        return {
            "EMAIL_DELIVERY_EFFECTIVE": EMAIL_DELIVERY_CONSOLE,
            "EMAIL_BACKEND": CONSOLE_EMAIL_BACKEND,
            "DEFAULT_FROM_EMAIL": default_from,
        }

    if mode == EMAIL_DELIVERY_RESEND:
        return _build_resend_email_settings(default_from=default_from)

    if mode == EMAIL_DELIVERY_SMTP:
        if require_smtp and not _smtp_credentials_configured():
            raise ImproperlyConfigured(
                "Correo obligatorio en producción: defina RESEND_API_KEY "
                "(recomendado en Railway Free/Hobby) o EMAIL_HOST_USER y "
                "EMAIL_HOST_PASSWORD para SMTP (Gmail: contraseña de aplicación)."
            )
        return _build_smtp_email_settings(default_from=default_from)

    raise ImproperlyConfigured(f"Modo de correo no soportado: {mode!r}")


def validate_email_settings_for_production() -> None:
    """
    Comprueba que producción pueda enviar correo real.

    En producción EMAIL_BACKEND no se define en .env ni en settings: lo asigna
    build_email_settings() según EMAIL_DELIVERY y las credenciales disponibles.
    """
    if (os.environ.get("EMAIL_BACKEND") or "").strip():
        raise ImproperlyConfigured(
            "No defina EMAIL_BACKEND en producción. Use EMAIL_DELIVERY=resend|smtp "
            "y RESEND_API_KEY o EMAIL_HOST_USER / EMAIL_HOST_PASSWORD. "
            "El backend lo asigna codas.settings._email."
        )
    build_email_settings(require_smtp=True)
