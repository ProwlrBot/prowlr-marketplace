# skills/ui-craftsman/tests/test_validate.py
import subprocess
import sys

SCRIPT = "skills/ui-craftsman/scripts/validate.py"

def _run(url: str) -> int:
    result = subprocess.run(
        [sys.executable, SCRIPT, url],
        capture_output=True,
    )
    return result.returncode


# --- blocked cases ---
def test_blocks_localhost():
    assert _run("http://127.0.0.1/secret") == 1

def test_blocks_loopback_hostname():
    assert _run("http://localhost/secret") == 1

def test_blocks_private_10():
    assert _run("http://10.0.0.1/secret") == 1

def test_blocks_private_172():
    assert _run("http://172.16.0.1/secret") == 1

def test_blocks_private_192():
    assert _run("http://192.168.1.1/secret") == 1

def test_blocks_metadata_ip():
    assert _run("http://169.254.169.254/latest/meta-data/") == 1

def test_blocks_hex_encoded_ip():
    assert _run("http://0x7f000001/secret") == 1

def test_blocks_decimal_encoded_ip():
    # 2130706433 == 127.0.0.1
    assert _run("http://2130706433/secret") == 1

def test_blocks_octal_encoded_ip():
    assert _run("http://0177.0.0.1/secret") == 1

def test_blocks_ipv6_loopback():
    assert _run("http://[::1]/secret") == 1

def test_blocks_ipv6_link_local():
    assert _run("http://[fe80::1]/secret") == 1

def test_blocks_zero_address():
    assert _run("http://0.0.0.0/secret") == 1

def test_blocks_ipv4_mapped_ipv6():
    # ::ffff:127.0.0.1 is IPv4-mapped loopback
    assert _run("http://[::ffff:127.0.0.1]/secret") == 1

# --- allowed cases ---
def test_allows_public_https():
    # vercel.com resolves to a public IP — exit 0
    assert _run("https://vercel.com") == 0

def test_allows_public_http():
    assert _run("http://example.com") == 0
