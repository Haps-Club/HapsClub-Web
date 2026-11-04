#!/usr/bin/env python3
"""Render the Haps Club link-preview (Open Graph) card, Design F (Nov 2026).

The card is plain HTML in scripts/og_card.html (fonts, colors and copy live
there). This renders it with headless Chrome:

    python3 scripts/make_og_card.py

Writes assets/og-card@2x.png (2400x1260) and assets/og-card.png (1200x630).
Every page's og:image / twitter:image points at https://haps.club/assets/og-card.png.
Apps cache link previews, so a new card can take a few days to show on old shares.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRC = os.path.join(ROOT, "scripts", "og_card.html")
OUT2X = os.path.join(ROOT, "assets", "og-card@2x.png")
OUT = os.path.join(ROOT, "assets", "og-card.png")

if not os.path.exists(CHROME):
    sys.exit("Google Chrome not found at " + CHROME)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--allow-file-access-from-files", "--force-device-scale-factor=2",
                "--window-size=1200,630", "--virtual-time-budget=6000",
                "--screenshot=" + OUT2X, "file://" + SRC],
               check=True, capture_output=True)
subprocess.run(["sips", "-z", "630", "1200", OUT2X, "--out", OUT], check=True, capture_output=True)
for p in (OUT2X, OUT):
    print("wrote", os.path.relpath(p, ROOT), os.path.getsize(p), "bytes")
