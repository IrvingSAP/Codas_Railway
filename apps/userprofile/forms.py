"""Formularios del mantenimiento de perfiles (panel)."""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model

from apps.company.models import Company
from apps.userprofile.models import UserProfile

User = get_user_model()

_INPUT = (
    "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 px-2.5 text-sm text-white "
    "outline-none transition focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
)
_SELECT = _INPUT
_TEXTAREA = (
    "w-full rounded-md border border-gray-600 bg-gray-900 px-2.5 py-2 text-sm text-white "
    "outline-none transition focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
)


class UserProfileMaintainerForm(forms.ModelForm):
    """Alta/edición de campos de negocio del perfil (no campos de seguridad internos)."""

    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": _INPUT, "maxlength": "150"}),
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": _INPUT, "maxlength": "150"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=False,
        widget=forms.EmailInput(attrs={"class": _INPUT, "maxlength": "254", "autocomplete": "email"}),
    )
    password1 = forms.CharField(
        label="Contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={"class": _INPUT, "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={"class": _INPUT, "autocomplete": "new-password"}),
    )

    class Meta:
        model = UserProfile
        fields = [
            "company",
            "phone",
            "document_id",
            "address",
            "status",
        ]
        widgets = {
            "company": forms.Select(attrs={"class": _SELECT}),
            "phone": forms.TextInput(attrs={"class": _INPUT, "maxlength": "20"}),
            "document_id": forms.TextInput(attrs={"class": _INPUT, "maxlength": "50"}),
            "address": forms.TextInput(attrs={"class": _INPUT, "maxlength": "255"}),
            "status": forms.Select(attrs={"class": _SELECT}),
        }

    def __init__(
        self,
        *args,
        connection_profile: UserProfile,
        show_company_select: bool,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._connection_profile = connection_profile
        user = self.instance.user if getattr(self.instance, "pk", None) else None
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
            self.fields["password1"].help_text = "Opcional: solo diligencie para cambiar la contraseña."
            self.fields["password2"].help_text = "Repita la contraseña nueva para confirmar."
        if show_company_select:
            self.fields["company"].queryset = Company.objects.all().order_by("name_short")
            self.fields["company"].required = False
        else:
            del self.fields["company"]

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            elif len(p1) < 8:
                self.add_error("password1", "La contraseña debe tener al menos 8 caracteres.")
        return cleaned


class UserProfileCreateForm(UserProfileMaintainerForm):
    """Incluye elección de usuario Django sin perfil existente."""

    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"class": _INPUT, "maxlength": "150", "autocomplete": "username"}),
    )
    class Meta(UserProfileMaintainerForm.Meta):
        fields = ["username", "email"] + list(UserProfileMaintainerForm.Meta.fields)

    def __init__(
        self,
        *args,
        connection_profile: UserProfile,
        show_company_select: bool,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            connection_profile=connection_profile,
            show_company_select=show_company_select,
            **kwargs,
        )
        self.fields["password1"].required = True
        self.fields["password2"].required = True
        self.fields["password1"].help_text = "Obligatoria para crear el usuario."
        self.fields["password2"].help_text = "Repita la contraseña para confirmar."

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise forms.ValidationError("El usuario es obligatorio.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ya existe un usuario con ese nombre.")
        return username
