from django import forms

from apps.company.models import Company


class CompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No está en POST si no se renderiza; el modelo tiene default=78.
        field = self.fields["sql_max_line_length"]
        field.required = False
        if self.instance.pk is None and not self.data:
            field.initial = 78

    class Meta:
        model = Company
        fields = [
            "name_short",
            "name_long",
            "tax_id",
            "address",
            "phone",
            "email",
            "logo",
            "sql_max_line_length",
            "is_active",
        ]
        widgets = {
            "name_short": forms.TextInput(
                attrs={
                    "class": (
                        "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 "
                        "px-2.5 text-sm text-white placeholder:text-gray-500 outline-none "
                        "transition focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
                    ),
                    "maxlength": "15",
                }
            ),
            "name_long": forms.TextInput(
                attrs={
                    "class": (
                        "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 "
                        "px-2.5 text-sm text-white outline-none transition "
                        "focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
                    ),
                    "maxlength": "150",
                }
            ),
            "tax_id": forms.TextInput(
                attrs={
                    "class": (
                        "h-[38px] w-full max-w-md rounded-md border border-gray-600 bg-gray-900 "
                        "px-2.5 text-sm text-white outline-none transition "
                        "focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
                    ),
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": (
                        "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 "
                        "px-2.5 text-sm text-white outline-none transition "
                        "focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
                    ),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": (
                        "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 "
                        "px-2.5 text-sm text-white outline-none transition "
                        "focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
                    ),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": (
                        "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 "
                        "px-2.5 text-sm text-white outline-none transition "
                        "focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
                    ),
                }
            ),
            "logo": forms.ClearableFileInput(
                attrs={
                    "class": (
                        "block w-full max-w-md text-sm text-gray-400 file:mr-4 file:rounded-md "
                        "file:border-0 file:bg-gray-700 file:px-3 file:py-2 file:text-gray-200"
                    ),
                }
            ),
            "sql_max_line_length": forms.NumberInput(
                attrs={
                    "class": (
                        "h-[38px] w-full max-w-xs rounded-md border border-gray-600 bg-gray-900 "
                        "px-2.5 text-sm text-white outline-none transition "
                        "focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
                    ),
                    "min": "40",
                    "max": "180",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "h-4 w-4 rounded border-gray-600 bg-gray-900 text-codas-blue-accent"}
            ),
        }
