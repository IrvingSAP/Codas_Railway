"""Servicios transversales de apps.core."""

from apps.core.services.operation_messages import ErrorCode
from apps.core.services.operation_result import OperationResult, safe_operation

__all__ = [
    "ErrorCode",
    "OperationResult",
    "safe_operation",
]
