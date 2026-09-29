#!/usr/bin/env python3
"""
Build issues.json for publish_issue.py from sent Kit broadcasts. Run from the repo root.

    python3 scripts/issues_from_kit.py broadcasts.json > issues.json

broadcasts.json = the `broadcasts` list from KIT_LIST_BROADCASTS (needs id, published_at, content).
Picks every broadcast published AFTER the newest issue already in archive/, dedupes resends
(same <h1>), and extracts intro + sections from the email HTML (pill spans -> lbl, first
non-meta <p> -> tagline, first <p> with &middot; -> meta, rest -> body; divider fragments are
dropped and carried forward as the next section's label; the standing footer block
"Everything worth leaving the house for" and everything after it is dropped).
Prints [] when nothing is new.
"""
import json, re, sys, html, os, datetime

def txt(h): return html.unescape(re.sub('<[^>]+>', '', h)).strip()
def clean(h):
    h = re.sub(r'\s+', ' ', h)
    h = re.sub(r'<(?!/?(a|strong|em|b|i|br)\b)[^>]+>', '', h)
    h = re.sub(r'<(strong|em|b|i)\b[^>]*>', r'<\1>', h)
    h = re.sub(r'<a\b[^>]*?(href="[^"]*")[^>]*>', r'<a \1>', h)
    return h.strip()
def spans(p): return ' · '.join(txt(s) for s in re.findall(r'<span[^>]*>(.*?)</span>', p, re.S))
def divider(h): t = txt(h); return len(t) < 50 and '.' not in t and '<a' not in h
def e(s): return html.escape(s, quote=False)
def slugify(s): return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower().replace("'", '').replace('’', ''))).strip('-')

def parse(c):
    m = re.search(r'<div[^>]*display:none[^>]*>.*?</div>\s*<div[^>]*>(.*?)</div>', c, re.S)
    dek = txt(m.group(1)) if m else ''
    c = re.sub(r'<div[^>]*display:none.*?</div>', '', c, flags=re.S)
    parts = re.split(r'(?=<h2\b)', c)
    h1m = re.search(r'<h1[^>]*>(.*?)</h1>', parts[0], re.S)
    if not h1m: return None
    h1 = txt(h1m.group(1)).replace('\xa0', ' ')
    intro, lbl = [], None
    for m in re.finditer(r'<p\b[^>]*>(.*?)</p>', parts[0][parts[0].find('</h1>'):], re.S):
        p = m.group(1)
        if '<span' in p: lbl = spans(p); continue
        p = clean(p)
        if '{{' in p:
            p = re.sub(r'^Hi \{\{[^}]*\}\}\s*(&mdash;|—|,)?\s*', '', p)
            if '{{' in p: continue
            p = p[:1].upper() + p[1:]
        if p: intro.append(p)
    secs, carry = [], None
    for seg in parts[1:]:
        h2 = txt(re.search(r'<h2[^>]*>(.*?)</h2>', seg, re.S).group(1))
        if h2.startswith('Everything worth leaving'): break
        rest = seg[seg.find('</h2>'):]
        items, nxt = [], None
        for m in re.finditer(r'<p\b[^>]*>(.*?)</p>|<td[^>]*>\s*(<a\b[^>]*>.*?</a>)\s*</td>', rest, re.S):
            if m.group(1) is not None:
                if '<span' in m.group(1): nxt = spans(m.group(1)); break
                items.append(clean(m.group(1)))
            else: items.append(clean(m.group(2)))
        items = [i for i in items if i and not txt(i).startswith('—') and '{{' not in i]
        popped = None
        while items:
            if divider(items[-1]): popped = txt(items.pop()); continue
            if len(items) >= 2 and divider(items[-2]) and len(txt(items[-1])) < 70:
                items.pop(); popped = txt(items.pop()); continue
            break
        L = (lbl or carry or 'Haps pick').replace('♥', '').strip()
        carry = popped; lbl = nxt
        tag = meta = ''
        if items and '&middot;' not in items[0] and '·' not in items[0]: tag = items.pop(0)
        if items and ('&middot;' in items[0] or '·' in items[0]): meta = items.pop(0)
        secs.append(dict(lbl=e(L), h2=e(h2), tagline=tag, meta=meta, body=items))
    return h1, dek, intro, secs

def main(path):
    bs = json.load(open(path))
    done = sorted(d[:10] for d in os.listdir('archive') if re.match(r'\d{4}-\d\d-\d\d-', d))
    last = done[-1] if done else '0000-00-00'
    seen, out = set(), []
    for b in sorted(bs, key=lambda b: b.get('published_at') or ''):
        pa = b.get('published_at')
        if not pa: continue
        dt = datetime.datetime.fromisoformat(pa.replace('Z', '+00:00')) - datetime.timedelta(hours=7)
        date = dt.strftime('%Y-%m-%d')
        if date <= last: continue
        r = parse(b.get('content') or '')
        if not r or not r[3]: continue
        h1, dek, intro, secs = r
        if h1 in seen: continue
        seen.add(h1)
        if any(x.endswith(slugify(h1)) for x in os.listdir('archive')): continue
        out.append(dict(date=date, slug=slugify(h1), title=e(h1),
                        pretty=dt.strftime('%A, %B ') + str(dt.day) + dt.strftime(', %Y'),
                        adate=dt.strftime('%b ') + str(dt.day) + dt.strftime(', %Y'),
                        dek=e(dek or txt(intro[0]) if intro else dek), intro=intro, sections=secs))
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main(sys.argv[1])
