"""Generación del script SQL READ (SELECT) alineado a CODAS_SP_ASISTIDO §9.7."""

from __future__ import annotations

import hashlib
from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db.models import Max
from django.utils import timezone

from apps.sp_asistido.models import SPAssignment, SPCondition, SPDefinition
from apps.sp_asistido.services.generate_delete_script import (
    _cond_sort_key,
    _where_clause_and,
    script_sha256,
)
from apps.sp_asistido.services.generate_insert_script import _db2_type_for_signature
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

# Marca en SPAssignment.source_value para columnas de proyección READ (no es literal SQL).
READ_PROJECTION_MARKER = "READ_PROJ"


def is_read_projection_assignment(a: SPAssignment) -> bool:
    return (
        a.source_kind == SPAssignment.SourceKind.LITERAL
        and (a.source_value or "").strip() == READ_PROJECTION_MARKER
    )


def _resolve_read_mode(definition: SPDefinition) -> str:
    raw = (getattr(definition, "read_mode", None) or "C").strip().upper()
    if raw not in {"C", "R"}:
        return "C"
    return raw


def _resolve_read_row_policy(definition: SPDefinition) -> str:
    raw = (getattr(definition, "read_row_policy", None) or "E").strip().upper()
    if raw not in {"E", "F"}:
        return "E"
    return raw


def _read_out_name_for_field(detail: DetailTable) -> str:
    short = (detail.field_name_short or "").strip().upper()
    if not short:
        return "O_COL"
    return f"O_{short}"[:30]


def build_read_procedure_sql(
    definition: SPDefinition,
    assignments: list[SPAssignment],
    where_conditions: list[SPCondition],
    order_conditions: list[SPCondition] | None,
    fetch_condition: SPCondition | None,
    *,
    generated_by: AbstractUser | None = None,
) -> str:
    """Genera READ-C (cursor) o READ-R (registro único) según definition.read_mode."""
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
    wcs = [c for c in (where_conditions or []) if c is not None]
    if not wcs:
        raise ValueError("READ requiere al menos un predicado WHERE.")
    where_sql = _where_clause_and(wcs)

    proj: list[SPAssignment] = [
        a
        for a in assignments
        if is_read_projection_assignment(a) and a.detail_field_id
    ]
    if not proj:
        raise ValueError("READ requiere al menos una columna de proyección.")
    proj_sorted = sorted(
        proj, key=lambda a: (a.detail_field.order_reg, a.detail_field_id)
    )
    col_list = ", ".join(
        (a.detail_field.field_name_short or "").strip().upper()
        for a in proj_sorted
        if a.detail_field
    )
    if not col_list:
        raise ValueError("No hay columnas de proyección válidas.")

    read_mode = _resolve_read_mode(definition)

    today = timezone.now().date()
    user_label = (
        generated_by.get_username()
        if generated_by and generated_by.is_authenticated
        else "—"
    )

    header_comment = (
        f"-- CODAS · SP Asistido · READ\n"
        f"-- Fecha: {today.isoformat()}\n"
        f"-- Usuario: {user_label}\n"
        f"-- Tabla diseño: {lib_table}\n"
        f"-- Operación: READ ({'CURSOR' if read_mode == 'C' else 'REGISTRO'})\n"
        f"-- Nombre largo: {definition.procedure_name_long}\n"
    )

    in_lines: list[str] = []
    seen_in: set[str] = set()
    for c in sorted(wcs, key=_cond_sort_key):
        if c.value_origin != SPCondition.ValueOrigin.IN_PARAM:
            continue
        name = (c.value_text or "").strip().upper()
        df = getattr(c, "detail_field", None)
        if not name or not df or name in seen_in:
            continue
        seen_in.add(name)
        in_lines.append(f"  IN {name} {_db2_type_for_signature(df)}")
    in_block = ",\n".join(in_lines)
    if in_block:
        in_block = in_block + ",\n"
    else:
        in_block = ""

    if read_mode == "R":
        read_row_policy = _resolve_read_row_policy(definition)
        out_proj_parts: list[str] = []
        out_proj_names: list[str] = []
        seen_out: set[str] = set()
        for a in proj_sorted:
            d = a.detail_field
            out_name = _read_out_name_for_field(d)
            if out_name in seen_out:
                continue
            seen_out.add(out_name)
            out_proj_names.append(out_name)
            out_proj_parts.append(f"  OUT {out_name} {_db2_type_for_signature(d)}")
        out_proj_block = ",\n".join(out_proj_parts)
        if out_proj_block:
            out_proj_block = out_proj_block + ",\n"

        into_cols = ", ".join(out_proj_names)

        multi_row_handler = ""
        multi_row_fetch = ""
        if read_row_policy == "E":
            multi_row_handler = """

  DECLARE EXIT HANDLER FOR SQLSTATE '21000'
  BEGIN
    SET P_ERROR_CODE = 102;
    SET P_ERROR_MSG = 'READ-R devolvió más de un registro.';
  END;"""
        else:
            multi_row_fetch = "\n  FETCH FIRST 1 ROW ONLY"

        body = f"""{header_comment}
CREATE OR REPLACE PROCEDURE {proc_qualified} (
{in_block}{out_proj_block}  OUT P_ERROR_CODE INTEGER,
  OUT P_ERROR_MSG VARCHAR(200)
)
LANGUAGE SQL
SPECIFIC {proc_short}
READS SQL DATA
BEGIN
  DECLARE v_sqlstate CHAR(5) DEFAULT '00000';
  DECLARE v_msg VARCHAR(200) DEFAULT '';

  DECLARE CONTINUE HANDLER FOR NOT FOUND
  BEGIN
    SET P_ERROR_CODE = 101;
    SET P_ERROR_MSG = 'No se encontró el registro.';
  END;
{multi_row_handler}

  DECLARE EXIT HANDLER FOR SQLSTATE '23505'
  BEGIN
    SET P_ERROR_CODE = 100;
    SET P_ERROR_MSG = 'Conflicto de unicidad en operación READ.';
  END;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1
      v_sqlstate = RETURNED_SQLSTATE,
      v_msg = MESSAGE_TEXT;
    SET P_ERROR_CODE = -1;
    SET P_ERROR_MSG = 'Error SQLSTATE=' || TRIM(v_sqlstate) || ' ' || v_msg;
  END;

  SET P_ERROR_CODE = 0;
  SET P_ERROR_MSG = 'OK';

  SELECT {col_list}
  INTO {into_cols}
  FROM {lib_table}
  WHERE {where_sql}{multi_row_fetch};
END"""
        return enforce_max_line_length(
            body,
            max_len=resolve_sql_line_length_limit(definition),
        )

    ocs = [c for c in (order_conditions or []) if c is not None and c.detail_field_id]
    ocs_sorted = sorted(ocs, key=_cond_sort_key) if ocs else []
    order_sql = ""
    order_parts: list[str] = []
    for c in ocs_sorted:
        df = getattr(c, "detail_field", None)
        if not df:
            continue
        ocol = (df.field_name_short or "").strip().upper()
        odr = (c.operator or "ASC").strip().upper()
        if odr not in ("ASC", "DESC"):
            odr = "ASC"
        if ocol:
            order_parts.append(f"{ocol} {odr}")
    if order_parts:
        order_sql = "\n    ORDER BY " + ", ".join(order_parts)

    fetch_sql = ""
    ftxt = (
        (getattr(fetch_condition, "value_text", None) or "").strip()
        if fetch_condition
        else ""
    )
    if ftxt:
        try:
            n = int(ftxt)
        except ValueError:
            n = 0
        if n > 0:
            n = max(1, min(n, 99_999))
            fetch_sql = f"\n    FETCH FIRST {n} ROWS ONLY"

    select_block = f"""  DECLARE c_read CURSOR WITH RETURN FOR
    SELECT {col_list}
    FROM {lib_table}
    WHERE {where_sql}{order_sql}{fetch_sql};"""

    body = f"""{header_comment}
CREATE OR REPLACE PROCEDURE {proc_qualified} (
{in_block}  OUT P_ERROR_CODE INTEGER,
  OUT P_ERROR_MSG VARCHAR(200)
)
LANGUAGE SQL
SPECIFIC {proc_short}
READS SQL DATA
DYNAMIC RESULT SETS 1
BEGIN
  DECLARE v_sqlstate CHAR(5) DEFAULT '00000';
  DECLARE v_msg VARCHAR(200) DEFAULT '';

  DECLARE EXIT HANDLER FOR SQLSTATE '23505'
  BEGIN
    SET P_ERROR_CODE = 100;
    SET P_ERROR_MSG = 'Conflicto de unicidad en operación READ.';
  END;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1
      v_sqlstate = RETURNED_SQLSTATE,
      v_msg = MESSAGE_TEXT;
    SET P_ERROR_CODE = -1;
    SET P_ERROR_MSG = 'Error SQLSTATE=' || TRIM(v_sqlstate) || ' ' || v_msg;
  END;

{select_block}
  OPEN c_read;

  SET P_ERROR_CODE = 0;
  SET P_ERROR_MSG = 'OK';
END"""

    return enforce_max_line_length(
        body,
        max_len=resolve_sql_line_length_limit(definition),
    )


def persist_generated_read_script(
    definition: SPDefinition,
    sql: str,
    *,
    user: AbstractUser | None,
    where_conditions: list[SPCondition],
    assignments: list[SPAssignment] | None = None,
) -> None:
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
    seen_in: set[str] = set()
    for c in sorted(
        [w for w in (where_conditions or []) if w is not None],
        key=_cond_sort_key,
    ):
        if c.value_origin != SPCondition.ValueOrigin.IN_PARAM:
            continue
        name = (c.value_text or "").strip().upper()
        df = getattr(c, "detail_field", None)
        if not name or not df or name in seen_in:
            continue
        seen_in.add(name)
        db2t = _db2_type_for_signature(df)
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

    if _resolve_read_mode(definition) == "R":
        seen_out: set[str] = set()
        for a in assignments or []:
            if not is_read_projection_assignment(a) or not a.detail_field_id:
                continue
            out_name = _read_out_name_for_field(a.detail_field)
            if out_name in seen_out:
                continue
            seen_out.add(out_name)
            SPParameter.objects.create(
                sp_definition=definition,
                direction=SPParameter.Direction.OUT,
                name=out_name,
                db2_type=_db2_type_for_signature(a.detail_field),
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
