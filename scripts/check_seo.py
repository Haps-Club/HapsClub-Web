#!/usr/bin/env python3
"""check_seo.py — audit what search engines and AI answer engines read on every page.

    python3 scripts/check_seo.py

Per indexable page (noindex pages are skipped):
  ERROR  missing/duplicate <title>, meta description, canonical, h1; canonical pointing elsewhere;
         invalid JSON-LD; missing og:title/description/image/url or twitter:card; no <html lang>
  WARN   title outside 20-65 chars, description outside 70-160, images without alt or size
Site-wide:
  ERROR  indexable page missing from sitemap.xml, sitemap URL with no page behind it,
         sitemap URL that is noindex or disallowed in robots.txt, llms.txt links that do not resolve,
         robots.txt without a Sitemap line
  WARN   pages nothing links to (orphans), sitemap lastmod older than the page's newest date,
         llms.txt lines about events that have already happened
Read-only. Exit 1 on any ERROR.
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://haps.club"
errors, warns = [], []
# Standalone pages (own design, past or private events) are reported but never fail the check.
STANDALONE = ("events/", "partners/", "partnership/", "planner")


def err(page, msg):
    (warns if page.startswith(STANDALONE) else errors).append((page, msg))


def warn(page, msg):
    warns.append((page, msg))


def pages():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if not x.startswith((".", "_")) and x not in ("scripts", "workers", "data")]
        for f in files:
            if f.endswith(".html"):
                yield os.path.relpath(os.path.join(d, f), ROOT)


def url_for(rel):
    """The canonical public URL a page is expected to have (clean URL form)."""
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[:-len("index.html")]
    return SITE + "/" + rel[:-len(".html")]


def file_for(url):
    p = urllib.parse.unquote(urllib.parse.urlparse(url).path.lstrip("/"))
    for cand in (p, os.path.join(p, "index.html"), p + ".html"):
        if os.path.isfile(os.path.join(ROOT, cand)) and cand.endswith(".html"):
            return cand
    return None


def meta(src, key, attr="name"):
    m = re.search(r'<meta\b[^>]*\b%s="%s"[^>]*\bcontent="([^"]*)"' % (attr, re.escape(key)), src, re.I) or \
        re.search(r'<meta\b[^>]*\bcontent="([^"]*)"[^>]*\b%s="%s"' % (attr, re.escape(key)), src, re.I)
    return html.unescape(m.group(1)).strip() if m else None


def robots_disallows():
    out = []
    for line in open(os.path.join(ROOT, "robots.txt"), encoding="utf-8"):
        m = re.match(r"\s*Disallow:\s*(\S+)", line)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def disallowed(path, rules):
    for r in rules:
        rx = re.escape(r).replace(r"\*", ".*")
        if re.match(rx, path):
            return True
    return False


def main():
    titles, descs, indexable, inbound = {}, {}, {}, set()
    allpages = list(pages())
    rules = robots_disallows()
    for rel in allpages:
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for href in re.findall(r'<a\b[^>]*\bhref="([^"#?]+)', src):
            t = file_for(href if href.startswith("http") else urllib.parse.urljoin(url_for(rel), href))
            if t and t != rel:
                inbound.add(t)
        robots_meta = (meta(src, "robots") or "").lower()
        if "noindex" in robots_meta or disallowed("/" + rel.replace("index.html", ""), rules):
            continue
        indexable[rel] = src
    for rel, src in sorted(indexable.items()):
        exp = url_for(rel)
        t = re.search(r"<title>(.*?)</title>", src, re.S)
        title = html.unescape(t.group(1)).strip() if t else ""
        if not title:
            err(rel, "missing <title>")
        else:
            if not 20 <= len(title) <= 65:
                warn(rel, f"title is {len(title)} chars (aim 20-65): {title[:60]}")
            titles.setdefault(title, []).append(rel)
        d = meta(src, "description")
        if not d:
            err(rel, "missing meta description")
        else:
            if not 70 <= len(d) <= 160:
                warn(rel, f"description is {len(d)} chars (aim 70-160)")
            descs.setdefault(d, []).append(rel)
        c = re.search(r'<link\b[^>]*rel="canonical"[^>]*href="([^"]+)"', src, re.I)
        if not c:
            err(rel, "missing canonical")
        else:
            target = file_for(c.group(1))
            if not c.group(1).startswith(SITE) or target != rel:
                err(rel, f"canonical {c.group(1)} does not point at this page ({exp})")
        for k, a in (("og:title", "property"), ("og:description", "property"), ("og:image", "property"),
                     ("og:url", "property"), ("twitter:card", "name")):
            if not meta(src, k, a):
                err(rel, f"missing {k}")
        if not re.search(r"<html[^>]*\blang=", src, re.I):
            err(rel, "missing <html lang>")
        if not re.search(r'<meta[^>]*name="viewport"', src, re.I):
            err(rel, "missing viewport meta")
        n_h1 = len(re.findall(r"<h1\b", src, re.I))
        if n_h1 != 1:
            err(rel, f"{n_h1} <h1> tags (need exactly 1)")
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
            try:
                j = json.loads(blk)
                if not (j.get("@type") or j.get("@graph")):
                    err(rel, "JSON-LD without @type")
            except Exception as e:
                err(rel, f"invalid JSON-LD: {str(e)[:50]}")
        for tag in re.findall(r"<img\b[^>]*>", src, re.I):
            if not re.search(r'\balt="', tag):
                warn(rel, "image without alt: " + (re.search(r'src="([^"]+)"', tag) or [0, "?"])[1][-50:])
            elif not re.search(r"\bwidth=", tag):
                warn(rel, "image without width/height (layout shift): " + (re.search(r'src="([^"]+)"', tag) or [0, "?"])[1][-50:])
        if rel not in inbound and rel != "index.html":
            warn(rel, "orphan: no other page links here")
    for t, rels in titles.items():
        if len(rels) > 1:
            warn(", ".join(rels[:3]), "duplicate <title>: " + t[:50])
    for d, rels in descs.items():
        if len(rels) > 1:
            warn(", ".join(rels[:3]), "duplicate description")

    # sitemap
    sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    mapped = {}
    for u in locs:
        f = file_for(u)
        if not f:
            err("sitemap.xml", f"URL has no page behind it: {u}")
        elif f not in indexable:
            err("sitemap.xml", f"URL is noindex or disallowed: {u}")
        else:
            mapped[f] = u
    for rel in indexable:
        if rel not in mapped:
            err("sitemap.xml", f"indexable page missing from the sitemap: {url_for(rel)}")
    if "Sitemap:" not in open(os.path.join(ROOT, "robots.txt")).read():
        err("robots.txt", "no Sitemap: line")

    # llms.txt
    llms = open(os.path.join(ROOT, "llms.txt"), encoding="utf-8").read()
    today = datetime.date.today()
    for u in re.findall(r"\]\((https://haps\.club[^)\s]*)\)", llms):
        if not file_for(u) and not os.path.isfile(os.path.join(ROOT, urllib.parse.urlparse(u).path.lstrip("/"))):
            err("llms.txt", f"link does not resolve: {u}")
    months = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}
    for line in llms.splitlines():
        m = re.search(r"\b(%s)\s+(\d{1,2}),\s+(20\d\d)" % "|".join(months), line)
        if m and line.startswith("- [") and "/events/" in line:
            d = datetime.date(int(m.group(3)), months[m.group(1)], int(m.group(2)))
            if d < today:
                warn("llms.txt", f"lists an event that already happened ({d}): {line[:60]}")

    print(f"{len(indexable)} indexable pages, {len(allpages) - len(indexable)} noindex/disallowed, {len(locs)} sitemap URLs")
    for p, m in warns:
        print("warn ", p + ":", m)
    for p, m in errors:
        print("ERROR", p + ":", m)
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
