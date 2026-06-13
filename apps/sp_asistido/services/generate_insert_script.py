"""Generación del script SQL ADD (INSERT) alineado a CODAS_SP_ASISTIDO §9."""

from __future__ import annotations

import hashlib
from datetime import date
from django.contrib.auth.models import AbstractUser
from django.db.models import Max
from django.utils import timezone

from apps.sp_asistido.models import SPAssignment, SPDefinition
from apps.sp_asistido.services.sql_qualification import (
    default_sp_qualification_style,
    sp_qualified_procedure_target,
    sp_qualified_table_dml,
)
from apps.sp_asistido.services.script_formatting import (
    enforce_max_line_length,
    resolve_sql_line_length_limit,
)
from apps.table_design.models import DetailTable


def _sql_string_literal(value: str) -> str:
    """Comilla simple duplicada según estándar SQL."""
    return "'" + (value or "").replace("'", "''") + "'"


def _format_literal_for_column(detail: DetailTable, raw: str) -> str:
    """Formatea literal SQL según tipo de columna (aproximación segura)."""
    raw = (raw or "").strip()
    ft = detail.field_type
    numeric_types = {
        DetailTable.FieldDB2Type.SMALLINT,
        DetailTable.FieldDB2Type.INTEGER,
        DetailTable.FieldDB2Type.BIGINT,
        DetailTable.FieldDB2Type.REAL,
        DetailTable.FieldDB2Type.DOUBLE,
        DetailTable.FieldDB2Type.DECFLOAT,
    }
    decimal_types = {
        DetailTable.FieldDB2Type.DECIMAL,
        DetailTable.FieldDB2Type.NUMERIC,
    }
    if ft in numeric_types | decimal_types:
        return raw if raw else "NULL"
    # texto y resto: entre comillas
    return _sql_string_literal(raw)


def _db2_type_for_signature(detail: DetailTable) -> str:
    """Tipo DB2 para firma IN (p. ej. VARCHAR(40), DECIMAL(9,0))."""
    ft = detail.field_type
    if ft in (
        DetailTable.FieldDB2Type.CHAR,
        DetailTable.FieldDB2Type.VARCHAR,
        DetailTable.FieldDB2Type.GRAPHIC,
        DetailTable.FieldDB2Type.VARGRAPHIC,
        DetailTable.FieldDB2Type.BINARY,
        DetailTable.FieldDB2Type.VARBINARY,
    ):
        ln = detail.field_length or 1
        return f"{ft}({ln})"
    if ft in (DetailTable.FieldDB2Type.DECIMAL, DetailTable.FieldDB2Type.NUMERIC):
        prec = detail.field_length or 1
        scale = detail.decimal_places if detail.decimal_places is not None else 0
        return f"{ft}({prec},{scale})"
    return str(ft)


def format_db2_type_for_parameter(detail: DetailTable) -> str:
    """Tipo DB2 para mostrar en firma (paso 6); mismo criterio que el script."""
    return _db2_type_for_signature(detail)


def _value_sql_fragment(
    detail: DetailTable, source_kind: str, source_value: str
) -> str:
    sk = source_kind
    sv = (source_value or "").strip()
    if sk == SPAssignment.SourceKind.NULL:
        return "NULL"
    if sk == SPAssignment.SourceKind.IN_PARAM:
        return sv.upper() if sv else "NULL"
    if sk == SPAssignment.SourceKind.LITERAL:
        return _format_literal_for_column(detail, sv)
    if sk == SPAssignment.SourceKind.EXPR:
        return sv
    return "NULL"


def build_insert_procedure_sql(
    definition: SPDefinition,
    assignments: list[tuple[DetailTable, str, str]],
    *,
    generated_by: AbstractUser | None = None,
) -> str:
    """
    assignments: tuplas (DetailTable, source_kind, source_value) en orden INSERT.

    Incluye cabecera comentada (§.cursorrules 6), OUT mínimos §9.2 y handlers §9.5.
    """
    header = definition.header_table
    schema = definition.schema_name.strip().upper()
    proc_short = definition.procedure_name_short.strip().upper()
    proc_long = definition.procedure_name_long.strip().upper()
    style = default_sp_qualification_style()
    lib_table = sp_qualified_table_dml(
        header.schema, header.table_name_short, style=style
    )
    proc_qualified = sp_qualified_procedure_target(
        schema, proc_long, style=style
    )

    in_lines: list[str] = []
    in_order: list[tuple[str, str]] = []
    seen_in: set[str] = set()

    for detail, sk, sv in assignments:
        if sk == SPAssignment.SourceKind.IN_PARAM:
            name = (sv or "").strip().upper()
            if name and name not in seen_in:
                seen_in.add(name)
                in_order.append((name, _db2_type_for_signature(detail)))

    for name, typ in in_order:
        in_lines.append(f"  IN {name} {typ}")

    in_block = ",\n".join(in_lines)
    if in_block:
        in_block = in_block + ",\n"
    else:
        in_block = ""

    col_names = ", ".join(d.field_name_short.strip().upper() for d, _, _ in assignments)
    values_sql = ", ".join(
        _value_sql_fragment(d, sk, sv) for d, sk, sv in assignments
    )

    today = timezone.now().date()
    user_label = (
        generated_by.get_username() if generated_by and generated_by.is_authenticated else "—"
    )

    header_comment = (
        f"-- CODAS · SP Asistido · ADD (INSERT)\n"
        f"-- Fecha: {today.isoformat()}\n"
        f"-- Usuario: {user_label}\n"
        f"-- Tabla diseño: {lib_table}\n"
        f"-- Operación: ADD\n"
        f"-- Nombre largo: {definition.procedure_name_long}\n"
    )

    body = f"""{header_comment}
CREATE OR REPLACE PROCEDURE {proc_qualified} (
{in_block}  OUT P_ERROR_CODE INTEGER,
  OUT P_ERROR_MSG VARCHAR(200)
)
LANGUAGE SQL
SPECIFIC {proc_short}
MODIFIES SQL DATA
BEGIN
  DECLARE v_sqlstate CHAR(5) DEFAULT '00000';
  DECLARE v_msg VARCHAR(200) DEFAULT '';

  DECLARE EXIT HANDLER FOR SQLSTATE '23505'
  BEGIN
    SET P_ERROR_CODE = 100;
    SET P_ERROR_MSG = 'El registro ya existe.';
  END;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1
      v_sqlstate = RETURNED_SQLSTATE,
      v_msg = MESSAGE_TEXT;
    SET P_ERROR_CODE = -1;
    SET P_ERROR_MSG = 'Error SQLSTATE=' || TRIM(v_sqlstate) || ' ' || v_msg;
  END;

  INSERT INTO {lib_table} ({col_names})
  VALUES ({values_sql});

  SET P_ERROR_CODE = 0;
  SET P_ERROR_MSG = 'OK';
END"""

    return enforce_max_line_length(
        body,
        max_len=resolve_sql_line_length_limit(definition),
    )


def script_sha256(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def persist_generated_script(
    definition: SPDefinition,
    sql: str,
    *,
    user: AbstractUser | None,
) -> None:
    """Marca versión de artefacto y banderas en cabecera (llamar dentro de atomic)."""
    from apps.sp_asistido.models import SPArtifactVersion, SPParameter

    agg = definition.artifact_versions.aggregate(m=Max("version"))
    ver = (agg.get("m") or 0) + 1

    definition.artifact_versions.filter(is_current=True).update(is_current=False)

    SPArtifactVersion.objects.create(
        sp_definition=definition,
        version=ver,
        sql_script=sql,
        script_hash=script_sha256(sql),
        is_current=True,
        created_by=user if user and user.is_authenticated else None,
        updated_by=user if user and user.is_authenticated else None,
    )

    definition.parameters.all().delete()
    ordinal = 1
    assignments = list(
        definition.assignments.select_related("detail_field").order_by(
            "detail_field__order_reg", "id"
        )
    )
    seen: set[str] = set()
    for a in assignments:
        if a.source_kind != SPAssignment.SourceKind.IN_PARAM:
            continue
        name = (a.source_value or "").strip().upper()
        if not name or name in seen:
            continue
        seen.add(name)
        db2t = _db2_type_for_signature(a.detail_field)
        SPParameter.objects.create(
            sp_definition=definition,
            direction=SPParameter.Direction.IN,
            name=name,
            db2_type=db2t,
            ordinal=ordinal,
            created_by=user if user and user.is_authenticated else None,
            updated_by=user if user and user.is_authenticated else None,
        )
        ordinal += 1

    SPParameter.objects.create(
        sp_definition=definition,
        direction=SPParameter.Direction.OUT,
        name="P_ERROR_CODE",
        db2_type="INTEGER",
        ordinal=ordinal,
        created_by=user if user and user.is_authenticated else None,
        updated_by=user if user and user.is_authenticated else None,
    )
    ordinal += 1
    SPParameter.objects.create(
        sp_definition=definition,
        direction=SPParameter.Direction.OUT,
        name="P_ERROR_MSG",
        db2_type="VARCHAR(200)",
        ordinal=ordinal,
        created_by=user if user and user.is_authenticated else None,
        updated_by=user if user and user.is_authenticated else None,
    )

    definition.script_generated = True
    definition.script_date = date.today()
    definition.current_step = 7
    definition.updated_by = user if user and user.is_authenticated else None
    definition.save(
        update_fields=[
            "script_generated",
            "script_date",
            "current_step",
            "updated_at",
            "updated_by",
        ]
    )
