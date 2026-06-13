"""Mensajes de persistencia SP Asistido (piloto OperationResult)."""

MSG_DEFINITION_SAVED = "Cambios guardados."
MSG_DEFINITION_REOPENED = (
    "Asistente reabierto en borrador. Revise pasos y regenere el script."
)
MSG_PROCEDURE_SHORT_DUPLICATE_FIELD = (
    "El nombre corto del SP ya está registrado en su compañía."
)

MSG_DRAFT_CREATED_ADD = (
    "Definición ADD creada en borrador. Continúe con columnas y orígenes."
)
MSG_DRAFT_CREATED_READ = (
    "Definición READ creada en borrador. Elija columnas del SELECT y criterio WHERE."
)
MSG_DRAFT_CREATED_DLT = (
    "Definición DLT creada en borrador. Defina el predicado WHERE obligatorio."
)
MSG_DRAFT_CREATED_UPD = (
    "Definición UPD creada en borrador. Elija columnas SET y orígenes."
)

MSG_SCRIPT_CONFIRMED_ADD = (
    "Script ADD generado y versión SQL guardada. Puede revisarlo en el listado."
)
MSG_SCRIPT_CONFIRMED_READ = (
    "Script READ generado y versión SQL guardada (§9.7). Puede revisarlo en el listado."
)
MSG_SCRIPT_CONFIRMED_DLT = (
    "Script DLT generado y versión SQL guardada. Puede revisarlo en el listado."
)
MSG_SCRIPT_CONFIRMED_UPD = (
    "Script UPD generado y versión SQL guardada. Puede revisarlo en el listado."
)

_DRAFT_CREATED_BY_OPERATION = {
    "ADD": MSG_DRAFT_CREATED_ADD,
    "READ": MSG_DRAFT_CREATED_READ,
    "DLT": MSG_DRAFT_CREATED_DLT,
    "UPD": MSG_DRAFT_CREATED_UPD,
}

_SCRIPT_CONFIRMED_BY_OPERATION = {
    "ADD": MSG_SCRIPT_CONFIRMED_ADD,
    "READ": MSG_SCRIPT_CONFIRMED_READ,
    "DLT": MSG_SCRIPT_CONFIRMED_DLT,
    "UPD": MSG_SCRIPT_CONFIRMED_UPD,
}


def draft_created_message(operation: str) -> str:
    return _DRAFT_CREATED_BY_OPERATION.get(operation, MSG_DRAFT_CREATED_ADD)


def script_confirmed_message(operation: str) -> str:
    return _SCRIPT_CONFIRMED_BY_OPERATION.get(operation, MSG_SCRIPT_CONFIRMED_ADD)
