# First day at a new company

A three-part path: install (`setup.sh`), then logins and the company setup (`/first-day` in Claude Code),
then the human side (this checklist).

## 0. Install

```bash
curl -fsSL https://raw.githubusercontent.com/elad-cohen-dev/claude-skills/main/bootstrap/setup.sh | bash
# re-run any step later:  ~/dev/personal/claude-skills/bootstrap/setup.sh --only plugins,skills
# preview first:          ... setup.sh --dry-run
```

It installs:
- **CLI:** git, gh, jq, ripgrep, tmux, uv, pyenv (Python 3.12), poetry, nvm (Node LTS), awscli, kubectl, pre-commit and docker-compose.
- **Apps:** Ghostty, PyCharm, Docker Desktop, MongoDB Compass, Raycast, Slack, Zoom and Chrome.
- **Shell:** oh-my-zsh, plus a marked block in `~/.zshrc` (PATH, nvm, pyenv and the `claude-yolo` alias).
- **Claude Code:** your portable settings (model, effort, status line via ccusage), the plugins (context7, atlassian, answer-me-with-html) and every skill and agent from this repo, symlinked so `git pull` keeps them current.

Then run `cd ~/dev && claude` and type `/first-day`.

## 1. Accounts and security (morning)

- [ ] Laptop: FileVault on, OS updated, IT/MDM agents installed by IT (don't fight them)
- [ ] SSO / identity provider and a password manager. Enroll 2FA on a hardware key or authenticator, never SMS if avoidable.
- [ ] Email, calendar (set working hours and time zone), Slack (profile photo, title, pronouns, time zone)
- [ ] GitHub: get added to the org with your work account, and check whether SSO is enforced for tokens and SSH keys
- [ ] Jira, Confluence or Notion, CI system, error tracker, log and metrics dashboards
- [ ] Cloud console access and VPN. Request **read-only** prod access first.
- [ ] HR, payroll and benefits forms. Find the expense and equipment policy.

## 2. People (first two weeks)

- [ ] 1:1 with your manager: expectations for 30/60/90 days, how success is measured, communication style, the team's top problem
- [ ] 1:1 with every report (team lead): their goals, what's frustrating, what they want more or less of from you, preferred feedback style
- [ ] Intros with peer leads, PM, design, QA, DevOps/SRE, support. Ask each: "What should I know that nobody will tell me?"
- [ ] Skip-level meeting
- [ ] Join the team channels, the incident/alerts channel and on-call rotation docs. Mute the noisy ones.
- [ ] Put recurring 1:1s on the calendar before the week fills up

## 3. Learn the system (week one)

- [ ] Run the main service locally end-to-end. Every README gap you hit is a first PR.
- [ ] Ship one small PR to production and learn the full path: review, CI, deploy and verify
- [ ] Read the architecture docs and recent incident postmortems
- [ ] Map who owns which service and where alerts go (`/first-day` drafts this into your notes)
- [ ] Shadow on-call or a deploy
- [ ] Read the current sprint and roadmap, then run `/sprint-pulse` and `/pr-radar` to see the team's flow

## 4. Team-lead questions to answer by day 30

- What does the team ship, how often, and what slows it down most?
- Where does work come from (roadmap, support, incidents), and who decides priority?
- What's the review culture (turnaround, size, who reviews)? `/pr-radar` gives data.
- Which rituals exist (standup, planning, retro, demo), and which of them help?
- Where is the tech debt that hurts, and is it written down?
- Who is ready for more scope, and who needs support?

## 5. Don't forget

- [ ] Personal and work separation: personal repos use your personal gh account; `~/dev/<co>/` uses the work identity (`/first-day` step 1)
- [ ] Never commit company names, ids or tokens into the personal skills repo. Company facts live in `~/dev/<co>/CLAUDE.md`, `~/.claude/team-lead.yaml` and `~/.zshrc`.
- [ ] Keep a running "first-week.md" (created by `/first-day`). Write down everything confusing. Fresh eyes expire after about 6 weeks.
