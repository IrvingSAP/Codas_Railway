"""Helpers de datos de prueba para table_design."""

from __future__ import annotations

from typing import Any

from apps.table_design.models import DetailTable, DetailTableDb2Attributes, HeaderTable
from apps.table_design.services.field_db2_attributes import DB2_ATTR_FIELD_NAMES


def create_detail_field_core_only(
    header: HeaderTable,
    order_reg: int,
    **kwargs: Any,
) -> DetailTable:
    """Solo ``DetailTable`` (paso 1 del flujo); sin fila ``DetailTableDb2Attributes``."""
    return DetailTable.objects.create(
        header=header,
        order_reg=order_reg,
        **kwargs,
    )


def create_detail_field(
    header: HeaderTable,
    order_reg: int,
    **kwargs: Any,
) -> DetailTable:
    """
    Crea ``DetailTable`` + ``DetailTableDb2Attributes`` (paso 1 y 2 completos).

    Usar cuando el test necesite NULL/DEFAULT/IDENTITY/CCSID/hidden en el DDL.
    Para campos solo en paso 1, usar ``create_detail_field_core_only``.
    """
    db2_kwargs: dict[str, Any] = {}
    for name in DB2_ATTR_FIELD_NAMES:
        if name in kwargs:
            db2_kwargs[name] = kwargs.pop(name)
    detail = DetailTable.objects.create(
        header=header,
        order_reg=order_reg,
        **kwargs,
    )
    if "nullable" not in db2_kwargs:
        db2_kwargs.setdefault("nullable", True)
    DetailTableDb2Attributes.objects.create(detail=detail, **db2_kwargs)
    return detail
