"""Validaciones de negocio para diseño de tablas (cabecera y, más adelante, detalle)."""

from __future__ import annotations

import re
from typing import Any

from apps.table_design.models import HeaderTable

# Convenciones de nombre de cabecera (más estrictas que max_length del modelo).
MIN_TABLE_NAME_LONG_LEN = 10
MAX_TABLE_NAME_LONG_LEN = 50
MIN_TABLE_NAME_SHORT_LEN = 8
MAX_TABLE_NAME_SHORT_LEN = 10
MAX_SCHEMA_LEN = 10

# Campos de detalle (DetailTable): validate_field, validate_order_key, duplicados — pantalla futura.

_LONG_NAME_RE = re.compile(
    rf"^[A-Za-z_]{{{MIN_TABLE_NAME_LONG_LEN},{MAX_TABLE_NAME_LONG_LEN}}}$"
)
_SHORT_NAME_RE = re.compile(
    rf"^[A-Z0-9]{{{MIN_TABLE_NAME_SHORT_LEN},{MAX_TABLE_NAME_SHORT_LEN}}}$"
)

MAX_PK_CONSTRAINT_NAME_LEN = 30
MAX_RECORD_FORMAT_NAME_LEN = 30
_PK_CONSTRAINT_RE = re.compile(r"^[A-Z0-9_]+$")
_RECORD_FORMAT_RE = re.compile(r"^[A-Z0-9_]+$")


def validate_pk_constraint_name_unique(
    *,
    pk_constraint_name: str | None,
    exclude_header_pk: int | None = None,
) -> dict[str, Any]:
    """Unicidad global de nombre de restricción PK (solo filas con valor no nulo)."""
    field_errors: dict[str, list[str]] = {}
    if not pk_constraint_name:
        return {"ok": True, "field_errors": field_errors}

    name = pk_constraint_name.strip().upper()
    if not name:
        return {"ok": True, "field_errors": field_errors}

    qs = HeaderTable.objects.filter(pk_constraint_name__iexact=name)
    if exclude_header_pk is not None:
        qs = qs.exclude(pk=exclude_header_pk)
    if qs.exists():
        field_errors.setdefault("pk_constraint_name", []).append(
            "Ya existe otra cabecera con este nombre de restricción PK. Elija otro nombre."
        )
    return {"ok": len(field_errors) == 0, "field_errors": field_errors}


def validate_header_ddl_options(
    *,
    pk_constraint_name: str | None,
    record_format_name: str | None,
) -> dict[str, Any]:
    """Valida campos opcionales de script DDL en cabecera (IBM i), sin parámetros IDENTITY."""
    field_errors: dict[str, list[str]] = {}
    normalized: dict[str, Any] = {}

    if pk_constraint_name:
        name = pk_constraint_name.strip().upper()
        if not name:
            normalized["pk_constraint_name"] = None
        elif len(name) > MAX_PK_CONSTRAINT_NAME_LEN:
            field_errors.setdefault("pk_constraint_name", []).append(
                f"El nombre de restricción PK no puede superar {MAX_PK_CONSTRAINT_NAME_LEN} caracteres."
            )
        elif not _PK_CONSTRAINT_RE.match(name):
            field_errors.setdefault("pk_constraint_name", []).append(
                "Solo se permiten letras mayúsculas, dígitos y guion bajo (_)."
            )
        else:
            normalized["pk_constraint_name"] = name
    else:
        normalized["pk_constraint_name"] = None

    if record_format_name:
        rf = record_format_name.strip().upper()
        if not rf:
            normalized["record_format_name"] = None
        elif len(rf) > MAX_RECORD_FORMAT_NAME_LEN:
            field_errors.setdefault("record_format_name", []).append(
                f"El nombre de formato de registro no puede superar {MAX_RECORD_FORMAT_NAME_LEN} caracteres."
            )
        elif not _RECORD_FORMAT_RE.match(rf):
            field_errors.setdefault("record_format_name", []).append(
                "Solo se permiten letras mayúsculas, dígitos y guion bajo (_)."
            )
        else:
            normalized["record_format_name"] = rf
    else:
        normalized["record_format_name"] = None

    return {
        "ok": len(field_errors) == 0,
        "field_errors": field_errors,
        "normalized": normalized,
    }


def validate_auto_key_config(
    *,
    identity_start: int | None,
    identity_increment: int | None,
    identity_cache: int | None,
    identity_cycle: bool,
) -> dict[str, Any]:
    """Valida parámetros globales de GENERATED AS IDENTITY (tabla hija 1:1)."""
    field_errors: dict[str, list[str]] = {}
    normalized: dict[str, Any] = {}

    if identity_start is not None and identity_start < 1:
        field_errors.setdefault("identity_start", []).append(
            "El valor inicial de identidad debe ser mayor o igual que 1."
        )
    if identity_increment is not None and identity_increment < 1:
        field_errors.setdefault("identity_increment", []).append(
            "El incremento de identidad debe ser mayor o igual que 1."
        )
    if identity_cache is not None and identity_cache < 1:
        field_errors.setdefault("identity_cache", []).append(
            "La caché de identidad debe ser mayor o igual que 1."
        )

    normalized["identity_start"] = identity_start
    normalized["identity_increment"] = identity_increment
    normalized["identity_cache"] = identity_cache
    normalized["identity_cycle"] = bool(identity_cycle)

    return {
        "ok": len(field_errors) == 0,
        "field_errors": field_errors,
        "normalized": normalized,
    }


def validate_header_table(
    *,
    table_name_long: str,
    table_name_short: str,
    schema: str | None,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Reglas de formato para alta/edición de cabecera (más estrictas que los límites de BD).

    ``schema``: tras strip en el caller; debe ser **no vacío** (obligatorio en alta/edición).
    ``notes``: opcional; el modelo es TextField sin tope explícito en BD.

    Devuelve ``field_errors`` con claves de campo del formulario Django para usar ``add_error``.
    """
    field_errors: dict[str, list[str]] = {}

    if (
        len(table_name_long) < MIN_TABLE_NAME_LONG_LEN
        or len(table_name_long) > MAX_TABLE_NAME_LONG_LEN
    ):
        field_errors.setdefault("table_name_long", []).append(
            f"El nombre largo debe tener entre {MIN_TABLE_NAME_LONG_LEN} y "
            f"{MAX_TABLE_NAME_LONG_LEN} caracteres "
            "(solo letras ASCII y guion bajo)."
        )
    elif not _LONG_NAME_RE.match(table_name_long):
        field_errors.setdefault("table_name_long", []).append(
            "El nombre largo solo puede contener letras A-Z, a-z y guion bajo (_)."
        )

    if (
        len(table_name_short) < MIN_TABLE_NAME_SHORT_LEN
        or len(table_name_short) > MAX_TABLE_NAME_SHORT_LEN
    ):
        field_errors.setdefault("table_name_short", []).append(
            f"El nombre corto debe tener entre {MIN_TABLE_NAME_SHORT_LEN} y "
            f"{MAX_TABLE_NAME_SHORT_LEN} caracteres "
            "(letras mayúsculas A–Z y dígitos 0–9)."
        )
    elif not _SHORT_NAME_RE.match(table_name_short):
        field_errors.setdefault("table_name_short", []).append(
            "El nombre corto solo puede contener letras mayúsculas (A–Z) y dígitos (0–9), "
            "sin espacios ni otros símbolos."
        )

    if schema is None or schema == "":
        field_errors.setdefault("schema", []).append(
            "El esquema / librería es obligatorio."
        )
    elif len(schema) > MAX_SCHEMA_LEN:
        field_errors.setdefault("schema", []).append(
            f"El esquema / librería no puede superar {MAX_SCHEMA_LEN} caracteres "
            "(coherente con el modelo de datos)."
        )

    if notes is not None and notes != "":
        pass  # Reservado si en el futuro hay límite de negocio sobre notas.

    ok = len(field_errors) == 0
    return {"ok": ok, "field_errors": field_errors}


def validate_header_duplicates(
    company_id: int,
    table_name_long: str,
    table_name_short: str,
) -> dict[str, Any]:
    """Unicidad por compañía: nombre largo y nombre corto (comparación case-insensitive)."""
    field_errors: dict[str, list[str]] = {}
    if HeaderTable.objects.filter(
        company_id=company_id,
        table_name_long__iexact=table_name_long,
    ).exists():
        field_errors.setdefault("table_name_long", []).append(
            "Ya existe una cabecera con el mismo nombre largo en su compañía."
        )
    if HeaderTable.objects.filter(
        company_id=company_id,
        table_name_short__iexact=table_name_short,
    ).exists():
        field_errors.setdefault("table_name_short", []).append(
            "Ya existe una cabecera con el mismo nombre corto en su compañía."
        )
    ok = len(field_errors) == 0
    return {"ok": ok, "field_errors": field_errors}


def validate_header_duplicates_edit(
    company_id: int,
    exclude_pk: int,
    table_name_long: str,
    table_name_short: str,
) -> dict[str, Any]:
    """Unicidad por compañía excluyendo la cabecera que se está editando."""
    field_errors: dict[str, list[str]] = {}
    base = HeaderTable.objects.filter(company_id=company_id)
    if base.filter(table_name_long__iexact=table_name_long).exclude(pk=exclude_pk).exists():
        field_errors.setdefault("table_name_long", []).append(
            "Ya existe otra cabecera con el mismo nombre largo en su compañía."
        )
    if base.filter(table_name_short__iexact=table_name_short).exclude(pk=exclude_pk).exists():
        field_errors.setdefault("table_name_short", []).append(
            "Ya existe otra cabecera con el mismo nombre corto en su compañía."
        )
    ok = len(field_errors) == 0
    return {"ok": ok, "field_errors": field_errors}
