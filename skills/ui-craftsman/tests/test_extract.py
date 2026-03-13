# skills/ui-craftsman/tests/test_extract.py
"""Tests for extract.py — classify_aesthetic and token parsing."""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from extract import classify_aesthetic, DEFAULT_TOKENS


def test_terminal_pro_black_bg():
    tokens = {**DEFAULT_TOKENS, "bg_primary": "#000000"}
    assert classify_aesthetic(tokens) == "terminal-pro"


def test_terminal_pro_near_black():
    tokens = {**DEFAULT_TOKENS, "bg_primary": "#0a0a0a"}
    assert classify_aesthetic(tokens) == "terminal-pro"


def test_bold_brand_via_gradients():
    tokens = {**DEFAULT_TOKENS, "bg_primary": "#ffffff", "uses_gradients": True}
    assert classify_aesthetic(tokens) == "bold-brand"


def test_data_rich_via_sidebar():
    tokens = {**DEFAULT_TOKENS, "bg_primary": "#0f1117", "nav_pattern": "sidebar"}
    assert classify_aesthetic(tokens) == "data-rich"


def test_minimal_light_white_bg():
    tokens = {**DEFAULT_TOKENS, "bg_primary": "#ffffff"}
    assert classify_aesthetic(tokens) == "minimal-light"


def test_enterprise_fallback():
    tokens = {**DEFAULT_TOKENS, "bg_primary": "#1a2540"}
    assert classify_aesthetic(tokens) == "enterprise"


def test_default_tokens_has_required_keys():
    required = [
        "bg_primary", "bg_secondary", "fg_primary", "fg_secondary",
        "accent", "font_sans", "font_mono", "border_radius",
        "spacing_unit", "uses_gradients", "nav_pattern", "card_style",
    ]
    for key in required:
        assert key in DEFAULT_TOKENS, f"Missing key: {key}"
