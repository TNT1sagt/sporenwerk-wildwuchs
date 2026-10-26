#!/usr/bin/env python3
"""Regression 1.92: actual Minecraft Colossus mesh, matching glow bones and PNG UVs."""
from pathlib import Path
import re,sys
from PIL import Image
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
m=(R/"src/main/java/de/sporenwerk/client/MutagenkolossModel.java").read_text(encoding="utf-8")

def need(ok,msg):
    if not ok:raise SystemExit("1.92 Colossus model validation: "+msg)
need(m.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "vanilla 256x256 skin and glow layers required")
for name in ("monolith_left","monolith_right","stinger_bloom",
             "monolith_prism","molten_rune",
             "stinger_prong_left","stinger_prong_right","stinger_prong_top"):
    expected=4 if name in ("monolith_prism","molten_rune") else 2
    need(m.count('addOrReplaceChild("'+name+'"')==expected,
         "skin+glow node missing or mismatched "+name)
for token in (
    "private final ModelPart monolithLeft;",
    "private final ModelPart monolithRight;",
    "private final ModelPart tailStinger;",
    'body.hasChild("monolith_left")',
    'body.hasChild("monolith_right")',
    'tailTip.hasChild("stinger_bloom")',
    "this.tail.xRot += 0.38F;",
    "this.tailMid.xRot += 0.59F;",
    "this.tailTip.xRot += 0.78F;",
    "this.tailStinger.xRot = 0.62F",
    "this.tailStinger.yRot",
    "this.tailStinger.zRot",
    "entity.getAttackState() == MutagenkolossEntity.ATTACK_BREATH",
    "this.monolithLeft.zRot = -0.19F - monolithPulse;",
    "this.monolithRight.zRot = 0.19F + monolithPulse;",
    'tailMid.getChild("tail_tip")',
    "animateWeightedLeg(this.frontLeft",
    "float crownBreathing = Mth.sin",
    "private final ModelPart lowerJaw;",
):
    need(token in m,"bone or combat-state rig missing "+token)
need(m.count("PartPose.offsetAndRotation(0.0F, -0.6F, 20.0F, 0.62F, 0.0F, 0.0F)")==2,
     "stinger skin/glow pivot alignment broken")
need(m.count("PartPose.offsetAndRotation(-17.0F, -7.0F, -9.0F, -0.18F, -0.10F, -0.19F)")==2,
     "left monolith pivot mismatches glow")
need(m.count("PartPose.offsetAndRotation(17.0F, -7.0F, -9.0F, -0.18F, 0.10F, 0.19F)")==2,
     "right monolith pivot mismatches glow")
need("getChunk(" not in m and "getChunkNow(" not in m and
     "destroyBlock(" not in m and "setBlock(" not in m,
     "visual model should never alter world or load chunks")

for filename in ("mutagenkoloss.png","mutagenkoloss_glow.png"):
    p=R/"src/main/resources/assets/sporenwerk/textures/entity"/filename
    with Image.open(p) as im:
        im=im.convert("RGBA")
        need(im.size==(256,256),filename+" wrong Minecraft atlas resolution")
        purples=sum(1 for y in range(228,252) for x in range(210,232)
                    if (lambda c:c[2]>c[1]+50 and c[0]>c[1]+30)(im.getpixel((x,y))))
        need(purples>=50,filename+" missing new crystal purple facets")
        amber=[im.getpixel((x,y)) for x,y in ((239,229),(244,237),(249,245))]
        need(all(p[0]>p[2] and p[0]>p[1] for p in amber),
             filename+" missing amber rune UV region")
        need(all(im.getpixel((x,y))[3]==255 for x,y in ((215,232),(243,233),(251,245))),
             filename+" UV areas must be opaque and visible")
build=(R/"build.gradle").read_text(encoding="utf-8")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.92\.0['\"]",build),"Gradle 1.92 version")
readme=(R/"README.md").read_text(encoding="utf-8")
need("Aktueller Entwicklungsstand: 1.92.0" in readme and
     "Version 1.92.0" in readme and "Version 1.91.0" in readme,
     "release notes and previous version")
print("Sporenwerk 1.92 two-layer actual Colossus model, curled multi-joint tail, crystal stinger and original animated UV palette passed.")
