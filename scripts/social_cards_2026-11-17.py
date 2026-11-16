#!/usr/bin/env python3
"""Render the Nov 17 2026 Haps social cards (Jazz Age Party, Happy Hour, Dinner) with headless Chrome.
Run from repo root: python3 scripts/social_cards_2026-11-17.py   (needs Google Chrome; sips for jpg)"""
import os, subprocess, tempfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'social/2026-11-17'); SRC=os.path.join(OUT,'src')
LOGO='file://'+os.path.join(ROOT,'assets/img/haps-logo.svg')
CH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
HP,FO,MU='#FF4F00','#FF9500','#AF52DE'
CSS='''@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;800;900&family=IBM+Plex+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;overflow:hidden;background:#111}
.s{position:relative;width:1080px;font-family:'Inter Tight',Helvetica,Arial,sans-serif;color:#fff;overflow:hidden}
.bg{position:absolute;inset:0;background-size:cover}
.bar{position:absolute;left:0;top:0;width:100%;height:14px;background:linear-gradient(90deg,#FF9500 0%,#FF4F00 40%,#AF52DE 75%,#292F71 100%);z-index:5}
.top{position:absolute;left:84px;right:84px;top:84px;display:flex;justify-content:space-between;align-items:flex-start;z-index:4}
.top img{width:132px;height:132px;filter:brightness(0) invert(1)}
.m{font-family:'IBM Plex Mono',Menlo,monospace;font-size:28px;letter-spacing:1px;text-transform:uppercase;line-height:1.35;text-align:right;color:#F1ECE6}
.pill{display:inline-block;font-family:'IBM Plex Mono',Menlo,monospace;font-size:26px;letter-spacing:1px;text-transform:uppercase;padding:12px 22px;border-radius:999px;color:#fff;margin-bottom:30px}
h1{font-weight:900;font-size:150px;line-height:.92;letter-spacing:-6px}
h2{font-weight:900;font-size:112px;line-height:.95;letter-spacing:-4px}
.sub{font-size:42px;line-height:1.3;font-weight:500;letter-spacing:-.5px;margin-top:30px;max-width:900px}
.meta{border-top:3px solid currentColor;margin-top:44px;padding-top:26px;display:flex;justify-content:space-between;gap:30px}
.meta div{font-family:'IBM Plex Mono',Menlo,monospace;font-size:27px;line-height:1.45;text-transform:uppercase;opacity:.85}
.meta b{display:block;font-weight:500;opacity:1}
.cta{font-family:'IBM Plex Mono',Menlo,monospace;font-size:27px;letter-spacing:1px;text-transform:uppercase;margin-top:26px;font-weight:500}
/* A: bottom text over full photo */
.A .shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,.15) 45%,rgba(0,0,0,.82) 78%,rgba(0,0,0,.92) 100%)}
.A .mid{position:absolute;left:84px;right:84px;bottom:192px;z-index:3}
/* B: photo top, color panel bottom */
.B .ph{position:absolute;left:0;top:0;right:0;height:540px;background-size:cover}
.B .shade{position:absolute;left:0;top:0;right:0;height:300px;background:linear-gradient(180deg,rgba(0,0,0,.45),rgba(0,0,0,0))}
.B .panel{position:absolute;left:0;right:0;bottom:0;top:540px;padding:50px 84px 0}
.B h1{font-size:124px}
.B .sub{font-size:38px;margin-top:22px}
/* C: poster, headline at top, white info bar at bottom */
.C .shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.7) 0%,rgba(0,0,0,.35) 45%,rgba(0,0,0,.1) 70%,rgba(0,0,0,.35) 100%)}
.C .head{position:absolute;left:84px;right:84px;top:290px;z-index:3}
.C .info{position:absolute;left:84px;right:84px;bottom:184px;background:#fff;color:#111;border-radius:26px;padding:34px 42px;z-index:3}
.C .info .sub{font-size:36px;margin:0 0 20px;color:#2A2622;max-width:none}
.C .info .meta{margin-top:0;border-top:3px solid #111}
.C .info .cta{color:#FF4F00;margin-top:18px}
/* D: photo band + white list panel */
.D .ph{position:absolute;left:0;top:0;right:0;height:440px;background-size:cover}
.D .shade{position:absolute;left:0;top:0;right:0;height:260px;background:linear-gradient(180deg,rgba(0,0,0,.45),rgba(0,0,0,0))}
.D .panel{position:absolute;left:0;right:0;top:440px;bottom:0;background:#fff;color:#111;padding:56px 84px 0}
.D h2{font-size:92px}
.D ul{list-style:none;margin-top:24px}
.D li{font-size:40px;font-weight:500;letter-spacing:-.5px;padding:12px 0;border-bottom:2px solid #E4DED6;color:#2A2622}
.D .meta{margin-top:30px;border-color:#111;color:#111}
.D .meta div{color:#6B6560}.D .meta b{color:#111}
.D .cta{color:#FF4F00;margin-top:20px}
'''
def meta(m): return '<div class="meta">'+''.join(f'<div><b>{a}</b>{b}</div>' for a,b in m)+'</div>'
def html(c,h):
    L=c['layout']; img='file://'+os.path.join(SRC,c['img'])+''; bgpos=c.get('pos','center')
    top=f'<div class="bar"></div><div class="top"><img src="{LOGO}"><div class="m">Los Angeles<br>{c["tag"]}</div></div>'
    pill=f'<span class="pill" style="background:{c["pillc"]}">{c["pill"]}</span>'
    cta=f'<div class="cta">{c.get("cta","Link in bio")}</div>'
    if L=='A':
        body=f'<div class="bg" style="background-image:url({img});background-position:{bgpos}"></div><div class="shade"></div>{top}<div class="mid">{pill}<h2>{c["h"]}</h2><p class="sub">{c["sub"]}</p>{meta(c["meta"])}{cta}</div>'
    elif L=='B':
        body=f'<div class="ph" style="background-image:url({img});background-position:{bgpos}"></div><div class="shade"></div>{top}<div class="panel" style="background:{c["panelc"]}">{pill}<h1>{c["h"]}</h1><p class="sub">{c["sub"]}</p>{meta(c["meta"])}</div>'
    elif L=='C':
        body=f'<div class="bg" style="background-image:url({img});background-position:{bgpos}"></div><div class="shade"></div>{top}<div class="head">{pill}<h1>{c["h"]}</h1></div><div class="info"><p class="sub">{c["sub"]}</p>{meta(c["meta"])}{cta}</div>'
    elif L=='D':
        lis=''.join(f'<li>{x}</li>' for x in c['list'])
        body=f'<div class="ph" style="background-image:url({img});background-position:{bgpos}"></div><div class="shade"></div>{top}<div class="panel">{pill}<h2>{c["h"]}</h2><ul>{lis}</ul>{meta(c["meta"])}{cta}</div>'
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="s {L}" style="height:{h}px">{body}</div></body></html>'
CARDS=[
 dict(name='jazz-1-coupe',layout='A',img='jazzage.jpg',pill='&#9829; Haps pick',pillc=HP,tag='Haps pick',h='The Jazz Age Party',sub='40+ are already coming. Live jazz, an open bar of Prohibition-era cocktails, and a historic home turning 100.',meta=[('Sat Nov 21','7:30&ndash;11 PM'),('$45 &middot; $80 for two','HAPSCLUBPLUS: 10% off')]),
 dict(name='jazz-2-sax',layout='C',img='jazz-sax.jpg',pos='center top',pill='Sat Nov 21',pillc=MU,tag='Haps pick',h='Saturday night, 1926.',sub='A live jazz trio, an open bar of Prohibition-era cocktails, and candlelight in a home that turned 100.',meta=[('Sat Nov 21','7:30&ndash;11 PM'),('$45 &middot; $80 for two','Jazz Age dress')]),
 dict(name='hh-1-margarita',layout='A',img='hh-margarita.jpg',pos='center 30%',pill='Free &middot; Thu Nov 19',pillc=FO,tag='Free to RSVP',h='Happy Hour at Hermanito',sub='See each other before the holidays get crazy. Drinks, bites, and new faces.',meta=[('Thu Nov 19','6&ndash;8 PM'),('Hermanito Broadway','Santa Monica')]),
 dict(name='hh-2-tomorrow',layout='B',img='hh-cider.jpg',pos='center 35%',panelc=HP,pill='Happy Hour',pillc='#111111',tag='Free to RSVP',h='Tomorrow, 6&nbsp;PM.',sub='Hermanito Broadway, Santa Monica. Join 50+ people, and RSVP to hold your spot.',meta=[('Thu Nov 19','6&ndash;8 PM'),('Free','RSVP on Luma')],cta=None),
 dict(name='dinner-1-taco',layout='A',img='dinner-taco.jpg',pos='center 60%',pill='Dinner series',pillc='#111111',tag='Tickets on Luma',h='Dinner at Hermanito',sub='A family-style dinner with one drink included. Everyone who&rsquo;s been is a fan.',meta=[('Thu Dec 10','6&ndash;9 PM'),('From $79','Hermanito Broadway')]),
 dict(name='dinner-2-menu',layout='D',img='dinner-table.jpg',pos='center 40%',pill='Thu Dec 10',pillc=FO,tag='Dinner series',h='What&rsquo;s on the table',list=['Guacamole, chips and salsa','Caesar salad and papas flautas','Sticky ribs and a variety of tacos','Dessert, and one drink included'],meta=[('Thu Dec 10 &middot; 6&ndash;9 PM','Hermanito Broadway'),('From $79','Santa Monica')]),
]
STORIES=[
 dict(name='story-hh-tonight',layout='C',img='hh-margarita.jpg',pos='center 25%',pill='Free &middot; Tonight',pillc=FO,tag='Sponsored by Blackbird',h='Tonight, 6&nbsp;PM.',sub='Happy Hour at Hermanito Broadway. Drinks, bites, and new faces.',meta=[('Thu Nov 19','6&ndash;8 PM'),('Hermanito Broadway','Santa Monica')],cta='Tap for details'),
]
def render(c,h):
    c=dict(c)
    if c.get('cta',1) is None: c['cta']=''
    p=os.path.join(tempfile.gettempdir(),c['name']+'.html'); open(p,'w').write(html(c,h))
    png=os.path.join(OUT,c['name']+'.png')
    subprocess.run([CH,'--headless=new','--disable-gpu','--allow-file-access-from-files','--hide-scrollbars',f'--window-size=1080,{h}','--virtual-time-budget=9000',f'--screenshot={png}','file://'+p],capture_output=True)
    jpg=png[:-4]+'.jpg'; subprocess.run(['sips','-s','format','jpeg','-s','formatOptions','90',png,'--out',jpg],capture_output=True); os.remove(png); print(jpg)
if __name__=='__main__':
    os.makedirs(SRC,exist_ok=True)
    jz=os.path.join(SRC,'jazzage.jpg')
    if not os.path.exists(jz): subprocess.run(['cp',os.path.join(ROOT,'social/2026-11-10/src/jazzage.jpg'),jz])
    for c in CARDS: render(c,1350)
    for c in STORIES: render(c,1920)
