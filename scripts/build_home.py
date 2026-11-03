#!/usr/bin/env python3
"""Build the haps.club homepage (index.html) from data/events.json.

Design F ("editorial, warmed up"), 2026-11.

Why this exists
---------------
The old homepage fetched events.json in the browser and drew the page with JS,
so Google saw an empty shell. This script renders every event straight into
the HTML (plus Event JSON-LD), so the page is fast, crawlable, and still
updated by editing ONE file: data/events.json.

What it does on every run
-------------------------
1. Drops anything whose `ends` is in the past (Pacific time) from events.json
   (featured, events, plan) and saves the pruned file.
2. Keeps 3 featured cards: if one expired, it promotes the next upcoming
   dated event automatically.
3. Writes index.html.

Run locally or let .github/workflows/build-home.yml run it on every push to
data/events.json and once a day at 7am PT.

    python3 scripts/build_home.py            # prune + build
    python3 scripts/build_home.py --no-prune # build only
"""
import html
import json
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_chrome as sc  # shared header/footer, same as every other page
from datetime import datetime, timedelta, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "events.json")
OUT = os.path.join(REPO, "index.html")

SITE = "https://haps.club"
LOGO = "https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/haps-club-logo.svg?v=5"
CAL = ("https://calendar.google.com/calendar/embed?src="
       "c_ea45ead7ce1909f199c95778b5b7afd9d1a9f9c9751f911bf3c672f267dc4384"
       "%40group.calendar.google.com")
IG = "https://instagram.com/thehapsclub/"
GA = "G-RKY63MK7ND"
# MailerLite embedded form "Haps: Website signup (haps.club)" -> groups Haps + Source: Website signup
ML_ACTION = "https://assets.mailerlite.com/jsonp/2758867/forms/202915208754103515/subscribe"

CATS = {  # tag -> (label, css class)
    "food": ("Food", "food"), "music": ("Music", "music"),
    "culture": ("Culture", "culture"), "outdoors": ("Outdoors", "out"),
}
AREAS = [("all", "Everywhere"), ("westside", "Westside"), ("midcity", "Mid-City"),
         ("dtla", "Downtown"), ("hollywood", "Hollywood"), ("eastside", "Eastside"),
         ("citywide", "Citywide")]
AREA_LABEL = dict(AREAS)
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


# ---------- time helpers (Pacific, DST-aware without tz database) ----------
def _pt_offset(dt_utc):
    """-7 during US daylight time, else -8."""
    y = dt_utc.year
    # 2nd Sunday of March 10:00 UTC, 1st Sunday of November 09:00 UTC
    mar = datetime(y, 3, 8, tzinfo=timezone.utc)
    start = mar + timedelta(days=(6 - mar.weekday()) % 7, hours=10)
    nov = datetime(y, 11, 1, tzinfo=timezone.utc)
    end = nov + timedelta(days=(6 - nov.weekday()) % 7, hours=9)
    return -7 if start <= dt_utc < end else -8


def now_pt_stamp():
    u = datetime.now(timezone.utc)
    return (u + timedelta(hours=_pt_offset(u))).strftime("%Y%m%dT%H%M%S")


def iso(stamp):
    """20261121T193000 (Pacific) -> 2026-11-21T19:30:00-08:00"""
    if not stamp:
        return None
    d = datetime.strptime(stamp, "%Y%m%dT%H%M%S")
    off = _pt_offset(d.replace(tzinfo=timezone.utc) + timedelta(hours=8))
    return d.strftime("%Y-%m-%dT%H:%M:%S") + f"{off:+03d}:00"


def e(s):
    return html.escape(html.unescape(str(s or "")), quote=True)


def nb(s):
    """Escape, then glue the last two words so a single word never sits alone."""
    s = e(s)
    i = s.rfind(" ")
    return s if i < 0 else s[:i] + "&nbsp;" + s[i + 1:]


def first_tag(item):
    for t in (item.get("tags") or "").split():
        if t in CATS:
            return t
    c = (item.get("cat") or "").lower()
    return "outdoors" if c.startswith("out") else (c if c in CATS else "culture")


def is_free(item):
    return "free" in (item.get("tags") or "").split() or str(item.get("price", "")).lower() == "free"


def is_ours(item):
    return bool(item.get("lead")) or "luma.com/hapsclub" in (item.get("link") or "")


# ---------- data ----------
def load_and_prune(prune=True):
    d = json.load(open(DATA, encoding="utf-8"))
    now = now_pt_stamp()
    def alive(x):
        end = x.get("ends") or (x["starts"][:8] + "T235959" if x.get("starts") else None)
        return not end or end >= now
    if prune:
        before = sum(len(d.get(k, [])) for k in ("featured", "events", "plan"))
        for k in ("featured", "events", "plan"):
            d[k] = [x for x in d.get(k, []) if alive(x)]
        after = sum(len(d.get(k, [])) for k in ("featured", "events", "plan"))
        if after != before:
            with open(DATA, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"pruned {before - after} expired item(s) from events.json")
    return d, now


def dated(x):
    return bool(x.get("starts") or x.get("ends")) and (x.get("month") or "").upper() in MONTHS


def sort_key(x):
    return (0, x.get("starts") or x.get("ends") or "") if dated(x) else (1, "")


# ---------- components ----------
def lead_card(x):
    when = x.get("when") or x.get("meta", "").split(" · ")[0]
    rows = []
    if x.get("meta"):
        parts = [p.strip() for p in x["meta"].split("·")]
        rows.append(("When", " · ".join(parts[:2])))
    if x.get("where"):
        rows.append(("Where", x["where"]))
    if x.get("price"):
        rows.append(("Tickets", x["price"] + (" · 10% off with HAPSCLUBPLUS" if "HAPSCLUBPLUS" in (x.get("link") or "") else "")))
    if x.get("dress"):
        rows.append(("Dress", x["dress"]))
    dl = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in rows)
    big = ""
    if x.get("starts"):
        s = x["starts"]
        big = f"{int(s[4:6])}.{int(s[6:8])}"
    going = f'<span class="going mono">&#9679; {e(x["going"])}</span>' if x.get("going") else ""
    return f'''
    <a class="lead-ev rv" href="{e(x.get('link'))}" target="_blank" rel="noopener">
      <div class="l">
        <span class="pill mono">&#9829; Hosted by Haps&nbsp;Club</span>
        <h3>{nb(x.get('title','').replace('Haps Club ',''))}</h3>
        <p class="tl">{nb(x.get('long') or x.get('tagline'))}</p>
        <dl class="mono">{dl}</dl>
        <div class="go"><span class="btn or">{e(x.get('cta') or 'Get your ticket')} &rarr;</span><span class="mono mute">Limited tickets</span></div>
      </div>
      <div class="r" aria-hidden="true">{going}<span class="big">{big}</span></div>
    </a>'''


def card(x, n):
    t = first_tag(x)
    _, cls = CATS[t]
    area = AREA_LABEL.get(x.get("area"), "")
    kicker = f"{CATS[t][0]} &middot; {e(x.get('hood_label') or area)}"
    when = x.get("pill") or x.get("when") or ""
    price = x.get("price") or ""
    price_html = f'<b class="free">{e(price)}</b>' if is_free(x) else f"<b>{e(price)}</b>"
    num = f'<div class="n">{n:02d}</div>' if n else ""
    return f'''
      <a class="card {cls} rv" href="{e(x.get('link'))}" target="_blank" rel="noopener">
        {num}
        <div class="mono k">{e(when) if not n else kicker}</div>
        <h3>{nb(x.get('title'))}</h3>
        <p class="tag">{nb(x.get('tagline'))}</p>
        <div class="meta mono"><span>{e(when) if n else e(x.get('meta','').split(' · ')[0] if x.get('meta') else '')}</span>{price_html}</div>
      </a>'''


def row(x):
    t = first_tag(x)
    label, cls = CATS[t]
    month = (x.get("month") or "").upper()
    if month in MONTHS:
        d, small = e(x.get("day")), month
    else:
        d, small = e(x.get("month") or "Any"), {"NEW": "Opening", "NOW": "On now", "ANY": "Anytime",
                                                  "SAT": "Weekly", "SUN": "Weekly"}.get(month, "")
    tags = set((x.get("tags") or "").split())
    cats = [CATS[k][0] for k in CATS if k in tags] or [label]
    if is_free(x):
        cats.append("Free")
    if "date" in tags:
        cats.append("Date night")
    ours = is_ours(x)
    p = e(x.get("price"))
    pcls = "p free" if is_free(x) else "p"
    return (f'<a class="row {cls}{" ours" if ours else ""} rv" data-c="{" ".join(cats)}" data-a="{e(x.get("area") or "citywide")}" '
            f'href="{e(x.get("link"))}" target="_blank" rel="noopener">'
            f'<div class="d">{d}<small>{e(small)}</small></div>'
            f'<div><h4>{e(x.get("title"))}</h4><div class="w">{e(x.get("where"))}</div></div>'
            f'<div class="cat mono">{"Haps event" if ours else label}</div><div class="{pcls}">{p}</div></a>')


def jsonld(lead, items):
    graph = [
        {"@type": "WebSite", "@id": SITE + "/#site", "name": "Haps Club", "url": SITE + "/",
         "description": "A hand-picked guide to the best things happening in Los Angeles every week."},
        {"@type": "Organization", "@id": SITE + "/#org", "name": "Haps Club", "url": SITE + "/",
         "logo": LOGO.split("?")[0], "sameAs": [IG],
         "founder": {"@type": "Person", "name": "Michael Abraham", "url": SITE + "/about.html"}},
    ]
    evs = []
    for x in ([lead] if lead else []) + items:
        if not x or not x.get("starts"):
            continue
        ev = {"@type": "Event", "name": html.unescape(x.get("title", "")),
              "startDate": iso(x["starts"]), "eventStatus": "https://schema.org/EventScheduled",
              "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
              "location": {"@type": "Place", "name": html.unescape(x.get("where") or "Los Angeles"),
                           "address": {"@type": "PostalAddress",
                                       "streetAddress": html.unescape(x.get("addr") or x.get("where") or ""),
                                       "addressLocality": "Los Angeles", "addressRegion": "CA",
                                       "addressCountry": "US"}},
              "description": html.unescape(x.get("tagline") or ""), "url": x.get("link")}
        if x.get("ends"):
            ev["endDate"] = iso(x["ends"])
        if is_ours(x):
            ev["organizer"] = {"@id": SITE + "/#org"}
        evs.append(ev)
    if evs:
        graph.append({"@type": "ItemList", "name": "This week in Los Angeles",
                      "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": ev}
                                          for i, ev in enumerate(evs)]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


# ---------- page ----------
def build(prune=True):
    d, now = load_and_prune(prune)
    featured = list(d.get("featured", []))
    events = sorted(d.get("events", []), key=sort_key)

    lead = next((x for x in featured if x.get("lead")), None) or next((x for x in featured if is_ours(x)), None)
    rest = [x for x in featured if x is not lead]
    if len(rest) < 3:  # auto-promote upcoming dated events
        seen = {x.get("title") for x in featured}
        for x in events:
            if len(rest) >= 3:
                break
            if dated(x) and x.get("title") not in seen and not is_ours(x):
                y = dict(x)
                y.setdefault("pill", f'{x["month"].title()} {x["day"]}')
                rest.append(y)
    rest = rest[:3]

    total = len(events)
    free = sum(1 for x in events if is_free(x))
    week = e(d.get("weekLabel") or "This week")

    upcoming = [x for x in events if dated(x)]
    ticker_src = ([lead] if lead else []) + upcoming[:10]
    tick = "".join(
        f'<span><i class="{CATS[first_tag(x)][1]}"></i>{e(x["title"])} &middot; '
        f'{e((x.get("month") or "").title() + " " + str(x.get("day") or "")) if dated(x) else e(x.get("pill") or "")}</span>'
        for x in ticker_src if x)
    rot = [(x["title"], CATS[first_tag(x)][1]) for x in (upcoming + [y for y in events if not dated(y)])[:8]]

    plan = d.get("plan", [])
    plan_html = ""
    if plan:
        cards = "".join(card(dict(p, pill=p.get("when")), 0) for p in plan[:3])
        plan_html = f'''
  <section class="blk">
    <div class="head"><div><div class="mono sig">(04) Save the date</div><h2>Plan for&nbsp;it</h2></div><span class="mono mute">Buy ahead, these&nbsp;go</span></div>
    <div class="plan">{cards}</div>
  </section>'''

    arch = d.get("archive", [])[:3]
    arch_html = ""
    if arch:
        items = "".join(
            f'<a class="iss rv" href="{e(a["url"])}"><span class="mono mute">{e(a["date"])}</span><b>{nb(a["title"])}</b><span class="ar">&rarr;</span></a>'
            for a in arch)
        arch_html = f'''
  <section class="blk">
    <div class="head"><div><div class="mono sig">(05) From the newsletter</div><h2>Recent&nbsp;issues</h2></div><a href="/archive/">All issues &rarr;</a></div>
    <div class="issues">{items}</div>
  </section>'''

    spons_html = "\n  " + sc.sponsors(d.get("sponsor"), label="(06) Sponsored by")

    chips = "".join(f'<button class="chip{" on" if k=="All" else ""}" data-f="{k}" aria-pressed="{str(k=="All").lower()}">{k}</button>'
                    for k in ["All", "Food", "Music", "Culture", "Outdoors", "Free", "Date night"])
    areas = "".join(f'<button class="chip a{" on" if k=="all" else ""}" data-area="{k}" aria-pressed="{str(k=="all").lower()}">{v}</button>' for k, v in AREAS)

    css_v = _hash(os.path.join(REPO, "assets", "home-f.css"))
    desc = "Everything worth leaving the house for in LA this week. Hand-picked, free weekly newsletter every Tuesday."
    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<script>document.documentElement.className+=" js"</script>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Haps Club — This Week in Los Angeles</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE}/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Haps Club">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{SITE}/">
<meta property="og:title" content="Haps Club — This Week in Los Angeles">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{SITE}/assets/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}/assets/og-card.png">
<meta name="theme-color" content="#FF4F00">
<link rel="icon" href="{LOGO}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500&display=swap">
{sc.chrome_css()}
<link rel="stylesheet" href="/assets/home-f.css?v={css_v}">
<script type="application/ld+json">{jsonld(lead, upcoming)}</script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
</head>
<body>
<!-- Generated by scripts/build_home.py from data/events.json on {now}. Do not hand-edit. -->
{sc.header(active="/#list", absolute=True)}

<div class="ticker mono" aria-hidden="true"><div class="track">{tick}{tick}</div></div>

<main class="wrap">
  <section class="hero" id="join">
    <div class="glow" aria-hidden="true"></div>
    <div class="mono sig">Los Angeles &middot; {week}</div>
    <h1 class="mega"><span class="w"><span>Here&rsquo;s</span></span> <span class="w"><span>what&rsquo;s</span></span> <span class="w"><span>good<span class="dot">.</span></span></span></h1>
    <p class="lead">A weekly edit of the best things happening in LA, plus the dinners, parties, and house concerts we host ourselves. Free, every&nbsp;Tuesday.</p>
    <p class="now"><span class="mono mute">On the list now</span><span class="rot" id="rot"></span></p>
    <form class="join" id="joinform" action="{ML_ACTION}" method="post">
      <label class="sr" for="em">Email address</label>
      <input id="em" type="email" name="fields[email]" required placeholder="Your email" autocomplete="email">
      <input type="hidden" name="ml-submit" value="1"><input type="hidden" name="anticsrf" value="true">
      <button class="btn or" type="submit">Get the Tuesday edit</button>
    </form>
    <div class="join-note mono mute" id="joinnote">Join 1,400+ Angelenos. One email a week. Leave any&nbsp;time.</div>
    <div class="stats">
      <div><div class="num c-sig" data-count="{total}">{total}</div><p class="mono mute">Picks this week</p></div>
      <div><div class="num c-free" data-count="{free}">{free}</div><p class="mono mute">Free&nbsp;picks</p></div>
      <div><div class="num c-music">Tue</div><p class="mono mute">Every week, by&nbsp;hand</p></div>
    </div>
  </section>

  <section class="blk" id="this-week">
    <div class="head"><div><div class="mono sig">(01) Haps picks</div><h2>Featured this&nbsp;week</h2></div><a href="#list">See all {total} &rarr;</a></div>
    {lead_card(lead) if lead else ""}
    <div class="feat">{"".join(card(x, i + 1) for i, x in enumerate(rest))}</div>
  </section>

  <section class="blk">
    <div class="head"><div><div class="mono sig">(02) Pick your scene</div><h2>What are you in the mood&nbsp;for?</h2></div></div>
    <div class="scenes">
      <a class="rv food" href="#list" data-go="Food"><span><span class="sw"></span>Dinners</span><span class="ar">&rarr;</span></a>
      <a class="rv music" href="#list" data-go="Music"><span><span class="sw"></span>Live music</span><span class="ar">&rarr;</span></a>
      <a class="rv culture" href="#list" data-go="Culture"><span><span class="sw"></span>Arts &amp; culture</span><span class="ar">&rarr;</span></a>
      <a class="rv out" href="#list" data-go="Outdoors"><span><span class="sw"></span>Outdoors</span><span class="ar">&rarr;</span></a>
      <a class="rv free" href="#list" data-go="Free"><span><span class="sw"></span>Free this week</span><span class="ar">&rarr;</span></a>
    </div>
  </section>

  <section class="blk" id="list">
    <div class="head"><div><div class="mono sig">(03) The list</div><h2>This week in&nbsp;LA</h2></div><a href="{CAL}" target="_blank" rel="noopener">Full calendar &rarr;</a></div>
    <div class="chips mono" role="group" aria-label="Category">{chips}</div>
    <div class="chips mono areas" role="group" aria-label="Neighborhood">{areas}</div>
    <div id="rows">{"".join(row(x) for x in events)}</div>
    <button class="btn ln more" id="more" type="button" hidden>Show all {total} picks</button>
    <p class="empty mono mute" id="empty" hidden>Nothing here this week. Try another&nbsp;filter.</p>
  </section>
{plan_html}
  <section class="cta rv">
    <div><h2>Get the Tuesday&nbsp;edit</h2><p>The best of LA, and first access to every Haps&nbsp;event.</p></div>
    <a class="btn wh" href="#join">Subscribe free &rarr;</a>
  </section>
{arch_html}
{spons_html}
</main>

{sc.footer(absolute=True)}

<script>window.HAPS_ROT={json.dumps(rot, ensure_ascii=False)};</script>
<script src="/assets/home-f.js?v={_hash(os.path.join(REPO, "assets", "home-f.js"))}" defer></script>
</body>
</html>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"index.html written: {total} picks, {free} free, lead={'yes' if lead else 'no'}, featured={len(rest)}")


def _hash(path):
    import hashlib
    try:
        return hashlib.md5(open(path, "rb").read()).hexdigest()[:8]
    except OSError:
        return "0"


if __name__ == "__main__":
    build(prune="--no-prune" not in sys.argv)
