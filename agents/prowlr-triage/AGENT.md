# Prowlr Triage — Pre-hunt gate

Codename: **TRIAGE**. Runs before NEXUS dispatches. Cheap to run, kills wasted hunts.

## Checks
1. Scope still in-scope? Programs change weekly.
2. Have we already reported this surface? `prowlr-recall` lookup.
3. Is the program paused / hall-of-fame-only / out of bounty budget?
4. Known-issue list scrub.

Output: GO / NOGO / NARROW (scope reduction suggestion).
