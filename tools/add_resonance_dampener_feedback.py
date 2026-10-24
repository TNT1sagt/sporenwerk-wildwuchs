#!/usr/bin/env python3
"""Give the resonance dampener feedback and rate-limit blocked pulse attempts (1.35.0)."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"


def require_anchor(text, anchor, label):
    if anchor not in text:
        raise SystemExit(f"Cannot harden resonance dampener: missing {label} anchor")


def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    require_anchor(text, old, label)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


entity_path = SRC / "entity/KristallpirscherEntity.java"
entity = entity_path.read_text(encoding="utf-8")

# A dampener already present before windup consumes the same 200-tick cooldown.
old_start = """            if (isResonanceDamped()) return;
            resonanceWindup = RESONANCE_WINDUP_TICKS;"""
new_start = """            if (isResonanceDamped()) {
                resonanceCooldown = RESONANCE_COOLDOWN_TICKS;
                return;
            }
            resonanceWindup = RESONANCE_WINDUP_TICKS;"""
replace_once(entity_path, old_start, new_start, "dampened windup gate")
entity = entity_path.read_text(encoding="utf-8")

# If one is placed during the 30-tick telegraph, cancel at release and rate-limit again.
old_release = """        if (isResonanceDamped()) {
            resonanceWindup = 0;
            return;
        }"""
new_release = """        if (isResonanceDamped()) {
            resonanceWindup = 0;
            resonanceCooldown = RESONANCE_COOLDOWN_TICKS;
            return;
        }"""
replace_once(entity_path, old_release, new_release, "dampened release gate")
entity = entity_path.read_text(encoding="utf-8")

# Tell nearby players that the dampener absorbed the pulse. This method only runs at
# windup start/release, not once per tick. Cooldown above prevents repeated scans and sounds.
old_found = """            if (level().getBlockState(pos).is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())) {
                return true;
            }"""
new_found = """            if (level().getBlockState(pos).is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())) {
                BlockPos dampenerPos = pos.immutable();
                if (level() instanceof ServerLevel serverLevel) {
                    serverLevel.sendParticles(ParticleTypes.END_ROD,
                            dampenerPos.getX() + 0.5D, dampenerPos.getY() + 1.0D,
                            dampenerPos.getZ() + 0.5D, 12, 0.28D, 0.24D, 0.28D, 0.025D);
                    level().playSound(null, dampenerPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                            SoundSource.BLOCKS, 0.75F, 1.25F);
                }
                return true;
            }"""
replace_once(entity_path, old_found, new_found, "dampener detection feedback")

# Version and release documentation.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.35.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.35.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.35.0 — Rückmeldung und Abklingzeit für den Resonanzdämpfer

- **Sichtbar abgewehrt:** Blockiert ein Dämpfer einen Resonanzimpuls, steigen sichtbare Partikel am Gerät auf und ein kurzer Amethystton bestätigt die Abwehr.
- **Keine Scan-Schleife:** Ein bereits gedämpfter Angriffsversuch verbraucht sofort die normale 200-Tick-Abklingzeit. Damit wird der Schutzbereich nicht in jedem Tick erneut vollständig durchsucht.
- **Reaktiv platzierbar:** Wird ein Dämpfer während der 30-Tick-Aufladung platziert, bricht er den Impuls beim Auslösen ab, gibt Feedback und startet die Abklingzeit.
- **Chunk-sicher:** Nur geladene Blöcke werden abgefragt. Die Suche läuft ausschließlich beim Beginn/Ende eines Impulses und nie als kontinuierliche Block-Tick-Schleife.

"""
if "## Version 1.35.0 — Rückmeldung und Abklingzeit für den Resonanzdämpfer" not in readme:
    marker = "## Version 1.34.0 — Mutagen-Resonanzdämpfer"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.34.0 dampener release notes")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.34.0 — baubare Resonanzdämpfung für Hochmutagen-Anlagen.**",
    "**Aktueller Entwicklungsstand: 1.35.0 — sichtbare und ressourcenschonende Resonanzabwehr.**"
).replace("## Aktueller Schwerpunkt — 1.34.0", "## Aktueller Schwerpunkt — 1.35.0")
readme_path.write_text(readme, encoding="utf-8")
print("Dampener suppression feedback, attempt cooldown, chunk-safe behavior and 1.35.0 notes generated.")
