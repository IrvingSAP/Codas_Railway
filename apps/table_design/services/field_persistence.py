"""Persistencia de ``DetailTable`` con ``OperationResult``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from apps.core.services.operation_messages import ErrorCode
from apps.core.services.operation_result import OperationResult, safe_operation
from apps.table_design.models import DetailTable, HeaderTable
from apps.table_design.services.field_order import normalize_order_reg
from apps.table_design.services.field_validation import sync_header_is_field_key
from apps.table_design.services.table_design_messages import (
    MSG_FIELD_CREATED,
    MSG_FIELD_DELETED,
    MSG_FIELD_NAME_DUPLICATE,
    MSG_FIELD_UPDATED,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def _enrich_field_duplicate_result(result: OperationResult) -> OperationResult:
    if result.ok or result.error_code != ErrorCode.DUPLICATE:
        return result
    return OperationResult.failure(
        error_code=result.error_code,
        error_message=result.error_message,
        field_errors={"field_name_short": [MSG_FIELD_NAME_DUPLICATE]},
    )


def create_detail_field(
    field: DetailTable,
    *,
    header: HeaderTable,
) -> OperationResult:
    """Crea un campo y sincroniza ``is_field_key`` en la cabecera."""
    def _persist() -> DetailTable:
        with transaction.atomic():
            field.full_clean()
            field.save()
        sync_header_is_field_key(header)
        return field

    result = safe_operation(
        _persist,
        context="table_design.field.create",
        success_message=MSG_FIELD_CREATED,
    )
    return _enrich_field_duplicate_result(result)


def update_detail_field(
    field: DetailTable,
    *,
    header: HeaderTable,
) -> OperationResult:
    """Actualiza un campo y sincroniza ``is_field_key`` en la cabecera."""
    def _persist() -> DetailTable:
        with transaction.atomic():
            field.full_clean()
            field.save()
        sync_header_is_field_key(header)
        return field

    result = safe_operation(
        _persist,
        context="table_design.field.update",
        success_message=MSG_FIELD_UPDATED,
    )
    return _enrich_field_duplicate_result(result)


def delete_detail_field(
    field: DetailTable,
    *,
    header: HeaderTable,
) -> OperationResult:
    """Elimina un campo, normaliza orden y sincroniza cabecera."""
    field_pk = field.pk

    def _persist() -> int:
        with transaction.atomic():
            field.delete()
            normalize_order_reg(header)
        sync_header_is_field_key(header)
        return field_pk

    return safe_operation(
        _persist,
        context="table_design.field.delete",
        success_message=MSG_FIELD_DELETED,
    )
