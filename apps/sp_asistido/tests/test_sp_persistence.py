"""Persistencia SP Asistido vía OperationResult."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.company.models import Company
from apps.sp_asistido.models import SPDefinition, SPStepState
from apps.sp_asistido.services.sp_asistido_messages import (
    MSG_DEFINITION_SAVED,
    MSG_SCRIPT_CONFIRMED_ADD,
    draft_created_message,
)
from apps.sp_asistido.services.sp_persistence import (
    confirm_generated_script,
    create_wizard_definition_draft,
    update_definition_identification,
    upsert_step_state,
)
from apps.table_design.models import HeaderTable
from apps.userprofile.models import UserProfile

User = get_user_model()


class SpPersistenceTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="SP1", name_long="SP Co")
        self.header = HeaderTable.objects.create(
            company=self.company,
            table_model=HeaderTable.TableModel.SIMPLE,
            table_name_long="TABLA_SP_PERSIST",
            table_name_short="TABSPP001",
            schema="LIBSP",
            table_type=HeaderTable.TableKind.PHYSICAL,
            status=HeaderTable.Status.ACTIVE,
        )
        self.user = User.objects.create_user(username="sp_persist", password="test-pass-123")
        UserProfile.objects.create(
            user=self.user,
            company=self.company,
            user_type=UserProfile.UserType.ADMIN_SYSTEM,
            status=UserProfile.Status.ACTIVE,
        )

    def test_create_wizard_definition_draft_success(self) -> None:
        step1 = {
            "schema_name": "LIBSP",
            "procedure_name_short": "SPNEW0001",
            "procedure_name_long": "SP nuevo persist",
            "procedure_comment": "test",
        }
        result = create_wizard_definition_draft(
            company_id=self.company.pk,
            header_table_id=self.header.pk,
            operation=SPDefinition.Operation.ADD,
            step1_data=step1,
            user=self.user,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, draft_created_message("ADD"))
        definition = result.data
        self.assertEqual(definition.procedure_name_short, "SPNEW0001")
        self.assertEqual(definition.current_step, 2)
        self.assertTrue(
            SPStepState.objects.filter(
                sp_definition=definition, step_number=2
            ).exists()
        )

    def test_update_definition_identification_success(self) -> None:
        definition = SPDefinition.objects.create(
            company=self.company,
            header_table=self.header,
            operation=SPDefinition.Operation.READ,
            schema_name="LIBSP",
            procedure_name_short="SPUPD0001",
            procedure_name_long="Antes",
            procedure_comment="",
            status=SPDefinition.Status.DRAFT,
        )
        result = update_definition_identification(
            definition,
            schema_name="LIBSP",
            procedure_name_short="SPUPD0001",
            procedure_name_long="Después",
            procedure_comment="comentario",
            status=SPDefinition.Status.ACTIVE,
            user=self.user,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, MSG_DEFINITION_SAVED)
        definition.refresh_from_db()
        self.assertEqual(definition.procedure_name_long, "Después")
        self.assertEqual(definition.status, SPDefinition.Status.ACTIVE)

    def test_confirm_generated_script_success(self) -> None:
        definition = SPDefinition.objects.create(
            company=self.company,
            header_table=self.header,
            operation=SPDefinition.Operation.ADD,
            schema_name="LIBSP",
            procedure_name_short="SPCONF001",
            procedure_name_long="Confirm test",
            procedure_comment="",
            status=SPDefinition.Status.DRAFT,
        )

        def _fake_persist(defn, sql, *, user, **kwargs):
            defn.script_generated = True
            defn.save(update_fields=["script_generated", "updated_at"])

        result = confirm_generated_script(
            definition,
            "CREATE PROCEDURE x",
            user=self.user,
            persist_fn=_fake_persist,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, MSG_SCRIPT_CONFIRMED_ADD)
        definition.refresh_from_db()
        self.assertTrue(definition.script_generated)
