"""
Persistencia de ``UserProfile`` (y ``User`` asociado) con ``OperationResult``.

Las vistas validan el formulario antes de llamar a estas funciones.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.core.services.operation_messages import ErrorCode
from apps.core.services.operation_result import OperationResult, safe_operation
from apps.userprofile.models import UserProfile
from apps.userprofile.services.userprofile_messages import (
    MSG_USERPROFILE_CREATED,
    MSG_USERPROFILE_DELETED,
    MSG_USERPROFILE_UPDATED,
    MSG_USERNAME_DUPLICATE_FIELD,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

User = get_user_model()


def _enrich_username_duplicate_result(result: OperationResult) -> OperationResult:
    """Mapea duplicado de integridad al campo ``username`` del formulario de alta."""
    if result.ok or result.error_code != ErrorCode.DUPLICATE:
        return result
    return OperationResult.failure(
        error_code=result.error_code,
        error_message=result.error_message,
        field_errors={"username": [MSG_USERNAME_DUPLICATE_FIELD]},
    )


def create_user_profile(
    profile: UserProfile,
    *,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    company_id: int | None,
    user_type: str,
    actor: AbstractUser,
) -> OperationResult:
    """
    Crea ``User`` + ``UserProfile`` en una transacción.

    ``profile`` proviene de ``form.save(commit=False)`` (sin ``user`` ni PK).
    """
    def _persist() -> UserProfile:
        with transaction.atomic():
            auth_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            auth_user.set_password(password)
            auth_user.save()
            profile.user = auth_user
            profile.company_id = company_id
            profile.user_type = user_type
            profile.created_by = actor
            profile.updated_by = actor
            profile.save()
            return profile

    result = safe_operation(
        _persist,
        context="userprofile.create",
        success_message=MSG_USERPROFILE_CREATED,
    )
    return _enrich_username_duplicate_result(result)


def update_user_profile(
    profile: UserProfile,
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str | None,
    company_id: int | None,
    actor: AbstractUser,
) -> OperationResult:
    """Actualiza ``User`` y ``UserProfile`` existentes."""
    auth_user = profile.user

    def _persist() -> UserProfile:
        with transaction.atomic():
            auth_user.first_name = first_name
            auth_user.last_name = last_name
            auth_user.email = email
            user_update_fields = ["first_name", "last_name", "email"]
            if password:
                auth_user.set_password(password)
                user_update_fields.append("password")
            auth_user.save(update_fields=user_update_fields)
            profile.company_id = company_id
            profile.updated_by = actor
            profile.save()
            return profile

    return safe_operation(
        _persist,
        context="userprofile.update",
        success_message=MSG_USERPROFILE_UPDATED,
    )


def delete_user_profile(profile: UserProfile) -> OperationResult:
    """Elimina la fila de ``UserProfile`` (mismo alcance que la vista actual)."""
    profile_pk = profile.pk

    def _persist() -> int:
        with transaction.atomic():
            profile.delete()
            return profile_pk

    return safe_operation(
        _persist,
        context="userprofile.delete",
        success_message=MSG_USERPROFILE_DELETED,
    )
