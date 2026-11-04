#!/usr/bin/env python3
"""sweep.py — one command that keeps the whole site fresh. Safe to run any time, any number of times.

    python3 scripts/sweep.py            # do everything, then run the checks
    python3 scripts/sweep.py --no-checks

In order:
  1. data      current week label; "New" badges older than settings.new_badge_days become evergreen
  2. homepage  build_home.py: drops anything past its end time, re-sorts, keeps 3 featured, rebuilds index.html
  3. guides    build_pages.py: refreshes every guide's live event list and schema, drops finished events
  4. chrome    normalize_chrome.py: header/footer/year, font + cache-buster hashes on every page
  5. feeds     build_feeds.py: calendar.ics, feed.xml, llms-full.txt, llms.txt "This week"
  6. checks    check_site.py, check_seo.py, check_links.py --internal (exit 1 if any fail)

Nothing is hard-coded: tunables live in data/settings.json, content in data/events.json.
The daily GitHub workflow runs this and commits whatever changed.
"""
import datetime
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS = os.path.join(ROOT, "data", "events.json")
CFG = json.load(open(os.path.join(ROOT, "data", "settings.json"), encoding="utf-8"))
TODAY = datetime.datetime.now(ZoneInfo(CFG["timezone"])).date()


def run(*args):
    r = subprocess.run([sys.executable] + list(args), cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def load():
    return json.load(open(EVENTS, encoding="utf-8"))


def save(d):
    with open(EVENTS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")


def refresh_data():
    """Week label follows the calendar; 'New' badges expire instead of living forever."""
    d, notes = load(), []
    monday = TODAY - datetime.timedelta(days=TODAY.weekday())
    label = "Week of " + monday.strftime("%b ") + str(monday.day)
    if d.get("weekLabel") != label:
        d["weekLabel"] = label
        notes.append(f"week label -> {label}")
    stamped = aged = 0
    for sec in ("events", "featured", "plan"):
        for x in d.get(sec, []):
            if x.get("month") != "New":
                continue
            if not x.get("added"):
                x["added"] = TODAY.isoformat()
                stamped += 1
            elif (TODAY - datetime.date.fromisoformat(x["added"])).days > CFG["new_badge_days"]:
                x["month"] = "Any"
                aged += 1
                notes.append(f"'{x['title']}' no longer new (added {x['added']})")
    if stamped:
        notes.append(f"{stamped} 'New' pick(s) now have a {CFG['new_badge_days']}-day clock")
    if notes:
        d["updated"] = TODAY.isoformat()
        save(d)
    return notes


def main():
    out = []
    before = open(EVENTS, "rb").read()
    out += ["data: " + n for n in refresh_data()] or ["data: current"]

    code, text = run("scripts/build_home.py")
    out.append("homepage: " + text.replace("\n", " | "))
    if open(EVENTS, "rb").read() != before and load().get("updated") != TODAY.isoformat():
        d = load(); d["updated"] = TODAY.isoformat(); save(d)      # build_home pruned expired items
    steps = [("guides", ["scripts/build_pages.py"]), ("chrome", ["scripts/normalize_chrome.py"]),
             ("feeds", ["scripts/build_feeds.py"])]
    for name, cmd in steps:
        code, text = run(*cmd)
        last = text.splitlines()[-1] if text else ""
        out.append(f"{name}: {'ok' if code == 0 else 'FAILED'} {last[:100]}")
        if code:
            print("\n".join(out)); sys.exit(code)
    # the feeds embed the data's `updated` date and week label, so rebuild them after the final data write
    run("scripts/build_feeds.py")

    failed = []
    if "--no-checks" not in sys.argv:
        for name, cmd in (("site", ["scripts/check_site.py"]), ("seo", ["scripts/check_seo.py"]),
                          ("links", ["scripts/check_links.py", "--internal"])):
            code, text = run(*cmd)
            out.append(f"check {name}: {'ok' if code == 0 else 'FAILED'}")
            if code:
                failed.append((name, text))
    print("\n".join(out))
    for name, text in failed:
        print(f"\n--- {name} ---\n{text[-1800:]}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
