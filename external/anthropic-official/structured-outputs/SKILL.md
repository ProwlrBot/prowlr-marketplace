---
name: structured-outputs
description: Use this skill when you need Claude to return structured JSON — data extraction, classification, form parsing, or any task needing machine-readable output.
source: https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/json_mode
---

# Structured Outputs

## Overview

Three reliable techniques for getting Claude to return structured JSON: tool use (most reliable), prefilling the assistant turn, and system prompt instruction. Choose based on complexity.

## Method 1: Tool Use (Recommended)

Force structured output by defining the schema as a tool and using `tool_choice`.

```python
import anthropic
import json

client = anthropic.Anthropic()

def extract_structured(text: str, schema: dict, schema_name: str = "extract") -> dict:
    """Extract structured data using tool use — guaranteed to match schema."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        tools=[{
            "name": schema_name,
            "description": "Extract the requested information",
            "input_schema": schema
        }],
        tool_choice={"type": "tool", "name": schema_name},
        messages=[{"role": "user", "content": text}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == schema_name:
            return block.input
    raise ValueError("No structured output returned")

# Example: extract contact info
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
        "company": {"type": "string"}
    },
    "required": ["name"]
}

result = extract_structured(
    "Hi, I'm Jane Smith from Acme Corp. Reach me at jane@acme.com or 555-1234.",
    schema,
    "contact_info"
)
# Returns: {"name": "Jane Smith", "email": "jane@acme.com", "phone": "555-1234", "company": "Acme Corp"}
```

## Method 2: Prefill Assistant Turn

```python
def extract_with_prefill(text: str, extraction_instruction: str) -> dict:
    """Prefill assistant turn with { to force JSON output."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"{extraction_instruction}\n\nText: {text}"},
            {"role": "assistant", "content": "{"},  # prefill forces JSON
        ],
    )
    raw = "{" + response.content[0].text
    return json.loads(raw)
```

## Method 3: System Prompt

```python
def classify_text(text: str, categories: list[str]) -> dict:
    """Classify text into categories with confidence scores."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        system=f"""Classify the input text. Return ONLY valid JSON in this format:
        {{"category": "<one of: {', '.join(categories)}>", "confidence": <0.0-1.0>, "reason": "<brief reason>"}}
        No explanation, no markdown, just the JSON object.""",
        messages=[{"role": "user", "content": text}],
    )
    return json.loads(response.content[0].text)

# Example
result = classify_text(
    "The app crashes when I click the submit button",
    ["bug", "feature-request", "question", "billing"]
)
# Returns: {"category": "bug", "confidence": 0.95, "reason": "Describes a crash on user action"}
```

## Common Extraction Schemas

```python
# Invoice extraction
INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor": {"type": "string"},
        "invoice_number": {"type": "string"},
        "date": {"type": "string", "format": "date"},
        "total": {"type": "number"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"}
                }
            }
        }
    }
}
```

## Quick Reference

| Method | Reliability | Best for |
|--------|------------|----------|
| Tool use + tool_choice | Highest | Complex schemas |
| Prefill `{` | High | Simple objects |
| System prompt | Medium | Classification |
