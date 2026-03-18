"""Tests for security_scan.py — marketplace security scanning."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile

import pytest

# Import the module under test
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from security_scan import scan_for_secrets, scan_urls, REPO_ROOT


class TestSecretDetection:

    def test_detects_openai_key(self, tmp_path):
        content = 'api_key = "sk-abc123def456ghi789jkl012mno345pqr678stu901"'
        findings = scan_for_secrets(content, tmp_path / "test.json")
        assert len(findings) > 0

    def test_detects_anthropic_key(self, tmp_path):
        content = 'key: "sk-ant-abc123def456ghi789jkl012"'
        findings = scan_for_secrets(content, tmp_path / "test.json")
        assert len(findings) > 0

    def test_detects_github_token(self, tmp_path):
        content = 'token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"'
        findings = scan_for_secrets(content, tmp_path / "test.json")
        assert len(findings) > 0

    def test_detects_aws_key(self, tmp_path):
        content = 'aws_key = "AKIAIOSFODNN7EXAMPAA"'
        findings = scan_for_secrets(content, tmp_path / "test.json")
        assert len(findings) > 0

    def test_detects_slack_token(self, tmp_path):
        content = 'slack = "xoxb-FAKE0TOKEN0FOR0TESTING0ONLY00"'
        findings = scan_for_secrets(content, tmp_path / "test.json")
        assert len(findings) > 0

    def test_detects_private_key(self, tmp_path):
        content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEow..."
        findings = scan_for_secrets(content, tmp_path / "test.pem")
        assert len(findings) > 0

    def test_ignores_placeholder_keys(self, tmp_path):
        content = 'api_key = "your-api-key-here"'
        findings = scan_for_secrets(content, tmp_path / "test.json")
        assert len(findings) == 0

    def test_ignores_example_keys(self, tmp_path):
        content = 'token = "example-token-placeholder-value"'
        findings = scan_for_secrets(content, tmp_path / "test.json")
        assert len(findings) == 0

    def test_clean_content_passes(self, tmp_path):
        content = '{"id": "test", "title": "My Skill", "description": "Does things"}'
        findings = scan_for_secrets(content, tmp_path / "test.json")
        assert len(findings) == 0


class TestURLScanning:

    def test_detects_javascript_uri(self, tmp_path):
        data = {"demo_url": "javascript:alert(1)"}
        findings = scan_urls(data, tmp_path / "manifest.json")
        assert len(findings) > 0

    def test_detects_data_uri(self, tmp_path):
        data = {"source": "data:text/html,<script>alert(1)</script>"}
        findings = scan_urls(data, tmp_path / "manifest.json")
        assert len(findings) > 0

    def test_detects_file_uri(self, tmp_path):
        data = {"repository": "file:///etc/passwd"}
        findings = scan_urls(data, tmp_path / "manifest.json")
        assert len(findings) > 0

    def test_allows_https_urls(self, tmp_path):
        data = {"repository": "https://github.com/example/repo"}
        findings = scan_urls(data, tmp_path / "manifest.json")
        assert len(findings) == 0

    def test_allows_empty_urls(self, tmp_path):
        data = {"demo_url": ""}
        findings = scan_urls(data, tmp_path / "manifest.json")
        assert len(findings) == 0


class TestExistingListingsSecurity:
    """Verify all existing listings pass security scanning."""

    def test_no_security_issues_in_repo(self):
        """Run the full scan and ensure no issues."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/security_scan.py", "--strict"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Security scan found issues:\n{result.stdout}"
