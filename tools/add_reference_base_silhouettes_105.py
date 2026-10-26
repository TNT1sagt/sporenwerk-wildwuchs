#!/usr/bin/env python3
"""Sporenwerk 1.105: reference SILHOUETTE correction in actual Forge mesh source.

Replace stock zombie primitive bones under the original custom growths on
both crystalline stalker and farm-horror Dämmerling. Make body ribs separated,
head narrower, limbs longer/slimmer, and avoid a painted solid fake 'hollow'
chest. Reduce the Colossus oversized muzzle to a smaller, visually distinct
rock snout without affecting parent pivots / combat. Keep old authored pixel
skin and selective glow, and no copied model assets from other mods.

These are real model-space voxel edits, not promotional concept art.
"""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(v,m):
    if not v:raise SystemExit("1.105 reference silhouette: "+m)
def patch(f,a,b,label):
    s=f.read_text(encoding="utf-8")
    need(s.count(a)==1,label+" expected exactly one anchor, got "+str(s.count(a)))
    f.write_text(s.replace(a,b,1),encoding="utf-8")

# Explicit Minecraft pixel bone dimensions. Keep existing humanoid pivot
# names/poses: zombie locomotion, look controls and child growth hierarchies
# cannot regress. Blank the stock helmet and replace with a smaller faceted
# head and ribbed chest rather than painting pixels onto a full zombie torso.
P=C/"KristallpirscherModel.java"
p=P.read_text(encoding="utf-8")
need('body.addOrReplaceChild("mineral_chest"' in p and
     'head.addOrReplaceChild("jaw_crystal"' in p and
     'this.thoraxResonator = this.body.getChild("thorax_resonator");' in p,
     "live 1.104 stalker anatomy, jaw and heartbeat bones missing")
patch(P,
"""        PartDefinition root = mesh.getRoot();
        PartDefinition body = root.getChild("body");""",
"""        PartDefinition root = mesh.getRoot();
        // 1.105: replace actual generic zombie BOXES but keep joint names
        // and exact vanilla attachment pivots for gait, head and special rigs.
        // Two chest slabs with an open rib gap instead of a filled torso.
        root.addOrReplaceChild("body",
                CubeListBuilder.create().texOffs(16, 16)
                        .addBox(-4.0F, 0.0F, -1.8F, 8.0F, 3.2F, 3.6F)
                        .texOffs(16, 16).addBox(-3.5F, 8.1F, -1.4F, 7.0F, 3.9F, 2.8F)
                        .texOffs(16, 16).addBox(-3.8F, 5.2F, -1.5F, 7.6F, 1.5F, 3.0F)
                        .texOffs(16, 16).addBox(-1.2F, 3.0F, -1.1F, 2.4F, 6.3F, 2.2F),
                PartPose.ZERO);
        root.addOrReplaceChild("head",
                CubeListBuilder.create().texOffs(0, 0)
                        .addBox(-3.25F, -7.5F, -3.4F, 6.5F, 7.6F, 6.8F)
                        .texOffs(0, 0).addBox(-2.5F, -1.0F, -4.1F, 5.0F, 2.6F, 3.0F),
                PartPose.ZERO);
        root.addOrReplaceChild("hat", CubeListBuilder.create(), PartPose.ZERO);
        root.addOrReplaceChild("left_arm",
                CubeListBuilder.create().texOffs(40, 16)
                        .addBox(-1.5F, -2.0F, -1.65F, 3.0F, 14.0F, 3.3F),
                PartPose.offset(5.0F, 2.0F, 0.0F));
        root.addOrReplaceChild("right_arm",
                CubeListBuilder.create().texOffs(40, 16)
                        .addBox(-1.5F, -2.0F, -1.65F, 3.0F, 14.0F, 3.3F),
                PartPose.offset(-5.0F, 2.0F, 0.0F));
        root.addOrReplaceChild("left_leg",
                CubeListBuilder.create().texOffs(0, 16)
                        .addBox(-1.4F, 0.0F, -1.6F, 2.8F, 12.0F, 3.2F),
                PartPose.offset(2.1F, 12.0F, 0.0F));
        root.addOrReplaceChild("right_leg",
                CubeListBuilder.create().texOffs(0, 16)
                        .addBox(-1.4F, 0.0F, -1.6F, 2.8F, 12.0F, 3.2F),
                PartPose.offset(-2.1F, 12.0F, 0.0F));
        PartDefinition body = root.getChild("body");""",
"replace stalker base primitives before 3D crystals are parented")
patch(P,
"""                        .addBox(-5.3F, -6.0F, -3.0F, 10.6F, 11.0F, 2.4F)
                        .texOffs(96, 48).addBox(-1.8F, -3.5F, -4.0F, 3.6F, 6.0F, 1.5F),""",
"""                        // Open ribcage: top, lower and left/right bone islands.
                        // Real negative space remains visible from side angles.
                        .addBox(-4.8F, -6.0F, -3.0F, 9.6F, 2.6F, 2.4F)
                        .texOffs(64, 48).addBox(-4.6F, -0.9F, -3.0F, 9.2F, 2.1F, 2.4F)
                        .texOffs(64, 48).addBox(-3.1F, 3.2F, -3.0F, 6.2F, 1.8F, 2.4F)
                        .texOffs(96, 48).addBox(-1.8F, -3.5F, -4.0F, 3.6F, 6.0F, 1.5F),""",
"make stalker mineral chest actual segmented void anatomy")
patch(P,
"""                        .addBox(-4.5F, -5.5F, 2.0F, 9.0F, 12.0F, 2.5F),""",
"""                        .addBox(-1.3F, -5.5F, 2.0F, 2.6F, 12.0F, 2.5F)
                        .texOffs(64, 48).addBox(-4.5F, -5.5F, 2.1F, 1.5F, 8.0F, 2.2F)
                        .texOffs(64, 48).addBox(3.0F, -5.5F, 2.1F, 1.5F, 8.0F, 2.2F),""",
"thin vertebral spine with visible side gaps")

# Farm stalker is not the crystal stalker: distinct thin woody rib-cage,
# asymmetrical long fingers and root-horns remain, now no underlying zombie.
D=C/"DaemmerlingModel.java"
d=D.read_text(encoding="utf-8")
need('body.addOrReplaceChild("hollow_chest"' in d and
     "this.feedingJaw = this.head.getChild" in d and
     "if(entity.isCropNibbling())" in d,
     "1.100-1.102 Dämmerling jaw and crop horror required")
patch(D,
"""        PartDefinition root=mesh.getRoot();
        PartDefinition body=root.getChild("body");""",
"""        PartDefinition root=mesh.getRoot();
        // Distinct farm-horror skeleton: a narrow open torso and uneven
        // slender joints, NOT vanilla zombie cubes under extra texture.
        root.addOrReplaceChild("body",
                CubeListBuilder.create().texOffs(16,16)
                        .addBox(-3.3F,0.0F,-1.65F,6.6F,3.2F,3.3F)
                        .texOffs(16,16).addBox(-2.65F,8.4F,-1.15F,5.3F,3.6F,2.3F)
                        .texOffs(16,16).addBox(-1.0F,2.8F,-0.95F,2.0F,7.0F,1.9F),
                PartPose.ZERO);
        root.addOrReplaceChild("head",
                CubeListBuilder.create().texOffs(0,0)
                        .addBox(-3.0F,-7.6F,-3.2F,6.0F,7.6F,6.4F),
                PartPose.ZERO);
        root.addOrReplaceChild("hat",CubeListBuilder.create(),PartPose.ZERO);
        root.addOrReplaceChild("left_arm",
                CubeListBuilder.create().texOffs(40,16)
                        .addBox(-1.35F,-2.0F,-1.4F,2.7F,13.8F,2.8F),
                PartPose.offset(5.0F,2.0F,0.0F));
        root.addOrReplaceChild("right_arm",
                CubeListBuilder.create().texOffs(40,16)
                        .addBox(-1.35F,-2.0F,-1.4F,2.7F,13.8F,2.8F),
                PartPose.offset(-5.0F,2.0F,0.0F));
        root.addOrReplaceChild("left_leg",
                CubeListBuilder.create().texOffs(0,16)
                        .addBox(-1.3F,0.0F,-1.45F,2.6F,12.0F,2.9F),
                PartPose.offset(2.0F,12.0F,0.0F));
        root.addOrReplaceChild("right_leg",
                CubeListBuilder.create().texOffs(0,16)
                        .addBox(-1.3F,0.0F,-1.45F,2.6F,12.0F,2.9F),
                PartPose.offset(-2.0F,12.0F,0.0F));
        PartDefinition body=root.getChild("body");""",
"replace Dämmerling original humanoid primitive geometry")
patch(D,
"""                        .addBox(-5.2F,-5.0F,-2.6F,10.4F,12.0F,5.2F),""",
"""                        // Three woody rib segments leave literal open slots.
                        .addBox(-5.2F,-5.0F,-2.6F,10.4F,2.7F,5.2F)
                        .texOffs(64,48).addBox(-4.5F,0.0F,-2.4F,9.0F,2.0F,4.8F)
                        .texOffs(64,48).addBox(-3.0F,4.7F,-2.1F,6.0F,2.3F,4.2F),""",
"open the broad Dämmerling chest cover")

# Koloss reference: not another enormous block muzzle. Preserve anchored
# head, ears, jaw, horns, crystal eyes, safety hitbox and 256x256 UVs.
B=C/"MutagenkolossModel.java"
b=B.read_text(encoding="utf-8")
need('PartDefinition head = body.addOrReplaceChild("head",' in b
     and 'this.tailMid.xRot += 0.59F;' in b
     and 'body.getChild("core_iris_left")' in b
     and 'this.armorFractureVeins = new ModelPart[]' in b,
     "latest 1.104 four-leg Colossus face+tail+crystal model required")
# Earlier reference passes have already sculpted the head cube, so do not
# assume the initial 1.58 literal dimensions survived. Replace ONLY the
# parent head mesh block (bounded by the following head-child declaration),
# preserving its original transform, all 3D children, bones and textures.
current=B.read_text(encoding="utf-8")
head_start=current.index('        PartDefinition head = body.addOrReplaceChild("head",')
head_next=current.index('\n        head.addOrReplaceChild(',head_start)
head_chunk=current[head_start:head_next]
need(head_chunk.count("CubeListBuilder.create()")==1,
     "one sole solid head builder before head children")
need('PartPose.offset(0.0F, -5.0F, -20.0F)' in head_chunk,
     "preserve original skull pivot, no changes to existing children")
head_new="""        PartDefinition head = body.addOrReplaceChild("head",
                // Smaller head / stepped rock muzzle, keeping armor, jaw,
                // horns and illuminated eyes parented to this pivot.
                CubeListBuilder.create().texOffs(100, 32)
                        .addBox(-7.6F, -6.8F, -9.3F, 15.2F, 12.0F, 15.1F)
                        .texOffs(144, 32).addBox(-5.5F, -2.0F, -16.0F, 11.0F, 6.0F, 9.0F)
                        .texOffs(144, 52).addBox(-4.8F, 3.0F, -14.8F, 9.6F, 2.5F, 8.5F),
                PartPose.offset(0.0F, -5.0F, -20.0F));"""
B.write_text(current[:head_start]+head_new+current[head_next:],encoding="utf-8")


# No unpainted atlas UVs and no counterfeit borrowed creature skins.
t=R/"src/main/resources/assets/sporenwerk/textures/entity"
for filename, dims in (("kristallpirscher.png",(128,128)),
                       ("kristallpirscher_glow.png",(128,128)),
                       ("daemmerling.png",(128,128)),
                       ("daemmerling_glow.png",(128,128)),
                       ("mutagenkoloss.png",(256,256)),
                       ("mutagenkoloss_glow.png",(256,256))):
    with Image.open(t/filename) as im:
        need(im.size==dims,"original Minecraft compatible atlas "+filename)
# Keep rolling 1.104 regressions/current-doc active version constraints.
for f in (R/"tools").glob("test_*.py"):
    if f.name=="test_reference_base_silhouettes_105.py":continue
    a=f.read_text(encoding="utf-8")
    q=a.replace("Aktueller Entwicklungsstand: 1.104.0",
                "Aktueller Entwicklungsstand: 1.105.0")
    if "build.gradle" in a:
        q=q.replace(r"1\.104\.0",r"1\.105\.0")
        q=q.replace("artifact must be version 1.104.0","artifact must be version 1.105.0")
    q=q.replace('"Version 1.104.0" in readme and "Version 1.103.0" in readme',
                '"Version 1.105.0" in readme and "Version 1.104.0" in readme')
    if q!=a:f.write_text(q,encoding="utf-8")
g=R/"build.gradle"
s,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.105.0'",g.read_text(encoding="utf-8"),count=1)
need(n==1,"version 1.105.0");g.write_text(s,encoding="utf-8")
readme=R/"README.md";s=readme.read_text(encoding="utf-8")
old="**Aktueller Entwicklungsstand: 1.104.0 — Verlässliche Feldchronik und passive Komposter-Farmwache.**"
need(old in s,"generated 1.104 README header")
s=s.replace(old,
"**Aktueller Entwicklungsstand: 1.105.0 — Referenzgebundene Grundkörper und überarbeitete Monstersilhouetten.**",1)
section="""## Aktueller Entwicklungsschritt — 1.105.0

- **Kristallkoloss näher an der Vorlage:** Der vorhandene massive vierbeinige Basaltkörper bleibt erhalten; seine zuvor übergroße, kastenförmige Schnauze ist deutlich schmaler und der Schädel klar vom gepanzerten Rumpf getrennt. Kristallkrone, offener Brustkern, Rückenmonolithen, cyanfarbene Klauen, vierteilige Blende und skorpionförmiger Schwanz mit Kristallblüte bleiben an ihren bisherigen Gelenken.
- **Kristallpirscher wirklich skulpturiert:** Nicht länger nur ein Zombie mit darüber gemalten Kristallen: Die primären normalen Torso-, Kopf-, Arm- und Beinwürfel werden durch lange schmale, speziell modellierte Knochen ersetzt. Die Brustpanzerung ist in drei auseinanderliegende Rippenreihen aufgeteilt und der Rücken besteht aus schlanker Wirbelsäule mit seitlichen Stegen. Zwischen den Elementen bleibt echte negative 3D-Luft.
- **Dämmerling ohne massiven Zombie-Grundkörper:** Der originale humanoide Bewegungsrig bleibt funktional, aber Körper, Kopf, Gliedmaßen und Torso werden aus schlanken, teilweise durchbrochenen Wurzelsegmenten geformt. Seine zwei ungleich langen Wurzelhörner, Hände, Fresskiefer, Jagd- und Fraßanimationen bleiben erhalten.
- **Skins und Glow bewusst unverändert:** Die originalen 128×128- und 256×256-Minecraft-Pixeltexturen und transparenten selektiven Leuchtebenen bleiben gültig. Keine Bilddateien, Modelle oder Texturen aus Referenzmods wurden kopiert.
- **Keine Änderung der Spielmechanik:** Nur clientseitige ModelParts/Boxgrößen, keine neuen Spawnregelungen, Trefferzonen, Schadenswerte, KI-Ticker, Infektionsmechaniken, Heilungsfolgen oder Farmmaschinen.
- **Optische Qualitätspflicht:** Diese Änderungen adressieren reale Formabweichungen in der bisherigen Geometrie. Vollständige Referenztreue ist ohne Originalbildvergleich mit tatsächlichen Minecraft-Client-Screenshots noch nicht bewiesen; eine Abnahme ist deshalb dokumentiert.

"""
need("## Aktueller Entwicklungsschritt — 1.104.0" in s,"previous steps")
s=s.replace("## Aktueller Entwicklungsschritt — 1.104.0",section+"## Aktueller Entwicklungsschritt — 1.104.0",1)
release="""## Version 1.105.0 — Referenztreue beginnt bei der echten 3D-Grundform

- Kristallkoloss erhält eine kleinere gestufte Schnauze, damit sein massiger, niedriger Vierbeinerkörper, Kristallpanzer und skorpionförmiger Schwanz zur beschriebenen Vorlage passen.
- Kristallpirscher und Dämmerling verlieren die massiven normalen Zombie-Körperboxen zugunsten schmaler langgliedriger Meshes und wirklich offener Körpersegmente; vorhandene Krallen, Kristalle, Glow-Masken und Animationen bleiben angebunden.
- Echte Forge-Minecraft-Modelle statt weiterer Konzeptgrafik. Kein Kopieren fremder Mod-Assets und keine Änderungen an Mutagenkontrolle oder Farm-Horror-Gameplay. Der finale In-Game-Vergleich muss noch erfolgen.

"""
need("## Version 1.104.0 —" in s,"prior release")
s=s.replace("## Version 1.104.0 —",release+"## Version 1.104.0 —",1)
readme.write_text(s,encoding="utf-8")
print("Sporenwerk 1.105: rebuild humanoid bases with genuine negative space and narrow reference head on Colossus.")
