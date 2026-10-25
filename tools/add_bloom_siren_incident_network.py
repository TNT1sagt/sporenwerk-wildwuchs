#!/usr/bin/env python3
"""Wire Mutagen Bloom incidents into the existing latched siren and containment relay network (1.53.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen Bloom incident network: " + message)


# Add an explicit incident entry point without changing the siren's real-redstone
# sampling or its manual acknowledgement behavior.
siren_path = SRC / "block/MutagenWarningSirenBlock.java"
siren = siren_path.read_text(encoding="utf-8")
if "public static boolean raiseBloomIncident(" not in siren:
    anchor = """    /** 0 = clear, 1 = warning (1–4), 2 = elevated (5–10), 3 = critical (11–15). */
    public static int riskBand(int signal) {"""
    method = """    /**
     * Raises a latched incident without pretending the event is a physical redstone input.
     * The normal right-click acknowledgement still clears the latch back to live redstone.
     */
    public static boolean raiseBloomIncident(Level level, BlockPos pos, int incidentSignal) {
        if (level.isClientSide || incidentSignal <= 0 || !level.hasChunkAt(pos)) return false;
        BlockState state = level.getBlockState(pos);
        if (!(state.getBlock() instanceof MutagenWarningSirenBlock)
                || !state.hasProperty(SIGNAL)) return false;

        int previous = state.getValue(SIGNAL);
        int next = Math.max(previous, Math.min(15, incidentSignal));
        if (next <= previous) return false;

        level.setBlock(pos, state.setValue(SIGNAL, next), 3);
        if (riskBand(next) > riskBand(previous)) {
            float pitch = switch (riskBand(next)) {
                case 3 -> 0.55F;
                case 2 -> 0.82F;
                default -> 1.18F;
            };
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BELL.value(),
                    SoundSource.BLOCKS, 0.9F, pitch);
        }
        MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);
        return true;
    }

"""
    require(anchor in siren, "could not locate the shared siren severity helper")
    siren = siren.replace(anchor, method + anchor, 1)
    # These imports are intentionally explicit; this patch runs after the relay implementation.
    if "import net.minecraft.sounds.SoundEvents;" not in siren:
        siren = siren.replace("import net.minecraft.network.chat.Component;",
                              "import net.minecraft.network.chat.Component;\nimport net.minecraft.sounds.SoundEvents;\nimport net.minecraft.sounds.SoundSource;", 1)
    siren_path.write_text(siren, encoding="utf-8")
require("public static boolean raiseBloomIncident(" in siren,
        "siren incident method was not installed")

# A single rare tier-III bloom fans out to a small number of nearby sirens. The spiral
# ordering prefers the closest installations, each block read is chunk-safe, and a hard
# four-siren cap prevents oversized bases from turning a bloom into an unbounded scan.
bloom_path = SRC / "infection/MutagenBloom.java"
bloom = bloom_path.read_text(encoding="utf-8")
if "private static int announceBloomToSirens(" not in bloom:
    anchor = "    private static void exposeNearbyPlayers(ServerLevel level, BlockPos origin) {"
    helper = """    private static final int BLOOM_SIREN_RADIUS = 12;
    private static final int BLOOM_SIREN_VERTICAL_RADIUS = 6;
    private static final int MAX_BLOOM_SIRENS = 4;
    private static final int BLOOM_INCIDENT_SIGNAL = 12;

    /**
     * Latch a critical alarm at up to four nearest sirens around a real Mutagen Bloom.
     * This runs only after the persistent bloom cooldown is claimed, never in a world tick.
     */
    private static int announceBloomToSirens(ServerLevel level, BlockPos origin) {
        int announced = 0;
        int radius = BLOOM_SIREN_RADIUS;
        int radiusSquared = radius * radius;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

        for (int ring = 0; ring <= radius && announced < MAX_BLOOM_SIRENS; ring++) {
            for (int dx = -ring; dx <= ring && announced < MAX_BLOOM_SIRENS; dx++) {
                for (int dz = -ring; dz <= ring && announced < MAX_BLOOM_SIRENS; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != ring
                            || dx * dx + dz * dz > radiusSquared) continue;
                    for (int dy = -BLOOM_SIREN_VERTICAL_RADIUS;
                         dy <= BLOOM_SIREN_VERTICAL_RADIUS && announced < MAX_BLOOM_SIRENS; dy++) {
                        int y = origin.getY() + dy;
                        if (y < level.getMinBuildHeight() || y >= level.getMaxBuildHeight()) continue;
                        cursor.set(origin.getX() + dx, y, origin.getZ() + dz);
                        if (!level.hasChunkAt(cursor)) continue;
                        if (MutagenWarningSirenBlock.raiseBloomIncident(
                                level, cursor.immutable(), BLOOM_INCIDENT_SIGNAL)) {
                            announced++;
                        }
                    }
                }
            }
        }
        return announced;
    }

"""
    require(anchor in bloom, "could not locate Bloom exposure handler")
    # The extra import is inserted after the 1.52 Dampener / relay imports.
    if "import de.sporenwerk.block.MutagenWarningSirenBlock;" not in bloom:
        require("import de.sporenwerk.block.MutagenContainmentRelayBlock;" in bloom,
                "could not locate existing containment imports")
        bloom = bloom.replace("import de.sporenwerk.block.MutagenContainmentRelayBlock;",
                              "import de.sporenwerk.block.MutagenContainmentRelayBlock;\nimport de.sporenwerk.block.MutagenWarningSirenBlock;", 1)
    bloom = bloom.replace(anchor, helper + anchor, 1)
    call_anchor = "        accelerateCrops(level, origin, random);\n        exposeNearbyPlayers(level, origin);"
    call_new = "        accelerateCrops(level, origin, random);\n        announceBloomToSirens(level, origin);\n        exposeNearbyPlayers(level, origin);"
    require(call_anchor in bloom, "could not locate real Bloom event dispatch")
    bloom = bloom.replace(call_anchor, call_new, 1)
    bloom_path.write_text(bloom, encoding="utf-8")

require("announceBloomToSirens(level, origin);" in bloom
        and "BLOOM_INCIDENT_SIGNAL = 12" in bloom
        and "MAX_BLOOM_SIRENS = 4" in bloom,
        "Bloom event was not connected to capped siren reporting")

# Bump only the active artifact/version contracts; the historical release notes stay intact.
updated_tests = 0
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.52.0",
                             "Aktueller Entwicklungsstand: 1.53.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.52\.0", r"1\.53\.0")
        updated = updated.replace("artifact must be version 1.52.0",
                                  "artifact must be version 1.53.0")
    updated = updated.replace(
        '"Version 1.52.0" in readme and "Version 1.51.0" in readme',
        '"Version 1.53.0" in readme and "Version 1.52.0" in readme')
    updated = updated.replace(
        "release notes must preserve previous release history",
        "release notes must preserve previous release history")
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")
        updated_tests += 1

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.53.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.53.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.53.0 — Mutagenblüten melden sich im Containment-Netz

- **Ereignis löst Alarm aus:** Eine echte Mutagenblüte der höchsten Feldstufe erhöht bis zu vier nahe Warnsirenen direkt auf die kritische Alarmstufe.
- **Die Sirene bleibt ehrlich:** Das Ereignis setzt einen klar gekennzeichneten Alarm-Latch, verändert aber keinen physischen Redstone-Eingang. Rechtsklick quittiert wie bisher und synchronisiert den gespeicherten Spitzenwert wieder auf das echte Redstone-Signal.
- **Relais folgen dem Ereignis:** Jede neu erhöhte Sirene aktualisiert ihr nahes Containment-Relaisnetz; dessen Comparator-Ausgang stellt den gespeicherten Alarmwert bereit.
- **Kein Daueralarm-Loop:** Die Benachrichtigung läuft nur im seltenen, persistent cooldown-geschützten Blütenereignis. Es gibt keinen neuen Block-Ticker oder Entity-Tick-Scan.
- **Begrenzte Suche:** Die Suche bleibt auf Radius 12 und sechs Blöcke Höhe begrenzt, bevorzugt nahe Sirenen und verarbeitet höchstens vier Geräte. Nicht geladene Chunks werden vor jedem Blockzugriff übersprungen.
- **Bestehendes Verhalten bleibt erhalten:** Filtermaske, Mutationsanker, Sporenabwehr, endliche Dämpferladung, Feldscanner, Stationsdiagnose und manuelle Alarmquittierung bleiben aktiv.
- **Qualitätssicherung:** Neue Regressionen prüfen Ereignispriorität, vier Sirenen als feste Obergrenze, Severity-Sound, Relaisaktualisierung, DE/EN-Strings, JSON, Forge-Build und Server-Smoke-Test.

"""
if "## Version 1.53.0 — Mutagenblüten melden sich im Containment-Netz" not in readme:
    marker = "## Version 1.52.0 — Mutagenblüte, Resonanzdämpfer und Containment-Netz"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.52.0 notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.53.0 — ereignisgesteuerte Mutagenblüten-Alarme im Containment-Netz.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines:
    readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.53.0", 1)
else:
    readme = readme.replace(headline, headline + "\n\n## Aktueller Schwerpunkt — 1.53.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print(f"1.53.0 Bloom incident signalling generated; refreshed {updated_tests} active version assertions.")
