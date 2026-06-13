"""Reglas de acceso al mantenimiento de compañías por UserProfile.user_type."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import QuerySet

from apps.company.models import Company
from apps.userprofile.models import UserProfile

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


MSG_UNAUTHORIZED_COMPANY = (
    "Usuario no autorizado al mantenimiento de companies"
)


def is_company_maintainer(profile: UserProfile) -> bool:
    """SU o AC pueden acceder al listado / detalle según reglas."""
    return profile.user_type in (
        UserProfile.UserType.SUPERUSER,
        UserProfile.UserType.ADMIN_COMPANY,
    )


def is_superuser_profile(profile: UserProfile) -> bool:
    return profile.user_type == UserProfile.UserType.SUPERUSER


def company_queryset_for_user(user: AbstractUser) -> QuerySet[Company]:
    """
    queryset permitido para listados y filtros de detalle.
    Llamar solo si is_company_maintainer(profile) es True.
    """
    profile = user.profile
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return Company.objects.all()
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY:
        if profile.company_id:
            return Company.objects.filter(pk=profile.company_id)
        return Company.objects.none()
    return Company.objects.none()


def user_can_view_company(user: AbstractUser, company: Company) -> bool:
    profile = user.profile
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return True
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY:
        return profile.company_id == company.pk
    return False
