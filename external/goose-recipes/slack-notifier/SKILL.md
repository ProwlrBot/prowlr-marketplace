---
name: slack-notifier
description: Use this skill when you want to send Slack messages — alerts, formatted reports, approval requests, or scheduled summaries — using Block Kit for rich formatting.
source: https://github.com/block/goose/tree/main/docs/recipes
---

# Slack Notifier

## Overview

Send rich Slack messages with Block Kit formatting: alerts with context, summary reports, approval request buttons, and threaded updates. Adapted from Block's Goose integration recipes.

## Setup

```bash
pip install slack-sdk anthropic
# Create Slack app at api.slack.com, get Bot Token with chat:write scope
export SLACK_BOT_TOKEN=xoxb-...
```

## Basic Message

```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

def send_message(channel: str, text: str) -> str:
    result = slack.chat_postMessage(channel=channel, text=text)
    return result["ts"]  # thread timestamp for follow-ups

def send_thread_reply(channel: str, thread_ts: str, text: str) -> None:
    slack.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)
```

## Rich Alert Block

```python
def send_alert(channel: str, title: str, message: str,
               severity: str = "warning", fields: dict | None = None) -> str:
    colors = {"critical": "#FF0000", "warning": "#FFA500", "info": "#36A64F", "success": "#36A64F"}
    icons = {"critical": "🔴", "warning": "🟡", "info": "🔵", "success": "✅"}

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{icons.get(severity, '📢')} {title}"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": message}
        }
    ]

    if fields:
        fields_block = {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*{k}*\n{v}"}
                for k, v in fields.items()
            ]
        }
        blocks.append(fields_block)

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"<!date^{int(time.time())}^{{date_short_pretty}} {{time}}|{datetime.now().isoformat()}> | ProwlrBot"}]
    })

    result = slack.chat_postMessage(
        channel=channel,
        text=title,  # fallback for notifications
        attachments=[{"color": colors.get(severity, "#808080"), "blocks": blocks}]
    )
    return result["ts"]
```

## Approval Request

```python
def request_approval(channel: str, title: str, description: str,
                     approve_action: str = "approve", deny_action: str = "deny") -> str:
    result = slack.chat_postMessage(
        channel=channel,
        text=f"Approval needed: {title}",
        blocks=[
            {"type": "header", "text": {"type": "plain_text", "text": f"⏳ {title}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": description}},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "action_id": approve_action
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Deny"},
                        "style": "danger",
                        "action_id": deny_action
                    }
                ]
            }
        ]
    )
    return result["ts"]
```

## AI-Generated Summary + Post

```python
import anthropic

def post_ai_summary(channel: str, data: str, summary_type: str = "daily") -> str:
    ac = anthropic.Anthropic()
    response = ac.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        system="You write concise Slack summaries. Use bullet points. Use *bold* for important items. 10 lines max.",
        messages=[{"role": "user", "content": f"Summarize this {summary_type} data:\n{data}"}]
    )
    summary = response.content[0].text
    return send_message(channel, summary)
```

## Quick Reference

| Function | Purpose |
|----------|---------|
| `send_message` | Plain text message |
| `send_alert` | Rich alert with severity color |
| `request_approval` | Interactive approve/deny buttons |
| `send_thread_reply` | Reply in thread |
| `post_ai_summary` | AI-generated summary |
