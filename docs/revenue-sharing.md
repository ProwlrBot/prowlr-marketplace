# Revenue Sharing

The ProwlrBot Marketplace supports both free and paid items.

---

## Free Items

Most items are free and open source. No setup needed — just submit a PR.

## Paid Items

Creators keep **70%** of revenue. The platform takes **30%** for hosting, review, and infrastructure.

### Setup

1. Create a [Stripe Connect](https://stripe.com/connect) account
2. Add pricing to your manifest:

```json
{
  "pricing": {
    "type": "paid",
    "amount": 9.99,
    "currency": "USD"
  },
  "stripe_account_id": "acct_..."
}
```

3. Submit your item as usual

### Pricing Guidelines

| Item Type | Suggested Range | Notes |
|-----------|----------------|-------|
| Skills | Free – $19.99 | Simple skills should be free |
| MCP Servers | Free – $49.99 | Complex integrations can charge more |
| Workflows | Free – $29.99 | Multi-step automations |
| Themes | Free – $9.99 | UI customizations |
| Agents | Free – $29.99 | Pre-built agent configs |

### Payouts

- Monthly payouts via Stripe
- Minimum payout: $10
- Dashboard shows sales, revenue, and download stats

---

## Questions?

Open an issue at [github.com/ProwlrBot/prowlr-marketplace/issues](https://github.com/ProwlrBot/prowlr-marketplace/issues).
