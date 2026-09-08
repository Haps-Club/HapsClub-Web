"""Canonical site chrome for haps.club — one header, one footer, every page.

Before this module the homepage and the subpages had drifted: the homepage
nav carried Calendar and Instagram and the subpages did not, and the homepage
had the four-column footer while every subpage had a thin centred link row.

Everything now comes from here:
  * scripts/normalize_chrome.py  rewrites index.html and all 32 subpages
  * scripts/build_guides.py      imports header()/footer() for guides/

So change the nav or the footer HERE, then run both scripts. Never hand-edit
a <header> or <footer> in a page file — the next build will overwrite it.

There is ONE shell on every page: <header class="nav"><div class="navbar">.
The old .snav / .snav-in subpage variant is gone, and so is the duplicated
CSS that went with it -- the header and footer are defined once, in
assets/chrome.css, which normalize_chrome.py links into every page.

DOM order inside .navbar is load-bearing:
    brand, navtog, nav, navcta, burger
The CSS drawer is `.navtog:checked ~ nav`, so nav and burger must both come
AFTER the checkbox, and navcta sits outside nav so Subscribe stays reachable
in the mobile bar instead of being buried in the drawer.
"""

import hashlib
import os

SITE = "https://haps.club"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def css_link(name):
    """A <link> for assets/<name> with a content hash on the end.

    Cloudflare serves the CSS with max-age=14400, so without this a stylesheet
    change keeps being served from the edge for up to four hours -- long enough
    to look like the change never shipped, or worse, to serve one page the new
    CSS and another page the old. The hash changes only when the file does.
    """
    path = os.path.join(REPO, "assets", name)
    try:
        h = hashlib.md5(open(path, "rb").read()).hexdigest()[:8]
    except OSError:
        h = "0"
    return f'<link rel="stylesheet" href="/assets/{name}?v={h}">'


def chrome_css():
    return css_link("chrome.css")

LOGO = ("https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/"
        "haps-club-logo.svg?v=5")
CAL = ("https://calendar.google.com/calendar/embed?src="
       "c_ea45ead7ce1909f199c95778b5b7afd9d1a9f9c9751f911bf3c672f267dc4384"
       "%40group.calendar.google.com")
IG = "https://instagram.com/thehapsclub/"
WA = "https://chat.whatsapp.com/CrQFCLOZjYm5eBqsU1vcA5?mode=gi_t"

# The logo SVG has a square viewBox (0 0 1100 1100). Declaring 112x28 told the
# browser the wrong aspect ratio and cost a layout shift on every page.
LOGO_W = LOGO_H = 84

# (label, href, opens_in_new_tab)
NAV_ITEMS = [
    ("This week", "/#week",    False),
    ("Calendar",  CAL,         True),
    ("Guides",    "/guides/",  False),
    ("Archive",   "/archive/", False),
    ("About",     "/about",    False),
    ("Instagram", IG,          True),
]

FOOTER_COLS = [
    ("Read", [("This week", "/#week", False),
              ("Calendar", CAL, True),
              ("Guides", "/guides/", False),
              ("Archive", "/archive/", False),
              ("Sitemap", "/sitemap", False)]),
    ("Join", [("Subscribe", "/subscribe", False),
              ("WhatsApp", WA, True),
              ("Instagram", IG, True),
              ("Submit a tip", "/about#tip", False)]),
    ("More", [("About", "/about", False),
              ("Contact", "mailto:michael@haps.club", False)]),
]

TAGLINE = "Everything worth leaving the house for, in Los Angeles."
COPYRIGHT = "&copy; 2026 Haps Club &middot; Made by hand in Los Angeles"


def _href(h, absolute):
    """Site-relative links stay relative on the homepage and go absolute
    everywhere else, so one nav definition works at any directory depth."""
    if h.startswith(("http", "mailto:")):
        return h
    if not absolute:
        return h if h != "/#week" else "#week"
    return SITE + h


def header(active="", absolute=True):
    """active: the NAV_ITEMS href to mark as current, e.g. '/guides/'."""
    links = ""
    for label, h, ext in NAV_ITEMS:
        cls = ' class="on"' if active and h == active else ""
        rel = ' target="_blank" rel="noopener"' if ext else ""
        links += f'<a href="{_href(h, absolute)}"{rel}{cls}>{label}</a>'
    sub = _href("/subscribe", absolute)
    return (
        f'<header class="nav"><div class="navbar">'
        f'<a class="brand" href="{_href("/", absolute)}" aria-label="Haps Club home">'
        f'<img class="logo" src="{LOGO}" alt="Haps Club" '
        f'width="{LOGO_W}" height="{LOGO_H}"></a>'
        f'<input class="navtog" type="checkbox" id="navtog" aria-hidden="true" tabindex="-1">'
        f'<nav>{links}</nav>'
        f'<a class="navcta" href="{sub}">Subscribe</a>'
        f'<label class="burger" for="navtog" aria-label="Open menu">'
        f'<span></span><span></span><span></span></label>'
        f'</div></header>'
    )


def footer(absolute=True):
    cols = ""
    for head, items in FOOTER_COLS:
        rows = "".join(
            '\n        <a href="%s"%s>%s</a>' % (
                _href(h, absolute),
                ' target="_blank" rel="noopener"' if ext else "",
                label)
            for label, h, ext in items)
        cols += f'\n      <div><h5>{head}</h5>{rows}\n      </div>'
    return (
        '<footer>\n'
        '  <div class="footin">\n'
        '    <div class="cols">\n'
        '      <div class="fcol-brand">\n'
        '        <div class="fbrand">Haps Club</div>\n'
        f'        <p class="fabout">{TAGLINE}</p>\n'
        '      </div>'
        f'{cols}\n'
        '    </div>\n'
        f'    <div class="fbot">{COPYRIGHT}</div>\n'
        '  </div>\n'
        '</footer>'
    )
