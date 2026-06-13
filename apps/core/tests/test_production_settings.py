"""Configuración HTTPS/CSRF del entorno production."""

from __future__ import annotations

import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from codas.settings._https import (
    build_https_settings,
    validate_https_settings_for_production,
)


class BuildHttpsSettingsTests(SimpleTestCase):
    def test_build_from_env(self) -> None:
        env = {"CSRF_TRUSTED_ORIGINS": "https://a.example.com,https://b.example.com"}
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = build_https_settings()
        self.assertEqual(
            cfg["CSRF_TRUSTED_ORIGINS"],
            ["https://a.example.com", "https://b.example.com"],
        )
        self.assertEqual(cfg["SECURE_PROXY_SSL_HEADER"], ("HTTP_X_FORWARDED_PROTO", "https"))
        self.assertTrue(cfg["SESSION_COOKIE_SECURE"])
        self.assertTrue(cfg["CSRF_COOKIE_SECURE"])


class ValidateHttpsSettingsTests(SimpleTestCase):
    def test_requires_csrf_trusted_origins(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            validate_https_settings_for_production([])

    def test_accepts_csrf_trusted_origins(self) -> None:
        validate_https_settings_for_production(["https://codas.up.railway.app"])
