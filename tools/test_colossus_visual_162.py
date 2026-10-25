#!/usr/bin/env python3
"""Regression checks for the 1.62 Crystal Colossus armor silhouette and emissive seams."""
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Colossus visual 1.62: " + message)


model = MODEL.read_text(encoding="utf-8")
for token in (
    "private final ModelPart shoulderArmorLeft;",
    "private final ModelPart shoulderArmorRight;",
    "private final ModelPart haunchArmorLeft;",
    "private final ModelPart haunchArmorRight;",
    'body.hasChild("shoulder_armor_left")',
    'body.hasChild("shoulder_armor_right")',
    'body.hasChild("haunch_armor_left")',
    'body.hasChild("haunch_armor_right")',
    'body.addOrReplaceChild("shoulder_armor_left"',
    'body.addOrReplaceChild("shoulder_armor_right"',
    'body.addOrReplaceChild("haunch_armor_left"',
    'body.addOrReplaceChild("haunch_armor_right"',
    'CubeListBuilder.create().texOffs(32, 224).addBox(-4.0F, -3.0F, -7.0F, 9.0F, 4.0F, 13.0F)',
    'CubeListBuilder.create().texOffs(0, 204).addBox(-4.0F, -3.0F, -7.0F, 8.0F, 4.0F, 14.0F)',
    "float armorShift = Mth.sin(ageInTicks * 0.048F) * 0.014F;",
    "this.shoulderArmorLeft.zRot = -0.18F + armorShift;",
    "this.haunchArmorRight.zRot = 0.10F - armorShift * 0.55F;",
    '"chest_core"',
    '"tail_tip"',
    '"spine_6"',
):
    require(token in model, "missing armor, animation, or core silhouette contract: " + token)

for child in ("shoulder_armor_left", "shoulder_armor_right", "haunch_armor_left", "haunch_armor_right"):
    require(model.count('body.addOrReplaceChild("' + child + '"') == 2,
            child + " must exist once in the normal model and once in the glow model")

regions = [
    (0, 204, 45, 222),
    (48, 204, 93, 222),
    (96, 204, 126, 220),
    (32, 224, 75, 242),
    (80, 224, 118, 241),
    (120, 224, 148, 240),
]
base_path = ASSETS / "textures/entity/mutagenkoloss.png"
glow_path = ASSETS / "textures/entity/mutagenkoloss_glow.png"
for path in (base_path, glow_path):
    with Image.open(path) as im:
        require(im.size == (256, 256), path.name + " must remain a 256x256 pixel atlas")

with Image.open(base_path) as im:
    rgba = im.convert("RGBA")
    for x1, y1, x2, y2 in regions:
        pixels = [rgba.getpixel((x, y)) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)]
        require(any(r < 65 and b < 115 and a == 255 for r, g, b, a in pixels),
                "armor UV patch must contain dark, opaque armor pixels")
        require(any(r > 90 and b > 115 and a == 255 for r, g, b, a in pixels),
                "armor UV patch must contain contrasting violet facets")

with Image.open(glow_path) as im:
    rgba = im.convert("RGBA")
    transparent = sum(1 for _, _, _, a in rgba.getdata() if a == 0)
    require(transparent > 40000, "glow atlas must remain mostly transparent")
    for x1, y1, x2, y2 in regions:
        pixels = [rgba.getpixel((x, y)) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)]
        require(any(g > 150 and b > 200 and a == 255 for r, g, b, a in pixels),
                "each armor UV patch must contain targeted cyan emissive seams")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.62\.0['\"]", build) is not None,
        "artifact must be version 1.62.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.62.0" in readme and "Version 1.61.0" in readme
        and "Aktueller Entwicklungsstand: 1.62.0" in readme,
        "README must retain new and previous releases plus current headline")
print("1.62 armor geometry, mirrored layers, movement, UV texture palette, emissive seams and release checks passed.")
