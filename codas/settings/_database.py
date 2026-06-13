"""Configuración de base de datos PostgreSQL (local y producción)."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

POSTGRES_ENGINE = "django.db.backends.postgresql"


def _conn_max_age() -> int | None:
    raw = (os.environ.get("DB_CONN_MAX_AGE") or "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"DB_CONN_MAX_AGE inválido: {raw!r}. Use un entero en segundos."
        ) from exc
    return max(value, 0)


def _postgres_options() -> dict[str, Any]:
    options: dict[str, Any] = {}
    sslmode = (os.environ.get("DB_SSLMODE") or "").strip()
    if sslmode:
        options["sslmode"] = sslmode
    return options


def _postgres_config_from_url(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in ("postgres", "postgresql"):
        raise ImproperlyConfigured(
            f"DATABASE_URL debe usar esquema postgresql:// (recibido: {parsed.scheme!r})."
        )
    db_name = (parsed.path or "").lstrip("/")
    if not db_name:
        raise ImproperlyConfigured("DATABASE_URL debe incluir el nombre de la base de datos.")

    config: dict[str, Any] = {
        "ENGINE": POSTGRES_ENGINE,
        "NAME": db_name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
    }
    conn_max_age = _conn_max_age()
    if conn_max_age is not None:
        config["CONN_MAX_AGE"] = conn_max_age
    options = _postgres_options()
    if options:
        config["OPTIONS"] = options
    return config


def _postgres_config_from_vars() -> dict[str, Any] | None:
    name = (os.environ.get("DB_NAME") or "").strip()
    user = (os.environ.get("DB_USER") or "").strip()
    password = os.environ.get("DB_PASSWORD")
    if password is None:
        password = ""
    host = (os.environ.get("DB_HOST") or "localhost").strip()
    port = (os.environ.get("DB_PORT") or "5432").strip()

    if not name or not user:
        return None

    config: dict[str, Any] = {
        "ENGINE": POSTGRES_ENGINE,
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port,
    }
    conn_max_age = _conn_max_age()
    if conn_max_age is not None:
        config["CONN_MAX_AGE"] = conn_max_age
    options = _postgres_options()
    if options:
        config["OPTIONS"] = options
    return config


def build_databases_settings() -> dict[str, dict[str, Any]]:
    """
    Construye DATABASES para Django.

    Prioridad: DATABASE_URL, luego DB_NAME + DB_USER (+ DB_PASSWORD, DB_HOST, DB_PORT).
    """
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if url:
        return {"default": _postgres_config_from_url(url)}

    from_vars = _postgres_config_from_vars()
    if from_vars is not None:
        return {"default": from_vars}

    raise ImproperlyConfigured(
        "Base de datos PostgreSQL no configurada. Defina DATABASE_URL o "
        "DB_NAME, DB_USER, DB_PASSWORD, DB_HOST y DB_PORT en .env "
        "(ver .env.example)."
    )


def apply_test_database_settings(databases: dict[str, dict[str, Any]]) -> None:
    """
    Ajusta la BD usada por ``manage.py test`` cuando el rol no tiene CREATEDB.

    Defina ``DB_TEST_NAME`` en ``.env`` (p. ej. ``test_codas_dev``) y cree esa
    base manualmente con un superusuario de PostgreSQL antes de ejecutar tests
    con ``--keepdb`` (ver docs/CODAS_DATABASE.md § 5).
    """
    test_name = (os.environ.get("DB_TEST_NAME") or "").strip()
    if not test_name:
        return
    default = databases.get("default")
    if default is None:
        return
    default["TEST"] = {"NAME": test_name}


def validate_database_settings() -> None:
    """Comprueba que la configuración PostgreSQL esté completa al arrancar."""
    build_databases_settings()
