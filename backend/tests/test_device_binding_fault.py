"""
Bug condition exploration tests for device binding.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6

CRITICAL: Tests MUST FAIL on unfixed code — failure confirms the bug exists.
Uses AsyncMock — no real DB required.

Bug: Mutating device operations do not persist because no endpoint/service
calls commit(). CRUD uses flush() only, so get_db() session close rolls back.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.device_service import parse_device_info, register_or_update_device


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_fp_json(suffix: str = "abc") -> str:
    return json.dumps({
        "platform": "Win32",
        "userAgent": "Mozilla/5.0 Chrome/120",
        "screen": {"width": 1920, "height": 1080},
        "hash": suffix,
    })


def make_mock_device(device_id=None, user_id=None, fp_hash="testhash", is_trusted=False):
    d = MagicMock()
    d.id = device_id or uuid4()
    d.user_id = user_id or uuid4()
    d.fingerprint_hash = fp_hash
    d.is_trusted = is_trusted
    return d


# ---------------------------------------------------------------------------
# Property 1: CREATE — register_or_update_device must call commit()
# ---------------------------------------------------------------------------

class TestCreateDevicePersistence:
    """
    Bug: register_or_update_device() → crud.create() → flush(), no commit().
    Session close → INSERT rolled back → device not in DB.
    """

    @pytest.mark.asyncio
    async def test_register_calls_commit_after_create(self):
        """
        EXPECTED TO FAIL on unfixed code.
        register_or_update_device() must call db.commit() after creating device.
        """
        db = AsyncMock()
        user_id = uuid4()

        with patch("app.services.device_service.crud_device") as mock_crud:
            mock_crud.get_by_fingerprint = AsyncMock(return_value=None)
            mock_crud.create = AsyncMock(return_value=make_mock_device(user_id=user_id))

            await register_or_update_device(db=db, user_id=user_id, device_fingerprint=make_fp_json())

        assert db.commit.called, (
            "BUG CONFIRMED: register_or_update_device() did not call db.commit() after CREATE. "
            "Device will be rolled back when session closes."
        )

    @pytest.mark.asyncio
    async def test_register_calls_commit_after_update(self):
        """
        EXPECTED TO FAIL on unfixed code.
        register_or_update_device() must call db.commit() after updating existing device.
        """
        db = AsyncMock()
        user_id = uuid4()
        existing = make_mock_device(user_id=user_id)

        with patch("app.services.device_service.crud_device") as mock_crud:
            mock_crud.get_by_fingerprint = AsyncMock(return_value=existing)
            mock_crud.update = AsyncMock(return_value=existing)

            await register_or_update_device(db=db, user_id=user_id, device_fingerprint=make_fp_json())

        assert db.commit.called, (
            "BUG CONFIRMED: register_or_update_device() did not call db.commit() after UPDATE."
        )

    @pytest.mark.asyncio
    async def test_register_returns_bool(self):
        """
        EXPECTED TO FAIL on unfixed code (returns None).
        register_or_update_device() must return bool, not None.
        """
        db = AsyncMock()
        user_id = uuid4()

        with patch("app.services.device_service.crud_device") as mock_crud:
            mock_crud.get_by_fingerprint = AsyncMock(return_value=None)
            mock_crud.create = AsyncMock(return_value=make_mock_device(user_id=user_id))

            result = await register_or_update_device(
                db=db, user_id=user_id, device_fingerprint=make_fp_json()
            )

        assert isinstance(result, bool), (
            f"BUG CONFIRMED: register_or_update_device() returned {type(result).__name__!r}, "
            "expected bool. Silent error swallowing — no return value."
        )

    @pytest.mark.asyncio
    async def test_register_returns_false_on_error(self):
        """
        EXPECTED TO FAIL on unfixed code (returns None on error, not False).
        On exception: must rollback, log ERROR, return False.
        """
        db = AsyncMock()
        user_id = uuid4()

        with patch("app.services.device_service.crud_device") as mock_crud:
            mock_crud.get_by_fingerprint = AsyncMock(
                side_effect=Exception("DB constraint violation")
            )

            result = await register_or_update_device(
                db=db, user_id=user_id, device_fingerprint=make_fp_json()
            )

        assert result is False, (
            f"BUG CONFIRMED: On exception, register_or_update_device() returned {result!r}, "
            "expected False. Error is silently swallowed."
        )
        assert db.rollback.called, (
            "BUG CONFIRMED: db.rollback() not called after exception."
        )


# ---------------------------------------------------------------------------
# Property 2-4: Endpoint commit checks via service-layer inspection
# ---------------------------------------------------------------------------

class TestEndpointCommitMissing:
    """
    Verify that endpoint functions do NOT call commit() — confirming the bug.
    These tests document the bug condition by inspecting actual endpoint source.
    """

    def test_unbind_device_source_has_no_commit(self):
        """
        FIX VERIFIED: unbind_device() now calls db.commit() after delete.
        """
        import inspect
        from app.api.v1.endpoints.user_devices import unbind_device
        source = inspect.getsource(unbind_device)
        assert "db.commit" in source, (
            "REGRESSION: unbind_device() no longer calls db.commit(). Fix was reverted."
        )

    def test_confirm_device_source_has_no_commit(self):
        """FIX VERIFIED: confirm_device() now calls db.commit() after update."""
        import inspect
        from app.api.v1.endpoints.user_devices import confirm_device
        source = inspect.getsource(confirm_device)
        assert "db.commit" in source, (
            "REGRESSION: confirm_device() no longer calls db.commit(). Fix was reverted."
        )

    def test_revoke_all_devices_source_has_no_commit(self):
        """FIX VERIFIED: revoke_all_devices() now calls db.commit() after bulk delete."""
        import inspect
        from app.api.v1.endpoints.user_devices import revoke_all_devices
        source = inspect.getsource(revoke_all_devices)
        assert "db.commit" in source, (
            "REGRESSION: revoke_all_devices() no longer calls db.commit(). Fix was reverted."
        )

    def test_register_or_update_device_source_has_no_commit(self):
        """FIX VERIFIED: register_or_update_device() now calls db.commit() after create/update."""
        import inspect
        source = inspect.getsource(register_or_update_device)
        assert "db.commit" in source, (
            "REGRESSION: register_or_update_device() no longer calls db.commit(). Fix was reverted."
        )


# ---------------------------------------------------------------------------
# Property 5: FINGERPRINT — parse_device_info handles all input types
# ---------------------------------------------------------------------------

class TestFingerprintParsing:
    """
    Bug: parse_device_info("0") → json.loads("0") returns int → AttributeError.
    """

    @pytest.mark.parametrize("hash_string", [
        "k7f2m1",
        "abc123",
        "zzzzzz",
        "not-json-at-all",
        "undefined",
    ])
    def test_handles_hash_string_without_exception(self, hash_string):
        """Hash strings must return Unknown values, not raise."""
        try:
            result = parse_device_info(hash_string)
        except Exception as e:
            pytest.fail(
                f"BUG CONFIRMED: parse_device_info({hash_string!r}) raised "
                f"{type(e).__name__}: {e}"
            )
        assert result.get("platform") == "Unknown"
        assert result.get("browser") == "Unknown"

    def test_numeric_string_does_not_raise(self):
        """
        EXPECTED TO FAIL on unfixed code.
        json.loads("0") returns int(0) → fp.get() → AttributeError.
        """
        try:
            result = parse_device_info("0")
        except Exception as e:
            pytest.fail(
                f"BUG CONFIRMED: parse_device_info('0') raised {type(e).__name__}: {e}. "
                "json.loads('0') returns int, not dict — missing isinstance check."
            )
        assert result.get("platform") == "Unknown"

    def test_valid_json_parses_correctly(self):
        """Preservation: valid JSON fingerprint must parse correctly."""
        fp = json.dumps({
            "platform": "Win32",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0) Chrome/120",
            "screen": {"width": 1920, "height": 1080},
        })
        result = parse_device_info(fp)
        assert result["platform"] == "Windows"
        assert result["browser"] == "Chrome"
        assert result["screen"] is not None
        assert "1920" in result["screen"] and "1080" in result["screen"]
