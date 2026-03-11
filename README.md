<p align="center">
  <img src="https://img.shields.io/badge/ProwlrBot-Marketplace-00E5FF?style=for-the-badge&logoColor=white" alt="ProwlrBot Marketplace" />
</p>

<h1 align="center">prowlr-marketplace</h1>

<p align="center">
  <strong>The bazaar where agents shop.</strong><br/>
  <sub>Community registry for skills, agents, prompts, MCP servers, themes, and workflows.</sub>
</p>

<p align="center">
  <a href="https://github.com/ProwlrBot/prowlrbot"><img src="https://img.shields.io/badge/core-prowlrbot-00E5FF?style=flat-square" /></a>
  <a href="https://github.com/ProwlrBot/prowlr-marketplace/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square" /></a>
</p>

---

> *"The value of a network is proportional to the square of the number of connected users."* — Metcalfe's Law
>
> Every listing makes the whole platform stronger.

---

## What Is This?

This is the **community registry** for [ProwlrBot](https://github.com/ProwlrBot/prowlrbot). Think npm for AI agents — but with 6 categories and a 70/30 revenue split.

When you run `prowlr market update`, your ProwlrBot fetches listings from this repo and makes them available locally.

## Categories

```
📂 skills/          → Agent capabilities (code review, web monitoring, PDF reading)
📂 agents/          → Pre-configured agent personalities and specializations
📂 prompts/         → Prompt packs for specific domains
📂 mcp-servers/     → MCP server integrations
📂 themes/          → Console UI themes
📂 workflows/       → Multi-step automation pipelines
```

## Browse What's Available

| Category | Listings | Highlights |
|:---------|:---------|:-----------|
| **Skills** | `web-monitor`, `code-review`, `pdf-reader` | Detection, analysis, extraction |
| **Agents** | `prowlr-scout`, `prowlr-guard` | Research hunter, security sentinel |
| **Prompts** | `business-analyst`, `code-assistant` | MBA without debt, pair programmer |
| **MCP Servers** | `prowlr-hub`, `prowlr-tools` | Coordination, execution |
| **Themes** | `dark-prowler`, `light-sentinel` | Night hunter, day guardian |
| **Workflows** | `deploy-review`, `daily-standup` | Ship faster, stay informed |

## Install a Listing

```bash
# Update your local registry
prowlr market update

# Browse listings
prowlr market search "code review"

# Install
prowlr market install skill-code-review
```

## Publish Your Own

1. Fork this repo
2. Create a directory under the right category: `skills/your-skill/manifest.json`
3. Follow the [manifest schema](#manifest-schema)
4. Open a PR

See [`templates/`](templates/) for starter templates and [`PUBLISHING.md`](PUBLISHING.md) for the full guide.

### Manifest Schema

Every listing needs a `manifest.json`:

```json
{
  "id": "unique-id",
  "title": "Human-Readable Title",
  "description": "What it does and why it matters.",
  "version": "1.0.0",
  "author": "your-github-handle",
  "category": "skills",
  "tags": ["relevant", "searchable", "tags"],
  "pricing_model": "free",
  "license": "Apache-2.0"
}
```

## Revenue Sharing

Creators earn **70%** of all credit purchases for premium listings. ProwlrBot takes 30% to keep the lights on.

| Tier | Monthly | Credits | Access |
|:-----|:--------|:--------|:-------|
| Free | $0 | 50/mo | All free listings |
| Starter | $5 | 500/mo | + Premium skills |
| Pro | $15 | 2000/mo | + Premium agents, priority |
| Team | $29 | 5000/mo | + Team features, bulk |

## The Ecosystem

| Repo | Role |
|:-----|:-----|
| [prowlrbot](https://github.com/ProwlrBot/prowlrbot) | Core platform — CLI, agents, channels, providers |
| **prowlr-marketplace** (you are here) | Community registry |
| [roar-protocol](https://github.com/ProwlrBot/roar-protocol) | Agent communication protocol spec |
| [prowlr-docs](https://github.com/ProwlrBot/prowlr-docs) | Documentation |
| [agentverse](https://github.com/ProwlrBot/agentverse) | Virtual world for agents |

---

<p align="center">
  <sub>Built by the pack. For the pack.</sub><br/>
  <sub>Got a listing idea? <a href="https://github.com/ProwlrBot/prowlr-marketplace/issues">Open an issue</a> — we're all ears.</sub>
</p>
