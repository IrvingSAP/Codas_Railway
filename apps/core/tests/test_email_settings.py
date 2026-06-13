"""Configuración de correo por entorno."""

from __future__ import annotations

import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from apps.core.services.email_delivery import send_codas_mail
from codas.settings._email import (
    CONSOLE_EMAIL_BACKEND,
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

    def test_production_requires_smtp_credentials(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                build_email_settings(require_smtp=True)

    def test_force_console(self) -> None:
        with mock.patch.dict(os.environ, {"EMAIL_DELIVERY": "console"}, clear=True):
            cfg = build_email_settings(require_smtp=True)
        self.assertEqual(cfg["EMAIL_BACKEND"], CONSOLE_EMAIL_BACKEND)

    def test_production_rejects_email_backend_env(self) -> None:
        env = {
            "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "EMAIL_HOST_USER": "user@test.com",
            "EMAIL_HOST_PASSWORD": "secret",
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
