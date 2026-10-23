#!/usr/bin/env python3
"""Build a visual QA sheet from the exact PNGs generated for this Sporenwerk build."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import sys

root = Path(sys.argv[1]).resolve()
assets = root / "src/main/resources/assets/sporenwerk"
out = root / "qa-output/sporenwerk-art-preview.png"
out.parent.mkdir(parents=True, exist_ok=True)

W, H = 1400, 1320
canvas = Image.new("RGB", (W, H), (17, 25, 21))
draw = ImageDraw.Draw(canvas)
font = ImageFont.load_default()
build_text = (root / "build.gradle").read_text(encoding="utf-8")
version_match = re.search(r"version\s*=\s*['\"](\d+\.\d+\.\d+)['\"]", build_text)
release_version = version_match.group(1) if version_match else "UNKNOWN"
draw.text((24, 15), f"SPORENWERK: WILDWUCHS {release_version}  /  MINECRAFT PIXEL TEXTURE QA", fill=(234, 219, 169), font=font)
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

panel(24, 365, 1352, 210, "OPAQUE MINECRAFT BLOCK FACES (16x16)")
block_faces = [
    ("infektionsherd_top", "Mutagenherd"),
    ("mutagen_boden_top", "Infizierter Boden"),
    ("mutagen_boden_side", "Boden-Seite"),
    ("mutationsanker_top", "Heilanker"),
    ("sporenresistenter_block_top", "Resistenter Block"),
    ("sporenabwehr", "Sporenabwehr AUS"),
    ("sporenabwehr_active", "Sporenabwehr AN"),
    ("feldsammler", "Feldsammler vorne"),
    ("feldsammler_side", "Feldsammler Seite"),
    ("feldsammler_top", "Feldsammler oben"),
]
for idx, (name, label) in enumerate(block_faces):
    row, col = divmod(idx, 5)
    x = 37 + col*260
    y = 392 + row*82
    paste_scaled(assets/"textures/block"/f"{name}.png", x, y, 88, 55, label)

panel(24, 580, 1352, 200, "CROP GROWTH STAGES / CUTOUT")
crop_names = ["faserrohr", "bernsteinkappe", "rotwurzel", "filtermoos"]
for row, name in enumerate(crop_names):
    x = 45 + row*332
    draw.text((x, 606), name.upper(), fill=(221, 197, 127), font=font)
    for stage in range(3):
        path = assets/"textures/block"/f"{name}_stage{stage}.png"
        paste_scaled(path, x+stage*96, 625, 86, 92, f"stage {stage+1}")

panel(24, 795, 1352, 185, "LIVE MUTAGEN PHENOTYPES — MATURE PLANTS")
crop_names = ["faserrohr", "bernsteinkappe", "rotwurzel", "filtermoos"]
for crop_idx, name in enumerate(crop_names):
    x = 45 + crop_idx*332
    draw.text((x, 817), name.upper(), fill=(221, 197, 127), font=font)
    for strength in range(4):
        suffix = "" if strength == 0 else f"_mutagen{strength}"
        path = assets/"textures/block"/f"{name}_stage2{suffix}.png"
        label = "normal" if strength == 0 else f"Feld {strength}"
        paste_scaled(path, x + strength*67, 838, 57, 70, label)

panel(24, 995, 1352, 295, "ITEM ICONS AND MUTAGEN RESEARCH")
items = [
    "faser", "bernsteinkappe", "rotwurzel", "filtermoos", "faserrohr_samen",
    "bernsteinkappe_sporen", "rotwurzel_samen", "filtermoos_sporen",
    "pflanzenreste", "biomasse", "feldwissen", "maschinenteil", "filter",
    "feldhandbuch", "wurzelkonzentrat", "myzelkompost", "verwitterte_notiz", "sporenfiltermaske",
    "mutagenprobe", "mutagenextrakt", "mutagene_sporen", "feldscanner"
]
for idx, name in enumerate(items):
    col, row = idx % 9, idx // 9
    x, y = 35 + col*150, 1022 + row*84
    paste_scaled(assets/"textures/item"/f"{name}.png", x, y, 78, 57, name)
canvas.save(out, optimize=True)
print(f"Wrote art preview: {out}")
