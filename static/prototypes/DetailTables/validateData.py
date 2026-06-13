from .models import HeaderTable, DetailTable

def validate_header_duplicates(company, table_name_long, table_name_short):
    errors = []

    # Validar nombre largo duplicado
    if HeaderTable.objects.filter(
        company=company,
        table_name_long__iexact=table_name_long
    ).exists():
        errors.append("El Nombre Largo ya existe en otra tabla.")

    # Validar nombre corto duplicado
    if HeaderTable.objects.filter(
        company=company,
        table_name_short__iexact=table_name_short
    ).exists():
        errors.append("El Nombre Corto ya existe en otra tabla.")

    if errors:
        return {"ok": False, "errors": errors}

    return {"ok": True}


def validate_header_duplicates_edit(company, table_id, table_name_long, table_name_short):
    errors = []

    # Nombre largo duplicado (excluyendo el actual)
    if HeaderTable.objects.filter(
        company=company,
        table_name_long__iexact=table_name_long
    ).exclude(id=table_id).exists():
        errors.append("El Nombre Largo ya existe en otra tabla.")

    # Nombre corto duplicado (excluyendo el actual)
    if HeaderTable.objects.filter(
        company=company,
        table_name_short__iexact=table_name_short
    ).exclude(id=table_id).exists():
        errors.append("El Nombre Corto ya existe en otra tabla.")

    if errors:
        return {"ok": False, "errors": errors}

    return {"ok": True}


def validate_field_duplicates(header, name_long, name_short):
    errors = []

    if DetailTable.objects.filter(header=header, field_name_long__iexact=name_long).exists():
        errors.append("El Nombre Largo ya existe en esta tabla.")

    if DetailTable.objects.filter(header=header, field_name_short__iexact=name_short).exists():
        errors.append("El Nombre Corto ya existe en esta tabla.")

    if errors:
        return {"ok": False, "errors": errors}

    return {"ok": True}

def validate_field_duplicates_edit(header, field, name_long, name_short):
    errors = []

    if DetailTable.objects.filter(header=header, field_name_long=name_long).exclude(id=field.id).exists():
        errors.append("Ya existe un campo con ese Nombre Largo.")

    if DetailTable.objects.filter(header=header, field_name_short=name_short).exclude(id=field.id).exists():
        errors.append("Ya existe un campo con ese Nombre Corto.")

    return {"ok": len(errors) == 0, "errors": errors}


def validate_order_key_dup(header, order_key):
    errors = []

    # Convertir a entero si viene como string
    try:
        order_key = int(order_key)
    except:
        order_key = 0

    # Si es 0 → no validar duplicados
    if order_key <= 0:
        return errors

    # Validar duplicados dentro del mismo header
    if DetailTable.objects.filter(header=header, order_key=order_key).exists():
        errors.append(f"Ya existe un campo con Orden Llave = {order_key}. No se permiten duplicados.")

    return errors


def validate_order_key_dup_edit(header, field, order_key):
    errors = []

    # Convertir a entero
    try:
        order_key = int(order_key)
    except:
        order_key = 0

    # Si es 0 → no validar duplicados
    if order_key <= 0:
        return errors

    # Validar duplicado (excluyendo el mismo campo)
    exists = (
        DetailTable.objects
        .filter(header=header, order_key=order_key)
        .exclude(id=field.id)
        .exists()
    )

    if exists:
        errors.append(f"Ya existe un campo con Orden Llave = {order_key}.")

    return errors




