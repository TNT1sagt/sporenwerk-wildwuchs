#!/usr/bin/env python3
"""1.61.0 heartbeat animation for the reference-directed Crystal Colossus core."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Colossus visual 1.61: " + message)


def patch(path, old, new, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return
    count = source.count(old)
    require(count == 1, f"{label}: expected one source anchor, got {count}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# The regular and emissive models are separate ModelPart trees. Optional child references
# let the same animation code drive chest_core in the skin layer and core_glow in the eyes layer.
field_anchor = '''    private final ModelPart body;
    private final ModelPart head;'''
field_new = '''    private final ModelPart body;
    private final ModelPart head;
    private final ModelPart chestCore;
    private final ModelPart chestGlow;
    private final ModelPart ribCrystalLeft;
    private final ModelPart ribCrystalRight;
    private final ModelPart flankCrystalLeft;
    private final ModelPart flankCrystalRight;
    private final ModelPart shoulderCrystalLeft;
    private final ModelPart shoulderCrystalRight;'''
patch(MODEL, field_anchor, field_new, "private final ModelPart chestCore;", "pulse part fields")

ctor_anchor = '''        this.body = root.getChild("body");
        this.head = body.getChild("head");'''
ctor_new = '''        this.body = root.getChild("body");
        this.head = body.getChild("head");
        this.chestCore = body.hasChild("chest_core") ? body.getChild("chest_core") : null;
        this.chestGlow = body.hasChild("core_glow") ? body.getChild("core_glow") : null;
        this.ribCrystalLeft = body.hasChild("rib_crystal_left") ? body.getChild("rib_crystal_left") : null;
        this.ribCrystalRight = body.hasChild("rib_crystal_right") ? body.getChild("rib_crystal_right") : null;
        this.flankCrystalLeft = body.hasChild("flank_crystal_left") ? body.getChild("flank_crystal_left") : null;
        this.flankCrystalRight = body.hasChild("flank_crystal_right") ? body.getChild("flank_crystal_right") : null;
        this.shoulderCrystalLeft = body.hasChild("shoulder_crystal_left") ? body.getChild("shoulder_crystal_left") : null;
        this.shoulderCrystalRight = body.hasChild("shoulder_crystal_right") ? body.getChild("shoulder_crystal_right") : null;'''
patch(MODEL, ctor_anchor, ctor_new, "this.chestCore = body.hasChild", "pulse part references")

anim_anchor = '''        this.head.xRot = headPitch * Mth.DEG_TO_RAD * 0.42F;
        this.head.yRot = netHeadYaw * Mth.DEG_TO_RAD * 0.42F;
        this.head.zRot = 0.0F;'''
anim_new = '''        this.head.xRot = headPitch * Mth.DEG_TO_RAD * 0.42F;
        this.head.yRot = netHeadYaw * Mth.DEG_TO_RAD * 0.42F;
        this.head.zRot = 0.0F;

        // A double-beat pulse makes the core feel alive in idle, then visibly surges before boss attacks.
        float heartbeat = Math.max(0.0F, Mth.sin(ageInTicks * 0.19F));
        float afterBeat = Math.max(0.0F, Mth.sin(ageInTicks * 0.19F + 1.35F));
        float pulseScale = 1.0F + 0.012F + heartbeat * 0.026F + afterBeat * 0.014F;
        int pulseState = entity.getAttackState();
        int pulseTicks = entity.getAttackTicks();
        if (pulseState == MutagenkolossEntity.ATTACK_BREATH) {
            pulseScale += 0.035F + (0.5F + 0.5F * Mth.sin(pulseTicks * 0.36F)) * 0.035F;
        } else if (pulseState == MutagenkolossEntity.ATTACK_AWAKENING) {
            pulseScale += 0.055F + (0.5F + 0.5F * Mth.sin(ageInTicks * 0.52F)) * 0.045F;
        } else if (pulseState == MutagenkolossEntity.ATTACK_STOMP && pulseTicks > 12) {
            pulseScale += 0.025F;
        }
        if (this.chestCore != null) {
            this.chestCore.xScale = pulseScale;
            this.chestCore.yScale = pulseScale;
            this.chestCore.zScale = 1.0F + (pulseScale - 1.0F) * 0.50F;
            this.chestCore.zRot = Mth.sin(ageInTicks * 0.045F) * 0.012F;
        }
        if (this.chestGlow != null) {
            float haloScale = pulseScale + 0.035F;
            this.chestGlow.xScale = haloScale;
            this.chestGlow.yScale = haloScale;
            this.chestGlow.zScale = 1.02F + (pulseScale - 1.0F) * 0.50F;
            this.chestGlow.zRot = Mth.sin(ageInTicks * 0.045F) * 0.012F;
        }
        float ribSway = Mth.sin(ageInTicks * 0.075F) * 0.028F;
        if (this.ribCrystalLeft != null) {
            this.ribCrystalLeft.zRot = -0.42F + ribSway;
            this.ribCrystalLeft.yRot = Mth.sin(ageInTicks * 0.055F) * 0.035F;
        }
        if (this.ribCrystalRight != null) {
            this.ribCrystalRight.zRot = 0.42F - ribSway;
            this.ribCrystalRight.yRot = -Mth.sin(ageInTicks * 0.055F) * 0.035F;
        }
        if (this.flankCrystalLeft != null) {
            this.flankCrystalLeft.zRot = -0.32F + ribSway * 0.7F;
        }
        if (this.flankCrystalRight != null) {
            this.flankCrystalRight.zRot = 0.32F - ribSway * 0.7F;
        }
        if (this.shoulderCrystalLeft != null) {
            this.shoulderCrystalLeft.zRot = -0.62F + ribSway;
        }
        if (this.shoulderCrystalRight != null) {
            this.shoulderCrystalRight.zRot = 0.62F - ribSway;
        }'''
patch(MODEL, anim_anchor, anim_new, "float pulseScale = 1.0F", "synchronised chest pulse")

# Dorsal crystal groups respond to the same pulse and flare slightly more during the awakening.
spine_anchor = '''        for (int i = 0; i < this.spines.length; i++) {
            this.spines[i].zRot = Mth.sin(ageInTicks * 0.045F + i * 0.74F) * 0.035F;
        }'''
spine_new = '''        for (int i = 0; i < this.spines.length; i++) {
            this.spines[i].zRot = Mth.sin(ageInTicks * 0.045F + i * 0.74F) * 0.035F;
            float spinePulse = 1.0F + heartbeat * 0.018F;
            if (entity.getAttackState() == MutagenkolossEntity.ATTACK_AWAKENING) {
                spinePulse += 0.025F + 0.025F * (0.5F + 0.5F * Mth.sin(ageInTicks * 0.52F + i * 0.3F));
            }
            this.spines[i].xScale = spinePulse;
            this.spines[i].yScale = spinePulse;
            this.spines[i].zScale = 1.0F + (spinePulse - 1.0F) * 0.5F;
        }'''
patch(MODEL, spine_anchor, spine_new, "float spinePulse = 1.0F", "dorsal crystal resonance")

# Advance Gradle/release assertions written into the clean snapshot by the preceding generators.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.60.0",
                             "Aktueller Entwicklungsstand: 1.61.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.60\.0", r"1\.61\.0")
        updated = updated.replace("artifact must be version 1.60.0",
                                  "artifact must be version 1.61.0")
    updated = updated.replace(
        '"Version 1.60.0" in readme and "Version 1.59.0" in readme',
        '"Version 1.61.0" in readme and "Version 1.60.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.61.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.61.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.61.0 — Pulsierender Kristallkern und resonierende Kristallrüstung

- **Lebendiger Doppel-Puls:** Der Brustkern pulsiert dauerhaft sichtbar mit zwei versetzten Impulsen; die getrennte Full-Bright-Schicht pulsiert etwas stärker und bildet einen sauberen Lichtsaum.
- **Reaktion auf Bossaktionen:** Beim Aufladen des Kristallatems verstärkt sich der Kernpuls. Während des Erwachens der zweiten Phase leuchten Kern und Rückenstacheln deutlich stärker; der Stampfangriff lässt den Kern kurz anschwellen.
- **Rüstung bewegt sich mit dem Kern:** Seitliche Rippenkristalle und Schulter-/Flankenkristalle schwingen subtil gegenläufig. So wirkt der Brustkern in die Panzerform eingebaut statt wie ein aufgeklebtes Leuchtrechteck.
- **Synchrone Haupt- und Glow-Geometrie:** Derselbe Animationscode erkennt die Haut- und Full-Bright-Modellebene getrennt und animiert beide anhand derselben Tick-Zeit.
- **Regressionen:** Neue Checks prüfen Doppel-Puls, attackabhängige Verstärkung, beide Modell-Layer und die Animation der Kristallrüstung.

Die Änderungen sind clientseitige Modellanimationen; Bosslogik, Kampfwerte und Survival-Ritual werden dadurch nicht verändert. Die tatsächliche Bildwirkung muss im Minecraft-Client beurteilt werden.

"""
if "## Version 1.61.0 — Pulsierender Kristallkern und resonierende Kristallrüstung" not in readme:
    marker = "## Version 1.60.0 — Referenz-Brustkern und violett-cyanfarbene Facetten"
    idx = readme.find(marker)
    if idx < 0:
        idx = readme.find("\n## ")
        if idx >= 0:
            idx += 1
        else:
            idx = len(readme)
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.61.0 — pulsierender violett-cyanfarbener Brustkern und resonierende Kristallrüstung.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus:
    readme = readme.replace(focus[0], "## Aktueller Schwerpunkt — 1.61.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Installed 1.61.0 heartbeat animation, attack-driven core surges, synchronized glow scaling and crystal armour resonance.")
