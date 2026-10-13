#!/usr/bin/env python3
"""sprint-pulse helper: map Jira keys -> PRs by scanning PR titles, branches and bodies.

One gh call per repo (not per ticket). Auth is gh's own; on multi-account machines
export GH_TOKEN=$(gh auth token -u <acct>) first.

Usage:
  link_prs.py --org ORG --repos a,b --projects ABC,DEF --since 2026-09-14
Prints JSON: {"links": {"ABC-12": [{repo, number, state, url, merged_at, ...}]}, "errors": [...]}
"""
import argparse, json, re, subprocess, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", required=True)
    ap.add_argument("--repos", required=True)
    ap.add_argument("--projects", required=True, help="Jira project keys, comma-separated")
    ap.add_argument("--since", required=True, help="YYYY-MM-DD, usually the sprint start")
    a = ap.parse_args()

    keys = "|".join(re.escape(k.strip()) for k in a.projects.split(",") if k.strip())
    key_re = re.compile(rf"\b({keys})-\d+\b", re.I)
    links, errors = {}, []

    for repo in [r.strip() for r in a.repos.split(",") if r.strip()]:
        r = subprocess.run(
            ["gh", "pr", "list", "-R", f"{a.org}/{repo}", "--state", "all", "--limit", "300",
             "--search", f"updated:>={a.since}",
             "--json", "number,title,headRefName,body,state,isDraft,url,author,mergedAt,"
                       "reviewDecision,updatedAt"],
            capture_output=True, text=True, timeout=120)
        if r.returncode:
            errors.append(f"{repo}: {r.stderr.strip()}")
            continue
        for p in json.loads(r.stdout or "[]"):
            text = " ".join([p.get("title") or "", p.get("headRefName") or "", p.get("body") or ""])
            for key in {m.group(0).upper() for m in key_re.finditer(text)}:
                links.setdefault(key, []).append({
                    "repo": repo, "number": p["number"], "url": p["url"],
                    "state": "DRAFT" if p.get("isDraft") and p["state"] == "OPEN" else p["state"],
                    "review": p.get("reviewDecision") or "",
                    "author": (p.get("author") or {}).get("login", ""),
                    "merged_at": p.get("mergedAt"), "updated_at": p.get("updatedAt"),
                })

    json.dump({"links": links, "errors": errors}, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
