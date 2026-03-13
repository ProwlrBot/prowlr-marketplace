---
name: log-analyzer
description: Use this skill when the user wants to analyze log files — find errors and their frequency, detect anomalies, build incident timelines, or summarize what happened during an outage.
---

# Log Analyzer

## Overview

Parse structured (JSON) or unstructured log files, extract errors and anomalies, build incident timelines, and generate human-readable summaries. Uses Claude for intelligent pattern recognition beyond simple regex.

## Log Parser

```python
import re
import json
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path

def parse_log_file(log_path: str) -> list[dict]:
    """Parse common log formats into structured records."""
    logs = []
    text = Path(log_path).read_text(errors="ignore")

    for line in text.splitlines():
        if not line.strip():
            continue

        # Try JSON first
        try:
            record = json.loads(line)
            logs.append(record)
            continue
        except json.JSONDecodeError:
            pass

        # Common log format: 2026-03-13 14:23:45 ERROR message
        m = re.match(
            r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})'
            r'[\s,]*(\w+)'
            r'[\s,]*(.*)',
            line
        )
        if m:
            logs.append({
                "timestamp": m.group(1),
                "level": m.group(2).upper(),
                "message": m.group(3),
                "raw": line
            })
        else:
            logs.append({"raw": line, "level": "UNKNOWN"})

    return logs

def extract_errors(logs: list[dict]) -> list[dict]:
    error_levels = {"ERROR", "CRITICAL", "FATAL", "EXCEPTION"}
    return [
        log for log in logs
        if log.get("level", "").upper() in error_levels
        or any(kw in log.get("message", "").lower()
               for kw in ["error", "exception", "traceback", "failed", "critical"])
    ]

def error_frequency(errors: list[dict], top_n: int = 10) -> list[dict]:
    """Find most common error patterns."""
    # Normalize messages (remove variable parts like IDs, timestamps)
    def normalize(msg: str) -> str:
        msg = re.sub(r'\b[0-9a-f]{8,}\b', '<id>', msg)
        msg = re.sub(r'\d{4}-\d{2}-\d{2}', '<date>', msg)
        msg = re.sub(r'\d+\.\d+\.\d+\.\d+', '<ip>', msg)
        return msg[:100]  # truncate long messages

    normalized = [normalize(e.get("message", e.get("raw", ""))) for e in errors]
    counts = Counter(normalized)
    return [{"pattern": p, "count": c} for p, c in counts.most_common(top_n)]
```

## AI Log Analysis

```python
import anthropic

client = anthropic.Anthropic()

def analyze_logs_with_ai(log_text: str, question: str) -> str:
    """Use Claude to answer questions about logs."""
    # Sample the logs if very large
    lines = log_text.splitlines()
    if len(lines) > 200:
        # Take errors + sample of others
        error_lines = [l for l in lines if any(k in l.lower() for k in ["error", "exception", "fail"])]
        sample = error_lines[:100] + lines[-50:]  # recent + errors
        log_sample = "\n".join(sample)
    else:
        log_sample = log_text

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system="You are an expert at analyzing application logs. Be specific about timestamps, error messages, and sequences.",
        messages=[{
            "role": "user",
            "content": f"Question: {question}\n\nLogs:\n{log_sample}"
        }],
    )
    return response.content[0].text

def build_incident_timeline(log_path: str, start_time: str, end_time: str) -> str:
    """Build a timeline of events during an incident window."""
    logs = parse_log_file(log_path)
    # Filter to time window
    window_logs = [
        l for l in logs
        if start_time <= l.get("timestamp", "") <= end_time
    ]
    log_text = "\n".join(l.get("raw", str(l)) for l in window_logs[:300])
    return analyze_logs_with_ai(log_text, "Build a chronological incident timeline. What happened, when, in what order?")
```

## Summary Report

```python
def generate_log_report(log_path: str) -> str:
    logs = parse_log_file(log_path)
    errors = extract_errors(logs)
    top_errors = error_frequency(errors)

    level_counts = Counter(l.get("level", "UNKNOWN") for l in logs)

    report_lines = [
        f"## Log Analysis: {Path(log_path).name}",
        f"Total lines: {len(logs)} | Errors: {len(errors)}",
        "",
        "### Level Distribution",
        *[f"- {level}: {count}" for level, count in level_counts.most_common()],
        "",
        "### Top Error Patterns",
        *[f"- ({e['count']}x) {e['pattern']}" for e in top_errors],
    ]
    return "\n".join(report_lines)
```

## Quick Reference

| Task | Function |
|------|----------|
| Parse logs | `parse_log_file(path)` |
| Find errors | `extract_errors(logs)` |
| Error frequency | `error_frequency(errors)` |
| AI analysis | `analyze_logs_with_ai(text, question)` |
| Incident timeline | `build_incident_timeline(path, start, end)` |
