# Haps Club website — haps.club

Static site on GitHub Pages (repo Haps-Club/HapsClub-Web, branch `main`), behind Cloudflare. Pushing to `main` goes live in about 1–2 minutes.

Read @PROJECT.md for what Haps Club is, who it's for, voice and editorial rules. Its repo names (`Hilex2030/haps-club`) and its navy/coral/serif design notes are out of date — the repo and design below win.

## How to work
- Patch existing pages. Never rebuild a page from scratch unless Michael asks.
- Preview locally first (`python3 -m http.server 8000`), then commit and push only after Michael approves.
- Always `git pull` before editing — other sessions edit this repo too.
- Keep short, plain answers. Show Michael the result, not the process.

## Site structure
- Weekly update = edit `data/events.json` only. Never regenerate `index.html` (it's the shell + renderer).
- `assets/sunset.css` (homepage) and `assets/sunset-pages.css` (interior pages) keep identical `:root` tokens — change a token in both.
- Interior pages have no inline `<style>`; reuse the shared class names.
- Neighborhood `area` values must have a chip in `HOODS` in index.html: westside, midcity, dtla, hollywood, eastside, citywide.
- Newsletter issues go to `/archive/` only via `python3 scripts/publish_issue.py issues.json` — never hand-build archive pages or edit the `archive` array in events.json. The homepage must always show the newest sent issue.
- Keep byte-identical: Google Analytics `G-RKY63MK7ND`, Kit form `9421017`, canonical/OG meta.

## Haps Club rules
- Haps Club is separate from AMRE, BizColab and Compass. No real estate anywhere.
- Never invent events, dates, venues, prices or links. Verify every date's weekday with Python and every URL is live; cut what can't be verified and say so.
- Never say "singles". No exclamation marks in card or story copy.
- Link to the venue's own site, not Eater, Infatuation or Yelp.

## Design rules ("Sunset" system)
- All-sans (SF Pro/Inter), 800-weight tight headlines, 26px radii, no borders or shadows.
- Accents: red #FF3B30, orange #FF9500, green #34C759, blue #007AFF, purple #AF52DE, navy #292F71. Change colors through the CSS tokens, never inline.
- Never bring back Instrument Serif or cream #FAF7F0. No light/dark toggle.
- Top-left logo always links to the homepage.

## Verify after deploy
- Every page returns 200, links the sunset CSS, has no `<style>`, has GA, ends with `</html>`; `data/events.json` parses.
- Never say it's live until a fetch of haps.club confirms it.
