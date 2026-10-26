#!/usr/bin/env python3
"""1.94 independent safety regression for sculpted Minecraft models and new UVs."""
from pathlib import Path
from PIL import Image
import re, sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC = ROOT/"src/main/java/de/sporenwerk/client"
T = ROOT/"src/main/resources/assets/sporenwerk/textures/entity"
def textfile(path):return path.read_text(encoding="utf-8")
def need(ok,why):
    if not ok:raise SystemExit("1.94 model regression: "+why)

stalker = textfile(SRC/"KristallpirscherModel.java")
boss = textfile(SRC/"MutagenkolossModel.java")
renderer = textfile(SRC/"KristallpirscherRenderer.java")
client = textfile(SRC/"ClientModEvents.java")
entity = textfile(ROOT/"src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")

for token in (
    'addOrReplaceChild("dorsal_fin_left"',
    'addOrReplaceChild("dorsal_fin_right"',
    'addOrReplaceChild("jaw_crystal"',
    'addOrReplaceChild("root_socket"',
    "private final ModelPart leftDorsalFin;",
    "private final ModelPart rightDorsalFin;",
    "private final ModelPart jawCrystal;",
    'this.body.getChild("dorsal_fin_left")',
    'this.body.getChild("dorsal_fin_right")',
    'this.head.getChild("jaw_crystal")',
    "this.leftDorsalFin.zRot = -0.52F",
    "this.rightDorsalFin.zRot = 0.42F",
    "this.jawCrystal.xRot = -0.12F",
    "this.leftDorsalFin.zRot -= 0.12F;",
    "this.rightDorsalFin.zRot += 0.18F;",
    "this.jawCrystal.xRot += 0.14F;",
    "float finWave = Mth.sin(ageInTicks * 0.065F - 0.8F)",
    "LayerDefinition.create(mesh, 128, 128)",
    "super.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);",
    'addArmGrowth(leftArm, "crystal_guard", -1.0F);',
    'addArmGrowth(rightArm, "crystal_guard", 1.0F);',
):
    need(token in stalker,"stalker original full model or new moving anatomy missing "+token)
need(stalker.count('addOrReplaceChild("root_socket"')==2,
     "both staggered dorsal crystal fins need sockets")
need("0.16F" in stalker and "entity.isAggressive()" in stalker,
     "hunched movement and combat stance must remain active")
need("KristallpirscherModel.LAYER_LOCATION" in renderer and
     "RenderType.eyes(GLOW)" in renderer and
     "event.registerLayerDefinition(KristallpirscherModel.LAYER_LOCATION" in client,
     "renderer must bake and render custom textured model rather than vanilla zombie")

for token in (
    "private static void addSiegeClawFacets(PartDefinition body, boolean glowing)",
    'body.getChild(legName).getChild("lower_leg").getChild("paw")',
    '"front_left", "front_right", "rear_left", "rear_right"',
    'String clawName = k == 0 ? "claw_left" : k == 1 ? "claw_middle" : "claw_right";',
    'claw.addOrReplaceChild("faceted_tip"',
    "addSiegeClawFacets(body, false);",
    "addSiegeClawFacets(body, true);",
    "PartPose.offset(x, 0.25F, z)",
    "private final ModelPart tailStinger;",
    'head.hasChild("crystal_crown_left")',
    "animateWeightedLeg(this.frontLeft",
    "this.tailMid.xRot += 0.59F;",
):
    need(token in boss,"Colossus real animated claw facets or prior model missing "+token)
need(boss.count("addSiegeClawFacets(body, false);")==1 and
     boss.count("addSiegeClawFacets(body, true);")==1,
     "4x3 claw facets must exist in skin and glow with same parenting")
need(boss.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "Colossus separate two layer return contract broken")
need("getChunk(" not in boss and "getChunk(" not in stalker and
     "setBlock(" not in boss and "destroyBlock(" not in stalker,
     "client geometry must be world-independent and free of chunk operations")

for filename in ("kristallpirscher.png","kristallpirscher_glow.png"):
    tex=T/filename
    with Image.open(tex) as opened: image=opened.convert("RGBA")
    need(image.size==(128,128),filename+" atlas size regression")
    colored=sum(1 for x in range(64,128) for y in range(96,128)
                if image.getpixel((x,y))[3]>0)
    if filename.endswith("_glow.png"):
        need(50<colored<400,"glow UV region must have narrow readable veins, not fullbright sheet")
        need(image.getpixel((70,98))[3]==0,
             "unused violet-black background must be transparent in glow atlas")
    else:
        need(colored==64*32, "skin UV region should be fully opaque")
        need(any((lambda c:c[0]>120 and c[2]>175)(image.getpixel((x,y)))
                 for x in range(96,116) for y in range(100,126)),
             "pixel art must visibly contain magenta-violet geometry")
        need(all(image.getpixel((x,y))[3]==255 for x in range(64) for y in range(64)),
             "previous humanoid texture UVs cannot be deleted")

for token in ("MobEffects.POISON, 80, 0","ModItems.SPORENFILTERMASKE.get()",
              "isOnHighTierSoil()","tickCount % 100 == 0"):
    need(token in entity,"stalker gameplay or counterplay must stay unchanged "+token)
gradle=textfile(ROOT/"build.gradle")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.94\.0['\"]",gradle),"1.94 release version")
readme=textfile(ROOT/"README.md")
need("Aktueller Entwicklungsstand: 1.94.0" in readme and
     "Version 1.94.0" in readme and "Version 1.93.0" in readme,
     "current and previous releases documented")
print("1.94 fully animated asymmetric Stalker anatomy, selective original UVs, twelve boss claw facets in both layers and survival compatibility passed.")
