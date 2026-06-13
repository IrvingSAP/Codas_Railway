"""Gestión de sesión temporal para asistentes SP Asistido."""

from __future__ import annotations

from datetime import timedelta

from django.http import HttpRequest
from django.utils import timezone
from django.utils.dateparse import parse_datetime

WIZARD_SESSION_TTL_HOURS = 4


def save_wizard_session(
    request: HttpRequest,
    session_key: str,
    payload: dict,
) -> None:
    request.session[session_key] = {
        "saved_at": timezone.now().isoformat(),
        "data": payload,
    }
    request.session.modified = True


def load_wizard_session(request: HttpRequest, session_key: str) -> tuple[dict | None, bool]:
    """
    Devuelve (payload, expired).

    - payload: datos vigentes o None.
    - expired: True si existía sesión pero venció y fue limpiada.
    """
    raw = request.session.get(session_key)
    if not raw:
        return None, False
    if not isinstance(raw, dict):
        clear_wizard_session(request, session_key)
        return None, True

    saved_at_raw = raw.get("saved_at")
    payload = raw.get("data")
    if not isinstance(saved_at_raw, str) or not isinstance(payload, dict):
        clear_wizard_session(request, session_key)
        return None, True

    saved_at = parse_datetime(saved_at_raw)
    if not saved_at:
        clear_wizard_session(request, session_key)
        return None, True
    if timezone.is_naive(saved_at):
        saved_at = timezone.make_aware(saved_at, timezone.get_current_timezone())

    if timezone.now() - saved_at > timedelta(hours=WIZARD_SESSION_TTL_HOURS):
        clear_wizard_session(request, session_key)
        return None, True

    return payload, False


def clear_wizard_session(request: HttpRequest, session_key: str) -> None:
    if session_key in request.session:
        del request.session[session_key]
        request.session.modified = True
