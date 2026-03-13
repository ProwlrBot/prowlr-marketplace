---
name: tool-use-orchestration
description: Use this skill when building agentic loops with Claude tool use — defining tools, handling tool calls, parallel execution, and multi-step reasoning.
source: https://github.com/anthropics/anthropic-cookbook/tree/main/tool_use
---

# Tool Use Orchestration

## Overview

Complete patterns for Claude tool use: defining tools, running the agentic loop, handling parallel tool calls, error handling, and building reliable multi-step workflows.

## Basic Tool Definition

```python
import anthropic
import json

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or coordinates"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["location"]
        }
    }
]

def get_weather(location: str, unit: str = "celsius") -> dict:
    # Replace with real weather API
    return {"temp": 22, "conditions": "sunny", "location": location}
```

## Agentic Loop

```python
def run_agent(user_message: str, tools: list, tool_handlers: dict) -> str:
    """Run a complete agentic loop until end_turn."""
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )

        # Collect text output
        text_outputs = [
            b.text for b in response.content
            if hasattr(b, "text")
        ]

        if response.stop_reason == "end_turn":
            return "\n".join(text_outputs)

        if response.stop_reason != "tool_use":
            raise ValueError(f"Unexpected stop reason: {response.stop_reason}")

        # Process all tool calls (may be parallel)
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = tool_handlers.get(block.name)
                if not handler:
                    result = {"error": f"Unknown tool: {block.name}"}
                else:
                    try:
                        result = handler(**block.input)
                    except Exception as e:
                        result = {"error": str(e)}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

## Parallel Tool Execution

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def execute_tools_parallel(tool_calls: list, handlers: dict) -> list:
    """Execute multiple tool calls in parallel."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                lambda tc=tc: handlers[tc.name](**tc.input)
            )
            for tc in tool_calls
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    return [
        {
            "type": "tool_result",
            "tool_use_id": tc.id,
            "content": json.dumps(r) if not isinstance(r, Exception) else f"Error: {r}",
            "is_error": isinstance(r, Exception),
        }
        for tc, r in zip(tool_calls, results)
    ]
```

## Quick Reference

| Pattern | When to use |
|---------|------------|
| Basic loop | Single tool, sequential |
| Parallel | Multiple independent tool calls |
| `is_error: true` | Tool failed, let Claude retry |
| `tool_choice: {"type": "tool", "name": "X"}` | Force specific tool |
| `tool_choice: {"type": "none"}` | Prevent tool use |
