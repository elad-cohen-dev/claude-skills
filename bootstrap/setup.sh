#!/usr/bin/env bash
# Day-one setup for a new Mac at a new company.
#
#   curl -fsSL https://raw.githubusercontent.com/elad-cohen-dev/claude-skills/main/bootstrap/setup.sh | bash
#   # or, from a clone:  ./bootstrap/setup.sh [--dry-run] [--only <step>[,<step>]]
#
# Steps: brew, shell, node, python, claude, plugins, skills
# Idempotent: safe to re-run; each step skips what's already there.
# Never touches credentials: logins (gh, Slack, Atlassian, AWS SSO) happen in /first-day.
set -euo pipefail

REPO="${SKILLS_REPO:-elad-cohen-dev/claude-skills}"
SKILLS_DIR="${SKILLS_DIR:-$HOME/dev/personal/claude-skills}"
NODE_VERSION="${NODE_VERSION:-lts/*}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
DRY_RUN=0; ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --only) ONLY="$2"; shift ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac; shift
done

say()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[32m✓\033[0m %s\n' "$*"; }
run()  { if [ "$DRY_RUN" = 1 ]; then echo "    [dry-run] $*"; else eval "$*"; fi; }
want() { [ -z "$ONLY" ] || [[ ",$ONLY," == *",$1,"* ]]; }
have() { command -v "$1" >/dev/null 2>&1; }

# Piped from curl? Clone the repo first and re-run from the clone, so every step has its files.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-.}")" 2>/dev/null && pwd || echo .)"
if [ ! -f "$SCRIPT_DIR/Brewfile" ]; then
  xcode-select -p >/dev/null 2>&1 || { xcode-select --install; echo "Finish the Xcode CLT dialog, then re-run."; exit 1; }
  [ -d "$SKILLS_DIR/.git" ] || git clone "https://github.com/$REPO.git" "$SKILLS_DIR"
  exec bash "$SKILLS_DIR/bootstrap/setup.sh" "$@"
fi
SKILLS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"   # the clone this script runs from

# Block appended to ~/.zshrc once, between markers, so re-runs replace it in place.
ZSHRC_BLOCK='# >>> new-company bootstrap >>>
export PATH="$HOME/.local/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
[ -s "$(brew --prefix nvm)/nvm.sh" ] && . "$(brew --prefix nvm)/nvm.sh"
eval "$(pyenv init --path)"; eval "$(pyenv init -)"
alias claude-yolo="claude --dangerously-skip-permissions"
# <<< new-company bootstrap <<<'

step_brew() {
  say "Xcode CLT + Homebrew + Brewfile"
  xcode-select -p >/dev/null 2>&1 && ok "Xcode CLT" || { xcode-select --install; echo "Finish the CLT dialog, then re-run."; exit 1; }
  if ! have brew; then
    run '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    run 'eval "$(/opt/homebrew/bin/brew shellenv)"'
  else ok "brew"; fi
  run "brew bundle --file='$SCRIPT_DIR/Brewfile'"
}

step_shell() {
  say "zsh: oh-my-zsh + bootstrap block"
  [ -d "$HOME/.oh-my-zsh" ] && ok "oh-my-zsh" || \
    run 'RUNZSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'
  touch "$HOME/.zshrc"
  if grep -q '>>> new-company bootstrap >>>' "$HOME/.zshrc"; then ok "zshrc block present"
  elif [ "$DRY_RUN" = 1 ]; then echo "    [dry-run] append bootstrap block to ~/.zshrc"
  else printf '\n%s\n' "$ZSHRC_BLOCK" >> "$HOME/.zshrc"; ok "zshrc block added"; fi
  mkdir -p "$HOME/dev" "$HOME/dev/personal"
}

step_node() {
  say "Node ($NODE_VERSION) via nvm + global CLIs"
  export NVM_DIR="$HOME/.nvm"; mkdir -p "$NVM_DIR"
  # shellcheck disable=SC1091
  [ -s "$(brew --prefix nvm)/nvm.sh" ] && . "$(brew --prefix nvm)/nvm.sh"
  run "nvm install '$NODE_VERSION' && nvm alias default '$NODE_VERSION'"
  run "npm install -g ccusage yarn"
}

step_python() {
  say "Python $PYTHON_VERSION via pyenv"
  eval "$(pyenv init --path)"; eval "$(pyenv init -)"
  pyenv versions --bare | grep -q "^$PYTHON_VERSION" && ok "python $PYTHON_VERSION" || run "pyenv install -s '$PYTHON_VERSION'"
  run "pyenv global \$(pyenv versions --bare | grep '^$PYTHON_VERSION' | tail -1)"
}

step_claude() {
  say "Claude Code + portable settings"
  have claude && ok "claude $(claude --version 2>/dev/null | head -1)" || run "curl -fsSL https://claude.ai/install.sh | bash"
  mkdir -p "$HOME/.claude"
  if [ "$DRY_RUN" = 1 ]; then echo "    [dry-run] merge claude-settings.json into ~/.claude/settings.json"; return; fi
  # Merge: existing keys win, permission lists are unioned — never overwrites a company-pushed setting.
  python3 - "$SCRIPT_DIR/claude-settings.json" <<'PY'
import json, os, sys
dst = os.path.expanduser("~/.claude/settings.json")
cur = json.load(open(dst)) if os.path.exists(dst) else {}
new = json.load(open(sys.argv[1]))
for k, v in new.items():
    if k == "permissions":
        p = cur.setdefault("permissions", {})
        p["allow"] = sorted(set(p.get("allow", [])) | set(v.get("allow", [])))
    elif k == "env":
        env = cur.setdefault("env", {})
        for ek, ev in v.items():
            env.setdefault(ek, ev)
    else:
        cur.setdefault(k, v)
json.dump(cur, open(dst, "w"), indent=2)
print("    merged settings ->", dst)
PY
}

step_plugins() {
  say "Claude Code marketplaces + plugins"
  have claude || { echo "    claude not on PATH yet — open a new shell and re-run with --only plugins"; return; }
  for m in anthropics/claude-plugins-official QingYunA/answer-me-with-html; do
    run "claude plugin marketplace add '$m' 2>/dev/null || true"
  done
  for p in context7@claude-plugins-official atlassian@claude-plugins-official \
           answer-me-with-html@answer-me-with-html; do
    run "claude plugin install '$p' 2>/dev/null && echo '    ✓ $p' || echo '    ! $p (install manually: /plugin)'"
  done
}

step_skills() {
  say "Personal skills + agents from github.com/$REPO"
  run "git -C '$SCRIPT_DIR/..' pull --ff-only || true"
  mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents"
  [ "$DRY_RUN" = 1 ] && { echo "    [dry-run] symlink skills/* and agents/*.md into ~/.claude"; return; }
  for d in "$SKILLS_DIR"/*/; do
    n="$(basename "$d")"
    case "$n" in agents|bootstrap) continue ;; esac
    [ -f "$d/SKILL.md" ] || [ "$n" = "_shared" ] || continue
    if [ -e "$HOME/.claude/skills/$n" ] && [ ! -L "$HOME/.claude/skills/$n" ]; then
      echo "    ! skipped $n (a real folder already exists there)"; continue; fi
    ln -sfn "${d%/}" "$HOME/.claude/skills/$n"
  done
  ln -sf "$SKILLS_DIR"/agents/*.md "$HOME/.claude/agents/"
  ok "$(ls "$HOME/.claude/skills" | wc -l | tr -d ' ') skills, $(ls "$HOME/.claude/agents" | wc -l | tr -d ' ') agents linked"
}

for s in brew shell node python claude plugins skills; do want "$s" && "step_$s"; done

say "Done. Next:"
cat <<EOF
    1. Open a new terminal (loads nvm/pyenv/PATH).
    2. Sign in to the apps IT didn't (Slack, Zoom, Chrome profile, Docker Desktop).
    3. Run:  cd ~/dev && claude   then type  /first-day
       It sets up git identity per folder, SSH, the work gh account, Atlassian/Slack,
       team-lead config and your first-week notes — asking before each step.
    Checklist for the human side: $SKILLS_DIR/bootstrap/FIRST-DAY.md
EOF
