"""Validación de payloads de `DetailTable` (tipos DB2, duplicados, orden de llave)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from apps.table_design.models import DetailTable, HeaderTable

# Reglas de negocio para nombres de campo (alineadas al diseño previo IBM i).
MIN_FIELD_NAME_LONG_LEN = 10
MAX_FIELD_NAME_LONG_LEN = 30
MIN_FIELD_NAME_SHORT_LEN = 8
MAX_FIELD_NAME_SHORT_LEN = 10

FIELD_NAME_SHORT_PATTERN = re.compile(r"^[A-Z0-9]+$")
FIELD_NAME_LONG_PATTERN = re.compile(r"^[A-Z0-9_]+$")

# Tipos con longitud fija en modelo (field_length debe coincidir al persistir).
FIXED_LENGTH_BY_TYPE: dict[str, int] = {
    DetailTable.FieldDB2Type.SMALLINT: 2,
    DetailTable.FieldDB2Type.INTEGER: 4,
    DetailTable.FieldDB2Type.BIGINT: 8,
    DetailTable.FieldDB2Type.REAL: 4,
    DetailTable.FieldDB2Type.DOUBLE: 8,
    DetailTable.FieldDB2Type.DATE: 4,
    DetailTable.FieldDB2Type.TIME: 3,
    DetailTable.FieldDB2Type.TIMESTAMP: 26,
    DetailTable.FieldDB2Type.ROWID: 17,
}

LENGTH_REQUIRED_TYPES: frozenset[str] = frozenset(
    {
        DetailTable.FieldDB2Type.CHAR,
        DetailTable.FieldDB2Type.VARCHAR,
        DetailTable.FieldDB2Type.GRAPHIC,
        DetailTable.FieldDB2Type.VARGRAPHIC,
        DetailTable.FieldDB2Type.BINARY,
        DetailTable.FieldDB2Type.VARBINARY,
    }
)

DECIMAL_TYPES: frozenset[str] = frozenset(
    {
        DetailTable.FieldDB2Type.DECIMAL,
        DetailTable.FieldDB2Type.NUMERIC,
    }
)

NO_LENGTH_TYPES: frozenset[str] = frozenset(
    {
        DetailTable.FieldDB2Type.CLOB,
        DetailTable.FieldDB2Type.BLOB,
        DetailTable.FieldDB2Type.XML,
        DetailTable.FieldDB2Type.DECFLOAT,
    }
)

# ALLOCATE(n) en DB2 for i: obligatorio para VARCHAR/VARGRAPHIC (p. ej. VARCHAR(300) ALLOCATE(270)).
ALLOCATE_REQUIRED_TYPES: frozenset[str] = frozenset(
    {
        DetailTable.FieldDB2Type.VARCHAR,
        DetailTable.FieldDB2Type.VARGRAPHIC,
    }
)

# IDENTITY: tipos de columna habituales en DB2 for i.
IDENTITY_FIELD_TYPES: frozenset[str] = frozenset(
    {
        DetailTable.FieldDB2Type.SMALLINT,
        DetailTable.FieldDB2Type.INTEGER,
        DetailTable.FieldDB2Type.BIGINT,
    }
)

# CCSID en sentencias: tipos de texto frecuentes.
CCSID_FIELD_TYPES: frozenset[str] = frozenset(
    {
        DetailTable.FieldDB2Type.CHAR,
        DetailTable.FieldDB2Type.VARCHAR,
        DetailTable.FieldDB2Type.GRAPHIC,
        DetailTable.FieldDB2Type.VARGRAPHIC,
        DetailTable.FieldDB2Type.CLOB,
    }
)

NUMERIC_DEFAULT_FIELD_TYPES: frozenset[str] = frozenset(
    {
        DetailTable.FieldDB2Type.SMALLINT,
        DetailTable.FieldDB2Type.INTEGER,
        DetailTable.FieldDB2Type.BIGINT,
        DetailTable.FieldDB2Type.DECIMAL,
        DetailTable.FieldDB2Type.NUMERIC,
        DetailTable.FieldDB2Type.DECFLOAT,
        DetailTable.FieldDB2Type.REAL,
        DetailTable.FieldDB2Type.DOUBLE,
    }
)

MAX_COLUMN_LABEL_LEN = 20
MAX_COLUMN_TEXT_LEN = 50
MAX_DEFAULT_VALUE_LEN = 50
MAX_DEFAULT_SQL_EXPRESSION_LEN = 200


def _parse_positive_int(value: Any, *, allow_zero: bool = False) -> int | None:
    if value is None or value == "":
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if n < 0:
        return None
    if not allow_zero and n == 0:
        return None
    return n


def _parse_nonneg_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if n < 0:
        return None
    return n


def validate_field_duplicates(
    header: HeaderTable,
    name_long: str,
    name_short: str,
    *,
    exclude_field_id: int | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    qs_long = header.fields.filter(field_name_long__iexact=name_long)
    qs_short = header.fields.filter(field_name_short__iexact=name_short)
    if exclude_field_id is not None:
        qs_long = qs_long.exclude(pk=exclude_field_id)
        qs_short = qs_short.exclude(pk=exclude_field_id)
    if qs_long.exists():
        errors.append("Ya existe un campo con el mismo nombre largo en esta tabla.")
    if qs_short.exists():
        errors.append("Ya existe un campo con el mismo nombre corto en esta tabla.")
    return {"ok": len(errors) == 0, "errors": errors}


def validate_order_key_among_key_fields(
    header: HeaderTable,
    order_key: int | None,
    *,
    is_key: bool,
    exclude_field_id: int | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not is_key:
        return {"ok": True, "errors": errors}
    if order_key is None or order_key < 1:
        errors.append("Si el campo es llave, indique un orden de llave mayor que cero.")
        return {"ok": False, "errors": errors}
    qs = header.fields.filter(
        is_key=True,
        order_key=order_key,
    ).exclude(status=DetailTable.Status.INACTIVE)
    if exclude_field_id is not None:
        qs = qs.exclude(pk=exclude_field_id)
    if qs.exists():
        errors.append(f"Ya existe otro campo llave con orden de llave {order_key}.")
    return {"ok": len(errors) == 0, "errors": errors}


def validate_single_identity_per_header(
    header: HeaderTable,
    *,
    exclude_field_id: int | None = None,
) -> dict[str, Any]:
    """Solo una columna IDENTITY activa por cabecera (p. ej. diseño SIMPLE incremental)."""
    errors: list[str] = []
    qs = header.fields.filter(
        is_identity=True,
        status=DetailTable.Status.ACTIVE,
    )
    if exclude_field_id is not None:
        qs = qs.exclude(pk=exclude_field_id)
    if qs.exists():
        errors.append(
            "Solo una columna por tabla puede ser IDENTITY. "
            "Desactive IDENTITY en el otro campo o use un campo inactivo."
        )
    return {"ok": len(errors) == 0, "errors": errors}


def validate_field_payload(
    *,
    header: HeaderTable,
    name_long: str,
    name_short: str,
    field_type: str,
    field_length: Any,
    decimal_places: Any,
    allocate_length: Any = None,
    nullable: bool,
    is_key: bool,
    order_key: Any,
    notes: str | None = None,
    exclude_field_id: int | None = None,
    is_identity: bool = False,
    is_hidden: bool = False,
    ccsid: Any = None,
    column_label: str | None = None,
    column_text: str | None = None,
    default_value: str | None = None,
    default_sql_expression: str | None = None,
    signed: bool = True,
    is_unique: bool = False,
    is_indexed: bool = False,
) -> dict[str, Any]:
    """
    Validación de negocio antes de instanciar/guardar `DetailTable`.
    Retorno unificado: ``{"ok": bool, "errors": list[str], "normalized": dict | None}``.
    """
    errors: list[str] = []

    name_long = (name_long or "").strip()
    if name_long:
        name_long = re.sub(r"\s+", "_", name_long)
        name_long = name_long.replace("-", "_")
        name_long = name_long.upper()
    name_short = (name_short or "").strip().upper()
    if not name_long:
        errors.append("El nombre largo del campo es obligatorio.")
    elif len(name_long) < MIN_FIELD_NAME_LONG_LEN:
        errors.append(
            f"El nombre largo debe tener entre {MIN_FIELD_NAME_LONG_LEN} y "
            f"{MAX_FIELD_NAME_LONG_LEN} caracteres."
        )
    elif len(name_long) > MAX_FIELD_NAME_LONG_LEN:
        errors.append(
            f"El nombre largo no puede superar {MAX_FIELD_NAME_LONG_LEN} caracteres."
        )
    elif not FIELD_NAME_LONG_PATTERN.fullmatch(name_long):
        errors.append(
            "El nombre largo solo permite letras, números y guion bajo (_), sin espacios ni otros caracteres."
        )
    if not name_short:
        errors.append("El nombre corto del campo es obligatorio.")
    elif len(name_short) < MIN_FIELD_NAME_SHORT_LEN:
        errors.append(
            f"El nombre corto debe tener entre {MIN_FIELD_NAME_SHORT_LEN} y "
            f"{MAX_FIELD_NAME_SHORT_LEN} caracteres."
        )
    elif len(name_short) > MAX_FIELD_NAME_SHORT_LEN:
        errors.append(
            f"El nombre corto no puede superar {MAX_FIELD_NAME_SHORT_LEN} caracteres."
        )
    elif not FIELD_NAME_SHORT_PATTERN.fullmatch(name_short):
        errors.append(
            "El nombre corto solo permite letras y números, sin espacios ni otros caracteres."
        )

    notes_clean = (notes or "").strip()
    if not notes_clean:
        errors.append("Las notas son obligatorias.")

    choices = {c[0] for c in DetailTable.FieldDB2Type.choices}
    if field_type not in choices:
        errors.append("Seleccione un tipo de dato válido.")

    length = _parse_nonneg_int(field_length)
    decimals = _parse_nonneg_int(decimal_places)
    ok_key_order = _parse_positive_int(order_key, allow_zero=False) if is_key else None
    if is_key and ok_key_order is None:
        errors.append("Si el campo es llave, indique el orden de la llave (entero ≥ 1).")

    if errors:
        return {"ok": False, "errors": errors, "normalized": None}

    assert field_type in choices  # for type checker / flow

    normalized_length = length if length is not None else 0
    normalized_decimals: int | None = decimals if decimals is not None else None

    if field_type in FIXED_LENGTH_BY_TYPE:
        expected = FIXED_LENGTH_BY_TYPE[field_type]
        if length is not None and length not in (0, expected):
            errors.append(
                f"El tipo {field_type} tiene longitud fija {expected} "
                f"(deje longitud en blanco o use {expected})."
            )
        if decimals not in (None, 0):
            errors.append(f"El tipo {field_type} no admite decimales.")
        normalized_length = expected
        normalized_decimals = None

    elif field_type in LENGTH_REQUIRED_TYPES:
        if length is None or length < 1:
            errors.append(f"El tipo {field_type} requiere una longitud mayor que cero.")
        if decimals not in (None, 0):
            errors.append(f"El tipo {field_type} no admite decimales.")
        normalized_decimals = None

    elif field_type in DECIMAL_TYPES:
        if length is None or length < 1:
            errors.append(f"El tipo {field_type} requiere longitud (precisión).")
        if decimals is None:
            errors.append(f"El tipo {field_type} requiere decimales (escala).")
        elif length is not None and decimals is not None and decimals > length:
            errors.append("Los decimales no pueden ser mayores que la longitud (precisión).")

    elif field_type in NO_LENGTH_TYPES:
        if length not in (None, 0):
            errors.append(f"El tipo {field_type} no debe tener longitud.")
        if decimals not in (None, 0):
            errors.append(f"El tipo {field_type} no admite decimales.")
        normalized_length = 0
        normalized_decimals = None

    else:
        # Resto (p. ej. TIME, TIMESTAMP ya en FIXED; otros): sin longitud explícita
        if length not in (None, 0):
            errors.append(f"Para el tipo {field_type} use longitud 0 o en blanco.")
        if decimals not in (None, 0):
            errors.append(f"El tipo {field_type} no admite decimales.")
        normalized_length = 0
        normalized_decimals = None

    dup = validate_field_duplicates(
        header, name_long, name_short, exclude_field_id=exclude_field_id
    )
    if not dup["ok"]:
        errors.extend(dup["errors"])

    if is_key and ok_key_order is not None:
        ok_dup = validate_order_key_among_key_fields(
            header,
            ok_key_order,
            is_key=True,
            exclude_field_id=exclude_field_id,
        )
        if not ok_dup["ok"]:
            errors.extend(ok_dup["errors"])

    alloc_parsed = _parse_nonneg_int(allocate_length)
    normalized_allocate: int | None = None
    if field_type in ALLOCATE_REQUIRED_TYPES and normalized_length >= 1:
        if alloc_parsed is None or alloc_parsed < 1:
            errors.append(
                "Indique ALLOCATE (entero mayor que cero) para VARCHAR o VARGRAPHIC; "
                "es la suballocación (p. ej. VARCHAR(300) ALLOCATE(270))."
            )
        elif alloc_parsed > normalized_length:
            errors.append(
                "ALLOCATE no puede ser mayor que la longitud máxima de la columna "
                f"({normalized_length})."
            )
        else:
            normalized_allocate = alloc_parsed
    else:
        if field_type not in ALLOCATE_REQUIRED_TYPES and alloc_parsed is not None:
            errors.append("ALLOCATE solo aplica a tipos VARCHAR o VARGRAPHIC.")

    is_identity_f = bool(is_identity)
    is_hidden_f = bool(is_hidden)
    is_unique_f = bool(is_unique)
    is_indexed_f = bool(is_indexed)
    signed_f = bool(signed)

    if is_identity_f:
        if field_type not in IDENTITY_FIELD_TYPES:
            errors.append("IDENTITY solo aplica a tipos SMALLINT, INTEGER o BIGINT.")
        if nullable:
            errors.append(
                "Una columna IDENTITY debe ser NOT NULL. Desactive «Permite nulos»."
            )
        id1 = validate_single_identity_per_header(
            header, exclude_field_id=exclude_field_id
        )
        if not id1["ok"]:
            errors.extend(id1["errors"])
    ccsid_n: int | None = _parse_nonneg_int(ccsid) if ccsid not in (None, "") else None
    if ccsid is not None and ccsid != "" and ccsid_n is None:
        errors.append("CCSID debe ser un entero no negativo.")
    if ccsid_n is not None and field_type not in CCSID_FIELD_TYPES:
        errors.append(f"CCSID no aplica al tipo {field_type}.")

    col_lbl = (column_label or "").strip()
    if len(col_lbl) > MAX_COLUMN_LABEL_LEN:
        errors.append(
            f"La etiqueta de columna (LABEL ON COLUMN) no puede superar "
            f"{MAX_COLUMN_LABEL_LEN} caracteres."
        )
    col_txt = (column_text or "").strip()
    if len(col_txt) > MAX_COLUMN_TEXT_LEN:
        errors.append(
            f"El texto de columna (LABEL ON COLUMN … TEXT IS) no puede superar "
            f"{MAX_COLUMN_TEXT_LEN} caracteres."
        )
    col_text_norm: str | None = col_txt if col_txt else None

    dval_raw = "" if default_value in (None, "") else str(default_value).strip()
    dval_norm: str | None = dval_raw if dval_raw else None
    dsql_raw = (
        "" if default_sql_expression in (None, "") else str(default_sql_expression).strip()
    )
    dsql_norm: str | None = dsql_raw if dsql_raw else None
    if dval_norm and dsql_norm:
        errors.append("Use un valor por defecto literal o una expresión SQL, no ambos.")
    if dval_norm and len(dval_norm) > MAX_DEFAULT_VALUE_LEN:
        errors.append(
            f"El valor por defecto no puede superar {MAX_DEFAULT_VALUE_LEN} caracteres."
        )
    if dsql_norm and len(dsql_norm) > MAX_DEFAULT_SQL_EXPRESSION_LEN:
        errors.append(
            f"La expresión SQL por defecto no puede superar {MAX_DEFAULT_SQL_EXPRESSION_LEN} caracteres."
        )
    if is_identity_f and (dval_norm or dsql_norm):
        errors.append(
            "Una columna IDENTITY no debe llevar DEFAULT literal ni expresión; "
            "el valor lo genera la secuencia."
        )
    if dval_norm and field_type in NUMERIC_DEFAULT_FIELD_TYPES:
        try:
            Decimal(dval_norm)
        except (InvalidOperation, ValueError):
            errors.append(
                f"El valor por defecto literal para {field_type} debe ser numérico."
            )

    if errors:
        return {"ok": False, "errors": errors, "normalized": None}

    return {
        "ok": True,
        "errors": [],
        "normalized": {
            "field_name_long": name_long,
            "field_name_short": name_short,
            "field_type": field_type,
            "field_length": normalized_length,
            "decimal_places": normalized_decimals,
            "allocate_length": normalized_allocate,
            "nullable": nullable,
            "is_key": is_key,
            "order_key": ok_key_order if is_key else None,
            "notes": notes_clean,
            "is_identity": is_identity_f,
            "is_hidden": is_hidden_f,
            "ccsid": ccsid_n,
            "column_label": col_lbl,
            "column_text": col_text_norm,
            "default_value": dval_norm,
            "default_sql_expression": dsql_norm,
            "signed": signed_f,
            "is_unique": is_unique_f,
            "is_indexed": is_indexed_f,
        },
    }


def sync_header_is_field_key(header: HeaderTable) -> None:
    """Actualiza ``HeaderTable.is_field_key`` según existan campos llave activos."""
    has_key = header.fields.filter(
        is_key=True,
        status=DetailTable.Status.ACTIVE,
    ).exists()
    HeaderTable.objects.filter(pk=header.pk).update(is_field_key=has_key)
