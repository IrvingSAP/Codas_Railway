from django.conf import settings
from django.db import models

from apps.company.models import Company


class UserProfile(models.Model):
    """Perfil extendido: compañía, tipo de usuario, seguridad y auditoría."""

    class UserType(models.TextChoices):
        SUPERUSER = "SU", "Super usuario"
        ADMIN_COMPANY = "AC", "Administrador de compañía"
        ADMIN_SYSTEM = "AS", "Administrador de sistema"
        USER = "US", "Usuario"

    class Status(models.TextChoices):
        ACTIVE = "A", "Activo"
        INACTIVE = "I", "Inactivo"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Usuario",
    )
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_profiles",
        verbose_name="Compañía",
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Teléfono",
    )
    document_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Documento de identidad",
    )
    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Dirección",
    )
    user_type = models.CharField(
        max_length=2,
        choices=UserType.choices,
        default=UserType.USER,
        verbose_name="Tipo de usuario",
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Estado",
    )
    totp_secret = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="Secreto TOTP",
    )
    tfa_verified = models.BooleanField(
        default=False,
        verbose_name="2FA verificado",
    )
    email_confirmed = models.BooleanField(
        default=False,
        verbose_name="Email confirmado",
    )
    email_confirm_code = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        verbose_name="Código de confirmación",
    )
    email_confirm_exp = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expiración del código",
    )
    last_totp_reset = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Último reset de TOTP",
    )
    last_password_change = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Último cambio de contraseña",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="created_profiles",
        on_delete=models.SET_NULL,
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="updated_profiles",
        on_delete=models.SET_NULL,
        verbose_name="Actualizado por",
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bloqueado hasta",
    )

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"
        ordering = ["user__username"]

    def __str__(self) -> str:
        return self.user.get_username()
