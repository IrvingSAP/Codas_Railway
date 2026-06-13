from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.company.models import Company
from apps.userprofile.models import UserProfile

User = get_user_model()


class UserProfileAccessTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(
            name_short="T1",
            name_long="Test Co",
        )
        self.su = User.objects.create_user(username="su", password="x")
        UserProfile.objects.create(
            user=self.su,
            user_type=UserProfile.UserType.SUPERUSER,
            status=UserProfile.Status.ACTIVE,
        )
        self.ac = User.objects.create_user(username="ac", password="x")
        UserProfile.objects.create(
            user=self.ac,
            company=self.company,
            user_type=UserProfile.UserType.ADMIN_COMPANY,
            status=UserProfile.Status.ACTIVE,
        )
        self.us = User.objects.create_user(username="us", password="x")
        UserProfile.objects.create(
            user=self.us,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )
        self.other = User.objects.create_user(username="other", password="x")
        UserProfile.objects.create(
            user=self.other,
            company=self.company,
            user_type=UserProfile.UserType.USER,
            status=UserProfile.Status.ACTIVE,
        )

    def test_us_redirects_from_list(self) -> None:
        c = Client()
        c.force_login(self.us)
        r = c.get(reverse("userprofile:list"))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse("dashboard:home"))

    def test_su_list_ok(self) -> None:
        c = Client()
        c.force_login(self.su)
        r = c.get(reverse("userprofile:list"))
        self.assertEqual(r.status_code, 200)

    def test_ac_sees_only_company_profiles(self) -> None:
        c = Client()
        c.force_login(self.ac)
        r = c.get(reverse("userprofile:list"))
        self.assertEqual(r.status_code, 200)
        usernames = [p.user.get_username() for p in r.context["profiles"]]
        self.assertIn("other", usernames)
        self.assertIn("ac", usernames)
        self.assertNotIn("su", usernames)
        self.assertNotIn("us", usernames)
