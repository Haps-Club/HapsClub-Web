#!/usr/bin/env python3
"""
daily_report.py — Haps Club daily review pipeline.

Runs once per morning. Produces a proposed update for index.html and asks
Michael to approve it via a GitHub Issue + email notification.

Flow:
  1. Read current index.html from main branch
  2. Prune expired dated events (date in the past — no grace period)
  3. Compute over-cap evergreens (no-date items beyond EVERGREEN_CAP = 30)
  4. Scan newsletter@haps.club for new event candidates via Claude Haiku 4.5
  5. Build a "proposed" version of index.html with all changes applied
  6. Push it to branch `pending-review` (overwriting if it exists)
  7. Open a GitHub Issue listing all proposed changes
  8. Email michael@haps.club with a link to the issue

Live site (main branch) is NEVER touched by this script.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup, Tag
from dateutil import parser as dateparser

# ---------- config ---------- #

INDEX_PATH = Path("index.html")
PENDING_BRANCH = "pending-review"
EVERGREEN_CAP = int(os.environ.get("EVERGREEN_CAP", "30"))
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "michael@haps.club")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "")
SKIP_INBOX = os.environ.get("SKIP_INBOX") == "true"
SKIP_EMAIL = os.environ.get("SKIP_EMAIL") == "true"

PACIFIC = timezone(timedelta(hours=-8))  # informational; real offsets come from data

SECTION_TODAY = "Today"
SECTION_WEEKEND = "This weekend"
SECTION_EARLIER = "Earlier this week"


# ---------- utilities ---------- #

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = dateparser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=PACIFIC)
        return dt
    except (ValueError, TypeError):
        return None


def all_cards(soup: BeautifulSoup) -> list[Tag]:
    """Every card across every section (articles + compact link-cards)."""
    return soup.select("section.stack-group article.card, section.stack-group a.card.card-compact")


def card_title(card: Tag) -> str:
    return (card.get("data-event-title")
            or (card.find(class_="card-headline").get_text(strip=True)
                if card.find(class_="card-headline") else "")
            or "(untitled)")


def is_dated(card: Tag) -> bool:
    """A card is 'dated' if it has data-event-end (or data-event-start)."""
    return bool(card.get("data-event-end") or card.get("data-event-start"))


def is_expired(card: Tag, now: datetime) -> bool:
    """Dated event whose end date is in the past."""
    end = parse_dt(card.get("data-event-end") or card.get("data-event-start"))
    return end is not None and end < now


def card_added_at(card: Tag) -> datetime:
    """When was this card added to the site? Falls back to a long-ago date so
    cards without a timestamp are treated as 'oldest' and pruned first."""
    return parse_dt(card.get("data-added-at")) or datetime(2020, 1, 1, tzinfo=timezone.utc)


def section_for(card: Tag) -> str:
    section = card.find_parent("section")
    if not section:
        return "(unknown)"
    h2 = section.find("h2")
    return h2.get_text(strip=True) if h2 else "(unknown)"


def update_group_counts(soup: BeautifulSoup) -> None:
    """Refresh '<N picks>' badges across all sections."""
    for section in soup.select("section.stack-group"):
        cards = section.select("article.card, a.card.card-compact")
        badge = section.find("span", class_="group-count")
        if badge:
            n = len(cards)
            badge.string = f"{n} picks" if n != 1 else "1 pick"


# ---------- phase 1: prune expired ---------- #

def prune_expired(soup: BeautifulSoup, now: datetime) -> list[str]:
    """Remove every dated card whose date has passed. No grace period.
    Evergreen cards (no date) are NEVER pruned by this function."""
    removed: list[str] = []
    for card in all_cards(soup):
        if not is_dated(card):
            continue  # evergreen — keep it
        if is_expired(card, now):
            removed.append(f"{card_title(card)} ({section_for(card)})")
            card.decompose()
    return removed


# ---------- phase 2: evergreen cap ---------- #

def enforce_evergreen_cap(soup: BeautifulSoup) -> list[str]:
    """If there are more than EVERGREEN_CAP evergreen items, drop the oldest first.
    Returns titles of removed items."""
    evergreens = [c for c in all_cards(soup) if not is_dated(c)]
    if len(evergreens) <= EVERGREEN_CAP:
        return []
    # Sort oldest-first by data-added-at
    evergreens.sort(key=card_added_at)
    over = len(evergreens) - EVERGREEN_CAP
    removed: list[str] = []
    for card in evergreens[:over]:
        removed.append(f"{card_title(card)} ({section_for(card)})")
        card.decompose()
    return removed


# ---------- phase 3: inbox ingestion ---------- #

@dataclass
class Candidate:
    title: str
    headline: str
    body: str
    location: str
    url: str
    start_iso: str
    end_iso: str
    section: str            # "Today" | "This weekend" | "Earlier this week" | "evergreen"
    category: str           # food | culture | event | outdoors
    is_evergreen: bool      # true = no specific date
    source_subject: str = ""
    confidence: float = 0.0
    notes: list[str] = field(default_factory=list)


def fetch_inbox_candidates() -> list[Candidate]:
    if SKIP_INBOX:
        print("[inbox] SKIP_INBOX=true, skipping")
        return []

    token_json = os.environ.get("GMAIL_TOKEN_JSON", "").strip()
    if not token_json:
        print("[inbox] GMAIL_TOKEN_JSON missing — skipping inbox ingestion")
        return []

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as e:
        print(f"[inbox] Google libraries missing: {e}")
        return []

    try:
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        query = "is:unread newer_than:3d"
        resp = service.users().messages().list(userId="me", q=query, maxResults=25).execute()
        message_refs = resp.get("messages", [])
        if not message_refs:
            print("[inbox] No new unread mail")
            return []

        all_candidates: list[Candidate] = []
        for ref in message_refs:
            msg = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
            text, subject = extract_message_text(msg)
            if not text:
                continue
            extracted = extract_events_with_claude(text, source_subject=subject)
            all_candidates.extend(extracted)
            # Mark read so we don't reprocess tomorrow
            service.users().messages().modify(
                userId="me", id=ref["id"], body={"removeLabelIds": ["UNREAD"]}
            ).execute()
        return all_candidates
    except Exception as e:
        print(f"[inbox] Fetch failed: {e}")
        return []


def extract_message_text(msg: dict) -> tuple[str, str]:
    """Return (body_text, subject) from a Gmail API message payload."""
    def walk(part: dict) -> Iterable[str]:
        mime = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data")
        if data and mime in ("text/plain", "text/html"):
            decoded = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            if mime == "text/html":
                decoded = BeautifulSoup(decoded, "html.parser").get_text(" ", strip=True)
            yield decoded
        for sub in part.get("parts", []) or []:
            yield from walk(sub)

    payload = msg.get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
    subject = headers.get("Subject", "")
    sender = headers.get("From", "")
    body_text = "\n\n".join(walk(payload))
    return f"FROM: {sender}\nSUBJECT: {subject}\n\n{body_text}"[:50_000], subject


def extract_events_with_claude(text: str, source_subject: str) -> list[Candidate]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("[claude] ANTHROPIC_API_KEY missing")
        return []
    try:
        from anthropic import Anthropic
    except ImportError:
        print("[claude] anthropic package not installed")
        return []

    today_str = now_utc().astimezone(PACIFIC).strftime("%A, %B %d, %Y")

    system = f"""You extract Los Angeles recommendations from email for Haps Club.
Today is {today_str} (Pacific time).

You produce TWO kinds of picks:

1. DATED event: a specific one-time thing with a date and time.
   start_iso and end_iso must be real ISO timestamps with Pacific offset.
   is_evergreen = false.

2. EVERGREEN pick: a standing recommendation (restaurant, museum, venue,
   ongoing exhibition, weekly thing). No specific date.
   start_iso = "" and end_iso = "". is_evergreen = true.

Strict rules:
- ONLY extract items with a real LA-area location (LA County).
- NEVER invent dates, addresses, prices, or details not explicit in the email.
- "This Friday" → calculate the actual ISO date from today.
- If a dated event is ambiguous (no clear date OR clear venue), skip it.
- An evergreen is fine without a date — but it MUST have a real venue/address.
- confidence: 1.0 if everything explicit; 0.7 if one detail inferred; lower → skip.

Return STRICT JSON only, no prose, no markdown fences:
{{"events": [{{
  "title": "Short name, no 'Haps Club:' prefix",
  "headline": "Conversational, 6-12 words, no exclamation marks",
  "body": "One sentence, includes neighborhood",
  "location": "Full address with city, state",
  "url": "Direct event/venue URL from the email",
  "start_iso": "2026-05-15T19:00:00-07:00" or "",
  "end_iso": "2026-05-15T22:00:00-07:00" or "",
  "section": "Today" or "This weekend" or "Earlier this week" or "evergreen",
  "category": "food" or "culture" or "event" or "outdoors",
  "is_evergreen": false,
  "confidence": 0.95,
  "notes": ["optional reasoning if low confidence"]
}}]}}

If no extractable picks, return {{"events": []}}."""

    client = Anthropic(api_key=api_key)
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": text}],
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        parsed = json.loads(raw)
    except Exception as e:
        print(f"[claude] extraction failed for {source_subject!r}: {e}")
        return []

    out: list[Candidate] = []
    for ev in parsed.get("events", []):
        try:
            if float(ev.get("confidence", 0)) < 0.7:
                continue
            out.append(Candidate(
                title=ev["title"],
                headline=ev.get("headline", ev["title"]),
                body=ev.get("body", ""),
                location=ev["location"],
                url=ev["url"],
                start_iso=ev.get("start_iso", "") or "",
                end_iso=ev.get("end_iso", "") or "",
                section=ev.get("section", "evergreen") if ev.get("is_evergreen") else ev.get("section", "This weekend"),
                category=ev.get("category", "event"),
                is_evergreen=bool(ev.get("is_evergreen", False)),
                source_subject=source_subject,
                confidence=float(ev.get("confidence", 0)),
                notes=list(ev.get("notes") or []),
            ))
        except KeyError as ke:
            print(f"[claude] missing field {ke}, skipping")
    return out


# ---------- phase 4: build proposed cards ---------- #

def build_card(soup: BeautifulSoup, c: Candidate) -> Tag:
    icon_class = {
        "food": "card-icon-food",
        "culture": "card-icon-culture",
        "event": "card-icon-event",
        "outdoors": "card-icon-outdoors",
    }.get(c.category, "card-icon-event")

    attrs = {
        "class": "card",
        "data-event-title": c.title,
        "data-event-location": c.location,
        "data-event-url": c.url,
        "data-event-desc": c.body,
        "data-added-at": now_utc().isoformat(),
    }
    if not c.is_evergreen:
        attrs["data-event-start"] = c.start_iso
        attrs["data-event-end"] = c.end_iso

    article = soup.new_tag("article", attrs=attrs)
    icon = soup.new_tag("div", attrs={"class": f"card-icon {icon_class}"})
    icon.string = "·"
    article.append(icon)
    meta = soup.new_tag("div", attrs={"class": "card-meta"})
    h3 = soup.new_tag("h3", attrs={"class": "card-headline"})
    h3.string = c.headline
    meta.append(h3)
    p = soup.new_tag("p", attrs={"class": "card-body"})
    p.string = c.body
    meta.append(p)
    if c.location:
        loc = soup.new_tag("span", attrs={"class": "card-location"})
        loc.string = c.location
        meta.append(loc)
    article.append(meta)
    return article


def find_section(soup: BeautifulSoup, header_text: str) -> Tag | None:
    for s in soup.select("section.stack-group"):
        h2 = s.find("h2")
        if h2 and header_text.lower() in h2.get_text(strip=True).lower():
            return s
    return None


def insert_candidates(soup: BeautifulSoup, candidates: list[Candidate]) -> list[Candidate]:
    """Insert each candidate into its target section. Returns the ones actually inserted.
    Evergreens go into 'Earlier this week' by default (the standing-picks section)."""
    inserted: list[Candidate] = []
    existing_urls = {c.get("data-event-url") for c in all_cards(soup) if c.get("data-event-url")}

    for c in candidates:
        if c.url in existing_urls:
            continue
        target_name = "Earlier this week" if c.is_evergreen else c.section
        section = find_section(soup, target_name)
        if section is None:
            print(f"[insert] section {target_name!r} not found, skipping {c.title}")
            continue
        grid = section.find("div", class_="card-grid") or section
        grid.append(build_card(soup, c))
        existing_urls.add(c.url)
        inserted.append(c)
    return inserted


# ---------- phase 5: write to pending-review branch ---------- #

def git(*args: str) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"git {' '.join(args)} failed: {result.stderr}", file=sys.stderr)
    return result.stdout.strip()


def push_to_pending_branch(soup: BeautifulSoup) -> str | None:
    """Write the proposed index.html, force-push to pending-review branch.
    Returns the commit SHA, or None if nothing changed vs main or git is unavailable."""
    INDEX_PATH.write_text(str(soup), encoding="utf-8")

    # Are we even in a git repo? (helps local testing not look broken)
    in_repo = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True
    )
    if in_repo.returncode != 0:
        print("[git] not in a git repo, skipping push (test mode)")
        return None

    # Check if anything actually changed vs main
    diff = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", "index.html"],
        capture_output=True
    )
    if diff.returncode == 0:
        print("[git] no changes vs main, skipping pending-review push")
        return None

    git("config", "user.name", "haps-bot")
    git("config", "user.email", "bot@haps.club")
    git("checkout", "-B", PENDING_BRANCH)
    git("add", "index.html")
    today = now_utc().astimezone(PACIFIC).strftime("%Y-%m-%d")
    git("commit", "-m", f"Proposed update {today}")
    git("push", "-f", "origin", PENDING_BRANCH)
    sha = git("rev-parse", "HEAD")
    if sha:
        print(f"[git] pushed {sha[:7]} to {PENDING_BRANCH}")
    return sha or None


# ---------- phase 6: GitHub Issue ---------- #

def open_issue(report: dict, pending_sha: str | None) -> dict | None:
    if not GH_TOKEN or not GH_REPO:
        print("[issue] GH_TOKEN or GH_REPO missing, can't open issue")
        return None

    today = now_utc().astimezone(PACIFIC).strftime("%A, %B %d, %Y")
    title = f"Haps Club daily — {today}"

    body = format_issue_body(report, pending_sha)
    labels = ["haps-daily"]

    r = requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
        },
        json={"title": title, "body": body, "labels": labels},
        timeout=30,
    )
    if r.status_code >= 300:
        print(f"[issue] failed: {r.status_code} {r.text}")
        return None
    issue = r.json()
    print(f"[issue] opened #{issue['number']}: {issue['html_url']}")
    return issue


def format_issue_body(report: dict, pending_sha: str | None) -> str:
    """The markdown body of the daily issue."""
    lines: list[str] = []
    lines.append("## Daily Haps Club review")
    lines.append("")
    if pending_sha:
        lines.append(f"Proposed changes live on branch [`pending-review`](https://github.com/{GH_REPO}/tree/pending-review) "
                     f"([compare to main](https://github.com/{GH_REPO}/compare/main...pending-review)).")
    else:
        lines.append("_No proposed changes today — everything below is informational only._")
    lines.append("")

    new_picks: list[Candidate] = report["inserted"]
    if new_picks:
        lines.append(f"### New picks pending ({len(new_picks)})")
        lines.append("")
        for i, c in enumerate(new_picks, 1):
            kind = "evergreen" if c.is_evergreen else f"{c.section}"
            datebit = f"{c.start_iso[:10]}" if c.start_iso else "no date"
            lines.append(f"**{i}. {c.headline}**  ")
            lines.append(f"📍 {c.location}  ")
            lines.append(f"🏷 {kind} · {c.category} · {datebit}  ")
            lines.append(f"🔗 {c.url}  ")
            if c.source_subject:
                lines.append(f"📧 from: *{c.source_subject}*  ")
            if c.notes:
                lines.append(f"⚠️ {'; '.join(c.notes)}  ")
            lines.append("")
    else:
        lines.append("### New picks pending")
        lines.append("_Nothing new from the inbox today._")
        lines.append("")

    if report["pruned"]:
        lines.append(f"### Pruned automatically ({len(report['pruned'])})")
        lines.append("_Dated events whose date has passed. No action needed._")
        for t in report["pruned"]:
            lines.append(f"- {t}")
        lines.append("")

    if report["evergreen_removed"]:
        lines.append(f"### Evergreen items dropped to stay under cap ({len(report['evergreen_removed'])})")
        lines.append(f"_Cap is {EVERGREEN_CAP}. Oldest go first._")
        for t in report["evergreen_removed"]:
            lines.append(f"- {t}")
        lines.append("")

    lines.append("### Current site stats (after proposed changes)")
    lines.append(f"- {report['stats']['dated']} dated events")
    lines.append(f"- {report['stats']['evergreen']} evergreen picks")
    lines.append(f"- {report['stats']['total']} total cards")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("### How to respond")
    lines.append("")
    lines.append("**To approve ALL proposed changes:** close this issue with the label `approved-all`.")
    lines.append("  _Or just comment `approve all` and close it — the bot will detect either._")
    lines.append("")
    if new_picks:
        lines.append("**To approve only some picks:** comment with the numbers, e.g. `approve: 1, 3` then close the issue.")
        lines.append("")
    lines.append("**To reject everything:** close with label `rejected` (or comment `reject all` then close).")
    lines.append("")
    lines.append("**Doing nothing:** the proposed changes stay on the `pending-review` branch but do NOT go live. "
                 "Tomorrow's run will rebuild from `main`, so unapproved picks will be lost unless you re-extract them.")
    return "\n".join(lines)


# ---------- phase 7: email notification ---------- #

def send_email(issue: dict | None, report: dict) -> None:
    if SKIP_EMAIL or not issue:
        return
    token_json = os.environ.get("GMAIL_TOKEN_JSON", "").strip()
    if not token_json:
        print("[email] no Gmail creds, skipping")
        return

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        print("[email] google libs missing")
        return

    today = now_utc().astimezone(PACIFIC).strftime("%A, %B %d, %Y")
    new_count = len(report["inserted"])
    pruned_count = len(report["pruned"])

    if new_count > 0:
        subject = f"Haps Club daily — {new_count} new pick{'s' if new_count != 1 else ''} pending"
    else:
        subject = f"Haps Club daily — nothing new today"

    body_lines = [
        f"Good morning. Here's today's Haps Club report ({today}).",
        "",
    ]
    if new_count > 0:
        body_lines.append(f"📬 {new_count} new pick{'s' if new_count != 1 else ''} pending your review:")
        for i, c in enumerate(report["inserted"], 1):
            datebit = f" ({c.start_iso[:10]})" if c.start_iso else " (evergreen)"
            body_lines.append(f"  {i}. {c.headline}{datebit}")
        body_lines.append("")
    if pruned_count > 0:
        body_lines.append(f"🗑 {pruned_count} expired event{'s' if pruned_count != 1 else ''} auto-pruned (no action needed):")
        for t in report["pruned"]:
            body_lines.append(f"  · {t}")
        body_lines.append("")
    if not new_count and not pruned_count:
        body_lines.append("Nothing changed today. Just sending this as your audit trail.")
        body_lines.append("")

    body_lines.extend([
        "Site stats:",
        f"  · {report['stats']['dated']} dated events live",
        f"  · {report['stats']['evergreen']} evergreen picks live",
        "",
        f"👉 Review on GitHub: {issue['html_url']}",
        "",
        "Quick actions on that page:",
        "  · Approve everything → close with label 'approved-all'",
        "  · Approve some → comment 'approve: 1, 3' then close",
        "  · Reject everything → close with label 'rejected'",
        "",
        "— Haps bot",
    ])
    text_body = "\n".join(body_lines)

    # Build a simple RFC 2822 message
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["To"] = NOTIFY_EMAIL
    msg["From"] = "newsletter@haps.club"
    msg["Subject"] = subject
    msg.set_content(text_body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try:
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"[email] sent to {NOTIFY_EMAIL}")
    except Exception as e:
        print(f"[email] failed to send: {e}")


# ---------- main ---------- #

def main() -> int:
    if not INDEX_PATH.exists():
        print("FATAL: index.html not found at repo root", file=sys.stderr)
        return 2

    soup = BeautifulSoup(INDEX_PATH.read_text(encoding="utf-8"), "html.parser")
    now = now_utc()

    pruned = prune_expired(soup, now)
    print(f"[phase 1] pruned {len(pruned)} expired event(s)")

    candidates = fetch_inbox_candidates()
    print(f"[phase 2] {len(candidates)} candidate(s) extracted from inbox")

    inserted = insert_candidates(soup, candidates)
    print(f"[phase 3] inserted {len(inserted)} new card(s)")

    evergreen_removed = enforce_evergreen_cap(soup)
    print(f"[phase 4] removed {len(evergreen_removed)} over-cap evergreen(s)")

    update_group_counts(soup)

    dated = sum(1 for c in all_cards(soup) if is_dated(c))
    evergreen = sum(1 for c in all_cards(soup) if not is_dated(c))
    stats = {"dated": dated, "evergreen": evergreen, "total": dated + evergreen}

    report = {
        "pruned": pruned,
        "inserted": inserted,
        "evergreen_removed": evergreen_removed,
        "stats": stats,
    }

    pending_sha = push_to_pending_branch(soup)
    issue = open_issue(report, pending_sha)
    send_email(issue, report)

    print(f"\n[done] {len(pruned)} pruned, {len(inserted)} new, {len(evergreen_removed)} over-cap removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
