from django.contrib import admin

from apps.sp_asistido import models


@admin.register(models.SPDefinition)
class SPDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "procedure_name_short",
        "operation",
        "company",
        "header_table",
        "status",
        "script_generated",
        "updated_at",
    )
    list_filter = ("operation", "status", "script_generated")
    search_fields = ("procedure_name_short", "procedure_name_long", "schema_name")


admin.site.register(models.SPStepState)
admin.site.register(models.SPParameter)
admin.site.register(models.SPAssignment)
admin.site.register(models.SPCondition)
admin.site.register(models.SPArtifactVersion)
