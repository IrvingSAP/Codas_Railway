"""Validación del asistente READ (SELECT)."""

from __future__ import annotations

_FETCH_MIN = 1
_FETCH_MAX = 99_999


def validate_read_column_selection(
    selected_ids: list[int], header_id: int, company_id: int
) -> list[str]:
    """F.3: al menos una columna en el SELECT; activas y de la cabecera."""
    from apps.sp_asistido.services.add_validation import validate_step3_columns

    if not selected_ids:
        return ["Seleccione al menos una columna para el resultado (SELECT)."]
    _ids, errors = validate_step3_columns(
        selected_ids, header_id, company_id
    )
    if errors:
        return [
            e.replace("INSERT", "SELECT (READ) ")
            .replace("insertables", "seleccionables")
            for e in errors
        ]
    return []


def validate_read_order_and_fetch(
    order_by: list[tuple[int, str]],
    *,
    fetch_unlimited: bool,
    fetch_limit_text: str,
    allowed_detail_ids: set[int],
) -> list[str]:
    """
    F.5: 0..N columnas de orden (cada par id + ASC|DESC) en el orden dado; FETCH opcional
    (sin límite) o 1..99_999; todas las columnas de ORDER deben estar en el SELECT.
    """
    errors: list[str] = []
    seen: set[int] = set()
    for did, dr in order_by:
        d = (dr or "").strip().upper()
        if d not in ("ASC", "DESC"):
            errors.append("Cada columna con orden usa ASC o DESC.")
            continue
        if did not in allowed_detail_ids:
            errors.append("Solo puede ordenar por columnas incluidas en el SELECT.")
            continue
        if did in seen:
            errors.append("No repita la misma columna en el orden (use una fila).")
            continue
        seen.add(did)

    if not fetch_unlimited:
        t = (fetch_limit_text or "").strip()
        try:
            n = int(t) if t else 0
        except ValueError:
            n = 0
        if n < _FETCH_MIN or n > _FETCH_MAX:
            errors.append(
                f"Con límite, indique un entero entre {_FETCH_MIN} y {_FETCH_MAX} de filas."
            )
    return errors
