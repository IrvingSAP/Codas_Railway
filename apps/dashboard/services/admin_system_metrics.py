"""
Métricas del panel para administrador de sistema (AS), acotadas por compañía.

Mantenimientos: el modelo usa ``GENERATED`` (G) como equivalente operativo de
«activo»; ``DRAFT`` (D) e ``INACTIVE`` (I). Los registros en ``ERROR`` (E) se
cuentan como inactivos en el resumen.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.maintenance_builder.models import MaintenanceDefinition
from apps.sp_asistido.models import SPDefinition
from apps.table_design.models import HeaderTable
from apps.userprofile.services.company_user_metrics import get_company_user_metrics


@dataclass(frozen=True)
class HeaderTableStatusCounts:
    """Diseños de tabla (HeaderTable) por estado."""

    active: int
    process: int
    inactive: int


@dataclass(frozen=True)
class DraftActiveInactiveCounts:
    """Conteos borrador / activo / inactivo (SP y mantenimientos)."""

    draft: int
    active: int
    inactive: int


@dataclass(frozen=True)
class AdminSystemDashboardMetrics:
    """Resumen del panel AS para una compañía."""

    header_tables: HeaderTableStatusCounts
    stored_procedures: DraftActiveInactiveCounts
    maintenance_definitions: DraftActiveInactiveCounts
    total_users: int


def _empty_header_counts() -> HeaderTableStatusCounts:
    return HeaderTableStatusCounts(active=0, process=0, inactive=0)


def _empty_draft_active_inactive() -> DraftActiveInactiveCounts:
    return DraftActiveInactiveCounts(draft=0, active=0, inactive=0)


def _empty_metrics() -> AdminSystemDashboardMetrics:
    return AdminSystemDashboardMetrics(
        header_tables=_empty_header_counts(),
        stored_procedures=_empty_draft_active_inactive(),
        maintenance_definitions=_empty_draft_active_inactive(),
        total_users=0,
    )


def get_admin_system_dashboard_metrics(
    company_id: int | None,
) -> AdminSystemDashboardMetrics:
    """Totales por módulo filtrados por ``company_id`` del usuario conectado."""
    if not company_id:
        return _empty_metrics()

    headers = HeaderTable.objects.filter(company_id=company_id)
    header_tables = HeaderTableStatusCounts(
        active=headers.filter(status=HeaderTable.Status.ACTIVE).count(),
        process=headers.filter(status=HeaderTable.Status.PROCESS).count(),
        inactive=headers.filter(status=HeaderTable.Status.INACTIVE).count(),
    )

    sps = SPDefinition.objects.filter(company_id=company_id)
    stored_procedures = DraftActiveInactiveCounts(
        draft=sps.filter(status=SPDefinition.Status.DRAFT).count(),
        active=sps.filter(status=SPDefinition.Status.ACTIVE).count(),
        inactive=sps.filter(status=SPDefinition.Status.INACTIVE).count(),
    )

    maintenances = MaintenanceDefinition.objects.filter(company_id=company_id)
    maintenance_definitions = DraftActiveInactiveCounts(
        draft=maintenances.filter(status=MaintenanceDefinition.Status.DRAFT).count(),
        active=maintenances.filter(
            status=MaintenanceDefinition.Status.GENERATED
        ).count(),
        inactive=maintenances.filter(
            status__in=(
                MaintenanceDefinition.Status.INACTIVE,
                MaintenanceDefinition.Status.ERROR,
            )
        ).count(),
    )

    total_users = get_company_user_metrics(company_id).total_users

    return AdminSystemDashboardMetrics(
        header_tables=header_tables,
        stored_procedures=stored_procedures,
        maintenance_definitions=maintenance_definitions,
        total_users=total_users,
    )
