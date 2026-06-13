"""Entorno local de desarrollo."""
from .base import *  # noqa: F403
from .base import env_bool
from ._database import (
    apply_test_database_settings,
    build_databases_settings,
    validate_database_settings,
)
from ._email import build_email_settings

DEBUG = env_bool("DJANGO_DEBUG", True)

if not SECRET_KEY:  # noqa: F405
    SECRET_KEY = "django-insecure-solo-desarrollo-local-cambiar"

if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = build_databases_settings()
apply_test_database_settings(DATABASES)

# Correo: SMTP si hay credenciales en .env; si no, consola (ver EMAIL_DELIVERY).
globals().update(build_email_settings(require_smtp=False))

validate_database_settings()
