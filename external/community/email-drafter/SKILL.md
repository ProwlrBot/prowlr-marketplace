---
name: email-drafter
description: Use this skill when the user wants to draft, improve, or respond to emails — cold outreach, follow-ups, escalations, team announcements, or any professional communication.
---

# Email Drafter

## Overview

Draft professional emails across any context and tone. Provides subject line variants, adjusts formality level, and adapts to the recipient relationship.

## Draft Email

```python
import anthropic

client = anthropic.Anthropic()

def draft_email(
    purpose: str,
    recipient: str,
    context: str,
    tone: str = "professional",  # professional, casual, formal, urgent
    length: str = "medium",  # short (3 sentences), medium (2 paragraphs), long (full)
    include_variants: int = 1,
) -> dict:
    system = f"""You are an expert email writer. Write emails that are {tone} in tone.
    Length: {length} ({{"short": "2-3 sentences", "medium": "2-3 paragraphs", "long": "full email"}}.get(length, "2-3 paragraphs")).
    Always provide a subject line. Be direct and get to the point in the first sentence."""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=system,
        messages=[{
            "role": "user",
            "content": f"""Write an email for this situation:

Purpose: {purpose}
Recipient: {recipient}
Context: {context}

Provide:
1. Subject: [subject line]
2. Body: [email body]
{"3. Alternative subject lines: [3 variants]" if include_variants else ""}"""
        }],
    )
    return {"draft": response.content[0].text}
```

## Email Types with Templates

```python
EMAIL_CONTEXTS = {
    "cold-outreach": "First contact — establish credibility quickly, lead with value, single CTA",
    "follow-up": "Following up after no response — add value, don't just check in",
    "escalation": "Escalating an unresolved issue — factual, specific timeline, clear ask",
    "announcement": "Team/company announcement — clear, positive, what changes for the reader",
    "apology": "Apologizing for an error — own it, specific, next steps to prevent recurrence",
    "rejection": "Declining a request/candidate — kind, brief, no false hope",
    "introduction": "Introducing yourself or two parties — why this matters to the reader",
    "request": "Asking for something — what you need, why, when, how much work for them",
}

def draft_by_type(email_type: str, **kwargs) -> dict:
    context = EMAIL_CONTEXTS.get(email_type, "professional email")
    return draft_email(
        purpose=f"{email_type}: {context}",
        **kwargs
    )
```

## Improve Existing Email

```python
def improve_email(existing_email: str, improvement_goal: str) -> str:
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system="Improve emails for clarity, impact, and professionalism. Keep the sender's voice.",
        messages=[{
            "role": "user",
            "content": f"""Improve this email. Goal: {improvement_goal}

Email:
{existing_email}

Show the improved version with a brief note on what you changed and why."""
        }],
    )
    return response.content[0].text
```

## Quick Reference

| Email Type | Key Principle |
|-----------|---------------|
| Cold outreach | Value first, ask last |
| Follow-up | Add new information, don't just ping |
| Escalation | Timeline + specific ask |
| Rejection | Kind, brief, no door left open |
| Apology | Own it, fix it, prevent it |
