"""
Bug condition exploration tests for sanitize_lexical_content().

Property 1: Fault Condition — text nodes with <, >, & must be preserved as-is.
These tests MUST FAIL on unfixed code (failure confirms the bug exists).
After the fix is applied, these tests MUST PASS.
"""
import sys
import os
import importlib.util

# Импортируем html_sanitizer напрямую, минуя app/utils/__init__.py
# который тянет всё приложение включая БД-зависимости
_mod_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'utils', 'html_sanitizer.py')
_spec = importlib.util.spec_from_file_location("html_sanitizer", _mod_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sanitize_lexical_content = _mod.sanitize_lexical_content

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


# Strategy: strings containing at least one of <, >, &
# Используем flatmap чтобы гарантировать наличие спецсимвола без filter()
special_chars = st.one_of(
    st.just('<'),
    st.just('>'),
    st.just('&'),
    st.builds(
        lambda prefix, char, suffix: prefix + char + suffix,
        prefix=st.text(alphabet=st.characters(blacklist_characters='<>&', blacklist_categories=('Cs', 'Cc')), max_size=20),
        char=st.sampled_from(['<', '>', '&']),
        suffix=st.text(alphabet=st.characters(blacklist_characters='<>&', blacklist_categories=('Cs', 'Cc')), max_size=20),
    ),
)


@given(value=special_chars)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
def test_text_node_with_special_chars_preserved(value):
    """Property 1: text nodes with <, >, & must be preserved as-is (not HTML-escaped)."""
    result = sanitize_lexical_content({"text": value})
    assert result["text"] == value, (
        f"Expected text to be preserved as-is, but got HTML-escaped result.\n"
        f"Input:    {value!r}\n"
        f"Expected: {value!r}\n"
        f"Got:      {result['text']!r}"
    )


def test_greater_than_preserved():
    """sales > 1000 must not become sales &gt; 1000"""
    result = sanitize_lexical_content({"text": "sales > 1000"})
    assert result["text"] == "sales > 1000", f"Got: {result['text']!r}"


def test_less_than_preserved():
    """i < n must not become i &lt; n"""
    result = sanitize_lexical_content({"text": "i < n"})
    assert result["text"] == "i < n", f"Got: {result['text']!r}"


def test_ampersand_preserved():
    """a && b must not become a &amp;&amp; b"""
    result = sanitize_lexical_content({"text": "a && b"})
    assert result["text"] == "a && b", f"Got: {result['text']!r}"


def test_complex_predicate_preserved():
    """30 > 18 && 35000 >= 30000 must be preserved"""
    result = sanitize_lexical_content({"text": "30 > 18 && 35000 >= 30000"})
    assert result["text"] == "30 > 18 && 35000 >= 30000", f"Got: {result['text']!r}"


def test_scores_length_preserved():
    """i < scores.Length must be preserved"""
    result = sanitize_lexical_content({"text": "i < scores.Length"})
    assert result["text"] == "i < scores.Length", f"Got: {result['text']!r}"


def test_no_double_encoding():
    """Calling sanitize_lexical_content twice must produce same result as once (no double-encoding)."""
    content = {"text": "a > b && c < d"}
    once = sanitize_lexical_content(content)
    twice = sanitize_lexical_content(once)
    assert once == twice, (
        f"Double-encoding detected!\n"
        f"After 1st call: {once['text']!r}\n"
        f"After 2nd call: {twice['text']!r}"
    )
