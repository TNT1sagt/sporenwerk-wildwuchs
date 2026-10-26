#!/usr/bin/env python3
"""Regression for articulated Crystal Colossus jaw and mouth-based breath windup (1.81.0)."""
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(value, description):
    if not value:
        raise SystemExit("Colossus jaw 1.81 regression: " + description)


model = read("src/main/java/de/sporenwerk/client/MutagenkolossModel.java")
entity = read("src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java")
require(model.count("return LayerDefinition.create(mesh, 256, 256);") == 2,
        "skin and glow geometry must retain their independent original UV atlases")
require(model.count('head.addOrReplaceChild("lower_jaw"') == 2,
        "skin and glow must share precisely matched jaw hinges")
require(model.count("PartPose.offset(0.0F, 2.0F, -6.0F)") == 2,
        "both model layers must pivot at the same rear attachment to the skull")
require('lowerJaw.addOrReplaceChild("jaw_armor"' in model,
        "existing 1.59 armor must move with the lower jaw")
require('head.addOrReplaceChild("jaw_armor"' not in model,
        "there must not be a second, static, obstructing jaw armor")
require('lowerJawGlow.addOrReplaceChild("mouth_glow"' in model,
        "mouth light must move with the jaw")
for bone in ("lower_fang_left", "lower_fang_right", "lower_fang_glow_left", "lower_fang_glow_right"):
    require('addOrReplaceChild("' + bone + '"' in model,
            "moving jaws must retain coherent physical and glowing crystal teeth: " + bone)
require("private final ModelPart lowerJaw;" in model
        and 'head.hasChild("lower_jaw")' in model,
        "both model instances must bind the independently animated jaw")
for token in (
    "entity.getAttackState()",
    "entity.getAttackTicks()",
    "(48.0F - entity.getAttackTicks()) / 48.0F",
    "elapsed * elapsed * (3.0F - 2.0F * elapsed)",
    "jawOpening = 0.12F + 0.66F * anticipation",
    "attackState == MutagenkolossEntity.ATTACK_AWAKENING",
    "attackState == MutagenkolossEntity.ATTACK_STOMP",
    "this.lowerJaw.xRot = Mth.clamp(jawOpening, 0.0F, 0.80F)",
    "this.lowerJaw.yRot = 0.0F;",
    "this.lowerJaw.zRot = 0.0F;",
):
    require(token in model, "phase-aware jaw motion missing: " + token)

require("this.level().isClientSide" in entity and "SynchedEntityData" in entity,
        "model animation must remain bound to original synchronized server state")
windup = entity.find("private void emitWindupParticles()")
release = entity.find("private void releaseAttack(", windup)
require(windup >= 0 and release > windup, "cannot isolate boss charge effect")
section = entity[windup:release]
for token in (
    "this.getLookAngle().normalize()",
    "mouthOrigin",
    "facing.scale(1.65D)",
    "(48.0D - this.attackTicksLeft) / 48.0D",
    "double spread = 0.55D - charge * 0.35D",
    "ParticleTypes.DRAGON_BREATH",
    "ParticleTypes.END_ROD",
    "if (this.attackTicksLeft % 6 != 0) return;",
):
    require(token in section, "mouth-based charging effect missing: " + token)
require("this.getX(), this.getY() + 2.2D, this.getZ(), 12" not in section,
        "do not render obsolete stationary breath clouds inside the Colossus body")
require("private void performCrystalBreath()" in entity
        and "this.attackCooldown = 128;" in entity,
        "actual breath attack and timing must remain intact")
require("getChunk(" not in model and "getChunkNow(" not in model,
        "client model may not force load chunks")

for name in ("mutagenkoloss.png", "mutagenkoloss_glow.png"):
    path = ASSETS / "textures/entity" / name
    require(path.is_file(), "missing Colossus atlas: " + name)
    with Image.open(path) as im:
        require(im.size == (256, 256), "wrong main/glow atlas dimensions")

gradle = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.81\.0['\"]", gradle),
        "built artifact is not 1.81.0")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.81.0" in readme
        and "Version 1.81.0" in readme and "Version 1.80.0" in readme,
        "README must preserve 1.80 and announce 1.81")
print("1.81 independently jointed lower jaw, moving light fangs, countdown-synced attack telegraph and texture/version checks passed.")
