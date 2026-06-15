# haps-club-refresh-SKILL.md

**Status:** v2 — supersedes prior locked design system  
**New baseline commit:** `9fa62a0` (`Haps-Club/haps-club@main` · `index.html`)  
**Last updated:** 2026-06-15

---

## 1. Design system (locked)

- **Palette**
  - `--navy` `#292f71` (primary; logo color)
  - `--navy-deep` `#1b1f52` (footer / hover)
  - `--coral` `#FF6B47` (single accent — CTAs only)
  - `--cream` `#FAF7F0` (page background)
  - `--paper` `#FFFFFF` (card surface)
  - `--line` `#E7DFCF` (hairlines)
  - Category colors: `--food` `#FF6B47`, `--culture` `#7C5CFF`, `--music` `#2D6CDF`,
    `--outdoors` `#1FA774`, `--date` `#E8458C`, `--free` `#0FB5A6`
- **Type**
  - Display: `'Instrument Serif'` (hero, section titles, card titles, date-tile day numbers)
  - UI/body: `'Inter'` (everything else)
  - All buttons: `display:inline-flex; align-items:center; justify-content:center; text-align:center`
- **Layout**
  - Max-width 1140px, radius 22px on cards, 980px on buttons/pills
  - Cream background with soft coral/violet radial wash
- **Nav & footer**
  - **Logo only**, top-left, 60px square — no "Haps Club" wordmark text anywhere
  - Sticky nav, frosted blur (`backdrop-filter:saturate(180%) blur(18px)`)
- **Signature element**: iOS-calendar date tile on every dated card (navy month cap + serif day numeral)

## 2. Required functionality on the homepage

1. **Category filter rail** — All, Saved, Food, Culture, Music, Outdoors, Date night, Free
2. **Neighborhood dropdown** — Westside, Mid-City, Hollywood, Downtown, Eastside, Northeast LA, Citywide
3. **Live result count** + Clear filters
4. **Save** (heart, persists via `localStorage` key `haps_saved`) + **Saved** filter
5. **Add to calendar** (Google Calendar pre-fill URL per card)
6. **Whole-card click** → outbound `data-link` opens in new tab; Enter/Space keyboard support
7. **Featured row** = max 3 image-gradient cards; on mobile becomes a swipe carousel
8. **Auto-expiry** (see §4 — non-negotiable)
9. **Calendar link** in nav, hero CTA, calstrip, section header, footer

## 3. Card data schema — REQUIRED for every dated card

```html
<article class="card t-<theme>"
  data-cat="<theme>"
  data-area="<westside|midcity|hollywood|dtla|eastside|nela|citywide>"
  data-when="upcoming"
  data-link="<outbound URL>"
  data-title="<title>"
  data-starts="YYYYMMDDTHHMMSS"   <!-- REQUIRED for dated events -->
  data-ends="YYYYMMDDTHHMMSS"     <!-- REQUIRED; falls back to data-starts -->
  tabindex="0" role="link"
  aria-label="<title> — open details">
```

- `<theme>` ∈ food | culture | music | outdoors | date | free
- For evergreen/recurring picks, omit `data-starts`/`data-ends` and use a "Now / ★" date tile
- Featured `<a class="fcard">` cards take the same `data-starts`/`data-ends`

## 4. Auto-expiry (live on production)

```js
(function(){var now=new Date();
  document.querySelectorAll('[data-ends],[data-starts]').forEach(function(el){
    var v=el.dataset.ends||el.dataset.starts; if(!v) return;
    var iso=v.slice(0,4)+'-'+v.slice(4,6)+'-'+v.slice(6,8)+'T'
           +(v.length>8?v.slice(9,11):'23')+':'
           +(v.length>8?v.slice(11,13):'59')+':00-07:00';
    var d=new Date(iso); if(!isNaN(d)&&d<now) el.dataset.expired='1';
  });
})();
```

Filter logic must AND in `el.dataset.expired !== '1'`. **Result:** past-dated cards self-hide; no manual pruning required.

## 5. SEO / AEO (must remain present)

- `<link rel="canonical">`, `robots`, `author`, `geo.region`, `theme-color`
- Full OG card set (image: `res.cloudinary.com/dimlqawuh/.../haps-og-card.png`)
- Twitter `summary_large_image`
- **`application/ld+json`** with a `WebSite` + `ItemList` of `Event` objects covering every dated card (name, startDate, endDate, location, url, `eventStatus: EventScheduled`, `eventAttendanceMode: OfflineEventAttendanceMode`)
- `llms.txt` and `sitemap.xml` updated on every newsletter/refresh

## 6. Refresh workflow

1. Pull `newsletter@haps.club` inbox (last 5–10 days) via `gmail-mcp` or Composio `gmail_unsing-pandy`
2. Verify dates from primary source (not LLM-extracted) — emails, venue site, Luma
3. Update cards in `index.html`:
   - Add new picks with full `data-*` attrs (§3)
   - Bump dates on recurring series
   - **Do not manually remove expired cards** — auto-expiry handles it
4. Publish newest issue to `/archive/YYYY-MM-DD-slug/` and update `/archive/`, `sitemap.xml`, `llms.txt`
5. Deploy: Composio `GITHUB_COMMIT_MULTIPLE_FILES` to `Haps-Club/haps-club@main` (use `upserts`, field name is `message` not `commit_message`)
6. Verify live with `curl` (don't claim live without confirming new markers)

## 7. Footer (homepage + archive — exact set, in order)

Subscribe · About · Submit a tip · Contact (mailto:michael@haps.club) · Instagram · WhatsApp · Calendar · Archive · Sitemap

## 8. Hard rules

- **Never** push to `Hilex2030/haps-club` — org repo `Haps-Club/haps-club` only
- Validate write access via `curl Bearer` before trusting any PAT
- No exclamation marks in copy
- One quote per source maximum when citing
- Test JSON-LD validity (`json.loads`) before commit
