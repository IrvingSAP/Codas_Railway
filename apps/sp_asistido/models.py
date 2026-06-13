"""Modelos persistidos para definiciones de SP Asistido (READ / ADD / UPD / DLT)."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.company.models import Company
from apps.table_design.models import DetailTable, HeaderTable


class SPDefinition(models.Model):
    """Cabecera de una definición de procedimiento guiada por el asistente."""

    class Operation(models.TextChoices):
        READ = "READ", "READ (SELECT)"
        ADD = "ADD", "ADD (INSERT)"
        UPD = "UPD", "UPD (UPDATE)"
        DLT = "DLT", "DLT (DELETE)"

    class Status(models.TextChoices):
        DRAFT = "D", "Borrador"
        ACTIVE = "A", "Activo"
        INACTIVE = "I", "Inactivo"

    class ReadMode(models.TextChoices):
        CURSOR = "C", "READ-C (cursor)"
        ROW = "R", "READ-R (registro único)"

    class ReadRowPolicy(models.TextChoices):
        ERROR = "E", "Error si devuelve más de uno"
        FIRST = "F", "Tomar primer registro"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="sp_definitions",
        verbose_name="Compañía",
    )
    header_table = models.ForeignKey(
        HeaderTable,
        on_delete=models.PROTECT,
        related_name="sp_definitions",
        verbose_name="Tabla diseño (cabecera)",
    )
    operation = models.CharField(
        max_length=4,
        choices=Operation.choices,
        verbose_name="Operación",
    )
    read_mode = models.CharField(
        max_length=1,
        choices=ReadMode.choices,
        default=ReadMode.CURSOR,
        verbose_name="Modalidad READ",
    )
    read_row_policy = models.CharField(
        max_length=1,
        choices=ReadRowPolicy.choices,
        default=ReadRowPolicy.ERROR,
        verbose_name="Política READ-R (múltiples filas)",
    )
    schema_name = models.CharField(
        max_length=10,
        verbose_name="Esquema / librería del SP",
    )
    procedure_name_short = models.CharField(
        max_length=10,
        verbose_name="Nombre corto del SP",
    )
    procedure_name_long = models.CharField(
        max_length=50,
        verbose_name="Nombre largo (descriptivo)",
    )
    procedure_comment = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Comentario descriptivo",
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Estado de la definición",
    )
    current_step = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Paso actual del wizard",
    )
    script_generated = models.BooleanField(
        default=False,
        verbose_name="Script generado",
    )
    script_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de script",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_definitions_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_definitions_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Definición SP asistido"
        verbose_name_plural = "Definiciones SP asistido"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["company", "operation"]),
            models.Index(fields=["company", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.procedure_name_short} ({self.operation})"


class SPStepState(models.Model):
    """Snapshot JSON por paso del wizard (reanudación y trazabilidad)."""

    sp_definition = models.ForeignKey(
        SPDefinition,
        on_delete=models.CASCADE,
        related_name="step_states",
        verbose_name="Definición SP",
    )
    step_number = models.PositiveSmallIntegerField(verbose_name="Número de paso")
    payload_json = models.JSONField(verbose_name="Payload del paso")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_step_states_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_step_states_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Estado de paso (wizard)"
        verbose_name_plural = "Estados de paso (wizard)"
        constraints = [
            models.UniqueConstraint(
                fields=["sp_definition", "step_number"],
                name="uq_sp_asistido_stepstate_definition_step",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sp_definition_id} · paso {self.step_number}"


class SPParameter(models.Model):
    """Parámetro IN/OUT de la firma del procedimiento generado."""

    class Direction(models.TextChoices):
        IN = "IN", "IN"
        OUT = "OUT", "OUT"

    sp_definition = models.ForeignKey(
        SPDefinition,
        on_delete=models.CASCADE,
        related_name="parameters",
        verbose_name="Definición SP",
    )
    direction = models.CharField(
        max_length=3,
        choices=Direction.choices,
        verbose_name="Dirección",
    )
    name = models.CharField(max_length=30, verbose_name="Nombre del parámetro")
    db2_type = models.CharField(max_length=50, verbose_name="Tipo DB2 / SQL")
    ordinal = models.PositiveSmallIntegerField(verbose_name="Orden en la firma")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_parameters_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_parameters_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Parámetro SP"
        verbose_name_plural = "Parámetros SP"
        ordering = ["sp_definition_id", "ordinal"]
        constraints = [
            models.UniqueConstraint(
                fields=["sp_definition", "name"],
                name="uq_sp_asistido_parameter_definition_name",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.direction})"


class SPAssignment(models.Model):
    """Mapeo columna destino ↔ origen de valor (ADD / UPD SET)."""

    class SourceKind(models.TextChoices):
        IN_PARAM = "IN", "Parámetro IN"
        LITERAL = "LITERAL", "Literal"
        NULL = "NULL", "NULL"
        EXPR = "EXPR", "Expresión SQL"

    sp_definition = models.ForeignKey(
        SPDefinition,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Definición SP",
    )
    detail_field = models.ForeignKey(
        DetailTable,
        on_delete=models.PROTECT,
        related_name="sp_asistido_assignments",
        verbose_name="Campo detalle",
    )
    source_kind = models.CharField(
        max_length=10,
        choices=SourceKind.choices,
        verbose_name="Origen del valor",
    )
    source_value = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Detalle (literal, nombre IN, expresión)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_assignments_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_assignments_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Asignación columna (SET/INSERT)"
        verbose_name_plural = "Asignaciones columna (SET/INSERT)"

    def __str__(self) -> str:
        return f"{self.detail_field_id} ← {self.source_kind}"


class SPCondition(models.Model):
    """Predicado WHERE u orden / paginación (READ y WHERE en UPD/DLT).

    Un mismo :class:`SPDefinition` puede tener **varias** filas con
    ``clause_kind=WHERE``; se interpretan en orden de ``ordinal`` y se unen con
    ``logical_join`` (p. ej. AND entre el primero y el segundo). Tanto el
    asistente **UPD** como el **DLT** permiten múltiples columnas en el
    ``WHERE`` (misma tabla) persistiendo un ``SPCondition`` por columna
    participante.
    """

    class ClauseKind(models.TextChoices):
        WHERE = "WHERE", "WHERE"
        ORDER = "ORDER", "ORDER BY"
        FETCH = "FETCH", "FETCH / paginación"

    class ValueOrigin(models.TextChoices):
        IN_PARAM = "IN", "Parámetro IN"
        LITERAL = "LITERAL", "Literal"
        EXPR = "EXPR", "Expresión SQL"
        NULL = "NULL", "NULL / IS NULL"

    class LogicalJoin(models.TextChoices):
        AND = "AND", "AND"
        OR = "OR", "OR"

    sp_definition = models.ForeignKey(
        SPDefinition,
        on_delete=models.CASCADE,
        related_name="conditions",
        verbose_name="Definición SP",
    )
    clause_kind = models.CharField(
        max_length=10,
        choices=ClauseKind.choices,
        verbose_name="Tipo de cláusula",
    )
    detail_field = models.ForeignKey(
        DetailTable,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sp_asistido_conditions",
        verbose_name="Campo detalle",
    )
    operator = models.CharField(
        max_length=12,
        blank=True,
        default="",
        verbose_name="Operador SQL",
    )
    value_origin = models.CharField(
        max_length=10,
        choices=ValueOrigin.choices,
        blank=True,
        default="",
        verbose_name="Origen del valor",
    )
    value_text = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Valor o nombre de parámetro",
    )
    logical_join = models.CharField(
        max_length=3,
        choices=LogicalJoin.choices,
        blank=True,
        default="",
        verbose_name="Unión con siguiente condición",
    )
    ordinal = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_conditions_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_conditions_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Condición SP (WHERE/ORDER/FETCH)"
        verbose_name_plural = "Condiciones SP (WHERE/ORDER/FETCH)"
        ordering = ["sp_definition_id", "ordinal", "id"]

    def __str__(self) -> str:
        return f"{self.clause_kind} #{self.ordinal}"


class SPArtifactVersion(models.Model):
    """Versión persistida del script SQL generado."""

    sp_definition = models.ForeignKey(
        SPDefinition,
        on_delete=models.CASCADE,
        related_name="artifact_versions",
        verbose_name="Definición SP",
    )
    version = models.PositiveIntegerField(verbose_name="Número de versión")
    sql_script = models.TextField(verbose_name="Script SQL")
    script_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Huella del script",
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name="Versión vigente",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_artifact_versions_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sp_asistido_artifact_versions_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Versión de artefacto SQL"
        verbose_name_plural = "Versiones de artefacto SQL"
        ordering = ["sp_definition_id", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["sp_definition", "version"],
                name="uq_sp_asistido_artifactversion_definition_version",
            ),
        ]

    def __str__(self) -> str:
        return f"v{self.version} · {self.sp_definition_id}"
