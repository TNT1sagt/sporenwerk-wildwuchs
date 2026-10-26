#!/usr/bin/env python3
"""Sporenwerk 1.100.0: independent animated Daemmerling voxel rig and glow berry farm decoy."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
J=R/"src/main/java/de/sporenwerk"
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
def need(ok,reason):
    if not ok:raise SystemExit("1.100 Daemmerling "+reason)
def patch(p,old,new,name):
    s=p.read_text(encoding="utf-8")
    need(s.count(old)==1,name+" source match "+str(s.count(old)))
    p.write_text(s.replace(old,new,1),encoding="utf-8")
model=r"""package de.sporenwerk.client;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.DaemmerlingEntity;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.ZombieModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

/** Root-thin nighttime farm stalker; custom geometry, no extra hitboxes. */
public final class DaemmerlingModel extends ZombieModel<DaemmerlingEntity> {
    public static final ModelLayerLocation LAYER_LOCATION = new ModelLayerLocation(
            new ResourceLocation(Sporenwerk.MODID,"daemmerling_shade"),"main");
    private final ModelPart leftHook,rightHook,leftClaws,rightClaws,headRoot;
    public DaemmerlingModel(ModelPart root) {
        super(root);
        this.leftHook = this.body.getChild("back_hook_left");
        this.rightHook = this.body.getChild("back_hook_right");
        this.leftClaws = this.leftArm.getChild("root_fingers");
        this.rightClaws = this.rightArm.getChild("root_fingers");
        this.headRoot = this.head.getChild("head_root");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh=HumanoidModel.createMesh(CubeDeformation.NONE,0.0F);
        PartDefinition root=mesh.getRoot();
        PartDefinition body=root.getChild("body");
        PartDefinition head=root.getChild("head");
        PartDefinition leftArm=root.getChild("left_arm");
        PartDefinition rightArm=root.getChild("right_arm");
        body.addOrReplaceChild("hollow_chest",
                CubeListBuilder.create().texOffs(64,48)
                        .addBox(-5.2F,-5.0F,-2.6F,10.4F,12.0F,5.2F),
                PartPose.offsetAndRotation(0.0F,-1.0F,0.4F,0.18F,0.0F,0.0F));
        body.addOrReplaceChild("back_hook_left",
                CubeListBuilder.create().texOffs(64,0)
                        .addBox(-2.0F,-10.0F,-1.8F,4.0F,11.0F,3.6F)
                        .texOffs(96,0).addBox(-1.2F,-17.0F,-1.2F,2.4F,7.5F,2.4F),
                PartPose.offsetAndRotation(-4.2F,-3.0F,3.0F,-0.23F,-0.12F,-0.54F));
        body.addOrReplaceChild("back_hook_right",
                CubeListBuilder.create().texOffs(64,0)
                        .addBox(-2.2F,-12.5F,-2.0F,4.4F,13.5F,4.0F)
                        .texOffs(96,0).addBox(-1.2F,-20.0F,-1.2F,2.4F,8.0F,2.4F),
                PartPose.offsetAndRotation(4.2F,-3.0F,3.4F,-0.28F,0.17F,0.44F));
        head.addOrReplaceChild("head_root",
                CubeListBuilder.create().texOffs(96,0)
                        .addBox(-2.1F,-11.0F,-1.7F,4.2F,7.4F,3.4F)
                        .texOffs(64,0).addBox(-1.1F,-16.0F,-1.0F,2.2F,5.7F,2.0F),
                PartPose.offsetAndRotation(2.9F,-4.0F,0.9F,-0.10F,0.12F,0.32F));
        head.addOrReplaceChild("hollow_jaw",
                CubeListBuilder.create().texOffs(96,48)
                        .addBox(-3.8F,0.0F,-4.9F,7.6F,3.8F,2.2F),
                PartPose.ZERO);
        addRootClaws(leftArm,-1.0F);
        addRootClaws(rightArm,1.0F);
        for (PartDefinition leg : new PartDefinition[] {root.getChild("left_leg"),root.getChild("right_leg")}) {
            leg.addOrReplaceChild("bark_shin",
                    CubeListBuilder.create().texOffs(64,48)
                            .addBox(-2.1F,2.0F,-2.8F,4.2F,8.9F,2.4F),PartPose.ZERO);
        }
        return LayerDefinition.create(mesh,128,128);
    }
    private static void addRootClaws(PartDefinition arm,float sign) {
        PartDefinition guard=arm.addOrReplaceChild("root_fingers",
                CubeListBuilder.create().texOffs(64,48)
                        .addBox(-2.3F,0.0F,-1.8F,4.6F,5.6F,3.6F),
                PartPose.offsetAndRotation(sign*0.3F,9.0F,-0.9F,-0.25F,0.0F,sign*0.14F));
        guard.addOrReplaceChild("left_finger",
                CubeListBuilder.create().texOffs(64,0)
                        .addBox(-0.8F,-1.0F,-1.1F,1.6F,7.5F,2.2F),
                PartPose.offsetAndRotation(-1.5F,3.2F,-1.0F,-0.22F,0.0F,-0.12F));
        guard.addOrReplaceChild("right_finger",
                CubeListBuilder.create().texOffs(96,0)
                        .addBox(-0.8F,-1.0F,-1.1F,1.6F,9.0F,2.2F),
                PartPose.offsetAndRotation(1.3F,3.2F,-1.0F,-0.21F,0.0F,0.13F));
    }
    @Override
    public void setupAnim(DaemmerlingEntity entity,float limbSwing,float limbSwingAmount,
                          float ageInTicks,float netHeadYaw,float headPitch) {
        super.setupAnim(entity,limbSwing,limbSwingAmount,ageInTicks,netHeadYaw,headPitch);
        float stride=Mth.clamp(limbSwingAmount,0.0F,1.0F);
        float pulse=Mth.sin(ageInTicks*0.067F);
        this.body.xRot=0.23F+Mth.sin(limbSwing*0.6662F)*stride*0.045F;
        this.head.xRot-=0.17F;
        this.leftHook.zRot=-0.54F+pulse*0.055F;
        this.rightHook.zRot=0.44F-pulse*0.048F;
        this.leftHook.xRot=-0.23F+Mth.sin(limbSwing*0.49F)*stride*0.065F;
        this.rightHook.xRot=-0.28F-Mth.sin(limbSwing*0.49F)*stride*0.075F;
        this.leftClaws.xRot=-0.25F+pulse*0.08F;
        this.rightClaws.xRot=-0.25F-pulse*0.08F;
        this.leftClaws.zRot=-0.14F-stride*0.09F;
        this.rightClaws.zRot=0.14F+stride*0.09F;
        this.headRoot.zRot=0.32F+pulse*0.04F;
        if(entity.isAggressive()) {
            this.body.xRot+=0.12F;
            this.leftClaws.xRot-=0.14F;
            this.rightClaws.xRot-=0.14F;
        }
    }
}
"""
(J/"client/DaemmerlingModel.java").write_text(model,encoding="utf-8")
renderer=J/"client/DaemmerlingRenderer.java"
need("ModelLayers.ZOMBIE" in renderer.read_text(encoding="utf-8"),"old zombie renderer required")
renderer.write_text("""package de.sporenwerk.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.DaemmerlingEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;

public final class DaemmerlingRenderer extends HumanoidMobRenderer<DaemmerlingEntity,DaemmerlingModel> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(Sporenwerk.MODID,"textures/entity/daemmerling.png");
    private static final ResourceLocation GLOW =
            new ResourceLocation(Sporenwerk.MODID,"textures/entity/daemmerling_glow.png");
    public DaemmerlingRenderer(EntityRendererProvider.Context context) {
        super(context,new DaemmerlingModel(context.bakeLayer(
                DaemmerlingModel.LAYER_LOCATION)),0.56F);
        this.addLayer(new EyesLayer(this));
    }
    @Override
    public ResourceLocation getTextureLocation(DaemmerlingEntity entity) { return TEXTURE; }
    private static final class EyesLayer extends RenderLayer<DaemmerlingEntity,DaemmerlingModel> {
        private EyesLayer(DaemmerlingRenderer renderer) { super(renderer); }
        @Override
        public void render(PoseStack pose,MultiBufferSource buffers,int light,
                           DaemmerlingEntity entity,float swing,float swingAmount,
                           float partialTicks,float ageInTicks,float yaw,float pitch) {
            float pulse=0.78F+0.12F*(1.0F+
                    net.minecraft.util.Mth.sin(ageInTicks*0.12F))*0.5F;
            VertexConsumer vc=buffers.getBuffer(RenderType.eyes(GLOW));
            this.getParentModel().renderToBuffer(pose,vc,0xF000F0,
                    OverlayTexture.NO_OVERLAY,pulse,pulse,pulse,1.0F);
        }
    }
}
""",encoding="utf-8")
client=J/"client/ClientModEvents.java"
patch(client,"import de.sporenwerk.client.KristallpirscherModel;",
      "import de.sporenwerk.client.KristallpirscherModel;\nimport de.sporenwerk.client.DaemmerlingModel;",
      "model layer import")
patch(client,"        event.registerLayerDefinition(KristallpirscherModel.LAYER_LOCATION, KristallpirscherModel::createBodyLayer);",
      "        event.registerLayerDefinition(KristallpirscherModel.LAYER_LOCATION, KristallpirscherModel::createBodyLayer);\n"
      "        event.registerLayerDefinition(DaemmerlingModel.LAYER_LOCATION, DaemmerlingModel::createBodyLayer);",
      "register baked shade layer")
old=T/"daemmerling.png"
im=Image.open(old).convert("RGBA")
need(im.size==(64,64),"previous shadow monster skin must use 64x64 UVs")
skin=Image.new("RGBA",(128,128),(28,34,30,255));skin.paste(im,(0,0))
d=ImageDraw.Draw(skin)
d.rectangle((64,0,127,45),fill=(24,50,40,255))
d.rectangle((64,48,127,93),fill=(29,48,38,255))
for x in range(66,124,9):
    d.polygon(((x,42),(x+4,5),(x+7,43)),fill=(40,80,60,255))
    d.line((x+4,12,x+5,35),fill=(114,185,101,255),width=2)
for x in (71,84,99,112):
    d.line((x,54,x+2,65,x-1,77),fill=(119,194,121,255),width=2)
skin.save(old,optimize=True)
glow=Image.new("RGBA",(128,128),(0,0,0,0))
g=ImageDraw.Draw(glow)
for x in (10,14):g.rectangle((x,10,x+1,11),fill=(225,92,126,255))
for x in range(66,124,9):
    g.line((x+4,12,x+5,35),fill=(169,76,119,255),width=2)
for x in (71,84,99,112):
    g.line((x,55,x+2,65,x-1,76),fill=(146,223,129,255),width=1)
glow.save(T/"daemmerling_glow.png",optimize=True)
mob=J/"entity/DaemmerlingEntity.java"
need("private boolean raidingCrops;" in mob.read_text(encoding="utf-8"),
     "existing crop-raid AI required")
patch(mob,
"""        private Player findLanternGuard(BlockPos cropPos) {
            for (Player nearby : mob.level().getEntitiesOfClass(Player.class,""",
"""        private Player findLanternGuard(BlockPos cropPos) {
            Player berryDecoy = null;
            for (Player nearby : mob.level().getEntitiesOfClass(Player.class,""",
"reuse existing single player scan")
patch(mob,
"""                if (nearby.getMainHandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)
                        || nearby.getOffhandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)) {
                    return nearby;
                }
            }
            return null;
        }""",
"""                if (nearby.getMainHandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)
                        || nearby.getOffhandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)) {
                    return nearby;
                }
                if (berryDecoy == null && (nearby.getMainHandItem().is(net.minecraft.world.item.Items.GLOW_BERRIES)
                        || nearby.getOffhandItem().is(net.minecraft.world.item.Items.GLOW_BERRIES))) {
                    berryDecoy = nearby;
                }
            }
            return berryDecoy;
        }""","fallback glowberry lure")
patch(mob,
"""            if (!(mob.level() instanceof ServerLevel level)) return;
            level.sendParticles(ParticleTypes.HAPPY_VILLAGER,
                    cropPos.getX() + 0.5D, cropPos.getY() + 0.75D,""",
"""            if (!(mob.level() instanceof ServerLevel level)) return;
            boolean berryDecoy = !player.getMainHandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)
                    && !player.getOffhandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)
                    && (player.getMainHandItem().is(net.minecraft.world.item.Items.GLOW_BERRIES)
                    || player.getOffhandItem().is(net.minecraft.world.item.Items.GLOW_BERRIES));
            level.sendParticles(berryDecoy ? ParticleTypes.WARPED_SPORE : ParticleTypes.HAPPY_VILLAGER,
                    cropPos.getX() + 0.5D, cropPos.getY() + 0.75D,""",
"distinct crop rescue response")
patch(mob,
"""            level.playSound(null, cropPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, 0.42F, 1.45F);
            long now = level.getGameTime();""",
"""            level.playSound(null, cropPos,
                    berryDecoy ? SoundEvents.AMETHYST_BLOCK_HIT : SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, 0.42F, berryDecoy ? 0.72F : 1.45F);
            long now = level.getGameTime();""","unique crop decoy sound")
patch(mob,
"""            long until = player.getPersistentData().getLong("SporenwerkLanternGuardUntil");
            if (now >= until || until - now > 1200L) {
                player.getPersistentData().putLong("SporenwerkLanternGuardUntil", now + 140L);
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.daemmerling.lantern_rescue"), true);
            }""",
"""            String guardKey = berryDecoy ? "SporenwerkGlowBerryDecoyUntil" : "SporenwerkLanternGuardUntil";
            long until = player.getPersistentData().getLong(guardKey);
            if (now >= until || until - now > 1200L) {
                player.getPersistentData().putLong(guardKey, now + 140L);
                player.displayClientMessage(Component.translatable(
                        berryDecoy ? "message.sporenwerk.daemmerling.berry_decoy"
                                : "message.sporenwerk.daemmerling.lantern_rescue"), true);
            }""","independent player cooldown and message")
patch(mob,
"""            if (player instanceof net.minecraft.server.level.ServerPlayer serverPlayer) {
                var milestone = level.getServer().getAdvancements().getAdvancement(""",
"""            if (!berryDecoy && player instanceof net.minecraft.server.level.ServerPlayer serverPlayer) {
                var milestone = level.getServer().getAdvancements().getAdvancement(""",
"nightwatch advancement belongs to soul lantern only")
# Preserve the old 1.90 night-watch contract: lantern protection remains,
# but the persistent cooldown is now selected from two named guard keys.
legacy=R/"tools/test_daemmerling_nachtwache_190.py"
old_legacy=legacy.read_text(encoding="utf-8")
for exact,new_token in (
    ('getLong("SporenwerkLanternGuardUntil")','getLong(guardKey)'),
    ('putLong("SporenwerkLanternGuardUntil", now + 140L)','putLong(guardKey, now + 140L)'),
):
    need(exact in old_legacy,"1.90 expected old guard cooldown test token missing: "+exact)
    old_legacy=old_legacy.replace(exact,new_token,1)
need('getLong(guardKey)' in old_legacy and 'putLong(guardKey, now + 140L)' in old_legacy,
     "old night-watch regression must still enforce valid guarded cooldown")
legacy.write_text(old_legacy,encoding="utf-8")
for lang,msg in (("de_de.json","Deine Leuchtbeeren lenken den Dämmerling vom Beet ab!"),
                 ("en_us.json","Your glow berries distract the Dämmerling from the crops!")):
    path=R/"src/main/resources/assets/sporenwerk/lang"/lang
    data=json.loads(path.read_text(encoding="utf-8"))
    data["message.sporenwerk.daemmerling.berry_decoy"]=msg
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for path in (R/"tools").glob("test_*.py"):
    if path.name=="test_daemmerling_shadow_100.py":continue
    s=path.read_text(encoding="utf-8")
    n=s.replace("Aktueller Entwicklungsstand: 1.99.0","Aktueller Entwicklungsstand: 1.100.0")
    if "build.gradle" in s:
        n=n.replace(r"1\.99\.0",r"1\.100\.0")
        n=n.replace("artifact must be version 1.99.0","artifact must be version 1.100.0")
    n=n.replace('"Version 1.99.0" in readme and "Version 1.98.0" in readme',
                '"Version 1.100.0" in readme and "Version 1.99.0" in readme')
    if n!=s:path.write_text(n,encoding="utf-8")
p=R/"build.gradle"
s,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.100.0'",p.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle version bump")
p.write_text(s,encoding="utf-8")
p=R/"README.md";s=p.read_text(encoding="utf-8")
h="**Aktueller Entwicklungsstand: 1.99.0 — Sichtbare Kristall-Kampfspuren und lebendige Monsterphasen.**"
need(h in s,"1.99 generated readme header missing")
s=s.replace(h,"**Aktueller Entwicklungsstand: 1.100.0 — Eigene Schattenkreatur und Feld-Lockköder.**",1)
step="""## Aktueller Entwicklungsschritt — 1.100.0

- Der Dämmerling hat einen eigenen Forge-ModelLayer und 128x128-Pixelatlas statt des generischen Zombie-Renderers. Zwei unterschiedlich geformte Rückenwurzeln, langgliedrige Krallen, krumme Kopfkrone und mineralisierte Schienen ändern seine echte 3D-Silhouette.
- Ein separates transparentes Glow-Atlas lässt nur schmale Wurzeladern und rote Augen unheimlich leuchten, nicht den gesamten Körper.
- Zwei Schulterhaken und Wurzelfinger bewegen sich im normalen Laufen unterschiedlich schnell. Aggressive Tiere verformen zusätzlich ihren Oberkörper. Die normale Dämmerling-KI, seine schwachen Schadenswerte und Nachterscheinungen bleiben.
- Bei einer echten laufenden Feldattacke können in der Nähe gehaltene Leuchtbeeren den Dämmerling kurz ablenken und eine Ernte retten. Das vorhandene 5-Tick-Wachsignal verwendet nur EINEN Player-Scan. Seelenlaternen haben Priorität und sind weiterhin für den Nachtwache-Fortschritt notwendig.
- Ein eigener Sporenimpuls und Amethystgeräusch unterscheiden die Köder-Ablenkung; Köder wird nicht konsumiert und es gibt keinen neuen Server-Ticker.
- Tests: Modellbake, Skin/Glow-Atlanten, schmale Partikeltextur, Crop-Goal-Schutz, Priorität und Cooldown, DE/EN-Texte, Forge-Build, JAR sowie Dedicated Server.

"""
need("## Aktueller Entwicklungsschritt — 1.99.0" in s,"old step absent")
s=s.replace("## Aktueller Entwicklungsschritt — 1.99.0",step+"## Aktueller Entwicklungsschritt — 1.99.0",1)
rel="""## Version 1.100.0 — Dämmerling-Schattenanatomie und Leuchtbeeren-Rettung

- Individuelles, animiertes Minecraft-Monstermodell mit rückenständigen Wurzelhaken, Klauen, Kopfkrone und selektivem roten/grünen Schimmer.
- Alternativer, ungefährlicher Glow-Berry-Lockköder gegen laufenden Feldfraß; Seelenlaterne bleibt bevorzugter Schutz und belohnungsrelevante Abwehr.
- Kein neuer Blockscanner oder zusätzlicher Server-Ticker, keine Änderungen an Infektionsheilung, Bosskampf, Spielerwerten oder geschützten Beeten.
- Minecraft-Client-Sichttest vor endgültiger visueller Abnahme erforderlich.

"""
need("## Version 1.99.0 —" in s,"previous release history absent")
s=s.replace("## Version 1.99.0 —",rel+"## Version 1.99.0 —",1)
p.write_text(s,encoding="utf-8")
print("1.100.0 Dämmerling custom rig, selective glow and fallback berry decoy integrated.")
