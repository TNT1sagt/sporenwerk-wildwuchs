#!/usr/bin/env python3
"""Crystal Colossus animated crown regression (1.80.0)."""
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, msg):
    if not ok:
        raise SystemExit("Crystal Crown 1.80 regression: " + msg)


model = MODEL.read_text(encoding="utf-8")
require(model.count("return LayerDefinition.create(mesh, 256, 256);") == 2,
        "skin and emissive model must retain separate 256x256 layers")
for name in ("crystal_crown_left", "crystal_crown_right"):
    require(model.count('head.addOrReplaceChild("' + name + '"') == 2,
            "skin and emissive layers must both include " + name)
require(model.count('addOrReplaceChild("blade_tip"') == 4,
        "each crown must have a tapered crystal tip in each layer")
require(model.count('addOrReplaceChild("middle_blade"') == 4,
        "each crown must have a stepped mid-section in each layer")
require(model.count('addOrReplaceChild("lower_blade"') == 4,
        "each crown must have a structural crystal root in each layer")
for token in (
    "private final ModelPart crystalCrownLeft;",
    "private final ModelPart crystalCrownRight;",
    'head.hasChild("crystal_crown_left")',
    'head.hasChild("crystal_crown_right")',
    "this.crystalCrownLeft.zRot = -0.52F - crownBreathing - crownFlare;",
    "this.crystalCrownRight.zRot = 0.52F + crownBreathing + crownFlare;",
    "this.crystalCrownLeft.xScale = crownPulse;",
    "this.crystalCrownRight.xScale = crownPulse;",
    "entity.getAttackState() == MutagenkolossEntity.ATTACK_BREATH",
    "entity.getAttackState() == MutagenkolossEntity.ATTACK_AWAKENING",
    "float crownBreathing = Mth.sin(ageInTicks * 0.065F)",
):
    require(token in model, "missing matched crown rig/animation contract: " + token)
for name in ("cheek_armor_left", "cheek_armor_right"):
    require(model.count('head.addOrReplaceChild("' + name + '"') == 1,
            "dark cheek plate must be skin-only and anchored to the moving head: " + name)
require(model.count("PartPose.offsetAndRotation(-12.0F, -3.0F, 3.0F") == 2
        and model.count("PartPose.offsetAndRotation(12.0F, -3.0F, 3.0F") == 2,
        "skin and emissive crown pivots must stay aligned")
require("getChunk(" not in model and "getChunkNow(" not in model,
        "visual-only model must never touch world chunk loading")
require("void setupAnim(MutagenkolossEntity entity" in model,
        "new animations must run through existing synced boss model hook")
for texture in ("mutagenkoloss.png", "mutagenkoloss_glow.png"):
    path = ASSETS / "textures/entity" / texture
    require(path.is_file(), "missing Colossus texture: " + texture)
    with Image.open(path) as im:
        require(im.size == (256, 256),
                "the new crown must reuse the correct vanilla compatible 256x256 atlas")
build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.80\.0['\"]", build),
        "Gradle artifact is not 1.80.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Aktueller Entwicklungsstand: 1.80.0" in readme
        and "Version 1.80.0" in readme and "Version 1.79.0" in readme,
        "1.80 release history is incomplete")
print("1.80 Crystal Colossus crown geometry, mirrored bones, separate emissive overlay, synchronized phase animation and release data passed.")
