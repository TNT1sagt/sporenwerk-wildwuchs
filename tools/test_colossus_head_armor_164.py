#!/usr/bin/env python3
"""Regression tests for the Crystal Colossus brow and cheek armor (1.64.0)."""
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Colossus head armor 1.64: " + message)


model = MODEL.read_text(encoding="utf-8")
for name in ("brow_armor_left", "brow_armor_right", "cheek_armor_left", "cheek_armor_right"):
    require(f'head.addOrReplaceChild("{name}"' in model, "main model missing " + name)
    require(f'head.addOrReplaceChild("{name}"' in model, "glow model missing " + name)
# Each child is present twice in the source: once in the skin model and once in the glow model.
for name in ("brow_armor_left", "brow_armor_right", "cheek_armor_left", "cheek_armor_right"):
    require(model.count(f'head.addOrReplaceChild("{name}"') == 2,
            name + " must exist once in both model layers")
require("getChild(\"head\")" in model and "this.head.xRot" in model,
        "head armor must inherit the existing head look animation")

base_path = ASSETS / "textures/entity/mutagenkoloss.png"
glow_path = ASSETS / "textures/entity/mutagenkoloss_glow.png"
regions = [
    (152, 68, 178, 82), (152, 84, 178, 98),
    (184, 68, 210, 82), (184, 84, 210, 98),
    (216, 68, 243, 82), (216, 84, 243, 98),
]
for path in (base_path, glow_path):
    with Image.open(path) as im:
        require(im.size == (256, 256), path.name + " must stay 256x256")
with Image.open(base_path) as im:
    rgba = im.convert("RGBA")
    for x1,y1,x2,y2 in regions:
        pixels = [rgba.getpixel((x,y)) for x in range(x1,x2+1) for y in range(y1,y2+1)]
        require(any(r < 70 and a == 255 for r,g,b,a in pixels), "base plate region must have dark opaque pixels")
        require(any(r > 85 and b > 120 and a == 255 for r,g,b,a in pixels), "base plate region must have violet facets")
with Image.open(glow_path) as im:
    rgba = im.convert("RGBA")
    transparent = sum(1 for _,_,_,a in rgba.getdata() if a == 0)
    require(transparent > 40000, "glow atlas should remain mostly transparent")
    for x1,y1,x2,y2 in regions:
        pixels = [rgba.getpixel((x,y)) for x in range(x1,x2+1) for y in range(y1,y2+1)]
        require(any(g > 170 and b > 200 and a == 255 for r,g,b,a in pixels),
                "each armor region needs a targeted cyan emissive crack")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.64\.0['\"]", build) is not None,
        "artifact must be version 1.64.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.64.0" in readme and "Version 1.63.0" in readme
        and "Aktueller Entwicklungsstand: 1.64.0" in readme,
        "release notes must retain current/previous release")
print("1.64 head armor model layers, inherited look animation, dark pixel art, cyan emissive cracks and version checks passed.")
