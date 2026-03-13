# skills/ui-craftsman/tests/test_serve.py
import socket
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from pathlib import Path
from serve import _find_free_port, _build_gallery_html, _PORT_RANGE


def test_port_range_bounds():
    assert _PORT_RANGE.start == 8400
    assert _PORT_RANGE.stop == 8501


def test_find_free_port_returns_int_in_range():
    port = _find_free_port()
    assert isinstance(port, int)
    assert port in _PORT_RANGE


def test_find_free_port_is_actually_free():
    port = _find_free_port()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.close()


def test_gallery_html_contains_iframes(tmp_path):
    f1 = tmp_path / "direction-A.html"
    f2 = tmp_path / "direction-B.html"
    f1.write_text("<html>A</html>")
    f2.write_text("<html>B</html>")
    html = _build_gallery_html([f1, f2])
    assert "<iframe" in html
    assert "direction-A.html" in html
    assert "direction-B.html" in html


def test_gallery_html_is_self_contained(tmp_path):
    f = tmp_path / "x.html"
    f.write_text("<html>X</html>")
    html = _build_gallery_html([f])
    assert "src=\"https://" not in html
