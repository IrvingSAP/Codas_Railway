from django.contrib import admin

from apps.company.models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name_short",
        "name_long",
        "sql_max_line_length",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name_short", "name_long", "tax_id")
    ordering = ("name_short",)
    readonly_fields = ("created_at", "updated_at")
