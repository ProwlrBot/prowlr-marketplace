---
name: computer-use
description: Use this skill when the user wants to automate desktop or browser tasks — clicking, typing, screenshotting, running GUI apps, or filling web forms.
source: https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo
---

# Computer Use

## Overview

Provides Claude with tools to interact with a computer: take screenshots, move the mouse, click, type text, and execute bash commands. Based on the Anthropic computer-use-demo quickstart with Prowlr integration.

## Tools Available

```python
# Screenshot — capture current screen state
{
  "name": "computer",
  "input": {
    "action": "screenshot"
  }
}

# Click at coordinates
{
  "name": "computer",
  "input": {
    "action": "left_click",
    "coordinate": [x, y]
  }
}

# Type text
{
  "name": "computer",
  "input": {
    "action": "type",
    "text": "Hello, world!"
  }
}

# Run bash command
{
  "name": "bash",
  "input": {
    "command": "ls -la ~/Desktop"
  }
}
```

## Usage Pattern

```python
import anthropic

client = anthropic.Anthropic()

# Start with a screenshot to understand current state
tools = [
    {"type": "computer_20241022", "name": "computer", "display_width_px": 1920, "display_height_px": 1080},
    {"type": "bash_20241022", "name": "bash"},
    {"type": "text_editor_20241022", "name": "str_replace_editor"},
]

response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "Open the browser, navigate to example.com, and take a screenshot."
    }],
    betas=["computer-use-2024-10-22"],
)
```

## Setup Requirements

```bash
# Docker container with display server recommended
docker run -it \
  -e DISPLAY=:1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  anthropic/computer-use-demo

# Or use with Xvfb on Linux
Xvfb :1 -screen 0 1920x1080x24 &
export DISPLAY=:1
```

## Safety Notes

- Run in a sandbox/container — Claude will have real control of the system
- Review actions before executing in production environments
- Use `--read-only` filesystem mounts where possible
- This skill has MEDIUM risk: real system access, network access possible

## Quick Reference

| Action | Input |
|--------|-------|
| Screenshot | `{"action": "screenshot"}` |
| Click | `{"action": "left_click", "coordinate": [x, y]}` |
| Type | `{"action": "type", "text": "..."}` |
| Key press | `{"action": "key", "text": "ctrl+c"}` |
| Scroll | `{"action": "scroll", "coordinate": [x, y], "direction": "down"}` |
| Bash | `{"command": "..."}` |
