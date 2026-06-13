"""Tests SP Asistido (validación ADD y fragmentos SQL)."""

from types import SimpleNamespace
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.company.models import Company
from apps.sp_asistido.models import SPAssignment, SPCondition, SPDefinition
from apps.sp_asistido.services.add_validation import (
    validate_not_null_with_null_origin,
    validate_source_detail_rule,
    validate_step1_identification,
)
from apps.sp_asistido.services.dlt_validation import (
    definition_has_where_clause,
    validate_where_row,
)
from apps.sp_asistido.services.generate_delete_script import build_delete_procedure_sql
from apps.sp_asistido.services.generate_update_script import build_update_procedure_sql
from apps.sp_asistido.services.generate_insert_script import build_insert_procedure_sql
from apps.sp_asistido.services.generate_read_script import (
    READ_PROJECTION_MARKER,
    build_read_procedure_sql,
)
from apps.sp_asistido.services.upd_validation import validate_upd_set_column_ids
from apps.table_design.models import DetailTable, HeaderTable
from apps.userprofile.models import UserProfile
from apps.sp_asistido.services.sql_qualification import sp_qualified_table_dml
from apps.sp_asistido.services.wizard_session import (
    WIZARD_SESSION_TTL_HOURS,
    load_wizard_session,
)


class AddStep1ValidationTests(SimpleTestCase):
    def test_schema_required(self):
        errs = validate_step1_identification("", "AB", "Nombre largo de prueba", "")
        self.assertTrue(any("esquema" in e.lower() for e in errs))

    def test_ok_minimal(self):
        errs = validate_step1_identification("R1DATA", "INSCUS00", "Alta cliente", "")
        self.assertEqual(errs, [])


class AddStep1DuplicateValidationTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name_short="C1", name_long="Compania Uno")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TABLA_PRUEBA_01",
            table_name_short="TABPRB0001",
            schema="LIBC1",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        SPDefinition.objects.create(
            company=self.company,
            header_table=self.header,
            operation=SPDefinition.Operation.ADD,
            schema_name="LIBC1",
            procedure_name_short="SPTEST001",
            procedure_name_long="SP prueba duplicado",
            procedure_comment="",
        )

    def test_duplicate_short_name_in_company(self):
        errs = validate_step1_identification(
            "LIBC1",
            "SPTEST001",
            "Otro nombre largo",
            "",
            company_id=self.company.id,
        )
        self.assertTrue(any("nombre corto" in e.lower() for e in errs), errs)

    def test_duplicate_long_name_in_company(self):
        errs = validate_step1_identification(
            "LIBC1",
            "OTROSP001",
            "SP prueba duplicado",
            "",
            company_id=self.company.id,
        )
        self.assertTrue(any("nombre largo" in e.lower() for e in errs), errs)


class AddSourceRulesTests(SimpleTestCase):
    def test_null_must_have_empty_detail(self):
        self.assertIsNotNone(validate_source_detail_rule(SPAssignment.SourceKind.NULL, "x"))

    def test_in_requires_detail(self):
        self.assertIsNotNone(
            validate_source_detail_rule(SPAssignment.SourceKind.IN_PARAM, "  ")
        )
        self.assertIsNone(
            validate_source_detail_rule(SPAssignment.SourceKind.IN_PARAM, "P_X")
        )


class UpdSetValidationTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name_short="C2", name_long="Compania Dos")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TABLA_UPD_VAL",
            table_name_short="TABUPDVAL1",
            schema="LIBC2",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        self.key_field = DetailTable.objects.create(
            header=self.header,
            field_name_short="IDKEY",
            field_name_long="ID_KEY",
            order_reg=1,
            field_type=DetailTable.FieldDB2Type.INTEGER,
            is_key=True,
            order_key=1,
            status=DetailTable.Status.ACTIVE,
        )
        self.non_key_field = DetailTable.objects.create(
            header=self.header,
            field_name_short="DESC01",
            field_name_long="DESC_01",
            order_reg=2,
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=50,
            is_key=False,
            status=DetailTable.Status.ACTIVE,
        )

    def test_rejects_key_fields_for_update_set(self):
        ids, errors = validate_upd_set_column_ids(
            [self.key_field.id, self.non_key_field.id],
            header_id=self.header.id,
            company_id=self.company.id,
        )
        self.assertEqual(ids, [self.non_key_field.id])
        self.assertTrue(any("campos clave" in e.lower() for e in errors), errors)


class AddNotNullTests(SimpleTestCase):
    def test_not_null_rejects_null_origin(self):
        col = SimpleNamespace(id=1, field_name_short="NM", nullable=False)
        errs = validate_not_null_with_null_origin(
            {1: col},
            [(1, SPAssignment.SourceKind.NULL, "")],
        )
        self.assertTrue(errs)


class GenerateInsertSqlTests(SimpleTestCase):
    def test_contains_codas_outs_and_insert(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUST")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="INSCUS00",
            procedure_name_long="Alta",
            header_table=header,
        )
        detail = SimpleNamespace(
            field_name_short="CUSNAME",
            field_type="VARCHAR",
            field_length=40,
            decimal_places=None,
        )
        sql = build_insert_procedure_sql(
            definition,
            [(detail, SPAssignment.SourceKind.IN_PARAM, "P_CUSNAME")],
            generated_by=None,
        )
        self.assertIn("P_ERROR_CODE", sql)
        self.assertIn("P_ERROR_MSG", sql)
        self.assertIn("23505", sql)
        self.assertIn("INSERT INTO R1DATA.CUST", sql)
        self.assertIn("IN P_CUSNAME VARCHAR(40)", sql)


class _MockWhereQS:
    def __init__(self, exists_val: bool):
        self._exists = exists_val

    def filter(self, **kwargs):
        return self

    def exists(self):
        return self._exists


class DefinitionHasWhereTests(SimpleTestCase):
    def test_false_when_no_where_rows(self):
        definition = SimpleNamespace(conditions=_MockWhereQS(False))
        self.assertFalse(definition_has_where_clause(definition))

    def test_true_when_where_rows(self):
        definition = SimpleNamespace(conditions=_MockWhereQS(True))
        self.assertTrue(definition_has_where_clause(definition))


class DltWhereValidationTests(SimpleTestCase):
    def test_missing_detail_field(self):
        errs = validate_where_row(None, "=", "IN", "P_X", header_id=1)
        self.assertTrue(any("campo" in e.lower() for e in errs))


class GenerateDeleteSqlTests(SimpleTestCase):
    def test_physical_delete_contains_where_outs_diagnostics(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUST")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="DLTCUS00",
            procedure_name_long="Baja cliente",
            header_table=header,
        )
        detail = SimpleNamespace(
            field_name_short="CUSID",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        wc = SimpleNamespace(
            detail_field=detail,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_CUSID",
        )
        sql = build_delete_procedure_sql(
            definition,
            [wc],
            mode_physical=True,
            logical_status_detail=None,
            logical_value_raw="",
            generated_by=None,
        )
        self.assertIn("DELETE FROM R1DATA.CUST", sql)
        self.assertIn("WHERE CUSID = P_CUSID", sql)
        self.assertIn("P_ERROR_CODE", sql)
        self.assertIn("P_ERROR_MSG", sql)
        self.assertIn("23505", sql)
        self.assertIn("GET DIAGNOSTICS", sql)
        self.assertIn("IN P_CUSID INTEGER", sql)

    def test_logical_update_contains_set_and_where(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUST")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="DLTCUS01",
            procedure_name_long="Baja lógica",
            header_table=header,
        )
        detail_where = SimpleNamespace(
            field_name_short="CUSID",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        wc = SimpleNamespace(
            detail_field=detail_where,
            operator="=",
            value_origin=SPCondition.ValueOrigin.LITERAL,
            value_text="42",
        )
        logical_col = SimpleNamespace(
            field_name_short="CUSSTAT",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=1,
            decimal_places=None,
        )
        sql = build_delete_procedure_sql(
            definition,
            [wc],
            mode_physical=False,
            logical_status_detail=logical_col,
            logical_value_raw="I",
            generated_by=None,
        )
        self.assertIn("UPDATE R1DATA.CUST", sql)
        self.assertIn("SET CUSSTAT =", sql)
        self.assertIn("WHERE CUSID = 42", sql)

    def test_two_where_predicates_and_in_signature(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUST")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="DLTCUS02",
            procedure_name_long="Baja",
            header_table=header,
        )
        d1 = SimpleNamespace(
            field_name_short="CUSID",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        d2 = SimpleNamespace(
            field_name_short="STATUS",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=1,
            decimal_places=None,
        )
        w1 = SimpleNamespace(
            detail_field=d1,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_CUSID",
            ordinal=0,
        )
        w2 = SimpleNamespace(
            detail_field=d2,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_STATUS",
            ordinal=1,
        )
        sql = build_delete_procedure_sql(
            definition,
            [w1, w2],
            mode_physical=True,
            logical_status_detail=None,
            logical_value_raw="",
            generated_by=None,
        )
        self.assertIn("WHERE CUSID = P_CUSID AND STATUS = P_STATUS", sql)
        self.assertIn("IN P_CUSID INTEGER", sql)
        self.assertIn("IN P_STATUS CHAR(1)", sql)


class GenerateUpdateSqlTests(SimpleTestCase):
    def test_update_none_mode_contains_set_where_outs(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUST")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="UPDCUS00",
            procedure_name_long="Cambio cliente",
            header_table=header,
        )
        col_nm = SimpleNamespace(
            field_name_short="CUSNAME",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=40,
            decimal_places=None,
        )
        detail_where = SimpleNamespace(
            field_name_short="CUSID",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        wc = SimpleNamespace(
            detail_field=detail_where,
            operator="=",
            value_origin="IN",
            value_text="P_CUSID",
        )
        tuples = [
            (col_nm, SPAssignment.SourceKind.IN_PARAM, "P_CUSNAME"),
        ]
        sql = build_update_procedure_sql(
            definition,
            tuples,
            [wc],
            concurrency_mode="none",
            generated_by=None,
        )
        self.assertIn("UPDATE R1DATA.CUST", sql)
        self.assertIn("SET", sql)
        self.assertIn("CUSNAME = P_CUSNAME", sql)
        self.assertIn("WHERE CUSID = P_CUSID", sql)
        self.assertIn("P_ERROR_CODE", sql)
        self.assertIn("P_ERROR_MSG", sql)
        self.assertIn("23505", sql)
        self.assertIn("GET DIAGNOSTICS", sql)

    def test_update_exactly_one_wraps_count(self):
        header = SimpleNamespace(schema="X", table_name_short="T")
        definition = SimpleNamespace(
            schema_name="X",
            procedure_name_short="UPDT01",
            procedure_name_long="Upd",
            header_table=header,
        )
        col = SimpleNamespace(
            field_name_short="A",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        wcol = SimpleNamespace(
            field_name_short="K",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        wc = SimpleNamespace(
            detail_field=wcol,
            operator="=",
            value_origin="LITERAL",
            value_text="1",
        )
        sql = build_update_procedure_sql(
            definition,
            [(col, SPAssignment.SourceKind.LITERAL, "2")],
            [wc],
            concurrency_mode="exactly_one",
            generated_by=None,
        )
        self.assertIn("IF (SELECT COUNT(*) FROM X.T WHERE K = 1) <> 1 THEN", sql)
        self.assertIn("UPDATE X.T", sql)

    def test_update_two_where_predicates_and(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="T1")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="UPDT02",
            procedure_name_long="Upd2",
            header_table=header,
        )
        a = SimpleNamespace(
            field_name_short="A",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        b = SimpleNamespace(
            field_name_short="B",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=1,
            decimal_places=None,
        )
        c1 = SimpleNamespace(
            detail_field=a,
            operator="=",
            value_origin="LITERAL",
            value_text="1",
        )
        c2 = SimpleNamespace(
            detail_field=b,
            operator="=",
            value_origin="LITERAL",
            value_text="X",
        )
        col = SimpleNamespace(
            field_name_short="C",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        sql = build_update_procedure_sql(
            definition,
            [(col, SPAssignment.SourceKind.LITERAL, "0")],
            [c1, c2],
            concurrency_mode="none",
            generated_by=None,
        )
        self.assertIn("WHERE A = 1 AND B = 'X'", sql.replace("\n", " ").replace("  ", " "))


class GenerateReadSqlTests(SimpleTestCase):
    def test_read_has_cursor_dynamic_result_sets_where_in_and_fetch(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUST")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="readcus",
            procedure_name_long="Lectura clientes",
            header_table=header,
        )
        d_proj = SimpleNamespace(
            id=1,
            order_reg=1,
            field_name_short="CUSNAME",
        )
        d_where = SimpleNamespace(
            id=2,
            field_name_short="CUSID",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        a = SimpleNamespace(
            source_kind=SPAssignment.SourceKind.LITERAL,
            source_value=READ_PROJECTION_MARKER,
            detail_field_id=1,
            detail_field=d_proj,
        )
        wc = SimpleNamespace(
            detail_field=d_where,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_CUSID",
            id=1,
            ordinal=0,
        )
        fetch = SimpleNamespace(value_text="25", detail_field_id=None)
        sql = build_read_procedure_sql(
            definition, [a], [wc], None, fetch, generated_by=None
        )
        self.assertNotIn("ORDER BY", sql)
        self.assertIn("DYNAMIC RESULT SETS 1", sql)
        self.assertIn("CURSOR WITH RETURN", sql)
        self.assertIn("READS SQL DATA", sql)
        self.assertIn("OUT P_ERROR_CODE", sql)
        self.assertIn("IN P_CUSID INTEGER", sql)
        self.assertIn("SELECT CUSNAME", sql)
        self.assertIn("FROM R1DATA.CUST", sql)
        self.assertIn("WHERE CUSID = P_CUSID", sql)
        self.assertIn("FETCH FIRST 25 ROWS ONLY", sql)

    def test_read_order_by_and_two_predicates(self):
        header = SimpleNamespace(schema="X", table_name_short="T")
        definition = SimpleNamespace(
            schema_name="X",
            procedure_name_short="R1",
            procedure_name_long="R",
            header_table=header,
        )
        f_nm = SimpleNamespace(
            id=1,
            order_reg=1,
            field_name_short="NM",
        )
        a = SimpleNamespace(
            source_kind=SPAssignment.SourceKind.LITERAL,
            source_value=READ_PROJECTION_MARKER,
            detail_field_id=1,
            detail_field=f_nm,
        )
        d1 = SimpleNamespace(
            id=1,
            field_name_short="K1",
            field_type=DetailTable.FieldDB2Type.CHAR,
            field_length=1,
            decimal_places=None,
        )
        w1 = SimpleNamespace(
            detail_field=d1,
            operator="=",
            value_origin=SPCondition.ValueOrigin.LITERAL,
            value_text="A",
            id=1,
            ordinal=0,
        )
        d2 = SimpleNamespace(
            id=2,
            field_name_short="K2",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        w2 = SimpleNamespace(
            detail_field=d2,
            operator="=",
            value_origin=SPCondition.ValueOrigin.LITERAL,
            value_text="1",
            id=2,
            ordinal=1,
        )
        o = SimpleNamespace(
            detail_field_id=1,
            operator="DESC",
            detail_field=f_nm,
            id=1,
            ordinal=0,
        )
        fetch = SimpleNamespace(value_text="5", detail_field_id=None)
        sql = build_read_procedure_sql(
            definition, [a], [w1, w2], [o], fetch, generated_by=None
        )
        self.assertIn("WHERE K1 = 'A' AND K2 = 1", sql.replace("\n", " "))
        self.assertIn("ORDER BY NM DESC", sql.replace("\n", " "))
        self.assertIn("FETCH FIRST 5 ROWS ONLY", sql.replace("\n", " "))

    def test_read_multicolumn_order_and_unlimited_omits_fetch(self):
        header = SimpleNamespace(schema="X", table_name_short="T2")
        definition = SimpleNamespace(
            schema_name="X",
            procedure_name_short="R2",
            procedure_name_long="R2",
            header_table=header,
        )
        c1 = SimpleNamespace(
            id=1, order_reg=1, field_name_short="A"
        )
        c2 = SimpleNamespace(
            id=2, order_reg=2, field_name_short="B"
        )
        a1 = SimpleNamespace(
            source_kind=SPAssignment.SourceKind.LITERAL,
            source_value=READ_PROJECTION_MARKER,
            detail_field_id=1,
            detail_field=c1,
        )
        a2 = SimpleNamespace(
            source_kind=SPAssignment.SourceKind.LITERAL,
            source_value=READ_PROJECTION_MARKER,
            detail_field_id=2,
            detail_field=c2,
        )
        dw = SimpleNamespace(
            id=9, field_name_short="Z", field_type=DetailTable.FieldDB2Type.INTEGER, field_length=None, decimal_places=None
        )
        wc = SimpleNamespace(
            detail_field=dw,
            operator="=",
            value_origin=SPCondition.ValueOrigin.LITERAL,
            value_text="1",
            id=0,
            ordinal=0,
        )
        oa = SimpleNamespace(
            detail_field_id=1,
            operator="ASC",
            detail_field=c1,
            id=1,
            ordinal=0,
        )
        ob = SimpleNamespace(
            detail_field_id=2,
            operator="DESC",
            detail_field=c2,
            id=2,
            ordinal=1,
        )
        fetch = SimpleNamespace(value_text="", detail_field_id=None)
        sql = build_read_procedure_sql(
            definition,
            [a1, a2],
            [wc],
            [ob, oa],
            fetch,
            generated_by=None,
        )
        self.assertIn("ORDER BY A ASC, B DESC", sql.replace("\n", " "))
        self.assertNotIn("FETCH FIRST", sql)

    def test_read_row_mode_uses_select_into_out_without_cursor(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUST")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="READONE",
            procedure_name_long="Lectura única",
            header_table=header,
            read_mode="R",
        )
        d_proj = SimpleNamespace(
            id=1,
            order_reg=1,
            field_name_short="CUSNAME",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=40,
            decimal_places=None,
        )
        d_where = SimpleNamespace(
            id=2,
            field_name_short="CUSID",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        a = SimpleNamespace(
            source_kind=SPAssignment.SourceKind.LITERAL,
            source_value=READ_PROJECTION_MARKER,
            detail_field_id=1,
            detail_field=d_proj,
        )
        wc = SimpleNamespace(
            detail_field=d_where,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_CUSID",
            id=1,
            ordinal=0,
        )
        sql = build_read_procedure_sql(
            definition, [a], [wc], None, None, generated_by=None
        )
        self.assertIn("OUT O_CUSNAME VARCHAR(40)", sql)
        self.assertIn("SELECT CUSNAME", sql)
        self.assertIn("INTO O_CUSNAME", sql)
        self.assertIn("SQLSTATE '21000'", sql)
        self.assertNotIn("DYNAMIC RESULT SETS", sql)
        self.assertNotIn("CURSOR WITH RETURN", sql)

    def test_read_row_mode_first_policy_fetches_first_row(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUST")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="READONE",
            procedure_name_long="Lectura única",
            header_table=header,
            read_mode="R",
            read_row_policy="F",
        )
        d_proj = SimpleNamespace(
            id=1,
            order_reg=1,
            field_name_short="CUSNAME",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=40,
            decimal_places=None,
        )
        d_where = SimpleNamespace(
            id=2,
            field_name_short="CUSID",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        a = SimpleNamespace(
            source_kind=SPAssignment.SourceKind.LITERAL,
            source_value=READ_PROJECTION_MARKER,
            detail_field_id=1,
            detail_field=d_proj,
        )
        wc = SimpleNamespace(
            detail_field=d_where,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_CUSID",
            id=1,
            ordinal=0,
        )
        sql = build_read_procedure_sql(
            definition, [a], [wc], None, None, generated_by=None
        )
        self.assertIn("FETCH FIRST 1 ROW ONLY", sql)
        self.assertNotIn("SQLSTATE '21000'", sql)


class SqlQualificationTests(SimpleTestCase):
    def test_dml_table_dot(self):
        self.assertEqual(
            sp_qualified_table_dml("libc1", "TAB01", style="dot"),
            "LIBC1.TAB01",
        )

    def test_dml_table_slash(self):
        self.assertEqual(
            sp_qualified_table_dml("libc1", "TAB01", style="slash"),
            "LIBC1/TAB01",
        )

    def test_mixed_uses_dot_for_dml(self):
        self.assertEqual(
            sp_qualified_table_dml("R1X", "X", style="mixed"),
            "R1X.X",
        )

    def test_empty_schema_returns_table_only(self):
        self.assertEqual(sp_qualified_table_dml("", "TBL", style="dot"), "TBL")


class SqlMaxLineLengthTests(SimpleTestCase):
    def _assert_max_sql_line_length(self, sql: str, max_len: int = 78):
        for line in sql.splitlines():
            self.assertLessEqual(len(line), max_len, msg=f"Línea > {max_len}: {line}")

    def test_insert_sql_respects_max_line_length(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUSTOMERS_TABLE")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="INSCUS00",
            procedure_name_long="INS_CUSTOMERS_LONG_NAME",
            header_table=header,
        )
        detail = SimpleNamespace(
            field_name_short="CUSTOMER_FULL_NAME",
            field_type="VARCHAR",
            field_length=40,
            decimal_places=None,
        )
        sql = build_insert_procedure_sql(
            definition,
            [(detail, SPAssignment.SourceKind.IN_PARAM, "P_CUSTOMER_FULL_NAME")],
            generated_by=None,
        )
        self._assert_max_sql_line_length(sql)

    def test_delete_sql_respects_max_line_length(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUSTOMERS_TABLE")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="DLTCUS00",
            procedure_name_long="DLT_CUSTOMERS_LONG_NAME",
            header_table=header,
        )
        detail = SimpleNamespace(
            field_name_short="CUSTOMER_IDENTIFIER",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        wc = SimpleNamespace(
            detail_field=detail,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_CUSTOMER_IDENTIFIER",
            ordinal=0,
            id=1,
        )
        sql = build_delete_procedure_sql(
            definition,
            [wc],
            mode_physical=True,
            logical_status_detail=None,
            logical_value_raw="",
            generated_by=None,
        )
        self._assert_max_sql_line_length(sql)

    def test_update_sql_respects_max_line_length(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUSTOMERS_TABLE")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="UPDCUS00",
            procedure_name_long="UPD_CUSTOMERS_LONG_NAME",
            header_table=header,
        )
        set_detail = SimpleNamespace(
            field_name_short="CUSTOMER_FULL_NAME",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=40,
            decimal_places=None,
        )
        where_detail = SimpleNamespace(
            field_name_short="CUSTOMER_IDENTIFIER",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        wc = SimpleNamespace(
            detail_field=where_detail,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_CUSTOMER_IDENTIFIER",
            ordinal=0,
            id=1,
        )
        sql = build_update_procedure_sql(
            definition,
            [(set_detail, SPAssignment.SourceKind.IN_PARAM, "P_CUSTOMER_FULL_NAME")],
            [wc],
            concurrency_mode="none",
            generated_by=None,
        )
        self._assert_max_sql_line_length(sql)

    def test_read_sql_respects_max_line_length(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUSTOMERS_TABLE")
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="READCUS0",
            procedure_name_long="READ_CUSTOMERS_LONG_NAME",
            header_table=header,
        )
        projection_detail = SimpleNamespace(
            id=1,
            order_reg=1,
            field_name_short="CUSTOMER_FULL_NAME",
            field_type=DetailTable.FieldDB2Type.VARCHAR,
            field_length=40,
            decimal_places=None,
        )
        where_detail = SimpleNamespace(
            id=2,
            order_reg=2,
            field_name_short="CUSTOMER_IDENTIFIER",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=None,
            decimal_places=None,
        )
        assignment = SimpleNamespace(
            source_kind=SPAssignment.SourceKind.LITERAL,
            source_value=READ_PROJECTION_MARKER,
            detail_field_id=1,
            detail_field=projection_detail,
        )
        where_condition = SimpleNamespace(
            detail_field=where_detail,
            detail_field_id=2,
            operator="=",
            value_origin=SPCondition.ValueOrigin.IN_PARAM,
            value_text="P_CUSTOMER_IDENTIFIER",
            ordinal=0,
            id=1,
        )
        order_condition = SimpleNamespace(
            detail_field=projection_detail,
            detail_field_id=1,
            operator="DESC",
            value_origin=SPCondition.ValueOrigin.LITERAL,
            value_text="",
            ordinal=0,
            id=1,
        )
        fetch_condition = SimpleNamespace(value_text="25", detail_field_id=None)
        sql = build_read_procedure_sql(
            definition,
            [assignment],
            [where_condition],
            [order_condition],
            fetch_condition,
            generated_by=None,
        )
        self._assert_max_sql_line_length(sql)

    def test_insert_sql_uses_company_configurable_limit(self):
        header = SimpleNamespace(schema="R1DATA", table_name_short="CUSTOMERS_TABLE")
        company = SimpleNamespace(sql_max_line_length=60)
        definition = SimpleNamespace(
            schema_name="R1DATA",
            procedure_name_short="INSCUS00",
            procedure_name_long="INS_CUSTOMERS_LONG_NAME",
            header_table=header,
            company=company,
        )
        detail = SimpleNamespace(
            field_name_short="CUSTOMER_FULL_NAME",
            field_type="VARCHAR",
            field_length=40,
            decimal_places=None,
        )
        sql = build_insert_procedure_sql(
            definition,
            [(detail, SPAssignment.SourceKind.IN_PARAM, "P_CUSTOMER_FULL_NAME")],
            generated_by=None,
        )
        self._assert_max_sql_line_length(sql, max_len=60)


class SpAsistidoSecurityTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.company_a = Company.objects.create(
            name_short="CA",
            name_long="Compania A",
        )
        self.company_b = Company.objects.create(
            name_short="CB",
            name_long="Compania B",
        )
        self.header_a = HeaderTable.objects.create(
            company=self.company_a,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TABLA_A",
            table_name_short="TABA000001",
            schema="LIBA",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        self.header_b = HeaderTable.objects.create(
            company=self.company_b,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TABLA_B",
            table_name_short="TABB000001",
            schema="LIBB",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        self.user_a = self.user_model.objects.create_user(
            username="usr_a",
            password="x1234567",
        )
        self.user_b = self.user_model.objects.create_user(
            username="usr_b",
            password="x1234567",
        )
        UserProfile.objects.create(
            user=self.user_a,
            company=self.company_a,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )
        UserProfile.objects.create(
            user=self.user_b,
            company=self.company_b,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )
        self.definition_a = SPDefinition.objects.create(
            company=self.company_a,
            header_table=self.header_a,
            operation=SPDefinition.Operation.ADD,
            schema_name="LIBA",
            procedure_name_short="SPA000001",
            procedure_name_long="SP A",
            procedure_comment="",
            status=SPDefinition.Status.DRAFT,
        )

    def test_idor_definition_detail_returns_404_outside_company(self):
        self.client.force_login(self.user_b)
        response = self.client.get(
            reverse("sp_asistido:detail", kwargs={"pk": self.definition_a.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_idor_add_wizard_step_returns_404_outside_company(self):
        self.client.force_login(self.user_b)
        response = self.client.get(
            reverse(
                "sp_asistido:add_step",
                kwargs={"definition_id": self.definition_a.pk, "step": 3},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_reopen_requires_post(self):
        self.client.force_login(self.user_a)
        response = self.client.get(
            reverse("sp_asistido:reopen", kwargs={"pk": self.definition_a.pk})
        )
        self.assertEqual(response.status_code, 405)

    def test_reopen_post_is_scoped_by_company(self):
        self.client.force_login(self.user_b)
        response = self.client.post(
            reverse("sp_asistido:reopen", kwargs={"pk": self.definition_a.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_wizard_cancel_requires_post(self):
        self.client.force_login(self.user_a)
        response = self.client.get(
            reverse("sp_asistido:wizard_cancel", kwargs={"flow": "add"})
        )
        self.assertEqual(response.status_code, 405)

    def test_wizard_cancel_clears_step1_session(self):
        self.client.force_login(self.user_a)
        session = self.client.session
        session["sp_asistido_add_step1"] = {
            "saved_at": timezone.now().isoformat(),
            "data": {
                "schema_name": "LIBA",
                "procedure_name_short": "SPA000001",
                "procedure_name_long": "SP A",
                "procedure_comment": "",
            },
        }
        session.save()
        response = self.client.post(
            reverse("sp_asistido:wizard_cancel", kwargs={"flow": "add"})
        )
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertNotIn("sp_asistido_add_step1", session)


class WizardSessionTests(SimpleTestCase):
    def test_load_wizard_session_expires_and_clears(self):
        class _Session(dict):
            modified = False

        class _Req:
            def __init__(self):
                self.session = _Session()

        request = _Req()
        session_key = "sp_asistido_read_step1"
        old = timezone.now() - timedelta(hours=WIZARD_SESSION_TTL_HOURS + 1)
        request.session[session_key] = {
            "saved_at": old.isoformat(),
            "data": {"schema_name": "LIBA"},
        }
        payload, expired = load_wizard_session(request, session_key)
        self.assertIsNone(payload)
        self.assertTrue(expired)
        self.assertNotIn(session_key, request.session)
