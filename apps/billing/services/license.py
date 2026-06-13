"""Evaluación de acceso según suscripción (prioridad documentada en CODAS_SUSCRIPCIONES_VALIDACION)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.billing.models import Subscription


class AccessBlockReason(Enum):
    """Motivo de bloqueo cuando el acceso no está permitido."""

    INVALID_SIGNATURE = "invalid_signature"
    EXPIRED = "expired"
    INACTIVE_STATUS = "inactive_status"


@dataclass(frozen=True)
class SubscriptionAccessResult:
    """Resultado único para middleware o vistas."""

    allowed: bool
    reason: AccessBlockReason | None = None
    license_payload: dict | None = None


def evaluate_subscription_access(subscription: Subscription) -> SubscriptionAccessResult:
    """
    Prioridad: firma inválida → vencimiento por fecha → estado distinto de activo.

    El vencimiento se evalúa con independencia del valor de ``status`` (coherente
    con la validación documentada).
    """
    payload = subscription.validate_license()
    if not payload["signature_valid"]:
        return SubscriptionAccessResult(
            allowed=False,
            reason=AccessBlockReason.INVALID_SIGNATURE,
            license_payload=payload,
        )
    if payload["is_expired"]:
        return SubscriptionAccessResult(
            allowed=False,
            reason=AccessBlockReason.EXPIRED,
            license_payload=payload,
        )
    if payload["status"] != subscription.Status.ACTIVE:
        return SubscriptionAccessResult(
            allowed=False,
            reason=AccessBlockReason.INACTIVE_STATUS,
            license_payload=payload,
        )
    return SubscriptionAccessResult(allowed=True, license_payload=payload)
