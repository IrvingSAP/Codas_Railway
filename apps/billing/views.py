"""Vistas HTTP de facturación (planes, suscripciones, contactos, pagos)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.billing.forms import (
    PaymentForm,
    PlanForm,
    SubscriptionContactForm,
    SubscriptionForm,
)
from apps.billing.models import Payment, Plan, Subscription, SubscriptionContact
from apps.billing.services.access import (
    companies_for_new_subscription,
    payment_queryset_for_user,
    subscription_queryset_for_related_forms,
    subscription_queryset_for_user,
    subscriptioncontact_queryset_for_user,
    user_can_view_payment,
    user_can_view_subscription,
    user_can_view_subscriptioncontact,
)
from apps.company.services.access import is_superuser_profile
from apps.company.views import (
    _require_profile,
    require_company_maintainer,
    require_superuser_company,
)
from apps.userprofile.models import UserProfile


def _billing_ctx(request: HttpRequest, **extra) -> dict:
    profile = request.user.profile
    return {
        "profile": profile,
        "dashboard_nav_active": "billing",
        "can_crud": is_superuser_profile(profile),
        **extra,
    }


# --- Hub ---


@login_required
@_require_profile
@require_company_maintainer
def billing_hub(request: HttpRequest) -> HttpResponse:
    return render(request, "billing/hub.html", _billing_ctx(request))


# --- Plan ---


@login_required
@_require_profile
@require_company_maintainer
def plan_list(request: HttpRequest) -> HttpResponse:
    plans = Plan.objects.all().order_by("code")
    return render(request, "billing/plan_list.html", _billing_ctx(request, plans=plans))


@login_required
@_require_profile
@require_company_maintainer
def plan_detail(request: HttpRequest, pk: int) -> HttpResponse:
    plan = get_object_or_404(Plan, pk=pk)
    return render(request, "billing/plan_detail.html", _billing_ctx(request, plan=plan))


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def plan_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan creado correctamente.")
            return redirect("billing:plan_detail", pk=form.instance.pk)
    else:
        form = PlanForm()
    return render(
        request,
        "billing/plan_form.html",
        _billing_ctx(request, form=form, is_edit=False),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def plan_update(request: HttpRequest, pk: int) -> HttpResponse:
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan actualizado correctamente.")
            return redirect("billing:plan_detail", pk=plan.pk)
    else:
        form = PlanForm(instance=plan)
    return render(
        request,
        "billing/plan_form.html",
        _billing_ctx(request, form=form, plan=plan, is_edit=True),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def plan_delete(request: HttpRequest, pk: int) -> HttpResponse:
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        try:
            plan.delete()
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar el plan: hay suscripciones que lo referencian.",
            )
            return redirect("billing:plan_detail", pk=pk)
        messages.success(request, "Plan eliminado correctamente.")
        return redirect("billing:plan_list")
    return render(
        request,
        "billing/plan_confirm_delete.html",
        _billing_ctx(request, plan=plan),
    )


# --- Subscription ---


@login_required
@_require_profile
@require_company_maintainer
def subscription_list(request: HttpRequest) -> HttpResponse:
    subscriptions = subscription_queryset_for_user(request.user)
    return render(
        request,
        "billing/subscription_list.html",
        _billing_ctx(request, subscriptions=subscriptions),
    )


@login_required
@_require_profile
@require_company_maintainer
def subscription_detail(request: HttpRequest, pk: int) -> HttpResponse:
    subscription = get_object_or_404(
        Subscription.objects.select_related("company", "plan").prefetch_related(
            "contacts", "payments"
        ),
        pk=pk,
    )
    if not user_can_view_subscription(request.user, subscription):
        raise Http404()
    license_info = subscription.validate_license()
    return render(
        request,
        "billing/subscription_detail.html",
        _billing_ctx(
            request,
            subscription=subscription,
            license_info=license_info,
        ),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def subscription_create(request: HttpRequest) -> HttpResponse:
    companies_qs = companies_for_new_subscription(request.user)
    if not companies_qs.exists():
        messages.warning(
            request,
            "No hay compañías disponibles para asignar una suscripción "
            "(todas tienen ya una suscripción o no tiene compañía asignada).",
        )
        return redirect("billing:subscription_list")

    if request.method == "POST":
        form = SubscriptionForm(
            request.POST,
            company_queryset=companies_qs,
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
            messages.success(request, "Suscripción creada correctamente.")
            return redirect("billing:subscription_detail", pk=obj.pk)
    else:
        form = SubscriptionForm(company_queryset=companies_qs)
    return render(
        request,
        "billing/subscription_form.html",
        _billing_ctx(request, form=form, is_edit=False),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def subscription_update(request: HttpRequest, pk: int) -> HttpResponse:
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            messages.success(request, "Suscripción actualizada correctamente.")
            return redirect("billing:subscription_detail", pk=obj.pk)
    else:
        form = SubscriptionForm(instance=subscription)
    return render(
        request,
        "billing/subscription_form.html",
        _billing_ctx(request, form=form, subscription=subscription, is_edit=True),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def subscription_delete(request: HttpRequest, pk: int) -> HttpResponse:
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == "POST":
        subscription.delete()
        messages.success(request, "Suscripción eliminada correctamente.")
        return redirect("billing:subscription_list")
    return render(
        request,
        "billing/subscription_confirm_delete.html",
        _billing_ctx(request, subscription=subscription),
    )


# --- SubscriptionContact ---


@login_required
@_require_profile
@require_company_maintainer
def subscriptioncontact_list(request: HttpRequest) -> HttpResponse:
    contacts = subscriptioncontact_queryset_for_user(request.user)
    return render(
        request,
        "billing/subscriptioncontact_list.html",
        _billing_ctx(request, contacts=contacts),
    )


@login_required
@_require_profile
@require_company_maintainer
def subscriptioncontact_detail(request: HttpRequest, pk: int) -> HttpResponse:
    contact = get_object_or_404(
        SubscriptionContact.objects.select_related("subscription", "subscription__company"),
        pk=pk,
    )
    if not user_can_view_subscriptioncontact(request.user, contact):
        raise Http404()
    return render(
        request,
        "billing/subscriptioncontact_detail.html",
        _billing_ctx(request, contact=contact),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def subscriptioncontact_create(request: HttpRequest) -> HttpResponse:
    sub_qs = subscription_queryset_for_related_forms(request.user)
    if not sub_qs.exists():
        messages.warning(request, "No hay suscripciones donde registrar contactos.")
        return redirect("billing:subscriptioncontact_list")

    if request.method == "POST":
        form = SubscriptionContactForm(
            request.POST,
            subscription_queryset=sub_qs,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Contacto registrado correctamente.")
            return redirect("billing:subscriptioncontact_detail", pk=form.instance.pk)
    else:
        form = SubscriptionContactForm(subscription_queryset=sub_qs)
    return render(
        request,
        "billing/subscriptioncontact_form.html",
        _billing_ctx(request, form=form, is_edit=False),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def subscriptioncontact_update(request: HttpRequest, pk: int) -> HttpResponse:
    contact = get_object_or_404(SubscriptionContact, pk=pk)
    if not user_can_view_subscriptioncontact(request.user, contact):
        raise Http404()
    sub_qs = subscription_queryset_for_related_forms(request.user)
    if request.method == "POST":
        form = SubscriptionContactForm(
            request.POST,
            instance=contact,
            subscription_queryset=sub_qs,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Contacto actualizado correctamente.")
            return redirect("billing:subscriptioncontact_detail", pk=contact.pk)
    else:
        form = SubscriptionContactForm(
            instance=contact,
            subscription_queryset=sub_qs,
        )
    return render(
        request,
        "billing/subscriptioncontact_form.html",
        _billing_ctx(request, form=form, contact=contact, is_edit=True),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def subscriptioncontact_delete(request: HttpRequest, pk: int) -> HttpResponse:
    contact = get_object_or_404(SubscriptionContact, pk=pk)
    if not user_can_view_subscriptioncontact(request.user, contact):
        raise Http404()
    if request.method == "POST":
        contact.delete()
        messages.success(request, "Contacto eliminado correctamente.")
        return redirect("billing:subscriptioncontact_list")
    return render(
        request,
        "billing/subscriptioncontact_confirm_delete.html",
        _billing_ctx(request, contact=contact),
    )


# --- Payment ---


@login_required
@_require_profile
@require_company_maintainer
def payment_list(request: HttpRequest) -> HttpResponse:
    payments = payment_queryset_for_user(request.user)
    return render(
        request,
        "billing/payment_list.html",
        _billing_ctx(request, payments=payments),
    )


@login_required
@_require_profile
@require_company_maintainer
def payment_detail(request: HttpRequest, pk: int) -> HttpResponse:
    payment = get_object_or_404(
        Payment.objects.select_related("subscription", "subscription__company"),
        pk=pk,
    )
    if not user_can_view_payment(request.user, payment):
        raise Http404()
    return render(
        request,
        "billing/payment_detail.html",
        _billing_ctx(request, payment=payment),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def payment_create(request: HttpRequest) -> HttpResponse:
    sub_qs = subscription_queryset_for_related_forms(request.user)
    if not sub_qs.exists():
        messages.warning(request, "No hay suscripciones donde registrar pagos.")
        return redirect("billing:payment_list")

    if request.method == "POST":
        form = PaymentForm(request.POST, subscription_queryset=sub_qs)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Pago registrado correctamente.")
            return redirect("billing:payment_detail", pk=obj.pk)
    else:
        form = PaymentForm(subscription_queryset=sub_qs)
    return render(
        request,
        "billing/payment_form.html",
        _billing_ctx(request, form=form, is_edit=False),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def payment_update(request: HttpRequest, pk: int) -> HttpResponse:
    payment = get_object_or_404(Payment, pk=pk)
    if not user_can_view_payment(request.user, payment):
        raise Http404()
    sub_qs = subscription_queryset_for_related_forms(request.user)
    if request.method == "POST":
        form = PaymentForm(
            request.POST,
            instance=payment,
            subscription_queryset=sub_qs,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Pago actualizado correctamente.")
            return redirect("billing:payment_detail", pk=payment.pk)
    else:
        form = PaymentForm(instance=payment, subscription_queryset=sub_qs)
    return render(
        request,
        "billing/payment_form.html",
        _billing_ctx(request, form=form, payment=payment, is_edit=True),
    )


@login_required
@_require_profile
@require_superuser_company
@require_http_methods(["GET", "POST"])
def payment_delete(request: HttpRequest, pk: int) -> HttpResponse:
    payment = get_object_or_404(Payment, pk=pk)
    if not user_can_view_payment(request.user, payment):
        raise Http404()
    if request.method == "POST":
        payment.delete()
        messages.success(request, "Pago eliminado correctamente.")
        return redirect("billing:payment_list")
    return render(
        request,
        "billing/payment_confirm_delete.html",
        _billing_ctx(request, payment=payment),
    )
