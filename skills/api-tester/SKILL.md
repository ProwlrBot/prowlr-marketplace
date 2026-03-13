---
name: api-tester
description: Use this skill when the user wants to test an API, validate endpoints, check response schemas, run API test suites, or do load testing.
---

# API Tester

## Overview

Tests REST and GraphQL APIs: validates status codes, response schemas, auth flows, and performance. Supports YAML-defined test suites and async load testing.

## Quick Start

```python
import httpx

def test_endpoint(url: str, method: str = "GET", headers: dict | None = None,
                  body: dict | None = None, expected_status: int = 200) -> dict:
    with httpx.Client(timeout=10) as client:
        resp = client.request(method, url, headers=headers or {}, json=body)
    return {
        "url": url,
        "status": resp.status_code,
        "passed": resp.status_code == expected_status,
        "latency_ms": resp.elapsed.total_seconds() * 1000,
        "body": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
    }
```

## Schema Validation

```python
import jsonschema

def validate_response(body: dict, schema: dict) -> list[str]:
    """Returns list of validation errors, empty if valid."""
    v = jsonschema.Draft7Validator(schema)
    return [e.message for e in v.iter_errors(body)]

# Example schema
USER_SCHEMA = {
    "type": "object",
    "required": ["id", "email"],
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "format": "email"},
        "name": {"type": "string"},
    },
    "additionalProperties": False,
}
```

## Auth Patterns

```python
# Bearer token
headers = {"Authorization": f"Bearer {token}"}

# Basic auth
import base64
creds = base64.b64encode(f"{user}:{password}".encode()).decode()
headers = {"Authorization": f"Basic {creds}"}

# API key (header)
headers = {"X-API-Key": api_key}

# OAuth2 client credentials
import httpx
def get_oauth_token(token_url: str, client_id: str, client_secret: str) -> str:
    resp = httpx.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    return resp.json()["access_token"]
```

## YAML Test Suite

```yaml
# tests.yaml
base_url: https://api.example.com
headers:
  Authorization: "Bearer ${TOKEN}"

tests:
  - name: Get user list
    method: GET
    path: /users
    expect_status: 200
    expect_schema: user_list_schema

  - name: Create user
    method: POST
    path: /users
    body:
      name: Test User
      email: test@example.com
    expect_status: 201
    expect_contains:
      id: "any"
```

```python
import yaml, httpx

def run_test_suite(suite_file: str, env: dict | None = None) -> list[dict]:
    suite = yaml.safe_load(open(suite_file))
    base = suite["base_url"]
    headers = {k: v.replace("${TOKEN}", (env or {}).get("TOKEN", ""))
               for k, v in suite.get("headers", {}).items()}
    results = []
    with httpx.Client(base_url=base, headers=headers, timeout=10) as client:
        for test in suite["tests"]:
            resp = client.request(test["method"], test["path"], json=test.get("body"))
            results.append({
                "name": test["name"],
                "passed": resp.status_code == test.get("expect_status", 200),
                "status": resp.status_code,
            })
    return results
```

## Async Load Testing

```python
import asyncio, httpx, time

async def load_test(url: str, concurrency: int = 10, total: int = 100) -> dict:
    latencies = []
    errors = 0
    async with httpx.AsyncClient(timeout=10) as client:
        async def one():
            t = time.perf_counter()
            try:
                await client.get(url)
                latencies.append((time.perf_counter() - t) * 1000)
            except Exception:
                nonlocal errors
                errors += 1
        tasks = [one() for _ in range(total)]
        await asyncio.gather(*tasks)
    latencies.sort()
    return {
        "requests": total, "errors": errors,
        "p50_ms": latencies[len(latencies)//2],
        "p95_ms": latencies[int(len(latencies)*0.95)],
        "p99_ms": latencies[int(len(latencies)*0.99)],
        "mean_ms": sum(latencies)/len(latencies) if latencies else 0,
    }
```

## Quick Reference

| Task | Tool | Notes |
|------|------|-------|
| Single request | `httpx.Client` | Sync, great for scripts |
| Async load test | `httpx.AsyncClient` | High concurrency |
| Schema validation | `jsonschema` | Draft 7 recommended |
| Auth: OAuth2 | `client_credentials` flow | Machine-to-machine |
| Test suite | YAML + httpx | Version control your tests |
