#!/usr/bin/env python3
"""Apply Design F to every interior page (one-time migration, 2026-11-01).

- links /assets/pages-f.css after the existing stylesheets
- swaps the Kit signup form for the MailerLite embedded form + ml-subscribe.js
- points "This week" links at the new homepage anchor
- adds id="about-michael" on the About page bio (newsletter sign-off target)
Asserts invariants before writing each file. Safe to re-run.
"""
import glob, hashlib, os, re, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML = "https://assets.mailerlite.com/jsonp/2758867/forms/202915208754103515/subscribe"
KIT = "https://app.kit.com/forms/9421017/subscriptions"
def h(p): return hashlib.md5(open(os.path.join(REPO, p), "rb").read()).hexdigest()[:8]
CSS = f'<link rel="stylesheet" href="/assets/pages-f.css?v={h("assets/pages-f.css")}">'
JS = f'<script src="/assets/ml-subscribe.js?v={h("assets/ml-subscribe.js")}" defer></script>'
HIDDEN = '<input type="hidden" name="ml-submit" value="1"><input type="hidden" name="anticsrf" value="true">'

pages = [p for p in glob.glob(os.path.join(REPO, "**/*.html"), recursive=True)
         if not any(s in p for s in ("/social/", "/events/", "/partners/", "/partnership/", "/planner", "/_wip/", "/.git/"))
         and not p.endswith(REPO + "/index.html")]
changed = 0
for p in sorted(pages):
    s = open(p, encoding="utf-8").read(); o = s
    inv = dict(ga=s.count("G-RKY63MK7ND"), ld=s.count("application/ld+json"), forms=s.count("<form"), style=s.count("<style"))
    if "pages-f.css" not in s:
        last = max(s.rfind('sunset-pages.css'), s.rfind('partners.css'), s.rfind('chrome.css'))
        assert last > 0, p
        end = s.index(">", last) + 1
        s = s[:end] + "\n" + CSS + s[end:]
    s = re.sub(r'<link rel="stylesheet" href="/assets/pages-f\.css\?v=\w+">', CSS, s)
    if KIT in s:
        s = s.replace(KIT, ML).replace('name="email_address"', 'name="fields[email]"')
        s = re.sub(r'(<form class="sub-form" action="' + re.escape(ML) + r'" method="post")\s*target="_blank"', r'\1', s)
        s = re.sub(r'(<input[^>]*name="fields\[email\]"[^>]*>)', lambda m: m.group(1) + HIDDEN, s, count=1)
    if ML in s and "ml-subscribe.js" not in s:
        s = s.replace("</body>", JS + "\n</body>")
    s = re.sub(r'<script src="/assets/ml-subscribe\.js\?v=\w+" defer></script>', JS, s)
    s = s.replace('href="https://haps.club/#week"', 'href="https://haps.club/#list"').replace('href="/#week"', 'href="/#list"')
    if p.endswith("/about.html"):
        s = s.replace('<section class="bio">', '<section class="bio" id="about-michael">', 1)
    assert s.count("G-RKY63MK7ND") == inv["ga"] and s.count("application/ld+json") == inv["ld"] and s.count("<form") == inv["forms"] and s.count("<style") == inv["style"], p
    assert s.rstrip().endswith("</html>"), p
    assert "9421017" not in s, p
    if s != o:
        open(p, "w", encoding="utf-8").write(s); changed += 1
print(f"{len(pages)} pages checked, {changed} changed")
