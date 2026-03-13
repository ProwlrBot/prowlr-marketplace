#!/usr/bin/env python3
"""validate.py <url> — exit 0 if safe to fetch, exit 1 if blocked."""
from __future__ import annotations

import ipaddress
import re
import socket
import sys
from urllib.parse import urlparse

_PRIVATE_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("::ffff:127.0.0.0/104"),
]
# NOTE: DNS rebinding attacks (where a hostname first resolves to a public IP
# then re-resolves to a private one) are a known limitation in v1. A full fix
# requires binding the resolved IP at fetch time (not just at validation time).

_HEX_RE = re.compile(r"^0x[0-9a-fA-F]+$")
_OCT_RE = re.compile(r"^0[0-7]+$")
_DEC_RE = re.compile(r"^\d+$")


def _block(reason: str) -> None:
    print(f"BLOCKED: {reason}", file=sys.stderr)
    sys.exit(1)


def _parse_encoded_ip(host: str) -> str | None:
    """Return dotted-decimal string if host is hex/octal/decimal encoded IP."""
    host = host.strip("[]")

    # Single-component hex: 0x7f000001
    if _HEX_RE.match(host):
        val = int(host, 16)
        return str(ipaddress.IPv4Address(val))

    # Dotted-octal: 0177.0.0.1 — each component may be octal
    if "." in host:
        parts = host.split(".")
        if len(parts) == 4 and all(_OCT_RE.match(p) for p in parts):
            try:
                octets = [int(p, 8) for p in parts]
                return ".".join(str(o) for o in octets)
            except ValueError:
                pass
        return None  # dotted but not dotted-octal — leave to DNS

    # Single-component octal: 0177777 (no dots)
    if _OCT_RE.match(host):
        try:
            val = int(host, 8)
            return str(ipaddress.IPv4Address(val))
        except (ValueError, ipaddress.AddressValueError):
            pass

    # Single-component decimal: 2130706433
    if _DEC_RE.match(host):
        try:
            return str(ipaddress.IPv4Address(int(host)))
        except (ValueError, ipaddress.AddressValueError):
            pass

    return None


def _check_ip(ip_str: str) -> None:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return
    # Unpack IPv4-mapped IPv6 (::ffff:x.x.x.x) to plain IPv4 for range checks
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped
    for net in _PRIVATE_NETS:
        try:
            if addr in net:
                _block(f"{ip_str} is in private range {net}")
        except TypeError:
            pass


def validate(url: str) -> None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.hostname:
        _block("URL must include scheme (https://) and hostname")

    host = parsed.hostname.strip("[]")

    if host in ("localhost",):
        _block("localhost is not allowed")

    decoded = _parse_encoded_ip(host)
    if decoded:
        _check_ip(decoded)

    try:
        addr = ipaddress.ip_address(host)
        _check_ip(str(addr))
        return
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        _block(f"DNS resolution failed: {exc}")
        return

    for _, _, _, _, sockaddr in infos:
        ip_str = sockaddr[0]
        _check_ip(ip_str)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate.py <url>", file=sys.stderr)
        sys.exit(1)
    validate(sys.argv[1])
