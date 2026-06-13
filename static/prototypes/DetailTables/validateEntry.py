import re

def validate_header_table(table_name_long, table_name_short, schema, notes):
    errors = []

    # Expresiones regulares
    regexLettersUnderscore = re.compile(r"^[A-Za-z_]+$")
    regexShortTableName = re.compile(r"^[A-Z0-9]{8,10}$")

    # ============================
    # 1 - Validación table_name_long
    # ============================
    if len(table_name_long) < 10 or len(table_name_long) > 50:
        errors.append("El campo 'Nombre Largo' debe tener entre 10 y 50 caracteres.")
        return {"ok": False, "errors": errors}
    
    if not regexLettersUnderscore.match(table_name_long):
        errors.append("El campo 'Nombre Largo' solo acepta letras y guion bajo (_).")
        return {"ok": False, "errors": errors}
    
    # ============================
    # 2 - Validación table_name_short
    # ============================
    table_name_short = table_name_short.strip().upper()
    if len(table_name_short) < 8 or len(table_name_short) > 10:
        errors.append("El campo 'Nombre Corto' debe tener entre 8 y 10 caracteres.")
        return {"ok": False, "errors": errors}

    if not regexShortTableName.match(table_name_short):
        errors.append(
            "El campo 'Nombre Corto' solo permite letras mayúsculas (A-Z) y dígitos (0-9)."
        )
        return {"ok": False, "errors": errors}
    
    # ============================
    # 3 - Validación schema
    # ============================
    schema = (schema or "").strip()
    if not schema:
        errors.append("El campo 'Esquema / librería' es obligatorio.")
        return {"ok": False, "errors": errors}
    if len(schema) > 10:
        errors.append("El campo 'schema' debe tener máximo 10 caracteres.")
        return {"ok": False, "errors": errors}

    return {"ok": True}


def validate_field(name_long, name_short, field_type, length, decimals, is_null, is_key, order_key):
    errors = []

    # -------------------------------
    # Validaciones básicas
    # -------------------------------
    if not name_long:
        errors.append("El Nombre Largo es obligatorio.")

    if not name_short:
        errors.append("El Nombre Corto es obligatorio.")

    if not field_type:
        errors.append("Debe seleccionar un Tipo de Dato.")

    # Convertir valores vacíos a None
    length = int(length) if length not in [None, "", "0"] else None
    decimals = int(decimals) if decimals not in [None, "", "0"] else None

    # -------------------------------
    # Tipos con longitud fija
    # -------------------------------
    FIXED_LENGTH_TYPES = {
        "SMALLINT": 2,
        "INTEGER": 4,
        "BIGINT": 8,
        "REAL": 4,
        "DOUBLE": 8,
        "DATE": 4,
        "TIME": 3,
        "TIMESTAMP": 26,
        "ROWID": 17,
    }

    if field_type in FIXED_LENGTH_TYPES:
        if length is not None and length != FIXED_LENGTH_TYPES[field_type]:
            errors.append(f"El tipo {field_type} debe tener longitud fija = {FIXED_LENGTH_TYPES[field_type]}.")
        if decimals not in [None, 0]:
            errors.append(f"El tipo {field_type} no permite decimales.")
        return {"ok": len(errors) == 0, "errors": errors}

    # -------------------------------
    # Tipos que requieren longitud (sin decimales)
    # -------------------------------
    LENGTH_REQUIRED_TYPES = [
        "CHAR", "VARCHAR", "GRAPHIC", "VARGRAPHIC",
        "BINARY", "VARBINARY"
    ]

    if field_type in LENGTH_REQUIRED_TYPES:
        if length is None:
            errors.append(f"El tipo {field_type} requiere una longitud.")
        if decimals not in [None, 0]:
            errors.append(f"El tipo {field_type} no permite decimales.")
        return {"ok": len(errors) == 0, "errors": errors}

    # -------------------------------
    # Tipos DECIMAL
    # -------------------------------
    if field_type in ["DECIMAL", ]:
        if length is None:
            errors.append(f"El tipo {field_type} requiere longitud.")
        if decimals is None:
            errors.append(f"El tipo {field_type} requiere decimales.")
        if length is not None and decimals is not None and decimals > length:
            errors.append("Los decimales no pueden ser mayores que la longitud.")
        return {"ok": len(errors) == 0, "errors": errors}
    
    # -------------------------------
    # Tipos NUMERIC
    # -------------------------------
    if field_type in ["NUMERIC", ]:
        if length is None:
            errors.append(f"El tipo {field_type} requiere longitud.")
        if length is not None and decimals is not None and decimals > length:
            errors.append("Los decimales no pueden ser mayores que la longitud.")
        return {"ok": len(errors) == 0, "errors": errors}

    # -------------------------------
    # Tipos sin longitud ni decimales
    # -------------------------------
    NO_LENGTH_TYPES = ["CLOB", "BLOB", "XML", "DECFLOAT"]

    if field_type in NO_LENGTH_TYPES:
        if length is not None:
            errors.append(f"El tipo {field_type} no debe tener longitud.")
        if decimals not in [None, 0]:
            errors.append(f"El tipo {field_type} no permite decimales.")
        return {"ok": len(errors) == 0, "errors": errors}

    # -------------------------------
    # Validación de llave
    # -------------------------------
    if is_key and not order_key:
        errors.append("Debe especificar el orden de la llave.")

    return {"ok": len(errors) == 0, "errors": errors}

def validate_order_key(is_key, order_key):
    errors = []

    # Convertir a entero si viene como string
    try:
        order_key = int(order_key)
    except:
        order_key = 0

    # Si NO es llave → order_key debe ser 0
    if not is_key:
        if order_key != 0:
            errors.append("El campo no es llave, por lo tanto el Orden Llave debe ser 0.")
        return errors

    # Si ES llave → order_key debe ser > 0
    if order_key == 0:
        errors.append("Debe especificar un Orden Llave mayor que 0 para un campo llave.")
        return errors


    return errors

