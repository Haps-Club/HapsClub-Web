#!/usr/bin/env python3
"""Render the Haps Club link-preview (Open Graph) card in the Sunset system.
Writes assets/og-card.png at 1200x630 (and @2x). Fonts + logo come from /tmp/f."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H, S = 1200, 630, 2                      # S = supersample factor
FD = '/tmp/f'
WGT = {'ExtraBold': 800, 'SemiBold': 600, 'Medium': 500}
def f(w, px):
    fo = ImageFont.truetype(f'{FD}/InterVar.ttf', px * S)
    fo.set_variation_by_axes([14, WGT[w]])   # optical size, weight
    return fo

# --- Sunset gradient, 135deg: #FF9500 0% -> #FF3B30 38% -> #AF52DE 72% -> #292F71 100%
STOPS = [(0.00, (0xFF,0x95,0x00)), (0.38, (0xFF,0x3B,0x30)),
         (0.72, (0xAF,0x52,0xDE)), (1.00, (0x29,0x2F,0x71))]
def at(t):
    for i in range(len(STOPS)-1):
        a, b = STOPS[i], STOPS[i+1]
        if a[0] <= t <= b[0]:
            k = (t-a[0])/(b[0]-a[0]) if b[0] > a[0] else 0
            return tuple(round(a[1][j] + (b[1][j]-a[1][j])*k) for j in range(3))
    return STOPS[-1][1]

cw, ch = W*S, H*S
img = Image.new('RGB', (cw, ch))
px = img.load()
# 135deg in CSS runs top-left -> bottom-right
for y in range(ch):
    for x in range(cw):
        px[x, y] = at((x/cw + y/ch) / 2)
d = ImageDraw.Draw(img)

def text(xy, s, font, fill=(255,255,255), anchor='la', spacing=None):
    d.text((xy[0]*S, xy[1]*S), s, font=font, fill=fill, anchor=anchor)

# --- logo, top left
logo = Image.open(f'{FD}/logo-white.png').convert('RGBA')
lh = 132*S
logo = logo.resize((round(logo.width*lh/logo.height), lh), Image.LANCZOS)
img.paste(logo, (64*S, 46*S), logo)

# --- kicker, top right
kf = f('SemiBold', 19)
kick = 'LOS ANGELES  ·  WEEKLY'
d.text(((W-64)*S, 104*S), ' '.join(kick), font=kf, fill=(255,255,255,235), anchor='rs')
kw = d.textlength(' '.join(kick), font=kf)
d.ellipse([((W-64)*S-kw-30*S, 90*S), ((W-64)*S-kw-16*S, 104*S)], fill=(255,255,255))

# --- headline
hf = f('ExtraBold', 92)
text((64, 214), "Here\u2019s what\u2019s", hf)
text((64, 314), "good.", hf)

# --- sub
sf = f('Medium', 30)
text((64, 442), 'Hand-picked events, food & culture —', sf, (255,255,255,236))
text((64, 484), 'one free email every Tuesday.', sf, (255,255,255,236))

# --- footer: domain + pill
df = f('ExtraBold', 30)
text((64, 552), 'haps.club', df)

pf = f('SemiBold', 26)
label = 'Subscribe free'
tw = d.textlength(label, font=pf)
pw, ph = tw + 60*S, 62*S
x1, y1 = (W-64)*S, 582*S
d.rounded_rectangle([x1-pw, y1-ph, x1, y1], radius=ph//2, fill=(255,255,255))
d.text((x1-pw/2, y1-ph/2), label, font=pf, fill=(0x29,0x2F,0x71), anchor='mm')

out = img.resize((W, H), Image.LANCZOS)
os.makedirs('assets', exist_ok=True)
out.save('assets/og-card.png', optimize=True)
img.resize((W*2, H*2), Image.LANCZOS).save('assets/og-card@2x.png', optimize=True)
print('wrote assets/og-card.png', os.path.getsize('assets/og-card.png'), 'bytes')
print('wrote assets/og-card@2x.png', os.path.getsize('assets/og-card@2x.png'), 'bytes')
