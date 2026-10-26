#!/usr/bin/env python3
"""Sporenwerk 1.99: actual Minecraft/Forge model battle wear, no gameplay changes.

As the Crystal Colossus loses health its existing four articulated basalt
shoulder/haunch plates spread slightly, revealing four individually drawn
crystal vein overlays on *both* skin and glow layers. The Crystal Stalker has a
small injury-driven limp and more stressed crystalline breathing. No mechanics,
hitboxes, client/server packet formats or external art assets are altered.
"""
from pathlib import Path
import re,sys

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=ROOT/"src/main/java/de/sporenwerk/client"
MODEL=C/"MutagenkolossModel.java"
PIRSCHER=C/"KristallpirscherModel.java"
RENDERER=C/"KristallpirscherRenderer.java"
def require(ok,why):
    if not ok: raise SystemExit("Sporenwerk 1.99 battle wear: "+why)
def patch(file,old,new,reason):
    s=file.read_text(encoding="utf-8")
    require(s.count(old)==1,reason+" anchor occurrences "+str(s.count(old)))
    file.write_text(s.replace(old,new,1),encoding="utf-8")

s=MODEL.read_text(encoding="utf-8")
require("private final ModelPart[] coreIrisPetals;" in s and
        'this.shoulderArmorLeft = body.hasChild("shoulder_armor_left")' in s and
        'this.haunchArmorRight = body.hasChild("haunch_armor_right")' in s and
        "addFourPetalCoreIris(body, true);" in s,
        "existing 1.98 core, glow alignment and armor bones required")
patch(MODEL, "    private final ModelPart[] coreIrisPetals;",
"""    private final ModelPart[] coreIrisPetals;
    private final ModelPart[] armorFractureVeins;""",
"four cached fracture gems")

patch(MODEL,"        this.resonanceRibs = new ModelPart[] {",
"""        // One-time lookup, no per-frame recursion through the model tree.
        this.armorFractureVeins = new ModelPart[] {
                body.getChild("shoulder_armor_left").getChild("fracture_vein"),
                body.getChild("shoulder_armor_right").getChild("fracture_vein"),
                body.getChild("haunch_armor_left").getChild("fracture_vein"),
                body.getChild("haunch_armor_right").getChild("fracture_vein")
        };
        this.resonanceRibs = new ModelPart[] {""",
"bind new child in skin and emissive mesh at same anchor")

helper="""
    /**
     * 1.99 embedded fracture seams follow their parent shoulder/haunch
     * plates and grow more visible in the second half of a boss fight.
     * The same small UV island already contains hand-painted magenta-cyan
     * pixels, so there is no UV overwrite and no copyrighted reference art.
     */
    private static void addBattleWearVeins(PartDefinition body, boolean glowing) {
        String[] armor = {
                "shoulder_armor_left", "shoulder_armor_right",
                "haunch_armor_left", "haunch_armor_right"
        };
        for (int i = 0; i < armor.length; i++) {
            boolean shoulder = i < 2;
            // Top-facing inset stripe: unlike the surrounding basalt it
            // becomes fullbright only in the selective glow layer.
            CubeListBuilder gem = CubeListBuilder.create()
                    .texOffs(190, 192)
                    .addBox(-1.2F, shoulder ? -7.65F : -7.6F,
                            shoulder ? -4.6F : -4.1F,
                            2.4F, glowing ? 0.25F : 0.45F,
                            shoulder ? 8.2F : 7.4F);
            body.getChild(armor[i]).addOrReplaceChild("fracture_vein", gem,
                    PartPose.ZERO);
        }
    }

"""
patch(MODEL, "    @Override\n    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,",
      helper+"    @Override\n    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,",
      "skeleton-ready armor fracture geometry")

s=MODEL.read_text(encoding="utf-8")
returns=list(re.finditer(r"(?m)^        return LayerDefinition\.create\(mesh, 256, 256\);",s))
require(len(returns)==2,"need both original and fullbright 256x256 model layers")
for idx in (1,0):
    val="true" if idx else "false"
    s=s[:returns[idx].start()]+"        addBattleWearVeins(body, "+val+");\n"+s[returns[idx].start():]
MODEL.write_text(s,encoding="utf-8")

end="""        this.head.zRot = -this.body.zRot * 0.60F;"""
patch(MODEL,end,"""        this.head.zRot = -this.body.zRot * 0.60F;
        // 1.99 gradual battle wear tied to authoritative health, without
        // combat or hitbox changes. Both skin and glow follow identical poses.
        float hpRatio = entity.getHealth() / Math.max(1.0F, entity.getMaxHealth());
        float fracture = Mth.clamp((0.70F - hpRatio) / 0.45F, 0.0F, 1.0F);
        float crystalStress = Math.max(0.0F, Mth.sin(ageInTicks * 0.16F))
                * 0.028F * fracture;
        // Let the four heavy armor plates hinge visibly outward.
        if (this.shoulderArmorLeft != null) {
            this.shoulderArmorLeft.zRot -= fracture * 0.19F + crystalStress;
        }
        if (this.shoulderArmorRight != null) {
            this.shoulderArmorRight.zRot += fracture * 0.19F + crystalStress;
        }
        if (this.haunchArmorLeft != null) {
            this.haunchArmorLeft.zRot -= fracture * 0.12F + crystalStress * 0.6F;
        }
        if (this.haunchArmorRight != null) {
            this.haunchArmorRight.zRot += fracture * 0.12F + crystalStress * 0.6F;
        }
        for (int i = 0; i < this.armorFractureVeins.length; i++) {
            ModelPart vein = this.armorFractureVeins[i];
            vein.visible = fracture > 0.015F;
            float opening = 0.65F + fracture * 0.45F;
            vein.xScale = opening;
            vein.yScale = 1.0F;
            vein.zScale = opening;
        }""",
"end of boss setupAnim, after earlier armor + attack-state animations")

p=PIRSCHER.read_text(encoding="utf-8")
require("private final ModelPart rightTalonB;" in p and
        "this.thoraxShardLeft.zRot = -0.36F - shardFlare;" in p and
        "this.thoraxShardRight.yRot = -0.10F - shardFlare * 0.34F;" in p,
        "1.97 stalker claws, shards and hunt pose required")
patch(PIRSCHER,
"        this.thoraxShardRight.yRot = -0.10F - shardFlare * 0.34F;",
"""        this.thoraxShardRight.yRot = -0.10F - shardFlare * 0.34F;
        // 1.99 a visibly strained, uneven gait late in a stalker's fight.
        // Rendering-only: movement speed, health, drops, and attack timing
        // are unchanged. All angles use original vanilla leg swing as base.
        float stalkerHealth = entity.getHealth() / Math.max(1.0F, entity.getMaxHealth());
        float crystalFatigue = Mth.clamp((0.55F - stalkerHealth) / 0.40F, 0.0F, 1.0F);
        float unevenStep = Mth.sin(limbSwing * 0.6662F) * pace * crystalFatigue;
        this.leftLeg.xRot += unevenStep * 0.16F;
        this.rightLeg.xRot -= unevenStep * 0.08F;
        this.body.zRot = Mth.sin(limbSwing * 0.6662F) * pace * crystalFatigue * 0.055F;
        this.headCrystal.zRot = 0.26F + crystalFatigue
                * Mth.sin(ageInTicks * 0.13F) * 0.045F;
        float fatigueBreath = crystalFatigue * Math.max(0.0F,
                Mth.sin(ageInTicks * 0.17F)) * 0.045F;
        this.thoraxResonator.xScale += fatigueBreath;
        this.thoraxResonator.yScale += fatigueBreath;
        this.thoraxResonator.zScale += fatigueBreath;""",
"low-health visual gait and stressed crystal core")

render=RENDERER.read_text(encoding="utf-8")
require("float pulse = 0.76F + 0.12F" in render and
        "if (entity.isAggressive()) pulse = Math.min(1.0F, pulse + 0.12F);" in render,
        "selective fullbright renderer required")
patch(RENDERER,
"            if (entity.isAggressive()) pulse = Math.min(1.0F, pulse + 0.12F);",
"""            if (entity.isAggressive()) pulse = Math.min(1.0F, pulse + 0.12F);
            float healthRatio = entity.getHealth() / Math.max(1.0F, entity.getMaxHealth());
            float stress = net.minecraft.util.Mth.clamp((0.55F - healthRatio) / 0.40F, 0.0F, 1.0F);
            pulse = Math.min(1.0F, pulse + stress * 0.075F);""",
"stalker visible health-dependent crystal luminescence")

# Previous functionality tests remain valid. Keep moving versions and old
# README lookups forward, with the historical releases preserved in context.
for path in (ROOT/"tools").glob("test_*.py"):
    if path.name=="test_crystal_battle_wear_199.py": continue
    before=path.read_text(encoding="utf-8")
    after=before.replace("Aktueller Entwicklungsstand: 1.98.0",
                         "Aktueller Entwicklungsstand: 1.99.0")
    if "build.gradle" in before:
        after=after.replace(r"1\.98\.0",r"1\.99\.0")
        after=after.replace("artifact must be version 1.98.0",
                            "artifact must be version 1.99.0")
    after=after.replace('"Version 1.98.0" in readme and "Version 1.97.0" in readme',
                        '"Version 1.99.0" in readme and "Version 1.98.0" in readme')
    if after!=before:path.write_text(after,encoding="utf-8")
gradle=ROOT/"build.gradle";g,n=re.subn(
    r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
    "version = '1.99.0'",gradle.read_text(encoding="utf-8"),count=1)
require(n==1,"Gradle 1.99 bump missing")
gradle.write_text(g,encoding="utf-8")

p=ROOT/"README.md";r=p.read_text(encoding="utf-8")
old_head="**Aktueller Entwicklungsstand: 1.98.0 — Korrigierte Koloss-Leuchtlayer und sichtbar öffnender Kristallkern.**"
require(old_head in r,"1.98 generated source README headline")
r=r.replace(old_head,
    "**Aktueller Entwicklungsstand: 1.99.0 — Sichtbare Kristall-Kampfspuren und lebendige Monsterphasen.**",1)
new_current="""## Aktueller Entwicklungsschritt — 1.99.0

- **Kristallkoloss mit visuellem Kampfschaden:** Die vier vorhandenen schweren Panzerplatten an Schultern und Hüften klappen beim Verlust von Lebenspunkten allmählich weiter aus. Die Veränderung beginnt unter 70 % Gesundheit und erreicht bei 25 % die deutlichste Darstellung.
- **Echte freigelegte Kristalladern:** An jedem dieser vier vorhandenen Panzerknochen sitzt eine kleine selektiv leuchtende Kristallfuge. Die Fugen werden erst beim sichtbaren Auseinanderklappen eingeblendet. Skin- und Glow-Modell enthalten die gleichen Knochen, sodass weder die leuchtende Struktur noch die Rüstung an falscher Stelle sitzen.
- **Kristallpirscher mit Erschöpfungsbewegung:** Bei niedrigem Lebensstand verändert sich ausschließlich die Darstellung: leicht ungleichmäßige Schritte, ein nervöser Kopfkristall und stärkeres Pulsieren des Brustresonators. Spawn, Laufgeschwindigkeit, Angriffe und Gegenwehr bleiben unverändert.
- **Keine neuen Renderdateien erforderlich:** Bereits original gestaltete violett-cyanfarbene UV-Flächen werden verwendet; die bestehenden Minecraft-konformen 256×256- und 128×128-Texturatlanten bleiben unverändert und kompatibel.
- **Persistenz ohne Zusatzdaten:** Die visuelle Phase wird aus den bestehenden serverseitig synchronisierten Lebenspunkten abgeleitet und beim Laden automatisch korrekt dargestellt, ohne neue Save-Tags oder Netzwerknachrichten.
- **Keine Nachteile für den Spieler:** Keine Änderungen an Schadenswerten, Loot, Maschinen, Infektionskontrolle, Schutztechnologie, Endgame-Heilung oder bestehenden Bossangriffen. Alle neuen Modelleffekte laufen clientseitig.
- **Qualitätssicherung:** Eigene Regression für die vier gepaarten Frakturkristalle, deterministische HP-Schwellen, Animationen, Glow-Pfade sowie den vollständigen Forge- und Server-Build. Ein Minecraft-Client-Sichttest bleibt weiterhin erforderlich.

"""
require("## Aktueller Entwicklungsschritt — 1.98.0" in r,
        "previous development notes missing")
r=r.replace("## Aktueller Entwicklungsschritt — 1.98.0",
            new_current+"## Aktueller Entwicklungsschritt — 1.98.0",1)
release="""## Version 1.99.0 — Kristallpanzer zerbrechen sichtbar

- Vier animierte Schulter-/Hüftpanzer des Kolosses spreizen sich abhängig vom bereits vorhandenen Lebensstand. Darunter erscheinen vier echte, schmale Kristalladern, die im Skin- und selektiven Glow-Layer identisch verankert sind.
- Der Kristallpirscher zeigt bei niedriger Gesundheit ein vorsichtiges asymmetrisches Hinken, Kopfkristallzittern und erhöhte Herzresonanz, ohne Bewegungsgeschwindigkeit oder Angriffsregeln zu verändern.
- Keine neuen Netzwerkpakete, Hitboxen, Schadenswerte, Tick-Listener oder fremden Ressourcen. Client-Sichttest gegenüber den Originaldesigns noch offen.

"""
require("## Version 1.98.0 —" in r,"release history 1.98 missing")
r=r.replace("## Version 1.98.0 —",release+"## Version 1.98.0 —",1)
p.write_text(r,encoding="utf-8")
print("Sporenwerk 1.99 battle phase visuals installed: four real glowing armor fractures and injured Crystal Stalker motion.")
