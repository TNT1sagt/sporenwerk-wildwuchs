#!/usr/bin/env python3
"""Sporenwerk 1.112: visible silhouette anchors, not more neon on old cubes.

Client-screenshot-driven geometry: a recognizable stone quadruped face with
recessed *already animated* crystal heart, a stronger curled scorpion tail,
reversed-jointed Stalker shins, and roots protruding from the actual hollow
Dämmerling ribs. No damage/AI/server/loot/scanner changes, no external assets.
"""
from pathlib import Path
from PIL import Image
import sys,re
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(ok,m):
    if not ok:raise SystemExit("1.112 silhouette rebuild: "+m)
def rep(file,a,b,label,n=1):
    code=file.read_text(encoding="utf-8")
    need(code.count(a)==n,label+": expected "+str(n)+" source anchors, found "+str(code.count(a)))
    file.write_text(code.replace(a,b,n),encoding="utf-8")

B=C/"MutagenkolossModel.java"
S=B.read_text(encoding="utf-8")
need('PartPose.offsetAndRotation(x, y + 10.0F, -24.6F' in S
     and 'PartPose.offset(0.0F, 10.0F, 14.0F)' in S
     and 'this.tailTip.xRot += 0.78F;' in S
     and S.count('head.addOrReplaceChild("lower_jaw"')==2,
     "1.111 aligned core and 1.81 two genuine jaw branches required")
# A real large skull that READS at distance, rather than the bright square
# heart obscuring every facial plane. Use the original stone UV islands.
# Emissive layer has the same child names, with empty basalt builders.
helper="""    /**
     * Signature angular quadruped head, visible from both 3/4 and front.
     * Matte basalt cheek plates + forward nasal crest are distinct 3D cubes.
     * Children of the moving head, NOT the recently recessed chest core.
     */
    private static void addPredatorySkullSilhouette(PartDefinition head, boolean glowing) {
        CubeListBuilder left = glowing ? CubeListBuilder.create()
                : CubeListBuilder.create().texOffs(100, 32)
                        .addBox(-1.8F, -3.4F, -4.6F, 3.6F, 6.8F, 9.2F)
                        .texOffs(144, 32).addBox(-1.3F, 1.9F, -5.4F, 2.6F, 2.5F, 7.5F);
        CubeListBuilder right = glowing ? CubeListBuilder.create()
                : CubeListBuilder.create().texOffs(100, 32)
                        .addBox(-1.8F, -3.4F, -4.6F, 3.6F, 6.8F, 9.2F)
                        .texOffs(144, 32).addBox(-1.3F, 1.9F, -5.4F, 2.6F, 2.5F, 7.5F);
        head.addOrReplaceChild("boss_zygoma_left", left,
                PartPose.offsetAndRotation(-8.0F, -0.4F, -11.5F,
                        0.10F, -0.22F, -0.19F));
        head.addOrReplaceChild("boss_zygoma_right", right,
                PartPose.offsetAndRotation(8.0F, -0.4F, -11.5F,
                        0.10F, 0.22F, 0.19F));
        CubeListBuilder nasal = glowing ? CubeListBuilder.create()
                : CubeListBuilder.create().texOffs(144, 52)
                        .addBox(-2.1F, -1.7F, -5.7F, 4.2F, 3.4F, 9.3F)
                        .texOffs(176, 100).addBox(-1.3F, -2.5F, -8.2F, 2.6F, 2.6F, 4.2F);
        head.addOrReplaceChild("boss_nasal_keel", nasal,
                PartPose.offsetAndRotation(0.0F, -1.8F, -14.2F,
                        -0.08F, 0.0F, 0.0F));
        // The independently animated mandible retains its existing dark/light teeth.
    }

"""
rep(B,"    public static LayerDefinition createBodyLayer() {",
    helper+"    public static LayerDefinition createBodyLayer() {",
    "insert real boss sculpted head geometry helper")
s=B.read_text(encoding="utf-8")
opaque,glow=s.split("    public static LayerDefinition createGlowLayer()",1)
need(opaque.count("return LayerDefinition.create(mesh, 256, 256);")==1
     and glow.count("return LayerDefinition.create(mesh, 256, 256);")==1
     and 'PartDefinition head = body.addOrReplaceChild("head"' in opaque
     and 'PartDefinition head = body.addOrReplaceChild("head"' in glow,
     "two distinct real head rig trees before bake")
opaque=opaque.replace("        return LayerDefinition.create(mesh, 256, 256);",
                      "        addPredatorySkullSilhouette(head, false);\n        return LayerDefinition.create(mesh, 256, 256);",1)
glow=glow.replace("        return LayerDefinition.create(mesh, 256, 256);",
                  "        addPredatorySkullSilhouette(head, true);\n        return LayerDefinition.create(mesh, 256, 256);",1)
B.write_text(opaque+"    public static LayerDefinition createGlowLayer()"+glow,encoding="utf-8")
# Dramatic curved rear silhouette based on the already 3-jointed stinger;
# leave the old 1.92 numerals intact for all historical pose tests.
rep(B,"""        this.tailTip.xRot += 0.78F;
        if (this.tailStinger != null) {""",
"""        this.tailTip.xRot += 0.78F;
        // A visibly elevated scorpion arc, rather than a long flat tube.
        // Frame-local additive constants; original 3-joint gait remains.
        this.tail.xRot += 0.10F;
        this.tailMid.xRot += 0.13F;
        this.tailTip.xRot += 0.14F;
        if (this.tailStinger != null) {""",
"elevate signature curled scorpion tail silhouette")

P=C/"KristallpirscherModel.java"
s=P.read_text(encoding="utf-8")
need('this.leftArm.xRot = 0.24F + quietStride * 0.17F;' in s
     and "return LayerDefinition.create(mesh, 128, 128);" in s
     and 'root.getChild("left_leg")' in s and 'root.getChild("right_leg")' in s,
     "1.111 hunters arms and original 128px legs required")
# Add visible heel hooks, each following the original gait limb. No more
# jagged backpack on the upright Zombie silhouette.
rep(P,"        return LayerDefinition.create(mesh, 128, 128);",
"""        // Backward hocks give the stalking legs an actual non-human side
        // profile; attached to moving leg bones, not a free-floating overlay.
        for (PartDefinition leg : new PartDefinition[] {
                root.getChild("left_leg"), root.getChild("right_leg") }) {
            leg.addOrReplaceChild("crystal_hock",
                    CubeListBuilder.create().texOffs(96, 48)
                            .addBox(-1.5F, -1.2F, -1.8F, 3.0F, 5.2F, 3.6F),
                    PartPose.offsetAndRotation(0.0F, 7.3F, 2.2F,
                            -0.44F, 0.0F, 0.0F));
            leg.addOrReplaceChild("crystal_heel_hook",
                    CubeListBuilder.create().texOffs(96, 0)
                            .addBox(-0.9F, -1.1F, -0.6F, 1.8F, 4.4F, 1.8F),
                    PartPose.offsetAndRotation(0.0F, 10.0F, 3.0F,
                            0.48F, 0.0F, 0.0F));
        }
        return LayerDefinition.create(mesh, 128, 128);""",
"new angular hunter leg silhouettes on moving joints")

D=C/"DaemmerlingModel.java"
s=D.read_text(encoding="utf-8")
need('body.getChild("rib_root_left")' in s
     and 'body.getChild("rib_root_right")' in s
     and 'leftHook.addOrReplaceChild("branch_left_outer"' in s
     and 'head.addOrReplaceChild("head_root"' in s,
     "existing true animated bark rib and actual 1.111 branches required")
rep(D,'        head.addOrReplaceChild("head_root",',
"""        // Roots must erupt from the hollow chest, not just resemble
        // ornamental reindeer horns on top of a vanilla human.
        body.getChild("rib_root_left").addOrReplaceChild("rib_fork",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-0.9F, -0.6F, -0.8F, 1.8F, 5.8F, 1.6F),
                PartPose.offsetAndRotation(-1.3F, 1.2F, 0.4F,
                        -0.32F, -0.18F, -0.82F));
        body.getChild("rib_root_right").addOrReplaceChild("rib_fork",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-0.8F, -0.5F, -0.8F, 1.6F, 7.3F, 1.6F),
                PartPose.offsetAndRotation(1.2F, 2.5F, 0.9F,
                        -0.18F, 0.16F, 0.69F));
        head.addOrReplaceChild("head_root",""",
"give living rib bones angular unequal outward branch prongs")
# User's original Minecraft-style 128/256 texels stay intact.
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for n,dim in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(n+suffix+".png")) as im:
            need(im.size==(dim,dim),"never drop Minecraft pixel atlas "+n+suffix)
# Upgrade latest-version metadata assertions only, not gameplay rules.
for f in (R/"tools").glob("test_*.py"):
    if f.name=="test_reference_anatomy_rework_112.py":continue
    s=f.read_text(encoding="utf-8")
    t=s.replace("Aktueller Entwicklungsstand: 1.111.0",
                "Aktueller Entwicklungsstand: 1.112.0")
    if "build.gradle" in s:
        t=t.replace(r"1\.111\.0",r"1\.112\.0").replace(
            "artifact must be version 1.111.0","artifact must be version 1.112.0")
    t=t.replace('"Version 1.111.0" in readme and "Version 1.110.0" in readme',
                '"Version 1.112.0" in readme and "Version 1.111.0" in readme')
    if t!=s:f.write_text(t,encoding="utf-8")
g=R/"build.gradle"
src,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
             "version = '1.112.0'",g.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle artifact version")
g.write_text(src,encoding="utf-8")
f=R/"README.md";readme=f.read_text(encoding="utf-8")
readme,n=re.subn(r"\*\*Aktueller Entwicklungsstand: 1\.111\.0[^\n]*\*\*",
    "**Aktueller Entwicklungsstand: 1.112.0 — Eigenständiger Koloss-Schädel, skorpionartiger Schwanzbogen, abgewinkelte Pirscher-/Wurzelbeine.**",readme,count=1)
need(n==1,"README latest summary")
step="""## Aktueller Entwicklungsschritt — 1.112.0

- **Kristallkoloss hat endlich eine erkennbare Felsenschnauze:** Neue echte, bewegte 3D-Wangenpanzer und ein abgestufter Nasenkiel sitzen auf dem vorhandenen Kopfknochen (nicht auf dem Brustkern). Die separaten Skin- und Glow-Bäume besitzen die exakt gleiche Topologie; der Lichtbaum enthält ausdrücklich KEINE vollleuchtenden Basaltquader. Augen, Kiefer, vier Brustiris-Blenden und vorhandene Spezialangriffe bleiben erhalten.
- **Schwanz gegen das gerade Rohr:** Die vorhandenen drei realen Schwanzgelenke formen im Idle einen ausgeprägteren Skorpionbogen. Der aus 1.92 erhaltene kristalline Stachel am Ende bewegt sich weiterhin während des Atemangriffs. Kein frei schwebender Fake-Stachel.
- **Kristallpirscher:** Eine tatsächliche, nach hinten versetzte, abgewinkelte Knöchel-/Fersenkonstruktion sitzt an BEIDEN beweglichen Unterschenkeln. Die ursprünglichen langen Kristallklauen hängen weiter korrekt und reagieren auf Jagd.
- **Dämmerling:** Zwei längenmäßig asymmetrische, seitlich aufbrechende 3D-Wurzelzacken sind nun Kinder der bereits atmenden hohlen Rippen statt weiterer gerade aufgesetzter Kopfstäbe. Nacht-/Fraßreaktion und Blickverhalten bleiben identisch.
- **Bilderkonflikt transparent:** Der vorhandene vierbeinige Koloss orientiert sich weiter am massigen Kristallpanzer-Referenzentwurf. Der anders gebaute frei schwebende Taiga-Kern ist als eigenständige Kreaturenform zu behandeln und wird nicht als gleicher Körper ausgegeben.
- **Sicherheit/Originalität:** Alles echte originale Minecraft-Forge-1.20.1-ModelParts mit den vorhandenen 128/256-Pixel-Texturen, keinerlei Asset-Übernahme anderer Mods. Mutagen, Farming, Endgame-Heilung, KI, Hitboxen, Angriffe und Netzwerk unberührt.
- **Abnahme:** Neue Struktur- und Layer-Regressionsprüfung. Der Vergleich mit den Konzepten im laufenden Minecraft-Client ist weiterhin erforderlich; ein erfolgreicher CI-Build beweist keine visuelle Gleichheit.

"""
need("## Aktueller Entwicklungsschritt — 1.111.0" in readme,"previous development notes")
readme=readme.replace("## Aktueller Entwicklungsschritt — 1.111.0",
                      step+"## Aktueller Entwicklungsschritt — 1.111.0",1)
release="""## Version 1.112.0 — Lesbare räuberische Anatomie statt Lichtkasten

- Basalt-Wangen, strukturierter dreidimensionaler Nasenkiel und matched opaque/empty-glow-ModelParts für den Colossus.
- Mehr skorpionartig gebogener echter, bereits dreifach animierter Schwanz und funktionsfähiger kristalliner Stachel.
- Beide Crystal-Stalker-Beine bekommen echte abgewinkelte Gelenksilhouetten.
- Zwei zusätzliche lebende Wurzelzacken des Dämmerlings wachsen aus beweglichen Rippen statt aus dem Kopf.
- Keine Fremdassets oder Gameplayregressions-Ausnahmen. Ingame-Vergleich bleibt ausstehend.

"""
need("## Version 1.111.0 —" in readme,"prior version notes")
readme=readme.replace("## Version 1.111.0 —",release+"## Version 1.111.0 —",1)
f.write_text(readme,encoding="utf-8")
print("Sporenwerk 1.112: real armored jaw and skull, raised articulated scorpion tail, digitigrade Stalker feet and rib-grown Dämmerling roots.")
