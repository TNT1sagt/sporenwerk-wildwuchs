#!/usr/bin/env python3
"""Sporenwerk 1.106.0: restore eye/skull alignment after 1.105, open up the
Crystal Stalker's arms and add true movable root filaments to Dämmerling.

Original opaque pixels and selective emissive masks only: no borrowed images,
no server tick, no additional entities, no combat modifications. This fixes
concrete geometry errors rather than asserting a screenshot-perfect match.
"""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(ok,msg):
    if not ok:raise SystemExit("Sporenwerk 1.106 model alignment: "+msg)
def patch(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    need(s.count(old)==1,label+" unique anchor count "+str(s.count(old)))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

# In 1.105 the skull shrunk to X +/- 7.6 and front z=-9.3, but both
# original 1.58 eyes still live at X -9.5/-6 and +6/+9.5!
# Put both fullbright eyes onto the *actual front upper face*, not in air.
B=C/"MutagenkolossModel.java"
boss=B.read_text(encoding="utf-8")
need('addBox(-7.6F, -6.8F, -9.3F, 15.2F, 12.0F, 15.1F)' in boss,
     "1.105 smaller original skull required")
need('head.addOrReplaceChild("eye_left"' in boss
     and 'head.addOrReplaceChild("eye_right"' in boss,
     "matched emissive anatomical eye bones required")
patch(B,
"""CubeListBuilder.create().texOffs(200, 28).addBox(-9.5F, -4.5F, -12.2F, 3.5F, 3.0F, 1.4F),""",
"""CubeListBuilder.create().texOffs(200, 28)
                        .addBox(-6.15F, -4.8F, -9.95F, 3.2F, 2.5F, 0.9F),""",
"Colossus left eye moved IN skull face plane")
patch(B,
"""CubeListBuilder.create().texOffs(200, 28).addBox(6.0F, -4.5F, -12.2F, 3.5F, 3.0F, 1.4F),""",
"""CubeListBuilder.create().texOffs(200, 28)
                        .addBox(2.95F, -4.8F, -9.95F, 3.2F, 2.5F, 0.9F),""",
"Colossus right eye correctly mirrored")
# The old brow armor is larger than the now reduced skull. Adjust just its
# rotationally anchored dark shielding, not its child name/pivot. This keeps
# matching emission bones but prevents fullbright ghost armor floating out.
for side,old,new in (
 ("left",'addBox(-8.18F, -8.72F, -14.38F, 8.36F, 4.24F, 8.36F)',
         'addBox(-7.10F, -8.1F, -12.8F, 7.25F, 3.65F, 7.1F)'),
 ("right",'addBox(-0.18F, -8.72F, -14.38F, 8.36F, 4.24F, 8.36F)',
          'addBox(-0.15F, -8.1F, -12.8F, 7.25F, 3.65F, 7.1F)'),
):
    # Only thin fullbright shell: real basalt brow remains from existing
    # opaque sculpture, emissive silhouette must not float beyond the face.
    patch(B,old,new,side+" fullbright brow constrained to new skull")

# Stalker's old 7.6 x 10 x 6.2 solid crystal shoulders hid its newly
# narrow 1.105 arm bones, cancelling the silhouette correction.
# Replace with 3 staggered crystal plates, leaving open gaps and long talons.
P=C/"KristallpirscherModel.java"
s=P.read_text(encoding="utf-8")
need('addOrReplaceChild("crystal_guard"' in s and
     'this.leftTalonA.xRot' in s and 'this.thoraxResonator.xScale' in s,
     "1.105 articulated crystalline stalker must be present")
patch(P,
"""                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-3.8F, -4.0F, -2.8F, 7.6F, 10.0F, 6.2F)
                        .texOffs(96, 48).addBox(-2.5F, 3.0F, -3.6F, 5.0F, 8.0F, 3.0F),""",
"""                // Split pauldrons, not one large cube hiding both arms.
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-3.25F, -3.8F, -2.65F, 6.5F, 3.8F, 5.3F)
                        .texOffs(64, 48).addBox(-2.35F, 1.05F, -2.3F, 4.7F, 2.8F, 4.6F)
                        .texOffs(96, 48).addBox(-1.55F, 5.0F, -3.15F, 3.1F, 4.9F, 2.8F),""",
"give both Pirscher arms separated crystalline pauldrons")

# The Dämmerling is a root horror, not a crystal zombie. Add two thin hanging
# filaments to the already genuinely hollow torso, with distinct and
# automatically reset animations on walking vs real crop nibbling.
D=C/"DaemmerlingModel.java"
d=D.read_text(encoding="utf-8")
need('body.addOrReplaceChild("hollow_chest"' in d and
     'this.feedingJaw = this.head.getChild("hollow_jaw");' in d and
     'if(entity.isCropNibbling()) {' in d,
     "1.105 hollow shade and 1.102 jaw locomotion required")
patch(D,
"""    private final ModelPart feedingJaw;""",
"""    private final ModelPart feedingJaw;
    private final ModelPart leftRibRoot,rightRibRoot;""",
"cache two new dangling roots")
patch(D,
"""        this.feedingJaw = this.head.getChild("hollow_jaw");""",
"""        this.feedingJaw = this.head.getChild("hollow_jaw");
        this.leftRibRoot = this.body.getChild("rib_root_left");
        this.rightRibRoot = this.body.getChild("rib_root_right");""",
"bind roots once during bake")
patch(D,
"""        head.addOrReplaceChild("head_root",""",
"""        // Open ribs remain visible between these two narrow drooping roots.
        // UVs reuse painted 128x128 Minecraft atlas root islands.
        body.addOrReplaceChild("rib_root_left",
                CubeListBuilder.create().texOffs(64,48)
                        .addBox(-0.75F,0.0F,-1.2F,1.5F,8.0F,2.4F)
                        .texOffs(96,0).addBox(-0.55F,7.5F,-0.9F,1.1F,4.7F,1.8F),
                PartPose.offsetAndRotation(-4.1F,2.0F,-1.55F,-0.12F,0.09F,-0.27F));
        body.addOrReplaceChild("rib_root_right",
                CubeListBuilder.create().texOffs(64,48)
                        .addBox(-0.75F,0.0F,-1.1F,1.5F,6.6F,2.2F)
                        .texOffs(96,0).addBox(-0.45F,6.2F,-0.9F,0.9F,5.2F,1.8F),
                PartPose.offsetAndRotation(4.1F,3.1F,-1.45F,-0.09F,-0.08F,0.23F));
        head.addOrReplaceChild("head_root",""",
"two separate original hanging root bones")
patch(D,
"""        this.headRoot.zRot=0.32F+pulse*0.04F;""",
"""        this.headRoot.zRot=0.32F+pulse*0.04F;
        // Recomputed absolutely every render frame; no rotation drift.
        this.leftRibRoot.zRot=-0.27F+pulse*0.075F+stride*0.035F;
        this.rightRibRoot.zRot=0.23F-pulse*0.063F-stride*0.025F;
        this.leftRibRoot.xRot=-0.12F+Mth.sin(ageInTicks*0.091F)*0.035F;
        this.rightRibRoot.xRot=-0.09F-Mth.sin(ageInTicks*0.081F)*0.041F;""",
"living asymmetric hanging roots")
patch(D,
"""        if(entity.isCropNibbling()) {
            float clawBeat=Mth.sin(ageInTicks*0.52F);""",
"""        if(entity.isCropNibbling()) {
            float clawBeat=Mth.sin(ageInTicks*0.52F);
            this.leftRibRoot.xRot-=0.18F+clawBeat*0.075F;
            this.rightRibRoot.xRot-=0.13F-clawBeat*0.055F;""",
"roots lean forward only during actual crop attack")

# Structural changes only: leave all original 128/256 textures and
# separate transparent glow PNGs alone; no 3rd-party JAR assets imported.
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for n,dim in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(n+suffix+".png")) as im:
            need(im.size==(dim,dim),"correct vanilla-friendly pixel atlas "+n+suffix)

# Upgrade older version-only checks; retain structural assertions.
for p in (R/"tools").glob("test_*.py"):
    if p.name=="test_reference_anatomy_106.py":continue
    orig=p.read_text(encoding="utf-8")
    update=orig.replace("Aktueller Entwicklungsstand: 1.105.0",
                        "Aktueller Entwicklungsstand: 1.106.0")
    if "build.gradle" in orig:
        update=update.replace(r"1\.105\.0",r"1\.106\.0")
        update=update.replace("artifact must be version 1.105.0",
                              "artifact must be version 1.106.0")
    update=update.replace('"Version 1.105.0" in readme and "Version 1.104.0" in readme',
                          '"Version 1.106.0" in readme and "Version 1.105.0" in readme')
    if update!=orig:p.write_text(update,encoding="utf-8")
G=R/"build.gradle"
g,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.106.0'",G.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle version replacement");G.write_text(g,encoding="utf-8")
F=R/"README.md";doc=F.read_text(encoding="utf-8")
head="**Aktueller Entwicklungsstand: 1.105.0 — Referenzgebundene Grundkörper und überarbeitete Monstersilhouetten.**"
need(head in doc,"1.105 generated README heading")
doc=doc.replace(head,
 "**Aktueller Entwicklungsstand: 1.106.0 — Korrekte Koloss-Leuchtaugen und feineres 3D-Kreaturenskelett.**",1)
section="""## Aktueller Entwicklungsschritt — 1.106.0

- **Korrekt ausgerichtete Koloss-Augen:** Nach der 1.105-Verkleinerung des Schädels lagen die alten Leuchtaugen teilweise außerhalb der neuen Kopfform. Ihre zwei originalen emissiven Minecraft-ModelParts wurden tatsächlich verschoben, gespiegelt und in die Stirn-/Gesichtsebene des kleineren Schädels verlegt. Die alten viel zu breiten Leucht-Brauenplatten werden enger an den Kopf geführt.
- **Pirscher: offene Schultern statt riesiger Kristallwürfel:** Zwei bisher je etwa 7.6×10×6.2 Pixel große massive Panzerboxen waren trotz der 1.105-Skelettkorrektur weiterhin breit über den schlanken Armen. Die Panzerung besteht jetzt pro Seite aus drei in 3D getrennten Abschnitten, sodass Gliedmaßen und lange Klauen besser lesbar sind.
- **Dämmerling: zwei echte hängende Wurzelfasern:** Neue asymmetrische, getrennt animierte Wurzelknochen am offenen Brustkorb; beim Gehen langsames Gegenpendeln, beim tatsächlichen Beetfraß zusätzliche Beugung. Alle Rotationen werden pro Frame auf Grundwerte zurückgesetzt und nie additiv akkumuliert.
- **Nur optische Arbeit:** Kein neuer Scanner, KI-Ticker, zusätzlicher Schaden, neue Hitbox, Mutagenfolge oder Verlust von Gegenständen. Die bisherigen separaten PNG-Haut-/Glow-Masken und Pixelatlas-Abmessungen bleiben erhalten.
- **Strengere Formprüfungen:** Neue Quell-Regression für tatsächliche Augenkoordinaten innerhalb des Kopfraums, gleich breite gespiegelte Augen, echte getrennte Schulterboxen und Wurzelpart-Geometrie, sowie für die fortbestehenden Koloss-Kern-/Boss-/Farm-Animationen.
- **Visuell weiter offen:** Originalbilder und reale Minecraft-Screenshots müssen direkt verglichen werden. Forge-/Server-Tests garantieren nicht, dass die Vorlage bereits exakt getroffen wurde.

"""
need("## Aktueller Entwicklungsschritt — 1.105.0" in doc,"prior development section")
doc=doc.replace("## Aktueller Entwicklungsschritt — 1.105.0",
                section+"## Aktueller Entwicklungsschritt — 1.105.0",1)
release="""## Version 1.106.0 — Referenznahe anatomische Fehlerkorrekturen

- Koloss: Leuchtaugen passend zum kleineren Schädel auf die tatsächliche Gesichtsfront verlegt und ausgefranste Glow-Brauen eingegrenzt.
- Kristallpirscher: zwei übergroße Schulterwülste durch je drei räumlich getrennte Facettenpanzer ersetzt, um die schlanke Silhouette von Version 1.105 nicht zu verdecken.
- Dämmerling: zwei echte, asymmetrisch wippende Wurzelknochen am offenen Brustkorb; zusätzlicher Reflex beim echten Fraß.
- Forge-1.20.1-Build, Pixelatlanten, Boss-/Farm-Regressionen und dedizierter Server werden automatisch geprüft. Originalbildgleiche Optik bleibt vom In-Game-Vergleich abhängig.

"""
need("## Version 1.105.0 —" in doc,"prior release")
doc=doc.replace("## Version 1.105.0 —",release+"## Version 1.105.0 —",1)
F.write_text(doc,encoding="utf-8")
print("1.106: facial emissive geometry aligned to smaller skull; slender crystalline shoulders, animated asymmetrical Dämmerling rib roots installed.")
