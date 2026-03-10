<p align="center">
  <h1 align="center">ProwlrBot Marketplace</h1>
  <p align="center"><strong>Skills, agents, MCP servers, themes, and workflows for ProwlrBot</strong></p>
  <p align="center">Default listings + community contributions. Revenue sharing: 70/30 (creator/platform).</p>
</p>

---

## What's in the Marketplace?

The marketplace has two tiers:

| Tier | Who maintains | How to get |
|------|--------------|-----------|
| **Defaults** | ProwlrBot team | Ship with ProwlrBot — always available |
| **Community** | Anyone | Install via `prowlr marketplace install` or browse the catalog |

---

## Categories

| Category | Description | Default examples |
|----------|-------------|-----------------|
| **Skills** | Agent capability packs (PDF, Office, browser, email, news) | `pdf`, `docx`, `browser_visible`, `news`, `file_reader` |
| **Agents** | Pre-built agent configurations and personalities | Base agent config, SOUL.md templates |
| **Prompts** | System prompts and templates | AGENTS.md, PROFILE.md templates |
| **MCP Servers** | Model Context Protocol integrations | **ProwlrHub** (war room coordination) |
| **Themes** | Console UI themes and customizations | Default dark theme |
| **Workflows** | Multi-step automation recipes | Monitor → Alert → Action chains |

---

## Default Listings

### MCP Servers

#### ProwlrHub — War Room Multi-Agent Coordination

Connect multiple Claude Code terminals into one coordinated team. Shared mission board, file locking, and discovery store.

```bash
# One-liner install
claude mcp add prowlr-hub -s local -e PYTHONPATH="$(pwd)/src" -- python3 -m prowlrbot.hub
```

| Feature | What it does |
|---------|-------------|
| Mission Board | See all tasks, owners, priorities, and progress |
| Atomic Task Claiming | Lock files and claim tasks in one transaction |
| File Coordination | Advisory locks prevent edit conflicts |
| Shared Context | Key-value store for sharing discoveries |
| Cross-Machine | HTTP bridge for Mac + WSL + Linux coordination |

**13 MCP tools**: `check_mission_board`, `claim_task`, `update_task`, `complete_task`, `fail_task`, `lock_file`, `unlock_file`, `check_conflicts`, `get_agents`, `broadcast_status`, `share_finding`, `get_shared_context`, `get_events`

[Full docs](https://github.com/mcpcentral/prowlrbot/tree/main/src/prowlrbot/hub)

---

### Skills (Built-in)

| Skill | Description | Key capabilities |
|-------|-------------|-----------------|
| `pdf` | Read and extract content from PDF files | Text extraction, page selection |
| `docx` | Read and create Word documents | Content extraction, document generation |
| `pptx` | Read and create PowerPoint presentations | Slide parsing, presentation building |
| `xlsx` | Read and create Excel spreadsheets | Cell reading, formula support |
| `news` | Fetch and summarize news articles | RSS feeds, content extraction |
| `file_reader` | Read various file formats | Universal file type detection |
| `browser_visible` | Browse the web with visual feedback | Screenshot capture, page interaction |
| `cron` | Schedule recurring tasks | Cron expressions, interval scheduling |
| `himalaya` | Email integration via Himalaya | Read, send, search emails |
| `dingtalk_channel` | DingTalk messaging channel | Send/receive DingTalk messages |

---

## Installing from the Marketplace

### Browse available items

```bash
prowlr marketplace list
prowlr marketplace list --category skills
prowlr marketplace search "pdf"
```

### Install a skill

```bash
prowlr marketplace install pdf-advanced
```

Skills are installed to `~/.prowlrbot/active_skills/`.

### Install an MCP server

```bash
prowlr marketplace install prowlr-hub
```

MCP servers are added to your `.mcp.json` automatically.

---

## Publishing to the Marketplace

### 1. Create your item

Use the templates in `templates/` to get started:

```bash
# Skill
cp -r templates/skill-template my-skill/

# MCP Server
cp -r templates/mcp-server-template my-mcp-server/

# Workflow
cp -r templates/workflow-template my-workflow/
```

### 2. Fill in the metadata

Every marketplace item needs a manifest:

**For skills** — `SKILL.md` with YAML frontmatter:

```yaml
---
name: my-awesome-skill
description: What this skill does in one sentence
version: 1.0.0
author: your-github-username
category: skills
tags: [pdf, document, extraction]
license: Apache-2.0
---

# My Awesome Skill

Instructions for the agent on how to use this skill.
```

**For MCP servers** — `manifest.json`:

```json
{
  "name": "my-mcp-server",
  "description": "What this MCP server does",
  "version": "1.0.0",
  "author": "your-github-username",
  "category": "mcp-servers",
  "install": {
    "command": "python3",
    "args": ["-m", "my_package.server"],
    "env": {"PYTHONPATH": "./src"}
  },
  "tools": ["tool_1", "tool_2"]
}
```

### 3. Test locally

```bash
# Skills
prowlr skills add ./my-skill/

# MCP servers
claude mcp add my-server -- python3 -m my_package.server
```

### 4. Submit

```bash
prowlr marketplace publish ./my-skill/
```

Or submit a PR to this repository with your item in the appropriate category folder.

---

## Revenue Sharing

Community items can be free or paid:

| Pricing | Revenue split | Who gets what |
|---------|--------------|---------------|
| Free | n/a | Open source, everyone benefits |
| Paid | 70/30 | 70% to creator, 30% to platform |

Paid items require a Stripe Connect account. See [docs/revenue-sharing.md](docs/revenue-sharing.md) for details.

---

## Quality Standards

All marketplace submissions are reviewed for:

| Check | What we look for |
|-------|-----------------|
| **Security** | No hardcoded credentials, no shell injection, sandboxed execution |
| **Documentation** | Clear description, usage examples, prerequisites |
| **Testing** | At least basic functionality tests |
| **Compatibility** | Works with Python 3.10+ and current ProwlrBot version |
| **Licensing** | Valid open-source license (Apache-2.0, MIT, BSD recommended) |

---

## Directory Structure

```
prowlr-marketplace/
├── README.md              # This file
├── INSTALL.md             # Setup guide
├── LICENSE                # Apache 2.0
├── categories.json        # Category definitions
├── defaults/              # Default items (ship with ProwlrBot)
│   ├── mcp-servers/
│   │   └── prowlr-hub/   # War room coordination
│   ├── skills/
│   │   ├── pdf/
│   │   ├── docx/
│   │   └── ...
│   └── agents/
│       └── base-agent/
├── community/             # Community submissions
│   ├── skills/
│   ├── mcp-servers/
│   ├── agents/
│   ├── prompts/
│   ├── themes/
│   └── workflows/
├── templates/             # Starter templates
│   ├── skill-template/
│   ├── mcp-server-template/
│   └── workflow-template/
└── docs/
    ├── publishing-guide.md
    ├── revenue-sharing.md
    └── review-process.md
```

---

## Contributing

1. Fork this repo
2. Create your item using a template
3. Test it locally with ProwlrBot
4. Submit a PR

See [INSTALL.md](INSTALL.md) for setup instructions and [docs/publishing-guide.md](docs/publishing-guide.md) for the full publishing guide.

---

## Links

- **ProwlrBot**: [github.com/mcpcentral/prowlrbot](https://github.com/mcpcentral/prowlrbot) — Core platform
- **ROAR Protocol**: [github.com/mcpcentral/roar-protocol](https://github.com/mcpcentral/roar-protocol) — Agent communication
- **AgentVerse**: [github.com/mcpcentral/agentverse](https://github.com/mcpcentral/agentverse) — Virtual agent world
- **Docs**: [mcpcentral.github.io/prowlr-docs](https://mcpcentral.github.io/prowlr-docs)

## License

[Apache 2.0](LICENSE)
