---
name: customer-support-agent
description: Use this skill when building a customer support agent with knowledge base lookup, ticket creation, and human escalation logic.
source: https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents/customer_support
---

# Customer Support Agent

## Overview

Multi-turn customer support agent pattern. Claude uses tools to look up knowledge base articles, create support tickets, check order status, and escalate to humans when needed. Based on the Anthropic Cookbook customer support pattern.

## Agent Architecture

```python
import anthropic

client = anthropic.Anthropic()

SUPPORT_TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": "Search the help documentation for relevant articles",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_ticket",
        "description": "Create a support ticket for issues that need human review",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}
            },
            "required": ["subject", "description", "priority"]
        }
    },
    {
        "name": "get_order_status",
        "description": "Look up the status of a customer order",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate this conversation to a human agent",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "summary": {"type": "string"}
            },
            "required": ["reason", "summary"]
        }
    }
]

SYSTEM_PROMPT = """You are a helpful customer support agent. Your goal is to resolve
customer issues efficiently and with empathy.

Guidelines:
- Search the knowledge base before creating tickets
- Create tickets for issues that need investigation
- Escalate to humans for: billing disputes, account termination, legal matters
- Be honest if you don't know something
- Always confirm before taking actions that affect the customer's account"""

def support_agent(user_message: str, conversation_history: list) -> dict:
    messages = conversation_history + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=SUPPORT_TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return {"response": response.content[0].text, "history": messages}

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
```

## Tool Implementation Stubs

```python
def execute_tool(name: str, inputs: dict) -> str:
    if name == "search_knowledge_base":
        return search_docs(inputs["query"])  # implement with your docs
    elif name == "create_ticket":
        return create_zendesk_ticket(**inputs)  # or your ticketing system
    elif name == "get_order_status":
        return lookup_order(inputs["order_id"])
    elif name == "escalate_to_human":
        return hand_off_to_agent(**inputs)
```

## Quick Reference

| Tool | When to use |
|------|------------|
| search_knowledge_base | Any question that might be in docs |
| create_ticket | Issues needing investigation |
| get_order_status | "Where is my order?" |
| escalate_to_human | Billing, legal, complex account issues |
