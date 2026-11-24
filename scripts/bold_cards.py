#!/usr/bin/env python3
"""bold_cards.py: bold editorial carousels (paper texture, heavy condensed headline, mustard serif-italic box).

  python3 scripts/bold_cards.py social/series-bold        # reads carousels.json, writes bold-<slug>-NN.jpg

carousels.json: {"carousels": [{"slug": "friends", "title": "...", "sub": "...",
                                 "slides": [{"h": "...", "box": "...", "body": "..."}], "end": {"h": "...", "box": "..."}}]}
Layout: Haps logo big top-left; nothing below y=1150 (Instagram overlay); no single word alone on a line.
"""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def nob(t):
    i = t.rfind(" ")
    return t[:i] + "&nbsp;" + t[i + 1:] if i > 0 and t.count(" ") >= 2 else t


def la(t):
    return t.replace("Los Angeles", "Los&nbsp;Angeles")


CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;background:#e9e6e1;color:#221d1a;font-family:'Inter Tight',sans-serif;position:relative}
.paper{position:absolute;inset:0;opacity:.55}
.bar{position:absolute;left:0;top:0;width:100%;height:14px;background:linear-gradient(90deg,#FF9500 0%,#FF4F00 40%,#AF52DE 75%,#292F71 100%)}
.logo{position:absolute;left:60px;top:44px;height:170px}
.count{position:absolute;right:70px;top:100px;font-family:'IBM Plex Mono',monospace;font-size:26px;letter-spacing:4px;opacity:.6}
.wrap{position:absolute;left:84px;right:90px;top:260px;bottom:270px;display:flex;flex-direction:column;justify-content:center}
.num{font-family:'Archivo',sans-serif;font-stretch:62%;font-weight:900;font-size:150px;line-height:.85;color:#FF4F00;margin-bottom:18px}
h1{font-family:'Archivo',sans-serif;font-stretch:72%;font-weight:900;letter-spacing:-2px;line-height:.92;text-wrap:balance}
.box{display:inline-block;align-self:flex-start;margin-top:34px;background:#E2B23A;padding:16px 26px 18px;max-width:880px;
font-family:'Source Serif 4',serif;font-style:italic;font-weight:600;line-height:1.15;text-wrap:balance}
.body{margin-top:30px;font-size:36px;line-height:1.3;max-width:860px;text-wrap:pretty;font-weight:500}
.foot{position:absolute;left:90px;right:90px;top:1090px;display:flex;justify-content:space-between;align-items:center;font-family:'IBM Plex Mono',monospace;font-size:24px}
.arrow{display:flex;align-items:center;gap:0}.arrow i{display:block;width:120px;height:2px;background:#221d1a}.arrow b{font-size:28px;line-height:1;margin-left:-4px}"""

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,900&family=Source+Serif+4:ital,wght@1,600'
         '&family=Inter+Tight:wght@500;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">')
PAPER = ('<svg class="paper" width="1080" height="1350"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" stitchTiles="stitch"/>'
         '<feColorMatrix values="0 0 0 0 .45  0 0 0 0 .42  0 0 0 0 .38  0 0 0 .22 0"/></filter><rect width="100%" height="100%" filter="url(#n)"/>'
         '<radialGradient id="v" cx="50%" cy="45%" r="75%"><stop offset="60%" stop-color="#fff" stop-opacity="0"/><stop offset="100%" stop-color="#8a8378" stop-opacity=".35"/></radialGradient>'
         '<rect width="100%" height="100%" fill="url(#v)"/></svg>')


def slide(i, n, h, box="", body="", num=None, hsize=150, bsize=40):
    numhtml = f'<div class="num">{num}</div>' if num else ""
    boxhtml = f'<div class="box" style="font-size:{bsize}px">{nob(la(box))}</div>' if box else ""
    bodyhtml = f'<div class="body">{nob(la(body))}</div>' if body else ""
    arrow = '<span class="arrow"><i></i><b>&rsaquo;</b></span>' if i < n else '<span>haps.club</span>'
    return (f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{CSS}</style></head><body>{PAPER}<div class="bar"></div>'
            f'<img class="logo" src="file://{ROOT}/assets/img/haps-logo.svg"><div class="count">{i:02d} / {n:02d}</div>'
            f'<div class="wrap">{numhtml}<h1 style="font-size:{hsize}px">{nob(la(h))}</h1>{boxhtml}{bodyhtml}</div>'
            f'<div class="foot"><span>Haps Club &middot; Los&nbsp;Angeles</span>{arrow}</div></body></html>')


def build(c):
    n = len(c["slides"]) + 2
    pages = [slide(1, n, c["title"], c["sub"], hsize=c.get("hsize", 150), bsize=44)]
    for k, s in enumerate(c["slides"], 2):
        pages.append(slide(k, n, s["h"], s.get("box", ""), s.get("body", ""), num=f"{k - 1:02d}", hsize=s.get("hsize", 104), bsize=36))
    e = c["end"]
    pages.append(slide(n, n, e["h"], e.get("box", ""), e.get("body", ""), hsize=e.get("hsize", 120), bsize=40))
    return pages


def main():
    folder = os.path.abspath(sys.argv[1])
    data = json.load(open(os.path.join(folder, "carousels.json"), encoding="utf-8"))
    tmp = tempfile.mkdtemp(prefix="haps-bold-")
    total = 0
    for c in data["carousels"]:
        for k, html in enumerate(build(c), 1):
            h = os.path.join(tmp, f"{c['slug']}-{k}.html")
            open(h, "w", encoding="utf-8").write(html)
            png = h[:-5] + ".png"
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=5000",
                            "--allow-file-access-from-files", "--window-size=1080,1350", f"--screenshot={png}", "file://" + h], capture_output=True)
            out = os.path.join(folder, f"bold-{c['slug']}-{k:02d}.jpg")
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90", png, "--out", out], capture_output=True)
            if not os.path.exists(out):
                sys.exit("render failed: " + out)
            total += 1
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{total} slides in {folder}")


if __name__ == "__main__":
    main()
