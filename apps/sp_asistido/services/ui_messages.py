"""Helpers de mensajería UI para SP Asistido."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest


def notify_success(request: HttpRequest, text: str) -> None:
    messages.success(request, text, extra_tags="sp_asistido")


def notify_error(request: HttpRequest, text: str) -> None:
    messages.error(request, text, extra_tags="sp_asistido")


def notify_warning(request: HttpRequest, text: str) -> None:
    messages.warning(request, text, extra_tags="sp_asistido")


def notify_info(request: HttpRequest, text: str) -> None:
    messages.info(request, text, extra_tags="sp_asistido")
