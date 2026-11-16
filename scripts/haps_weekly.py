#!/usr/bin/env python3
"""haps_weekly.py — the mechanical half of the weekly events run (inbox -> site -> social).

The judgement (which events, what copy) is Claude's, following the haps-weekly-events skill.
This script does the checks and the building, so every run comes out the same way.

  python3 scripts/haps_weekly.py verify  candidates.json            # check cards before they go on the site
  python3 scripts/haps_weekly.py merge   candidates.json            # add verified cards to data/events.json
  python3 scripts/haps_weekly.py photos  social/2026-11-22          # pull each venue's own promo image
  python3 scripts/haps_weekly.py commons social/2026-11-22 slug "Walt Disney Concert Hall" [--pick 2]
  python3 scripts/haps_weekly.py cards   social/2026-11-22          # render every card to JPG
  python3 scripts/haps_weekly.py plan    social/2026-11-22          # captions, schedule, Buffer payloads, review files

A run folder holds run.json (see the skill for the format). Files starting with "_" in a run folder
are review drafts and are git-ignored. Nothing here pushes, publishes or schedules anything.
"""
import argparse
import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS = os.path.join(ROOT, "data", "events.json")
CFG = json.load(open(os.path.join(ROOT, "data", "settings.json"), encoding="utf-8"))
SITE = CFG["site_url"].rstrip("/")
TZ = ZoneInfo(CFG["timezone"])
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"

AREAS = {"westside", "midcity", "dtla", "hollywood", "eastside", "citywide"}
CATS = {"Food", "Music", "Culture", "Outdoors"}
TAGS = {"food", "date", "culture", "music", "free", "outdoors"}
CARD_KEYS = ["title", "month", "day", "cat", "tags", "area", "where", "price", "link", "tagline", "starts", "ends", "addr"]
COLOR = {"Music": "#AF52DE", "Food": "#FF9500", "Culture": "#007AFF", "Outdoors": "#34C759", "Haps": "#FF4F00"}
REVIEW_SITES = ("eater.com", "theinfatuation.com", "yelp.com", "timeout.com", "bucketlisters.com", "feverup.com",
                "resident.com", "discoverlosangeles.com", "lamag.com", "substack.com")
BANNED = re.compile(r"!|\bsingles\b|\bcurated\b|hidden gem|must-visit|hot spot|\biconic\b|\belevated\b|\bjourney\b"
                    r"|\bvibe|don't miss|you won't want to miss|hottest", re.I)
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
IG = "6a6aae084b2d03035f672a37"        # Instagram @thehapsclub
THREADS = "6a692cd74b2d03035f5b5a9c"   # Threads @thehapsclub  (the only two channels this script ever targets)
MAX_FEED_PER_WEEK = 14


# ---------- small helpers ----------
def ts(s):
    return datetime.datetime.strptime(s[:15], "%Y%m%dT%H%M%S") if s else None


def hm(t):
    return f"{t.hour % 12 or 12}" + (f":{t.minute:02d}" if t.minute else "") + (" PM" if t.hour >= 12 else " AM")


def dlabel(d):
    return d.strftime("%a %b ") + str(d.day)


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).replace("’", "'").strip()


def load_events():
    return json.load(open(EVENTS, encoding="utf-8"))


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def http_code(url):
    r = subprocess.run(["curl", "-s", "-L", "-o", "/dev/null", "-w", "%{http_code}", "-A", UA, "--max-time", "25", url],
                       capture_output=True, text=True)
    return r.stdout.strip() or "000"


def last_day(s, en):
    """Last calendar day of a run; an end before 6 AM belongs to the night before."""
    if not en:
        return s.date()
    return en.date() - datetime.timedelta(days=1) if (en.hour < 6 and en.date() > s.date()) else en.date()


# ---------- verify / merge ----------
def check_card(c, existing, now, check_links=True):
    """Returns (fails, warns) for one candidate card."""
    F, W = [], []
    for k in ("title", "cat", "tags", "area", "where", "price", "link", "tagline"):
        if not c.get(k):
            F.append(f"missing {k}")
    if c.get("area") and c["area"] not in AREAS:
        F.append(f"area '{c['area']}' not one of {sorted(AREAS)}")
    if c.get("cat") and c["cat"] not in CATS:
        F.append(f"cat '{c['cat']}' not one of {sorted(CATS)}")
    bad_tags = set((c.get("tags") or "").split()) - TAGS
    if bad_tags:
        F.append(f"unknown tags {sorted(bad_tags)}")
    t = (c.get("title") or "").lower()
    if any(t == e or t.startswith(e) or e.startswith(t) for e in existing if e):
        F.append("already on the site (same or overlapping title)")
    s, en = ts(c.get("starts")), ts(c.get("ends"))
    if c.get("ends") and not c.get("starts") and not (c.get("month") and c.get("day")):
        W.append("has an end but no start: stays off the calendar")
    if s:
        if c.get("month") != MON[s.month - 1] or str(c.get("day")) != str(s.day):
            F.append(f"month/day ({c.get('month')} {c.get('day')}) do not match starts ({MON[s.month-1]} {s.day})")
        if en and en <= s:
            F.append("ends is not after starts")
        if not en:
            W.append("no ends: it will never drop off the site by itself")
        days = {s.strftime("%A").lower(), last_day(s, en).strftime("%A").lower()}
        named = [d for d in WEEKDAYS if re.search(rf"\b{d}\b", (c.get("tagline") or "").lower())]
        if named and last_day(s, en) - s.date() <= datetime.timedelta(days=1) and not set(named) <= days:
            F.append(f"tagline says {named} but the date is a {sorted(days)}")
    if en and en < now:
        F.append("already over")
    for k in ("title", "tagline", "where", "price"):
        m = BANNED.search(c.get(k) or "")
        if m:
            F.append(f"{k} uses a banned word or mark: '{m.group(0)}'")
    if re.search(r"\bLA\b", c.get("tagline") or ""):
        W.append("tagline says 'LA': write 'Los Angeles' unless it is an official name")
    if len(c.get("tagline") or "") > 140:
        W.append(f"tagline is {len(c['tagline'])} chars (aim for 140 or fewer)")
    host = urllib.parse.urlparse(c.get("link") or "").netloc.lower()
    if any(host.endswith(r) for r in REVIEW_SITES):
        F.append(f"link goes to {host}: link the venue's own page")
    if check_links and c.get("link"):
        code = http_code(c["link"])
        if code in ("401", "403", "405", "429"):
            W.append(f"link returned {code} to curl (bot block?): open it in a browser to confirm")
        elif code != "200":
            F.append(f"link returned {code}")
    if not c.get("source"):
        W.append("no 'source' noted (which newsletter or page this came from)")
    return F, W


def cmd_verify(a, quiet=False):
    cand = json.load(open(a.file, encoding="utf-8"))
    d = load_events()
    existing = [e["title"].lower() for e in d["events"]]
    now = datetime.datetime.now()
    ok, results = [], []
    seen = []
    for c in cand.get("cards", []):
        F, W = check_card(c, existing + seen, now, not a.no_links)
        seen.append((c.get("title") or "").lower())
        results.append((c, F, W))
        if not F:
            ok.append(c)
    if not quiet:
        for c, F, W in results:
            s, en = ts(c.get("starts")), ts(c.get("ends"))
            when = (s.strftime("%a %b %d %Y %I:%M %p") + (" -> " + en.strftime("%a %b %d %I:%M %p") if en else "")) if s else "evergreen"
            print(("FAIL " if F else "ok   ") + (c.get("title") or "?")[:60], "|", when)
            for x in F:
                print("       FAIL:", x)
            for x in W:
                print("       warn:", x)
        print(f"\n{len(ok)} of {len(results)} cards pass; {len(cand.get('cut', []))} already cut by hand.")
    return ok, [r for r in results if r[1]]


def cmd_merge(a):
    ok, failed = cmd_verify(a, quiet=True)
    if failed and not a.skip_failed:
        print(f"{len(failed)} card(s) fail verify. Fix them, move them to 'cut', or pass --skip-failed.")
        for c, F, _ in failed:
            print("  FAIL", c.get("title"), "->", "; ".join(F))
        sys.exit(1)
    d = load_events()
    add = [{k: c[k] for k in CARD_KEYS if k in c} for c in ok]
    dated = sorted([e for e in d["events"] if e.get("starts")] + [x for x in add if x.get("starts")], key=lambda e: e["starts"])
    rest = [e for e in d["events"] if not e.get("starts")] + [x for x in add if not x.get("starts")]
    d["events"] = dated + rest
    cand = json.load(open(a.file, encoding="utf-8"))
    for key in ("featured", "plan"):
        if cand.get(key):
            if key == "featured" and len(cand[key]) != 3:
                sys.exit("featured must have exactly 3 cards")
            d[key] = cand[key]
            print(f"replaced {key} ({len(cand[key])} cards)")
    save_json(EVENTS, d)
    print(f"added {len(add)} card(s); events.json now has {len(d['events'])}. Next: python3 scripts/sweep.py")


# ---------- photos ----------
def fetch(url, timeout=25):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout).read()


def to_jpg(src, dst):
    subprocess.run(["sips", "-s", "format", "jpeg", src, "--out", dst], capture_output=True)
    return os.path.exists(dst)


def run_paths(folder):
    folder = os.path.abspath(folder)
    return folder, os.path.join(folder, "run.json"), os.path.join(folder, "src")


def sheet(files, out, cols=8, width=1600, labels=True):
    """Contact sheet PNG of image files, rendered outside the repo."""
    tmp = tempfile.mkdtemp(prefix="haps-sheet-")
    cells = "".join(
        f'<div style="position:relative"><img src="file://{f}" style="width:100%;display:block">'
        + (f'<span style="position:absolute;left:0;bottom:0;background:#000c;color:#fff;font:11px sans-serif;padding:2px 4px">{os.path.basename(f)}</span>' if labels else "")
        + "</div>" for f in files)
    page = os.path.join(tmp, "s.html")
    open(page, "w").write(f'<html><body style="margin:0;background:#333;display:grid;grid-template-columns:repeat({cols},1fr);gap:3px;width:{width}px;align-items:start">{cells}</body></html>')
    rows = -(-len(files) // cols)
    h = int(rows * (width / cols) * 1.3) + 20
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--window-size={width},{h}", f"--screenshot={out}", "file://" + page], capture_output=True)
    shutil.rmtree(tmp, ignore_errors=True)


def cmd_photos(a):
    folder, runf, src = run_paths(a.folder)
    run = json.load(open(runf, encoding="utf-8"))
    os.makedirs(src, exist_ok=True)
    got = []
    events = {e["title"]: e for e in load_events()["events"]}
    for p in run["posts"]:
        link = p.get("link") or (event_for(p, events) or {}).get("link")
        if "photo" in p or not link:
            continue
        try:
            page = fetch(link).decode("utf8", "ignore")
            m = (re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page)
                 or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', page))
            if not m:
                p["photo"] = None
                print("none ", p["slug"], "(no og:image)")
                continue
            raw = os.path.join(src, "_" + p["slug"])
            open(raw, "wb").write(fetch(urllib.parse.urljoin(link, html.unescape(m.group(1)))))
            dst = os.path.join(src, p["slug"] + ".jpg")
            if to_jpg(raw, dst):
                p["photo"], p["photo_source"] = "src/" + p["slug"] + ".jpg", "venue page"
                got.append(dst)
                print("photo", p["slug"])
            os.remove(raw)
        except Exception as ex:
            p["photo"] = None
            print("none ", p["slug"], str(ex)[:50])
    save_json(runf, run)
    if got:
        out = os.path.join(folder, "_photos.png")
        sheet(got, out)
        print(f"\nLook at {out}. Logos, posters and text-heavy images make bad backgrounds: set those posts' \"photo\" to null.")


def cmd_commons(a):
    folder, runf, src = run_paths(a.folder)
    stash = os.path.join(folder, "_commons")
    os.makedirs(stash, exist_ok=True)
    credf = os.path.join(stash, "credits.json")
    cred = json.load(open(credf)) if os.path.exists(credf) else {}
    if a.pick:
        key = f"{a.slug}-{a.pick}"
        if key not in cred:
            sys.exit(f"no saved candidate {key}; run without --pick first")
        os.makedirs(src, exist_ok=True)
        shutil.copy(os.path.join(stash, key + ".jpg"), os.path.join(src, a.slug + ".jpg"))
        run = json.load(open(runf, encoding="utf-8"))
        for p in run["posts"]:
            if p["slug"] == a.slug:
                c = cred[key]
                p["photo"], p["photo_source"] = "src/" + a.slug + ".jpg", c["url"]
                free = re.search(r"public domain|CC0|^PD", c["license"], re.I)
                p["credit"] = None if free else f"{c['artist']}, {c['license']}, via Wikimedia Commons"
                print("set", a.slug, "->", c["title"], "| credit:", p["credit"] or "none needed")
        save_json(runf, run)
        return
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                "gsrsearch": a.query + " filetype:bitmap", "gsrlimit": 8, "prop": "imageinfo",
                                "iiprop": "url|size|extmetadata", "iiurlwidth": 1600})
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + q, headers={"User-Agent": "HapsCardBuilder/1.0 (https://haps.club)"})
    pages = sorted(json.load(urllib.request.urlopen(req, timeout=25)).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    n, files = 0, []
    for p in pages:
        ii = p["imageinfo"][0]
        md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        if ii["width"] < 1000 or not re.search(r"CC|Public domain|PD", lic, re.I):
            continue
        n += 1
        key = f"{a.slug}-{n}"
        f = os.path.join(stash, key + ".jpg")
        open(f, "wb").write(urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers={"User-Agent": "HapsCardBuilder/1.0 (https://haps.club)"}), timeout=30).read())
        artist = plain(md.get("Artist", {}).get("value", "")).split("\n")[0][:60]
        cred[key] = {"title": p["title"], "artist": artist, "license": lic, "url": ii["descriptionurl"]}
        files.append(f)
        print(f"{n}. {p['title']} | {artist} | {lic}")
        if n >= 4:
            break
    save_json(credf, cred)
    if files:
        out = os.path.join(stash, a.slug + "-sheet.png")
        sheet(files, out, cols=4, width=1200)
        print(f"\nLook at {out}, check the photo really shows the right place, then: commons {a.folder} {a.slug} \"{a.query}\" --pick N")
    else:
        print("no freely licensed photos found")


# ---------- cards ----------
EXTRA_CSS = (".compact h2{font-size:76px;letter-spacing:-2.5px;line-height:.98}.compact .sub{font-size:32px;max-width:760px;margin-top:22px}"
             ".compact .meta{margin-top:30px;padding-top:18px}.compact .meta div{font-size:22px}.compact .pill{font-size:22px;padding:9px 18px}"
             ".statement h2.stmt{font-size:104px;line-height:.98;letter-spacing:-4px;max-width:900px}.statement .cue{margin-top:44px;font-size:26px;opacity:.85}")


def card_css():
    page = open(os.path.join(ROOT, "scripts", "social_cards.html"), encoding="utf-8").read()
    return re.search(r"<style>(.*?)</style>", page, re.S).group(1) + EXTRA_CSS


def event_for(p, events):
    return events.get(p.get("event") or p.get("title") or "")


def card_meta(p, e, today):
    if p.get("meta"):
        return p["meta"]
    if not e:
        sys.exit(f"post '{p['slug']}' has no matching event in events.json and no \"meta\"")
    s, en = ts(e.get("starts")), ts(e.get("ends"))
    place = html.escape(e.get("where", "").split(",")[-1].strip() or "Los Angeles")
    price = html.escape(e.get("price", ""))
    if not s and not en:
        return [["Now open", html.escape(e.get("where", "").split(",")[0])], [place, price]]
    if not s:
        return [["Through " + en.strftime("%b ") + str(en.day), ""], [place, price]]
    last = last_day(s, en)
    if last == s.date():
        return [[dlabel(s), hm(s) + ("&ndash;" + hm(en) if en and en > s and not p.get("start_only") else "")], [place, price]]
    return [["Opens " + dlabel(s) if s.date() > today else "Now on", "Through " + last.strftime("%b ") + str(last.day)], [place, price]]


def card_pill(p, e):
    if "pill" in p:
        return [p["pill"][0], COLOR.get(p["pill"][1], p["pill"][1])] if p["pill"] else None
    if not e:
        return None
    return [("Free &middot; " if "free" in e.get("tags", "") else "") + e["cat"], COLOR[e["cat"]]]


def card_html(d, css, folder, story=False, label="Haps pick"):
    cls, bg = d.get("cls", ""), d.get("bg")
    white = bool(bg) or cls == "orange"
    logo = '<img src="file://%s/assets/img/haps-logo.svg"%s>' % (ROOT, ' style="filter:brightness(0) invert(1)"' if white else "")
    inner = f'<div class="bg" style="background-image:url(file://{bg})"></div><div class="shade"></div>' if bg else ""
    inner += f'<div class="bar"></div><div class="top">{logo}<div class="m n">Los Angeles<br>{label}</div></div><div class="mid">'
    scls = "s photo" if bg else ("s " + cls).strip()
    if d.get("layout") == "C" and d.get("statement"):
        scls += " statement"
        inner += f'<h2 class="stmt">{d["statement"]}</h2><div class="cue m">Details in the caption &darr;</div></div>'
    else:
        if d.get("layout") == "B":
            scls += " compact"
        if d.get("pill"):
            inner += f'<span class="pill" style="background:{d["pill"][1]}">{d["pill"][0]}</span>'
        inner += d["h"] + f'<p class="sub">{d["sub"]}</p><div class="meta">' + "".join(f"<div><b>{x}</b>{y}</div>" for x, y in d["meta"]) + "</div></div>"
    fonts = '<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;700;800;900&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">'
    return f'<!doctype html><html><head><meta charset="utf-8">{fonts}<style>{css}</style></head><body class="{"story" if story else ""}"><div class="{scls}" id="s">{inner}</div></body></html>'


def build_cards(folder, run, events, today):
    """Returns {slug: card dict} and the render jobs [(filename, html, story)]."""
    css = card_css()
    cards, jobs = {}, []
    plain_cycle = ["", "lead", "orange"]
    n_plain = 0
    for p in run["posts"]:
        e = event_for(p, events)
        when = p.get("post_at") or p.get("story_at")           # "Opens ..." vs "Now on" is judged on the posting day
        day = datetime.date.fromisoformat(when[:10]) if when else today
        d = {"h": f'<h2>{p["headline"]}</h2>', "sub": p.get("sub", ""), "meta": card_meta(p, e, day), "pill": card_pill(p, e),
             "layout": p.get("layout", "A"), "statement": p.get("statement")}
        if d["layout"] == "C" and not d["statement"]:
            sys.exit(f"post '{p['slug']}' is layout C but has no \"statement\"")
        if p.get("photo"):
            d["bg"] = os.path.join(folder, p["photo"])
            if not os.path.exists(d["bg"]):
                sys.exit(f"post '{p['slug']}': photo {p['photo']} not found")
        else:
            d["cls"] = p.get("cls", plain_cycle[n_plain % 3])
            n_plain += 1
        cards[p["slug"]] = d
        if p.get("post_at"):
            jobs.append((f'single-{p["slug"]}.jpg', card_html(d, css, folder), False))
        if p.get("story_at"):
            jobs.append((f'story-{p["slug"]}.jpg', card_html(dict(d, layout="A"), css, folder, story=True), True))
    for c in run.get("carousels", []):
        n = len(c["items"]) + 1
        cover = {"h": f'<h1>{c["title"]}<span class="dot">.</span></h1>', "sub": c["sub"], "meta": c["meta"], "cls": c.get("cls", "")}
        jobs.append((f'carousel-{c["slug"]}-01.jpg', card_html(cover, css, folder, label=f"01 / {n:02d}"), False))
        for j, s in enumerate(c["items"], 2):
            if s not in cards:
                sys.exit(f"carousel '{c['slug']}' item '{s}' is not a post slug")
            jobs.append((f'carousel-{c["slug"]}-{j:02d}.jpg', card_html(dict(cards[s], layout="A"), css, folder, label=f"{j:02d} / {n:02d}"), False))
    return cards, jobs


def cmd_cards(a):
    folder, runf, _ = run_paths(a.folder)
    run = json.load(open(runf, encoding="utf-8"))
    events = {e["title"]: e for e in load_events()["events"]}
    _, jobs = build_cards(folder, run, events, datetime.date.today())
    tmp = tempfile.mkdtemp(prefix="haps-cards-")
    made = []
    for name, page, story in jobs:
        h = os.path.join(tmp, name + ".html")
        open(h, "w", encoding="utf-8").write(page)
        png = os.path.join(tmp, name + ".png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000",
                        "--allow-file-access-from-files", f"--window-size=1080,{1920 if story else 1350}",
                        f"--screenshot={png}", "file://" + h], capture_output=True)
        out = os.path.join(folder, name)
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "88", png, "--out", out], capture_output=True)
        if not os.path.exists(out):
            sys.exit(f"render failed: {name}")
        made.append(out)
    shutil.rmtree(tmp, ignore_errors=True)
    for old in [f for f in os.listdir(folder) if f.startswith("_preview-")]:
        os.remove(os.path.join(folder, old))
    for i in range(0, len(made), 40):
        sheet(made[i:i + 40], os.path.join(folder, f"_preview-{i // 40 + 1}.png"), cols=10, labels=False)
    print(f"{len(made)} cards rendered. Review sheets: {folder}/_preview-*.png")


# ---------- plan ----------
def details_line(p, e, post_day):
    if "details" in p:
        return p["details"]
    if not e:
        return ""
    s, en = ts(e.get("starts")), ts(e.get("ends"))
    where = e.get("where", "")
    price = e.get("price", "")
    price = "" if price.lower() in ("tickets", "reservations", "reservations required", "") else "\n" + price
    if not s and not en:
        return f"Now open · {where}"
    if not s:
        return f"Through {en.strftime('%b')} {en.day} · {where}{price}"
    last = last_day(s, en)
    if last == s.date():
        t = hm(s) + ("–" + hm(en) if en and en > s and not p.get("start_only") else "")
        return f"{dlabel(s)} · {t} · {where}{price}"
    if s.date() <= post_day:
        return f"Through {last.strftime('%a %b')} {last.day} · {where}{price}"
    return f"{dlabel(s)} – {last.strftime('%a %b')} {last.day} · {where}{price}"


def aware(local):
    return datetime.datetime.strptime(local, "%Y-%m-%dT%H:%M").replace(tzinfo=TZ)


def image_asset(folder, name, alt):
    return {"image": {"url": f"{SITE}/social/{os.path.basename(folder)}/{name}", "metadata": {"altText": alt[:300]}}}


def cmd_plan(a):
    folder, runf, _ = run_paths(a.folder)
    run = json.load(open(runf, encoding="utf-8"))
    events = {e["title"]: e for e in load_events()["events"]}
    cards, jobs = build_cards(folder, run, events, datetime.date.today())
    missing = [n for n, _, _ in jobs if not os.path.exists(os.path.join(folder, n))]
    if missing:
        sys.exit(f"{len(missing)} card(s) not rendered yet (run `cards` first): {missing[:3]}")
    now = datetime.datetime.now(TZ)
    posts = {p["slug"]: p for p in run["posts"]}
    alt = {s: plain(posts[s]["headline"]) + ". " + plain(posts[s].get("sub", "")) for s in posts}
    rows, problems, warns = [], [], []

    def add(channel, kind, at, key, text, assets, meta):
        if at <= now:
            problems.append(f"{key}: {kind} time {at:%a %b %d %H:%M} is in the past")
        rows.append({"channelId": channel, "schedulingType": "automatic", "mode": "customScheduled", "dueAt": at.isoformat(),
                     "text": text, "assets": assets, "metadata": meta, "_kind": kind, "_key": key, "_at": at})

    def lint(key, text, where):
        m = BANNED.search(text)
        if m:
            problems.append(f"{key} {where}: banned word or mark '{m.group(0)}'")
        if re.search(r"\b(today|tonight|tomorrow)\b", text, re.I):
            warns.append(f"{key} {where}: says today/tonight/tomorrow; check it matches the posting day")

    for p in run["posts"]:
        e = event_for(p, events)
        link = p.get("link") or (e or {}).get("link")
        if not p.get("post_at") and not p.get("story_at"):
            continue
        if not link:
            problems.append(f"{p['slug']}: no link")
        if p.get("post_at"):
            at = aware(p["post_at"])
            det = details_line(p, e, at.date())
            credit = f"Photo: {p['credit']}\n\n" if p.get("credit") else ""
            cap = "\n\n".join(x for x in [p["hook"], p["body"], det, f'{p.get("linkword", "Details")}: link in bio', p["question"]] if x)
            cap += "\n\n" + credit + p["hashtags"]
            lint(p["slug"], cap, "caption")
            img = [image_asset(folder, f'single-{p["slug"]}.jpg', alt[p["slug"]])]
            add(IG, "IG feed", at, p["slug"], cap, img, {"instagram": {"type": "post", "shouldShareToFeed": True, "firstComment": link}})
            if p.get("threads", True):
                th = f'{p["hook"]} {p["body"]}\n\n{link}\n\n{p["question"]}'
                if len(th) > 500:
                    problems.append(f"{p['slug']} Threads: {len(th)} chars (max 500)")
                lint(p["slug"], th, "Threads")
                add(THREADS, "Threads", aware(p["threads_at"]) if p.get("threads_at") else at + datetime.timedelta(hours=1),
                    p["slug"], th, img, {"threads": {"type": "post"}})
        if p.get("story_at"):
            add(IG, "IG story", aware(p["story_at"]), p["slug"], "", [image_asset(folder, f'story-{p["slug"]}.jpg', alt[p["slug"]])],
                {"instagram": {"type": "story", "shouldShareToFeed": False, "link": link}})
    for c in run.get("carousels", []):
        at = aware(c["post_at"])
        link = c.get("link", SITE)
        credits = "; ".join(sorted({posts[s]["credit"].replace(", via Wikimedia Commons", "") for s in c["items"] if posts[s].get("credit")}))
        credit = f"Photos: {credits}, via Wikimedia Commons\n\n" if credits else ""
        cap = "\n\n".join([c["hook"], c["body"], f'{c.get("linkline", "All on haps.club")}: link in bio', c["question"]]) + "\n\n" + credit + c["hashtags"]
        lint(c["slug"], cap, "caption")
        n = len(c["items"]) + 1
        cover_alt = plain(c["title"]) + ". " + plain(c["sub"])
        imgs = [image_asset(folder, f'carousel-{c["slug"]}-01.jpg', cover_alt)] + [
            image_asset(folder, f'carousel-{c["slug"]}-{j:02d}.jpg', alt[s]) for j, s in enumerate(c["items"], 2)]
        if n > 10:
            problems.append(f"{c['slug']}: {n} slides (Instagram allows 10)")
        add(IG, "IG feed", at, c["slug"], cap, imgs, {"instagram": {"type": "post", "shouldShareToFeed": True, "firstComment": link}})
        if c.get("threads", True):
            th = f'{c["hook"]} {c["body"]}\n\n{link}\n\n{c["question"]}'
            if len(th) > 500:
                problems.append(f"{c['slug']} Threads: {len(th)} chars (max 500)")
            add(THREADS, "Threads", at + datetime.timedelta(hours=1), c["slug"], th, imgs[:1], {"threads": {"type": "post"}})

    # slot checks: within this run, and against what Buffer already holds (_busy.json, written from list_posts)
    busyf = os.path.join(folder, "_busy.json")
    busy = set()
    if os.path.exists(busyf):
        for b in json.load(open(busyf)):
            busy.add((b["channelId"], datetime.datetime.fromisoformat(b["dueAt"].replace("Z", "+00:00")).astimezone(TZ).strftime("%Y-%m-%d %H:%M")))
    else:
        warns.append("no _busy.json: slots were NOT checked against the existing Buffer queue")
    seen = {}
    for r in rows:
        k = (r["channelId"], r["_at"].strftime("%Y-%m-%d %H:%M"))
        if k in busy:
            problems.append(f"{r['_key']}: {r['_kind']} slot {k[1]} is already taken in Buffer")
        k2 = k + (r["_kind"] == "IG story",)          # a story and a feed post may share a minute
        if k2 in seen:
            problems.append(f"{r['_key']}: two {r['_kind']} posts at {k[1]}")
        seen[k2] = r["_kind"]
    feed = [r for r in rows if r["_kind"] == "IG feed"]
    per_day = {}
    for r in feed:
        per_day[r["_at"].date()] = per_day.get(r["_at"].date(), 0) + 1
    for day, n in per_day.items():
        if n > 3:
            warns.append(f"{n} feed posts on {day:%a %b %d} (3 a day is the ceiling)")
    if len(feed) > MAX_FEED_PER_WEEK:
        warns.append(f"{len(feed)} feed posts in this run (weekly target is 10 to {MAX_FEED_PER_WEEK})")

    rows.sort(key=lambda r: r["_at"])
    payloads = [{k: v for k, v in r.items() if not k.startswith("_") and not (k == "text" and not v)} for r in rows]
    save_json(os.path.join(folder, "_payloads.json"), payloads)
    md = [f"# Haps social run: {os.path.basename(folder)}", "",
          "Draft for review. Nothing is pushed or scheduled until Michael says go.", "",
          f"- Instagram feed: {len(feed)} · stories: {sum(r['_kind'] == 'IG story' for r in rows)} · Threads: {sum(r['_kind'] == 'Threads' for r in rows)}",
          "- Card previews: `_preview-*.png` in this folder", ""]
    if problems:
        md += ["## Problems to fix before scheduling", ""] + [f"- {x}" for x in problems] + [""]
    if warns:
        md += ["## Check", ""] + [f"- {x}" for x in warns] + [""]
    md += ["## Schedule (Pacific)", "", "| When | Channel | Post | Layout | Images |", "|---|---|---|---|---|"]
    for r in rows:
        lay = posts[r["_key"]].get("layout", "A") if r["_key"] in posts and r["_kind"] == "IG feed" else ""
        md.append(f"| {r['_at']:%a %b %-d, %-I:%M %p} | {r['_kind']} | {r['_key']} | {lay} | {len(r['assets'])} |")
    md += ["", "## Captions", ""]
    for r in rows:
        if r["text"]:
            md += [f"### {r['_at']:%a %b %-d, %-I:%M %p} · {r['_kind']} · {r['_key']}", "", "```", r["text"], "```", ""]
    if run.get("cut"):
        md += ["## Left out this week", ""] + [f"- **{c['title']}**: {c['reason']}" for c in run["cut"]] + [""]
    open(os.path.join(folder, "_PLAN.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"{len(rows)} posts planned: {len(feed)} feed, {sum(r['_kind'] == 'IG story' for r in rows)} stories, {sum(r['_kind'] == 'Threads' for r in rows)} Threads")
    for x in problems:
        print("PROBLEM:", x)
    for x in warns:
        print("check:  ", x)
    print(f"Review: {folder}/_PLAN.md  ·  Buffer payloads: {folder}/_payloads.json")
    sys.exit(1 if problems else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("verify", "merge"):
        s = sub.add_parser(name)
        s.add_argument("file")
        s.add_argument("--no-links", action="store_true", help="skip the live-link check")
        if name == "merge":
            s.add_argument("--skip-failed", action="store_true", help="merge the passing cards and leave the failing ones out")
    for name in ("photos", "cards", "plan"):
        sub.add_parser(name).add_argument("folder")
    s = sub.add_parser("commons")
    s.add_argument("folder")
    s.add_argument("slug")
    s.add_argument("query")
    s.add_argument("--pick", type=int)
    a = ap.parse_args()
    {"verify": cmd_verify, "merge": cmd_merge, "photos": cmd_photos, "commons": cmd_commons, "cards": cmd_cards, "plan": cmd_plan}[a.cmd](a)


if __name__ == "__main__":
    main()
