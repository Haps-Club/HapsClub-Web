# Haps Club automation — operations runbook

This is the **humans-only** runbook for the daily pipeline. Read this when
something's wrong and you need to fix it, or when you want to understand
what's running.

For the design and architecture, see `SETUP.md` (initial setup) and the
project's Claude skill `haps-club-automation` (full architecture).

---

## Daily flow (what should be happening)

| Time (PT) | What happens |
|---|---|
| 9:00 AM | `daily-report.yml` cron fires |
| 9:00–9:02 | Bot prunes expired events, scans `newsletter@haps.club`, builds proposed `index.html` |
| 9:02 | Bot pushes to `pending-review` branch |
| 9:02 | Bot opens GitHub Issue titled `Haps Club daily — <date>` with `haps-daily` label |
| 9:02–9:03 | Bot emails `michael@haps.club` with the issue link |
| Whenever | Michael opens the issue, decides, closes with a label |
| +30s | `process-approval.yml` fires on the close event |
| +60s | If approved: `main` updates, `pending-review` deleted, confirmation comment posted |
| +120s | `haps.club` reflects the new content via GitHub Pages |

If any link in that chain is broken, the section below tells you where to look.

---

## Diagnostic order of operations

When something's wrong, check these in order. Stop at the first one that's red:

### 1. Did the cron actually fire?

Go to https://github.com/Hilex2030/haps-club/actions and look for "Daily Haps
Club report" entries from this morning.

- **Run exists, green:** cron fired and finished cleanly. Go to step 2.
- **Run exists, red:** cron fired but the bot crashed. Click the run, expand
  "Run daily report" step, read the Python traceback at the bottom. Common
  causes are in the failure catalog below.
- **No run at all from this morning:** the cron didn't fire. Either:
  - The workflow was disabled (Actions tab → "Daily Haps Club report" → check for "Enable workflow" button).
  - GitHub Actions had an outage (check https://status.github.com).
  - The cron expression is wrong (check `.github/workflows/daily-report.yml` for `cron: "0 16 * * *"`).
  - The workflow file has a syntax error (would show as a separate failure on the commit page).

### 2. Did the issue get created?

Go to https://github.com/Hilex2030/haps-club/issues?q=label%3Ahaps-daily

- **Today's issue is there:** the bot ran end-to-end. If you didn't get an
  email, it's a send-side problem (step 3). If the issue looks wrong, it's
  a content problem (step 4).
- **No issue from today:** the bot ran but couldn't open the issue. In the
  workflow run logs, search for `[issue] failed:`. Most common cause is a
  `GITHUB_TOKEN` permission issue — verify `permissions: { issues: write }`
  is still in `daily-report.yml`.

### 3. Did the email arrive?

Check `michael@haps.club`. Check spam too.

- **Email is in spam:** mark "not spam." This happens occasionally for new
  bot senders. After 2-3 corrections Gmail learns.
- **No email at all:** workflow run logs will say `[email] failed to send: <reason>`.
  Most common: expired Gmail OAuth refresh token. See "Refreshing the Gmail token" below.

### 4. Did the right picks show up (or get pruned)?

If the issue body looks wrong:

- **Missing picks the bot should have found:** verify the source newsletter
  actually landed in `newsletter@haps.club` Inbox before 9am, and that it
  was unread. The bot only reads unread mail from the last 3 days.
- **Fabricated picks:** check the source emails — did the bot have the data,
  or did Haiku invent it? Filter against the workflow run logs which print
  `[claude] extraction failed for ...` for empty extractions.
- **Wrong date on a pick:** Haiku 4.5 occasionally miscomputes ISO dates
  from natural-language references like "this Friday." If this happens
  more than once a week, sharpen the system prompt in
  `extract_events_with_claude()`.
- **Expired event still showing on main:** check whether the card has a
  `data-event-end` attribute at all. Evergreens (no end date) are never
  pruned. Either add the attribute or remove the card by hand.

### 5. Did approval merge to main?

If you closed the issue and the site didn't update:

- Go to https://github.com/Hilex2030/haps-club/actions and look for "Process
  Haps approval" runs.
- **No run:** the issue probably wasn't labeled `haps-daily`. The trigger
  is gated on that label. If you closed an issue that the bot didn't create,
  no approval workflow fires.
- **Run exists, red:** click the run, read the Python traceback.
- **Run exists, green, but no commit to main:** the bot detected "no decision"
  from the labels and comments. Either re-open the issue and add label
  `approved-all` then close it again, or just merge `pending-review` into
  `main` manually via the GitHub UI.

---

## Failure catalog

### "Gmail authentication failed" / "token has been expired or revoked"

The OAuth refresh token has expired. Gmail's free OAuth refresh tokens can
expire after 6 months of inactivity, or if the user revokes access in their
Google Account security settings.

**Fix:**

```bash
cd ~/haps-auth   # or wherever you ran setup the first time
python3 get_token.py
# Browser opens, sign in as newsletter@haps.club, grant both scopes.
# Copy the new JSON output.
```

Then update the `GMAIL_TOKEN_JSON` secret at
https://github.com/Hilex2030/haps-club/settings/secrets/actions.

### "ANTHROPIC_API_KEY missing"

The secret got deleted or was never set. Get a key from
https://console.anthropic.com → API Keys, and re-add the secret.

### "model_not_found" or similar Claude API error

Anthropic occasionally deprecates older model strings. The current model
is `claude-haiku-4-5` (set in `extract_events_with_claude` in `daily_report.py`).
If this stops working, check https://docs.claude.com/en/docs/about-claude/models
for the current Haiku model ID.

### "pending-review branch already exists" merge conflict

Shouldn't happen — the bot force-pushes — but if it does:

```bash
git push origin --delete pending-review
```

Tomorrow's run recreates it cleanly.

### Issue body is malformed, partial approval fails

The partial-approval parser (`parse_issue_picks` in `process_approval.py`)
matches a specific regex against the issue body that `format_issue_body`
produces. If you change one, change both. The current format is:

```
**N. Headline text**
📍 Address
🔗 https://url
```

If the regex stops finding picks, dump the issue body and verify it still
matches.

### Bot pushes empty changes (commits with no diff)

Built-in guard: `daily_report.py` checks `git diff --quiet` against `main`
before committing. If you see empty commits, the guard's broken — check the
log for "[git] no changes vs main, skipping" lines.

### Site looks broken after a merge

1. Open the offending commit on GitHub: https://github.com/Hilex2030/haps-club/commits/main
2. Click "Revert this commit." Merges to a PR; merge the PR.
3. Site recovers within 60s.
4. Open the original GitHub Issue (still closed) for triage, or open a new
   issue describing what went wrong.

---

## Manual operations

### Trigger a daily run on demand

GitHub → Actions → "Daily Haps Club report" → "Run workflow"

Options:
- `skip_inbox`: skips Gmail scan and Claude extraction (useful when testing prune/cap logic)
- `skip_email`: doesn't send the email (issue still gets created)

### Run end-to-end test before the real 9am

```bash
# Locally, with all secrets set as env vars:
git clone https://github.com/Hilex2030/haps-club && cd haps-club
pip install -r scripts/requirements.txt

# Dry run, skipping inbox:
SKIP_INBOX=true python3 scripts/daily_report.py
```

This won't push or email (no `GH_TOKEN` set), but exercises the prune/cap
logic and prints what would change.

### Pause the daily automation

Edit `.github/workflows/daily-report.yml`, comment out the `schedule:`
block, commit to `main`. Cron stops immediately. Manual `workflow_dispatch`
still works for testing. Re-enable by uncommenting.

### Permanently delete a card

Edit `index.html` on `main` via the GitHub web UI. The bot doesn't fight
manual edits — it just reads whatever's on `main` each morning and builds
from there.

### Force the bot to forget about an email it already saw

The bot marks emails read after extracting from them. To reprocess:

1. Open `newsletter@haps.club` in Gmail web UI
2. Find the message
3. Right-click → "Mark as unread"
4. Wait for tomorrow's 9am run, or trigger manually

---

## Monitoring & alerts

GitHub Actions emails the repo admin on workflow failures by default. If
you're not getting these:

- https://github.com/settings/notifications → "Actions" → enable email
  notifications for failed workflows.

There's no separate uptime monitor. The daily email itself is the heartbeat
— if it stops arriving, something's broken. If you go a week without a daily
email and didn't pause anything, run the diagnostic flow above.

---

## Costs

- **Anthropic API:** ~$0.05/day, ~$1.50/month at typical volume. Monitor at
  https://console.anthropic.com/usage.
- **GitHub Actions:** free (well under the public-repo allowance).
- **Gmail API:** free.

If costs spike, the most likely cause is an inbox flood — the bot has a cap
of 25 messages per run, so even an extreme day costs maybe $0.20.

---

## When to ask Claude for help

If something on this list isn't covered, or you're not sure where to start,
opening a fresh Claude conversation and saying "the Haps Club automation is
broken — here's what I'm seeing: [paste]" will work fine. Claude has the
`haps-club-automation` skill which covers the full architecture.

If the fix involves changing the workflow files (`.github/workflows/*.yml`),
remember that Claude can't write there directly — it'll either give you the
new YAML to paste, or push to `scripts/workflows/` and tell you to rename.

---

## Change log

- **2026-05-11:** Pipeline created. Daily-review architecture, no grace
  period on prune, evergreen cap at 30, GitHub Issue approval flow.
