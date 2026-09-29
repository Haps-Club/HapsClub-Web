#!/usr/bin/env python3
"""
build_guides_fall.py — the three guides added 2026-09-29.

Kept separate from build_guides.py on purpose: several older guides were
hand-corrected after they were generated (the museum page's monthly checks),
so re-running build_guides.py would roll those fixes back. This file only
writes its own three pages.

    python3 scripts/build_guides_fall.py
    python3 scripts/build_pages.py

Unlike build_guides.py, venues here do not have to have run in a Haps issue
(Michael changed that rule on 2026-09-29) but every one is checked against
its own site. The Halloween page is dated on purpose: it is a seasonal page,
re-dated every September.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_guides import (head, ghero, facts, jump, intro, sec, place, placelist,
                          oneline, table, live_block, morelinks, breadcrumb, webpage,
                          itemlist, ld, w, FOOT, OG)
TODAY = "2026-09-29"
PUB   = "2026-09-29"

def a(href, text):
    return f'<a href="{href}" target="_blank" rel="noopener">{text}</a>'

def ev_node(title, desc, start, end, venue, addr, url, price=None, organizer=None):
    org = {"@type": "Organization", "name": organizer or venue, "url": url}
    n = {"@type": "Event", "name": title, "description": desc, "startDate": start, "endDate": end,
         "eventStatus": "https://schema.org/EventScheduled",
         "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
         "image": [OG], "url": url, "organizer": org, "performer": dict(org),
         "location": {"@type": "Place", "name": venue,
                      "address": {"@type": "PostalAddress", "addressLocality": addr,
                                  "addressRegion": "CA", "addressCountry": "US"}}}
    if price is not None:
        n["offers"] = {"@type": "Offer", "price": str(price), "priceCurrency": "USD",
                       "availability": "https://schema.org/InStock", "url": url, "validFrom": "2026-09-01"}
    return n

# ============================== HALLOWEEN ==============================
SPOOKY = [
 # (anchor-group, name, detail, cat, url, tags, start, end, venue, locality, price, desc)
 ("lanterns","Carved at Descanso Gardens","Nightly Oct 2 – Nov 1 · 6–10pm · from $29 adults, under 2 free.","park",
  "https://www.descansogardens.org/carved/",[("Nightly","cat")],"2026-10-02T18:00:00-07:00","2026-11-01T22:00:00-07:00","Descanso Gardens","La Cañada Flintridge",29,
  "Hand-carved pumpkins, glowing trails and wood spirits take over the garden after dark."),
 ("lanterns","Magic of the Jack O'Lanterns","Select nights through Nov 1 · South Coast Botanic Garden · from $28.99 adults.","park",
  "https://magicofthejackolanterns.com/la/",[("Timed entry","cat")],"2026-09-18T18:00:00-07:00","2026-11-01T22:00:00-07:00","South Coast Botanic Garden","Palos Verdes Peninsula",28.99,
  "More than 10,000 carved pumpkins along a mile-long trail."),
 ("lanterns","Mr. Bones Pumpkin Patch","Daily Oct 2 – 31 · Culver City · $10–$25 by date, under 3 free.","outdoors",
  "https://mrbonespumpkinpatch.com/admissions/",[("Westside","cat")],"2026-10-02T10:00:00-07:00","2026-10-31T21:00:00-07:00","Mr. Bones Pumpkin Patch","Culver City",10,
  "The Westside's classic patch, with hay mazes, slides and a pumpkin credit included with admission."),
 ("movies","Cinespia: Carrie, 50th anniversary","Sat Oct 10 · gates 5:30pm, film 7:15pm · Hollywood Forever.","ticket",
  "https://cinespia.org/event/carrie-50/",[("Ticketed","cat")],"2026-10-10T19:15:00-07:00","2026-10-10T23:59:00-07:00","Hollywood Forever Cemetery","Hollywood",None,
  "De Palma's prom-night horror turns fifty on the cemetery lawn."),
 ("movies","Cinespia Halloween weekend","Fri Oct 30 Jennifer's Body, Sat Oct 31 The Thing · gates 5:30pm.","ticket",
  "https://cinespia.org/",[("Ticketed","cat")],"2026-10-30T19:15:00-07:00","2026-10-31T23:59:00-07:00","Hollywood Forever Cemetery","Hollywood",None,
  "Two cult horror picks close out Halloween among the headstones."),
 ("movies","Street Food Cinema: Boo-ze, Bites & Frights","Oct 16, 17, 23, 24 · Heritage Square · $65 GA, $45 per car.","ticket",
  "https://streetfoodcinema.com/schedule/boo-ze-bites-2026",[("Ticketed","cat")],"2026-10-16T17:30:00-07:00","2026-10-24T23:00:00-07:00","Heritage Square Museum","Montecito Heights",45,
  "Horror double features in front of haunted Victorian houses."),
 ("haunts","Halloween Horror Nights","Select nights through Nov 1 · Universal Studios Hollywood · from about $77.","ticket",
  "https://www.universalstudioshollywood.com/hhn/en/us",[("Big","cat")],"2026-09-03T19:00:00-07:00","2026-11-01T23:59:00-07:00","Universal Studios Hollywood","Universal City",77,
  "Eight haunted houses and scare zones across the studio backlot."),
 ("haunts","Delusion: Den of the Mosquito","Select nights through Nov 8 · Beckett Mansion, West Adams · from $143, 18+.","ticket",
  "https://enterdelusion.com/",[("Immersive","cat")],"2026-09-17T19:00:00-07:00","2026-11-08T23:59:00-08:00","Beckett Mansion","West Adams",143,
  "Interactive horror theatre set in a 1920s vampire den, back in its original mansion."),
 ("haunts","Queen Mary's Dark Harbor","Select nights through Nov 1 · Long Beach · from about $30.","ticket",
  "https://www.queenmary.com/dark-harbor.htm",[("Ticketed","cat")],"2026-09-18T19:00:00-07:00","2026-11-01T23:59:00-07:00","The Queen Mary","Long Beach",29.99,
  "Mazes through a famously haunted ocean liner, with bars on the dock."),
 ("haunts","Knott's Scary Farm","Select nights through Oct 31 · Buena Park · from $65 online.","ticket",
  "https://www.sixflags.com/knotts/events/scary-farm",[("Ticketed","cat")],"2026-09-17T19:00:00-07:00","2026-10-31T23:59:00-07:00","Knott's Berry Farm","Buena Park",65,
  "The original theme-park haunt, past fifty years and still loud."),
 ("free","Marina Halloween Spooktacular","Sat–Sun Oct 24–25 · 4–10pm · Burton Chace Park · free with RSVP.","beach",
  "https://visitmdr.com/annual-events/halloween-spooktacular",[("Free","free"),("Westside","cat")],"2026-10-24T16:00:00-07:00","2026-10-25T22:00:00-07:00","Burton Chace Park","Marina del Rey",0,
  "A free waterfront festival: face painting at dusk, a blackout maze after dark."),
 ("free","Boo at the L.A. Zoo","Oct 24–25 and Oct 31 – Nov 1 · 10am–3pm · free with zoo admission.","park",
  "https://lazoo.org/plan-your-visit/special-experiences/boo-at-the-l-a-zoo-2026/",[("Kids","cat")],"2026-10-24T10:00:00-07:00","2026-11-01T15:00:00-08:00","Los Angeles Zoo","Griffith Park",None,
  "Costumed trick-or-treating and animals tearing into pumpkins."),
 ("free","West Hollywood Halloween Carnaval","Sat Oct 31 · 6–11pm · Santa Monica Blvd, Doheny to La Cienega · free.","music",
  "https://www.visitwesthollywood.com/events/halloween-carnaval/",[("Free","free")],"2026-10-31T18:00:00-07:00","2026-10-31T23:00:00-07:00","Santa Monica Boulevard","West Hollywood",0,
  "A mile of Santa Monica Boulevard and more than 100,000 people in costume."),
 ("free","Magic Market: Bewitched","Sat–Sun Oct 10–11 · 5–10pm · Heritage Square · $15.","shop",
  "https://www.eventbrite.com/e/magic-markets-bewitched-los-angeles-tickets-1998619035336",[("Night market","cat")],"2026-10-10T17:00:00-07:00","2026-10-11T22:00:00-07:00","Heritage Square Museum","Montecito Heights",15,
  "A witchy night market with tarot, vintage and live music."),
 ("muertos","Día de los Muertos at Hollywood Forever","Sat Oct 24 · noon–midnight in three entry windows · ticketed, ages 5+.","art",
  "https://www.ladayofthedead.com/event-info/",[("Ticketed","cat")],"2026-10-24T12:00:00-07:00","2026-10-24T23:59:00-07:00","Hollywood Forever Cemetery","Hollywood",None,
  "The city's largest Día de los Muertos, in its 27th year, with altars, a procession and live bands."),
 ("muertos","Downtown Día de los Muertos at Grand Park","Oct 24 – Nov 2 · altars up 8am–9pm daily · free.","art",
  "https://grandparkla.org/diadelosmuertos",[("Free","free")],"2026-10-24T11:00:00-07:00","2026-11-02T21:00:00-08:00","Gloria Molina Grand Park","Civic Center",0,
  "Seventeen artist altars stand for ten days in the middle of downtown."),
 ("muertos","Día de los Muertos on Olvera Street","Oct 25 – Nov 2 · nightly procession, Danza de la Muerte at 6pm · free.","walk",
  "https://www.olveraevents.com/day-of-the-dead-olvera-street",[("Free","free")],"2026-10-25T10:00:00-07:00","2026-11-02T21:00:00-08:00","Olvera Street","El Pueblo",0,
  "Nine nights of procession through the oldest street in the city."),
]

def rows_for(group):
    return [place(n, d, c, u, t) for (g, n, d, c, u, t, *_ ) in SPOOKY if g == group]

def build_halloween():
    url = "https://haps.club/guides/halloween-events-los-angeles/"
    title = "Halloween Events in Los Angeles 2026: Pumpkins, Haunts and Día de los Muertos"
    desc = ("Every Halloween and Día de los Muertos event in LA worth your October — pumpkin nights, "
            "cemetery screenings, haunts and the free ones — with 2026 dates checked on each official site.")
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("Halloween in LA", url)]
    # Season events go in their own ld+json block: build_pages.splice_ld rewrites
    # the Event nodes of the FIRST block every Sunday and would delete these.
    season = [ev_node(n, dsc, s, e, v, loc, u, pr) for (g, n, d, c, u, t, s, e, v, loc, pr, dsc) in SPOOKY]
    b = head(title, desc, url, ld(nodes))
    b += '<script type="application/ld+json">' + ld(season) + '</script>\n'
    b += ghero("Los Angeles &middot; October 2026", "Spooky season in LA, <em>sorted</em>",
               "Pumpkins, cemetery movies, the proper haunts and Día de los Muertos. Every 2026 date checked on the official site.")
    b += facts([("Season", "Oct 2 – Nov 2"), ("Book first", "Carrie &amp; Delusion"),
                ("Best free", "WeHo Carnaval"), ("Westside", "Mr. Bones, the Marina")])
    b += jump([("Pumpkin nights", "lanterns", "park"), ("Cemetery movies", "movies", "ticket"),
               ("Haunts", "haunts", "ticket"), ("Free", "free", "beach"),
               ("Día de los Muertos", "muertos", "art"), ("This week", "this-week", "ticket")])
    b += intro(["LA does Halloween in two very different ways. There is the theme-park version, loud and expensive and very good at it, and there is the version that happens in gardens and cemeteries, which is what the rest of the country does not have.",
                "This page is the short list of both, plus Día de los Muertos, which in this city is the bigger event of the two and deserves its own week."])
    b += sec("Pumpkin nights", "Go after dark, go on a weeknight.",
             ["Carved at Descanso is the pick: a real garden, lit properly, with carving you actually stop to look at. It is in La Cañada Flintridge, not Glendale, and weeknight tickets are the cheap ones.",
              "Magic of the Jack O'Lanterns is the bigger count, ten thousand pumpkins on a mile of trail. Mr. Bones is the one to take kids to on the Westside."], "lanterns")
    b += placelist(rows_for("lanterns"))
    b += sec("Cemetery movies", "Horror, on a lawn, among the headstones.",
             ["Cinespia at Hollywood Forever is the most LA thing on this page. Carrie's fiftieth on October 10 will sell out before the week of, so buy now, bring a blanket and arrive when the gates open at 5:30.",
              "Street Food Cinema runs horror double features in front of the Victorian houses at Heritage Square, which is as close as LA gets to a haunted street."], "movies")
    b += placelist(rows_for("movies"))
    b += sec("The proper haunts", "Pick one. They are not cheap.",
             ["Halloween Horror Nights is the benchmark, and a weeknight early in October is the way to do it without a two-hour line. Delusion is the opposite: fifty minutes, a small group, a mansion in West Adams, and far scarier for it."], "haunts")
    b += placelist(rows_for("haunts"))
    b += sec("Free, or nearly", "The ones that cost nothing.",
             ["The West Hollywood Carnaval on Halloween night is a hundred thousand people in costume on a mile of Santa Monica Boulevard, and it is free. On the Westside, the Marina's Spooktacular the weekend before is the easy one with kids."], "free")
    b += placelist(rows_for("free"))
    b += sec("Día de los Muertos", "The bigger holiday here.",
             ["Hollywood Forever's celebration is the city's largest, with altars built across the whole cemetery. Grand Park and Olvera Street run for more than a week and are free, so you can go on a weeknight and see the altars without the crowd."], "muertos")
    b += placelist(rows_for("muertos"))
    b += table(["What", "When", "Cost"], [
        [a(u, n), d.split(" · ")[0], (d.split(" · ")[-1])] for (g, n, d, c, u, t, *_ ) in SPOOKY])
    b += oneline("If you only do one thing",
        "Cinespia's Carrie on October 10. A horror film in a cemetery, in Hollywood, fifty years to the season. Nowhere else can do that.")
    b += live_block("tags:halloween", "tags:culture", 6, "Halloween on the homepage this week",
        "Refreshed every Sunday night from the same list that runs on the homepage.",
        "Also on this week")
    b += morelinks([("Free this weekend →", "/guides/free-things-to-do-in-la-this-weekend/"),
                    ("Supper clubs →", "/guides/supper-clubs-los-angeles/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w("guides/halloween-events-los-angeles/index.html", b)

# ============================== SUPPER CLUBS ==============================
def build_supper():
    url = "https://haps.club/guides/supper-clubs-los-angeles/"
    title = "Supper Clubs and Chef's Tables in LA: Where to Eat With Strangers"
    desc = ("LA's best supper clubs, long-table dinners and counter omakase — how each one books, "
            "what it costs, and which ones are worth the effort.")
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("Supper clubs", url),
             itemlist("Supper clubs and chef's tables in Los Angeles", url, [
                ("Hermanito Broadway", "802 Broadway, Santa Monica", "https://luma.com/hapsclub-hermanito-dinnertime?coupon=HAPSCLUB5"),
                ("LA Foodshop", None, "https://www.lafoodshop.com/get-invited/"),
                ("Twentieth Street Garden", "2267 W 20th St", "https://www.hotplate.com/twentiethstreetgarden"),
                ("Outstanding in the Field", None, "https://outstandinginthefield.com/"),
                ("Timeleft", None, "https://timeleft.com/"),
                ("222", None, "https://222.place/"),
                ("Shunji", "3003 Ocean Park Blvd, Santa Monica", "https://www.exploretock.com/shunji/"),
                ("Mori Nozomi", "11500 W Pico Blvd", "https://www.exploretock.com/mori-nozomi-los-angeles"),
                ("Ueki at Blue Ribbon Sushi", "15225 Palisades Village Ln, Pacific Palisades", "https://www.brsushipalisades.com/reservations"),
                ("Loreto", "1991 Blake Ave", "https://www.loreto.la/omakase"),
                ("Hayato", "1320 E 7th St", "https://www.exploretock.com/hayato")], ordered=False)]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; Westside &amp; citywide", "Dinner with <em>strangers</em>",
               "Supper clubs, long tables and the counter seats where the chef is the evening.")
    b += facts([("Cheapest in", "Timeleft"), ("Most social", "Long tables"),
                ("Hardest seat", "Hayato"), ("Ours", "Hermanito, Santa Monica")])
    b += jump([("Long tables", "long", "food"), ("Matched dinners", "apps", "drink"),
               ("Counter seats", "counter", "food"), ("This week", "this-week", "ticket")])
    b += intro(["The best dinners in LA right now are the ones where you do not choose who you sit next to.",
                "They come in three shapes: a long table someone else has set, an app that picks your five dinner companions, and a counter of eight seats where the chef talks you through every course. This page has the ones worth booking in each."])
    b += sec("Long tables", "Someone else sets the table.",
             ["We run our own at Hermanito on Broadway in Santa Monica: mingle first, then a family-style Japanese-Mexican dinner where the seating does the introductions.",
              "LA Foodshop is the long-running one, a monthly dinner in a different space each time, invitation by email list. Twentieth Street Garden drops backyard dinners and asados on Hotplate a few times a year, and they go in a day."], "long")
    b += placelist([
        place("Haps Club at Hermanito", "802 Broadway, Santa Monica · family-style dinner, one drink included · code HAPSCLUB5.", "food",
              "https://luma.com/hapsclub-hermanito-dinnertime?coupon=HAPSCLUB5", [("Ours", "cat"), ("Luma", "cat")]),
        place("LA Foodshop", "Venice-based, rotating venues · monthly · get on the list and wait for the email.", "food",
              "https://www.lafoodshop.com/get-invited/", [("Invite list", "cat")]),
        place("Twentieth Street Garden", "2267 W 20th St, West Adams · backyard dinners and concerts · tickets drop on Hotplate.", "food",
              "https://www.hotplate.com/twentiethstreetgarden", [("Irregular", "cat")]),
        place("Outstanding in the Field", "One long table on a farm · Malibu dates sell out, so join the waitlist.", "outdoors",
              "https://outstandinginthefield.com/", [("$$$$", "cat")])])
    b += sec("Matched dinners", "Let the app pick the table.",
             ["Timeleft seats you with five strangers every Wednesday and reveals the restaurant that afternoon. 222 does the same off a personality questionnaire and plans the rest of the night. Both are better than they sound and best done with an open evening after."], "apps")
    b += placelist([
        place("Timeleft", "Wednesday nights, citywide · membership, then you pay for your own dinner.", "drink", "https://timeleft.com/", [("Weekly", "cat")]),
        place("222", "Citywide · questionnaire, then a group of about five and a planned night.", "drink", "https://222.place/", [("App", "cat")])])
    b += sec("Counter seats", "Eight stools and a chef.",
             ["The counter is the other way to eat with strangers: the same menu, the same pace, the whole room watching one set of hands.",
              "On the Westside, Shunji in Santa Monica has seven seats and Mori Nozomi on Pico is the quiet one. The new one is Ueki, fourteen seats behind a curtain inside Blue Ribbon in the Palisades. East of the river, Loreto's Wednesday omakase does Baja seafood in ten courses, and Hayato downtown is the hardest reservation in the city."], "counter")
    b += placelist([
        place("Shunji", "3003 Ocean Park Blvd, Santa Monica · seven seats · Tock releases on the 7th and 22nd.", "food", "https://www.exploretock.com/shunji/", [("$$$$", "cat")]),
        place("Mori Nozomi", "11500 W Pico Blvd · counter omakase · booked on Tock.", "food", "https://www.exploretock.com/mori-nozomi-los-angeles", [("$$$$", "cat")]),
        place("Ueki at Blue Ribbon Sushi", "Palisades Village · fourteen seats, one 6:30 seating, Wed–Sun · book by phone.", "food", "https://www.brsushipalisades.com/reservations", [("New", "cat")]),
        place("Loreto Wednesday omakase", "1991 Blake Ave, Frogtown · eight seafood courses and two desserts · every Wednesday.", "food", "https://www.loreto.la/omakase", [("Weekly", "cat")]),
        place("Hayato", "ROW DTLA · seven guests, one seating · Tock releases monthly.", "food", "https://www.exploretock.com/hayato", [("Hardest seat", "cat")])])
    b += oneline("If you only do one thing",
        "Book a long table rather than a counter. The counter is about the chef; the long table is about who you meet, and that is the part you remember.")
    b += live_block("tags:supper", "tags:food", 4, "Dinners on the calendar",
        "Refreshed every Sunday night from the same list that runs on the homepage.",
        "Food on the homepage this week", cat="food")
    b += morelinks([("Santa Monica →", "/guides/santa-monica/"), ("Venice →", "/guides/venice/"),
                    ("All guides →", "/guides/")])
    b += FOOT
    w("guides/supper-clubs-los-angeles/index.html", b)

# ============================== SKEPTICS ==============================
SKEP = [
 ("getty","museum","Morning","The Getty, then the Country Mart.",
  ["Richard Meier's hilltop explains LA's sprawl better than any skyline. Admission is free with a timed booking; parking is $25, $15 after 3pm, and it is closed Mondays.",
   "On the way down, the Brentwood Country Mart does lunch: Reddi Chick fries, or Farmshop."],
  [("Getty Center","Free with timed entry · closed Mondays · Saturdays until 9pm for sunset.","museum","https://www.getty.edu/visit/center/")]),
 ("canals","walk","Morning","The Venice canals, before Abbot Kinney wakes up.",
  ["Five minutes from the boardwalk, the canals are the quietest walk in the city. Park on a side street, walk them first, then do Abbot Kinney for coffee."],
  [("Abbot Kinney Blvd","Coffee, shops and lunch after the canals.","walk","https://www.abbotkinneyblvd.com/")]),
 ("malibu","beach","Saturday","A farm stand and a sea-stack cove.",
  ["Thorne Family Farm opens its stand on Saturdays only, 9am to 1pm. Buy fruit, then drive ten minutes to El Matador for the cove. The lot is small, so go early or at golden hour."],
  [("Thorne Family Farm","6043 Bonsall Dr, Malibu · Saturdays 9am–1pm.","food","https://www.thornefamilyfarm.com/")]),
 ("bluffs","beach","Sunset","Palisades Park to the pier.",
  ["Start at Montana forty-five minutes before sunset and walk south along the bluff to the Ferris wheel. It is the postcard and it lives up to it. Park in a downtown structure, not on the pier deck."],
  [("Palisades Park","Ocean Ave bluffs, Santa Monica · free.","park","https://www.santamonica.gov/places/parks/palisades-park")]),
 ("bowl","music","Night","A picnic at the Hollywood Bowl.",
  ["Bring the picnic and the wine, both allowed, take the Park &amp; Ride shuttle, and sit on the cheap benches. Seventeen thousand people under the stars is the ritual that converts people."],
  [("Hollywood Bowl","Season runs through October · picnics allowed · shuttle over parking.","music","https://www.hollywoodbowl.com/")]),
 ("observatory","park","Evening","Walk up to the Observatory.",
  ["Park near Fern Dell, get coffee and pie at Trails, and hike up rather than fight for the top lot. Stay until dark, when the grid lights up and the city finally makes sense. Closed Mondays."],
  [("Griffith Observatory","Free · closed Mondays · opens noon weekdays, 10am weekends.","park","https://griffithobservatory.lacity.gov/visit/")]),
 ("ktown","drink","Night","Koreatown: a soak, then galbi.",
  ["Wi Spa is open all night. Two hours of soaking, then Park's BBQ on Vermont for prime galbi. Get there before six on a weekend."],
  [("Wi Spa","2700 Wilshire Blvd · open 24 hours.","drink","https://wispausa.com/")]),
 ("market","food","Lunch","Grand Central Market.",
  ["The city has eaten here since 1917. Graze three stalls rather than commit to one, then ride Angels Flight up Bunker Hill."],
  [("Grand Central Market","317 S Broadway · validated lot on Hill St.","food","https://grandcentralmarket.com/visit-the-market/")]),
 ("larchmont","walk","Sunday","Larchmont on a Sunday.",
  ["A small-town main street hiding in the middle of the city. Sunday has the farmers market; afterwards, walk the Hancock Park blocks for the houses."],
  [("Larchmont Village","Larchmont Blvd · Sunday farmers market.","shop","http://www.larchmontvillagebid.com/")]),
 ("huntington","park","Afternoon","The Huntington's gardens.",
  ["Two hundred acres of gardens and a Gainsborough or two. Buy timed tickets, skip Tuesdays when it is closed, and go straight to the Japanese and Chinese gardens."],
  [("The Huntington","San Marino · closed Tuesdays · timed tickets.","park","https://www.huntington.org/plan-your-visit")]),
]
def build_skeptic():
    url = "https://haps.club/guides/la-for-skeptics/"
    title = "Where to Take Someone Who Says They Don't Like LA"
    desc = ("Ten places that change a visitor's mind about Los Angeles — the Getty, the canals, "
            "a Malibu farm stand, the Bowl — with the timing and parking that make them work.")
    from build_guides import stop, route
    nodes = [webpage(title, url, desc, PUB, TODAY), breadcrumb("LA for skeptics", url),
             itemlist("Where to take an LA skeptic", url,
                      [(p[0], None, p[3]) for s in SKEP for p in s[5]], ordered=False)]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; Westside first", "For the friend who <em>hates</em> LA",
               "Ten places, in roughly the order of how fast they work.")
    b += facts([("Start with", "The Getty"), ("Cost", "Mostly free"),
                ("Avoid", "Mondays"), ("Secret weapon", "Timing")])
    b += intro(["Everyone who says they do not like LA has had the same trip: a car, a freeway, the Walk of Fame, a long drive back.",
                "The fix is not a better attraction. It is the right place at the right hour, and none of these need a reservation more than a day out."])
    b += route([stop(an, cat, when, h2, paras, placelist([place(n, d, c, u) for (n, d, c, u) in pl]))
                for (an, cat, when, h2, paras, pl) in SKEP])
    b += oneline("If you only have one day",
        "The Getty in the morning, lunch at the Country Mart, the bluff walk to the pier at sunset. All on the Westside, one car park each, and nobody sits on a freeway.")
    b += live_block("area:westside", "", 4, "On the Westside this week",
        "Refreshed every Sunday night from the same list that runs on the homepage.")
    b += morelinks([("Venice →", "/guides/venice/"), ("Santa Monica →", "/guides/santa-monica/"),
                    ("Free museum days →", "/guides/free-museum-days-los-angeles/")])
    b += FOOT
    w("guides/la-for-skeptics/index.html", b)

NEW_GUIDES = [
 ("/guides/halloween-events-los-angeles/","ticket","Citywide · October 2026","Halloween Events in Los Angeles",
  "Pumpkin nights, cemetery movies, the proper haunts and Día de los Muertos, with every 2026 date checked."),
 ("/guides/supper-clubs-los-angeles/","food","Westside &amp; citywide · dinner","Supper Clubs &amp; Chef's Tables in LA",
  "Long tables, matched dinners and eight-seat counters — how each one books and which are worth it."),
 ("/guides/la-for-skeptics/","beach","Westside first · ten stops","Where to Take Someone Who Says They Don't Like LA",
  "Ten places that change a visitor's mind, with the timing and parking that make them work."),
]

if __name__ == "__main__":
    build_halloween(); build_supper(); build_skeptic()
    print("done")
