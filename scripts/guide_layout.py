#!/usr/bin/env python3
"""guide_layout.py — the box-free guide layout (Nov 2026): headline on the page, reading column on
the left aligned with the logo, a quiet "at a glance" + "on this page" column on the right.

    python3 scripts/guide_layout.py            # restyle every guide page in place (idempotent)
    python3 scripts/guide_layout.py --check    # exit 1 if any guide page is not in the new layout

Also imported by build_guides.w(), so a guide rebuilt from its generator comes out in the new
layout. The generators keep emitting the same blocks (ghero, facts, jump, intro, sec, places, ...);
this rearranges them:

  <section class="ghero">            -> stays, full width, no card
  <div class="facts">  + <div class="jump">   -> <aside class="g2-rail">  (glance list + page links)
  everything else except .cta        -> <div class="g2-main">  (the reading column)
  <section class="cta">              -> full width at the bottom

Styles live in assets/site.css under ".g2". Skips guides/_drafts (unpublished).
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_RE = re.compile(r'(<main class="wrap wide)(">\n)(.*?)(</main>)', re.S)


def _block(body, cls):
    """First top-level <section|div class="...cls..."> block (balanced), or ''."""
    m = re.search(r'<(section|div)\b[^>]*class="%s"[^>]*>' % cls, body)
    if not m:
        return ""
    start, tag, depth = m.start(), m.group(1), 0
    for x in re.finditer(r"<(/?)%s\b[^>]*>" % tag, body[start:]):
        depth += -1 if x.group(1) else 1
        if depth == 0:
            return body[start:start + x.end()]
    return ""


def transform(page):
    m = MAIN_RE.search(page)
    if not m or "g2" in m.group(1) or 'class="ghero"' not in m.group(3):
        return page
    body = m.group(3)
    hero, facts, jump, cta = (_block(body, c) for c in ("ghero", "facts", "jump", "cta"))
    rest = body
    for blk in (hero, facts, jump, cta):
        if blk:
            rest = rest.replace(blk, "", 1)
    hero = re.sub(r'<svg class="art".*?</svg>', "", hero, flags=re.S)       # decorative squiggle is retired
    glance = "".join(f"<div><dt>{l}</dt><dd>{v}</dd></div>"
                     for l, v in re.findall(r"<b>(.*?)</b><span>(.*?)</span>", facts, re.S))
    toc = "".join(f'<a href="{h}">{html.unescape(t).strip()}</a>'
                  for h, t in re.findall(r'<a href="(#[^"]+)"[^>]*>.*?</svg>(.*?)</a>', jump, re.S))
    rail = ""
    if glance or toc:
        rail = ('  <aside class="g2-rail">\n'
                + (f'    <dl class="g2-glance">{glance}</dl>\n' if glance else "")
                + (f'    <nav class="g2-toc" aria-label="On this page"><span class="g2-toc-l">On this page</span>{toc}</nav>\n' if toc else "")
                + "  </aside>\n")
    grid_cls = "g2-grid" if rail else "g2-grid g2-solo"
    new = (f'{m.group(1)} g2{m.group(2)}{hero}\n<div class="{grid_cls}">\n{rail}'
           f'  <div class="g2-main">\n{rest.strip()}\n  </div>\n</div>\n{cta}{m.group(4)}')
    return page[:m.start()] + new + page[m.end():]


def guide_pages():
    base = os.path.join(ROOT, "guides")
    for d, dirs, files in os.walk(base):
        dirs[:] = [x for x in dirs if not x.startswith("_")]
        if "index.html" in files:
            yield os.path.join(d, "index.html")


def main():
    check = "--check" in sys.argv
    stale = []
    for p in guide_pages():
        s = open(p, encoding="utf-8").read()
        t = transform(s)
        if t != s:
            stale.append(os.path.relpath(p, ROOT))
            if not check:
                open(p, "w", encoding="utf-8").write(t)
    print(("not in the new layout: " if check else "restyled: ") + (", ".join(stale) or "nothing (all guides current)"))
    sys.exit(1 if (check and stale) else 0)


if __name__ == "__main__":
    main()
