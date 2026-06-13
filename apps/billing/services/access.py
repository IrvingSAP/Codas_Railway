"""Reglas de acceso a facturación (planes, suscripciones, contactos, pagos) por UserProfile."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import QuerySet

from apps.billing.models import Payment, Plan, Subscription, SubscriptionContact
from apps.company.models import Company
from apps.company.services.access import is_superuser_profile
from apps.userprofile.models import UserProfile

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def subscription_queryset_for_user(user: AbstractUser) -> QuerySet[Subscription]:
    """Listados de suscripción: SU ve todo; AC solo la de su compañía."""
    profile = user.profile
    qs = Subscription.objects.select_related("company", "plan")
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return qs.order_by("-created_at")
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY and profile.company_id:
        return qs.filter(company_id=profile.company_id).order_by("-created_at")
    return Subscription.objects.none()


def user_can_view_subscription(user: AbstractUser, subscription: Subscription) -> bool:
    profile = user.profile
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return True
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY:
        return profile.company_id == subscription.company_id
    return False


def companies_for_new_subscription(user: AbstractUser) -> QuerySet[Company]:
    """Compañías sin fila de suscripción aún; AC solo la suya si aplica."""
    profile = user.profile
    base = Company.objects.filter(subscription__isnull=True).order_by("name_short")
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return base
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY and profile.company_id:
        return base.filter(pk=profile.company_id)
    return Company.objects.none()


def subscription_queryset_for_related_forms(user: AbstractUser) -> QuerySet[Subscription]:
    """Selector de suscripción en contactos y pagos."""
    return subscription_queryset_for_user(user)


def subscriptioncontact_queryset_for_user(user: AbstractUser) -> QuerySet[SubscriptionContact]:
    profile = user.profile
    qs = SubscriptionContact.objects.select_related("subscription", "subscription__company")
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return qs.order_by("subscription_id", "pk")
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY and profile.company_id:
        return qs.filter(subscription__company_id=profile.company_id).order_by(
            "subscription_id", "pk"
        )
    return SubscriptionContact.objects.none()


def user_can_view_subscriptioncontact(
    user: AbstractUser, contact: SubscriptionContact
) -> bool:
    return user_can_view_subscription(user, contact.subscription)


def payment_queryset_for_user(user: AbstractUser) -> QuerySet[Payment]:
    profile = user.profile
    qs = Payment.objects.select_related("subscription", "subscription__company")
    if profile.user_type == UserProfile.UserType.SUPERUSER:
        return qs.order_by("-payment_date")
    if profile.user_type == UserProfile.UserType.ADMIN_COMPANY and profile.company_id:
        return qs.filter(subscription__company_id=profile.company_id).order_by("-payment_date")
    return Payment.objects.none()


def user_can_view_payment(user: AbstractUser, payment: Payment) -> bool:
    return user_can_view_subscription(user, payment.subscription)


def can_write_billing(user: AbstractUser) -> bool:
    """Alta/edición/baja: solo superusuario (misma regla que compañías)."""
    return is_superuser_profile(user.profile)
