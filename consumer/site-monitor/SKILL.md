---
name: Site Monitor
description: Uptime, performance, and SSL monitoring for your websites with instant alerts when something goes wrong.
version: 1.0.0
author: ProwlrBot Team
category: skills
---

# Site Monitor

If your website goes down and you don't know about it, your customers do. Site Monitor checks your URLs at regular intervals, measures response time, watches SSL certificate expiry dates, and detects unexpected content changes. When something goes wrong, you get an alert within seconds — not hours later when a customer emails you.

## What It Does

- Checks your websites every 1-15 minutes and alerts you within 30 seconds of downtime
- Tracks response time trends and warns you when performance degrades before it becomes a problem
- Monitors SSL certificates and sends warnings at 30, 14, and 7 days before expiry

## How It Works

1. Add the URLs you want to monitor during setup — homepages, API endpoints, login pages, etc.
2. Set your check frequency and alert preferences.
3. Get instant alerts on downtime and a weekly performance report showing uptime percentage and response trends.

## Works With

- Any public website or API endpoint
- Slack, Discord, Telegram (instant alerts)
- PagerDuty, Email
- Webhooks (for custom integrations)

## Example Usage

```
ALERT: SITE DOWN — mystore.com

Status: HTTP 503 (Service Unavailable)
Detected: March 11, 2:01:34 AM
Last OK: March 11, 2:00:12 AM
Duration so far: 1 minute 22 seconds

Checked from: US-East, US-West, EU-West
  US-East: 503  |  US-West: 503  |  EU-West: 503

This appears to be a full outage (all regions affected).

[ View status page ]  [ Acknowledge ]  [ Mute for 1 hour ]

---

WEEKLY UPTIME REPORT — March 4-10

mystore.com
  Uptime: 99.94% (5 min downtime on March 7)
  Avg response: 342ms (down from 380ms last week)
  SSL expires: April 22 (42 days — no action needed)

api.mystore.com
  Uptime: 100%
  Avg response: 89ms
  SSL expires: April 22 (42 days)

blog.mystore.com
  Uptime: 99.99%
  Avg response: 1,240ms (WARNING: above 1s threshold)
  SSL expires: March 28 (17 days — RENEWAL RECOMMENDED)
  -> Action: Renew SSL certificate for blog.mystore.com soon
```
