"""
PROTOTIPO — diseño de modelos TableDesign (cabecera / detalle DB2 for i).

No forma parte de INSTALLED_APPS: sirve para revisar el diseño antes de
copiar a p. ej. apps.table_design/models.py.

Alineado a convenciones CODAS (apps.company, AUTH_USER_MODEL, estados A/I/P).
FK compañía con PROTECT para evitar borrado accidental de diseños de alto impacto.
"""

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
        ACTIVE = "A", "Activo"
        INACTIVE = "I", "Inactivo"
        PROCESS = "P", "Proceso"

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
        help_text="Librería IBM i (obligatorio en modelo real; ver migración 0004).",
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
        default=Status.ACTIVE,
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

    class Meta:
        verbose_name = "Diseño de tabla (cabecera)"
        verbose_name_plural = "Diseños de tabla (cabeceras)"
        ordering = ["company", "table_name_short"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "table_name_short"],
                name="uq_table_design_header_company_table_short",
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
        # Modelos A/E: validar en vistas/servicios que exista la fila en
        # HeaderTableAdvanced / HeaderTableExpert cuando toque.


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
    field_description = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Descripción / texto de columna",
        help_text="Máximo 20 caracteres (convención legado / etiqueta corta).",
    )
    nullable = models.BooleanField(default=True, verbose_name="Permite nulos")
    default_value = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Valor por defecto",
    )
    signed = models.BooleanField(default=True, verbose_name="Con signo")
    is_unique = models.BooleanField(default=False, verbose_name="Único")
    is_indexed = models.BooleanField(default=False, verbose_name="Indexado")
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


# --- Extensiones reservadas para modelos A / E (1:1 con cabecera) ----------------


class HeaderTableAdvanced(models.Model):
    """Placeholder: parámetros adicionales cuando `table_model == Avanzado`."""

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
    """Placeholder: parámetros adicionales cuando `table_model == Experto`."""

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
