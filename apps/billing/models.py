"""
Modelos de facturación: planes, suscripción por compañía, contactos y pagos.

La huella ``integrity_signature`` usa HMAC-SHA256 sobre fechas en ISO (véase
docs/CODAS_SUSCRIPCIONES_VALIDACION.md). No usar ``QuerySet.update()`` ni SQL
directo sobre fechas sin recalcular la firma vía ``Subscription.save()`` o
``Subscription.refresh_integrity_signature()``.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.company.models import Company


def _license_secret_key_bytes() -> bytes:
    """Secreto para HMAC: LICENSE_SECRET_KEY; en DEBUG se puede usar SECRET_KEY como respaldo."""
    explicit = getattr(settings, "LICENSE_SECRET_KEY", "") or ""
    if explicit:
        return explicit.encode("utf-8")
    if settings.DEBUG:
        sk = getattr(settings, "SECRET_KEY", "") or ""
        if not sk:
            raise ImproperlyConfigured(
                "Defina LICENSE_SECRET_KEY o SECRET_KEY para la firma de suscripciones."
            )
        return sk.encode("utf-8")
    raise ImproperlyConfigured(
        "LICENSE_SECRET_KEY es obligatorio cuando DEBUG es False "
        "(integridad de suscripciones)."
    )


def _subscription_hmac_message(start: date, end: date) -> bytes:
    """Mensaje canónico para la huella de integridad (fechas en ISO, separador explícito)."""
    return f"{start.isoformat()}\n{end.isoformat()}".encode("utf-8")


class Plan(models.Model):
    """Catálogo de planes contratables (referencia de ``Subscription``)."""

    class BillingPeriod(models.TextChoices):
        MONTHLY = "monthly", "Mensual"
        ANNUAL = "annual", "Anual"
        ENTERPRISE = "enterprise", "Enterprise"

    name = models.CharField(max_length=100, verbose_name="Nombre")
    code = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="Código",
        help_text="Identificador estable para integraciones y reportes.",
    )
    billing_period = models.CharField(
        max_length=20,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY,
        verbose_name="Periodo de facturación",
    )
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo en catálogo")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


class Subscription(models.Model):
    """Licencia activa de una compañía (núcleo del licenciamiento)."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        EXPIRED = "expired", "Expirada"
        CANCELED = "canceled", "Cancelada"
        PENDING = "pending", "Pendiente de pago"

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name="Compañía",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        verbose_name="Plan",
    )

    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(verbose_name="Fecha de fin")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Estado",
    )

    auto_renew = models.BooleanField(default=True, verbose_name="Renovación automática")

    integrity_signature = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Huella de integridad (HMAC-SHA256)",
        help_text="Recalculada en cada guardado; no editar manualmente en BD.",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subscriptions_created",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subscriptions_updated",
        verbose_name="Actualizado por",
    )

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.company.name_short} — {self.plan.name}"

    def generate_signature(self) -> str:
        key = _license_secret_key_bytes()
        msg = _subscription_hmac_message(self.start_date, self.end_date)
        return hmac.new(key, msg, hashlib.sha256).hexdigest()

    def is_signature_valid(self) -> bool:
        expected = self.generate_signature()
        return hmac.compare_digest(self.integrity_signature, expected)

    def validate_license(self) -> dict:
        return {
            "signature_valid": self.is_signature_valid(),
            "is_expired": date.today() > self.end_date,
            "status": self.status,
            "contacts": list(self.contacts.all()[:3]),
        }

    def _sync_status_with_end_date(self) -> None:
        """Si la vigencia ya pasó y seguía activa, marca expirada (solo en ``save``)."""
        if self.end_date < date.today() and self.status == self.Status.ACTIVE:
            self.status = self.Status.EXPIRED

    def refresh_integrity_signature(self) -> None:
        """Para uso tras ``bulk_update`` manual de fechas (misma instancia en memoria)."""
        self.integrity_signature = self.generate_signature()

    def save(self, *args, **kwargs) -> None:
        self._sync_status_with_end_date()
        self.integrity_signature = self.generate_signature()
        super().save(*args, **kwargs)


class SubscriptionContact(models.Model):
    """Contactos de soporte asociados a la suscripción (p. ej. pantallas de error)."""

    MAX_CONTACTS = 3

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name="Suscripción",
    )

    full_name = models.CharField(max_length=150, verbose_name="Nombre completo")
    phone = models.CharField(max_length=50, verbose_name="Teléfono")
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo electrónico",
    )
    role = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Rol o cargo",
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notas adicionales")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = "Contacto de suscripción"
        verbose_name_plural = "Contactos de suscripción"
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["subscription", "email"],
                condition=Q(email__isnull=False),
                name="billing_subscriptioncontact_subscription_email_uniq_when_set",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.subscription.company.name_short})"

    def clean(self) -> None:
        super().clean()
        qs = SubscriptionContact.objects.filter(subscription=self.subscription)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.count() >= self.MAX_CONTACTS:
            raise ValidationError(
                {"subscription": f"Máximo {self.MAX_CONTACTS} contactos por suscripción."}
            )
        if self.email:
            dup = qs.filter(email__iexact=self.email).exists()
            if dup:
                raise ValidationError(
                    {"email": "Ya existe un contacto con este correo en la suscripción."}
                )


class Payment(models.Model):
    """Registro de pagos asociados a una suscripción (auditoría / renovaciones)."""

    class Method(models.TextChoices):
        MANUAL = "manual", "Manual"
        CARD = "card", "Tarjeta"
        TRANSFER = "transfer", "Transferencia"
        STRIPE = "stripe", "Stripe"
        PAYPAL = "paypal", "PayPal"

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Suscripción",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Monto",
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de pago")
    method = models.CharField(
        max_length=50,
        choices=Method.choices,
        default=Method.MANUAL,
        verbose_name="Método de pago",
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ID de transacción",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments_created",
        verbose_name="Creado por",
    )

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-payment_date"]

    def __str__(self) -> str:
        return f"Pago {self.amount} — {self.subscription.company.name_short}"

    def clean(self) -> None:
        super().clean()
        allowed = (Subscription.Status.ACTIVE, Subscription.Status.PENDING)
        if self.subscription_id and self.subscription.status not in allowed:
            raise ValidationError(
                {
                    "subscription": (
                        "Solo se permiten pagos con suscripción activa o pendiente de pago."
                    )
                }
            )
