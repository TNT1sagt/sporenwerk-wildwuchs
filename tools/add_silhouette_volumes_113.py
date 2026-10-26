#!/usr/bin/env python3
"""Sporenwerk 1.113: physically broken-up armor silhouette + open face.

Minecraft Forge 1.20.1 real Java ModelPart geometry, applied *after* 1.112.
Correct the screenshot's boxy quadruped flanks, zombie-like solid facial
mask, and too-human lower forest horror. No texture transfers or game rules.
"""
from pathlib import Path
from PIL import Image
import re,sys

R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"

def need(ok,reason):
    if not ok: raise SystemExit("1.113 silhouette topology: "+reason)

def rep(file,old,new,why,n=1):
    code=file.read_text(encoding="utf-8")
    need(code.count(old)==n,why+" anchor count "+str(code.count(old))+" expected "+str(n))
    file.write_text(code.replace(old,new,n),encoding="utf-8")

boss=C/"MutagenkolossModel.java"
old=boss.read_text(encoding="utf-8")
need('private static void addPredatorySkullSilhouette(PartDefinition head, boolean glowing)' in old
     and "addPredatorySkullSilhouette(head, false);" in old
     and "addPredatorySkullSilhouette(head, true);" in old
     and "paw.y = 12.0F - lift * 1.65F;" in old
     and 'PartPose.offsetAndRotation(x, y + 10.0F, -24.6F' in old,
     "need 1.112 genuine skull, lowered four legs, recessed iris")
# The old silhouette is a single train-car chest decorated by seven crystals.
# Separate basalt volume that extends OUTWARD from shoulder and haunch.
# These are 4 matte stone shells in the normal model and 4 *empty* bones
# in the matching glow model. Nothing gets fullbright except old veins.
armored_sides="""    /** Front heavy shoulder shields and narrower rear haunch mantles.
     *  Four separate angled stone shapes with genuine gaps at the waist.
     *  Both baked model trees own the same bones for correct rendering.
     */
    private static void addSegmentedBeastMantle(PartDefinition body, boolean glowing) {
        for (int side = -1; side <= 1; side += 2) {
            String direction = side < 0 ? "left" : "right";
            CubeListBuilder front = glowing ? CubeListBuilder.create()
                    : CubeListBuilder.create().texOffs(32, 224)
                            .addBox(-3.1F, -6.5F, -7.0F, 6.2F, 12.0F, 14.0F)
                            .texOffs(80, 224)
                            .addBox(-2.4F, 3.3F, -6.0F, 4.8F, 3.0F, 12.0F);
            body.addOrReplaceChild("boss_mantle_front_" + direction, front,
                    PartPose.offsetAndRotation(side * 17.7F, -2.9F, -14.0F,
                            -0.10F, side * -0.10F, side * 0.27F));
            CubeListBuilder rear = glowing ? CubeListBuilder.create()
                    : CubeListBuilder.create().texOffs(32, 224)
                            .addBox(-2.6F, -4.8F, -5.8F, 5.2F, 9.8F, 11.6F)
                            .texOffs(80, 224)
                            .addBox(-1.8F, 3.0F, -4.0F, 3.6F, 2.7F, 8.0F);
            body.addOrReplaceChild("boss_mantle_rear_" + direction, rear,
                    PartPose.offsetAndRotation(side * 15.0F, -2.4F, 15.0F,
                            0.08F, side * 0.14F, side * 0.34F));
        }
    }

"""
rep(boss,"    public static LayerDefinition createBodyLayer() {",
    armored_sides+"    public static LayerDefinition createBodyLayer() {",
    "create mirrored tiered shoulder and hip armors")
s=boss.read_text(encoding="utf-8")
skin,glow=s.split("    public static LayerDefinition createGlowLayer()",1)
need(skin.count("        addPredatorySkullSilhouette(head, false);")==1
     and glow.count("        addPredatorySkullSilhouette(head, true);")==1,
     "matched existing head builder anchors")
skin=skin.replace("        addPredatorySkullSilhouette(head, false);",
    "        addSegmentedBeastMantle(body, false);\n        addPredatorySkullSilhouette(head, false);",1)
glow=glow.replace("        addPredatorySkullSilhouette(head, true);",
    "        addSegmentedBeastMantle(body, true);\n        addPredatorySkullSilhouette(head, true);",1)
boss.write_text(skin+"    public static LayerDefinition createGlowLayer()"+glow,
                encoding="utf-8")

stalker=C/"KristallpirscherModel.java"
s=stalker.read_text(encoding="utf-8")
need('head.addOrReplaceChild("face_mask"' in s
     and 'head.addOrReplaceChild("head_crystal"' in s
     and "this.leftArm.xRot = 0.24F + quietStride * 0.17F;" in s
     and 'leg.addOrReplaceChild("crystal_hock"' in s,
     "real 1.112 hunter posture and leg hocks required")
# This is an actual hole between cheek plates at x[-1, +1], not a
# differently painted purple square covering the whole face.
rep(stalker,
    "addBox(-3.0F, -1.9F, -4.5F, 6.0F, 4.2F, 1.35F)",
    """addBox(-3.1F, -1.9F, -4.5F, 2.1F, 4.2F, 1.35F)
                        .texOffs(64, 48)
                        .addBox(1.0F, -1.6F, -4.5F, 2.1F, 3.9F, 1.35F)""",
    "split solid zombie mask into two physically separated 3D cheek plates")
# Separate small mandible blades, following the real head articulation
# instead of adding a brightly coloured outline on the PNG.
rep(stalker,"        return LayerDefinition.create(mesh, 128, 128);",
"""        head.addOrReplaceChild("face_mandible_left",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-1.0F, -0.5F, -0.9F, 2.0F, 4.8F, 2.0F),
                PartPose.offsetAndRotation(-2.0F, 1.0F, -4.6F,
                        0.17F, -0.17F, -0.23F));
        head.addOrReplaceChild("face_mandible_right",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-1.0F, -0.5F, -0.9F, 2.0F, 4.8F, 2.0F),
                PartPose.offsetAndRotation(2.0F, 1.0F, -4.6F,
                        0.15F, 0.20F, 0.20F));
        return LayerDefinition.create(mesh, 128, 128);""",
    "two independent angular mandibular prongs on real hunter head")

shade=C/"DaemmerlingModel.java"
src=shade.read_text(encoding="utf-8")
need('body.getChild("rib_root_left").addOrReplaceChild("rib_fork"' in src
     and 'body.getChild("rib_root_right").addOrReplaceChild("rib_fork"' in src
     and 'head.addOrReplaceChild("head_root"' in src
     and 'this.leftRibRoot.zRot' in src,
     "animated open bark-rib skeleton from 1.112 required")
# An empty sternum isn't enough. A creature with most of its anatomy
# in its head still looks like a skinny humanoid. These body-root struts
# branch off its moving rib bones and bend BACK toward the ground.
rep(shade,'        head.addOrReplaceChild("head_root",',
"""        PartDefinition waistRootLeft = body.getChild("rib_root_left")
                .addOrReplaceChild("waist_root_left",
                        CubeListBuilder.create().texOffs(64, 48)
                                .addBox(-0.9F, -0.8F, -1.0F, 1.8F, 9.6F, 2.0F),
                        PartPose.offsetAndRotation(-1.0F, 8.2F, 0.4F,
                                0.29F, -0.18F, -0.51F));
        waistRootLeft.addOrReplaceChild("waist_talon",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-0.6F, 0.0F, -0.7F, 1.2F, 5.2F, 1.4F),
                PartPose.offsetAndRotation(-1.2F, 7.3F, 0.6F,
                        0.34F, 0.12F, -0.48F));
        PartDefinition waistRootRight = body.getChild("rib_root_right")
                .addOrReplaceChild("waist_root_right",
                        CubeListBuilder.create().texOffs(64, 48)
                                .addBox(-0.85F, -0.8F, -1.1F, 1.7F, 8.4F, 2.2F),
                        PartPose.offsetAndRotation(1.0F, 8.2F, -0.4F,
                                0.17F, 0.20F, 0.58F));
        waistRootRight.addOrReplaceChild("waist_talon",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-0.6F, 0.0F, -0.7F, 1.2F, 4.7F, 1.4F),
                PartPose.offsetAndRotation(1.3F, 7.2F, -0.3F,
                        -0.20F, -0.12F, 0.51F));
        head.addOrReplaceChild("head_root",""",
    "forked asymmetric dangling roots from breathing torso, not antlers")

T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for n,d in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(n+suffix+".png")) as im:
            need(im.size==(d,d),"keep Minecraft 128/256 pixel UV atlas "+n+suffix)

# Only roll current-release test metadata. Do NOT suppress feature tests.
for f in (R/"tools").glob("test_*.py"):
    if f.name=="test_silhouette_volumes_113.py": continue
    s=f.read_text(encoding="utf-8")
    t=s.replace("Aktueller Entwicklungsstand: 1.112.0",
                "Aktueller Entwicklungsstand: 1.113.0")
    if "build.gradle" in s:
        t=t.replace(r"1\.112\.0",r"1\.113\.0").replace(
            "artifact must be version 1.112.0","artifact must be version 1.113.0")
    t=t.replace('"Version 1.112.0" in readme and "Version 1.111.0" in readme',
                '"Version 1.113.0" in readme and "Version 1.112.0" in readme')
    if t!=s:f.write_text(t,encoding="utf-8")
gradle=R/"build.gradle";s,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
    "version = '1.113.0'",gradle.read_text(encoding="utf-8"),count=1)
need(n==1,"ForgeGradle version declaration");gradle.write_text(s,encoding="utf-8")
readme=R/"README.md";s=readme.read_text(encoding="utf-8")
s,n=re.subn(r"\*\*Aktueller Entwicklungsstand: 1\.112\.0[^\n]*\*\*",
    "**Aktueller Entwicklungsstand: 1.113.0 — Gestaffelter Vierbeiner-Panzer, echter gespalten maskierter Jäger, asymmetrische Wurzelglieder.**",s,count=1)
need(n==1,"README current heading")
section="""## Aktueller Entwicklungsschritt — 1.113.0

- **Massiver Koloss ohne durchgehende Kasten-Seiten:** Vier große, in X/Y/Z versetzte und in Y/Z angestellte Basaltmantelplatten wachsen aus den vorderen Schultern und den hinteren Hüften. Es bleiben sichtbare Zwischenräume im Taillenbereich. Die beiden Skin-/Glow-Bäume haben die exakt gleichen Modellknochen, aber die dunklen Panzerwürfel sind im Glow-Tree absichtlich leer. Der bestehende Bosskopf, der zurückversetzte Kern, vier bewegliche Blenden, Beine, Stachel und Angriffssysteme bleiben intakt.
- **Kristallpirscher nicht länger mit flacher Zombiemaske:** Die bisherige durchgehende Frontplatte ist jetzt aus zwei echten schmalen Gesichtspanzern mit einer zentralen offenen Lücke gebaut. Zwei nach unten angewinkelte Kieferfortsätze besitzen reale Kopfknochen, keine gemalten Kristallpixel. Jagdklauen, Rückenprismen und die neuen Knöchelgelenke bleiben erhalten.
- **Dämmerling jetzt auch im unteren Körper eine Wurzelkreatur:** An beiden schon atmenden Rippengelenken hängen längere, ungleich große, gebogene Wurzelstränge mit eigener Endverzweigung, statt sämtlicher Silhouette nur aus Kopf-Hörnern entstehen zu lassen. Feldfraß und Nachtverhalten unverändert.
- **Echtes Minecraft, keine fremden Assets:** Forge 1.20.1 mit bestehenden 128/256-Pixelatlanten und tatsächlicher CubeListBuilder-/ModelPart-Hierarchie. Keine Übernahme von Inhalten der Inspirationsmods.
- **Sichtabnahme bleibt offen:** CI kontrolliert geometrische 3D-Lücken und Körperachsen sowie das Kompilieren. Originalgleichheit kann ausschließlich durch neue Ingame-Bilder aus vergleichbaren Perspektiven bewertet werden.

"""
need("## Aktueller Entwicklungsschritt — 1.112.0" in s,"old dev section")
s=s.replace("## Aktueller Entwicklungsschritt — 1.112.0",
            section+"## Aktueller Entwicklungsschritt — 1.112.0",1)
release="""## Version 1.113.0 — Verbundener Basaltmantel und echte offene Gesichtsanatomie

- Vier voneinander getrennte und geneigte Basalt-Mantelpanzer am vierbeinigen Kristallkoloss, ohne zusätzlichen vollleuchtenden Fels.
- Kristallpirscher hat statt durchgehender Würfelmaske zwei getrennte schmale Gesichtsteile und zwei echte Kieferfortsätze.
- Dämmerling trägt asymmetrische knickende lebendige Bauchwurzeln auf den vorhandenen animierten Rippenknochen.
- Alle Gameplaypfade und Kern-/Ganganimationen bleiben erhalten. Exakter Minecraft-Client-Vergleich weiterhin nötig.

"""
need("## Version 1.112.0 —" in s,"old release")
s=s.replace("## Version 1.112.0 —",release+"## Version 1.112.0 —",1)
readme.write_text(s,encoding="utf-8")
print("1.113 applied: twin front/rear matte mantles, open real hunter facial mask, hooked moving lower roots.")
