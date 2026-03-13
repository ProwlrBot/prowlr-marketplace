---
name: test-runner
description: Use this skill when the user wants to run tests, check test coverage, set up a test suite, parse test results, or integrate testing into CI/CD.
---

# Test Runner

## Overview

Runs pytest test suites, measures coverage, parallelizes test execution, and generates summary reports. Parses JUnit XML for CI integration and produces human-readable markdown summaries.

## Run Tests

```bash
# Basic run
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Parallel (install pytest-xdist)
pytest tests/ -n auto          # use all CPU cores
pytest tests/ -n 4             # 4 parallel workers

# Stop on first failure
pytest tests/ -x

# Run only failed tests from last run
pytest tests/ --lf

# Run tests matching a pattern
pytest tests/ -k "auth or login"

# Specific test file/function
pytest tests/test_auth.py::test_login_success
```

## Programmatic Test Execution

```python
import subprocess, json

def run_tests(test_path: str = "tests/", extra_args: list[str] | None = None) -> dict:
    cmd = [
        "python", "-m", "pytest", test_path,
        "--tb=short", "-q",
        f"--junit-xml=test_results.xml",
        "--json-report", "--json-report-file=test_results.json"
    ]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
```

## Parse JUnit XML

```python
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_junit_xml(xml_path: str = "test_results.xml") -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    return {
        "tests":    int(suite.get("tests", 0)),
        "failures": int(suite.get("failures", 0)),
        "errors":   int(suite.get("errors", 0)),
        "skipped":  int(suite.get("skipped", 0)),
        "time_s":   float(suite.get("time", 0)),
        "passed":   int(suite.get("tests", 0))
                    - int(suite.get("failures", 0))
                    - int(suite.get("errors", 0))
                    - int(suite.get("skipped", 0)),
        "failed_tests": [
            {"name": tc.get("name"), "classname": tc.get("classname"),
             "message": tc.find("failure").get("message", "") if tc.find("failure") is not None else ""}
            for tc in suite.findall(".//testcase")
            if tc.find("failure") is not None or tc.find("error") is not None
        ],
    }
```

## Coverage Report

```python
import subprocess, re

def get_coverage_summary(source: str = "src/") -> dict:
    result = subprocess.run(
        ["python", "-m", "coverage", "report", "--include=src/**"],
        capture_output=True, text=True
    )
    # Parse total line
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
    total_pct = int(match.group(1)) if match else 0
    # Find files below threshold
    low_coverage = []
    for line in result.stdout.splitlines():
        m = re.match(r"(\S+)\s+\d+\s+\d+\s+(\d+)%", line)
        if m and int(m.group(2)) < 80:
            low_coverage.append({"file": m.group(1), "coverage": int(m.group(2))})
    return {"total_pct": total_pct, "low_coverage": low_coverage}
```

## Markdown Summary Report

```python
def format_test_summary(results: dict, coverage: dict | None = None) -> str:
    status = "PASSED" if results["passed"] == results["tests"] else "FAILED"
    lines = [
        f"## Test Results — {status}",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total  | {results['tests']} |",
        f"| Passed | {results['passed']} |",
        f"| Failed | {results['failures'] + results['errors']} |",
        f"| Skipped | {results['skipped']} |",
        f"| Duration | {results['time_s']:.2f}s |",
    ]
    if coverage:
        lines.append(f"| Coverage | {coverage['total_pct']}% |")

    if results.get("failed_tests"):
        lines += ["", "### Failed Tests", ""]
        for t in results["failed_tests"]:
            lines.append(f"- **{t['classname']}::{t['name']}**")
            if t["message"]:
                lines.append(f"  `{t['message'][:100]}`")
    return "\n".join(lines)
```

## pytest.ini / pyproject.toml Config

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
    "--tb=short",
    "--strict-markers",
    "-q",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

## Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| Run all tests | `pytest tests/ -v` | Verbose output |
| With coverage | `pytest --cov=src` | Add `--cov-report=html` |
| Parallel | `pytest -n auto` | Requires pytest-xdist |
| Only failures | `pytest --lf` | Last-failed |
| JUnit XML | `pytest --junit-xml=out.xml` | CI integration |
| Coverage % | `coverage report` | After `coverage run` |
| Fail below % | `coverage report --fail-under=80` | CI gate |
