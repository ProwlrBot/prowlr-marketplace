---
name: cron-scheduler
description: Use this skill when the user wants to schedule recurring tasks, convert natural language schedules to cron expressions, or manage APScheduler jobs.
---

# Cron Scheduler

## Overview

Convert natural language schedules to cron expressions, manage APScheduler jobs, and build recurring automation with proper error handling and logging.

## Natural Language to Cron

```python
import anthropic

client = anthropic.Anthropic()

def parse_schedule(natural_language: str) -> dict:
    """Convert natural language to cron expression."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        tools=[{
            "name": "cron_schedule",
            "description": "Parse a natural language schedule into cron format",
            "input_schema": {
                "type": "object",
                "properties": {
                    "cron_expression": {
                        "type": "string",
                        "description": "Standard 5-field cron expression: min hour day month weekday"
                    },
                    "human_readable": {
                        "type": "string",
                        "description": "Plain English confirmation of what this schedule means"
                    },
                    "timezone_note": {
                        "type": "string",
                        "description": "If schedule implies a timezone, note it"
                    }
                },
                "required": ["cron_expression", "human_readable"]
            }
        }],
        tool_choice={"type": "tool", "name": "cron_schedule"},
        messages=[{"role": "user", "content": f'Convert to cron: "{natural_language}"'}],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return {}

# Examples:
# parse_schedule("every Monday at 9am") → {"cron_expression": "0 9 * * 1", "human_readable": "Every Monday at 9:00 AM"}
# parse_schedule("first day of month at midnight") → {"cron_expression": "0 0 1 * *", ...}
# parse_schedule("every 15 minutes on weekdays") → {"cron_expression": "*/15 * * * 1-5", ...}
```

## APScheduler Integration

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def add_cron_job(job_id: str, func, schedule: str,
                 timezone: str = "UTC", **kwargs) -> str:
    """Add a job using natural language or cron expression."""
    if any(c in schedule for c in ["*", "/"]):
        # Already a cron expression
        cron_expr = schedule
    else:
        # Parse natural language
        parsed = parse_schedule(schedule)
        cron_expr = parsed["cron_expression"]
        logger.info(f"Parsed '{schedule}' → '{cron_expr}' ({parsed.get('human_readable', '')})")

    parts = cron_expr.split()
    trigger = CronTrigger(
        minute=parts[0], hour=parts[1],
        day=parts[2], month=parts[3], day_of_week=parts[4],
        timezone=timezone
    )

    scheduler.add_job(
        func, trigger=trigger, id=job_id,
        kwargs=kwargs, replace_existing=True,
        misfire_grace_time=60,  # allow 60s late execution
        coalesce=True,          # don't stack up missed runs
    )
    return cron_expr

def remove_job(job_id: str) -> bool:
    try:
        scheduler.remove_job(job_id)
        return True
    except Exception:
        return False

def list_jobs() -> list[dict]:
    return [
        {
            "id": job.id,
            "next_run": str(job.next_run_time),
            "trigger": str(job.trigger),
        }
        for job in scheduler.get_jobs()
    ]
```

## Example Jobs

```python
async def daily_report():
    logger.info("Running daily report...")
    # your report logic

async def cleanup_old_files():
    logger.info("Cleaning up files older than 30 days...")

# Usage
add_cron_job("daily-report", daily_report, "every day at 8am", timezone="America/New_York")
add_cron_job("cleanup", cleanup_old_files, "0 2 * * 0")  # 2am Sunday

scheduler.start()
```

## Quick Reference

| Schedule | Cron Expression |
|----------|----------------|
| Every minute | `* * * * *` |
| Every hour | `0 * * * *` |
| Daily at midnight | `0 0 * * *` |
| Every Monday 9am | `0 9 * * 1` |
| 1st of month | `0 0 1 * *` |
| Every 15 minutes | `*/15 * * * *` |
| Weekdays 9-5 | `0 9-17 * * 1-5` |
