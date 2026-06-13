from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.company.models import Company
from apps.sources.models import SourceTemplate
from apps.sp_asistido.models import SPDefinition
from apps.table_design.models import HeaderTable


class AuditModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        abstract = True


class MaintenanceDefinition(AuditModel):
    class Status(models.TextChoices):
        DRAFT = "D", "Borrador"
        GENERATED = "G", "Generado"
        ERROR = "E", "Error"
        INACTIVE = "I", "Inactivo"

    class GenerationResult(models.TextChoices):
        SUCCESS = "S", "Success"
        ERROR = "E", "Error"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="maintenance_definitions",
        verbose_name="Compañía",
    )
    name_short = models.CharField(max_length=10, verbose_name="Nombre corto")
    name_long = models.CharField(max_length=50, verbose_name="Nombre largo")
    comment = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Comentario",
    )
    header_table = models.ForeignKey(
        HeaderTable,
        on_delete=models.PROTECT,
        related_name="maintenance_definitions",
        verbose_name="Tabla base",
    )
    dspf_template = models.ForeignKey(
        SourceTemplate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="maintenance_definitions_dspf",
        verbose_name="Plantilla DSPF",
    )
    sqlrpgle_template = models.ForeignKey(
        SourceTemplate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="maintenance_definitions_sqlrpgle",
        verbose_name="Plantilla SQLRPGLE",
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Estado",
    )
    current_step = models.PositiveSmallIntegerField(default=1, verbose_name="Paso actual")
    is_generation_pending = models.BooleanField(default=False, verbose_name="Generación pendiente")
    last_generation_at = models.DateTimeField(null=True, blank=True, verbose_name="Última generación")
    last_generation_result = models.CharField(
        max_length=1,
        choices=GenerationResult.choices,
        null=True,
        blank=True,
        verbose_name="Resultado última generación",
    )
    last_error_message = models.CharField(
        max_length=300,
        blank=True,
        default="",
        verbose_name="Último error",
    )

    class Meta:
        verbose_name = "Definición de mantenimiento"
        verbose_name_plural = "Definiciones de mantenimiento"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name_short"],
                name="uq_maintenance_builder_company_name_short",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["company", "name_short"]),
        ]

    def __str__(self) -> str:
        return f"{self.name_short} ({self.company.name_short})"

    def clean(self) -> None:
        super().clean()
        if self.header_table_id and self.company_id and self.header_table.company_id != self.company_id:
            raise ValidationError({"header_table": "La tabla base no pertenece a la compañía seleccionada."})
        self._validate_template_scope_and_type(self.dspf_template, SourceTemplate.SourceType.DSPF, "dspf_template")
        self._validate_template_scope_and_type(
            self.sqlrpgle_template,
            SourceTemplate.SourceType.SQLRPGLE,
            "sqlrpgle_template",
        )

    def _validate_template_scope_and_type(
        self,
        template: SourceTemplate | None,
        expected_type: str,
        field_name: str,
    ) -> None:
        if not template:
            return
        if template.source_type != expected_type:
            raise ValidationError({field_name: f"La plantilla debe ser de tipo {expected_type}."})
        if template.company_id and template.company_id != self.company_id:
            raise ValidationError({field_name: "La plantilla no pertenece a la compañía ni es global."})


class MaintenanceSpSelection(AuditModel):
    class OperationRole(models.TextChoices):
        READ_C = "READ_C", "READ-C"
        ADD = "ADD", "ADD"
        READ_R = "READ_R", "READ-R"
        UPD = "UPD", "UPD"
        DLT = "DLT", "DLT"

    class SelectionStatus(models.TextChoices):
        SELECTED = "S", "Seleccionado"
        NOT_SELECTED = "N", "No seleccionado"

    maintenance = models.ForeignKey(
        MaintenanceDefinition,
        on_delete=models.CASCADE,
        related_name="sp_selections",
        verbose_name="Mantenimiento",
    )
    operation = models.CharField(max_length=6, choices=OperationRole.choices, verbose_name="Operación")
    sp_definition = models.ForeignKey(
        SPDefinition,
        on_delete=models.PROTECT,
        related_name="maintenance_sp_selections",
        null=True,
        blank=True,
        verbose_name="SP seleccionado",
    )
    is_required = models.BooleanField(default=False, verbose_name="Obligatorio")
    selection_status = models.CharField(
        max_length=1,
        choices=SelectionStatus.choices,
        default=SelectionStatus.NOT_SELECTED,
        verbose_name="Estado de selección",
    )

    class Meta:
        verbose_name = "Selección de SP"
        verbose_name_plural = "Selecciones de SP"
        constraints = [
            models.UniqueConstraint(
                fields=["maintenance", "operation"],
                name="uq_maintenance_builder_sp_selection_operation",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.maintenance_id} · {self.operation}"

    def clean(self) -> None:
        super().clean()
        if not self.sp_definition_id:
            if self.is_required:
                raise ValidationError({"sp_definition": "Esta operación requiere un SP seleccionado."})
            return
        if self.sp_definition.company_id != self.maintenance.company_id:
            raise ValidationError({"sp_definition": "El SP no pertenece a la compañía del mantenimiento."})
        self._validate_operation_mapping()

    def _validate_operation_mapping(self) -> None:
        if self.operation == self.OperationRole.READ_C:
            if (
                self.sp_definition.operation != SPDefinition.Operation.READ
                or self.sp_definition.read_mode != SPDefinition.ReadMode.CURSOR
            ):
                raise ValidationError({"sp_definition": "Para READ_C debe seleccionar un SP READ con modo cursor."})
            return
        if self.operation == self.OperationRole.READ_R:
            if (
                self.sp_definition.operation != SPDefinition.Operation.READ
                or self.sp_definition.read_mode != SPDefinition.ReadMode.ROW
            ):
                raise ValidationError({"sp_definition": "Para READ_R debe seleccionar un SP READ con modo fila."})
            return
        if self.sp_definition.operation != self.operation:
            raise ValidationError({"sp_definition": f"El SP debe ser de operación {self.operation}."})


class MaintenanceSourceSelection(AuditModel):
    class RoleCode(models.TextChoices):
        BASE_DSPF = "BASE_DSPF", "Base DSPF"
        BASE_SQLRPGLE = "BASE_SQLRPGLE", "Base SQLRPGLE"

    maintenance = models.ForeignKey(
        MaintenanceDefinition,
        on_delete=models.CASCADE,
        related_name="source_selections",
        verbose_name="Mantenimiento",
    )
    role_code = models.CharField(max_length=14, choices=RoleCode.choices, verbose_name="Rol")
    source_template = models.ForeignKey(
        SourceTemplate,
        on_delete=models.PROTECT,
        related_name="maintenance_source_selections",
        verbose_name="Plantilla fuente",
    )
    source_type_expected = models.CharField(max_length=20, verbose_name="Tipo esperado")

    class Meta:
        verbose_name = "Selección de plantilla"
        verbose_name_plural = "Selecciones de plantilla"
        constraints = [
            models.UniqueConstraint(
                fields=["maintenance", "role_code"],
                name="uq_maintenance_builder_source_selection_role",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.maintenance_id} · {self.role_code}"

    def clean(self) -> None:
        super().clean()
        expected_type = self._expected_source_type()
        if self.source_type_expected and self.source_type_expected != expected_type:
            raise ValidationError({"source_type_expected": f"El tipo esperado debe ser {expected_type}."})
        if self.source_template.source_type != expected_type:
            raise ValidationError({"source_template": f"La plantilla debe ser de tipo {expected_type}."})
        if self.source_template.company_id and self.source_template.company_id != self.maintenance.company_id:
            raise ValidationError({"source_template": "La plantilla no pertenece a la compañía ni es global."})

    def save(self, *args, **kwargs):
        self.source_type_expected = self._expected_source_type()
        super().save(*args, **kwargs)

    def _expected_source_type(self) -> str:
        if self.role_code == self.RoleCode.BASE_DSPF:
            return SourceTemplate.SourceType.DSPF
        return SourceTemplate.SourceType.SQLRPGLE


class MaintenanceStepState(AuditModel):
    maintenance = models.ForeignKey(
        MaintenanceDefinition,
        on_delete=models.CASCADE,
        related_name="step_states",
        verbose_name="Mantenimiento",
    )
    step_number = models.PositiveSmallIntegerField(verbose_name="Paso")
    payload_json = models.JSONField(verbose_name="Payload")
    is_completed = models.BooleanField(default=False, verbose_name="Paso completado")

    class Meta:
        verbose_name = "Estado de paso"
        verbose_name_plural = "Estados de paso"
        constraints = [
            models.UniqueConstraint(
                fields=["maintenance", "step_number"],
                name="uq_maintenance_builder_step_state_per_step",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.maintenance_id} · paso {self.step_number}"


class MaintenanceScriptVersion(AuditModel):
    class GenerationStatus(models.TextChoices):
        SUCCESS = "S", "Success"
        ERROR = "E", "Error"

    maintenance = models.ForeignKey(
        MaintenanceDefinition,
        on_delete=models.CASCADE,
        related_name="script_versions",
        verbose_name="Mantenimiento",
    )
    version = models.PositiveIntegerField(verbose_name="Versión")
    script_sqlrpgle = models.TextField(verbose_name="Script SQLRPGLE")
    script_hash = models.CharField(max_length=64, blank=True, default="", verbose_name="Hash del script")
    generation_status = models.CharField(
        max_length=1,
        choices=GenerationStatus.choices,
        default=GenerationStatus.SUCCESS,
        verbose_name="Resultado de generación",
    )
    error_message = models.CharField(max_length=300, blank=True, default="", verbose_name="Mensaje de error")
    is_current = models.BooleanField(default=False, verbose_name="Versión vigente")

    class Meta:
        verbose_name = "Versión de script"
        verbose_name_plural = "Versiones de script"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["maintenance", "version"],
                name="uq_maintenance_builder_script_version_number",
            ),
            models.UniqueConstraint(
                fields=["maintenance"],
                condition=Q(is_current=True),
                name="uq_maintenance_builder_single_current_script",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.maintenance_id} · v{self.version}"


class MaintenanceProcessLog(AuditModel):
    class EventType(models.TextChoices):
        SAVE = "SAVE", "Guardar"
        GENERATE = "GENERATE", "Generar"
        ERROR = "ERROR", "Error"

    class EventStatus(models.TextChoices):
        SUCCESS = "S", "Success"
        ERROR = "E", "Error"

    maintenance = models.ForeignKey(
        MaintenanceDefinition,
        on_delete=models.CASCADE,
        related_name="process_logs",
        verbose_name="Mantenimiento",
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices, verbose_name="Tipo de evento")
    event_status = models.CharField(max_length=1, choices=EventStatus.choices, verbose_name="Estado del evento")
    event_message = models.CharField(max_length=300, verbose_name="Mensaje")
    event_detail_json = models.JSONField(null=True, blank=True, verbose_name="Detalle")

    class Meta:
        verbose_name = "Bitácora de proceso"
        verbose_name_plural = "Bitácoras de proceso"
        ordering = ["-created_at"]

# Create your models here.
