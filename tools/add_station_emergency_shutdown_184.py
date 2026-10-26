#!/usr/bin/env python3
"""1.84.0: a manual, chunk-safe emergency shutdown for controlled Mutagen nodes.

Sneak + right-click on the existing Mutagen Field Control Station moves loaded,
nearby MutationNodeBlock sources to DORMANT. It does not touch terrain, crop
growth, global end-game sterilization, existing node registration, or redstone.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(value, description):
    if not value:
        raise SystemExit("Station emergency shutdown 1.84: " + description)


def replace_exact(path, old, new, label):
    original = path.read_text(encoding="utf-8")
    if new in original:
        return
    require(original.count(old) == 1,
            label + f": source anchor must appear exactly once (found {original.count(old)})")
    path.write_text(original.replace(old, new, 1), encoding="utf-8")


station_path = SRC / "block/MutagenFieldControlStationBlock.java"
station = station_path.read_text(encoding="utf-8")
for imp, anchor in (
    ("import net.minecraft.core.particles.ParticleTypes;", "import net.minecraft.core.BlockPos;"),
    ("import net.minecraft.world.level.block.state.properties.IntegerProperty;", "import net.minecraft.world.level.block.state.BlockState;"),
):
    if imp not in station:
        # IntegerProperty is already present since comparator support; use it as a sanity anchor.
        require(anchor in station, "expected station import missing: " + anchor)
        station = station.replace(anchor, anchor + "\n" + imp, 1)

# The MutationNodeBlock is in the same Java package, no new import required.
station_path.write_text(station, encoding="utf-8")

use_anchor = """        if (!(level instanceof ServerLevel serverLevel)) return InteractionResult.CONSUME;"""
use_branch = use_anchor + """
        if (hand == InteractionHand.MAIN_HAND && player.isShiftKeyDown()) {
            int silenced = emergencyShutdown(serverLevel, pos);
            player.displayClientMessage(Component.translatable(
                    silenced == 0
                            ? "message.sporenwerk.fieldstation.shutdown_none"
                            : "message.sporenwerk.fieldstation.shutdown_done",
                    silenced).withStyle(silenced == 0 ? ChatFormatting.GRAY : ChatFormatting.GREEN), false);
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.shutdown_hint").withStyle(ChatFormatting.DARK_GRAY), false);
            serverLevel.playSound(null, pos, silenced > 0
                            ? SoundEvents.BEACON_DEACTIVATE : SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.BLOCKS, 0.65F, silenced > 0 ? 0.72F : 0.9F);
            return InteractionResult.CONSUME;
        }"""
replace_exact(station_path, use_anchor, use_branch, "manual sneaking interaction")

# No current-mode toggles or power changes: dormant nodes retain their state and
# players can resume each independently using the existing node right-click modes.
survey_anchor = """    private static Survey survey(ServerLevel level, BlockPos center) {"""
shutdown_code = """    /**
     * Manual emergency stop for the controlled enclosure. Only already loaded
     * columns in the same circular 16-block, +/-8-block station survey are touched.
     * No chunks are loaded; old scheduled and random ticks obey MODE == 2.
     */
    private static int emergencyShutdown(ServerLevel level, BlockPos center) {
        int halted = 0;
        int effects = 0;
        int minY = Math.max(level.getMinBuildHeight(), center.getY() - VERTICAL_SCAN_RADIUS);
        int maxY = Math.min(level.getMaxBuildHeight() - 1, center.getY() + VERTICAL_SCAN_RADIUS);
        int radiusSq = HORIZONTAL_SCAN_RADIUS * HORIZONTAL_SCAN_RADIUS;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++) {
            for (int dz = -HORIZONTAL_SCAN_RADIUS; dz <= HORIZONTAL_SCAN_RADIUS; dz++) {
                if (dx * dx + dz * dz > radiusSq) continue;
                int x = center.getX() + dx;
                int z = center.getZ() + dz;
                // Absolutely no level.getBlockState() until the column's chunk is loaded.
                if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;
                for (int y = minY; y <= maxY; y++) {
                    cursor.set(x, y, z);
                    BlockState nodeState = level.getBlockState(cursor);
                    if (!(nodeState.getBlock() instanceof MutationNodeBlock)
                            || nodeState.getValue(MutationNodeBlock.MODE) == 2) continue;
                    // Preserve POWERED, active-node data and player-owned infection fields.
                    level.setBlock(cursor, nodeState.setValue(MutationNodeBlock.MODE, 2), 3);
                    halted++;
                    // Visual feedback remains bounded even in extreme node installations.
                    if (effects++ < 24) {
                        level.sendParticles(ParticleTypes.SMOKE,
                                x + 0.5D, y + 0.72D, z + 0.5D,
                                6, 0.18D, 0.18D, 0.18D, 0.012D);
                    }
                }
            }
        }
        return halted;
    }

""" + survey_anchor
replace_exact(station_path, survey_anchor, shutdown_code, "bounded emergency stop implementation")

hint_anchor = """        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.loaded_chunks_only").withStyle(ChatFormatting.DARK_GRAY), false);"""
hint_new = hint_anchor + """
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.shutdown_usage")
                .withStyle(ChatFormatting.GRAY), false);"""
replace_exact(station_path, hint_anchor, hint_new, "discoverability in regular station report")

station = station_path.read_text(encoding="utf-8")
for token in ("private static int emergencyShutdown(", "MutationNodeBlock.MODE", "level.hasChunkAt(new BlockPos(x, minY, z))",
              "nodeState.setValue(MutationNodeBlock.MODE, 2)", "player.isShiftKeyDown()"):
    require(token in station, "missing safety action: " + token)
require("getChunk(" not in station and "getChunkNow(" not in station,
        "station is not permitted to force load chunks")

for locale, messages in (
    ("de_de.json", {
        "message.sporenwerk.fieldstation.shutdown_usage":
            "Notabschaltung: Geduckt rechtsklicken, um Mutagenknoten im Scanbereich auf RUHE zu setzen.",
        "message.sporenwerk.fieldstation.shutdown_done":
            "Notabschaltung ausgeführt: %s Mutagenknoten in den Ruhezustand versetzt.",
        "message.sporenwerk.fieldstation.shutdown_none":
            "Notabschaltung: keine aktiven Mutagenknoten in bereits geladenen Bereichen gefunden (%s geändert).",
        "message.sporenwerk.fieldstation.shutdown_hint":
            "Nur geladene Chunks, Radius 16 / Höhe ±8. Einzelne Knoten können anschließend wieder manuell aktiviert werden."
    }),
    ("en_us.json", {
        "message.sporenwerk.fieldstation.shutdown_usage":
            "Emergency stop: sneak-right-click to set nearby Mutagen Nodes to DORMANT.",
        "message.sporenwerk.fieldstation.shutdown_done":
            "Emergency stop complete: %s Mutagen Nodes switched to dormant.",
        "message.sporenwerk.fieldstation.shutdown_none":
            "Emergency stop: no active Mutagen Nodes found in loaded chunks (%s changed).",
        "message.sporenwerk.fieldstation.shutdown_hint":
            "Loaded chunks only, radius 16 / height ±8. Individual nodes can be manually reactivated later."
    }),
):
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(messages)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Advance current-version contracts but keep historical test names and versions.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_station_emergency_shutdown_184.py":
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.83.0",
                             "Aktueller Entwicklungsstand: 1.84.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.83\.0", r"1\.84\.0")
        updated = updated.replace("artifact must be version 1.83.0",
                                  "artifact must be version 1.84.0")
    updated = updated.replace(
        '"Version 1.83.0" in readme and "Version 1.82.0" in readme',
        '"Version 1.84.0" in readme and "Version 1.83.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

gradle = ROOT / "build.gradle"
build, n = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                   "version = '1.84.0'", gradle.read_text(encoding="utf-8"), count=1)
require(n == 1, "could not update Gradle version to 1.84.0")
gradle.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.84.0

- **Notabschaltung an der Kontrollstation:** Geduckter Rechtsklick versetzt sämtliche geladenen Mutagenknoten im bestehenden Scanradius 16 (Höhe ±8) in den RUHE-Modus. Ein normaler Rechtsklick liefert weiterhin den gewohnten Diagnosebericht.
- **Kein versehentlicher Neustart:** Der RUHE-Modus ist ein bereits vorhandener persistenter Blockzustand. Die vorhandene Spread- und Cultivation-Logik respektiert diesen Zustand sowohl bei geplanten als auch zufälligen Ticks. Die zuvor gewählten Modi werden nur durch manuelles Bedienen einzelner Knoten wieder verändert.
- **Bestehende Feldinfrastruktur bleibt:** Abschalten ist kein globaler Sterilisierungsprozess. Stabilisatoren, Sporenabwehrsender, Forschungsrelais und kontrollierte Anbauflächen bleiben erhalten; Knotenregistrierung und Redstone-Status bleiben unverändert.
- **Klare Rückmeldung:** Die Station meldet die tatsächlich stillgelegte Knotenzahl, zeigt begrenzte Rauchpartikel und warnt ausdrücklich vor ungeladenen Chunks. Das normale Stationsprotokoll erklärt die neue Bedienung.
- **Sicherheit und Performance:** Ein einmaliger, kreisförmiger, höhenbegrenzter Scan mit vorheriger Loaded-Chunk-Prüfung, maximal 24 visuellen Knotenrückmeldungen und keinen neuen Tick-Schleifen. Eigene Regression und vollständiger Forge-Build prüfen die Integration.

"""
if "## Aktueller Entwicklungsschritt — 1.84.0" not in readme:
    anchor = "## Aktueller Entwicklungsschritt — 1.83.0"
    require(anchor in readme, "missing 1.83 development section")
    readme = readme.replace(anchor, current + anchor, 1)
release = """## Version 1.84.0 — Mutagen-Notabschaltung der Feldkontrollstation

- **Neue Anlagenfunktion:** Geduckter Rechtsklick auf eine Feldkontrollstation stellt alle geladenen Mutagenknoten im Radius 16 / Höhe ±8 von SPREAD bzw. CULTIVATION auf DORMANT. Die normale Diagnose bleibt verfügbar.
- **Unveränderter Schutzpfad:** Mutagenknoten behalten ihre Registrierung und ihren Redstone-Zustand. Der bestehende Mode-2-Zweig verhindert sowohl Ausbreitung als auch Kultivierung, bis ein einzelner Knoten gezielt umgestellt wird.
- **Sicherheit beim Eingriff:** Bereits ruhende Knoten werden nicht verändert. Der Scan überspringt ungeladene Chunks, verwendet nur bestehende Blockzustände und führt keinen dauerhaften Hintergrundticker ein.
- **Messbare Rückmeldung:** Spieler erhalten eine serverseitige Knotenzahl und einen Hinweis auf die Scanbegrenzung. Maximal 24 betroffene Knoten erzeugen Rauchpartikel; eine stationäre Klangrückmeldung bestätigt die Betätigung.
- **Kontrollierte Experimente bleiben möglich:** So lassen sich aktivierte Mutagenanlagen gezielt stilllegen, ohne eine Weltheilung auszulösen oder die spätere Wiedernutzung von Infektionsfeldern zu verhindern.
- **Qualitätskontrolle:** Regressionen für Eingabe, Radius, Loaded-Chunk-Guard, Spielerhinweise, Zustandserhalt, ursprüngliche Knotenticks, Metadaten und Übersetzungen sowie Forge-Kompilierung und dedizierter Serverstart.

"""
if "## Version 1.84.0 — Mutagen-Notabschaltung der Feldkontrollstation" not in readme:
    anchor = "## Version 1.83.0 —"
    require(anchor in readme, "missing release notes 1.83")
    readme = readme.replace(anchor, release + anchor, 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.83.0 — seismische Stampfvorwarnung und ausweichbare Kristallwelle.**",
    "**Aktueller Entwicklungsstand: 1.84.0 — Mutagen-Notabschaltung über die Feldkontrollstation.**")
require("Aktueller Entwicklungsstand: 1.84.0" in readme,
        "README current development level still outdated")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.84.0: loaded-chunk-safe station emergency shutdown preserves controlled mutagen farming and existing reports.")
