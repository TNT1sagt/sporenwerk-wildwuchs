#!/usr/bin/env python3
"""Sporenwerk 1.108: real sculpted negative space on the Pirscher's back crest,
Colossus pair of basalt crystal towers, and both Dämmerling root palms.

Minecraft Forge 1.20.1 ModelParts: preserve child names, pivots, live
animations, matched 128/256 textures and selective glow, without copying
foreign mods' copyrighted art. These are client mesh improvements, not a
claim of exact on-screen matching with the user's original concepts.
"""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"

def need(ok,msg):
    if not ok:raise SystemExit("1.108 segmented Minecraft silhouettes: "+msg)
def replace_once(path,old,new,description):
    code=path.read_text(encoding="utf-8")
    need(code.count(old)==1,description+" unique source pattern "+str(code.count(old)))
    path.write_text(code.replace(old,new,1),encoding="utf-8")

# Real 3D gap between rear high dorsal spires: the old 10x17x5 giant
# crystalline slab made the lanky Pirscher appear thick and blocky despite
# the narrowed chest from v1.105. Keep the SAME back_crest parent pivot and
# crest_side_shard child, so its animated look/attack poses are unchanged.
p=C/"KristallpirscherModel.java"
stalker=p.read_text(encoding="utf-8")
need('this.backCrest.xRot = -0.20F + sway;' in stalker
     and 'crest.addOrReplaceChild("crest_side_shard"' in stalker
     and 'addOrReplaceChild("dorsal_fin_left"' in stalker,
     "1.93+ animated chest, rear crest and 1.94 fins required")
replace_once(p,
"""                CubeListBuilder.create().texOffs(64, 0)
                        .addBox(-5.0F, -15.0F, 1.5F, 10.0F, 17.0F, 5.0F)
                        .texOffs(96, 0)
                        .addBox(-4.0F, -21.0F, 2.0F, 8.0F, 7.0F, 4.0F),""",
"""                // Three prongs separated by genuine air, not a painted
                // crack across the previous 10-pixel-wide solid back slab.
                CubeListBuilder.create().texOffs(64, 0)
                        .addBox(-4.8F, -15.0F, 1.5F, 2.6F, 16.8F, 4.2F)
                        .texOffs(64, 0)
                        .addBox(-0.9F, -21.0F, 2.0F, 2.8F, 22.0F, 4.0F)
                        .texOffs(96, 0)
                        .addBox(3.0F, -13.4F, 2.3F, 2.4F, 14.5F, 3.4F),""",
"three independent angled growth shafts on the animated Crystal Stalker")

# Both physical monoliths have their OWN articulated bones with independent
# mirror-sway animation. Subdivide only the normal basalt cubes; preserve
# the emission-layer transparent basalt (and its bright prism + rune children)
# identically so the two baked LayerDefinitions still have the same topology.
b=C/"MutagenkolossModel.java"
boss=b.read_text(encoding="utf-8")
need(boss.count('body.addOrReplaceChild("monolith_')==4
     and boss.count('fin_left.addOrReplaceChild("monolith_prism"')==2
     and boss.count('fin_right.addOrReplaceChild("monolith_prism"')==2,
     "matched skin and glow Colossus monoliths and prism children required")
old="""CubeListBuilder.create().texOffs(32, 224).addBox(-5.5F, -17.0F, -5.0F, 11.0F, 18.0F, 10.0F).texOffs(80, 224).addBox(-4.2F, -24.0F, -3.8F, 8.4F, 8.0F, 7.6F)"""
new="""CubeListBuilder.create().texOffs(32, 224)
                        .addBox(-5.1F, -17.0F, -4.6F, 3.4F, 17.0F, 9.2F)
                        .texOffs(32, 224).addBox(1.7F, -17.0F, -4.6F, 3.4F, 17.0F, 9.2F)
                        .texOffs(80, 224).addBox(-2.2F, -18.0F, 2.2F, 4.4F, 18.0F, 2.4F)
                        .texOffs(80, 224).addBox(-3.8F, -24.0F, -3.2F, 7.6F, 8.0F, 6.4F)"""
need(boss.count(old)==2,
     "matched left and right historical basalt base monolith dimensions")
boss=boss.replace(old,new)
b.write_text(boss,encoding="utf-8")

# 1.100 Dämmerling uses real 3D elongated fingers, but both palms are still
# one huge 4.6x5.6x3.6 root mitten. Leave all child fingers in place and
# sculpt each palm as two slender side struts with a lower joint bridge.
d=C/"DaemmerlingModel.java"
shade=d.read_text(encoding="utf-8")
need('private final ModelPart leftRibRoot,rightRibRoot;' in shade
     and 'guard.addOrReplaceChild("left_finger"' in shade
     and 'guard.addOrReplaceChild("right_finger"' in shade
     and 'this.leftClaws.xRot=-0.65F+' in shade,
     "1.106 animated roots and 1.101 crop-nibbling fingers required")
replace_once(d,
"""                CubeListBuilder.create().texOffs(64,48)
                        .addBox(-2.3F,0.0F,-1.8F,4.6F,5.6F,3.6F),""",
"""                // Two root metacarpals flank a real open hollow space.
                // Child fingers retain their exact old animation pivots.
                CubeListBuilder.create().texOffs(64,48)
                        .addBox(-2.20F,0.0F,-1.65F,1.45F,4.30F,3.0F)
                        .texOffs(64,48).addBox(0.75F,0.0F,-1.65F,1.45F,4.30F,3.0F)
                        .texOffs(64,48).addBox(-1.90F,4.25F,-1.10F,3.80F,1.30F,2.20F),""",
"open hand metacarpals with preserved moving root fingers")

# Keep correct Minecraft 128/256 atlases used for skin and emission. These
# UV islands were already created in earlier patch releases.
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for n,w in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(n+suffix+".png")) as im:
            need(im.size==(w,w),"pixel-textured layer mismatch "+n+suffix)

# Old tests assert active version but retain every gameplay/geometry rule.
for test in (R/"tools").glob("test_*.py"):
    if test.name=="test_segmented_creature_voids_108.py":continue
    s=test.read_text(encoding="utf-8")
    changed=s.replace("Aktueller Entwicklungsstand: 1.107.0",
                      "Aktueller Entwicklungsstand: 1.108.0")
    if "build.gradle" in s:
        changed=changed.replace(r"1\.107\.0",r"1\.108\.0")
        changed=changed.replace("artifact must be version 1.107.0",
                                "artifact must be version 1.108.0")
    changed=changed.replace('"Version 1.107.0" in readme and "Version 1.106.0" in readme',
                            '"Version 1.108.0" in readme and "Version 1.107.0" in readme')
    if changed!=s:test.write_text(changed,encoding="utf-8")
g=R/"build.gradle"
version,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                  "version = '1.108.0'",g.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle release declaration")
g.write_text(version,encoding="utf-8")

f=R/"README.md";doc=f.read_text(encoding="utf-8")
prior="**Aktueller Entwicklungsstand: 1.107.0 — Koloss-Gesichtspanzer und eigenständige Kristall-/Wurzelfüße.**"
need(prior in doc,"generated README 1.107 heading")
doc=doc.replace(prior,
"**Aktueller Entwicklungsstand: 1.108.0 — Getrennte Kristallrücken und echte offene Wurzelhände.**",1)
section="""## Aktueller Entwicklungsschritt — 1.108.0

- **Kristallpirscher mit drei getrennten Rückenprismen:** Der bislang durchgehende, große 10×17×5-Pixel-Kristallkasten aus der ursprünglichen 1.93-Version wurde entfernt und durch drei unterschiedlich hohe, schmale Kristallrücken mit tatsächlicher Luft dazwischen ersetzt. Die ursprüngliche bewegte Rückenkrone und ihre Seitenkristalle bleiben auf demselben animierten Knochen; Brustresonator, Kopf, Finnen und lange Klauen bleiben ebenfalls verbunden.
- **Koloss: Wirklich gespaltene Basaltmonolithen:** Die beiden ursprünglich monolithischen Rückenpfeiler bekommen durchgehende Schlitze zwischen den dunklen Außenstützen, einen dünnen rückseitigen Steg und eine kleine obere Panzerkappe. Ihre violetten Prisma- und Runen-Kinder bleiben an denselben Gelenken, die transparenten Glow-Layer werden nicht durch zusätzliches Basaltleuchten überlagert.
- **Dämmerling: Offene Wurzelhandflächen:** Die früheren dicken Wurzelhandschuhe werden durch zwei schlanke Knochenseiten mit Luftspalt und eine kleine Verbindung am Fingeransatz ersetzt. Die alten beiden langen animierten Finger an jedem Arm bleiben über ihre originalen Gelenk-Namen befestigt.
- **Minecraft-Rendering statt Konzeptbild:** Alles sind echte ModelPart-Cubes mit normalen Minecraft-Pixelatlanten (128×128 bzw. 256×256), keine fremden Assets und keine gesonderten nicht-renderbaren Meshdateien. Die tatsächliche Optik bleibt erst nach einem Minecraft-Client-Bildvergleich als vorlagentreu bewertbar.
- **Keine Gameplay-Veränderungen:** Bosskampf, Mutagen-Heilung, Maschinenschutz, KI, Crops, Spielerstatus, Spawns und Hitboxen bleiben unangetastet; keinerlei zusätzliche Server-Ticker oder Chunk-Scans.

"""
need("## Aktueller Entwicklungsschritt — 1.107.0" in doc,"prior development step")
doc=doc.replace("## Aktueller Entwicklungsschritt — 1.107.0",
                section+"## Aktueller Entwicklungsschritt — 1.107.0",1)
release="""## Version 1.108.0 — Echte Zwischenräume und getrennte Kristallanatomie

- Kristallpirscher: riesige massive Rückenplatte durch drei offene schlanke 3D-Kristallsporne ersetzt, mit intakten alten Knochen und Animationen.
- Koloss: beide basaltfarbenen Rückenmonolithen in zwei Seitenrippen, hintere Verbindung und kleine obere Kappe aufgeteilt. Ihre Leuchtprismen und aktiven Bossbewegungen bleiben erhalten.
- Dämmerling: offen modellierte Wurzelhandflächen statt grober würfelförmiger Fäustlinge; Finger und Nacht-/Fraßanimationen bleiben funktionsfähig.
- CI testet den gesamten Forge-1.20.1-Quellstand, Dedicated-Server-Start und die gesonderte Silhouetten-Regression. Der Originalbildvergleich muss noch im Minecraft-Client erfolgen.

"""
need("## Version 1.107.0 —" in doc,"prior release")
doc=doc.replace("## Version 1.107.0 —",release+"## Version 1.107.0 —",1)
f.write_text(doc,encoding="utf-8")
print("1.108 completed: original 3D multi-prong Stalker crest; actual negative-space basalt boss monoliths; two hollow Dämmerling root palms.")
