"""Acceso al listado de SP Asistido por perfil y compañía."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.sp_asistido.models import SPDefinition
from apps.userprofile.models import UserProfile

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


MSG_UNAUTHORIZED_SP_ASISTIDO = (
    "No tiene permiso para acceder a SP Asistido. "
    "Perfiles permitidos: Administrador de sistema, Usuario o Administrador de compañía, con compañía asignada."
)

MSG_SP_ASISTIDO_NO_COMPANY = (
    "Su perfil no tiene compañía asignada; no puede consultar SP Asistido."
)


def has_sp_asistido_list_access(profile: UserProfile) -> bool:
    """AS, US o AC con compañía asociada (alineado a checklist A.2 / B.5)."""
    if not profile.company_id:
        return False
    return profile.user_type in (
        UserProfile.UserType.ADMIN_SYSTEM,
        UserProfile.UserType.USER,
        UserProfile.UserType.ADMIN_COMPANY,
    )


def sp_definition_queryset_for_user(user: AbstractUser) -> QuerySet[SPDefinition]:
    """Definiciones visibles: solo la compañía del perfil."""
    profile = user.profile
    if not has_sp_asistido_list_access(profile):
        return SPDefinition.objects.none()
    return (
        SPDefinition.objects.filter(company_id=profile.company_id)
        .select_related("header_table", "company")
        .order_by("-updated_at")
    )


def get_sp_definition_or_404(
    user: AbstractUser,
    definition_id: int,
    *,
    operation: str | None = None,
) -> SPDefinition:
    """
    Obtiene una definición visible para el usuario en su compañía.

    Regla de seguridad (G.4): si el ID no pertenece al scope del usuario, responde 404.
    """
    qs = sp_definition_queryset_for_user(user)
    if operation:
        qs = qs.filter(operation=operation)
    return get_object_or_404(qs, pk=definition_id)
