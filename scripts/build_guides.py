#!/usr/bin/env python3
"""
build_guides.py — regenerate every page under guides/ from this file.

The guides are generated, not hand-edited. Change the copy here and re-run:

    python3 scripts/build_guides.py
    python3 scripts/build_pages.py     # then fill the live blocks + schema

Conventions this file encodes, all of which matter:
  * Header and footer come from scripts/site_chrome.py — the same markup the
    homepage uses. Never write nav or footer HTML here.
  * Pages use the shared .snav nav and the 1080 .wrap.wide container; every
    content block inside it shares one 764px measure.
  * Prose is emitted one <div class="body"> per paragraph, because
    sunset-pages.css styles .body p:nth-child(2) as a small grey caption and a
    multi-paragraph .body silently demotes its second sentence.
  * .route / .stop is only for content that really is a sequence.
  * Every number in a heading must match the list under it ("Four rooms" means
    four .place rows).
  * No dates in guide copy. These pages are evergreen; anything time-bound
    belongs in the HAPS:LIVE block, which build_pages.py fills and prunes.
  * Every venue named here has appeared in a Haps Club newsletter issue.
"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_chrome

OUT  = os.environ.get("REPO") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GA   = "G-RKY63MK7ND"
KIT  = "9421017"
LOGO = "https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/haps-club-logo.svg?v=5"
OG   = "https://haps.club/assets/og-card.png"
TODAY = "2026-09-07"

FOOTER = site_chrome.footer()


# ---------- shared components v2: nav, icons, hero, route, places ----------
SPRITE = '''<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="i-food" viewBox="0 0 24 24"><path d="M6 3v7a2 2 0 0 0 2 2 2 2 0 0 0 2-2V3M8 12v9"/><path d="M17 3c-1.5 1.5-2 3.5-2 6 0 1.7.8 3 2 3v9"/></symbol>
<symbol id="i-coffee" viewBox="0 0 24 24"><path d="M4 8h13v6a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V8Z"/><path d="M17 9h2a2.5 2.5 0 0 1 0 5h-2"/><path d="M7 3v2M11 3v2"/></symbol>
<symbol id="i-drink" viewBox="0 0 24 24"><path d="M5 4h14l-6 7v7"/><path d="M9 21h6"/></symbol>
<symbol id="i-art" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><circle cx="9" cy="9.5" r="1.1"/><circle cx="15" cy="9.5" r="1.1"/><circle cx="9.5" cy="15" r="1.1"/></symbol>
<symbol id="i-music" viewBox="0 0 24 24"><path d="M9 18V6l10-2v12"/><circle cx="6.5" cy="18" r="2.6"/><circle cx="16.5" cy="16" r="2.6"/></symbol>
<symbol id="i-walk" viewBox="0 0 24 24"><circle cx="13.5" cy="4" r="1.9"/><path d="M11 21l1.6-6.2L9.5 12V8.4l4-1.6 2.5 3 2.5 1.1"/><path d="M12.6 14.8 9 21"/></symbol>
<symbol id="i-beach" viewBox="0 0 24 24"><path d="M3 16c2 0 2-1.8 4-1.8S9 16 11 16s2-1.8 4-1.8S17 16 19 16"/><path d="M3 20.5c2 0 2-1.8 4-1.8s2 1.8 4 1.8 2-1.8 4-1.8 2 1.8 4 1.8"/><circle cx="17" cy="6" r="3"/></symbol>
<symbol id="i-museum" viewBox="0 0 24 24"><path d="M12 3l9 5H3l9-5Z"/><path d="M5 9v9M9.5 9v9M14.5 9v9M19 9v9M2.5 21h19"/></symbol>
<symbol id="i-park" viewBox="0 0 24 24"><path d="M12 3l5 7h-3l4 6H6l4-6H7l5-7Z"/><path d="M12 16.5V21"/></symbol>
<symbol id="i-shop" viewBox="0 0 24 24"><path d="M4.2 8h15.6l-1.2 12H5.4L4.2 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></symbol>
<symbol id="i-ticket" viewBox="0 0 24 24"><path d="M3 9.5V6h18v3.5a2.5 2.5 0 0 0 0 5V18H3v-3.5a2.5 2.5 0 0 0 0-5Z"/><path d="M13 6v12"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.6"/><path d="M12 7v5.4l3.3 2"/></symbol>
<symbol id="i-map" viewBox="0 0 24 24"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Z"/><path d="M9 4v14M15 6v14"/></symbol>
<symbol id="i-go" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
</defs></svg>'''

HERO_ART = '''<svg class="art" viewBox="0 0 340 300" fill="none" aria-hidden="true">
<path d="M18 262C56 232 44 186 92 172s86 22 122-16S258 74 306 58" stroke="url(#gA)" stroke-width="3"
 stroke-linecap="round" stroke-dasharray="1 11"/>
<circle cx="18" cy="262" r="7" fill="#FF9500"/><circle cx="92" cy="172" r="7" fill="#FF3B30"/>
<circle cx="214" cy="156" r="7" fill="#AF52DE"/><circle cx="306" cy="58" r="7" fill="#292F71"/>
<defs><linearGradient id="gA" x1="18" y1="262" x2="306" y2="58" gradientUnits="userSpaceOnUse">
<stop stop-color="#FF9500"/><stop offset=".38" stop-color="#FF3B30"/>
<stop offset=".72" stop-color="#AF52DE"/><stop offset="1" stop-color="#292F71"/></linearGradient></defs></svg>'''

def icon(name, cls="ci"):
    c = f' class="{cls}"' if cls else ""
    return f'<svg{c} aria-hidden="true"><use href="#i-{name}"/></svg>'

def snav(active="/guides/"):
    """The shared site header. Markup lives in scripts/site_chrome.py so the
    homepage and every subpage cannot drift apart again."""
    return site_chrome.header(active=active) + "\n"

def facts(items):
    """items: list of (label, value)"""
    cells = "".join(f'  <div><b>{l}</b><span>{v}</span></div>\n' for l, v in items)
    return f'<div class="facts">\n{cells}</div>\n'

def jump(items):
    """items: list of (label, anchor, cat)"""
    a = "".join(f'  <a href="#{h}" class="cat-{c}">{icon(ICON_FOR[c])}{t}</a>\n' for t, h, c in items)
    return f'<div class="jump">\n{a}</div>\n'

ICON_FOR = {"food": "food", "drink": "drink", "coffee": "coffee", "art": "art",
            "music": "music", "outdoors": "park", "park": "park", "walk": "walk",
            "beach": "beach", "museum": "museum", "shop": "shop", "ticket": "ticket",
            "clock": "clock", "map": "map", "go": "go"}

def ghero(eyebrow, h1, dek, art=True):
    return (f'<section class="ghero">\n'
            f'  <div class="eyebrow"><span class="pin">&#9679;</span> {eyebrow}</div>\n'
            f'  <h1>{h1}</h1>\n  <div class="dek">{dek}</div>\n'
            f'  {HERO_ART if art else ""}\n</section>\n')

def intro(paras):
    return "".join(f'<div class="intro"><p>{p}</p></div>\n' for p in paras)

def stop(anchor, cat, when, h2, paras, extra=""):
    body = "".join(f'  <div class="body"><p>{p}</p></div>\n' for p in paras)
    return (f'<div class="stop cat-{cat}" id="{anchor}">\n'
            f'  <span class="when">{icon(ICON_FOR[cat])}{when}</span>\n'
            f'  <h2>{h2}</h2>\n{body}{extra}</div>\n')

def route(stops):
    return '<div class="route">\n' + "".join(stops) + '</div>\n'

def place(name, detail, cat, href=None, tags=()):
    tg = "".join(f'<span class="tag {t[1]}">{t[0]}</span>' for t in tags)
    inner = (f'<span class="chip-i">{icon(ICON_FOR[cat])}</span>'
             f'<span><span class="pt">{name}</span>'
             f'<span class="pd">{tg}{detail}</span></span>')
    if href:
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        return (f'  <a class="place cat-{cat}" href="{href}"{ext}>{inner}'
                f'<span class="pgo">{icon("go","")}</span></a>\n')
    return f'  <div class="place cat-{cat}">{inner}</div>\n'

def placelist(rows):
    return '<div class="places">\n' + "".join(rows) + '</div>\n'

def oneline(label, text):
    return f'<div class="oneline"><b>{label}</b><p>{text}</p></div>\n'

def table(head_cells, rows):
    th = "".join(f"<th>{h}</th>" for h in head_cells)
    tr = ""
    for r in rows:
        tds = "".join(f"<td>{c}</td>" for c in r)
        tr += f"<tr>{tds}</tr>"
    return (f'<div class="tscroll"><table class="mtable">'
            f'<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>\n')


def w(path, body):
    p = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(body)
    print("  wrote", path, f"({len(body):,}b)")

def head(title, desc, url, ld, og_type="article", active="/guides/", robots=None):
    rb = robots or "index,follow,max-image-preview:large,max-snippet:-1"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="{rb}">
<meta name="author" content="Michael Abraham">
<meta name="theme-color" content="#F5F5F7">
<meta name="geo.region" content="US-CA"><meta name="geo.placename" content="Los Angeles">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Haps Club">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{OG}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Haps Club — everything worth leaving the house for in LA, every week.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{OG}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{GA}");</script>
<script type="application/ld+json">{ld}</script>
<link rel="stylesheet" href="/assets/sunset-pages.css">
</head>
<body>
{SPRITE}
{snav(active)}<main class="wrap wide">
'''

FOOT = f'''
<section class="cta">
  <h3>One email, every Tuesday.</h3>
  <p>This guide stays current because a real person walks the city every week. Get the short version in your inbox — free, and you can leave whenever.</p>
  <form class="sub-form" action="https://app.kit.com/forms/{KIT}/subscriptions" method="post" target="_blank">
    <input type="email" name="email_address" placeholder="you@email.com" aria-label="Your email address" required>
    <button type="submit">Subscribe</button>
  </form>
  <p class="reassure">Free forever. No more than one email a week. Unsubscribe in one click.</p>
</section>
</main>
{FOOTER}
</body>
</html>
'''

def live_block(filt, fallback, limit, heading, note, altheading="", cat="ticket"):
    alt = altheading or heading
    return f'''
<section class="sec" id="this-week">
  <div class="lbl">{icon(ICON_FOR[cat])} Updated every Sunday night</div>
  <!-- HAPS:LIVE start filter="{filt}" fallback="{fallback}" limit="{limit}" -->
  <h2 data-haps-heading="{heading}" data-haps-alt="{alt}">{heading}</h2>
  <div class="body"><p>{note}</p></div>
  <div class="list">
    <div class="row"><div class="txt"><div class="t">Waiting for the first build</div><div class="d">Run <code>python3 scripts/build_pages.py</code>.</div></div></div>
  </div>
  <!-- HAPS:LIVE end -->
</section>
'''

def sec(lbl, h2, paras, anchor=""):
    body = "".join(f'  <div class="body"><p>{p}</p></div>\n' for p in paras)
    aid = f' id="{anchor}"' if anchor else ""
    return f'\n<section class="sec"{aid}>\n  <div class="lbl">{lbl}</div>\n  <h2>{h2}</h2>\n{body}</section>\n'

def morelinks(links):
    a = "\n".join(f'  <a href="{h}">{t}</a>' for t, h in links)
    return f'\n<div class="morelinks">\n{a}\n</div>\n'

def breadcrumb(name, url):
    return {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":"https://haps.club/"},
        {"@type":"ListItem","position":2,"name":"Guides","item":"https://haps.club/guides/"},
        {"@type":"ListItem","position":3,"name":name,"item":url}]}

def webpage(name, url, desc, pub, mod):
    return {"@type":"WebPage","@id":url+"#page","name":name,"url":url,"description":desc,
            "inLanguage":"en-US","datePublished":pub,"dateModified":mod,
            "isPartOf":{"@type":"WebSite","name":"Haps Club","url":"https://haps.club/"},
            "author":{"@type":"Person","name":"Michael Abraham"},
            "publisher":{"@type":"Organization","name":"Haps Club","url":"https://haps.club/"}}

def itemlist(name, url, items, ordered=True):
    order = "ItemListOrderAscending" if ordered else "ItemListUnordered"
    el = []
    for i, (nm, addr, site) in enumerate(items, 1):
        it = {"@type":"LocalBusiness","name":nm}
        if site: it["url"] = site
        if addr:
            it["address"] = {"@type":"PostalAddress","streetAddress":addr,
                             "addressLocality":"Los Angeles","addressRegion":"CA","addressCountry":"US"}
        el.append({"@type":"ListItem","position":i,"item":it})
    return {"@type":"ItemList","name":name,"url":url,"numberOfItems":len(el),
            "itemListOrder":"https://schema.org/"+order,"itemListElement":el}

def ld(nodes):
    return json.dumps({"@context":"https://schema.org","@graph":nodes}, ensure_ascii=False)

# ============================== VENICE ==============================
def build_venice():
    url = "https://haps.club/guides/venice/"
    title = "Things to Do in Venice, CA: A Local's Walk West of Lincoln"
    desc = ("Where to eat, walk and drink in Venice, in the order a local would do it — "
            "Abbot Kinney, the canals, the boardwalk. Updated weekly with what's on.")
    nodes = [webpage(title,url,desc,"2026-09-07",TODAY), breadcrumb("Venice",url),
             itemlist("Things to Do in Venice, CA",url,
                [("Gjusta",None,None),("Venice Canals",None,"https://www.venicecanals.org/"),
                 ("Bodega + Palms","1915 Penmar Ave",None),("The Tasting Kitchen","1633 Abbot Kinney Blvd",None),
                 ("Gjelina","1429 Abbot Kinney Blvd",None),("San Damián","1025 Abbot Kinney Blvd",None),
                 ("Felix Trattoria","Abbot Kinney Blvd",None),("The KINN","150 Horizon Ave",None)])]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; Westside", "Venice, walked <em>west of Lincoln</em>",
               "One day, on foot, in the order that actually works.")
    b += facts([("Best time","Weekday morning"),("Cost","Free to $$$"),
                ("How long","Half a day"),("Getting there","Park once, walk")])
    b += jump([("Morning","morning","coffee"),("The canals","canals","walk"),
               ("Abbot Kinney","abbot-kinney","shop"),("Dinner","dinner","food"),
               ("After","after","music"),("This week","this-week","ticket")])
    b += intro(["Everything below sits west of Lincoln Boulevard — meaning you don't have to leave, and arguably you never should.",
                "This is not a list of the twenty best things in Venice. It is one day, in sequence, built out of places we have actually sent people to in the newsletter."])
    free_rows = [
      place("The Venice Canals","Park near Washington and Pacific and walk the bridges — a mile and a half of water most LA natives have never done.",
            "walk","https://www.venicecanals.org/",[("Free","free")]),
      place("Venice Beach Recreation Center","Paddle tennis, pickleball and volleyball on the sand, any day. Ocean Front Walk.",
            "beach",None,[("Free","free")]),
      place("Venice Skate Park","On the boardwalk. The light at the end of the day is the reason to be there.",
            "outdoors",None,[("Free","free")]),
      place("The Strand","Flat and fast for a morning run, bike or skate, all the way down the coast.",
            "walk",None,[("Free","free")])]
    b += route([
      stop("morning","coffee","Morning","Start at the bakery, not the boardwalk.",
        ["Gjusta, and early.",
         "It is a bakery in a warehouse off Sunset Avenue, the queue is part of the deal, and it is the single best argument for getting to Venice before ten.",
         "Eat there rather than taking it away — the yard is the point."],
        placelist([
          place("Gjusta","A warehouse off Sunset Avenue that happens to make the best bread in the city. Go before ten.","coffee",None,[("$$","cat")])])),
      stop("canals","walk","Late morning","The canals, which almost no local has walked.",
        ["Park near Washington and Pacific and walk the bridges.",
         "A mile and a half of water, front gardens, and people who have clearly thought hard about their porch furniture.",
         "Free, about forty minutes, and quietly one of the most romantic miles in Los Angeles. Come out at the north end and you are on Abbot Kinney."],
        placelist(free_rows)),
      stop("abbot-kinney","shop","Afternoon","Abbot Kinney, top to bottom, then coffee.",
        ["Walk the boulevard for the shop windows, drop down to the boardwalk at the skate park, and watch for a while.",
         "Then back up Rose Avenue, which is where the afternoon actually gets good.",
         "The whole loop is about two miles and costs the price of a coffee."],
        placelist([
          place("Menotti's","Rose Ave. A flat white on the walk back up, and a room that takes espresso far too seriously.","coffee",None,[("$","cat")]),
          place("Great White","Rose Ave. Pastries, and a patio that runs all morning into all afternoon.","coffee",None,[("$$","cat")]),
          place("Bodega + Palms","1915 Penmar Ave · Mon–Sat 8am–8pm. The 100-year-old Mitchell's Market, reborn as a coffee bar and a proper neighbourhood bodega.","shop",None,[("$","cat")])])),
      stop("dinner","food","Dinner","Four rooms, easiest to hardest.",
        ["Gjelina is still the one to beat, and it still takes walk-ins at the bar if you are willing to stand around looking patient.",
         "The Tasting Kitchen has Casey Lane back in the kitchen, which is the reason to go rather than a nostalgia note.",
         "San Damián is Enrique Olvera's mariscos in the old Atla space — book it, because it does not happen by accident.",
         "And Felix is the hardest table on the street. If you keep one reservation in Venice, keep that one."],
        placelist([
          place("Gjelina","1429 Abbot Kinney Blvd. The standard-bearer. Walk-ins at the bar.","food",None,[("$$$","cat"),("Walk-in","cat")]),
          place("The Tasting Kitchen","1633 Abbot Kinney Blvd. The room that defined the street, open again with Casey Lane cooking.","food",None,[("$$$","cat"),("Book ahead","cat")]),
          place("San Damián","1025 Abbot Kinney Blvd. Enrique Olvera's mariscos, feet from the beach, in the old Atla space.","food",None,[("$$$","cat"),("Resy","cat")]),
          place("Felix Trattoria","Abbot Kinney Blvd. Handmade pasta, and the hardest table in Venice.","food",None,[("$$$","cat"),("Hard","cat")])])),
      stop("after","music","After dinner","One room, if the night has legs.",
        ["The KINN is a listening room on Horizon Avenue — vinyl nights, live podcast tapings, forty people at most.",
         "Check what is on before you walk over; it is not open every night."],
        placelist([
          place("The KINN","150 Horizon Ave. A listening room and event space. Small crowds, good sound.","music",None,[("Ticketed","cat")])])),
    ])
    b += oneline("If you only do one thing",
        "Walk the canals at golden hour, then eat at Gjelina's bar without a reservation. That is the whole of Venice in three hours.")
    b += live_block("hood:venice","area:westside",4,"Happening in Venice this week",
        "Pulled from the same hand-picked list that runs on the homepage. Anything past its end time is removed automatically.",
        "Happening on the Westside this week")
    b += sec(icon("map")+" Getting there","Park once, then walk.",
        ["The mistake is driving between Abbot Kinney, the canals and the boardwalk — they are all within the same twenty-minute walk.",
         "Park near Washington and Pacific for the canals end, or on a residential street east of Abbot Kinney and accept the two-block hike.",
         "Beach lot parking is the expensive way to do it and the lots fill by late morning on weekends."])
    b += sec("From the newsletter","We have sent people here a lot.",
        ['Three issues that leaned Venice: <a href="/archive/2026-07-28-after-the-long-table/">After the Long Table</a>, '
         '<a href="/archive/2026-06-29-red-white-long-weekend/">Red, White &amp; the Long Weekend</a>, and '
         '<a href="/archive/2026-07-21-save-the-dates/">Save the Dates</a>.'])
    b += morelinks([("Santa Monica →","/guides/santa-monica/"),("Culver City →","/guides/culver-city/"),
                    ("Free this weekend →","/guides/free-things-to-do-in-la-this-weekend/")])
    b += FOOT
    w("guides/venice/index.html", b)

# ============================== SANTA MONICA ==============================
def build_sm():
    url = "https://haps.club/guides/santa-monica/"
    title = "Free Things to Do in Santa Monica, and What to Pay For"
    desc = ("The free stairs, the Wednesday market and the beach house nobody realises is "
            "public — plus the few Santa Monica tables worth booking. Updated weekly.")
    nodes = [webpage(title,url,desc,"2026-09-07",TODAY), breadcrumb("Santa Monica",url),
             itemlist("Free Things to Do in Santa Monica",url,
                [("The Santa Monica Stairs","Adelaide Dr & 4th St",None),
                 ("Annenberg Community Beach House",None,"https://annenbergbeachhouse.com/"),
                 ("Santa Monica Farmers Market","155-199 Arizona Ave",None),
                 ("West Side Oyster Club","1355 Ocean Ave",None),
                 ("Blankspaces","929 Colorado Ave",None)], ordered=False)]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; Westside","Santa Monica, <em>mostly free</em>",
               "The stairs, the market, the beach house — and the few things worth paying for.")
    b += facts([("Best time","Early morning"),("Cost","Mostly free"),
                ("Market","Wed 8am–1pm"),("Getting there","Street parking")])
    b += jump([("The stairs","stairs","walk"),("Beach house","beach-house","beach"),
               ("The market","market","food"),("Worth paying for","paid","food"),
               ("This week","this-week","ticket")])
    b += intro(["Santa Monica has a reputation as the expensive part of the Westside, and the reputation is only half earned.",
                "The best things here cost nothing: a staircase, a beach house, a farmers market that has been running since 1981."])
    b += route([
      stop("stairs","walk","Free","Start with the stairs.",
        ["Two public staircases drop into the canyon at Adelaide and 4th.",
         "It is free, it is brutal, and it is somehow the most social workout in the city — the same people are there every morning and they will nod at you by week two.",
         "Go before it gets hot, park on the street, and do not attempt to look composed."],
        placelist([place("The Santa Monica stairs","Adelaide Dr &amp; 4th St · two public staircases into the canyon.","walk",None,[("Free","free"),("Street parking","cat")])])),
      stop("beach-house","beach","Free","The beach house nobody realises is public.",
        ["The Annenberg Community Beach House has a courtyard, a splash pad and beach courts, and all of that is free to wander whether or not you swim.",
         "The pool is a small pass on top.",
         "Parking fills by eleven on a weekend, so bike or walk in if you can."],
        placelist([
          place("Annenberg Community Beach House","Courtyard, splash pad and beach courts free to all. Pool is a small pass. Lot fills by 11am weekends.","beach","https://annenbergbeachhouse.com/",[("Free","free")]),
          place("Back on the Beach Café","On the sand at the Annenberg. Breakfast with your feet in it.","food",None,[("$$","cat")])])),
      stop("market","food","Free","Wednesday, not Saturday.",
        ["The Arizona Avenue market on a Wednesday is the one LA's kitchens actually shop at.",
         "Sixty-plus farms, a chefs' market, eight in the morning until one.",
         "The Saturday market is bigger and worse."],
        placelist([
          place("Wednesday market on Arizona Ave","155–199 Arizona Ave · Wed 8am–1pm · sixty-plus farms and the chefs' market, running since 1981.","food",None,[("Free entry","free")]),
          place("The Strand and the beach path","Flat, fast, and it runs all the way to Venice and beyond.","walk",None,[("Free","free")])])),
      stop("paid","food","Worth paying for","Three rooms and a desk.",
        ["West Side Oyster Club on Ocean Avenue does lobster rolls and chowder bread bowls looking at the Pacific, and it is counter service, which keeps everyone honest.",
         "Hermanito on Broadway is where we have run a long-table dinner — the strongest thing we can say about a room.",
         "The Broad Stage books a small season that is consistently better than it needs to be.",
         "And Blankspaces on Colorado is the answer when you have brought a laptop to the beach and realised your mistake."],
        placelist([
          place("West Side Oyster Club","1355 Ocean Ave · counter service · lobster rolls and chowder bread bowls above the Pacific, from the family behind Rusty's on the pier.","food",None,[("$$","cat")]),
          place("Hermanito","Broadway, Santa Monica · the room we have run a long-table dinner in.","food",None,[("$$$","cat")]),
          place("Blankspaces","929 Colorado Ave · a downtown loft to work from when the beach is a bad idea for your inbox.","shop",None,[("Day pass","cat")]),
          place("The Broad Stage","The season is small and consistently better than it needs to be.","music",None,[("Ticketed","cat")])])),
    ])
    b += oneline("If you only do one thing",
        "The Adelaide stairs at seven, then the Wednesday market on Arizona. Two hours, about four dollars, and you will have seen the real Santa Monica.")
    b += live_block("hood:santa-monica","area:westside",4,"Happening in Santa Monica this week",
        "Refreshed every Sunday night from the same list that runs on the homepage.",
        "Happening on the Westside this week")
    b += sec("From the newsletter","Issues that leaned this way.",
        ['<a href="/archive/2026-07-14-free-in-the-plaza/">Free in the Plaza</a>, '
         '<a href="/archive/2026-08-18-summer-time-fun/">Summer Time Fun All Week</a>, and '
         '<a href="/archive/2026-08-21-tonight-at-sunset/">Tonight at Sunset</a>, written from a beachfront hotel about a mile from the stairs.'])
    b += morelinks([("Venice →","/guides/venice/"),("Culver City →","/guides/culver-city/"),
                    ("Free this weekend →","/guides/free-things-to-do-in-la-this-weekend/")])
    b += FOOT
    w("guides/santa-monica/index.html", b)

# ============================== CULVER CITY ==============================
def build_culver():
    url = "https://haps.club/guides/culver-city/"
    title = "Things to Do in Culver City: Downtown, Ivy Station, Helms"
    desc = ("Culver City in three walkable pieces — the Culver Steps, Ivy Station and the Helms "
            "district — plus what's on this week and where to park once.")
    nodes = [webpage(title,url,desc,"2026-09-07",TODAY), breadcrumb("Culver City",url),
             itemlist("Things to Do in Culver City",url,
                [("The Culver Steps","9300 Culver Blvd",None),("Ivy Station",None,None),
                 ("The Wende Museum","10808 Culver Blvd",None),("Helms Design Center","8745 Washington Blvd",None)])]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; Westside","Culver City in <em>three</em> walkable pieces",
               "Downtown, Ivy Station, Helms — ten minutes apart, best done in that order.")
    b += facts([("Best time","Thursday evening"),("Cost","Free"),
                ("Size","3 districts, 10 min apart"),("Transit","Metro E Line")])
    b += jump([("Downtown","downtown","music"),("Ivy Station","ivy-station","music"),
               ("Helms &amp; the Wende","helms","art"),("This week","this-week","ticket")])
    b += intro(["Culver City is small enough to do properly in an evening, and it is almost always written up as if it were a suburb of Los Angeles rather than a city with its own downtown.",
                "This guide is deliberately short. It names what we have actually covered rather than padding to twenty entries — and it grows as we cover more."])
    b += route([
      stop("downtown","music","Piece one","Downtown, and the Steps.",
        ["The Culver Steps at Town Plaza is the centre of gravity.",
         "In summer it runs a Thursday-night sunset concert series that is free and genuinely well booked — pop, soul and blues, seven to nine.",
         "The plaza works the rest of the year as the place you agree to meet before deciding where to eat."],
        placelist([place("The Culver Steps","Town Plaza, 9300 Culver Blvd · downtown Culver City's Thursday-night habit, and the anchor of the summer sunset concert series.","music",None,[("Free","free")])])),
      stop("ivy-station","music","Piece two","Ivy Station, for the salsa.",
        ["Summer Salsa Nights at Ivy Station is the best free thing Culver City does.",
         "A thirty-minute beginner lesson at half six, then a live band.",
         "No partner needed and nobody is watching you as closely as you think."],
        placelist([place("Ivy Station","Where the Summer Salsa Nights run — a 30-minute beginner lesson, then a live band, no partner required.","music",None,[("Free","free")])])),
      stop("helms","art","Piece three","Helms, and the Wende.",
        ["The Helms Design District is furniture showrooms by day and a surprisingly good openings calendar the rest of the time.",
         "Ten minutes west, the Wende Museum is a Cold War museum in a former armoury, and KCRW turns it into a dance floor with a food night market on summer Fridays.",
         "That combination — free, strange, and actually good — is the most Culver City thing on this page."],
        placelist([
          place("The Wende Museum","10808 Culver Blvd · a Cold War museum that turns into a dance floor for KCRW's summer night markets.","museum",None,[("Free","free"),("RSVP","cat")]),
          place("Helms Design Center","8745 Washington Blvd · the design district's exhibition space — openings are usually free and open to all.","art",None,[("Free","free")])])),
    ])
    b += oneline("If you only do one thing",
        "A Thursday in summer: the Culver Steps at seven for the free concert, then walk five minutes to Ivy Station. Both free, both good, no plan required.")
    b += live_block("hood:culver-city","area:westside",4,"Happening in Culver City this week",
        "Refreshed every Sunday night. Culver City is a small listing, so when it is quiet this widens to the rest of the Westside and says so.",
        "Happening on the Westside this week")
    b += sec(icon("map")+" Parking","Park once at the Steps and walk.",
        ["Downtown Culver City and Ivy Station are a five-minute walk apart and share the same structure parking.",
         "Helms is far enough to drive if you are short on time, close enough to walk if you are not.",
         "The Metro E Line stops at Culver City station, which puts you at Ivy Station without a car at all."])
    b += sec("From the newsletter","Where these came from.",
        ['<a href="/archive/2026-07-21-save-the-dates/">Save the Dates</a>, '
         '<a href="/archive/2026-08-04-the-sound-of-august/">The Sound of August</a>, and '
         '<a href="/archive/2026-06-09-the-garden-party/">The Garden Party</a>.'])
    b += morelinks([("Venice →","/guides/venice/"),("Santa Monica →","/guides/santa-monica/"),
                    ("Free museum days →","/guides/free-museum-days-los-angeles/")])
    b += FOOT
    w("guides/culver-city/index.html", b)

# ============================== MUSEUM DAYS ==============================
ALWAYS = [
 ("The Broad","Free general admission","Timed ticket recommended, walk-ups daily. Some exhibitions carry a separate charge.","https://www.thebroad.org/visit"),
 ("Getty Center","Free","<span class='w'>Timed reservation required.</span> Parking $25, $15 after 3pm, $10 after 6pm, free Sat after 6pm.","https://www.getty.edu/visit/center/"),
 ("Getty Villa","Free","<span class='w'>Timed reservation required.</span> Closed Tuesdays. Parking $25, $15 after 3pm.","https://www.getty.edu/visit/villa/"),
 ("Hammer Museum","Free","No advance reservation needed. Parking $9 for three hours with validation; $9 flat after 5pm weekdays and all day weekends.","https://hammer.ucla.edu/visit"),
 ("MOCA Grand Avenue","Free","Reservations recommended, not required.","https://www.moca.org/visit"),
 ("California Science Center","Free","Permanent galleries free, no reservation. IMAX and special exhibitions ticketed separately.","https://californiasciencecenter.org/visit"),
 ("Griffith Observatory","Free","Planetarium is ticketed, $12 adult — <span class='w'>sold only at the Observatory, same day.</span>","https://griffithobservatory.lacity.gov/visit/"),
 ("Fowler Museum at UCLA","Always free","Closed Mon &amp; Tue. Wed 12–8pm, Thu–Sun 12–5pm. Parking $5/hr, $17 daily max.","https://fowler.ucla.edu/visit/")]

DAYS = [
 ("LACMA","Second Tuesday of the month","Free to all. Also free to LA County residents weekdays after 3pm with ID. Closed Wednesdays.","https://www.lacma.org/tickets"),
 ("Natural History Museum","Weekdays 3–5pm","LA County residents only, <span class='w'>claimed onsite — not bookable online.</span> Closed first Tuesday monthly.","https://nhm.org/free-hours-and-admission"),
 ("The Autry","<span class='w'>First Wednesday</span> of the month","10am–4pm, all exhibitions. Advance registration encouraged; some dates sell out. Free parking.","https://theautry.org/events/free-admission-days"),
 ("The Huntington","First Thursday of the month","<span class='w'>Reservation required.</span> Tickets release the last Thursday at 9am for the following week and sell out. Limit five per household per year.","https://www.huntington.org/plan-your-visit/free-day"),
 ("Skirball Cultural Center","Every Thursday","Free to all, free on-site parking. Same-day reservations cannot be made online.","https://www.skirball.org/visit"),
 ("Norton Simon","First Friday, 4–7pm","Free to all. Also free <em>every</em> day for students with ID and anyone 18 and under. Free parking lot.","https://www.nortonsimon.org/visit/"),
 ("Craft Contemporary","Sundays","<span class='w'>Pay what you wish, not free.</span> $12 general otherwise; under 12 and EBT holders free.","https://www.craftcontemporary.org/visit")]

CLOSED = [
 ("Annenberg Space for Photography","Permanently closed in 2020 — still listed as free on several LA round-ups."),
 ("Japanese American National Museum","Closed for a major renovation. Its free Friday evenings are not running while the building is shut."),
 ("La Brea Tar Pits Museum","Closed for construction. The outdoor areas of Hancock Park remain open and free."),
 ("Geffen Contemporary at MOCA","Temporarily closed for installation. MOCA Grand Avenue is open and free."),
 ("Academy Museum","There is no California-resident free admission. Free for visitors 17 and under, members and EBT cardholders; adults $25.")]

def build_museums():
    url = "https://haps.club/guides/free-museum-days-los-angeles/"
    title = "Free Museum Days in Los Angeles, Checked Monthly"
    desc = ("Which LA museums are always free, which are free on set days, and which \"free\" "
            "days still need a timed reservation. Re-checked against each museum's own site.")
    nodes = [webpage(title,url,desc,"2026-09-07",TODAY), breadcrumb("Free Museum Days",url),
             itemlist("Always-free museums in Los Angeles",url,
                      [(n,None,u) for n,_,_,u in ALWAYS], ordered=False)]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; Citywide","Every free museum day in LA, <em>checked</em>",
               "Re-checked against each museum's own site at the start of every month.")
    b += facts([("Always free","8 museums"),("Free on set days","7 more"),
                ("Commonly wrong","5 listings"),("Re-checked","First Monday monthly")])
    b += jump([("Always free","always","museum"),("Set days","set-days","clock"),
               ("Reservation traps","traps","ticket"),("Get these wrong","wrong","art")])
    b += intro(["Most free-museum lists for Los Angeles are wrong in the same three ways: they include a museum that closed in 2020, they list free days for a museum shut for renovation until 2027, and they get the Autry's free day wrong.",
                "This page is re-checked at the start of every month against each museum's own website, never against another list."])
    b += sec(icon("museum")+" The short answer","Eight museums are free every day they are open.",
        ["The Broad, the Getty Center, the Getty Villa, the Hammer, MOCA Grand Avenue, the California Science Center, Griffith Observatory and the Fowler at UCLA.",
         "Free admission does not mean a free visit: the Getty charges $25 to park and the Hammer charges $9, which is more than some museums charge to get in."],
        anchor="always")
    b += table(["Museum","Admission","The catch"],
               [(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>', a, c) for n,a,c,u in ALWAYS])
    b += sec(icon("clock")+" Free on a set day","Seven more, if you time it.",
        ["The two most commonly misreported are here.",
         "The Autry's free day is the <b>first Wednesday</b>, not the second Tuesday — the single most-repeated error in LA free-museum listings.",
         "And Craft Contemporary's Sunday is pay-what-you-wish rather than free, which matters if you turn up with nothing."],
        anchor="set-days")
    b += table(["Museum","When it's free","The catch"],
               [(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>', d, c) for n,d,c,u in DAYS])
    b += oneline("The trap that ruins most free museum days",
        "Both Getty sites require a timed reservation. Not recommended — required. Turning up without one is the most common way a free Getty day fails.")
    b += sec(icon("ticket")+" The reservation traps","Free does not mean walk in.",
        ["<b>The Huntington's free day is the hardest ticket in the city.</b> Tickets release the last Thursday of each month at 9am for the following week, there is a virtual waiting room, they sell out, and you are limited to five per household per year.",
         "<b>The Natural History Museum's free hours are claimed onsite.</b> You cannot book the 3–5pm resident window online.",
         "<b>Skirball's free Thursday cannot be reserved same-day online.</b> Walk-ups are welcome but only a reservation guarantees entry.",
         "<b>Griffith Observatory's planetarium tickets are same-day and in-person only.</b> The building is free, the show is not, and you cannot plan it from home."],
        anchor="traps")
    b += sec(icon("art")+" Do not believe the old lists","Five things other guides still get wrong.",
        ["Every one of these appears on at least one LA free-museum round-up that is currently ranking."],
        anchor="wrong")
    b += placelist([place(n, d, "museum", None, [("Check first","cat")]) for n, d in CLOSED])
    b += sec("What we could not verify","Left off on purpose.",
        ["The Petersen Automotive Museum lists three different prices across three of its own pages, so we are not printing one — and it has no free-admission day.",
         "Descanso Gardens' Free Tuesday appears to have ended, but nothing on their site says so outright, so we are not claiming either way.",
         "The county-wide Museums Free-For-All is an annual one-day event rather than a standing programme, so it is not listed here.",
         'If you spot something here that has changed, <a href="/about#tip">tell us</a> and it gets fixed in the next monthly pass.'])
    b += morelinks([("Free this weekend →","/guides/free-things-to-do-in-la-this-weekend/"),
                    ("Venice →","/guides/venice/"),("Santa Monica →","/guides/santa-monica/")])
    b += FOOT
    w("guides/free-museum-days-los-angeles/index.html", b)

# ============================== FREE WEEKEND ==============================
def build_freeweekend():
    url = "https://haps.club/guides/free-things-to-do-in-la-this-weekend/"
    title = "Free Things to Do in LA This Weekend"
    desc = ("A short, checked list of free things happening in Los Angeles this weekend — "
            "updated every Sunday night. Nothing expired, nothing padded.")
    nodes = [webpage(title,url,desc,"2026-09-07",TODAY), breadcrumb("Free This Weekend",url),
             itemlist("Free things to do in Los Angeles every weekend",url,
                [("Griffith Observatory",None,"https://griffithobservatory.lacity.gov/visit/"),
                 ("The Venice Canals",None,"https://www.venicecanals.org/"),
                 ("Annenberg Community Beach House",None,"https://annenbergbeachhouse.com/"),
                 ("Smorgasburg LA","777 S Alameda St",None)], ordered=False)]
    b = head(title, desc, url, ld(nodes))
    b += ghero("Los Angeles &middot; Citywide","Free things to do in LA <em>this weekend</em>",
               "Updated every Sunday night. Nothing expired, nothing padded.")
    b += facts([("Updated","Every Sunday 9pm"),("Cost","$0"),
                ("Always free","8 museums"),("Watch out for","Parking")])
    b += jump([("This weekend","this-week","ticket"),("Free every weekend","evergreen","park"),
               ("If you time it","timed","clock"),("What free leaves out","costs","map")])
    b += intro(["Most \"free things to do in LA\" pages are a hundred entries long and a third of them closed.",
                "This one is short on purpose. The top block is what is actually on this weekend; everything under it is free every weekend of the year, which is the part worth bookmarking."])
    b += live_block("tags:free","","8","On this weekend",
        "Friday to Sunday. Anything past its end time is removed automatically, so this list is never padded with things that already happened.")
    b += sec(icon("park")+" Free every weekend","The list that does not change.",
        ["These are free all year and they are the reason you never actually need a plan in this city.",
         "Museums first, because the free ones in LA are genuinely world-class and people still assume they cost money."],
        anchor="evergreen")
    b += placelist([
      place("Griffith Observatory","Free admission, any day. The planetarium is ticketed and same-day only.","museum","https://griffithobservatory.lacity.gov/visit/",[("Free","free")]),
      place("The Broad, the Hammer, MOCA Grand and the Fowler","Free every day they are open. The Getty is free too — but book the timed ticket.","museum","/guides/free-museum-days-los-angeles/",[("Free","free")]),
      place("The Venice Canals","A mile and a half of bridges most LA natives have never walked.","walk","https://www.venicecanals.org/",[("Free","free")]),
      place("The Santa Monica stairs","Adelaide Dr &amp; 4th St. Street parking.","walk","/guides/santa-monica/",[("Free","free")]),
      place("Annenberg Community Beach House","Courtyard, splash pad and beach courts. Parking fills by 11am.","beach","https://annenbergbeachhouse.com/",[("Free","free")]),
      place("Venice Beach Recreation Center","Ocean Front Walk. Paddle tennis, pickleball and volleyball on the sand.","beach","/guides/venice/",[("Free","free")]),
      place("Smorgasburg LA","ROW DTLA, 777 S Alameda St · Sundays 10am–4pm. Free entry, then go hungry.","food",None,[("Free entry","free")]),
      place("The Strand","Flat and fast from Santa Monica south, on foot, bike or skates.","walk",None,[("Free","free")])])
    b += sec(icon("clock")+" Free if you time it right","Monthly and seasonal, worth a calendar reminder.",
        ["Each of these is free but only lands on certain days.",
         "First Friday and second Thursday between them cover most of a month."],
        anchor="timed")
    b += placelist([
      place("First Fridays on Abbot Kinney","First Friday, 5–9:30pm. Shops open late, food trucks on the block.","shop","/guides/venice/",[("Free","free"),("Monthly","cat")]),
      place("Downtown LA Art Walk","Second Thursday of the month. Galleries and pop-ups across downtown.","art",None,[("Free","free"),("Monthly","cat")]),
      place("Grand Performances at California Plaza","350 S Grand Ave, DTLA. A full season of free outdoor concerts in downtown's prettiest water-court plaza.","music",None,[("Free","free"),("RSVP","cat")]),
      place("The Culver Steps summer concerts","Town Plaza, 9300 Culver Blvd. Thursdays in summer.","music","/guides/culver-city/",[("Free","free"),("Seasonal","cat")]),
      place("Summer Salsa Nights at Ivy Station","Culver City. Beginner lesson at 6:30, then a live band.","music","/guides/culver-city/",[("Free","free"),("Seasonal","cat")])])
    b += oneline("What free actually costs",
        "Parking. The Getty is free and charges $25 to park; the Hammer is free and charges $9; the Annenberg fills its lot by eleven. Park once, walk more than you meant to, go early.")
    b += sec(icon("map")+" What free leaves out","The costs nobody lists.",
        ["Beach lots on a summer weekend will cost you more than dinner.",
         "The workaround is the same every time: park once, walk more than you meant to, and go early."],
        anchor="costs")
    b += sec("From the newsletter","Where these came from.",
        ['<a href="/archive/2026-07-14-free-in-the-plaza/">Free in the Plaza</a>, '
         '<a href="/archive/2026-08-18-summer-time-fun/">Summer Time Fun All Week</a>, and '
         '<a href="/archive/2026-07-07-downtown-nights-westside-days/">Downtown Nights, Westside Days</a>.'])
    b += morelinks([("Free museum days →","/guides/free-museum-days-los-angeles/"),
                    ("Venice →","/guides/venice/"),("Santa Monica →","/guides/santa-monica/")])
    b += FOOT
    w("guides/free-things-to-do-in-la-this-weekend/index.html", b)

# ============================== GUIDES INDEX ==============================
GUIDES = [
 ("/guides/venice/","walk","Westside · walking guide","Things to Do in Venice, CA",
  "One day on foot west of Lincoln — Gjusta, the canals, Abbot Kinney top to bottom, and four dinners in order of difficulty."),
 ("/guides/santa-monica/","beach","Westside · mostly free","Free Things to Do in Santa Monica",
  "The stairs, the Wednesday market and the beach house nobody realises is public — plus the few rooms worth paying for."),
 ("/guides/culver-city/","music","Westside · three districts","Things to Do in Culver City",
  "Downtown, Ivy Station and Helms, ten minutes apart and best done in that order. Park once and walk."),
 ("/guides/free-museum-days-los-angeles/","museum","Citywide · checked monthly","Free Museum Days in Los Angeles",
  "Eight museums are free every day, seven more on set days, and five that other lists still get wrong."),
 ("/guides/free-things-to-do-in-la-this-weekend/","park","Citywide · updated Sundays","Free Things to Do in LA This Weekend",
  "What's actually free this weekend, rebuilt every Sunday night — plus everything that's free every weekend of the year."),
]

def build_index():
    url = "https://haps.club/guides/"
    title = "Guides to Los Angeles — Haps Club"
    desc = ("Evergreen guides to LA neighbourhoods and to what's free — hand-written, and "
            "refreshed every week with what's actually on.")
    nodes = [{"@type":"CollectionPage","@id":url+"#page","name":title,"url":url,"description":desc,
              "inLanguage":"en-US","dateModified":TODAY,
              "isPartOf":{"@type":"WebSite","name":"Haps Club","url":"https://haps.club/"},
              "publisher":{"@type":"Organization","name":"Haps Club","url":"https://haps.club/"}},
             {"@type":"BreadcrumbList","itemListElement":[
               {"@type":"ListItem","position":1,"name":"Home","item":"https://haps.club/"},
               {"@type":"ListItem","position":2,"name":"Guides","item":url}]},
             {"@type":"ItemList","itemListElement":[
               {"@type":"ListItem","position":i,"url":"https://haps.club"+h,"name":t}
               for i,(h,_,_,t,_) in enumerate(GUIDES,1)]}]
    b = head(title, desc, url, ld(nodes), og_type="website")
    b += ghero("Los Angeles &middot; Haps Club","Guides to Los Angeles,<br>by someone who <em>goes</em>",
               "Written once, kept current every week.")
    b += facts([("Coverage","Westside &amp; citywide"),("Refreshed","Every Sunday"),
                ("Venues named","All from past issues"),("Cost","Free, no signup")])
    b += intro(["The homepage tells you what is on this week. These are the pages that stay useful after the week ends — neighbourhood walks, and the honest version of what is free in this city.",
                "Every place named here has appeared in a Haps Club issue. Each guide refreshes every Sunday night with what is actually on."])
    b += '<div class="glist">\n'
    for href, cat, meta, h2, d in GUIDES:
        b += (f'  <a class="gcard cat-{cat}" href="{href}">\n'
              f'    <div class="gtop"><span class="chip-i">{icon(ICON_FOR[cat])}</span>'
              f'<span class="kick">{meta}</span></div>\n'
              f'    <h2>{h2}</h2>\n    <p>{d}</p>\n'
              f'    <span class="rd">Read the guide {icon("go","")}</span>\n  </a>\n')
    b += '</div>\n'
    b += oneline("Why there are a handful and not fifty",
        "A guide goes up when we have walked enough of a neighbourhood to have a real opinion about the order you should do it in. Anything less than that is padding, and the internet has plenty.")
    b += FOOT
    w("guides/index.html", b)

# ============================== DRAFTS ==============================
def build_draft(slug, name, title, dek, note, sources):
    url = f"https://haps.club/guides/{slug}/"
    desc = f"Draft — {name} guide, not yet published."
    b = head(f"DRAFT · {title}", desc, url, ld([webpage(title,url,desc,TODAY,TODAY)]),
             robots="noindex,nofollow")
    b += ghero("Draft &middot; not linked, not indexed", title, dek, art=False)
    b += intro(["<b>This page is a draft.</b> It carries <code>noindex,nofollow</code>, it is not in the sitemap, and nothing links to it.", note])
    b += sec(icon("map")+" What the archive already has", "Verified venues, from your own issues.", sources)
    b += sec("What is still needed","Fill these before publishing.",
        ["Morning: one coffee and one walk worth naming.",
         "Afternoon: two or three shops, galleries or rooms.",
         "Dinner: three tables at three price points.",
         "After dinner: one bar and one room with music.",
         "Then delete the noindex, add the page to sitemap.xml and llms.txt, add a card to /guides/, and cross-link it from the sibling guides."])
    b += live_block(f"hood:{slug}","area:eastside",4,f"Happening in {name} this week",
        "Live block is already wired — it fills on the next build once events carry the hood field.")
    b += FOOT
    w(f"guides/_drafts/{slug}/index.html", b)

def build_drafts():
    build_draft("highland-park","Highland Park","Things to Do in Highland Park",
      "Held back: one verified venue is not a guide.",
      "The archive has one Highland Park venue across the whole run of issues, so writing this now would mean inventing the rest. It is also the softest target on the keyword list, which makes it worth walking properly rather than faking.",
      ['<b>Garibaldina Society</b> — 4533 N Figueroa St. The oldest Italian society in America, founded in Highland Park in 1877, still running monthly pasta nights in its time-capsule hall. From <a href="/archive/2026-06-09-the-garden-party/">The Garden Party</a>.',
       "That is the complete list. Everything else on this page would be guesswork."])
    build_draft("silver-lake","Silver Lake","Things to Do in Silver Lake",
      "Held back: one verified venue is not a guide.",
      "One venue across the whole run of issues. Nobody is seriously defending this neighbourhood in search, so it stays winnable — but it needs a real week of walking first.",
      ['<b>Amiguita</b> — Afro-Caribbean from chef Alejandro Eusebio, a Top Chef alum. Mon–Sat 5–10pm, and walk-ins are still possible most nights, which is rare on that block. From <a href="/archive/2026-05-12-date-night-la/">Date Night LA</a>.',
       "Sqirl appears in the same issue but sits in Virgil Village rather than Silver Lake proper, so it is not counted here."])

if __name__ == "__main__":
    print("Building guides v2 →", os.path.abspath(OUT))
    build_venice(); build_sm(); build_culver(); build_museums(); build_freeweekend()
    build_index(); build_drafts()
    print("done")
