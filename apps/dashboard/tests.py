"""Pruebas del panel por rol."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.company.models import Company
from apps.dashboard.services.admin_system_metrics import get_admin_system_dashboard_metrics
from apps.maintenance_builder.models import MaintenanceDefinition
from apps.sp_asistido.models import SPDefinition
from apps.table_design.models import HeaderTable
from apps.userprofile.models import UserProfile

User = get_user_model()


def _header(company: Company, short: str, status: str) -> HeaderTable:
    return HeaderTable.objects.create(
        company=company,
        schema="LIBTST",
        table_name_short=short,
        table_name_long=f"Tabla {short}",
        status=status,
    )


class AdminCompanyDashboardTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="ACCO", name_long="AC Co")
        self.ac_user = User.objects.create_user(username="ac_dash", password="x")
        UserProfile.objects.create(
            user=self.ac_user,
            company=self.company,
            user_type=UserProfile.UserType.ADMIN_COMPANY,
            status=UserProfile.Status.ACTIVE,
        )
        for idx, utype in enumerate(
            [
                UserProfile.UserType.USER,
                UserProfile.UserType.USER,
                UserProfile.UserType.ADMIN_SYSTEM,
            ],
            start=1,
        ):
            user = User.objects.create_user(username=f"member{idx}", password="x")
            UserProfile.objects.create(
                user=user,
                company=self.company,
                user_type=utype,
                status=UserProfile.Status.ACTIVE,
            )
        other_co = Company.objects.create(name_short="OTHR", name_long="Otra")
        other_user = User.objects.create_user(username="ext_us", password="x")
        UserProfile.objects.create(
            user=other_user,
            company=other_co,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )
        self.client = Client()
        self.client.force_login(self.ac_user)

    def test_home_shows_company_user_counts(self) -> None:
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_users"], 2)
        self.assertEqual(response.context["total_admin_system"], 1)
        self.assertContains(response, "2")
        self.assertContains(response, "Usuarios (tipo US)")


class AdminSystemMetricsTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="ASCO", name_long="AS Co")
        self.other = Company.objects.create(name_short="OTHR", name_long="Otra")

    def test_metrics_filtered_by_company(self) -> None:
        _header(self.company, "HTA", HeaderTable.Status.ACTIVE)
        _header(self.company, "HTP", HeaderTable.Status.PROCESS)
        _header(self.company, "HTI", HeaderTable.Status.INACTIVE)
        _header(self.other, "XHT", HeaderTable.Status.ACTIVE)

        header = _header(self.company, "SPB", HeaderTable.Status.ACTIVE)
        SPDefinition.objects.create(
            company=self.company,
            header_table=header,
            operation=SPDefinition.Operation.READ,
            schema_name="LIBTST",
            procedure_name_short="SPREAD",
            procedure_name_long="SP Read",
            status=SPDefinition.Status.ACTIVE,
        )
        SPDefinition.objects.create(
            company=self.company,
            header_table=header,
            operation=SPDefinition.Operation.ADD,
            schema_name="LIBTST",
            procedure_name_short="SPADD",
            procedure_name_long="SP Add",
            status=SPDefinition.Status.DRAFT,
        )

        MaintenanceDefinition.objects.create(
            company=self.company,
            header_table=header,
            name_short="MT01",
            name_long="Mant 1",
            status=MaintenanceDefinition.Status.GENERATED,
        )
        MaintenanceDefinition.objects.create(
            company=self.company,
            header_table=header,
            name_short="MT02",
            name_long="Mant 2",
            status=MaintenanceDefinition.Status.DRAFT,
        )

        user = User.objects.create_user(username="us_as", password="x")
        UserProfile.objects.create(
            user=user,
            company=self.company,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )
        ext = User.objects.create_user(username="us_ext", password="x")
        UserProfile.objects.create(
            user=ext,
            company=self.other,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )

        metrics = get_admin_system_dashboard_metrics(self.company.pk)
        self.assertEqual(metrics.header_tables.active, 2)
        self.assertEqual(metrics.header_tables.process, 1)
        self.assertEqual(metrics.header_tables.inactive, 1)
        self.assertEqual(metrics.stored_procedures.active, 1)
        self.assertEqual(metrics.stored_procedures.draft, 1)
        self.assertEqual(metrics.stored_procedures.inactive, 0)
        self.assertEqual(metrics.maintenance_definitions.active, 1)
        self.assertEqual(metrics.maintenance_definitions.draft, 1)
        self.assertEqual(metrics.total_users, 1)


class AdminSystemDashboardTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="ASD", name_long="AS Dash")
        self.as_user = User.objects.create_user(username="as_dash", password="x")
        UserProfile.objects.create(
            user=self.as_user,
            company=self.company,
            user_type=UserProfile.UserType.ADMIN_SYSTEM,
            status=UserProfile.Status.ACTIVE,
        )
        for idx in (1, 2):
            user = User.objects.create_user(username=f"as_us{idx}", password="x")
            UserProfile.objects.create(
                user=user,
                company=self.company,
                user_type=UserProfile.UserType.USER,
                status=UserProfile.Status.ACTIVE,
            )
        _header(self.company, "D01", HeaderTable.Status.PROCESS)
        self.client = Client()
        self.client.force_login(self.as_user)

    def test_home_uses_admin_system_template_and_metrics(self) -> None:
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/home_admin_system.html")
        self.assertEqual(response.context["metrics"].header_tables.process, 1)
        self.assertEqual(response.context["total_users"], 2)
        self.assertEqual(response.context["metrics"].total_users, 2)
        self.assertContains(response, "Diseños de tablas")
        self.assertContains(response, "Store Procedure")
        self.assertContains(response, "Mantenimientos")
        self.assertContains(response, "Usuarios (tipo US)")
