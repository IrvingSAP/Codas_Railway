"""Validación del asistente UPD (UPDATE)."""

from __future__ import annotations

from apps.sp_asistido.services.add_validation import validate_step3_columns
from apps.table_design.models import DetailTable


def validate_upd_set_column_ids(
    selected_ids: list[int], header_id: int, company_id: int
) -> tuple[list[int], list[str]]:
    """Columnas SET: mismas reglas que insertables ADD; mensajes orientados a UPDATE."""
    ids, errors = validate_step3_columns(selected_ids, header_id, company_id)
    key_ids = set(
        DetailTable.objects.filter(
            id__in=ids,
            header_id=header_id,
            status=DetailTable.Status.ACTIVE,
            is_key=True,
        ).values_list("id", flat=True)
    )
    if key_ids:
        ids = [i for i in ids if i not in key_ids]
        errors.append(
            "No se permite actualizar campos clave en UPDATE (SET)."
        )
    mapped = [
        e.replace("INSERT", "UPDATE (SET)")
        .replace("insertables", "actualizables")
        for e in errors
    ]
    return ids, mapped


def normalize_col_flags(post_data, detail_ids: list[int]) -> list[int]:
    """Devuelve ids de detalle marcados con checkbox col_<id> en POST."""
    out: list[int] = []
    for pk in detail_ids:
        key = f"col_{pk}"
        if post_data.get(key):
            out.append(pk)
    return out


def normalize_where_col_flags(post_data, detail_ids: list[int]) -> list[int]:
    """Checkbox where_col_<id> (paso WHERE UPD)."""
    out: list[int] = []
    for pk in detail_ids:
        if post_data.get(f"where_col_{pk}"):
            out.append(pk)
    return out


def ordered_selected_detail_ids(
    details: list, selected_ids: list[int]
) -> list[int]:
    """Conserva el orden de `details` para los ids seleccionados."""
    s = set(selected_ids)
    return [d.id for d in details if d.id in s]


def validate_concurrency_mode(mode: str) -> list[str]:
    m = (mode or "").strip().lower()
    if m not in ("none", "exactly_one"):
        return ["Modo de concurrencia no válido."]
    return []
