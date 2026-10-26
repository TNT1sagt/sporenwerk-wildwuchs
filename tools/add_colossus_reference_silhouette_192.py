#!/usr/bin/env python3
"""1.92 reference-based 3D Crystal Colossus: curled scorpion tail, paired armored
crystal towers and original colored 256x256 skin/emissive pixels. Forge ModelParts
only. No references or resources from other mods are copied."""
from pathlib import Path
from PIL import Image, ImageDraw
import re
import sys

R = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
M = R/"src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
T = R/"src/main/resources/assets/sporenwerk/textures/entity"
s = M.read_text(encoding="utf-8")

def need(ok, msg):
    if not ok: raise SystemExit("1.92 model: "+msg)

def patch(old, new, label):
    global s
    need(s.count(old)==1, label+" anchor count "+str(s.count(old)))
    s=s.replace(old,new,1)

need("private final ModelPart tailMid;" in s and
     "private final ModelPart crystalCrownLeft;" in s and
     "animateWeightedLeg(this.frontLeft" in s,
     "earlier four-leg, crown and three-joint tail rig is required")

# Both model layers must contain matching parent/child skeletons. Only the
# normal layer has opaque basalt; glow carries crystal and amber fissures.
def fin_geometry(glow):
    out=[]
    for side, x, yaw, roll in (("left",-17.0,-0.10,-0.19),
                               ("right",17.0,0.10,0.19)):
        name="monolith_"+side
        builder=("CubeListBuilder.create()" if glow else
                 'CubeListBuilder.create().texOffs(32, 224).addBox(-5.5F, -17.0F, -5.0F, 11.0F, 18.0F, 10.0F).texOffs(80, 224).addBox(-4.2F, -24.0F, -3.8F, 8.4F, 8.0F, 7.6F)')
        out.append('        PartDefinition fin_'+side+' = body.addOrReplaceChild("'+name+'",\n'
                   '                '+builder+',\n'
                   '                PartPose.offsetAndRotation('+f'{x:.1f}F, -7.0F, -9.0F, -0.18F, {yaw:.2f}F, {roll:.2f}F));')
        prism=("CubeListBuilder.create().texOffs(210, 228)"
               ".addBox(-2.5F, -9.7F, -2.5F, 5.0F, 10.2F, 5.0F)"
               ".texOffs(214, 228).addBox(-1.35F, -16.7F, -1.35F, 2.7F, 6.5F, 2.7F)" if glow else
               "CubeListBuilder.create().texOffs(210, 228)"
               ".addBox(-3.0F, -10.0F, -3.0F, 6.0F, 11.0F, 6.0F)"
               ".texOffs(214, 228).addBox(-1.8F, -17.0F, -1.8F, 3.6F, 7.0F, 3.6F)")
        out.append('        fin_'+side+'.addOrReplaceChild("monolith_prism",\n'
                   '                '+prism+', PartPose.offset(0.0F, -23.0F, 0.0F));')
        runes=("CubeListBuilder.create().texOffs(236, 228).addBox(-1.75F, -12.5F, -5.55F, 3.5F, 5.0F, 0.45F)"
               if glow else
               "CubeListBuilder.create().texOffs(236, 228).addBox(-2.4F, -13.0F, -5.45F, 4.8F, 6.0F, 1.0F)")
        out.append('        fin_'+side+'.addOrReplaceChild("molten_rune", '+runes+', PartPose.ZERO);')
    return "\n".join(out)

def stinger_geometry(glow):
    main=("CubeListBuilder.create().texOffs(210, 228).addBox(-2.4F, -2.4F, -1.8F, 4.8F, 4.8F, 8.4F)"
          if glow else
          "CubeListBuilder.create().texOffs(210, 228).addBox(-3.0F, -3.0F, -2.0F, 6.0F, 6.0F, 9.0F)")
    out=['        PartDefinition stinger = tailTip.addOrReplaceChild("stinger_bloom",',
         '                '+main+',',
         '                PartPose.offsetAndRotation(0.0F, -0.6F, 20.0F, 0.62F, 0.0F, 0.0F));']
    b=("CubeListBuilder.create().texOffs(210, 228).addBox(-1.6F, -2.0F, 0.2F, 3.2F, 4.0F, 8.3F).texOffs(214, 228).addBox(-0.7F, -1.0F, 7.7F, 1.4F, 2.0F, 5.8F)"
        if glow else
        "CubeListBuilder.create().texOffs(210, 228).addBox(-2.2F, -2.8F, 0.0F, 4.4F, 5.6F, 9.0F).texOffs(214, 228).addBox(-1.2F, -1.7F, 8.0F, 2.4F, 3.4F, 6.0F)")
    for side,x,sign in (("left",-3.0,-1),("right",3.0,1)):
        out.append('        stinger.addOrReplaceChild("stinger_prong_'+side+'", '+b+','
                   f' PartPose.offsetAndRotation({x:.1f}F, -0.4F, 3.5F, -0.08F, {0.18*sign:.2f}F, {0.56*sign:.2f}F));')
    out.append('        stinger.addOrReplaceChild("stinger_prong_top", '+b+
               ', PartPose.offsetAndRotation(0.0F, -3.0F, 3.5F, -0.52F, 0.0F, 0.0F));')
    return "\n".join(out)

marks=list(re.finditer(r"(?m)^        return LayerDefinition\.create\(mesh, 256, 256\);",s))
need(len(marks)==2, "two skin and glowing model returns")
for index in (1,0):
    code="        // 1.92 real articulated crystal tower and scorpion stinger meshes\n"
    code+=fin_geometry(index==1)+"\n"+stinger_geometry(index==1)+"\n"
    s=s[:marks[index].start()]+code+s[marks[index].start():]
patch("    private final ModelPart crystalCrownRight;",
"""    private final ModelPart crystalCrownRight;
    private final ModelPart monolithLeft;
    private final ModelPart monolithRight;
    private final ModelPart tailStinger;""","animated bones")
constructor='        this.crystalCrownRight = head.hasChild("crystal_crown_right") ? head.getChild("crystal_crown_right") : null;'
patch(constructor,constructor+"""
        this.monolithLeft = body.hasChild("monolith_left") ? body.getChild("monolith_left") : null;
        this.monolithRight = body.hasChild("monolith_right") ? body.getChild("monolith_right") : null;
        this.tailStinger = tailTip.hasChild("stinger_bloom") ? tailTip.getChild("stinger_bloom") : null;""","both layer bone references")
anchor="""        this.tailTip.yRot += Mth.sin(stridePhase - 1.70F) * stride * 0.14F;
        for (int i = 0; i < this.spines.length; i++) {"""
patch(anchor,"""        this.tailTip.yRot += Mth.sin(stridePhase - 1.70F) * stride * 0.14F;
        // 1.92 actual tail silhouette: arch upward, then curl toward the head.
        this.tail.xRot += 0.38F;
        this.tailMid.xRot += 0.59F;
        this.tailTip.xRot += 0.78F;
        if (this.tailStinger != null) {
            this.tailStinger.xRot = 0.62F + Mth.sin(ageInTicks * 0.083F) * 0.08F;
            this.tailStinger.yRot = Mth.sin(ageInTicks * 0.051F) * 0.10F;
            this.tailStinger.zRot = Mth.sin(ageInTicks * 0.13F) * 0.075F;
            if (entity.getAttackState() == MutagenkolossEntity.ATTACK_BREATH) {
                this.tailStinger.xRot += 0.23F;
            }
        }
        float monolithPulse = Mth.sin(ageInTicks * 0.058F) * 0.03F;
        if (this.monolithLeft != null) {
            this.monolithLeft.zRot = -0.19F - monolithPulse;
            this.monolithLeft.xRot = -0.18F - monolithPulse * 0.28F;
        }
        if (this.monolithRight != null) {
            this.monolithRight.zRot = 0.19F + monolithPulse;
            this.monolithRight.xRot = -0.18F - monolithPulse * 0.28F;
        }
        for (int i = 0; i < this.spines.length; i++) {""","tail curl and armor breath")
need(s.count('addOrReplaceChild("stinger_bloom"')==2 and
     s.count('addOrReplaceChild("monolith_left"')==2 and
     s.count('addOrReplaceChild("monolith_right"')==2, "all additions must exist in both layers")
need("getChunk(" not in s and "getChunkNow(" not in s, "renderer must not touch chunk data")
M.write_text(s,encoding="utf-8")

# Newly reserved atlas zone (top-right 208..255, 226..253) becomes faceted
# magenta-violet and amber glow in game; rest of texture remains unchanged.
for name in ("mutagenkoloss.png","mutagenkoloss_glow.png"):
    p=T/name
    image=Image.open(p).convert("RGBA")
    need(image.size==(256,256),"vanilla compatible 256 atlas: "+name)
    d=ImageDraw.Draw(image)
    light=name.endswith("_glow.png")
    d.rectangle((208,226,232,253),fill=(112,31,181,255) if light else (67,25,92,255))
    for k in range(4):
        x=210+k*5
        d.polygon(((x,250),(x+2,229),(x+4,249)),
                  fill=(229,95+k*24,255,255) if light else (151+k*16,51+k*20,207,255))
    d.rectangle((236,227,254,252),fill=(96,39,18,255) if light else (65,29,34,255))
    for k in range(5):
        y=229+k*4
        d.line((238+k%2,y,251-k%3,y+2),
               fill=(255,162+k*15,57+k*10,255) if light else (252,111+k*22,29,255),width=2)
    image.save(p,optimize=True)

# Keep all previous behavior contracts but move active release assertions.
for p in (R/"tools").glob("test_*.py"):
    if p.name=="test_colossus_reference_silhouette_192.py": continue
    before=p.read_text(encoding="utf-8")
    after=before.replace("Aktueller Entwicklungsstand: 1.91.0","Aktueller Entwicklungsstand: 1.92.0")
    if "build.gradle" in before:
        after=after.replace(r"1\.91\.0",r"1\.92\.0")
        after=after.replace("artifact must be version 1.91.0","artifact must be version 1.92.0")
    after=after.replace('"Version 1.91.0" in readme and "Version 1.90.0" in readme',
                        '"Version 1.92.0" in readme and "Version 1.91.0" in readme')
    if after!=before:p.write_text(after,encoding="utf-8")
p=R/"build.gradle"
gradle,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                "version = '1.92.0'",p.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle version")
p.write_text(gradle,encoding="utf-8")
p=R/"README.md"; readme=p.read_text(encoding="utf-8")
head="**Aktueller Entwicklungsstand: 1.91.0 — Koloss-Auftritt und lebendige Nachtwache.**"
need(head in readme,"generated source README current headline")
readme=readme.replace(head,"**Aktueller Entwicklungsstand: 1.92.0 — neue Kristallkoloss-Geometrie und Texturen im Spiel.**",1)
section="""## Aktueller Entwicklungsschritt — 1.92.0

- **Echtes 3D-Modell:** Die existierende Koloss-Entität besitzt nun einen viergelenkigen, hochgebogenen Skorpionschwanz mit einer dreizackigen magentafarbenen Kristallblüte.
- **Gepanzerte Rückenflügel:** Zwei hohe Basalt-Monolithen flankieren den Rücken und tragen violette Kristallspitzen und orange Resonanzadern. Die vorhandene Kristallkrone, der Brustkern und die cyanfarbenen Klauen bleiben erhalten.
- **Zwei passende Modellschichten:** Neue Forge-ModelParts mit identischen Ansatzpunkten für Haut und Glow. Nur Kristalle und Erzadern leuchten, nicht der dunkle Panzer.
- **Pixeltexturen:** Neue violette und bernsteinfarbene Pixel-Facetten direkt in beiden 256x256-PNG-Atlanten. Keine fremden JAR-Assets übernommen.
- **Animation:** Schwanz und Kristallblüte reagieren auf Bewegung sowie Kristallatem; die Monolithen bewegen sich leicht mit der Atmung.
- **Technische Qualität:** Keine neuen Server-Ticker oder Chunk-Forceloads. Bestehende KI, Bosskampf, Mutagenfelder und Schutzmechaniken bleiben unverändert. Client-Sichtkontrolle der Form steht noch aus.

"""
need("## Aktueller Entwicklungsschritt — 1.91.0" in readme,"previous current section")
readme=readme.replace("## Aktueller Entwicklungsschritt — 1.91.0",section+"## Aktueller Entwicklungsschritt — 1.91.0",1)
release="""## Version 1.92.0 — Koloss-Skorpionschwanz und kristalline Rückenpanzer

- Animierte dreizackige Schwanzkristallblüte, gebogener Schwanz, zwei hohe Kristallmonolithen, original magenta-orange Pixelatlasflächen, deckungsgleiche Glow-Modellknochen.
- Bestehende Spielsysteme, Kampfschaden und Forschungswege bleiben erhalten. Automatisierte Tests verifizieren den Forge-Build; visuelle Gleichheit mit Referenzbildern muss im Spiel überprüft werden.

"""
need("## Version 1.91.0 —" in readme,"release history")
readme=readme.replace("## Version 1.91.0 —",release+"## Version 1.91.0 —",1)
p.write_text(readme,encoding="utf-8")
print("Sporenwerk 1.92 actual Minecraft model: vaulted stinger tail, monoliths, magenta/amber atlases and mirrored glow geometry.")
