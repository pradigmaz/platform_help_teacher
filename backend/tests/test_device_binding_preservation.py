"""
Preservation property tests for device binding.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7

IMPORTANT: All tests MUST PASS on unfixed code — they document baseline
behavior that must NOT be broken by the fix.

These tests act as regression guards: if any of them fail after the fix,
something that was working before has been broken.
"""
import inspect
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.device_service import (
    hash_fingerprint,
    parse_device_info,
    register_or_update_device,
)
from app.crud import crud_device


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_fp_json(**overrides) -> str:
    """Build a valid JSON fingerprint string."""
    base = {
        "platform": "Win32",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
        "screen": {"width": 1920, "height": 1080},
    }
    base.update(overrides)
    return json.dumps(base)


def make_mock_device(device_id=None, user_id=None, fp_hash="testhash"):
    d = MagicMock()
    d.id = device_id or uuid4()
    d.user_id = user_id or uuid4()
    d.fingerprint_hash = fp_hash
    d.is_trusted = False
    return d


# ---------------------------------------------------------------------------
# Preservation 1: CRUD flush() — req 3.3
# ---------------------------------------------------------------------------

class TestCrudFlushPreservation:
    """
    PRESERVATION: crud_device.create() uses flush(), NOT commit().
    This is the correct CRUD-layer pattern — commit belongs at endpoint/service level.
    The fix must NOT move commit into CRUD.
    """

    def test_crud_create_uses_flush_not_commit(self):
        """
        Preservation req 3.3: CRUD create() calls flush(), not commit().
        Source inspection confirms the correct pattern is preserved.
        """
        source = inspect.getsource(crud_device.create)
        assert "flush" in source, (
            "REGRESSION: crud_device.create() no longer calls flush(). "
            "CRUD layer must use flush() for intermediate operations."
        )
        assert "commit" not in source, (
            "REGRESSION: crud_device.create() now calls commit() directly. "
            "Commit belongs at endpoint/service level, not in CRUD."
        )

    def test_crud_update_uses_flush_not_commit(self):
        """
        Preservation req 3.3: CRUD update() calls flush(), not commit().
        """
        source = inspect.getsource(crud_device.update)
        assert "flush" in source, (
            "REGRESSION: crud_device.update() no longer calls flush()."
        )
        assert "commit" not in source, (
            "REGRESSION: crud_device.update() now calls commit() directly."
        )

    def test_crud_delete_one_uses_flush_not_commit(self):
        """
        Preservation req 3.3: CRUD delete_one() calls flush(), not commit().
        """
        source = inspect.getsource(crud_device.delete_one)
        assert "flush" in source, (
            "REGRESSION: crud_device.delete_one() no longer calls flush()."
        )
        assert "commit" not in source, (
            "REGRESSION: crud_device.delete_one() now calls commit() directly."
        )

    def test_crud_bulk_delete_uses_flush_not_commit(self):
        """
        Preservation req 3.3: CRUD bulk_delete_by_user() calls flush(), not commit().
        """
        source = inspect.getsource(crud_device.bulk_delete_by_user)
        assert "flush" in source, (
            "REGRESSION: crud_device.bulk_delete_by_user() no longer calls flush()."
        )
        assert "commit" not in source, (
            "REGRESSION: crud_device.bulk_delete_by_user() now calls commit() directly."
        )


# ---------------------------------------------------------------------------
# Preservation 2: GET devices is read-only — req 3.2
# ---------------------------------------------------------------------------

class TestGetDevicesReadOnly:
    """
    PRESERVATION: get_my_devices() endpoint is read-only — must NOT call commit().
    Read operations should never trigger a commit.
    """

    def test_get_my_devices_source_has_no_commit(self):
        """
        Preservation req 3.2: get_my_devices() must not call db.commit().
        Read-only operations must remain read-only after the fix.
        """
        from app.api.v1.endpoints.user_devices import get_my_devices
        source = inspect.getsource(get_my_devices)
        assert "db.commit" not in source, (
            "REGRESSION: get_my_devices() now calls db.commit(). "
            "Read-only endpoints must not commit."
        )

    def test_get_device_source_has_no_commit(self):
        """
        Preservation req 3.2: get_device() (single device) must not call db.commit().
        """
        from app.api.v1.endpoints.user_devices import get_device
        source = inspect.getsource(get_device)
        assert "db.commit" not in source, (
            "REGRESSION: get_device() now calls db.commit(). "
            "Read-only endpoints must not commit."
        )

    @pytest.mark.asyncio
    async def test_get_my_devices_does_not_call_commit(self):
        """
        Preservation req 3.2: Calling get_my_devices() must not trigger db.commit().
        Verified via mock — no commit call on the session.
        """
        from unittest.mock import patch
        from app.api.v1.endpoints.user_devices import get_my_devices
        from starlette.requests import Request as StarletteRequest

        db = AsyncMock()
        user = MagicMock()
        user.id = uuid4()
        # slowapi requires a real starlette Request
        scope = {"type": "http", "method": "GET", "path": "/me/devices",
                 "headers": [], "query_string": b""}
        request = StarletteRequest(scope)

        with patch("app.api.v1.endpoints.user_devices.crud_device.get_by_user",
                   AsyncMock(return_value=[])):
            with patch("app.api.v1.endpoints.user_devices.crud_device.count_by_user",
                       AsyncMock(return_value=0)):
                await get_my_devices(request=request, current_user=user, db=db)

        db.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Preservation 3: parse_device_info with valid JSON — req 3.4
# ---------------------------------------------------------------------------

class TestParseFingerprintPreservation:
    """
    PRESERVATION: parse_device_info() correctly extracts platform/browser/screen
    from valid JSON fingerprint. This behavior must be preserved after the fix.
    """

    def test_windows_chrome_fingerprint(self):
        """
        Preservation req 3.4: Windows + Chrome fingerprint parses correctly.
        """
        fp = make_fp_json(
            platform="Win32",
            userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
        )
        result = parse_device_info(fp)
        assert result["platform"] == "Windows"
        assert result["browser"] == "Chrome"
        assert result["screen"] == "1920×1080"

    def test_macos_safari_fingerprint(self):
        """
        Preservation req 3.4: macOS + Safari fingerprint parses correctly.
        """
        fp = make_fp_json(
            platform="MacIntel",
            userAgent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
        )
        result = parse_device_info(fp)
        assert result["platform"] == "macOS"
        assert result["browser"] == "Safari"

    def test_linux_firefox_fingerprint(self):
        """
        Preservation req 3.4: Linux + Firefox fingerprint parses correctly.
        """
        fp = make_fp_json(
            platform="Linux x86_64",
            userAgent="Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
        )
        result = parse_device_info(fp)
        assert result["platform"] == "Linux"
        assert result["browser"] == "Firefox"

    def test_android_chrome_fingerprint(self):
        """
        Preservation req 3.4: Android + Chrome fingerprint parses correctly.
        """
        fp = make_fp_json(
            platform="Android",
            userAgent="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120",
        )
        result = parse_device_info(fp)
        assert result["platform"] == "Android"
        assert result["browser"] == "Chrome"

    def test_screen_resolution_extracted(self):
        """
        Preservation req 3.4: Screen resolution is extracted from fingerprint.
        """
        fp = make_fp_json(screen={"width": 2560, "height": 1440})
        result = parse_device_info(fp)
        assert result["screen"] == "2560×1440"

    def test_missing_screen_returns_none(self):
        """
        Preservation req 3.4: Missing screen field returns None (not error).
        """
        fp = json.dumps({"platform": "Win32", "userAgent": "Chrome/120"})
        result = parse_device_info(fp)
        assert result["screen"] is None


# ---------------------------------------------------------------------------
# Preservation 4: parse_device_info with empty fingerprint
# ---------------------------------------------------------------------------

class TestParseFingerprintEmptyPreservation:
    """
    PRESERVATION: parse_device_info() handles empty/None fingerprint gracefully.
    Returns Unknown values without raising exceptions.
    """

    def test_none_fingerprint_returns_unknown(self):
        """Empty fingerprint (None) returns Unknown values without exception."""
        result = parse_device_info(None)
        assert result["platform"] == "Unknown"
        assert result["browser"] == "Unknown"
        assert result["screen"] is None

    def test_empty_string_fingerprint_returns_unknown(self):
        """Empty string fingerprint returns Unknown values without exception."""
        result = parse_device_info("")
        assert result["platform"] == "Unknown"
        assert result["browser"] == "Unknown"

    def test_empty_json_object_returns_unknown(self):
        """'{}' fingerprint returns Unknown values without exception."""
        result = parse_device_info("{}")
        assert result["platform"] == "Unknown"
        assert result["browser"] == "Unknown"


# ---------------------------------------------------------------------------
# Preservation 5: register_or_update_device with empty fingerprint — early return
# ---------------------------------------------------------------------------

class TestRegisterOrUpdateEmptyFingerprintPreservation:
    """
    PRESERVATION: register_or_update_device() with empty fingerprint does early return.
    Must not raise, must not call any CRUD operations.
    """

    @pytest.mark.asyncio
    async def test_empty_fingerprint_early_return(self):
        """
        Empty fingerprint causes early return — no DB operations performed.
        This behavior must be preserved after the fix.
        """
        db = AsyncMock()
        user_id = uuid4()

        await register_or_update_device(db=db, user_id=user_id, device_fingerprint=None)

        # No DB operations should have been called
        db.commit.assert_not_called()
        db.flush.assert_not_called()
        db.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_string_fingerprint_early_return(self):
        """
        Empty string fingerprint causes early return without exception.
        """
        db = AsyncMock()
        user_id = uuid4()

        # Must not raise
        await register_or_update_device(db=db, user_id=user_id, device_fingerprint="")

        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_json_fingerprint_early_return(self):
        """
        '{}' fingerprint causes early return without exception.
        """
        db = AsyncMock()
        user_id = uuid4()

        await register_or_update_device(db=db, user_id=user_id, device_fingerprint="{}")

        db.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Preservation 6: hash_fingerprint is deterministic
# ---------------------------------------------------------------------------

class TestHashFingerprintPreservation:
    """
    PRESERVATION: hash_fingerprint() is a pure deterministic function.
    Same input always produces same output. Must not be changed by the fix.
    """

    def test_same_input_same_output(self):
        """
        Determinism: identical fingerprint strings produce identical hashes.
        """
        fp = make_fp_json()
        h1 = hash_fingerprint(fp)
        h2 = hash_fingerprint(fp)
        assert h1 == h2, "hash_fingerprint() must be deterministic"

    def test_different_inputs_different_outputs(self):
        """
        Collision resistance: different fingerprints produce different hashes.
        """
        fp1 = make_fp_json(platform="Win32")
        fp2 = make_fp_json(platform="MacIntel")
        assert hash_fingerprint(fp1) != hash_fingerprint(fp2)

    def test_returns_string(self):
        """hash_fingerprint() always returns a string."""
        result = hash_fingerprint("any-string")
        assert isinstance(result, str)

    def test_returns_sha256_hex(self):
        """hash_fingerprint() returns a 64-char hex string (SHA256)."""
        result = hash_fingerprint("test")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_multiple_calls_consistent(self):
        """
        Property: for any fingerprint string, hash is always the same across calls.
        Simulates property-based testing with a set of representative inputs.
        """
        test_inputs = [
            make_fp_json(),
            make_fp_json(platform="MacIntel"),
            "k7f2m1",
            "abc123",
            json.dumps({"platform": "Android", "userAgent": "Chrome"}),
        ]
        for fp in test_inputs:
            h1 = hash_fingerprint(fp)
            h2 = hash_fingerprint(fp)
            assert h1 == h2, f"Non-deterministic hash for input: {fp[:30]!r}"


# ---------------------------------------------------------------------------
# Preservation 7: security_monitor._get_fingerprint with valid JSON — req 3.4
# ---------------------------------------------------------------------------

class TestSecurityMonitorFingerprintPreservation:
    """
    PRESERVATION: SecurityMonitorMiddleware._get_fingerprint() correctly parses
    valid JSON fingerprint from request header. Security detection pipeline
    must continue to work after the fix.
    """

    def test_get_fingerprint_source_parses_json(self):
        """
        Preservation req 3.4: _get_fingerprint() uses json.loads() to parse header.
        Source inspection confirms JSON parsing is present.
        """
        from app.middleware.security_monitor import SecurityMonitorMiddleware
        source = inspect.getsource(SecurityMonitorMiddleware._get_fingerprint)
        assert "json.loads" in source, (
            "REGRESSION: _get_fingerprint() no longer uses json.loads(). "
            "Security monitor fingerprint parsing is broken."
        )

    def test_get_fingerprint_with_valid_json(self):
        """
        Preservation req 3.4: _get_fingerprint() returns parsed dict for valid JSON.
        """
        from app.middleware.security_monitor import SecurityMonitorMiddleware

        middleware = SecurityMonitorMiddleware(app=MagicMock())
        fp_data = {"platform": "Win32", "userAgent": "Chrome/120", "screen": {"width": 1920}}
        fp_json = json.dumps(fp_data)

        request = MagicMock()
        request.headers.get = MagicMock(return_value=fp_json)

        result = middleware._get_fingerprint(request)

        assert result is not None, (
            "REGRESSION: _get_fingerprint() returned None for valid JSON fingerprint."
        )
        assert result.get("platform") == "Win32"
        assert result.get("userAgent") == "Chrome/120"

    def test_get_fingerprint_returns_none_for_missing_header(self):
        """
        Preservation req 3.4: _get_fingerprint() returns None when header is absent.
        """
        from app.middleware.security_monitor import SecurityMonitorMiddleware

        middleware = SecurityMonitorMiddleware(app=MagicMock())
        request = MagicMock()
        request.headers.get = MagicMock(return_value=None)

        result = middleware._get_fingerprint(request)
        assert result is None

    def test_get_fingerprint_returns_none_for_hash_string(self):
        """
        After task 3.7 fix: _get_fingerprint() returns {"hash": value} for hash strings.
        Hash string fingerprint is preserved for security tracking instead of being lost.
        """
        from app.middleware.security_monitor import SecurityMonitorMiddleware

        middleware = SecurityMonitorMiddleware(app=MagicMock())
        request = MagicMock()
        request.headers.get = MagicMock(return_value="k7f2m1")

        result = middleware._get_fingerprint(request)
        # Fixed behavior: hash string → {"hash": value} for security tracking
        assert result == {"hash": "k7f2m1"}, (
            "After task 3.7 fix: hash string fingerprint should be preserved as "
            '{"hash": value} instead of being lost (None).'
        )
