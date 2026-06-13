"""Vistas y acceso HTTP de campos (`DetailTable`); §9 CODAS_TABLE_DESIGN."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.company.models import Company
from apps.table_design.models import DetailTable, HeaderTable
from apps.table_design.tests.factories import create_detail_field
from apps.userprofile.models import UserProfile

User = get_user_model()


def _user_with_company_table_design_access(company: Company) -> User:
    user = User.objects.create_user(username="tdv_user", password="test-pw-123")
    UserProfile.objects.create(
        user=user,
        company=company,
        user_type=UserProfile.UserType.USER,
        status=UserProfile.Status.ACTIVE,
    )
    return user


def _valid_field_post(ftype: str = DetailTable.FieldDB2Type.VARCHAR) -> dict[str, str]:
    d: dict[str, str] = {
        "field_name_long": "CUSTOMER_ID",
        "field_name_short": "FLDCUST01",
        "field_type": ftype,
        "field_length": "20",
        "notes": "Nota obligatoria de prueba.",
    }
    if ftype in (
        DetailTable.FieldDB2Type.VARCHAR,
        DetailTable.FieldDB2Type.VARGRAPHIC,
    ):
        d["allocate_length"] = "18"
    else:
        d["allocate_length"] = ""
    return d


class FieldListAccessTests(TestCase):
    """Listado y mutaciones: ámbito por compañía, bloqueo de cabecera."""

    def setUp(self) -> None:
        self.c1 = Company.objects.create(name_short="C1", name_long="Company One")
        self.c2 = Company.objects.create(name_short="C2", name_long="Company Two")
        self.user = _user_with_company_table_design_access(self.c1)
        self.header_ours = HeaderTable.objects.create(
            company=self.c1,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TABLE_OURS_LONGN",
            table_name_short="OURSTABLE1",
            schema="LIBC1",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            script_generated=False,
        )
        self.header_other = HeaderTable.objects.create(
            company=self.c2,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="THEIR_LONG_TEN",
            table_name_short="THRTAB123",
            schema="LIBC2",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        self.field_ours = create_detail_field(
            self.header_ours,
            1,
            field_name_long="FIRSTCLNAME",
            field_name_short="FIRCLNAME",
            field_type=DetailTable.FieldDB2Type.INTEGER,
            field_length=4,
            notes="n",
            nullable=False,
            status=DetailTable.Status.ACTIVE,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_field_list_404_for_other_company_header(self) -> None:
        url = reverse(
            "table_design:field_list", kwargs={"header_pk": self.header_other.pk}
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

    def test_field_create_404_for_other_company(self) -> None:
        url = reverse(
            "table_design:field_create", kwargs={"header_pk": self.header_other.pk}
        )
        r = self.client.post(url, _valid_field_post())
        self.assertEqual(r.status_code, 404)

    def test_field_update_404_for_other_company(self) -> None:
        url = reverse(
            "table_design:field_update",
            kwargs={"header_pk": self.header_other.pk, "field_pk": 9999},
        )
        r = self.client.post(url, _valid_field_post())
        self.assertEqual(r.status_code, 404)

    def test_field_create_blocked_when_script_generated(self) -> None:
        self.header_ours.script_generated = True
        self.header_ours.save(update_fields=["script_generated"])
        n_before = DetailTable.objects.filter(header=self.header_ours).count()
        url = reverse(
            "table_design:field_create", kwargs={"header_pk": self.header_ours.pk}
        )
        r = self.client.post(url, _valid_field_post())
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            DetailTable.objects.filter(header=self.header_ours).count(), n_before
        )
        self.assertIn(
            reverse("table_design:field_list", kwargs={"header_pk": self.header_ours.pk}),
            r["Location"] or "",
        )

    def test_field_create_blocked_when_header_inactive(self) -> None:
        self.header_ours.status = HeaderTable.Status.INACTIVE
        self.header_ours.save(update_fields=["status"])
        n_before = DetailTable.objects.filter(header=self.header_ours).count()
        url = reverse(
            "table_design:field_create", kwargs={"header_pk": self.header_ours.pk}
        )
        r = self.client.post(url, _valid_field_post())
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            DetailTable.objects.filter(header=self.header_ours).count(), n_before
        )

    def test_field_update_succeeds_when_header_editable(self) -> None:
        url = reverse(
            "table_design:field_update",
            kwargs={
                "header_pk": self.header_ours.pk,
                "field_pk": self.field_ours.pk,
            },
        )
        data = {
            "field_name_long": "FIRSTCLNAME1",
            "field_name_short": "FIRCLNAME",
            "field_type": self.field_ours.field_type,
            "field_length": "4",
            "notes": "nueva nota mín",
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302)
        self.field_ours.refresh_from_db()
        self.assertEqual(self.field_ours.field_name_long, "FIRSTCLNAME1")

    def test_field_update_rejected_when_script_before_post(self) -> None:
        self.header_ours.script_generated = True
        self.header_ours.save(update_fields=["script_generated"])
        self.field_ours.field_name_long = "ORIGINALN1"
        self.field_ours.save(update_fields=["field_name_long"])
        url = reverse(
            "table_design:field_update",
            kwargs={
                "header_pk": self.header_ours.pk,
                "field_pk": self.field_ours.pk,
            },
        )
        data = {
            "field_name_long": "SHOULDNTSAVE",
            "field_name_short": "FIRCLNAME",
            "field_type": self.field_ours.field_type,
            "field_length": "4",
            "notes": "cambio de nota",
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302)
        self.field_ours.refresh_from_db()
        self.assertEqual(self.field_ours.field_name_long, "ORIGINALN1")

    def test_field_create_success(self) -> None:
        n0 = DetailTable.objects.filter(header=self.header_ours).count()
        url = reverse(
            "table_design:field_create", kwargs={"header_pk": self.header_ours.pk}
        )
        data = {**_valid_field_post(), "field_name_short": "NEWFLD0001"}
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302, repr(r.get("Location")))
        self.assertIn("/fields/", r["Location"])
        self.assertNotIn("db2-attributes", r["Location"])
        self.assertEqual(DetailTable.objects.filter(header=self.header_ours).count(), n0 + 1)
        new_f = (
            DetailTable.objects.filter(
                header=self.header_ours, field_name_short="NEWFLD0001"
            ).get()
        )
        self.assertEqual(new_f.order_reg, 2)

    def test_field_db2_attributes_get(self) -> None:
        url = reverse(
            "table_design:field_db2_attributes",
            kwargs={
                "header_pk": self.header_ours.pk,
                "field_pk": self.field_ours.pk,
            },
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "user_defined_field")

    def test_field_db2_attributes_post_is_unique(self) -> None:
        from apps.table_design.models import DetailTableDb2Attributes

        url = reverse(
            "table_design:field_db2_attributes",
            kwargs={
                "header_pk": self.header_ours.pk,
                "field_pk": self.field_ours.pk,
            },
        )
        r = self.client.post(
            url,
            {"sel_is_unique": "on"},
        )
        self.assertEqual(r.status_code, 302)
        attrs = DetailTableDb2Attributes.objects.get(detail=self.field_ours)
        self.assertTrue(attrs.is_unique)


class HeaderUpdateAccessTests(TestCase):
    """Edición de cabecera: script generado ya no bloquea; inactiva sí."""

    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="C1", name_long="Company One")
        self.user = _user_with_company_table_design_access(self.company)
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TABLE_SCRIPT_OK",
            table_name_short="SCRGEN01",
            schema="LIBC1",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
            script_generated=True,
            script_date="2026-01-15",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_update_get_allowed_when_script_generated(self) -> None:
        url = reverse("table_design:header_update", kwargs={"pk": self.header.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_edit_identity"])

    def test_update_get_blocked_when_inactive(self) -> None:
        self.header.status = HeaderTable.Status.INACTIVE
        self.header.save(update_fields=["status"])
        url = reverse("table_design:header_update", kwargs={"pk": self.header.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("table_design:header_list"))

    def _update_post_data(self, **overrides: str) -> dict[str, str]:
        data = {
            "table_model": self.header.table_model,
            "table_name_long": self.header.table_name_long,
            "table_name_short": self.header.table_name_short,
            "schema": self.header.schema,
            "table_type": self.header.table_type,
            "status": self.header.status,
            "pk_constraint_name": "",
            "record_format_name": "",
            "identity_start": "",
            "identity_increment": "",
            "identity_cache": "",
            "notes": "",
        }
        data.update(overrides)
        return data

    def test_update_post_resets_script_when_field_changed(self) -> None:
        url = reverse("table_design:header_update", kwargs={"pk": self.header.pk})
        response = self.client.post(
            url,
            self._update_post_data(notes="Notas actualizadas tras script"),
        )
        self.assertEqual(response.status_code, 302)
        self.header.refresh_from_db()
        self.assertFalse(self.header.script_generated)
        self.assertIsNone(self.header.script_date)

    def test_update_post_keeps_script_when_unchanged(self) -> None:
        """Guardar desde edición con script previo siempre invalida el DDL."""
        url = reverse("table_design:header_update", kwargs={"pk": self.header.pk})
        response = self.client.post(url, self._update_post_data())
        self.assertEqual(response.status_code, 302)
        self.header.refresh_from_db()
        self.assertFalse(self.header.script_generated)
        self.assertIsNone(self.header.script_date)
