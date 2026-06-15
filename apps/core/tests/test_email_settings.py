"""Configuración de correo por entorno."""

from __future__ import annotations

import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from apps.core.services.email_delivery import email_delivery_user_message, send_codas_mail
from codas.settings._email import (
    CONSOLE_EMAIL_BACKEND,
    EMAIL_DELIVERY_RESEND,
    SMTP_EMAIL_BACKEND,
    build_email_settings,
    validate_email_settings_for_production,
)


class BuildEmailSettingsTests(SimpleTestCase):
    def test_local_auto_without_credentials_uses_console(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = build_email_settings(require_smtp=False)
        self.assertEqual(cfg["EMAIL_DELIVERY_EFFECTIVE"], "console")
        self.assertEqual(cfg["EMAIL_BACKEND"], CONSOLE_EMAIL_BACKEND)

    def test_local_auto_with_credentials_uses_smtp(self) -> None:
        env = {
            "EMAIL_HOST_USER": "user@test.com",
            "EMAIL_HOST_PASSWORD": "secret",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = build_email_settings(require_smtp=False)
        self.assertEqual(cfg["EMAIL_DELIVERY_EFFECTIVE"], "smtp")
        self.assertEqual(cfg["EMAIL_BACKEND"], SMTP_EMAIL_BACKEND)
        self.assertEqual(cfg["EMAIL_HOST_USER"], "user@test.com")

    def test_local_auto_with_resend_key_uses_resend(self) -> None:
        env = {
            "RESEND_API_KEY": "re_test_key",
            "DEFAULT_FROM_EMAIL": "CODAS <onboarding@resend.dev>",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = build_email_settings(require_smtp=False)
        self.assertEqual(cfg["EMAIL_DELIVERY_EFFECTIVE"], EMAIL_DELIVERY_RESEND)
        self.assertEqual(cfg["RESEND_API_KEY"], "re_test_key")
        self.assertNotIn("EMAIL_BACKEND", cfg)

    def test_production_auto_prefers_resend_over_smtp(self) -> None:
        env = {
            "RESEND_API_KEY": "re_test_key",
            "EMAIL_HOST_USER": "user@test.com",
            "EMAIL_HOST_PASSWORD": "secret",
            "DEFAULT_FROM_EMAIL": "CODAS <onboarding@resend.dev>",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = build_email_settings(require_smtp=True)
        self.assertEqual(cfg["EMAIL_DELIVERY_EFFECTIVE"], EMAIL_DELIVERY_RESEND)
        self.assertEqual(cfg["RESEND_API_KEY"], "re_test_key")

    def test_production_requires_delivery_credentials(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                build_email_settings(require_smtp=True)

    def test_production_with_resend_api_key(self) -> None:
        env = {
            "RESEND_API_KEY": "re_test_key",
            "DEFAULT_FROM_EMAIL": "CODAS <onboarding@resend.dev>",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = build_email_settings(require_smtp=True)
        self.assertEqual(cfg["EMAIL_DELIVERY_EFFECTIVE"], EMAIL_DELIVERY_RESEND)

    def test_force_smtp_still_available(self) -> None:
        env = {
            "EMAIL_DELIVERY": "smtp",
            "EMAIL_HOST_USER": "user@test.com",
            "EMAIL_HOST_PASSWORD": "secret",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = build_email_settings(require_smtp=True)
        self.assertEqual(cfg["EMAIL_DELIVERY_EFFECTIVE"], "smtp")
        self.assertEqual(cfg["EMAIL_BACKEND"], SMTP_EMAIL_BACKEND)

    def test_force_console(self) -> None:
        with mock.patch.dict(os.environ, {"EMAIL_DELIVERY": "console"}, clear=True):
            cfg = build_email_settings(require_smtp=True)
        self.assertEqual(cfg["EMAIL_BACKEND"], CONSOLE_EMAIL_BACKEND)

    def test_production_rejects_email_backend_env(self) -> None:
        env = {
            "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "RESEND_API_KEY": "re_test_key",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                validate_email_settings_for_production()


class SendCodasMailTests(SimpleTestCase):
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@test.com",
        EMAIL_DELIVERY_EFFECTIVE="smtp",
    )
    def test_send_codas_mail_uses_locmem(self) -> None:
        from django.core import mail

        send_codas_mail(
            subject="Test",
            body="Hola",
            recipients=["dest@test.com"],
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["dest@test.com"])

    @override_settings(
        DEFAULT_FROM_EMAIL="CODAS <onboarding@resend.dev>",
        EMAIL_DELIVERY_EFFECTIVE=EMAIL_DELIVERY_RESEND,
        RESEND_API_KEY="re_test_key",
    )
    @mock.patch("apps.core.services.email_delivery.resend.Emails.send")
    def test_send_codas_mail_uses_resend_sdk(self, mock_send: mock.Mock) -> None:
        send_codas_mail(
            subject="CODAS — Código",
            body="Su código es: 123456",
            recipients=["dest@test.com"],
        )
        mock_send.assert_called_once()
        params = mock_send.call_args[0][0]
        self.assertEqual(params["from"], "CODAS <onboarding@resend.dev>")
        self.assertEqual(params["to"], ["dest@test.com"])
        self.assertEqual(params["text"], "Su código es: 123456")

    def test_resend_sandbox_user_message(self) -> None:
        from resend.exceptions import ResendError

        exc = ResendError(
            code=403,
            error_type="validation_error",
            message=(
                "You can only send testing emails to your own email address. "
                "To send emails to other recipients, please verify a domain."
            ),
            suggested_action="Verify domain",
        )
        msg = email_delivery_user_message(exc)
        self.assertIn("modo prueba", msg)
        self.assertIn("resend.com/domains", msg)
