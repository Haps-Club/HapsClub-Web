"""
Deploy a file to main from a GitHub issue.

Triggered by issues with title `deploy: <path>` (e.g. `deploy: index.html`).
The issue body must contain a fenced code block (```...```) with the new file content.

What this does:
1. Parse target path from issue title
2. Extract file content from issue body's code fence
3. Write file, commit to main, push
4. Close issue, comment "Deployed ✅"

Only one author is trusted: the repo owner. (Issue authors are the user who opened
the issue, so this prevents random people from triggering deploys.)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
import json
from pathlib import Path

GH_TOKEN = os.environ["GH_TOKEN"]
GH_REPO = os.environ["GH_REPO"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE = os.environ["ISSUE_TITLE"]
ISSUE_BODY = os.environ.get("ISSUE_BODY", "") or ""
ISSUE_AUTHOR = os.environ.get("ISSUE_AUTHOR", "")

REPO_ROOT = Path(__file__).resolve().parent.parent

# Allowlist: only these GitHub usernames can trigger deploys.
# Add yourself here. (Issue author must be one of these.)
ALLOWED_AUTHORS = {"Hilex2030"}


def log(msg: str) -> None:
    print(msg, flush=True)


def gh_api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {GH_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode()
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"GitHub {method} {path}: {e.code} {body}")


def comment(text: str) -> None:
    gh_api("POST", f"/repos/{GH_REPO}/issues/{ISSUE_NUMBER}/comments",
           {"body": text})


def close_issue() -> None:
    gh_api("PATCH", f"/repos/{GH_REPO}/issues/{ISSUE_NUMBER}",
           {"state": "closed"})


def fail(msg: str) -> int:
    log(f"FAIL: {msg}")
    try:
        comment(f"❌ Deploy failed: {msg}\n\nFix the issue body and edit (don't open a new issue).")
    except Exception as e:
        log(f"could not comment: {e}")
    return 1


def parse_target_path(title: str) -> str | None:
    # Title format: "deploy: <path>"
    m = re.match(r"^deploy:\s*(.+?)\s*$", title)
    return m.group(1) if m else None


def extract_content(body: str) -> str | None:
    """
    Pull the first fenced code block from the issue body.
    Accepts ```html, ```, etc. Ignores any leading/trailing whitespace.
    """
    # Match ```optional_lang\n...content...\n```
    m = re.search(r"```[a-zA-Z0-9_-]*\r?\n(.*?)\r?\n```", body, re.DOTALL)
    if not m:
        return None
    return m.group(1)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=REPO_ROOT, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def main() -> int:
    log(f"issue #{ISSUE_NUMBER} by @{ISSUE_AUTHOR}: {ISSUE_TITLE}")

    if ISSUE_AUTHOR not in ALLOWED_AUTHORS:
        return fail(
            f"Author `@{ISSUE_AUTHOR}` is not authorized. "
            f"Allowed: {', '.join(sorted(ALLOWED_AUTHORS))}."
        )

    target = parse_target_path(ISSUE_TITLE)
    if not target:
        return fail("Title must look like `deploy: <path>` (e.g. `deploy: index.html`).")

    # Safety: only allow specific files / extensions, no path traversal
    if ".." in target or target.startswith("/"):
        return fail(f"Refusing to deploy to `{target}` (no `..` or absolute paths).")
    if not re.match(r"^[A-Za-z0-9._/\-]+$", target):
        return fail(f"Path `{target}` contains disallowed characters.")
    allowed_files = {"index.html", "about.html"}
    if target not in allowed_files:
        return fail(
            f"Path `{target}` is not in the deploy allowlist: "
            f"{', '.join(sorted(allowed_files))}."
        )

    content = extract_content(ISSUE_BODY)
    if content is None:
        return fail(
            "Couldn't find a fenced code block in the issue body. "
            "Paste the new file content inside ```` ``` ```` fences."
        )
    if len(content) < 100:
        return fail(f"Content is only {len(content)} bytes. Looks truncated.")
    if len(content) > 500_000:
        return fail(f"Content is {len(content)} bytes — over 500KB limit.")

    # Write file
    target_path = REPO_ROOT / target
    target_path.write_text(content, encoding="utf-8")
    log(f"wrote {len(content)} bytes to {target}")

    # Commit and push
    git("config", "user.name", "haps-deploy-bot")
    git("config", "user.email", "bot@haps.club")
    git("add", target)
    # If nothing changed, the commit will fail — handle that
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=REPO_ROOT
    )
    if status.returncode == 0:
        log("no changes to commit")
        comment(f"ℹ️ `{target}` was identical to current `main`. No commit made.")
        close_issue()
        return 0

    git("commit", "-m", f"Deploy {target} from issue #{ISSUE_NUMBER}")
    git("push", "origin", "HEAD:main")
    log("pushed to main")

    # Get short SHA for confirmation
    sha = git("rev-parse", "--short", "HEAD")
    comment(
        f"✅ Deployed `{target}` to `main` as `{sha}`.\n\n"
        f"Live at https://haps.club within ~60 seconds.\n"
        f"Diff: https://github.com/{GH_REPO}/commit/{sha}"
    )
    close_issue()
    return 0


if __name__ == "__main__":
    sys.exit(main())
