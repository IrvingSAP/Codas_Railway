"""Emisión de script DDL DB2 for i (modelo SIMPLE). §9.11 CODAS_TABLE_DESIGN + prototipos ScripSQL."""

from __future__ import annotations

from typing import Literal

from apps.table_design.models import DetailTable, DetailTableDb2Attributes, HeaderTable
from apps.table_design.services.auto_key_config import get_auto_key_config
from apps.table_design.services.field_validation import (
    ALLOCATE_REQUIRED_TYPES,
    CCSID_FIELD_TYPES,
    DECIMAL_TYPES,
    FIXED_LENGTH_BY_TYPE,
    LENGTH_REQUIRED_TYPES,
    NO_LENGTH_TYPES,
)

MAX_SQL_LINE = 78
INDENT_COL_NAME = "    "
INDENT_CONT = "        "
INDENT_IDENTITY_INNER = "         "
def _db2_attrs(field: DetailTable) -> DetailTableDb2Attributes | None:
    try:
        return field.db2_attributes
    except DetailTableDb2Attributes.DoesNotExist:
        return None


def _db2_bool(field: DetailTable, name: str, *, default: bool = False) -> bool:
    attrs = _db2_attrs(field)
    if attrs is None:
        return default
    return bool(getattr(attrs, name, default))


def _db2_optional(field: DetailTable, name: str):
    attrs = _db2_attrs(field)
    if attrs is None:
        return None
    return getattr(attrs, name, None)


NUMERIC_DEFAULT_FIELD_TYPES: frozenset[str] = frozenset(
    {
        DetailTable.FieldDB2Type.SMALLINT,
        DetailTable.FieldDB2Type.INTEGER,
        DetailTable.FieldDB2Type.BIGINT,
        DetailTable.FieldDB2Type.DECIMAL,
        DetailTable.FieldDB2Type.NUMERIC,
        DetailTable.FieldDB2Type.DECFLOAT,
        DetailTable.FieldDB2Type.REAL,
        DetailTable.FieldDB2Type.DOUBLE,
    }
)


def escape_sql_string_literal(value: str) -> str:
    return value.replace("'", "''")


def _qualifier_separator(qualification_style: Literal["dot", "slash", "mixed"]) -> str:
    if qualification_style == "slash":
        return "/"
    return "."


def _qualified_table_name(
    header: HeaderTable,
    *,
    qualification_style: Literal["dot", "slash", "mixed"],
) -> str:
    sch = (header.schema or "").strip()
    long_n = header.table_name_long.strip()
    if sch:
        return f"{sch}{_qualifier_separator(qualification_style)}{long_n}"
    return long_n


def _qualified_table_label_comment(
    header: HeaderTable,
    *,
    qualification_style: Literal["dot", "slash", "mixed"],
) -> str:
    """Objeto calificado estilo IBM i para LABEL/COMMENT (§9.11.6 G, prototipo básica)."""
    sch = (header.schema or "").strip()
    short = header.table_name_short.strip()
    if sch:
        if qualification_style == "mixed":
            return f"{sch}/{short}"
        sep = _qualifier_separator(qualification_style)
        return f"{sch}{sep}{short}"
    return short


def _type_core_string(f: DetailTable) -> str:
    """Solo tipo + longitud/ALLOCATE (sin NULL, CCSID, DEFAULT)."""
    t = f.field_type
    if t in FIXED_LENGTH_BY_TYPE:
        if t in (DetailTable.FieldDB2Type.SMALLINT, DetailTable.FieldDB2Type.INTEGER):
            return str(t)
        if t == DetailTable.FieldDB2Type.BIGINT:
            return "BIGINT"
        if t in (DetailTable.FieldDB2Type.REAL, DetailTable.FieldDB2Type.DOUBLE):
            return str(t)
        if t in (
            DetailTable.FieldDB2Type.DATE,
            DetailTable.FieldDB2Type.TIME,
            DetailTable.FieldDB2Type.TIMESTAMP,
            DetailTable.FieldDB2Type.ROWID,
        ):
            return str(t)
        ln = FIXED_LENGTH_BY_TYPE[t]
        return f"{t}({ln})"

    if t in LENGTH_REQUIRED_TYPES:
        ln = int(f.field_length or 0)
        if t in (DetailTable.FieldDB2Type.CHAR, DetailTable.FieldDB2Type.GRAPHIC):
            return f"{t}({ln})"
        if t in ALLOCATE_REQUIRED_TYPES:
            alloc = f.allocate_length or 0
            return f"{t}({ln}) ALLOCATE({alloc})"
        if t in (DetailTable.FieldDB2Type.BINARY, DetailTable.FieldDB2Type.VARBINARY):
            return f"{t}({ln})"
        return f"{t}({ln})"

    if t in DECIMAL_TYPES:
        p = int(f.field_length or 0)
        s = int(f.decimal_places or 0)
        return f"{t}({p}, {s})"

    if t in NO_LENGTH_TYPES:
        if t == DetailTable.FieldDB2Type.CLOB:
            return "CLOB(1048576)"
        if t == DetailTable.FieldDB2Type.BLOB:
            return "BLOB(1048576)"
        if t == DetailTable.FieldDB2Type.XML:
            return "XML"
        if t == DetailTable.FieldDB2Type.DECFLOAT:
            return "DECFLOAT(34)"
        return str(t)

    return str(t)


def _identity_lines(header: HeaderTable) -> list[str]:
    """
    Bloque IDENTITY en varias líneas (§9.11.6 C–E, prototipo incremental).
    CACHE solo si identity_cache > 0 (§9.11.2 E).
    CYCLE solo si identity_cycle es True; si no, NO CYCLE.
    """
    config = get_auto_key_config(header)
    start = int((config.identity_start if config else None) or 1)
    inc = int((config.identity_increment if config else None) or 1)
    identity_cache = config.identity_cache if config else None
    identity_cycle = bool(config.identity_cycle) if config else False
    lines: list[str] = []
    lines.append(f"{INDENT_CONT}GENERATED ALWAYS AS IDENTITY")
    lines.append(f"{INDENT_CONT}(START WITH {start} INCREMENT BY {inc}")
    lines.append(f"{INDENT_IDENTITY_INNER}NO MINVALUE NO MAXVALUE")
    cycle_kw = "CYCLE" if identity_cycle else "NO CYCLE"
    if identity_cache is not None and int(identity_cache) > 0:
        inner = f"{cycle_kw} NO ORDER CACHE {int(identity_cache)}"
    else:
        inner = f"{cycle_kw} NO ORDER"
    lines.append(f"{INDENT_IDENTITY_INNER}{inner}")
    lines.append(f"{INDENT_CONT})")
    return lines


def _flow_atomic_tokens(
    tokens: list[str],
    first_prefix: str,
    cont_prefix: str,
    max_len: int = MAX_SQL_LINE,
) -> list[str]:
    """
    Une tokens con espacio; cada token es atómico (no se parte).
    Si un token solo supera max_len, se emite igual (caso anómalo).
    """
    lines: list[str] = []
    current = ""
    prefix = first_prefix

    def flush() -> None:
        nonlocal current, prefix
        if current.strip():
            lines.append(current.rstrip())
        current = ""
        prefix = cont_prefix

    for tok in tokens:
        if not tok:
            continue
        cand = prefix + tok if not current else prefix + current + " " + tok
        if len(cand) <= max_len:
            current = (current + " " + tok).strip() if current else tok
            if not lines and first_prefix:
                current = first_prefix + current
                prefix = ""
        else:
            if current.strip():
                lines.append((prefix + current).rstrip())
            current = tok
            prefix = cont_prefix
            if len(prefix + current) > max_len:
                lines.append((prefix + current).rstrip())
                current = ""
    if current.strip() or (not current and prefix):
        lines.append((prefix + current).rstrip() if current else prefix.rstrip())
    return [ln for ln in lines if ln]


def _column_name_lines(field_long: str, field_short: str) -> list[str]:
    """Línea(s) '<LONG> FOR COLUMN <SHORT>' con corte preferido antes de FOR COLUMN."""
    core = f"{field_long.strip()} FOR COLUMN {field_short.strip()}"
    first = INDENT_COL_NAME
    if len(first + core) <= MAX_SQL_LINE:
        return [first + core]
    # Partir antes de FOR COLUMN si cabe la segunda parte en continuación
    split_at = core.find(" FOR COLUMN ")
    if split_at > 0:
        part_a = core[:split_at].rstrip()
        part_b = core[split_at:].lstrip()
        if len(first + part_a) <= MAX_SQL_LINE and len(INDENT_CONT + part_b) <= MAX_SQL_LINE:
            return [first + part_a, INDENT_CONT + part_b]
    return _flow_atomic_tokens([core], first, INDENT_CONT, MAX_SQL_LINE)


def _pre_identity_fragments(
    f: DetailTable, *, emit_default_null_for_nullable: bool
) -> list[str]:
    """
    Tipo desde ``DetailTable``; NULL/CCSID/DEFAULT solo si existe fila
    ``DetailTableDb2Attributes`` (paso 2 del flujo de campos).
    """
    t = f.field_type
    parts: list[str] = [_type_core_string(f)]
    attrs = _db2_attrs(f)
    if attrs is None:
        return parts

    nullable = bool(attrs.nullable)
    ccsid = attrs.ccsid
    default_sql_expression = attrs.default_sql_expression
    default_value = attrs.default_value
    if ccsid is not None and t in CCSID_FIELD_TYPES:
        parts.append(f"CCSID {int(ccsid)}")
    parts.append("NOT NULL" if not nullable else "NULL")
    if default_sql_expression and str(default_sql_expression).strip():
        parts.append(f"DEFAULT {str(default_sql_expression).strip()}")
    elif default_value and str(default_value).strip():
        default_literal = str(default_value).strip()
        if t in NUMERIC_DEFAULT_FIELD_TYPES:
            parts.append(f"DEFAULT {default_literal}")
        else:
            lit = escape_sql_string_literal(default_literal)
            parts.append(f"DEFAULT '{lit}'")
    elif nullable and emit_default_null_for_nullable:
        parts.append("DEFAULT NULL")
    return parts


def _column_body_lines(
    header: HeaderTable,
    f: DetailTable,
    *,
    emit_default_null_for_nullable: bool,
) -> list[str]:
    """Líneas de tipo y atributos (IDENTITY e IMPLICITLY HIDDEN en líneas propias)."""
    t = f.field_type
    has_identity = _db2_bool(f, "is_identity") and t in (
        DetailTable.FieldDB2Type.SMALLINT,
        DetailTable.FieldDB2Type.INTEGER,
        DetailTable.FieldDB2Type.BIGINT,
    )
    frags = _pre_identity_fragments(
        f, emit_default_null_for_nullable=emit_default_null_for_nullable
    )
    lines = _flow_atomic_tokens(frags, INDENT_CONT, INDENT_CONT, MAX_SQL_LINE)
    if has_identity:
        lines.extend(_identity_lines(header))
    if _db2_bool(f, "is_hidden"):
        lines.extend(
            _flow_atomic_tokens(
                ["IMPLICITLY", "HIDDEN"], INDENT_CONT, INDENT_CONT, MAX_SQL_LINE
            )
        )
    return lines


def _hard_wrap_at_spaces(
    text: str, first_indent: str, cont_indent: str, max_len: int = MAX_SQL_LINE
) -> list[str]:
    """Parte por espacios; cada token se mantiene entero (no se cortan literales con espacio)."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    cur = first_indent + words[0]
    for w in words[1:]:
        if len(cur) + 1 + len(w) <= max_len:
            cur += " " + w
        else:
            lines.append(cur)
            cur = cont_indent + w
    lines.append(cur)
    return lines


def _append_comma_to_last_non_empty(lines: list[str]) -> None:
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            if not lines[i].rstrip().endswith(","):
                lines[i] = lines[i].rstrip() + ","
            return


def _closing_paren_lines(header: HeaderTable) -> list[str]:
    """Cierre `)` + `RCDFMT` + `;` respetando 78 caracteres."""
    rf = (header.record_format_name or "").strip()
    if rf:
        one = f") RCDFMT {rf};"
        if len(one) <= MAX_SQL_LINE:
            return [one]
        return [")", f"    RCDFMT {rf};"]
    one = ");"
    if len(one) <= MAX_SQL_LINE:
        return [one]
    return [")", ";"]


def _label_on_column_group(
    qual: str,
    entries: list[tuple[str, str]],
    *,
    text_clause: bool,
) -> list[str]:
    """
    Genera bloque agrupado:
      LABEL ON COLUMN QUAL (
          COL1 IS '...',
          COL2 IS '...'
      );
    """
    if not entries:
        return []
    op = "TEXT IS" if text_clause else "IS"
    lines: list[str] = [f"LABEL ON COLUMN {qual} ("]
    for idx, (col_short, lit_escaped) in enumerate(entries):
        is_last = idx == len(entries) - 1
        lines.extend(
            _label_group_entry_lines(
                col_short.strip(),
                op,
                lit_escaped,
                trailing_comma=not is_last,
            )
        )
    lines.append(");")
    return lines


def _label_group_entry_lines(
    field_long: str, op: str, lit_escaped: str, *, trailing_comma: bool
) -> list[str]:
    """
    Entrada dentro de LABEL ON COLUMN agrupado.
    Si no cabe en una línea, usa CONCAT en líneas continuadas.
    """
    # Alineación solicitada: literal IS/TEXT IS en columna fija
    # (ancho 30 para field_name_long + 2 espacios adicionales).
    name_block = f"{field_long[:30]:<32}"
    one = f"    {name_block}{op} '{lit_escaped}'"
    if trailing_comma:
        one += ","
    if len(one) <= MAX_SQL_LINE:
        return [one]

    base = f"    {name_block}{op} "
    # Presupuestos para que no se excedan 78 caracteres ni en línea base ni en CONCAT.
    first_budget = MAX_SQL_LINE - len(base) - len("''")
    cont_indent = " " * len(base)
    cont_budget = MAX_SQL_LINE - len(cont_indent) - len("CONCAT ''")
    chunk_size = min(first_budget, cont_budget)
    if chunk_size < 8:
        chunk_size = 8
    chunks: list[str] = []
    i = 0
    while i < len(lit_escaped):
        chunks.append(lit_escaped[i : i + chunk_size])
        i += chunk_size

    out: list[str] = [f"{base}'{chunks[0]}'"]
    for ch in chunks[1:]:
        seg = f"CONCAT '{ch}'"
        candidate = out[-1] + " " + seg
        if len(candidate) <= MAX_SQL_LINE:
            out[-1] = candidate
        else:
            out.append(f"{cont_indent}{seg}")
    if trailing_comma:
        out[-1] = out[-1] + ","
    return out


def _pk_lines(header: HeaderTable, key_fields: list[DetailTable]) -> list[str]:
    cols = [k.field_name_short.strip() for k in key_fields]
    pk_cols = ", ".join(cols)
    pk_name = (header.pk_constraint_name or "").strip()
    if pk_name:
        head = f"{INDENT_COL_NAME}CONSTRAINT {pk_name} PRIMARY KEY ("
        raw = f"{head}{pk_cols})"
    else:
        head = f"{INDENT_COL_NAME}PRIMARY KEY ("
        raw = f"{head}{pk_cols})"
    if len(raw) <= MAX_SQL_LINE:
        return [raw]
    if len(head) > MAX_SQL_LINE:
        return _hard_wrap_at_spaces(raw, INDENT_COL_NAME, INDENT_CONT, MAX_SQL_LINE)
    body = _hard_wrap_at_spaces(pk_cols + ")", INDENT_CONT, INDENT_CONT, MAX_SQL_LINE)
    return [head] + body


def _table_label_comment_lines(qual: str, escaped_long: str) -> list[str]:
    """LABEL ON TABLE y COMMENT ON TABLE; parten literales largos con CONCAT."""
    stmts = [
        ("LABEL ON TABLE", f"'{escaped_long}'"),
        ("COMMENT ON TABLE", f"'{escaped_long}'"),
    ]
    out: list[str] = []
    for kw, lit_part in stmts:
        base = f"{kw} {qual} IS {lit_part};"
        if len(base) <= MAX_SQL_LINE:
            out.append(base)
            continue
        # IS en siguiente línea
        out.append(f"{kw} {qual} IS")
        inner = lit_part.strip("'")
        chunks = []
        i = 0
        budget = MAX_SQL_LINE - len(f"{INDENT_CONT}CONCAT ''") - 5
        while i < len(inner):
            chunks.append(inner[i : i + max(10, budget)])
            i += max(10, budget)
        if not chunks:
            out.append(f"{INDENT_CONT}'';")
            continue
        out.append(f"{INDENT_CONT}'{chunks[0]}'")
        for ch in chunks[1:]:
            seg = f"CONCAT '{ch}'"
            if len(out[-1] + " " + seg) <= MAX_SQL_LINE:
                out[-1] = out[-1] + " " + seg
            else:
                out.append(f"{INDENT_CONT}{seg}")
        if not out[-1].endswith(";"):
            out[-1] = out[-1].rstrip() + ";"
    return out


def script_line_length_violations(sql: str, max_len: int = MAX_SQL_LINE) -> list[tuple[int, str]]:
    """Para tests: (número de línea 1-based, contenido) si supera max_len."""
    bad: list[tuple[int, str]] = []
    for i, line in enumerate(sql.splitlines(), start=1):
        if len(line) > max_len:
            bad.append((i, line))
    return bad


def build_simple_sql_script(
    header: HeaderTable,
    *,
    emit_set_current_schema: bool = False,
    qualification_style: Literal["dot", "slash", "mixed"] = "mixed",
    emit_default_null_for_nullable: bool = False,
) -> tuple[bool, str, list[str]]:
    """
    Genera DDL SIMPLE para ``header`` (CREATE TABLE + labels/comentarios).

    **Tipo de columna:** siempre desde ``DetailTable`` (``field_type``, longitud,
    ``allocate_length``).

    **Atributos DB2** (``NULL``/``NOT NULL``, ``CCSID``, ``DEFAULT``, ``IDENTITY``,
    ``IMPLICITLY HIDDEN``): solo si existe fila ``DetailTableDb2Attributes`` (paso 2
    del flujo de campos). Sin esa fila, la columna se emite únicamente con su tipo.

    ``emit_default_null_for_nullable`` añade ``DEFAULT NULL`` en columnas anulables
    que ya tienen fila de atributos y carecen de otro default; no infiere nullability
    cuando no hay paso 2.
    """
    errors: list[str] = []
    if qualification_style not in {"dot", "slash", "mixed"}:
        return (
            False,
            "",
            [
                "qualification_style inválido. Use 'dot', 'slash' o 'mixed'.",
            ],
        )
    if header.table_model != HeaderTable.TableModel.SIMPLE:
        errors.append(
            "La generación DDL automática solo está disponible para modelo de tabla "
            "«Simple» (S)."
        )
        return False, "", errors

    sch = (header.schema or "").strip()
    if not sch:
        errors.append("El esquema / librería es obligatorio para calificar el CREATE TABLE.")
        return False, "", errors

    fields = list(
        header.fields.filter(status=DetailTable.Status.ACTIVE)
        .select_related("db2_attributes")
        .order_by("order_reg", "pk")
    )
    if not fields:
        errors.append("No hay campos activos para generar el script.")
        return False, "", errors

    for f in fields:
        if f.field_type in ALLOCATE_REQUIRED_TYPES:
            if not f.allocate_length or f.allocate_length < 1:
                errors.append(
                    f"Campo {f.field_name_short}: ALLOCATE obligatorio y > 0 para "
                    f"{f.field_type}."
                )
        attrs = _db2_attrs(f)
        if (
            attrs is not None
            and attrs.is_identity
            and attrs.nullable
        ):
            errors.append(
                f"Campo {f.field_name_short}: IDENTITY requiere NOT NULL."
            )
        if attrs is not None and attrs.is_identity and f.field_type not in (
            DetailTable.FieldDB2Type.SMALLINT,
            DetailTable.FieldDB2Type.INTEGER,
            DetailTable.FieldDB2Type.BIGINT,
        ):
            errors.append(
                f"Campo {f.field_name_short}: IDENTITY solo con SMALLINT, INTEGER o BIGINT."
            )
        if f.is_key and f.order_key is None:
            errors.append(
                f"Campo {f.field_name_short}: es llave; indique el orden de la llave."
            )

    id_count = sum(1 for f in fields if _db2_bool(f, "is_identity"))
    if id_count > 1:
        errors.append("Solo puede existir una columna IDENTITY en el script.")

    key_candidates = [f for f in fields if f.is_key]
    key_fields = [f for f in key_candidates if f.order_key is not None]
    key_fields.sort(key=lambda x: (x.order_key or 0, x.pk))
    if header.is_field_key and not key_fields:
        errors.append(
            "La cabecera indica «Tiene llave», pero no hay columnas de llave activas "
            "con orden definido."
        )

    if errors:
        return False, "", errors

    q_table = _qualified_table_name(header, qualification_style=qualification_style)
    short = header.table_name_short.strip()
    qual_slash = _qualified_table_label_comment(
        header, qualification_style=qualification_style
    )

    lines: list[str] = []
    if emit_set_current_schema:
        lines.append(f"SET CURRENT SCHEMA {sch};")
        lines.append("")
    lines.append("-- DEFINICION DE LA TABLA (CODAS table_design)")
    create_head = f"CREATE OR REPLACE TABLE {q_table}"
    if len(create_head) <= MAX_SQL_LINE:
        lines.append(create_head)
    else:
        lines.extend(_flow_atomic_tokens(create_head.split(), "", INDENT_COL_NAME, MAX_SQL_LINE))
    for_sys = f"{INDENT_COL_NAME}FOR SYSTEM NAME {short} ("
    if len(for_sys) <= MAX_SQL_LINE:
        lines.append(for_sys)
    else:
        lines.append(f"{INDENT_COL_NAME}FOR SYSTEM NAME {short}")
        lines.append(f"{INDENT_COL_NAME}(")

    for fi, f in enumerate(fields):
        lines.append("")
        lines.extend(_column_name_lines(f.field_name_long, f.field_name_short))
        body = _column_body_lines(
            header,
            f,
            emit_default_null_for_nullable=emit_default_null_for_nullable,
        )
        lines.extend(body)
        is_last_field = fi == len(fields) - 1 and not key_fields
        if not is_last_field:
            _append_comma_to_last_non_empty(lines)

    if key_fields:
        lines.append("")
        lines.extend(_pk_lines(header, key_fields))

    lines.extend(_closing_paren_lines(header))
    lines.append("")

    lbl = escape_sql_string_literal(header.table_name_long.strip())
    lines.extend(_table_label_comment_lines(qual_slash, lbl))

    label_entries: list[tuple[str, str]] = []
    text_entries: list[tuple[str, str]] = []
    for f in fields:
        cl = (f.column_label or "").strip()
        if cl:
            label_entries.append(
                (f.field_name_long.strip(), escape_sql_string_literal(cl))
            )
        ct = (f.column_text or "").strip()
        if ct:
            text_entries.append(
                (f.field_name_long.strip(), escape_sql_string_literal(ct))
            )

    if label_entries:
        lines.append("")
        lines.extend(_label_on_column_group(qual_slash, label_entries, text_clause=False))
    if text_entries:
        lines.append("")
        lines.extend(_label_on_column_group(qual_slash, text_entries, text_clause=True))

    sql = "\n".join(lines) + "\n"
    viol = script_line_length_violations(sql)
    if viol:
        # No debería ocurrir; si ocurre, devolver error explícito
        errors = [
            f"Línea {n} supera {MAX_SQL_LINE} caracteres (generador): {s[:40]}…"
            for n, s in viol[:3]
        ]
        return False, "", errors

    return True, sql, []


def build_simple_sql_script_or_raise(
    header: HeaderTable,
    *,
    emit_set_current_schema: bool = False,
    qualification_style: Literal["dot", "slash", "mixed"] = "mixed",
    emit_default_null_for_nullable: bool = False,
) -> str:
    ok, sql, errs = build_simple_sql_script(
        header,
        emit_set_current_schema=emit_set_current_schema,
        qualification_style=qualification_style,
        emit_default_null_for_nullable=emit_default_null_for_nullable,
    )
    if not ok:
        raise ValueError("; ".join(errs))
    return sql
