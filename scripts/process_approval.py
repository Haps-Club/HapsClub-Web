#!/usr/bin/env python3
"""
process_approval.py — runs when a haps-daily issue is closed.

Decision logic (in priority order):
  1. Issue closed with label `approved-all` → merge pending-review into main
  2. Issue closed with label `rejected`     → delete pending-review, no changes
  3. Issue body or comments contain `approve all` → same as approved-all
  4. Issue body or comments contain `reject all`  → same as rejected
  5. Issue body or comments contain `approve: 1, 3` → partial approval
     (this requires re-parsing the pending-review index.html and removing
     cards that weren't approved, then merging the trimmed version)
  6. None of the above → leave pending-review in place, comment "no decision detected"
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
ISSUE_LABELS = json.loads(os.environ.get("ISSUE_LABELS", "[]"))
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
INDEX_PATH = Path("index.html")
PENDING_BRANCH = "pending-review"


def git(*args: str, check: bool = False) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr}")
    return r.stdout.strip()


def gh_api(method: str, path: str, **kwargs):
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    return requests.request(
        method, f"https://api.github.com/repos/{GH_REPO}{path}",
        headers=headers, timeout=30, **kwargs,
    )


def fetch_all_comments() -> list[str]:
    r = gh_api("GET", f"/issues/{ISSUE_NUMBER}/comments")
    if r.status_code >= 300:
        return []
    return [c.get("body", "") for c in r.json()]


def post_comment(text: str) -> None:
    gh_api("POST", f"/issues/{ISSUE_NUMBER}/comments", json={"body": text})


def detect_decision(all_text: str) -> tuple[str, list[int] | None]:
    """Return (decision, picks) where decision is one of:
    'approve_all', 'reject_all', 'approve_partial', 'none'."""
    if "approved-all" in ISSUE_LABELS:
        return "approve_all", None
    if "rejected" in ISSUE_LABELS:
        return "reject_all", None

    lower = all_text.lower()

    # Partial: "approve: 1, 3" or "approve 1,3"
    match = re.search(r"approve[:\s]+(\d+(?:\s*,\s*\d+)*)", lower)
    if match:
        nums = [int(n) for n in re.findall(r"\d+", match.group(1))]
        if nums:
            return "approve_partial", nums

    if re.search(r"\bapprove\s+all\b", lower):
        return "approve_all", None
    if re.search(r"\breject\s+all\b", lower):
        return "reject_all", None
    return "none", None


def merge_pending_to_main() -> bool:
    """Fast-forward main to pending-review's index.html. Returns True on success."""
    git("config", "user.name", "haps-bot")
    git("config", "user.email", "bot@haps.club")
    # Fetch pending branch
    git("fetch", "origin", PENDING_BRANCH)
    # Checkout its index.html on top of main
    r = subprocess.run(
        ["git", "checkout", f"origin/{PENDING_BRANCH}", "--", "index.html"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"checkout failed: {r.stderr}")
        return False
    # Verify there's actually something to commit
    diff = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "index.html"], capture_output=True)
    if diff.returncode == 0:
        print("nothing changed vs main")
        return False
    git("add", "index.html")
    git("commit", "-m", f"Apply approved picks (issue #{ISSUE_NUMBER})")
    git("push", "origin", "HEAD:main")
    # Clean up the pending branch
    git("push", "origin", "--delete", PENDING_BRANCH)
    return True


def apply_partial_approval(approved_nums: list[int]) -> bool:
    """Pull pending-review's index.html, remove cards corresponding to numbers
    NOT in approved_nums (preserving order from the issue body), then merge."""
    git("config", "user.name", "haps-bot")
    git("config", "user.email", "bot@haps.club")
    git("fetch", "origin", PENDING_BRANCH)
    r = subprocess.run(
        ["git", "checkout", f"origin/{PENDING_BRANCH}", "--", "index.html"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"checkout failed: {r.stderr}")
        return False

    # Parse the new-picks list from the original issue body to map numbers → URLs
    body_picks = parse_issue_picks(ISSUE_BODY)
    if not body_picks:
        post_comment("⚠️ Couldn't parse the numbered pick list from the original issue. "
                     "Manually edit `index.html` on `main` instead.")
        return False

    keep_urls = {body_picks[n - 1]["url"] for n in approved_nums if 1 <= n <= len(body_picks)}
    remove_urls = {p["url"] for i, p in enumerate(body_picks, 1) if i not in approved_nums}

    soup = BeautifulSoup(INDEX_PATH.read_text(encoding="utf-8"), "html.parser")
    removed_count = 0
    for card in soup.select("article.card, a.card.card-compact"):
        url = card.get("data-event-url") or card.get("href")
        if url and url in remove_urls and url not in keep_urls:
            card.decompose()
            removed_count += 1

    # Refresh group counts
    for section in soup.select("section.stack-group"):
        cards = section.select("article.card, a.card.card-compact")
        badge = section.find("span", class_="group-count")
        if badge:
            n = len(cards)
            badge.string = f"{n} picks" if n != 1 else "1 pick"

    INDEX_PATH.write_text(str(soup), encoding="utf-8")

    diff = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "index.html"], capture_output=True)
    if diff.returncode == 0:
        print("nothing changed after partial filter")
        return False

    git("add", "index.html")
    git("commit", "-m", f"Apply partial approval (issue #{ISSUE_NUMBER}): kept {sorted(approved_nums)}, removed {removed_count}")
    git("push", "origin", "HEAD:main")
    git("push", "origin", "--delete", PENDING_BRANCH)
    return True


def parse_issue_picks(body: str) -> list[dict]:
    """Extract the numbered picks from the issue body. Order = pick number."""
    picks = []
    # Match "**N. headline**" headers
    pattern = re.compile(
        r"\*\*(\d+)\.\s+(.+?)\*\*.*?🔗\s+(\S+)",
        re.DOTALL,
    )
    for m in pattern.finditer(body):
        picks.append({
            "n": int(m.group(1)),
            "headline": m.group(2).strip(),
            "url": m.group(3).strip(),
        })
    picks.sort(key=lambda p: p["n"])
    return picks


def delete_pending_branch() -> None:
    git("push", "origin", "--delete", PENDING_BRANCH)


def main() -> int:
    if not GH_TOKEN or not GH_REPO or not ISSUE_NUMBER:
        print("Missing GH_TOKEN / GH_REPO / ISSUE_NUMBER", file=sys.stderr)
        return 2

    # Gather all text — issue body + every comment — to look for decisions
    comments = fetch_all_comments()
    all_text = ISSUE_BODY + "\n\n" + "\n\n".join(comments)

    decision, approved_nums = detect_decision(all_text)
    print(f"[decision] {decision} approved={approved_nums}")

    if decision == "approve_all":
        if merge_pending_to_main():
            post_comment("✅ Approved all. Merged into `main`. Site updates within 60 seconds.")
        else:
            post_comment("⚠️ Tried to merge but there were no changes vs main. Nothing to do.")

    elif decision == "approve_partial":
        if apply_partial_approval(approved_nums):
            post_comment(f"✅ Approved picks {sorted(approved_nums)}. Merged into `main`. Site updates within 60 seconds.")
        else:
            post_comment("⚠️ Partial approval failed — see workflow logs.")

    elif decision == "reject_all":
        try:
            delete_pending_branch()
        except Exception as e:
            print(f"branch delete error (probably already gone): {e}")
        post_comment("🗑 Rejected all. `pending-review` branch deleted. `main` is unchanged.")

    else:
        post_comment(
            "ℹ️ Couldn't detect a decision from the labels or comments.\n\n"
            "To approve everything: add label `approved-all` or comment `approve all`.\n"
            "To reject everything: add label `rejected` or comment `reject all`.\n"
            "To approve some: comment `approve: 1, 3` listing the pick numbers.\n\n"
            "The `pending-review` branch is left as-is. Reopen this issue if you want to revisit."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
