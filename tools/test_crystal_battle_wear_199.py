#!/usr/bin/env python3
"""1.99 health-driven crystal monster render-only model regression."""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def read(p):return p.read_text(encoding="utf-8")
def need(value,message):
    if not value:raise SystemExit("Sporenwerk 1.99 visual battle phases: "+message)
boss=read(C/"MutagenkolossModel.java")
stalker=read(C/"KristallpirscherModel.java")
renderer=read(C/"KristallpirscherRenderer.java")
for token in (
    "private final ModelPart[] armorFractureVeins;",
    "this.armorFractureVeins = new ModelPart[]",
    'body.getChild("shoulder_armor_left").getChild("fracture_vein")',
    'body.getChild("shoulder_armor_right").getChild("fracture_vein")',
    'body.getChild("haunch_armor_left").getChild("fracture_vein")',
    'body.getChild("haunch_armor_right").getChild("fracture_vein")',
    "private static void addBattleWearVeins(PartDefinition body, boolean glowing)",
    "addBattleWearVeins(body, false);",
    "addBattleWearVeins(body, true);",
    'body.getChild(armor[i]).addOrReplaceChild("fracture_vein", gem,',
    "float hpRatio = entity.getHealth() / Math.max(1.0F, entity.getMaxHealth());",
    "float fracture = Mth.clamp((0.70F - hpRatio) / 0.45F, 0.0F, 1.0F);",
    "this.shoulderArmorLeft.zRot -= fracture * 0.19F",
    "this.shoulderArmorRight.zRot += fracture * 0.19F",
    "this.haunchArmorLeft.zRot -= fracture * 0.12F",
    "this.haunchArmorRight.zRot += fracture * 0.12F",
    "vein.visible = fracture > 0.015F;",
    "vein.xScale = opening;",
    "vein.yScale = 1.0F;",
    "vein.zScale = opening;",
    "private final ModelPart[] coreIrisPetals;",
    "float coreOpening = irisProgress * irisProgress * (3.0F - 2.0F * irisProgress);",
    "private final ModelPart[] resonanceRibs;",
    "this.pawCrystalTips = new ModelPart[12];",
    "this.tailMid.xRot += 0.59F;",
):
    need(token in boss,"boss full crystal wear or legacy model missing "+token)
need(boss.count("addBattleWearVeins(body, false);")==1 and
     boss.count("addBattleWearVeins(body, true);")==1,
     "two baked model layers must contain four fracture seams each")
need(boss.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "both Forge Colossus layers must be 256x256")
need(boss.count('addOrReplaceChild("fracture_vein"')==1,
     "all fractures derived from exactly one shared safe builder")
need("CubeListBuilder.create()" in boss and "glowing ? 0.25F : 0.45F" in boss,
     "thin positive-size geometry for both layers required")
# HP thresholds should be bounded and reversible with no saved markers.
for ratio, lower, upper in ((1.0,0,0),(0.70,0,0.00001),
                            (0.475,0.49,0.51),(0.25,0.99,1),
                            (0.05,0.99,1)):
    effect=max(0.0,min(1.0,(0.70-ratio)/0.45))
    need(lower<=effect<=upper,"health mapped fracture should ease smoothly")
for token in (
    "float stalkerHealth = entity.getHealth() / Math.max(1.0F, entity.getMaxHealth());",
    "float crystalFatigue = Mth.clamp((0.55F - stalkerHealth) / 0.40F, 0.0F, 1.0F);",
    "this.leftLeg.xRot += unevenStep * 0.16F;",
    "this.rightLeg.xRot -= unevenStep * 0.08F;",
    "this.body.zRot = Mth.sin(limbSwing * 0.6662F) * pace * crystalFatigue * 0.055F;",
    "this.headCrystal.zRot = 0.26F + crystalFatigue",
    "this.thoraxResonator.xScale += fatigueBreath;",
    "this.thoraxResonator.yScale += fatigueBreath;",
    "this.thoraxResonator.zScale += fatigueBreath;",
    "float pursuit = entity.isAggressive() ? 1.0F : 0.0F;",
    'addOrReplaceChild("dorsal_fin_left"',
    'addOrReplaceChild("dorsal_fin_right"',
    'resonator.addOrReplaceChild("thorax_shard_left"',
    'resonator.addOrReplaceChild("thorax_shard_right"',
):
    need(token in stalker,"stalker visual fatigue must retain existing creature animation: "+token)
for token in (
    "float healthRatio = entity.getHealth() / Math.max(1.0F, entity.getMaxHealth());",
    "float stress = net.minecraft.util.Mth.clamp((0.55F - healthRatio) / 0.40F, 0.0F, 1.0F);",
    "pulse = Math.min(1.0F, pulse + stress * 0.075F);",
    "RenderType.eyes(GLOW)",
    "this.getParentModel().renderToBuffer",
):
    need(token in renderer,"stalker selective glowing renderer missing "+token)
for path in (C/"MutagenkolossModel.java",C/"KristallpirscherModel.java",C/"KristallpirscherRenderer.java"):
    for forbidden in ("setBlock(", "destroyBlock(", "getChunk(", "getChunkNow(",
                      ".hurt(", "getEntitiesOfClass(", "PacketDistributor",
                      "serverLevel."):
        need(forbidden not in read(path),
             "render-only behavior must never change server/world: "+str(path)+": "+forbidden)
for name,wh in (("mutagenkoloss.png",(256,256)),("mutagenkoloss_glow.png",(256,256)),
                ("kristallpirscher.png",(128,128)),("kristallpirscher_glow.png",(128,128))):
    with Image.open(R/"src/main/resources/assets/sporenwerk/textures/entity"/name) as i:
        need(i.size==wh,"unchanged base UV atlas dimensions: "+name)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.99\.0['\"]",
     read(R/"build.gradle")) is not None,"Gradle 1.99 release")
readme=read(R/"README.md")
need("Aktueller Entwicklungsstand: 1.99.0" in readme and
     "Version 1.99.0" in readme and "Version 1.98.0" in readme,
     "new and prior release documentation")
print("1.99 verified 4 paired skin/glow fracture bones, deterministic HP damage stages, Pirscher render-only fatigue and original atlas dimensions.")
