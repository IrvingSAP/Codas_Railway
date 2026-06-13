
from .models import DetailTable

def get_next_order_reg(header):
    last = DetailTable.objects.filter(header=header).order_by("-order_reg").first()
    if last:
        return last.order_reg + 1
    return 1

def normalize_order_reg(header):
    fields = header.fields.all().order_by("order_reg")
    new_order = 1

    for f in fields:
        if f.order_reg != new_order:
            f.order_reg = new_order
            f.save()
        new_order += 1




