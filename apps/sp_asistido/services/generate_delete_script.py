"""Generación del script SQL DLT (DELETE / baja lógica) alineado a CODAS_SP_ASISTIDO §9."""

from __future__ import annotations

import hashlib
from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db.models import Max
from django.utils import timezone

from apps.sp_asistido.models import SPCondition, SPDefinition
from apps.sp_asistido.services.generate_insert_script import (
    _db2_type_for_signature,
    _format_literal_for_column,
)
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


def script_sha256(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _where_value_sql(condition: SPCondition) -> str:
    detail = condition.detail_field
    if not detail:
        return "NULL"
    if condition.value_origin == SPCondition.ValueOrigin.IN_PARAM:
        return (condition.value_text or "").strip().upper() or "NULL"
    if condition.value_origin == SPCondition.ValueOrigin.LITERAL:
        return _format_literal_for_column(detail, condition.value_text)
    return "NULL"


def _where_predicate_sql(condition: SPCondition) -> str:
    col = (condition.detail_field.field_name_short or "").strip().upper()
    op = (condition.operator or "=").strip()
    if op not in ("=", "<>"):
        op = "="
    rhs = _where_value_sql(condition)
    return f"{col} {op} {rhs}"


def _cond_sort_key(c) -> tuple:
    oid = getattr(c, "ordinal", 0) or 0
    p = getattr(c, "pk", None) or getattr(c, "id", None) or 0
    return (oid, p)


def _where_clause_and(conditions: list[SPCondition]) -> str:
    """Une predicados WHERE con AND (misma tabla, orden ``ordinal`` / id)."""
    if not conditions:
        return "1=0"
    parts: list[str] = []
    for c in sorted(conditions, key=_cond_sort_key):
        if not getattr(c, "detail_field", None):
            continue
        parts.append(_where_predicate_sql(c))
    return " AND ".join(parts) if parts else "1=0"


def build_delete_procedure_sql(
    definition: SPDefinition,
    where_conditions: list[SPCondition],
    *,
    mode_physical: bool,
    logical_status_detail: DetailTable | None,
    logical_value_raw: str,
    generated_by: AbstractUser | None = None,
) -> str:
    """
    DML principal: DELETE (físico) o UPDATE de estado (lógico).
    ``where_conditions``: al menos un predicado WHERE (D.8); se unen con AND.
    """
    if not where_conditions:
        where_conditions = []
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
    where_sql = _where_clause_and(list(where_conditions))

    if mode_physical:
        dml = f"DELETE FROM {lib_table}\n  WHERE {where_sql};"
    else:
        if not logical_status_detail:
            raise ValueError("Modo lógico requiere campo de estado en detalle.")
        set_col = (logical_status_detail.field_name_short or "").strip().upper()
        set_val = _format_literal_for_column(
            logical_status_detail, logical_value_raw or ""
        )
        dml = (
            f"UPDATE {lib_table}\n"
            f"  SET {set_col} = {set_val}\n"
            f"  WHERE {where_sql};"
        )

    today = timezone.now().date()
    user_label = (
        generated_by.get_username()
        if generated_by and generated_by.is_authenticated
        else "—"
    )
    op_label = "DELETE" if mode_physical else "UPDATE (baja lógica)"

    header_comment = (
        f"-- CODAS · SP Asistido · DLT\n"
        f"-- Fecha: {today.isoformat()}\n"
        f"-- Usuario: {user_label}\n"
        f"-- Tabla diseño: {lib_table}\n"
        f"-- Operación: DLT · {op_label}\n"
        f"-- Nombre largo: {definition.procedure_name_long}\n"
    )

    in_lines: list[str] = []
    seen_in: set[str] = set()
    for where_condition in sorted(
        [c for c in (where_conditions or []) if c is not None],
        key=_cond_sort_key,
    ):
        if where_condition.value_origin == SPCondition.ValueOrigin.IN_PARAM:
            name = (where_condition.value_text or "").strip().upper()
            df = getattr(where_condition, "detail_field", None)
            if not name or name in seen_in or not df:
                continue
            seen_in.add(name)
            typ = _db2_type_for_signature(df)
            in_lines.append(f"  IN {name} {typ}")
    in_block = ",\n".join(in_lines)
    if in_block:
        in_block = in_block + ",\n"
    else:
        in_block = ""

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
    SET P_ERROR_MSG = 'Conflicto de unicidad en operación DLT.';
  END;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1
      v_sqlstate = RETURNED_SQLSTATE,
      v_msg = MESSAGE_TEXT;
    SET P_ERROR_CODE = -1;
    SET P_ERROR_MSG = 'Error SQLSTATE=' || TRIM(v_sqlstate) || ' ' || v_msg;
  END;

  {dml}

  SET P_ERROR_CODE = 0;
  SET P_ERROR_MSG = 'OK';
END"""

    return enforce_max_line_length(
        body,
        max_len=resolve_sql_line_length_limit(definition),
    )


def persist_generated_dlt_script(
    definition: SPDefinition,
    sql: str,
    *,
    user: AbstractUser | None,
    where_conditions: list[SPCondition],
) -> None:
    """Versión SQL, parámetros IN del WHERE (múltiples) y OUT §9.2."""
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
    definition.current_step = 6
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
