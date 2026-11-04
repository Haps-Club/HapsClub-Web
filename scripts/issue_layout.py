"""Archive issue layout (Nov 2026): callouts first, then compact typed rows.

publish_issue.py calls main_html(iss) for the <main> of every new issue page.
It reads the same issues.json sections as before ({lbl, h2, tagline, meta, body})
and works out the rest:

  * Every label group except the last is a callout. The first callout is the
    lead card (big date, facts); the others are dark side cards.
  * The last group becomes compact rows with an icon per category, split into
    "This weekend"/"This week" and "Coming up" by date.
  * Category comes from keywords in the title/text (music, culture, market,
    outdoors, food). Colors are the site tokens in site.css.
  * A sticky "In this issue" bar links to the callouts and the first row of
    each category.

Styles: the .ix-* rules in assets/site.css. Older issues keep their old
markup and the .sec rules.
"""
import datetime
import html
import re

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
DAYS = "Mon Tue Wed Thu Fri Sat Sun".split()

ICON = {
    "haps": '<path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.6 6.6 19.5l1.2-6L3.3 9.3l6.1-.7z"/>',
    "music": '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>',
    "culture": '<path d="M3 21h18M5 21V10m4 11V10m6 11V10m4 11V10M2 10l10-6 10 6z"/>',
    "market": '<path d="M6 7h12l1 13H5zM9 7a3 3 0 0 1 6 0"/>',
    "outdoors": '<path d="M3 20l6-10 4 6 3-4 5 8z"/><circle cx="17" cy="6" r="2"/>',
    "food": '<path d="M7 3v8a2 2 0 0 0 4 0V3M9 11v10M17 3c-2 0-3 2-3 6s1 4 3 4v8"/>',
}
LABEL = {"haps": "Haps event", "music": "Music", "culture": "Culture",
         "market": "Market", "outdoors": "Outdoors", "food": "Food"}
COLOR = {"haps": "var(--signal)", "music": "var(--music)", "culture": "var(--culture)",
         "market": "var(--culture)", "outdoors": "var(--out-ink)", "food": "var(--food-ink)"}
CHIP = {"market": "culture"}          # markets count under Culture in the wayfinding bar

KEYWORDS = {
    "music": "jazz piano salsa music concert band dj trio orchestra symphony singer songwriter "
             "hip-hop rock punk choir opera live set album tour",
    "culture": "museum exhibit exhibition gallery art artist architect film screening cinema book "
               "reading lecture talk theater theatre installation lacma moca hammer getty",
    "market": "flea market vintage makers craft fair pop-up shop sale",
    "outdoors": "hike trail beach park garden picking farm apple run bike ride walk ocean mountain "
                "camp maze sunset",
    "food": "dinner supper restaurant chef menu pasta taco tasting wine brunch eat eataly food bakery",
}


def _txt(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h or "")).strip()


def category(s):
    text = (_txt(s["h2"]) + " ") * 2 + " ".join(          # title counts twice
        [_txt(s.get("tagline", ""))] + [_txt(b) for b in s.get("body", [])])
    words = re.findall(r"[a-z][a-z\-]+", text.lower())
    score = {c: sum(words.count(k) for k in ks.split()) for c, ks in KEYWORDS.items()}
    best = max(score, key=score.get)
    return best if score[best] else "culture"


def icon(cat, size=22):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{ICON[cat]}</svg>')


def link_of(s):
    """-> (href, label, body paragraphs without the call-to-action link)"""
    links = [b for b in s.get("body", []) if _txt(b) and re.fullmatch(r"\s*<a [^>]*>.*?</a>\s*", b, re.S)]
    rest = [b for b in s.get("body", []) if b not in links]
    if not links:
        return None, None, rest
    m = re.search(r'href="([^"]+)"[^>]*>(.*?)</a>', links[-1], re.S)
    return html.unescape(m.group(1)), _txt(m.group(2)).rstrip(" →").strip(), rest


def split_meta(meta):
    """'Sat Nov 21 · 7:30 pm · Dress: Jazz Age · Tickets: $45 · 10% off' ->
    (['Sat Nov 21', '7:30 pm'], [('Dress', 'Jazz Age'), ('Tickets', '$45 · 10% off')])"""
    plain, facts = [], []
    for seg in [x.strip() for x in _txt(meta).split(" · ") if x.strip()]:
        m = re.match(r"^([A-Z][A-Za-z ]{1,14}):\s*(.+)$", seg)
        if m:
            facts.append([m.group(1), m.group(2)])
        elif facts:
            facts[-1][1] += " · " + seg
        else:
            plain.append(seg)
    return plain, [tuple(f) for f in facts]


def dates_of(when, year):
    """'Fri–Sat Nov 6–7' -> (start, end); 'Through Nov 26' -> (None, end)."""
    m = re.search(r"\b(" + "|".join(MONTHS) + r")\w*\.?\s+(\d{1,2})(?:\s*–\s*(?:(" + "|".join(MONTHS) +
                  r")\w*\.?\s+)?(\d{1,2}))?", when)
    if not m:
        return None, None
    mon = MONTHS.index(m.group(1)) + 1
    start = datetime.date(year, mon, int(m.group(2)))
    end = start
    if m.group(4):
        end = datetime.date(year, MONTHS.index(m.group(3)) + 1 if m.group(3) else mon, int(m.group(4)))
    if when.lower().startswith("through"):
        return None, start
    return start, end


def span(dates):
    a, b = min(dates), max(dates)
    if a == b:
        return f"{MONTHS[a.month - 1]} {a.day}"
    if a.month == b.month:
        return f"{MONTHS[a.month - 1]} {a.day}–{b.day}"
    return f"{MONTHS[a.month - 1]} {a.day}–{MONTHS[b.month - 1]} {b.day}"


def when_parts(when):
    """'Opens Thu Nov 12' -> ('Opens Thu', 'Nov 12')"""
    m = re.match(r"^(.*?)\s*((?:" + "|".join(MONTHS) + r")\b.*)$", when)
    return (m.group(1), m.group(2)) if m else ("", when)


def main_html(iss, intro_html, cal):
    sections = iss["sections"]
    year = int(iss["date"][:4])
    issue_day = datetime.date.fromisoformat(iss["date"])
    labels = []
    for s in sections:
        if s["lbl"] not in labels:
            labels.append(s["lbl"])
    callouts = [s for s in sections if s["lbl"] != labels[-1]] if len(labels) > 1 else sections[:1]
    rows = [s for s in sections if s not in callouts]

    # ---- callouts
    ours = []
    for i, s in enumerate(callouts):
        href, cta, paras = link_of(s)
        plain, facts = split_meta(s["meta"])
        btn = f'<a class="ix-btn" href="{html.escape(href)}">{html.escape(cta)} &rarr;</a>' if href else ""
        if i == 0:
            start, _ = dates_of(plain[0] if plain else "", year)
            big = (f'<div class="ix-date" aria-hidden="true"><span>{DAYS[start.weekday()]}</span>'
                   f'<b>{start.day}</b><span>{MONTHS[start.month - 1]}</span></div>') if start else ""
            dl = [("When", " · ".join(plain))] if plain else []
            dl += facts
            facts_html = "".join(f"<div><dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd></div>" for k, v in dl)
            more = "".join(f'<p class="ix-tl">{p}</p>' for p in paras)
            ours.append(f'''    <article class="ix-lead">
      <div class="ix-lead-main">
        <div class="ix-kick">{icon("haps", 16)} {html.escape(s["lbl"])}</div>
        <h2>{s["h2"]}</h2>
        <p class="ix-tl">{s["tagline"]}</p>{more}
        <dl class="ix-facts">{facts_html}</dl>
        {btn}
      </div>
      {big}
    </article>''')
        else:
            body = "".join(f"<p>{p}</p>" for p in [s["tagline"]] + paras if p)
            foot = html.escape(" · ".join(plain + [f"{k}: {v}" for k, v in facts]))
            link = f'<a href="{html.escape(href)}">{html.escape(cta)} &rarr;</a>' if href else ""
            ours.append(f'''    <article class="ix-side">
      <div class="ix-kick">{icon(category(s), 16)} {html.escape(s["lbl"])}</div>
      <h2>{s["h2"]}</h2>
      {body}
      <div class="ix-side-foot"><span>{foot}</span>{link}</div>
    </article>''')
    side = ""
    if len(ours) > 1:
        side = '\n    <div class="ix-sides">\n' + "\n".join(ours[1:]) + "\n    </div>"
    ours_html = (f'  <section class="ix-ours{" ix-solo" if len(ours) == 1 else ""}" id="ours">\n'
                 f'{ours[0]}{side}\n  </section>') if ours else ""

    # ---- rows, grouped by date
    week_end = issue_day + datetime.timedelta(days=(6 - issue_day.weekday()) % 7)
    soon, later, first_of = [], [], {}
    for n, s in enumerate(rows):
        href, cta, paras = link_of(s)
        plain, facts = split_meta(s["meta"])
        when = plain[0] if plain else ""
        where = plain[-1] if len(plain) > 1 else ""
        start, end = dates_of(when, year)
        cat = category(s)
        rid = f"pick-{n + 1}"
        first_of.setdefault(CHIP.get(cat, cat), rid)
        small, big = when_parts(when)
        desc = " ".join([s["tagline"]] + paras)
        meta = LABEL[cat] + (f" · {html.escape(where)}" if where else "")
        tag = "a" if href else "div"
        attr = f' href="{html.escape(href)}"' if href else ""
        go = f'<div class="ix-go">{html.escape(cta)} <span>&rarr;</span></div>' if href else ""
        row = f'''    <{tag} class="ix-row" id="{rid}"{attr} style="--c:{COLOR[cat]}">
      <div class="ix-when"><span>{html.escape(small)}</span><b>{html.escape(big)}</b></div>
      <div class="ix-ico">{icon(cat)}</div>
      <div class="ix-txt"><h3>{s["h2"]}</h3><p>{desc}</p><div class="ix-meta"><span>{LABEL[cat]}</span>{meta[len(LABEL[cat]):]}</div></div>
      {go}
    </{tag}>'''
        (soon if start and start <= week_end else later).append((row, start, end))

    def group(items, title, gid):
        if not items:
            return ""
        ds = [d for _, a, b in items for d in (a, b) if d]
        rng = f"<span>{span(ds)}</span>" if ds else ""
        return (f'  <section class="ix-list" id="{gid}">\n    <div class="ix-gh"><h2>{title}</h2>{rng}</div>\n'
                + "\n".join(r for r, _, _ in items) + "\n  </section>")

    weekend = soon and all(a.weekday() >= 4 for _, a, _ in soon)
    lists = group(soon, "This weekend" if weekend else "This week", "soon") + "\n" + group(later, "Coming up", "later")

    # ---- wayfinding
    counts = {}
    for s in rows:
        c = CHIP.get(category(s), category(s))
        counts[c] = counts.get(c, 0) + 1
    chips = []
    if callouts:
        chips.append(f'<a class="ix-chip" href="#ours" style="--c:{COLOR["haps"]}">{icon("haps", 16)}'
                     f'{LABEL["haps"]} <b>{len(callouts)}</b></a>')
    for c in ("music", "culture", "outdoors", "food"):
        if counts.get(c):
            chips.append(f'<a class="ix-chip" href="#{first_of[c]}" style="--c:{COLOR[c]}">{icon(c, 16)}'
                         f'{LABEL[c]} <b>{counts[c]}</b></a>')

    return f'''<main class="ix">
  <section class="ix-hero">
    <div class="eyebrow">Issue · {iss["pretty"]}</div>
    <h1>{iss["title"]}</h1>
    <p class="ix-dek">{iss["dek"]}</p>
    <div class="ix-intro">{intro_html}</div>
  </section>
  <nav class="ix-way" aria-label="In this issue"><span class="ix-way-l">In this issue</span>{"".join(chips)}</nav>
{ours_html}
{lists}
  <section class="ix-next">
    <div><h3>Get the next one</h3><p>One email, every Tuesday morning. Free, unsubscribe anytime.</p></div>
    <a class="ix-btn" href="/subscribe">Subscribe free &rarr;</a>
  </section>
  <p class="ix-more">More: <a href="/">this week in LA</a> &middot; <a href="{cal}">the calendar</a> &middot; <a href="/archive/">every issue</a></p>
</main>'''
