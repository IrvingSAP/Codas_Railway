"""Resultado estructurado de operaciones de persistencia y consulta."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    ValidationError,
)
from django.db import DatabaseError, DataError, IntegrityError, OperationalError, ProgrammingError
from django.db.models.deletion import ProtectedError

from apps.core.services.operation_messages import (
    ErrorCode,
    MSG_DATA_ERROR,
    MSG_DB_CONNECTION,
    MSG_DUPLICATE,
    MSG_MULTIPLE_FOUND,
    MSG_NOT_FOUND,
    MSG_PROTECTED_DELETE,
    MSG_SAVE_SUCCESS,
    MSG_UNEXPECTED,
    MSG_VALIDATION_MODEL,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class OperationResult:
    """Resultado de una operación en capa de servicio."""

    ok: bool
    data: Any = None
    error_message: str = ""
    error_code: str = ""
    field_errors: dict[str, list[str]] | None = field(default=None)

    @classmethod
    def success(
        cls,
        data: Any = None,
        *,
        message: str = MSG_SAVE_SUCCESS,
    ) -> OperationResult:
        return cls(
            ok=True,
            data=data,
            error_message=message,
            error_code=ErrorCode.SUCCESS,
        )

    @classmethod
    def failure(
        cls,
        *,
        error_code: str,
        error_message: str,
        field_errors: dict[str, list[str]] | None = None,
    ) -> OperationResult:
        return cls(
            ok=False,
            data=None,
            error_message=error_message,
            error_code=error_code,
            field_errors=field_errors,
        )


def _validation_field_errors(exc: ValidationError) -> dict[str, list[str]] | None:
    if hasattr(exc, "message_dict") and exc.message_dict:
        result: dict[str, list[str]] = {}
        for key, value in exc.message_dict.items():
            if isinstance(value, (list, tuple)):
                result[str(key)] = [str(item) for item in value]
            else:
                result[str(key)] = [str(value)]
        return result
    if hasattr(exc, "messages") and exc.messages:
        return {"__all__": [str(m) for m in exc.messages]}
    return None


def safe_operation(
    operation: Callable[[], T],
    *,
    context: str = "",
    success_message: str = MSG_SAVE_SUCCESS,
) -> OperationResult:
    """
    Ejecuta ``operation`` y devuelve OperationResult sin propagar excepciones de BD/ORM.

    El detalle técnico se registra en log; el mensaje al usuario sigue el catálogo
    docs/CODAS_UI_MESSAGES.md.
    """
    log_prefix = f"[{context}] " if context else ""

    try:
        data = operation()
        return OperationResult.success(data=data, message=success_message)
    except ObjectDoesNotExist as exc:
        logger.warning("%sRegistro no encontrado: %s", log_prefix, exc)
        return OperationResult.failure(
            error_code=ErrorCode.NOT_FOUND,
            error_message=MSG_NOT_FOUND,
        )
    except MultipleObjectsReturned as exc:
        logger.error("%sMúltiples registros: %s", log_prefix, exc)
        return OperationResult.failure(
            error_code=ErrorCode.MULTIPLE_FOUND,
            error_message=MSG_MULTIPLE_FOUND,
        )
    except ProtectedError as exc:
        logger.warning("%sEliminación protegida: %s", log_prefix, exc)
        return OperationResult.failure(
            error_code=ErrorCode.PROTECTED_DELETE,
            error_message=MSG_PROTECTED_DELETE,
        )
    except IntegrityError as exc:
        logger.warning("%sIntegridad: %s", log_prefix, exc)
        return OperationResult.failure(
            error_code=ErrorCode.DUPLICATE,
            error_message=MSG_DUPLICATE,
        )
    except ValidationError as exc:
        logger.info("%sValidación de modelo: %s", log_prefix, exc)
        return OperationResult.failure(
            error_code=ErrorCode.VALIDATION_MODEL,
            error_message=MSG_VALIDATION_MODEL,
            field_errors=_validation_field_errors(exc),
        )
    except DataError as exc:
        logger.exception("%sError de datos", log_prefix)
        return OperationResult.failure(
            error_code=ErrorCode.DATA_ERROR,
            error_message=MSG_DATA_ERROR,
        )
    except OperationalError as exc:
        logger.exception("%sError operacional de BD", log_prefix)
        return OperationResult.failure(
            error_code=ErrorCode.DB_CONNECTION,
            error_message=MSG_DB_CONNECTION,
        )
    except ProgrammingError as exc:
        logger.exception("%sError de programación SQL", log_prefix)
        return OperationResult.failure(
            error_code=ErrorCode.DB_INTERNAL,
            error_message=MSG_UNEXPECTED,
        )
    except DatabaseError as exc:
        logger.exception("%sError general de BD", log_prefix)
        return OperationResult.failure(
            error_code=ErrorCode.DB_INTERNAL,
            error_message=MSG_UNEXPECTED,
        )
    except Exception as exc:
        logger.exception("%sError inesperado", log_prefix)
        return OperationResult.failure(
            error_code=ErrorCode.UNEXPECTED,
            error_message=MSG_UNEXPECTED,
        )
