"""
Persistencia de ``SPDefinition`` y confirmación de scripts con ``OperationResult``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.core.services.operation_messages import ErrorCode
from apps.core.services.operation_result import OperationResult, safe_operation
from apps.sp_asistido.models import SPDefinition, SPStepState
from apps.sp_asistido.services.sp_asistido_messages import (
    MSG_DEFINITION_REOPENED,
    MSG_DEFINITION_SAVED,
    MSG_PROCEDURE_SHORT_DUPLICATE_FIELD,
    draft_created_message,
    script_confirmed_message,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def upsert_step_state(
    definition: SPDefinition,
    step_number: int,
    payload: dict,
    user: AbstractUser,
) -> None:
    """Crea o actualiza snapshot JSON de un paso del wizard."""
    row, created = SPStepState.objects.get_or_create(
        sp_definition=definition,
        step_number=step_number,
        defaults={
            "payload_json": payload,
            "created_by": user if user.is_authenticated else None,
            "updated_by": user if user.is_authenticated else None,
        },
    )
    if not created:
        row.payload_json = payload
        row.updated_by = user if user.is_authenticated else None
        row.save(update_fields=["payload_json", "updated_at", "updated_by"])


def _enrich_procedure_short_duplicate(result: OperationResult) -> OperationResult:
    if result.ok or result.error_code != ErrorCode.DUPLICATE:
        return result
    return OperationResult.failure(
        error_code=result.error_code,
        error_message=result.error_message,
        field_errors={"procedure_name_short": [MSG_PROCEDURE_SHORT_DUPLICATE_FIELD]},
    )


def create_wizard_definition_draft(
    *,
    company_id: int,
    header_table_id: int,
    operation: str,
    step1_data: dict[str, Any],
    user: AbstractUser,
) -> OperationResult:
    """Paso 2 del wizard: crea ``SPDefinition`` en borrador y estados de paso 1 y 2."""
    schema_name = (step1_data.get("schema_name") or "").strip()
    procedure_name_short = (step1_data.get("procedure_name_short") or "").strip()
    procedure_name_long = (step1_data.get("procedure_name_long") or "").strip()
    procedure_comment = (step1_data.get("procedure_comment") or "").strip()

    def _persist() -> SPDefinition:
        with transaction.atomic():
            definition = SPDefinition.objects.create(
                company_id=company_id,
                header_table_id=header_table_id,
                operation=operation,
                schema_name=schema_name,
                procedure_name_short=procedure_name_short,
                procedure_name_long=procedure_name_long,
                procedure_comment=procedure_comment,
                status=SPDefinition.Status.DRAFT,
                current_step=2,
                created_by=user,
                updated_by=user,
            )
            upsert_step_state(
                definition,
                1,
                {k: v for k, v in step1_data.items()},
                user,
            )
            upsert_step_state(
                definition,
                2,
                {"header_table_id": header_table_id},
                user,
            )
            return definition

    result = safe_operation(
        _persist,
        context=f"sp_asistido.draft.create.{operation}",
        success_message=draft_created_message(operation),
    )
    return _enrich_procedure_short_duplicate(result)


def update_definition_identification(
    definition: SPDefinition,
    *,
    schema_name: str,
    procedure_name_short: str,
    procedure_name_long: str,
    procedure_comment: str,
    status: str,
    user: AbstractUser,
) -> OperationResult:
    """Actualiza metadatos de identificación desde ``definition_edit``."""
    def _persist() -> SPDefinition:
        with transaction.atomic():
            definition.schema_name = schema_name.strip()
            definition.procedure_name_short = procedure_name_short.strip()
            definition.procedure_name_long = procedure_name_long.strip()
            definition.procedure_comment = (procedure_comment or "").strip()
            definition.status = status
            definition.updated_by = user
            definition.save(
                update_fields=[
                    "schema_name",
                    "procedure_name_short",
                    "procedure_name_long",
                    "procedure_comment",
                    "status",
                    "updated_at",
                    "updated_by",
                ]
            )
            return definition

    result = safe_operation(
        _persist,
        context="sp_asistido.definition.update_identification",
        success_message=MSG_DEFINITION_SAVED,
    )
    return _enrich_procedure_short_duplicate(result)


def reopen_definition_wizard(
    definition: SPDefinition,
    *,
    user: AbstractUser,
    current_step: int = 3,
) -> OperationResult:
    """Invalida script generado y deja la definición en borrador para reanudar wizard."""
    def _persist() -> SPDefinition:
        with transaction.atomic():
            definition.script_generated = False
            definition.script_date = None
            definition.status = SPDefinition.Status.DRAFT
            definition.current_step = current_step
            definition.updated_by = user
            definition.save(
                update_fields=[
                    "script_generated",
                    "script_date",
                    "status",
                    "current_step",
                    "updated_at",
                    "updated_by",
                ]
            )
            return definition

    return safe_operation(
        _persist,
        context="sp_asistido.definition.reopen_wizard",
        success_message=MSG_DEFINITION_REOPENED,
    )


def confirm_generated_script(
    definition: SPDefinition,
    sql: str,
    *,
    user: AbstractUser,
    persist_fn: Callable[..., None],
    persist_kwargs: dict[str, Any] | None = None,
) -> OperationResult:
    """
    Confirma generación: ejecuta ``persist_fn`` dentro de transacción atómica.

    ``persist_fn`` es ``persist_generated_script`` o equivalente por operación.
    """
    operation = definition.operation
    kwargs = dict(persist_kwargs or {})

    def _persist() -> SPDefinition:
        with transaction.atomic():
            persist_fn(definition, sql, user=user, **kwargs)
            return definition

    return safe_operation(
        _persist,
        context=f"sp_asistido.script.confirm.{operation}",
        success_message=script_confirmed_message(operation),
    )
