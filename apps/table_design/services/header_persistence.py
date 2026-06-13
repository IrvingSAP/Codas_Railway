"""Persistencia de ``HeaderTable`` con ``OperationResult``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.core.services.operation_messages import ErrorCode
from apps.core.services.operation_result import OperationResult, safe_operation
from apps.table_design.models import HeaderTable
from apps.table_design.services.auto_key_config import persist_auto_key_from_cleaned
from apps.table_design.services.header_script_state import (
    apply_script_invalidation_on_header_edit,
)
from apps.table_design.services.table_design_messages import (
    MSG_HEADER_CREATED,
    MSG_HEADER_DUPLICATE,
    MSG_HEADER_UPDATED,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def _enrich_header_duplicate_result(result: OperationResult) -> OperationResult:
    if result.ok or result.error_code != ErrorCode.DUPLICATE:
        return result
    return OperationResult.failure(
        error_code=result.error_code,
        error_message=result.error_message,
        field_errors={"__all__": [MSG_HEADER_DUPLICATE]},
    )


def create_header_table(
    header: HeaderTable,
    *,
    cleaned_data: dict[str, Any],
    user: AbstractUser,
) -> OperationResult:
    """Alta de cabecera + configuración IDENTITY opcional."""
    def _persist() -> HeaderTable:
        with transaction.atomic():
            header.save()
            persist_auto_key_from_cleaned(header, cleaned_data, user=user)
            return header

    result = safe_operation(
        _persist,
        context="table_design.header.create",
        success_message=MSG_HEADER_CREATED,
    )
    return _enrich_header_duplicate_result(result)


def update_header_table(
    candidate: HeaderTable,
    *,
    cleaned_data: dict[str, Any],
    user: AbstractUser,
    had_script_generated: bool,
) -> OperationResult:
    """
    Actualización de cabecera.

    Si tenía ``script_generated=True``, tras un guardado exitoso pasa a ``False``
    y ``script_date`` queda en ``None`` (el script DDL debe regenerarse).
    """
    candidate.updated_by = user
    apply_script_invalidation_on_header_edit(
        candidate,
        had_script_generated=had_script_generated,
    )

    def _persist() -> HeaderTable:
        with transaction.atomic():
            candidate.save()
            persist_auto_key_from_cleaned(candidate, cleaned_data, user=user)
            return candidate

    result = safe_operation(
        _persist,
        context="table_design.header.update",
        success_message=MSG_HEADER_UPDATED,
    )
    return _enrich_header_duplicate_result(result)
