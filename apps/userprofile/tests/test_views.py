"""Vistas de perfiles (piloto OperationResult)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.company.models import Company
from apps.userprofile.models import UserProfile

User = get_user_model()


def _valid_create_post(
    *,
    username: str = "paneluser01",
    password: str = "secret-pass-8",
) -> dict[str, str]:
    return {
        "username": username,
        "email": "panel@test.com",
        "first_name": "Panel",
        "last_name": "User",
        "password1": password,
        "password2": password,
        "phone": "",
        "document_id": "",
        "address": "",
        "status": UserProfile.Status.ACTIVE,
    }


class UserProfileMaintainerMixin:
    def setUp(self) -> None:
        self.company = Company.objects.create(name_short="VCO", name_long="Vista Co")
        self.su = User.objects.create_user(username="su_up_view", password="test-pass-123")
        UserProfile.objects.create(
            user=self.su,
            user_type=UserProfile.UserType.SUPERUSER,
            status=UserProfile.Status.ACTIVE,
        )
        self.client = Client()
        self.client.force_login(self.su)


class UserProfileCreateViewTests(UserProfileMaintainerMixin, TestCase):
    def test_create_redirects_on_success(self) -> None:
        response = self.client.post(
            reverse("userprofile:create"),
            _valid_create_post(username="created01"),
        )
        self.assertEqual(response.status_code, 302)
        profile = UserProfile.objects.get(user__username="created01")
        self.assertEqual(response.url, reverse("userprofile:detail", pk=profile.pk))

    def test_create_duplicate_username_rerenders_form(self) -> None:
        User.objects.create_user(username="exists01", password="x")
        response = self.client.post(
            reverse("userprofile:create"),
            _valid_create_post(username="exists01"),
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertIn("username", form.errors)

    def test_create_invalid_form_shows_catalog_message(self) -> None:
        data = _valid_create_post()
        data["password2"] = "otra-pass-99"
        response = self.client.post(reverse("userprofile:create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
