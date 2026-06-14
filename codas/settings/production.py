"""Entorno producción (DEBUG off, variables obligatorias vía .env o sistema)."""
from .base import *  # noqa: F403
from ._database import build_databases_settings, validate_database_settings
from ._email import build_email_settings, validate_email_settings_for_production
from ._https import build_https_settings, validate_https_settings_for_production

DEBUG = False

DATABASES = build_databases_settings()

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],  # noqa: F405
]

globals().update(build_https_settings())

# Correo: Resend (HTTPS) o SMTP; EMAIL_BACKEND lo asigna _email.py (no definir en .env).
globals().update(build_email_settings(require_smtp=True))

validate_production()  # noqa: F405
validate_database_settings()
validate_email_settings_for_production()
validate_https_settings_for_production(CSRF_TRUSTED_ORIGINS)  # noqa: F405
