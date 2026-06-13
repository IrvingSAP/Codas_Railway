"""Textos y códigos de error para OperationResult (catálogo CODAS_UI_MESSAGES)."""

from __future__ import annotations


class ErrorCode:
    """Identificadores estables; no se muestran al usuario."""

    SUCCESS = "success"
    VALIDATION_FORM = "validation_form"
    VALIDATION_MODEL = "validation_model"
    DUPLICATE = "duplicate"
    NOT_FOUND = "not_found"
    MULTIPLE_FOUND = "multiple_found"
    PROTECTED_DELETE = "protected_delete"
    DATA_ERROR = "data_error"
    DB_CONNECTION = "db_connection"
    DB_INTERNAL = "db_internal"
    EMPTY_SEARCH = "empty_search"
    UNAUTHORIZED = "unauthorized"
    BUSINESS_BLOCKED = "business_blocked"
    UNEXPECTED = "unexpected"


# Mensajes al usuario (docs/CODAS_UI_MESSAGES.md § 3).
MSG_SAVE_SUCCESS = "El registro se guardó correctamente."
MSG_FORM_INVALID = "Revise los datos marcados en rojo; no se pudo guardar."
MSG_VALIDATION_MODEL = "Los datos no son válidos. Revise los campos indicados."
MSG_DUPLICATE = (
    "Ya existe un registro con ese identificador. Revise el nombre corto o el código."
)
MSG_DATA_ERROR = (
    "Algún valor no es válido para el sistema. Revise longitudes y formatos."
)
MSG_DB_CONNECTION = (
    "No se pudo completar la operación. Verifique la conexión o intente más tarde."
)
MSG_SAVE_UNEXPECTED = (
    "Ocurrió un error al guardar. Si persiste, contacte al administrador de sistemas."
)
MSG_NOT_FOUND = "No se encontró el registro solicitado."
MSG_EMPTY_SEARCH = "No hay registros que coincidan con la búsqueda."
MSG_MULTIPLE_FOUND = (
    "Hay datos inconsistentes para esta consulta. Contacte al administrador de sistemas."
)
MSG_DELETE_SUCCESS = "El registro se eliminó correctamente."
MSG_PROTECTED_DELETE = (
    "No se puede eliminar: existen datos asociados que deben resolverse antes."
)
MSG_ALREADY_DELETED = "El registro ya no existe o fue eliminado."
MSG_UNEXPECTED = (
    "Ocurrió un error inesperado. Si persiste, contacte al administrador de sistemas."
)
