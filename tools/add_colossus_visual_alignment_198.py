#!/usr/bin/env python3
"""Sporenwerk 1.98: fix a genuine Minecraft client visual alignment bug.

The historical Colossus skin uses body pivot y=-4 while its separately baked
fullbright layer used y=+9: every glow appendage was vertically misplaced by
13 model pixels. Align both at y=-4. Additionally move the four 1.97 chest iris
panels *in front of* the actual front-facing crystal core and ease their opening
so players can actually see the core revealed. Preserve gameplay and atlas art.

All fixes are in the Forge 1.20.1 client model source, NOT standalone images.
"""
from pathlib import Path
import re, sys

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
MODEL=ROOT/"src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
README=ROOT/"README.md"

def require(value, context):
    if not value: raise SystemExit("1.98 Colossus visual alignment: "+context)

def replace_once(old, new, context):
    src=MODEL.read_text(encoding="utf-8")
    require(src.count(old)==1, context+": anchor count "+str(src.count(old)))
    MODEL.write_text(src.replace(old,new,1),encoding="utf-8")

source=MODEL.read_text(encoding="utf-8")
require('private final ModelPart[] coreIrisPetals;' in source and
        'addFourPetalCoreIris(body, true);' in source and
        'addFourPetalCoreIris(body, false);' in source,
        "existing 1.97 four-part crystal iris and model layers required")

# The first root body is the opaque skin at -4 pixels. The second was +9 in
# the original 1.58 generator and never actually realigned; the mismatched
# hinge origin displaces eyes, heartbeat core, claws, plates and mouth glow.
opaque,glow=source.split("    public static LayerDefinition createGlowLayer()",1)
skin_pivot='PartPose.offset(0.0F, -4.0F, 0.0F)'
old_glow='PartPose.offset(0.0F, 9.0F, 0.0F)'
require(skin_pivot in opaque,"original opaque model uses -4 body pivot")
require(old_glow in glow,"original emissive model still has +9 body pivot")
require(glow.count(old_glow)==1, "exactly one fullbright origin to realign")
# Only change the y-pivot of the GLOW body's root, not any tail or jaw pivots.
first=glow.index('PartDefinition body = root.addOrReplaceChild("body",')
fragment=glow[first:first+220]
require(old_glow in fragment,
        "expected the old +9 pivot directly on the glow root, not a child")
glow=glow[:first]+glow[first:].replace(old_glow,skin_pivot,1)
source=opaque+"    public static LayerDefinition createGlowLayer()"+glow
MODEL.write_text(source,encoding="utf-8")

# The existing solid chest_core goes to z=-36.6, while the glow can reach
# z=-37.1. In 1.97 the iris was placed at z=-28.4: geometrically BEHIND the
# visible core and the decorative core mount. Move its hinge forward so all
# four leaves are readable from the player's front-facing view.
replace_once('PartPose.offsetAndRotation(x, y, -28.4F, 0.0F, 0.0F, 0.0F));',
             'PartPose.offsetAndRotation(x, y, -38.6F, 0.0F, 0.0F, 0.0F));',
             "bring iris hinges to the front of original chest crystal")

# Rounded/eased geometric 3D movement instead of a hard linear hinge pop.
# Use the existing synced ATTACK_TICKS to avoid client-server desync.
replace_once("""        float coreOpening = Math.max(breathCharge * 0.78F,
                Math.max(stompCharge * 0.34F, awakeningCharge * 0.90F));
        float shimmer = Math.max(0.0F, Mth.sin(ageInTicks * 0.17F)) * 0.025F;""",
"""        float irisProgress = Math.max(breathCharge * 0.78F,
                Math.max(stompCharge * 0.34F, awakeningCharge * 0.90F));
        // Smoothstep starts the aperture gently, then widens clearly.
        // Every frame recalculates the pose from synced attack state.
        irisProgress = Mth.clamp(irisProgress, 0.0F, 1.0F);
        float coreOpening = irisProgress * irisProgress * (3.0F - 2.0F * irisProgress);
        float shimmer = Math.max(0.0F, Mth.sin(ageInTicks * 0.17F)) * 0.025F;""",
"eased four-leaf iris opening and snap-safe reset")

# A small, dark raised crystal-ring lip outlines the shutter at all times.
# Emit exactly the same named ring (thin emissive trim only in glow) and pivot
# in both layers, maintaining the synchronized Minecraft visual silhouette.
old='''        for (int part = 0; part < 4; part++) {
            boolean sideways = part < 2;'''
new='''        // 1.98 four framed edge pieces surround the existing core aperture;
        // no fullbright solid basalt. Thin gem trim is drawn only as crystals.
        for (int corner = 0; corner < 4; corner++) {
            float sx = corner % 2 == 0 ? -1.0F : 1.0F;
            float sy = corner < 2 ? -1.0F : 1.0F;
            String edgeName = "iris_rim_" + corner;
            CubeListBuilder rimShell = glowing ? CubeListBuilder.create()
                    : CubeListBuilder.create().texOffs(128, 192)
                            .addBox(-2.3F, -2.3F, -1.3F, 4.6F, 4.6F, 2.6F);
            PartDefinition rim = body.addOrReplaceChild(edgeName, rimShell,
                    PartPose.offset(sx * 9.4F, sy * 8.6F, -37.9F));
            rim.addOrReplaceChild("gem_edge",
                    CubeListBuilder.create().texOffs(190, 192)
                            .addBox(-1.2F, -1.2F, -1.6F, 2.4F, 2.4F, 0.9F),
                    PartPose.ZERO);
        }
        for (int part = 0; part < 4; part++) {
            boolean sideways = part < 2;'''
replace_once(old,new,"visible framed ring with separate selective glow")

# Visual alignment must not alter any historical attack damage, AI, synced
# packets or server blocks. Only currently-active version assertions roll over.
for p in (ROOT/"tools").glob("test_*.py"):
    if p.name=="test_colossus_visual_alignment_198.py": continue
    before=p.read_text(encoding="utf-8")
    after=before.replace("Aktueller Entwicklungsstand: 1.97.0",
                         "Aktueller Entwicklungsstand: 1.98.0")
    if "build.gradle" in before:
        after=after.replace(r"1\.97\.0",r"1\.98\.0")
        after=after.replace("artifact must be version 1.97.0","artifact must be version 1.98.0")
    after=after.replace('"Version 1.97.0" in readme and "Version 1.96.0" in readme',
                        '"Version 1.98.0" in readme and "Version 1.97.0" in readme')
    if before!=after:p.write_text(after,encoding="utf-8")
gradle=ROOT/"build.gradle"
src=gradle.read_text(encoding="utf-8")
src,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
              "version = '1.98.0'",src,count=1)
require(n==1,"ForgeGradle version must be 1.98.0")
gradle.write_text(src,encoding="utf-8")

r=README.read_text(encoding="utf-8")
old_head="**Aktueller Entwicklungsstand: 1.97.0 — Kristallblende des Kolosses und bewegliche Mutagenherzen.**"
require(old_head in r,"generated README 1.97 headline required")
r=r.replace(old_head,"**Aktueller Entwicklungsstand: 1.98.0 — Korrigierte Koloss-Leuchtlayer und sichtbar öffnender Kristallkern.**",1)
section="""## Aktueller Entwicklungsschritt — 1.98.0

- **13 Pixel Glow-Versatz behoben:** Der Koloss besitzt zwei getrennt gebackene Minecraft-Modellbäume, deren Body-Pivot bisher um 13 Modellpixel in der Höhe voneinander abwich. Der Glow-Körper erhält nun exakt denselben Ursprung wie die normale 3D-Haut. Das korrigiert die Position von Leuchtaugen, Brustkern, Rückenmonolithen, Laufklauen und Schwanzkristallen gleichzeitig.
- **Kristallblende endlich vor dem Kern:** Die vier bereits in 1.97 modellierten Brustblätter saßen vorher hinter dem eigentlichen, weit nach vorne ragenden Kristallkern. Ihre Scharniere werden vor die leuchtende Kernspitze gesetzt, sodass sie aus frontaler Sicht tatsächlich eine Öffnung bilden können.
- **Glattere Öffnung:** Sanftes Anlaufen und Ausfächern der vier Blätter mittels Smoothstep über die bereits synchronisierten Angriffsticker. Im Leerlauf werden ihre Gelenke weiterhin absolut zurückgesetzt.
- **Ein echter eingerahmter Kern:** Vier zusätzliche, dunkle Steinhalterungen am Rand des Brustkristalls besitzen schmale violette Leuchtsteine. Beide Layer enthalten die gleichen vier Halterungen, während Basalt bewusst nur im normalen Layer liegt.
- **Alle Kampf- und Farmfunktionen erhalten:** Kein Eingriff in Trefferzonen, Angriffsberechnung, Boss-KI, Feldkontrollstation, Mutagen-Modi, Heilung oder Sporenmaschinen. Nur die clientseitigen Forge-ModelParts und ihr Ursprung werden korrigiert.
- **Verifizierbare Qualität:** Eigener Regressionstest misst beide Modellursprünge, die Z-Reihenfolge von Kern und Blende, die beiden Modellbäume, die unbeschädigten Texturatlanten und die bereits getestete synchronisierte Attack-Animation. Forge-Build, JAR und dedizierter Serverstart schließen die CI ab.

"""
require("## Aktueller Entwicklungsschritt — 1.97.0" in r,"previous current section missing")
r=r.replace("## Aktueller Entwicklungsschritt — 1.97.0",
            section+"## Aktueller Entwicklungsschritt — 1.97.0",1)
release="""## Version 1.98.0 — Kristallkoloss: Renderausrichtung, sichtbare Blende und Panzerfassung

- Normaler Modellbaum und Glow-Layer teilen endlich die gleiche vertikale Körperwurzel (Fix des historischen 13-Pixel-Versatzes).
- Vier vorhandene Brustkristall-Scharniere vor den leuchtenden Kern verlagert und mit einer geglätteten 3D-Öffnung versehen.
- Vier zusätzliche, tatsächlich modellierte Kristallfassungen an den Brustkanten mit selektivem Leuchtmaterial.
- Keine Änderungen an Boss-Schaden, KI, Infektion oder Farm-Horror; Client-Sichttest ist weiterhin Voraussetzung für ein endgültiges visuelles Urteil.

"""
require("## Version 1.97.0 —" in r,"release history 1.97 missing")
r=r.replace("## Version 1.97.0 —",release+"## Version 1.97.0 —",1)
README.write_text(r,encoding="utf-8")
print("Sporenwerk 1.98 installed: matching glow/skin pivots, forward four-leaf core iris, smooth opening and 4 crystal rim corners.")
