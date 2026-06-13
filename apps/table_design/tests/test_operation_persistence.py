"""Persistencia table_design vía OperationResult."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.company.models import Company
from apps.core.services.operation_messages import ErrorCode
from apps.table_design.models import DetailTable, HeaderTable
from apps.table_design.services.field_persistence import (
    create_detail_field,
    delete_detail_field,
    update_detail_field,
)
from apps.table_design.services.header_persistence import (
    create_header_table,
    update_header_table,
)
from apps.table_design.services.table_design_messages import MSG_HEADER_DUPLICATE
from apps.table_design.tests.factories import create_detail_field as factory_field

User = get_user_model()


class HeaderPersistenceTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="TD", name_long="Table Design Co")
        self.user = User.objects.create_user(username="td_persist", password="x")

    def test_create_header_success(self) -> None:
        header = HeaderTable(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="PERSIST_LONG_NAME",
            table_name_short="PERS01",
            schema="LIBTD",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.PROCESS,
            created_by=self.user,
            updated_by=self.user,
        )
        result = create_header_table(header, cleaned_data={}, user=self.user)
        self.assertTrue(result.ok)
        self.assertTrue(HeaderTable.objects.filter(table_name_short="PERS01").exists())

    def test_update_resets_script_when_changed(self) -> None:
        header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="SCRIPT_LONG_NAME",
            table_name_short="SCR001",
            schema="LIBTD",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            script_generated=True,
            script_date="2026-01-01",
        )
        candidate = HeaderTable.objects.get(pk=header.pk)
        candidate.notes = "Cambio tras script"
        result = update_header_table(
            candidate,
            cleaned_data={},
            user=self.user,
            had_script_generated=True,
        )
        self.assertTrue(result.ok)
        header.refresh_from_db()
        self.assertFalse(header.script_generated)
        self.assertIsNone(header.script_date)

    def test_create_duplicate_returns_field_errors(self) -> None:
        HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="DUP_LONG_NAME",
            table_name_short="DUP001",
            schema="LIBTD",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        duplicate = HeaderTable(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="OTHER_LONG_NAME",
            table_name_short="DUP001",
            schema="LIBTD",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.PROCESS,
            created_by=self.user,
            updated_by=self.user,
        )
        result = create_header_table(duplicate, cleaned_data={}, user=self.user)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.DUPLICATE)
        self.assertIn("__all__", result.field_errors or {})


class FieldPersistenceTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="TD2", name_long="TD Co 2")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="FIELD_LONG_NAME",
            table_name_short="FLD001",
            schema="LIBTD",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )

    def test_create_and_delete_field(self) -> None:
        field = DetailTable(
            header=self.header,
            field_name_long="COL_ONE",
            field_name_short="COLONE01",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            notes="Nota de prueba.",
            order_reg=1,
            status=DetailTable.Status.ACTIVE,
        )
        create_result = create_detail_field(field, header=self.header)
        self.assertTrue(create_result.ok)
        pk = create_result.data.pk
        delete_result = delete_detail_field(create_result.data, header=self.header)
        self.assertTrue(delete_result.ok)
        self.assertFalse(DetailTable.objects.filter(pk=pk).exists())

    def test_update_field(self) -> None:
        field = factory_field(
            self.header,
            1,
            field_name_long="UPD_COL",
            field_name_short="UPDCOL01",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=10,
            notes="Antes",
        )
        field.notes = "Después"
        result = update_detail_field(field, header=self.header)
        self.assertTrue(result.ok)
        field.refresh_from_db()
        self.assertEqual(field.notes, "Después")
