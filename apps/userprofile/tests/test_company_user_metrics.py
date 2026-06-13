from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.company.models import Company
from apps.userprofile.models import UserProfile
from apps.userprofile.services.company_user_metrics import get_company_user_metrics

User = get_user_model()


class CompanyUserMetricsTests(TestCase):
    def setUp(self) -> None:
        self.company_a = Company.objects.create(name_short="COA", name_long="Compañía A")
        self.company_b = Company.objects.create(name_short="COB", name_long="Compañía B")

    def _profile(self, username: str, company: Company, user_type: str) -> UserProfile:
        user = User.objects.create_user(username=username, password="x")
        return UserProfile.objects.create(
            user=user,
            company=company,
            user_type=user_type,
            status=UserProfile.Status.ACTIVE,
        )

    def test_counts_us_and_as_for_company(self) -> None:
        self._profile("us1", self.company_a, UserProfile.UserType.USER)
        self._profile("us2", self.company_a, UserProfile.UserType.USER)
        self._profile("as1", self.company_a, UserProfile.UserType.ADMIN_SYSTEM)
        self._profile("other", self.company_b, UserProfile.UserType.USER)
        self._profile("ac1", self.company_a, UserProfile.UserType.ADMIN_COMPANY)

        metrics = get_company_user_metrics(self.company_a.pk)
        self.assertEqual(metrics.total_users, 2)
        self.assertEqual(metrics.total_admin_system, 1)

    def test_none_company_returns_zero(self) -> None:
        metrics = get_company_user_metrics(None)
        self.assertEqual(metrics.total_users, 0)
        self.assertEqual(metrics.total_admin_system, 0)
