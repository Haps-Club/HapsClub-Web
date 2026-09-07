#!/usr/bin/env python3
"""
retrofit_archive_links.py — turn 19 dead-end archive issues into links.

Every archived issue currently links only back to /archive/ and /. Each one is
a page about specific LA neighbourhoods, so each one can feed the matching
guide. This adds one line to the .morelinks block at the foot of each issue,
picking the guide by counting neighbourhood mentions in the issue text.

It also fixes the /about.html -> /about canonical mismatch in the footers.

    python3 scripts/retrofit_archive_links.py --dry-run
    python3 scripts/retrofit_archive_links.py
"""
import argparse, glob, html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GUIDES = [
    ("/guides/venice/",        "the Venice guide",        r"Venice|Abbot Kinney|Gjelina|Gjusta"),
    ("/guides/santa-monica/",  "the Santa Monica guide",  r"Santa Monica"),
    ("/guides/culver-city/",   "the Culver City guide",   r"Culver|Wende|Helms|Ivy Station"),
]
FREE = ("/guides/free-things-to-do-in-la-this-weekend/", "what's free in LA this weekend")
MARKER = "<!-- guide-link -->"

def text_of(doc):
    t = re.sub(r"<script.*?</script>", " ", doc, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", t))

def pick(doc):
    body = text_of(doc)
    scored = sorted(((len(re.findall(p, body, re.I)), h, l) for h, l, p in GUIDES), reverse=True)
    best_n, best_h, best_l = scored[0]
    if best_n >= 3:
        return best_h, best_l
    if len(re.findall(r"\bfree\b", body, re.I)) >= 6:
        return FREE
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, "archive", "*", "index.html")))
    # the archive listing page itself: canonical fix + a link into /guides/
    listing = os.path.join(ROOT, "archive", "index.html")
    if os.path.exists(listing):
        doc = open(listing, encoding="utf-8").read()
        orig = doc
        doc = doc.replace("https://haps.club/about.html", "https://haps.club/about")
        if "/guides/" not in doc:
            doc = doc.replace('<a href="https://haps.club/about">About</a>',
                              '<a href="https://haps.club/guides/">Guides</a>\n  '
                              '<a href="https://haps.club/about">About</a>', 1)
            doc = doc.replace('<div class="alist">',
                '<p class="intro">Looking for something that stays useful after the week ends? '
                'The <a href="/guides/">guides</a> cover Venice, Santa Monica and Culver City, '
                'and what is actually free in LA.</p>\n  <div class="alist">', 1)
        if doc != orig:
            print(("would patch " if a.dry_run else "patched ") + "archive/index.html")
            if not a.dry_run:
                open(listing, "w", encoding="utf-8").write(doc)
    done = skipped = 0
    for f in files:
        doc = open(f, encoding="utf-8").read()
        orig = doc
        # canonical fix, everywhere in the file
        doc = doc.replace("https://haps.club/about.html", "https://haps.club/about")

        if MARKER not in doc:
            href, label = pick(doc)
            if href:
                # two markup shapes exist across the 19 issues
                m = re.search(r'(<div class="morelinks">\s*\n)', doc)
                if m:
                    line = (f'    {MARKER}<a href="{href}">Reading this later? '
                            f'{label[0].upper()}{label[1:]} stays current →</a>\n')
                    doc = doc[:m.end(1)] + line + doc[m.end(1):]
                else:
                    m = re.search(r'<p class="morelinks">.*?(</p>)', doc, re.S)
                    if m:
                        line = (f'{MARKER} &middot; <a href="{href}">'
                                f'{label} (kept current)</a>')
                        doc = doc[:m.start(1)] + line + doc[m.start(1):]
                    else:
                        skipped += 1
            else:
                skipped += 1

        if doc != orig:
            done += 1
            print(("would patch " if a.dry_run else "patched ") + os.path.relpath(f, ROOT)
                  + ("" if MARKER in doc else "  (links unchanged, canonical only)"))
            if not a.dry_run:
                open(f, "w", encoding="utf-8").write(doc)

    print(f"\n{done} issue(s) changed, {skipped} with no clear guide match, "
          f"{len(files)} total.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
