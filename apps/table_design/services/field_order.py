"""Orden de registro (`order_reg`) para campos de una cabecera."""

from __future__ import annotations

from django.db import transaction
from django.db.models import Max

from apps.table_design.models import DetailTable, HeaderTable


def get_next_order_reg(header: HeaderTable) -> int:
    current = header.fields.aggregate(m=Max("order_reg"))["m"]
    return (current or 0) + 1


@transaction.atomic
def normalize_order_reg(header: HeaderTable) -> None:
    """Renumera ``order_reg`` de 1..n según el orden actual."""
    rows = list(header.fields.order_by("order_reg", "pk"))
    updates: list[DetailTable] = []
    for i, row in enumerate(rows, start=1):
        if row.order_reg != i:
            row.order_reg = i
            updates.append(row)
    if updates:
        DetailTable.objects.bulk_update(updates, ["order_reg"])


def _temp_order_reg(header: HeaderTable) -> int:
    m = header.fields.aggregate(mx=Max("order_reg"))["mx"] or 0
    return m + 10_000


@transaction.atomic
def swap_order_reg(header: HeaderTable, a: DetailTable, b: DetailTable) -> None:
    """Intercambia ``order_reg`` entre dos filas de la misma cabecera (evita huecos y valores inválidos)."""
    if a.header_id != header.pk or b.header_id != header.pk:
        raise ValueError("Los campos deben pertenecer a la cabecera indicada.")
    tmp = _temp_order_reg(header)
    oa, ob = a.order_reg, b.order_reg
    DetailTable.objects.filter(pk=a.pk).update(order_reg=tmp)
    DetailTable.objects.filter(pk=b.pk).update(order_reg=oa)
    DetailTable.objects.filter(pk=a.pk).update(order_reg=ob)


def move_field_up(header: HeaderTable, field: DetailTable) -> bool:
    prev = (
        header.fields.filter(order_reg__lt=field.order_reg)
        .order_by("-order_reg")
        .first()
    )
    if prev is None:
        return False
    swap_order_reg(header, field, prev)
    return True


def move_field_down(header: HeaderTable, field: DetailTable) -> bool:
    nxt = (
        header.fields.filter(order_reg__gt=field.order_reg)
        .order_by("order_reg")
        .first()
    )
    if nxt is None:
        return False
    swap_order_reg(header, field, nxt)
    return True
