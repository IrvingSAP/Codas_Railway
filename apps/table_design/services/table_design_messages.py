"""Mensajes de persistencia table_design (piloto OperationResult)."""

MSG_HEADER_CREATED = "Cabecera de diseño de tabla creada correctamente."
MSG_HEADER_UPDATED = "Cabecera de diseño de tabla actualizada correctamente."
MSG_HEADER_DUPLICATE = (
    "No se pudo guardar: puede existir ya una cabecera con el mismo nombre corto "
    "en su compañía o el nombre de restricción PK ya está en uso (unicidad global). "
    "Revise nombre corto y constraint PK."
)
MSG_FIELD_CREATED = "Campo guardado correctamente."
MSG_FIELD_UPDATED = "Campo actualizado correctamente."
MSG_FIELD_DELETED = "Campo eliminado correctamente."
MSG_FIELD_NAME_DUPLICATE = (
    "No se pudo guardar el campo (posible nombre duplicado). Revise los datos."
)
