#!/usr/bin/env python3
"""1.93 Kristallpirscher: actual in-game model, animated crystals, registered layer,
original enlarged Minecraft UV atlas and strictly selective emissive crystal mask."""
from pathlib import Path
from PIL import Image
import re,sys

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC=ROOT/"src/main/java/de/sporenwerk"
TEX=ROOT/"src/main/resources/assets/sporenwerk/textures/entity"

def read(p):return p.read_text(encoding="utf-8")
def need(ok,why):
    if not ok: raise SystemExit("1.93 Kristallpirscher 3D model regression: "+why)
model=read(SRC/"client/KristallpirscherModel.java")
renderer=read(SRC/"client/KristallpirscherRenderer.java")
client=read(SRC/"client/ClientModEvents.java")
entity=read(SRC/"entity/KristallpirscherEntity.java")
for token in (
    "class KristallpirscherModel extends ZombieModel<KristallpirscherEntity>",
    "HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F)",
    'new ResourceLocation(Sporenwerk.MODID, "kristallpirscher_crystal")',
    'PartDefinition body = root.getChild("body");',
    'PartDefinition head = root.getChild("head");',
    'PartDefinition leftArm = root.getChild("left_arm");',
    'PartDefinition rightArm = root.getChild("right_arm");',
    'PartDefinition leftLeg = root.getChild("left_leg");',
    'PartDefinition rightLeg = root.getChild("right_leg");',
    'addOrReplaceChild("back_crest"',
    'addOrReplaceChild("crest_side_shard"',
    'addOrReplaceChild("mineral_chest"',
    'addOrReplaceChild("mineral_spine"',
    'addOrReplaceChild("head_crystal"',
    'addOrReplaceChild("face_mask"',
    'addOrReplaceChild("shin_crystal"',
    'addOrReplaceChild("talon_a"',
    'addOrReplaceChild("talon_b"',
    "addArmGrowth(leftArm",
    "addArmGrowth(rightArm",
    "LayerDefinition.create(mesh, 128, 128)",
    "this.backCrest.xRot = -0.20F + sway;",
    "this.leftShoulder.zRot = -0.12F",
    "this.rightShoulder.zRot = 0.12F",
    "this.headCrystal.xRot = -0.10F",
    "entity.isAggressive()",
    "super.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);"
):
    need(token in model,"model/anatomy animation missing "+token)
for token in (
    "HumanoidMobRenderer<KristallpirscherEntity, KristallpirscherModel>",
    "context.bakeLayer(",
    "KristallpirscherModel.LAYER_LOCATION",
    "this.addLayer(new CrystalGlowLayer(this));",
    'textures/entity/kristallpirscher.png',
    'textures/entity/kristallpirscher_glow.png',
    "RenderType.eyes(GLOW)",
    "OverlayTexture.NO_OVERLAY",
    "0xF000F0",
    "this.getParentModel().renderToBuffer(",
):
    need(token in renderer,"custom renderer missing "+token)
need("ModelLayers.ZOMBIE" not in renderer and "new ZombieModel<>" not in renderer,
     "renderer must no longer use stock zombie mesh")
need("event.registerLayerDefinition(KristallpirscherModel.LAYER_LOCATION, KristallpirscherModel::createBodyLayer);" in client,
     "no baked custom model layer in Forge client registration")
need("KristallpirscherRenderer::new" in client,
     "entity renderer must still be bound to the registered stalker")

for name in ("kristallpirscher.png","kristallpirscher_glow.png"):
    with Image.open(TEX/name) as loaded:
        tex=loaded.convert("RGBA")
    need(tex.size==(128,128),name+" texture atlas must be Minecraft-compatible 128x128")
    if name.endswith("_glow.png"):
        transparent=sum(1 for px in tex.getdata() if px[3]==0)
        colored=sum(1 for px in tex.getdata() if px[3]==255)
        need(transparent>14000 and 200<colored<1400,
             "glow must light only crystal stripes/eyes, not entire zombie body: "+str((transparent,colored)))
        need(tex.getpixel((30,30))[3]==0,
             "unused zombie skin UV must be transparent on fullbright pass")
        need(tex.getpixel((10,10))[3]==255,
             "old cyan eyes must remain visibly emissive")
    else:
        need(all(tex.getpixel((x,y))[3]==255 for y in range(64) for x in range(64)),
             "original 64x64 Zombie UVs must be preserved as opaque")
        need(any(tex.getpixel((x,y))[0]>145 and tex.getpixel((x,y))[2]>175
                 for y in range(2,45) for x in range(96,126)),
             "new purple crystal growth material missing")
        need(any(tex.getpixel((x,y))[1]>190 and tex.getpixel((x,y))[2]>190
                 for y in range(50,95) for x in range(64,127)),
             "cyan glowing fissures missing")

for token in (
    "MobEffects.POISON, 80, 0",
    "ModItems.SPORENFILTERMASKE.get()",
    "tickCount % 100 == 0",
    "isOnHighTierSoil()",
):
    need(token in entity,"do not remove survival counterplay/spawn gameplay: "+token)
need("getChunk(" not in model and "getChunk(" not in renderer,
     "client model must not trigger chunk loads")
build=read(ROOT/"build.gradle")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.93\.0['\"]",build),
     "1.93 artifact version not set")
readme=read(ROOT/"README.md")
need("Aktueller Entwicklungsstand: 1.93.0" in readme and
     "Version 1.93.0" in readme and "Version 1.92.0" in readme,
     "release history and current version must be recorded")
print("1.93 custom Kristallpirscher 3D layer/renderer, animated silhouette, selective emissive atlas, original UVs and all prior combat counterplay passed.")
