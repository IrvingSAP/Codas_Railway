"""Métricas de perfiles por compañía (panel AC)."""

from __future__ import annotations

from dataclasses import dataclass

from apps.userprofile.models import UserProfile


@dataclass(frozen=True)
class CompanyUserMetrics:
    """Totales de perfiles en una compañía por tipo de usuario."""

    total_users: int
    total_admin_system: int


def get_company_user_metrics(company_id: int | None) -> CompanyUserMetrics:
    """
    Cuenta perfiles ``US`` y ``AS`` con ``UserProfile.company_id`` igual a la compañía.

    Si ``company_id`` es ``None``, devuelve ceros.
    """
    if not company_id:
        return CompanyUserMetrics(total_users=0, total_admin_system=0)

    base = UserProfile.objects.filter(company_id=company_id)
    return CompanyUserMetrics(
        total_users=base.filter(user_type=UserProfile.UserType.USER).count(),
        total_admin_system=base.filter(
            user_type=UserProfile.UserType.ADMIN_SYSTEM
        ).count(),
    )
