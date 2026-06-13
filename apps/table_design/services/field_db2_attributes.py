"""Persistencia de atributos DB2 por columna (1:1 con DetailTable)."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from apps.table_design.models import DetailTable, DetailTableDb2Attributes
from apps.table_design.services.db2_attributes_ui import DB2_UI_FIELD_KEYS

UI_MANAGED_FIELDS: frozenset[str] = DB2_UI_FIELD_KEYS

DB2_ATTR_FIELD_NAMES: tuple[str, ...] = (
    *UI_MANAGED_FIELDS,
    "is_identity",
    "signed",
    "default_value",
    "is_indexed",
    "identity_generation",
    "generated_kind",
    "is_row_change_timestamp",
    "is_generated_rowid",
    "associated_trigger_name",
    "security_label",
    "temporal_role",
)

_ATTR_DEFAULTS: dict[str, Any] = {
    "ccsid": None,
    "is_hidden": False,
    "default_sql_expression": None,
    "nullable": True,
    "default_value": None,
    "is_unique": False,
    "check_constraint_sql": "",
    "generated_kind": DetailTableDb2Attributes.GeneratedKind.NONE,
    "generated_expression": "",
    "fieldproc_program": "",
    "for_bit_data": False,
    "compress_mode": DetailTableDb2Attributes.CompressMode.NONE,
    "mask_function": "",
    "user_defined_field": "",
}


def persist_field_db2_attributes(
    detail: DetailTable,
    *,
    cleaned_data: dict[str, Any],
    user: AbstractBaseUser | None = None,
) -> DetailTableDb2Attributes:
    """Compatibilidad con formulario monolítico legacy."""
    selected = {name for name in UI_MANAGED_FIELDS if name in cleaned_data}
    return persist_field_db2_attributes_from_form(
        detail,
        cleaned_data=cleaned_data,
        selected=selected,
        user=user,
        user_defined_only=False,
    )


def persist_field_db2_attributes_from_form(
    detail: DetailTable,
    *,
    cleaned_data: dict[str, Any],
    selected: set[str],
    user: AbstractBaseUser | None = None,
    user_defined_only: bool = False,
) -> DetailTableDb2Attributes:
    """Crea o actualiza atributos según filas activas en el paso 2."""
    defaults: dict[str, Any] = {}
    if user is not None:
        defaults["created_by"] = user
        defaults["updated_by"] = user

    attrs, created = DetailTableDb2Attributes.objects.get_or_create(
        detail=detail,
        defaults=defaults,
    )

    if user_defined_only:
        _reset_ui_managed(attrs)
        attrs.user_defined_field = (cleaned_data.get("user_defined_field") or "").strip()
    elif not selected:
        _reset_ui_managed(attrs)
    else:
        _reset_ui_managed(attrs)
        _apply_selected(attrs, cleaned_data, selected)

    if user is not None:
        if created and attrs.created_by_id is None:
            attrs.created_by = user
        attrs.updated_by = user

    attrs.full_clean()
    attrs.save()
    return attrs


def _reset_ui_managed(attrs: DetailTableDb2Attributes) -> None:
    for name, value in _ATTR_DEFAULTS.items():
        setattr(attrs, name, value)


def _apply_selected(
    attrs: DetailTableDb2Attributes,
    cleaned_data: dict[str, Any],
    selected: set[str],
) -> None:
    if "ccsid" in selected:
        attrs.ccsid = cleaned_data.get("ccsid")

    if "is_hidden" in selected:
        attrs.is_hidden = True

    if "default_sql_expression" in selected:
        expr = (cleaned_data.get("default_sql_expression") or "").strip()
        attrs.default_sql_expression = expr or None

    if "nullable" in selected:
        mode = cleaned_data.get("nullable_mode") or ""
        if mode == "null":
            attrs.nullable = True
        else:
            attrs.nullable = False
            if mode == "not_null_default" and not attrs.default_sql_expression:
                attrs.default_sql_expression = (
                    (cleaned_data.get("default_sql_expression") or "").strip() or None
                )

    if "is_unique" in selected:
        attrs.is_unique = True

    if "check_constraint_sql" in selected:
        attrs.check_constraint_sql = (
            cleaned_data.get("check_constraint_sql") or ""
        ).strip()

    if "generated_expression" in selected:
        expr = (cleaned_data.get("generated_expression") or "").strip()
        attrs.generated_expression = expr
        attrs.generated_kind = DetailTableDb2Attributes.GeneratedKind.EXPRESSION

    if "fieldproc_program" in selected:
        attrs.fieldproc_program = (
            cleaned_data.get("fieldproc_program") or ""
        ).strip()

    if "for_bit_data" in selected:
        attrs.for_bit_data = True

    if "compress_mode" in selected:
        mode = cleaned_data.get("compress_mode") or ""
        if mode:
            attrs.compress_mode = mode

    if "mask_function" in selected:
        attrs.mask_function = (cleaned_data.get("mask_function") or "").strip()

    if "user_defined_field" in selected:
        attrs.user_defined_field = (
            cleaned_data.get("user_defined_field") or ""
        ).strip()
