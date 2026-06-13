"""Validación del asistente DLT (DELETE / baja lógica)."""

from __future__ import annotations

import re

from apps.sp_asistido.models import SPCondition
from apps.table_design.models import DetailTable

_IN_PARAM_RE = re.compile(r"^P_[A-Z0-9_#]+$", re.IGNORECASE)

_ALLOWED_OPERATORS = frozenset({"=", "<>"})


def validate_where_row(
    detail_field_id: int | None,
    operator: str,
    value_origin: str,
    value_text: str,
    *,
    header_id: int,
) -> list[str]:
    """Una fila WHERE obligatoria (D.3 / D.8)."""
    errors: list[str] = []
    if not detail_field_id:
        errors.append("Seleccione un campo para la condición WHERE.")
        return errors
    if not DetailTable.objects.filter(
        pk=detail_field_id, header_id=header_id, status=DetailTable.Status.ACTIVE
    ).exists():
        errors.append("El campo seleccionado no es válido para esta tabla.")
        return errors
    op = (operator or "").strip()
    if op not in _ALLOWED_OPERATORS:
        errors.append("Operador no permitido (use = o <>).")
    vo = (value_origin or "").strip().upper()
    if vo not in ("IN", "LITERAL"):
        errors.append("Origen del valor: use IN o LITERAL.")
    vt = (value_text or "").strip()
    if not vt:
        errors.append("El valor o parámetro IN no puede quedar vacío.")
    elif vo == "IN" and not _IN_PARAM_RE.match(vt):
        errors.append("Nombre de parámetro IN inválido (prefijo P_, letras/números/_/#).")
    return errors


def validate_dlt_mode_payload(
    mode: str,
    logical_field: str,
    logical_value: str,
    *,
    header_id: int,
) -> list[str]:
    """Paso modo físico vs lógico (D.4)."""
    errors: list[str] = []
    m = (mode or "").strip().lower()
    if m not in ("fisico", "logico"):
        errors.append("Seleccione modo físico o lógico.")
        return errors
    if m == "logico":
        f = (logical_field or "").strip().upper()
        v = (logical_value or "").strip()
        if not f or not v:
            errors.append("En modo lógico, campo de estado y valor son obligatorios.")
            return errors
        if not DetailTable.objects.filter(
            header_id=header_id,
            field_name_short__iexact=f,
            status=DetailTable.Status.ACTIVE,
        ).exists():
            errors.append("El campo de estado no existe en el detalle de esta cabecera.")
    return errors


def definition_has_where_clause(definition) -> bool:
    """D.8: no generar DELETE/UPDATE sin al menos una condición WHERE persistida."""
    return definition.conditions.filter(
        clause_kind=SPCondition.ClauseKind.WHERE
    ).exists()
