#!/usr/bin/env python3
"""Build ask/index.html — the Ask Haps search page. Rerun after editing copy here."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_chrome as sc
ROOT = sc.REPO
about = open(os.path.join(ROOT, "about.html"), encoding="utf-8").read()
css = re.findall(r'<link rel="stylesheet" href="/assets/[^"]+">', about)

TITLE = "Ask Haps — What to Do in Los Angeles"
DESC = "Ask in plain words and get hand-picked things to do in Los Angeles, pulled from Haps Club picks and the best local newsletters."
CHIPS = ["Something outdoors this Saturday", "Free things this weekend", "Date night on the Westside", "Live music tonight"]

def h(path):
    import hashlib
    return hashlib.md5(open(os.path.join(ROOT, path), "rb").read()).hexdigest()[:8]

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="https://haps.club/ask/">
<meta name="robots" content="noindex,follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Haps Club">
<meta property="og:url" content="https://haps.club/ask/">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="https://haps.club/assets/og-card.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-RKY63MK7ND"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","G-RKY63MK7ND");</script>
{chr(10).join(css)}
<link rel="stylesheet" href="/assets/ask.css?v={h("assets/ask.css")}">
</head>
<body>
{sc.header(active="/ask/")}
<main>
<section class="ask-hero"><div class="ask-wrap">
  <div class="ask-eyebrow">Ask Haps</div>
  <h1>What are you in the mood for?</h1>
  <p class="ask-sub">Ask in plain words. We'll pull from this week's picks and the best Los Angeles newsletters.</p>
  <form class="ask-box" id="ask-form" role="search">
    <input id="ask-q" type="text" maxlength="300" autocomplete="off" placeholder="Try “something outdoors this Saturday”" aria-label="Ask Haps">
    <button type="submit">Ask</button>
  </form>
  <div class="ask-chips">{"".join(f'<button type="button">{c}</button>' for c in CHIPS)}</div>
</div></section>
<section class="ask-res"><div class="ask-wrap" id="ask-res"></div></section>
</main>
{sc.footer()}
<script src="/assets/ask.js?v={h("assets/ask.js")}"></script>
</body>
</html>
'''
os.makedirs(os.path.join(ROOT, "ask"), exist_ok=True)
open(os.path.join(ROOT, "ask", "index.html"), "w", encoding="utf-8").write(html)
print("wrote ask/index.html")
