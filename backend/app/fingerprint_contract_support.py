"""Internal helpers for fingerprint migration compatibility."""

from __future__ import annotations

import json
from typing import Any

FINGERPRINT_SCHEMA = "fingerprint-migration-v1"
FINGERPRINT_KIND_MISSING = "missing"
FINGERPRINT_KIND_OPAQUE = "opaque_hash"
FINGERPRINT_KIND_LEGACY = "legacy_structured"
FINGERPRINT_KIND_REPLACEMENT = "normalized_replacement"

def classify_fingerprint_payload(parsed: Any, *, raw_header: str | None = None) -> dict[str, Any]:
    if isinstance(parsed, dict):
        if parsed.get("schema") == FINGERPRINT_SCHEMA:
            return normalize_existing_envelope(parsed)
        return build_legacy_envelope(parsed)
    return build_opaque_envelope(raw_header or stable_stringify(parsed), parsed)


def build_legacy_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    summary = build_legacy_summary(payload)
    matching = build_legacy_matching(payload)
    opaque_hash = non_empty_string(payload.get("hash") or payload.get("opaque_hash"))
    if opaque_hash and summary is None and matching is None:
        return build_opaque_envelope(opaque_hash, payload)
    return build_envelope(
        kind=FINGERPRINT_KIND_LEGACY,
        raw_payload=payload,
        summary=summary,
        matching=matching,
        opaque_hash=None,
    )

def normalize_existing_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    kind = str(payload.get("kind") or FINGERPRINT_KIND_REPLACEMENT)
    raw_payload = payload.get("raw_payload")
    if raw_payload is None and "raw" in payload:
        raw_payload = payload.get("raw")

    if kind == FINGERPRINT_KIND_MISSING:
        return build_envelope(
            kind=kind,
            raw_payload=raw_payload,
            summary=None,
            matching=None,
            opaque_hash=None,
        )

    summary = normalize_summary(payload.get("normalized_summary") or payload.get("summary"))
    matching = normalize_matching(payload.get("normalized_matching") or payload.get("matching"), payload.get("client"))
    opaque_hash = non_empty_string(payload.get("opaque_hash") or payload.get("hash"))

    if kind == FINGERPRINT_KIND_LEGACY and matching is None and isinstance(raw_payload, dict):
        matching = build_legacy_matching(raw_payload)
    if kind == FINGERPRINT_KIND_LEGACY and summary is None and isinstance(raw_payload, dict):
        summary = build_legacy_summary(raw_payload)
    if kind == FINGERPRINT_KIND_REPLACEMENT and raw_payload is None:
        raw_payload = payload
    if kind == FINGERPRINT_KIND_OPAQUE and not opaque_hash:
        opaque_hash = stable_stringify(raw_payload) if raw_payload is not None else None

    return build_envelope(
        kind=kind,
        raw_payload=raw_payload,
        summary=summary,
        matching=matching,
        opaque_hash=opaque_hash,
    )

def build_opaque_envelope(raw_value: str, raw_payload: Any) -> dict[str, Any]:
    return build_envelope(
        kind=FINGERPRINT_KIND_OPAQUE,
        raw_payload=raw_payload,
        summary=None,
        matching=None,
        opaque_hash=raw_value,
    )


def build_envelope(
    *,
    kind: str,
    raw_payload: Any,
    summary: dict[str, Any] | None,
    matching: dict[str, Any] | None,
    opaque_hash: str | None,
) -> dict[str, Any]:
    return {
        "schema": FINGERPRINT_SCHEMA,
        "kind": kind,
        "raw_payload": raw_payload,
        "opaque_hash": opaque_hash,
        "normalized_summary": summary,
        "normalized_matching": matching,
        "quality": compute_quality(kind, summary, matching, opaque_hash),
    }


def compute_quality(
    kind: str,
    summary: dict[str, Any] | None,
    matching: dict[str, Any] | None,
    opaque_hash: str | None,
) -> str:
    if kind == FINGERPRINT_KIND_MISSING:
        return "missing"
    if opaque_hash:
        return "opaque"
    if matching:
        return "full"
    if summary:
        return "summary_only"
    return "reduced"


def build_legacy_summary(payload: dict[str, Any]) -> dict[str, Any] | None:
    platform = normalize_platform_family(payload.get("platform"))
    browser = detect_browser_family(payload.get("userAgent"))
    screen = normalize_screen(payload.get("screen"), include_color_depth=False)

    summary: dict[str, Any] = {}
    if platform:
        summary["platform"] = platform
    if browser:
        summary["browser"] = browser
    if screen:
        summary["screen"] = {"width": screen["width"], "height": screen["height"]}
    return summary or None


def build_legacy_matching(payload: dict[str, Any]) -> dict[str, Any] | None:
    screen = normalize_screen(payload.get("screen"), include_color_depth=True)
    webgl = normalize_webgl(payload.get("webgl"))
    canvas = non_empty_string(payload.get("canvas"))
    platform = non_empty_string(payload.get("platform"))
    user_agent = non_empty_string(payload.get("userAgent"))
    hardware_concurrency = positive_int(payload.get("hardwareConcurrency"))

    matching: dict[str, Any] = {}
    if platform:
        matching["platform"] = platform
    if hardware_concurrency is not None:
        matching["hardwareConcurrency"] = hardware_concurrency
    if screen:
        matching["screen"] = screen
    if webgl:
        matching["webgl"] = webgl
    if canvas:
        matching["canvas"] = canvas
    if user_agent:
        matching["userAgent"] = user_agent
    return matching or None


def normalize_summary(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    platform = normalize_platform_family(payload.get("platform") or payload.get("platform_family"))
    browser = detect_browser_family(payload.get("browser") or payload.get("browser_family") or payload.get("userAgent"))
    screen = normalize_screen(payload.get("screen"), include_color_depth=False)

    summary: dict[str, Any] = {}
    if platform:
        summary["platform"] = platform
    if browser:
        summary["browser"] = browser
    if screen:
        summary["screen"] = {"width": screen["width"], "height": screen["height"]}
    return summary or None


def normalize_matching(payload: Any, client: Any = None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        payload = {}
    client_dict = client if isinstance(client, dict) else {}

    platform = non_empty_string(payload.get("platform"))
    hardware_concurrency = positive_int(payload.get("hardwareConcurrency"))
    screen = normalize_screen(payload.get("screen"), include_color_depth=True)
    webgl = normalize_webgl(payload.get("webgl"))
    canvas = non_empty_string(payload.get("canvas") or payload.get("canvas_hash"))
    user_agent = non_empty_string(payload.get("userAgent") or client_dict.get("userAgent"))

    matching: dict[str, Any] = {}
    if platform:
        matching["platform"] = platform
    if hardware_concurrency is not None:
        matching["hardwareConcurrency"] = hardware_concurrency
    if screen:
        matching["screen"] = screen
    if webgl:
        matching["webgl"] = webgl
    if canvas:
        matching["canvas"] = canvas
    if user_agent:
        matching["userAgent"] = user_agent
    return matching or None


def normalize_platform_family(value: Any) -> str | None:
    platform = non_empty_string(value)
    if not platform:
        return None
    if "Win" in platform:
        return "Windows"
    if "Mac" in platform:
        return "macOS"
    if "Linux" in platform:
        return "Linux"
    if "Android" in platform:
        return "Android"
    if "iPhone" in platform or "iPad" in platform:
        return "iOS"
    return platform


def detect_browser_family(value: Any) -> str | None:
    user_agent = non_empty_string(value)
    if not user_agent:
        return None
    if user_agent == "Edge":
        return "Edge"
    if "Chrome" in user_agent and "Edg" not in user_agent:
        return "Chrome"
    if "Firefox" in user_agent:
        return "Firefox"
    if "Safari" in user_agent and "Chrome" not in user_agent:
        return "Safari"
    if "Edg" in user_agent:
        return "Edge"
    if "Opera" in user_agent or "OPR" in user_agent:
        return "Opera"
    return user_agent if user_agent in {"Chrome", "Firefox", "Safari", "Edge", "Opera"} else None


def normalize_screen(value: Any, *, include_color_depth: bool) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    width = positive_int(value.get("width"))
    height = positive_int(value.get("height"))
    if width is None or height is None:
        return None

    screen: dict[str, Any] = {"width": width, "height": height}
    if include_color_depth:
        screen["colorDepth"] = positive_int(value.get("colorDepth")) or 24
    return screen


def normalize_webgl(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    vendor = non_empty_string(value.get("vendor"))
    renderer = non_empty_string(value.get("renderer"))
    if not vendor and not renderer:
        return None
    webgl: dict[str, Any] = {}
    if vendor:
        webgl["vendor"] = vendor
    if renderer:
        webgl["renderer"] = renderer
    return webgl or None


def positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float) and value.is_integer():
        return int(value) if value > 0 else None
    if isinstance(value, str) and value.isdigit():
        parsed = int(value)
        return parsed if parsed > 0 else None
    return None


def format_screen(screen: Any) -> str | None:
    if not isinstance(screen, dict):
        return None
    width = screen.get("width")
    height = screen.get("height")
    if width and height:
        return f"{width}×{height}"
    return None

def non_empty_string(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None

def stable_stringify(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError):
        return str(value)
