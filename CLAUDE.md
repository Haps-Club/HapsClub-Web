# Haps Club website — haps.club

Static site on GitHub Pages (repo Haps-Club/HapsClub-Web, branch `main`), behind Cloudflare. Pushing to `main` goes live in about 1–2 minutes. Git pushes directly (gh CLI is the credential helper).

Read @PROJECT.md for what Haps Club is, who it's for, voice and editorial rules. Its repo names (`Hilex2030/haps-club`), its navy/coral/serif design notes and its "one file" homepage are out of date — this file wins on mechanics and design.

## How to work
- `git pull` before editing — other sessions edit this repo, and a bot commits `Rebuild homepage from events.json` after pushes and every morning.
- Patch existing pages. Never rebuild a page from scratch unless Michael asks.
- Preview: start the `haps` preview (`.claude/launch.json`, port 8002 — 8000 is BizColab's, 8001 is AMRE's).
- Before every commit: `python3 scripts/check_site.py` must pass. Commit and push only after Michael approves.
- Keep short, plain answers. Show Michael the result, not the process.

## Which file to edit
| Job | Edit | Then |
|---|---|---|
| Weekly / daily picks, featured, announcement, sponsor | `data/events.json` | `python3 scripts/build_home.py` to preview. CI rebuilds `index.html` on push anyway. |
| Homepage layout or copy | `scripts/build_home.py`, `assets/home-f.css`, `assets/home-f.js` | `python3 scripts/build_home.py`. Never hand-edit `index.html` — it's generated and gets overwritten. |
| Nav or footer (every page) | `scripts/site_chrome.py` (markup), `assets/chrome.css` (looks) | `python3 scripts/normalize_chrome.py`, then `python3 scripts/build_home.py` (both refresh the `?v=` hashes) |
| Interior page look | `assets/site.css` | `python3 scripts/normalize_chrome.py` to refresh `?v=` on every page |
| Newsletter issue into `/archive/` | Automatic: `archive-issues.yml` runs `scripts/issues_from_mailerlite.py` (sent MailerLite campaigns named "Haps Weekly …") | By hand: `python3 scripts/issues_from_mailerlite.py --html email.html --sent YYYY-MM-DD > issues.json`, then `python3 scripts/publish_issue.py issues.json` and `python3 scripts/build_home.py`. Never hand-build archive pages or edit the `archive` array. (`issues_from_kit.py` is for the old Kit issues.) |
| Guides (`guides/`) | `scripts/build_guides.py` or `build_guides_fall.py` (don't rerun `build_guides.py` blindly — some guides were hand-fixed) | `python3 scripts/build_pages.py` fills the live event blocks + schema |
| Ask Haps page (`/ask/`) | `scripts/build_ask.py`; worker source in `workers/ask-haps.js` (deployed to Cloudflare separately) | `python3 scripts/build_ask.py` |
| Interior pages (about, subscribe, privacy, partners, sitemap) | the `.html` file directly | reuse shared classes; no inline `<style>` |

## events.json
- Top level: `updated`, `weekLabel`, `featured` (exactly 3), `events` (soonest first, undated evergreen below), `plan`, `archive`, `sponsor`, `announcement`.
- Event fields: `title, month ("NOV"), day, cat, tags, area, where, price, link`, plus `tagline, starts, ends, hood, addr`. Times are `YYYYMMDDTHHMMSS` Pacific.
- Anything with an `ends` drops off automatically once it passes (build_home.py, daily at 7:05am PT). Items with no `starts`/`ends` never expire — prune them by hand.
- `area` must be one of: westside, midcity, dtla, hollywood, eastside, citywide (the `AREAS` chips in build_home.py).
- Haps Club's own events: link `luma.com/hapsclub…` (or set `"lead": true`) and they render as the lead card.

## Design rules ("Design F", Nov 2026)
- Fonts: Inter Tight (headlines/body) + IBM Plex Mono (small uppercase labels). No other fonts.
- Colors live only in CSS tokens: ink #111111, stone #F4F2EF, line #E4DED6, signal orange #FF4F00, navy #292F71; category colors food #FF9500, music #AF52DE, culture #007AFF, outdoors #34C759. Never inline a color.
- Stylesheets — each rule lives in exactly one file:
  - `assets/chrome.css` — header + footer, loaded first by every page (homepage too).
  - `assets/site.css` — every interior page; tokens in its single `:root` block at the top.
  - `assets/home-f.css` — homepage only. Page extras load alongside: `partners.css` (before site.css), `ask.css` (after).
  - A token used on both the homepage and interior pages lives in both `home-f.css` and `site.css` — change both.
  - The old `chrome-f.css`, `sunset-pages.css` and `pages-f.css` were merged into these in Nov 2026; don't bring them back.
- CSS/JS links carry `?v=<first 8 of md5>` for cache-busting. Edit an asset → update its `?v=` on every page that links it (the build scripts do this for pages they generate; `check_site.py` flags stale ones).
- Never bring back Instrument Serif or cream #FAF7F0. No light/dark toggle. Top-left logo always links home.
- Signup form is MailerLite (`assets/ml-subscribe.js`, form action in build_home.py) — Kit is no longer the site form.
- Archive issue pages (from Nov 3, 2026 on) use the callout + compact-row layout from `scripts/issue_layout.py` (`.ix-*` in site.css): every label group but the last becomes a callout, the last becomes typed rows with category icons. Categories come from keywords in `KEYWORDS` there. Older issues keep the `.sec` layout; don't regenerate them.
- Standalone pages (own inline `<style>`, no GA, noindex): `planner/`, `planner-svetlana/`, `partners/*/`, `partnership/macallan/`, `events/*/` and their `ops/` pages. Leave them unless asked.
- Keep byte-identical: Google Analytics `G-RKY63MK7ND`, canonical/OG meta.

## Haps Club rules
- Haps Club is separate from AMRE, BizColab and Compass. No real estate anywhere. BizColab may appear only as a labeled sponsor in the "Sponsored by" block (`site_chrome.sponsors()`), never in picks or copy.
- Never invent events, dates, venues, prices or links. Verify every date's weekday with Python and every URL is live; cut what can't be verified and say so.
- Never say "singles". No exclamation marks in card or story copy.
- Link to the venue's own site, not Eater, Infatuation or Yelp.

## Automation (GitHub Actions)
- `build-home.yml` — rebuilds `index.html` on push to events.json/home assets and daily 7:05am PT.
- `archive-issues.yml` — Tuesdays ~11am PT + daily: archives new "Haps Weekly" MailerLite sends and refreshes the homepage's Recent issues. Needs the `MAILERLITE_API_KEY` repo secret; skips with a warning without it. Name weekly campaigns "Haps Weekly YYYY-MM-DD: …" so it picks them up (tests and one-offs are ignored).
- `deploy-from-issue.yml` — old fallback: an issue titled `deploy: <path>` with a base64 body writes that file. Not needed now that git push works.
- The May 2026 daily inbox report (`daily-report.yml` / `process-approval.yml`) was retired: its scripts were removed 2026-05-11 and the workflows on 2026-11-02. Don't restore them unless Michael asks.

## Verify
- Before commit: `python3 scripts/check_site.py` (pages end with `</html>`, have GA, link their CSS with fresh `?v=`, no stray `<style>`, local links resolve, events.json valid, weekday names match dates, no "singles"/exclamation marks in event copy).
- After push: `python3 scripts/check_site.py --live` fetches every page from haps.club. Never say it's live until that passes.
