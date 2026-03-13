# skills/ui-craftsman/tests/test_share.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from share import strip_markup, get_next_seq


def test_strip_markup_removes_tags():
    assert strip_markup("<b>hello</b>") == "hello"


def test_strip_markup_removes_script():
    assert "script" not in strip_markup("<script>alert(1)</script>bad")


def test_strip_markup_truncates_at_280():
    long = "a" * 400
    assert len(strip_markup(long)) <= 280


def test_strip_markup_preserves_plain_text():
    assert strip_markup("hello world") == "hello world"


def test_get_next_seq_empty():
    assert get_next_seq([], "alice", "20260313") == "001"


def test_get_next_seq_one_existing():
    entries = [{"id": "alice-20260313-001"}]
    assert get_next_seq(entries, "alice", "20260313") == "002"


def test_get_next_seq_different_author():
    entries = [{"id": "bob-20260313-001"}]
    assert get_next_seq(entries, "alice", "20260313") == "001"


def test_get_next_seq_different_date():
    entries = [{"id": "alice-20260312-001"}]
    assert get_next_seq(entries, "alice", "20260313") == "001"


def test_get_next_seq_pads_to_three():
    entries = [{"id": f"alice-20260313-{str(i+1).zfill(3)}"} for i in range(9)]
    assert get_next_seq(entries, "alice", "20260313") == "010"
