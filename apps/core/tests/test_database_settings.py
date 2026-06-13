"""Configuración PostgreSQL por entorno."""

from __future__ import annotations

import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from codas.settings._database import build_databases_settings


class BuildDatabasesSettingsTests(SimpleTestCase):
    def test_database_url(self) -> None:
        env = {"DATABASE_URL": "postgresql://user:secret@dbhost:5433/mydb"}
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = build_databases_settings()
        default = cfg["default"]
        self.assertEqual(default["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(default["NAME"], "mydb")
        self.assertEqual(default["USER"], "user")
        self.assertEqual(default["PASSWORD"], "secret")
        self.assertEqual(default["HOST"], "dbhost")
        self.assertEqual(default["PORT"], "5433")

    def test_db_vars(self) -> None:
        env = {
            "DB_NAME": "codas",
            "DB_USER": "codas",
            "DB_PASSWORD": "pwd",
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "5432",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = build_databases_settings()
        self.assertEqual(cfg["default"]["NAME"], "codas")

    def test_missing_config_raises(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                build_databases_settings()
