# Copilot Agents Demo

Use the following 3 files to setup your Copilot Agents demo. 
Paste the ISSUE.md file into a new issue in that repository. 

## What this demo shows
- Assign an issue to Copilot to start an agent task
- Monitor progress in AgentHQ
- Re-steer mid-session with a new requirement
- Review the resulting PR like a teammate’s work

## Demo files
- `ISSUE.md` contains the exact issue text to copy/paste into GitHub
- `STEER.md` contains the mid-session requirement change to paste while the agent is working

## Quick demo steps
1. Create a new GitHub Issue by copying the Title and Body from `ISSUE.md`
2. Assign the issue to Copilot to start the agent task
3. Open AgentHQ to monitor progress
4. Paste `STEER.md` into the agent session to re-steer the work
5. Review the PR diff for clarity, completeness, and constraints.
6. Verify the PR edited the README.md file by adding priority levels plus the steered examples. 

---

## Ticket Triage Policy (Current)

We currently triage support tickets using Severity only.

### Severity levels
- Low means minor annoyance with an easy workaround
- Medium means a meaningful user impact but workarounds exist
- High means blocks key workflows or causes data loss

### Current rules
- Triage happens daily
- High severity should be addressed first
- We do not currently define priority labels, default ownership, or a fast triage checklist

---

## Priority Levels

| Priority | Label | Definition |
|----------|-------|------------|
| P0 | Critical | Production is down or data loss is actively occurring. Requires immediate response 24/7. |
| P1 | High | Core functionality is broken for many users with no workaround. Must be addressed within one business day. |
| P2 | Medium | Meaningful user impact exists but a workaround is available. Target resolution within the current sprint. |
| P3 | Low | Minor annoyance or cosmetic issue with little user impact. Schedule for a future sprint. |

## Severity → Priority Mapping

| Severity | Default Priority |
|----------|-----------------|
| High | P0 or P1 (P0 if production is down, P1 otherwise) |
| Medium | P2 |
| Low | P3 |

## How to Triage in 60 Seconds

1. **Read the ticket** — understand what is broken and who is affected.
2. **Assign a Severity** — High / Medium / Low based on user impact.
3. **Set the default Priority** — use the Severity → Priority mapping above.
4. **Adjust if needed** — bump up to P0 if production is down; bump down if impact is narrower than it appears.
5. **Add a label** — apply the matching priority label (P0 / P1 / P2 / P3) in GitHub.
6. **Route it** — assign to the on-call engineer for P0/P1, or to the backlog for P2/P3.
