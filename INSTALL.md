# ProwlrBot Marketplace — Setup

---

## For Users (Installing from the Marketplace)

### Prerequisites

- ProwlrBot installed ([setup guide](https://github.com/mcpcentral/prowlrbot/blob/main/INSTALL.md))
- Python 3.10+

### Browse and Install

```bash
# List all available items
prowlr marketplace list

# Filter by category
prowlr marketplace list --category skills
prowlr marketplace list --category mcp-servers

# Search
prowlr marketplace search "pdf"

# Install a skill
prowlr marketplace install pdf-advanced

# Install an MCP server
prowlr marketplace install prowlr-hub
```

### Install ProwlrHub (Default MCP Server)

ProwlrHub ships with ProwlrBot. To connect your Claude Code terminal to the war room:

```bash
cd /path/to/prowlrbot
claude mcp add prowlr-hub -s local -e PYTHONPATH="$(pwd)/src" -- python3 -m prowlrbot.hub
```

Then restart Claude Code and ask your agent to `check_mission_board`.

---

## For Contributors (Publishing to the Marketplace)

### 1. Clone the marketplace

```bash
git clone https://github.com/mcpcentral/prowlr-marketplace.git
cd prowlr-marketplace
```

### 2. Create from a template

```bash
# Skill
cp -r templates/skill-template community/skills/my-skill/

# MCP Server
cp -r templates/mcp-server-template community/mcp-servers/my-server/

# Workflow
cp -r templates/workflow-template community/workflows/my-workflow/
```

### 3. Build your item

Edit the SKILL.md (for skills) or manifest.json (for MCP servers) with your metadata. Add your code, scripts, and documentation.

### 4. Test locally

```bash
# Install ProwlrBot if you haven't
cd /path/to/prowlrbot
pip install -e ".[dev]"

# Test a skill
prowlr skills add /path/to/my-skill/

# Test an MCP server
claude mcp add my-server -- python3 -m my_package.server
```

### 5. Submit

```bash
# From the marketplace repo
git checkout -b add-my-skill
git add community/skills/my-skill/
git commit -m "feat: add my-skill to marketplace"
git push origin add-my-skill
```

Then open a PR. The review team will check security, documentation, and compatibility.

---

## Directory Structure

```
prowlr-marketplace/
├── defaults/          # Built-in items (ProwlrBot team maintains)
├── community/         # Community contributions (PRs welcome)
├── templates/         # Starter templates for each category
├── docs/              # Publishing guides and policies
├── categories.json    # Category definitions
└── INSTALL.md         # This file
```

---

## Links

- [ProwlrBot](https://github.com/mcpcentral/prowlrbot) — Core platform
- [Publishing Guide](docs/publishing-guide.md) — Detailed submission instructions
- [Revenue Sharing](docs/revenue-sharing.md) — How paid items work
