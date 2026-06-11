# Haps Club Dashboard Refresh — SKILL

Refresh the command dashboard at `https://haps.club/dashboard/` (password `haps#2026`, noindex). The page renders entirely from `/dashboard/data.json`; a refresh means rewriting that JSON and pushing it. `index.html` only changes when the structure changes.

**Cadence:** fold into the Tuesday full sweep; on demand otherwise.

## Architecture

- `dashboard/index.html` — self-contained (inline CSS/JS, hand-rolled SVG charts, Haps brand: navy `#292f71`, coral `#FF6B47`, Instrument Serif + Inter, logo from `cdn.jsdelivr.net/gh/Hilex2030/haps-club-assets@main/`). Fetches `data.json?v=<ts>`. Modules: overview tiles, events + signup cadence chart, revenue, audience/newsletter, traffic + outbound clicks, GSC, Instagram. Every module renders an honest empty state when its data block is null.
- `dashboard/data.json` — single source of truth. Top-level `generated_at` ISO timestamp plus a `sources` block recording when each feed was last refreshed (`null` = pending).
- `dashboard/seo/` — separate deep dive; do not touch except its existing back-link.

## Refresh steps

1. **GA4** — Composio, account `google_analytics_maim-marked`, property `properties/536909119`. Always apply `dimensionFilter` `hostName = haps.club` at query level. Pull in one `GOOGLE_ANALYTICS_BATCH_RUN_REPORTS` call (max 5 requests): daily sessions since 2026-05-09, top pages (30d), channel mix (30d), and outbound clicks (`eventName = click` + `hostName` in an `andGroup`, dimension `linkUrl`, metric `eventCount`). Outbound clicks are the card-click tracking — GA4 enhanced measurement logs them automatically, no site code needed. Map raw linkUrls to short human labels in `traffic.ga4.outbound_clicks.items`.
2. **GSC** — Composio, account `google_search_console_tactus-speedy`, site `sc-domain:haps.club`. Daily clicks/impressions, top queries and pages (28d, end date 2 days back). Sparse data is expected; label it, do not pad it.
3. **Stripe** — Stripe MCP, read-only. `GetPaymentIntents` caps at 10/page regardless of `limit`; for aggregates and cadence use `search_stripe_resources` with `payment_intents:status:"succeeded" AND created>=X AND created<Y` (search caps at 100 results — windowing avoids it). Amounts are cents. Use PT-midnight epochs (UTC midnight + 25200) for day windows. Update: monthly array (current month gets `"partial": true`), by_event, recent 10 (the paginated list endpoint has timestamps), balance via `retrieve_balance`.
   - **Refund policy:** Proper Hotel dinner series (Apr 2026, 8 payments, $1,540) was fully refunded and is excluded everywhere; keep the explanatory note on `revenue.note`. Stripe search still returns these PIs as succeeded — subtract them. Apply the same treatment to any future fully-refunded event.
4. **Signup cadence** (`cadence` block) — cumulative payments vs days-until-event per event, target line at 100. Maintain the Solstice series daily (one PT-day window per missing day, append `{days_out, cum}`); Cinco is frozen weekly history (13/22/34/58 at 21/14/7/0 days out, event 2026-05-05). When a new event starts selling, add a series and keep past events for comparison. Counts are payments, not headcount.
5. **Kit** — Kit MCP: `get_growth_stats` (subscribers + net adds), `get_stats_for_a_list_of_broadcasts` (per-issue opens/clicks). If calls return "No approval received" even with always-allow set, the connector needs a disconnect/reconnect in Settings → Connectors.
6. **Instagram** — no connector; Michael pastes professional-dashboard insights in-session. Map into `engagement.instagram` (followers, views + follower split, reach, content-type mixes, interactions, profile activity, active_times, top content).
7. **Uploads** — parse any Luma/Partiful/Kit CSVs provided and merge (registrations, check-ins, per-issue stats).
8. **History discipline** — append one point per metric per refresh (e.g. `audience.history`, cadence points). Never overwrite accumulated history.
9. **Commit** — rewrite `dashboard/data.json` (`generated_at` + `sources` updated) and push via Composio `GITHUB_COMMIT_MULTIPLE_FILES` (owner `Haps-Club`, repo `haps-club`, branch `main`), one atomic commit. Include `index.html` only if structure changed. Large-file relay when needed: base64 the file as `.txt`, upload to tmpfiles.org, fetch the `/dl/` URL with a `Mozilla/5.0` UA inside `COMPOSIO_REMOTE_WORKBENCH`, sha256 round-trip verify, then `run_composio_tool('GITHUB_COMMIT_MULTIPLE_FILES', ...)` from the workbench.
10. **Verify** — wait ~75s for Pages, then `curl "https://haps.club/dashboard/data.json?v=<ts>"` and confirm `generated_at` updated. Spot-check homepage integrity markers untouched: GA `G-RKY63MK7ND`, Kit form `forms/9421017`, logo CDN, Blackbird, footer, `</html>`, `CNAME`.

## Guardrails

- Touch only `/dashboard/` paths (plus this skill file). Never homepage `index.html`, `CNAME`, `/archive/`, `sitemap.xml`, `llms.txt`, `robots.txt`.
- Do not add `/dashboard/` to `sitemap.xml` or `llms.txt`; keep `noindex,nofollow` meta.
- First Composio write of a session may return "No approval received" — wait 30–60s and retry.
- `node --check` the inline script and JSON-validate `data.json` before every push.
- Brand only: navy/coral plus tints, no third color, no banned words (leverage, streamline, ecosystem, curated), no exclamation marks. Logo sizes: topbar 75px, gate 110px.
- Payment counts ≠ attendees (multi-ticket orders exist); label accordingly.
