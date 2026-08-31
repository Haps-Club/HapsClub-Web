#!/usr/bin/env python3
"""
Haps Club weekly homepage refresh — the mechanical half.

Enforces the three standing rules on data/events.json:
  1. featured is always exactly 3
  2. events run chronologically, soonest first, evergreen below
  3. anything whose `ends` has passed is gone

Usage (on the Composio workbench, from anywhere):
    python3 weekly_refresh.py                       # prune + sort, report
    python3 weekly_refresh.py --featured picks.json # also splice in new featured cards

Writes /tmp/events.new.json and prints a JSON summary. Commits nothing.
"""
import argparse, datetime, json, subprocess, sys

RAW = "https://raw.githubusercontent.com/Haps-Club/HapsClub-Web/main/data/events.json"
OUT = "/tmp/events.new.json"
MON = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
AREAS = {"westside","midcity","dtla","hollywood","eastside","citywide"}
FMT = "%Y%m%dT%H%M%S"


def ts(s):
    return datetime.datetime.strptime(s, FMT) if s else None


def load(path=None):
    if path:
        return json.load(open(path))
    raw = subprocess.run(["curl", "-fsSL", RAW], capture_output=True, text=True, check=True).stdout
    return json.loads(raw)


def refresh(d, now, picks=None):
    alive = lambda x: (ts(x.get("ends")) or now + datetime.timedelta(days=1)) > now
    dropped = {k: [e["title"] for e in d.get(k, []) if not alive(e)]
               for k in ("featured", "events", "plan")}
    for k in ("featured", "events", "plan"):
        if k in d:
            d[k] = [e for e in d[k] if alive(e)]
    if d.get("announcement") and not alive(d["announcement"]):
        d.pop("announcement")

    # splice in new featured cards, newest picks first, cap at 3
    for p in (picks or []):
        if p["title"] not in [f["title"] for f in d["featured"]]:
            d["featured"].append(p)
        if not any(e["title"] == p["title"] for e in d["events"]):
            k = ts(p.get("starts")) or ts(p.get("ends"))
            d["events"].append({
                "title": p["title"],
                "month": MON[k.month - 1] if k else "New", "day": str(k.day) if k else "★",
                "cat": p["tags"].split()[0].capitalize(), "tags": p["tags"], "area": p["area"],
                "where": p.get("where", ""), "price": p.get("price", ""), "link": p["link"],
                **({"starts": p["starts"]} if p.get("starts") else {}),
                **({"ends": p["ends"]} if p.get("ends") else {}),
            })

    key = lambda x: ((0, ts(x.get("starts")) or ts(x.get("ends"))) if (x.get("starts") or x.get("ends")) else (1, now))
    d["featured"].sort(key=key)
    d["featured"] = d["featured"][:3]
    d["events"].sort(key=key)

    # a run whose printed label has already passed gets relabelled to its end date
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    relabelled = []
    for e in d["events"]:
        k = ts(e.get("starts")) or ts(e.get("ends"))
        if k and e["month"] in MON and e["day"].isdigit():
            if datetime.datetime(now.year, MON.index(e["month"]) + 1, int(e["day"])) < midnight:
                relabelled.append(e["title"])
                e["month"], e["day"] = MON[k.month - 1], str(k.day)

    monday = now + datetime.timedelta(days=(7 - now.weekday()) % 7 or 7) if now.weekday() != 0 else now
    d["updated"] = now.strftime("%Y-%m-%d")
    d["weekLabel"] = "Week of " + monday.strftime("%b %-d")

    bad = [e["title"] for e in d["events"] if e.get("area") not in AREAS]
    return {
        "dropped": dropped,
        "relabelled": relabelled,
        "featured": [f["title"] for f in d["featured"]],
        "featured_slots_to_fill": 3 - len(d["featured"]),
        "events": len(d["events"]),
        "weekLabel": d["weekLabel"],
        "bad_area": bad,
        "next_up": [(e["month"], e["day"], e["title"]) for e in d["events"][:6]],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--featured", help="JSON file: array of new featured cards to splice in")
    ap.add_argument("--infile", help="read events.json from disk instead of the live raw URL")
    ap.add_argument("--now", help="override current time, YYYYmmddTHHMMSS (testing)")
    a = ap.parse_args()

    now = ts(a.now) if a.now else datetime.datetime.now()
    d = load(a.infile)
    picks = json.load(open(a.featured)) if a.featured else []
    summary = refresh(d, now, picks)

    assert len(d["featured"]) <= 3, "featured overflow"
    assert d.get("archive") and d.get("sponsor"), "archive/sponsor must survive"
    json.dump(d, open(OUT, "w"), ensure_ascii=False, indent=2)
    open(OUT, "a").write("\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if summary["featured_slots_to_fill"]:
        print(f"\n!! {summary['featured_slots_to_fill']} featured slot(s) empty — "
              "write picks.json and re-run with --featured picks.json", file=sys.stderr)


if __name__ == "__main__":
    main()
