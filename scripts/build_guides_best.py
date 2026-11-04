#!/usr/bin/env python3
"""
build_guides_best.py — two evergreen guides added 2026-11-04.

    python3 scripts/build_guides_best.py     # writes both pages and registers them
    python3 scripts/build_pages.py           # (the sweep does this) fills the live event blocks

  /guides/best-museums-los-angeles/   which museum for which mood
  /guides/fall-hikes-los-angeles/     what is open, what is still closed after the fires

Same rules as the other guides: every fact below was read on the venue's or agency's own page and the
page is linked next to it. Anything that could not be confirmed is listed under "Left off on purpose".

RE-CHECK: the hikes page makes status claims that change. When you re-verify, update CHECKED_HIKES
and CHECKED_MUSEUMS below (the date shows on the page). Separate file from build_guides.py on purpose:
re-running that file would roll back hand corrections to older guides.

Registration (guides/index.html card, sitemap.xml, llms.txt) is automatic and idempotent.
"""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_guides import (head, ghero, facts, jump, intro, sec, place, placelist, oneline, table,
                          live_block, morelinks, breadcrumb, webpage, ld, w, FOOT, ICON_FOR, icon)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://haps.club"
PUB = "2026-11-04"
CHECKED_MUSEUMS = "4 November 2026"
CHECKED_HIKES = "4 November 2026"
TODAY = datetime.date.today().isoformat()


def a(href, text):
    return f'<a href="{href}" target="_blank" rel="noopener">{text}</a>'


# ============================== MUSEUMS ==============================
# (anchor-group, name, detail, cat, url, tags, schema address or None)
MUSEUMS = [
 ("art", "Getty Center",
  "Free · timed reservation required · closed Mondays · parking $25, $15 after 3pm, $10 after 6pm, free Saturday after 6pm.",
  "museum", "https://www.getty.edu/visit/center/", [("Free", "free"), ("Hilltop", "cat")], None),
 ("art", "LACMA",
  "$25 for LA County residents, $30 for everyone else · free second Tuesday and for county residents weekdays after 3pm · closed Wednesdays.",
  "museum", "https://www.lacma.org/tickets", [("Sprawling", "cat")], None),
 ("art", "The Broad",
  "Free · 221 S Grand Ave · closed Mondays · timed ticket recommended, walk-ups daily · parking $19 for 3 hours with validation, $29 a day.",
  "museum", "https://www.thebroad.org/visit", [("Free", "free"), ("Contemporary", "cat")], None),
 ("art", "MOCA Grand Avenue",
  "Free · 250 S Grand Ave · closed Mondays · open until 8pm on the first Thursday of the month (second in January and July).",
  "museum", "https://www.moca.org/plan-your-visit", [("Free", "free"), ("Contemporary", "cat")], "250 S Grand Ave"),
 ("art", "Hammer Museum",
  "Free, no reservation · 10899 Wilshire Blvd, Westwood · Tue–Sun 11am–6pm · parking $9 for 3 hours with validation.",
  "museum", "https://hammer.ucla.edu/visit", [("Free", "free"), ("Westside", "cat")], "10899 Wilshire Blvd"),
 ("more", "Academy Museum of Motion Pictures",
  "$25 adults · 6067 Wilshire Blvd · Wed–Mon 10am–6pm, closed Tuesdays · advance tickets encouraged.",
  "art", "https://www.academymuseum.org/visit", [("Film", "cat")], "6067 Wilshire Blvd"),
 ("more", "Natural History Museum",
  "Open daily 9:30am–5pm · closed the first Tuesday of every month · free for LA County residents weekdays 3–5pm, bookable online with ID.",
  "museum", "https://nhm.org/plan-your-visit/nhm-buy-tickets", [("Dinosaurs", "cat")], None),
 ("more", "California Science Center",
  "Free permanent galleries, no reservation · IMAX and special exhibitions are ticketed separately.",
  "museum", "https://californiasciencecenter.org/visit", [("Free", "free"), ("Science", "cat")], None),
 ("quiet", "The Huntington",
  "San Marino · closed Tuesdays · timed tickets · free first Thursday of the month, with a reservation that sells out.",
  "park", "https://www.huntington.org/plan-your-visit", [("Gardens", "cat")], None),
 ("quiet", "Norton Simon Museum",
  "Pasadena · free first Friday 4–7pm · free every day for students and anyone 18 and under · free parking lot.",
  "museum", "https://www.nortonsimon.org/visit/", [("Pasadena", "cat")], None),
 ("quiet", "Skirball Cultural Center",
  "$20 general · free on Thursdays · 2701 N Sepulveda Blvd · Tue–Fri noon–5pm, Sat–Sun 10am–5pm, closed Mondays · free on-site parking.",
  "museum", "https://www.skirball.org/visit/overview", [("Free Thursdays", "free")], "2701 N Sepulveda Blvd"),
]


def build_museums():
    url = f"{SITE}/guides/best-museums-los-angeles/"
    title = "Best Museums in Los Angeles: Which One for Which Mood"
    desc = ("Los Angeles' best museums sorted by mood, with what is free, which day each is closed "
            "and what it costs, all read off each museum's own site.")
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("Best museums", url),
             {"@type": "ItemList", "name": "Best museums in Los Angeles", "url": url,
              "numberOfItems": len(MUSEUMS), "itemListOrder": "https://schema.org/ItemListUnordered",
              "itemListElement": [
                  {"@type": "ListItem", "position": i, "item": dict(
                      {"@type": "Museum" if m[3] != "park" else "Garden", "name": m[1], "url": m[4]},
                      **({"address": {"@type": "PostalAddress", "streetAddress": m[6], "addressLocality": "Los Angeles",
                                      "addressRegion": "CA", "addressCountry": "US"}} if m[6] else {}))}
                  for i, m in enumerate(MUSEUMS, 1)]}]
    rows = lambda g: [place(n, d, c, u, t) for (gg, n, d, c, u, t, _) in MUSEUMS if gg == g]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; citywide", "Which museum, <em>for which mood</em>",
               "Eleven that are worth the drive, sorted by what you actually feel like doing.")
    b += facts([("Free every day", "Getty, Broad, MOCA, Hammer"), ("Closed Mondays", "Most of the art ones"),
                ("Best first visit", "The Getty"), ("Checked", CHECKED_MUSEUMS)])
    b += jump([("Big art", "art", "museum"), ("Film, dinosaurs, space", "more", "art"),
               ("Gardens and quiet", "quiet", "park"), ("Closed days", "closed", "clock"),
               ("This week", "this-week", "ticket")])
    b += intro(["LA has no single museum you have to see, which is the problem. There are a dozen good ones, scattered across forty miles, and the wrong choice means a bad parking garage and a room you did not want.",
                "So this is not a ranking. It is a way to pick: how much time you have, whether you want contemporary or old, indoors or out. Each one is linked to its own site, and the free ones say so."])
    b += sec("Big art", "Five that fill an afternoon.",
             ["<b>The Getty Center</b> is the one for a first visit: a hilltop of Richard Meier architecture and gardens that explains the city before you look at a single painting. Free, but you need a timed reservation and the parking is $25.",
              "<b>LACMA</b> is the only one of the five that charges, and a campus you can lose a day in. If you are a county resident, go on a weekday after 3pm and it is free; everyone else gets the second Tuesday of the month.",
              "<b>The Broad</b> and <b>MOCA</b> sit a block apart on Grand Avenue, both free, both contemporary, and you can do them in one trip. The Broad's Infinity Mirrored Room needs its own advance reservation. The <b>Hammer</b> in Westwood is the small, easy one: free, no reservation, two hours is plenty."],
             "art")
    b += placelist(rows("art"))
    b += sec("Film, dinosaurs and space", "For when you want a reason to go, not a gallery.",
             ["The <b>Academy Museum</b> is the film one and the only one in this group that closes on Tuesdays. The <b>Natural History Museum</b> is the dinosaurs, and with the free county-resident hours on weekday afternoons it is the cheapest good afternoon in the city.",
              "The <b>California Science Center</b> is free to walk in; budget separately for IMAX and the special exhibitions."],
             "more")
    b += placelist(rows("more"))
    b += sec("Gardens and quiet rooms", "Slower, and further out.",
             ["<b>The Huntington</b> is the one to spend a whole day on: two hundred acres, and the Japanese and Chinese gardens are the reason to go. Buy timed tickets and skip Tuesdays.",
              "<b>Norton Simon</b> in Pasadena is a compact, serious collection with a free parking lot. <b>Skirball</b> on the Sepulveda Pass is free on Thursdays, with free parking, which makes it the best-value weekday visit on the Westside."],
             "quiet")
    b += placelist(rows("quiet"))
    b += sec("Plan around the closed day", "Almost every one closes on a different day.",
             ["The mistake that wastes a drive is turning up on the day that museum is dark. Here is the day each one is closed."], "closed")
    b += table(["Museum", "Closed", "Cost"], [
        ["Getty Center, The Broad, MOCA, Hammer, Skirball", "Mondays", "Free except Skirball ($20, free Thursdays)"],
        ["Academy Museum", "Tuesdays", "$25 adults"],
        ["The Huntington", "Tuesdays", "Timed tickets, free first Thursday"],
        ["LACMA", "Wednesdays", "$25 county residents, $30 others"],
        ["Natural History Museum", "First Tuesday of the month", "Free weekdays 3–5pm for county residents"]])
    b += oneline("If you only do one thing",
        "The Getty on a weekday morning, then lunch in Brentwood. It is free, it is on the Westside, and it works for someone who does not like museums.")
    b += sec("What we could not verify", "Left off on purpose.",
             ["The Museum of Jurassic Technology on Venice Boulevard is a real favourite, but its hours and admission are not on any page we could read, so we are not printing them. The Petersen Automotive Museum lists different prices on different pages of its own site.",
              "If you spot something that has changed, <a href=\"/about#tip\">tell us</a> and it gets fixed on the next check."])
    b += live_block("tags:culture", "", 4, "Museums and culture this week",
        "Refreshed every day from the same list that runs on the homepage.", "Culture this week", cat="museum")
    b += morelinks([("Free museum days →", "/guides/free-museum-days-los-angeles/"),
                    ("Fall hikes →", "/guides/fall-hikes-los-angeles/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w("guides/best-museums-los-angeles/index.html", b)


# ============================== FALL HIKES ==============================
HIKES = [
 ("open", "Griffith Park, from the Observatory",
  "Free · Observatory open Tue–Fri noon–10pm, Sat–Sun 10am–10pm, closed Mondays · trailheads on its grounds lead to Mount Hollywood, the Greek Theatre area and Fern Dell.",
  "park", "https://griffithobservatory.lacity.gov/visit/", [("Free", "free"), ("City", "cat")]),
 ("open", "Temescal Gateway Park, Pacific Palisades",
  "Reopened July 17, 2026 · the rebuilt Rivas Trail reaches two overlooks, the Sunset Trail runs up to the ridge · the waterfall trail is still closed.",
  "park", "https://smmc.ca.gov/press/temescal-gateway-park-to-reopen-july-17-2026-marking-major-milestone-in-palisades-fire-recovery/", [("Reopened", "cat")]),
 ("open", "Solstice Canyon, Malibu",
  "National Park Service · easy to strenuous options, about the first half mile paved · ends at the Roberts Ranch ruins and a waterfall that is only a trickle · dogs on a leash of six feet or less.",
  "park", "https://www.nps.gov/samo/planyourvisit/solsticecanyon.htm", [("Malibu", "cat")]),
 ("open", "Sycamore Canyon, Point Mugu State Park",
  "Open with some restricted services · day use $12 · Sycamore Canyon parking 8am–10pm, the beach and La Jolla Canyon lots 8am to sunset · more than 70 miles of trails in the park.",
  "park", "https://www.parks.ca.gov/?page_id=630", [("State park", "cat")]),
 ("open", "Angeles National Forest, Eaton-fire trails that reopened",
  "Sunset Ridge, Dawn Mine, Tom Sloane and Bear Canyon trails are open again, and so is the Mount Wilson Trail out of Sierra Madre · the road up to Sunset Ridge is closed to cars until fall 2026, so check before you drive.",
  "park", "https://trails.lacounty.gov/Alert/4270/eaton-fire-closures-and-palisades-fire-closures", [("Reopened", "cat")]),
]

CLOSED = [
 ("Eaton Canyon Trail and Eaton Canyon Waterfall", "Altadena", "December 31, 2027"),
 ("Altadena Crest, Chaney and Hastings Debris Basin trails", "Altadena", "December 31, 2027"),
 ("Mount Lowe, Echo Mountain, Idlehour and Sam Merrill trails", "Angeles National Forest", "December 31, 2027"),
 ("Bailey Canyon Wilderness Park", "Sierra Madre", "Closed, no date given"),
 ("Temescal Canyon Trail to the waterfall", "Pacific Palisades", "Until further notice"),
 ("Rogers Road, Bent Arrow, Josepho Spur, Rustic Canyon and Temescal Canyon trails", "Topanga State Park", "Closed since June 12, 2026"),
 ("West Inspiration Loop and Lower Betty Rogers Trail", "Will Rogers State Historic Park", "Closed, no date given"),
]


def build_hikes():
    url = f"{SITE}/guides/fall-hikes-los-angeles/"
    title = "Fall Hikes in Los Angeles: What's Open and What's Closed"
    desc = ("Fall hikes in Los Angeles that are open right now, the popular trails still closed after "
            "the fires, and how red flag closures work. Checked against official park notices.")
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("Fall hikes", url),
             {"@type": "ItemList", "name": "Fall hikes in Los Angeles that are open", "url": url,
              "numberOfItems": len(HIKES), "itemListOrder": "https://schema.org/ItemListUnordered",
              "itemListElement": [{"@type": "ListItem", "position": i,
                                   "item": {"@type": "Park", "name": h[1], "url": h[4]}}
                                  for i, h in enumerate(HIKES, 1)]}]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; fall", "Fall hikes in LA, <em>and which are closed</em>",
               "Five that are open, the trails still closed, and the one rule that shuts the whole range.")
    b += facts([("Open and checked", "5 places"), ("Still closed", "Eaton Canyon to 2027"),
                ("Biggest fall risk", "Red flag days"), ("Checked", CHECKED_HIKES)])
    b += jump([("Red flag days", "redflag", "clock"), ("Open", "open", "park"),
               ("Closed", "closed", "map"), ("This week", "this-week", "ticket")])
    b += intro(["Fall is the best hiking weather in Los Angeles and also the season the mountains close. Santa Ana winds bring red flag days, and since the fires a long list of the famous trails has stayed shut.",
                "A list written before the fires can send you to a trail that is shut. This page names what is open, what is not, and where to check on the morning."])
    b += sec("The rule that closes everything", "On a red flag day, the Santa Monica Mountains close.",
             ["When the National Weather Service issues a Red Flag Warning for the Los Angeles and Oxnard area, the state parks, the National Park Service, the Santa Monica Mountains Conservancy and the MRCA close their trails, backcountry and parking lots. It applies to the whole day, and decisions usually come the day before.",
              "Beaches are generally not closed. Not every closed area is signed or gated, so check the managing agency's site or the NWS fire weather forecast before you drive out. "
              + a("https://home.nps.gov/samo/learn/management/park-closures-during-red-flag-warnings.htm", "The agencies' closure page is here") + ".",
              "The other fall catch is daylight. After the clocks change in early November the sun sets around five, and the Point Mugu beach and canyon lots close at sunset. Start by two."],
             "redflag")
    b += sec("Open, and worth it", "Five that are open as of the check date.",
             ["Griffith Park is the easy answer, with trailheads you can reach without a long drive. Temescal Gateway is back after nearly a year and a half. Solstice Canyon and Point Mugu are the two to drive for."],
             "open")
    b += placelist([place(n, d, c, u, t) for (g, n, d, c, u, t) in HIKES])
    b += sec("Closed, so do not go", "Still shut, from the official notices.",
             ["These are the trails that most lists still send people to. LA County, the Forest Service and State Parks have each posted closures, and the Eaton fire closures now run through the end of 2027. "
              + a("https://trails.lacounty.gov/Alert/4270/eaton-fire-closures-and-palisades-fire-closures", "The county's full list is here") + "."],
             "closed")
    b += table(["Trail", "Where", "Closed until"], [[n, w_, u] for (n, w_, u) in CLOSED])
    b += oneline("If you only do one thing",
        "Start at the Observatory. It is free, the trailheads are on its grounds, and nothing in it is on the county's closure list. Go on a weekday afternoon, because the Observatory is closed Mondays.")
    b += sec("What we could not verify", "Left off on purpose.",
             ["Runyon Canyon and Escondido Falls are two of the most popular hikes in the city, but we could not confirm their current status from an official page, so they are not on the list. Check the city or the managing agency before you go.",
              "Trail conditions change by the week. If you find one that is open or closed and we have it wrong, <a href=\"/about#tip\">tell us</a>."])
    b += live_block("tags:outdoors", "", 4, "Outdoors this week",
        "Refreshed every day from the same list that runs on the homepage.", "Outdoors this week", cat="park")
    b += morelinks([("Best museums →", "/guides/best-museums-los-angeles/"),
                    ("Free things this weekend →", "/guides/free-things-to-do-in-la-this-weekend/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w("guides/fall-hikes-los-angeles/index.html", b)


# ============================== REGISTRATION ==============================
NEW_GUIDES = [
 ("/guides/best-museums-los-angeles/", "museum", "Citywide · checked on each museum's site", "Best Museums in Los Angeles",
  "Eleven worth the drive, sorted by mood, with what is free, which day each is closed and what it costs.",
  "monthly", "0.8"),
 ("/guides/fall-hikes-los-angeles/", "park", "Citywide · checked against park notices", "Fall Hikes in Los Angeles",
  "What is open, what is still closed after the fires, and how red flag closures work.",
  "weekly", "0.8"),
]


def _read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


def _write(p, s):
    open(os.path.join(ROOT, p), "w", encoding="utf-8").write(s)


def register():
    idx, sm, lms = _read("guides/index.html"), _read("sitemap.xml"), _read("llms.txt")
    for href, cat, meta, h2, d, freq, prio in reversed(NEW_GUIDES):      # reversed: first listed ends up first
        full = SITE + href
        if f'href="{href}"' not in idx:
            card = (f'  <a class="gcard cat-{cat}" href="{href}">\n'
                    f'    <div class="gtop"><span class="chip-i">{icon(ICON_FOR[cat])}</span><span class="kick">{meta}</span></div>\n'
                    f'    <h2>{h2}</h2>\n    <p>{d}</p>\n'
                    f'    <span class="rd">Read the guide {icon("go", "")}</span>\n  </a>\n')
            m = re.search(r'<div class="glist">\n', idx)
            idx = idx[:m.end()] + card + idx[m.end():]
        if full not in sm:
            sm = sm.replace("</urlset>", f"  <url><loc>{full}</loc><lastmod>{TODAY}</lastmod>"
                            f"<changefreq>{freq}</changefreq><priority>{prio}</priority></url>\n</urlset>")
        if full not in lms:
            line = f"- [{h2}]({full}): {d}\n"
            gm = re.search(r"^## Guides\n(?:.*\n)*?(?=\n## |\Z)", lms, re.M)
            lms = lms[:gm.end()].rstrip("\n") + "\n" + line + lms[gm.end():] if gm else lms + line
    # renumber the guide index's ItemList JSON-LD from the cards actually on the page
    cards = re.findall(r'<a class="gcard[^"]*" href="(/guides/[^"]+)">.*?<h2>(.*?)</h2>', idx, re.S)
    items = [{"@type": "ListItem", "position": i, "url": SITE + h, "name": re.sub(r"&amp;", "&", t)}
             for i, (h, t) in enumerate(cards, 1)]
    def fix(m):
        return m.group(1) + json.dumps({"@type": "ItemList", "itemListElement": items}, ensure_ascii=False) + m.group(3)
    idx = re.sub(r'(<script type="application/ld\+json">)(.*?"@graph": \[)', lambda m: m.group(0), idx, count=1)
    blob = re.search(r'<script type="application/ld\+json">(\{.*?\})</script>', idx, re.S)
    if blob:
        j = json.loads(blob.group(1))
        for n in j.get("@graph", []):
            if n.get("@type") == "ItemList":
                n["itemListElement"] = items
        idx = idx.replace(blob.group(1), json.dumps(j, ensure_ascii=False))
    _write("guides/index.html", idx)
    _write("sitemap.xml", sm)
    _write("llms.txt", lms)


def crosslink():
    """One-line 'Best museums' / 'Fall hikes' links on sibling guides (idempotent)."""
    adds = {"guides/free-museum-days-los-angeles/index.html": [("Best museums →", "/guides/best-museums-los-angeles/")],
            "guides/la-for-skeptics/index.html": [("Best museums →", "/guides/best-museums-los-angeles/"),
                                                  ("Fall hikes →", "/guides/fall-hikes-los-angeles/")],
            "guides/free-things-to-do-in-la-this-weekend/index.html": [("Fall hikes →", "/guides/fall-hikes-los-angeles/")]}
    for path, links in adds.items():
        if not os.path.exists(os.path.join(ROOT, path)):
            continue
        s = _read(path)
        add = "".join(f'  <a href="{h}">{t}</a>\n' for t, h in links if f'href="{h}"' not in s)
        if add:
            s = re.sub(r'(<div class="morelinks">\n(?:  <a [^\n]*\n)+)', lambda m: m.group(1) + add, s, count=1)
            _write(path, s)


if __name__ == "__main__":
    build_museums()
    build_hikes()
    register()
    crosslink()
    print("built guides/best-museums-los-angeles and guides/fall-hikes-los-angeles; registered in index, sitemap, llms.txt")
