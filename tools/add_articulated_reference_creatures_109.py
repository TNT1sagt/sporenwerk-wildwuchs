#!/usr/bin/env python3
"""1.109: articulate the actual Minecraft creature models, not concept art.

The three physically separated crystal spines from 1.108 become independently
animated ModelPart bones without changing their resting silhouette. The root
horror opens and closes hollow palms while feeding; the Colossus monoliths
twist slightly with the existing network-synchronized breath windup. No
server-side damage, pathfinding, world/block, inventory or hitbox changes.
"""
from pathlib import Path
from PIL import Image
import re
import sys

R = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C = R/"src/main/java/de/sporenwerk/client"

def need(condition, message):
    if not condition:
        raise SystemExit("1.109 articulated Minecraft monster geometry: "+message)

def change(path, old, new, description):
    src = path.read_text(encoding="utf-8")
    need(src.count(old)==1, description+" expected one anchor; got "+str(src.count(old)))
    path.write_text(src.replace(old,new,1),encoding="utf-8")

p = C/"KristallpirscherModel.java"
s = p.read_text(encoding="utf-8")
need('this.backCrest.xRot = -0.20F + sway;' in s
     and 'crest.addOrReplaceChild("crest_side_shard"' in s
     and 'this.thoraxResonator.xScale' in s,
     "keep existing crystal torso and animated back crest")
change(p, """                CubeListBuilder.create().texOffs(64, 0)
                        .addBox(-4.8F, -15.0F, 1.5F, 2.6F, 16.8F, 4.2F)
                        .texOffs(64, 0)
                        .addBox(-0.9F, -21.0F, 2.0F, 2.8F, 22.0F, 4.0F)
                        .texOffs(96, 0)
                        .addBox(3.0F, -13.4F, 2.3F, 2.4F, 14.5F, 3.4F),""",
"""                // The three prisms now have independently movable bones.
                // They remain at exactly the same coordinates in neutral pose.
                CubeListBuilder.create(),""",
"remove fixed prongs from back parent without touching its joint")
change(p, '        crest.addOrReplaceChild("crest_side_shard",',
"""        crest.addOrReplaceChild("crest_prong_left",
                CubeListBuilder.create().texOffs(64, 0)
                        .addBox(-4.8F, -15.0F, 1.5F, 2.6F, 16.8F, 4.2F),
                PartPose.ZERO);
        crest.addOrReplaceChild("crest_prong_center",
                CubeListBuilder.create().texOffs(64, 0)
                        .addBox(-0.9F, -21.0F, 2.0F, 2.8F, 22.0F, 4.0F),
                PartPose.ZERO);
        crest.addOrReplaceChild("crest_prong_right",
                CubeListBuilder.create().texOffs(96, 0)
                        .addBox(3.0F, -13.4F, 2.3F, 2.4F, 14.5F, 3.4F),
                PartPose.ZERO);
        crest.addOrReplaceChild("crest_side_shard",""",
"three separate Minecraft ModelPart joints follow their shared animated crest")
change(p, '    private final ModelPart backCrest;',
"""    private final ModelPart backCrest;
    private final ModelPart crestProngLeft, crestProngCenter, crestProngRight;""",
"cache individual dorsal joints")
change(p, '        this.backCrest = this.body.getChild("back_crest");',
"""        this.backCrest = this.body.getChild("back_crest");
        this.crestProngLeft = this.backCrest.getChild("crest_prong_left");
        this.crestProngCenter = this.backCrest.getChild("crest_prong_center");
        this.crestProngRight = this.backCrest.getChild("crest_prong_right");""",
"bind three real crystal joints once at model bake")
change(p, '        this.backCrest.zRot = -0.16F + Mth.sin(limbSwing * 0.56F) * pace * 0.08F;',
"""        this.backCrest.zRot = -0.16F + Mth.sin(limbSwing * 0.56F) * pace * 0.08F;
        // Independent secondary motion with small angles to preserve the two
        // real >= 1-pixel rest-pose gaps. Every frame computes absolute poses.
        float crystalBreath = Mth.sin(ageInTicks * 0.105F);
        float hunting = entity.isAggressive() ? 1.0F : 0.0F;
        this.crestProngLeft.zRot = -0.022F - crystalBreath * 0.016F
                - hunting * 0.030F;
        this.crestProngCenter.xRot = -0.013F + Mth.sin(ageInTicks * 0.081F) * 0.025F
                - hunting * 0.060F;
        this.crestProngRight.zRot = 0.022F + crystalBreath * 0.016F
                + hunting * 0.030F;""",
"articulated three-prong idle breathe and predator silhouette")

d = C/"DaemmerlingModel.java"
shade = d.read_text(encoding="utf-8")
need('guard.addOrReplaceChild("left_finger"' in shade
     and 'guard.addOrReplaceChild("right_finger"' in shade
     and 'this.leftClaws.zRot=-0.14F-stride*0.09F;' in shade
     and 'entity.isCropNibbling()' in shade,
     "hollow root hands, old articulated fingers and real crop state required")
change(d, '        this.rightClaws.zRot=0.14F+stride*0.09F;',
"""        this.rightClaws.zRot=0.14F+stride*0.09F;
        // Palms are now open root struts; rotate them as a group so their
        // articulated fingers splay while actually biting crops, not forever.
        // All values are absolute per-frame poses: no accumulated drift.
        float nibbleSplay = entity.isCropNibbling() ? 0.16F : 0.0F;
        this.leftClaws.yRot = -0.055F - nibbleSplay
                - Mth.sin(ageInTicks * 0.083F) * 0.022F;
        this.rightClaws.yRot = 0.055F + nibbleSplay
                + Mth.sin(ageInTicks * 0.091F) * 0.022F;""",
"active crop nibble moves actual open palms and connected fingers")

b = C/"MutagenkolossModel.java"
boss = b.read_text(encoding="utf-8")
need('this.monolithLeft.zRot' in boss and 'this.monolithRight.zRot' in boss
     and 'float breathCharge = crystalState == MutagenkolossEntity.ATTACK_BREATH' in boss
     and 'this.head.zRot = -this.body.zRot * 0.60F;' in boss,
     "existing synchronized boss attacks and twin articulated monoliths required")
change(b, '        this.head.zRot = -this.body.zRot * 0.60F;',
"""        // Small inward/outward rotation of the NEW hollow basalt monoliths,
        // synchronized to the same existing crystal-breath attack charge.
        // Both visible and glow model trees evaluate this identical pose.
        float monolithBreath = Mth.sin(ageInTicks * 0.069F) * 0.018F;
        this.monolithLeft.yRot = 0.016F + monolithBreath + breathCharge * 0.075F;
        this.monolithRight.yRot = -0.016F - monolithBreath - breathCharge * 0.075F;
        this.head.zRot = -this.body.zRot * 0.60F;""",
"paired moving hollow basalt monoliths and emissive crystal prisms")

tex = R/"src/main/resources/assets/sporenwerk/textures/entity"
for name, dimension in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(tex/(name+suffix+".png")) as im:
            need(im.size==(dimension,dimension),
                 "keep Minecraft pixel skin + emissive atlas "+name+suffix)

# Update ONLY floating latest-release assertions from previous tests.
for test in (R/"tools").glob("test_*.py"):
    if test.name=="test_articulated_reference_creatures_109.py":
        continue
    src=test.read_text(encoding="utf-8")
    updated=src.replace("Aktueller Entwicklungsstand: 1.108.0",
                        "Aktueller Entwicklungsstand: 1.109.0")
    if "build.gradle" in src:
        updated=updated.replace(r"1\.108\.0",r"1\.109\.0")
        updated=updated.replace("artifact must be version 1.108.0",
                                "artifact must be version 1.109.0")
    updated=updated.replace('"Version 1.108.0" in readme and "Version 1.107.0" in readme',
                            '"Version 1.109.0" in readme and "Version 1.108.0" in readme')
    if updated!=src:
        test.write_text(updated,encoding="utf-8")

gradle = R/"build.gradle"
src=gradle.read_text(encoding="utf-8")
updated,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                  "version = '1.109.0'",src,count=1)
need(n==1,"single ForgeGradle release declaration")
gradle.write_text(updated,encoding="utf-8")

readme=R/"README.md"
src=readme.read_text(encoding="utf-8")
src,n=re.subn(r"\*\*Aktueller Entwicklungsstand: 1\.108\.0[^\n]*\*\*",
"""**Aktueller Entwicklungsstand: 1.109.0 — Eigenständig animierte Kristallspitzen, Wurzelhände und Basaltmonolithen.**""",src,count=1)
need(n==1,"generated 1.108 README heading")
section="""## Aktueller Entwicklungsschritt — 1.109.0

- **Pirscher: drei eigenständig bewegliche Rückenprismen:** Die drei offenen, bereits echten Kristallquader aus 1.108 besitzen jetzt separate ModelPart-Gelenke. Mittlerer Dorn neigt sich vor, beide äußeren antworten asymmetrisch auf Gehen, Atmen und Jagd. Im Ruhezustand sind die Originalproportionen und Luftzwischenräume unverändert. Keine bloßen 2D-Risse.
- **Dämmerling: lebendige offene Wurzelhände:** Die echten zweiteiligen Handstränge und daran hängenden Finger spreizen sich beim bereits bestehenden synchronisierten Beetfraß. Die Bewegung geht nach dem Angriff zurück; keine Drehung sammelt sich über mehrere Frames.
- **Kristallkoloss: bewegte Basaltmonolithen:** Die zwei 1.108 physisch geschlitzten Rückenpanzer reagieren jetzt auch entlang der Y-Achse leicht auf den vorhandenen Atemangriff. Normaler Haut-Layer und separat gebackener selektiver Glow-Layer rechnen mit denselben Zuständen.
- **Originale Minecraft-Pixeltexturen erhalten:** 128x128 bzw. 256x256 Haut-/Glühatlanten. Die komplette Mutagen-/Heil-/Farming-/Bossbalance, Kollisionsflächen und Serverlast werden nicht verändert.
- **Technische Regression:** drei echte prong-ModelParts, vollständige Knochenhierarchie, Ruhepose mit 3D-Luftspalten und Zustandsanimationen werden überprüft. CI prüft anschließend Forge-1.20.1-JAR und dedizierten Server.
- **Bildtreue noch nicht bestätigt:** Ein Client-Screenshot aus gleicher Perspektive wie die verbindlichen Referenzbilder bleibt für eine seriöse 1:1-Abnahme erforderlich. Die bestehende geometrische Querschnittsgrafik ersetzt keine Minecraft-Aufnahme.

"""
need("## Aktueller Entwicklungsschritt — 1.108.0" in src,
     "previous development section required")
src=src.replace("## Aktueller Entwicklungsschritt — 1.108.0",
                section+"## Aktueller Entwicklungsschritt — 1.108.0",1)
release="""## Version 1.109.0 — Eigenständig artikulierte Minecraft-Kristall- und Wurzelanatomie

- Drei einzelne bewegliche Kristalldornen des Pirschers statt einer einzigen starren Rückenkrone.
- Tatsächlich hohle, beim Fressen aufklappende Dämmerling-Wurzelhände.
- Gespiegelte, atemsynchrone Y-Rotation der beiden geschlitzten Koloss-Rückenmonolithen.
- Keine Third-Party-Assets und keine Änderung an bestehenden KI-, Farm-, Mutagen- oder Spielerregeln.

"""
need("## Version 1.108.0 —" in src,"previous release-history section")
src=src.replace("## Version 1.108.0 —",release+"## Version 1.108.0 —",1)
readme.write_text(src,encoding="utf-8")
print("1.109: 3 individually animated open crystal prongs, living Dämmerling palms and breath-responsive twin Colossus monoliths.")
