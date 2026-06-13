"""Configuración HTTPS/CSRF para producción (proxy TLS, cookies seguras)."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .base import env_list


def build_https_settings() -> dict[str, Any]:
    """Construye CSRF_TRUSTED_ORIGINS y cabeceras/cookies para HTTPS en PaaS."""
    return {
        "CSRF_TRUSTED_ORIGINS": env_list("CSRF_TRUSTED_ORIGINS"),
        "SECURE_PROXY_SSL_HEADER": ("HTTP_X_FORWARDED_PROTO", "https"),
        "SESSION_COOKIE_SECURE": True,
        "CSRF_COOKIE_SECURE": True,
    }


def validate_https_settings_for_production(csrf_trusted_origins: list[str]) -> None:
    """Comprueba orígenes CSRF para POST con HTTPS en producción."""
    if not csrf_trusted_origins:
        raise ImproperlyConfigured(
            "CSRF_TRUSTED_ORIGINS es obligatorio en producción "
            "(p. ej. https://tu-proyecto.up.railway.app)."
        )
