#!/usr/bin/env python3
"""check_links.py — verify every link on the site, and that each one is the right one.

    python3 scripts/check_links.py                 # all pages, all links
    python3 scripts/check_links.py --internal      # local files and #anchors only (fast)
    python3 scripts/check_links.py --json out.json # also write a machine-readable report

Checks
  * internal links resolve to a file, and #anchors exist on the target page
  * external links answer with 2xx (follows redirects, retries once)
  * permanent redirects are reported with the URL to use instead
  * "blocked" (403/429/999, bot walls such as Instagram) is reported separately, not as broken
  * CLAUDE.md rule: no Eater / Infatuation / Yelp links (link the venue's own site)
  * http:// links (should be https://)

Exit code 1 only for broken internal links, dead external links (404/410/5xx/DNS) or rule
violations, so it is safe to run in CI. Read-only.
"""
import concurrent.futures as cf
import html
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://haps.club"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 haps-linkcheck"
BAD_HOSTS = ("eater.com", "theinfatuation.com", "yelp.com")
BLOCKED = {401, 403, 405, 406, 429, 451, 999}
SKIP = re.compile(r"^(mailto:|tel:|javascript:|data:|#$|sms:|\{)")
TAG_RE = re.compile(r'<(a|link|img|script|source|iframe)\b([^>]*)>', re.I)
ATTR_RE = re.compile(r'\b(href|src)="([^"]+)"', re.I)
HINT_RE = re.compile(r'\brel="(?:preconnect|dns-prefetch)"', re.I)
ID_RE = re.compile(r'\bid="([^"]+)"')


def pages():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if not x.startswith((".", "_")) and x != "node_modules"]
        for f in files:
            if f.endswith(".html"):
                yield os.path.relpath(os.path.join(d, f), ROOT)


def local_target(url_path):
    p = urllib.parse.unquote(url_path.lstrip("/"))
    full = os.path.join(ROOT, p)
    for cand in (full, os.path.join(full, "index.html"), full + ".html"):
        if os.path.isfile(cand):
            return cand
    return None


def collect():
    internal, external, ids = [], {}, {}
    for rel in pages():
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
        ids[rel] = set(ID_RE.findall(src))
        base = "/" + os.path.dirname(rel)
        for tag, attrs in TAG_RE.findall(src):
            m = ATTR_RE.search(attrs)
            if not m or HINT_RE.search(attrs):        # preconnect hints are origins, not pages
                continue
            url = html.unescape(m.group(2)).strip()
            if SKIP.match(url):
                continue
            if url.startswith("//"):
                url = "https:" + url
            if url.startswith(SITE):
                url = url[len(SITE):] or "/"
            if re.match(r"^https?://", url):
                external.setdefault(url.split("#")[0], []).append(rel)
            else:
                path, _, frag = url.partition("#")
                path = path.split("?")[0]
                if not path:
                    internal.append((rel, rel, frag))
                    continue
                t = path if path.startswith("/") else os.path.normpath(os.path.join(base, path))
                internal.append((rel, t, frag))
    return internal, external, ids


def check_internal(internal, ids):
    bad = []
    for rel, target, frag in internal:
        if target in ids:                       # same-page anchor
            tf = target
        else:
            t = local_target(target)
            if not t:
                bad.append((rel, target + ("#" + frag if frag else ""), "file not found"))
                continue
            tf = os.path.relpath(t, ROOT)
        if frag and tf in ids and frag not in ids[tf] and frag != "top":
            bad.append((rel, f"{target}#{frag}", "anchor not found"))
    return bad


def fetch(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            return r.status, r.geturl(), None
    except urllib.error.HTTPError as e:
        return e.code, url, None
    except Exception as e:                      # DNS, TLS, timeout
        return 0, url, str(e)[:80]


def curl_fetch(url):
    """Second opinion with curl: this Mac's Python TLS is old and some hosts reject it."""
    try:
        out = subprocess.run(["curl", "-sS", "-L", "-o", "/dev/null", "-m", "25", "-A", UA,
                              "-w", "%{http_code} %{url_effective}", url],
                             capture_output=True, text=True, timeout=40)
        code, _, final = out.stdout.partition(" ")
        return int(code or 0), final or url, (out.stderr.strip()[:80] or None)
    except Exception as e:
        return 0, url, str(e)[:80]


def check_external(url):
    status, final, err = fetch(url)
    if status == 0 or status in BLOCKED or status >= 500:
        s2, f2, e2 = curl_fetch(url)
        if 200 <= s2 < 400 or status == 0:
            status, final, err = s2, f2, e2
    if status in (0, 403, 405, 429, 500, 502, 503) or status >= 500:
        s2, f2, e2 = fetch(url)                 # one retry
        if s2 == 200 or status == 0:
            status, final, err = s2, f2, e2
    moved = None
    if 200 <= status < 300 and final.rstrip("/") != url.rstrip("/"):
        a, b = urllib.parse.urlparse(url), urllib.parse.urlparse(final)
        if (a.netloc.replace("www.", "") != b.netloc.replace("www.", "")
                or a.path.rstrip("/") != b.path.rstrip("/")):
            moved = final
    return {"url": url, "status": status, "final": final, "moved": moved, "error": err}


def main():
    args = sys.argv[1:]
    internal, external, ids = collect()
    bad_internal = check_internal(internal, ids)
    print(f"{len(list(pages()))} pages, {len(internal)} internal links, {len(external)} unique external links")
    for rel, t, why in bad_internal:
        print(f"BROKEN internal  {rel}: {t} ({why})")
    results = []
    if "--internal" not in args:
        with cf.ThreadPoolExecutor(max_workers=12) as ex:
            results = list(ex.map(check_external, sorted(external)))
    def live_pages(u):                         # pages that can still be edited
        return [p for p in external[u] if not p.startswith("archive/20")]
    dead_all = [r for r in results if r["status"] in (404, 410) or r["status"] >= 500 or r["status"] == 0]
    history = [r for r in dead_all if not live_pages(r["url"])]
    dead = [r for r in dead_all if live_pages(r["url"])]
    blocked = [r for r in results if r["status"] in BLOCKED]
    moved = [r for r in results if r["moved"]]
    def bad_host(u):
        host = urllib.parse.urlparse(u).netloc.lower()
        return any(host == h or host.endswith("." + h) for h in BAD_HOSTS)
    rule = [(u, p) for u, p in external.items() if bad_host(u) and live_pages(u)]
    rule_history = [u for u in external if bad_host(u) and not live_pages(u)]
    insecure = [(u, p) for u, p in external.items() if u.startswith("http://")]
    for r in dead:
        print(f"DEAD {r['status'] or 'ERR'}  {r['url']}  {r['error'] or ''}\n        on: {', '.join(external[r['url']][:3])}")
    for u, p in rule:
        print(f"RULE (not the venue's own site)  {u}\n        on: {', '.join(p[:3])}")
    for r in [m for m in moved if live_pages(m["url"])]:
        print(f"MOVED  {r['url']}\n   ->  {r['moved']}\n        on: {', '.join(external[r['url']][:3])}")
    for u, p in insecure:
        print(f"HTTP (use https)  {u}  on: {', '.join(p[:2])}")
    if history or rule_history:
        print(f"HISTORY (only in archived issues, left as sent): {len(history)} dead link(s) to past events, "
              f"{len(rule_history)} link(s) to review sites")
    if blocked:
        print("CANNOT VERIFY (site blocks bots): " + ", ".join(sorted({urllib.parse.urlparse(r['url']).netloc for r in blocked})))
    ok = len(results) - len(dead_all) - len(blocked)
    print(f"\n{ok} ok, {len(moved)} moved, {len(blocked)} unverifiable, {len(dead)} dead, {len(history)} dead in archive, "
          f"{len(bad_internal)} broken internal, {len(rule)} rule violations")
    if "--json" in args:
        out = args[args.index("--json") + 1]
        json.dump({"internal_bad": bad_internal, "results": results,
                   "pages": {u: p for u, p in external.items()}}, open(out, "w"), indent=1)
    sys.exit(1 if (dead or bad_internal or rule) else 0)


if __name__ == "__main__":
    main()
