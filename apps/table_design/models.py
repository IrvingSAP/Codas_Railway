"""Modelos de diseño de tablas DB2 for i (cabecera, detalle y extensiones A/E)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.company.models import Company


class HeaderTable(models.Model):
    """Cabecera de diseño de tabla (metadatos IBM i / DB2)."""

    class TableModel(models.TextChoices):
        SIMPLE = "S", "Simple"
        ADVANCED = "A", "Avanzado"
        EXPERT = "E", "Experto"

    class Status(models.TextChoices):
        PROCESS = "P", "Proceso"
        ACTIVE = "A", "Activo"
        INACTIVE = "I", "Inactivo"

    class TableKind(models.TextChoices):
        PHYSICAL = "PHYSICAL", "Física"
        LOGICAL = "LOGICAL", "Lógica"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="table_design_headers",
        verbose_name="Compañía",
    )
    table_model = models.CharField(
        max_length=1,
        choices=TableModel.choices,
        default=TableModel.SIMPLE,
        verbose_name="Modelo de tabla",
    )
    table_name_long = models.CharField(
        max_length=128,
        verbose_name="Nombre largo de la tabla",
    )
    table_name_short = models.CharField(
        max_length=10,
        verbose_name="Nombre corto de la tabla",
        help_text="Nombre de archivo / miembro según convención IBM i (hasta 10).",
    )
    schema = models.CharField(
        max_length=10,
        verbose_name="Esquema / librería",
        help_text="Librería / esquema IBM i (obligatorio; máx. 10 caracteres).",
    )
    table_type = models.CharField(
        max_length=20,
        choices=TableKind.choices,
        default=TableKind.PHYSICAL,
        verbose_name="Tipo de tabla",
    )
    is_field_key = models.BooleanField(
        default=False,
        verbose_name="Tiene llave",
    )
    is_auto_key = models.BooleanField(
        default=False,
        verbose_name="Llave autogenerada",
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.PROCESS,
        verbose_name="Estado",
    )
    notes = models.TextField(null=True, blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_design_headers_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_design_headers_updated",
        verbose_name="Actualizado por",
    )
    script_date = models.DateField(null=True, blank=True, verbose_name="Fecha de script")
    script_generated = models.BooleanField(
        default=False,
        verbose_name="Script generado",
    )
    sp_associated = models.BooleanField(
        default=False,
        verbose_name="Procedimiento almacenado asociado",
    )
    mt_associated = models.BooleanField(
        default=False,
        verbose_name="Mantenimiento asociado",
    )
    pk_constraint_name = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        verbose_name="Nombre del constraint de PK",
        help_text=(
            "Patrón A-Z0-9_. Opcional: null/vacío no emite CONSTRAINT nominado en DDL. "
            "Unicidad global si tiene valor."
        ),
    )
    record_format_name = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        verbose_name="Nombre record format (RCDFMT)",
        help_text="Opcional. Si tiene valor, el script puede emitir RCDFMT.",
    )


    class Meta:
        verbose_name = "Diseño de tabla (cabecera)"
        verbose_name_plural = "Diseños de tabla (cabeceras)"
        ordering = ["company", "table_name_short"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "table_name_short"],
                name="uq_table_design_header_company_table_short",
            ),
            models.UniqueConstraint(
                fields=["pk_constraint_name"],
                condition=Q(pk_constraint_name__isnull=False),
                name="uq_table_design_header_pk_constraint_name",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["company", "table_name_short"]),
        ]

    def __str__(self) -> str:
        return f"{self.table_name_short} — {self.table_name_long}"

    def clean(self) -> None:
        super().clean()
        if self.is_auto_key and not self.is_field_key:
            raise ValidationError(
                {
                    "is_auto_key": (
                        "La llave autogenerada requiere que la tabla tenga llave "
                        "(`Tiene llave` activo)."
                    )
                }
            )


class HeaderTableAutoKeyConfig(models.Model):
    """Parámetros de GENERATED AS IDENTITY (1:1 con HeaderTable)."""

    header = models.OneToOneField(
        HeaderTable,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="auto_key_config",
        verbose_name="Cabecera",
    )
    identity_start = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="IDENTITY: START WITH",
        help_text="Parámetro global para GENERATED AS IDENTITY (p. ej. 1).",
    )
    identity_increment = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="IDENTITY: INCREMENT BY",
    )
    identity_cache = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="IDENTITY: CACHE",
    )
    identity_cycle = models.BooleanField(
        default=False,
        verbose_name="IDENTITY: CYCLE",
        help_text="Si es verdadero, se emite CYCLE en el bloque IDENTITY cuando aplique.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_design_auto_key_configs_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_design_auto_key_configs_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Configuración de llave autogenerada"
        verbose_name_plural = "Configuraciones de llave autogenerada"

    def __str__(self) -> str:
        return f"Auto key · {self.header_id} · {self.header.table_name_short}"

    def clean(self) -> None:
        super().clean()
        if self.identity_start is not None and self.identity_start < 1:
            raise ValidationError(
                {"identity_start": "El valor inicial de identidad debe ser mayor o igual que 1."}
            )
        if self.identity_increment is not None and self.identity_increment < 1:
            raise ValidationError(
                {"identity_increment": "El incremento de identidad debe ser mayor o igual que 1."}
            )
        if self.identity_cache is not None and self.identity_cache < 1:
            raise ValidationError(
                {"identity_cache": "La caché de identidad debe ser mayor o igual que 1."}
            )


class DetailTable(models.Model):
    """Detalle: columnas / campos asociados a una cabecera de diseño."""

    class FieldDB2Type(models.TextChoices):
        CHAR = "CHAR", "CHAR"
        VARCHAR = "VARCHAR", "VARCHAR"
        CLOB = "CLOB", "CLOB"
        GRAPHIC = "GRAPHIC", "GRAPHIC"
        VARGRAPHIC = "VARGRAPHIC", "VARGRAPHIC"
        SMALLINT = "SMALLINT", "SMALLINT"
        INTEGER = "INTEGER", "INTEGER"
        BIGINT = "BIGINT", "BIGINT"
        DECIMAL = "DECIMAL", "DECIMAL"
        NUMERIC = "NUMERIC", "NUMERIC"
        DECFLOAT = "DECFLOAT", "DECFLOAT"
        REAL = "REAL", "REAL"
        DOUBLE = "DOUBLE", "DOUBLE"
        DATE = "DATE", "DATE"
        TIME = "TIME", "TIME"
        TIMESTAMP = "TIMESTAMP", "TIMESTAMP"
        BINARY = "BINARY", "BINARY"
        VARBINARY = "VARBINARY", "VARBINARY"
        BLOB = "BLOB", "BLOB"
        ROWID = "ROWID", "ROWID"
        XML = "XML", "XML"

    class Status(models.TextChoices):
        ACTIVE = "A", "Activo"
        INACTIVE = "I", "Inactivo"
        PROCESS = "P", "Proceso"

    header = models.ForeignKey(
        HeaderTable,
        on_delete=models.CASCADE,
        related_name="fields",
        verbose_name="Cabecera de diseño",
    )
    order_reg = models.PositiveIntegerField(verbose_name="Orden de registro")
    field_name_long = models.CharField(
        max_length=30,
        verbose_name="Nombre largo del campo",
    )
    field_name_short = models.CharField(
        max_length=10,
        verbose_name="Nombre corto del campo",
    )
    field_type = models.CharField(
        max_length=20,
        choices=FieldDB2Type.choices,
        verbose_name="Tipo de dato",
    )
    field_length = models.PositiveIntegerField(
        default=0,
        verbose_name="Longitud",
        help_text="Para tipos sin longitud fija usar 0; validar por tipo en services/ al generar DDL.",
    )
    decimal_places = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Decimales",
    )
    allocate_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ALLOCATE (VARCHAR/VARGRAPHIC)",
        help_text="Suballocación DB2 for i: obligatorio al dar de alta VARCHAR o VARGRAPHIC (debe ser > 0 y ≤ longitud).",
    )
    column_label = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Etiqueta (LABEL ON COLUMN … IS)",
        help_text="Texto para LABEL ON COLUMN (máximo 20 caracteres).",
    )
    column_text = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Texto (LABEL ON COLUMN … TEXT IS)",
    )
    is_key = models.BooleanField(default=False, verbose_name="Llave")
    order_key = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Orden de llave",
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Estado",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_design_fields_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_design_fields_updated",
        verbose_name="Actualizado por",
    )
    script_generated = models.BooleanField(
        default=False,
        verbose_name="Script generado",
    )
    script_date = models.DateField(null=True, blank=True, verbose_name="Fecha de script")
    notes = models.TextField(null=True, blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Campo de diseño de tabla"
        verbose_name_plural = "Campos de diseño de tabla"
        ordering = ["header", "order_reg"]
        constraints = [
            models.UniqueConstraint(
                fields=["header", "order_reg"],
                name="uq_table_design_field_header_order",
            ),
            models.UniqueConstraint(
                fields=["header", "field_name_short"],
                name="uq_table_design_field_header_short_name",
            ),
        ]
        indexes = [
            models.Index(fields=["header", "order_reg"]),
            models.Index(fields=["header", "field_name_short"]),
        ]

    def __str__(self) -> str:
        return f"{self.header.table_name_short} · {self.order_reg} · {self.field_name_short}"

    def clean(self) -> None:
        super().clean()
        if self.field_type in (
            self.FieldDB2Type.DECIMAL,
            self.FieldDB2Type.NUMERIC,
        ):
            if self.decimal_places is None:
                raise ValidationError(
                    {
                        "decimal_places": (
                            "Indique decimales para tipos DECIMAL o NUMERIC "
                            "(precisión/escala en el generador de DDL)."
                        )
                    }
                )
        if self.is_key and self.order_key is None:
            raise ValidationError(
                {
                    "order_key": "Si el campo es llave, indique el orden de la llave.",
                }
            )


class DetailTableDb2Attributes(models.Model):
    """Atributos DB2 for i adicionales por columna (1:1 con DetailTable)."""

    class IdentityGeneration(models.TextChoices):
        ALWAYS = "ALWAYS", "GENERATED ALWAYS AS IDENTITY"
        BY_DEFAULT = "BY_DEFAULT", "GENERATED BY DEFAULT AS IDENTITY"

    class GeneratedKind(models.TextChoices):
        NONE = "NONE", "Sin columna generada"
        EXPRESSION = "EXPR", "GENERATED ALWAYS AS (expresión)"
        ROW_CHANGE_TIMESTAMP = "RCTS", "ROW CHANGE TIMESTAMP"
        ROW_BEGIN = "RBEGIN", "GENERATED ALWAYS AS ROW BEGIN"
        ROW_END = "REND", "GENERATED ALWAYS AS ROW END"

    class CompressMode(models.TextChoices):
        NONE = "NONE", "Sin compresión"
        SYSTEM_DEFAULT = "SYSTEM_DEFAULT", "COMPRESS SYSTEM DEFAULT"

    class TemporalRole(models.TextChoices):
        NONE = "NONE", "Ninguno"
        SYSTEM_TIME_START = "ST_START", "PERIOD SYSTEM_TIME (inicio)"
        SYSTEM_TIME_END = "ST_END", "PERIOD SYSTEM_TIME (fin)"
        APPLICATION_TIME_START = "AT_START", "PERIOD APPLICATION_TIME (inicio)"
        APPLICATION_TIME_END = "AT_END", "PERIOD APPLICATION_TIME (fin)"

    detail = models.OneToOneField(
        DetailTable,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="db2_attributes",
        verbose_name="Campo de diseño",
    )
    is_identity = models.BooleanField(
        default=False,
        verbose_name="Columna IDENTITY",
        help_text="Marca la columna como GENERATED ALWAYS AS IDENTITY en el script.",
    )
    ccsid = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="CCSID",
        help_text="Opcional. Para tipos de texto en DB2 i (p. ej. 284).",
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name="LLAVE_SCRIPT CHAR(32) DEFAULT 'N/A' IMPLICITLY HIDDEN",
    )
    default_sql_expression = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="DEFAULT como expresión SQL",
        help_text="CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    )
    nullable = models.BooleanField(default=True, verbose_name="Permite nulos")
    default_value = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Valor por defecto",
        help_text="IS_ACTIVE SMALLINT NOT NULL WITH DEFAUL , NOT NULL,NULL, ",
    )
    signed = models.BooleanField(default=True, verbose_name="Con signo")
    is_unique = models.BooleanField(default=False, verbose_name="Único", help_text="CODIGO_SKU     VARCHAR(30) UNIQUE,  ")
    is_indexed = models.BooleanField(default=False, verbose_name="Indexado")
    check_constraint_sql = models.TextField(
        blank=True,
        default="",
        verbose_name="CHECK (expresión SQL)",
        help_text="STATUS CHAR(1) CHECK (STATUS IN ('A','I','P'))",
    )
    generated_kind = models.CharField(
        max_length=8,
        choices=GeneratedKind.choices,
        default=GeneratedKind.NONE,
        verbose_name="Tipo de columna generada",
    )
    generated_expression = models.TextField(
        blank=True,
        default="",
        verbose_name="Expresión GENERATED ALWAYS AS",
        help_text="Obligatorio si generated_kind=EXPR.",
    )
    fieldproc_program = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="FIELDPROC (programa calificado)",
        help_text="DOCUMENTO VARCHAR(20) FIELDPROC CODASLIB/ENCRIPTAR_DOC",
    )
    for_bit_data = models.BooleanField(
        default=False,
        verbose_name="FOR BIT DATA",
        help_text="DOCUMENTO VARCHAR(20) FOR BIT DATA",
    )
    compress_mode = models.CharField(
        max_length=16,
        choices=CompressMode.choices,
        default=CompressMode.NONE,
        verbose_name="Compresión de columna",
        help_text="DOCUMENTO VARCHAR(20) COMPRESS SYSTEM DEFAULT",
    )
    identity_generation = models.CharField(
        max_length=10,
        choices=IdentityGeneration.choices,
        default=IdentityGeneration.ALWAYS,
        verbose_name="Modo IDENTITY",
        help_text="Aplica solo si is_identity es verdadero.",
    )
    mask_function = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Función MASKED WITH",
        help_text="EMAIL VARCHAR(254) MASKED WITH (FUNCTION 'EMAIL')",
    )
    is_row_change_timestamp = models.BooleanField(
        default=False,
        verbose_name="ROW CHANGE TIMESTAMP",
    )
    is_generated_rowid = models.BooleanField(
        default=False,
        verbose_name="ROWID generado",
    )
    associated_trigger_name = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="Trigger asociado (nombre)",
    )
    security_label = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="SECURITY LABEL",
    )
    temporal_role = models.CharField(
        max_length=12,
        choices=TemporalRole.choices,
        default=TemporalRole.NONE,
        verbose_name="Rol temporal (PERIOD / ROW BEGIN-END)",
    )
    user_defined_field = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="User Defined Field",
        help_text="Ej.: Definido por el usuario",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_design_field_db2_attrs_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_design_field_db2_attrs_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Atributos DB2 de columna"
        verbose_name_plural = "Atributos DB2 de columnas"

    def __str__(self) -> str:
        return f"DB2 attrs · {self.detail_id} · {self.detail.field_name_short}"

    def clean(self) -> None:
        super().clean()
        detail = self.detail

        if self.generated_kind == self.GeneratedKind.EXPRESSION and not self.generated_expression.strip():
            raise ValidationError(
                {"generated_expression": "Indique la expresión para columna generada."}
            )

        if self.generated_kind != self.GeneratedKind.NONE and self.is_identity:
            raise ValidationError(
                "No combine IDENTITY con columna generada por expresión."
            )

        if self.is_row_change_timestamp and self.generated_kind not in (
            self.GeneratedKind.NONE,
            self.GeneratedKind.ROW_CHANGE_TIMESTAMP,
        ):
            raise ValidationError(
                {"is_row_change_timestamp": "Conflicto con otro tipo de columna generada."}
            )

        if self.is_row_change_timestamp and detail.field_type != DetailTable.FieldDB2Type.TIMESTAMP:
            raise ValidationError(
                {"is_row_change_timestamp": "ROW CHANGE TIMESTAMP requiere tipo TIMESTAMP."}
            )

        if self.is_generated_rowid and detail.field_type != DetailTable.FieldDB2Type.ROWID:
            raise ValidationError(
                {"is_generated_rowid": "Solo aplica a columnas ROWID."}
            )

        if self.for_bit_data and detail.field_type not in (
            DetailTable.FieldDB2Type.BINARY,
            DetailTable.FieldDB2Type.VARBINARY,
        ):
            raise ValidationError(
                {"for_bit_data": "FOR BIT DATA solo aplica a BINARY o VARBINARY."}
            )



class HeaderTableAdvanced(models.Model):
    """Parámetros adicionales cuando el modelo de tabla es Avanzado."""

    header = models.OneToOneField(
        HeaderTable,
        on_delete=models.CASCADE,
        related_name="advanced_extension",
        verbose_name="Cabecera",
    )
    params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Parámetros (JSON)",
        help_text="Iteración hasta congelar columnas fijas en el modelo.",
    )

    class Meta:
        verbose_name = "Extensión avanzada de diseño de tabla"
        verbose_name_plural = "Extensiones avanzadas de diseño de tabla"


class HeaderTableExpert(models.Model):
    """Parámetros adicionales cuando el modelo de tabla es Experto."""

    header = models.OneToOneField(
        HeaderTable,
        on_delete=models.CASCADE,
        related_name="expert_extension",
        verbose_name="Cabecera",
    )
    params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Parámetros (JSON)",
        help_text="Iteración hasta congelar columnas fijas en el modelo.",
    )

    class Meta:
        verbose_name = "Extensión experta de diseño de tabla"
        verbose_name_plural = "Extensiones expertas de diseño de tabla"
