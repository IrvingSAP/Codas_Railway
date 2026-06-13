"""Helpers de formato para scripts SQL generados."""

from __future__ import annotations

import textwrap


MAX_SQL_LINE_LENGTH = 78
MIN_SQL_LINE_LENGTH = 40
MAX_SQL_LINE_LENGTH_ALLOWED = 180


def enforce_max_line_length(sql: str, max_len: int = MAX_SQL_LINE_LENGTH) -> str:
    """Ajusta saltos de línea para no superar ``max_len`` caracteres por línea."""
    if max_len < 20:
        raise ValueError("max_len demasiado pequeño para formato SQL legible.")

    output_lines: list[str] = []
    for raw_line in sql.splitlines():
        if len(raw_line) <= max_len:
            output_lines.append(raw_line)
            continue

        indent_size = len(raw_line) - len(raw_line.lstrip(" "))
        indent = " " * indent_size
        available = max_len - indent_size
        if available < 20:
            available = max_len
            indent = ""

        wrapped = textwrap.wrap(
            raw_line.strip(),
            width=available,
            break_long_words=False,
            break_on_hyphens=False,
        )
        if not wrapped:
            output_lines.append(raw_line)
            continue

        output_lines.append(f"{indent}{wrapped[0]}")
        for fragment in wrapped[1:]:
            output_lines.append(f"{indent}{fragment}")

    return "\n".join(output_lines)


def resolve_sql_line_length_limit(definition) -> int:
    """Obtiene el límite por compañía/proyecto con fallback seguro."""
    company = getattr(definition, "company", None)
    configured = getattr(company, "sql_max_line_length", None) if company else None
    if isinstance(configured, int):
        return max(MIN_SQL_LINE_LENGTH, min(configured, MAX_SQL_LINE_LENGTH_ALLOWED))
    return MAX_SQL_LINE_LENGTH
