"""Tests de servicios para campos (`DetailTable`)."""

from django.test import TestCase

from apps.company.models import Company
from apps.table_design.models import DetailTable, HeaderTable
from apps.table_design.tests.factories import create_detail_field
from apps.table_design.services.field_order import (
    get_next_order_reg,
    move_field_down,
    move_field_up,
    normalize_order_reg,
)
from apps.table_design.services.field_validation import (
    MAX_COLUMN_LABEL_LEN,
    MAX_COLUMN_TEXT_LEN,
    validate_field_duplicates,
    validate_field_payload,
    validate_order_key_among_key_fields,
)


def _valid_notes() -> str:
    return "Notas obligatorias del campo."


class FieldValidationTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="TC", name_long="Test Co")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TABLE_LONGNM",
            table_name_short="SHORTABCDE",
            schema="LIBTEST",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )

    def test_validate_varchar_ok(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="Identificador",
            name_short="CUSTOMRF1",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=36,
            decimal_places=None,
            allocate_length=30,
            nullable=False,
            is_key=True,
            order_key=1,
            notes=notes,
            exclude_field_id=None,
        )
        self.assertTrue(r["ok"], r["errors"])
        assert r["normalized"] is not None
        self.assertEqual(r["normalized"]["field_length"], 36)
        self.assertEqual(r["normalized"]["allocate_length"], 30)
        self.assertEqual(r["normalized"]["order_key"], 1)

    def test_validate_varchar_requires_allocate(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="CUSTOMER_IDENTIFIER",
            name_short="VARCHR001",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=100,
            decimal_places=None,
            allocate_length=None,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(any("ALLOCATE" in e for e in r["errors"]), r["errors"])

    def test_validate_allocate_cannot_exceed_length(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="CUSTOMER_IDENTIFIER",
            name_short="VARCHR002",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=100,
            decimal_places=None,
            allocate_length=150,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any("no puede ser mayor" in e.lower() for e in r["errors"]),
            r["errors"],
        )

    def test_validate_integer_rejects_allocate(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="MYINTFIELD1",
            name_short="INTFIELD01",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            decimal_places=None,
            allocate_length=1,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any("ALLOCATE solo aplica" in e for e in r["errors"]), r["errors"]
        )

    def test_validate_name_short_too_short(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="CUSTOMER_IDENTIFIER",
            name_short="SHORT",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=10,
            decimal_places=None,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any("entre 8 y 10" in e.lower() for e in r["errors"]), r["errors"]
        )

    def test_validate_name_long_too_short(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="SHORTLONG",
            name_short="FIELDNAME1",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=10,
            decimal_places=None,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any("entre 10 y 30" in e.lower() for e in r["errors"]), r["errors"]
        )

    def test_validate_name_short_no_underscore(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="CUSTOMER_IDENTIFIER",
            name_short="CUSTOM_RF1",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=10,
            decimal_places=None,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any("solo permite letras y números" in e.lower() for e in r["errors"]),
            r["errors"],
        )

    def test_validate_name_long_charset(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="CAMPO_INVALID@CHAR",
            name_short="FIELDNAME1",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=10,
            decimal_places=None,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any("nombre largo solo permite" in e.lower() for e in r["errors"]),
            r["errors"],
        )

    def test_validate_notes_required(self) -> None:
        r = validate_field_payload(
            header=self.header,
            name_long="CUSTOMER_IDENTIFIER",
            name_short="FIELDNAME1",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=10,
            decimal_places=None,
            nullable=True,
            is_key=False,
            order_key=None,
            notes="",
            exclude_field_id=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(any("notas" in e.lower() for e in r["errors"]), r["errors"])

    def test_validate_order_key_duplicate(self) -> None:
        create_detail_field(
            self.header,
            1,
            field_name_long="Col A",
            field_name_short="COLA",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            is_key=True,
            order_key=1,
            nullable=False,
            status=DetailTable.Status.ACTIVE,
        )
        r = validate_order_key_among_key_fields(
            self.header, 1, is_key=True, exclude_field_id=None
        )
        self.assertFalse(r["ok"])

    def test_validate_column_label_max_length(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="CUSTOMER_IDENTIFIER",
            name_short="FIELDNM01",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=30,
            decimal_places=None,
            allocate_length=20,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
            column_label="X" * (MAX_COLUMN_LABEL_LEN + 1),
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any(str(MAX_COLUMN_LABEL_LEN) in e for e in r["errors"]),
            r["errors"],
        )

    def test_validate_column_text_max_length(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="CUSTOMER_IDENTIFIER",
            name_short="FIELDNM02",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=30,
            decimal_places=None,
            allocate_length=20,
            nullable=True,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
            column_text="Y" * (MAX_COLUMN_TEXT_LEN + 1),
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any(str(MAX_COLUMN_TEXT_LEN) in e for e in r["errors"]),
            r["errors"],
        )

    def test_validate_numeric_default_literal_requires_numeric_value(self) -> None:
        notes = _valid_notes()
        r = validate_field_payload(
            header=self.header,
            name_long="AMOUNT_VALUE",
            name_short="AMOUNT001",
            field_type=DetailTable.FieldDB2Type.DECIMAL,
            field_length=15,
            decimal_places=2,
            allocate_length=None,
            nullable=False,
            is_key=False,
            order_key=None,
            notes=notes,
            exclude_field_id=None,
            default_value="ABC",
            default_sql_expression=None,
        )
        self.assertFalse(r["ok"])
        self.assertTrue(
            any("debe ser numérico" in e.lower() for e in r["errors"]),
            r["errors"],
        )


class FieldDuplicateTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="D3", name_long="Dup fields")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="DUPF_LONG_NM1",
            table_name_short="DUPFTAB000",
            schema="LIBD3",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        create_detail_field(
            self.header,
            1,
            field_name_long="ExistingLong",
            field_name_short="EXSTSH001",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            nullable=False,
            status=DetailTable.Status.ACTIVE,
        )

    def test_duplicate_name_long_iexact(self) -> None:
        r = validate_field_duplicates(
            self.header, "existinglong", "NEWSH0001", exclude_field_id=None
        )
        self.assertFalse(r["ok"])
        self.assertTrue(any("largo" in e.lower() for e in r["errors"]))

    def test_duplicate_name_short_iexact(self) -> None:
        r = validate_field_duplicates(
            self.header, "OtherLongerName1", "exstsh001", exclude_field_id=None
        )
        self.assertFalse(r["ok"])
        self.assertTrue(any("corto" in e.lower() for e in r["errors"]))

    def test_excluded_field_allows_same_names(self) -> None:
        f = self.header.fields.get(field_name_short="EXSTSH001")
        r = validate_field_duplicates(
            self.header, "ExistingLong", "EXSTSH001", exclude_field_id=f.pk
        )
        self.assertTrue(r["ok"])


class FieldOrderTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="T2", name_long="Test 2")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="OTHER_LONG",
            table_name_short="OTHERTABLE",
            schema="LIBTEST",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        self.a = create_detail_field(
            self.header,
            1,
            field_name_long="Primera",
            field_name_short="F001",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            nullable=False,
            status=DetailTable.Status.ACTIVE,
        )
        self.b = create_detail_field(
            self.header,
            2,
            field_name_long="Segunda",
            field_name_short="F002",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            nullable=False,
            status=DetailTable.Status.ACTIVE,
        )

    def test_get_next_order_reg(self) -> None:
        self.assertEqual(get_next_order_reg(self.header), 3)

    def test_move_field_up_down(self) -> None:
        self.assertTrue(move_field_up(self.header, self.b))
        self.a.refresh_from_db()
        self.b.refresh_from_db()
        self.assertEqual(self.a.order_reg, 2)
        self.assertEqual(self.b.order_reg, 1)
        self.assertTrue(move_field_down(self.header, self.b))
        self.a.refresh_from_db()
        self.b.refresh_from_db()
        self.assertEqual(self.a.order_reg, 1)
        self.assertEqual(self.b.order_reg, 2)

    def test_normalize_order_reg(self) -> None:
        self.b.order_reg = 5
        self.b.save(update_fields=["order_reg"])
        normalize_order_reg(self.header)
        self.a.refresh_from_db()
        self.b.refresh_from_db()
        self.assertEqual(self.a.order_reg, 1)
        self.assertEqual(self.b.order_reg, 2)
