"""Shared helpers for device binding tests."""

import json
from uuid import uuid4

from unittest.mock import MagicMock


def make_fp_json(**overrides) -> str:
    base = {
        "platform": "Win32",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
        "screen": {"width": 1920, "height": 1080},
    }
    base.update(overrides)
    return json.dumps(base)


def make_mock_device(device_id=None, user_id=None, fp_hash="testhash", is_trusted=False):
    device = MagicMock()
    device.id = device_id or uuid4()
    device.user_id = user_id or uuid4()
    device.fingerprint_hash = fp_hash
    device.is_trusted = is_trusted
    return device
