"""Persistencia de UserProfile vía OperationResult."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.company.models import Company
from apps.core.services.operation_messages import ErrorCode
from apps.userprofile.models import UserProfile
from apps.userprofile.services.userprofile_messages import (
    MSG_USERPROFILE_CREATED,
    MSG_USERPROFILE_DELETED,
    MSG_USERPROFILE_UPDATED,
    MSG_USERNAME_DUPLICATE_FIELD,
)
from apps.userprofile.services.userprofile_persistence import (
    create_user_profile,
    delete_user_profile,
    update_user_profile,
)

User = get_user_model()


class UserProfilePersistenceTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="UPCO", name_long="Co persist")
        self.actor = User.objects.create_user(username="actor_up", password="test-pass-123")
        UserProfile.objects.create(
            user=self.actor,
            user_type=UserProfile.UserType.SUPERUSER,
            status=UserProfile.Status.ACTIVE,
        )

    def test_create_user_profile_success(self) -> None:
        profile = UserProfile(
            phone="300",
            status=UserProfile.Status.ACTIVE,
        )
        result = create_user_profile(
            profile,
            username="newuser01",
            email="new@test.com",
            first_name="Nuevo",
            last_name="Usuario",
            password="secret-pass-8",
            company_id=self.company.pk,
            user_type=UserProfile.UserType.USER,
            actor=self.actor,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, MSG_USERPROFILE_CREATED)
        self.assertEqual(result.data.user.username, "newuser01")
        self.assertEqual(result.data.company_id, self.company.pk)
        self.assertEqual(result.data.created_by, self.actor)
        self.assertTrue(User.objects.filter(username="newuser01").exists())

    def test_create_user_profile_duplicate_username(self) -> None:
        User.objects.create_user(username="dupuser", password="x")
        profile = UserProfile(status=UserProfile.Status.ACTIVE)
        result = create_user_profile(
            profile,
            username="dupuser",
            email="",
            first_name="",
            last_name="",
            password="secret-pass-8",
            company_id=None,
            user_type=UserProfile.UserType.USER,
            actor=self.actor,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.DUPLICATE)
        self.assertEqual(
            result.field_errors,
            {"username": [MSG_USERNAME_DUPLICATE_FIELD]},
        )
        self.assertEqual(
            UserProfile.objects.filter(user__username="dupuser").count(),
            0,
        )

    def test_update_user_profile_success(self) -> None:
        user = User.objects.create_user(
            username="editme",
            password="old-pass-12",
            email="old@test.com",
        )
        profile = UserProfile.objects.create(
            user=user,
            company=self.company,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )
        profile.phone = "999"
        result = update_user_profile(
            profile,
            first_name="Editado",
            last_name="Nombre",
            email="new@test.com",
            password="new-pass-1234",
            company_id=self.company.pk,
            actor=self.actor,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, MSG_USERPROFILE_UPDATED)
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertEqual(user.first_name, "Editado")
        self.assertEqual(user.email, "new@test.com")
        self.assertEqual(profile.updated_by, self.actor)
        self.assertTrue(user.check_password("new-pass-1234"))

    def test_delete_user_profile_success(self) -> None:
        user = User.objects.create_user(username="todelete", password="x")
        profile = UserProfile.objects.create(
            user=user,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )
        pk = profile.pk
        result = delete_user_profile(profile)
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, MSG_USERPROFILE_DELETED)
        self.assertEqual(result.data, pk)
        self.assertFalse(UserProfile.objects.filter(pk=pk).exists())
