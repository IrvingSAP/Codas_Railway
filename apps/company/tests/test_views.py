"""Pruebas de vistas y formularios de compañías (piloto OperationResult)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.company.forms import CompanyForm
from apps.company.models import Company
from apps.company.services.company_messages import (
    MSG_COMPANY_CREATED,
    MSG_COMPANY_DELETED,
    MSG_COMPANY_UPDATED,
    MSG_NAME_SHORT_DUPLICATE_FIELD,
)
from apps.core.services.operation_messages import MSG_FORM_INVALID, MSG_DUPLICATE
from apps.table_design.models import HeaderTable
from apps.userprofile.models import UserProfile

User = get_user_model()


def _valid_company_post(
    *,
    name_short: str = "TESTCO",
    name_long: str = "Compañía de prueba",
) -> dict[str, str]:
    return {
        "name_short": name_short,
        "name_long": name_long,
        "tax_id": "",
        "address": "",
        "phone": "",
        "email": "",
        "is_active": "on",
    }


class CompanyFormTests(TestCase):
    def test_create_without_sql_max_in_post_uses_default(self) -> None:
        data = {
            "name_short": "NEWCO01",
            "name_long": "Nueva compañía prueba",
            "tax_id": "",
            "address": "Local",
            "phone": "300",
            "email": "nueva@test.com",
            "is_active": "on",
        }
        form = CompanyForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        company = form.save()
        self.assertEqual(company.sql_max_line_length, 78)


class CompanySuperuserMixin:
    """Cliente autenticado como SU (mantenimiento completo de compañías)."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="su_company",
            password="test-pass-123",
        )
        UserProfile.objects.create(
            user=self.user,
            user_type=UserProfile.UserType.SUPERUSER,
            status=UserProfile.Status.ACTIVE,
        )
        self.client = Client()
        self.client.force_login(self.user)


class CompanyCreateViewTests(CompanySuperuserMixin, TestCase):
    def test_create_redirects_on_success(self) -> None:
        response = self.client.post(
            "/panel/companies/nueva/",
            _valid_company_post(name_short="VIEWCO01", name_long="Compañía desde vista"),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Company.objects.filter(name_short="VIEWCO01").exists())

    def test_create_success_message_on_detail(self) -> None:
        response = self.client.post(
            "/panel/companies/nueva/",
            _valid_company_post(name_short="MSGOK01"),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MSG_COMPANY_CREATED)

    def test_create_duplicate_name_short_stays_on_form(self) -> None:
        Company.objects.create(name_short="DUPVIEW", name_long="Original")
        response = self.client.post(
            "/panel/companies/nueva/",
            _valid_company_post(name_short="DUPVIEW", name_long="Duplicado vista"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MSG_NAME_SHORT_DUPLICATE_FIELD)
        self.assertContains(response, MSG_DUPLICATE)
        self.assertEqual(Company.objects.filter(name_short="DUPVIEW").count(), 1)

    def test_create_invalid_form_shows_catalog_message(self) -> None:
        response = self.client.post(
            "/panel/companies/nueva/",
            {"name_short": "", "name_long": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MSG_FORM_INVALID)

    def test_create_invalid_email_shows_form_error(self) -> None:
        response = self.client.post(
            "/panel/companies/nueva/",
            {**_valid_company_post(name_short="BADMAIL"), "email": "no-es-correo"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MSG_FORM_INVALID)
        self.assertFalse(Company.objects.filter(name_short="BADMAIL").exists())


class CompanyUpdateViewTests(CompanySuperuserMixin, TestCase):
    def test_update_redirects_on_success(self) -> None:
        company = Company.objects.create(name_short="UPDV01", name_long="Antes")
        response = self.client.post(
            f"/panel/companies/{company.pk}/editar/",
            _valid_company_post(name_short="UPDV01", name_long="Después"),
        )
        self.assertEqual(response.status_code, 302)
        company.refresh_from_db()
        self.assertEqual(company.name_long, "Después")

    def test_update_success_message_on_detail(self) -> None:
        company = Company.objects.create(name_short="UPDV02", name_long="Viejo")
        response = self.client.post(
            f"/panel/companies/{company.pk}/editar/",
            _valid_company_post(name_short="UPDV02", name_long="Nuevo"),
            follow=True,
        )
        self.assertContains(response, MSG_COMPANY_UPDATED)

    def test_update_duplicate_name_short_stays_on_form(self) -> None:
        Company.objects.create(name_short="TAKEN1", name_long="Primera")
        company = Company.objects.create(name_short="MINE01", name_long="Segunda")
        response = self.client.post(
            f"/panel/companies/{company.pk}/editar/",
            _valid_company_post(name_short="TAKEN1", name_long="Segunda"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MSG_NAME_SHORT_DUPLICATE_FIELD)
        company.refresh_from_db()
        self.assertEqual(company.name_short, "MINE01")


class CompanyDeleteViewTests(CompanySuperuserMixin, TestCase):
    def test_delete_redirects_to_list_on_success(self) -> None:
        company = Company.objects.create(name_short="DELV01", name_long="Borrar")
        pk = company.pk
        response = self.client.post(f"/panel/companies/{pk}/eliminar/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("company:list"))
        self.assertFalse(Company.objects.filter(pk=pk).exists())

    def test_delete_success_message_on_list(self) -> None:
        company = Company.objects.create(name_short="DELV02", name_long="Borrar dos")
        response = self.client.post(
            f"/panel/companies/{company.pk}/eliminar/",
            follow=True,
        )
        self.assertContains(response, MSG_COMPANY_DELETED)

    def test_delete_blocked_when_header_exists(self) -> None:
        company = Company.objects.create(name_short="DELBLK", name_long="Con cabecera")
        HeaderTable.objects.create(
            company=company,
            schema="LIBDEL",
            table_name_short="HD01",
            table_name_long="Cabecera bloqueo",
        )
        response = self.client.post(
            f"/panel/companies/{company.pk}/eliminar/",
            follow=True,
        )
        self.assertTrue(Company.objects.filter(pk=company.pk).exists())
        self.assertContains(response, "cabecera")

    def test_delete_free_company_without_headers(self) -> None:
        """Compañía sin diseños: borrado permitido (contraste con cabeceras)."""
        company = Company.objects.create(name_short="DELFREE", name_long="Sin FK")
        response = self.client.post(f"/panel/companies/{company.pk}/eliminar/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Company.objects.filter(pk=company.pk).exists())


class CompanyAccessViewTests(TestCase):
    def test_admin_company_cannot_create(self) -> None:
        user = User.objects.create_user(username="ac_company", password="test-pass-123")
        UserProfile.objects.create(
            user=user,
            user_type=UserProfile.UserType.ADMIN_COMPANY,
            status=UserProfile.Status.ACTIVE,
        )
        client = Client()
        client.force_login(user)
        response = client.post(
            "/panel/companies/nueva/",
            _valid_company_post(name_short="ACDENY"),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Company.objects.filter(name_short="ACDENY").exists())
