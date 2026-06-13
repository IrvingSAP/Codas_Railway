"""Formularios de facturación (ModelForm alineados con estilos CODAS)."""

from __future__ import annotations

from typing import Any

from django import forms

from apps.billing.models import Payment, Plan, Subscription, SubscriptionContact

CODAS_INPUT = (
    "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 "
    "px-2.5 text-sm text-white placeholder:text-gray-500 outline-none "
    "transition focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
)
CODAS_TEXTAREA = (
    "min-h-[100px] w-full rounded-md border border-gray-600 bg-gray-900 "
    "px-2.5 py-2 text-sm text-white outline-none transition "
    "focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
)
CODAS_SELECT = CODAS_INPUT + " max-w-xl"


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["name", "code", "billing_period", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": CODAS_INPUT, "maxlength": "100"}),
            "code": forms.TextInput(attrs={"class": CODAS_INPUT + " font-mono", "maxlength": "50"}),
            "billing_period": forms.Select(attrs={"class": CODAS_SELECT}),
            "description": forms.Textarea(attrs={"class": CODAS_TEXTAREA, "rows": 3}),
            "is_active": forms.CheckboxInput(
                attrs={"class": "h-4 w-4 rounded border-gray-600 bg-gray-900 text-codas-blue-accent"}
            ),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["company", "plan", "start_date", "end_date", "status", "auto_renew"]
        widgets = {
            "company": forms.Select(attrs={"class": CODAS_SELECT}),
            "plan": forms.Select(attrs={"class": CODAS_SELECT}),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": CODAS_INPUT + " max-w-xs"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": CODAS_INPUT + " max-w-xs"}
            ),
            "status": forms.Select(attrs={"class": CODAS_SELECT}),
            "auto_renew": forms.CheckboxInput(
                attrs={"class": "h-4 w-4 rounded border-gray-600 bg-gray-900 text-codas-blue-accent"}
            ),
        }

    def __init__(self, *args: Any, company_queryset: Any = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields["company"]
        elif company_queryset is not None:
            self.fields["company"].queryset = company_queryset


class SubscriptionContactForm(forms.ModelForm):
    class Meta:
        model = SubscriptionContact
        fields = ["subscription", "full_name", "phone", "email", "role", "notes"]
        widgets = {
            "subscription": forms.Select(attrs={"class": CODAS_SELECT}),
            "full_name": forms.TextInput(attrs={"class": CODAS_INPUT, "maxlength": "150"}),
            "phone": forms.TextInput(attrs={"class": CODAS_INPUT, "maxlength": "50"}),
            "email": forms.EmailInput(attrs={"class": CODAS_INPUT}),
            "role": forms.TextInput(attrs={"class": CODAS_INPUT + " max-w-xl", "maxlength": "100"}),
            "notes": forms.Textarea(attrs={"class": CODAS_TEXTAREA, "rows": 3}),
        }

    def __init__(self, *args: Any, subscription_queryset: Any = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if subscription_queryset is not None:
            self.fields["subscription"].queryset = subscription_queryset


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["subscription", "amount", "method", "transaction_id"]
        widgets = {
            "subscription": forms.Select(attrs={"class": CODAS_SELECT}),
            "amount": forms.NumberInput(
                attrs={"class": CODAS_INPUT + " max-w-xs", "step": "0.01", "min": "0.01"}
            ),
            "method": forms.Select(attrs={"class": CODAS_SELECT}),
            "transaction_id": forms.TextInput(
                attrs={"class": CODAS_INPUT + " max-w-xl font-mono text-sm", "maxlength": "100"}
            ),
        }

    def __init__(self, *args: Any, subscription_queryset: Any = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if subscription_queryset is not None:
            self.fields["subscription"].queryset = subscription_queryset
