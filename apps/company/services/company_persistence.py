"""
Persistencia de ``Company`` con ``OperationResult``.

Las vistas validan ``CompanyForm`` antes de llamar a estas funciones.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from apps.company.models import Company
from apps.company.services.access import user_can_view_company
from apps.company.services.company_messages import (
    MSG_COMPANY_CREATED,
    MSG_COMPANY_DELETED,
    MSG_COMPANY_UPDATED,
    MSG_NAME_SHORT_DUPLICATE_FIELD,
)
from apps.company.services.deletion import get_company_delete_context
from apps.core.services.operation_messages import ErrorCode
from apps.core.services.operation_result import OperationResult, safe_operation

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def _enrich_duplicate_result(result: OperationResult) -> OperationResult:
    """Añade error de campo en ``name_short`` cuando falla por unicidad."""
    if result.ok or result.error_code != ErrorCode.DUPLICATE:
        return result
    return OperationResult.failure(
        error_code=result.error_code,
        error_message=result.error_message,
        field_errors={"name_short": [MSG_NAME_SHORT_DUPLICATE_FIELD]},
    )


def create_company(company: Company, *, user: AbstractUser) -> OperationResult:
    """
    Guarda una instancia nueva de ``Company``.

    ``company`` debe venir de ``form.save(commit=False)`` con campos ya validados.
    """
    def _persist() -> Company:
        with transaction.atomic():
            company.created_by = user
            company.updated_by = user
            company.save()
            return company

    result = safe_operation(
        _persist,
        context="company.create",
        success_message=MSG_COMPANY_CREATED,
    )
    return _enrich_duplicate_result(result)


def update_company(company: Company, *, user: AbstractUser) -> OperationResult:
    """Actualiza una ``Company`` existente (instancia con PK)."""
    def _persist() -> Company:
        with transaction.atomic():
            company.updated_by = user
            company.save()
            return company

    result = safe_operation(
        _persist,
        context="company.update",
        success_message=MSG_COMPANY_UPDATED,
    )
    return _enrich_duplicate_result(result)


def delete_company(company: Company) -> OperationResult:
    """
    Elimina la fila de ``Company``.

    Las reglas de negocio previas (diseños de tabla, etc.) deben comprobarse
    en la vista con ``get_company_delete_context`` antes de llamar aquí.
    """
    company_pk = company.pk

    def _persist() -> int:
        with transaction.atomic():
            company.delete()
            return company_pk

    return safe_operation(
        _persist,
        context="company.delete",
        success_message=MSG_COMPANY_DELETED,
    )


def delete_company_if_allowed(company: Company) -> OperationResult:
    """
    Elimina solo si ``get_company_delete_context`` no bloquea el borrado.

    Útil para centralizar mensajes de bloqueo de negocio en la capa de servicio.
    """
    delete_ctx = get_company_delete_context(company)
    if delete_ctx["delete_blocked"]:
        blockers = delete_ctx["delete_blockers"]
        message = str(blockers[0]) if blockers else (
            "No se puede eliminar la compañía por datos asociados."
        )
        return OperationResult.failure(
            error_code=ErrorCode.BUSINESS_BLOCKED,
            error_message=message,
        )
    return delete_company(company)


def get_company_for_user(pk: int, *, user: AbstractUser) -> OperationResult:
    """Obtiene compañía por PK si el usuario puede verla."""
    def _fetch() -> Company:
        company = Company.objects.get(pk=pk)
        if not user_can_view_company(user, company):
            raise Company.DoesNotExist()
        return company

    return safe_operation(_fetch, context="company.get")
