"""Contracts for parsing, hashing, and propagating device fingerprint data."""

import json
from unittest.mock import MagicMock

import pytest

from app.services.device_service import hash_fingerprint, parse_device_info
from tests.support.device_binding import make_fp_json


class TestFingerprintParsingContract:
    @pytest.mark.parametrize("hash_string", ["k7f2m1", "abc123", "zzzzzz", "not-json-at-all", "undefined"])
    def test_handles_hash_string_without_exception(self, hash_string):
        result = parse_device_info(hash_string)
        assert result.get("platform") == "Unknown"
        assert result.get("browser") == "Unknown"

    def test_numeric_string_does_not_raise(self):
        result = parse_device_info("0")
        assert result["platform"] == "Unknown"
        assert result["browser"] == "Unknown"

    def test_valid_json_parses_correctly(self):
        result = parse_device_info(make_fp_json())
        assert result["platform"] == "Windows"
        assert result["browser"] == "Chrome"
        assert result["screen"] == "1920×1080"

    def test_platform_variants_parse_correctly(self):
        cases = [
            (make_fp_json(platform="MacIntel", userAgent="Mozilla/5.0 Safari/605.1.15"), "macOS", "Safari"),
            (make_fp_json(platform="Linux x86_64", userAgent="Mozilla/5.0 Firefox/121.0"), "Linux", "Firefox"),
            (make_fp_json(platform="Android", userAgent="Mozilla/5.0 Chrome/120"), "Android", "Chrome"),
        ]
        for payload, platform, browser in cases:
            result = parse_device_info(payload)
            assert result["platform"] == platform
            assert result["browser"] == browser

    def test_missing_screen_returns_none(self):
        result = parse_device_info(json.dumps({"platform": "Win32", "userAgent": "Chrome/120"}))
        assert result["screen"] is None


class TestFingerprintHashContract:
    def test_same_input_same_output(self):
        payload = make_fp_json()
        assert hash_fingerprint(payload) == hash_fingerprint(payload)

    def test_different_inputs_different_outputs(self):
        assert hash_fingerprint(make_fp_json(platform="Win32")) != hash_fingerprint(make_fp_json(platform="MacIntel"))

    def test_returns_string(self):
        assert isinstance(hash_fingerprint("any-string"), str)

    def test_returns_sha256_hex(self):
        result = hash_fingerprint("test")
        assert len(result) == 64
        assert all(char in "0123456789abcdef" for char in result)


class TestSecurityMonitorFingerprintContract:
    def test_get_fingerprint_with_valid_json(self):
        from app.middleware.security_monitor import SecurityMonitorMiddleware

        middleware = SecurityMonitorMiddleware(app=MagicMock())
        request = MagicMock()
        request.headers.get = MagicMock(return_value=make_fp_json())

        result = middleware._get_fingerprint(request)

        assert result is not None
        assert result.get("schema") == "fingerprint-migration-v1"
        assert result.get("kind") == "legacy_structured"
        assert result.get("normalized_summary", {}).get("platform") == "Windows"

    def test_get_fingerprint_returns_none_for_missing_header(self):
        from app.middleware.security_monitor import SecurityMonitorMiddleware

        middleware = SecurityMonitorMiddleware(app=MagicMock())
        request = MagicMock()
        request.headers.get = MagicMock(return_value=None)

        assert middleware._get_fingerprint(request) is None

    def test_get_fingerprint_wraps_hash_string_as_opaque_envelope(self):
        from app.middleware.security_monitor import SecurityMonitorMiddleware

        middleware = SecurityMonitorMiddleware(app=MagicMock())
        request = MagicMock()
        request.headers.get = MagicMock(return_value="k7f2m1")

        result = middleware._get_fingerprint(request)
        assert result == {
            "schema": "fingerprint-migration-v1",
            "kind": "opaque_hash",
            "raw_payload": "k7f2m1",
            "opaque_hash": "k7f2m1",
            "normalized_summary": None,
            "normalized_matching": None,
            "quality": "opaque",
        }
