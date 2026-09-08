#!/usr/bin/env python3
"""Rewrite the <header> and <footer> of every page from scripts/site_chrome.py.

Idempotent: it matches whatever header/footer is there and replaces it with the
canonical one, so running it twice changes nothing the second time.

  python3 scripts/normalize_chrome.py            # write
  python3 scripts/normalize_chrome.py --check    # exit 1 if any page is stale

Scope: index.html plus every page that already uses the shared subpage shell
(header class="snav" or class="nav"). The standalone one-offs under events/,
planner/, planner-svetlana/ and partnership/ have their own bespoke chrome and
are deliberately left alone.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_chrome as sc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = ("events", "planner", "planner-svetlana", "partnership", ".git")

HEADER_RE = re.compile(r'<header class="(?:snav|nav)"[^>]*>.*?</header>', re.S)
FOOTER_RE = re.compile(r'<footer[^>]*>.*?</footer>', re.S)

# Which nav item to mark current, by path prefix. Longest match wins.
ACTIVE = [("guides/", "/guides/"), ("archive/", "/archive/"),
          ("about.html", "/about"), ("subscribe.html", "/subscribe")]


def active_for(rel):
    for prefix, href in ACTIVE:
        if rel.startswith(prefix) or rel == prefix:
            return href
    return ""


def pages():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith("_")]
        for fn in sorted(filenames):
            if fn.endswith(".html"):
                yield os.path.relpath(os.path.join(dirpath, fn), ROOT)


def main(check=False):
    stale, done = [], []
    for rel in pages():
        path = os.path.join(ROOT, rel)
        src = open(path, encoding="utf-8").read()
        if not HEADER_RE.search(src):
            continue                      # bespoke page, not ours
        home = rel == "index.html"
        new = HEADER_RE.sub(
            lambda m: sc.header(active=active_for(rel), absolute=not home,
                                shell="nav" if home else "snav"),
            src, count=1)
        if FOOTER_RE.search(new):
            new = FOOTER_RE.sub(lambda m: sc.footer(absolute=not home),
                                new, count=1)
        if new == src:
            continue
        stale.append(rel)
        if not check:
            open(path, "w", encoding="utf-8").write(new)
            done.append(rel)
    if check:
        if stale:
            print("stale chrome in %d page(s):" % len(stale))
            for r in stale:
                print("  " + r)
            return 1
        print("chrome up to date")
        return 0
    print("rewrote chrome on %d page(s)" % len(done))
    for r in done:
        print("  " + r)
    return 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
