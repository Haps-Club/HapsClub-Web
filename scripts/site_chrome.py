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

import datetime
import hashlib
import html
import os

SITE = "https://haps.club"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def file_hash(path):
    """First 8 hex chars of the file's md5, the site's cache-busting version."""
    try:
        return hashlib.md5(open(path, "rb").read()).hexdigest()[:8]
    except OSError:
        return "0"


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


def fonts_html():
    """Preconnect + ONE stylesheet link for the site fonts, placed in <head> before the CSS.
    (An @import inside a stylesheet makes the browser fetch fonts only after the CSS arrives.)"""
    return ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link rel="stylesheet" href="{FONTS_HREF}">')


def chrome_css():
    return css_link("chrome.css")


def page_css():
    """The one stylesheet every interior page loads after chrome.css."""
    return css_link("site.css")

LOGO_PATH = "/assets/img/haps-logo.svg"          # self-hosted: no third-party request on every page
LOGO = "https://haps.club" + LOGO_PATH           # absolute form, for JSON-LD and Open Graph
FONTS_HREF = ("https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800;900"
              "&family=IBM+Plex+Mono:wght@400;500&display=swap")
CAL = ("https://calendar.google.com/calendar/embed?src="
       "c_ea45ead7ce1909f199c95778b5b7afd9d1a9f9c9751f911bf3c672f267dc4384"
       "%40group.calendar.google.com")
IG = "https://instagram.com/thehapsclub/"

# The logo SVG has a square viewBox (0 0 1100 1100). Declaring 112x28 told the
# browser the wrong aspect ratio and cost a layout shift on every page.
LOGO_W = LOGO_H = 84

# (label, href, opens_in_new_tab)
NAV_ITEMS = [
    ("This week", "/#list",    False),
    ("Ask Haps",  "/ask/",     False),
    ("Calendar",  CAL,         True),
    ("Guides",    "/guides/",  False),
    ("Archive",   "/archive/", False),
    ("Dinners",   "/dinners/", False),
    ("About",     "/about",    False),
]

FOOTER_COLS = [
    ("Read", [("This week", "/#list", False),
              ("Calendar", CAL, True),
              ("Guides", "/guides/", False),
              ("Archive", "/archive/", False),
              ("Sitemap", "/sitemap", False)]),
    ("Join", [("Subscribe", "/subscribe", False),
              ("Dinners", "/dinners/", False),
              ("Instagram", IG, True),
              ("Submit a tip", "/about#tip", False)]),
    ("More", [("About", "/about", False),
              ("Partner with us", "/partners", False),
              ("Privacy", "/privacy", False),
              ("Contact", "mailto:michael@haps.club", False)]),
]

TAGLINE = "Everything worth leaving the house for, in Los Angeles."
COPYRIGHT = "&copy; %d Haps Club &middot; Made by hand in Los Angeles" % datetime.date.today().year


def _href(h, absolute):
    """Site-relative links stay relative on the homepage and go absolute
    everywhere else, so one nav definition works at any directory depth."""
    if h.startswith(("http", "mailto:")):
        return h
    if not absolute:
        return h if h != "/#list" else "#list"
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
        f'<img class="logo" src="{_href(LOGO_PATH, absolute)}" alt="Haps Club" '
        f'width="{LOGO_W}" height="{LOGO_H}"></a>'
        f'<input class="navtog" type="checkbox" id="navtog" aria-hidden="true" tabindex="-1">'
        f'<nav>{links}</nav>'
        f'<a class="navcta" href="{sub}">Subscribe</a>'
        f'<label class="burger" for="navtog" aria-label="Open menu">'
        f'<span></span><span></span><span></span></label>'
        f'</div></header>'
    )


def sponsors(sp=None, label="Sponsored by", cls="blk"):
    """The "Sponsored by" block that sits above the footer: the homepage
    (build_home.py, cls="blk") and interior pages (normalize_chrome.py,
    cls="blk spons-wrap") share this one definition. `sp` is the `sponsor`
    object from data/events.json; it fills the Blackbird card."""
    e = html.escape
    name = e(sp["name"]) if sp else "Blackbird"
    link = e(sp["link"]) if sp else "https://app.blackbird.xyz/r/bb-igyo61"
    return f'''<section class="{cls}">
    <div class="head"><div><div class="mono sig">{label}</div></div></div>
    <div class="spons">
      <div class="rv">
        <div class="mono navy">BizColab</div>
        <h3>Six founders. One&nbsp;month.</h3>
        <p>A four-week mastermind for founders and operators, with real accountability and honest&nbsp;feedback.</p>
        <a href="https://bizcolab.com/" target="_blank" rel="noopener">Request a seat &rarr;</a>
      </div>
      <div class="rv">
        <div class="mono purple">{name}</div>
        <h3>Get rewarded for eating&nbsp;out</h3>
        <p>Earn $FLY at restaurants around LA. Code <b>bb-igyo61</b> gets you $20 to&nbsp;start.</p>
        <a href="{link}" target="_blank" rel="noopener">Claim it &rarr;</a>
      </div>
    </div>
  </section>'''


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
