"""
Preservation property tests for sanitize_lexical_content().

Property 2: Preservation — HTML-nodes and URL-nodes must be sanitized as before.
These tests MUST PASS on both unfixed and fixed code.
"""
import os
import importlib.util

# Импортируем напрямую, минуя app/utils/__init__.py
_mod_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'utils', 'html_sanitizer.py')
_spec = importlib.util.spec_from_file_location("html_sanitizer", _mod_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sanitize_lexical_content = _mod.sanitize_lexical_content

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


# --- HTML-node preservation ---

def test_html_script_tag_stripped():
    """Dangerous <script> tag must be removed from html nodes (bleach strips tag + content)."""
    result = sanitize_lexical_content({"html": "<script>alert(1)</script>"})
    assert "<script>" not in result["html"]
    # bleach with strip=True removes the tag but may keep inner text — key is no executable script tag


def test_html_allowed_tag_preserved():
    """Allowed <p> tag must be preserved in html nodes."""
    result = sanitize_lexical_content({"html": "<p>hello</p>"})
    assert "hello" in result["html"]
    assert "<p>" in result["html"]


def test_html_iframe_stripped():
    """<iframe> must be stripped from html nodes."""
    result = sanitize_lexical_content({"html": '<iframe src="evil.com"></iframe>'})
    assert "<iframe" not in result["html"]


# --- URL-node preservation ---

def test_url_javascript_blocked():
    """javascript: protocol must be blocked."""
    result = sanitize_lexical_content({"url": "javascript:alert(1)"})
    assert result["url"] == "#blocked"


def test_url_vbscript_blocked():
    """vbscript: protocol must be blocked."""
    result = sanitize_lexical_content({"url": "vbscript:msgbox(1)"})
    assert result["url"] == "#blocked"


def test_url_https_preserved():
    """https:// URL must be preserved."""
    result = sanitize_lexical_content({"url": "https://example.com"})
    assert result["url"] == "https://example.com"


def test_url_http_preserved():
    """http:// URL must be preserved."""
    result = sanitize_lexical_content({"url": "http://example.com/path"})
    assert result["url"] == "http://example.com/path"


# --- Text without special chars — unchanged ---

def test_plain_text_unchanged():
    """Text without <, >, & must pass through unchanged."""
    result = sanitize_lexical_content({"text": "hello world"})
    assert result["text"] == "hello world"


def test_empty_text_unchanged():
    """Empty text must pass through unchanged."""
    result = sanitize_lexical_content({"text": ""})
    assert result["text"] == ""


# --- Structural keys pass-through ---

def test_non_text_keys_passed_through():
    """Structural keys (type, format, version) must pass through unchanged."""
    content = {"type": "paragraph", "format": 0, "version": 1}
    result = sanitize_lexical_content(content)
    assert result == content


# --- Recursive traversal ---

def test_nested_dict_traversed():
    """Nested dicts must be recursively processed."""
    content = {"root": {"children": [{"text": "hello"}]}}
    result = sanitize_lexical_content(content)
    assert result["root"]["children"][0]["text"] == "hello"


def test_nested_html_node_sanitized():
    """HTML nodes inside nested structure must be sanitized."""
    content = {"root": {"html": "<script>xss</script>"}}
    result = sanitize_lexical_content(content)
    assert "<script>" not in result["root"]["html"]


# --- Property-based: text without special chars preserved ---

safe_text = st.text(
    alphabet=st.characters(
        blacklist_characters='<>&',
        blacklist_categories=('Cs', 'Cc'),  # исключаем суррогаты и управляющие символы
    ),
    min_size=0,
    max_size=200,
)


@given(value=safe_text)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_pbt_safe_text_unchanged(value):
    """PBT: text without <, >, & must be preserved as-is."""
    result = sanitize_lexical_content({"text": value})
    assert result["text"] == value


# --- Idempotency for non-bug-condition inputs ---

def test_idempotency_html_node():
    """sanitize_lexical_content applied twice to html node = same as once."""
    content = {"html": "<p>hello <b>world</b></p>"}
    once = sanitize_lexical_content(content)
    twice = sanitize_lexical_content(once)
    assert once == twice


def test_idempotency_url_node():
    """sanitize_lexical_content applied twice to url node = same as once."""
    content = {"url": "https://example.com"}
    once = sanitize_lexical_content(content)
    twice = sanitize_lexical_content(once)
    assert once == twice


def test_idempotency_safe_text():
    """sanitize_lexical_content applied twice to safe text = same as once."""
    content = {"text": "hello world"}
    once = sanitize_lexical_content(content)
    twice = sanitize_lexical_content(once)
    assert once == twice
