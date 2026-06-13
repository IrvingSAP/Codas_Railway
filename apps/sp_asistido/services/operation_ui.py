"""Helpers de UI para OperationResult en sp_asistido."""

from __future__ import annotations

from apps.core.services.operation_result import OperationResult


def extend_errors_from_result(errors: list[str], result: OperationResult) -> None:
    """Añade mensajes de ``field_errors`` a una lista de errores de plantilla."""
    if not result.field_errors:
        return
    for field_name, error_list in result.field_errors.items():
        for message in error_list:
            if field_name == "__all__":
                errors.append(message)
            else:
                errors.append(message)
