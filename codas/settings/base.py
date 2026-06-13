"""Configuración base compartida (local y production)."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def env_list(key: str, default: str = "") -> list[str]:
    raw = os.environ.get(key, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")

# Secreto dedicado a la huella HMAC de suscripciones (recomendado en producción).
LICENSE_SECRET_KEY = os.environ.get("LICENSE_SECRET_KEY", "")

DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS: list[str] = env_list("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.company",
    "apps.billing",
    "apps.sources",
    "apps.table_design",
    "apps.sp_asistido",
    "apps.maintenance_builder",
    "apps.userprofile",
    "apps.security",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "codas.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.dashboard.context_processors.dashboard_sidebar",
            ],
        },
    },
]

WSGI_APPLICATION = "codas.wsgi.application"

# DATABASES: definir en local.py y production.py (PostgreSQL vía _database.py).

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

# Debe ser ruta absoluta desde la raíz del sitio (barra inicial). Si es "static/", el navegador
# puede resolver el CSS respecto a /panel/... y no cargar el bundle correcto.
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/ingresar/"
LOGIN_REDIRECT_URL = "/panel/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "codas": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "codas",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


def validate_production() -> None:
    """Llamar desde production si faltan variables críticas."""
    if not SECRET_KEY:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatorio en producción.")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS es obligatorio en producción (lista separada por comas).")
    if not (os.environ.get("LICENSE_SECRET_KEY") or "").strip():
        raise ImproperlyConfigured(
            "LICENSE_SECRET_KEY es obligatorio en producción (integridad de suscripciones)."
        )
