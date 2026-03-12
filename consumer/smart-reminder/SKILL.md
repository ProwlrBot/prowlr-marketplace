---
name: Smart Reminder
description: Context-aware reminders that adapt to your schedule — just tell it what to remember in plain language.
version: 1.1.0
author: ProwlrBot Team
category: skills
---

# Smart Reminder

Your brain is terrible at remembering to do things at the right time. You remember the dentist appointment in the shower, the passport renewal at the airport, and the free trial cancellation the day after you're charged. Smart Reminder lets you say things like "remind me to cancel Netflix before March 20" or "remind me to buy Mom's birthday gift two weeks before May 3" in plain language. It figures out the right timing, sends the reminder where you'll see it, and follows up if you don't act.

## What It Does

- Accepts reminders in natural language — no date pickers, forms, or specific formatting required
- Intelligently schedules the reminder at the right time (not just when it's due, but when you need to act)
- Adapts to your schedule patterns and follows up if you don't respond

## How It Works

1. Tell ProwlrBot what you need to remember, in plain language. That's it.
2. The skill determines the right time to remind you and confirms it.
3. You get reminded at the right moment, in the right channel, with enough context to take action immediately.

## Works With

- Apple Reminders, Google Calendar
- Todoist
- Slack, Telegram, Discord
- Email

## Example Usage

```
YOU: "Remind me to cancel the Hulu free trial before it charges
me on March 20"

SMART REMINDER: Got it! I'll remind you on March 18 (2 days before)
to cancel Hulu. That gives you a buffer in case you're busy.
I'll remind again on March 19 if you haven't marked it done.

---

[March 18, 9:00 AM]

SMART REMINDER: Hey! Your Hulu free trial ends in 2 days (March 20).
Cancel now to avoid the $14.99 charge.

Here's how: Open Hulu > Account > Cancel Subscription
Or go directly to: hulu.com/account

[ Mark as done ]  [ Snooze to tomorrow ]  [ I already cancelled ]

---

YOU: "Remember that I lent Jake my camping gear and he said he'd
return it after Memorial Day"

SMART REMINDER: Noted! I'll remind you on May 27 (day after
Memorial Day) to follow up with Jake about your camping gear.
```
