#!/usr/bin/env python3
"""meme_cards.py: funny, shareable Haps LA meme cards built from drawn iconography (no photos).

  python3 scripts/meme_cards.py social/series-memes        # writes meme-<slug>.jpg
  python3 scripts/meme_cards.py social/series-memes texts-rain bingo   # only these

Rules: every joke is in Haps's own voice; never attribute an invented line to a real person.
Layout: Haps logo big, top-left. Nothing below y=1150 (Instagram's caption/UI overlay).
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NAVY, ORANGE, CREAM, PINK, GOLD, PURPLE = "#1a1f4d", "#FF4F00", "#F4F1EC", "#FBE1EA", "#FF9500", "#AF52DE"
SAFE = 1150  # no content below this line


def nob(t):
    """Keep the last two words together (no single word alone on the last line)."""
    parts = t.split("<br>")
    out = []
    for seg in parts:
        i = seg.rfind(" ")
        out.append(seg[:i] + "&nbsp;" + seg[i + 1:] if i > 0 and seg.count(" ") >= 2 else seg)
    return "<br>".join(out)

BASE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Overpass:wght@600;800;900&family=Inter+Tight:wght@500;700;800;900&family=IBM+Plex+Mono:wght@500;700&family=Caveat:wght@700&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;overflow:hidden;background:{bg};font-family:'Inter Tight',sans-serif;color:{ink};position:relative}}
.bar{{position:absolute;left:0;top:0;width:100%;height:14px;background:linear-gradient(90deg,#FF9500 0%,#FF4F00 40%,#AF52DE 75%,#292F71 100%)}}
.logo{{position:absolute;left:60px;top:44px;height:170px;z-index:5;{logo}}}
.kicker{{position:absolute;top:96px;right:64px;width:620px;text-align:right;font-family:'IBM Plex Mono',monospace;font-size:24px;letter-spacing:4px;text-transform:uppercase;opacity:.8;line-height:1.35}}
.hand{{font-family:'Caveat',cursive;font-weight:700}}
.b,.c,.la,.en,.cap,.t,.title,.small,.note,.big,.via,.kicker{{text-wrap:balance}}
{css}</style></head><body><div class="bar"></div><img class="logo" src="file://{root}/assets/img/haps-logo.svg">{body}</body></html>"""


def page(bg, ink, body, css="", dark=False):
    return BASE.format(bg=bg, ink=ink, body=body, css=css, root=ROOT, logo="filter:brightness(0) invert(1);" if dark else "")


# ---------- group texts ----------
PHONE_CSS = """.phone{position:absolute;left:50%;transform:translateX(-50%);top:235px;width:640px;height:900px;background:#fff;border-radius:60px;
border:14px solid #111;padding:96px 36px 30px;box-shadow:0 30px 60px rgba(0,0,0,.22);overflow:hidden}
.notch{position:absolute;left:50%;transform:translateX(-50%);top:16px;width:170px;height:32px;background:#111;border-radius:20px}
.name{position:absolute;top:56px;left:0;width:100%;text-align:center;font-weight:700;font-size:23px;color:#555}
.b{max-width:440px;padding:18px 26px;border-radius:32px;font-size:34px;line-height:1.2;margin-bottom:16px;clear:both}
.me{float:right;background:#0a84ff;color:#fff}.them{float:left;background:#e9e9eb;color:#111}
.ts{clear:both;text-align:center;font-size:19px;color:#999;margin:6px 0 14px}"""


def texts(kicker, name, msgs, bg=GOLD, ink=NAVY, dark=False):
    rows = "".join(f'<div class="ts">{t}</div>' if w == "ts" else f'<div class="b {w}">{nob(t)}</div>' for w, t in msgs)
    body = f'<div class="kicker">{kicker}</div><div class="phone"><div class="notch"></div><div class="name">{name}</div>{rows}</div>'
    return page(bg, ink, body, PHONE_CSS, dark)


def texts_parking():
    return texts("Every plan in<br>Los&nbsp;Angeles", "Sam", [
        ("them", "how far are you"), ("me", "like 20 min"), ("ts", "7:41 PM"), ("them", "ok"), ("ts", "8:24 PM"),
        ("me", "ok parking now"), ("ts", "8:39 PM"), ("me", "still parking"), ("them", "we ordered for you")])


def texts_quake():
    return texts("3:02 AM,<br>Los&nbsp;Angeles", "Jess", [
        ("them", "did you feel that"), ("me", "feel what"), ("them", "ok nvm"), ("ts", "3:04 AM"),
        ("me", "ok I felt that one"), ("them", "everyone&rsquo;s already posting about it"), ("me", "going back to bed")], bg=PINK)


def texts_rain():
    return texts("First rain<br>of the season", "Mom", [
        ("them", "it&rsquo;s raining"), ("me", "cancel everything"), ("them", "should we stock up"), ("me", "on what"),
        ("them", "i don&rsquo;t know. soup?"), ("ts", "11:12 AM"), ("me", "it stopped"), ("them", "still not leaving")], bg="#B9BEE6")


def texts_plans():
    return texts("Making plans<br>in Los&nbsp;Angeles", "Dinner??", [
        ("them", "dinner this week?"), ("me", "can&rsquo;t do tues"), ("them", "thurs?"), ("me", "only west of the 405"),
        ("them", "fri in Silver Lake?"), ("me", "so january then"), ("them", "january works")], bg=CREAM)


def texts_outside():
    return texts("Meeting a friend<br>anywhere in L.A.", "Alex", [
        ("them", "i&rsquo;m outside"), ("me", "i don&rsquo;t see you"), ("them", "by the valet"), ("me", "which valet"),
        ("them", "there are four valets"), ("ts", "8:02 PM"), ("me", "i&rsquo;m going home"), ("them", "same")], bg=ORANGE, ink="#fff", dark=True)


# ---------- other formats ----------
def freeway(kicker="Today&rsquo;s commute", num="405", big="405 North", small="Leave now. Arrive emotionally&nbsp;different.", cap="Send it to whoever&rsquo;s driving.", bg=CREAM):
    css = """.sign{position:absolute;left:90px;top:270px;width:900px;height:560px;background:#0B6B3A;border:10px solid #fff;border-radius:28px;
box-shadow:0 0 0 6px #0B6B3A,0 30px 60px rgba(0,0,0,.25);color:#fff;font-family:'Overpass',sans-serif;padding:60px 70px}
.shield{position:absolute;right:70px;top:56px;width:170px}
.big{font-weight:900;font-size:96px;line-height:1;letter-spacing:-1px;margin-top:60px}
.small{font-weight:800;font-size:50px;line-height:1.1;margin-top:26px;max-width:640px}
.arrow{position:absolute;left:70px;bottom:44px;font-size:90px;font-weight:900}
.post{position:absolute;top:840px;width:26px;height:150px;background:#9aa0a6}.post.l{left:300px}.post.r{left:760px}
.cap{position:absolute;top:1040px;left:0;width:100%;text-align:center;font-size:58px;color:#1a1f4d}"""
    shield = """<svg class="shield" viewBox="0 0 100 110"><path d="M5 18 Q50 -2 95 18 L95 40 Q95 85 50 108 Q5 85 5 40 Z" fill="#fff"/>
<path d="M11 22 Q50 6 89 22 L89 32 L11 32 Z" fill="#c8102e"/><path d="M11 32 L89 32 L89 42 Q88 80 50 100 Q12 80 11 42 Z" fill="#003da5"/>
<text x="50" y="76" font-family="Overpass" font-weight="900" font-size="34" fill="#fff" text-anchor="middle">{num}</text></svg>""".replace("{num}", num)
    body = (f'<div class="kicker">{kicker}</div><div class="post l"></div><div class="post r"></div>'
            f'<div class="sign">{shield}<div class="big">{big}</div><div class="small">{small}</div>'
            f'<div class="arrow">&#8599;</div></div><div class="cap hand">{cap}</div>')
    return page(bg, NAVY, body, css)


def parking():
    css = """.stack{position:absolute;left:100px;top:240px;width:540px}
.pole{position:absolute;left:358px;top:220px;width:24px;height:930px;background:#8d939a}
.sg{position:relative;background:#fff;border:6px solid #111;border-radius:14px;margin-bottom:18px;padding:18px 22px;text-align:center;
font-family:'Overpass',sans-serif;font-weight:900;color:#c8102e;line-height:1.02}
.sg.g{color:#0B6B3A}.sg.b{color:#111}.sg .t{font-size:48px}.sg .s{font-size:27px;font-weight:800;color:#111;margin-top:6px}
.note{position:absolute;right:40px;top:560px;width:330px;font-size:66px;color:#FF4F00;transform:rotate(-6deg);line-height:1}"""
    body = ('<div class="pole"></div><div class="stack">'
            '<div class="sg"><div class="t">NO PARKING 7&ndash;9 AM</div><div class="s">MON &ndash; FRI</div></div>'
            '<div class="sg g"><div class="t">2 HOUR PARKING</div><div class="s">9 AM &ndash; 6 PM EXCEPT SUNDAY</div></div>'
            '<div class="sg"><div class="t">STREET CLEANING</div><div class="s">2ND TUESDAY &middot; 10 AM &ndash; NOON</div></div>'
            '<div class="sg b"><div class="t">PERMIT 14 ONLY</div><div class="s">AFTER 6 PM &middot; OTHERS CITED</div></div>'
            '<div class="sg"><div class="t">TOW AWAY</div><div class="s">NO STOPPING ANY TIME</div></div></div>'
            '<div class="note hand">so&hellip; can I park here or&nbsp;not</div>')
    return page(PINK, NAVY, body, css)


def forecast():
    sun = '<svg viewBox="0 0 100 100" width="92" height="92"><circle cx="50" cy="50" r="22" fill="#FF9500"/>' + "".join(
        f'<rect x="48" y="4" width="5" height="16" rx="2" fill="#FF9500" transform="rotate({a} 50 50)"/>' for a in range(0, 360, 45)) + "</svg>"
    cloud = '<svg viewBox="0 0 120 80" width="104" height="70"><path d="M30 70 Q5 70 8 48 Q10 30 32 32 Q38 10 62 12 Q86 14 90 36 Q115 36 114 54 Q112 70 92 70 Z" fill="#B9BEE6"/></svg>'
    rows = "".join(f'<div class="d"><div class="n">{n}</div>{sun}<div class="t">72&deg;</div></div>' for n in ["MON", "TUE", "WED", "THU", "FRI", "SAT"])
    rows += f'<div class="d hot"><div class="n">SUN</div>{cloud}<div class="t">63&deg;</div><div class="w">puffer jacket<br>emergency</div></div>'
    css = """.title{position:absolute;top:260px;width:100%;text-align:center;font-weight:900;font-size:76px;letter-spacing:-2px;color:#fff}
.grid{position:absolute;top:400px;left:70px;width:940px;display:grid;grid-template-columns:repeat(7,1fr);gap:14px}
.d{background:rgba(255,255,255,.08);border-radius:22px;padding:24px 0;text-align:center;color:#fff;height:320px}
.d .n{font-family:'IBM Plex Mono',monospace;font-size:24px;letter-spacing:3px;margin-bottom:18px}
.d .t{font-weight:900;font-size:50px;margin-top:14px}.d.hot{background:#FF4F00}
.d .w{font-family:'Caveat',cursive;font-weight:700;font-size:23px;line-height:1;margin-top:14px}
.cap{position:absolute;top:820px;width:100%;text-align:center;color:#fff;font-size:66px;line-height:1.1;padding:0 120px}"""
    body = (f'<div class="title">Los&nbsp;Angeles, 7-day</div><div class="grid">{rows}</div>'
            '<div class="cap hand">Tag the friend who owns three coats for one cold&nbsp;day.</div>')
    return page(NAVY, "#fff", body, css, dark=True)


def chart():
    css = """.t{position:absolute;top:250px;width:100%;text-align:center;font-weight:900;font-size:64px;letter-spacing:-1.5px}
.sub{position:absolute;top:335px;width:100%;text-align:center;font-family:'IBM Plex Mono',monospace;font-size:24px;opacity:.7}
svg.c{position:absolute;left:90px;top:400px}"""
    svg = """<svg class="c" width="900" height="720" viewBox="0 0 900 760">
<line x1="80" y1="40" x2="80" y2="660" stroke="#1a1f4d" stroke-width="5"/><line x1="80" y1="660" x2="860" y2="660" stroke="#1a1f4d" stroke-width="5"/>
<text x="470" y="725" font-family="IBM Plex Mono" font-size="26" fill="#1a1f4d" text-anchor="middle">MILES AWAY</text>
<text x="30" y="350" font-family="IBM Plex Mono" font-size="26" fill="#1a1f4d" text-anchor="middle" transform="rotate(-90 30 350)">MINUTES IN THE CAR</text>
<path d="M80 640 L260 600 L420 560 L520 120 L600 520 L860 470" fill="none" stroke="#FF4F00" stroke-width="12" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="520" cy="120" r="16" fill="#FF4F00"/>
<text x="545" y="105" font-family="Caveat" font-weight="700" font-size="46" fill="#1a1f4d">the 10 at 5:15 PM</text>
<text x="590" y="560" font-family="Caveat" font-weight="700" font-size="40" fill="#1a1f4d">Malibu on a Tuesday</text>
<text x="110" y="560" font-family="Caveat" font-weight="700" font-size="40" fill="#1a1f4d">walking to the corner</text></svg>"""
    return page(CREAM, NAVY, '<div class="t">Distance in Los&nbsp;Angeles</div><div class="sub">(a scientific study)</div>' + svg, css)


def bingo(kicker="Dinner party", title="Los&nbsp;Angeles <span>bingo</span>", cells=None, cap="Screenshot it. Mark your squares. Tag your&nbsp;table.", bg=NAVY):
    cells = cells or ["&ldquo;It&rsquo;s only 20 minutes&rdquo;", "Someone is &ldquo;writing something&rdquo;", "&ldquo;We should hike&rdquo;",
             "A parking story", "FREE SPACE<br>the weather", "&ldquo;Was that an earthquake?&rdquo;",
             "&ldquo;Which freeway did you take?&rdquo;", "A taco truck ranking", "&ldquo;I could never live in New York&rdquo;"]
    grid = "".join(f'<div class="c{" free" if "FREE" in c else ""}">{nob(c)}</div>' for c in cells)
    css = """.t{position:absolute;top:240px;left:0;width:100%;text-align:center;font-weight:900;font-size:66px;letter-spacing:-1.5px;color:#fff;line-height:1}
.t span{color:#FF9500}
.g{position:absolute;top:350px;left:90px;width:900px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.c{height:228px;background:#fff;border-radius:22px;display:flex;align-items:center;justify-content:center;text-align:center;
padding:20px;font-weight:800;font-size:36px;line-height:1.12;color:#1a1f4d}
.c.free{background:#FF4F00;color:#fff}
.cap{position:absolute;top:1090px;width:100%;text-align:center;color:#fff;font-size:44px}"""
    body = (f'<div class="kicker">{kicker}</div><div class="t">{title}</div><div class="g">{grid}</div>'
            f'<div class="cap hand">{cap}</div>')
    return page(bg, "#fff", body, css, dark=True)


def maps(kicker="Going 3 miles<br>on a Thursday", mins="51 min", dist="3.2 mi", via="Fastest route, somehow", cap="should&rsquo;ve walked", bg=PINK):
    streets = "".join(f'<line x1="0" y1="{y}" x2="760" y2="{y - 60}" stroke="#e3ded6" stroke-width="10"/>' for y in range(40, 560, 70))
    streets += "".join(f'<line x1="{x}" y1="0" x2="{x + 40}" y2="520" stroke="#e3ded6" stroke-width="10"/>' for x in range(30, 760, 90))
    svg = f"""<svg viewBox="0 0 760 520" width="760" height="520">{streets}
<path d="M-20 360 C200 300 420 330 780 230" stroke="#FFC6A8" stroke-width="44" fill="none"/>
<path d="M-20 360 C200 300 420 330 780 230" stroke="#FF4F00" stroke-width="10" fill="none" stroke-dasharray="2 18" stroke-linecap="round"/>
<path d="M140 120 C260 260 250 330 330 330 C420 330 430 250 520 260 C600 270 610 380 640 420" stroke="#0a84ff" stroke-width="16" fill="none" stroke-linecap="round"/>
<circle cx="140" cy="120" r="20" fill="#fff" stroke="#0a84ff" stroke-width="8"/>
<path d="M640 444 C620 420 610 404 610 392 a30 30 0 1 1 60 0 C670 404 660 420 640 444 Z" fill="#c8102e"/><circle cx="640" cy="392" r="10" fill="#fff"/></svg>"""
    css = """.card{position:absolute;left:100px;top:240px;width:880px;height:880px;background:#fff;border-radius:44px;overflow:hidden;box-shadow:0 30px 60px rgba(0,0,0,.18)}
.map{background:#f4f1ec;height:560px;display:flex;align-items:center;justify-content:center}
.sheet{padding:34px 48px}.big{font-weight:900;font-size:76px;letter-spacing:-2px;color:#c8102e}.big span{color:#111;font-weight:700;font-size:44px;margin-left:16px}
.via{font-size:30px;color:#666;margin-top:6px}.btn{display:inline-block;margin-top:22px;background:#e9e9eb;color:#111;font-weight:800;font-size:30px;padding:16px 36px;border-radius:40px}
.cap{position:absolute;right:120px;top:1000px;font-size:56px;color:#FF4F00;transform:rotate(-5deg)}"""
    body = (f'<div class="kicker">{kicker}</div><div class="card"><div class="map">{svg}</div>'
            f'<div class="sheet"><div class="big">{mins}<span>{dist}</span></div><div class="via">{via}</div>'
            f'<div class="btn">Start</div></div></div><div class="cap hand">{cap}</div>')
    return page(bg, NAVY, body, css)


def dictionary(title="Los&nbsp;Angeles <span>&rarr;</span> English", hdr=("WHAT THEY SAY", "WHAT THEY MEAN"), rows=None, bg=CREAM):
    rows = rows or [("&ldquo;Let&rsquo;s grab coffee sometime&rdquo;", "See you at a wedding in 2029."),
            ("&ldquo;It&rsquo;s only 20 minutes&rdquo;", "It is 50 minutes."),
            ("&ldquo;I&rsquo;m 5 minutes away&rdquo;", "I am in the shower."),
            ("&ldquo;We should hike&rdquo;", "We should talk about hiking."),
            ("&ldquo;Traffic was insane&rdquo;", "I left late.")]
    items = "".join(f'<div class="r"><div class="la">{nob(a)}</div><div class="en">{nob(b)}</div></div>' for a, b in rows)
    css = """.t{position:absolute;top:250px;left:90px;font-weight:900;font-size:70px;letter-spacing:-2px;line-height:1}
.t span{color:#FF4F00}.hdr{position:absolute;top:350px;left:90px;width:900px;display:flex;font-family:'IBM Plex Mono',monospace;font-size:22px;letter-spacing:3px;opacity:.6}
.hdr div{width:50%}.list{position:absolute;top:400px;left:90px;width:900px}
.r{display:flex;border-top:3px solid #1a1f4d;padding:26px 0}.r:last-child{border-bottom:3px solid #1a1f4d}
.la{width:50%;font-weight:800;font-size:36px;line-height:1.15;padding-right:24px}.en{width:50%;font-family:'Caveat',cursive;font-weight:700;font-size:48px;line-height:1;color:#FF4F00}"""
    body = (f'<div class="t">{title}</div><div class="hdr"><div>{hdr[0]}</div><div>{hdr[1]}</div></div>'
            f'<div class="list">{items}</div>')
    return page(bg, NAVY, body, css)


# ---------- realistic iPhone Messages ----------
IOS_CSS = """.dev{position:absolute;left:50%;transform:translateX(-50%);top:228px;width:610px;height:912px;border-radius:84px;
background:linear-gradient(145deg,#5b5b60,#2c2c2f 40%,#4a4a4e);padding:11px;box-shadow:0 40px 80px rgba(0,0,0,.28)}
.btn{position:absolute;background:#3a3a3d;border-radius:3px}.b1{left:-5px;top:180px;width:5px;height:56px}.b2{left:-5px;top:260px;width:5px;height:90px}
.b3{left:-5px;top:365px;width:5px;height:90px}.b4{right:-5px;top:280px;width:5px;height:130px}
.bez{width:100%;height:100%;background:#000;border-radius:74px;padding:9px}
.scr{position:relative;width:100%;height:100%;background:#fff;border-radius:66px;overflow:hidden;font-family:-apple-system,'SF Pro Text','Inter Tight',sans-serif;color:#000}
.island{position:absolute;left:50%;transform:translateX(-50%);top:14px;width:150px;height:42px;background:#000;border-radius:24px}
.sb{position:absolute;top:22px;left:46px;right:38px;display:flex;justify-content:space-between;align-items:center;font-weight:600;font-size:23px}
.hd{position:absolute;top:66px;left:0;width:100%;height:150px;border-bottom:1px solid #e5e5ea;background:rgba(249,249,249,.96)}
.back{position:absolute;left:24px;top:38px;color:#0a84ff;font-size:44px;font-weight:300;line-height:1}
.cnt{position:absolute;left:52px;top:44px;background:#0a84ff;color:#fff;font-size:17px;font-weight:600;border-radius:14px;padding:3px 10px}
.av{position:absolute;left:50%;transform:translateX(-50%);top:14px;width:76px;height:76px;border-radius:50%;
background:linear-gradient(180deg,#a8adb6,#868b94);color:#fff;font-weight:600;font-size:32px;display:flex;align-items:center;justify-content:center}
.nm{position:absolute;top:98px;width:100%;text-align:center;font-size:19px;color:#000}.nm span{color:#8e8e93}
.msgs{position:absolute;top:226px;left:22px;right:22px}
.m{position:relative;max-width:390px;padding:13px 20px;border-radius:26px;font-size:28px;line-height:1.22;margin-bottom:7px;clear:both;text-wrap:balance}
.me{float:right;background:#0a84ff;color:#fff}.them{float:left;background:#e9e9eb;color:#000}
.me.tail:before{content:'';position:absolute;right:-8px;bottom:0;width:22px;height:24px;background:#0a84ff;border-bottom-left-radius:16px 14px}
.me.tail:after{content:'';position:absolute;right:-26px;bottom:0;width:26px;height:24px;background:#fff;border-bottom-left-radius:12px}
.them.tail:before{content:'';position:absolute;left:-8px;bottom:0;width:22px;height:24px;background:#e9e9eb;border-bottom-right-radius:16px 14px}
.them.tail:after{content:'';position:absolute;left:-26px;bottom:0;width:26px;height:24px;background:#fff;border-bottom-right-radius:12px}
.gap{clear:both;height:12px}
.ts{clear:both;text-align:center;font-size:16px;color:#8e8e93;margin:10px 0 10px}.ts b{font-weight:600}
.rc{clear:both;text-align:right;font-size:16px;color:#8e8e93;margin:-2px 6px 6px 0;font-weight:500}
.inp{position:absolute;left:18px;right:18px;bottom:44px;display:flex;align-items:center;gap:14px}
.plus{width:46px;height:46px;border-radius:50%;background:#e9e9eb;color:#8e8e93;font-size:36px;line-height:44px;text-align:center;font-weight:300}
.fld{flex:1;height:46px;border:1.5px solid #d1d1d6;border-radius:24px;padding:0 18px;display:flex;align-items:center;justify-content:space-between;color:#c4c4c7;font-size:21px}
.home{position:absolute;left:50%;transform:translateX(-50%);bottom:12px;width:190px;height:7px;border-radius:4px;background:#000}"""

STATUS = """<div class="sb"><span>9:41</span><span style="display:flex;gap:8px;align-items:center">
<svg width="30" height="20" viewBox="0 0 30 20"><rect x="0" y="13" width="5" height="7" rx="1.5"/><rect x="8" y="9" width="5" height="11" rx="1.5"/><rect x="16" y="5" width="5" height="15" rx="1.5"/><rect x="24" y="0" width="5" height="20" rx="1.5"/></svg>
<svg width="28" height="20" viewBox="0 0 28 20"><path d="M14 18 l4-4.5 a6 6 0 0 0-8 0z"/><path d="M14 9 a11 11 0 0 1 8 3.4 l2.4-2.7 a15 15 0 0 0-20.8 0 l2.4 2.7 A11 11 0 0 1 14 9z"/><path d="M14 2.5 a17.5 17.5 0 0 1 12.6 5.2 l2.3-2.6 a21 21 0 0 0-29.8 0 l2.3 2.6 A17.5 17.5 0 0 1 14 2.5z"/></svg>
<svg width="44" height="22" viewBox="0 0 44 22"><rect x="1" y="1" width="37" height="20" rx="6" fill="none" stroke="#000" stroke-opacity=".4" stroke-width="2"/><rect x="4" y="4" width="31" height="14" rx="3.5"/><rect x="40" y="7" width="3" height="8" rx="1.5" fill-opacity=".4"/></svg></span></div>"""


def iphone(kicker, contact, msgs, bg=GOLD, ink=NAVY, dark=False, receipt="Delivered"):
    initials = "".join(w[0] for w in contact.split()[:2]).upper()
    rows, n = [], len(msgs)
    for i, (w, t) in enumerate(msgs):
        if w == "ts":
            rows.append(f'<div class="ts">{t}</div>')
            continue
        nxt = msgs[i + 1][0] if i + 1 < n else None
        tail = " tail" if nxt != w else ""
        rows.append(f'<div class="m {w}{tail}">{nob(t)}</div>' + ('<div class="gap"></div>' if tail else ""))
    last_me = max((i for i, (w, _) in enumerate(msgs) if w == "me"), default=None)
    if receipt and last_me is not None and last_me == n - 1:
        rows.append(f'<div class="rc">{receipt}</div>')
    body = (f'<div class="kicker">{kicker}</div><div class="dev"><div class="btn b1"></div><div class="btn b2"></div><div class="btn b3"></div><div class="btn b4"></div>'
            f'<div class="bez"><div class="scr"><div class="island"></div>{STATUS}'
            f'<div class="hd"><div class="back">&#8249;</div><div class="cnt">12</div><div class="av">{initials}</div><div class="nm">{contact} <span>&rsaquo;</span></div></div>'
            f'<div class="msgs">{"".join(rows)}</div>'
            '<div class="inp"><div class="plus">+</div><div class="fld">iMessage<svg width="22" height="28" viewBox="0 0 22 28"><rect x="6" y="1" width="10" height="17" rx="5" fill="#c4c4c7"/><path d="M2 13a9 9 0 0 0 18 0" stroke="#c4c4c7" stroke-width="2.5" fill="none"/><rect x="10" y="22" width="2.5" height="5" fill="#c4c4c7"/></svg></div></div>'
            '<div class="home"></div></div></div></div>')
    return page(bg, ink, body, IOS_CSS, dark)


def ios_brunch():
    return iphone("Brunch in<br>Los&nbsp;Angeles", "Maya", [
        ("ts", "<b>Saturday</b> 9:12 AM"), ("them", "brunch?"), ("me", "where"), ("them", "the place with the line"),
        ("me", "which one"), ("them", "all of them"), ("me", "see you at 2")], bg=PINK)


def ios_bowl():
    return iphone("Going to<br>the Bowl", "Chris", [
        ("ts", "<b>Today</b> 3:05 PM"), ("them", "show starts at 8"), ("me", "so we leave at 5"), ("them", "for an 8 pm show?"),
        ("me", "have you met Highland"), ("them", "ok leaving at 4:30")], bg=CREAM, receipt=None)


def ios_towed():
    return iphone("Second Tuesday<br>of the month", "Roommate", [
        ("ts", "<b>Tuesday</b> 10:47 AM"), ("me", "where is my car"), ("them", "street cleaning"), ("me", "it&rsquo;s tuesday"),
        ("them", "second tuesday"), ("me", "how much"), ("them", "don&rsquo;t look it up")], bg="#B9BEE6")


def ios_santaana():
    return iphone("December<br>in Los&nbsp;Angeles", "Dad", [
        ("ts", "<b>Today</b> 1:18 PM"), ("them", "why is it 88 degrees"), ("me", "santa anas"), ("them", "it&rsquo;s december"),
        ("me", "shorts for christmas"), ("them", "sweater for new year&rsquo;s"), ("me", "this is the way")], bg=GOLD, receipt="Read 1:20 PM")


def ios_valley():
    return iphone("Crossing<br>the hill", "Nico", [
        ("ts", "<b>Friday</b> 6:40 PM"), ("them", "party in echo park tonight"), ("me", "i&rsquo;m in the valley"), ("them", "so is that a no"),
        ("me", "that&rsquo;s a see you in spring"), ("them", "valid")], bg=ORANGE, ink="#fff", dark=True, receipt=None)


# ---------- batch 3 ----------
def ios_dinner():
    return iphone("Getting a table<br>in Los&nbsp;Angeles", "Priya", [
        ("ts", "<b>Monday</b> 11:02 AM"), ("them", "can you book us for saturday at 7"), ("me", "the only times are 5:15 or 10:45"),
        ("them", "5:15"), ("me", "we&rsquo;re early bird people now"), ("them", "always have been")], bg=PINK, receipt=None)


def ios_hike():
    return iphone("Weekend plans<br>in Los&nbsp;Angeles", "Jordan", [
        ("ts", "<b>Friday</b> 8:30 PM"), ("them", "hike tomorrow?"), ("me", "which one"), ("them", "runyon"),
        ("me", "so a photoshoot"), ("them", "fine. griffith at 7"), ("me", "parking at 7 or never")], bg=CREAM)


def ios_moving():
    return iphone("Moving across<br>Los&nbsp;Angeles", "Sam", [
        ("ts", "<b>Today</b> 6:14 PM"), ("me", "thinking about moving to silver lake"), ("them", "you&rsquo;ll never see your westside friends"),
        ("me", "i don&rsquo;t see them now"), ("them", "then sign the lease")], bg=GOLD, receipt=None)


def ios_celeb():
    return iphone("Grocery run<br>in Los&nbsp;Angeles", "Taylor", [
        ("ts", "<b>Sunday</b> 4:47 PM"), ("me", "just saw someone famous in the cereal aisle"), ("them", "who"),
        ("me", "no idea but everyone stared"), ("them", "classic"), ("me", "bought the same cereal just in case")], bg="#B9BEE6")


def bingo_date():
    return bingo(kicker="First date", title="Los&nbsp;Angeles date <span>bingo</span>", cells=[
        "They have a project &ldquo;in development&rdquo;", "Took three tries to schedule", "Valet or street parking debate",
        "They asked your sign", "FREE SPACE<br>They&rsquo;re late", "Ten minutes on traffic",
        "Mentions their podcast", "A very specific oat milk order", "&ldquo;I&rsquo;m mostly on the Eastside now&rdquo;"],
        cap="How many did you get? Be&nbsp;honest.", bg="#3a1f4d")


def maps_friday():
    return maps(kicker="Friday at 5,<br>any direction", mins="74 min", dist="2.1 mi", via="Every route is the slow route",
                cap="faster on&nbsp;foot", bg=GOLD)


def freeway_eta():
    return freeway(kicker="Heading to the beach", num="10", big="10 West", small="Santa Monica 14 mi.<br>See you in&nbsp;spring.",
                   cap="Tag your beach friend.", bg=PINK)


IPAD_CSS = """.ipad{position:absolute;left:50%;transform:translateX(-50%);top:232px;width:900px;height:900px;border-radius:52px;background:#1c1c1e;padding:22px;
box-shadow:0 40px 80px rgba(0,0,0,.25)}
.scr{width:100%;height:100%;background:#fff;border-radius:32px;overflow:hidden;position:relative;font-family:-apple-system,'SF Pro Text','Inter Tight',sans-serif;color:#000}
.sb{display:flex;justify-content:space-between;padding:16px 30px 0;font-size:19px;font-weight:600}
.tb{display:flex;justify-content:space-between;align-items:center;padding:14px 30px;color:#e0a100;font-size:24px}
.nt{padding:6px 54px}.nt h3{font-size:58px;font-weight:800;letter-spacing:-.5px;margin-bottom:6px;text-wrap:balance}
.nt .d{color:#8e8e93;font-size:19px;margin-bottom:22px}
.li{display:flex;align-items:flex-start;gap:22px;font-size:37px;line-height:1.22;margin-bottom:26px;text-wrap:balance}
.ck{flex:none;width:38px;height:38px;border-radius:50%;border:2.5px solid #c7c7cc;margin-top:3px}
.ck.on{background:#e0a100;border-color:#e0a100;position:relative}.ck.on:after{content:'';position:absolute;left:10px;top:4px;width:9px;height:17px;border:solid #fff;border-width:0 3.5px 3.5px 0;transform:rotate(45deg)}
.li.done span{color:#8e8e93;text-decoration:line-through}"""


def ipad_resolutions():
    items = [(False, "Go east of La Brea at least once"), (False, "Finally learn our street cleaning day"),
             (False, "Actually go to the Getty"), (False, "Hike something that isn&rsquo;t Runyon"),
             (False, "Leave 40 minutes early for everything"), (False, "Find parking on the first try"), (True, "Complain about traffic")]
    lis = "".join(f'<div class="li{" done" if d else ""}"><div class="ck{" on" if d else ""}"></div><span>{nob(t)}</span></div>' for d, t in items)
    body = ('<div class="kicker">New year,<br>same Los&nbsp;Angeles</div><div class="ipad"><div class="scr">'
            '<div class="sb"><span>9:41 AM&nbsp; Thu Jan 1</span><span>100%</span></div>'
            '<div class="tb"><span>&#8249; Notes</span><span>Done</span></div>'
            f'<div class="nt"><h3>2027 resolutions</h3><div class="d">January 1, 2027 at 9:41 AM</div>{lis}</div></div></div>')
    return page(CREAM, NAVY, body, IPAD_CSS)


# ---------- batch 4 ----------
def ios_lax():
    return iphone("The biggest favor<br>in Los&nbsp;Angeles", "Chris", [
        ("ts", "<b>Thursday</b> 2:12 PM"), ("them", "can you pick me up from LAX tomorrow"), ("me", "what time"),
        ("them", "5:30 pm"), ("me", "on a friday?"), ("me", "i love you but no")], bg=GOLD)


def ios_coffee():
    return iphone("Coffee plans<br>in Los&nbsp;Angeles", "Ava", [
        ("ts", "<b>Saturday</b> 9:58 AM"), ("them", "coffee at 10?"), ("me", "where"), ("them", "anywhere with parking"),
        ("me", "so nowhere"), ("them", "i&rsquo;ll bring coffee to your car")], bg=PINK, receipt=None)


def ios_housewarming():
    return iphone("Housewarming<br>season", "Nina", [
        ("ts", "<b>Tuesday</b> 7:20 PM"), ("them", "housewarming saturday"), ("me", "yay where"), ("them", "glendale"),
        ("me", "i&rsquo;m in santa monica"), ("them", "so you&rsquo;re sending a gift"), ("me", "sending a gift")], bg=CREAM)


def ios_snow():
    return iphone("The morning<br>after the rain", "Mom", [
        ("ts", "<b>Today</b> 8:04 AM"), ("me", "you can see snow on the mountains"), ("them", "send a picture"),
        ("me", "palm trees in front of snow"), ("them", "this is why you pay that rent"), ("me", "exactly this")], bg="#B9BEE6", receipt="Read 8:06 AM")


def ios_gym():
    return iphone("December in<br>Los&nbsp;Angeles", "Gym buddy", [
        ("ts", "<b>Monday</b> 6:01 AM"), ("them", "every spin class is booked until january"), ("me", "it&rsquo;s december"),
        ("them", "holiday party photos"), ("me", "see you in january"), ("them", "see you in january")], bg=ORANGE, ink="#fff", dark=True, receipt=None)


def bingo_lax():
    return bingo(kicker="Pickup and drop-off", title="LAX <span>bingo</span>", cells=[
        "Third lap around the loop", "Your ride is &ldquo;2 min away&rdquo; for 20", "Sunglasses indoors",
        "The rideshare lot shuttle", "FREE SPACE<br>Construction", "Sandwich, $19",
        "Wrong terminal, right airport", "Waved off by the officer", "Celebrity sighting"],
        cap="Tag who you&rsquo;re picking&nbsp;up.", bg="#0f4c5c")


def maps_lax():
    return maps(kicker="Getting to LAX<br>on a Thursday", mins="1 hr 12 min", dist="8 mi", via="Should&rsquo;ve left yesterday",
                cap="see you at the&nbsp;gate", bg="#B9BEE6")


def freeway_101():
    return freeway(kicker="Morning commute", num="101", big="101 South", small="Downtown 6 mi.<br>Patience&nbsp;required.",
                   cap="Send it to your carpool.", bg=GOLD)


def dictionary_weather():
    return dictionary(title="Weather <span>&rarr;</span> English", hdr=("WHAT WE SAY", "WHAT IT MEANS"), rows=[
        ("&ldquo;It&rsquo;s freezing&rdquo;", "It is 61 degrees."),
        ("&ldquo;It&rsquo;s pouring&rdquo;", "A light drizzle, briefly."),
        ("&ldquo;Heat wave&rdquo;", "It is 84. Stay inside."),
        ("&ldquo;Marine layer&rdquo;", "Bring a sweater until noon."),
        ("&ldquo;Perfect weather&rdquo;", "Tuesday. Also Wednesday.")], bg=PINK)


CAL_CSS = IPAD_CSS + """.cal{position:absolute;left:28px;right:28px;top:66px;bottom:26px}
.ch{display:grid;grid-template-columns:58px repeat(5,1fr);font-size:17px;color:#8e8e93;font-weight:600;text-align:center;padding-bottom:8px;border-bottom:1px solid #e5e5ea}
.ch b{display:block;color:#000;font-size:26px}
.grid{position:relative;height:600px;display:grid;grid-template-columns:58px repeat(5,1fr)}
.hr{position:absolute;left:58px;right:0;border-top:1px solid #f0f0f2}.hl{position:absolute;left:0;width:52px;text-align:right;font-size:13px;color:#8e8e93;transform:translateY(-8px)}
.col{position:relative;border-left:1px solid #f0f0f2}
.ev{position:absolute;left:4px;right:4px;border-radius:8px;padding:6px 9px;font-size:16px;font-weight:600;line-height:1.15;overflow:hidden;border-left:4px solid}
.ev small{display:block;font-weight:500;font-size:13px;opacity:.8}
.drive{background:#ffe3d6;color:#a53000;border-color:#FF4F00}.plan{background:#dcecff;color:#0040a0;border-color:#0a84ff}
.mon{font-size:30px;font-weight:800;padding:0 4px 10px}"""


def ipad_calendar():
    start, end, H = 7, 22, 600
    def y(h): return (h - start) / (end - start) * H
    days = [("MON", "7", [("drive", 17.5, 19, "Drive to dinner", "5:30 PM"), ("plan", 19, 20, "Dinner", "7 PM"), ("drive", 20, 21.7, "Drive home", "8 PM")]),
            ("TUE", "8", [("drive", 8.0, 9.2, "Find parking", "8 AM"), ("plan", 9.25, 10.25, "Coffee", "9:15 AM")]),
            ("WED", "9", [("plan", 7.1, 8.2, "Gym", "7 AM"), ("drive", 12, 14, "Cross the 405", "Noon"), ("plan", 14, 15, "Lunch", "2 PM")]),
            ("THU", "10", [("drive", 13, 16.5, "Leave for LAX", "1 PM"), ("plan", 16.5, 17.5, "Flight", "4:30 PM")]),
            ("FRI", "11", [("drive", 15.5, 18, "Santa Monica to Silver Lake", "3:30 PM"), ("plan", 18, 19.5, "Happy hour", "6 PM")])]
    hours = "".join(f'<div class="hr" style="top:{y(h):.0f}px"></div><div class="hl" style="top:{y(h):.0f}px">{(h - 1) % 12 + 1} {"AM" if h < 12 else "PM"}</div>' for h in range(8, 22, 2))
    cols = ""
    for _, _, evs in days:
        cols += '<div class="col">' + "".join(f'<div class="ev {k}" style="top:{y(a):.0f}px;height:{y(b) - y(a) - 3:.0f}px">{t}<small>{tm}</small></div>' for k, a, b, t, tm in evs) + "</div>"
    head = '<div class="ch"><div></div>' + "".join(f'<div>{d}<b>{n}</b></div>' for d, n, _ in days) + "</div>"
    body = ('<div class="kicker">A normal week<br>in Los&nbsp;Angeles</div><div class="ipad"><div class="scr">'
            '<div class="sb"><span>9:41 AM&nbsp; Mon Dec 7</span><span>100%</span></div>'
            '<div class="cal"><div class="mon">December 2026</div>' + head + f'<div class="grid">{hours}<div></div>{cols}</div></div></div></div>')
    return page(CREAM, NAVY, body, CAL_CSS)


# ---------- new formats: receipt, wrapped, lock screen ----------
def receipt(kicker="One night out<br>in Los&nbsp;Angeles", sub="Saturday &middot; 7:00 PM &ndash; 1:14 AM", items=None, total="$295.00",
            ty="THANK YOU. SEE YOU SATURDAY.", stamp="worth&nbsp;it", bg=PINK):
    items = items or [("Valet", "25.00"), ("Two cocktails", "44.00"), ("&ldquo;Small plates&rdquo; x 6", "96.00"), ("Rideshare surge", "48.00"),
             ("Parking ticket (the valet was full)", "73.00"), ("Late-night tacos", "9.00")]
    rows = "".join(f'<div class="ln"><span>{nob(a)}</span><span>{"$" if b[0].isdigit() else ""}{b}</span></div>' for a, b in items)
    css = """.rc{position:absolute;left:50%;top:228px;transform:translateX(-50%) rotate(-1.5deg);width:640px;background:#fffdf7;padding:46px 50px 40px;
font-family:'IBM Plex Mono',monospace;color:#222;box-shadow:0 30px 60px rgba(0,0,0,.18);
-webkit-mask:linear-gradient(#000 0 0) top/100% calc(100% - 18px) no-repeat,radial-gradient(circle 12px at 12px 100%,#0000 98%,#000) bottom/24px 18px repeat-x}
.rc h4{text-align:center;font-size:30px;letter-spacing:4px}.rc .sub{text-align:center;font-size:19px;color:#777;margin:6px 0 22px}
.dash{border-top:3px dashed #bbb;margin:18px 0}.ln{display:flex;justify-content:space-between;gap:20px;font-size:25px;line-height:1.3;margin:12px 0}
.tot{display:flex;justify-content:space-between;font-size:34px;font-weight:700}.ty{text-align:center;font-size:22px;margin-top:20px;color:#555}
.bar{} .bc{height:56px;margin:22px auto 0;width:420px;background:repeating-linear-gradient(90deg,#222 0 3px,#fff 3px 6px,#222 6px 7px,#fff 7px 11px)}
.stamp{position:absolute;right:120px;top:880px;font-size:64px;color:#FF4F00;transform:rotate(-8deg)}"""
    body = (f'<div class="kicker">{kicker}</div><div class="rc"><h4>LOS ANGELES</h4><div class="sub">{sub}</div>'
            f'<div class="dash"></div>{rows}<div class="dash"></div><div class="tot"><span>TOTAL</span><span>{total}</span></div>'
            f'<div class="ty">{ty}</div><div class="bc"></div></div><div class="stamp hand">{stamp}</div>')
    return page(bg, NAVY, body, css)


def wrapped():
    css = """.w{position:absolute;left:90px;right:90px;top:250px;height:880px;border-radius:44px;padding:56px 60px;color:#fff;
background:radial-gradient(circle at 85% 10%,#FF9500 0,#FF4F00 30%,#AF52DE 65%,#292F71 100%);box-shadow:0 30px 60px rgba(0,0,0,.25)}
.w .yr{font-family:'IBM Plex Mono',monospace;font-size:24px;letter-spacing:4px;opacity:.85}
.w h2{font-weight:900;font-size:84px;letter-spacing:-2px;line-height:.95;margin:14px 0 40px;text-wrap:balance}
.st{display:grid;grid-template-columns:1fr 1fr;gap:34px 30px}.st div{font-size:22px;opacity:.85;font-family:'IBM Plex Mono',monospace;letter-spacing:1px;text-transform:uppercase}
.st b{display:block;font-family:'Inter Tight',sans-serif;font-size:44px;letter-spacing:-1px;opacity:1;text-transform:none;line-height:1.05;margin-top:6px;text-wrap:balance}"""
    stats = [("Top neighborhood", "The 405"), ("Minutes in the car", "41,280"), ("Top genre", "Parking podcasts"),
             ("Most said", "&ldquo;Like 20 min&rdquo;"), ("Top weather", "72 and sunny, 311 times"), ("Personality", "Eastside, on weekends")]
    grid = "".join(f'<div>{a}<b>{nob(b)}</b></div>' for a, b in stats)
    body = (f'<div class="kicker">Your year<br>in review</div><div class="w"><div class="yr">2026</div><h2>Los&nbsp;Angeles, Wrapped</h2>'
            f'<div class="st">{grid}</div></div>')
    return page(CREAM, NAVY, body, css)


def lockscreen():
    notes = [("Maps", "MAPS", "#34C759", "now", "Leave now to arrive on time.", "You will not arrive on time."),
             ("Weather", "WEATHER", "#0a84ff", "2m ago", "It&rsquo;s 64&deg; and cloudy.", "Your friends are in puffer jackets."),
             ("Calendar", "CALENDAR", "#FF3B30", "18m ago", "Dinner in Silver Lake, 7:00 PM", "You live in Santa Monica."),
             ("Messages", "MESSAGES", "#34C759", "1h ago", "Sam", "&ldquo;i&rsquo;m outside&rdquo; (Sam is not outside)")]
    cards = "".join(f'<div class="n"><div class="ap" style="background:{c}">{a[0]}</div><div class="tx"><div class="hd"><span>{ap}</span><span>{t}</span></div>'
                    f'<b>{nob(h)}</b><p>{nob(b)}</p></div></div>' for a, ap, c, t, h, b in notes)
    css = """.ph{position:absolute;left:50%;transform:translateX(-50%);top:228px;width:610px;height:912px;border-radius:84px;padding:11px;
background:linear-gradient(145deg,#5b5b60,#2c2c2f 40%,#4a4a4e);box-shadow:0 40px 80px rgba(0,0,0,.28)}
.scr{width:100%;height:100%;border-radius:74px;overflow:hidden;position:relative;font-family:-apple-system,'SF Pro Text','Inter Tight',sans-serif;
background:linear-gradient(180deg,#ff9a5a 0%,#ff6a88 35%,#7a5cc7 70%,#2b2f6e 100%);color:#fff;border:9px solid #000}
.isl{position:absolute;left:50%;transform:translateX(-50%);top:12px;width:150px;height:42px;background:#000;border-radius:24px}
.dt{text-align:center;margin-top:84px;font-size:22px;font-weight:600;opacity:.9}.tm{text-align:center;font-size:118px;font-weight:700;letter-spacing:-3px;line-height:1}
.ns{position:absolute;left:16px;right:16px;bottom:96px}
.n{display:flex;gap:14px;background:rgba(255,255,255,.72);backdrop-filter:blur(20px);color:#000;border-radius:26px;padding:16px 18px;margin-top:10px}
.ap{flex:none;width:46px;height:46px;border-radius:12px;color:#fff;font-weight:800;font-size:24px;display:flex;align-items:center;justify-content:center}
.tx{flex:1}.hd{display:flex;justify-content:space-between;font-size:14px;color:#555;font-weight:600;letter-spacing:.5px}
.tx b{display:block;font-size:20px;margin-top:2px;text-wrap:balance}.tx p{font-size:19px;line-height:1.2;margin-top:2px;text-wrap:balance}
.hm{position:absolute;left:50%;transform:translateX(-50%);bottom:12px;width:190px;height:7px;border-radius:4px;background:#fff}"""
    body = ('<div class="kicker">Every evening<br>in Los&nbsp;Angeles</div><div class="ph"><div class="scr"><div class="isl"></div>'
            f'<div class="dt">Friday, December 4</div><div class="tm">5:41</div><div class="ns">{cards}</div><div class="hm"></div></div></div>')
    return page(GOLD, NAVY, body, css)


# ---------- batch 5: new concepts ----------
def tag_yourself():
    cells = [("Silver Lake", "Has a natural wine opinion"), ("Santa Monica", "Already went on a run"), ("Echo Park", "Technically in a band"),
             ("West Hollywood", "Brunch is a personality"), ("Venice", "Owns a skateboard, rides a bike"), ("Highland Park", "Was here before it was cool"),
             ("The Valley", "Has a pool. Will mention it."), ("Downtown", "Lives for a rooftop"), ("Pasadena", "Has a favorite library")]
    grid = "".join(f'<div class="c"><b>{nob(n)}</b><span>{nob(t)}</span></div>' for n, t in cells)
    css = """.t{position:absolute;top:240px;width:100%;text-align:center;font-weight:900;font-size:76px;letter-spacing:-2px;line-height:1}.t span{color:#FF4F00}
.g{position:absolute;top:350px;left:90px;width:900px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.c{height:232px;background:#fff;border-radius:22px;padding:22px;display:flex;flex-direction:column;justify-content:center;text-align:center;box-shadow:0 6px 0 #1a1f4d}
.c b{font-size:34px;font-weight:900;letter-spacing:-.5px;color:#FF4F00;line-height:1.05;text-wrap:balance}
.c span{margin-top:12px;font-size:27px;font-weight:700;line-height:1.15;color:#1a1f4d;text-wrap:balance}"""
    body = f'<div class="kicker">Los&nbsp;Angeles<br>edition</div><div class="t">Tag <span>yourself</span></div><div class="g">{grid}</div>'
    return page(PINK, NAVY, body, css)


def alignment():
    cells = ["Leaves 40 minutes early", "Signals on the 405", "Saves six spots in the brunch line",
             "Shares their secret parking spot", "&ldquo;It&rsquo;s only 20 minutes&rdquo;", "Won&rsquo;t say where the tacos are",
             "Drives you to LAX", "Parks at the meter and runs", "Takes the 405 at 5 PM on purpose"]
    rows = ["LAWFUL", "NEUTRAL", "CHAOTIC"]; cols = ["GOOD", "NEUTRAL", "EVIL"]
    grid = '<div></div>' + "".join(f'<div class="ch">{c}</div>' for c in cols)
    for r in range(3):
        grid += f'<div class="rh">{rows[r]}</div>' + "".join(f'<div class="c">{nob(cells[r * 3 + k])}</div>' for k in range(3))
    css = """.t{position:absolute;top:240px;width:100%;text-align:center;font-weight:900;font-size:64px;letter-spacing:-1.5px;line-height:1;color:#fff}
.g{position:absolute;top:340px;left:60px;width:960px;display:grid;grid-template-columns:62px repeat(3,minmax(0,1fr));grid-template-rows:40px repeat(3,232px);gap:12px}
.ch{font-family:'IBM Plex Mono',monospace;font-size:20px;letter-spacing:3px;color:#FF9500;text-align:center;align-self:end}
.rh{font-family:'IBM Plex Mono',monospace;font-size:20px;letter-spacing:3px;color:#FF9500;writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;align-self:center}
.c{background:#fff;border-radius:18px;display:flex;align-items:center;justify-content:center;text-align:center;padding:18px;font-weight:800;font-size:30px;line-height:1.12;color:#1a1f4d;text-wrap:balance}"""
    body = f'<div class="kicker">Which one<br>are you</div><div class="t">Los&nbsp;Angeles alignment chart</div><div class="g">{grid}</div>'
    return page(NAVY, "#fff", body, css, dark=True)


def review_405():
    star = lambda on: f'<span style="color:{"#f4b400" if on else "#d6d6d6"}">&#9733;</span>'
    css = """.card{position:absolute;left:100px;top:240px;width:880px;height:890px;background:#fff;border-radius:40px;padding:48px 54px;box-shadow:0 30px 60px rgba(0,0,0,.18);font-family:-apple-system,'Inter Tight',sans-serif;color:#202124}
.nm{font-size:58px;font-weight:800;letter-spacing:-1px}.rt{font-size:30px;margin-top:8px;color:#5f6368}.rt b{color:#202124}.st{font-size:32px;letter-spacing:2px}
.cat{font-size:26px;color:#5f6368;margin-top:6px}.chips{display:flex;gap:12px;margin:26px 0 30px}.chips span{border:2px solid #dadce0;border-radius:30px;padding:10px 22px;font-size:22px;color:#1a73e8;font-weight:600}
.rv{border-top:2px solid #eee;padding-top:26px;margin-top:6px}.who{display:flex;align-items:center;gap:16px}.av{width:58px;height:58px;border-radius:50%;background:#FF4F00;color:#fff;font-weight:800;font-size:26px;display:flex;align-items:center;justify-content:center}
.who b{font-size:24px}.who small{display:block;font-size:19px;color:#5f6368}.rs{font-size:22px;color:#5f6368;margin-top:12px}.rx{font-size:31px;line-height:1.3;margin-top:8px;text-wrap:pretty}"""
    body = ('<div class="kicker">Reviews<br>are in</div><div class="card"><div class="nm">The 405</div>'
            f'<div class="rt"><b>1.2</b> <span class="st">{star(1)}{star(0)}{star(0)}{star(0)}{star(0)}</span> (48,019)</div><div class="cat">Freeway &middot; Los&nbsp;Angeles &middot; Open 24 hours, technically</div>'
            '<div class="chips"><span>Directions</span><span>Save</span><span>Leave earlier</span></div>'
            f'<div class="rv"><div class="who"><div class="av">J</div><div><b>Jordan</b><small>Local Guide &middot; 212 reviews</small></div></div><div class="rs">{star(1)}{star(0)}{star(0)}{star(0)}{star(0)} &nbsp;a week ago</div>'
            f'<div class="rx">{nob("Spent my twenties here. Saw the Getty from it once. Never actually got there. Would not drive again.")}</div></div>'
            f'<div class="rv" style="margin-top:26px"><div class="who"><div class="av" style="background:#0a84ff">P</div><div><b>Priya</b><small>3 reviews</small></div></div><div class="rs">{star(1)}{star(1)}{star(0)}{star(0)}{star(0)} &nbsp;2 days ago</div>'
            f'<div class="rx">{nob("Two stars because the sunset over the hills was nice. I had time to watch all of it.")}</div></div></div>')
    return page(GOLD, NAVY, body, css)


def weather_app():
    hours = [("Now", "64&deg;"), ("1PM", "65&deg;"), ("2PM", "66&deg;"), ("3PM", "65&deg;"), ("4PM", "63&deg;"), ("5PM", "61&deg;")]
    hr = "".join(f'<div><small>{h}</small><i>&#9728;&#65039;</i><b>{t}</b></div>' for h, t in hours)
    css = """.ph{position:absolute;left:50%;transform:translateX(-50%);top:228px;width:610px;height:912px;border-radius:84px;padding:11px;background:linear-gradient(145deg,#5b5b60,#2c2c2f 40%,#4a4a4e);box-shadow:0 40px 80px rgba(0,0,0,.28)}
.scr{width:100%;height:100%;border-radius:74px;overflow:hidden;position:relative;border:9px solid #000;background:linear-gradient(180deg,#3d7bd9 0%,#5fa0ea 55%,#8cbcf0 100%);color:#fff;font-family:-apple-system,'Inter Tight',sans-serif;text-align:center}
.isl{position:absolute;left:50%;transform:translateX(-50%);top:12px;width:150px;height:42px;background:#000;border-radius:24px}
.loc{margin-top:96px;font-size:40px;font-weight:500}.tmp{font-size:150px;font-weight:200;line-height:1;margin-left:30px}.cond{font-size:26px;font-weight:600}.hl{font-size:24px;font-weight:600;opacity:.9}
.bx{margin:28px 26px 0;background:rgba(255,255,255,.18);border-radius:26px;padding:20px 22px;text-align:left}.bx small{font-size:16px;letter-spacing:1px;opacity:.8;font-weight:600}
.bx b{display:block;font-size:52px;font-weight:300;margin-top:4px}.bx p{font-size:22px;margin-top:6px;line-height:1.25;text-wrap:balance}
.hrs{display:flex;justify-content:space-between;margin-top:16px}.hrs div{display:flex;flex-direction:column;gap:6px;font-size:19px}.hrs i{font-style:normal;font-size:24px}.hrs b{font-size:21px;font-weight:600}"""
    body = ('<div class="kicker">Today&rsquo;s<br>forecast</div><div class="ph"><div class="scr"><div class="isl"></div>'
            '<div class="loc">Los&nbsp;Angeles</div><div class="tmp">64&deg;</div><div class="cond">Mostly Sunny</div><div class="hl">H:66&deg; L:52&deg;</div>'
            '<div class="bx"><small>&#127777;&#65039; FEELS LIKE</small><b>Freezing</b><p>According to everyone you know. Puffer jackets advised.</p></div>'
            f'<div class="bx"><small>&#128336; HOURLY FORECAST</small><div class="hrs">{hr}</div></div></div></div>')
    return page(PINK, NAVY, body, css)


def dating_prompt():
    css = """.cd{position:absolute;left:120px;width:840px;background:#fff;border-radius:30px;padding:40px 46px 46px;box-shadow:0 20px 50px rgba(0,0,0,.14)}
.cd small{font-size:26px;font-weight:700;color:#1a1f4d}.cd p{font-family:'DM Serif Display',serif;font-size:50px;line-height:1.12;margin-top:16px;color:#111;text-wrap:balance}
.hrt{position:absolute;right:-26px;bottom:-26px;width:84px;height:84px;border-radius:50%;background:#fff;box-shadow:0 8px 20px rgba(0,0,0,.18);display:flex;align-items:center;justify-content:center;font-size:40px;color:#FF4F00}"""
    prompts = [("My most irrational fear", "Parallel parking on Abbot Kinney on a Saturday."), ("We&rsquo;ll get along if", "You know which day is street cleaning."),
               ("Green flag", "Offers to drive to my side of the 405.")]
    cards = "".join(f'<div class="cd" style="top:{240 + i * 300}px"><small>{a}</small><p>{nob(b)}</p><div class="hrt">&#9829;</div></div>' for i, (a, b) in enumerate(prompts))
    body = f'<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&display=swap" rel="stylesheet"><div class="kicker">Dating profile,<br>Los&nbsp;Angeles</div>{cards}'
    return page("#ffe9d6", NAVY, body, css)


def ticket():
    css = """.tk{position:absolute;left:50%;top:250px;transform:translateX(-50%) rotate(1.5deg);width:640px;background:#fffbe6;border:3px solid #c8102e;padding:34px 40px;font-family:'IBM Plex Mono',monospace;color:#222;box-shadow:0 30px 60px rgba(0,0,0,.2)}
.tk h4{background:#c8102e;color:#fff;text-align:center;font-size:26px;letter-spacing:3px;padding:12px;margin:-34px -40px 8px}.tk .p{text-align:center;font-size:16px;color:#c8102e;letter-spacing:2px;margin-bottom:18px}
.f{border-bottom:2px solid #ddd;padding:12px 0}.f small{display:block;font-size:15px;color:#888;letter-spacing:1.5px}.f b{font-size:28px;line-height:1.25;text-wrap:balance}
.fine{margin-top:22px}.fine span{display:block;font-size:15px;color:#888;letter-spacing:1.5px}.fine b{display:block;font-size:46px;color:#c8102e;line-height:1.1}
.st{position:absolute;right:70px;top:1000px;font-size:62px;color:#FF4F00;transform:rotate(-8deg)}"""
    fields = [("VIOLATION", "Believed the sign"), ("LOCATION", "The only open spot in Los&nbsp;Feliz"), ("VEHICLE", "Yours, unfortunately"),
              ("TIME", "4 minutes after you left"), ("NOTES", "There were five signs. You read four.")]
    fs = "".join(f'<div class="f"><small>{a}</small><b>{nob(b)}</b></div>' for a, b in fields)
    body = (f'<div class="kicker">Saturday<br>parking</div><div class="tk"><h4>PARKING CITATION</h4><div class="p">A PARODY &middot; NOT A REAL TICKET</div>{fs}'
            '<div class="fine"><span>FINE</span><b>Your whole Saturday</b></div></div><div class="st hand">every&nbsp;time</div>')
    return page(CREAM, NAVY, body, css)


def payments():
    rows = [("S", "#FF4F00", "Sam", "Alex", "Tacos and parking, split 3 ways", "$36.00"), ("P", "#0a84ff", "Priya", "Jordan", "Valet (why was it $25)", "$12.50"),
            ("T", "#AF52DE", "Taylor", "Nico", "Gas to the Valley and back", "$20.00"), ("A", "#34C759", "Ava", "Sam", "Brunch line holding fee", "$5.00"),
            ("J", "#FF9500", "Jordan", "Priya", "Parking ticket, my fault, sorry", "$73.00"), ("N", "#c8102e", "Nico", "Taylor", "Bowl tickets, parking was extra", "$58.00")]
    feed = "".join(f'<div class="r"><div class="av" style="background:{c}">{i}</div><div class="tx"><b>{a}</b> paid <b>{b}</b><p>{nob(n)}</p></div><div class="amt">{m}</div></div>' for i, c, a, b, n, m in rows)
    css = """.app{position:absolute;left:100px;top:236px;width:880px;height:880px;background:#fff;border-radius:40px;padding:36px 44px;box-shadow:0 30px 60px rgba(0,0,0,.18);font-family:-apple-system,'Inter Tight',sans-serif}
.app h3{font-size:40px;font-weight:800;letter-spacing:-.5px;margin-bottom:8px}.app h6{font-size:20px;color:#888;font-weight:600;margin-bottom:12px}
.r{display:flex;gap:20px;align-items:flex-start;padding:22px 0;border-bottom:1.5px solid #f0f0f0}.av{flex:none;width:62px;height:62px;border-radius:50%;color:#fff;font-weight:800;font-size:28px;display:flex;align-items:center;justify-content:center}
.tx{flex:1;font-size:25px;color:#111}.tx p{font-size:27px;margin-top:4px;color:#333;text-wrap:balance}.amt{font-size:26px;font-weight:700;color:#1a1f4d}"""
    body = f'<div class="kicker">The group<br>chat ledger</div><div class="app"><h3>Friends</h3><h6>THIS WEEK IN LOS&nbsp;ANGELES</h6>{feed}</div>'
    return page(GOLD, NAVY, body, css)


def this_or_that():
    pairs = [("Eastside", "Westside"), ("Al pastor", "Carne asada"), ("Beach day", "Mountain hike"), ("The Getty", "LACMA"), ("The 10", "The 405"), ("Dodger dog", "Stadium nachos")]
    rows = "".join(f'<div class="r"><span>{a}</span><i>or</i><span>{b}</span></div>' for a, b in pairs)
    css = """.t{position:absolute;top:240px;width:100%;text-align:center;font-weight:900;font-size:76px;letter-spacing:-2px;line-height:1;color:#fff}.t span{color:#FF9500}
.l{position:absolute;top:350px;left:110px;width:860px}.r{display:flex;align-items:center;gap:18px;margin-bottom:18px}
.r span{flex:1;background:#fff;color:#1a1f4d;border-radius:20px;padding:24px 10px;text-align:center;font-weight:800;font-size:38px}
.r i{font-family:'Caveat',cursive;font-style:normal;font-weight:700;font-size:44px;color:#FF9500}
.cap{position:absolute;top:1080px;width:100%;text-align:center;color:#fff;font-size:48px}"""
    body = f'<div class="kicker">Los&nbsp;Angeles<br>edition</div><div class="t">This <span>or</span> that</div><div class="l">{rows}</div><div class="cap hand">Comment your&nbsp;answers.</div>'
    return page("#0f4c5c", "#fff", body, css, dark=True)


def fill_blank():
    css = """.q{position:absolute;left:90px;right:90px;top:300px;font-weight:900;font-size:96px;letter-spacing:-3px;line-height:1.02;text-wrap:balance}
.q span{color:#FF4F00}.ln{position:absolute;left:90px;right:90px;height:6px;background:#1a1f4d;border-radius:3px}
.cap{position:absolute;left:90px;top:1040px;font-size:56px;color:#FF4F00}"""
    body = ('<div class="kicker">Finish<br>the sentence</div><div class="q">You know you&rsquo;ve lived in Los&nbsp;Angeles too long&nbsp;when<span>&hellip;</span></div>'
            '<div class="ln" style="top:820px"></div><div class="ln" style="top:920px"></div><div class="cap hand">Best answers get their own&nbsp;post.</div>')
    return page(CREAM, NAVY, body, css)


# ---------- batch 6: dating in Los Angeles ----------
def ios_date_plans():
    return iphone("Planning a first date<br>in Los&nbsp;Angeles", "Alex", [
        ("ts", "<b>Monday</b> 7:12 PM"), ("them", "drinks this week?"), ("me", "slammed. next week?"), ("them", "out of town. the 14th?"),
        ("me", "of december?"), ("them", "january"), ("me", "see you in 2027")], bg=PINK, receipt="Read 7:31 PM")


def ios_date_middle():
    return iphone("Meeting<br>in the middle", "Jamie", [
        ("ts", "<b>Thursday</b> 6:02 PM"), ("them", "let&rsquo;s meet in the middle"), ("me", "i&rsquo;m in silver lake"),
        ("them", "i&rsquo;m in santa monica"), ("me", "so&hellip; culver city"), ("them", "that&rsquo;s still 40 minutes"),
        ("me", "for both of us. that&rsquo;s love")], bg=CREAM, receipt=None)


def maps_date():
    return maps(kicker="Matched with someone<br>in Santa Monica", mins="1 hr 22 min", dist="19 mi",
                via="From Silver Lake, Friday at 6", cap="long distance, basically", bg="#B9BEE6")


def dictionary_dating():
    return dictionary(title="Dating <span>&rarr;</span> English", hdr=("WHAT THEY TEXT", "WHAT THEY MEAN"), rows=[
        ("&ldquo;I&rsquo;m slammed right now&rdquo;", "You live across the 405."),
        ("&ldquo;Let&rsquo;s grab coffee first&rdquo;", "This is round one of interviews."),
        ("&ldquo;I&rsquo;m pretty close to you&rdquo;", "Forty minutes with no traffic."),
        ("&ldquo;I&rsquo;m working on a few projects&rdquo;", "Please don&rsquo;t ask about the projects."),
        ("&ldquo;Let&rsquo;s play it by ear&rdquo;", "I&rsquo;ll cancel at 6:15.")], bg=PINK)


def receipt_date():
    return receipt(kicker="First date<br>in Los&nbsp;Angeles", sub="Thursday &middot; 7:30 PM &ndash; 10:05 PM", items=[
        ("Valet", "25.00"), ("Two mezcal cocktails", "44.00"), ("Bread (not free)", "9.00"), ("&ldquo;Shareable&rdquo; plates x 4", "72.00"),
        ("Rideshare home, surge pricing", "38.00"), ("Second date", "TBD")], total="$188.00",
        ty="THANK YOU. TEXT WHEN YOU GET HOME.", stamp="worth&nbsp;it?", bg=CREAM)


def match():
    css = """.cd{position:absolute;left:100px;top:240px;width:880px;height:880px;border-radius:44px;padding:70px 60px;text-align:center;color:#fff;
background:linear-gradient(160deg,#FF9500 0%,#FF4F00 45%,#AF52DE 100%);box-shadow:0 30px 60px rgba(0,0,0,.22)}
.its{font-family:'Caveat',cursive;font-weight:700;font-size:118px;line-height:1;transform:rotate(-4deg)}
.pp{display:flex;justify-content:center;margin:46px 0 34px}.pp div{width:190px;height:190px;border-radius:50%;border:8px solid #fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:76px}
.pp .a{background:#1a1f4d;font-size:54px;position:relative;z-index:2}.pp .b{background:#0f4c5c;margin-left:-30px}
.sub{font-size:38px;font-weight:700}.loc{display:inline-block;margin-top:22px;background:rgba(0,0,0,.22);border-radius:30px;padding:12px 28px;font-size:28px;font-weight:600}
.btns{display:flex;flex-direction:column;gap:18px;margin:44px auto 0;width:560px}.btns div{border-radius:44px;padding:22px;font-size:32px;font-weight:800}
.p1{background:#fff;color:#FF4F00}.p2{border:3px solid #fff}"""
    body = ('<div class="kicker">Dating apps<br>in Los&nbsp;Angeles</div><div class="cd"><div class="its">It&rsquo;s a match!</div>'
            '<div class="pp"><div class="a">You</div><div class="b">A</div></div><div class="sub">You and Alex liked each&nbsp;other.</div>'
            '<div class="loc">&#128205; 23 miles away &middot; 70 min on a Friday</div>'
            '<div class="btns"><div class="p1">Send a message</div><div class="p2">Check traffic first</div></div></div>')
    return page(CREAM, NAVY, body, css)


def search():
    sugg = ["lives across the 405", "wants to meet at 5 PM on a Friday", "doesn&rsquo;t validate parking",
            "says they&rsquo;re &ldquo;like 20 min away&rdquo;", "still hasn&rsquo;t seen the ocean", "picks the brunch spot with the line"]
    mag = '<svg width="30" height="30" viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" fill="none" stroke="#9aa0a6" stroke-width="2.4"/><path d="M15 15l6 6" stroke="#9aa0a6" stroke-width="2.4" stroke-linecap="round"/></svg>'
    rows = "".join(f'<div class="s">{mag}<span>is it a red flag if my date <b>{s}</b></span></div>' for s in sugg)
    css = """.box{position:absolute;left:90px;top:250px;width:900px;background:#fff;border-radius:40px;box-shadow:0 24px 60px rgba(0,0,0,.18);font-family:-apple-system,'Inter Tight',sans-serif;color:#202124;overflow:hidden}
.q{display:flex;align-items:center;gap:20px;padding:30px 36px;font-size:34px;border-bottom:2px solid #eee}.q i{display:inline-block;width:3px;height:40px;background:#1a73e8;margin-left:2px;vertical-align:middle}
.s{display:flex;align-items:center;gap:22px;padding:24px 36px;font-size:29px;line-height:1.25;color:#444}.s svg{flex:none}.s b{color:#111;font-weight:700}
.cap{position:absolute;left:0;width:100%;text-align:center;top:930px;font-size:58px;color:#FF4F00}"""
    body = (f'<div class="kicker">Searching at 1 AM<br>in Los&nbsp;Angeles</div><div class="box"><div class="q">{mag}<span>is it a red flag if my date<i></i></span></div>{rows}</div>'
            '<div class="cap hand">asking for a&nbsp;friend</div>')
    return page("#B9BEE6", NAVY, body, css)


def flags():
    flag = lambda c: f'<svg width="40" height="46" viewBox="0 0 40 46"><rect x="3" y="2" width="5" height="44" rx="2" fill="#1a1f4d"/><path d="M8 4 H36 L29 14 L36 24 H8 Z" fill="{c}"/></svg>'
    green = ["Offers to drive to your side of town", "Knows a spot with free parking", "Texts &ldquo;leaving now&rdquo; and means it", "Booked the table already"]
    red = ["Suggests the 405 at 5 PM", "&ldquo;5 minutes away&rdquo; from the Valley", "Wants to split the valet", "Sunday brunch, no reservation"]
    col = lambda items, c: "".join(f'<div class="it">{flag(c)}<span>{nob(t)}</span></div>' for t in items)
    css = """.t{position:absolute;top:240px;width:100%;text-align:center;font-weight:900;font-size:70px;letter-spacing:-2px;line-height:1}
.cols{position:absolute;top:350px;left:70px;width:940px;display:grid;grid-template-columns:1fr 1fr;gap:24px}
.h{font-family:'IBM Plex Mono',monospace;font-weight:700;font-size:26px;letter-spacing:4px;margin-bottom:14px;text-align:center}
.it{display:flex;gap:16px;align-items:center;background:#fff;border-radius:22px;padding:22px 22px;margin-bottom:16px;min-height:160px;font-weight:800;font-size:31px;line-height:1.15;box-shadow:0 6px 0 rgba(26,31,77,.9)}
.it svg{flex:none}.it span{text-wrap:balance}"""
    body = ('<div class="kicker">Los&nbsp;Angeles<br>edition</div><div class="t">Dating <span style="color:#1f9d55">green</span> and <span style="color:#c8102e">red</span> flags</div>'
            f'<div class="cols"><div><div class="h" style="color:#1f9d55">GREEN FLAGS</div>{col(green, "#1f9d55")}</div>'
            f'<div><div class="h" style="color:#c8102e">RED FLAGS</div>{col(red, "#c8102e")}</div></div>')
    return page(CREAM, NAVY, body, css)


def venn():
    css = """.t{position:absolute;top:250px;width:100%;text-align:center;font-weight:900;font-size:68px;letter-spacing:-2px;line-height:1.02}
.v{position:absolute;left:90px;top:400px}.lb{position:absolute;width:250px;text-align:center;font-weight:800;font-size:34px;line-height:1.12;color:#fff;text-wrap:balance}
.mid{position:absolute;left:390px;top:640px;width:300px;text-align:center;font-family:'Caveat',cursive;font-weight:700;font-size:76px;color:#1a1f4d;line-height:1;transform:rotate(-6deg)}
.cap{position:absolute;left:0;width:100%;text-align:center;top:1070px;font-size:50px;color:#FF4F00}"""
    svg = ('<svg class="v" width="900" height="620" viewBox="0 0 900 620"><circle cx="300" cy="310" r="290" fill="#FF4F00" fill-opacity=".85"/>'
           '<circle cx="600" cy="310" r="290" fill="#AF52DE" fill-opacity=".8"/>'
           '<path d="M450 59 A290 290 0 0 1 450 561 A290 290 0 0 1 450 59 Z" fill="#FF9500"/></svg>')
    body = (f'<div class="kicker">Dating in<br>Los&nbsp;Angeles</div><div class="t">Who you&rsquo;ll actually date</div>{svg}'
            '<div class="lb" style="left:125px;top:625px">People who swiped&nbsp;right</div>'
            '<div class="lb" style="left:705px;top:625px">People on your side of the&nbsp;405</div>'
            '<div class="mid">your ex</div><div class="cap hand">it&rsquo;s always the&nbsp;ex</div>')
    return page(PINK, NAVY, body, css)


MEMES = {"texts-parking": texts_parking, "texts-quake": texts_quake, "texts-rain": texts_rain, "texts-plans": texts_plans,
         "texts-outside": texts_outside, "bingo": bingo, "maps": maps, "dictionary": dictionary,
         "freeway": freeway, "parking": parking, "forecast": forecast, "chart": chart,
         "ios-brunch": ios_brunch, "ios-bowl": ios_bowl, "ios-towed": ios_towed, "ios-santaana": ios_santaana, "ios-valley": ios_valley,
         "ios-dinner": ios_dinner, "ios-hike": ios_hike, "ios-moving": ios_moving, "ios-celeb": ios_celeb,
         "bingo-date": bingo_date, "maps-friday": maps_friday, "freeway-eta": freeway_eta, "ipad-resolutions": ipad_resolutions,
         "ios-lax": ios_lax, "ios-coffee": ios_coffee, "ios-housewarming": ios_housewarming, "ios-snow": ios_snow, "ios-gym": ios_gym,
         "bingo-lax": bingo_lax, "maps-lax": maps_lax, "freeway-101": freeway_101, "dictionary-weather": dictionary_weather, "ipad-calendar": ipad_calendar,
         "receipt": receipt, "wrapped": wrapped, "lockscreen": lockscreen,
         "tag-yourself": tag_yourself, "alignment": alignment, "review-405": review_405, "weather-app": weather_app, "dating-prompt": dating_prompt,
         "ticket": ticket, "payments": payments, "this-or-that": this_or_that, "fill-blank": fill_blank,
         "ios-date-plans": ios_date_plans, "ios-date-middle": ios_date_middle, "maps-date": maps_date, "dictionary-dating": dictionary_dating,
         "receipt-date": receipt_date, "match": match, "search": search, "flags": flags, "venn": venn}


def main():
    folder = os.path.abspath(sys.argv[1])
    only = sys.argv[2:] or list(MEMES)
    os.makedirs(folder, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="haps-memes-")
    for slug in only:
        h = os.path.join(tmp, slug + ".html")
        open(h, "w", encoding="utf-8").write(MEMES[slug]())
        png = os.path.join(tmp, slug + ".png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=5000",
                        "--allow-file-access-from-files", "--window-size=1080,1350", f"--screenshot={png}", "file://" + h], capture_output=True)
        out = os.path.join(folder, f"meme-{slug}.jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90", png, "--out", out], capture_output=True)
        if not os.path.exists(out):
            sys.exit("render failed: " + slug)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(only)} meme cards in {folder}")


if __name__ == "__main__":
    main()
