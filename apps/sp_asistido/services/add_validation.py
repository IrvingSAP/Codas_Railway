"""Validación por paso del asistente ADD (checklist C.3–C.5)."""

from __future__ import annotations

import re
from typing import Any

from django.db.models import QuerySet

from apps.sp_asistido.models import SPAssignment, SPDefinition
from apps.table_design.models import DetailTable, HeaderTable


# Identificadores IBM i / CODAS (alineado a prototipos HTML)
_SCHEMA_RE = re.compile(r"^[A-Za-z0-9#]{1,10}$")
_NAME_SHORT_RE = re.compile(r"^[A-Za-z0-9_#]{1,10}$")


def validate_step1_identification(
    schema_name: str,
    procedure_name_short: str,
    procedure_name_long: str,
    procedure_comment: str,
    *,
    company_id: int | None = None,
    exclude_definition_pk: int | None = None,
) -> list[str]:
    """Devuelve lista de mensajes de error (vacía si OK)."""
    errors: list[str] = []
    schema_name = (schema_name or "").strip()
    procedure_name_short = (procedure_name_short or "").strip()
    procedure_name_long = (procedure_name_long or "").strip()
    procedure_comment = (procedure_comment or "").strip()

    if not schema_name:
        errors.append("Indique el esquema / librería.")
    elif not _SCHEMA_RE.match(schema_name):
        errors.append(
            "Esquema / librería: máximo 10 caracteres; solo letras, dígitos y #."
        )

    if not procedure_name_short:
        errors.append("Indique el nombre corto del SP.")
    elif not _NAME_SHORT_RE.match(procedure_name_short):
        errors.append(
            "Nombre corto SP: máximo 10 caracteres; letras, dígitos, _ y #."
        )

    if not procedure_name_long:
        errors.append("Indique el nombre largo (descriptivo).")
    elif len(procedure_name_long) > 50:
        errors.append("El nombre largo admite como máximo 50 caracteres.")

    if len(procedure_comment) > 200:
        errors.append("El comentario admite como máximo 200 caracteres.")

    if not errors and company_id:
        short_qs = SPDefinition.objects.filter(
            company_id=company_id,
            procedure_name_short__iexact=procedure_name_short,
        )
        if exclude_definition_pk is not None:
            short_qs = short_qs.exclude(pk=exclude_definition_pk)
        if short_qs.exists():
            errors.append(
                "El nombre corto del SP ya está registrado en su compañía."
            )
        long_qs = SPDefinition.objects.filter(
            company_id=company_id,
            procedure_name_long__iexact=procedure_name_long,
        )
        if exclude_definition_pk is not None:
            long_qs = long_qs.exclude(pk=exclude_definition_pk)
        if long_qs.exists():
            errors.append(
                "El nombre largo del SP ya está registrado en su compañía."
            )

    return errors


def insertable_details_for_header(header_id: int) -> QuerySet[DetailTable]:
    """Columnas candidatas a INSERT: detalle activo y no IDENTITY (C.3)."""
    return (
        DetailTable.objects.filter(
            header_id=header_id,
            status=DetailTable.Status.ACTIVE,
            is_identity=False,
        )
        .select_related("header")
        .order_by("order_reg", "id")
    )


def header_belongs_to_company(header_id: int, company_id: int) -> bool:
    return HeaderTable.objects.filter(
        pk=header_id, company_id=company_id
    ).exists()


def normalize_selected_field_ids(raw_ids: list[Any]) -> list[int]:
    out: list[int] = []
    for x in raw_ids:
        try:
            i = int(x)
        except (TypeError, ValueError):
            continue
        if i > 0 and i not in out:
            out.append(i)
    return out


def validate_step3_columns(
    selected_ids: list[int], header_id: int, company_id: int
) -> tuple[list[int], list[str]]:
    """
    Comprueba que todos los ids pertenecen a columnas insertables de la cabecera.
    Devuelve (ids_válidos_ordenados, errores).
    """
    errors: list[str] = []
    if not selected_ids:
        return [], ["Seleccione al menos una columna para INSERT."]

    if not header_belongs_to_company(header_id, company_id):
        return [], ["La tabla de diseño no pertenece a su compañía."]

    allowed = set(
        insertable_details_for_header(header_id).values_list("id", flat=True)
    )
    bad = [i for i in selected_ids if i not in allowed]
    if bad:
        errors.append("Hay columnas no válidas o no insertables en la selección.")

    valid = [i for i in selected_ids if i in allowed]
    return valid, errors


def validate_source_detail_rule(
    source_kind: str, source_value: str
) -> str | None:
    """
    Reglas C.4: NULL → detalle vacío; IN / LITERAL / EXPR → detalle obligatorio.
    Devuelve mensaje de error o None.
    """
    v = (source_value or "").strip()
    if source_kind == SPAssignment.SourceKind.NULL:
        if v:
            return "Si el origen es NULL, el detalle debe quedar vacío."
        return None
    if source_kind in (
        SPAssignment.SourceKind.IN_PARAM,
        SPAssignment.SourceKind.LITERAL,
        SPAssignment.SourceKind.EXPR,
    ):
        if not v:
            return (
                "Si el origen es parámetro IN, literal o expresión SQL, "
                "el detalle no puede quedar vacío."
            )
        return None
    return "Origen de valor no reconocido."


def validate_not_null_with_null_origin(
    details: dict[int, DetailTable], assignments: list[tuple[int, str, str]]
) -> list[str]:
    """
    assignments: lista (detail_field_id, source_kind, source_value).
    Columnas NOT NULL no pueden usar origen NULL (C.5).
    """
    errors: list[str] = []
    for fid, sk, _ in assignments:
        d = details.get(fid)
        if not d:
            continue
        if not d.nullable and sk == SPAssignment.SourceKind.NULL:
            errors.append(
                f"La columna {d.field_name_short} es obligatoria (NOT NULL) "
                "y no admite origen NULL."
            )
    return errors


def suggested_specific_name(procedure_name_short: str) -> str:
    """Nombre interno SPECIFIC conservador (≤18) para mostrar en firma."""
    base = (procedure_name_short or "").strip().upper()[:10] or "SP"
    suffix = "SP1"
    combined = f"{base}{suffix}"
    return combined[:18]
