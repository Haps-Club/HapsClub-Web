#!/usr/bin/env python3
"""
Publish one or more sent Haps Club newsletter issues to /archive/, and refresh
every place the site references the archive. Run from the repo root.

    python3 scripts/publish_issue.py issues.json

issues.json is a list of objects:
  {"date":"2026-08-18","slug":"summer-time-fun","title":"Summer Time Fun All Week",
   "pretty":"Tuesday, August 18, 2026","adate":"Aug 18, 2026","dek":"...",
   "intro":["<p html>","..."],
   "sections":[{"lbl":"...","h2":"...","tagline":"...","meta":"...","body":["..."]}]}

Touches, in one pass:
  archive/<date>-<slug>/index.html   (new page, Sunset system)
  archive/index.html                 (.acard first in .alist + ld+json ItemList renumbered)
  sitemap.xml                        (new <url>, archive/ lastmod bumped)
  llms.txt                           (issue line at top of the archive list)
  data/events.json                   ("archive" array = 4 most recent, homepage teaser)
"""
import json, re, sys, html, os

ROOT = os.getcwd()
CAL = ("https://calendar.google.com/calendar/embed?src=c_ea45ead7ce1909f199c95778b5b7afd9d"
       "1a9f9c9751f911bf3c672f267dc4384%40group.calendar.google.com")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} — Haps Club</title>
<meta name="description" content="{dek_attr}">
<link rel="canonical" href="https://haps.club/archive/{date}-{slug}/">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="author" content="Haps Club">
<meta name="theme-color" content="#F5F5F7">
<meta name="geo.region" content="US-CA"><meta name="geo.placename" content="Los Angeles">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Haps Club">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="https://haps.club/archive/{date}-{slug}/">
<meta property="og:title" content="{title_attr} — Haps Club">
<meta property="og:description" content="{dek_attr}">
<meta property="og:image" content="https://res.cloudinary.com/dimlqawuh/image/upload/v1780950616/haps-og-card.png">
<meta property="og:image:width" content="2400"><meta property="og:image:height" content="1260">
<meta property="og:image:alt" content="Haps Club — everything worth leaving the house for in LA, every week.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title_attr} — Haps Club">
<meta name="twitter:description" content="{dek_attr}">
<meta name="twitter:image" content="https://res.cloudinary.com/dimlqawuh/image/upload/v1780950616/haps-og-card.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/sunset-pages.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-RKY63MK7ND"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","G-RKY63MK7ND");</script>
<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="bar"><div class="bar-in">
  <a class="logo" href="/" aria-label="Haps Club home"><img src="https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/haps-club-logo.svg?v=5" alt="Haps Club"></a>
  <a class="back" href="/archive/"><svg class="ic" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>All issues</a>
</div></header>
<main class="wrap">
  <article>
    <div class="eyebrow"><span class="pin">&#9679;</span> {pretty}</div>
    <h1>{title}</h1>
    <div class="dek">{dek}</div>
    <div class="intro">{intro}</div>
{sections}
  </article>
  <div class="cta">
    <h3>Get the next one</h3>
    <p>One email, every Tuesday morning. Free, unsubscribe anytime.</p>
    <a href="/subscribe">Subscribe free <svg class="ic" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
  </div>
  <p class="morelinks">More: <a href="/">this week in LA</a> &middot; <a href="{cal}">the calendar</a> &middot; <a href="/archive/">every issue</a></p>
</main>
<footer>
  <a href="https://haps.club/subscribe">Subscribe</a>
  <a href="https://haps.club/about.html">About</a>
  <a href="https://haps.club/about.html#tip">Submit a tip</a>
  <a href="mailto:michael@haps.club">Contact</a>
  <a href="https://instagram.com/thehapsclub/" target="_blank" rel="noopener">Instagram</a>
  <a href="https://chat.whatsapp.com/CrQFCLOZjYm5eBqsU1vcA5?mode=gi_t" target="_blank" rel="noopener">WhatsApp</a>
  <a href="{cal}" target="_blank" rel="noopener">Calendar</a>
  <a href="https://haps.club/archive/">Archive</a>
  <a href="https://haps.club/sitemap">Sitemap</a>
  <span class="made">&copy; 2026 Haps Club &middot; Made by hand in Los Angeles</span>
</footer>
</body>
</html>
"""

SEC = """    <section class="sec"><div class="lbl">{lbl}</div>
<h2>{h2}</h2>
<div class="body"><p><em>{tagline}</em></p>
<p>{meta}</p>
{body}</div>
</section>
"""

def esc(s):
    return html.escape(re.sub(r'<[^>]+>', '', s), quote=True)

def build(iss):
    ld = json.dumps({"@context":"https://schema.org","@type":"Article",
                     "headline":re.sub(r'<[^>]+>','',iss['title']),
                     "datePublished":iss['date'],"dateModified":iss['date'],
                     "author":{"@type":"Organization","name":"Haps Club"},
                     "publisher":{"@type":"Organization","name":"Haps Club","url":"https://haps.club/"},
                     "mainEntityOfPage":"https://haps.club/archive/%s-%s/"%(iss['date'],iss['slug']),
                     "description":re.sub(r'<[^>]+>','',iss['dek'])}, ensure_ascii=False)
    secs = "".join(SEC.format(lbl=s['lbl'], h2=s['h2'], tagline=s['tagline'],
                              meta=s['meta'] or '&nbsp;',
                              body="".join("<p>%s</p>\n"%p for p in s['body']))
                   for s in iss['sections'])
    return PAGE.format(title=iss['title'], title_attr=esc(iss['title']),
                       dek=iss['dek'], dek_attr=esc(iss['dek']),
                       date=iss['date'], slug=iss['slug'], pretty=iss['pretty'],
                       intro="".join("<p>%s</p>\n"%p for p in iss['intro']),
                       sections=secs, ld=ld, cal=CAL)

def main(path):
    issues = json.load(open(path, encoding='utf-8'))
    issues.sort(key=lambda i: i['date'])          # oldest first, so newest ends up on top
    idx_path = 'archive/index.html'
    idx = open(idx_path, encoding='utf-8').read()
    sm  = open('sitemap.xml', encoding='utf-8').read()
    lms = open('llms.txt', encoding='utf-8').read()
    ev  = json.load(open('data/events.json', encoding='utf-8'))

    for iss in issues:
        url  = "/archive/%s-%s/" % (iss['date'], iss['slug'])
        full = "https://haps.club" + url
        d    = 'archive/%s-%s' % (iss['date'], iss['slug'])
        os.makedirs(d, exist_ok=True)
        open(d + '/index.html', 'w', encoding='utf-8').write(build(iss))

        if 'href="%s"' % url not in idx:          # idempotent
            card = ('      <a class="acard" href="%s">\n'
                    '        <div class="meta">%s &middot; %s</div>\n'
                    '        <h2>%s</h2>\n'
                    '        <div class="d">%s</div>\n'
                    '        <div class="r">Read this issue <svg class="ic" viewBox="0 0 24 24">'
                    '<path d="M5 12h14M13 6l6 6-6 6"/></svg></div>\n'
                    '      </a>\n') % (url, iss['pretty'], iss['title'].lower(),
                                       iss['title'], re.sub(r'<[^>]+>','',iss['dek']))
            m = re.search(r'(<div class="alist"[^>]*>\s*)', idx)
            idx = idx[:m.end()] + card + idx[m.end():]
            # ld+json ItemList: insert at position 1 and renumber
            lm = re.search(r'"itemListElement"\s*:\s*\[', idx)
            if lm:
                item = ('{"@type": "ListItem", "position": 1, "url": "%s", "name": "%s"}, '
                        % (full, re.sub(r'<[^>]+>','',iss['title']).replace('"', '\\"')))
                start = lm.end()
                idx = idx[:start] + item + idx[start:]
                # find the matching close bracket of this array, then renumber inside it
                depth, j = 1, start
                while depth and j < len(idx):
                    if idx[j] == '[': depth += 1
                    elif idx[j] == ']': depth -= 1
                    j += 1
                n = [0]
                def bump(mo):
                    n[0] += 1
                    return '"position": %d' % n[0]
                inner = re.sub(r'"position"\s*:\s*\d+', bump, idx[start:j-1])
                idx = idx[:start] + inner + idx[j-1:]

        if full not in sm:
            sm = sm.replace('</urlset>',
                 '  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq>'
                 '<priority>0.6</priority></url>\n</urlset>' % (full, iss['date']))
        sm = re.sub(r'(<loc>https://haps\.club/archive/</loc><lastmod>)[\d-]+',
                    r'\g<1>' + issues[-1]['date'], sm)

        if full not in lms:
            line = '- [%s](%s): %s\n' % (re.sub(r'<[^>]+>','',iss['title']), full,
                                          re.sub(r'<[^>]+>','',iss['dek']))
            am = re.search(r'^.*archive.*$\n', lms, re.M | re.I)
            lms = (lms[:am.end()] + line + lms[am.end():]) if am else lms + line

    # homepage teaser: rebuild from archive/index.html, which is the source of truth
    cards = re.findall(r'class="acard" href="(/archive/[^"]+)">\s*<div class="meta">(.*?)</div>\s*<h2>(.*?)</h2>', idx, re.S)
    teaser = []
    for href, meta, title in cards[:6]:
        m = re.match(r'\w+day,\s*(\w+)\s+(\d+),\s*(\d{4})', re.sub(r'<[^>]+>','',meta).strip())
        pretty = '%s %s, %s' % (m.group(1)[:3], m.group(2), m.group(3)) if m else re.sub(r'<[^>]+>','',meta).strip()[:14]
        teaser.append({"date": pretty, "title": re.sub(r'<[^>]+>','',title).strip(),
                       "url": "https://haps.club" + href})
    if teaser:
        ev['archive'] = teaser
    open(idx_path,'w',encoding='utf-8').write(idx)
    open('sitemap.xml','w',encoding='utf-8').write(sm)
    open('llms.txt','w',encoding='utf-8').write(lms)
    json.dump(ev, open('data/events.json','w',encoding='utf-8'), indent=1, ensure_ascii=False)
    print('published:', [i['date']+'-'+i['slug'] for i in issues])
    print('homepage teaser now:', [a['title'] for a in ev['archive']])

if __name__ == '__main__':
    main(sys.argv[1])
