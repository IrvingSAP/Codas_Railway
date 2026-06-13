

def generate_db2_script(header):
    fields = header.fields.all().order_by("order_reg")

    lines = []
    pk_fields = []
    column_labels = []

    # Posición fija para la segunda línea (30 chars + 2 spaces)
    indent = " " * 32

    for f in fields:

        # ============================
        # 1. Tipo DB2
        # ============================
        if f.field_type in ["CHAR", "VARCHAR", "GRAPHIC", "VARGRAPHIC", "BINARY", "VARBINARY"]:
            type_def = f"{f.field_type}({f.field_length})"

        elif f.field_type in ["DECIMAL", "NUMERIC"]:
            decimals = f.decimal_places if f.decimal_places is not None else 0
            type_def = f"{f.field_type}({f.field_length},{decimals})"

        elif f.field_type in ["SMALLINT", "INTEGER", "BIGINT", "REAL", "DOUBLE", "DATE", "TIME", "TIMESTAMP", "ROWID"]:
            type_def = f.field_type

        else:
            type_def = f.field_type

        # NULL / NOT NULL
        null_def = "NULL" if f.nullable else "NOT NULL"

        # DEFAULT
        default_def = ""
        if f.default_value not in [None, ""]:
            default_def = f" DEFAULT {f.default_value}"

        # ============================
        # 2. Primera línea (nombre largo + FOR COLUMN)
        # ============================
        col_long = f"{f.field_name_long:<30}"
        col_short = f"{f.field_name_short}"

        first_line = f"    {col_long}  FOR COLUMN {col_short}"

        # ============================
        # 3. Segunda línea (tipo alineado)
        # ============================
        second_line = f"{indent}{type_def} {null_def}{default_def},"

        lines.append(first_line)
        lines.append(second_line)

        # ============================
        # 4. Llave primaria
        # ============================
        if f.is_key and f.order_key:
            pk_fields.append((f.order_key, f.field_name_short))

        # ============================
        # 5. Label de columna
        # ============================
        if f.field_description not in [None, ""]:
            column_labels.append(
                f"    {f.field_name_short:<10} IS '{f.field_description}'"
            )

    # Ordenar llaves
    pk_fields = [name for _, name in sorted(pk_fields)]

    # ============================
    # 6. CREATE TABLE
    # ============================
    script = []
    script.append(f"-- DEFINICION DE LA TABLA")
    script.append(
        f"CREATE OR REPLACE TABLE {header.table_name_long}\n"
        f"    FOR SYSTEM NAME {header.table_name_short} (\n"
        + "\n".join(lines)
    )

    if pk_fields:
        script.append(
            f"    CONSTRAINT {header.table_name_short}_PK PRIMARY KEY ("
            + ", ".join(pk_fields)
            + ")"
        )

    script.append(");\n")

    # ============================
    # 7. LABEL ON TABLE
    # ============================
    script.append(f"-- ETIQUETA DE TABLA")
    script.append(
        f"LABEL ON TABLE {header.table_name_short} IS\n"
        f"'{header.table_name_long}';\n"
    )

    # ============================
    # 8. COMMENT ON TABLE
    # ============================
    print('Entro aqui 8. COMMENT ON TABLE')
    script.append(
        f"COMMENT ON TABLE {header.table_name_short} IS\n"
        f"'{header.table_name_long}';\n"
    )

    # ============================
    # 9. LABEL ON COLUMN
    # ============================
    if column_labels:
        print('Entro aqui 9. LABEL ON COLUMN')
        script.append(f"LABEL ON COLUMN {header.table_name_short} (")

        # Agregar comas excepto en la última línea
        for i, lbl in enumerate(column_labels):
            if i < len(column_labels) - 1:
                script.append(f"{lbl},")
            else:
                script.append(lbl)

        script.append(");\n")


    return "\n".join(script)
