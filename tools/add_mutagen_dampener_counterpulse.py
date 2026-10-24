#!/usr/bin/env python3
"""Turn a charged dampener's successful block into a small counterpulse (1.39.0)."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Resonance counterpulse generation: " + message)


entity_path = SRC / "entity/KristallpirscherEntity.java"
entity = entity_path.read_text(encoding="utf-8")

old = """                level().playSound(null, dampenerPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                        SoundSource.BLOCKS, 0.75F, 1.25F);
            }
            return true;"""
new = """                level().playSound(null, dampenerPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                        SoundSource.BLOCKS, 0.75F, 1.25F);

                // Reflect a controlled fraction of the blocked pulse back at its source.
                // Damage and the short slow are applied server-side and only after a charge is spent.
                serverLevel.sendParticles(ParticleTypes.CRIT,
                        getX(), getY() + 0.8D, getZ(), 16,
                        0.45D, 0.35D, 0.45D, 0.08D);
                hurt(level().damageSources().magic(), 2.0F);
                addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 0));
            }
            return true;"""

if new not in entity:
    require(old in entity, "could not find the charged, successful dampener-block anchor")
    entity = entity.replace(old, new, 1)

require("import net.minecraft.world.effect.MobEffectInstance;" in entity,
        "MobEffectInstance import is required")
require("import net.minecraft.world.effect.MobEffects;" in entity,
        "MobEffects import is required")
require("ParticleTypes.CRIT" in entity, "counterpulse impact particles are missing")
require(entity.count("hurt(level().damageSources().magic(), 2.0F);") == 1,
        "counterpulse damage must be installed exactly once")
require("if (charge <= 0) continue;" in entity,
        "empty dampeners must not trigger a counterpulse")
require("if (!level().hasChunkAt(pos)) continue;" in entity,
        "the dampener scan must remain chunk-safe")
entity_path.write_text(entity, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(
    r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
    "version = '1.39.0'",
    build_path.read_text(encoding="utf-8"),
    count=1,
)
require(count == 1, "could not advance Gradle version to 1.39.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.39.0 — Resonanzrückkopplung gegen den Kristallpirscher

- **Abwehr mit Konsequenz:** Wenn ein geladener Dämpfer einen echten Resonanzimpuls blockiert, wird ein kleiner Teil der Welle zum Kristallpirscher zurückgeworfen.
- **Treffer statt bloßer Meldung:** Der Angreifer erhält 2 Schadenspunkte und wird durch die Rückkopplung 30 Ticks lang leicht verlangsamt. Der Treffer wird mit klaren Krit-Partikeln am Gegner sichtbar.
- **Ladungsgebunden und begrenzt:** Die Rückkopplung findet nur statt, nachdem eine vorhandene Ladung verbraucht wurde. Ein leerer Dämpfer blockiert und kontert nichts; die bestehende 200-Tick-Abklingzeit bleibt erhalten.
- **Serverautorität:** Schaden und Statuseffekt werden ausschließlich serverseitig ausgeführt. Die bestehende geladene-Chunk-Prüfung und die begrenzte Suche bleiben unverändert.

"""
if "## Version 1.39.0 — Resonanzrückkopplung gegen den Kristallpirscher" not in readme:
    marker = "## Version 1.38.0 — Ladungsmanagement und Redstone-Ausgang"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.38.0 charge-management notes")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.38.0 — Ladungsmanagement und Comparator für den Resonanzdämpfer.**",
    "**Aktueller Entwicklungsstand: 1.39.0 — Resonanzrückkopplung für taktische Gegenwehr.**",
).replace(
    "## Aktueller Schwerpunkt — 1.38.0",
    "## Aktueller Schwerpunkt — 1.39.0",
)
readme_path.write_text(readme, encoding="utf-8")
print("Resonance counterpulse damage, short slow, visible impact, charge gating, and 1.39.0 notes generated.")
