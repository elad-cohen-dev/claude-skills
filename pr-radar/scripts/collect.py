#!/usr/bin/env python3
"""pr-radar collector: bucket a team's open PRs using the gh CLI (stdlib only).

Auth is gh's own. On multi-account machines export GH_TOKEN=$(gh auth token -u <acct>) first.

Usage:
  collect.py --org ORG --repos a,b --me LOGIN [--team l1,l2] [--stale-days 2]
             [--large 600] [--protected main,master] [--search-team]
Prints one JSON object to stdout.
"""
import argparse, datetime as dt, json, subprocess, sys

FIELDS = ("number,title,author,url,createdAt,updatedAt,isDraft,baseRefName,headRefName,"
          "mergeable,reviewDecision,reviewRequests,latestReviews,statusCheckRollup,"
          "additions,deletions,changedFiles")
FAILED = {"FAILURE", "ERROR", "TIMED_OUT", "STARTUP_FAILURE", "CANCELLED", "ACTION_REQUIRED"}


def gh(args):
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        sys.exit("gh CLI not found")
    if r.returncode:
        return None, r.stderr.strip()
    return json.loads(r.stdout or "null"), None


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def checks(roll):
    if not roll:
        return "none", []
    failing = [c.get("name") or c.get("context") for c in roll
               if (c.get("conclusion") or c.get("state")) in FAILED]
    if failing:
        return "failing", failing
    if any(c.get("status") in ("PENDING", "IN_PROGRESS", "QUEUED") or
           (c.get("conclusion") is None and c.get("state") in (None, "PENDING")) for c in roll):
        return "pending", []
    return "passing", []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", required=True)
    ap.add_argument("--repos", required=True)
    ap.add_argument("--me", required=True)
    ap.add_argument("--team", default="")
    ap.add_argument("--stale-days", type=float, default=2)
    ap.add_argument("--large", type=int, default=600)
    ap.add_argument("--protected", default="main,master")
    ap.add_argument("--search-team", action="store_true",
                    help="also find team PRs in repos outside --repos")
    a = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    repos = [r.strip() for r in a.repos.split(",") if r.strip()]
    team = [t.strip() for t in a.team.split(",") if t.strip()]
    protected = set(a.protected.split(","))
    errors, prs = [], []

    for repo in repos:
        data, err = gh(["pr", "list", "-R", f"{a.org}/{repo}", "--state", "open",
                        "--limit", "100", "--json", FIELDS])
        if err:
            errors.append(f"{repo}: {err}")
            continue
        for p in data:
            reviews = p.get("latestReviews") or []
            my_review = next((r for r in reviews if (r.get("author") or {}).get("login") == a.me), None)
            last_commit = None
            if my_review and my_review.get("state") in ("CHANGES_REQUESTED", "COMMENTED"):
                c, _ = gh(["api", f"repos/{a.org}/{repo}/pulls/{p['number']}/commits?per_page=100",
                           "--jq", "[.[-1].commit.committer.date]"])
                last_commit = ts(c[0]) if c else None
            state, failing = checks(p.get("statusCheckRollup") or [])
            requested = [(x.get("login") or x.get("slug") or x.get("name") or "")
                         for x in (p.get("reviewRequests") or [])]
            prs.append({
                "repo": repo, "number": p["number"], "title": p["title"], "url": p["url"],
                "author": (p.get("author") or {}).get("login", ""),
                "draft": p.get("isDraft", False), "base": p.get("baseRefName", ""),
                "head": p.get("headRefName", ""),
                "age_d": round((now - ts(p["createdAt"])).total_seconds() / 86400, 1),
                "idle_d": round((now - ts(p["updatedAt"])).total_seconds() / 86400, 1),
                "size": (p.get("additions") or 0) + (p.get("deletions") or 0),
                "files": p.get("changedFiles") or 0,
                "decision": p.get("reviewDecision") or "",
                "approvals": sum(r.get("state") == "APPROVED" for r in reviews),
                "changes_requested": sum(r.get("state") == "CHANGES_REQUESTED" for r in reviews),
                "reviewers": sorted({(r.get("author") or {}).get("login", "") for r in reviews}),
                "requested": requested,
                "checks": state, "failing_checks": failing,
                "conflicts": p.get("mergeable") == "CONFLICTING",
                "my_review": my_review.get("state") if my_review else None,
                "pushed_since_my_review": bool(my_review and last_commit and
                                               last_commit > ts(my_review.get("submittedAt"))),
            })

    def slim(p, why):
        keys = ("repo", "number", "title", "url", "author", "age_d", "idle_d", "size",
                "checks", "failing_checks", "conflicts", "approvals", "requested")
        return {**{k: p[k] for k in keys}, "why": why}

    b = {k: [] for k in ("waiting_on_me", "needs_first_review", "ready_to_merge",
                         "failing_ci", "conflicts", "stale", "oversized", "my_open")}
    for p in prs:
        if p["author"] == a.me:
            b["my_open"].append(slim(p, p["decision"] or ("draft" if p["draft"] else "open")))
        if p["draft"]:
            continue
        if a.me in p["requested"]:
            b["waiting_on_me"].append(slim(p, "review requested"))
        elif p["my_review"] in ("CHANGES_REQUESTED", "COMMENTED") and p["pushed_since_my_review"]:
            b["waiting_on_me"].append(slim(p, f"new commits since your {p['my_review'].lower()} review"))
        if p["approvals"] and not p["changes_requested"]:
            if p["checks"] in ("passing", "none") and not p["conflicts"]:
                b["ready_to_merge"].append(slim(p, "approved + green"))
        elif not p["approvals"] and not [r for r in p["reviewers"] if r != p["author"]]:
            why = "no reviewer yet" + ("" if p["requested"] else ", none requested")
            if p["base"] not in protected:
                why += f" (targets {p['base']})"
            b["needs_first_review"].append(slim(p, why))
        if p["checks"] == "failing":
            b["failing_ci"].append(slim(p, ", ".join(p["failing_checks"][:3])))
        if p["conflicts"]:
            b["conflicts"].append(slim(p, "merge conflicts"))
        if p["idle_d"] >= a.stale_days:
            b["stale"].append(slim(p, f"idle {p['idle_d']}d"))
        if p["size"] >= a.large:
            b["oversized"].append(slim(p, f"{p['size']} lines / {p['files']} files"))
    for v in b.values():
        v.sort(key=lambda x: -x["idle_d"])

    load = []
    for login in team:
        load.append({
            "login": login,
            "open_authored": sum(p["author"] == login and not p["draft"] for p in prs),
            "reviews_pending": sum(login in p["requested"] for p in prs),
            "oldest_pending_review_d": max([p["idle_d"] for p in prs if login in p["requested"]],
                                           default=0),
        })

    outside = []
    if a.search_team and team:
        for login in team:
            data, err = gh(["search", "prs", "--owner", a.org, "--author", login, "--state", "open",
                            "--json", "repository,number,title,url,updatedAt", "--limit", "30"])
            for p in data or []:
                repo = (p.get("repository") or {}).get("name", "")
                if repo not in repos:
                    outside.append({"repo": repo, "number": p["number"], "title": p["title"],
                                    "url": p["url"], "author": login})

    json.dump({"generated_at": now.isoformat(timespec="minutes"), "me": a.me,
               "totals": {"open": len(prs), "drafts": sum(p["draft"] for p in prs)},
               "buckets": b, "review_load": load, "outside_repos": outside,
               "errors": errors}, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
