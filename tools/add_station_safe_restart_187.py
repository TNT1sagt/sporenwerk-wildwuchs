#!/usr/bin/env python3
"""1.87.0: safely restart controlled farming after the Mutagen Control Station emergency stop.

Holding an AMETHYST_SHARD while sneaking switches *only* registered, active, dormant
Mutation Nodes to CULTIVATION. The old empty-hand emergency shutdown and ordinary
surveys remain unchanged. No source registration, block spread, consumption or chunk loads.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(value, msg):
    if not value:
        raise SystemExit("Safe station restart 1.87: " + msg)


def patch_once(path, old, new, label):
    s = path.read_text(encoding="utf-8")
    if new in s:
        return
    require(s.count(old) == 1, f"{label}: expected one source anchor, got {s.count(old)}")
    path.write_text(s.replace(old, new, 1), encoding="utf-8")


station_path = SRC / "block/MutagenFieldControlStationBlock.java"
s = station_path.read_text(encoding="utf-8")
for imp, anchor in (
    ("import net.minecraft.world.item.Items;", "import net.minecraft.world.level.block.Block;"),
    ("import de.sporenwerk.infection.MutationNodeData;", "import de.sporenwerk.infection.MutationField;"),
):
    if imp not in s:
        require(anchor in s, "missing Java import anchor " + anchor)
        s = s.replace(anchor, anchor + "\n" + imp, 1)
station_path.write_text(s, encoding="utf-8")

shortcut = """        if (hand == InteractionHand.MAIN_HAND && player.isShiftKeyDown()) {
            int silenced = emergencyShutdown(serverLevel, pos);"""
shortcut_new = """        if (hand == InteractionHand.MAIN_HAND && player.isShiftKeyDown()) {
            // A normal amethyst shard has no useOn handler, unlike the handheld scanner.
            if (player.getItemInHand(hand).is(Items.AMETHYST_SHARD)) {
                int restarted = restartSafeCultivation(serverLevel, pos);
                player.displayClientMessage(Component.translatable(
                        restarted > 0
                                ? "message.sporenwerk.fieldstation.restart_done"
                                : "message.sporenwerk.fieldstation.restart_none",
                        restarted).withStyle(restarted > 0 ? ChatFormatting.GREEN : ChatFormatting.GRAY), false);
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.fieldstation.restart_guard")
                        .withStyle(ChatFormatting.DARK_GRAY), false);
                serverLevel.playSound(null, pos,
                        restarted > 0 ? SoundEvents.BEACON_ACTIVATE : SoundEvents.AMETHYST_BLOCK_CHIME,
                        SoundSource.BLOCKS, 0.65F, restarted > 0 ? 1.35F : 0.95F);
                return InteractionResult.CONSUME;
            }
            int silenced = emergencyShutdown(serverLevel, pos);"""
patch_once(station_path, shortcut, shortcut_new, "station amethyst restart gesture")

# Deliberately position before emergencyShutdown to preserve existing 1.84 regression
# boundaries. The emergency-only code never queries the active-node registry.
anchor = """    private static int emergencyShutdown(ServerLevel level, BlockPos center) {"""
method = """    /**
     * Recover a controlled experiment WITHOUT reactivating cured/inactive sources.
     * No sources in SPREAD mode are affected. Redstone pause is never overridden.
     */
    private static int restartSafeCultivation(ServerLevel level, BlockPos center) {
        int restarted = 0;
        int feedback = 0;
        int minY = Math.max(level.getMinBuildHeight(), center.getY() - VERTICAL_SCAN_RADIUS);
        int maxY = Math.min(level.getMaxBuildHeight() - 1, center.getY() + VERTICAL_SCAN_RADIUS);
        int radiusSq = HORIZONTAL_SCAN_RADIUS * HORIZONTAL_SCAN_RADIUS;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        MutationNodeData nodes = MutationNodeData.get(level);
        for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++) {
            for (int dz = -HORIZONTAL_SCAN_RADIUS; dz <= HORIZONTAL_SCAN_RADIUS; dz++) {
                if (dx * dx + dz * dz > radiusSq) continue;
                int x = center.getX() + dx;
                int z = center.getZ() + dz;
                if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;
                for (int y = minY; y <= maxY; y++) {
                    cursor.set(x, y, z);
                    BlockState state = level.getBlockState(cursor);
                    if (!(state.getBlock() instanceof MutationNodeBlock nodeBlock)
                            || state.getValue(MutationNodeBlock.MODE) != 2
                            || !nodes.isActive(cursor)) continue;
                    BlockState cultivated = state.setValue(MutationNodeBlock.MODE, 1);
                    level.setBlock(cursor, cultivated, 3);
                    restarted++;
                    if (!cultivated.getValue(MutationNodeBlock.POWERED)
                            && !level.hasNeighborSignal(cursor)) {
                        level.scheduleTick(cursor.immutable(), nodeBlock, 1);
                    }
                    if (feedback++ < 24) {
                        level.sendParticles(ParticleTypes.HAPPY_VILLAGER,
                                x + 0.5D, y + 0.72D, z + 0.5D,
                                7, 0.25D, 0.24D, 0.25D, 0.015D);
                    }
                }
            }
        }
        return restarted;
    }

""" + anchor
patch_once(station_path, anchor, method, "bounded safe restart loop")
old_hint = """        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.shutdown_usage")
                .withStyle(ChatFormatting.GRAY), false);"""
new_hint = old_hint + """
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.restart_usage")
                .withStyle(ChatFormatting.AQUA), false);"""
patch_once(station_path, old_hint, new_hint, "restart instructions in regular survey")

for locale, entries in (
    ("de_de.json", {
        "message.sporenwerk.fieldstation.restart_usage": "Sicherer Neustart: Amethystscherbe halten und geduckt rechtsklicken (RUHE -> ANBAU).",
        "message.sporenwerk.fieldstation.restart_done": "Kontrollierter Neustart: %s ruhende Mutagenknoten auf ANBAU umgestellt.",
        "message.sporenwerk.fieldstation.restart_none": "Kein Neustart: %s Knoten geändert. Keine aktiven ruhenden Knoten im geladenen Bereich.",
        "message.sporenwerk.fieldstation.restart_guard": "Niemals AUSBREITUNG. Geheilte Quellen bleiben inaktiv, Redstone bleibt aktiv; die Scherbe wird nicht verbraucht."
    }),
    ("en_us.json", {
        "message.sporenwerk.fieldstation.restart_usage": "Safe restart: hold an amethyst shard and sneak-right-click (DORMANT -> CULTIVATION).",
        "message.sporenwerk.fieldstation.restart_done": "Controlled restart: %s dormant Mutagen Nodes switched to CULTIVATION.",
        "message.sporenwerk.fieldstation.restart_none": "No restart: %s nodes changed. No active dormant nodes found in loaded range.",
        "message.sporenwerk.fieldstation.restart_guard": "Never SPREAD. Cured sources remain inactive, Redstone stays in control, and the shard is not consumed."
    }),
):
    p = ASSETS / "lang" / locale
    data = json.loads(p.read_text(encoding="utf-8"))
    data.update(entries)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

station = station_path.read_text(encoding="utf-8")
require('player.getItemInHand(hand).is(Items.AMETHYST_SHARD)' in station
        and 'state.setValue(MutationNodeBlock.MODE, 1)' in station
        and 'MutationNodeData.get(level)' in station,
        "safe restart was not installed")
require("getChunk(" not in station and "getChunkNow(" not in station,
        "no forced chunk loads are permitted")

for test in (ROOT / "tools").glob("test_*.py"):
    if test.name == "test_station_safe_restart_187.py":
        continue
    original = test.read_text(encoding="utf-8")
    changed = original.replace("Aktueller Entwicklungsstand: 1.86.0",
                               "Aktueller Entwicklungsstand: 1.87.0")
    if "build.gradle" in original:
        changed = changed.replace(r"1\.86\.0", r"1\.87\.0")
        changed = changed.replace("artifact must be version 1.86.0",
                                  "artifact must be version 1.87.0")
    changed = changed.replace(
        '"Version 1.86.0" in readme and "Version 1.85.0" in readme',
        '"Version 1.87.0" in readme and "Version 1.86.0" in readme')
    if original != changed:
        test.write_text(changed, encoding="utf-8")

build_file = ROOT / "build.gradle"
gradle, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.87.0'", build_file.read_text(encoding="utf-8"), count=1)
require(count == 1, "Gradle artifact version not found")
build_file.write_text(gradle, encoding="utf-8")

readme_file = ROOT / "README.md"
readme = readme_file.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.87.0

- **Sicherer Wiederanlauf kontrollierter Mutagenanlagen:** Geduckt mit einer Amethystscherbe in der Hand auf die Feldkontrollstation rechtsklicken: Nur bisher ruhende und noch aktive Mutagenknoten innerhalb Radius 16 / Höhe ±8 werden auf ANBAU zurückgestellt.
- **Not-Abschaltung und Diagnose bleiben intakt:** Geduckter Rechtsklick ohne Amethystscherbe legt wie in 1.84 alle Knoten still; normaler Rechtsklick erstellt weiterhin den vorhandenen Forschungsbericht.
- **Welt-Heilung wird nicht rückgängig gemacht:** Die Station prüft die gespeicherte aktive Quellenregistrierung. Inaktive beziehungsweise endgültig geheilte Quellen können durch den Neustart nicht wieder eingeschaltet werden.
- **Nie aggressive Ausbreitung:** Der Neustart setzt ausschließlich den vorhandenen Kultivierungsmodus. Bereits aktive Quellen in anderen Modi werden nicht verändert. Redstone-Pausen bleiben unverändert.
- **Gute Bedienung:** Die Amethystscherbe wird nicht verbraucht. Eine Zählmeldung, dezente grüne Partikel, Amethystklang und die Anleitung im Stationsbericht erklären den sicheren Vorgang auf Deutsch und Englisch.
- **Performance:** Ein einmaliger, kreisförmiger Loaded-Chunk-Scan ohne Dauer-Ticker und mit begrenzten Partikeln; vorhandene Anbau-Ticks werden nur bei Redstone-freien Quellen neu geplant.

"""
if "## Aktueller Entwicklungsschritt — 1.87.0" not in readme:
    require("## Aktueller Entwicklungsschritt — 1.86.0" in readme, "1.86 current step missing")
    readme = readme.replace("## Aktueller Entwicklungsschritt — 1.86.0",
                            current + "## Aktueller Entwicklungsschritt — 1.86.0", 1)
release = """## Version 1.87.0 — Wiederanlauf sicherer Mutagenfarmen

- **Drei Betriebswege an derselben Station:** Normaler Rechtsklick untersucht die Anlage, geduckter Rechtsklick stellt sie still, geduckter Rechtsklick mit Amethystscherbe aktiviert ausschließlich sichere Kultivierung.
- **Kein unkontrolliertes Wiederausbrechen:** Aktive, registrierte und bereits ruhende Knoten können wieder in den Anbaumodus wechseln; niemals in den Ausbreitungsmodus. Knoten aus geheilten Welten bleiben inaktiv.
- **Technisch schonend:** Unveränderte Redstone-Pausen, keine Itemkosten, nur geladene Chunks, begrenzte Rückmeldungen und kein zusätzliches Hintergrundsystem.
- **Prüfung:** Neue Regression für Interaktion, Schutzschranken, sichere Feldmodi, Übersetzungen und bestehenden Not-Aus-Pfad, kompletter Forge-Build und dedizierter Serverstart.

"""
if "## Version 1.87.0 — Wiederanlauf sicherer Mutagenfarmen" not in readme:
    require("## Version 1.86.0 —" in readme, "1.86 release missing")
    readme = readme.replace("## Version 1.86.0 —", release + "## Version 1.86.0 —", 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.86.0 — Dämmerling mit dynamischem Blickkontakt-Verhalten.**",
    "**Aktueller Entwicklungsstand: 1.87.0 — sicherer Wiederanlauf kontrollierter Mutagenfarmen.**")
require("Aktueller Entwicklungsstand: 1.87.0" in readme, "README title not updated")
readme_file.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.87.0 installed: amethyst-triggered cultivation-only restart, loaded-chunk and cured-world guards.")
