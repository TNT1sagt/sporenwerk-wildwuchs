#!/usr/bin/env python3
"""Give the Crystal Colossus an animated, three-point crystal crown and cheek armor (1.80.0).

All geometry and animations are original Forge ModelPart shapes. The existing 256x256
Sporenwerk textures are reused, without copying reference-mod assets or their code.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Crown 1.80: " + message)


def patch(old, new, sentinel, label):
    source = MODEL.read_text(encoding="utf-8")
    if sentinel in source:
        return
    require(source.count(old) == 1, label + " anchor must appear exactly once")
    MODEL.write_text(source.replace(old, new, 1), encoding="utf-8")


def insert_before_layer_return(layer, code, sentinel):
    source = MODEL.read_text(encoding="utf-8")
    if sentinel in source:
        return
    returns = list(re.finditer(r"(?m)^        return LayerDefinition\.create\(mesh, 256, 256\);", source))
    require(len(returns) == 2, "expected separate 256x256 skin and emissive layers")
    at = returns[layer].start()
    MODEL.write_text(source[:at] + code + "\n" + source[at:], encoding="utf-8")


# The crown is wider than the skull and articulated independently of its head.
# Three stepped tiers form each projecting crystal blade; sideplates are dark stone.
# Existing violet/cyan crystal UVs and 1.62 armor UVs keep the material coherent.
skin = """        // 1.80 crystalline crown: mirror-paired detachable silhouette above each cheek.
        PartDefinition crownLeft = head.addOrReplaceChild("crystal_crown_left",
                CubeListBuilder.create().texOffs(100, 32)
                        .addBox(-3.5F, -4.0F, -4.0F, 7.0F, 7.0F, 8.0F),
                PartPose.offsetAndRotation(-12.0F, -3.0F, 3.0F, -0.15F, -0.08F, -0.52F));
        crownLeft.addOrReplaceChild("lower_blade",
                CubeListBuilder.create().texOffs(96, 176)
                        .addBox(-2.6F, -12.0F, -3.2F, 5.2F, 9.0F, 6.4F),
                PartPose.ZERO);
        crownLeft.addOrReplaceChild("middle_blade",
                CubeListBuilder.create().texOffs(104, 176)
                        .addBox(-1.8F, -20.0F, -2.4F, 3.6F, 8.0F, 4.8F),
                PartPose.ZERO);
        crownLeft.addOrReplaceChild("blade_tip",
                CubeListBuilder.create().texOffs(112, 176)
                        .addBox(-0.9F, -27.0F, -1.1F, 1.8F, 7.0F, 2.2F),
                PartPose.ZERO);

        PartDefinition crownRight = head.addOrReplaceChild("crystal_crown_right",
                CubeListBuilder.create().texOffs(100, 32)
                        .addBox(-3.5F, -4.0F, -4.0F, 7.0F, 7.0F, 8.0F),
                PartPose.offsetAndRotation(12.0F, -3.0F, 3.0F, -0.15F, 0.08F, 0.52F));
        crownRight.addOrReplaceChild("lower_blade",
                CubeListBuilder.create().texOffs(128, 176)
                        .addBox(-2.6F, -12.0F, -3.2F, 5.2F, 9.0F, 6.4F),
                PartPose.ZERO);
        crownRight.addOrReplaceChild("middle_blade",
                CubeListBuilder.create().texOffs(136, 176)
                        .addBox(-1.8F, -20.0F, -2.4F, 3.6F, 8.0F, 4.8F),
                PartPose.ZERO);
        crownRight.addOrReplaceChild("blade_tip",
                CubeListBuilder.create().texOffs(144, 176)
                        .addBox(-0.9F, -27.0F, -1.1F, 1.8F, 7.0F, 2.2F),
                PartPose.ZERO);

        // The jaw needs a solid mineral transition; otherwise the crown looks glued on.
        head.addOrReplaceChild("cheek_armor_left",
                CubeListBuilder.create().texOffs(32, 224)
                        .addBox(-3.5F, -4.0F, -7.0F, 7.0F, 6.0F, 11.0F)
                        .texOffs(80, 224)
                        .addBox(-2.6F, -5.5F, -6.0F, 5.2F, 2.0F, 7.0F),
                PartPose.offsetAndRotation(-9.0F, 0.0F, -2.0F, 0.08F, -0.12F, -0.15F));
        head.addOrReplaceChild("cheek_armor_right",
                CubeListBuilder.create().texOffs(32, 224)
                        .addBox(-3.5F, -4.0F, -7.0F, 7.0F, 6.0F, 11.0F)
                        .texOffs(80, 224)
                        .addBox(-2.6F, -5.5F, -6.0F, 5.2F, 2.0F, 7.0F),
                PartPose.offsetAndRotation(9.0F, 0.0F, -2.0F, 0.08F, 0.12F, 0.15F));"""
insert_before_layer_return(0, skin, "1.80 crystalline crown:")

# Keep the glow structure on the same moving model bones as the physical crest,
# but only light the inner crystal blades: do not full-bright the heavy armor sockets.
glow = """        // 1.80 crown glow uses the same head pivots to avoid emissive-layer drift.
        PartDefinition crownGlowLeft = head.addOrReplaceChild("crystal_crown_left",
                CubeListBuilder.create(),
                PartPose.offsetAndRotation(-12.0F, -3.0F, 3.0F, -0.15F, -0.08F, -0.52F));
        crownGlowLeft.addOrReplaceChild("lower_blade",
                CubeListBuilder.create().texOffs(96, 176)
                        .addBox(-1.55F, -11.7F, -1.9F, 3.1F, 8.5F, 3.8F),
                PartPose.ZERO);
        crownGlowLeft.addOrReplaceChild("middle_blade",
                CubeListBuilder.create().texOffs(104, 176)
                        .addBox(-1.0F, -19.8F, -1.3F, 2.0F, 7.6F, 2.6F),
                PartPose.ZERO);
        crownGlowLeft.addOrReplaceChild("blade_tip",
                CubeListBuilder.create().texOffs(112, 176)
                        .addBox(-0.7F, -26.7F, -0.8F, 1.4F, 6.6F, 1.6F),
                PartPose.ZERO);

        PartDefinition crownGlowRight = head.addOrReplaceChild("crystal_crown_right",
                CubeListBuilder.create(),
                PartPose.offsetAndRotation(12.0F, -3.0F, 3.0F, -0.15F, 0.08F, 0.52F));
        crownGlowRight.addOrReplaceChild("lower_blade",
                CubeListBuilder.create().texOffs(128, 176)
                        .addBox(-1.55F, -11.7F, -1.9F, 3.1F, 8.5F, 3.8F),
                PartPose.ZERO);
        crownGlowRight.addOrReplaceChild("middle_blade",
                CubeListBuilder.create().texOffs(136, 176)
                        .addBox(-1.0F, -19.8F, -1.3F, 2.0F, 7.6F, 2.6F),
                PartPose.ZERO);
        crownGlowRight.addOrReplaceChild("blade_tip",
                CubeListBuilder.create().texOffs(144, 176)
                        .addBox(-0.7F, -26.7F, -0.8F, 1.4F, 6.6F, 1.6F),
                PartPose.ZERO);"""
insert_before_layer_return(1, glow, "1.80 crown glow uses")

field_old = """    private final ModelPart haunchArmorRight;"""
field_new = field_old + """
    private final ModelPart crystalCrownLeft;
    private final ModelPart crystalCrownRight;"""
patch(field_old, field_new, "private final ModelPart crystalCrownLeft;", "crown references")

ctor_old = """        this.haunchArmorRight = body.hasChild("haunch_armor_right") ? body.getChild("haunch_armor_right") : null;"""
ctor_new = ctor_old + """
        this.crystalCrownLeft = head.hasChild("crystal_crown_left") ? head.getChild("crystal_crown_left") : null;
        this.crystalCrownRight = head.hasChild("crystal_crown_right") ? head.getChild("crystal_crown_right") : null;"""
patch(ctor_old, ctor_new, "this.crystalCrownLeft =", "crown skin+glow constructor")

anim_old = """        if (this.haunchArmorRight != null) {
            this.haunchArmorRight.zRot = 0.10F - armorShift * 0.55F;
        }"""
anim_new = anim_old + """

        // Synchronized, state-reactive crystallization; both model layers use setupAnim.
        // Reset to known base rotations on every call so animation states cannot accumulate.
        float crownBreathing = Mth.sin(ageInTicks * 0.065F) * 0.025F;
        float crownFlare = entity.getAttackState() == MutagenkolossEntity.ATTACK_AWAKENING
                ? 0.20F : entity.getAttackState() == MutagenkolossEntity.ATTACK_BREATH
                ? 0.11F : 0.0F;
        float crownPulse = 1.0F + Math.max(0.0F, Mth.sin(ageInTicks * 0.19F)) * 0.025F;
        if (entity.getAttackState() == MutagenkolossEntity.ATTACK_AWAKENING) {
            crownPulse += 0.09F * (0.5F + 0.5F * Mth.sin(ageInTicks * 0.42F));
        }
        if (this.crystalCrownLeft != null) {
            this.crystalCrownLeft.zRot = -0.52F - crownBreathing - crownFlare;
            this.crystalCrownLeft.yRot = -0.08F - crownFlare * 0.16F;
            this.crystalCrownLeft.xScale = crownPulse;
            this.crystalCrownLeft.yScale = crownPulse;
            this.crystalCrownLeft.zScale = crownPulse;
        }
        if (this.crystalCrownRight != null) {
            this.crystalCrownRight.zRot = 0.52F + crownBreathing + crownFlare;
            this.crystalCrownRight.yRot = 0.08F + crownFlare * 0.16F;
            this.crystalCrownRight.xScale = crownPulse;
            this.crystalCrownRight.yScale = crownPulse;
            this.crystalCrownRight.zScale = crownPulse;
        }"""
patch(anim_old, anim_new, "float crownBreathing = Mth.sin", "crown idle and attack animation")

# Advance only current-version tests, preserving explicit historical checks and scripts.
for path in (ROOT / "tools").glob("test_*.py"):
    if path.name == "test_colossus_crystal_crown_180.py":
        continue
    source = path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.79.0",
                             "Aktueller Entwicklungsstand: 1.80.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.79\.0", r"1\.80\.0")
        updated = updated.replace("artifact must be version 1.79.0",
                                  "artifact must be version 1.80.0")
    updated = updated.replace(
        '"Version 1.79.0" in readme and "Version 1.78.0" in readme',
        '"Version 1.80.0" in readme and "Version 1.79.0" in readme')
    if updated != source:
        path.write_text(updated, encoding="utf-8")

gradle = ROOT / "build.gradle"
current, changed = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                          "version = '1.80.0'", gradle.read_text(encoding="utf-8"), count=1)
require(changed == 1, "could not update Gradle mod version")
gradle.write_text(current, encoding="utf-8")

readme = ROOT / "README.md"
source = readme.read_text(encoding="utf-8")
current_section = """## Aktueller Entwicklungsschritt — 1.80.0

- **Kristallkoloss: mehr als nur eine Textur:** Zwei weit ausgreifende, dreistufige Kristallkronen flankieren jetzt den Kopf. Dunkle Wangenpanzer verbinden sie sichtbar mit Schädel und Hals.
- **Getrennte, deckungsgleiche Leuchtschicht:** Die neuen Kristalle besitzen innere Emissiv-Geometrie, während ihre dunklen Gesteinsfassungen unbeleuchtet bleiben. Haupt- und Glow-Layer verwenden dieselben Knochenpositionen.
- **Bewegte Anatomie:** Beide Kristallflügel atmen subtil im Leerlauf, fächern bei Atemangriffen auf und entfalten sich stärker beim Erwachen. Jede Animation setzt ihre Drehungen neu und wird auf Client und Glow-Layer identisch berechnet.
- **Eigene Gestaltung:** Die Forge-ModelParts und Bewegungen sind neu für Sporenwerk erstellt. Die beiden hochgeladenen Fremdmods wurden nur hinsichtlich technischer Struktur, Animationsumfang und Texturdichte untersucht; ihre Ressourcen werden nicht übernommen.
- **Qualität:** Eine eigene Regression prüft beide Modellbäume, Animation, Angriffsphasen, Versionsstand und Ressourcen. Der Forge-Build und der Serverstart sichern die technische Integration; die tatsächliche Bildwirkung muss im Minecraft-Client geprüft werden.

"""
if "## Aktueller Entwicklungsschritt — 1.80.0" not in source:
    anchor = "## Aktueller Entwicklungsschritt — 1.79.0"
    require(anchor in source, "could not find previous current development section")
    source = source.replace(anchor, current_section + anchor, 1)
release = """## Version 1.80.0 — Kristallkoloss: lebendige Kristallkrone

- **Neue Silhouette:** Spiegelbildliche, jeweils dreistufige Kristallklingen ragen aus der Kopfpartie und werden durch dunkle Wangenpanzer verankert.
- **Echte Gelenke:** Beide Kristallkronen besitzen eigene ModelParts und bewegen sich unabhängig vom Kopf. Der bestehende Leucht-Layer ist geometrisch ausgerichtet und beleuchtet nur die inneren Kristallflächen.
- **Kampfbezogene Animation:** Eine sanfte Idle-Atmung geht bei Kristallatem in ein sichtbares Auffächern und beim Erwachen in eine deutlich größere Krystallresonanz über.
- **Leistungsbewusst:** Die Animation basiert auf der vorhandenen synchronisierten Boss-Zustandsvariable; es gibt keinen neuen Tick-Loop, kein Shader-Framework und keine zusätzlich erzwungenen Chunks.
- **Visuelle Referenz:** Belowland und The Wonderland dienten ausschließlich als Analysemaßstab für hochwertige Modelldichte und Animationsstruktur. Keine fremden Modelle, Texturen oder Animationen sind im Mod enthalten.
- **Prüfung:** Regressionen, Forge-JAR, unabhängige Emissiv-Layer und dedizierter Serverstart; manuelle Sicht- und Kampfprüfung im Client weiterhin erforderlich.

"""
if "## Version 1.80.0 — Kristallkoloss: lebendige Kristallkrone" not in source:
    anchor = "## Version 1.79.0 —"
    require(anchor in source, "missing 1.79 release notes")
    source = source.replace(anchor, release + anchor, 1)
source = source.replace("**Aktueller Entwicklungsstand: 1.79.0 — Automatischer Pflanzenreste-Kreislauf.**",
                        "**Aktueller Entwicklungsstand: 1.80.0 — lebendige Kristallkrone für den Kristallkoloss.**")
require("Aktueller Entwicklungsstand: 1.80.0" in source, "README headline not updated")
readme.write_text(source, encoding="utf-8")
print("Sporenwerk 1.80.0 generated: mirrored multi-segment crown geometry, dark cheek armor, synchronized emissive bones and boss-state animation.")
