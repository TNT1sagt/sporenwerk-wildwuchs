#!/usr/bin/env python3
"""Regression checks for the 1.59.0 Crystal Colossus visual pass."""
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Crystal Colossus visual 1.59: " + message)


model = MODEL_PATH.read_text(encoding="utf-8")
for token in (
    "private final ModelPart tailMid;",
    'this.tailMid = tail.getChild("tail_mid")',
    'this.tailTip = tailMid.getChild("tail_tip")',
    'PartDefinition tailMid = tail.addOrReplaceChild("tail_mid"',
    'PartDefinition tailTip = tailMid.addOrReplaceChild("tail_tip"',
    '"tail_spine_0"', '"tail_spine_1"', '"tail_spine_2"',
    '"tail_vein"', '"tail_mid_vein"', '"tail_tip_vein"',
    "this.tailMid.xRot", "this.tailTip.yRot",
    '"chest_core_mount"', '"chest_core"', '"armor_plate_left"',
    '"flank_crystal_left"', '"temple_crystal_left"',
    '"shoulder_crystal_left"', '"jaw_armor"',
    'addGlowCrystal(body, "flank_crystal_left"',
    'addGlowCrystal(head, "temple_crystal_left"',
):
    require(token in model, "missing model/animation part: " + token)
require('addCrystal(tailMid, "tail_spine_1"' in model
        and 'addGlowCrystal(tailTip, "tail_spine_2"' in model,
        "each animated tail joint needs a matching crystal and emissive overlay")
require("this.tailMid.yRot += Mth.sin(ageInTicks * 0.18F)" in model,
        "the tail must react during the Crystal Breath wind-up")

skin_path = ASSETS / "textures/entity/mutagenkoloss.png"
glow_path = ASSETS / "textures/entity/mutagenkoloss_glow.png"
with Image.open(skin_path) as im:
    skin = im.convert("RGBA")
require(skin.size == (256, 256), "main texture UV atlas must remain 256x256")
core_skin = [skin.getpixel((x, y)) for x in range(205, 254) for y in range(130, 173)]
require(any(r > 90 and b > 150 and g < 130 for r, g, b, a in core_skin),
        "chest core UV region must contain violet/cyan pixel art")
with Image.open(glow_path) as im:
    glow = im.convert("RGBA")
require(glow.size == (256, 256), "emissive texture must remain 256x256")
core_glow = [glow.getpixel((x, y)) for x in range(205, 254) for y in range(130, 173)]
require(any(a == 255 and g > 190 and b > 200 for r, g, b, a in core_glow),
        "chest core glow UV region must contain full-bright cyan pixels")
alpha = [pixel[3] for pixel in glow.getdata()]
require(alpha.count(0) > 40000 and alpha.count(255) > 700,
        "glow atlas must stay transparent outside major highlights")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.59\.0['\"]", build) is not None,
        "Gradle version must be 1.59.0")
readme = read("README.md")
require("Version 1.59.0" in readme and "Version 1.58.0" in readme
        and "Aktueller Entwicklungsstand: 1.59.0" in readme,
        "current and previous release notes must both be present")
print("1.59.0 chest core, layered head/flank crystals, segmented tail, glow atlas and release checks passed.")
