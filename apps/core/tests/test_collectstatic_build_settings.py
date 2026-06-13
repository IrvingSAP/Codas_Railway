"""Settings de build para collectstatic en Railway."""

from __future__ import annotations

from django.test import SimpleTestCase

from codas.settings import collectstatic_build


class CollectstaticBuildSettingsTests(SimpleTestCase):
    def test_module_has_static_root_and_secret(self) -> None:
        self.assertEqual(collectstatic_build.STATIC_ROOT.name, "staticfiles")
        self.assertTrue(collectstatic_build.SECRET_KEY)
        self.assertIn("postgresql", collectstatic_build.DATABASES["default"]["ENGINE"])
