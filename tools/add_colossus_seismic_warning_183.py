#!/usr/bin/env python3
"""Give Crystal Colossus stomps a bounded shockwave warning and jump-dodge counterplay (1.83.0).

This patch modifies the existing synchronized boss attack cycle. It adds no new
block changes, ticking capability, biome dependencies, client assets, or chunk loads.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ENTITY = SRC / "entity/MutagenkolossEntity.java"


def require(value, description):
    if not value:
        raise SystemExit("Colossus seismic warning 1.83: " + description)


def replace_exact(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(source.count(old) == 1,
            f"{label}: expected one source anchor, found {source.count(old)}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# The ring is drawn from its attack radius and synced countdown, not from unreliable
# client-side estimates. Three warning pulses (36, 24, 12) are visible on a level floor
# and don't run on every entity tick. Particle positions don't access terrain chunks.
old_warning = """        } else {
            serverLevel.sendParticles(ParticleTypes.CRIT,
                    this.getX(), this.getY() + 0.4D, this.getZ(), 18,
                    1.0D, 0.16D, 1.0D, 0.08D);
        }
    }

    private void releaseAttack(int state) {"""
new_warning = """        } else if (state == ATTACK_STOMP || state == ATTACK_AWAKENING) {
            // 1.83 three radial danger-ring pulses before the already-existing impact.
            // The size matches the actual normal or empowered damaging radius.
            if (this.attackTicksLeft > 0 && this.attackTicksLeft % 12 == 0) {
                double radius = state == ATTACK_AWAKENING ? 7.2D : 5.8D;
                emitGroundRing(serverLevel, radius, false);
                serverLevel.sendParticles(ParticleTypes.CRIT,
                        this.getX(), this.getY() + 0.30D, this.getZ(), 12,
                        0.85D, 0.10D, 0.85D, 0.045D);
                if (this.attackTicksLeft == 12) {
                    this.level().playSound(null, this.blockPosition(),
                            SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.1F, 0.52F);
                }
            }
        }
    }

    /**
     * Ring markers are particles only; never place, damage, replace, or inspect blocks.
     * Each sample is one tiny packet emitted only from the server, not a forced chunk lookup.
     */
    private void emitGroundRing(ServerLevel serverLevel, double radius, boolean impact) {
        final int samples = impact ? 32 : 24;
        final double surface = this.getY() + (impact ? 0.22D : 0.15D);
        for (int point = 0; point < samples; point++) {
            double angle = Math.PI * 2.0D * point / samples;
            double x = this.getX() + Math.cos(angle) * radius;
            double z = this.getZ() + Math.sin(angle) * radius;
            if (impact) {
                serverLevel.sendParticles(ParticleTypes.END_ROD,
                        x, surface, z, 2, 0.06D, 0.055D, 0.06D, 0.035D);
                serverLevel.sendParticles(ParticleTypes.CRIT,
                        x, surface + 0.12D, z, 1, 0.08D, 0.04D, 0.08D, 0.06D);
            } else {
                serverLevel.sendParticles(ParticleTypes.REVERSE_PORTAL,
                        x, surface, z, 1, 0.06D, 0.025D, 0.06D, 0.006D);
                if (point % 3 == 0) {
                    serverLevel.sendParticles(ParticleTypes.END_ROD,
                            x, surface + 0.11D, z, 1, 0.0D, 0.02D, 0.0D, 0.0D);
                }
            }
        }
    }

    private void releaseAttack(int state) {"""
replace_exact(ENTITY, old_warning, new_warning, "warning rings in existing boss windup")

# Two outward ripples on impact visually connect the feet to the damage circle.
# They are visual cues only; the original damage, radius and cooldown remain unchanged.
old_stomp = """    private void performStomp(float damage, double radius) {
        if (this.level() instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(ParticleTypes.EXPLOSION,"""
new_stomp = """    private void performStomp(float damage, double radius) {
        if (this.level() instanceof ServerLevel serverLevel) {
            // 1.83 concentric non-destructive shockwave: center -> real hit radius.
            emitGroundRing(serverLevel, radius * 0.54D, true);
            emitGroundRing(serverLevel, radius, true);
            serverLevel.sendParticles(ParticleTypes.EXPLOSION,"""
replace_exact(ENTITY, old_stomp, new_stomp, "non-destructive impact shockwave")

# The old square AABB was used as the full hit test, damaging players standing outside
# the circle drawn by the new warning. Keep AABB as the broad phase and use horizontal
# circular distance for the actual radius. Jumping counters the strictly ground-based
# wave; flying/airborne entities do not receive its damage or knockback.
old_hit = """        for (LivingEntity victim : victims) {
            victim.hurt(this.damageSources().mobAttack(this), damage);
            victim.knockback(1.65D, this.getX() - victim.getX(), this.getZ() - victim.getZ());
            if (damage > 15.0F) victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 70, 1));
        }
    }"""
new_hit = """        for (LivingEntity victim : victims) {
            // 1.83 fair shockwave geometry: the warning ring exactly matches its hit area.
            double dx = victim.getX() - this.getX();
            double dz = victim.getZ() - this.getZ();
            if (dx * dx + dz * dz > radius * radius) continue;
            // Jumping is explicit counterplay; airborne creatures are not struck by the ground.
            if (!victim.onGround()) continue;
            victim.hurt(this.damageSources().mobAttack(this), damage);
            victim.knockback(1.65D, this.getX() - victim.getX(), this.getZ() - victim.getZ());
            if (damage > 15.0F) victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 70, 1));
        }
    }"""
replace_exact(ENTITY, old_hit, new_hit, "circular ground-only stomp hit test")

entity = ENTITY.read_text(encoding="utf-8")
require("private void performStomp(float damage, double radius)" in entity
        and "emitGroundRing(serverLevel, radius, true)" in entity,
        "existing stomp and visual shockwave must both remain")
require("private void performCrystalBreath()" in entity,
        "Crystal Breath attack must not be altered")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "boss must not force-load terrain")

# Move active contracts to the next version while preserving 1.82 and older releases.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_colossus_seismic_warning_183.py":
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.82.0",
                             "Aktueller Entwicklungsstand: 1.83.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.82\.0", r"1\.83\.0")
        updated = updated.replace("artifact must be version 1.82.0",
                                  "artifact must be version 1.83.0")
    updated = updated.replace(
        '"Version 1.82.0" in readme and "Version 1.81.0" in readme',
        '"Version 1.83.0" in readme and "Version 1.82.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

gradle = ROOT / "build.gradle"
build, changed = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                         "version = '1.83.0'", gradle.read_text(encoding="utf-8"), count=1)
require(changed == 1, "could not update Gradle version")
gradle.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.83.0

- **Bodenerschütterung mit Vorwarnung:** Der Kristallkoloss erzeugt beim Stampfen drei deutlich sichtbare, ringförmige Warnpulse aus Partikeln. Der normale Radius beträgt 5,8 Blöcke, beim Erwachen 7,2 Blöcke.
- **Ring entspricht Trefferbereich:** Eine runde Distanzprüfung ersetzt das alte rechteckige Treffergebiet. Wer außerhalb des sichtbaren Warnkreises steht, wird vom Stampfen nicht getroffen.
- **Ausweichmechanik:** Wer rechtzeitig springt und bei der Auslösung nicht am Boden steht, kann die bodengebundene Erschütterung vermeiden. Schaden und Rückstoß für getroffene Ziele bleiben unverändert.
- **Aufprall mit zwei Leuchtwellen:** Beim Stampfstoß laufen ein innerer und ein äußerer Kristall-Partikelring über den Boden. Die Umgebung wird nicht abgebaut oder beschädigt.
- **Technische Qualität:** Nur vorhandene Bossangriffs-Ticks und standardmäßige Minecraft-Partikel; keine Blockänderungen, Chunk-Forceloads oder zusätzlichen Dauer-Ticker. Regression prüft Treffergeometrie, Ausweichmechanik, Warnzeitpunkte und unveränderte Kampfwerte; der Forge-Build und Serverstart prüfen die Integration.

"""
if "## Aktueller Entwicklungsschritt — 1.83.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.82.0"
    require(marker in readme, "missing 1.82 current section")
    readme = readme.replace(marker, current + marker, 1)
release = """## Version 1.83.0 — Kristallkoloss: seismischer Warnring und Sprung-Kontermöglichkeit

- **Telegraphierter Stampfangriff:** Drei Bodenkreise während der 42-Tick-Stampf- oder 36-Tick-Erwachensvorbereitung zeigen die gefährdete Zone. Ein zusätzlicher Klang warnt kurz vor dem Aufprall.
- **Klarer Trefferkreis:** Die vorhandene AABB dient nur als grobe Vorauswahl; eine genaue horizontale Kreisprüfung sichert den Radius von 5,8 bzw. 7,2 Blöcken.
- **Faire Kontermöglichkeit:** Hochspringen kann den Bodenschock abwehren, wenn das Ziel beim Impact nicht auf dem Boden steht. Die Angriffsstärke, Rückstoß- und Verlangsamungswerte bleiben erhalten.
- **Doppelter Aufprallring:** Zeitgleiche innere und äußere Kristallpartikel erzeugen einen gut sichtbaren Einschlag, ohne Blöcke abzubauen, zu ersetzen oder Chunks zu laden.
- **Performance:** Warnpulse nur dreimal pro Attacke, begrenzte Partikelanzahl pro Ring und keine dauerhaften Zusatzprüfungen.
- **Qualitätssicherung:** Neue Regression für Countdown, Partikel, realen Hit-Radius, Sprung-Ausweichen, unveränderte Angriffe, vorhandene Texturen und Version; Forge-Build und dedizierter Serverstart. Auf unebenem Gelände ist ein Minecraft-Client-Sichttest weiter nötig.

"""
if "## Version 1.83.0 — Kristallkoloss: seismischer Warnring und Sprung-Kontermöglichkeit" not in readme:
    marker = "## Version 1.82.0 —"
    require(marker in readme, "missing 1.82 historical release")
    readme = readme.replace(marker, release + marker, 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.82.0 — gewichtete Laufanimation und bewegliche Tatzen für den Kristallkoloss.**",
    "**Aktueller Entwicklungsstand: 1.83.0 — seismische Stampfvorwarnung und ausweichbare Kristallwelle.**")
require("Aktueller Entwicklungsstand: 1.83.0" in readme,
        "README headline still points to an old version")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.83.0: pulsed stomp danger circles, two concentric impact ripples, circular ground-only damage and jump counterplay.")
