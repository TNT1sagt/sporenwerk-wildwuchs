#!/usr/bin/env python3
"""1.111: separate the Colossus' snout from its giant opaque chest iris;
give Pirscher relaxed non-Zombie arms, Dämmerling four 3D antler branches.
Only alter Minecraft ModelParts and their current-version test fixtures.
"""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(ok,m):
    if not ok:raise SystemExit("1.111 client anatomy: "+m)
def rep(f,a,b,label):
    s=f.read_text(encoding="utf8")
    need(s.count(a)==1,label+": source anchor "+str(s.count(a)))
    f.write_text(s.replace(a,b,1),encoding="utf8")

b=C/"MutagenkolossModel.java"
boss=b.read_text(encoding="utf8")
need('PartPose.offsetAndRotation(x, y, -38.6F, 0.0F, 0.0F, 0.0F));' in boss
     and 'paw.y = 12.0F - lift * 1.65F;' in boss,
     "1.98 iris and 1.110 grounded boss required")
for name in ("chest_core_mount","chest_core","core_glow"):
    s=b.read_text(encoding="utf8")
    key='body.addOrReplaceChild("'+name+'"'
    need(s.count(key)==1,"single chest/eyes node "+name)
    start=s.index(key)
    end=s.index('PartPose.ZERO);',start)
    need(end-start<1900 and 'CubeListBuilder.create()' in s[start:end],
         name+" must retain its original real Minecraft cubes")
    s=s[:end]+'PartPose.offset(0.0F, 10.0F, 14.0F));'+s[end+len('PartPose.ZERO);'):]
    b.write_text(s,encoding="utf8")
rep(b,'PartPose.offsetAndRotation(x, y, -38.6F, 0.0F, 0.0F, 0.0F));',
      'PartPose.offsetAndRotation(x, y + 10.0F, -24.6F, 0.0F, 0.0F, 0.0F));',
      "all four movable iris leaves follow recessed lower heart")
# The four corner gems are separately parented to the Colossus body.
# Their old z=-37.9 would float in front of the real snout after relocation.
rep(b,'PartPose.offset(sx * 9.4F, sy * 8.6F, -37.9F)',
      'PartPose.offset(sx * 9.4F, sy * 8.6F + 10.0F, -23.9F)',
      "realign all four crystal rim corner gems")
# Update coordinate-only assertions in 1.98's strict original regression.
# Preserve ALL other attack/geometry and glow alignment assertions.
old=R/"tools/test_colossus_visual_alignment_198.py"
qa=old.read_text(encoding="utf8")
for a,z in (
    ('PartPose.offset(sx * 9.4F, sy * 8.6F, -37.9F)',
     'PartPose.offset(sx * 9.4F, sy * 8.6F + 10.0F, -23.9F)'),
    (r'PartPose\.offsetAndRotation\(x, y, ([-\d.]+)F,',
     r'PartPose\.offsetAndRotation\(x, y \+ 10\.0F, ([-\d.]+)F,'),
    ('iris_z <= -38.0 and iris_z > -41.0',
     'iris_z <= -24.0 and iris_z > -25.2'),
    ('iris_z < -37.1',
     'iris_z < (-37.1 + 14.0)'),
):
    need(qa.count(a)==1,"old 1.98 hard-coded iris fixture "+a)
    qa=qa.replace(a,z,1)
old.write_text(qa,encoding="utf8")
# The real head muzzle at approximately world-z -36 is now *in front*
# of the core focal point at about -23, rather than behind its bright slabs.
p=C/"KristallpirscherModel.java"
need('this.leftArm.xRot = this.leftArm.xRot * (1.0F - pursuit * 0.23F)' in p.read_text(encoding="utf8"),
     "retain existing state-driven crystal pursuit pose")
rep(p,'        this.body.xRot = 0.16F + Mth.sin(limbSwing * 0.56F) * pace * 0.055F;',
"""        // Long predator hands drop naturally, except during true pursuit.
        // Applied after ZombieModel.setupAnim; existing hunt animation layers on top.
        float quietStride = Mth.sin(limbSwing * 0.66F) * pace;
        this.leftArm.xRot = 0.24F + quietStride * 0.17F;
        this.rightArm.xRot = 0.14F - quietStride * 0.17F;
        this.body.xRot = 0.16F + Mth.sin(limbSwing * 0.56F) * pace * 0.055F;""",
"replace inherited forward zombie arm stance")
d=C/"DaemmerlingModel.java"
need('this.leftArm.xRot=entity.isAggressive() ? -0.62F' in d.read_text(encoding="utf8"),
     "retain 1.110 lowered horror arms")
rep(d,'        head.addOrReplaceChild("head_root",',
"""        // Four actual angled solid-voxel tines, with independent depth and
        // lengths: visibly open forks rather than painted horns or straight rods.
        PartDefinition leftHook = body.getChild("back_hook_left");
        leftHook.addOrReplaceChild("branch_left_outer",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-1.0F, -8.2F, -0.9F, 2.0F, 8.5F, 1.8F),
                PartPose.offsetAndRotation(-1.0F, -7.0F, 0.4F,
                        0.14F, -0.10F, -0.78F));
        leftHook.addOrReplaceChild("branch_left_inner",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-0.65F, -5.8F, -0.7F, 1.3F, 6.3F, 1.4F),
                PartPose.offsetAndRotation(0.9F, -10.0F, -0.5F,
                        -0.10F, 0.20F, 0.49F));
        PartDefinition rightHook = body.getChild("back_hook_right");
        rightHook.addOrReplaceChild("branch_right_outer",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-0.95F, -10.0F, -0.9F, 1.9F, 10.2F, 1.8F),
                PartPose.offsetAndRotation(1.2F, -8.0F, -0.6F,
                        -0.13F, 0.16F, 0.69F));
        rightHook.addOrReplaceChild("branch_right_inner",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(-0.6F, -5.8F, -0.7F, 1.2F, 6.3F, 1.4F),
                PartPose.offsetAndRotation(-0.8F, -9.5F, 0.8F,
                        0.21F, -0.13F, -0.47F));
        head.addOrReplaceChild("head_root",""",
"branch living roots rather than long straight planks")
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for creature,dim in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(creature+suffix+".png")) as im:
            need(im.size==(dim,dim),"original Minecraft atlas unchanged "+creature+suffix)

# Keep EVERY historical gameplay check; only advance current-release metadata.
for f in (R/"tools").glob("test_*.py"):
    if f.name=="test_open_face_root_branch_111.py":continue
    s=f.read_text(encoding="utf8")
    t=s.replace("Aktueller Entwicklungsstand: 1.110.0","Aktueller Entwicklungsstand: 1.111.0")
    if "build.gradle" in s:
        t=t.replace(r"1\.110\.0",r"1\.111\.0")
        t=t.replace("artifact must be version 1.110.0","artifact must be version 1.111.0")
    t=t.replace('"Version 1.110.0" in readme and "Version 1.109.0" in readme',
                '"Version 1.111.0" in readme and "Version 1.110.0" in readme')
    if t!=s:f.write_text(t,encoding="utf8")
g=R/"build.gradle"
t,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.111.0'",g.read_text(encoding="utf8"),count=1)
need(n==1,"Gradle artifact release version")
g.write_text(t,encoding="utf8")
doc=R/"README.md";s=doc.read_text(encoding="utf8")
s,n=re.subn(r"\*\*Aktueller Entwicklungsstand: 1\.110\.0[^\n]*\*\*",
            "**Aktueller Entwicklungsstand: 1.111.0 — Koloss-Schnauze vor dem Brustkern, eigenständige Jäger- und Wurzelanatomie.**",s,count=1)
need(n==1,"README release heading")
step="""## Aktueller Entwicklungsschritt — 1.111.0

- **Koloss-Schnauze tatsächlich freigestellt:** Die alte vordere Brust-/Kristall-/Glow-Box verdeckte im echten Minecraft das Gesicht. Die drei echten Kernelemente liegen nun 14 Modellpixel weiter hinten und 10 Pixel tiefer; alle vier beweglichen Iris-Blenden folgen derselben neuen räumlichen Transformierung. Augen, Kopf, Unterkiefer und alle bisherigen Bossattacken behalten ihre Gelenke.
- **Pirscher statt Zombie:** Beide langen Klauenarme hängen nun im Idle/Gehen unterhalb der Schulter. Die ursprüngliche Jagdbewegung wird unverändert auf die neuen Grundwinkel geschichtet.
- **Dämmerling statt gerader Stangen:** An beiden beweglichen Hauptrückenwurzeln sitzen jetzt je zwei weitere echte schräg versetzte Holzäste. Vier neue 3D-Wurzelgabeln sind asymmetrisch in Tiefe, Winkel und Länge; die existierende Nacht-/Fraß-Animation bleibt erhalten.
- **Keine fremden Assets oder Gameplayänderung:** Minecraft-128/256-Pixelatlas und Forge 1.20.1, Farming, Mutagen, Heilpfade, AI, Hitboxen und Netzwerk unverändert.
- **Konzeptbilder sind nicht widerspruchsfrei:** Die früheren quadrupeden Boss-Referenzen und das spätere schwebende Kristallkern-Bild zeigen unterschiedliche Körperkonzepte. Dieser Rebuild trennt Kopf und Kern für die bestehende vierbeinige Kreatur; das schwebende Konzept wäre ein separates Wesen.
- **Offene visuelle Abnahme:** CI kann Struktur und Kompilierung prüfen; die tatsächliche Bildgleichheit muss im laufenden Minecraft-Client getestet werden.

"""
need("## Aktueller Entwicklungsschritt — 1.110.0" in s,"previous development milestone")
s=s.replace("## Aktueller Entwicklungsschritt — 1.110.0",
            step+"## Aktueller Entwicklungsschritt — 1.110.0",1)
release="""## Version 1.111.0 — Sichtbarer Schädel statt verdecktem Kristallkasten

- Schwere 3D-Brustleuchte und animierte vierteilige Iris tief und rückwärts versetzt, sodass der eigentliche quadrupede Schädel hervortreten kann.
- Lange Pirscherhände in echter Ruhestellung statt Zombie-Angriffspose.
- Vier neue eigenständige schräge Wurzelzweige des Dämmerlings an beweglichen Elternknochen.
- Unveränderte Kampfsysteme, Mutagenregeln und originalgetreue Minecraft-Pixelatlanten; Client-Vergleich ausstehend.

"""
need("## Version 1.110.0 —" in s,"previous release history")
s=s.replace("## Version 1.110.0 —",release+"## Version 1.110.0 —",1)
doc.write_text(s,encoding="utf8")
print("1.111: spatial snout/core separation, proper hunter arms and forked root antlers installed.")
