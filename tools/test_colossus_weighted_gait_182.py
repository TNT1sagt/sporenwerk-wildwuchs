#!/usr/bin/env python3
"""Regression checks for the four-leg weighted Crystal Colossus walk cycle (1.82.0)."""
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(value, message):
    if not value:
        raise SystemExit("Colossus weighted gait 1.82 regression: " + message)


s = MODEL.read_text(encoding="utf-8")
for token in (
    "private static void animateWeightedLeg(ModelPart leg, float phase, float stride, boolean rearLeg)",
    "ModelPart lowerLeg = leg.getChild(\"lower_leg\");",
    "ModelPart paw = lowerLeg.getChild(\"paw\");",
    "float lift = Math.max(0.0F, Mth.cos(phase)) * stride;",
    "lowerLeg.xRot = Math.max(0.0F, -swing)",
    "paw.xRot = -leg.xRot * 0.38F - lowerLeg.xRot * 0.55F;",
    "paw.y = 6.0F - lift * 1.65F;",
    "paw.z = -1.0F - lift * 0.45F;",
    "float stride = Mth.clamp(limbSwingAmount, 0.0F, 1.0F);",
    "float stridePhase = limbSwing * 0.42F;",
    "this.body.zRot = Mth.sin(stridePhase) * stride * 0.026F;",
    "this.head.zRot = -this.body.zRot * 0.60F;",
):
    require(token in s, "missing weighted step, knee or counterbalance contract: " + token)
for token in (
    "animateWeightedLeg(this.frontLeft, stridePhase, stride, false);",
    "animateWeightedLeg(this.frontRight, stridePhase + Mth.PI, stride, false);",
    "animateWeightedLeg(this.rearLeft, stridePhase + Mth.PI, stride, true);",
    "animateWeightedLeg(this.rearRight, stridePhase, stride, true);",
):
    require(token in s, "four legs must have paired opposite diagonal phases: " + token)
for token in (
    "this.tail.yRot += Mth.sin(stridePhase - 0.65F) * stride * 0.055F;",
    "this.tailMid.yRot += Mth.sin(stridePhase - 1.15F) * stride * 0.095F;",
    "this.tailTip.yRot += Mth.sin(stridePhase - 1.70F) * stride * 0.14F;",
    'ModelPart stompPawLeft = this.frontLeft.getChild("lower_leg").getChild("paw");',
    'ModelPart stompPawRight = this.frontRight.getChild("lower_leg").getChild("paw");',
    "stompPawLeft.y = 6.0F;",
    "stompPawRight.y = 6.0F;",
    "stompPawLeft.z = -1.0F;",
    "stompPawRight.z = -1.0F;",
):
    require(token in s, "weighted tail inertia or stationary stomp pose missing: " + token)
require("float gait = Mth.sin(limbSwing * 0.42F)" not in s,
        "must replace the old identical-rigid-pendulum step animation")
require("getChunk(" not in s and "getChunkNow(" not in s,
        "client-only leg animation must not load world chunks")
require(s.count("return LayerDefinition.create(mesh, 256, 256);") == 2,
        "original and glow models must retain distinct 256-pixel UV atlases")
for token in ('leg.addOrReplaceChild("lower_leg"', 'lower.addOrReplaceChild("paw"', 'head.addOrReplaceChild("lower_jaw"',
              "this.crystalCrownLeft.zRot", "this.crystalCrownRight.zRot", "this.lowerJaw.xRot"):
    require(token in s, "keep original leg, jaw and crystal crown rigs: " + token)
for name in ("mutagenkoloss.png", "mutagenkoloss_glow.png"):
    path = ASSETS / "textures/entity" / name
    require(path.is_file(), "missing the Colossus texture " + name)
    with Image.open(path) as image:
        require(image.size == (256, 256), "Colossus textures must retain their 256x256 UV format")
gradle = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.82\.0['\"]", gradle),
        "artifact must be version 1.82.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Aktueller Entwicklungsstand: 1.82.0" in readme and "Version 1.82.0" in readme
        and "Version 1.81.0" in readme, "release history must preserve 1.81 and identify 1.82")
print("1.82 four-phase leg pose, lift/contact cycle, paw compensation, triple-tail inertia, fixed stomp pose and original assets passed.")
