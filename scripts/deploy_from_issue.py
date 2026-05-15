"""
Deploy a file to main from a GitHub issue.

Issue title: `deploy: <path>` (e.g. `deploy: index.html`)
Issue body: a single base64-encoded blob of the new file content, optionally
surrounded by anything else. The script finds the longest run of valid base64
characters and decodes that.

Why base64? GitHub's issue form sanitizes/strips raw HTML and Markdown. Base64
is opaque to that sanitizer — it survives the round trip intact.
"""
from __future__ import annotations

import base64
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
ALLOWED_AUTHORS = {"Hilex2030"}
ALLOWED_FILES = {"index.html", "about.html"}


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
        err = e.read().decode()
        raise RuntimeError(f"GitHub {method} {path}: {e.code} {err}")


def comment(text: str) -> None:
    gh_api("POST", f"/repos/{GH_REPO}/issues/{ISSUE_NUMBER}/comments",
           {"body": text})


def close_issue() -> None:
    gh_api("PATCH", f"/repos/{GH_REPO}/issues/{ISSUE_NUMBER}",
           {"state": "closed"})


def fail(msg: str) -> int:
    log(f"FAIL: {msg}")
    try:
        comment(
            f"❌ Deploy failed: {msg}\n\n"
            f"Edit the issue body to fix (do not open a new issue) — the workflow re-runs on edit."
        )
    except Exception as e:
        log(f"could not comment: {e}")
    return 1


def parse_target_path(title: str) -> str | None:
    m = re.match(r"^deploy:\s*(.+?)\s*$", title)
    return m.group(1) if m else None


def extract_base64(body: str) -> bytes | None:
    """
    Find the longest contiguous run of base64-safe characters in the body and
    try to decode it.

    The decoded bytes may be (a) plain UTF-8 text, or (b) gzip-compressed text.
    We try both — gzip is preferred for HTML payloads since it shrinks ~70%
    and lets large files fit under GitHub's 65,536-char issue body limit.

    Strategy: collapse all whitespace, find runs of base64 chars at least
    100 chars long, decode the longest, then try gunzip; fall back to raw bytes.
    """
    import gzip

    stripped = re.sub(r"\s+", "", body)
    runs = re.findall(r"[A-Za-z0-9+/=]{100,}", stripped)
    if not runs:
        return None
    runs.sort(key=len, reverse=True)
    for candidate in runs[:5]:
        candidate = candidate.rstrip("=")
        pad = (-len(candidate)) % 4
        try:
            raw = base64.b64decode(candidate + "=" * pad, validate=True)
        except ValueError:
            continue
        # Try gunzip first (gzip magic bytes 1f 8b)
        if raw[:2] == b"\x1f\x8b":
            try:
                decompressed = gzip.decompress(raw)
                decompressed.decode("utf-8", errors="strict")  # sanity check
                return decompressed
            except (OSError, UnicodeDecodeError):
                pass
        # Otherwise try raw UTF-8
        try:
            raw.decode("utf-8", errors="strict")
            return raw
        except UnicodeDecodeError:
            continue
    return None


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
        return fail("Title must be `deploy: <path>` (e.g. `deploy: index.html`).")

    if ".." in target or target.startswith("/"):
        return fail(f"Refusing to deploy to `{target}` (no `..` or absolute paths).")
    if target not in ALLOWED_FILES:
        return fail(
            f"`{target}` is not in the allowlist: {', '.join(sorted(ALLOWED_FILES))}."
        )

    decoded = extract_base64(ISSUE_BODY)
    if decoded is None:
        return fail(
            "Couldn't find a base64-encoded blob in the issue body.\n\n"
            "Paste the file content as a single base64-encoded string. "
            "Gzip first if the file is large (over ~45KB):\n"
            "```\n"
            "# Plain (works for small files):\n"
            "base64 -i index.html | pbcopy\n\n"
            "# Compressed (for large files):\n"
            "gzip -c index.html | base64 | pbcopy\n"
            "```\n"
            "The bot auto-detects gzip vs plain. Whitespace and surrounding text are OK."
        )
    if len(decoded) < 100:
        return fail(f"Decoded content is only {len(decoded)} bytes. Looks truncated.")
    if len(decoded) > 500_000:
        return fail(f"Decoded content is {len(decoded)} bytes — over 500KB limit.")

    text = decoded.decode("utf-8")
    target_path = REPO_ROOT / target
    target_path.write_text(text, encoding="utf-8")
    log(f"wrote {len(text)} chars to {target}")

    git("config", "user.name", "haps-deploy-bot")
    git("config", "user.email", "bot@haps.club")
    git("add", target)
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=REPO_ROOT
    )
    if status.returncode == 0:
        log("no changes")
        comment(f"ℹ️ `{target}` is identical to current `main`. No commit made.")
        close_issue()
        return 0

    git("commit", "-m", f"Deploy {target} from issue #{ISSUE_NUMBER}")
    git("push", "origin", "HEAD:main")
    log("pushed")

    sha = git("rev-parse", "--short", "HEAD")
    comment(
        f"✅ Deployed `{target}` to `main` as `{sha}`.\n\n"
        f"Live at https://haps.club within ~60 seconds.\n"
        f"Commit: https://github.com/{GH_REPO}/commit/{sha}"
    )
    close_issue()
    return 0


if __name__ == "__main__":
    sys.exit(main())
