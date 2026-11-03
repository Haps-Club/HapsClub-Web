#!/usr/bin/env python3
"""check_site.py — one command to check the whole site before (and after) a push.

    python3 scripts/check_site.py          # local checks, exit 1 on any error
    python3 scripts/check_site.py --live   # also fetch every page from haps.club

Errors (fail the check):
  * every .html page ends with </html> and carries GA G-RKY63MK7ND
  * no inline <style> outside the known exception folders
  * every /assets/ link exists and its ?v= matches the file's md5[:8]
  * every local href/src resolves to a file in the repo
  * data/events.json parses; featured is 3; area is a known chip;
    starts/ends look like YYYYMMDDTHHMMSS
  * weekday names in event copy match their dates ("Sun Nov 1", "Sat 11/21")
  * no "singles" anywhere and no "!" in event titles/copy
Warnings (printed, don't fail): PROJECT.md's banned words in event copy.

Read-only. Never writes a file.
"""
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GA = "G-RKY63MK7ND"
SITE = "https://haps.club"
AREAS = {"westside", "midcity", "dtla", "hollywood", "eastside", "citywide"}
# Pages that are allowed their own <style> block (see CLAUDE.md).
STYLE_OK = ("planner/", "planner-svetlana/", "partners/", "partnership/", "events/")
BANNED_WARN = ["curated", "hidden gem", "must-visit", "hot spot", "iconic", "elevated",
               "don't miss", "journey", "unleash", "leverage", "ecosystem"]
COPY_FIELDS = ("title", "tagline", "meta", "pill", "when", "cta", "text")
MONTHS = {m: i + 1 for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split())}
DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def md5_8(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()[:8]


def pages():
    out = []
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        out += [os.path.relpath(os.path.join(d, f), ROOT) for f in files if f.endswith(".html")]
    return sorted(out)


def resolves(url_path):
    p = url_path.split("#")[0].split("?")[0].lstrip("/")
    if p == "":
        return True
    full = os.path.join(ROOT, p)
    return (os.path.isfile(full) or os.path.isfile(os.path.join(full, "index.html"))
            or os.path.isfile(full + ".html"))


# ---------- pages ----------
def check_page(rel):
    s = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    standalone = rel.startswith(STYLE_OK)  # private/pitch pages: own styles, no GA
    if not s.rstrip().endswith("</html>"):
        err(f"{rel}: does not end with </html>")
    if GA not in s and not standalone:
        err(f"{rel}: missing Google Analytics {GA}")
    if "<style" in s and not standalone:
        err(f"{rel}: has an inline <style> block")
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)  # templates in comments aren't links
    base = os.path.dirname(rel)
    for attr, url in re.findall(r'\b(href|src)="([^"]+)"', s):
        if re.match(r"^(https?:|mailto:|tel:|#|data:|javascript:|//|\{)", url):
            continue
        path = url if url.startswith("/") else "/" + os.path.normpath(os.path.join(base, url))
        m = re.match(r"^(/assets/[^?#]+)\?v=(\w+)", path)
        if m:
            f = os.path.join(ROOT, m.group(1).lstrip("/"))
            if not os.path.isfile(f):
                err(f"{rel}: {m.group(1)} does not exist")
            elif not re.fullmatch(r"[0-9a-f]{8}", m.group(2)):
                warn(f"{rel}: {m.group(1)}?v={m.group(2)} is a hand-set version, not a hash")
            elif md5_8(f) != m.group(2):
                err(f"{rel}: {m.group(1)}?v={m.group(2)} is stale (file is {md5_8(f)})")
            continue
        if not resolves(path):
            err(f"{rel}: broken local link {url}")


# ---------- events.json ----------
def guess_year(month, ref):
    # Dates in copy have no year; pick the one closest to the event/updated date.
    y = ref.year
    if month - ref.month > 6:
        y -= 1
    elif ref.month - month > 6:
        y += 1
    return y


def check_weekdays(where, text, ref):
    # "Sun Nov 1", "Sunday, November 1", "Sat 11/21"
    pats = [r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b",
            r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(\d{1,2})/(\d{1,2})\b"]
    for i, pat in enumerate(pats):
        for m in re.finditer(pat, text, re.I):
            wd = DAYS[m.group(1).lower()[:3]]
            mon = MONTHS[m.group(2).lower()[:3]] if i == 0 else int(m.group(2))
            day = int(m.group(3))
            try:
                d = date(guess_year(mon, ref), mon, day)
            except ValueError:
                err(f"{where}: impossible date '{m.group(0)}'")
                continue
            if d.weekday() != wd:
                err(f"{where}: '{m.group(0)}' but {d:%b %-d %Y} is a {d:%A}")


def check_copy(where, item, ref):
    for k in COPY_FIELDS:
        v = item.get(k)
        if not isinstance(v, str):
            continue
        low = v.lower()
        if re.search(r"\bsingles\b", low):
            err(f"{where}.{k}: says 'singles'")
        if "!" in v:
            err(f"{where}.{k}: exclamation mark")
        for w in BANNED_WARN:
            if w in low:
                warn(f"{where}.{k}: banned word '{w}'")
        check_weekdays(f"{where}.{k}", v, ref)


def check_events():
    path = os.path.join(ROOT, "data", "events.json")
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as ex:
        err(f"data/events.json does not parse: {ex}")
        return
    try:
        upd = date.fromisoformat(d.get("updated", ""))
    except ValueError:
        err("events.json: 'updated' is not YYYY-MM-DD")
        upd = date.today()
    if len(d.get("featured", [])) != 3:  # build_home.py promotes the next event to fill 3
        warn(f"events.json: featured has {len(d.get('featured', []))} items; homepage auto-fills to 3")
    if re.search(r"\bsingles\b", json.dumps(d, ensure_ascii=False), re.I):
        err("events.json: says 'singles' somewhere")
    for sect in ("featured", "events", "plan"):
        for i, x in enumerate(d.get(sect, [])):
            where = f"{sect}[{i}] {x.get('title', '?')[:40]!r}"
            if x.get("area") and x["area"] not in AREAS:
                err(f"{where}: unknown area '{x['area']}'")
            for k in ("starts", "ends"):
                if x.get(k) and not re.fullmatch(r"\d{8}T\d{6}", x[k]):
                    err(f"{where}: {k} '{x[k]}' is not YYYYMMDDTHHMMSS")
            ref = upd
            if x.get("starts"):
                ref = date(int(x["starts"][:4]), int(x["starts"][4:6]), int(x["starts"][6:8]))
            check_copy(where, x, ref)
    if isinstance(d.get("announcement"), dict):
        check_copy("announcement", d["announcement"], upd)


# ---------- live ----------
def check_live(rels):
    for rel in rels:
        if re.search(r"(^|/)_", rel):  # GitHub Pages doesn't publish _folders
            continue
        url = SITE + "/" + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 haps-check"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode("utf-8", "replace")
                if r.status != 200:
                    err(f"live {url}: HTTP {r.status}")
                elif GA not in body and not rel.startswith(STYLE_OK):
                    err(f"live {url}: missing GA")
        except Exception as ex:
            err(f"live {url}: {ex}")


def main():
    rels = pages()
    for rel in rels:
        check_page(rel)
    check_events()
    if "--live" in sys.argv:
        check_live(rels)
    for w in warnings:
        print("warn ", w)
    for e in errors:
        print("ERROR", e)
    print(f"\n{len(rels)} pages checked{' + live' if '--live' in sys.argv else ''}: "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
