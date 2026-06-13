"""Servicios del panel CODAS."""

from apps.dashboard.services.admin_system_metrics import (
    AdminSystemDashboardMetrics,
    get_admin_system_dashboard_metrics,
)

__all__ = [
    "AdminSystemDashboardMetrics",
    "get_admin_system_dashboard_metrics",
]
