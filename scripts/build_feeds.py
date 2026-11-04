#!/usr/bin/env python3
"""build_feeds.py — generate every machine-readable view of the site from the data.

    python3 scripts/build_feeds.py          # write
    python3 scripts/build_feeds.py --check  # exit 1 if any file is stale

Reads data/events.json, data/settings.json and archive/index.html. Writes:

  calendar.ics     every dated pick as a calendar event. Subscribe once ("add calendar from URL")
                   and Google / Apple / Outlook calendars stay current on their own.
  feed.xml         RSS 2.0 of the newsletter archive (readers, podcast apps, AI crawlers).
  llms-full.txt    this week's picks and the archive as plain text for AI answer engines.
  llms.txt         the "This week" block between <!-- AUTO:WEEK --> markers is regenerated,
                   and lines about events that already happened are dropped.

Output is deterministic (no timestamps from "now"), so nothing changes in git until the data does.
"""
import datetime
import email.utils
import hashlib
import html
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "data", "settings.json"), encoding="utf-8"))
DATA = json.load(open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8"))
SITE = CFG["site_url"].rstrip("/")
TZ = ZoneInfo(CFG["timezone"])
UTC = datetime.timezone.utc
TODAY = datetime.datetime.now(TZ).date()
HOODS = {"westside": "Westside", "midcity": "Mid-City", "dtla": "Downtown", "hollywood": "Hollywood",
         "eastside": "Eastside", "citywide": "Citywide"}


def stamp(s):
    """'20261121T193000' (Pacific) -> aware datetime, or None."""
    if not s:
        return None
    return datetime.datetime.strptime(s[:15], "%Y%m%dT%H%M%S").replace(tzinfo=TZ)


def picks():
    """Every dated pick once, soonest first. Needs a start time to be calendar-worthy."""
    seen, out = set(), []
    for sec in ("featured", "events", "plan"):
        for x in DATA.get(sec, []):
            if x["title"] in seen:
                continue
            seen.add(x["title"])
            x = dict(x)
            x["_start"], x["_end"] = stamp(x.get("starts")), stamp(x.get("ends"))
            out.append(x)
    dated = [x for x in out if x["_start"]]
    return sorted(dated, key=lambda x: x["_start"]), [x for x in out if not x["_start"]]


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def where(x):
    place, addr = clean(x.get("where") or ""), clean(x.get("addr") or "")
    return ", ".join(p for p in (place, addr if addr and addr not in place else "") if p)


# ---------- calendar.ics ----------
def ics_escape(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    out, b = [], line.encode("utf-8")
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80:          # never split a multi-byte character
            cut -= 1
        out.append(b[:cut].decode("utf-8"))
        b = b[cut:]
        b = b" " + b
    out.append(b.decode("utf-8"))
    return "\r\n".join(out)


def build_ics():
    dated, _ = picks()
    stamp_utc = datetime.datetime.strptime(DATA["updated"], "%Y-%m-%d").replace(tzinfo=UTC)
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{CFG['site_name']}//{SITE}//EN", "CALSCALE:GREGORIAN",
         "METHOD:PUBLISH", "X-WR-CALNAME:" + ics_escape(CFG["calendar_name"]), f"X-WR-TIMEZONE:{CFG['timezone']}",
         "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
    for x in dated:
        s = x["_start"]
        e = x["_end"] if x["_end"] and x["_end"] > s else s + datetime.timedelta(hours=CFG["default_event_hours"])
        uid = hashlib.sha1((x["title"] + x["starts"]).encode()).hexdigest()[:20] + "@" + SITE.split("//")[1]
        desc = clean(x.get("tagline") or x.get("meta") or "")
        if x.get("price"):
            desc += (" " if desc else "") + "Price: " + clean(x["price"]) + "."
        if x.get("link"):
            desc += "\n" + x["link"]
        L += ["BEGIN:VEVENT", "UID:" + uid, "DTSTAMP:" + stamp_utc.strftime("%Y%m%dT%H%M%SZ"),
              "DTSTART:" + s.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ"),
              "DTEND:" + e.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ"),
              "SUMMARY:" + ics_escape(clean(x["title"]))]
        if where(x):
            L.append("LOCATION:" + ics_escape(where(x)))
        if desc:
            L.append("DESCRIPTION:" + ics_escape(desc))
        if x.get("link"):
            L.append("URL:" + x["link"])
        L.append("END:VEVENT")
    L.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in L) + "\r\n"


# ---------- feed.xml ----------
def archive_cards():
    src = open(os.path.join(ROOT, "archive", "index.html"), encoding="utf-8").read()
    out = []
    for href, meta, title, dek in re.findall(
            r'class="acard" href="(/archive/[^"]+)">\s*<div class="meta">(.*?)</div>\s*<h2>(.*?)</h2>\s*<div class="d">(.*?)</div>', src, re.S):
        d = re.search(r"/archive/(\d{4}-\d{2}-\d{2})-", href)
        if d:
            out.append({"url": SITE + href, "title": clean(title), "dek": clean(dek), "date": d.group(1)})
    return out


def build_rss():
    items = archive_cards()[:CFG["feed_items"]]
    def pub(d):
        t = datetime.datetime.strptime(d, "%Y-%m-%d").replace(hour=8, tzinfo=TZ)   # Tuesday-morning send
        return email.utils.format_datetime(t.astimezone(UTC))
    last = pub(items[0]["date"]) if items else email.utils.format_datetime(datetime.datetime(2026, 1, 1, tzinfo=UTC))
    x = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
         f"<title>{html.escape(CFG['site_name'])}: newsletter archive</title>", f"<link>{SITE}/archive/</link>",
         f"<description>{html.escape(CFG['feed_description'])}</description>", "<language>en-us</language>",
         f"<lastBuildDate>{last}</lastBuildDate>",
         f'<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>']
    for i in items:
        x += ["<item>", f"<title>{html.escape(i['title'])}</title>", f"<link>{i['url']}</link>",
              f'<guid isPermaLink="true">{i["url"]}</guid>', f"<pubDate>{pub(i['date'])}</pubDate>",
              f"<description>{html.escape(i['dek'])}</description>", "</item>"]
    x += ["</channel>", "</rss>"]
    return "\n".join(x) + "\n"


# ---------- llms.txt / llms-full.txt ----------
def pick_line(x):
    when = x["_start"].strftime("%a %b ") + str(x["_start"].day)
    bits = [when, clean(x.get("where") or ""), HOODS.get(x.get("area"), ""), clean(x.get("price") or "")]
    return f"- [{clean(x['title'])}]({x.get('link', SITE)}): " + " · ".join(b for b in bits if b)


def this_week():
    dated, _ = picks()
    now = datetime.datetime.now(TZ)
    horizon = now + datetime.timedelta(days=CFG["this_week_days"])
    return [x for x in dated if (x["_end"] or x["_start"]) >= now and x["_start"] <= horizon]


def week_block():
    L = [f"## This week ({DATA.get('weekLabel', '')})", "",
         f"Hand-picked, dated events for the next {CFG['this_week_days']} days, generated from the site's data "
         f"and refreshed daily. Full list: {SITE}/ and {SITE}/llms-full.txt.", ""]
    L += [pick_line(x) for x in this_week()] or ["- Nothing dated right now; see the homepage for evergreen picks."]
    return "\n".join(L)


def update_llms():
    p = os.path.join(ROOT, "llms.txt")
    s = open(p, encoding="utf-8").read()
    block = "<!-- AUTO:WEEK -->\n" + week_block() + "\n<!-- /AUTO:WEEK -->"
    if "<!-- AUTO:WEEK -->" in s:
        s = re.sub(r"<!-- AUTO:WEEK -->.*?<!-- /AUTO:WEEK -->", lambda m: block, s, flags=re.S)
    else:
        s = s.replace("\n## Guides", "\n" + block + "\n\n## Guides", 1)
    if "llms-full.txt" not in s.split("## Guides")[0]:
        s = s.replace("\n## Key pages\n", f"\n## Key pages\n- [Full text for AI]({SITE}/llms-full.txt): This week's picks and the newsletter archive as plain text, regenerated daily.\n"
                      f"- [Calendar feed]({SITE}/calendar.ics): Every dated pick as an iCalendar feed to subscribe to.\n"
                      f"- [Newsletter RSS]({SITE}/feed.xml): The archive as an RSS feed.\n", 1)
    months = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}
    keep = []
    for line in s.split("\n"):
        m = re.search(r"\b(%s)\s+(\d{1,2}),\s+(20\d\d)" % "|".join(months), line)
        if m and line.startswith("- [") and "/events/" in line:
            if datetime.date(int(m.group(3)), months[m.group(1)], int(m.group(2))) < TODAY:
                continue                                    # that event has happened
        keep.append(line)
    s = "\n".join(keep)
    if re.search(r"## Events\s*(\n## |\Z)", s):
        s = re.sub(r"\n## Events\s*(?=\n## |\Z)", "", s)       # nothing left under Events
    return s if s.endswith("\n") else s + "\n"


def build_llms_full():
    base = open(os.path.join(ROOT, "llms.txt"), encoding="utf-8").read()
    head = base.split("\n## ")[0].strip()
    dated, undated = picks()
    now = datetime.datetime.now(TZ)
    L = [head, "", f"Updated {DATA['updated']}. Generated from {SITE}/ data; times are {CFG['timezone']}.", "",
         f"## Dated picks ({DATA.get('weekLabel', '')} onward)", ""]
    for x in dated:
        if (x["_end"] or x["_start"]) < now:
            continue
        end = f" to {x['_end'].strftime('%b ')}{x['_end'].day}" if x["_end"] and x["_end"].date() > x["_start"].date() else ""
        L += [f"### {clean(x['title'])}",
              f"- When: {x['_start'].strftime('%A, %B ')}{x['_start'].day}{end}, {x['_start'].strftime('%-I:%M %p')}",
              f"- Where: {where(x)} ({HOODS.get(x.get('area'), 'Los Angeles')})",
              f"- Price: {clean(x.get('price') or 'see link')}",
              f"- Category: {clean(x.get('cat') or '')}",
              f"- Details: {x.get('link', SITE)}"]
        if x.get("tagline"):
            L.append(f"- About: {clean(x['tagline'])}")
        L.append("")
    groups = {}
    for x in undated:
        groups.setdefault(clean(x.get("cat") or "More"), []).append(x)
    L += ["## Always worth knowing (no fixed date)", ""]
    for cat, xs in sorted(groups.items()):
        L += [f"### {cat}"] + [f"- [{clean(x['title'])}]({x.get('link', SITE)}): {where(x)} · {HOODS.get(x.get('area'), '')}"
                              + (" · new" if x.get("month") == "New" else "") for x in xs] + [""]
    L += ["## Newsletter archive", ""]
    L += [f"- [{c['title']}]({c['url']}) ({c['date']}): {c['dek']}" for c in archive_cards()]
    return "\n".join(L).rstrip() + "\n"


def main():
    check = "--check" in sys.argv
    llms = update_llms()
    files = {"calendar.ics": build_ics(), "feed.xml": build_rss(), "llms.txt": llms}
    # llms-full.txt reads the (just updated) llms.txt header; write that first so both stay consistent
    stale = []
    for name, text in files.items():
        p = os.path.join(ROOT, name)
        old = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else ""
        if old != text:
            stale.append(name)
            if not check:
                open(p, "w", encoding="utf-8", newline="").write(text)
    full = build_llms_full()
    p = os.path.join(ROOT, "llms-full.txt")
    old = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    if old != full:
        stale.append("llms-full.txt")
        if not check:
            open(p, "w", encoding="utf-8").write(full)
    n_ics = sum(1 for l in files["calendar.ics"].split("\r\n") if l == "BEGIN:VEVENT")
    print(("stale: " if check else "wrote: ") + (", ".join(stale) or "nothing (already current)"),
          f"| {n_ics} calendar events, {len(archive_cards()[:CFG['feed_items']])} feed items")
    sys.exit(1 if (check and stale) else 0)


if __name__ == "__main__":
    main()
