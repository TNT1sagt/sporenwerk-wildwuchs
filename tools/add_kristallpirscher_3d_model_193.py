#!/usr/bin/env python3
"""Sporenwerk 1.93: replace the Kristallpirscher's stock Zombie model with
custom, animated voxel ModelParts, and a selective cyan/violet emissive overlay.

Original pixel atlases only; never import copyrighted reference-mod resources.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import re, sys

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC=ROOT/"src/main/java/de/sporenwerk"
TEX=ROOT/"src/main/resources/assets/sporenwerk/textures/entity"

def need(ok, msg):
    if not ok: raise SystemExit("1.93 Kristallpirscher renderer: "+msg)

def change(path, before, after, name):
    s=path.read_text(encoding="utf-8")
    if after in s:return
    need(s.count(before)==1,name+" anchor count "+str(s.count(before)))
    path.write_text(s.replace(before,after,1),encoding="utf-8")

model=r"""
package de.sporenwerk.client;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.KristallpirscherEntity;
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

/**
 * Custom 128x128 voxel creature model built on top of the proven vanilla
 * humanoid animation rig. This is not a retextured ZombieModel: independent,
 * animated growths change the stalker's silhouette from every viewing angle.
 */
public final class KristallpirscherModel extends ZombieModel<KristallpirscherEntity> {
    public static final ModelLayerLocation LAYER_LOCATION = new ModelLayerLocation(
            new ResourceLocation(Sporenwerk.MODID, "kristallpirscher_crystal"), "main");

    private final ModelPart backCrest;
    private final ModelPart leftShoulder;
    private final ModelPart rightShoulder;
    private final ModelPart headCrystal;

    public KristallpirscherModel(ModelPart root) {
        super(root);
        this.backCrest = this.body.getChild("back_crest");
        this.leftShoulder = this.leftArm().getChild("crystal_guard");
        this.rightShoulder = this.rightArm().getChild("crystal_guard");
        this.headCrystal = this.head.getChild("head_crystal");
    }

    // Parent ZombieModel uses public HumanoidModel limbs. Keep helper methods
    // separate from field names so Forge versions with inherited field members work.
    private ModelPart leftArm() { return this.leftArm; }
    private ModelPart rightArm() { return this.rightArm; }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F);
        PartDefinition root = mesh.getRoot();
        PartDefinition body = root.getChild("body");
        PartDefinition head = root.getChild("head");
        PartDefinition leftArm = root.getChild("left_arm");
        PartDefinition rightArm = root.getChild("right_arm");
        PartDefinition leftLeg = root.getChild("left_leg");
        PartDefinition rightLeg = root.getChild("right_leg");

        // Hunched crystalline backpack: two perpendicular crystal pillars and
        // a plate row create the asymmetric reference silhouette.
        PartDefinition crest = body.addOrReplaceChild("back_crest",
                CubeListBuilder.create().texOffs(64, 0)
                        .addBox(-5.0F, -15.0F, 1.5F, 10.0F, 17.0F, 5.0F)
                        .texOffs(96, 0)
                        .addBox(-4.0F, -21.0F, 2.0F, 8.0F, 7.0F, 4.0F),
                PartPose.offsetAndRotation(1.5F, -2.0F, 1.0F, -0.20F, 0.12F, -0.16F));
        crest.addOrReplaceChild("crest_side_shard",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-2.8F, -11.0F, -2.8F, 5.6F, 13.0F, 5.6F)
                        .texOffs(64, 0).addBox(-1.8F, -18.0F, -1.8F, 3.6F, 7.0F, 3.6F),
                PartPose.offsetAndRotation(6.0F, -7.0F, 2.0F, -0.15F, 0.08F, 0.40F));
        body.addOrReplaceChild("mineral_chest",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-5.3F, -6.0F, -3.0F, 10.6F, 11.0F, 2.4F)
                        .texOffs(96, 48).addBox(-1.8F, -3.5F, -4.0F, 3.6F, 6.0F, 1.5F),
                PartPose.ZERO);
        body.addOrReplaceChild("mineral_spine",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-4.5F, -5.5F, 2.0F, 9.0F, 12.0F, 2.5F),
                PartPose.ZERO);

        // Asymmetric mask and crystalline horns: far removed from stock zombie.
        head.addOrReplaceChild("head_crystal",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-3.2F, -10.2F, -1.0F, 5.6F, 6.3F, 5.0F)
                        .texOffs(112, 0).addBox(-2.0F, -15.0F, 0.0F, 3.5F, 5.5F, 3.3F),
                PartPose.offsetAndRotation(3.6F, -3.5F, 0.5F, -0.10F, 0.0F, 0.26F));
        head.addOrReplaceChild("face_mask",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-4.2F, -1.8F, -4.9F, 8.4F, 5.0F, 1.5F),
                PartPose.ZERO);

        // Angular mineral pauldrons and long cyan talons, following arm bones.
        addArmGrowth(leftArm, "crystal_guard", -1.0F);
        addArmGrowth(rightArm, "crystal_guard", 1.0F);
        for (PartDefinition leg : new PartDefinition[] { leftLeg, rightLeg }) {
            leg.addOrReplaceChild("shin_crystal",
                    CubeListBuilder.create().texOffs(96, 48)
                            .addBox(-2.0F, 1.0F, -2.9F, 4.0F, 9.0F, 1.5F),
                    PartPose.ZERO);
        }
        return LayerDefinition.create(mesh, 128, 128);
    }

    private static void addArmGrowth(PartDefinition arm, String name, float sign) {
        PartDefinition growth = arm.addOrReplaceChild(name,
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-3.8F, -4.0F, -2.8F, 7.6F, 10.0F, 6.2F)
                        .texOffs(96, 48).addBox(-2.5F, 3.0F, -3.6F, 5.0F, 8.0F, 3.0F),
                PartPose.offsetAndRotation(sign * 0.65F, 2.0F, -0.8F,
                        -0.16F, 0.0F, sign * 0.12F));
        growth.addOrReplaceChild("talon_a",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-1.0F, 0.0F, -1.5F, 2.0F, 8.5F, 3.0F),
                PartPose.offsetAndRotation(-2.4F, 9.0F, -1.0F,
                        -0.20F, 0.0F, -0.12F));
        growth.addOrReplaceChild("talon_b",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-1.0F, 0.0F, -1.5F, 2.0F, 10.5F, 3.0F),
                PartPose.offsetAndRotation(2.1F, 8.5F, -1.0F,
                        -0.20F, 0.0F, 0.13F));
    }

    @Override
    public void setupAnim(KristallpirscherEntity entity, float limbSwing,
                          float limbSwingAmount, float ageInTicks,
                          float netHeadYaw, float headPitch) {
        super.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);
        // A permanently hunched silhouette with delayed shoulder and crest motion.
        float pace = Mth.clamp(limbSwingAmount, 0.0F, 1.0F);
        this.body.xRot = 0.16F + Mth.sin(limbSwing * 0.56F) * pace * 0.055F;
        this.head.xRot -= 0.10F;
        float sway = Mth.sin(ageInTicks * 0.073F) * 0.06F;
        this.backCrest.xRot = -0.20F + sway;
        this.backCrest.zRot = -0.16F + Mth.sin(limbSwing * 0.56F) * pace * 0.08F;
        this.leftShoulder.zRot = -0.12F + sway * 0.55F;
        this.rightShoulder.zRot = 0.12F - sway * 0.55F;
        this.headCrystal.xRot = -0.10F + Mth.sin(ageInTicks * 0.10F) * 0.06F;
        if (entity.isAggressive()) {
            this.backCrest.xRot -= 0.18F;
            this.leftShoulder.xRot = -0.24F;
            this.rightShoulder.xRot = -0.24F;
        } else {
            this.leftShoulder.xRot = -0.16F;
            this.rightShoulder.xRot = -0.16F;
        }
    }
}
""".lstrip()
model_path=SRC/"client/KristallpirscherModel.java"
model_path.write_text(model,encoding="utf-8")
renderer=SRC/"client/KristallpirscherRenderer.java"
old_renderer=renderer.read_text(encoding="utf-8")
need("new ZombieModel<>(context.bakeLayer(ModelLayers.ZOMBIE))" in old_renderer,
     "vanilla ZombieModel renderer must still be in use")

renderer.write_text("""package de.sporenwerk.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.KristallpirscherEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;

public final class KristallpirscherRenderer extends HumanoidMobRenderer<KristallpirscherEntity, KristallpirscherModel> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(Sporenwerk.MODID, "textures/entity/kristallpirscher.png");
    private static final ResourceLocation GLOW =
            new ResourceLocation(Sporenwerk.MODID, "textures/entity/kristallpirscher_glow.png");

    public KristallpirscherRenderer(EntityRendererProvider.Context context) {
        super(context, new KristallpirscherModel(context.bakeLayer(
                KristallpirscherModel.LAYER_LOCATION)), 0.65F);
        this.addLayer(new CrystalGlowLayer(this));
    }

    @Override
    public ResourceLocation getTextureLocation(KristallpirscherEntity entity) {
        return TEXTURE;
    }

    // Transparent pixels in the glow atlas ensure that only the creature's
    // crystalline fissures and prongs glow, not the whole dark stone body.
    private static final class CrystalGlowLayer extends RenderLayer<KristallpirscherEntity, KristallpirscherModel> {
        private CrystalGlowLayer(KristallpirscherRenderer renderer) {
            super(renderer);
        }

        @Override
        public void render(PoseStack poseStack, MultiBufferSource buffer, int packedLight,
                           KristallpirscherEntity entity, float limbSwing, float limbSwingAmount,
                           float partialTick, float ageInTicks, float netHeadYaw, float headPitch) {
            VertexConsumer vertex = buffer.getBuffer(RenderType.eyes(GLOW));
            this.getParentModel().renderToBuffer(poseStack, vertex, 0xF000F0,
                    OverlayTexture.NO_OVERLAY, 1.0F, 1.0F, 1.0F, 1.0F);
        }
    }
}
""",encoding="utf-8")

client_path=SRC/"client/ClientModEvents.java"
change(client_path,"import de.sporenwerk.client.KristallpirscherRenderer;",
       "import de.sporenwerk.client.KristallpirscherRenderer;\nimport de.sporenwerk.client.KristallpirscherModel;",
       "client model import")
change(client_path,"        event.registerLayerDefinition(MutagenkolossModel.GLOW_LAYER_LOCATION, MutagenkolossModel::createGlowLayer);",
       "        event.registerLayerDefinition(MutagenkolossModel.GLOW_LAYER_LOCATION, MutagenkolossModel::createGlowLayer);\n        event.registerLayerDefinition(KristallpirscherModel.LAYER_LOCATION, KristallpirscherModel::createBodyLayer);",
       "register custom crystal stalker model")

# Keep the old 64x64 vanilla UV exactly intact in the upper left. This retains
# the original painted eyes / torso while providing 128x128 crystal islands.
orig=TEX/"kristallpirscher.png"
im=Image.open(orig).convert("RGBA")
need(im.size==(64,64),"expected original 64x64 UV atlas")
base=Image.new("RGBA",(128,128),(28,42,49,255))
base.paste(im,(0,0))
d=ImageDraw.Draw(base)
# These are UV islands used by the NEW ModelPart cubes, not just ornaments.
for box in ((64,0,95,47),(96,0,127,47),(64,48,95,93),(96,48,127,93)):
    d.rectangle(box,fill=(19,29,43,255))
# Sharp dark armor ribs and teal-malachite vein lines.
for yy in range(49,94,8):
    d.polygon(((64,yy),(91,yy+2),(85,yy+5),(64,yy+7)),
              fill=(30,56+yy//3,75,255))
    d.line(((68,yy+2),(78,yy+4),(88,yy+3)),fill=(30,165,187,255),width=2)
for yy in range(51,94,11):
    d.line(((98,yy+2),(105,yy+5),(115,yy+1),(125,yy+4)),fill=(13,211,234,255),width=2)
for x in range(65,94,6):
    d.polygon(((x,42),(x+3,6),(x+5,42)),fill=(20,108,135,255))
    d.line(((x+3,12),(x+4,37)),fill=(32,224,234,255),width=1)
for x in range(96,125,7):
    d.polygon(((x,44),(x+3,3),(x+6,44)),fill=(64,26,121,255))
    d.line(((x+3,8),(x+4,34)),fill=(197,61,251,255),width=2)
# One bright shard face and asymmetric emerald mineral crack.
d.polygon(((99,10),(104,3),(108,15),(103,29)),fill=(177,61,239,255))
d.line(((76,52),(82,62),(76,73),(89,89)),fill=(24,231,237,255),width=2)
base.save(orig,optimize=True)
glow=Image.new("RGBA",(128,128),(0,0,0,0))
g=ImageDraw.Draw(glow)
# Original eyes stay visible in darkness, independent of local lighting.
for x in (9,13):
    g.rectangle((x,10,x+1,11),fill=(57,253,249,255))
for x in range(65,94,6):
    g.line(((x+3,13),(x+4,37)),fill=(57,252,253,255),width=2)
for x in range(96,125,7):
    g.line(((x+3,9),(x+4,35)),fill=(244,105,255,255),width=2)
for y in range(49,94,8):
    g.line(((68,y+2),(78,y+4),(88,y+3)),fill=(36,238,250,255),width=1)
for y in range(51,94,11):
    g.line(((98,y+2),(105,y+5),(115,y+1),(125,y+4)),fill=(30,248,251,255),width=2)
glow.save(TEX/"kristallpirscher_glow.png",optimize=True)

# Keep the historical behavioral test, but reflect this intentional atlas
# upgrade: original 64x64 remains opaque with unchanged vanilla body UV.
old_test=ROOT/"tools/test_kristallpirscher.py"
before=old_test.read_text(encoding="utf-8")
for old,new in (
    ('require(texture.size == (64, 64), "entity skin must use the standard 64x64 humanoid UV")',
     'require(texture.size == (128, 128), "entity skin must preserve 64x64 zombie UV and include new 128x128 crystal islands")'),
    ('require(all(px[3] == 255 for px in texture.getdata()), "entity skin must be fully opaque")',
     'require(all(texture.getpixel((x,y))[3] == 255 for y in range(64) for x in range(64)), "original zombie skin UV must remain opaque")')
):
    need(old in before,"original historical regression missing "+old)
    before=before.replace(old,new,1)
old_test.write_text(before,encoding="utf-8")

# All old 1.38+ features are unchanged. Advance ONLY rolling release assertions.
for p in (ROOT/"tools").glob("test_*.py"):
    if p.name=="test_kristallpirscher_3d_model_193.py":continue
    old=p.read_text(encoding="utf-8")
    new=old.replace("Aktueller Entwicklungsstand: 1.92.0",
                    "Aktueller Entwicklungsstand: 1.93.0")
    if "build.gradle" in old:
        new=new.replace(r"1\.92\.0",r"1\.93\.0")
        new=new.replace("artifact must be version 1.92.0",
                        "artifact must be version 1.93.0")
    new=new.replace('"Version 1.92.0" in readme and "Version 1.91.0" in readme',
                    '"Version 1.93.0" in readme and "Version 1.92.0" in readme')
    if new!=old: p.write_text(new,encoding="utf-8")
p=ROOT/"build.gradle"
gradle,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                "version = '1.93.0'",p.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle version bump")
p.write_text(gradle,encoding="utf-8")
p=ROOT/"README.md"
readme=p.read_text(encoding="utf-8")
head="**Aktueller Entwicklungsstand: 1.92.0 — neue Kristallkoloss-Geometrie und Texturen im Spiel.**"
need(head in readme,"generated 1.92 README release headline missing")
readme=readme.replace(head,
    "**Aktueller Entwicklungsstand: 1.93.0 — Kristallpirscher erhält ein eigenes animiertes 3D-Modell.**",1)
current="""## Aktueller Entwicklungsschritt — 1.93.0

- **Eigenes Kristallpirscher-Modell:** Keine bloße Zombie-Textur mehr. Eigenes Forge-Modell mit ungleichen Wucherungen, breiterem Rückenpanzer, Kristallkrone, mineralischer Gesichtspartie, Brustpanzer und langen doppelseitigen Klauen.
- **Animierte Organe:** Der von der dritten Kreaturenvorlage inspirierte Kristallpanzer lehnt sich mit dem Kopf vor und schwingt beim Gehen; Armkristalle und Rückenwucherungen reagieren zusätzlich auf aggressive Kampfhaltung. Die bewährte Humanoid-Laufanimation bleibt funktional.
- **Selektives Leuchten:** Neues 128x128-Minecraft-Texturatlas und separate transparente Glow-PNG: cyanfarbene Risse und Augen sowie violette Kristallstreifen leuchten, dunkler Stein dagegen nicht.
- **Richtige Forge-Einbindung:** Neu gebackener ModelLayer wird im Client registriert und vom Kristallpirscher-Renderer statt ModelLayers.ZOMBIE verwendet. Es werden echte Game-ModelParts gerendert.
- **Gameplay erhalten:** Tier-III-Feld-Spawns, Sporenfiltermaske, Jagd-KI, Schaden, Beute und Fortschritte werden nicht verändert.
- **Qualität:** Eigener Regressionstest für Modellbaum, Emissiv-Maske, Materialtransparenz und registrierte Layer. Forge-JAR und Dedicated-Server-Test bleiben verpflichtend.

"""
need("## Aktueller Entwicklungsschritt — 1.92.0" in readme,
     "old current step missing")
readme=readme.replace("## Aktueller Entwicklungsschritt — 1.92.0",
                      current+"## Aktueller Entwicklungsschritt — 1.92.0",1)
release="""## Version 1.93.0 — Der Kristallpirscher bekommt einen Körper

- Eigenes animiertes Minecraft-3D-Modell mit kristallinen Schulterknochen, Rückenkamm, markantem Kopf, verlängerten mineralischen Klauen und 128x128-Pixeltextur.
- Neues selektives Cyan-/Violett-Glühen statt flächiger Belichtung; originale Zombie-UV-Flächen werden vom bisherigen Sporenwerk-Look übernommen.
- Spawn-Bedingungen, Filtermaske, Drops, Bosskampf und bestehende Mutagenmechaniken unverändert. Sicht- und Funktionsprüfung im Minecraft-Client nach technischem Build notwendig.

"""
need("## Version 1.92.0 —" in readme,"prior release notes missing")
readme=readme.replace("## Version 1.92.0 —",release+"## Version 1.92.0 —",1)
p.write_text(readme,encoding="utf-8")
print("1.93 Kristallpirscher real original custom model, 128x128 voxel skin, selective cyan/violet glow, layered renderer and compatibility installed.")
