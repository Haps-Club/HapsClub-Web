# Haps Club Dashboard Refresh — SKILL

Refresh the command dashboard at `https://haps.club/dashboard/` (password `haps#2026`, noindex). The page renders entirely from `/dashboard/data.json`; a refresh means rewriting that JSON and pushing it. `index.html` only changes when the structure changes.

**Cadence:** fold into the Tuesday full sweep; on demand otherwise.

## Architecture

- `dashboard/index.html` — self-contained (inline CSS/JS, hand-rolled SVG charts, Haps brand: navy `#292f71`, coral `#FF6B47`, Instrument Serif + Inter). Fetches `data.json?v=<ts>`.
- `dashboard/data.json` — single source of truth. Top-level `generated_at` ISO timestamp plus a `sources` block recording when each feed was last refreshed (`null` = pending; the page renders honest empty states).
- `dashboard/seo/` — separate deep dive; do not touch except its existing back-link.

## Refresh steps

1. **GA4** — Composio, account `google_analytics_maim-marked`, property `properties/536909119`. Always apply `dimensionFilter` `hostName = haps.club` at query level. Pull: daily sessions/users (90d), top pages (30d), channel mix (30d). Property data begins 2026-05-09.
2. **GSC** — Composio, account `google_search_console_tactus-speedy`, site `sc-domain:haps.club`. Pull daily clicks/impressions (90d), top queries and pages (28d, end date 2 days back). Sparse data is expected; label it, do not pad it.
3. **Stripe** — Stripe MCP, read-only. `GetPaymentIntents` caps at 10/page regardless of `limit`; for aggregates use `search_stripe_resources` with `payment_intents:status:"succeeded" AND created>=X AND created<Y` month windows (search caps at 100 results — windowing avoids the cap). Amounts are cents. Update: monthly array (append/refresh current month with `"partial": true`), by_event, recent 10 (from the paginated list endpoint, which has timestamps), balance via `retrieve_balance`.
4. **Kit** — Kit MCP connector: `get_growth_stats` (subscribers point-in-time + net adds), `get_stats_for_a_list_of_broadcasts` (per-issue opens/clicks). If tool calls return "No approval received", the connector needs approval in the Claude UI.
5. **Uploads** — parse any Luma/Partiful/Kit/Instagram CSVs provided in-session and merge (registrations, check-ins, follower counts, per-issue stats).
6. **History discipline** — append one new point per metric per refresh (e.g. `audience.history`). Never overwrite accumulated history; trends only get good if points accumulate.
7. **Commit** — rewrite `dashboard/data.json` (`generated_at` + `sources` timestamps updated) and push via Composio `GITHUB_COMMIT_MULTIPLE_FILES` (owner `Haps-Club`, repo `haps-club`, branch `main`), one atomic commit. Include `index.html` only if structure changed.
8. **Verify** — `curl -s "https://haps.club/dashboard/data.json?v=$(date +%s)" | jq .generated_at` and confirm it updated (GitHub Pages lag 1–3 min). Spot-check homepage integrity markers untouched: GA `G-RKY63MK7ND`, Kit form `forms/9421017`, logo CDN, Blackbird, footer, `</html>`, `CNAME`.

## Guardrails

- Touch only `/dashboard/` paths (plus this skill file). Never homepage `index.html`, `CNAME`, `/archive/`, `sitemap.xml`, `llms.txt`, `robots.txt`.
- Do not add `/dashboard/` to `sitemap.xml` or `llms.txt`; keep `noindex,nofollow` meta.
- First Composio write of a session may return "No approval received" — wait 30–60s and retry.
- Brand only: navy/coral plus tints, no third color, no banned words, no exclamation marks.
- Payment counts ≠ attendees (multi-ticket orders exist); label accordingly.
