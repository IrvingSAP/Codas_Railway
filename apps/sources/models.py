from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.company.models import Company


class SourceTemplate(models.Model):
    """Plantilla base de código fuente para generar programas."""

    class SourceType(models.TextChoices):
        DSPF = "DSPF", "Pantalla (DDS)"
        SQLRPGLE = "SQLRPGLE", "Programa SQLRPGLE"
        RPGLE = "RPGLE", "Programa RPGLE"
        CLLE = "CLLE", "Programa CLLE"

    class Status(models.TextChoices):
        ACTIVE = "A", "Activo"
        INACTIVE = "I", "Inactivo"

    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="source_templates",
        verbose_name="Compañía",
        help_text="Nulo = plantilla global; con valor = plantilla de compañía.",
    )
    name = models.CharField(max_length=100, verbose_name="Nombre de la plantilla")
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descripción",
    )
    filename = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre del archivo",
    )
    source_text = models.TextField(verbose_name="Contenido de la plantilla")
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.DSPF,
        verbose_name="Tipo de fuente",
    )
    version = models.PositiveIntegerField(default=1, verbose_name="Versión")
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
        null=True,
        blank=True,
        related_name="source_templates_created",
        on_delete=models.SET_NULL,
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="source_templates_updated",
        on_delete=models.SET_NULL,
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Plantilla fuente"
        verbose_name_plural = "Plantillas fuente"
        ordering = ["company__name_short", "name", "-version"]
        indexes = [
            models.Index(fields=["company", "source_type", "status"]),
            models.Index(fields=["name", "version"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name", "version"],
                name="uq_source_template_company_name_version",
            ),
            models.UniqueConstraint(
                fields=["company", "filename", "version"],
                condition=Q(filename__gt=""),
                name="uq_source_template_company_filename_version_when_filename",
            ),
        ]

    def __str__(self) -> str:
        company_label = self.company.name_short if self.company else "GLOBAL"
        return f"{company_label} · {self.name} (v{self.version})"

    def clean(self) -> None:
        super().clean()
        if self.version < 1:
            raise ValidationError({"version": "La versión debe ser mayor o igual a 1."})
        if self.filename:
            ext = Path(self.filename).suffix.lower()
            expected_ext = {
                self.SourceType.DSPF: ".dspf",
                self.SourceType.SQLRPGLE: ".sqlrpgle",
                self.SourceType.RPGLE: ".rpgle",
                self.SourceType.CLLE: ".clle",
            }[self.source_type]
            if ext and ext != expected_ext:
                raise ValidationError(
                    {
                        "filename": (
                            "La extensión del archivo no coincide con el tipo de fuente. "
                            f"Esperada: {expected_ext}"
                        )
                    }
                )
