#!/usr/bin/env python3
"""
build_guides_season.py — evergreen holiday + dating guides added 2026-11-23.

    python3 scripts/build_guides_season.py   # writes the pages and registers them
    python3 scripts/sweep.py                 # fills the live event blocks, FAQ, feeds, checks

  /guides/christmas-lights-los-angeles/        light displays, free streets, the boat parade
  /guides/holiday-things-to-do-los-angeles/    rinks, Nutcrackers, sing-alongs, markets
  /guides/new-years-eve-los-angeles/           NYE and New Year's Day
  /guides/date-ideas-los-angeles/              date ideas by kind of date
  /guides/meet-people-los-angeles/             how to meet people without an app

URLs carry no year on purpose: each one is a page that gets re-checked every season and keeps
its search history. The season's dates live in the data lists below, next to the official page
each was read on. Anything that could not be confirmed is under "What we could not verify".

RE-CHECK every season (October for the holiday pages, monthly for the dating pages) and bump
the CHECKED_* dates. Separate file from build_guides.py on purpose (see build_guides_best.py).
FAQ blocks for these pages live in add_guide_faq.py, like the other guides.
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
PUB = "2026-11-23"
SEASON = "2026"                    # the holiday season the dates below belong to
CHECKED_HOLIDAY = "23 November 2026"
CHECKED_DATING = "23 November 2026"
TODAY = datetime.date.today().isoformat()


def a(href, text):
    return f'<a href="{href}" target="_blank" rel="noopener">{text}</a>'


def event_node(name, url, start, end, place_name, locality, free=False, desc=None):
    """schema.org Event for a dated, verified occurrence."""
    n = {"@type": "Event", "name": name, "url": url, "startDate": start, "endDate": end,
         "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
         "eventStatus": "https://schema.org/EventScheduled",
         "location": {"@type": "Place", "name": place_name,
                      "address": {"@type": "PostalAddress", "addressLocality": locality,
                                  "addressRegion": "CA", "addressCountry": "US"}}}
    if free:
        n["isAccessibleForFree"] = True
    if desc:
        n["description"] = desc
    return n


# ============================== CHRISTMAS LIGHTS ==============================
# (group, name, detail, cat, url, tags, schema: (start, end, place, locality, free) or None)
LIGHTS = [
 ("ticketed", "Enchanted: Forest of Light, Descanso Gardens",
  "La Cañada Flintridge · Nov 22, 2026 to Jan 9, 2027 · 5:30–10pm · closed Thanksgiving and Christmas Day · "
  "$29–$52 non-members, timed entry, buy ahead · about a mile on foot · rain or shine · free parking.",
  "park", "https://www.descansogardens.org/events-and-activities/enchanted/", [("Best walk", "cat")],
  ("2026-11-22", "2027-01-09", "Descanso Gardens", "La Cañada Flintridge", False)),
 ("ticketed", "L.A. Zoo Lights, Griffith Park",
  "Select nights Nov 20, 2026 to Jan 10, 2027 · dark Nov 26 and 30, Dec 1, 7, 14–16, 24, 25 and 31, and Jan 4–7 · "
  "tickets from $19 · free parking · Pride Night Dec 17, sensory-inclusive night Dec 8.",
  "park", "https://lazoo.org/plan-your-visit/special-experiences/zoolights", [("From $19", "cat")],
  ("2026-11-20", "2027-01-10", "Los Angeles Zoo", "Los Angeles", False)),
 ("ticketed", "Holiday Lights Train Ride, Griffith Park",
  "Los Feliz side of the park · late November through Jan 3, 2027, weather permitting · Mon–Thu 5–8pm, Fri–Sun 5–9pm · "
  "from $10 a person · dark Thanksgiving and Dec 24, 25 and 31 · weekends sell out.",
  "park", "https://griffithparktrainrides.com/holiday-lights-train-ride/", [("From $10", "cat")], None),
 ("ticketed", "Tinker Bell's Neverland, South Coast Botanic Garden",
  "Palos Verdes · Nov 13, 2026 to Jan 3, 2027 · 5:30–8:30pm · closed Thanksgiving and Christmas Day · "
  "timed tickets through Fever · this year's show replaces Astra Lumina.",
  "park", "https://tinkerbellsneverland.com/los-angeles/", [("New this year", "cat")],
  ("2026-11-13", "2027-01-03", "South Coast Botanic Garden", "Palos Verdes Peninsula", False)),
 ("free", "Christmas Tree Lane, Altadena",
  "Santa Rosa Ave at Mariposa St · more than a hundred years of lit deodar cedars, back since the Eaton fire · "
  "lighting ceremony Sat Dec 5, 2026 at 6pm, Winterfest craft fair 3–9pm the same day · free.",
  "walk", "https://christmastreelane.net/events", [("Free", "free")],
  ("2026-12-05T18:00", "2026-12-05T21:00", "Christmas Tree Lane", "Altadena", True)),
 ("free", "Candy Cane Lane, Woodland Hills",
  "Lubao Ave at Oxnard St, near Pierce College · about eight blocks, lit since 1952 · "
  "first Saturday in December to the first Saturday after New Year's · lights 6–10pm · free · park and walk.",
  "walk", "https://woodlandhillscc.net/community/candy-cane-lane.html", [("Free", "free")], None),
 ("free", "Marina del Rey Holiday Boat Parade",
  "Sat Dec 12, 2026 · Burton Chace Park activities from 4pm, light show 5:45pm, parade 6–8pm · "
  "watch from the Main Channel between Basins B and H · free · county lots $5–$15.",
  "beach", "https://beaches.lacounty.gov/holidayboatparade/", [("Free", "free"), ("Westside", "cat")],
  ("2026-12-12T16:00", "2026-12-12T20:00", "Burton Chace Park", "Marina del Rey", True)),
 ("free", "The Grove and The Americana at Brand",
  "Free to wander · The Grove's nightly snowfall runs through Dec 31 at 6pm and 8pm · "
  "the Americana's tree is up Nov 2 to Dec 25, 2026.",
  "shop", "https://thegrovela.com/", [("Free", "free")], None),
]


def build_lights():
    slug = "christmas-lights-los-angeles"
    url = f"{SITE}/guides/{slug}/"
    title = f"Christmas Lights in Los Angeles {SEASON}: Dates, Prices, Free Streets"
    desc = ("Christmas lights in Los Angeles this season: Descanso, Zoo Lights, the Griffith Park train, "
            "free streets in Altadena and Woodland Hills, with dates checked.")
    events = [event_node(n, u, s[0], s[1], s[2], s[3], s[4]) for (g, n, d, c, u, t, s) in LIGHTS if s]
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("Christmas lights", url),
             {"@type": "ItemList", "name": "Christmas lights in Los Angeles", "url": url,
              "numberOfItems": len(LIGHTS), "itemListOrder": "https://schema.org/ItemListUnordered",
              "itemListElement": [{"@type": "ListItem", "position": i, "name": l[1], "url": l[4]}
                                  for i, l in enumerate(LIGHTS, 1)]}] + events
    rows = lambda g: [place(n, d, c, u, t) for (gg, n, d, c, u, t, s) in LIGHTS if gg == g]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; December", "Christmas lights in LA, <em>and which are free</em>",
               "Four worth a ticket, four that cost nothing, and the two that are off this year.")
    b += facts([("Best walk-through", "Descanso Gardens"), ("Best free street", "Christmas Tree Lane"),
                ("On the water", "Sat Dec 12"), ("Checked", CHECKED_HOLIDAY)])
    b += jump([("Worth a ticket", "ticketed", "park"), ("Free", "free", "walk"),
               ("Off this year", "off", "clock"), ("At a glance", "glance", "map"),
               ("This week", "this-week", "ticket")])
    b += intro(["Every December the same question goes around: where are the good lights. The honest answer is that LA does two kinds. There are the ticketed walks through gardens and the zoo, which are well made and sell out on weekends, and there are the streets where neighbours have been stringing lights for decades and nobody charges a thing.",
                "Every date and price here was read on the organiser's own page this season. This is an El Niño winter and two big displays have already called it off for weather, so check the page on the day if it has been raining."])
    b += sec("Worth a ticket", "Four that justify the drive and the timed entry.",
             ["<b>Descanso Gardens</b> is the one to book if you only book one. The route is about a mile under the oaks and it is the most grown-up of the four. Pick a weeknight entry and the price drops toward the bottom of the range.",
              "<b>Zoo Lights</b> is the cheapest ticketed option and parking is free, but it is dark on more nights than people expect, including Christmas Eve and New Year's Eve. The <b>Griffith Park train</b> is a fifteen-minute loop for ten dollars, which is exactly what it should be. <b>Tinker Bell's Neverland</b> in Palos Verdes is new this year and runs on timed tickets with a fifteen-minute grace period."],
             "ticketed")
    b += placelist(rows("ticketed"))
    b += sec("Free", "The streets, the harbor and the snow.",
             ["<b>Christmas Tree Lane</b> in Altadena lost none of its cedars in the Eaton fire and the lighting on Saturday, December 5 is the best free evening of the season. Go for the craft fair in the afternoon and stay for the lights at six.",
              "<b>Candy Cane Lane</b> asks you to dim your headlights and drive slowly, and on a weekend you are better off parking a few blocks out and walking. The <b>Marina del Rey boat parade</b> is the Westside's one: decorated boats down the Main Channel, and Burton Chace Park fills early. The Grove's fake snow is free and it is what it is."],
             "free")
    b += placelist(rows("free"))
    b += sec("Off this year", "Two that most lists still send you to.",
             [f"<b>Holiday Road</b> at King Gillette Ranch in Calabasas is taking {SEASON} off for projected El Niño weather and says it plans to return in 2027. The <b>Naples Island boat parade</b> in Long Beach was cancelled for high tides, and so was its house-decorating contest. "
              + a("https://holidayroadusa.com/", "Holiday Road's notice is here") + "."],
             "off")
    b += sec("At a glance", "Dates and cost, side by side.", [], "glance")
    b += table(["Display", "Runs", "Cost"], [
        ["Descanso Gardens", "Nov 22 – Jan 9", "$29–$52, timed"],
        ["L.A. Zoo Lights", "Nov 20 – Jan 10, select nights", "From $19"],
        ["Griffith Park train", "Late Nov – Jan 3", "From $10"],
        ["Tinker Bell's Neverland", "Nov 13 – Jan 3", "Timed, via Fever"],
        ["Christmas Tree Lane", "Lighting Sat Dec 5, 6pm", "Free"],
        ["Candy Cane Lane", "First Sat of Dec – first Sat after New Year's", "Free"],
        ["Marina del Rey boat parade", "Sat Dec 12, 6–8pm", "Free, parking $5–$15"]])
    b += oneline("If you only do one thing",
        "Descanso on a weeknight, at the first entry time, then dinner in Montrose or Pasadena on the way home. Book the ticket this week; December weekends go first.")
    b += sec("What we could not verify", "Left off on purpose.",
             ["The old Griffith Park drive-through festival, Moonlight Forest at the Arboretum and the Rose Bowl drive-through have no listing for this season. Nightly hours and an end date for Christmas Tree Lane are not on its site, and the Griffith Park train's own page gives two different start dates, so we have printed the safer one.",
              "If you know a street that should be here, <a href=\"/about#tip\">tell us</a> and we will go look."])
    b += live_block("tags:outdoors", "", 4, "Out this week",
        "Refreshed every day from the same list that runs on the homepage.", "Out this week", cat="park")
    b += morelinks([("Holiday things to do →", "/guides/holiday-things-to-do-los-angeles/"),
                    ("New Year's Eve →", "/guides/new-years-eve-los-angeles/"),
                    ("Date ideas →", "/guides/date-ideas-los-angeles/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w(f"guides/{slug}/index.html", b)


# ============================== HOLIDAY THINGS TO DO ==============================
HOLIDAY = [
 ("skate", "Holiday Ice Rink, Pershing Square",
  "532 S Olive St, Downtown · daily Nov 12, 2026 to Jan 3, 2027 · weekdays 3–10pm, weekends noon–10pm, "
  "noon–10pm every day Dec 21 to Jan 3 · $23.32 with skates · 60-minute sessions.",
  "ticket", "https://holidayicerinkdowntownla.com/ice-skating-downtown-la/", [("Downtown", "cat")],
  ("2026-11-12", "2027-01-03", "Pershing Square", "Los Angeles", False)),
 ("skate", "Frost on 5th, Santa Monica",
  "1324 5th St at Arizona Ave · the old Ice at Santa Monica under a new name · weekdays 3–10pm, weekends and holidays noon–10pm · "
  "$22 with skates.",
  "ticket", "https://frostonfifth.com/", [("Westside", "cat")], None),
 ("stage", "The Nutcracker, Los Angeles Ballet",
  "Royce Hall at UCLA Dec 11–13, then the Dolby Theatre in Hollywood Dec 18–27 with a live orchestra · "
  "2pm matinee on Christmas Eve · sensory-friendly show Sat Dec 26 at 2pm.",
  "music", "https://www.losangelesballet.org/2026-2027-season/the-nutcracker", [("Live orchestra", "cat")],
  ("2026-12-11", "2026-12-27", "Dolby Theatre", "Hollywood", False)),
 ("stage", "The Nutcracker Suite, American Contemporary Ballet",
  "Downtown · Nov 28 to Dec 24, 2026 · small, close-up staging that the company says sells out fast.",
  "music", "https://www.acbdances.com/calendar", [("Small room", "cat")],
  ("2026-11-28", "2026-12-24", "American Contemporary Ballet", "Los Angeles", False)),
 ("stage", "A Christmas Carol, A Noise Within",
  "3352 E Foothill Blvd, Pasadena · Nov 28 to Dec 24, 2026 · Thu–Fri 7pm, Sat 2pm and 7pm, Sun 2pm · "
  "pay what you choose ($10–$40) Thu Dec 3 at 7pm · closes Christmas Eve at 2pm.",
  "art", "https://www.anoisewithin.org/play/a-christmas-carol-5/", [("Pasadena", "cat")],
  ("2026-11-28", "2026-12-24", "A Noise Within", "Pasadena", False)),
 ("sing", "Holiday Sing-Along, LA Phil",
  "Walt Disney Concert Hall · Sat Dec 19, 2026 at 11:30am and 2:30pm · tickets from $39.",
  "music", "https://www.laphil.com/events/holiday-sing-along-2026", [("From $39", "cat")],
  ("2026-12-19T11:30", "2026-12-19T13:00", "Walt Disney Concert Hall", "Los Angeles", False)),
 ("sing", "The Great Messiah Sing-Along, LA Master Chorale",
  "Walt Disney Concert Hall · Sun Dec 20, 2026 at 7pm · two thousand voices, yours included · box office 213-972-7282.",
  "music", "https://lamasterchorale.org/show-details/the-great-messiah-sing-along-two-thousand-voices-at-walt-disney-concert-hall",
  [("Bring your voice", "cat")],
  ("2026-12-20T19:00", "2026-12-20T21:30", "Walt Disney Concert Hall", "Los Angeles", False)),
 ("sing", "A Very Dolly Holiday, Gay Men's Chorus of Los Angeles",
  "Saban Theatre, 8440 Wilshire Blvd · Sat Dec 12, 2026 at 7pm and Sun Dec 13 at 3:30pm.",
  "music", "https://gmcla.org/season", [("Two shows", "cat")],
  ("2026-12-12T19:00", "2026-12-13T17:30", "Saban Theatre", "Beverly Hills", False)),
 ("free", "L.A. County Holiday Celebration, Music Center",
  "Dorothy Chandler Pavilion · now Sun Dec 20, 2026, not Christmas Eve · shows at 11am and 3pm · free · "
  "reservations open at 10am Dec 8, 9 and 10, up to four each · free parking in the Music Center garages.",
  "music", "https://www.pbssocal.org/press-room/the-67th-annual-l-a-county-holiday-celebration-returns-to-the-music-centers-dorothy-chandler-pavilion-on-a-new-date-and-time-plus-a-christmas-eve-broadcast-on-pbs-socal",
  [("Free", "free")],
  ("2026-12-20T11:00", "2026-12-20T16:30", "Dorothy Chandler Pavilion", "Los Angeles", True)),
 ("free", "Marina del Rey Holiday Boat Parade",
  "Burton Chace Park · Sat Dec 12, 2026 · activities from 4pm, light show 5:45pm, parade 6–8pm · free to watch.",
  "beach", "https://beaches.lacounty.gov/holidayboatparade/", [("Free", "free")], None),
 ("free", "Unique Markets, the last holiday market",
  "Cooper Design Space penthouse, 860 S Los Angeles St · Sat–Sun Dec 12–13, 2026, 10am–4pm · "
  "$15 a day, $20 the weekend · billed as the final one after nineteen years.",
  "shop", "https://www.uniquemarkets.com/thegrandfinale", [("Last one", "cat")],
  ("2026-12-12T10:00", "2026-12-13T16:00", "Cooper Design Space", "Los Angeles", False)),
]


def build_holiday():
    slug = "holiday-things-to-do-los-angeles"
    url = f"{SITE}/guides/{slug}/"
    title = f"Holiday Things to Do in Los Angeles {SEASON}: Skating, Nutcracker"
    desc = ("Holiday things to do in LA: outdoor ice rinks, the Nutcracker, sing-alongs at Disney Hall "
            "and the free Music Center celebration, with this year's dates.")
    events = [event_node(n, u, s[0], s[1], s[2], s[3], s[4]) for (g, n, d, c, u, t, s) in HOLIDAY if s]
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("Holiday things to do", url),
             {"@type": "ItemList", "name": "Holiday things to do in Los Angeles", "url": url,
              "numberOfItems": len(HOLIDAY), "itemListOrder": "https://schema.org/ItemListUnordered",
              "itemListElement": [{"@type": "ListItem", "position": i, "name": h[1], "url": h[4]}
                                  for i, h in enumerate(HOLIDAY, 1)]}] + events
    rows = lambda g: [place(n, d, c, u, t) for (gg, n, d, c, u, t, s) in HOLIDAY if gg == g]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; the holidays", "The holidays in LA, <em>done properly</em>",
               "Two outdoor rinks, two Nutcrackers, a room of two thousand people singing Handel, and the free show that moved.")
    b += facts([("Outdoor ice", "Pershing Sq, Santa Monica"), ("Free and big", "Sun Dec 20"),
                ("Christmas Eve", "Matinees until 2pm"), ("Checked", CHECKED_HOLIDAY)])
    b += jump([("Ice skating", "skate", "ticket"), ("On stage", "stage", "music"),
               ("Sing along", "sing", "music"), ("Free", "free", "walk"),
               ("Christmas week", "week", "clock"), ("This week", "this-week", "ticket")])
    b += intro(["December in Los Angeles is not short of things to do. It is short of the right ones, because the city's holiday calendar is mostly shopping centres with a tree. This is the other list: the rooms where a few hundred people turn up to do the same seasonal thing together, which is most of the point of the season.",
                "Dates and prices were read on each organiser's own page. Christmas lights have their own guide, and so does New Year's Eve."])
    b += sec("Ice skating", "Two outdoor rinks this year.",
             ["Downtown's rink in <b>Pershing Square</b> is the classic: skyline on every side, an hour on the ice, and on weeknights it opens at three. On the Westside, the Santa Monica rink is back as <b>Frost on 5th</b>, a block from the Wednesday farmers market. Burbank and Glendale have not brought theirs back."],
             "skate")
    b += placelist(rows("skate"))
    b += sec("On stage", "The Nutcracker twice, and Dickens in Pasadena.",
             ["<b>Los Angeles Ballet</b> does the full production with a live orchestra, first at Royce Hall and then a longer run at the Dolby. <b>American Contemporary Ballet</b> does the opposite: a small room downtown where you sit close enough to hear the shoes. <b>A Noise Within</b> has made its Christmas Carol a Pasadena habit, and one Thursday is pay what you choose."],
             "stage")
    b += placelist(rows("stage"))
    b += sec("Sing along", "The best kind of audience participation.",
             ["The <b>Messiah Sing-Along</b> is the one people talk about afterwards: the whole of Disney Hall sings the choruses, scores in laps, and nobody minds if you come in late on the Hallelujah. The LA Phil's afternoon sing-along is the lighter version. The <b>Gay Men's Chorus</b> does Dolly Parton this year at the Saban, two shows only."],
             "sing")
    b += placelist(rows("sing"))
    b += sec("Free", "Including the one that changed its date.",
             ["The <b>L.A. County Holiday Celebration</b> has been a Christmas Eve fixture for decades. This year it is on Sunday, December 20, for the first time, with two shows. It is free, and the reservations that guarantee a seat are released at 10am on December 8, 9 and 10. It still airs on PBS SoCal on Christmas Eve at 3pm.",
              "The <b>Unique Markets</b> holiday market is calling this one its last, after nineteen years. It is the place to buy a present from the person who made it."],
             "free")
    b += placelist(rows("free"))
    b += sec("Christmas week", "What is still on, Dec 21 to 27.",
             ["The Pershing Square rink runs noon to 10pm every day from December 21 through January 3. On Thursday, December 24, LA Ballet has a 2pm matinee at the Dolby and A Noise Within closes its Christmas Carol at 2pm. LA Ballet picks up again on Saturday the 26th.",
              "On Christmas Day itself, check before you go: most venues on this page have not published Christmas Day hours."],
             "week")
    b += oneline("If you only do one thing",
        "Reserve the free Music Center show at 10am on December 8, then skate Pershing Square afterwards. It is a five-minute walk and the whole afternoon costs the price of the rink.")
    b += sec("What we could not verify", "Left off on purpose.",
             ["Las Posadas on Olvera Street, the Kwanzaa parade in Leimert Park and the public menorah lightings usually happen, but none had a listing for this season on an official page when we checked. The Naples boat parade in Long Beach is cancelled. Debbie Allen's Hot Chocolate Nutcracker lists December dates with no year, and Christmas Carol Goes Wrong at the Ahmanson sat behind a queue page, so both are out until we can read them.",
              "If you run one of these, <a href=\"/about#tip\">send us the page</a> and it goes in."])
    b += live_block("tags:culture", "", 4, "On this week",
        "Refreshed every day from the same list that runs on the homepage.", "On this week", cat="ticket")
    b += morelinks([("Christmas lights →", "/guides/christmas-lights-los-angeles/"),
                    ("New Year's Eve →", "/guides/new-years-eve-los-angeles/"),
                    ("Meet people →", "/guides/meet-people-los-angeles/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w(f"guides/{slug}/index.html", b)


# ============================== NEW YEAR'S EVE ==============================
NYE = [
 ("free", "NYELA, Gloria Molina Grand Park",
  "200 N Grand Ave, Downtown · Thu Dec 31, 2026, 8pm–1am · free, no ticket, and anyone selling one is not the park · "
  "$10 flat parking at the Music Center and Disney Hall garages · Civic Center/Grand Park station on the B and D lines.",
  "music", "https://grandparkla.org/nyela/", [("Free", "free"), ("Downtown", "cat")],
  ("2026-12-31T20:00", "2027-01-01T01:00", "Gloria Molina Grand Park", "Los Angeles", True)),
 ("free", "Fireworks and Glow Party, Marina del Rey",
  "Burton Chace Park, 13650 Mindanao Way · Dec 31, glow party 7pm to midnight · fireworks from the south jetty at 11:59pm, "
  "about ten minutes, visible across the marina · free with an RSVP · marina lots $11–$20, the park's own lot is closed.",
  "beach", "https://beaches.lacounty.gov/nye/", [("Free", "free"), ("Westside", "cat")],
  ("2026-12-31T19:00", "2027-01-01T00:15", "Burton Chace Park", "Marina del Rey", True)),
 ("ticket", "A Yacht Rock NYE with Christopher Cross, LA Phil",
  "Walt Disney Concert Hall · Thu Dec 31, 2026 from 7pm, with the Pacific Jazz Orchestra · BP Hall opens at 5:30pm · "
  "champagne for the first 350 in · tickets from $101.",
  "music", "https://www.laphil.com/events/a-yacht-rock-nye-with-christopher-cross", [("From $101", "cat")],
  ("2026-12-31T19:00", "2026-12-31T22:30", "Walt Disney Concert Hall", "Los Angeles", False)),
 ("ticket", "New Year's Eve dinner cruise, Marina del Rey",
  "City Cruises from Fisherman's Village, 13755 Fiji Way · board 8:30pm, sail 9pm–12:30am · buffet, DJ, a toast and the "
  "marina fireworks from the deck · cocktail attire · from $343.97 with fees.",
  "beach", "https://citycruises.com/tickets/marina-del-rey/marina-del-rey-new-years-eve-premier-dinner-cruise",
  [("On the water", "cat")], None),
 ("ticket", "Glitz & Glamour Masquerade, The Queen Mary",
  "1126 Queens Hwy, Long Beach · Dec 31 · general admission $175 in advance, $195 on the day, VIP $295 · "
  "fifteen minutes of midnight fireworks over Long Beach Harbor.",
  "ticket", "https://www.queenmary.com/new-years-eve-celebrations.htm", [("Long Beach", "cat")], None),
 ("day", "Rose Parade, Pasadena",
  "Fri Jan 1, 2027, 8am to about 10am · 5.5 miles, most of it on Colorado Blvd · free from the curb · "
  "overnight street parking opens at noon Dec 31 and the route closes at 10pm · grandstand seats sold separately.",
  "walk", "https://tournamentofroses.com/rose-parade/", [("Free", "free")],
  ("2027-01-01T08:00", "2027-01-01T10:00", "Colorado Boulevard", "Pasadena", True)),
 ("day", "Rose Bowl Game, Pasadena",
  "Fri Jan 1, 2027 · a College Football Playoff quarterfinal this year · teams and kickoff are set on Selection Day in early December.",
  "ticket", "https://rosebowlgame.com/news/2026/2/3/general-cfp-announces-2026-and-2027-playoff-sites-rose-bowl-game-to-be-quarterfinal.aspx",
  [("Quarterfinal", "cat")], None),
 ("day", "First Day Hikes, California State Parks",
  "Fri Jan 1, 2027 · free guided hikes across the state parks, park day-use or parking fees may apply · the parks taking part are on the state's map.",
  "park", "https://www.parks.ca.gov/?page_id=30737", [("Free", "free")], None),
 ("day", "New Year's Day brunch cruise, Marina del Rey",
  "City Cruises · board 10:30am, sail 11am–1pm · brunch buffet and mimosas · from $134.94.",
  "beach", "https://citycruises.com/tickets/marina-del-rey/marina-del-rey-new-years-day-premier-brunch-cruise",
  [("Slow start", "cat")], None),
]


def build_nye():
    slug = "new-years-eve-los-angeles"
    url = f"{SITE}/guides/{slug}/"
    title = f"New Year's Eve in Los Angeles {SEASON}: Free Parties and Fireworks"
    desc = ("New Year's Eve in Los Angeles: free NYELA at Grand Park, Marina del Rey fireworks, a Disney Hall "
            "concert, and the Rose Parade on New Year's Day.")
    events = [event_node(n, u, s[0], s[1], s[2], s[3], s[4]) for (g, n, d, c, u, t, s) in NYE if s]
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("New Year's Eve", url),
             {"@type": "ItemList", "name": "New Year's Eve in Los Angeles", "url": url,
              "numberOfItems": len(NYE), "itemListOrder": "https://schema.org/ItemListUnordered",
              "itemListElement": [{"@type": "ListItem", "position": i, "name": e[1], "url": e[4]}
                                  for i, e in enumerate(NYE, 1)]}] + events
    rows = lambda g: [place(n, d, c, u, t) for (gg, n, d, c, u, t, s) in NYE if gg == g]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; Dec 31", "New Year's Eve in LA, <em>without the cover charge</em>",
               "Two free countdowns, one good concert, a boat if you want one, and a parade in the morning.")
    b += facts([("Free countdown", "Grand Park, 8pm–1am"), ("Fireworks", "Marina del Rey, 11:59pm"),
                ("New Year's Day", "Rose Parade, 8am"), ("Checked", CHECKED_HOLIDAY)])
    b += jump([("Free", "free", "walk"), ("Ticketed", "ticket", "ticket"),
               ("New Year's Day", "day", "clock"), ("Getting home", "home", "map"),
               ("This week", "this-week", "ticket")])
    b += intro(["Most New Year's Eve advice in Los Angeles is a list of bars charging two hundred dollars for an open bar you will not use. The better nights are the ones where a lot of people stand in the same place at midnight, and in this city two of the best of those are free.",
                "Times and prices were read on each organiser's own page. A lot of venues had not posted their New Year's plans when we checked, so this page gets re-checked through December."])
    b += sec("Free", "The two countdowns worth going to.",
             ["<b>NYELA at Grand Park</b> is the city's own party: a free stage downtown, projections on City Hall at midnight, and a crowd that takes the train in. The lineup for this year was not up yet.",
              "On the Westside, <b>Marina del Rey</b> does a free glow party at Burton Chace Park and launches fireworks off the south jetty at 11:59pm. You can see them from most of the marina, so a walk along the water works as well as a spot in the park."],
             "free")
    b += placelist(rows("free"))
    b += sec("Ticketed", "If you want a seat and a toast.",
             ["The LA Phil's <b>Yacht Rock NYE</b> at Disney Hall is the grown-up choice: Christopher Cross, a jazz orchestra, champagne at the door, and you are out in time to make another party. The <b>dinner cruise</b> out of Marina del Rey puts you on the water for the fireworks. The <b>Queen Mary</b> masquerade in Long Beach is the big dress-up one, with its own fireworks over the harbor."],
             "ticket")
    b += placelist(rows("ticket"))
    b += sec("New Year's Day", "Falls on a Friday this time.",
             ["The <b>Rose Parade</b> starts at 8am on Colorado Boulevard, and the people who see it best camped on the curb the night before. If that sounds like a lot, a <b>First Day Hike</b> with a ranger or a <b>brunch cruise</b> are the gentler ways to start the year. The Rose Bowl is a playoff quarterfinal this time, and its kickoff is set in early December."],
             "day")
    b += placelist(rows("day"))
    b += sec("Getting home", "The part that ruins the night if you skip it.",
             ["Grand Park sits on top of four Metro stations, which is the main argument for going. Last year Metro ran free fares and kept several rail lines running all night, but it has not announced this year's plan, so "
              + a("https://www.metro.net/", "check metro.net") + " in the last week of December. In Marina del Rey, Mindanao Way closes westbound from 5pm, so park in a county lot and walk in."],
             "home")
    b += oneline("If you only do one thing",
        "Take the train to Grand Park. It is free, it is the one place in LA where a few thousand strangers count down together, and you do not have to find parking at 1am.")
    b += sec("What we could not verify", "Left off on purpose.",
             ["The Long Beach waterfront party, Pasadena's New Year's Eve events, jazz club and comedy club New Year's shows, the Little Tokyo Oshogatsu festival and the January polar bear swims had no listing for this year on an official page when we checked. Marina del Rey has run an earlier 9pm show in past years; this year's page lists only midnight.",
              "If you are hosting something worth a mention, <a href=\"/about#tip\">send it in</a>."])
    b += live_block("tags:music", "", 4, "On this week",
        "Refreshed every day from the same list that runs on the homepage.", "On this week", cat="music")
    b += morelinks([("Holiday things to do →", "/guides/holiday-things-to-do-los-angeles/"),
                    ("Christmas lights →", "/guides/christmas-lights-los-angeles/"),
                    ("Date ideas →", "/guides/date-ideas-los-angeles/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w(f"guides/{slug}/index.html", b)


# ============================== DATE IDEAS ==============================
# (group, name, detail, cat, url, tags)
DATES = [
 ("first", "Hammer Museum, Westwood",
  "Free, no reservation · Tue–Sun 11am–6pm, closed Mondays · parking $9 for three hours with validation, $9 flat after 5pm on weekdays.",
  "museum", "https://hammer.ucla.edu/visit", [("Free", "free"), ("Westside", "cat")]),
 ("first", "Getty Center, Brentwood",
  "Free with a timed reservation · open until 9pm on Saturdays · closed Mondays · parking $25, cheaper after 3pm and 6pm.",
  "museum", "https://www.getty.edu/visit/center/plan/hours.html", [("Free", "free"), ("Westside", "cat")]),
 ("first", "Melrose Trading Post, Fairfax",
  "Every Sunday 10am–5pm at Fairfax High, 7850 Melrose Ave · enter at Melrose and Genesee · valet with three free hours at 544 N Fairfax.",
  "shop", "https://melrosetradingpost.org", [("Sundays", "cat")]),
 ("first", "Skylight Books, Los Feliz",
  "1818 N Vermont Ave · author talks most weeks at 7pm, RSVP through the store · three and a half blocks from the Sunset/Vermont station.",
  "shop", "https://www.skylightbooks.com/events", [("Books", "cat")]),
 ("first", "Point Dume, Malibu",
  "Free two-hour parking at the top, and very little of it · gray whales December to mid-April · no dogs on the trails or beach.",
  "beach", "https://www.parks.ca.gov/?page_id=623", [("Sunset", "cat")]),
 ("activity", "Intro to Wheel Throwing, Good Dirt LA",
  "4505 S Centinela Ave, Del Rey · a one-time two-hour class, $85 a person, six people max · reschedule up to 72 hours before.",
  "art", "https://www.gooddirtla.com/classes", [("$85", "cat"), ("Westside", "cat")]),
 ("activity", "Moonlight Rollerway, Glendale",
  "5110 San Fernando Rd · evening sessions 8–11pm nightly, Mondays 18 and over · $23 online plus $8 skates.",
  "music", "https://www.moonlightrollerway.com", [("$31 each", "cat")]),
 ("activity", "Highland Park Bowl, Highland Park",
  "5621 N Figueroa St · 21 and over after 8pm · walk-in lanes by the hour, reservations only for two-hour packages.",
  "drink", "https://highlandparkbowl.com", [("Walk-in", "cat")]),
 ("activity", "New Beverly Cinema, Beverly Grove",
  "Film prints only, 35mm and 16mm, usually as a double feature · phones out once and you are out, no refund.",
  "ticket", "https://thenewbev.com/", [("35mm", "cat")]),
 ("activity", "Vidiots, Eagle Rock",
  "4884 Eagle Rock Blvd · repertory screenings, a beer and wine bar, and a video store of 60,000 titles to argue over · limited walk-up tickets 45 minutes before.",
  "ticket", "https://vidiotsfoundation.org", [("Film", "cat")]),
 ("activity", "Sunset trail ride, Sunset Ranch Hollywood",
  "3400 N Beachwood Dr · the Mt Hollywood evening ride is about two hours, no experience needed, book ahead · runs seasonally.",
  "park", "https://www.sunsetranchhollywood.com/evening-tours", [("Book ahead", "cat")]),
 ("big", "Largo at the Coronet, La Cienega",
  "366 N La Cienega Blvd · most shows $40 · doors 7pm, show 8pm, arrive fifteen minutes early · no phones · cash bar.",
  "ticket", "https://largo-la.com/ticket-info/", [("$40", "cat")]),
 ("big", "Catalina Jazz Club, Hollywood",
  "6725 Sunset Blvd · tickets roughly $33–$83 plus an entrée or two-item minimum · doors 7pm, show 8:30pm.",
  "music", "https://www.catalinajazzclub.com", [("Jazz", "cat")]),
 ("big", "Sam First, near LAX",
  "6171 W Century Blvd · doors 6pm, sets around 7:30pm and 9:30pm · the room asks you not to talk through the music.",
  "music", "https://samfirstbar.com/upcoming-shows", [("Jazz", "cat"), ("Westside", "cat")]),
 ("big", "Geffen Playhouse, Westwood",
  "10886 Le Conte Ave · Purpose, directed by Phylicia Rashad, through Dec 20, 2026 · Liberation from Jan 27, 2027.",
  "art", "https://www.geffenplayhouse.org", [("Theater", "cat"), ("Westside", "cat")]),
 ("big", "The Magic Castle, Hollywood",
  "Members' club: you need a member's invitation · invited guests dine there, $50 minimum each · 21 and over at night · strict dress code.",
  "drink", "https://www.magiccastle.com/faqs/", [("By invitation", "cat")]),
 ("free", "Griffith Observatory, Griffith Park",
  "Free · Tue–Fri noon–10pm, Sat–Sun 10am–10pm, closed Mondays · the lawn and the city lights are the point.",
  "park", "https://griffithobservatory.lacity.gov/visit/", [("Free", "free")]),
 ("free", "The Broad, Downtown",
  "Free, timed ticket recommended · open until 8pm Thursdays · closed Mondays · the Infinity Mirror Room is a separate reservation.",
  "museum", "https://www.thebroad.org/visit", [("Free", "free")]),
 ("free", "Walt Disney Concert Hall tour, Downtown",
  "Free self-guided audio tour most days, about an hour, from the Grand Avenue lobby · then the rooftop garden.",
  "music", "https://www.laphil.com/visit/when-youre-here/tours", [("Free", "free")]),
 ("free", "LACMA, Miracle Mile",
  "Free for LA County residents weekdays after 3pm with ID, and for everyone the second Tuesday · open until 8pm Fridays · closed Wednesdays.",
  "museum", "https://www.lacma.org/tickets", [("Free after 3", "free")]),
 ("rain", "Academy Museum of Motion Pictures, Miracle Mile",
  "$25, or $18 after 4:30pm · Wed–Mon 10am–6pm, closed Tuesdays.",
  "art", "https://www.academymuseum.org/en/visit", [("$18 late", "cat")]),
 ("rain", "The Last Bookstore, Downtown",
  "453 S Spring St · open until 11pm Wednesday to Saturday.",
  "shop", "https://www.lastbookstorela.com/downtown-la", [("Late", "cat")]),
]


def build_dates():
    slug = "date-ideas-los-angeles"
    url = f"{SITE}/guides/{slug}/"
    title = "Date Ideas in Los Angeles: First Dates, Free Dates, Big Nights"
    desc = ("Date ideas in Los Angeles sorted by the kind of date: easy first dates, things to do together, "
            "free nights, big nights out and rainy days.")
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("Date ideas", url),
             {"@type": "ItemList", "name": "Date ideas in Los Angeles", "url": url,
              "numberOfItems": len(DATES), "itemListOrder": "https://schema.org/ItemListUnordered",
              "itemListElement": [{"@type": "ListItem", "position": i, "name": d[1], "url": d[4]}
                                  for i, d in enumerate(DATES, 1)]}]
    rows = lambda g: [place(n, d, c, u, t) for (gg, n, d, c, u, t) in DATES if gg == g]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; for two", "Date ideas in LA, <em>sorted by the kind of date</em>",
               "A first date wants an easy exit. A fifth date wants something to do. Here is which is which.")
    b += facts([("Best first date", "The Hammer, free"), ("Best night out", "Largo, $40"),
                ("Best free night", "Griffith Observatory"), ("Checked", CHECKED_DATING)])
    b += jump([("First dates", "first", "coffee"), ("Do something", "activity", "art"),
               ("Big nights", "big", "music"), ("Free", "free", "walk"),
               ("Rainy days", "rain", "clock"), ("This week", "this-week", "ticket")])
    b += intro(["The trouble with most date-idea lists is that they treat every date the same. A first date and an anniversary want opposite things. The first one wants something short, cheap and easy to extend if it is going well. Later ones want a thing to do, because sitting across a table is the least interesting way to learn about a person.",
                "So this is sorted by the kind of date. Everything here was checked on the venue's own site, and the Westside ones are marked."])
    b += sec("First dates", "Short, cheap, and easy to extend.",
             ["The best first date in LA is a free museum on a weekday afternoon. <b>The Hammer</b> is small enough to see in an hour, needs no reservation, and Westwood has a dozen places to keep talking if it is going well. The <b>Getty</b> on a Saturday stays open until nine, so you can catch the sunset from the garden.",
              "On a Sunday, walk <b>Melrose Trading Post</b> together; a flea market gives you something to talk about every thirty seconds. If you are both readers, an evening author talk at <b>Skylight Books</b> answers the question of what to talk about over the drink afterwards."],
             "first")
    b += placelist(rows("first"))
    b += sec("Do something", "For the second date onwards.",
             ["A pottery wheel is the best date activity in the city because both of you will be bad at it. <b>Good Dirt</b> in Del Rey runs two-hour intro classes for six people. <b>Moonlight Rollerway</b> in Glendale still has an organ and a disco ball, and <b>Highland Park Bowl</b> is a 1927 bowling alley with walk-in lanes.",
              "For film, the <b>New Beverly</b> shows only prints, often as a double feature, and <b>Vidiots</b> in Eagle Rock has a bar and a video store you can browse while you wait. The <b>Sunset Ranch</b> evening ride up Mount Hollywood is the one to book for a birthday."],
             "activity")
    b += placelist(rows("activity"))
    b += sec("Big nights", "Book these.",
             ["<b>Largo</b> is the best comedy room in the city: forty dollars, no phones, and you never quite know who will turn up. For music, <b>Sam First</b> near LAX is a small jazz room where people actually listen, and <b>Catalina</b> on Sunset is the dinner-and-a-set version. The <b>Geffen</b> in Westwood is the theater night, and the <b>Magic Castle</b> is the one to save for when a member owes you a favour."],
             "big")
    b += placelist(rows("big"))
    b += sec("Free", "The good ones cost nothing.",
             ["<b>Griffith Observatory</b> after dark is free, open until ten, and the lawn looks straight down at the city. Downtown, take the free audio tour of <b>Disney Hall</b> and walk up to the rooftop garden, then cross the street to <b>The Broad</b>, which is free too. On the Westside, the Venice canals at dusk are a free forty-minute walk."],
             "free")
    b += placelist(rows("free"))
    b += sec("Rainy days", "This is an El Niño winter.",
             ["When it rains, go indoors and stay a while. The <b>Academy Museum</b> drops to $18 after 4:30pm, which is the right time to go anyway. <b>The Last Bookstore</b> is open until eleven most nights. Every film, bowling and comedy pick above works in the rain too."],
             "rain")
    b += placelist(rows("rain"))
    b += oneline("If you only do one thing",
        "The Hammer on a weekday afternoon, then a walk through Westwood. Free, an hour if it is not working, the whole evening if it is.")
    b += sec("What we could not verify", "Left off on purpose.",
             ["Cinespia had no winter dates posted. The Hollywood Bowl is closed until June and Barnsdall's Friday wine nights are a summer series. The Tar Pits museum is closed for construction, and the Two Bit Circus arcade downtown appears to have closed. UCB, the Huntington and Norton Simon would not load for us this time, so they are not here; the Huntington and Norton Simon are in our <a href=\"/guides/best-museums-los-angeles/\">museums guide</a>.",
              "Know a date that should be on this list? <a href=\"/about#tip\">Tell us</a>."])
    b += live_block("tags:date", "", 4, "Good for a date this week",
        "Refreshed every day from the same list that runs on the homepage.", "Good for a date this week", cat="ticket")
    b += morelinks([("Meet people in LA →", "/guides/meet-people-los-angeles/"),
                    ("Supper clubs →", "/guides/supper-clubs-los-angeles/"),
                    ("Best museums →", "/guides/best-museums-los-angeles/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w(f"guides/{slug}/index.html", b)


# ============================== MEET PEOPLE ==============================
MEET = [
 ("run", "Koreatown Run Club",
  "Mondays 7pm from Wilshire and Oxford, Thursdays 8pm from Love Hour, 532 N Western Ave · three or five miles · no sign-up, just show up.",
  "walk", "https://www.koreatownrunclub.com/pages/schedule", [("Free", "free")]),
 ("run", "Silver Lake Track Club",
  "Tuesdays 7pm, a three-mile loop of the reservoir from Red Lion Tavern, 2366 Glendale Blvd · every run free, no sign-up · schedule on their Strava and Instagram.",
  "walk", None, [("Free", "free")]),
 ("run", "Los Angeles Running Club",
  "Mondays 6:45pm, run or walk three or five miles from 13150 Bluff Creek Dr, Playa Vista · Wednesday track night 6:30pm in Santa Monica, capped at 40 · check membership on their site.",
  "walk", "https://runsignup.com/MemberOrg/LosAngelesRunningClub/Page/Schedule", [("Westside", "cat")]),
 ("class", "Improv for Beginners, The Groundlings School",
  "Melrose Ave · one two-and-a-half-hour session for $55, no experience · or Workshop A, six weeks for $365 · new classes posted Tuesdays at 1pm.",
  "art", "https://www.groundlings.com/school", [("From $55", "cat")]),
 ("class", "Saturday swing dance, Pasadena Ballroom Dance Association",
  "73 N Hill Ave, Pasadena · $25 for a lesson at 7:30pm and a live band 8–11pm · no partner needed · free parking.",
  "music", "https://www.pbda.dance/", [("$25", "cat")]),
 ("class", "Intro to Wheel Throwing, Good Dirt LA",
  "4505 S Centinela Ave, Del Rey · a two-hour class for six people, $85 · you will all be equally bad at it, which helps.",
  "art", "https://www.gooddirtla.com/classes", [("Westside", "cat")]),
 ("table", "Haps Club dinners",
  "Our own long-table dinners, at Hermanito in Santa Monica and elsewhere · seats go to the newsletter first.",
  "food", "https://luma.com/TheHapsClub", [("Westside", "cat")]),
 ("table", "Timeleft",
  "Matched dinners for four to six strangers, Wednesdays and Fridays at 7pm, on the Westside, in WeHo and in NoHo · $19.99 a ticket, you pay for your own meal · the one app worth an exception.",
  "food", "https://timeleft.com/", [("App", "cat")]),
 ("help", "Big Sunday, Hollywood",
  "Weekday-morning projects, 10–11:30am, from 1741 N Cherokee Ave · Holiday Singalong & Toy Drive Sun Dec 6, 3–5pm.",
  "walk", "https://bigsunday.org/", [("Free", "free")]),
 ("help", "Heal the Bay beach cleanups",
  "Monthly, on a different LA County beach each time · dates posted by the first of the month and spaces fill.",
  "beach", "https://healthebay.org/beach-cleanups/", [("Free", "free"), ("Westside", "cat")]),
 ("help", "TreePeople",
  "Tree planting, trail care and restoration across the county · no experience needed · events posted a month ahead, register as one person.",
  "park", "https://www.treepeople.org/volunteer/", [("Free", "free")]),
 ("help", "Los Angeles Regional Food Bank",
  "Warehouse shifts at 1734 E 41st St and two other sites · 14 and over · sign up online, no walk-ins.",
  "food", "https://www.lafoodbank.org/volunteer/", [("Free", "free")]),
 ("league", "Volo Sports",
  "Kickball, volleyball, pickleball, soccer and more in Santa Monica, Venice, Mar Vista, Culver City, WeHo and beyond · "
  "$95–$165 for a six-to-eight-week season · sign up alone as a free agent and they place you on a team.",
  "park", "https://www.volosports.com/los-angeles", [("Join alone", "cat")]),
 ("league", "Book clubs at Skylight Books",
  "1818 N Vermont Ave, Los Feliz · the Rabbit Hole nonfiction club meets the third Thursday at 7:30pm · the fiction club returns Jan 26, 2027.",
  "shop", "https://www.skylightbooks.com/events", [("Monthly", "cat")]),
]


def build_meet():
    slug = "meet-people-los-angeles"
    url = f"{SITE}/guides/{slug}/"
    title = "How to Meet People in Los Angeles (Without an App)"
    desc = ("How to meet people in Los Angeles in your 30s and 40s: free run clubs, improv and dance classes, "
            "dinners with strangers and leagues you can join alone.")
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("Meet people in LA", url),
             {"@type": "ItemList", "name": "Ways to meet people in Los Angeles", "url": url,
              "numberOfItems": len(MEET), "itemListOrder": "https://schema.org/ItemListUnordered",
              "itemListElement": [dict({"@type": "ListItem", "position": i, "name": m[1]}, **({"url": m[4]} if m[4] else {}))
                                  for i, m in enumerate(MEET, 1)]}]
    rows = lambda g: [place(n, d, c, u, t) for (gg, n, d, c, u, t) in MEET if gg == g]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; getting out", "How to meet people in LA, <em>without an app</em>",
               "Pick one thing that happens every week and keep going back. Here are fourteen of them.")
    b += facts([("Free and weekly", "Run clubs"), ("Join alone", "Volo, Groundlings"),
                ("Dinner with strangers", "Haps Club, Timeleft"), ("Checked", CHECKED_DATING)])
    b += jump([("Run clubs", "run", "walk"), ("Classes", "class", "art"),
               ("Dinner", "table", "food"), ("Volunteer", "help", "park"),
               ("Leagues and clubs", "league", "ticket"), ("This week", "this-week", "ticket")])
    b += intro(["People say Los Angeles is a hard city to make friends in, and they are half right. It is spread out and everyone drives, so the chance meetings that happen on a New York sidewalk do not happen here. What works instead is repetition: one thing, at the same time every week, until the faces become names.",
                "So this guide is mostly recurring things: weekly runs, six-week classes, monthly cleanups. Going once is a nice evening. Going four times is how you meet people. Every schedule here was read on the group's own page."])
    b += sec("Run clubs", "The fastest way in, and free.",
             ["Run clubs have become the city's default social club, and the good ones welcome walkers and slow runners. <b>Koreatown Run Club</b> meets twice a week and asks nothing of you but showing up. <b>Silver Lake Track Club</b> loops the reservoir on Tuesday nights and ends at the bar it started from. On the Westside, the <b>Los Angeles Running Club</b> runs from Playa Vista on Monday evenings."],
             "run")
    b += placelist(rows("run"))
    b += sec("Classes", "Being a beginner together.",
             ["Improv is the class people credit most often with finding their friends in LA, because it is built on paying attention to strangers. <b>The Groundlings</b> has a single beginner session for $55 if you want to try before committing. In Pasadena, the <b>Saturday swing dance</b> starts with a half-hour lesson and needs no partner; you will dance with a dozen people before the band starts."],
             "class")
    b += placelist(rows("class"))
    b += sec("Dinner with strangers", "Let the seating do the introductions.",
             ["A long table solves the hardest part of meeting people, which is starting the conversation. Haps Club runs its own dinners for exactly this reason, and our <a href=\"/guides/supper-clubs-los-angeles/\">supper clubs guide</a> has the rest of the city's. If you would rather be matched, Timeleft seats you with a handful of strangers and tells you the restaurant shortly before."],
             "table")
    b += placelist(rows("table"))
    b += sec("Volunteer", "Work alongside someone for two hours.",
             ["Volunteering is underrated as a way to meet people, because you talk while your hands are busy and nobody has to think of a question. <b>Big Sunday</b> runs short weekday projects in Hollywood. <b>Heal the Bay</b> cleans a different beach every month, and <b>TreePeople</b> plants trees in neighbourhoods that need them."],
             "help")
    b += placelist(rows("help"))
    b += sec("Leagues and clubs", "Somebody else does the organising.",
             ["Rec leagues are not just for people who played sport in school. <b>Volo</b> lets you sign up alone and puts you on a team, and kickball is mostly an excuse for the bar afterwards. For quieter people, a monthly <b>book club</b> at Skylight gives you the same faces every month and something to talk about."],
             "league")
    b += placelist(rows("league"))
    b += oneline("If you only do one thing",
        "Choose the one closest to where you live or work, put it in your calendar for the next four weeks, and go every time. Proximity beats the perfect group.")
    b += sec("What we could not verify", "Left off on purpose.",
             ["Venice Run Club's website now leads to a domain-sale page, and Santa Monica Track Club has no official site we could find, so neither is listed. UCB's class pages would not load for us. Jazz at LACMA, Grand Performances and the Natural History Museum's First Fridays are some of the best places in the city to meet people, but they run spring and summer, and they go in the weekly email when they return.",
              "Run a group that should be here? <a href=\"/about#tip\">Send us the page</a>."])
    b += live_block("tags:date", "", 4, "Places to meet people this week",
        "Refreshed every day from the same list that runs on the homepage.", "Places to meet people this week", cat="ticket")
    b += morelinks([("Date ideas →", "/guides/date-ideas-los-angeles/"),
                    ("Supper clubs →", "/guides/supper-clubs-los-angeles/"),
                    ("Free things this weekend →", "/guides/free-things-to-do-in-la-this-weekend/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w(f"guides/{slug}/index.html", b)


# ============================== REGISTRATION ==============================
NEW_GUIDES = [
 ("/guides/christmas-lights-los-angeles/", "park", "December · checked on each organiser's site", "Christmas Lights in Los Angeles",
  "Descanso, Zoo Lights, the Griffith Park train, the free streets in Altadena and Woodland Hills, and the Marina del Rey boat parade, with this season's dates.",
  "weekly", "0.8"),
 ("/guides/holiday-things-to-do-los-angeles/", "ticket", "The holidays · checked on each organiser's site", "Holiday Things to Do in Los Angeles",
  "Outdoor ice rinks, two Nutcrackers, the Messiah sing-along at Disney Hall and the free Music Center celebration, which has moved to December 20.",
  "weekly", "0.8"),
 ("/guides/new-years-eve-los-angeles/", "music", "Dec 31 · checked on each organiser's site", "New Year's Eve in Los Angeles",
  "Free NYELA at Grand Park, Marina del Rey fireworks at 11:59pm, a Disney Hall concert, cruises, and the Rose Parade on New Year's Day.",
  "weekly", "0.8"),
 ("/guides/date-ideas-los-angeles/", "art", "Citywide · for two", "Date Ideas in Los Angeles",
  "Sorted by the kind of date: easy first dates, things to do together, big nights, free nights and rainy days.",
  "monthly", "0.8"),
 ("/guides/meet-people-los-angeles/", "walk", "Citywide · weekly things to join", "How to Meet People in Los Angeles",
  "Free run clubs, improv and swing classes, dinners with strangers, volunteering and leagues you can join alone.",
  "monthly", "0.8"),
]

from build_guides_best import _read, _write  # noqa: E402
import build_guides_best as _bgb  # noqa: E402


def register():
    _bgb.NEW_GUIDES = NEW_GUIDES        # reuse the tested, idempotent registration
    _bgb.register()


def crosslink():
    adds = {"guides/supper-clubs-los-angeles/index.html": [("Meet people in LA →", "/guides/meet-people-los-angeles/"),
                                                          ("Date ideas →", "/guides/date-ideas-los-angeles/")],
            "guides/la-for-skeptics/index.html": [("Date ideas →", "/guides/date-ideas-los-angeles/")],
            "guides/free-things-to-do-in-la-this-weekend/index.html": [("Christmas lights →", "/guides/christmas-lights-los-angeles/")],
            "guides/halloween-events-los-angeles/index.html": [("Holiday things to do →", "/guides/holiday-things-to-do-los-angeles/")]}
    for path, links in adds.items():
        if not os.path.exists(os.path.join(ROOT, path)):
            continue
        s = _read(path)
        add = "".join(f'  <a href="{h}">{t}</a>\n' for t, h in links if f'href="{h}"' not in s)
        if add:
            s = re.sub(r'(<div class="morelinks">\n(?:  <a [^\n]*\n)+)', lambda m: m.group(1) + add, s, count=1)
            _write(path, s)


if __name__ == "__main__":
    build_lights()
    build_holiday()
    build_nye()
    build_dates()
    build_meet()
    register()
    crosslink()
    print("built 5 season/dating guides; registered in index, sitemap, llms.txt")
