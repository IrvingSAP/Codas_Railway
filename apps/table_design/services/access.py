"""Reglas de acceso al listado de diseño de tablas (cabeceras) por perfil y compañía."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Count, QuerySet

from apps.table_design.models import HeaderTable
from apps.userprofile.models import UserProfile

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


MSG_UNAUTHORIZED_TABLE_DESIGN = (
    "No tiene permiso para acceder al diseño de tablas. "
    "Solo los perfiles Administrador de sistema o Usuario pueden usar este módulo."
)

MSG_TABLE_DESIGN_NO_COMPANY = (
    "Su perfil no tiene compañía asignada; no puede consultar el diseño de tablas."
)


def has_table_design_list_access(profile: UserProfile) -> bool:
    """Solo AS o US, con compañía asociada."""
    if not profile.company_id:
        return False
    return profile.user_type in (
        UserProfile.UserType.ADMIN_SYSTEM,
        UserProfile.UserType.USER,
    )


def header_table_queryset_for_user(user: AbstractUser) -> QuerySet[HeaderTable]:
    """Cabeceras visibles: únicamente la compañía del usuario conectado."""
    profile = user.profile
    if not has_table_design_list_access(profile):
        return HeaderTable.objects.none()
    return (
        HeaderTable.objects.filter(company_id=profile.company_id)
        .select_related("company")
        .annotate(field_count=Count("fields", distinct=True))
    )
