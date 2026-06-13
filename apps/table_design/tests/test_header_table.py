"""Tests de validación y formularios de cabecera (`HeaderTable`)."""

from __future__ import annotations

from django.test import TestCase

from apps.company.models import Company
from apps.table_design.forms import HeaderTableCreateForm, HeaderTableUpdateForm
from apps.table_design.models import HeaderTable, HeaderTableAutoKeyConfig
from apps.table_design.services.auto_key_config import persist_auto_key_from_cleaned
from apps.table_design.services.validation import (
    validate_auto_key_config,
    validate_header_ddl_options,
    validate_header_duplicates,
    validate_header_table,
    validate_pk_constraint_name_unique,
)


def _valid_long() -> str:
    return "ABCDEFGHIJABCDEFGHIJ"  # 20 caracteres, patrón permitido


class ValidateHeaderTableTests(TestCase):
    def test_schema_required_empty_none(self) -> None:
        r = validate_header_table(
            table_name_long=_valid_long(),
            table_name_short="NAME12345",
            schema=None,
            notes=None,
        )
        self.assertFalse(r["ok"])
        self.assertIn("schema", r["field_errors"])

    def test_schema_required_empty_string(self) -> None:
        r = validate_header_table(
            table_name_long=_valid_long(),
            table_name_short="NAME12345",
            schema="",
            notes=None,
        )
        self.assertFalse(r["ok"])
        self.assertIn("schema", r["field_errors"])

    def test_schema_max_length(self) -> None:
        r = validate_header_table(
            table_name_long=_valid_long(),
            table_name_short="NAME12345",
            schema="12345678901",
            notes=None,
        )
        self.assertFalse(r["ok"])
        self.assertIn("schema", r["field_errors"])

    def test_ok_with_schema_and_short_with_digits(self) -> None:
        r = validate_header_table(
            table_name_long=_valid_long(),
            table_name_short="TAB123456",
            schema="LIBIACP",
            notes=None,
        )
        self.assertTrue(r["ok"])


class ValidateHeaderDdlTests(TestCase):
    def test_pk_constraint_invalid_char(self) -> None:
        r = validate_header_ddl_options(
            pk_constraint_name="bad-name",
            record_format_name=None,
        )
        self.assertFalse(r["ok"])
        self.assertIn("pk_constraint_name", r["field_errors"])

    def test_pk_constraint_normalized_upper(self) -> None:
        r = validate_header_ddl_options(
            pk_constraint_name="ct_pk_01",
            record_format_name=None,
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["normalized"]["pk_constraint_name"], "CT_PK_01")


class PersistAutoKeyFromCleanedTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="AK", name_long="Auto Key Co")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="AUTO_KEY_TABLE_LONG",
            table_name_short="AUTKEYTAB1",
            schema="LIBAK",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )

    def test_no_input_does_not_create_row(self) -> None:
        persist_auto_key_from_cleaned(
            self.header,
            {
                "identity_start": None,
                "identity_increment": None,
                "identity_cache": None,
                "identity_cycle": False,
            },
        )
        self.assertFalse(
            HeaderTableAutoKeyConfig.objects.filter(header=self.header).exists()
        )

    def test_input_creates_row(self) -> None:
        persist_auto_key_from_cleaned(
            self.header,
            {
                "identity_start": 1,
                "identity_increment": 2,
                "identity_cache": 10,
                "identity_cycle": True,
            },
        )
        config = HeaderTableAutoKeyConfig.objects.get(header=self.header)
        self.assertEqual(config.identity_start, 1)
        self.assertEqual(config.identity_increment, 2)
        self.assertTrue(config.identity_cycle)

    def test_unchanged_values_do_not_touch_row(self) -> None:
        HeaderTableAutoKeyConfig.objects.create(
            header=self.header,
            identity_start=5,
            identity_increment=1,
            identity_cache=None,
            identity_cycle=False,
        )
        config = persist_auto_key_from_cleaned(
            self.header,
            {
                "identity_start": 5,
                "identity_increment": 1,
                "identity_cache": None,
                "identity_cycle": False,
            },
        )
        self.assertEqual(HeaderTableAutoKeyConfig.objects.filter(header=self.header).count(), 1)
        self.assertEqual(config.identity_start, 5)

    def test_clearing_input_deletes_row(self) -> None:
        HeaderTableAutoKeyConfig.objects.create(
            header=self.header,
            identity_start=1,
            identity_increment=1,
        )
        persist_auto_key_from_cleaned(
            self.header,
            {
                "identity_start": None,
                "identity_increment": None,
                "identity_cache": None,
                "identity_cycle": False,
            },
        )
        self.assertFalse(
            HeaderTableAutoKeyConfig.objects.filter(header=self.header).exists()
        )


class ValidateAutoKeyConfigTests(TestCase):
    def test_identity_start_below_one(self) -> None:
        r = validate_auto_key_config(
            identity_start=0,
            identity_increment=None,
            identity_cache=None,
            identity_cycle=False,
        )
        self.assertFalse(r["ok"])
        self.assertIn("identity_start", r["field_errors"])

    def test_ok_with_values(self) -> None:
        r = validate_auto_key_config(
            identity_start=1,
            identity_increment=1,
            identity_cache=100,
            identity_cycle=True,
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["normalized"]["identity_start"], 1)
        self.assertTrue(r["normalized"]["identity_cycle"])


class ValidatePkConstraintUniqueTests(TestCase):
    def setUp(self) -> None:
        self.c1 = Company.objects.create(name_short="C1", name_long="Company One")
        self.c2 = Company.objects.create(name_short="C2", name_long="Company Two")
        self.pk_name = "UQ_PK_HDR_TEST01"
        HeaderTable.objects.create(
            company=self.c1,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="FIRST_TABLE_LONG_NAME",
            table_name_short="FIRSTTAB1",
            schema="LIBONE",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            pk_constraint_name=self.pk_name,
        )

    def test_duplicate_pk_constraint_fails(self) -> None:
        r = validate_pk_constraint_name_unique(
            pk_constraint_name=self.pk_name,
            exclude_header_pk=None,
        )
        self.assertFalse(r["ok"])
        self.assertIn("pk_constraint_name", r["field_errors"])

    def test_same_name_allowed_when_excluding_self(self) -> None:
        h2 = HeaderTable.objects.create(
            company=self.c2,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="SECOND_TABLE_LONG_NAME",
            table_name_short="SECONDTAB",
            schema="LIBTWO",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            pk_constraint_name="OTHER_PK_NAME",
        )
        r = validate_pk_constraint_name_unique(
            pk_constraint_name="OTHER_PK_NAME",
            exclude_header_pk=h2.pk,
        )
        self.assertTrue(r["ok"])


class HeaderTableCreateFormTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="TC", name_long="Test Co")

    def _base_post(self) -> dict[str, str]:
        return {
            "table_model": HeaderTable.TableModel.SIMPLE,
            "table_name_long": _valid_long(),
            "table_name_short": "NEWHDR01",
            "schema": "LIBPOST",
            "table_type": HeaderTable.TableKind.PHYSICAL,
            "status": HeaderTable.Status.ACTIVE,
            "pk_constraint_name": "",
            "record_format_name": "",
            "identity_start": "",
            "identity_increment": "",
            "identity_cache": "",
            "notes": "",
        }

    def test_rejects_empty_schema(self) -> None:
        data = self._base_post()
        data["schema"] = ""
        form = HeaderTableCreateForm(data, company_id=self.company.pk)
        self.assertFalse(form.is_valid())
        self.assertIn("schema", form.errors)

    def test_valid_minimal_ddl(self) -> None:
        data = self._base_post()
        form = HeaderTableCreateForm(data, company_id=self.company.pk)
        self.assertTrue(form.is_valid(), form.errors)
        inst = form.save(commit=False)
        self.assertEqual(inst.schema, "LIBPOST")
        self.assertIsNone(inst.pk_constraint_name)

    def test_empty_form_defaults_status_to_process(self) -> None:
        form = HeaderTableCreateForm(company_id=self.company.pk)
        self.assertEqual(
            form.fields["status"].initial,
            HeaderTable.Status.PROCESS,
        )


class HeaderTableUpdateFormTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="TU", name_long="Test Update")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="UPDATE_LONG_NAME",
            table_name_short="UPDTABL01",
            schema="LIBOLD",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )

    def test_update_schema_required(self) -> None:
        data = {
            "table_model": self.header.table_model,
            "table_name_long": self.header.table_name_long,
            "table_name_short": self.header.table_name_short,
            "schema": "",
            "table_type": self.header.table_type,
            "status": self.header.status,
            "pk_constraint_name": "",
            "record_format_name": "",
            "identity_start": "",
            "identity_increment": "",
            "identity_cache": "",
            "notes": "",
        }
        form = HeaderTableUpdateForm(
            data,
            instance=self.header,
            company_id=self.company.pk,
            can_edit_identity=True,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("schema", form.errors)

    def test_update_changes_schema(self) -> None:
        data = {
            "table_model": self.header.table_model,
            "table_name_long": self.header.table_name_long,
            "table_name_short": self.header.table_name_short,
            "schema": "LIBNEW",
            "table_type": self.header.table_type,
            "status": self.header.status,
            "pk_constraint_name": "",
            "record_format_name": "",
            "identity_start": "",
            "identity_increment": "",
            "identity_cache": "",
            "notes": "",
        }
        form = HeaderTableUpdateForm(
            data,
            instance=self.header,
            company_id=self.company.pk,
            can_edit_identity=True,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.schema, "LIBNEW")


class ValidateHeaderDuplicatesTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="D1", name_long="Dup Co")
        HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="DUP_LONG_NAME_ONE",
            table_name_short="DUPTABL01",
            schema="LIBDUP",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )

    def test_duplicate_short_name(self) -> None:
        r = validate_header_duplicates(
            self.company.pk,
            "OTHER_LONG_NAME_TWO",
            "DUPTABL01",
        )
        self.assertFalse(r["ok"])
        self.assertIn("table_name_short", r["field_errors"])
