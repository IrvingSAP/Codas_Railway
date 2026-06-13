"""Reglas de acceso al mantenimiento de perfiles por UserProfile.user_type (usuario de conexión)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import QuerySet

from apps.userprofile.models import UserProfile

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


MSG_UNAUTHORIZED_USERPROFILE = (
    "Usuario no autorizado al mantenimiento de Usuarios"
)


def is_userprofile_maintainer(profile: UserProfile) -> bool:
    """SU, AC o AS pueden acceder al módulo de perfiles."""
    return profile.user_type in (
        UserProfile.UserType.SUPERUSER,
        UserProfile.UserType.ADMIN_COMPANY,
        UserProfile.UserType.ADMIN_SYSTEM,
    )


def is_superuser_connection(profile: UserProfile) -> bool:
    return profile.user_type == UserProfile.UserType.SUPERUSER


def company_readonly_for_connection(profile: UserProfile) -> bool:
    """AC/AS: compañía fijada a la de conexión (solo lectura en formulario)."""
    return profile.user_type in (
        UserProfile.UserType.ADMIN_COMPANY,
        UserProfile.UserType.ADMIN_SYSTEM,
    )


def userprofile_queryset_for_user(user: AbstractUser) -> QuerySet[UserProfile]:
    """
    Queryset de listados y base para permisos de objeto.
    Llamar solo si is_userprofile_maintainer(user.profile).
    """
    profile = user.profile
    qs = UserProfile.objects.select_related("user", "company")
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return qs
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY:
        if profile.company_id:
            return qs.filter(company_id=profile.company_id)
        return qs.none()
    if profile.user_type == UserProfile.UserType.ADMIN_SYSTEM:
        if profile.company_id:
            return qs.filter(
                company_id=profile.company_id,
                user_type=UserProfile.UserType.USER,
            )
        return qs.none()
    return qs.none()


def user_can_access_target_profile(actor: AbstractUser, target: UserProfile) -> bool:
    """Detalle / edición / borrado: el objeto debe pertenecer al ámbito del actor."""
    ap = actor.profile
    if ap.user_type == UserProfile.UserType.SUPERUSER:
        return True
    if ap.user_type == UserProfile.UserType.ADMIN_COMPANY:
        if not ap.company_id:
            return False
        return target.company_id == ap.company_id
    if ap.user_type == UserProfile.UserType.ADMIN_SYSTEM:
        if not ap.company_id:
            return False
        return (
            target.company_id == ap.company_id
            and target.user_type == UserProfile.UserType.USER
        )
    return False


def resolve_company_for_save(
    connection_profile: UserProfile,
    posted_company_id: int | None,
) -> int | None:
    """
    Devuelve el company_id a persistir en create/update.
    AC/AS: siempre el de conexión (ignora POST). SU: el enviado en formulario.
    """
    if company_readonly_for_connection(connection_profile):
        return connection_profile.company_id
    return posted_company_id


def resolve_new_profile_user_type(connection_profile: UserProfile) -> str:
    """
    UserType por defecto al crear un perfil, según el tipo del usuario conectado.
    SU -> AC, AC -> AS, AS -> US.
    """
    if connection_profile.user_type == UserProfile.UserType.SUPERUSER:
        return UserProfile.UserType.ADMIN_COMPANY
    if connection_profile.user_type == UserProfile.UserType.ADMIN_COMPANY:
        return UserProfile.UserType.ADMIN_SYSTEM
    if connection_profile.user_type == UserProfile.UserType.ADMIN_SYSTEM:
        return UserProfile.UserType.USER
    return UserProfile.UserType.USER
