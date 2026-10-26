#!/usr/bin/env python3
"""1.95: hunt poses, stinger phase synchronization and four-leg crystal rig regression."""
from pathlib import Path
import re,sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=ROOT/"src/main/java/de/sporenwerk/client"
def read(p):return p.read_text(encoding="utf-8")
def need(ok,why):
    if not ok:raise SystemExit("1.95 living crystal regression: "+why)
s=read(C/"KristallpirscherModel.java")
r=read(C/"KristallpirscherRenderer.java")
b=read(C/"MutagenkolossModel.java")
entity=read(ROOT/"src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java")
for x in (
    "private final ModelPart leftTalonA;",
    "private final ModelPart leftTalonB;",
    "private final ModelPart rightTalonA;",
    "private final ModelPart rightTalonB;",
    'this.leftShoulder.getChild("talon_a")',
    'this.leftShoulder.getChild("talon_b")',
    'this.rightShoulder.getChild("talon_a")',
    'this.rightShoulder.getChild("talon_b")',
    "float pursuit = entity.isAggressive() ? 1.0F : 0.0F;",
    "this.body.xRot += pursuit * (0.14F",
    "this.head.xRot -= pursuit * 0.09F;",
    "this.leftArm.xRot = this.leftArm.xRot *",
    "this.rightArm.xRot = this.rightArm.xRot *",
    "this.leftTalonA.xRot = -0.20F",
    "this.leftTalonB.xRot = -0.20F",
    "this.rightTalonA.xRot = -0.20F",
    "this.rightTalonB.xRot = -0.20F",
    "this.leftTalonA.zRot = -0.12F",
    "this.rightTalonB.zRot = 0.13F",
    "this.leftDorsalFin.zRot",
    "this.rightDorsalFin.zRot",
    "this.jawCrystal.xRot",
    'addOrReplaceChild("dorsal_fin_left"',
    'addOrReplaceChild("dorsal_fin_right"',
    'addOrReplaceChild("talon_a"',
    'addOrReplaceChild("talon_b"',
    "super.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);"
):
    need(x in s,"lost or missing stalker model bone/hunt animation: "+x)
for x in (
    "RenderType.eyes(GLOW)",
    "float pulse = 0.76F + 0.12F",
    "net.minecraft.util.Mth.sin(ageInTicks * 0.19F)",
    "if (entity.isAggressive()) pulse = Math.min(1.0F, pulse + 0.12F);",
    "OverlayTexture.NO_OVERLAY, pulse, pulse, pulse, 1.0F",
    "0xF000F0",
):
    need(x in r,"stalker selective glowing veins must use dynamic pulse: "+x)
need("textures/entity/kristallpirscher_glow.png" in r,
     "only glow PNG should be fullbright")
for x in (
    "private final ModelPart[] stingerProngs;",
    "private final ModelPart[] pawCrystalTips;",
    'this.tailStinger.getChild("stinger_prong_left")',
    'this.tailStinger.getChild("stinger_prong_right")',
    'this.tailStinger.getChild("stinger_prong_top")',
    "this.pawCrystalTips = new ModelPart[12];",
    "this.frontLeft, this.frontRight, this.rearLeft, this.rearRight",
    'paw.getChild(claw).getChild("faceted_tip")',
    "int crystalState = entity.getAttackState();",
    "int remaining = Math.max(0, entity.getAttackTicks());",
    "MutagenkolossEntity.ATTACK_BREATH",
    "MutagenkolossEntity.ATTACK_STOMP",
    "MutagenkolossEntity.ATTACK_AWAKENING",
    "Mth.clamp((48.0F - remaining) / 48.0F",
    "Mth.clamp((42.0F - remaining) / 42.0F",
    "Mth.clamp((36.0F - remaining) / 36.0F",
    "this.monolithLeft.zRot -= crystalTension",
    "this.monolithRight.zRot += crystalTension",
    "this.stingerProngs[0].zRot = -0.56F - spread;",
    "this.stingerProngs[1].zRot = 0.56F + spread;",
    "this.stingerProngs[2].xRot = -0.52F - spread * 0.60F;",
    "for (int i = 0; i < this.pawCrystalTips.length; i++)",
    "tip.xScale = glint;",
    "tip.yScale = glint;",
    "tip.zScale = glint;",
    "tip.xRot = -crystalTension * 0.10F;",
    "private final ModelPart tailStinger;",
    "private static void addSiegeClawFacets(PartDefinition body, boolean glowing)",
    "this.tailMid.xRot += 0.59F;",
    "private final ModelPart lowerJaw;",
    "this.crystalCrownLeft.zRot",
    "this.crystalCrownRight.zRot",
):
    need(x in b,"colossus state-dependent real model animation: "+x)
need(b.index('this.tailStinger = this.tailTip.hasChild("stinger_bloom")')<
     b.index('this.stingerProngs = new ModelPart[]'),
     "bind prongs only after existing stinger is initialized")
need(b.count("addSiegeClawFacets(body, false);")==1
     and b.count("addSiegeClawFacets(body, true);")==1
     and b.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "two existing skin/glow skeletons still host actual claw geometry")
for x in ("private static final int STOMP_WINDUP = 42;",
          "private static final int BREATH_WINDUP = 48;",
          "private static final int AWAKENING_WINDUP = 36;"):
    need(x in entity, "rendered phase countdown must match actual combat timing: "+x)
for v in ("getChunk(", "getChunkNow(", "setBlock(", "destroyBlock(", ".hurt("):
    need(v not in b and v not in s and v not in r,
         "client animation must not change gameplay or chunk loading: "+v)
readme=read(ROOT/"README.md")
need("Aktueller Entwicklungsstand: 1.95.0" in readme
     and "Version 1.95.0" in readme
     and "Version 1.94.0" in readme,
     "release history or documentation missing")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.95\.0['\"]",read(ROOT/"build.gradle")) is not None,
     "Gradle version 1.95.0 missing")
print("1.95 crystal motion and selective glow tests: stalker 4 talons, 12 cached boss facets, 3 petals and existing attack state sync passed.")
