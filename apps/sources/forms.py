from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from apps.sources.models import SourceTemplate

_INPUT = (
    "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 px-2.5 text-sm text-white "
    "outline-none transition focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
)

_SELECT = _INPUT

_TEXTAREA = (
    "w-full rounded-md border border-gray-600 bg-gray-900 px-2.5 py-2 text-sm text-white "
    "outline-none transition focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
)

_SOURCE_TEXT = (
    "w-full rounded-md border border-emerald-700 bg-[#07120a] px-2.5 py-2 font-mono text-sm text-emerald-400 "
    "outline-none transition focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
)


class SourceTemplateForm(forms.ModelForm):
    def __init__(self, *args, company_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_id = company_id
        # Siempre usar company_id (no solo el FK en memoria): así validate_unique
        # coincide con lo que se persiste en source_create / source_update.
        if company_id is not None:
            self.instance.company_id = company_id

    class Meta:
        model = SourceTemplate
        fields = [
            "name",
            "description",
            "filename",
            "source_text",
            "source_type",
            "version",
            "status",
        ]
        help_texts = {
            "filename": (
                "Opcional. Si lo indica, la extensión debe coincidir con el tipo de fuente "
                "(p. ej. .dspf para Pantalla DDS, .sqlrpgle para Programa SQLRPGLE)."
            ),
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": _INPUT, "maxlength": "100"}),
            "description": forms.TextInput(attrs={"class": _INPUT, "maxlength": "255"}),
            "filename": forms.TextInput(attrs={"class": _INPUT, "maxlength": "100"}),
            "source_text": forms.Textarea(attrs={"class": _SOURCE_TEXT, "rows": 10}),
            "source_type": forms.Select(attrs={"class": _SELECT}),
            "version": forms.NumberInput(attrs={"class": _INPUT, "min": "1"}),
            "status": forms.Select(attrs={"class": _SELECT}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if self.company_id is not None:
            self.instance.company_id = self.company_id

        name = cleaned_data.get("name")
        version = cleaned_data.get("version")
        if self.company_id is not None and name not in (None, "") and version is not None:
            qs = SourceTemplate.objects.filter(
                company_id=self.company_id,
                name=name,
                version=version,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    "Ya existe una plantilla con este nombre y versión para su compañía. "
                    "Cambie el nombre o incremente la versión."
                )
        return cleaned_data
