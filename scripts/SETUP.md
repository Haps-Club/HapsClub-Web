# Haps Club daily review — setup

A daily automation for `haps.club`. Every morning at 9am Pacific, you get
**one email** at `michael@haps.club` summarizing what changed overnight.
The live site never changes until you tap one button on a GitHub Issue.

---

## Quick status (current state of this repo)

✅ `scripts/daily_report.py` — installed
✅ `scripts/process_approval.py` — installed
✅ `scripts/requirements.txt` — installed
⏳ `scripts/workflows/daily-report.yml` — needs to be moved to `.github/workflows/daily-report.yml`
⏳ `scripts/workflows/process-approval.yml` — needs to be moved to `.github/workflows/process-approval.yml`
⏳ Secrets — need `ANTHROPIC_API_KEY` and `GMAIL_TOKEN_JSON` added to repo

The two workflow files are in `scripts/workflows/` because the integration
that pushed everything else cannot write to `.github/workflows/` for security
reasons. The two-click move below activates them.

---

## Step 1: Move the workflow files (60 seconds)

GitHub's UI lets you rename a file's path to "move" it. Do this twice:

**File 1:** Open https://github.com/Hilex2030/haps-club/blob/main/scripts/workflows/daily-report.yml
- Click the pencil icon (top right)
- Change the filename at the very top of the page from `daily-report.yml` to:
  `../../.github/workflows/daily-report.yml`
- The path display will auto-update to show `.github/workflows/daily-report.yml`
- Scroll down, click "Commit changes"

**File 2:** Open https://github.com/Hilex2030/haps-club/blob/main/scripts/workflows/process-approval.yml
- Same thing: edit, change filename to `../../.github/workflows/process-approval.yml`
- Commit

After both moves, the workflows are live.

---

## Step 2: Add the two secrets (20 minutes total)

### A — Anthropic API key (3 minutes)

1. Go to https://console.anthropic.com → Settings → API Keys → Create Key
2. Add ~$5 of credits (this runs ~$0.05/day)
3. Copy the key (starts with `sk-ant-`)
4. Go to https://github.com/Hilex2030/haps-club/settings/secrets/actions
5. "New repository secret" → Name: `ANTHROPIC_API_KEY` → paste key → Save

### B — Gmail OAuth token (15 minutes, one-time on your Mac)

```bash
# On your Mac:
mkdir -p ~/haps-auth && cd ~/haps-auth

# 1) Create OAuth client at https://console.cloud.google.com:
#    - Pick or create a project
#    - APIs & Services → Enable: "Gmail API"
#    - Credentials → Create Credentials → OAuth client ID → Desktop app
#    - Download JSON → save as `credentials.json` here

# 2) Generate token:
pip install google-auth-oauthlib google-api-python-client

cat > get_token.py <<'PY'
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)
print("\n=== Copy everything below into GitHub secret GMAIL_TOKEN_JSON ===\n")
print(creds.to_json())
PY

python3 get_token.py
# Browser opens — sign in as newsletter@haps.club. Grant both permissions.
# Copy the JSON printed at the end.
```

3. Go to https://github.com/Hilex2030/haps-club/settings/secrets/actions
4. "New repository secret" → Name: `GMAIL_TOKEN_JSON` → paste the JSON → Save

---

## Step 3: Test it (30 seconds)

1. Go to https://github.com/Hilex2030/haps-club/actions
2. Click "Daily Haps Club report" in the left sidebar
3. Top right → "Run workflow" → Run workflow

Within ~30 seconds you should see:
- A new issue titled "Haps Club daily — Monday, May 11, 2026" appear in the Issues tab
- An email at michael@haps.club
- A new branch called `pending-review` in the repo

If something breaks, open the workflow run for full logs. The most common
failure is misconfigured Gmail OAuth — re-do Step 2B if the email never arrives.

---

## How the daily flow works

**9am Pacific:** workflow fires automatically.

The bot reads `index.html`, removes any dated event whose date has passed
(no grace period — gone the day after), then scans `newsletter@haps.club`
for new picks using Claude Haiku 4.5. Anything it finds gets written to a
branch called `pending-review` (not main). It opens a GitHub Issue listing
all proposed changes, and emails you a link.

**You open the email,** tap the GitHub link, see the picks, and decide:

- **Approve all** → add label `approved-all`, close the issue → site updates within 60s
- **Reject all** → add label `rejected`, close → nothing changes
- **Approve some** → comment `approve: 1, 3` then close → only those picks merge
- **Do nothing** → site stays as-is; tomorrow's run rebuilds from main

Evergreens (museums, restaurants, ongoing things — items without a date)
accumulate up to 30; when over, the oldest get dropped automatically.

---

## Rollback / kill switch

Three ways to undo or stop:

1. **Pause the cron:** edit `.github/workflows/daily-report.yml`, comment out
   the `schedule:` block, commit. The 9am run stops.
2. **Revert a bad commit:** GitHub → commit → "Revert this commit" → done.
3. **Edit `index.html` directly on main** — the bot doesn't interfere with
   manual edits. It just builds from whatever's on main each morning.
