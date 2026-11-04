#!/usr/bin/env python3
"""
Build issues.json for publish_issue.py from sent MailerLite campaigns. Run from the repo root.

    python3 scripts/issues_from_mailerlite.py > issues.json            # CI: needs MAILERLITE_API_KEY
    python3 scripts/issues_from_mailerlite.py --html email.html --sent 2026-11-03 > issues.json

The API mode lists sent campaigns whose name starts with "Haps Weekly" (so [TEST] sends and
one-off emails like the AMRE crossover heads-up are skipped), drops any whose date already has
a folder in archive/, and reads each email from its public MailerLite preview page, because the
API does not return email HTML. --html parses one saved email instead (no API key needed).

Parses the Design F email template (Nov 2026): hidden preheader -> dek, "TUESDAY · NOV 3" -> date,
p.mega -> title, the 23px paragraph after it -> intro, "(01) ..." mono labels -> section labels,
then each pick: mono meta line, title, description, link. The lead pick's bullets, DRESS and
TICKETS cells fold into its body. Stops at "The full list is on the site" / the sponsors.
Weekday names in the email are checked against the calendar; mismatches print to stderr.
Prints [] when nothing is new.
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://connect.mailerlite.com/api"
PREFIX = "Haps Weekly"
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
SMALL = {"a", "an", "and", "at", "for", "in", "of", "off", "on", "or", "the", "to", "am", "pm"}


def txt(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<br\s*/?>", " ", re.sub(r"<(?!br)[^>]+>", "", h)))).strip()


def clean(h):
    """Keep only links and inline emphasis; drop MailerLite's tracking attributes and styles."""
    h = re.sub(r"\s+", " ", h)
    h = re.sub(r"<(?!/?(a|strong|em|b|i)\b)[^>]+>", "", h)
    h = re.sub(r"<(strong|em|b|i)\b[^>]*>", r"<\1>", h)
    h = re.sub(r'<a\b[^>]*?(href="[^"]*")[^>]*>', r"<a \1>", h)
    return h.strip()


def title_case(s):
    """'FRI DEC 11 · 9 PM–MIDNIGHT · EATALY, CENTURY CITY' -> 'Fri Dec 11 · 9 pm–Midnight · Eataly, Century City'"""
    out, prev = [], ""
    for i, w in enumerate(re.split(r"(\s+|–|-|/)", s)):
        core = w.strip(",.:").lower()
        if not w.strip():
            out.append(w)
            continue
        if prev == "code":                                   # discount codes stay as written
            out.append(w)
        elif (core in SMALL or core in ("code", "required", "midnight", "noon")) and i and prev != "·":
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:].lower())
        prev = core
    return "".join(out)


def slugify(s):
    s = s.lower().replace("'", "").replace("’", "")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def check_weekdays(text, year, where):
    # "Sat Nov 21" and ranges like "Fri–Sat Nov 6–7" (each weekday checked against its own date)
    day = r"(mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?"
    pat = rf"\b{day}(?:\s*–\s*{day})?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{{1,2}})(?:\s*–\s*(\d{{1,2}}))?\b"
    for m in re.finditer(pat, text, re.I):
        mon = MONTHS.index(m.group(3).lower()[:3]) + 1
        for wd, dd in ((m.group(1), m.group(4)), (m.group(2), m.group(5))):
            if not (wd and dd):
                continue
            try:
                d = datetime.date(year, mon, int(dd))
            except ValueError:
                continue
            if d.weekday() != DAYS[wd.lower()[:3]]:
                print(f"warning: {where}: '{m.group(0)}' but {d:%b %-d %Y} is a {d:%A}", file=sys.stderr)


def blocks(doc):
    """Leaf blocks in document order: (kind, class, font-size, inner html)."""
    body = doc[doc.find("<body"):]
    pat = re.compile(r"<p\b([^>]*)>(.*?)</p>|<td\b([^>]*)>((?:(?!<td\b|<table\b|<p\b).)*?)</td>", re.S)
    for m in pat.finditer(body):
        attrs, inner = (m.group(1), m.group(2)) if m.group(1) is not None else (m.group(3), m.group(4))
        if not txt(inner):
            continue
        cls = (re.search(r'class="([^"]*)"', attrs) or [None, ""])[1]
        fs = int((re.search(r"font-size:(\d+)px", attrs) or [None, 0])[1])
        yield ("p" if m.group(1) is not None else "td", cls, fs, inner)


def parse(doc, sent):
    """-> issue dict for publish_issue.py, or None if this isn't a Design F weekly."""
    pre = re.search(r"<div[^>]*display:none[^>]*>(.*?)</div>", doc, re.S)
    dek = txt(pre.group(1)) if pre else ""
    dm = re.search(r"\b(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\s*·\s*([A-Z]{3})\s+(\d{1,2})\b", doc)
    mega = re.search(r'<p[^>]*class="[^"]*\bmega\b[^"]*"[^>]*>(.*?)</p>', doc, re.S)
    if not (dm and mega):
        return None
    sent_d = datetime.date.fromisoformat(sent)
    date = datetime.date(sent_d.year, MONTHS.index(dm.group(2).lower()) + 1, int(dm.group(3)))
    if abs((date - sent_d).days) > 7:                    # header month is Dec, sent in early Jan, etc.
        date = date.replace(year=sent_d.year + (1 if date < sent_d else -1))
    if date.strftime("%A").upper() != dm.group(1):
        print(f"warning: header says {dm.group(1)} but {date} is a {date:%A}", file=sys.stderr)
    title = txt(mega.group(1)).replace(" .", ".").rstrip(".")

    intro, secs, label, cur, lead = [], [], None, None, False
    seen_mega = False
    for kind, cls, fs, inner in blocks(doc):
        t = txt(inner)
        if "mega" in cls:
            seen_mega = True
            continue
        if not seen_mega:
            continue
        if t.startswith("The full list is on the site") or t.startswith("SPONSORED"):
            break
        mono = cls.split()[:1] == ["m"]
        if mono and re.match(r"^\(\d+\)\s", t):             # (01) ONE OF OURS · THE HAPS PICK
            label = title_case(re.sub(r"^\(\d+\)\s*", "", t))
            cur = None
            continue
        if label is None:                                    # intro paragraph(s) before the first label
            if kind == "p" and fs >= 18:
                intro.append(clean(inner))
            continue
        if mono:
            if t.startswith("●"):                            # "● 30+ GOING" badge
                continue
            if cur and lead and kind == "td":                # DRESS / TICKETS cells on the lead pick
                head, _, rest = t.partition(" ")
                cur["extra"].append(f"{head.title()}: {title_case(rest)}")
                continue
            cur = {"lbl": label, "h2": "", "tagline": "", "meta": title_case(t), "body": [], "extra": []}
            secs.append(cur)
            lead = False
            continue
        if cur is None:
            continue
        if not cur["h2"] and fs >= 23:
            cur["h2"] = t
            lead = "lead" in cls
            continue
        if t.startswith("•"):
            cur["body"].append(clean(inner).lstrip("• ").strip())
            continue
        a = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', inner, re.S)
        if a and txt(inner) == txt(a.group(2)):              # a lone "Get tickets →" link
            cur["body"].append(f'<a href="{html.escape(a.group(1))}">{html.escape(txt(a.group(2)))}</a>')
            continue
        if not cur["tagline"]:
            cur["tagline"] = clean(inner)
        else:
            cur["body"].append(clean(inner))

    sections = []
    for s in secs:
        if not s["h2"]:
            continue
        bullets = [b for b in s["body"] if not b.startswith("<a ")]
        links = [b for b in s["body"] if b.startswith("<a ")]
        body = []
        if s["extra"]:
            s["meta"] = " · ".join([s["meta"]] + s["extra"])
        if bullets and s["extra"]:                           # lead pick: bullets read as one paragraph
            body.append("; ".join((b if not i else b[:1].lower() + b[1:]).rstrip(".") for i, b in enumerate(bullets)) + ".")
        else:
            body += bullets
        body += links
        sections.append({"lbl": s["lbl"], "h2": s["h2"], "tagline": s["tagline"], "meta": s["meta"], "body": body})
        check_weekdays(s["meta"], date.year, s["h2"])

    return {"date": date.isoformat(), "slug": slugify(title), "title": title,
            "pretty": date.strftime("%A, %B ") + str(date.day) + date.strftime(", %Y"),
            "adate": date.strftime("%b ") + str(date.day) + date.strftime(", %Y"),
            "dek": dek, "intro": intro, "sections": sections}


def get(url, key=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 haps-archive",
                                               **({"Authorization": f"Bearer {key}"} if key else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def archived_dates():
    return {d[:10] for d in os.listdir(os.path.join(ROOT, "archive")) if re.match(r"\d{4}-\d{2}-\d{2}-", d)}


def from_api(key):
    camps, url = [], f"{API}/campaigns?filter[status]=sent&limit=50"
    while url:
        page = json.loads(get(url, key))
        camps += page["data"]
        url = (page.get("links") or {}).get("next")
    done, issues = archived_dates(), []
    for c in camps:
        if not c["name"].startswith(PREFIX) or not c.get("finished_at"):
            continue
        emails = c["emails"]
        email = next((e for e in emails if e.get("is_winner")), emails[0])
        iss = parse(get(email["preview_url"]), c["finished_at"][:10])
        if not iss:
            print(f"warning: could not parse campaign {c['name']!r}", file=sys.stderr)
        elif iss["date"] not in done:
            issues.append(iss)
            done.add(iss["date"])
    return issues


def main():
    a = sys.argv[1:]
    if "--html" in a:
        doc = open(a[a.index("--html") + 1], encoding="utf-8").read()
        iss = parse(doc, a[a.index("--sent") + 1])
        issues = [iss] if iss and iss["date"] not in archived_dates() else []
    else:
        key = os.environ.get("MAILERLITE_API_KEY")
        if not key:
            sys.exit("MAILERLITE_API_KEY is not set")
        issues = from_api(key)
    print(json.dumps(issues, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
