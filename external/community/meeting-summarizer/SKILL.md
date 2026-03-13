---
name: meeting-summarizer
description: Use this skill when the user has a meeting recording, transcript, or notes and wants a structured summary with action items, decisions, and follow-ups.
---

# Meeting Summarizer

## Overview

Transform meeting recordings or transcripts into structured summaries: key decisions, action items with owners, discussion topics, and follow-up questions. Works from audio files (via Whisper) or raw text transcripts.

## Transcribe Audio (Whisper)

```python
import whisper
from pathlib import Path

def transcribe_audio(audio_path: str, model_size: str = "base") -> str:
    """Transcribe audio file to text using Whisper."""
    model = whisper.load_model(model_size)  # tiny/base/small/medium/large
    result = model.transcribe(audio_path, language="en")
    return result["text"]

# Install: pip install openai-whisper
# For GPU: pip install openai-whisper torch
```

## Summarize Meeting

```python
import anthropic
import json

client = anthropic.Anthropic()

def summarize_meeting(transcript: str, meeting_type: str = "general",
                       attendees: list[str] | None = None) -> dict:
    attendee_context = f"Attendees: {', '.join(attendees)}" if attendees else ""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        tools=[{
            "name": "meeting_summary",
            "description": "Structured meeting summary",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "executive_summary": {"type": "string", "description": "2-3 sentence summary"},
                    "decisions_made": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Concrete decisions reached in this meeting"
                    },
                    "action_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task": {"type": "string"},
                                "owner": {"type": "string"},
                                "due": {"type": "string"},
                                "priority": {"type": "string", "enum": ["high", "medium", "low"]}
                            },
                            "required": ["task"]
                        }
                    },
                    "key_topics": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "open_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Questions raised but not resolved"
                    },
                    "next_meeting_agenda": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["executive_summary", "decisions_made", "action_items"]
            }
        }],
        tool_choice={"type": "tool", "name": "meeting_summary"},
        messages=[{
            "role": "user",
            "content": f"""Summarize this {meeting_type} meeting.
{attendee_context}

Transcript:
{transcript[:6000]}"""
        }],
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return {}
```

## Format as Markdown

```python
def format_meeting_notes(summary: dict) -> str:
    lines = [
        f"# {summary.get('title', 'Meeting Summary')}",
        "",
        "## Summary",
        summary.get("executive_summary", ""),
        "",
        "## Decisions Made",
    ]
    for d in summary.get("decisions_made", []):
        lines.append(f"- {d}")

    lines.extend(["", "## Action Items", ""])
    for item in summary.get("action_items", []):
        owner = f" — **{item['owner']}**" if item.get("owner") else ""
        due = f" (due: {item['due']})" if item.get("due") else ""
        lines.append(f"- [ ] {item['task']}{owner}{due}")

    if summary.get("open_questions"):
        lines.extend(["", "## Open Questions"])
        for q in summary["open_questions"]:
            lines.append(f"- {q}")

    return "\n".join(lines)
```

## Full Pipeline

```python
def process_meeting_recording(audio_path: str, **kwargs) -> str:
    transcript = transcribe_audio(audio_path)
    summary = summarize_meeting(transcript, **kwargs)
    return format_meeting_notes(summary)

# Usage
notes = process_meeting_recording(
    "team-standup-2026-03-13.mp3",
    meeting_type="standup",
    attendees=["Alice", "Bob", "Charlie"]
)
print(notes)
```

## Quick Reference

| Input | Process |
|-------|---------|
| Audio file | Whisper → transcript → summarize |
| Transcript text | Direct → summarize |
| Meeting notes | Summarize + extract action items |
| Whisper models | tiny (fast) → large (accurate) |
