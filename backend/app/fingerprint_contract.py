"""Shared fingerprint compatibility contract for the migration period."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.fingerprint_contract_support import (
    FINGERPRINT_KIND_MISSING,
    FINGERPRINT_KIND_OPAQUE,
    FINGERPRINT_KIND_REPLACEMENT,
    FINGERPRINT_SCHEMA,
    build_legacy_envelope,
    build_opaque_envelope,
    classify_fingerprint_payload,
    compute_quality,
    format_screen,
    normalize_existing_envelope,
)


def is_fingerprint_envelope(value: Any) -> bool:
    return isinstance(value, dict) and value.get("schema") == FINGERPRINT_SCHEMA and isinstance(value.get("kind"), str)


def parse_fingerprint_payload(value: str | dict[str, Any] | None) -> dict[str, Any] | None:
    """Parse raw header/string/dict into a canonical fingerprint envelope."""
    if value is None:
        return None

    if isinstance(value, str):
        raw_header = value.strip()
        if not raw_header or raw_header == "{}":
            return None
        try:
            parsed = json.loads(raw_header)
        except (json.JSONDecodeError, TypeError):
            return build_opaque_envelope(raw_header, raw_header)
        return classify_fingerprint_payload(parsed, raw_header=raw_header)

    if isinstance(value, dict):
        if is_fingerprint_envelope(value):
            return normalize_existing_envelope(value)
        return build_legacy_envelope(value)

    return build_opaque_envelope(str(value), value)


def build_audit_fingerprint(value: str | dict[str, Any] | None) -> dict[str, Any] | None:
    """Build the JSON-safe fingerprint payload stored in audit records."""
    return parse_fingerprint_payload(value)


def build_compact_audit_fingerprint(value: str | dict[str, Any] | None) -> dict[str, Any] | None:
    """Build a compact fingerprint envelope for audit storage without raw payload."""
    envelope = parse_fingerprint_payload(value)
    if not envelope:
        return None

    summary = envelope.get("normalized_summary")
    normalized_summary = summary if isinstance(summary, dict) and summary else None

    matching = envelope.get("normalized_matching")
    normalized_matching = matching if isinstance(matching, dict) and matching else None

    opaque_hash = envelope.get("opaque_hash")
    normalized_opaque_hash = opaque_hash if isinstance(opaque_hash, str) and opaque_hash else None

    kind = envelope.get("kind")
    if kind == FINGERPRINT_KIND_MISSING:
        normalized_kind = FINGERPRINT_KIND_MISSING
    elif kind == FINGERPRINT_KIND_OPAQUE:
        normalized_kind = FINGERPRINT_KIND_OPAQUE
    else:
        normalized_kind = FINGERPRINT_KIND_REPLACEMENT

    return {
        "schema": FINGERPRINT_SCHEMA,
        "kind": normalized_kind,
        "opaque_hash": normalized_opaque_hash,
        "normalized_summary": normalized_summary,
        "normalized_matching": normalized_matching,
        "quality": compute_quality(
            normalized_kind,
            normalized_summary,
            normalized_matching,
            normalized_opaque_hash,
        ),
    }


def get_fingerprint_summary(value: str | dict[str, Any] | None) -> dict[str, Any] | None:
    envelope = parse_fingerprint_payload(value)
    if not envelope:
        return None
    summary = envelope.get("normalized_summary")
    return summary if isinstance(summary, dict) and summary else None


def get_fingerprint_matching(value: str | dict[str, Any] | None) -> dict[str, Any] | None:
    envelope = parse_fingerprint_payload(value)
    if not envelope:
        return None
    matching = envelope.get("normalized_matching")
    return matching if isinstance(matching, dict) and matching else None


def get_fingerprint_kind(value: str | dict[str, Any] | None) -> str | None:
    envelope = parse_fingerprint_payload(value)
    if not envelope:
        return None
    kind = envelope.get("kind")
    return kind if isinstance(kind, str) else None


def compute_fingerprint_digest(value: str | dict[str, Any] | None) -> str | None:
    envelope = parse_fingerprint_payload(value)
    if not envelope:
        return None
    if envelope.get("kind") == FINGERPRINT_KIND_MISSING:
        return None

    opaque_hash = envelope.get("opaque_hash")
    if isinstance(opaque_hash, str) and opaque_hash:
        digest_payload: dict[str, Any] = {
            "kind": FINGERPRINT_KIND_OPAQUE,
            "opaque_hash": opaque_hash,
        }
    else:
        digest_payload = {
            "kind": envelope.get("kind"),
            "matching": envelope.get("normalized_matching") or {},
            "summary": envelope.get("normalized_summary") or {},
        }

    serialized = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def build_device_info(value: str | dict[str, Any] | None) -> dict[str, Any]:
    summary = get_fingerprint_summary(value) or {}
    screen = summary.get("screen") if isinstance(summary.get("screen"), dict) else None

    return {
        "platform": summary.get("platform") or "Unknown",
        "browser": summary.get("browser") or "Unknown",
        "screen": format_screen(screen),
    }


def build_session_device_summary(value: str | dict[str, Any] | None) -> dict[str, object] | None:
    summary = get_fingerprint_summary(value)
    if not summary:
        return None

    session_summary: dict[str, object] = {
        "platform": summary.get("platform") or "",
        "browser": summary.get("browser") or "",
        "userAgent": summary.get("browser") or "",
        "screen": {},
    }

    screen = summary.get("screen")
    if isinstance(screen, dict):
        width = screen.get("width")
        height = screen.get("height")
        if width and height:
            session_summary["screen"] = {"width": width, "height": height}

    return session_summary
