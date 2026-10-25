#!/usr/bin/env python3
"""Regression checks that the 1.60 chest core resembles the specified visual target."""
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Colossus visual 1.60: " + message)


model = MODEL.read_text(encoding="utf-8")
for token in (
    "Version 1.60 reference chest scale",
    'addBox(-10.5F, -8.5F, -30.8F, 21.0F, 17.0F, 5.5F)',
    'addBox(-7.0F, -7.0F, -35.0F, 14.0F, 14.0F, 3.5F)',
    'addBox(-10.9F, -8.9F, -31.3F, 21.8F, 17.8F, 6.2F)',
    '"rib_crystal_left"', '"rib_crystal_right"',
    'addGlowCrystal(body, "rib_crystal_left"',
    '"tail_mid"', '"tail_spine_2"',
    '"temple_crystal_left"', '"shoulder_crystal_left"',
):
    require(token in model, "missing reference geometry: " + token)

for path in (ASSETS / "textures/entity/mutagenkoloss.png",
             ASSETS / "textures/entity/mutagenkoloss_glow.png"):
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
        require(rgba.size == (256, 256), path.name + " must remain a 256x256 atlas")
        core = [rgba.getpixel((x, y)) for x in range(204, 255) for y in range(128, 175)]
        require(any(r > 90 and b > 150 and g < 140 and a == 255 for r, g, b, a in core),
                path.name + " must contain violet/purple crystal facets in the chest-core UV zone")
        require(any(g > 170 and b > 200 and a == 255 for r, g, b, a in core),
                path.name + " must contain cyan highlights in the chest-core UV zone")

with Image.open(ASSETS / "textures/entity/mutagenkoloss_glow.png") as im:
    alpha = [p[3] for p in im.convert("RGBA").getdata()]
require(alpha.count(0) > 40000 and alpha.count(255) > 700,
        "glow atlas must remain mostly transparent outside luminous crystal details")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.60\.0['\"]", build) is not None,
        "artifact must use version 1.60.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.60.0" in readme and "Version 1.59.0" in readme
        and "Aktueller Entwicklungsstand: 1.60.0" in readme,
        "new release and previous release must both remain in the README")
print("1.60 chest scale, rib crystals, matching pixel atlases, glow transparency and release contracts passed.")
