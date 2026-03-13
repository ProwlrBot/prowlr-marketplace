#!/usr/bin/env python3
"""serve.py <file> [--gallery <f1> <f2> ...] — local preview server on 127.0.0.1."""
from __future__ import annotations

import argparse
import html as _html
import http.server
import os
import socket
import sys
from pathlib import Path

_PORT_RANGE = range(8400, 8501)
_HOST = "127.0.0.1"


def _find_free_port() -> int:
    for port in _PORT_RANGE:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((_HOST, port))
                return port
            except OSError:
                continue
    print("No free port in range 8400-8500", file=sys.stderr)
    sys.exit(1)


def _build_gallery_html(files: list[Path]) -> str:
    cards = ""
    for f in files:
        label = _html.escape(f.stem)
        cards += (
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:8px">'
            f'<div style="font-family:monospace;font-size:11px;color:#888">{label}</div>'
            f'<iframe src="{f.name}" width="300" height="200"'
            f' style="border:1px solid #1f1f1f;border-radius:8px"'
            f" loading=\"lazy\"></iframe>"
            f"</div>"
        )

    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<title>UI Craftsman — Direction Gallery</title>\n"
        "<style>\n"
        "  body{background:#0a0a0a;margin:0;padding:24px;font-family:system-ui}\n"
        "  h1{color:#e2e2e2;font-size:16px;margin:0 0 24px}\n"
        "  .grid{display:flex;flex-wrap:wrap;gap:24px}\n"
        "</style>\n</head>\n<body>\n"
        "<h1>Pick a direction</h1>\n"
        f'<div class="grid">{cards}</div>\n'
        "</body>\n</html>"
    )


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class _GalleryHandler(_QuietHandler):
    _gallery_html: str = ""

    def do_GET(self):
        if self.path in ("/", ""):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            data = self._gallery_html.encode("utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            super().do_GET()


def serve_single(file: Path) -> None:
    port = _find_free_port()
    os.chdir(file.parent)
    with http.server.HTTPServer((_HOST, port), _QuietHandler) as httpd:
        print(f"http://{_HOST}:{port}/{file.name}", flush=True)
        httpd.serve_forever()


def serve_gallery(files: list[Path]) -> None:
    port = _find_free_port()
    os.chdir(files[0].parent)
    gallery_html = _build_gallery_html(files)

    class Handler(_GalleryHandler):
        pass
    Handler._gallery_html = gallery_html

    with http.server.HTTPServer((_HOST, port), Handler) as httpd:
        print(f"http://{_HOST}:{port}/", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("--gallery", nargs="+")
    args = parser.parse_args()

    if args.gallery:
        serve_gallery([Path(f).resolve() for f in args.gallery])
    elif args.file:
        serve_single(Path(args.file).resolve())
    else:
        print("Usage: serve.py <file> | --gallery <f1> <f2> ...", file=sys.stderr)
        sys.exit(1)
