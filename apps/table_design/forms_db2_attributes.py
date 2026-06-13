"""Formulario paso 2: atributos DB2 (`DetailTableDb2Attributes`)."""

from __future__ import annotations

from typing import Any

from django import forms
from django.core.exceptions import ValidationError

from apps.table_design.models import DetailTable, DetailTableDb2Attributes
from apps.table_design.services.db2_attributes_ui import (
    DB2_ATTRIBUTE_UI_ROWS,
    DB2_UI_FIELD_KEYS,
)
from apps.table_design.services.field_validation import CCSID_FIELD_TYPES

_CHECKBOX = (
    "h-4 w-4 rounded border-gray-600 bg-gray-900 text-codas-blue-accent "
    "focus:ring-codas-blue-accent"
)
_INPUT = (
    "codas-input h-9 w-full rounded-md border border-gray-600 bg-gray-900 "
    "px-2.5 text-sm text-white outline-none focus:border-codas-blue-accent "
    "focus:ring-1 focus:ring-codas-blue-accent"
)
_TEXTAREA = (
    "codas-textarea w-full rounded-md border border-gray-600 bg-gray-900 "
    "px-2.5 py-2 text-sm text-white outline-none focus:border-codas-blue-accent "
    "focus:ring-1 focus:ring-codas-blue-accent"
)


def _sel_name(field_key: str) -> str:
    return f"sel_{field_key}"


class DetailTableDb2AttributesForm(forms.Form):
    """Atributos DB2 por columna; selección múltiple salvo `user_defined_field`."""

    def __init__(
        self,
        *args,
        detail: DetailTable,
        attrs_instance: DetailTableDb2Attributes | None = None,
        **kwargs,
    ):
        self.detail = detail
        self.attrs_instance = attrs_instance
        super().__init__(*args, **kwargs)

        for row in DB2_ATTRIBUTE_UI_ROWS:
            key = row.field_key
            initial_sel = False
            if attrs_instance is not None:
                initial_sel = _row_selected(attrs_instance, row)
            sel_attrs = {
                "class": _CHECKBOX,
                "data-field": key,
                "data-row-select": "1",
            }
            if key == "user_defined_field":
                sel_attrs["id"] = "sel-user_defined_field"
            self.fields[_sel_name(key)] = forms.BooleanField(
                required=False,
                initial=initial_sel,
                widget=forms.CheckboxInput(attrs=sel_attrs),
            )

        self.fields["ccsid"] = forms.IntegerField(
            required=False,
            min_value=0,
            widget=forms.NumberInput(
                attrs={"class": _INPUT, "placeholder": "1208", "data-attr-input": "1"}
            ),
        )
        self.fields["default_sql_expression"] = forms.CharField(
            required=False,
            max_length=200,
            widget=forms.TextInput(
                attrs={
                    "class": _INPUT,
                    "placeholder": "CURRENT TIMESTAMP",
                    "data-attr-input": "1",
                }
            ),
        )
        self.fields["nullable_mode"] = forms.ChoiceField(
            required=False,
            choices=(
                ("", "—"),
                ("not_null_default", "NOT NULL WITH DEFAULT (valor por defecto)"),
                ("not_null", "NOT NULL (no permite nulos)"),
            ),
            widget=forms.Select(
                attrs={"class": _INPUT + " max-w-md cursor-pointer", "data-attr-input": "1"}
            ),
        )
        self.fields["check_constraint_sql"] = forms.CharField(
            required=False,
            widget=forms.Textarea(
                attrs={
                    "class": _TEXTAREA + " font-mono text-xs min-h-[4.5rem]",
                    "rows": 3,
                    "placeholder": "STATUS IN ('A','I','P')",
                    "data-attr-input": "1",
                }
            ),
        )
        self.fields["generated_expression"] = forms.CharField(
            required=False,
            widget=forms.Textarea(
                attrs={
                    "class": _TEXTAREA + " font-mono text-xs min-h-[4.5rem]",
                    "rows": 3,
                    "data-attr-input": "1",
                    "placeholder": "TABLE_NAME_SHORT CONCAT '-' CONCAT TABLE_NAME_LONG",
                }
            ),
        )
        self.fields["fieldproc_program"] = forms.CharField(
            required=False,
            max_length=128,
            widget=forms.TextInput(
                attrs={
                    "class": _INPUT,
                    "placeholder": "CODASLIB/ENCRIPTAR_DOC",
                    "data-attr-input": "1",
                }
            ),
        )
        self.fields["compress_mode"] = forms.ChoiceField(
            required=False,
            choices=(
                ("", "—"),
                *DetailTableDb2Attributes.CompressMode.choices,
            ),
            widget=forms.Select(
                attrs={"class": _INPUT + " max-w-md cursor-pointer", "data-attr-input": "1"}
            ),
        )
        self.fields["mask_function"] = forms.CharField(
            required=False,
            max_length=64,
            label="is_masked",
            widget=forms.TextInput(
                attrs={"class": _INPUT, "placeholder": "EMAIL", "data-attr-input": "1"}
            ),
        )
        self.fields["user_defined_field"] = forms.CharField(
            required=False,
            max_length=255,
            widget=forms.Textarea(
                attrs={
                    "class": _TEXTAREA,
                    "rows": 3,
                    "placeholder": "Definición creada por el usuario",
                    "data-attr-input": "1",
                }
            ),
        )

        if attrs_instance is not None:
            self._apply_instance_initial(attrs_instance)

    def _apply_instance_initial(self, attrs: DetailTableDb2Attributes) -> None:
        if attrs.ccsid is not None:
            self.fields["ccsid"].initial = attrs.ccsid
        if attrs.default_sql_expression:
            self.fields["default_sql_expression"].initial = attrs.default_sql_expression
        if attrs.nullable:
            self.fields["nullable_mode"].initial = "null"
        else:
            if attrs.default_sql_expression or attrs.default_value:
                self.fields["nullable_mode"].initial = "not_null_default"
            else:
                self.fields["nullable_mode"].initial = "not_null"
        if attrs.check_constraint_sql:
            self.fields["check_constraint_sql"].initial = attrs.check_constraint_sql
        if attrs.generated_expression:
            self.fields["generated_expression"].initial = attrs.generated_expression
        if attrs.fieldproc_program:
            self.fields["fieldproc_program"].initial = attrs.fieldproc_program
        if attrs.compress_mode != DetailTableDb2Attributes.CompressMode.NONE:
            self.fields["compress_mode"].initial = attrs.compress_mode
        if attrs.mask_function:
            self.fields["mask_function"].initial = attrs.mask_function
        if attrs.user_defined_field:
            self.fields["user_defined_field"].initial = attrs.user_defined_field

    def selected_field_keys(self) -> set[str]:
        keys: set[str] = set()
        for row in DB2_ATTRIBUTE_UI_ROWS:
            if self.cleaned_data.get(_sel_name(row.field_key)):
                keys.add(row.field_key)
        return keys

    def user_defined_only(self) -> bool:
        return "user_defined_field" in self.selected_field_keys()

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        selected = self.selected_field_keys()
        if not selected:
            return cleaned

        if self.user_defined_only():
            udf = (cleaned.get("user_defined_field") or "").strip()
            if not udf:
                self.add_error(
                    "user_defined_field",
                    "Indique la definición cuando active «user_defined_field».",
                )
            return cleaned

        field_type = self.detail.field_type

        if "ccsid" in selected:
            ccsid = cleaned.get("ccsid")
            if ccsid is None:
                self.add_error("ccsid", "Indique CCSID cuando active este atributo.")
            elif field_type not in CCSID_FIELD_TYPES:
                self.add_error(
                    "ccsid",
                    f"CCSID no aplica al tipo {field_type}.",
                )

        if "default_sql_expression" in selected:
            expr = (cleaned.get("default_sql_expression") or "").strip()
            if not expr:
                self.add_error(
                    "default_sql_expression",
                    "Indique la expresión DEFAULT SQL.",
                )

        if "nullable" in selected:
            if not cleaned.get("nullable_mode"):
                self.add_error("nullable_mode", "Seleccione el modo nullable.")

        if "check_constraint_sql" in selected:
            chk = (cleaned.get("check_constraint_sql") or "").strip()
            if not chk:
                self.add_error(
                    "check_constraint_sql",
                    "Indique la expresión CHECK.",
                )

        if "generated_expression" in selected:
            gen = (cleaned.get("generated_expression") or "").strip()
            if not gen:
                self.add_error(
                    "generated_expression",
                    "Indique la expresión GENERATED ALWAYS AS.",
                )

        if "fieldproc_program" in selected:
            fp = (cleaned.get("fieldproc_program") or "").strip()
            if not fp:
                self.add_error(
                    "fieldproc_program",
                    "Indique el programa FIELDPROC calificado.",
                )

        if "compress_mode" in selected:
            mode = cleaned.get("compress_mode") or ""
            if not mode:
                self.add_error("compress_mode", "Seleccione el modo de compresión.")

        if "mask_function" in selected:
            mask = (cleaned.get("mask_function") or "").strip()
            if not mask:
                self.add_error(
                    "mask_function",
                    "Indique la función MASKED WITH.",
                )

        return cleaned


def _row_selected(attrs: DetailTableDb2Attributes, row) -> bool:
    key = row.field_key
    if key == "ccsid":
        return attrs.ccsid is not None
    if key == "is_hidden":
        return attrs.is_hidden
    if key == "default_sql_expression":
        return bool(attrs.default_sql_expression)
    if key == "nullable":
        return not attrs.nullable or bool(attrs.default_sql_expression or attrs.default_value)
    if key == "is_unique":
        return attrs.is_unique
    if key == "check_constraint_sql":
        return bool(attrs.check_constraint_sql.strip())
    if key == "generated_expression":
        return bool(attrs.generated_expression.strip())
    if key == "fieldproc_program":
        return bool(attrs.fieldproc_program)
    if key == "for_bit_data":
        return attrs.for_bit_data
    if key == "compress_mode":
        return attrs.compress_mode != DetailTableDb2Attributes.CompressMode.NONE
    if key == "mask_function":
        return bool(attrs.mask_function)
    if key == "user_defined_field":
        return bool(attrs.user_defined_field)
    return False


def build_db2_attributes_form_context(
    form: DetailTableDb2AttributesForm,
) -> dict[str, object]:
    """Contexto de plantilla: filas enlazadas al formulario."""
    table_rows: list[dict[str, object]] = []
    for row in DB2_ATTRIBUTE_UI_ROWS:
        key = row.field_key
        errs: list[str] = []
        sel_err = form.errors.get(_sel_name(key))
        if sel_err:
            errs.extend(sel_err)
        input_field = None
        if row.input_kind == "si":
            if key == "nullable":
                input_field = form["nullable_mode"]
                if form.errors.get("nullable_mode"):
                    errs.extend(form.errors["nullable_mode"])
            else:
                input_field = form[key]
                if key in form.errors:
                    errs.extend(form.errors[key])
        table_rows.append(
            {
                "meta": row,
                "selector": form[_sel_name(key)],
                "input_field": input_field,
                "errors": errs,
            }
        )
    return {
        "db2_form": form,
        "db2_table_rows": table_rows,
    }
