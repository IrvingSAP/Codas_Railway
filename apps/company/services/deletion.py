"""Comprobaciones antes de eliminar una fila de ``Company``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import apps

if TYPE_CHECKING:
    from apps.company.models import Company


def get_company_delete_context(company: Company) -> dict[str, object]:
    """
    Contexto para la pantalla de confirmación de borrado y para la vista POST.

    Los módulos de dominio acotan datos por compañía del usuario; al borrar
    ``Company`` hay que respetar ``PROTECT`` (p. ej. diseños de tabla) y
    informar de borrados en cascada (p. ej. suscripción).
    """
    HeaderTable = apps.get_model("table_design", "HeaderTable")
    header_count = HeaderTable.objects.filter(company_id=company.pk).count()
    delete_blockers: list[str] = []
    if header_count:
        delete_blockers.append(
            f"Existen {header_count} cabecera(s) de diseño de tabla "
            f"(app TableDesign) asociadas a esta compañía. Elimine o reubique "
            f"esos diseños antes de borrar la compañía."
        )

    Subscription = apps.get_model("billing", "Subscription")
    has_subscription = Subscription.objects.filter(company_id=company.pk).exists()

    return {
        "delete_blockers": delete_blockers,
        "delete_blocked": bool(delete_blockers),
        "has_subscription": has_subscription,
    }
