#!/usr/bin/env python3
"""1.100 Dämmerling original voxel rig, glow pixels, one-scan crop decoy safety."""
from pathlib import Path
from PIL import Image
import json,re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
J=R/"src/main/java/de/sporenwerk"
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
def load(p):return p.read_text(encoding="utf-8")
def need(ok,msg):
    if not ok:raise SystemExit("1.100 Dämmerling full mod regression: "+msg)
model=load(J/"client/DaemmerlingModel.java")
renderer=load(J/"client/DaemmerlingRenderer.java")
client=load(J/"client/ClientModEvents.java")
mob=load(J/"entity/DaemmerlingEntity.java")
for key in (
    "class DaemmerlingModel extends ZombieModel<DaemmerlingEntity>",
    "HumanoidModel.createMesh(CubeDeformation.NONE,0.0F)",
    'new ResourceLocation(Sporenwerk.MODID,"daemmerling_shade")',
    "PartDefinition body=root.getChild",
    'addOrReplaceChild("hollow_chest"',
    'addOrReplaceChild("back_hook_left"',
    'addOrReplaceChild("back_hook_right"',
    'addOrReplaceChild("head_root"',
    'addOrReplaceChild("hollow_jaw"',
    'addOrReplaceChild("root_fingers"',
    'addOrReplaceChild("left_finger"',
    'addOrReplaceChild("right_finger"',
    'addOrReplaceChild("bark_shin"',
    "this.leftHook.zRot=-0.54F",
    "this.rightHook.zRot=0.44F",
    "this.leftClaws.xRot=-0.25F",
    "this.rightClaws.xRot=-0.25F",
    "this.headRoot.zRot=0.32F",
    "if(entity.isAggressive())",
    "super.setupAnim(entity,limbSwing,limbSwingAmount,ageInTicks,netHeadYaw,headPitch)",
    "LayerDefinition.create(mesh,128,128)",
):
    need(key in model,"real client silhouette or animation missing "+key)
for key in (
    "HumanoidMobRenderer<DaemmerlingEntity,DaemmerlingModel>",
    "context.bakeLayer(",
    "DaemmerlingModel.LAYER_LOCATION",
    "RenderType.eyes(GLOW)",
    "textures/entity/daemmerling_glow.png",
    "textures/entity/daemmerling.png",
    "this.getParentModel().renderToBuffer",
):
    need(key in renderer,"custom renderer or selective glow absent "+key)
need("ModelLayers.ZOMBIE" not in renderer and "new ZombieModel<>" not in renderer,
     "stock zombie mesh must not be used")
need("event.registerLayerDefinition(DaemmerlingModel.LAYER_LOCATION, DaemmerlingModel::createBodyLayer);" in client,
     "custom baked model layer not on Forge mod event bus")
need("DaemmerlingRenderer::new" in client,"existing entity renderer binding lost")
for name in ("daemmerling.png","daemmerling_glow.png"):
    with Image.open(T/name) as im: tex=im.convert("RGBA")
    need(tex.size==(128,128),name+" must use enlarged Minecraft UV atlas")
    if name.endswith("_glow.png"):
        colored=sum(1 for px in tex.getdata() if px[3])
        need(80<colored<850,"glow must be narrowly selective, not fullbright body "+str(colored))
        need(tex.getpixel((30,30))[3]==0,"dark body must remain dark")
        need(tex.getpixel((11,10))[3]==255,"red eyes missing")
    else:
        need(all(tex.getpixel((x,y))[3]==255 for x in range(64) for y in range(64)),
             "old 64x64 original skin UV must remain opaque")
        need(any(tex.getpixel((x,y))[1]>115 for x in range(66,127) for y in range(3,45)),
             "original pixel-color root veins missing")
crop=mob[mob.index("private static final class CropThreatGoal extends Goal"):]
for key in (
    "if (chewTicks % 5 == 0)",
    "Player guard = findLanternGuard(target);",
    "repelFromLantern(guard, target);",
    "Player berryDecoy = null;",
    "Items.GLOW_BERRIES",
    "Items.SOUL_LANTERN",
    "return berryDecoy;",
    "berryDecoy ? ParticleTypes.WARPED_SPORE : ParticleTypes.HAPPY_VILLAGER",
    "berryDecoy ? SoundEvents.AMETHYST_BLOCK_HIT : SoundEvents.AMETHYST_BLOCK_CHIME",
    "SporenwerkGlowBerryDecoyUntil",
    "SporenwerkLanternGuardUntil",
    "message.sporenwerk.daemmerling.berry_decoy",
    "message.sporenwerk.daemmerling.lantern_rescue",
    "if (!berryDecoy && player instanceof net.minecraft.server.level.ServerPlayer serverPlayer)",
    "if (++chewTicks >= 30)",
    "mob.level().hasChunkAt(target)",
    "isMatureCrop(target) && !isProtected(target)",
    "mob.level().destroyBlock(target, false, mob);",
    "mob.raidingCrops = false;",
):
    need(key in crop,"safe decoy or existing raid protection missing "+key)
need(crop.count("getEntitiesOfClass(")==2,"reuse lantern scan and existing player-warning scan only")
need(crop.index("Items.SOUL_LANTERN")<crop.index("Items.GLOW_BERRIES"),
     "lantern must win when competing with glowberry lure")
need(crop.index("repelFromLantern(guard, target)")<crop.index("mob.level().destroyBlock(target, false, mob);"),
     "decoy must prevent crop destruction before bite")
for key in ("private static final class WatchedStillnessGoal extends Goal",
            "this.goalSelector.addGoal(5, new CropThreatGoal(this))",
            "FilterMossSymbiosis.protects(mob.level(), cropPos)"):
    need(key in mob,"gaze + FilterMoss protection retained "+key)
for lang in ("de_de.json","en_us.json"):
    strings=json.loads(load(R/"src/main/resources/assets/sporenwerk/lang"/lang))
    need("message.sporenwerk.daemmerling.berry_decoy" in strings
         and "message.sporenwerk.daemmerling.lantern_rescue" in strings,
         "localized berry+lantern help missing: "+lang)
for p in (J/"client/DaemmerlingModel.java",J/"client/DaemmerlingRenderer.java"):
    for forbidden in ("getChunk(","setBlock(","destroyBlock(",".hurt(","getEntitiesOfClass("):
        need(forbidden not in load(p),"client renderer must not touch server/world: "+forbidden)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.100\.0['\"]",
               load(R/"build.gradle")) is not None,"Gradle version")
r=load(R/"README.md")
need("Aktueller Entwicklungsstand: 1.100.0" in r and
     "Version 1.100.0" in r and "Version 1.99.0" in r,
     "README release history")
print("1.100: custom shadow creature layer, textured/transparent eyes, one-scanned glowberry lure with soul-lantern priority, mature-crop protection and old KI passed.")
