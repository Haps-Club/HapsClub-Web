# haps-club-refresh-SKILL.md

**Status:** v3 — supersedes v2
**Repo / live site:** `Haps-Club/HapsClub-Web` -> haps.club (public, GitHub Pages + Cloudflare). The old name `Haps-Club/haps-club` is retired — always push to **HapsClub-Web**.
**Last updated:** 2026-06-21

## 0. What a refresh means now
Two jobs, every time:
1. Make the homepage feel **targeted to the next ~6 weeks** — lead with dated, time-specific picks (events, openings, one-night dinners, festivals, restaurant happenings), not evergreen filler. Evergreen "LA staples" cards stay but sit **below** the dated cards.
2. **Mirror every featured/dated event into the Haps Club Google Calendar** (non-negotiable — Michael asked for this explicitly).

## 1. Design system (locked)
- **Palette:** `--navy #292f71` (primary; logo), `--navy-deep #1b1f52` (footer/hover), `--coral #FF6B47` (single accent — CTAs only), `--cream #FAF7F0` (page bg), `--paper #FFFFFF` (card), `--line #E7DFCF` (hairlines). Category colors: `--food #FF6B47`, `--culture #7C5CFF`, `--music #2D6CDF`, `--outdoors #1FA774`, `--date #E8458C`, `--free #0FB5A6`.
- **Type:** Display `'Instrument Serif'` (hero, section + card titles, date-tile day numbers); UI/body `'Inter'`.
- **Layout:** max-width 1140px; radius 22px cards, 980px buttons/pills; cream bg with soft coral/violet radial wash.
- **Nav & footer:** logo only, top-left, 60px square — no "Haps Club" wordmark text anywhere. Sticky frosted-blur nav.
- **Signature element:** iOS-calendar date tile on every dated card (navy month cap + serif day numeral).

## 2. Required homepage functionality
1. Category filter rail — All, Saved, Food, Culture, Music, Outdoors, Date night, Free
2. Neighborhood dropdown — Westside, Mid-City, Hollywood, Downtown, Eastside, Northeast LA, Citywide
3. Live result count + Clear filters
4. Save (heart, `localStorage` key `haps_saved`) + Saved filter
5. Add-to-calendar (Google Calendar pre-fill URL per card)
6. Whole-card click -> outbound `data-link` opens new tab; Enter/Space keyboard support
7. Featured row = **max 3** image-gradient `fcard`s; mobile = swipe carousel
8. Auto-expiry (see s4 — non-negotiable)
9. Calendar link in nav, hero CTA, calstrip, section header, footer

## 3. Card schema (REQUIRED on every dated card)
Grid card:
```html
<article class="card t-<theme>" data-cat="<theme...>" data-area="<westside|midcity|hollywood|dtla|eastside|nela|citywide>"
  data-when="upcoming" data-link="<url>" data-title="<title>"
  data-starts="YYYYMMDDTHHMMSS" data-ends="YYYYMMDDTHHMMSS" tabindex="0" role="link" aria-label="<title> — open details">
  <div class="card-top"><span class="datetile"><span class="m">MON</span><span class="d">DD</span></span>
    <div class="card-head"><span class="cat">CatLabel</span><h3><a href="<url>" target="_blank" rel="noopener"><title></a></h3></div>
    <button class="iconbtn save" ...></button></div>
  <div class="card-foot"><span class="where">...NEIGHBORHOOD</span>
    <span class="right"><span class="price">PRICE</span><a class="iconbtn add" href="<gcal pre-fill>" ...></a>...</span></div>
</article>
```
- `<theme>` in food | culture | music | outdoors | date | free.
- Featured `<a class="fcard t-theme">` cards take the same `data-starts`/`data-ends`.
- Evergreen/recurring picks: omit `data-starts`/`data-ends`, use a "Now / *" date tile.

## 4. Auto-expiry (live on prod — do NOT remove)
A small script reads `data-ends` (fallback `data-starts`), parses ISO at -07:00, and sets `dataset.expired='1'` on anything in the past. Filter logic ANDs `el.dataset.expired !== '1'`. **Past-dated cards self-hide — never manually prune them.** Verify it's present with: content contains `dataset.expired`.

## 5. Inbox mining for dated content (newsletter@haps.club)
- Pull the last ~10–24 days from **newsletter@haps.club** via **Composio Gmail** (account alias `haps-newsletter`, id `gmail_unsing-pandy`). The gmail-mcp token for this box is currently `invalid_grant` — use Composio, not gmail-mcp.
- Inbox is mostly promo noise + Luma RSVP pings. Real signal: venue/restaurant PR (Maydan LA, Eataly, Stanley's, Helms Design District, Petersen, The Broad, Electric Lodge, ICA LA, CAAM) and LA roundups (LA Unfolded, KCRW Insider, Discover Hollywood, DTLA Alliance, LA Mag Weekend Guide, FOUND LA, Getty).
- Extract items landing in the next ~6 weeks. **Verify each date from the source email / venue site / Eventbrite / Luma — never LLM-guessed.**
- Skip off-brand items (B2B / brand conferences, out-of-market, pure product marketing).

## 6. Build + deploy
1. Fetch live `index.html` via Composio `GITHUB_GET_REPOSITORY_CONTENT`.
2. Featured row: max 3 `fcard`s. Grid: insert new dated `<article class="card">` immediately after `<div class="grid" id="grid">` so dated leads; keep evergreen below.
3. Update the inline `application/ld+json` `ItemList`: append one `Event` per new dated card (parse with `json.loads`, append, re-dump, validate).
4. **Deploy via Composio** `GITHUB_COMMIT_MULTIPLE_FILES` to `Haps-Club/HapsClub-Web@main`, run inside `COMPOSIO_REMOTE_WORKBENCH` so the ~93KB file stays server-side. **The project PAT is expired (401) — do not use it.**
5. Verify live: `curl https://haps.club/` and confirm new titles + card count before claiming done.

## 7. Calendar sync (every refresh — non-negotiable)
- Calendar: **Haps Club Calendar** `c_ea45ead7ce1909f199c95778b5b7afd9d1a9f9c9751f911bf3c672f267dc4384@group.calendar.google.com`.
- The dedicated Google Calendar MCP is **reader-only** on this calendar -> use **Composio `GOOGLECALENDAR_CREATE_EVENT`** (writes as michael@haps.club).
- Pass **naive** `start_datetime`/`end_datetime` (NO timezone offset) + `timezone: America/Los_Angeles`. Passing an offset mangles the time. Use `create_meeting_room:false`, `exclude_organizer:true`, `transparency:transparent`, `visibility:public`.
- List existing events for the window first (avoid duplicates); add only the missing ones. Description style: one or two lines + ticket link + a final `More: https://haps.club`.

## 8. Footer (homepage + archive — exact, in order)
Subscribe · About · Submit a tip · Contact (mailto:michael@haps.club) · Instagram · WhatsApp · Calendar · Archive · Sitemap

## 9. Hard rules
- Push to the **org** repo `Haps-Club/HapsClub-Web` only; never `Hilex2030/*`.
- Validate write access before trusting any PAT (the current PAT is dead — use the Composio GitHub connection, account Hilex2030).
- No exclamation marks in copy. One quote per source maximum when citing.
- Validate JSON-LD (`json.loads`) before every commit.
