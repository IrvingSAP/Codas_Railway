"""Persistencia de parámetros IDENTITY por cabecera (`HeaderTableAutoKeyConfig`)."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from apps.table_design.models import HeaderTable, HeaderTableAutoKeyConfig


def get_auto_key_config(header: HeaderTable) -> HeaderTableAutoKeyConfig | None:
    try:
        return header.auto_key_config
    except HeaderTableAutoKeyConfig.DoesNotExist:
        return None


def persist_auto_key_config(
    header: HeaderTable,
    *,
    identity_start: int | None,
    identity_increment: int | None,
    identity_cache: int | None,
    identity_cycle: bool,
    user: AbstractBaseUser | None = None,
) -> HeaderTableAutoKeyConfig:
    config, created = HeaderTableAutoKeyConfig.objects.get_or_create(
        header=header,
        defaults={
            "created_by": user,
            "updated_by": user,
        },
    )
    config.identity_start = identity_start
    config.identity_increment = identity_increment
    config.identity_cache = identity_cache
    config.identity_cycle = bool(identity_cycle)
    if user is not None:
        if created:
            config.created_by = user
        config.updated_by = user
    config.full_clean()
    config.save()
    return config


def auto_key_config_has_input(
    *,
    identity_start: int | None,
    identity_increment: int | None,
    identity_cache: int | None,
    identity_cycle: bool,
) -> bool:
    """True si el POST incluye al menos un parámetro IDENTITY distinto de vacío."""
    if identity_cycle:
        return True
    return any(
        value is not None
        for value in (identity_start, identity_increment, identity_cache)
    )


def auto_key_config_changed(
    existing: HeaderTableAutoKeyConfig,
    *,
    identity_start: int | None,
    identity_increment: int | None,
    identity_cache: int | None,
    identity_cycle: bool,
) -> bool:
    """True si algún parámetro IDENTITY difiere del registro actual."""
    return (
        existing.identity_start != identity_start
        or existing.identity_increment != identity_increment
        or existing.identity_cache != identity_cache
        or existing.identity_cycle != bool(identity_cycle)
    )


def delete_auto_key_config(header: HeaderTable) -> None:
    """Elimina la fila 1:1 cuando el usuario deja vacíos todos los parámetros IDENTITY."""
    HeaderTableAutoKeyConfig.objects.filter(header=header).delete()


def persist_auto_key_from_cleaned(
    header: HeaderTable,
    cleaned_data: dict[str, Any],
    *,
    user: AbstractBaseUser | None = None,
) -> HeaderTableAutoKeyConfig | None:
    """
    Sincroniza ``HeaderTableAutoKeyConfig`` solo cuando hay parámetros IDENTITY informados.

    - Sin ningún valor en el formulario: no debe existir fila (se borra si había).
    - Con valores y sin cambios respecto a BD: no escribe (no hubo actualización).
    - Con valores nuevos o modificados: crea o actualiza la fila 1:1.
    """
    identity_start = cleaned_data.get("identity_start")
    identity_increment = cleaned_data.get("identity_increment")
    identity_cache = cleaned_data.get("identity_cache")
    identity_cycle = bool(cleaned_data.get("identity_cycle"))

    if not auto_key_config_has_input(
        identity_start=identity_start,
        identity_increment=identity_increment,
        identity_cache=identity_cache,
        identity_cycle=identity_cycle,
    ):
        delete_auto_key_config(header)
        return None

    existing = get_auto_key_config(header)
    if existing is not None and not auto_key_config_changed(
        existing,
        identity_start=identity_start,
        identity_increment=identity_increment,
        identity_cache=identity_cache,
        identity_cycle=identity_cycle,
    ):
        return existing

    return persist_auto_key_config(
        header,
        identity_start=identity_start,
        identity_increment=identity_increment,
        identity_cache=identity_cache,
        identity_cycle=identity_cycle,
        user=user,
    )


def auto_key_initial_from_header(header: HeaderTable) -> dict[str, Any]:
    config = get_auto_key_config(header)
    if not config:
        return {
            "identity_start": None,
            "identity_increment": None,
            "identity_cache": None,
            "identity_cycle": False,
        }
    return {
        "identity_start": config.identity_start,
        "identity_increment": config.identity_increment,
        "identity_cache": config.identity_cache,
        "identity_cycle": config.identity_cycle,
    }
