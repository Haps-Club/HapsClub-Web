#!/usr/bin/env python3
"""quote_cards.py: graphic Haps quote cards (no photos), centered script type.

  python3 scripts/quote_cards.py social/series-quotes      # reads quotes.json, writes quote-NN.jpg + _preview.png

quotes.json: {"quotes": [{"slug": "warhol", "quote": "...", "who": "Andy Warhol", "where": "POPism, 1980",
                          "send": "your plastic friend", "theme": "cream|orange|navy|pink"}]}
"Los Angeles" and "L.A." never break across lines. Nothing here publishes anything.
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

THEMES = {  # background, quote ink, accent, small text
    "cream":  ("#F4F1EC", "#1a1f4d", "#FF4F00", "#6b6862"),
    "orange": ("#FF4F00", "#FFFFFF", "#1a1f4d", "#FFE3D6"),
    "navy":   ("#1a1f4d", "#FFFFFF", "#FF9500", "#B9BEE6"),
    "pink":   ("#FBE1EA", "#1a1f4d", "#FF4F00", "#7a5b66"),
}

SUN = '<svg viewBox="0 0 100 100" width="{s}" height="{s}"><circle cx="50" cy="50" r="22" fill="{c}"/>' + \
      "".join(f'<rect x="48" y="4" width="4" height="14" rx="2" fill="{{c}}" transform="rotate({a} 50 50)"/>' for a in range(0, 360, 45)) + "</svg>"
PALM = ('<svg viewBox="0 0 100 160" width="{w}" height="{h}"><path d="M52 160 C50 120 48 90 50 60" stroke="{c}" stroke-width="5" fill="none" stroke-linecap="round"/>'
        '<path d="M50 60 C35 40 15 40 2 52 C18 44 34 48 50 60 Z" fill="{c}"/><path d="M50 60 C65 40 85 40 98 52 C82 44 66 48 50 60 Z" fill="{c}"/>'
        '<path d="M50 60 C42 34 30 20 14 16 C30 26 40 40 50 60 Z" fill="{c}"/><path d="M50 60 C58 34 70 20 86 16 C70 26 60 40 50 60 Z" fill="{c}"/>'
        '<path d="M50 60 C50 36 50 20 50 6 C54 22 54 40 50 60 Z" fill="{c}"/></svg>')
SPARK = '<svg viewBox="0 0 40 40" width="{s}" height="{s}"><path d="M20 0 C22 14 26 18 40 20 C26 22 22 26 20 40 C18 26 14 22 0 20 C14 18 18 14 20 0 Z" fill="{c}"/></svg>'


def keep_together(t):
    t = html.escape(t)
    t = re.sub(r"Los Angeles", "Los&nbsp;Angeles", t)
    t = re.sub(r"L\.\s?A\.", "L.A.", t)
    return t


FONTS = {  # family, css name, size scale, line-height
    "yellowtail": ("Yellowtail", "'Yellowtail',cursive", 1.0, 1.12),
    "pacifico": ("Pacifico", "'Pacifico',cursive", 0.78, 1.35),
    "caveat": ("Caveat:wght@600", "'Caveat',cursive", 1.0, 1.05),
    "shrikhand": ("Shrikhand", "'Shrikhand',cursive", 0.74, 1.2),
    "marker": ("Permanent+Marker", "'Permanent Marker',cursive", 0.72, 1.2),
    "greatvibes": ("Great+Vibes", "'Great Vibes',cursive", 1.05, 1.15),
    "dmserif": ("DM+Serif+Display:ital@1", "'DM Serif Display',serif", 0.86, 1.08),
    "lobster": ("Lobster", "'Lobster',cursive", 0.86, 1.15),
}


def card(q):
    bg, ink, acc, small = THEMES[q.get("theme", "cream")]
    n = len(q["quote"])
    size = 150 if n < 30 else 128 if n < 60 else 104 if n < 95 else 88 if n < 130 else 76 if n < 180 else 66
    fam, css, scale, lh = FONTS[q.get("font", "yellowtail")]
    size = int(size * scale)
    logo_filter = "" if q.get("theme", "cream") in ("cream", "pink") else "filter:brightness(0) invert(1);"
    deco = (f'<div class="sun">{SUN.format(s=150, c=acc)}</div>'
            f'<div class="palm l">{PALM.format(w=120, h=190, c=acc)}</div>'
            f'<div class="palm r">{PALM.format(w=90, h=150, c=acc)}</div>'
            f'<div class="sp a">{SPARK.format(s=38, c=acc)}</div><div class="sp b">{SPARK.format(s=26, c=acc)}</div>'
            f'<div class="sp c">{SPARK.format(s=30, c=acc)}</div>')
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family={fam}&family=Yellowtail&family=Inter+Tight:wght@500;700;800&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:{bg};overflow:hidden;font-family:'Inter Tight',sans-serif}}
.c{{position:relative;width:1080px;height:1350px;display:flex;flex-direction:column;align-items:center;text-align:center}}
.bar{{position:absolute;left:0;top:0;width:100%;height:14px;background:linear-gradient(90deg,#FF9500 0%,#FF4F00 40%,#AF52DE 75%,#292F71 100%)}}
.logo{{margin-top:70px;height:118px;{logo_filter}}}
.badge{{margin-top:34px;font-family:'IBM Plex Mono',monospace;font-size:26px;letter-spacing:6px;color:{ink};border:3px solid {ink};border-radius:999px;padding:12px 30px 12px 36px}}
.badge b{{color:{acc}}}
.q{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:0 110px}}
.mark{{font-family:{css};font-size:220px;line-height:.5;color:{acc};height:90px;margin-right:40px}}
.quote{{font-family:{css};font-size:{size}px;line-height:{lh};color:{ink};text-wrap:balance}}
.who{{margin-top:54px;font-weight:800;font-size:34px;letter-spacing:1px;color:{ink};text-transform:uppercase}}
.where{{margin-top:10px;font-family:'IBM Plex Mono',monospace;font-size:22px;color:{small};letter-spacing:1px}}
.foot{{margin-bottom:70px;font-family:'IBM Plex Mono',monospace;font-size:22px;letter-spacing:3px;color:{small};text-transform:uppercase}}
.foot b{{color:{ink}}}
.sun{{position:absolute;right:70px;top:150px;opacity:.9}}
.palm{{position:absolute;bottom:-6px;opacity:.95;transform:scale(1.25);transform-origin:bottom left}}.palm.l{{left:40px}}.palm.r{{left:150px;bottom:0}}
.sp{{position:absolute}}.sp.a{{left:120px;top:250px}}.sp.b{{right:150px;bottom:260px}}.sp.c{{right:90px;bottom:420px}}
</style></head><body><div class="c"><div class="bar"></div>{deco}
<img class="logo" src="file://{ROOT}/assets/img/haps-logo.svg">
<div class="q"><div class="mark">&ldquo;</div><div class="quote">{keep_together(q["quote"])}</div>
<div class="who">{html.escape(q["who"])}</div><div class="where">{html.escape(q.get("where", ""))}</div></div>
<div class="foot">Send it to <b>{html.escape(q.get("send", "someone who gets it"))}</b></div>
</div></body></html>"""


def portrait_card(q, folder):
    """Text left, the speaker on the right as a duotone ("duotone") or line drawing ("line")."""
    bg, ink, acc, small = THEMES[q.get("theme", "cream")]
    fam, css, scale, lh = FONTS[q.get("font", "yellowtail")]
    n = len(q["quote"])
    size = int((104 if n < 40 else 86 if n < 80 else 72 if n < 120 else 60) * scale)
    photo = "file://" + os.path.join(folder, q["photo"])
    pos = q.get("pos", "center top")
    logo_filter = "" if q.get("theme", "cream") in ("cream", "pink") else "filter:brightness(0) invert(1);"
    if q.get("style") == "line":
        art = (f'<svg class="art" viewBox="0 0 500 1350" preserveAspectRatio="xMidYMid slice"><defs><filter id="ln" x="0" y="0" width="100%" height="100%">'
               '<feColorMatrix type="saturate" values="0"/><feGaussianBlur stdDeviation="2.2"/>'
               '<feConvolveMatrix order="3" kernelMatrix="-1 -1 -1 -1 8 -1 -1 -1 -1" preserveAlpha="true"/>'
               '<feComponentTransfer><feFuncR type="linear" slope="-14" intercept="1.25"/><feFuncG type="linear" slope="-14" intercept="1.25"/>'
               '<feFuncB type="linear" slope="-14" intercept="1.25"/></feComponentTransfer>'
               f'<feColorMatrix type="matrix" values="0 0 0 0 {int(ink[1:3],16)/255:.3f} 0 0 0 0 {int(ink[3:5],16)/255:.3f} 0 0 0 0 {int(ink[5:7],16)/255:.3f} -1 0 0 0 1"/>'
               f'</filter></defs><image href="{photo}" width="500" height="1350" preserveAspectRatio="xMidYMin slice" filter="url(#ln)"/></svg>')
    else:
        art = (f'<div class="art duo" style="background:{q.get("dark", "#1a1f4d")}"><img src="{photo}" style="object-position:{pos}">'
               f'<div class="tint" style="background:{q.get("light", acc)}"></div></div>')
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family={fam}&family=Inter+Tight:wght@500;700;800&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:{bg};overflow:hidden;font-family:'Inter Tight',sans-serif}}
.bar{{position:absolute;left:0;top:0;width:100%;height:14px;z-index:3;background:linear-gradient(90deg,#FF9500 0%,#FF4F00 40%,#AF52DE 75%,#292F71 100%)}}
.art{{position:absolute;right:0;top:0;width:500px;height:1350px}}
.duo img{{width:100%;height:100%;object-fit:cover;filter:grayscale(1) contrast(1.25) brightness(1.05);mix-blend-mode:screen;display:block}}
.duo .tint{{position:absolute;inset:0;mix-blend-mode:multiply}}
.txt{{position:absolute;left:80px;top:0;width:470px;height:1350px;display:flex;flex-direction:column;justify-content:center}}
.logo{{position:absolute;left:80px;top:70px;height:100px;{logo_filter}}}
.mark{{font-family:{css};font-size:180px;line-height:.5;color:{acc};height:70px}}
.quote{{font-family:{css};font-size:{size}px;line-height:{lh};color:{ink};text-wrap:pretty}}
.who{{margin-top:44px;font-weight:800;font-size:30px;color:{ink};text-transform:uppercase;letter-spacing:1px}}
.where{{margin-top:8px;font-family:'IBM Plex Mono',monospace;font-size:20px;color:{small}}}
.foot{{position:absolute;left:80px;bottom:64px;font-family:'IBM Plex Mono',monospace;font-size:20px;letter-spacing:3px;color:{small};text-transform:uppercase}}
.foot b{{color:{ink}}}
.credit{{position:absolute;right:18px;bottom:14px;font-family:'IBM Plex Mono',monospace;font-size:13px;color:{'#6b6862' if q.get('style')=='line' else '#fff'};opacity:.85;z-index:3}}
</style></head><body><div class="bar"></div>{art}
<img class="logo" src="file://{ROOT}/assets/img/haps-logo.svg">
<div class="txt"><div class="mark">&ldquo;</div><div class="quote">{keep_together(q["quote"])}</div>
<div class="who">{html.escape(q["who"])}</div><div class="where">{html.escape(q.get("where", ""))}</div></div>
<div class="foot">Send it to <b>{html.escape(q.get("send", "someone who gets it"))}</b></div>
<div class="credit">Photo: {html.escape(q.get("credit", ""))}</div>
</body></html>"""


def main():
    folder = os.path.abspath(sys.argv[1])
    data = json.load(open(os.path.join(folder, "quotes.json"), encoding="utf-8"))
    tmp = tempfile.mkdtemp(prefix="haps-quotes-")
    made = []
    for i, q in enumerate(data["quotes"], 1):
        h = os.path.join(tmp, f"{i}.html")
        open(h, "w", encoding="utf-8").write(portrait_card(q, folder) if q.get("photo") else card(q))
        png = os.path.join(tmp, f"{i}.png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=5000",
                        "--allow-file-access-from-files", "--window-size=1080,1350", f"--screenshot={png}", "file://" + h],
                       capture_output=True)
        out = os.path.join(folder, f"quote-{q['slug']}.jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90", png, "--out", out], capture_output=True)
        if not os.path.exists(out):
            sys.exit(f"render failed: {q['slug']}")
        made.append(out)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(made)} quote cards in {folder}")


if __name__ == "__main__":
    main()
