from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Company(models.Model):
    """Datos básicos de una compañía en CODAS."""

    name_short = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="Nombre corto",
        help_text="Código o sigla única de la compañía.",
    )
    name_long = models.CharField(max_length=150, verbose_name="Nombre largo")
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Identificación tributaria",
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Dirección",
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Teléfono",
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo electrónico",
    )
    logo = models.ImageField(
        upload_to="company_logos/",
        blank=True,
        null=True,
        verbose_name="Logo",
    )
    sql_max_line_length = models.PositiveSmallIntegerField(
        default=78,
        validators=[MinValueValidator(40), MaxValueValidator(180)],
        verbose_name="Máximo de caracteres por línea SQL",
        help_text="Límite de longitud por línea para scripts SQL generados.",
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="companies_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="companies_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Compañía"
        verbose_name_plural = "Compañías"
        ordering = ["name_short"]

    def __str__(self) -> str:
        return self.name_short
