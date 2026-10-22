---
name: first-day
description: Day-one setup at a new company, run inside Claude Code after bootstrap/setup.sh — work git identity per folder, SSH key and the work GitHub account next to the personal one, Atlassian/Slack connectors, company config for the personal skills (Confluence, team-lead.yaml, golden repos), cloning the team's repos, cloud CLI login, and a first-week notes file with a people/systems map and a 30-60-90 plan. Asks before every step; resumable. Trigger on /first-day, "set up my new job", "first day at the new company", "onboard me to <company>".
argument-hint: "[company name] [--step <name>]"
---

# First Day

The interactive half of joining a new company. `bootstrap/setup.sh` already installed apps,
CLIs, Claude Code, plugins and these skills; this does everything that needs **logins,
company facts or judgment**. It's resumable: progress lives in the notes file (Step 0),
so a second run picks up where the first stopped.

Rules:
- `--dry-run` (or "dry run" in the arguments): run every read-only check for real, show
  each step's exact diffs/commands and its prompt, but write nothing and run no logins.
- One step at a time. Before each, say what it changes and ask (`AskUserQuestion`:
  Do it / Skip / Later). Never batch silent writes.
- **Never ask for, read, echo or store secrets** (tokens, passwords, SSO codes). Interactive
  logins are run by the user with the `!` prefix (e.g. `! gh auth login`); tokens go into
  `~/.zshrc` by the user's own hand.
- Never overwrite existing files — append marked blocks or create new files; show diffs.
- Company names, emails, ids go into **local** files only (`~/.gitconfig-<co>`,
  `~/.claude/team-lead.yaml`, `~/.zshrc`, notes) — never into the personal skills repo.

## Step 0 — Basics and notes file

Ask (one `AskUserQuestion` + free text): company name (`<co>`, lowercase slug), work email,
GitHub org, Jira/Confluence site (`<site>.atlassian.net`) if any, Slack workspace, your role
and team name, manager's name, start date.

Create `~/Documents/<Co>/first-week.md` (ask for another location if preferred) with:

```markdown
# <Co> — first week   (started <date>)
## Setup progress            ← one line per step below: done / skipped / later
## People                    ← name · role · how they relate to me · 1:1 cadence
## Systems map               ← repos, services, environments, dashboards, runbooks
## Glossary                  ← internal names, acronyms
## Open questions
## 30-60-90
```

## Step 1 — Git identity per folder

First check `git config --global user.email`. If it's a **work** address (a previous
company's domain — common when the laptop or habits carry over), propose fixing that first:
set the global email to the personal one, and pin the old company's identity to its folder
with its own `includeIf` + `~/.gitconfig-<oldco>` (ask which folder(s) hold its repos, e.g.
`~/dev/<oldco>/` or the individual repo dirs). Show the diff before writing.

Keep the global identity personal. Add a work identity for `~/dev/<co>/`:

```ini
# appended to ~/.gitconfig
[includeIf "gitdir:~/dev/<co>/"]
    path = ~/.gitconfig-<co>
```
```ini
# ~/.gitconfig-<co>
[user]
    name = <name>
    email = <work email>
[url "git@github.com:<org>/"]
    insteadOf = https://github.com/<org>/
```

`mkdir -p ~/dev/<co>`. Verify: `git -C ~/dev/<co> config user.email` after the first clone.

## Step 2 — SSH key + work GitHub account

Personal repos keep using HTTPS through `gh`; work repos use SSH (the `insteadOf` above),
so the two accounts never fight over the credential helper.

1. `ssh-keygen -t ed25519 -C "<work email>" -f ~/.ssh/id_ed25519_<co>` — the user runs it
   (`! ...`) so they choose the passphrase.
2. Check what already owns `github.com`: `grep -nE '^\s*(Host|IdentityFile)' ~/.ssh/config`
   (names only — never read key files) and `ssh -T -o BatchMode=yes git@github.com`, which
   prints the account the current key authenticates as.
   - **Nothing configured** → append:
     ```
     Host github.com
       AddKeysToAgent yes
       UseKeychain yes
       IdentityFile ~/.ssh/id_ed25519_<co>
     ```
   - **`github.com` already belongs to another account** (personal *or* a previous company's)
     → leave that block untouched and add an alias:
     ```
     Host github-<co>
       HostName github.com
       AddKeysToAgent yes
       UseKeychain yes
       IdentityFile ~/.ssh/id_ed25519_<co>
       IdentitiesOnly yes
     ```
     `IdentitiesOnly yes` stops ssh from offering the other key first. Then change the
     Step 1 `insteadOf` to `[url "git@github-<co>:<org>/"] insteadOf = https://github.com/<org>/`
     (and `git@github.com:<org>/` too, so copied SSH clone URLs also route through the alias).
3. User runs `! gh auth login` (GitHub.com → HTTPS → browser) with the **work** account,
   then `! gh ssh-key add ~/.ssh/id_ed25519_<co>.pub --title "<co> laptop"`.
4. Switch the active account back to personal: `gh auth switch -u <personal>`; work reads
   go through `github.account` in team-lead.yaml (Step 5).
5. Verify **both** setups — the new one works *and* the old one still does:
   - `ssh -T git@github-<co>` (or `git@github.com` if no alias) → `Hi <work-login>!`
   - `ssh -T git@github.com` → still the previous account, if one was there
   - `gh auth status` → every account listed, the personal one active
   - after the first clone in Step 6: `git -C ~/dev/<co>/<repo> remote -v` shows the alias host
   If the org enforces SSO, remind the user to authorize the SSH key and token for the org
   on github.com (Settings → SSH keys / Tokens → Configure SSO).

## Step 3 — Claude Code for this company

- **Connectors**: Atlassian, Slack, Google (Drive/Calendar/Gmail) — the user connects them in
  claude.ai → Settings → Connectors, or `/mcp` for local servers. Verify each with one
  read call (`atlassianUserInfo`, a `slack_search_channels`, etc.).
- **Company plugin marketplace**: ask if the org has one; if so
  `claude plugin marketplace add <org>/<repo>` and install what the team uses.
- **Company context**: create `~/dev/<co>/CLAUDE.md` (local, not committed anywhere) with the
  org, main repos, environments and "never touch" areas — fill it as Steps 6-7 discover
  them. Suggest revisiting auto-mode/permission settings after week one, once real usage shows
  which commands are routine.

## Step 4 — Company config for the personal skills

Each is optional — offer only those whose systems the company uses:
- **confluence / excalidraw-diagrams**: user adds to `~/.zshrc`
  `export CONFLUENCE_BASE_URL=https://<site>.atlassian.net/wiki`,
  `export CONFLUENCE_EMAIL=<work email>`, `export CONFLUENCE_TOKEN=…` (token created at
  id.atlassian.com by the user). Verify with one read-only REST call.
- **code-review-default / codepilot-***: they search "golden repos" (`your-org/*`
  placeholders in `_shared/references/sourcegraph-search.md`). That file is a symlink into the
  personal repo — don't edit it. Instead add a `## Golden repos` section to
  `~/dev/<co>/CLAUDE.md` (the team's 2-3 best-maintained repos, from Step 6); it overrides the
  placeholders whenever Claude runs under `~/dev/<co>/`.
- **epic-breakdown / feature-composer**: nothing to configure — they discover field ids.
- **hld**: add a `## HLD` section to `~/dev/<co>/CLAUDE.md` (template + reference HLD URLs,
  space, roles, request path, deploy-config repo, log/event indexes, E2E suites) — the skill
  lists the fields and asks for any that are missing.

## Step 5 — Team-lead config

Run the setup in `~/.claude/skills/_shared/references/team-lead-config.md` (create a new
`~/.claude/team-lead.yaml`): org + repos, `github.account` = work login, Jira cloud id /
project / team scope, priority names (read them off a real issue — sites differ, e.g. P1/P2
vs Highest/High), roster from recent PR authors, Slack team channel.
Smoke-test: `/pr-radar` and `/sprint-pulse standup`.

## Step 6 — Repos and local environment

- `gh repo list <org> --limit 200 --json name,pushedAt,description` (as the work account) →
  propose the 3-6 most active repos for the user's team; clone the chosen ones into
  `~/dev/<co>/`.
- For the main repo: read README / CONTRIBUTING / Makefile / docker-compose / `.tool-versions`
  / `.nvmrc` / `.python-version`; list the exact steps to run it locally and offer to run them
  one by one. Record gaps ("README says X, reality is Y") in the notes — a great first PR.
- Install the repo's hooks if it uses them (`pre-commit install`).

## Step 7 — Cloud & internal access

Ask which cloud(s). For AWS: user runs `! aws configure sso` per profile; add an alias
(`alias sso-<co>="aws sso login --profile <profile>"`) to `~/.zshrc`. For GCP:
`! gcloud auth login` + `gcloud config set project`. Kubernetes: `kubectl config get-contexts`
— note which contexts are prod and record them in the company CLAUDE.md as protected.
VPN / internal DNS: just note what's needed; IT owns it.

## Step 8 — People and systems map (team-lead lens)

Using whatever is connected (Jira, Slack, GitHub):
- Team roster: recent PR authors + Jira assignees on the team's board + team channel members →
  People table with role guesses for the user to correct.
- Systems: services/repos the team owns, deploy path (CI workflows), dashboards and alert
  channels (search Slack for "alerts", "oncall", "incident").
- Draft the **30-60-90** section: 30 = learn (1:1s with every report and key peers, ship one
  small PR, shadow on-call, map the system), 60 = contribute (own a feature end-to-end, fix one
  process pain), 90 = lead (team rituals tuned, roadmap input, first improvements measured).
- Draft **first 1:1 questions** for reports, manager and peers into Open questions.

## Step 9 — Wrap up

- Update "Setup progress" in the notes file; list everything marked *later* with the exact
  command to finish it.
- Save a project memory: company, start date, notes-file path, work gh account, repo dir.
- Point to `~/dev/personal/claude-skills/bootstrap/FIRST-DAY.md` for the human checklist.
