---
name: performance-profiler
description: Use this skill when the user wants to profile code performance, find bottlenecks, measure execution time, analyze memory usage, or optimize slow functions.
---

# Performance Profiler

## Overview

Profiles Python applications, web endpoints, and database queries. Identifies CPU hotspots, memory leaks, and slow paths using cProfile, line_profiler, memory_profiler, and py-spy.

## CPU Profiling with cProfile

```python
import cProfile, pstats, io

def profile(func, *args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    result = func(*args, **kwargs)
    pr.disable()

    buf = io.StringIO()
    ps = pstats.Stats(pr, stream=buf).sort_stats("cumulative")
    ps.print_stats(20)  # top 20 functions
    print(buf.getvalue())
    return result

# Or as decorator:
import functools

def profiled(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return profile(func, *args, **kwargs)
    return wrapper
```

### Read cProfile output

Key columns:
- `ncalls` — number of calls
- `tottime` — time in this function (excluding callees)
- `cumtime` — time in this function + all called functions
- Focus on functions with high `cumtime` or called many times

## Line-by-Line Profiling

```bash
pip install line_profiler
```

```python
# Add @profile decorator to functions you want to analyze
# Then run: kernprof -l -v script.py

@profile  # noqa — added by kernprof at runtime
def slow_function(data):
    result = []
    for item in data:           # ← this line's time will show
        result.append(item * 2) # ← and this one
    return result
```

## Memory Profiling

```bash
pip install memory_profiler
```

```python
from memory_profiler import profile as mem_profile

@mem_profile
def memory_hungry(n: int) -> list:
    return [i ** 2 for i in range(n)]

# Or measure peak:
from memory_profiler import memory_usage
peak_mb = max(memory_usage((memory_hungry, (10_000_000,), {})))
print(f"Peak memory: {peak_mb:.1f} MB")
```

## py-spy (Production Profiling)

```bash
pip install py-spy

# Attach to running process (no restart needed):
py-spy top --pid <PID>

# Record flame graph:
py-spy record -o profile.svg --pid <PID> --duration 30

# Profile a script:
py-spy record -o profile.svg -- python myscript.py
```

## Simple Timing Utilities

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(label: str = ""):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed*1000:.2f}ms")

# Usage:
with timer("database query"):
    results = db.execute(query)
```

```python
import timeit

def benchmark(stmt: str, setup: str = "pass", n: int = 1000) -> float:
    """Returns average time per call in microseconds."""
    total = timeit.timeit(stmt, setup=setup, number=n)
    return total / n * 1e6

# benchmark("sorted(range(1000))", n=10000) → ~35µs
```

## Database Query Analysis

```python
# PostgreSQL EXPLAIN ANALYZE
def explain_query(conn, query: str, params=None) -> str:
    with conn.cursor() as cur:
        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {query}", params)
        return "\n".join(row[0] for row in cur.fetchall())

# What to look for:
# - "Seq Scan" on large tables → add index
# - "Hash Join" vs "Nested Loop" → join order matters
# - High "actual rows" vs "estimated rows" → stale stats (ANALYZE)
# - "Buffers: shared hit/read" → cache miss rate
```

## Web Performance — Lighthouse CLI

```bash
npm install -g lighthouse
lighthouse https://mysite.com --output json --output-path report.json
```

```python
import subprocess, json

def run_lighthouse(url: str) -> dict:
    result = subprocess.run(
        ["lighthouse", url, "--output=json", "--quiet"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    cats = data.get("categories", {})
    return {k: round(v["score"] * 100) for k, v in cats.items()}
```

## Quick Reference

| Bottleneck Type | Tool | Command |
|----------------|------|---------|
| CPU hotspots | cProfile | `python -m cProfile -s cumtime script.py` |
| Line-by-line CPU | line_profiler | `kernprof -l -v script.py` |
| Memory leaks | memory_profiler | `@profile` decorator |
| Production profiling | py-spy | `py-spy top --pid PID` |
| Flame graphs | py-spy | `py-spy record -o flame.svg` |
| DB slow queries | EXPLAIN ANALYZE | Add to any SQL query |
| Web performance | Lighthouse | Scores 0-100 per category |
