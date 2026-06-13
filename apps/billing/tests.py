from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.billing.models import Payment, Plan, Subscription, SubscriptionContact
from apps.company.models import Company


@override_settings(
    DEBUG=True,
    LICENSE_SECRET_KEY="clave-de-prueba-solo-tests-hmac-32bytes!!",
)
class SubscriptionModelTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(
            name_short="TST",
            name_long="Compañía de prueba",
        )
        self.plan = Plan.objects.create(
            name="Plan mensual",
            code="monthly-test",
        )

    def test_signature_valid_after_save(self) -> None:
        today = timezone.now().date()
        sub = Subscription.objects.create(
            company=self.company,
            plan=self.plan,
            start_date=today,
            end_date=today + timedelta(days=30),
        )
        self.assertTrue(sub.is_signature_valid())

    def test_max_three_contacts(self) -> None:
        today = timezone.now().date()
        sub = Subscription.objects.create(
            company=self.company,
            plan=self.plan,
            start_date=today,
            end_date=today + timedelta(days=30),
        )
        for i in range(3):
            SubscriptionContact.objects.create(
                subscription=sub,
                full_name=f"Contacto {i}",
                phone=f"+100000{i}",
                email=f"c{i}@example.com",
            )
        fourth = SubscriptionContact(
            subscription=sub,
            full_name="Extra",
            phone="+1999",
            email="extra@example.com",
        )
        with self.assertRaises(ValidationError):
            fourth.full_clean()


@override_settings(
    DEBUG=True,
    LICENSE_SECRET_KEY="clave-de-prueba-solo-tests-hmac-32bytes!!",
)
class PaymentModelTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(
            name_short="PAY",
            name_long="Pago test",
        )
        self.plan = Plan.objects.create(name="Plan", code="plan-pay")
        today = timezone.now().date()
        self.subscription = Subscription.objects.create(
            company=self.company,
            plan=self.plan,
            start_date=today,
            end_date=today + timedelta(days=1),
            status=Subscription.Status.CANCELED,
        )

    def test_payment_rejected_when_subscription_not_active_or_pending(self) -> None:
        payment = Payment(
            subscription=self.subscription,
            amount="10.00",
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()
