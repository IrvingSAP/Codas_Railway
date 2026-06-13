"""Efectos sobre script DDL tras editar una cabecera."""

from __future__ import annotations

from typing import Any

from apps.table_design.models import HeaderTable
from apps.table_design.services.auto_key_config import (
    auto_key_config_changed,
    auto_key_config_has_input,
    get_auto_key_config,
)

_HEADER_EDIT_COMPARE_FIELDS = (
    "table_model",
    "table_name_long",
    "table_name_short",
    "schema",
    "table_type",
    "status",
    "pk_constraint_name",
    "record_format_name",
    "notes",
)


def header_table_edit_fields_changed(
    original: HeaderTable,
    candidate: HeaderTable,
) -> bool:
    """True si algún campo editable de cabecera difiere del registro en BD."""
    for name in _HEADER_EDIT_COMPARE_FIELDS:
        if getattr(original, name) != getattr(candidate, name):
            return True
    return False


def auto_key_edit_will_mutate(header: HeaderTable, cleaned_data: dict[str, Any]) -> bool:
    """True si el POST modificará o eliminará ``HeaderTableAutoKeyConfig``."""
    identity_start = cleaned_data.get("identity_start")
    identity_increment = cleaned_data.get("identity_increment")
    identity_cache = cleaned_data.get("identity_cache")
    identity_cycle = bool(cleaned_data.get("identity_cycle"))
    existing = get_auto_key_config(header)

    if not auto_key_config_has_input(
        identity_start=identity_start,
        identity_increment=identity_increment,
        identity_cache=identity_cache,
        identity_cycle=identity_cycle,
    ):
        return existing is not None

    if existing is None:
        return True

    return auto_key_config_changed(
        existing,
        identity_start=identity_start,
        identity_increment=identity_increment,
        identity_cache=identity_cache,
        identity_cycle=identity_cycle,
    )


def apply_script_invalidation_on_header_edit(
    candidate: HeaderTable,
    *,
    had_script_generated: bool,
) -> None:
    """Tras editar y guardar, el DDL previo deja de ser válido."""
    if had_script_generated:
        candidate.script_generated = False
        candidate.script_date = None


def reset_header_script_after_edit(
    header: HeaderTable,
    *,
    had_script_generated: bool,
    cleaned_data: dict[str, Any],
    header_data_changed: bool = False,
    header_form_changed: bool | None = None,
) -> bool:
    """
    Si la cabecera tenía script generado y hubo cambios en la edición,
    marca ``script_generated=False`` y limpia ``script_date``.

    ``header_form_changed`` es alias obsoleto de ``header_data_changed``.
    """
    if header_form_changed is not None:
        header_data_changed = header_form_changed
    if not had_script_generated:
        return False
    if not header_data_changed and not auto_key_edit_will_mutate(header, cleaned_data):
        return False

    HeaderTable.objects.filter(pk=header.pk).update(
        script_generated=False,
        script_date=None,
    )
    return True
