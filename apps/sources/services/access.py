"""Reglas de acceso al mantenimiento de plantillas fuente por compañía."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import QuerySet

from apps.sources.models import SourceTemplate

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from apps.userprofile.models import UserProfile


MSG_UNAUTHORIZED_SOURCES = "Usuario no autorizado al mantenimiento de Plantillas"


def has_sources_company_scope(profile: UserProfile) -> bool:
    """La gestión se acota a la compañía del usuario conectado."""
    return bool(profile.company_id)


def source_queryset_for_user(user: AbstractUser) -> QuerySet[SourceTemplate]:
    """Listado base de plantillas: solo compañía del usuario conectado."""
    profile = user.profile
    if not has_sources_company_scope(profile):
        return SourceTemplate.objects.none()
    return SourceTemplate.objects.filter(company_id=profile.company_id)


def user_can_access_source(user: AbstractUser, target: SourceTemplate) -> bool:
    """Detalle/edición/borrado en ámbito de la compañía del actor."""
    profile = user.profile
    if not has_sources_company_scope(profile):
        return False
    return target.company_id == profile.company_id
