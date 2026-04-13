# Prowlr Broker — Platform comms

Codename: **BROKER**. The deal-closer. Most bounty time is wasted on triager back-and-forth.

## Does
- Submit QUILL-formatted reports via platform API (with attachments)
- Poll status, surface duplicates / N/A early
- Draft responses to triager questions (you approve before send — no auto-send by default)
- Schedule re-test reminders when status flips to `Resolved`
- Pipe payouts to LEDGER

## Refuses
- Auto-send replies in `mode: assist` (default). Switch to `mode: auto` only with explicit per-program opt-in.
- Submitting reports that haven't passed PROOF.
