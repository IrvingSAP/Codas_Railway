"""Claves de sesión para el flujo de autenticación en varios pasos (CODAS_SECURITY §6)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest

SESSION_PENDING_USER_ID = "security_pending_user_id"


def set_pending_user(request: HttpRequest, user_id: int) -> None:
    request.session[SESSION_PENDING_USER_ID] = user_id


def get_pending_user_id(request: HttpRequest) -> int | None:
    raw = request.session.get(SESSION_PENDING_USER_ID)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def clear_security_flow(request: HttpRequest) -> None:
    request.session.pop(SESSION_PENDING_USER_ID, None)
