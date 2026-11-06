#!/usr/bin/env python3
"""make_favicon.py — draws the site icon (navy tile, white H) and writes every size the web needs:
assets/img/favicon.svg, /favicon.ico (16+32+48), assets/img/apple-touch-icon.png (180),
assets/img/icon-192.png, icon-512.png. Needs Google Chrome (same as make_og_card.py).
Colours are the site tokens: navy #292F71, white.   python3 scripts/make_favicon.py
Then: python3 scripts/normalize_chrome.py (adds the <link> tags to every page)."""
import os, struct, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NAVY = "#292F71"
SVG = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{NAVY}"/><path fill="#fff" d="M18 15h9v13h10V15h9v34h-9V36H27v13h-9z"/></svg>
'''
FLAT = SVG.replace('rx="14"', 'rx="0"')      # full-bleed square for the iOS icon (iOS rounds it itself)


def render(svg, size, out):
    with tempfile.TemporaryDirectory() as d:
        page = os.path.join(d, "i.html")
        open(page, "w").write(f'<html><body style="margin:0;background:transparent">{svg.replace("<svg ", f"<svg width=%d height=%d " % (size, size), 1)}</body></html>')
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                        f"--window-size={size},{size}", f"--screenshot={out}", "file://" + page],
                       check=True, capture_output=True)


def ico(pngs):
    data = [open(p, "rb").read() for p, _ in pngs]
    head = struct.pack("<HHH", 0, 1, len(pngs))
    off, ent = 6 + 16 * len(pngs), b""
    for (p, s), b in zip(pngs, data):
        ent += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(b), off)
        off += len(b)
    return head + ent + b"".join(data)


def main():
    if not os.path.exists(CHROME):
        sys.exit("Google Chrome not found at " + CHROME)
    open(os.path.join(IMG, "favicon.svg"), "w").write(SVG)
    tmp = tempfile.mkdtemp()
    sizes = []
    for s in (16, 32, 48):
        p = os.path.join(tmp, f"{s}.png"); render(SVG, s, p); sizes.append((p, s))
    open(os.path.join(ROOT, "favicon.ico"), "wb").write(ico(sizes))
    render(FLAT, 180, os.path.join(IMG, "apple-touch-icon.png"))
    render(SVG, 192, os.path.join(IMG, "icon-192.png"))
    render(SVG, 512, os.path.join(IMG, "icon-512.png"))
    print("wrote favicon.svg, favicon.ico, apple-touch-icon.png, icon-192.png, icon-512.png")


if __name__ == "__main__":
    main()
