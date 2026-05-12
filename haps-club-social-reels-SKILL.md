---
name: haps-club-social-reels
description: Use this skill any time the user asks to create a social media reel, carousel, Instagram post, TikTok post, or any visual social asset for Haps Club. Triggers include "make a reel," "create a social post," "Instagram graphics for this week," "carousel for the newsletter," "post about [pick]," or any request to turn the website's picks or the newsletter's content into shareable visuals. The skill produces 9:16 vertical SVG-based decks (typically 8 slides), a companion PNG downloader page, and matching captions in the Haps Club voice. All assets live in Hilex2030/haps-club-assets. This skill is the canonical, tested workflow proven on the May 11 2026 reel.
---

# Haps Club Social Reels Skill

The Haps Club site refreshes weekly. The newsletter goes out Tuesday mornings. Social posts amplify both. This skill is the playbook for turning website picks or newsletter content into Instagram reels, carousels, and single-pick posts — fast, on-brand, and with zero fabricated content.

**Read this fully before making any social asset.** The shortcuts here are the result of an actual session that worked. Skipping ahead leads to fabricated venues, broken logos, or generic-looking decks that don't feel like Haps Club.

---

## What this skill produces

For a given week or topic, the standard output is:

1. **A deck HTML page** — `Hilex2030/haps-club-assets/html/reel-YYYY-MM-DD.html` — 8 slides as full-page 1080×1920 SVGs, viewable in browser
2. **8 standalone SVG files** — `Hilex2030/haps-club-assets/images/reel-YYYY-MM-DD/NN-name.svg` — one per slide, exportable individually
3. **A PNG downloader page** — `Hilex2030/haps-club-assets/html/download-reel-YYYY-MM-DD.html` — opens in a browser, bakes the 8 SVGs into 1080×1920 PNGs locally using Canvas, downloads them all with one click
4. **A caption** — Instagram reel caption (default) or other format if specified

For carousel posts or single-pick teasers, see "Other formats" below.

---

## The user's stated requirements (from May 11 2026)

> "Let's do a text-based and illustrator graphic reel that we can use. No product will be PNGs or JPEGs, so keep that in mind."

> "Please make sure to add our logo to at least the end and beginning slides."

> "I like how this was, and I would like to be able to repeat it in the future."

That's the brief. Hand-coded SVG illustrations only. No stock photos, no AI-generated images of real venues, no copyrighted imagery. Logo on the open and close slides minimum. The format and process from the May 11 session is the template — do it the same way every time.

---

## The 8-slide structure

This is the proven order. Don't deviate without a reason.

| # | Purpose | Background | Content |
|---|---------|------------|---------|
| 01 | **Open** | Cream `#FAFAF7` with subtle navy/coral gradient wash | Real Haps Club logo (navy) + "THIS WEEK IN LA" eyebrow + date range + tagline |
| 02 | **Hook** | Solid navy `#292f71` with coral radial glow lower-right | "5 picks. One city." or equivalent + brand promise line ("Hand-picked. No filler. No sponcon.") |
| 03 | **Pick 1 (featured)** | Themed to the pick (e.g. coral sunset gradient for a rooftop, navy night sky for a Bowl show) | Hand-coded SVG illustration + eyebrow date/time/price + big serif headline + neighborhood meta |
| 04 | **Pick 2** | Themed to the pick | Same structure as 03 |
| 05 | **Pick 3** | Themed to the pick | Same structure as 03 |
| 06 | **Pick 4** | Themed to the pick | Same structure as 03 |
| 07 | **CTA** | Solid coral `#FF6B47` with subtle gradient overlay | "Plus N more picks" eyebrow + "The full list is online" big serif + navy URL pill with "haps.club" + subline |
| 08 | **Close** | Deep navy `#1a1f4d` with radial spotlight | Real Haps Club logo (white) + hairline accent + tagline "A daily glance at what's worth doing in Los Angeles." + "@THEHAPSCLUB · HAPS.CLUB" |

**Variations on this structure:**

- **5 picks instead of 4:** combine two related picks on one slide (e.g. "Salsa under sunset OR jazz on the lawn" for the May 11 Friday doubleheader). Don't extend the deck past 8 slides — engagement drops sharply.
- **Themed week:** if the user asks for a topical reel (e.g. "all restaurants this week"), keep the same structure but theme every pick slide to food (warm tints, plate/glass illustrations, neighborhood-anchored type).
- **Single-pick teaser:** see "Other formats" below.

---

## Brand discipline — non-negotiable

### Colors (only these)

```
--navy:        #292f71    Primary brand
--navy-deep:   #1a1f4d    Subscribe block, deep background, hover states
--navy-tint:   #EEF0F8    Soft navy backgrounds
--accent:      #FF6B47    Warm coral — the single accent
--accent-deep: #E54D2B    Coral hover
--accent-tint: #FFF1ED    Soft coral wash for featured cards/sky gradients
--bg:          #FAFAF7    Warm off-white (NOT pure white)
--ink:         #0F1117    Body text
--ink-3:       #6B6F7A    Muted text
```

**Never introduce a third brand color.** If a slide feels like it needs more visual interest, get it from gradient layering or illustration detail, not from a new color.

### Typography

- **Inter** — UI, body, eyebrows, meta lines, weights 400–800
- **Instrument Serif** — headlines, italic for emphasis (e.g. "*most fun room*" as the italic accent line)
- Both load from Google Fonts. Always include the `<link>` tag.
- **Never a third font.**

### The logo — always real, never fabricated

The real Haps Club wordmark lives at:

- **Navy variant** (for light backgrounds): `https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/haps-club-logo.svg` (viewBox 1100×1100)
- **White variant** (for dark backgrounds): `https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/haps-club-logo-white.svg` (viewBox 900×900)

Embed the logo paths inline as `<symbol>` definitions at the top of the deck HTML, then `<use href="#hc-logo-navy">` (or `#hc-logo-white`) on slides 1 and 8. Inline embedding ensures the deck renders offline and exports cleanly.

**Do NOT** under any circumstance create a fabricated monogram (e.g. a circle with "HC" in it) as a substitute. Past Claude did this on the May 11 session. The user noticed immediately. The real wordmark is the wordmark — don't invent a new mark.

If you need to verify the logo exists, check `images/INDEX.md` in the assets repo for the catalog.

### Voice (carries over from the website skill)

- Conversational, not promotional. ✅ "SUSHISAMBA's rooftop is the most fun room in LA right now." / ❌ "Don't miss SUSHISAMBA!"
- Always name the neighborhood (West Hollywood, Culver City, Pacific Palisades, etc.)
- Times use natural phrasing: "Doors 6, talk 7" not "6:00 PM doors"
- Em dashes for parentheticals are fine
- **Never use exclamation marks in slide bodies or captions**
- **Banned words:** cancellation, monetize, democratize, streamline, unleash, leverage, ecosystem, journey, curated

---

## Illustration approach

Each pick slide gets a hand-coded SVG illustration that **evokes** the venue without faking it. The proven approach from May 11:

- **SUSHISAMBA rooftop** → coral sunset gradient, layered Hollywood Hills silhouettes, building floor, retractable dome arch with slats, palm tree in navy, small coral cocktail glass on the rooftop
- **Friday doubleheader (Salsa + Jazz)** → split background (navy top, cream bottom), floating coral music notes, white saxophone silhouette up top, navy stylized dancers below with one coral skirt swirl
- **Getty Villa** → cream gradient background, navy classical pediment with 4 fluted Doric columns, coral bead row on entablature, steps below
- **Bright Eyes at Hollywood Bowl** → deep navy night gradient, scattered stars, crescent moon (two circles trick), Hollywood Bowl shell as nested arches in white with a coral innermost arch, coral stage light triangles

**Rules for illustrations:**

1. **Only brand colors.** Even fading layers should use `opacity` on a navy/coral fill, not a different color.
2. **Geometric, not realistic.** Think editorial illustration — Apple News, NYT graphics. Not Disney, not stock vector.
3. **Anchor each illustration in the upper 50–55% of the slide.** Lower 45% is reserved for the type block.
4. **Never illustrate real people, real logos of venues, real album covers, or copyrighted IP.** A bowl shell is fine. A specific Bright Eyes album cover is not. A generic palm tree is fine. The SUSHISAMBA logo is not.

If you can't think of a clean illustration for a pick (e.g. "trivia at The Penmar"), fall back to a single typographic element — a giant serif numeral, a quote mark, a hairline frame — and let the type do the work.

---

## File structure and naming

For a reel dated `YYYY-MM-DD` (use the Monday of the week the reel covers):

```
Hilex2030/haps-club-assets/
├── html/
│   ├── reel-YYYY-MM-DD.html              ← the deck viewer
│   └── download-reel-YYYY-MM-DD.html     ← the PNG downloader
└── images/
    └── reel-YYYY-MM-DD/
        ├── 01-open.svg
        ├── 02-hook.svg
        ├── 03-<topic>.svg                ← e.g. 03-sushisamba.svg
        ├── 04-<topic>.svg
        ├── 05-<topic>.svg
        ├── 06-<topic>.svg
        ├── 07-cta.svg
        └── 08-close.svg
```

**Naming the topic slides:** use the venue or event slug, kebab-case, no special characters. `sushisamba`, `friday-doubleheader`, `getty-villa`, `bright-eyes`. Match what's in the deck.

---

## The deck HTML — the proven template

The May 11 deck at `https://hilex2030.github.io/haps-club-assets/html/reel-2026-05-11.html` is the canonical template. To make a new deck:

1. **Fetch the May 11 deck** via `GitHub:get_file_contents` on `Hilex2030/haps-club-assets/html/reel-2026-05-11.html`
2. **Copy the entire file** to a new path: `html/reel-YYYY-MM-DD.html`
3. **Keep these parts byte-identical:**
   - `<head>` (meta, fonts link, all CSS in `<style>`)
   - The two `<symbol>` definitions for `hc-logo-navy` and `hc-logo-white` at the top of `<body>`
   - The toolbar div
   - The `.deck` wrapping div structure
   - Slide 2 (Hook) — change the date if needed but the structure stays
   - Slide 7 (CTA) — only the "PLUS N MORE PICKS" number changes
   - Slide 8 (Close) — never changes
4. **Replace these parts:**
   - Slide 1 date eyebrow ("THIS WEEK IN LA") and date range
   - Slides 3-6 illustrations, eyebrows, headlines, and meta lines per the picks

The HTML is hand-written, no build step, no frameworks. Don't introduce React, Vue, or any preprocessor.

---

## The PNG downloader page — also proven

The May 11 downloader at `https://hilex2030.github.io/haps-club-assets/html/download-reel-2026-05-11.html` is the canonical template. To make a new one:

1. **Fetch** `html/download-reel-2026-05-11.html`
2. **Copy to** `html/download-reel-YYYY-MM-DD.html`
3. **Change only the `BASE` constant and the `slides` array** in the script. Everything else (CSS, button, status text, render logic) stays byte-identical.

```js
const BASE = 'https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/reel-YYYY-MM-DD/';
const slides = [
  { file: '01-open.svg',          label: '01 · Open' },
  { file: '02-hook.svg',          label: '02 · Hook' },
  { file: '03-<topic>.svg',       label: '03 · <Name>' },
  // ... 04-07 ...
  { file: '08-close.svg',         label: '08 · Close' },
];
```

The downloader uses inline `@import` of Google Fonts injected into the SVG before rasterization, so the PNGs render Inter + Instrument Serif correctly. **Don't strip the font injection** — without it, fonts fall back to generics and the brand discipline breaks.

---

## Standalone SVG files — for individual export

For each pick slide in the deck, also write a standalone SVG file to `images/reel-YYYY-MM-DD/NN-name.svg`. These are what the downloader fetches. Each standalone SVG:

- Has its own `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">` root
- Has its own `<defs>` block with any gradients it uses (gradients in the deck HTML use IDs that won't be in the standalone)
- For slides 01 and 08 (with the logo), embeds the logo as its own `<symbol>` inside `<defs>` — the standalone can't reference the deck's symbols
- Is self-contained — open it in any browser and it renders correctly

---

## The caption — the proven recipe

The May 11 caption format works. Reuse it:

```
[Hook line — usually echoes slide 2: "Five picks for the week ahead in LA."]

[Featured pick — 2-3 sentences, neighborhood-anchored, with a small action prompt at the end]

[Pick 2 / 3 / 4 — one short paragraph each, conversational, dates and times in natural phrasing]

[Final pick — usually the biggest upcoming event, "mark your calendar"-style]

Full list, every Tuesday — link in bio.

.
.
.

#LosAngeles #ThingsToDoInLA #LALife [+ relevant neighborhood and topic tags] #HapsClub
```

**Hashtag formula:** 12–15 tags total. Mix:
- 3-4 broad LA tags (`#LosAngeles`, `#ThingsToDoInLA`, `#LALife`, `#LAEvents`)
- 4-5 neighborhood tags from the picks (`#WestHollywood`, `#CulverCity`, etc.)
- 2-3 topic tags (`#LAFood`, `#LAMusic`, `#LAArt`)
- 2-3 venue/event-specific tags where relevant (`#HollywoodBowl`, `#GettyVilla`)
- 1 brand tag (`#HapsClub`)

The three-dot break pushes hashtags below the IG caption fold.

---

## Other formats

### Single-pick teaser (1:1 or 4:5, IG feed, mid-week)

When the user says "make a post about [pick]":

- One image, square (1080×1080) or 4:5 portrait (1080×1350)
- Same brand colors, same fonts, same illustration approach
- One headline, one eyebrow, one CTA
- Caption: 3-4 sentences max, end with "Full guide at haps.club" or "Link in bio"
- File at `images/post-YYYY-MM-DD-<topic>.svg`

### Carousel (1:1, IG feed, 5-7 slides)

When the user says "make a carousel":

- 1:1 (1080×1080) instead of 9:16
- Same 8-slide-style structure compressed to 5-7: open → 3-5 picks → CTA/close combined
- Each slide has the "Swipe →" prompt in the lower-right
- Caption replaces "link in bio" with "Swipe through →"

### Story sticker (9:16, IG story, single pick)

- 1080×1920 like a reel slide
- Larger type, less detail (stories are glanced at)
- Add a "Tap for more" or "Swipe up" prompt in the lower third where the IG sticker tray sits
- File at `images/story-YYYY-MM-DD-<topic>.svg`

---

## Workflow — step by step

When the user asks for a reel:

1. **Confirm the source.** Are the picks coming from (a) this week's site state, (b) the latest newsletter draft in Gmail, or (c) a topic/theme they're naming? Default: this week's site state.
2. **Verify the picks exist and dates are correct.** Run the `newsletter-date-check` skill if dates are involved. Cross-reference against the live `index.html` if pulling from the site.
3. **Pick the 4-5 strongest picks** for slides 3-6 (or 3-7 if doing 5 picks). Bias toward dated events for the current week + 1-2 evergreen/major upcoming events.
4. **Determine the featured pick** (slide 3). This should be the strongest single thing — usually matches the site's Editor's Pick.
5. **Read the May 11 reel** at `Hilex2030/haps-club-assets/html/reel-2026-05-11.html` for the template.
6. **Build the deck HTML** at `html/reel-YYYY-MM-DD.html` by adapting the template — replace illustrations and type per pick, keep the logo embeds and shell intact.
7. **Build 8 standalone SVGs** at `images/reel-YYYY-MM-DD/NN-name.svg`. These are the SVGs the downloader will fetch.
8. **Build the downloader page** at `html/download-reel-YYYY-MM-DD.html` by adapting the May 11 downloader — change only `BASE` and the `slides` array.
9. **Write the caption** using the proven recipe above.
10. **Report back** with: deck URL, downloader URL, caption (as a copyable block), and a one-line summary of which picks were used.

### Speed target

End-to-end, under 10 minutes from "make a reel for this week" to deck + downloader + caption all live. The May 11 session hit this. If it's taking longer, you're overthinking — the templates exist exactly so you don't have to design from scratch.

---

## Hard rules — these must not be broken

1. **Never fabricate events, dates, venues, or people.** If a pick can't be verified, leave it out. Run `web_search` on anything you don't have a primary source for.
2. **Never use real photos of venues, food, people, or events.** Even AI-generated photos of "SUSHISAMBA rooftop" are fabrication. Stick to SVG illustration.
3. **Never use copyrighted imagery.** No real album covers, no movie stills, no venue press photos, no Disney/Marvel/etc. ever.
4. **Always use the real Haps Club logo** on slides 1 and 8. Never fabricate a monogram or alternative mark.
5. **Always run `newsletter-date-check`** when dates are involved.
6. **Never introduce a third brand color or third font.**
7. **Never use exclamation marks in slide bodies or captions.**
8. **Never write to `/mnt/user-data/uploads/`** — it's read-only. Always push to the assets repo or write to `/mnt/user-data/outputs/`.
9. **Never write to `.github/workflows/`** — GitHub MCP can't write there (403).

---

## Known issues and context

1. **The user prefers concrete options to abstract recommendations.** When something has tradeoffs (e.g. PNG vs JPG, 8 slides vs 6, with-photos vs SVG-only), offer 2-3 concrete shapes rather than asking open-ended questions.

2. **GitHub MCP works for this user except for workflow files.** Push directly via `create_or_update_file` or `push_files`. Don't ask permission to push, just push and report.

3. **The user works on Mac, often from mobile.** Keep deploy instructions copy-pasteable. The downloader page exists specifically because mobile-only users can't easily run a screen recording of an 8-slide deck — they need PNGs they can drop into IG.

4. **The download page works best on desktop Chrome or Safari.** Mobile browsers throttle or block multi-file downloads. Note this in the report-back if the user is on mobile.

5. **Cost discipline:** the entire pipeline costs $0 to run — no AI image generation, no third-party APIs, no rendering services. SVG + browser-side Canvas only.

6. **Two repos, two purposes (carryover from website skill):**
   - `Hilex2030/haps-club` is the website
   - `Hilex2030/haps-club-assets` is where social reel assets, logos, and brand artifacts live
   - Social reels live in `haps-club-assets`, never in `haps-club`

---

## Related skills

- **`haps-club-website`** — the website's design system, color palette, logo URLs, voice rules. Social posts must match.
- **`haps-club-refresh`** — the weekly site refresh workflow. Social posts usually correspond to whatever week's picks just shipped to the site.
- **`haps-weekly-newsletter`** — Tuesday morning Kit newsletter. Picks often overlap with the reel. If both are being made the same week, the reel's featured slide should match the newsletter lead.
- **`newsletter-date-check`** — always run alongside this skill whenever dates are involved.

---

## Quick reference

| What | Value |
|------|-------|
| Reel dimensions | 1080 × 1920 (9:16) |
| Carousel dimensions | 1080 × 1080 (1:1) |
| Single post dimensions | 1080 × 1350 (4:5) or 1080 × 1080 (1:1) |
| Story dimensions | 1080 × 1920 (9:16) |
| Slide count for reels | 8 (open + hook + 4-5 picks + CTA + close) |
| Assets repo | `Hilex2030/haps-club-assets` |
| Logo navy URL | `https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/haps-club-logo.svg` |
| Logo white URL | `https://cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/images/haps-club-logo-white.svg` |
| Brand navy | `#292f71` |
| Brand accent | `#FF6B47` |
| Brand cream | `#FAFAF7` |
| Canonical template | `html/reel-2026-05-11.html` |
| Canonical downloader | `html/download-reel-2026-05-11.html` |
| Caption hashtag count | 12-15 |

---

## Example session (canonical, from May 11 2026)

User: "could you create a reel for social media for this, if yes can you pull image from the webs to use?"

Claude:
1. Declined to use web photos (copyright + fabrication concerns), offered three concrete options (text-driven reel, carousel, fill-in template)
2. User picked text-driven reel, 8 slides, with logo on open and close
3. Built `html/reel-2026-05-11.html` with all 8 slides as inline SVG
4. User noticed the logo was fabricated (HC monogram in a circle, not the real wordmark)
5. Fetched the real logo SVG paths, embedded as `<symbol>` definitions, recolored white version for the dark close slide
6. User asked for JPGs/PNGs
7. Built standalone SVG files for each slide at `images/reel-2026-05-11/`
8. Built `html/download-reel-2026-05-11.html` with Canvas-based PNG export
9. User asked for a caption
10. Wrote IG reel caption with hook + 4 pick paragraphs + CTA + 15 hashtags below dot break

Total time once the picks were locked: about 25 minutes including the logo correction round-trip. Should be faster next time because the templates exist now.

That's the model. Do this every time.
