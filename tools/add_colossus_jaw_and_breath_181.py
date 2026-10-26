#!/usr/bin/env python3
"""Version 1.81: articulated lower jaw and directional breath charge for the Crystal Colossus.

Built exclusively from original Forge 1.20.1 ModelPart geometry, synchronized boss state
and vanilla particles. Keeps existing entity registration, combat damage and loot unchanged.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ENTITY = ROOT / "src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java"


def require(value, description):
    if not value:
        raise SystemExit("Articulated Colossus jaw 1.81: " + description)


def replace_exact(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    require(text.count(old) == 1, label + " needs exactly one known source anchor")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Isolate the fixed lower mandible from the head's cuboids so that opening the mouth
# creates a physical gap instead of drawing a second jaw over a permanently closed one.
fixed_chin = """                        .texOffs(144, 32).addBox(-7.0F, -2.0F, -17.0F, 14.0F, 7.0F, 10.0F)
                        .texOffs(144, 52).addBox(-6.0F, 3.0F, -15.0F, 12.0F, 3.0F, 10.0F),"""
upper_skull = """                        .texOffs(144, 32).addBox(-7.0F, -2.0F, -17.0F, 14.0F, 7.0F, 10.0F),"""
replace_exact(MODEL, fixed_chin, upper_skull, "free the lower mandible from the skull")

# The original 1.59 armor is moved under the new hinge; the original head armor and
# existing 1.80 crown remain untouched. Local offsets preserve the closed-mouth pose.
static_armor = """        head.addOrReplaceChild("jaw_armor",
                CubeListBuilder.create().texOffs(144, 52)
                        .addBox(-7.0F, 1.0F, -18.0F, 14.0F, 4.0F, 12.0F)
                        .texOffs(176, 100).addBox(-5.0F, 3.0F, -19.0F, 10.0F, 2.5F, 9.0F),
                PartPose.ZERO);"""
articulated_armor = """        // 1.81 real jaw hinge: mouth opens around its rear attachment to the skull.
        PartDefinition lowerJaw = head.addOrReplaceChild("lower_jaw",
                CubeListBuilder.create().texOffs(144, 52)
                        .addBox(-6.0F, 1.0F, -9.0F, 12.0F, 3.0F, 10.0F),
                PartPose.offset(0.0F, 2.0F, -6.0F));
        lowerJaw.addOrReplaceChild("jaw_armor",
                CubeListBuilder.create().texOffs(144, 52)
                        .addBox(-7.0F, -1.0F, -12.0F, 14.0F, 4.0F, 12.0F)
                        .texOffs(176, 100).addBox(-5.0F, 1.0F, -13.0F, 10.0F, 2.5F, 9.0F),
                PartPose.ZERO);
        // Individually modeled crystal teeth are dark on the outside and light up
        // via tiny, separately aligned teeth on the full-bright model below.
        lowerJaw.addOrReplaceChild("lower_fang_left",
                CubeListBuilder.create().texOffs(176, 100)
                        .addBox(-5.7F, -4.5F, -12.7F, 2.3F, 4.0F, 2.6F),
                PartPose.ZERO);
        lowerJaw.addOrReplaceChild("lower_fang_right",
                CubeListBuilder.create().texOffs(176, 100)
                        .addBox(3.4F, -4.5F, -12.7F, 2.3F, 4.0F, 2.6F),
                PartPose.ZERO);"""
replace_exact(MODEL, static_armor, articulated_armor, "move old jaw armor onto new hinge")

# Reparent the existing mouth light onto the same jaw. Both layers use the same pivot.
fixed_glow = """        head.addOrReplaceChild("mouth_glow",
                CubeListBuilder.create().texOffs(200, 44).addBox(-4.0F, 2.5F, -17.8F, 8.0F, 1.2F, 1.0F),
                PartPose.ZERO);"""
hinged_glow = """        // 1.81 matching emissive hinge; the light follows the moving lower mandible.
        PartDefinition lowerJawGlow = head.addOrReplaceChild("lower_jaw",
                CubeListBuilder.create(), PartPose.offset(0.0F, 2.0F, -6.0F));
        lowerJawGlow.addOrReplaceChild("mouth_glow",
                CubeListBuilder.create().texOffs(200, 44)
                        .addBox(-4.0F, 0.5F, -11.8F, 8.0F, 1.2F, 1.0F),
                PartPose.ZERO);
        lowerJawGlow.addOrReplaceChild("lower_fang_glow_left",
                CubeListBuilder.create().texOffs(224, 44)
                        .addBox(-5.15F, -4.1F, -12.5F, 1.2F, 3.3F, 1.5F),
                PartPose.ZERO);
        lowerJawGlow.addOrReplaceChild("lower_fang_glow_right",
                CubeListBuilder.create().texOffs(224, 44)
                        .addBox(3.95F, -4.1F, -12.5F, 1.2F, 3.3F, 1.5F),
                PartPose.ZERO);"""
replace_exact(MODEL, fixed_glow, hinged_glow, "attach emissive mouth and teeth to matching hinge")

field = """    private final ModelPart crystalCrownRight;"""
replace_exact(MODEL, field, field + """
    private final ModelPart lowerJaw;""", "register new joint")

ctor = """        this.crystalCrownRight = head.hasChild("crystal_crown_right") ? head.getChild("crystal_crown_right") : null;"""
replace_exact(MODEL, ctor, ctor + """
        this.lowerJaw = head.hasChild("lower_jaw") ? head.getChild("lower_jaw") : null;""",
              "bind jaw in normal and emissive model constructors")

# Existing client-synchronized attack tick countdown is 48 -> 0 during breath windup.
# Animate the 48-tick opening directly and avoid resetting jaw angle between frames.
anim_anchor = """        if (this.crystalCrownRight != null) {
            this.crystalCrownRight.zRot = 0.52F + crownBreathing + crownFlare;
            this.crystalCrownRight.yRot = 0.08F + crownFlare * 0.16F;
            this.crystalCrownRight.xScale = crownPulse;
            this.crystalCrownRight.yScale = crownPulse;
            this.crystalCrownRight.zScale = crownPulse;
        }"""
anim_patch = anim_anchor + """

        // 1.81 legible windup: the physical gap and its inner glow open together.
        // No new networking: both model layers read the synced ATTACK_STATE / ATTACK_TICKS.
        if (this.lowerJaw != null) {
            float jawOpening = 0.02F + Math.max(0.0F, Mth.sin(ageInTicks * 0.11F)) * 0.015F;
            int attackState = entity.getAttackState();
            if (attackState == MutagenkolossEntity.ATTACK_BREATH) {
                float elapsed = Mth.clamp((48.0F - entity.getAttackTicks()) / 48.0F, 0.0F, 1.0F);
                float anticipation = elapsed * elapsed * (3.0F - 2.0F * elapsed);
                jawOpening = 0.12F + 0.66F * anticipation
                        + Mth.sin(ageInTicks * 0.30F) * 0.022F;
            } else if (attackState == MutagenkolossEntity.ATTACK_AWAKENING) {
                jawOpening = 0.25F + Math.max(0.0F, Mth.sin(ageInTicks * 0.38F)) * 0.16F;
            } else if (attackState == MutagenkolossEntity.ATTACK_STOMP) {
                jawOpening = 0.12F;
            }
            this.lowerJaw.xRot = Mth.clamp(jawOpening, 0.0F, 0.80F);
            this.lowerJaw.yRot = 0.0F;
            this.lowerJaw.zRot = 0.0F;
        }"""
replace_exact(MODEL, anim_anchor, anim_patch, "apply directional jaw windup on both layers")

# A cloud centered in the body reads as pollution; move the existing warning particles
# to the actual muzzle, tightening the emission cone as the windup approaches release.
old_cloud = """        if (state == ATTACK_BREATH) {
            serverLevel.sendParticles(ParticleTypes.DRAGON_BREATH,
                    this.getX(), this.getY() + 2.2D, this.getZ(), 12,
                    0.45D, 0.35D, 0.45D, 0.02D);
        } else {"""
charged_muzzle = """        if (state == ATTACK_BREATH) {
            // 1.81 recognizable muzzle charging; particles narrow as the jaw opens.
            Vec3 facing = this.getLookAngle().normalize();
            Vec3 mouthOrigin = this.position().add(0.0D, 2.15D, 0.0D)
                    .add(facing.scale(1.65D));
            double charge = Math.min(1.0D, Math.max(0.0D,
                    (48.0D - this.attackTicksLeft) / 48.0D));
            double spread = 0.55D - charge * 0.35D;
            serverLevel.sendParticles(ParticleTypes.DRAGON_BREATH,
                    mouthOrigin.x, mouthOrigin.y, mouthOrigin.z, 7 + (int) (charge * 7),
                    spread, spread * 0.8D, spread, 0.015D);
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    mouthOrigin.x, mouthOrigin.y, mouthOrigin.z, 3,
                    spread * 0.45D, spread * 0.45D, spread * 0.45D, 0.02D);
        } else {"""
replace_exact(ENTITY, old_cloud, charged_muzzle, "align windup particles to the mouth")

# Verify the public gameplay contract remains stable: no damage/range edits.
entity = ENTITY.read_text(encoding="utf-8")
require("private void performCrystalBreath()" in entity and "victim.hurt" in entity,
        "the original damaging attack must remain active")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "new warning particles must not force-load terrain")

# Advance source-bundle regression versions, preserving historical feature checks.
for path in (ROOT / "tools").glob("test_*.py"):
    if path.name == "test_colossus_jaw_and_breath_181.py":
        continue
    source = path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.80.0",
                             "Aktueller Entwicklungsstand: 1.81.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.80\.0", r"1\.81\.0")
        updated = updated.replace("artifact must be version 1.80.0",
                                  "artifact must be version 1.81.0")
    updated = updated.replace(
        '"Version 1.80.0" in readme and "Version 1.79.0" in readme',
        '"Version 1.81.0" in readme and "Version 1.80.0" in readme')
    if updated != source:
        path.write_text(updated, encoding="utf-8")

gradle = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.81.0'", gradle.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle version 1.81.0")
gradle.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.81.0

- **Beweglicher Unterkiefer:** Der Kristallkoloss erhält ein echtes Kiefergelenk statt einer fest am Schädel liegenden Unterkieferfläche. Die bisherigen Gesteinsplatten wurden an den beweglichen Teil gebunden.
- **Leuchtende Kristallzähne:** Kleine fangartige Kristalle und das Maulleuchten bewegen sich in einem deckungsgleichen Emissiv-Modell mit dem echten Kiefer.
- **Erkennbarer Kristallatem:** Über die bestehende, synchronisierte 48-Tick-Angriffsphase öffnet der Boss sein Maul zunehmend. Die bisherigen Atem-Partikel entstehen jetzt vor seiner Schnauze und verdichten sich während des Aufladens, statt im Rumpf zu erscheinen.
- **Zusätzliche Phasenanimation:** Bei der Verwandlung reißt der Koloss das Maul stoßweise weiter auf; bei Stampfangriffen spannt sich der Kiefer.
- **Sicherer Ausbau:** Forge-ModelParts ohne zusätzliche Animationsbibliothek, bestehende Schadens- und Reichweitenlogik unverändert, keine neuen Chunkzugriffe, DE/EN-Texturassets beibehalten. Regressionen, Forge-Build und Server-Smoke-Test prüfen die Integration.

"""
if "## Aktueller Entwicklungsschritt — 1.81.0" not in readme:
    anchor = "## Aktueller Entwicklungsschritt — 1.80.0"
    require(anchor in readme, "missing 1.80 development step")
    readme = readme.replace(anchor, current + anchor, 1)
release = """## Version 1.81.0 — Beweglicher Kristallkiefer und gerichtete Atemladung

- **Neues Gelenk:** Die untere Schnauzengeometrie des Kristallkolosses ist nicht länger fest in den Schädel eingebaut. Bestehender Kieferpanzer und neue Kristallzähne bewegen sich gemeinsam.
- **Synchronisierte Leuchtgeometrie:** Maulleuchten und Zähne folgen dem Kiefer auf dem Full-Bright-Layer, während Wangenpanzer und die Kristallkrone an ihren alten Positionen erhalten bleiben.
- **Angriffe mit Vorwarnung:** Während der bestehenden 48 Ticks Kristallatem wächst der Maulwinkel von leichter Spannung zur breiten Öffnung. Die Warnpartikel laden sichtbar an der Schnauze auf, bevor der unveränderte Strahl ausgelöst wird.
- **Weitere Ausdrucksformen:** Ruhige Atembewegung, verstärktes Aufreißen beim Erwachen, angespanntes Maul beim Stampfen.
- **Technische Prüfung:** Eigene neue Regression für Geometrie, Phasenanimation, Ladungsformel, getrennte Modell-Layer, Assets und Metadaten plus Forge-JAR und dedizierter Serverstart. Eine tatsächliche Client-Bildkontrolle ist weiterhin erforderlich.

"""
if "## Version 1.81.0 — Beweglicher Kristallkiefer und gerichtete Atemladung" not in readme:
    anchor = "## Version 1.80.0 —"
    require(anchor in readme, "missing 1.80 release section")
    readme = readme.replace(anchor, release + anchor, 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.80.0 — lebendige Kristallkrone für den Kristallkoloss.**",
    "**Aktueller Entwicklungsstand: 1.81.0 — beweglicher Kristallkiefer und aufladender Kristallatem.**")
require("Aktueller Entwicklungsstand: 1.81.0" in readme,
        "README still points to previous version")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.81.0 generated: articulated jaw, aligned glow fangs, attack-state opening and directed crystal-breath charge.")
