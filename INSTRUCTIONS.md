# Haps Club — Daily Update Routine

You are updating the Haps Club homepage with fresh LA event recommendations sourced from my Gmail inbox. This runs **once per day**. Today's date is the date in the conversation context — use it as your reference for what counts as "current" and "upcoming."

## What you can and cannot change

**You may ONLY modify the events/content section of `index.html`, plus the two specific exceptions below.**

Do **NOT** touch:

- The `<head>` (meta tags, title, fonts, scripts, styles)
- The top navigation / topbar (logo, subscribe form)
- The hero / header section *(except the two exceptions below)*
- The footer
- The sponsor block (Blackbird or any other sponsor card)
- The tip-submission form
- Any CSS, any `<script>` blocks, any `<style>` rules
- Any class names, IDs, or structural markup outside the events list itself

**Two specific exceptions to the "don't touch" rules:**

1. **Greeting.** The greeting in the hero (currently "Good Evening" or any time-of-day phrase) should be changed to **"Welcome"** — a general greeting that works any time of day.
2. **Last-updated stamp.** A "Last updated" stamp should appear opposite the main date display in the hero (right side if the date is on the left, or vice versa). Format: `Last updated [Month D]` — e.g., `Last updated May 9`. Update this every time you commit. If a stamp already exists, replace its value; if not, add it inline with styling that matches the existing date display.

If you're unsure whether something is "content" or "structure," err on the side of leaving it alone.

## Step 1 — Read the inbox

Search Gmail for messages received in the **last 7 days** that contain LA event information. Run these searches in order:

1. `newer_than:7d (event OR opening OR pop-up OR popup OR show OR concert OR dinner OR party OR launch OR screening) -in:promotions -in:social`
2. `newer_than:7d to:michael@haps.club` — anything sent directly to me
3. `newer_than:7d from:(*@haps.club)` — tip-form submissions (subject usually starts with "Haps Club tip")
4. `newer_than:7d (RSVP OR invite OR invitation OR "you're invited")`

For each thread, read the full content. Skip:

- Newsletters I subscribe to (unless they name a specific dated event)
- Receipts, calendar notifications, password resets
- Spam, cold sales, unrelated work email
- The daily-update confirmation emails this routine sends to me (subject starts with `Haps Club daily update —`)

## Step 2 — Extract candidate events

For each plausible event, capture:

- **Name** (venue or event title)
- **Date and time** (specific — "this weekend" doesn't count; if no date is given, skip)
- **Location** (neighborhood + address if available)
- **One-line description** in my voice: dry, specific, no hype words like "amazing," "incredible," "must-see"
- **Source link** (venue site, Resy, Eventbrite, IG — whatever the email pointed to)
- **Source email** (sender + subject, for traceability)

Discard if:

- Date has passed
- Outside LA County
- Link is broken or behind a login wall
- Already covered (see Step 3 for the dedup check, with the repeat-event exception below)

## Step 3 — Repeating events (allowed and encouraged)

A previously-featured event **can** repeat in the list when it's high value. "High value" means at least one of:

- **Recurring** with a fresh upcoming date (a weekly residency, a Sunday market, a monthly opening) — the date moves, the listing refreshes
- **Long-running** and not yet seen by most readers (a museum show open through August, a popup running for two more weeks)
- **Endorsed twice** — it came in via two independent tips/sources, which is a strong signal

When you repeat an event:

- Use the **next upcoming date**, not the original one
- Refresh the description if the angle has changed (new menu, new headliner, last weekend, etc.) — otherwise leave the existing copy alone
- Flag it in the summary as "repeat — [reason]" so I can confirm

Don't repeat an event more than 3 weeks running without a new hook. Repetition without a fresh angle reads like filler.

## Step 4 — Read the current site

Pull the current `index.html` from `Hilex2030/haps-club` on `main`. Identify:

- The exact boundaries of the events section (where it starts, where it ends)
- The card markup pattern (classes, structure, date format) — match it precisely
- The hero greeting element (where "Good Evening" or similar lives)
- Whether a "Last updated" stamp already exists, and if so, where
- Which events are already listed and their dates
- Any event whose date has passed — these get removed

Your edit must leave everything outside the allowed-change zones byte-for-byte identical.

## Step 5 — Build the updated homepage

Produce a new `index.html` that:

- **Keeps** the head, nav, sponsor block, tip form, footer, all CSS, and all JS untouched
- **Replaces** any time-of-day greeting ("Good Evening," "Good Morning," etc.) with **"Welcome"**
- **Updates the "Last updated" stamp** in the hero to today's date (format: `Last updated [Month D]`), positioned opposite the main date display, styled to match
- **Removes** any event whose date has passed
- **Adds** the new candidates from Step 2, using the existing card markup exactly
- **Refreshes** repeating high-value events with their next date
- **Orders** events chronologically, soonest first
- **Caps** at ~8 visible events — if there are more, pick the strongest and list the rest in the summary

Tone rules for descriptions:

- 1–2 sentences, max 25 words
- No exclamation points, no "must," no "amazing"
- Lead with the concrete (what, where, when), not the adjective
- If you're guessing or filling in, flag it in the summary — never in the card itself

## Step 6 — Verify before committing

Before pushing, run these checks:

1. **Diff check.** Compare your new file to the current one. Allowed differences: the events section, the hero greeting ("Welcome"), and the "Last updated" stamp value. Everything else must be byte-for-byte identical. If anything else changed — even whitespace in the head, a moved `<script>` tag, a tweaked footer link — revert it and re-do the edit more surgically.
2. **Date check.** For every event, confirm the day-of-week matches the date. A Friday event listed as "Saturday" kills trust.
3. **Link check.** Use `web_fetch` on every event link. If it 404s or redirects somewhere unexpected, drop the event or fix the link.
4. **Tone read.** Anything that sounds like AI marketing copy gets rewritten in my voice or cut.
5. **Stamp sanity check.** Confirm the "Last updated" date matches today's date and is positioned/styled correctly.

## Step 7 — Commit

Commit the updated `index.html` to `Hilex2030/haps-club` on `main` with:

```
Daily update — [YYYY-MM-DD] — added [N], removed [M], repeated [R]
```

If nothing new is worth adding **and** no expired events need removing, still commit if the **"Last updated" stamp** needs to roll forward to today's date — the stamp itself is meaningful even on a "no changes" day. If genuinely nothing has changed (same day, no events expiring), skip the commit and proceed to Step 8 with a "no changes needed today" note.

## Step 8 — Email me a confirmation

After every run — whether you committed or not — send an email to **michael@haps.club** so I have a record in my inbox.

- **To:** `michael@haps.club`
- **Subject:** `Haps Club daily update — [Month D]` (e.g., `Haps Club daily update — May 9`). On no-op days, append ` (no changes)`.
- **Body:** the same summary described in Step 9, formatted as readable plain text or light HTML. Include the commit SHA and a link to the live site (`https://haps.club`) at the bottom.

If the email send fails, retry once. If it still fails, surface the error in the chat summary so I know the inbox record is missing — never silently drop it.

## Step 9 — Chat summary

Give me a chat summary with these sections (this is also the body of the Step 8 email):

- **Added:** new events with date + neighborhood
- **Repeated:** which events stayed on with refreshed dates, and why each qualified as high value
- **Removed:** what dropped off (expired / broken link / replaced)
- **Skipped but worth knowing:** inbox items that almost made it but didn't, with a one-line reason — so I can override
- **Flags:** anything uncertain (date parsing, unverified links, possible duplicates)
- **Commit:** SHA + message, or "no commit — nothing changed today"
