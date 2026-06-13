from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from apps.table_design.models import DetailTable, HeaderTable
from apps.table_design.services.field_validation import (
    MIN_FIELD_NAME_LONG_LEN,
    MIN_FIELD_NAME_SHORT_LEN,
    validate_field_payload,
)
from apps.table_design.services.auto_key_config import auto_key_initial_from_header
from apps.table_design.services.validation import (
    validate_auto_key_config,
    validate_header_duplicates,
    validate_header_duplicates_edit,
    validate_header_ddl_options,
    validate_header_table,
    validate_pk_constraint_name_unique,
)

_INPUT = (
    "h-[38px] w-full rounded-md border border-gray-600 bg-gray-900 px-2.5 text-sm text-white "
    "outline-none transition focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
)

_SELECT = _INPUT

_CHECKBOX = (
    "h-4 w-4 rounded border-gray-600 bg-gray-900 text-codas-blue-accent "
    "focus:ring-codas-blue-accent"
)

_INPUT_MONO = f"{_INPUT} font-mono"

_TEXTAREA = (
    "w-full rounded-md border border-gray-600 bg-gray-900 px-2.5 py-2 text-sm text-white "
    "outline-none transition focus:border-codas-blue-accent focus:ring-1 focus:ring-codas-blue-accent"
)


def apply_header_ddl_cleaned(
    form: forms.ModelForm,
    cleaned_data: dict,
    *,
    exclude_header_pk: int | None,
) -> None:
    """Normaliza y valida campos DDL de cabecera; escribe resultados en ``cleaned_data``."""
    pk_raw = cleaned_data.get("pk_constraint_name")
    pk_for_val = None if pk_raw in (None, "") else str(pk_raw).strip() or None

    rf_raw = cleaned_data.get("record_format_name")
    rf_for_val = None if rf_raw in (None, "") else str(rf_raw).strip() or None

    ddl = validate_header_ddl_options(
        pk_constraint_name=pk_for_val,
        record_format_name=rf_for_val,
    )
    for fname, msgs in ddl["field_errors"].items():
        for msg in msgs:
            form.add_error(fname, msg)
    if not ddl["ok"]:
        return

    id_start = cleaned_data.get("identity_start")
    id_inc = cleaned_data.get("identity_increment")
    id_cache = cleaned_data.get("identity_cache")
    id_cycle = bool(cleaned_data.get("identity_cycle"))

    auto_key = validate_auto_key_config(
        identity_start=id_start,
        identity_increment=id_inc,
        identity_cache=id_cache,
        identity_cycle=id_cycle,
    )
    for fname, msgs in auto_key["field_errors"].items():
        for msg in msgs:
            form.add_error(fname, msg)
    if not auto_key["ok"]:
        return

    n = ddl["normalized"]
    cleaned_data["pk_constraint_name"] = n["pk_constraint_name"]
    cleaned_data["record_format_name"] = n["record_format_name"]

    ak = auto_key["normalized"]
    cleaned_data["identity_start"] = ak["identity_start"]
    cleaned_data["identity_increment"] = ak["identity_increment"]
    cleaned_data["identity_cache"] = ak["identity_cache"]
    cleaned_data["identity_cycle"] = ak["identity_cycle"]

    uniq = validate_pk_constraint_name_unique(
        pk_constraint_name=n["pk_constraint_name"],
        exclude_header_pk=exclude_header_pk,
    )
    for fname, msgs in uniq["field_errors"].items():
        for msg in msgs:
            form.add_error(fname, msg)


class _HeaderAutoKeyFieldsMixin:
    """Campos IDENTITY persistidos en ``HeaderTableAutoKeyConfig`` (no en ``HeaderTable``)."""

    AUTO_KEY_FIELD_NAMES = (
        "identity_start",
        "identity_increment",
        "identity_cache",
        "identity_cycle",
    )

    def _install_auto_key_fields(self) -> None:
        """
        Registra campos en ``self.fields`` (no como atributos de clase).

        Evita que la plantilla resuelva ``form.identity_start`` al objeto Field
        en lugar del widget HTML (colisión con declaración a nivel de clase).
        """
        self.fields["identity_start"] = forms.IntegerField(
            required=False,
            label="IDENTITY: START WITH",
            min_value=1,
            widget=forms.NumberInput(
                attrs={"class": _INPUT, "min": 1, "step": 1, "placeholder": "1"}
            ),
        )
        self.fields["identity_increment"] = forms.IntegerField(
            required=False,
            label="IDENTITY: INCREMENT BY",
            min_value=1,
            widget=forms.NumberInput(
                attrs={"class": _INPUT, "min": 1, "step": 1, "placeholder": "1"}
            ),
        )
        self.fields["identity_cache"] = forms.IntegerField(
            required=False,
            label="IDENTITY: CACHE",
            min_value=1,
            widget=forms.NumberInput(
                attrs={"class": _INPUT, "min": 1, "step": 1, "placeholder": "1000"}
            ),
        )
        self.fields["identity_cycle"] = forms.BooleanField(
            required=False,
            label="IDENTITY: CYCLE",
            widget=forms.CheckboxInput(attrs={"class": _CHECKBOX}),
        )

    def _bind_auto_key_initial(self) -> None:
        if not getattr(self.instance, "pk", None):
            return
        for key, value in auto_key_initial_from_header(self.instance).items():
            if key in self.fields:
                self.fields[key].initial = value


class HeaderTableCreateForm(_HeaderAutoKeyFieldsMixin, forms.ModelForm):
    def __init__(self, *args, company_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._install_auto_key_fields()
        self.company_id = company_id
        if company_id is not None:
            self.instance.company_id = company_id

    class Meta:
        model = HeaderTable
        fields = [
            "table_model",
            "table_name_long",
            "table_name_short",
            "schema",
            "table_type",
            "status",
            "pk_constraint_name",
            "record_format_name",
            "notes",
        ]
        widgets = {
            "table_model": forms.Select(attrs={"class": _SELECT}),
            "table_name_long": forms.TextInput(
                attrs={"class": _INPUT, "maxlength": "128", "autocomplete": "off"}
            ),
            "table_name_short": forms.TextInput(
                attrs={"class": _INPUT, "maxlength": "10", "autocomplete": "off"}
            ),
            "schema": forms.TextInput(
                attrs={"class": _INPUT, "maxlength": "10", "autocomplete": "off"}
            ),
            "table_type": forms.Select(attrs={"class": _SELECT}),
            "status": forms.Select(attrs={"class": _SELECT}),
            "pk_constraint_name": forms.TextInput(
                attrs={
                    "class": _INPUT_MONO,
                    "maxlength": "30",
                    "autocomplete": "off",
                }
            ),
            "record_format_name": forms.TextInput(
                attrs={
                    "class": _INPUT_MONO,
                    "maxlength": "30",
                    "autocomplete": "off",
                }
            ),
            "notes": forms.Textarea(attrs={"class": _TEXTAREA, "rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if self.company_id is not None:
            self.instance.company_id = self.company_id

        raw_long = (cleaned_data.get("table_name_long") or "").strip()
        raw_short = (cleaned_data.get("table_name_short") or "").strip().upper()
        raw_schema = (cleaned_data.get("schema") or "").strip()
        schema_norm = raw_schema if raw_schema else None
        raw_notes = cleaned_data.get("notes")
        notes_str = (raw_notes or "").strip()
        notes_norm = notes_str if notes_str else None

        cleaned_data["table_name_long"] = raw_long
        cleaned_data["table_name_short"] = raw_short
        cleaned_data["schema"] = schema_norm
        cleaned_data["notes"] = notes_norm

        fmt = validate_header_table(
            table_name_long=raw_long,
            table_name_short=raw_short,
            schema=schema_norm,
            notes=notes_norm,
        )
        for fname, msgs in fmt["field_errors"].items():
            for msg in msgs:
                self.add_error(fname, msg)

        if not fmt["ok"]:
            return cleaned_data

        if self.company_id is None:
            raise ValidationError(
                "No se pudo determinar la compañía del perfil; no se puede crear la cabecera."
            )

        dup = validate_header_duplicates(
            self.company_id,
            raw_long,
            raw_short,
        )
        for fname, msgs in dup["field_errors"].items():
            for msg in msgs:
                self.add_error(fname, msg)

        if not dup["ok"]:
            return cleaned_data

        apply_header_ddl_cleaned(self, cleaned_data, exclude_header_pk=None)
        return cleaned_data


class HeaderTableUpdateForm(_HeaderAutoKeyFieldsMixin, forms.ModelForm):
    """Edición de cabecera: todos los campos editables salvo bloqueo por estado inactivo."""

    def __init__(self, *args, company_id=None, can_edit_identity=True, **kwargs):
        super().__init__(*args, **kwargs)
        self._install_auto_key_fields()
        self.company_id = company_id
        self.can_edit_identity = can_edit_identity
        if company_id is not None:
            self.instance.company_id = company_id
        self._bind_auto_key_initial()
        if not can_edit_identity:
            for name in (
                "table_name_long",
                "table_name_short",
                "schema",
                "pk_constraint_name",
                "record_format_name",
                "identity_start",
                "identity_increment",
                "identity_cache",
                "identity_cycle",
            ):
                if name in self.fields:
                    self.fields[name].disabled = True

    class Meta:
        model = HeaderTable
        fields = [
            "table_model",
            "table_name_long",
            "table_name_short",
            "schema",
            "table_type",
            "status",
            "pk_constraint_name",
            "record_format_name",
            "notes",
        ]
        widgets = {
            "table_model": forms.Select(attrs={"class": _SELECT}),
            "table_name_long": forms.TextInput(
                attrs={"class": _INPUT, "maxlength": "128", "autocomplete": "off"}
            ),
            "table_name_short": forms.TextInput(
                attrs={"class": _INPUT, "maxlength": "10", "autocomplete": "off"}
            ),
            "schema": forms.TextInput(
                attrs={"class": _INPUT, "maxlength": "10", "autocomplete": "off"}
            ),
            "table_type": forms.Select(attrs={"class": _SELECT}),
            "status": forms.Select(attrs={"class": _SELECT}),
            "pk_constraint_name": forms.TextInput(
                attrs={
                    "class": _INPUT_MONO,
                    "maxlength": "30",
                    "autocomplete": "off",
                }
            ),
            "record_format_name": forms.TextInput(
                attrs={
                    "class": _INPUT_MONO,
                    "maxlength": "30",
                    "autocomplete": "off",
                }
            ),
            "notes": forms.Textarea(attrs={"class": _TEXTAREA, "rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if self.company_id is not None:
            self.instance.company_id = self.company_id

        if self.can_edit_identity:
            raw_long = (cleaned_data.get("table_name_long") or "").strip()
            raw_short = (cleaned_data.get("table_name_short") or "").strip().upper()
            raw_schema = (cleaned_data.get("schema") or "").strip()
        else:
            raw_long = (self.instance.table_name_long or "").strip()
            raw_short = (self.instance.table_name_short or "").strip().upper()
            raw_schema = (self.instance.schema or "").strip()

        schema_norm = raw_schema if raw_schema else None
        raw_notes = cleaned_data.get("notes")
        notes_str = (raw_notes or "").strip()
        notes_norm = notes_str if notes_str else None

        cleaned_data["table_name_long"] = raw_long
        cleaned_data["table_name_short"] = raw_short
        cleaned_data["schema"] = schema_norm
        cleaned_data["notes"] = notes_norm

        fmt = validate_header_table(
            table_name_long=raw_long,
            table_name_short=raw_short,
            schema=schema_norm,
            notes=notes_norm,
        )
        for fname, msgs in fmt["field_errors"].items():
            for msg in msgs:
                self.add_error(fname, msg)

        if not fmt["ok"]:
            return cleaned_data

        if self.company_id is None or self.instance.pk is None:
            raise ValidationError(
                "No se pudo determinar la compañía o el registro a actualizar."
            )

        if self.can_edit_identity:
            dup = validate_header_duplicates_edit(
                self.company_id,
                self.instance.pk,
                raw_long,
                raw_short,
            )
            for fname, msgs in dup["field_errors"].items():
                for msg in msgs:
                    self.add_error(fname, msg)
            if not dup["ok"]:
                return cleaned_data

        apply_header_ddl_cleaned(
            self,
            cleaned_data,
            exclude_header_pk=self.instance.pk,
        )
        return cleaned_data


class DetailTableForm(forms.ModelForm):
    """Alta/edición de campo (`DetailTable`) bajo una cabecera."""

    field_length = forms.IntegerField(required=False, min_value=0)
    decimal_places = forms.IntegerField(required=False, min_value=0)
    allocate_length = forms.IntegerField(
        required=False,
        min_value=0,
        help_text="Obligatorio para VARCHAR y VARGRAPHIC (suballocación DB2).",
    )
    order_key = forms.IntegerField(required=False, min_value=1)
    notes = forms.CharField(
        required=True,
        strip=True,
        widget=forms.Textarea(attrs={"class": _TEXTAREA, "rows": 2}),
    )

    def __init__(
        self,
        *args,
        header: HeaderTable | None = None,
        exclude_field_id: int | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.header = header
        self.exclude_field_id = exclude_field_id

    class Meta:
        model = DetailTable
        fields = [
            "field_name_long",
            "field_name_short",
            "field_type",
            "field_length",
            "decimal_places",
            "allocate_length",
            "is_key",
            "order_key",
            "column_label",
            "column_text",
            "notes",
        ]
        widgets = {
            "field_name_long": forms.TextInput(
                attrs={
                    "class": _INPUT,
                    "maxlength": "30",
                    "minlength": str(MIN_FIELD_NAME_LONG_LEN),
                    "autocomplete": "off",
                }
            ),
            "field_name_short": forms.TextInput(
                attrs={
                    "class": _INPUT,
                    "maxlength": "10",
                    "minlength": str(MIN_FIELD_NAME_SHORT_LEN),
                    "autocomplete": "off",
                }
            ),
            "field_type": forms.Select(attrs={"class": _SELECT}),
            "field_length": forms.NumberInput(
                attrs={"class": _INPUT, "min": 0, "step": 1}
            ),
            "decimal_places": forms.NumberInput(
                attrs={"class": _INPUT, "min": 0, "step": 1}
            ),
            "allocate_length": forms.NumberInput(
                attrs={"class": _INPUT, "min": 0, "step": 1, "placeholder": "ALLOCATE"}
            ),
            "is_key": forms.CheckboxInput(
                attrs={
                    "class": "rounded border-gray-600 bg-gray-900 text-codas-blue-accent focus:ring-codas-blue-accent"
                }
            ),
            "order_key": forms.NumberInput(attrs={"class": _INPUT, "min": 1, "step": 1}),
            "column_label": forms.TextInput(
                attrs={"class": _INPUT, "maxlength": "20", "autocomplete": "off"}
            ),
            "column_text": forms.TextInput(
                attrs={
                    "class": _INPUT,
                    "maxlength": "50",
                    "autocomplete": "off",
                    "placeholder": "TEXT IS (opcional, máx. 50)",
                },
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        if self.header is None:
            raise ValidationError("Cabecera no definida para validar el campo.")

        is_key = bool(cleaned_data.get("is_key"))

        payload = validate_field_payload(
            header=self.header,
            name_long=cleaned_data.get("field_name_long"),
            name_short=cleaned_data.get("field_name_short"),
            field_type=cleaned_data.get("field_type") or "",
            field_length=cleaned_data.get("field_length"),
            decimal_places=cleaned_data.get("decimal_places"),
            allocate_length=cleaned_data.get("allocate_length"),
            nullable=True,
            is_key=is_key,
            order_key=cleaned_data.get("order_key"),
            notes=cleaned_data.get("notes"),
            exclude_field_id=self.exclude_field_id,
            column_label=cleaned_data.get("column_label") or "",
            column_text=cleaned_data.get("column_text") or "",
        )
        if not payload["ok"]:
            for msg in payload["errors"]:
                self.add_error(None, msg)
            return cleaned_data

        n = payload["normalized"]
        assert n is not None
        cleaned_data["field_name_long"] = n["field_name_long"]
        cleaned_data["field_name_short"] = n["field_name_short"]
        cleaned_data["field_type"] = n["field_type"]
        cleaned_data["field_length"] = n["field_length"]
        cleaned_data["decimal_places"] = n["decimal_places"]
        cleaned_data["allocate_length"] = n["allocate_length"]
        cleaned_data["is_key"] = n["is_key"]
        cleaned_data["order_key"] = n["order_key"]
        cleaned_data["column_label"] = n["column_label"]
        cleaned_data["column_text"] = n["column_text"]
        cleaned_data["notes"] = n["notes"]

        return cleaned_data
