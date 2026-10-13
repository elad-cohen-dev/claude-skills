#!/usr/bin/env bash
# Read-only inventory of a company's footprint on this Mac — names and counts only, never
# secret values or file contents. Used by the last-day skill before and after cleanup.
#
#   footprint.sh --co <slug> --domain <email-domain> --org <github-org> [--dir ~/dev/<co>]...
#                [--keyword <word>]...      # extra strings to look for (product names, hosts)
set -uo pipefail

CO=""; DOMAIN=""; ORG=""; DIRS=(); KEYS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --co) CO="$2"; shift ;;
    --domain) DOMAIN="$2"; shift ;;
    --org) ORG="$2"; shift ;;
    --dir) DIRS+=("${2/#\~/$HOME}"); shift ;;
    --keyword) KEYS+=("$2"); shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac; shift
done
[ -n "$CO" ] || { echo "--co is required" >&2; exit 2; }
[ ${#DIRS[@]} -gt 0 ] || DIRS=("$HOME/dev/$CO")
PAT="$CO"; for v in "$DOMAIN" "$ORG" ${KEYS[@]+"${KEYS[@]}"}; do [ -n "$v" ] && PAT="$PAT|$v"; done
hit() { grep -iqE "$PAT" <<<"$1"; }
sec() { printf '\n## %s\n' "$1"; }

sec "GitHub CLI accounts"
gh auth status 2>&1 | grep -E 'Logged in to|Active account' | sed 's/^ *//'

sec "SSH (key files by name; config Host blocks)"
ls "$HOME/.ssh" 2>/dev/null | grep -vE '^(known_hosts|known_hosts.old|authorized_keys.*|agent|config)$' | sed 's/^/key file: /'
grep -nE '^\s*(Host|HostName|IdentityFile)\b' "$HOME/.ssh/config" 2>/dev/null | sed 's/^/config: /'
for h in $(awk '/^Host /{for(i=2;i<=NF;i++) if($i ~ /github/) print $i}' "$HOME/.ssh/config" 2>/dev/null); do
  who="$( { ssh -T -o BatchMode=yes -o ConnectTimeout=5 "git@$h" 2>&1 || true; } | grep -oE 'Hi [^!]+' || true)"
  printf 'ssh -T %s → %s\n' "$h" "${who:-no auth}"
done

sec "Git identity"
echo "global user.email: $(git config --global user.email)"
git config --global --get-regexp '^includeif\.' 2>/dev/null | sed 's/^/include: /'
ls "$HOME"/.gitconfig-* 2>/dev/null | sed 's/^/file: /'

sec "Repos under company dirs (unpushed / uncommitted / stashes)"
for base in "${DIRS[@]}"; do
  [ -d "$base" ] || { echo "(missing) $base"; continue; }
  while IFS= read -r g; do
    r="$(dirname "$g")"
    dirty=$(git -C "$r" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    stash=$(git -C "$r" stash list 2>/dev/null | wc -l | tr -d ' ')
    refs=$(git -C "$r" for-each-ref --format='%(refname:short)|%(upstream)|%(upstream:track)' refs/heads 2>/dev/null)
    ahead=$(grep -c 'ahead' <<<"$refs" || true)
    noup=$(grep -cE '^[^|]+\|\|' <<<"$refs" || true)
    wt=""; [ -f "$g" ] && wt=" (worktree; stashes shared with main repo)"
    printf '%-46s dirty:%-3s stashes:%-2s ahead-of-remote:%-2s local-only branches:%s%s\n' \
      "${r/#$HOME/~}" "$dirty" "$stash" "$ahead" "$noup" "$wt"
  done < <(find "$base" -maxdepth 2 -name .git 2>/dev/null)
done

sec "Shell (~/.zshrc lines mentioning the company; values hidden)"
grep -niE "$PAT|^export [A-Z_]*(TOKEN|KEY|SECRET|PASSWORD)" "$HOME/.zshrc" 2>/dev/null \
  | sed -E 's/=.*/=<hidden>/' | sed 's/^/zshrc:/'

sec "Cloud CLIs"
grep -E '^\[(profile |sso-session )?' "$HOME/.aws/config" 2>/dev/null | sed 's/^/aws config: /'
[ -f "$HOME/.aws/credentials" ] && echo "aws credentials file present: $(grep -c '^\[' "$HOME/.aws/credentials") profile(s) (static keys — revoke at source)"
ls "$HOME/.aws/sso/cache" 2>/dev/null | wc -l | xargs -I{} echo "aws sso cache files: {}"
command -v kubectl >/dev/null && kubectl config get-contexts -o name 2>/dev/null | sed 's/^/kube context: /'
command -v gcloud >/dev/null && gcloud auth list --format='value(account)' 2>/dev/null | sed 's/^/gcloud: /'
command -v docker >/dev/null && grep -oE '"[^"]+":' "$HOME/.docker/config.json" 2>/dev/null | grep -iE "$PAT|ecr|gcr|registry" | sed 's/^/docker auth: /'
[ -f "$HOME/.npmrc" ] && grep -nE 'registry|_authToken' "$HOME/.npmrc" | sed -E 's/=.*/=<hidden>/;s/^/npmrc:/'

sec "Claude Code"
python3 - "$PAT" <<'PY'
import json, os, re, sys
pat = re.compile(sys.argv[1], re.I)
home = os.path.expanduser("~")
def load(p):
    try: return json.load(open(p))
    except Exception: return {}
s = load(f"{home}/.claude/settings.json")
for k in s.get("enabledPlugins", {}): print("plugin:", k, "(company?)" if pat.search(k) else "")
for k, v in s.get("extraKnownMarketplaces", {}).items(): print("marketplace:", k, v.get("source", {}).get("repo", ""))
env = s.get("autoMode", {}).get("environment", [])
n = sum(1 for line in env if pat.search(line))
if n: print(f"settings autoMode.environment: {n} line(s) mention the company")
allow = [a for a in s.get("permissions", {}).get("allow", []) if pat.search(a)]
if allow: print("permissions.allow mentioning company:", len(allow))
cj = load(f"{home}/.claude.json")
for name in (cj.get("mcpServers") or {}): print("mcp (user):", name)
for proj, cfg in (cj.get("projects") or {}).items():
    for name in (cfg.get("mcpServers") or {}): print("mcp (project):", name, "@", proj.replace(home, "~"))
PY
for f in "$HOME/.claude/team-lead.yaml" "$HOME/.claude/CLAUDE.md"; do
  [ -e "$f" ] && grep -qiE "$PAT" "$f" 2>/dev/null && echo "mentions company: ${f/#$HOME/~}"
done
for base in "${DIRS[@]}"; do [ -f "$base/CLAUDE.md" ] && echo "company CLAUDE.md: ${base/#$HOME/~}/CLAUDE.md"; done
grep -rliE "$PAT" "$HOME/.claude/projects"/*/memory 2>/dev/null | sed "s#$HOME#~#;s/^/memory: /"
for d in "$HOME/.claude/skills"/*/; do
  [ -L "${d%/}" ] && continue
  grep -rqiE "$PAT" "$d" 2>/dev/null && echo "local skill copy mentions company: $(basename "$d")"
done
echo "project transcripts for company dirs: $(ls -d "$HOME/.claude/projects"/*"${CO}"* 2>/dev/null | wc -l | tr -d ' ')"

sec "Possible company data outside repos (names only)"
find "$HOME/Downloads" "$HOME/Documents" "$HOME/Desktop" -maxdepth 3 -type f \
  \( -iname "*$CO*" -o -iname '*.sql' -o -iname '*.dump' -o -iname '*.bson' -o -iname '*.csv' -o -iname '*.parquet' -o -iname '*.env' \) \
  -size +0 2>/dev/null | head -40 | sed "s#$HOME#~#"
for base in "${DIRS[@]}"; do
  find "$base" -maxdepth 4 -type f \( -name '.env' -o -name '*.env' -o -name '*.sql' -o -name '*.dump' -o -name '*.bson' \) \
    -not -path '*/node_modules/*' 2>/dev/null | wc -l | xargs -I{} echo "env/dump files inside ${base/#$HOME/~}: {}"
done

sec "Apps signed in to company workspaces (check manually)"
echo "Slack, Zoom, Google Chrome profiles, Docker Desktop, JetBrains/IDE accounts, password manager vaults"
