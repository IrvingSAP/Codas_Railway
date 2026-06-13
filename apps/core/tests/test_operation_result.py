"""OperationResult y safe_operation."""

from __future__ import annotations

from unittest import mock

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import DataError, IntegrityError, OperationalError
from django.db.models.deletion import ProtectedError
from django.test import SimpleTestCase

from apps.core.services.operation_messages import (
    ErrorCode,
    MSG_DUPLICATE,
    MSG_NOT_FOUND,
    MSG_PROTECTED_DELETE,
    MSG_SAVE_SUCCESS,
    MSG_VALIDATION_MODEL,
)
from apps.core.services.operation_result import OperationResult, safe_operation


class OperationResultTests(SimpleTestCase):
    def test_success_factory(self) -> None:
        result = OperationResult.success(data={"id": 1})
        self.assertTrue(result.ok)
        self.assertEqual(result.data, {"id": 1})
        self.assertEqual(result.error_code, ErrorCode.SUCCESS)

    def test_failure_factory(self) -> None:
        result = OperationResult.failure(
            error_code=ErrorCode.DUPLICATE,
            error_message=MSG_DUPLICATE,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.DUPLICATE)


class SafeOperationTests(SimpleTestCase):
    def test_returns_data_on_success(self) -> None:
        result = safe_operation(lambda: "payload", context="test")
        self.assertTrue(result.ok)
        self.assertEqual(result.data, "payload")
        self.assertEqual(result.error_message, MSG_SAVE_SUCCESS)

    def test_custom_success_message(self) -> None:
        result = safe_operation(
            lambda: None,
            success_message="Eliminado.",
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.error_message, "Eliminado.")

    def test_object_does_not_exist(self) -> None:
        def raise_not_found() -> None:
            raise ObjectDoesNotExist("missing")

        result = safe_operation(raise_not_found)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.NOT_FOUND)
        self.assertEqual(result.error_message, MSG_NOT_FOUND)

    def test_integrity_error(self) -> None:
        def raise_integrity() -> None:
            raise IntegrityError("unique")

        result = safe_operation(raise_integrity)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.DUPLICATE)
        self.assertEqual(result.error_message, MSG_DUPLICATE)
        self.assertNotIn("unique", result.error_message)

    def test_protected_error(self) -> None:
        def raise_protected() -> None:
            raise ProtectedError("blocked", set())

        result = safe_operation(raise_protected)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.PROTECTED_DELETE)
        self.assertEqual(result.error_message, MSG_PROTECTED_DELETE)

    def test_validation_error_with_message_dict(self) -> None:
        def raise_validation() -> None:
            raise ValidationError({"name_short": ["Duplicado."]})

        result = safe_operation(raise_validation)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.VALIDATION_MODEL)
        self.assertEqual(result.error_message, MSG_VALIDATION_MODEL)
        self.assertEqual(result.field_errors, {"name_short": ["Duplicado."]})

    def test_operational_error(self) -> None:
        def raise_operational() -> None:
            raise OperationalError("timeout")

        result = safe_operation(raise_operational)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.DB_CONNECTION)
        self.assertNotIn("timeout", result.error_message)

    def test_data_error(self) -> None:
        def raise_data() -> None:
            raise DataError("bad value")

        result = safe_operation(raise_data)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.DATA_ERROR)

    def test_unexpected_exception(self) -> None:
        def raise_runtime() -> None:
            raise RuntimeError("secret detail")

        with mock.patch("apps.core.services.operation_result.logger") as log_mock:
            result = safe_operation(raise_runtime, context="unit")
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, ErrorCode.UNEXPECTED)
        self.assertNotIn("secret", result.error_message)
        log_mock.exception.assert_called()
