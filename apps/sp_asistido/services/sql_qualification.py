"""Calificación de objetos en SQL de SP (alineable a `table_design` / CODAS_TABLE_DESIGN §9.11)."""

from __future__ import annotations

from typing import Literal

SpQualificationStyle = Literal["dot", "slash", "mixed"]


def default_sp_qualification_style() -> SpQualificationStyle:
    """
    Estilo de calificación en cuerpos SQL de SP (DML y `CREATE OR REPLACE PROCEDURE`).

    Convención paralela a ``table_design.services.sql_script`` (separadores
    «dot» / «slash» / «mixed»): en SP Asistido, **mixed** se aplica al cuerpo
    SQL con el mismo separador que **dot** (punto), coherente con el DDL de
    ``CREATE TABLE`` en table_design; el estilo **slash** usa ``/`` entre
    librería y objeto (IBM i).
    """
    return "dot"


def _separator_for_style(style: SpQualificationStyle) -> str:
    if style == "slash":
        return "/"
    return "."


def sp_qualified_table_dml(
    schema: str,
    table_name_short: str,
    *,
    style: SpQualificationStyle | None = None,
) -> str:
    """
    Nombre de tabla en DML (p. ej. ``INSERT INTO lib.tab``).

    Si ``schema`` está vacío, devuelve solo el nombre de tabla en mayúsculas.
    """
    st = style or default_sp_qualification_style()
    sch = (schema or "").strip().upper()
    t = (table_name_short or "").strip().upper()
    if not t:
        return t
    if not sch:
        return t
    return f"{sch}{_separator_for_style(st)}{t}"


def sp_qualified_procedure_target(
    schema: str,
    procedure_name_long: str,
    *,
    style: SpQualificationStyle | None = None,
) -> str:
    """
    Nombre inmediatamente posterior a ``CREATE OR REPLACE PROCEDURE`` (librería + SP).
    """
    return sp_qualified_table_dml(
        schema,
        procedure_name_long,
        style=style,
    )
