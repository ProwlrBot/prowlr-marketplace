# Publishing Guide

How to publish your skill, MCP server, agent, or workflow to the ProwlrBot Marketplace.

---

## Step 1: Choose a Category

| Category | Template | What to build |
|----------|----------|--------------|
| Skills | `templates/skill-template/` | Agent capability packs with SKILL.md manifest |
| MCP Servers | `templates/mcp-server-template/` | MCP stdio servers with manifest.json |
| Workflows | `templates/workflow-template/` | Multi-step automation recipes |
| Agents | (coming soon) | Pre-built agent configs |
| Prompts | (coming soon) | System prompt templates |
| Themes | (coming soon) | Console UI themes |

## Step 2: Build It

1. Copy the appropriate template
2. Replace placeholder values with your actual content
3. Add your code, scripts, and documentation
4. Test locally with ProwlrBot

## Step 3: Test Locally

### Skills
```bash
prowlr skills add ./my-skill/
# Then ask your agent to use the skill
```

### MCP Servers
```bash
claude mcp add my-server -- python3 -m my_package.server
# Then restart Claude Code and verify tools appear
```

## Step 4: Submit a PR

```bash
git checkout -b add-my-item
git add community/<category>/my-item/
git commit -m "feat: add my-item to marketplace"
git push origin add-my-item
```

Open a PR against `main`. Include:
- Description of what your item does
- How to test it
- Screenshots if applicable

## Review Criteria

| Criterion | Required | Notes |
|-----------|----------|-------|
| Working code | Yes | Must function as described |
| Security | Yes | No hardcoded secrets, no shell injection |
| Documentation | Yes | Clear description, usage examples |
| Tests | Recommended | At least basic functionality tests |
| License | Yes | Apache-2.0, MIT, or BSD |
| Compatibility | Yes | Python 3.10+, current ProwlrBot |

## After Approval

Your item appears in the marketplace catalog. Users can install it with:

```bash
prowlr marketplace install your-item-name
```

## Paid Items

To monetize your item (70/30 revenue split):

1. Set `"pricing": {"type": "paid", "amount": 9.99, "currency": "USD"}` in your manifest
2. Set up a Stripe Connect account
3. Add your Stripe account ID to the manifest

See [revenue-sharing.md](revenue-sharing.md) for details.
