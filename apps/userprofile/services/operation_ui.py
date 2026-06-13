"""Helpers de UI para OperationResult en userprofile."""

from __future__ import annotations

from django.forms import Form

from apps.core.services.operation_result import OperationResult


def apply_operation_field_errors(form: Form, result: OperationResult) -> None:
    """Mapea ``field_errors`` del servicio al formulario Django."""
    if not result.field_errors:
        return
    for field_name, error_list in result.field_errors.items():
        for message in error_list:
            if field_name == "__all__":
                form.add_error(None, message)
            else:
                form.add_error(field_name, message)
