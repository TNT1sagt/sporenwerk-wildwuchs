#!/usr/bin/env python3
"""Build a visual QA sheet from the exact PNGs generated for this Sporenwerk build."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

root = Path(sys.argv[1]).resolve()
assets = root / "src/main/resources/assets/sporenwerk"
out = root / "qa-output/sporenwerk-art-preview.png"
out.parent.mkdir(parents=True, exist_ok=True)

W, H = 1400, 920
canvas = Image.new("RGB", (W, H), (17, 25, 21))
draw = ImageDraw.Draw(canvas)
font = ImageFont.load_default()
draw.text((24, 15), "SPORENWERK: WILDWUCHS 1.2.0  /  ART REVIEW", fill=(234, 219, 169), font=font)
draw.line((24, 35, W-24, 35), fill=(103, 132, 100), width=1)

def panel(x, y, w, h, title):
    draw.rectangle((x, y, x+w, y+h), fill=(25, 38, 30), outline=(77, 98, 73), width=1)
    draw.text((x+8, y+7), title, fill=(210, 203, 161), font=font)

def paste_scaled(path, x, y, maxw, maxh, label=None):
    path = Path(path)
    if not path.is_file():
        draw.text((x, y), "MISSING: " + path.name, fill=(235, 90, 80), font=font)
        return
    image = Image.open(path).convert("RGBA")
    factor = min(maxw / image.width, maxh / image.height)
    size = (max(1, int(image.width*factor)), max(1, int(image.height*factor)))
    image = image.resize(size, Image.Resampling.NEAREST)
    canvas.paste(image, (x+(maxw-size[0])//2, y+(maxh-size[1])//2), image)
    if label:
        draw.text((x, y+maxh+2), label, fill=(188, 201, 180), font=font)

panel(24, 48, 258, 300, "MACHINE WINDOW")
paste_scaled(assets/"textures/gui/machine_interface.png", 45, 72, 215, 240)
panel(294, 48, 405, 300, "FIELD KNOWLEDGE / SKILL TREE")
paste_scaled(assets/"textures/gui/skilltree_interface.png", 308, 78, 380, 245)
panel(713, 48, 663, 300, "DISTINCT MACHINE PANELS")
machine_names = ["feldsammler", "saatgutpresse", "biomasse_bioreaktor"]
for i, name in enumerate(machine_names):
    paste_scaled(assets/"textures/block"/f"{name}_panel.png", 735+i*210, 105, 160, 130, name.upper())
    paste_scaled(assets/"models/block"/f"{name}.json", 735+i*210, 250, 1, 1, None) if False else None

panel(24, 365, 1352, 240, "CROP GROWTH STAGES")
crop_names = ["faserrohr", "bernsteinkappe", "rotwurzel", "filtermoos"]
for row, name in enumerate(crop_names):
    x = 45 + row*332
    draw.text((x, 392), name.upper(), fill=(221, 197, 127), font=font)
    for stage in range(3):
        path = assets/"textures/block"/f"{name}_stage{stage}.png"
        paste_scaled(path, x+stage*96, 414, 86, 105, f"stage {stage+1}")

panel(24, 620, 1352, 275, "ITEM ICONS AND STORY")
items = [
    "faser", "bernsteinkappe", "rotwurzel", "filtermoos", "faserrohr_samen",
    "bernsteinkappe_sporen", "rotwurzel_samen", "filtermoos_sporen",
    "pflanzenreste", "biomasse", "feldwissen", "maschinenteil", "filter",
    "feldhandbuch", "wurzelkonzentrat", "myzelkompost", "verwitterte_notiz",
    "daemmerling_spawn_egg"
]
for idx, name in enumerate(items):
    col, row = idx % 9, idx // 9
    x, y = 45 + col*145, 655 + row*108
    paste_scaled(assets/"textures/item"/f"{name}.png", x, y, 86, 76, name)
canvas.save(out, optimize=True)
print(f"Wrote art preview: {out}")
