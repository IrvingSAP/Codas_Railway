"""
Settings mínimos para ``collectstatic`` en build CI/Railway.

No sustituye ``production`` en runtime (Gunicorn usa ``codas.settings.production`` vía
``wsgi.py``). Evita exigir DATABASE_URL, SMTP ni CSRF durante la fase de build.
"""

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = os.environ.get(  # noqa: F405
    "DJANGO_SECRET_KEY",
    "collectstatic-build-only-no-usar-en-runtime",
)

ALLOWED_HOSTS = ["*"]

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

# Placeholder: collectstatic no abre conexión a la BD.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "collectstatic_build",
        "USER": "collectstatic_build",
        "PASSWORD": "collectstatic_build",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}
