#!/usr/bin/env python3
"""
Generate a simple 32x32 icon for the EasyEDA to KiCad addon.
Requires Pillow: pip install Pillow

Run this script once to produce icon.png in the same directory.
"""

from __future__ import annotations

import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit(
        "Pillow is required to generate the icon.\n"
        "Install it with:  pip install Pillow"
    )

SIZE = 32
BG_COLOUR = (0, 100, 200)      # blue
TEXT_COLOUR = (255, 255, 255)  # white

img = Image.new("RGBA", (SIZE, SIZE), BG_COLOUR)
draw = ImageDraw.Draw(img)

# Draw a simple "E→K" label
try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 10)
except OSError:
    font = ImageFont.load_default()

draw.text((2, 10), "E→K", fill=TEXT_COLOUR, font=font)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
img.save(out_path)
print(f"Icon saved to {out_path}")
