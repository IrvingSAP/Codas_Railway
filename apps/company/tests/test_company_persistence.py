"""Persistencia de Company vía OperationResult."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.company.models import Company
from apps.company.services.company_messages import (
    MSG_COMPANY_CREATED,
    MSG_COMPANY_DELETED,
    MSG_COMPANY_UPDATED,
    MSG_NAME_SHORT_DUPLICATE_FIELD,
)
from apps.company.services.company_persistence import (
    create_company,
    delete_company,
    delete_company_if_allowed,
    get_company_for_user,
    update_company,
)
from apps.core.services.operation_messages import ErrorCode, MSG_PROTECTED_DELETE
from apps.table_design.models import HeaderTable
from apps.userprofile.models import UserProfile

User = get_user_model()


class CompanyPersistenceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="su_persist",
            password="test-pass-123",
        )
        UserProfile.objects.create(
            user=self.user,
            user_type=UserProfile.UserType.SUPERUSER,
            status=UserProfile.Status.ACTIVE,
        )

    def test_create_company_success(self) -> None:
        company = Company(
            name_short="PERS01",
            name_long="Persistencia prueba",
            is_active=True,
        )
        result = create_company(company, user=self.user)
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, MSG_COMPANY_CREATED)
        self.assertEqual(result.data.name_short, "PERS01")
        self.assertEqual(result.data.created_by, self.user)
        self.assertTrue(Company.objects.filter(name_short="PERS01").exists())

    def test_create_company_duplicate(self) -> None:
        Company.objects.create(name_short="DUP01", name_long="Original")
        duplicate = Company(name_short="DUP01", name_long="Otro")
        result = create_company(duplicate, user=self.user)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.DUPLICATE)
        self.assertEqual(
            result.field_errors,
            {"name_short": [MSG_NAME_SHORT_DUPLICATE_FIELD]},
        )
        self.assertEqual(Company.objects.filter(name_short="DUP01").count(), 1)

    def test_update_company_success(self) -> None:
        company = Company.objects.create(name_short="UPD01", name_long="Antes")
        company.name_long = "Después"
        result = update_company(company, user=self.user)
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, MSG_COMPANY_UPDATED)
        company.refresh_from_db()
        self.assertEqual(company.name_long, "Después")
        self.assertEqual(company.updated_by, self.user)

    def test_update_company_duplicate_name_short(self) -> None:
        Company.objects.create(name_short="A001", name_long="A")
        other = Company.objects.create(name_short="B001", name_long="B")
        other.name_short = "A001"
        result = update_company(other, user=self.user)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.DUPLICATE)
        self.assertIn("name_short", result.field_errors or {})

    def test_delete_company_success(self) -> None:
        company = Company.objects.create(name_short="DEL01", name_long="Borrar")
        pk = company.pk
        result = delete_company(company)
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, MSG_COMPANY_DELETED)
        self.assertEqual(result.data, pk)
        self.assertFalse(Company.objects.filter(pk=pk).exists())

    def test_delete_company_protected(self) -> None:
        company = Company.objects.create(name_short="PROT01", name_long="Protegida")
        HeaderTable.objects.create(
            company=company,
            schema="LIBTEST",
            table_name_short="T01",
            table_name_long="Tabla prueba",
        )
        result = delete_company(company)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.PROTECTED_DELETE)
        self.assertEqual(result.error_message, MSG_PROTECTED_DELETE)
        self.assertTrue(Company.objects.filter(pk=company.pk).exists())

    def test_delete_company_if_allowed_blocked(self) -> None:
        company = Company.objects.create(name_short="BLK01", name_long="Bloqueada")
        HeaderTable.objects.create(
            company=company,
            schema="LIBBLK",
            table_name_short="T02",
            table_name_long="Tabla bloqueo",
        )
        result = delete_company_if_allowed(company)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.BUSINESS_BLOCKED)
        self.assertIn("cabecera", result.error_message.lower())
        self.assertTrue(Company.objects.filter(pk=company.pk).exists())

    def test_get_company_for_user_success(self) -> None:
        company = Company.objects.create(name_short="GET01", name_long="Leer")
        result = get_company_for_user(company.pk, user=self.user)
        self.assertTrue(result.ok)
        self.assertEqual(result.data.pk, company.pk)

    def test_get_company_for_user_not_found(self) -> None:
        result = get_company_for_user(99999, user=self.user)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.NOT_FOUND)
