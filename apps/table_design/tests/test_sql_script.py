"""Generación de script DDL (`services.sql_script`) y vista `header_script`.

Regla DDL (may/2026): el tipo sale de ``DetailTable.field_type``; NULL/NOT NULL,
CCSID, DEFAULT, IDENTITY e IMPLICITLY HIDDEN solo si existe fila en
``DetailTableDb2Attributes`` (paso 2). Ver ``create_detail_field`` vs
``create_detail_field_core_only`` en ``factories.py``.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from apps.company.models import Company
from apps.table_design.models import DetailTable, HeaderTable, HeaderTableAutoKeyConfig
from apps.table_design.tests.factories import (
    create_detail_field,
    create_detail_field_core_only,
)
from apps.table_design.services.sql_script import (
    build_simple_sql_script,
    script_line_length_violations,
)
from apps.userprofile.models import UserProfile

User = get_user_model()


def _user_with_company(company: Company) -> User:
    user = User.objects.create_user(username="sqlscr_user", password="test-pw-123")
    UserProfile.objects.create(
        user=user,
        company=company,
        user_type=UserProfile.UserType.USER,
        status=UserProfile.Status.ACTIVE,
    )
    return user


class BuildSimpleSqlScriptTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="C1", name_long="Co One")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="CUSTOMER_MASTER_FILE",
            table_name_short="CUSMAST01",
            schema="LIBDATA",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            is_field_key=True,
            pk_constraint_name="PK_CUSMAST01",
            record_format_name="CUSMAST0R",
            script_generated=False,
        )
        HeaderTableAutoKeyConfig.objects.create(
            header=self.header,
            identity_start=1,
            identity_increment=1,
            identity_cache=20,
            identity_cycle=False,
        )
        create_detail_field(
            self.header,
            1,
            field_name_long="CUSTOMER_IDENTIFIER",
            field_name_short="CUSTID",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            nullable=False,
            is_key=True,
            order_key=1,
            status=DetailTable.Status.ACTIVE,
        )
        create_detail_field(
            self.header,
            2,
            field_name_long="CUSTOMER_NAME_FIELD",
            field_name_short="CUSTNAME",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=50,
            allocate_length=40,
            column_label="Nombre del cliente",
            status=DetailTable.Status.ACTIVE,
        )

    def test_ok_contains_create_pk_rcdfmt(self) -> None:
        ok, sql, errs = build_simple_sql_script(self.header)
        self.assertTrue(ok, errs)
        self.assertFalse(errs)
        self.assertIn("CREATE OR REPLACE TABLE LIBDATA.CUSTOMER_MASTER_FILE", sql)
        self.assertIn("FOR SYSTEM NAME CUSMAST01", sql)
        self.assertIn("PRIMARY KEY (CUSTID)", sql)
        self.assertIn("CONSTRAINT PK_CUSMAST01", sql)
        self.assertIn("RCDFMT CUSMAST0R;", sql)
        self.assertIn("INTEGER NOT NULL", sql)
        self.assertIn("VARCHAR(50) ALLOCATE(40) NULL", sql)
        # §9.11.6 G: LABEL/COMMENT con librería/nombre corto (estilo prototipo básica)
        self.assertIn("LABEL ON TABLE LIBDATA/CUSMAST01 IS", sql)

    def test_column_without_db2_attributes_emits_type_only(self) -> None:
        """Solo DetailTable (paso 1): tipo desde FieldDB2Type, sin NULL/CCSID/DEFAULT."""
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TYPE_ONLY_TABLE",
            table_name_short="TYPONLY01",
            schema="LIBTYPE",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        create_detail_field_core_only(
            h,
            1,
            field_name_long="CAMPO2",
            field_name_short="CAMPO2",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            status=DetailTable.Status.ACTIVE,
        )
        ok, sql, errs = build_simple_sql_script(h)
        self.assertTrue(ok, errs)
        self.assertIn("CAMPO2 FOR COLUMN CAMPO2", sql)
        self.assertIn("        INTEGER", sql)
        self.assertNotIn("INTEGER NULL", sql)
        self.assertNotIn("INTEGER NOT NULL", sql)

    def test_mixed_core_only_and_db2_attributes_on_same_table(self) -> None:
        """Mezcla paso 1 + paso 2: nullability solo en columnas con fila de atributos."""
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="MIXED_ATTRS_TABLE",
            table_name_short="MIXATTR01",
            schema="LIBMIX",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        create_detail_field_core_only(
            h,
            1,
            field_name_long="CORE_ONLY_INT",
            field_name_short="COREINT01",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            status=DetailTable.Status.ACTIVE,
        )
        create_detail_field(
            h,
            2,
            field_name_long="WITH_ATTRS_CHAR",
            field_name_short="WITHCHR01",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=5,
            nullable=False,
            status=DetailTable.Status.ACTIVE,
        )
        ok, sql, errs = build_simple_sql_script(h)
        self.assertTrue(ok, errs)
        self.assertIn("CORE_ONLY_INT FOR COLUMN COREINT01", sql)
        self.assertNotIn("INTEGER NOT NULL", sql)
        self.assertNotIn("INTEGER NULL", sql)
        self.assertIn("CHAR(5) NOT NULL", sql)

    def test_defaults_not_emitted_without_db2_attributes(self) -> None:
        """default_value/default_sql_expression en DetailTable no emiten DEFAULT sin paso 2."""
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="NO_DEFAULTS_TABLE",
            table_name_short="NODFLT001",
            schema="LIBND",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        create_detail_field_core_only(
            h,
            1,
            field_name_long="AMOUNT_VALUE",
            field_name_short="AMOUNT001",
            field_type=DetailTable.FieldDB2Type.DECIMAL,
            field_length=15,
            decimal_places=2,
            status=DetailTable.Status.ACTIVE,
        )
        ok, sql, errs = build_simple_sql_script(h)
        self.assertTrue(ok, errs)
        self.assertIn("DECIMAL(15, 2)", sql)
        self.assertNotIn("DEFAULT", sql)

    def test_emit_default_null_requires_db2_attributes(self) -> None:
        """emit_default_null_for_nullable no aplica si no hay fila DetailTableDb2Attributes."""
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="NO_ATTRS_NULL_FLAG",
            table_name_short="NOATRNULL",
            schema="LIBNA",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        create_detail_field_core_only(
            h,
            1,
            field_name_long="OPTIONAL_TEXT",
            field_name_short="OPTTEXT1",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=10,
            status=DetailTable.Status.ACTIVE,
        )
        ok, sql, errs = build_simple_sql_script(
            h, emit_default_null_for_nullable=True
        )
        self.assertTrue(ok, errs)
        self.assertIn("CHAR(10)", sql)
        self.assertNotIn("NULL", sql)
        self.assertNotIn("DEFAULT NULL", sql)

    def test_s10_no_line_exceeds_78_chars(self) -> None:
        ok, sql, errs = build_simple_sql_script(self.header)
        self.assertTrue(ok, errs)
        viol = script_line_length_violations(sql)
        self.assertEqual(
            viol,
            [],
            msg=f"Líneas > 78: {viol!r}\n---\n{sql}",
        )

    def test_identity_hidden_varchar_like_ifs_rutas(self) -> None:
        """Caso cercano a INSUMO_RUTAS_IFS: IDENTITY en líneas propias, sin superar 78 cols."""
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="INSUMO_RUTAS_IFS",
            table_name_short="CTRTBIFS00",
            schema="CTRLIBRA",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            is_field_key=False,
            record_format_name="AMGIFS00",
        )
        HeaderTableAutoKeyConfig.objects.create(
            header=h,
            identity_start=1,
            identity_increment=1,
            identity_cache=None,
            identity_cycle=False,
        )
        create_detail_field(
            h,
            1,
            field_name_long="ID_RUTA_IFS",
            field_name_short="IDRUTAIFS",
            field_type=DetailTable.FieldDB2Type.BIGINT,
            field_length=8,
            nullable=False,
            is_identity=True,
            is_hidden=True,
            column_label="X" * 60,
            column_text="Y" * 70,
            status=DetailTable.Status.ACTIVE,
        )
        create_detail_field(
            h,
            2,
            field_name_long="VALOR_RUTA_ISF",
            field_name_short="VRUTAIFSAL",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=300,
            allocate_length=270,
            nullable=False,
            status=DetailTable.Status.ACTIVE,
        )
        ok, sql, errs = build_simple_sql_script(h)
        self.assertTrue(ok, errs)
        self.assertEqual(script_line_length_violations(sql), [])
        self.assertIn("GENERATED ALWAYS AS IDENTITY", sql)
        self.assertIn("(START WITH 1 INCREMENT BY 1", sql)
        self.assertIn("NO MINVALUE NO MAXVALUE", sql)
        self.assertIn("IMPLICITLY HIDDEN", sql)
        self.assertIn("VARCHAR(300) ALLOCATE(270)", sql)
        self.assertIn("LABEL ON COLUMN CTRLIBRA/CTRTBIFS00 (", sql)

    def test_labels_are_grouped_in_single_statement_per_kind(self) -> None:
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="INSUMO_RUTAS_IFS",
            table_name_short="CTRTBIFS00",
            schema="CTRLIBRA",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        create_detail_field(
            h,
            1,
            field_name_long="ID_RUTA_IFS",
            field_name_short="IDRUTAIFS",
            field_type=DetailTable.FieldDB2Type.BIGINT,
            field_length=8,
            nullable=False,
            column_label="Identificador",
            column_text="Identificador interno incremental",
            status=DetailTable.Status.ACTIVE,
        )
        create_detail_field(
            h,
            2,
            field_name_long="VALOR_RUTA_IFS",
            field_name_short="VRUTAIFS",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=300,
            allocate_length=270,
            nullable=False,
            column_label="Ruta IFS",
            column_text="Ruta IFS de destino",
            status=DetailTable.Status.ACTIVE,
        )
        ok, sql, errs = build_simple_sql_script(h)
        self.assertTrue(ok, errs)
        self.assertEqual(sql.count("LABEL ON COLUMN CTRLIBRA/CTRTBIFS00 ("), 2)
        self.assertIn("    ID_RUTA_IFS                     IS 'Identificador',", sql)
        self.assertIn("    VALOR_RUTA_IFS                  IS 'Ruta IFS'", sql)
        self.assertIn(
            "    ID_RUTA_IFS                     TEXT IS 'Identificador interno inc'",
            sql,
        )
        self.assertIn("CONCAT 'remental',", sql)
        self.assertIn("    VALOR_RUTA_IFS                  TEXT IS 'Ruta IFS de destino'", sql)

    def test_advanced_model_rejected(self) -> None:
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.ADVANCED,
            table_name_long="ADV_TABLE_LONG_NAME",
            table_name_short="ADVTAB123",
            schema="LIBX",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        ok, sql, errs = build_simple_sql_script(h)
        self.assertFalse(ok)
        self.assertEqual(sql, "")
        self.assertTrue(any("Simple" in e for e in errs))

    def test_default_literals_by_type_numeric_unquoted_and_text_quoted(self) -> None:
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="DEFAULTS_MIXED_TABLE",
            table_name_short="DFLTMIX01",
            schema="LIBDEF",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        create_detail_field(
            h,
            1,
            field_name_long="AMOUNT_VALUE",
            field_name_short="AMOUNT001",
            field_type=DetailTable.FieldDB2Type.DECIMAL,
            field_length=15,
            decimal_places=2,
            nullable=False,
            default_value="10.25",
            status=DetailTable.Status.ACTIVE,
        )
        create_detail_field(
            h,
            2,
            field_name_long="STATUS_TEXT",
            field_name_short="STATUSTX1",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=1,
            nullable=False,
            default_value="A",
            status=DetailTable.Status.ACTIVE,
        )
        create_detail_field(
            h,
            3,
            field_name_long="CREATED_AT_TS",
            field_name_short="CRTATTS01",
            field_type=DetailTable.FieldDB2Type.TIMESTAMP,
            field_length=26,
            nullable=False,
            default_sql_expression="CURRENT_TIMESTAMP",
            status=DetailTable.Status.ACTIVE,
        )

        ok, sql, errs = build_simple_sql_script(h)
        self.assertTrue(ok, errs)
        self.assertIn("DECIMAL(15, 2) NOT NULL DEFAULT 10.25", sql)
        self.assertIn("CHAR(1) NOT NULL DEFAULT 'A'", sql)
        self.assertIn("TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP", sql)

    def test_emit_set_current_schema_prefix(self) -> None:
        ok, sql, errs = build_simple_sql_script(
            self.header, emit_set_current_schema=True
        )
        self.assertTrue(ok, errs)
        self.assertTrue(sql.startswith("SET CURRENT SCHEMA LIBDATA;"))

    def test_qualification_style_dot_and_slash(self) -> None:
        ok_dot, sql_dot, errs_dot = build_simple_sql_script(
            self.header, qualification_style="dot"
        )
        self.assertTrue(ok_dot, errs_dot)
        self.assertIn("CREATE OR REPLACE TABLE LIBDATA.CUSTOMER_MASTER_FILE", sql_dot)
        self.assertIn("LABEL ON TABLE LIBDATA.CUSMAST01 IS", sql_dot)
        self.assertIn("COMMENT ON TABLE LIBDATA.CUSMAST01 IS", sql_dot)

        ok_slash, sql_slash, errs_slash = build_simple_sql_script(
            self.header, qualification_style="slash"
        )
        self.assertTrue(ok_slash, errs_slash)
        self.assertIn(
            "CREATE OR REPLACE TABLE LIBDATA/CUSTOMER_MASTER_FILE", sql_slash
        )
        self.assertIn("LABEL ON TABLE LIBDATA/CUSMAST01 IS", sql_slash)
        self.assertIn("COMMENT ON TABLE LIBDATA/CUSMAST01 IS", sql_slash)

    def test_emit_default_null_for_nullable(self) -> None:
        """Con fila Db2Attributes y nullable=True; bandera agrega DEFAULT NULL explícito."""
        h = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="NULL_DEFAULT_TABLE",
            table_name_short="NULLDFLT1",
            schema="LIBNULL",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        create_detail_field(
            h,
            1,
            field_name_long="OPTIONAL_TEXT",
            field_name_short="OPTTEXT1",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=10,
            nullable=True,
            status=DetailTable.Status.ACTIVE,
        )
        ok_off, sql_off, errs_off = build_simple_sql_script(
            h, emit_default_null_for_nullable=False
        )
        self.assertTrue(ok_off, errs_off)
        self.assertNotIn("DEFAULT NULL", sql_off)

        ok_on, sql_on, errs_on = build_simple_sql_script(
            h, emit_default_null_for_nullable=True
        )
        self.assertTrue(ok_on, errs_on)
        self.assertIn("CHAR(10) NULL DEFAULT NULL", sql_on)


class HeaderScriptViewTests(TestCase):
    def setUp(self) -> None:
        self.c1 = Company.objects.create(name_short="C1", name_long="Company One")
        self.c2 = Company.objects.create(name_short="C2", name_long="Company Two")
        self.user = _user_with_company(self.c1)
        self.header = HeaderTable.objects.create(
            company=self.c1,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="VIEW_SCRIPT_LONG",
            table_name_short="VWSCRPT01",
            schema="LIBC1",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            script_generated=False,
        )
        create_detail_field(
            self.header,
            1,
            field_name_long="ONLYFIELDNM",
            field_name_short="ONLYFLD01",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=10,
            nullable=True,
            status=DetailTable.Status.ACTIVE,
        )
        self.header_other = HeaderTable.objects.create(
            company=self.c2,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="OTHER_LONG_NAME",
            table_name_short="OTHERTAB1",
            schema="LIBC2",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_script_404_other_company(self) -> None:
        url = reverse(
            "table_design:header_script", kwargs={"header_pk": self.header_other.pk}
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

    def test_script_get_200(self) -> None:
        url = reverse(
            "table_design:header_script", kwargs={"header_pk": self.header.pk}
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "CREATE OR REPLACE TABLE")

    def test_script_post_marks_generated(self) -> None:
        url = reverse(
            "table_design:header_script", kwargs={"header_pk": self.header.pk}
        )
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.header.refresh_from_db()
        self.assertTrue(self.header.script_generated)
        self.assertIsNotNone(self.header.script_date)

    def test_script_get_applies_format_options(self) -> None:
        url = reverse(
            "table_design:header_script", kwargs={"header_pk": self.header.pk}
        )
        r = self.client.get(
            url,
            {
                "qualification_style": "dot",
                "emit_set_current_schema": "1",
                "emit_default_null_for_nullable": "1",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "SET CURRENT SCHEMA LIBC1;")
        self.assertContains(r, "LABEL ON TABLE LIBC1.VWSCRPT01")
        self.assertContains(r, "DEFAULT NULL")

    def test_script_format_options_ignore_default_null_without_db2_attrs(self) -> None:
        h = HeaderTable.objects.create(
            company=self.c1,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="VIEW_NO_ATTRS_LONG",
            table_name_short="VWNOATR01",
            schema="LIBC1",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            script_generated=False,
        )
        create_detail_field_core_only(
            h,
            1,
            field_name_long="ONLYFIELDNM",
            field_name_short="ONLYFLD01",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=10,
            status=DetailTable.Status.ACTIVE,
        )
        url = reverse("table_design:header_script", kwargs={"header_pk": h.pk})
        r = self.client.get(
            url,
            {
                "emit_default_null_for_nullable": "1",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "CHAR(10)")
        self.assertNotContains(r, "DEFAULT NULL")
        self.assertNotContains(r, "CHAR(10) NULL")

    def test_script_invalid_qualification_style_falls_back_to_mixed(self) -> None:
        url = reverse(
            "table_design:header_script", kwargs={"header_pk": self.header.pk}
        )
        r = self.client.get(url, {"qualification_style": "invalid-style"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "LABEL ON TABLE LIBC1/VWSCRPT01")
        msgs = [m.message for m in get_messages(r.wsgi_request)]
        self.assertTrue(any("qualification_style inválido" in m for m in msgs), msgs)
