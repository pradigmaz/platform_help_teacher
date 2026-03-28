import hashlib
import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.audit.suspicion.fingerprint import calculate_fingerprint_score, detect_inconsistencies
from app.fingerprint_contract import (
    build_audit_fingerprint,
    build_device_info,
    build_session_device_summary,
    compute_fingerprint_digest,
    parse_fingerprint_payload,
)
from app.services.device_service import hash_fingerprint
from app.services.device_service import register_or_update_device
from app.services.security_monitor.detector import SecurityDetector


def test_parse_fingerprint_payload_returns_none_for_missing_inputs() -> None:
    assert parse_fingerprint_payload(None) is None
    assert parse_fingerprint_payload("") is None
    assert parse_fingerprint_payload("{}") is None


def test_parse_fingerprint_payload_wraps_legacy_json_in_envelope() -> None:
    payload = json.dumps(
        {
            "platform": "Win32",
            "userAgent": "Mozilla/5.0 Chrome/122.0",
            "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
            "webgl": {"vendor": "Intel", "renderer": "Iris"},
            "hardwareConcurrency": 8,
            "canvas": "legacy-canvas",
        }
    )

    result = parse_fingerprint_payload(payload)

    assert result is not None
    assert result["schema"] == "fingerprint-migration-v1"
    assert result["kind"] == "legacy_structured"
    assert result["raw_payload"]["platform"] == "Win32"
    assert result["normalized_summary"] == {
        "platform": "Windows",
        "browser": "Chrome",
        "screen": {"width": 1920, "height": 1080},
    }
    assert result["normalized_matching"]["platform"] == "Win32"
    assert result["normalized_matching"]["hardwareConcurrency"] == 8


def test_parse_fingerprint_payload_wraps_opaque_hash_in_envelope() -> None:
    result = parse_fingerprint_payload("k7f2m1")

    assert result is not None
    assert result["kind"] == "opaque_hash"
    assert result["opaque_hash"] == "k7f2m1"
    assert result["normalized_summary"] is None
    assert result["normalized_matching"] is None


def test_parse_fingerprint_payload_accepts_normalized_replacement() -> None:
    replacement = {
        "schema": "fingerprint-migration-v1",
        "kind": "normalized_replacement",
        "summary": {
            "platform": "Windows",
            "browser": "Chrome",
            "screen": {"width": 1920, "height": 1080},
        },
        "matching": {
            "platform": "Win32",
            "hardwareConcurrency": 8,
            "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
            "webgl": {"vendor": "Intel", "renderer": "Iris"},
            "canvas": "replacement-canvas",
        },
        "client": {"userAgent": "Mozilla/5.0 Chrome/122.0"},
        "raw": {"vendorPayload": True},
    }

    result = parse_fingerprint_payload(replacement)

    assert result is not None
    assert result["kind"] == "normalized_replacement"
    assert result["raw_payload"] == {"vendorPayload": True}
    assert result["normalized_summary"]["browser"] == "Chrome"
    assert result["normalized_matching"]["userAgent"] == "Mozilla/5.0 Chrome/122.0"


def test_parse_fingerprint_payload_accepts_browser_family_summary() -> None:
    replacement = {
        "schema": "fingerprint-migration-v1",
        "kind": "normalized_replacement",
        "summary": {
            "platform_family": "Windows",
            "browser_family": "Chrome",
            "screen": {"width": 1920, "height": 1080},
        },
    }

    result = parse_fingerprint_payload(replacement)

    assert result is not None
    assert result["normalized_summary"] == {
        "platform": "Windows",
        "browser": "Chrome",
        "screen": {"width": 1920, "height": 1080},
    }


def test_compute_fingerprint_digest_is_stable_across_json_key_order() -> None:
    payload_a = json.dumps(
        {
            "platform": "Win32",
            "userAgent": "Mozilla/5.0 Chrome/122.0",
            "screen": {"width": 1920, "height": 1080},
        }
    )
    payload_b = json.dumps(
        {
            "screen": {"height": 1080, "width": 1920},
            "userAgent": "Mozilla/5.0 Chrome/122.0",
            "platform": "Win32",
        }
    )

    assert compute_fingerprint_digest(payload_a) == compute_fingerprint_digest(payload_b)


def test_compute_fingerprint_digest_returns_none_for_missing_envelope() -> None:
    missing = {"schema": "fingerprint-migration-v1", "kind": "missing"}

    assert compute_fingerprint_digest(missing) is None


def test_device_hash_keeps_legacy_raw_header_compatibility() -> None:
    payload = json.dumps(
        {
            "platform": "Win32",
            "userAgent": "Mozilla/5.0 Chrome/122.0",
            "screen": {"width": 1920, "height": 1080},
        }
    )

    assert hash_fingerprint(payload) == hashlib.sha256(payload.encode()).hexdigest()


def test_device_hash_skips_missing_envelope() -> None:
    missing = json.dumps({"schema": "fingerprint-migration-v1", "kind": "missing"})

    assert hash_fingerprint(missing) == ""


def test_security_hash_keeps_legacy_mapping_compatibility() -> None:
    payload = {
        "platform": "Win32",
        "userAgent": "Mozilla/5.0 Chrome/122.0",
        "screen": {"width": 1920, "height": 1080},
    }

    detector = SecurityDetector()

    assert detector._hash_fingerprint(payload) == hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()[:16]


def test_security_hash_keeps_opaque_mapping_compatibility() -> None:
    detector = SecurityDetector()

    assert detector._hash_fingerprint(
        {"schema": "fingerprint-migration-v1", "kind": "opaque_hash", "opaque_hash": "opaque-token"}
    ) == hashlib.sha256(json.dumps({"hash": "opaque-token"}, sort_keys=True).encode()).hexdigest()[:16]


def test_security_hash_skips_missing_envelope() -> None:
    detector = SecurityDetector()

    assert detector._hash_fingerprint({"schema": "fingerprint-migration-v1", "kind": "missing"}) == ""


@pytest.mark.asyncio
async def test_register_or_update_device_skips_missing_envelope() -> None:
    db = AsyncMock()
    missing = json.dumps({"schema": "fingerprint-migration-v1", "kind": "missing"})

    assert await register_or_update_device(db, uuid4(), missing) is None
    db.commit.assert_not_called()


def test_build_session_and_device_info_use_canonical_summary() -> None:
    replacement = {
        "schema": "fingerprint-migration-v1",
        "kind": "normalized_replacement",
        "normalized_summary": {
            "platform": "Windows",
            "browser": "Chrome",
            "screen": {"width": 1920, "height": 1080},
        },
    }

    assert build_device_info(replacement) == {
        "platform": "Windows",
        "browser": "Chrome",
        "screen": "1920×1080",
    }
    assert build_session_device_summary(replacement) == {
        "platform": "Windows",
        "browser": "Chrome",
        "userAgent": "Chrome",
        "screen": {"width": 1920, "height": 1080},
    }


def test_build_audit_fingerprint_preserves_opaque_hash() -> None:
    result = build_audit_fingerprint("opaque-token")

    assert result is not None
    assert result["kind"] == "opaque_hash"
    assert result["opaque_hash"] == "opaque-token"

    wrapped = build_audit_fingerprint({"hash": "opaque-token"})
    assert wrapped is not None
    assert wrapped["kind"] == "opaque_hash"


def test_suspicion_helpers_short_circuit_on_opaque_envelope() -> None:
    opaque = parse_fingerprint_payload("opaque-token")

    assert calculate_fingerprint_score(opaque, opaque) == (0, [])
    assert detect_inconsistencies(opaque) == []


def test_suspicion_helpers_accept_normalized_replacement_payload() -> None:
    replacement = parse_fingerprint_payload(
        {
            "schema": "fingerprint-migration-v1",
            "kind": "normalized_replacement",
            "summary": {"platform": "Windows", "browser": "Chrome"},
            "matching": {
                "platform": "Win32",
                "hardwareConcurrency": 8,
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
                "webgl": {"vendor": "Intel", "renderer": "Iris"},
                "canvas": "shared-canvas",
            },
            "client": {"userAgent": "Mozilla/5.0 Chrome/122.0"},
        }
    )

    score, matches = calculate_fingerprint_score(replacement, replacement)

    assert score > 0
    assert {"webgl", "screen", "platform", "canvas"}.issubset(set(matches))
