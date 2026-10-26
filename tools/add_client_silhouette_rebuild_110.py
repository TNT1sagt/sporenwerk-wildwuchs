#!/usr/bin/env python3
"""1.110: screenshot-led Forge ModelPart silhouette rebuild, NOT standalone art."""
from pathlib import Path
from PIL import Image
import sys,re
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(ok,msg):
    if not ok: raise SystemExit("1.110 reference reconstruction: "+msg)
def rep(path,old,new,why,count=1):
    s=path.read_text(encoding="utf8")
    need(s.count(old)==count,why+": anchor count "+str(s.count(old))+" expected "+str(count))
    path.write_text(s.replace(old,new,count),encoding="utf8")
b=C/"MutagenkolossModel.java"
# Massive continuous 40x20x52 block -> segmented shoulder/thorax/pelvis armor.
rep(b,"""CubeListBuilder.create().texOffs(0, 0).addBox(-20.0F, -8.0F, -26.0F, 40.0F, 20.0F, 52.0F)
                        .texOffs(0, 60).addBox(-21.0F, -7.0F, -25.0F, 42.0F, 17.0F, 24.0F)
                        .texOffs(80, 60).addBox(-19.0F, -6.0F, 3.0F, 38.0F, 15.0F, 22.0F)""",
"""CubeListBuilder.create()
                        // Split front shoulders, slim central spine and haunches.
                        .texOffs(0, 0).addBox(-17.5F, -9.5F, -23.0F, 35.0F, 10.5F, 23.0F)
                        .texOffs(0, 60).addBox(-12.0F, -1.0F, -19.5F, 24.0F, 11.0F, 24.0F)
                        .texOffs(80, 60).addBox(-14.0F, -8.5F, 8.5F, 28.0F, 11.0F, 16.0F)
                        .texOffs(0, 0).addBox(-8.5F, -1.5F, 4.0F, 17.0F, 7.0F, 6.5F)""","split horizontal solid boss torso")
# Four formerly tiny leg chains ended at model Y=10, not standard ground=24.
rep(b,""".texOffs(u, v).addBox(-8.0F, -2.0F, -6.5F, 16.0F, 8.0F, 13.0F)
                        .texOffs(u, v + 18).addBox(-6.4F, 3.0F, -5.5F, 12.8F, 5.0F, 11.0F)""",
""".texOffs(u, v).addBox(-6.2F, -2.0F, -5.9F, 12.4F, 14.5F, 11.8F)
                        .texOffs(u, v + 18).addBox(-4.6F, 8.6F, -4.7F, 9.2F, 6.0F, 9.4F)""","new long weight-bearing thighs")
rep(b,".addBox(-4.8F, -1.0F, -4.8F, 9.6F, 7.0F, 9.6F)",
      ".addBox(-3.8F, -1.0F, -4.0F, 7.6F, 12.0F, 8.0F)","narrow long lower legs")
rep(b,"PartPose.offsetAndRotation(0.0F, 6.0F, 0.0F, 0.0F, 0.0F,",
      "PartPose.offsetAndRotation(0.0F, 14.0F, 0.0F, 0.0F, 0.0F,","skin knee pivot")
rep(b,"PartPose.offset(0.0F, 6.0F, 0.0F));","PartPose.offset(0.0F, 14.0F, 0.0F));","glow knee pivot")
rep(b,"PartPose.offset(0.0F, 6.0F, -1.0F));","PartPose.offset(0.0F, 12.0F, -1.0F));","both paw pivots",count=2)
for old,new in (
    ("paw.y = 6.0F - lift * 1.65F;","paw.y = 12.0F - lift * 1.65F;"),
    ("stompPawLeft.y = 6.0F;","stompPawLeft.y = 12.0F;"),
    ("stompPawRight.y = 6.0F;","stompPawRight.y = 12.0F;"),
    (".addBox(-1.8F, 0.0F, -6.8F, 3.6F, 6.2F, 0.9F)",".addBox(-1.8F, 0.0F, -6.8F, 3.6F, 12.0F, 0.9F)"),
    (".addBox(-1.5F, 0.0F, -5.0F, 3.0F, 6.0F, 0.9F)",".addBox(-1.5F, 0.0F, -5.0F, 3.0F, 10.5F, 0.9F)"),
): rep(b,old,new,"align 1.110 pose and slender glow limb")
# Eliminate fullbright 14x15 cyan carpet under each paw; only vein stripe glows.
rep(b,"""PartDefinition paw = lower.addOrReplaceChild("paw", CubeListBuilder.create().texOffs(208, 48)
                .addBox(-7.0F, 0.0F, -8.0F, 14.0F, 2.0F, 15.0F),""",
"""PartDefinition paw = lower.addOrReplaceChild("paw", CubeListBuilder.create().texOffs(208, 48)
                .addBox(-2.6F, 0.12F, -7.9F, 5.2F, 0.4F, 0.8F),""",
"reduce excessive cyan paw fullbright")
# Seven rigid tall dorsal crystals: stagger heights, preserve all original names.
for z,h,lean,short in (("-16.0F",22,"-0.28F",17),("-13.0F",29,"0.22F",21),
                      ("-7.0F",24,"-0.16F",15),("-1.0F",31,"0.24F",20),
                      ("5.0F",24,"-0.18F",16),("11.0F",20,"0.22F",13),
                      ("17.0F",17,"0.0F",11)):
    rep(b,", "+z+", "+str(h)+", "+lean+");",
          ", "+z+", "+str(short)+", "+lean+");","mixed Colossus crystal lengths",count=2)
p=C/"KristallpirscherModel.java"
# Change REAL independently articulated crest part boxes, not concepts/PNG.
for old,new in (
    ("addBox(-4.8F, -15.0F, 1.5F, 2.6F, 16.8F, 4.2F)","addBox(-4.8F, -10.5F, 3.2F, 2.6F, 11.8F, 3.0F)"),
    ("addBox(-0.9F, -21.0F, 2.0F, 2.8F, 22.0F, 4.0F)","addBox(-0.9F, -14.5F, 3.0F, 2.8F, 15.5F, 3.4F)"),
    ("addBox(3.0F, -13.4F, 2.3F, 2.4F, 14.5F, 3.4F)","addBox(3.0F, -9.0F, 3.8F, 2.4F, 10.3F, 2.8F)"),
    ("addBox(-2.8F, -11.0F, -2.8F, 5.6F, 13.0F, 5.6F)","addBox(-2.2F, -8.0F, -2.2F, 4.4F, 10.0F, 4.4F)"),
    ("addBox(-1.8F, -18.0F, -1.8F, 3.6F, 7.0F, 3.6F)","addBox(-1.5F, -12.0F, -1.5F, 3.0F, 5.0F, 3.0F)"),
    ("PartPose.offsetAndRotation(6.0F, -7.0F, 2.0F, -0.15F, 0.08F, 0.40F)",
     "PartPose.offsetAndRotation(5.5F, -4.0F, 3.8F, -0.15F, 0.08F, 0.40F)"),
    ("addBox(-3.25F, -7.5F, -3.4F, 6.5F, 7.6F, 6.8F)","addBox(-2.7F, -7.8F, -3.2F, 5.4F, 7.8F, 6.4F)"),
    ("addBox(-4.2F, -1.8F, -4.9F, 8.4F, 5.0F, 1.5F)","addBox(-3.0F, -1.9F, -4.5F, 6.0F, 4.2F, 1.35F)"),
): rep(p,old,new,"Pirscher physically reshape crystal fan/head")
rep(p,""".addBox(-4.0F, 0.0F, -1.8F, 8.0F, 3.2F, 3.6F)
                        .texOffs(16, 16).addBox(-3.5F, 8.1F, -1.4F, 7.0F, 3.9F, 2.8F)
                        .texOffs(16, 16).addBox(-3.8F, 5.2F, -1.5F, 7.6F, 1.5F, 3.0F)
                        .texOffs(16, 16).addBox(-1.2F, 3.0F, -1.1F, 2.4F, 6.3F, 2.2F)""",
""".addBox(-3.5F, -0.2F, -1.8F, 7.0F, 2.6F, 3.6F)
                        .texOffs(16, 16).addBox(-2.55F, 9.1F, -1.3F, 5.1F, 2.9F, 2.6F)
                        .texOffs(16, 16).addBox(-2.9F, 4.9F, -1.3F, 5.8F, 1.3F, 2.6F)
                        .texOffs(16, 16).addBox(-0.95F, 2.0F, -1.0F, 1.9F, 8.1F, 2.0F)""",
"narrow true crystal hunter rib cage")
rep(p,"addBox(-1.5F, -2.0F, -1.65F, 3.0F, 14.0F, 3.3F)",
      "addBox(-1.2F, -2.0F, -1.4F, 2.4F, 14.8F, 2.8F)",
      "physically narrower predator arms",count=2)
d=C/"DaemmerlingModel.java"
for old,new in (
    ("addBox(-2.0F,-10.0F,-1.8F,4.0F,11.0F,3.6F)","addBox(-1.55F,-8.0F,-1.5F,3.1F,9.0F,3.0F)"),
    ("addBox(-1.2F,-17.0F,-1.2F,2.4F,7.5F,2.4F)","addBox(-0.95F,-13.0F,-0.95F,1.9F,5.4F,1.9F)"),
    ("addBox(-2.2F,-12.5F,-2.0F,4.4F,13.5F,4.0F)","addBox(-1.6F,-8.5F,-1.5F,3.2F,9.6F,3.0F)"),
    ("addBox(-1.2F,-20.0F,-1.2F,2.4F,8.0F,2.4F)","addBox(-0.9F,-15.0F,-0.85F,1.8F,6.6F,1.7F)"),
    ("addBox(-2.1F,-11.0F,-1.7F,4.2F,7.4F,3.4F)","addBox(-1.7F,-8.2F,-1.4F,3.4F,5.8F,2.8F)"),
    ("addBox(-1.1F,-16.0F,-1.0F,2.2F,5.7F,2.0F)","addBox(-0.85F,-12.1F,-0.75F,1.7F,4.4F,1.5F)"),
    ("addBox(-3.0F,-7.6F,-3.2F,6.0F,7.6F,6.4F)","addBox(-2.6F,-8.0F,-3.0F,5.2F,8.0F,6.0F)"),
): rep(d,old,new,"shorter irregular bark growth silhouette")
rep(d,""".addBox(-3.3F,0.0F,-1.65F,6.6F,3.2F,3.3F)
                        .texOffs(16,16).addBox(-2.65F,8.4F,-1.15F,5.3F,3.6F,2.3F)
                        .texOffs(16,16).addBox(-1.0F,2.8F,-0.95F,2.0F,7.0F,1.9F)""",
""".addBox(-2.9F,0.0F,-1.45F,5.8F,2.6F,2.9F)
                        .texOffs(16,16).addBox(-1.95F,9.0F,-1.0F,3.9F,3.0F,2.0F)
                        .texOffs(16,16).addBox(-0.72F,2.2F,-0.85F,1.44F,8.2F,1.7F)""",
"slim truly rooted torso")
rep(d,"        this.body.xRot=0.23F+Mth.sin(limbSwing*0.6662F)*stride*0.045F;",
"""        // Override the stock ZombieModel forward-held arms in normal idle.
        // The existing actual field-biting branch below still takes priority.
        this.leftArm.xRot=entity.isAggressive() ? -0.62F
                : 0.11F+Mth.sin(limbSwing*0.6662F)*stride*0.21F;
        this.rightArm.xRot=entity.isAggressive() ? -0.47F
                : -0.05F-Mth.sin(limbSwing*0.6662F)*stride*0.24F;
        this.body.xRot=0.23F+Mth.sin(limbSwing*0.6662F)*stride*0.045F;""",
"remove default outstretched zombie arms")
for creature,dim in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(R/"src/main/resources/assets/sporenwerk/textures/entity"/(creature+suffix+".png")) as img:
            need(img.size==(dim,dim),"Minecraft UV atlas preserved "+creature+suffix)
# 1.105 checks formerly pinned the exact obsolete wide primitive boxes.
# Retain every behavioral/structural assertion but update the positive
# geometry fixtures to the narrower verified 1.110 Minecraft ModelParts.
old_mesh_qa=R/"tools/test_reference_base_silhouettes_105.py"
qa=old_mesh_qa.read_text(encoding="utf8")
for old,new in (
    ("addBox(-4.0F, 0.0F, -1.8F, 8.0F, 3.2F, 3.6F)",
     "addBox(-3.5F, -0.2F, -1.8F, 7.0F, 2.6F, 3.6F)"),
    ("addBox(-3.5F, 8.1F, -1.4F, 7.0F, 3.9F, 2.8F)",
     "addBox(-2.55F, 9.1F, -1.3F, 5.1F, 2.9F, 2.6F)"),
    ("addBox(-1.2F, 3.0F, -1.1F, 2.4F, 6.3F, 2.2F)",
     "addBox(-0.95F, 2.0F, -1.0F, 1.9F, 8.1F, 2.0F)"),
    ("addBox(-1.5F, -2.0F, -1.65F, 3.0F, 14.0F, 3.3F)",
     "addBox(-1.2F, -2.0F, -1.4F, 2.4F, 14.8F, 2.8F)"),
    ("addBox(-3.25F, -7.5F, -3.4F, 6.5F, 7.6F, 6.8F)",
     "addBox(-2.7F, -7.8F, -3.2F, 5.4F, 7.8F, 6.4F)"),
    ("addBox(-3.3F,0.0F,-1.65F,6.6F,3.2F,3.3F)",
     "addBox(-2.9F,0.0F,-1.45F,5.8F,2.6F,2.9F)"),
    ("addBox(-1.0F,2.8F,-0.95F,2.0F,7.0F,1.9F)",
     "addBox(-0.72F,2.2F,-0.85F,1.44F,8.2F,1.7F)"),
    ("addBox(-20.0F, -8.0F, -26.0F, 40.0F, 20.0F, 52.0F)",
     "addBox(-17.5F, -9.5F, -23.0F, 35.0F, 10.5F, 23.0F)"),
):
    need(qa.count(old)==1,"obsolete reference fixture count "+old)
    qa=qa.replace(old,new,1)
old_mesh_qa.write_text(qa,encoding="utf8")
# Old gait test's measured 6px suspension is intentionally replaced by 12px
# lowered pads, while its detailed animation/test contract stays intact.
gait=R/"tools/test_colossus_weighted_gait_182.py"
s=gait.read_text(encoding="utf8")
for old,new in (("paw.y = 6.0F - lift * 1.65F;","paw.y = 12.0F - lift * 1.65F;"),
                ("stompPawLeft.y = 6.0F;","stompPawLeft.y = 12.0F;"),
                ("stompPawRight.y = 6.0F;","stompPawRight.y = 12.0F;")):
    need(s.count(old)==1,"old gait fixture "+old);s=s.replace(old,new,1)
gait.write_text(s,encoding="utf8")
# Roll latest version assertions, never suppress old gameplay tests.
for f in (R/"tools").glob("test_*.py"):
    if f.name=="test_client_silhouette_rebuild_110.py":continue
    s=f.read_text(encoding="utf8")
    t=s.replace("Aktueller Entwicklungsstand: 1.109.0","Aktueller Entwicklungsstand: 1.110.0")
    if "build.gradle" in s:
        t=t.replace(r"1\.109\.0",r"1\.110\.0").replace("artifact must be version 1.109.0","artifact must be version 1.110.0")
    t=t.replace('"Version 1.109.0" in readme and "Version 1.108.0" in readme',
                '"Version 1.110.0" in readme and "Version 1.109.0" in readme')
    if s!=t:f.write_text(t,encoding="utf8")
g=R/"build.gradle"
s,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.110.0'",g.read_text(encoding="utf8"),count=1)
need(n==1,"Gradle version bump");g.write_text(s,encoding="utf8")
f=R/"README.md";s=f.read_text(encoding="utf8")
s,n=re.subn(r"\*\*Aktueller Entwicklungsstand: 1\.109\.0[^\n]*\*\*",
            "**Aktueller Entwicklungsstand: 1.110.0 — Silhouettenumbau nach echten Minecraft-Aufnahmen.**",s,count=1)
need(n==1,"README generated heading")
section="""## Aktueller Entwicklungsschritt — 1.110.0

- **Koloss:** Durchgehender rechteckiger 40×20×52-Pixel-Grundkörper durch gestaffelte, in der Mitte schmalere Basaltmassen ersetzt. Alle vier Beine besitzen jetzt längere Ober- und Unterschenkel mit tiefer gesetzten Knien und Tatzen, sodass die Modell-Fußhöhe etwa bei 24 statt 10 Pixeln liegt.
- **Kein leuchtender Tatzen-Teppich mehr:** Das bisherige 14×15 große vollleuchtende Sohlenrechteck wurde im Glow-Layer durch einen dünnen Kristallstreifen ersetzt. Die animierten Klauen bleiben erhalten.
- **Koloss-Obersilhouette:** Sieben vorhandene unterschiedlich hoch animierte Rückenprismen verkürzt, um Kopf und zentralen Kristallkern klarer erkennen zu lassen. Zwei markante bewegliche Basaltmonolithen bleiben.
- **Kristallpirscher:** Drei eigenständig bewegliche Rückenprismen und das Seitenprisma physisch deutlich kleiner und weiter am Rücken. Echter schmaler Torso, kleinerer Kopf und Gesichtsmaske, schlankere lange Arme.
- **Dämmerling:** Die bisherigen sehr geraden überlangen Hörner/Wurzelspitzen und der Kopfaufbau verkürzt, schmalerer echter Wurzeltorso, normale Ruhelaufhaltung mit hängenden asymmetrischen Armen anstatt Vanilla-Zombie-T-Stellung.
- **Bestehende Mechaniken beibehalten:** Infektion, Endgame-Heilung, Farm, KI, Boss-Angriffe, Serverlast, Spawns und Hitboxen unberührt. Bestehende 128×128- und 256×256-Minecraft-Pixeltexturen weiterverwendet.
- **Ehrlicher Abnahmestand:** Quellgeometrie und Kompilierung werden automatisiert geprüft, echte Vorlagen-Gleichheit benötigt neue Minecraft-Client-Aufnahmen. Keine kopierten Assets anderer Mods.

"""
need("## Aktueller Entwicklungsschritt — 1.109.0" in s,"old generated section")
s=s.replace("## Aktueller Entwicklungsschritt — 1.109.0",section+"## Aktueller Entwicklungsschritt — 1.109.0",1)
release="""## Version 1.110.0 — Primäre Körperformen und Bodenkontakt

- Koloss: schmalerer gestaffelter Torso, vier nach unten verlängerte Beine und korrekt tiefer geführte Tatzen; überhellen Fußboden-Glow entfernt.
- Pirscher: riesigen Rückenfächer reduziert und Schädel sowie Torso tatsächlich neu proportioniert.
- Dämmerling: lange gerade Hörner gekürzt und die typischen horizontalen Zombie-Arme im Idle beseitigt.
- Alle vorangegangenen Minecraft-Forge-Mechaniken und ModelPart-Joints bleiben erhalten. Exakter Client-Bildvergleich offen.

"""
need("## Version 1.109.0 —" in s,"previous release section")
s=s.replace("## Version 1.109.0 —",release+"## Version 1.109.0 —",1)
f.write_text(s,encoding="utf8")
print("1.110 ModelPart silhouette rebuild installed: 24px grounded four-leg Colossus, narrower Stalker and asymmetric root horror.")
