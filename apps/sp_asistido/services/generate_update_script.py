"""Generación del script SQL UPD (UPDATE) alineado a CODAS_SP_ASISTIDO §9."""

from __future__ import annotations

import hashlib
from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db.models import Max
from django.utils import timezone

from apps.sp_asistido.models import SPAssignment, SPCondition, SPDefinition
from apps.sp_asistido.services.generate_delete_script import _where_predicate_sql
from apps.sp_asistido.services.generate_insert_script import (
    _db2_type_for_signature,
    _value_sql_fragment,
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


def script_sha256(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _where_clause_and(conditions: list[SPCondition]) -> str:
    """Une predicados WHERE con AND (misma tabla)."""
    parts: list[str] = []
    for c in conditions:
        if not getattr(c, "detail_field", None):
            continue
        parts.append(_where_predicate_sql(c))
    return " AND ".join(parts) if parts else "1=0"


def _collect_in_order(
    assignments: list[tuple],
    where_conditions: list[SPCondition],
) -> list[tuple[str, str]]:
    """Tuplas (nombre IN mayúsculas, tipo DB2) sin duplicados."""
    seen: set[str] = set()
    order: list[tuple[str, str]] = []

    for detail, sk, sv in assignments:
        if sk != SPAssignment.SourceKind.IN_PARAM:
            continue
        name = (sv or "").strip().upper()
        if not name or name in seen:
            continue
        seen.add(name)
        order.append((name, _db2_type_for_signature(detail)))

    for where_condition in where_conditions:
        if where_condition.value_origin == SPCondition.ValueOrigin.IN_PARAM:
            name = (where_condition.value_text or "").strip().upper()
            df = getattr(where_condition, "detail_field", None)
            if not name or not df:
                continue
            if name in seen:
                continue
            seen.add(name)
            order.append(
                (name, _db2_type_for_signature(df))
            )

    return order


def build_update_procedure_sql(
    definition: SPDefinition,
    assignments: list[tuple],
    where_conditions: list[SPCondition],
    *,
    concurrency_mode: str,
    generated_by: AbstractUser | None = None,
) -> str:
    """
    assignments: tuplas (DetailTable, source_kind, source_value) ordenadas para SET.
    where_conditions: predicados WHERE (orden = ordinal; se unen con AND).

    concurrency_mode: ``none`` | ``exactly_one`` (pre-condición COUNT = 1 antes de UPDATE).
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
    where_sql = _where_clause_and(where_conditions)

    set_parts = [
        f"{d.field_name_short.strip().upper()} = {_value_sql_fragment(d, sk, sv)}"
        for d, sk, sv in assignments
    ]
    set_sql = ",\n    ".join(set_parts)

    mode = (concurrency_mode or "none").strip().lower()
    if mode == "exactly_one":
        dml = f"""IF (SELECT COUNT(*) FROM {lib_table} WHERE {where_sql}) <> 1 THEN
    SET P_ERROR_CODE = 101;
    SET P_ERROR_MSG = 'Se esperaba exactamente una fila coincidente.';
  ELSE
    UPDATE {lib_table}
    SET
    {set_sql}
    WHERE {where_sql};
    SET P_ERROR_CODE = 0;
    SET P_ERROR_MSG = 'OK';
  END IF"""
    else:
        dml = f"""UPDATE {lib_table}
  SET
  {set_sql}
  WHERE {where_sql};

  SET P_ERROR_CODE = 0;
  SET P_ERROR_MSG = 'OK'"""

    today = timezone.now().date()
    user_label = (
        generated_by.get_username()
        if generated_by and generated_by.is_authenticated
        else "—"
    )
    conc_note = (
        "concurrencia: exactamente una fila"
        if mode == "exactly_one"
        else "concurrencia: sin control adicional"
    )

    header_comment = (
        f"-- CODAS · SP Asistido · UPD (UPDATE)\n"
        f"-- Fecha: {today.isoformat()}\n"
        f"-- Usuario: {user_label}\n"
        f"-- Tabla diseño: {lib_table}\n"
        f"-- Operación: UPD · {conc_note}\n"
        f"-- Nombre largo: {definition.procedure_name_long}\n"
    )

    in_order = _collect_in_order(assignments, where_conditions)
    in_lines = [f"  IN {name} {typ}" for name, typ in in_order]
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
    SET P_ERROR_MSG = 'Conflicto de unicidad en operación UPD.';
  END;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1
      v_sqlstate = RETURNED_SQLSTATE,
      v_msg = MESSAGE_TEXT;
    SET P_ERROR_CODE = -1;
    SET P_ERROR_MSG = 'Error SQLSTATE=' || TRIM(v_sqlstate) || ' ' || v_msg;
  END;

  {dml};
END"""

    return enforce_max_line_length(
        body,
        max_len=resolve_sql_line_length_limit(definition),
    )


def persist_generated_upd_script(
    definition: SPDefinition,
    sql: str,
    *,
    user: AbstractUser | None,
    assignments: list[tuple],
    where_conditions: list[SPCondition],
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
    for name, db2t in _collect_in_order(assignments, where_conditions):
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
