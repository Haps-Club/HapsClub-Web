#!/usr/bin/env python3
"""
build_pages.py — bake data/events.json into the HTML, at commit time.

Why this exists
---------------
index.html used to ship an empty shell and fetch() the events on load, so
view-source contained zero event content and Googlebot had nothing to index
without a second render pass. This script writes the same markup into the
HTML before it is committed. The client-side fetch stays as progressive
enhancement for the category / neighbourhood filters.

What it does
------------
  1. Renders the homepage #grid rows into index.html.
  2. Fills every <!-- HAPS:LIVE ... --> block in guides/**/index.html.
  3. Emits Event JSON-LD for everything currently listed (never expired ones).
  4. Bumps dateModified in each guide's JSON-LD and lastmod in sitemap.xml.

Run it after weekly_refresh.py, in the same Sunday 9pm PT task, and commit
data/events.json + index.html + guides/ + sitemap.xml together.

    python3 scripts/build_pages.py            # write in place
    python3 scripts/build_pages.py --check    # exit 1 if anything is stale
"""
import argparse, datetime, html, json, os, re, sys

try:
    from zoneinfo import ZoneInfo
    LA = ZoneInfo("America/Los_Angeles")
except Exception:                                     # pragma: no cover
    LA = None

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS = os.path.join(ROOT, "data", "events.json")
INDEX  = os.path.join(ROOT, "index.html")
GUIDES = os.path.join(ROOT, "guides")
SITEMAP= os.path.join(ROOT, "sitemap.xml")
BASE   = "https://haps.club"

ARROW  = '<svg class="ic" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
MARK   = re.compile(
    r'(<!--\s*HAPS:LIVE start(?P<attrs>[^>]*?)-->)(?P<body>.*?)(<!--\s*HAPS:LIVE end\s*-->)',
    re.S)
GRID   = re.compile(
    r'(<!--\s*HAPS:GRID start\s*-->)(?P<body>.*?)(<!--\s*HAPS:GRID end\s*-->)', re.S)

def esc(s):
    return html.escape(str(s or ""), quote=True)

# ---------------------------------------------------------------- time
def parse_ts(s):
    """'20260908T200000' -> aware datetime in America/Los_Angeles."""
    if not s:
        return None
    try:
        dt = datetime.datetime.strptime(str(s)[:15], "%Y%m%dT%H%M%S")
    except ValueError:
        return None
    return dt.replace(tzinfo=LA) if LA else dt

def iso(s):
    dt = parse_ts(s)
    return dt.isoformat() if dt else None

MONTHS = {m: i for i, m in enumerate(
    ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"], 1)}
# Standing picks use month/day as a label, not a date: "New ★", "Any ★", "Now •".
STANDING = {"now": "Open now", "new": "New", "any": "Any day",
            "sun": "Sundays", "sat": "Saturdays", "fri": "Fridays",
            "mon": "Mondays", "tue": "Tuesdays", "wed": "Wednesdays", "thu": "Thursdays"}

def label_of(e):
    """('dated', datetime) or ('standing', 'Any day')."""
    mon = (e.get("month") or "").strip()
    day = (e.get("day") or "").strip()
    dt = parse_ts(e.get("starts"))
    if dt:
        return "dated", dt
    if mon.upper() in MONTHS and day.isdigit():
        now = datetime.datetime.now(LA) if LA else datetime.datetime.now()
        yr = now.year
        try:
            d = datetime.datetime(yr, MONTHS[mon.upper()], int(day), tzinfo=LA)
        except ValueError:
            return "standing", STANDING.get(mon.lower(), mon)
        if (now - d).days > 180:                 # month already well past: next year
            d = d.replace(year=yr + 1)
        return "dated", d
    return "standing", STANDING.get(mon.lower(), mon or "Any day")

def is_live(e, now):
    """Not yet finished. Falls back to starts when ends is missing."""
    end = parse_ts(e.get("ends"))
    if end:
        return end >= now
    kind, val = label_of(e)
    if kind == "standing":
        return True
    return val.date() >= now.date()

# ---------------------------------------------------------------- filters
def first_tag(e):
    t = (e.get("tags") or "").split()
    return t[0] if t else "food"

def matches(e, spec):
    """spec looks like 'hood:venice', 'area:westside' or 'tags:free'."""
    if not spec:
        return False
    key, _, val = spec.partition(":")
    if key == "tags":
        return val.lower() in (e.get("tags") or "").lower().split()
    got = (e.get(key) or "").strip().lower()
    if not got and key == "hood":                     # graceful pre-backfill
        return False
    return got == val.strip().lower()

def select(events, filt, fallback, limit, now):
    live = [e for e in events if is_live(e, now)]
    hits = [e for e in live if matches(e, filt)]
    used = filt
    if len(hits) < 2 and fallback:
        hits, used = [e for e in live if matches(e, fallback)], fallback
    far = datetime.datetime.max.replace(tzinfo=LA) if LA else datetime.datetime.max
    def key(e):
        kind, val = label_of(e)
        return (0, val) if kind == "dated" else (1, far)
    hits.sort(key=key)
    return hits[:limit], (used != filt)

# ---------------------------------------------------------------- render
def render_grid(events, now):
    """Homepage .week rows — markup identical to the client-side renderer."""
    out = []
    for e in events:
        if not is_live(e, now):
            continue
        price = ""
        if e.get("price"):
            free = " free" if re.match(r"^free$", e["price"], re.I) else ""
            price = f'<span class="price{free}">{esc(e["price"])}</span>'
        out.append(
            f'<a class="row" href="{esc(e.get("link"))}" target="_blank" rel="noopener">'
            f'<div class="date"><div class="d">{esc(e.get("day"))}</div>'
            f'<div class="m">{esc(e.get("month"))}</div></div>'
            f'<div><h3>{esc(e.get("title"))}</h3>'
            f'<p class="meta">{esc(e.get("cat"))} &middot; {esc(e.get("where"))}</p></div>'
            f'<div class="rside">{price}'
            f'<span class="stripe s-{first_tag(e)}"></span></div></a>')
    return "\n".join(out)

def render_live(rows):
    """Guide live block — sunset-pages.css .list / .link / .txt vocabulary."""
    if not rows:
        return ('  <div class="list">\n    <div class="row"><div class="txt">'
                '<div class="t">Nothing listed here this week</div>'
                '<div class="d">The <a href="/">homepage</a> has the full city.</div>'
                '</div></div>\n  </div>')
    out = ['  <div class="list">']
    for e in rows:
        kind, val = label_of(e)
        when = val.strftime("%a %-d %b") if kind == "dated" else val
        bits = [b for b in (e.get("where"), e.get("price")) if b]
        detail = " &middot; ".join([esc(when)] + [esc(b) for b in bits])
        out.append(
            f'    <a class="link" href="{esc(e.get("link"))}" target="_blank" rel="noopener">'
            f'<div class="txt"><div class="t">{esc(e.get("title"))}</div>'
            f'<div class="d">{detail}</div></div>'
            f'<span class="go">{ARROW}</span></a>')
    out.append("  </div>")
    return "\n".join(out)

def event_nodes(rows):
    nodes = []
    for e in rows:
        kind, val = label_of(e)
        if kind != "dated":
            continue          # a restaurant that is open "Any day" is not an Event
        start = iso(e.get("starts")) or val.date().isoformat()
        n = {"@type": "Event", "name": e.get("title"), "startDate": start,
             "eventStatus": "https://schema.org/EventScheduled",
             "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
             "location": {"@type": "Place", "name": e.get("where"),
                          "address": {"@type": "PostalAddress",
                                      "streetAddress": e.get("addr") or None,
                                      "addressLocality": "Los Angeles",
                                      "addressRegion": "CA", "addressCountry": "US"}}}
        n["location"]["address"] = {k: v for k, v in n["location"]["address"].items() if v}
        if iso(e.get("ends")):
            n["endDate"] = iso(e["ends"])
        if e.get("link"):
            n["url"] = e["link"]
        price = (e.get("price") or "").strip()
        if price:
            amt = "0" if re.match(r"^free$", price, re.I) else \
                  (re.sub(r"[^\d.]", "", price) or None)
            if amt:                       # skip "Varies", "Ticketed", "2 sets nightly"
                n["offers"] = {"@type": "Offer", "price": amt, "priceCurrency": "USD",
                               "availability": "https://schema.org/InStock",
                               "url": e.get("link")}
        nodes.append(n)
    return nodes

# ---------------------------------------------------------------- json-ld
def splice_ld(doc, events_for_page, today):
    """Replace the Event nodes in the page's @graph and bump dateModified."""
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', doc, re.S)
    if not m:
        return doc
    try:
        data = json.loads(m.group(2))
    except json.JSONDecodeError:
        return doc
    graph = data.get("@graph")
    if graph is None:
        return doc
    graph = [n for n in graph if n.get("@type") != "Event"]
    for n in graph:
        if n.get("@type") in ("WebPage", "CollectionPage"):
            n["dateModified"] = today
    graph += event_nodes(events_for_page)
    data["@graph"] = graph
    return doc[:m.start(2)] + json.dumps(data, ensure_ascii=False) + doc[m.end(2):]

HEAD2 = re.compile(
    r'<h2 data-haps-heading="(?P<main>[^"]*)" data-haps-alt="(?P<alt>[^"]*)">.*?</h2>', re.S)

def swap_heading(doc, used_fallback):
    """Say what the list actually is. A Culver City page showing Westside events
    should not still be headed 'Happening in Culver City this week'."""
    def sub(m):
        text = m.group("alt") if used_fallback else m.group("main")
        return (f'<h2 data-haps-heading="{m.group("main")}" '
                f'data-haps-alt="{m.group("alt")}">{text}</h2>')
    return HEAD2.sub(sub, doc)

def bump_sitemap(paths, today):
    if not os.path.exists(SITEMAP):
        return False
    src = open(SITEMAP, encoding="utf-8").read()
    out = src
    for p in paths:
        loc = re.escape(BASE + p)
        out = re.sub(rf'(<loc>{loc}</loc><lastmod>)[^<]*(</lastmod>)',
                     rf'\g<1>{today}\g<2>', out)
    if out != src:
        open(SITEMAP, "w", encoding="utf-8").write(out)
        return True
    return False

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would change and exit 1 if anything is stale")
    ap.add_argument("--min-rows", type=int, default=3,
                    help="fail rather than publish a thin 'this weekend' block")
    a = ap.parse_args()

    now = datetime.datetime.now(LA) if LA else datetime.datetime.now()
    today = now.date().isoformat()
    data = json.load(open(EVENTS, encoding="utf-8"))
    events = data.get("events", [])
    changed, problems = [], []

    # 1. homepage -------------------------------------------------------
    if os.path.exists(INDEX):
        src = open(INDEX, encoding="utf-8").read()
        if GRID.search(src):
            new = GRID.sub(lambda m: m.group(1) + "\n" + render_grid(events, now) + "\n" + m.group(3), src)
            new = splice_ld(new, [e for e in events if is_live(e, now)], today)
            if new != src:
                changed.append("index.html")
                if not a.check:
                    open(INDEX, "w", encoding="utf-8").write(new)
        else:
            problems.append("index.html has no <!-- HAPS:GRID start/end --> markers — "
                            "the homepage is still JS-only and will not be indexed")

    # 2. guides ---------------------------------------------------------
    touched = []
    for dirpath, dirnames, filenames in os.walk(GUIDES):
        dirnames[:] = [d for d in dirnames if d != "_drafts"]
        if "index.html" not in filenames:
            continue
        path = os.path.join(dirpath, "index.html")
        src = open(path, encoding="utf-8").read()
        page_events, fallbacks = [], []

        def fill(m):
            attrs = m.group("attrs")
            g = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
            limit = int(g.get("limit") or 4)
            rows, used_fb = select(events, g.get("filter"), g.get("fallback"), limit, now)
            fallbacks.append(used_fb)
            if g.get("filter", "").startswith("tags:free") and len(rows) < a.min_rows:
                problems.append(f"{os.path.relpath(path, ROOT)}: only {len(rows)} free "
                                f"events this weekend (min {a.min_rows}) — not publishing a thin block")
            page_events.extend(rows)
            return m.group(1) + "\n" + render_live(rows) + "\n  " + m.group(4)

        new = MARK.sub(fill, src)
        new = swap_heading(new, any(fallbacks))
        new = splice_ld(new, page_events, today)
        if new != src:
            rel = os.path.relpath(path, ROOT)
            changed.append(rel)
            touched.append("/" + os.path.relpath(dirpath, ROOT).replace(os.sep, "/") + "/")
            if not a.check:
                open(path, "w", encoding="utf-8").write(new)

    # 3. sitemap --------------------------------------------------------
    if touched and not a.check:
        if bump_sitemap(touched + ["/"], today):
            changed.append("sitemap.xml")

    print(json.dumps({"date": today, "events_total": len(events),
                      "events_live": sum(1 for e in events if is_live(e, now)),
                      "changed": changed, "problems": problems}, indent=1))
    if problems:
        print("\n".join("! " + p for p in problems), file=sys.stderr)
        return 1
    if a.check and changed:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
