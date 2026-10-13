---
name: last-day
description: Offboarding when leaving a company — the mirror of first-day. Inventories the company's footprint on this Mac (gh accounts, SSH keys, git identity, unpushed work, shell secrets, AWS/kube/docker auth, Claude Code plugins/MCP/settings/memories, data files), hands over unfinished work, saves the generic parts of your skills and your own non-confidential notes, has you revoke access at the source, then removes local traces step by step with approval and re-runs the inventory until it's clean. Trigger on /last-day, "offboarding", "leaving the company", "my last day", "clean up <company> from my laptop".
argument-hint: "[company slug] [--dry-run] [--step <name>]"
---

# Last Day

Leave cleanly: nothing of yours left behind, nothing of theirs taken along, no access left
dangling. Mirror of `/first-day`. Resumable — progress lives in the notes file.

Rules:
- **Inventory first, then one step at a time.** Before each step show exactly what will
  change (paths, diffs, commands) and ask (`AskUserQuestion`: Do it / Skip / Later).
- **Nothing is deleted without being listed and approved.** Prefer "move to an archive folder
  for 30 days" over `rm` for anything that isn't obviously regenerable; deleting keys, repos
  and data needs a separate explicit yes per item.
- **Never read, print or copy secrets** (key files, token values, `.env` contents). Work with
  names only. Tokens are revoked by the user at the provider; local lines are removed by the
  user or by a shown, approved edit.
- **Company data stays with the company.** Exports are limited to the user's own
  non-confidential notes, reviewed line by line; no code, customer data, internal docs,
  credentials, hostnames or ids.
- `--dry-run`: run the inventory and every read-only check for real, show each step's plan,
  write nothing.

## Step 0 — Scope

Ask: company slug, email domain, GitHub org, company folders (default `~/dev/<co>/`; ask —
older setups often use `~/dev/` itself), extra keywords (product names, internal hosts),
last working day, and **which device**:
- **Company laptop being returned** → focus on handing over work, taking *your* things
  (personal notes, personal-skill improvements), and signing your *personal* accounts out
  (personal gh account, browser profiles, password manager, Claude account). IT wipes the rest.
- **Personal Mac used for work** → full cleanup of the company footprint (Steps 1-7).

Create/continue `~/Documents/<Co>/last-day.md`:
`## Inventory (before)`, `## Handover`, `## Revoked at source`, `## Removed locally`,
`## Kept (and why)`, `## Inventory (after)`.

## Step 1 — Inventory (read-only)

```bash
~/.claude/skills/last-day/scripts/footprint.sh --co <co> --domain <domain> --org <org> \
  --dir <company folder> [--dir …] [--keyword <word> …]
```
Paste the result into the notes under *Inventory (before)* and summarize it as a short
checklist grouped like the steps below. Everything listed must end in Removed, Kept (with a
reason) or Handed over.

## Step 2 — Hand over work (do this while access still works)

- **Uncommitted / stashed / local-only work** (from the inventory): for each repo, show
  `git status --short | head`, `git stash list`, and local-only branches. Per item the user
  picks: push a branch (`git push -u origin <branch>` — through the work account), turn into a
  draft PR, give to a teammate, or drop. Nothing is dropped silently.
- **Open PRs** you authored (`gh search prs --author @me --state open --owner <org>` via the
  work account): reassign, close with a note, or hand to someone — draft the comments.
- **Jira** tickets assigned to you (`assignee = currentUser() AND statusCategory != Done`):
  propose new owners from the team; reassign only on explicit approval per ticket.
- **Handover doc**: draft one page — what you owned, where things live, in-flight work and
  its state, known risks, who to ask. Publish where the team keeps docs (Confluence via the
  `confluence` skill, or paste-ready markdown) — the user approves before publishing.
- Team-lead extras: 1:1 notes and feedback docs belong to the company/HR — hand to the
  manager, don't keep.

## Step 3 — Keep what's yours

- **Personal skills**: run the usual sync — diff local skill copies against the personal repo,
  port only generic improvements, scan for company names/ids, push as the personal account.
  After that, the local copies with company details can be removed (Step 6).
- **Claude memories**: list memory files that mention the company. For each, decide:
  delete (company-specific), or rewrite as a generic lesson into a personal memory/skill
  (e.g. "re-fetch a remote doc before editing it") with every company detail removed — show
  the rewritten text for approval.
- **Your own notes** (first-week.md, career notes, learnings): copy only after a line-by-line
  review that strips confidential content. Performance reviews of others, customer names,
  internal metrics, architecture details stay behind.

## Step 4 — Revoke access at the source (user does it; you prepare the list)

Build a checklist with direct links, the user ticks each off:
- GitHub: remove the SSH key and any personal access tokens from the **work** account
  (Settings → SSH keys / Developer settings); leave the org or let the admin remove you.
- Atlassian API tokens (id.atlassian.com → Security → API tokens), Slack apps/tokens,
  package-registry tokens, cloud access keys (static AWS keys in `~/.aws/credentials` → IAM),
  any OAuth apps you authorized for work.
- Claude: disconnect company connectors (claude.ai → Settings → Connectors) and remove any
  company workspace/org seat if applicable.
- Personal accounts that use the **work email** or the **work phone for 2FA** — move them now
  (this is the one people regret most).

## Step 5 — Sign out locally

Show each command, run after approval:
- `gh auth logout -h github.com -u <work-login>` (only after Step 2 pushes are done)
- `aws sso logout`; list AWS profiles/sso-sessions from the inventory for removal from
  `~/.aws/config` (show the exact blocks); `~/.aws/credentials` profiles → remove after the
  keys are revoked at source.
- `kubectl config delete-context <ctx>` / `delete-cluster` / `delete-user` for company contexts.
- `docker logout <registry>` for company registries; company entries in `~/.npmrc`, pip/uv
  index config.
- Apps: sign out of the company Slack workspace, Zoom, JetBrains/IDE org licences, Chrome
  work profile (remove the profile), password-manager work vault.

## Step 6 — Remove local traces (approval per group)

| Group | What | How |
|---|---|---|
| SSH | company key files + their `~/.ssh/config` block | show the block; move keys to `~/.offboarding-archive/<co>/` first, delete after 30 days |
| Git | company `includeIf` + `~/.gitconfig-<co>`; global identity stays personal | show the diff |
| Shell | company aliases/exports in `~/.zshrc` (names from the inventory) | show the lines; user removes token lines themselves |
| Claude Code | company plugin(s) and marketplace (`claude plugin uninstall`, `claude plugin marketplace remove`), company MCP servers (`claude mcp remove`), company lines in `settings.json` `autoMode.environment` / `permissions`, `~/.claude/team-lead.yaml` (and its symlink target), company `CLAUDE.md`, company memory folders after Step 3, project transcripts for company dirs (`~/.claude/projects/*<co>*`), local skill copies containing company details (re-link them to the personal repo) | diff for settings; list for files |
| Repos | company clones — **only** after the inventory shows no dirty/stash/local-only work for that repo | list sizes; move to archive or delete per repo |
| Data | `.env` files, dumps, CSV/exports, downloads with company/customer data | list by name; delete per item — customer data is never archived, only deleted |

## Step 7 — Verify and wrap up

- Re-run `footprint.sh` with the same arguments; paste under *Inventory (after)*. Anything
  still listed must be in *Kept (and why)* — otherwise loop back.
- Confirm the personal setup still works: `gh auth status` (personal active),
  `git config --global user.email` (personal), personal repo push dry-run
  (`git push --dry-run` in the personal skills repo).
- Save a short personal memory: company left on <date>, and any generic lessons kept.
- Human checklist: return equipment, final expenses, benefits/pension transfer, exit
  interview, say goodbye (and swap personal contacts) with people you want to stay in touch
  with, update LinkedIn/CV with what you shipped (no confidential numbers).
