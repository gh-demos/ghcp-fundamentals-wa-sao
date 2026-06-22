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

## Ticket Triage Policy

Triage happens daily. Use the table below to set Severity, then derive the default Priority.

### Priority levels

| Priority | Default Severity | Definition |
|----------|-----------------|------------|
| **P0** Critical | High (outage) | Production down or active data loss — respond immediately, 24/7 |
| **P1** High | High | Core feature broken, no workaround — fix within one business day |
| **P2** Medium | Medium | Meaningful impact, workaround available — resolve this sprint |
| **P3** Low | Low | Minor annoyance or cosmetic issue — schedule for a future sprint |

### How to triage in 60 seconds

1. **Read the ticket** — what's broken and who's affected?
2. **Assign Severity** — High (blocks workflows / data loss) · Medium (workaround exists) · Low (minor).
3. **Set Priority** — use the table above; bump to P0 if production is actively down.
4. **Label & route** — apply the P0–P3 label; assign to on-call for P0/P1, backlog for P2/P3.
