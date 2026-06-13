"""Compañía del perfil conectado para métricas del panel."""

from __future__ import annotations

from apps.userprofile.models import UserProfile


def get_dashboard_company_id(profile: UserProfile) -> int | None:
    """
    ID de compañía para filtrar métricas del panel.

    Usa ``company_id`` (FK) y no la carga de ``profile.company``, para no
    devolver ``None`` si el objeto Company no está en caché o falló el join.
    """
    return profile.company_id
