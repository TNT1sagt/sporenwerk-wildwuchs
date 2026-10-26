#!/usr/bin/env python3
"""Sporenwerk 1.89: copper-assisted rescue of live spreading nodes into safe cultivation.

A non-consumable copper ingot on the control station converts only ACTIVE,
UNPOWERED SPREAD nodes in already loaded columns. Cured/sterilized sources,
paused nodes and existing farms remain untouched. The first successful
conversion awards a survival advancement.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"
DATA = ROOT / "src/main/resources/data/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.89 copper containment: " + message)


def patch_once(path, old, new, label):
    content = path.read_text(encoding="utf-8")
    if new in content:
        return
    require(content.count(old) == 1, label + ": expected one anchor, found " + str(content.count(old)))
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


station_path = SRC / "block/MutagenFieldControlStationBlock.java"
station = station_path.read_text(encoding="utf-8")
require("private static int restartSafeCultivation(" in station
        and "private static int emergencyShutdown(" in station
        and "private static Survey survey(" in station,
        "this feature must run after the 1.88 node audit")

# Route the new action ahead of amethyst restart and the default emergency stop.
interaction_anchor = "            if (player.getItemInHand(hand).is(Items.AMETHYST_SHARD)) {"
copper_action = """            if (player.getItemInHand(hand).is(Items.COPPER_INGOT)) {
                // Ground only active, unpowered spreading sources, without consuming the ingot.
                int converted = convertSpreadToCultivation(serverLevel, pos);
                player.displayClientMessage(Component.translatable(
                        converted > 0
                                ? "message.sporenwerk.fieldstation.copper_done"
                                : "message.sporenwerk.fieldstation.copper_none",
                        converted).withStyle(converted > 0
                                ? ChatFormatting.GREEN : ChatFormatting.GRAY), false);
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.fieldstation.copper_guard")
                        .withStyle(ChatFormatting.DARK_GRAY), false);
                serverLevel.playSound(null, pos,
                        converted > 0 ? SoundEvents.BEACON_ACTIVATE : SoundEvents.AMETHYST_BLOCK_CHIME,
                        SoundSource.BLOCKS, 0.7F, converted > 0 ? 1.18F : 0.85F);
                if (converted > 0
                        && player instanceof net.minecraft.server.level.ServerPlayer serverPlayer) {
                    var advancement = serverLevel.getServer().getAdvancements().getAdvancement(
                            new net.minecraft.resources.ResourceLocation(
                                    "sporenwerk", "knotenrettung"));
                    if (advancement != null) {
                        serverPlayer.getAdvancements().award(advancement, "converted");
                    }
                }
                return InteractionResult.CONSUME;
            }
""" + interaction_anchor
patch_once(station_path, interaction_anchor, copper_action, "copper control gesture")

# Share the *single* one-shot cultivation scheduling call with the 1.87 safe
# restart; this also preserves the legacy one-scheduleTick station invariant.
old_schedule = """                    if (!cultivated.getValue(MutationNodeBlock.POWERED)
                            && !level.hasNeighborSignal(cursor)) {
                        level.scheduleTick(cursor.immutable(), nodeBlock, 1);
                    }"""
patch_once(station_path, old_schedule,
           "                    scheduleSafeCultivationTick(level, cursor, nodeBlock, cultivated);",
           "unify cultivation scheduling")

restart_anchor = "    private static int restartSafeCultivation(ServerLevel level, BlockPos center) {"
convert_method = """    /**
     * Copper grounding: convert dangerous, LIVE SPREAD nodes into safe CULTIVATION.
     * Does not heal terrain or revive cured Mutagen sources. Uses the same
     * bounded loaded-chunk circle as manual shutdown and safe restart.
     */
    private static int convertSpreadToCultivation(ServerLevel level, BlockPos center) {
        int converted = 0;
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
                            || state.getValue(MutationNodeBlock.MODE) != 0
                            || state.getValue(MutationNodeBlock.POWERED)
                            || level.hasNeighborSignal(cursor)
                            || !nodes.isActive(cursor)) continue;
                    BlockState cultivated = state.setValue(MutationNodeBlock.MODE, 1);
                    level.setBlock(cursor, cultivated, 3);
                    scheduleSafeCultivationTick(level, cursor, nodeBlock, cultivated);
                    converted++;
                    if (feedback++ < 24) {
                        level.sendParticles(ParticleTypes.HAPPY_VILLAGER,
                                x + 0.5D, y + 0.72D, z + 0.5D,
                                7, 0.22D, 0.21D, 0.22D, 0.013D);
                        level.sendParticles(ParticleTypes.END_ROD,
                                x + 0.5D, y + 0.75D, z + 0.5D,
                                2, 0.13D, 0.17D, 0.13D, 0.005D);
                    }
                }
            }
        }
        return converted;
    }

""" + restart_anchor
patch_once(station_path, restart_anchor, convert_method, "bounded copper conversion")

emergency_anchor = "    private static int emergencyShutdown(ServerLevel level, BlockPos center) {"
helper = """    /** One shared, one-shot wake-up for both safe cultivation actions. */
    private static void scheduleSafeCultivationTick(ServerLevel level,
                                                   BlockPos.MutableBlockPos cursor,
                                                   MutationNodeBlock nodeBlock,
                                                   BlockState cultivated) {
        if (!cultivated.getValue(MutationNodeBlock.POWERED)
                && !level.hasNeighborSignal(cursor)) {
            level.scheduleTick(cursor.immutable(), nodeBlock, 1);
        }
    }

""" + emergency_anchor
patch_once(station_path, emergency_anchor, helper, "shared node-only tick scheduler")

hint_anchor = """        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.restart_usage")
                .withStyle(ChatFormatting.AQUA), false);"""
patch_once(station_path, hint_anchor, hint_anchor + """
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.copper_usage")
                .withStyle(ChatFormatting.GOLD), false);""", "copper discoverability")

station = station_path.read_text(encoding="utf-8")
require(station.count("scheduleTick(") == 1, "one-shot node scheduling must remain a single call site")
require("getChunk(" not in station and "getChunkNow(" not in station
        and "getTicker(" not in station, "no chunk forcing or station ticker")
require("private static int convertSpreadToCultivation(" in station
        and "private static int emergencyShutdown(" in station,
        "conversion may not replace the emergency pathway")

for locale, entries in (
    ("de_de.json", {
        "message.sporenwerk.fieldstation.copper_usage":
            "Knotenrettung: Kupferbarren halten und geduckt rechtsklicken (AUSBREITUNG -> ANBAU).",
        "message.sporenwerk.fieldstation.copper_done":
            "Knotenrettung erfolgreich: %s aktive Gefahrenquellen auf sicheren ANBAU umgestellt.",
        "message.sporenwerk.fieldstation.copper_none":
            "Knotenrettung: %s Quellen umgestellt. Keine aktiven, ungepausten Ausbreitungsknoten in geladenen Chunks.",
        "message.sporenwerk.fieldstation.copper_guard":
            "Geheilte, inaktive und Redstone-pausierte Quellen bleiben unverändert. Kupfer wird nicht verbraucht.",
        "advancement.sporenwerk.knotenrettung.title": "Aus Gefahr wird Wachstum",
        "advancement.sporenwerk.knotenrettung.description":
            "Wandle einen aktiven Mutagenherd per Kupfererdung in eine kontrollierte Anbauquelle um."
    }),
    ("en_us.json", {
        "message.sporenwerk.fieldstation.copper_usage":
            "Node rescue: hold a copper ingot and sneak-right-click (SPREAD -> CULTIVATION).",
        "message.sporenwerk.fieldstation.copper_done":
            "Node rescue complete: %s active hazards converted to safe CULTIVATION.",
        "message.sporenwerk.fieldstation.copper_none":
            "Node rescue: %s sources changed. No active, unpaused spreading nodes in loaded chunks.",
        "message.sporenwerk.fieldstation.copper_guard":
            "Cured, inactive and Redstone-paused sources remain untouched. Copper is not consumed.",
        "advancement.sporenwerk.knotenrettung.title": "From Danger to Growth",
        "advancement.sporenwerk.knotenrettung.description":
            "Ground an active Mutagen source with copper and repurpose it as a safe crop field."
    }),
):
    locale_path = ASSETS / "lang" / locale
    lang = json.loads(locale_path.read_text(encoding="utf-8"))
    lang.update(entries)
    locale_path.write_text(json.dumps(lang, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")

adv_path = DATA / "advancements/knotenrettung.json"
adv_path.parent.mkdir(parents=True, exist_ok=True)
adv_path.write_text(json.dumps({
    "display": {
        "icon": {"item": "minecraft:copper_ingot"},
        "title": {"translate": "advancement.sporenwerk.knotenrettung.title"},
        "description": {"translate": "advancement.sporenwerk.knotenrettung.description"},
        "frame": "task", "show_toast": True,
        "announce_to_chat": True, "hidden": False
    },
    "criteria": {"converted": {"trigger": "minecraft:impossible"}},
    "requirements": [["converted"]]
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Upgrade only rolling current-version expectations. Every old milestone
# remains in README and the tests retain their own historical assertions.
for path in (ROOT / "tools").glob("test_*.py"):
    if path.name == "test_fieldstation_copper_conversion_189.py":
        continue
    original = path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.88.0",
                               "Aktueller Entwicklungsstand: 1.89.0")
    if "build.gradle" in original:
        updated = updated.replace(r"1\.88\.0", r"1\.89\.0")
        updated = updated.replace("artifact must be version 1.88.0",
                                  "artifact must be version 1.89.0")
    updated = updated.replace(
        '"Version 1.88.0" in readme and "Version 1.87.0" in readme',
        '"Version 1.89.0" in readme and "Version 1.88.0" in readme')
    if updated != original:
        path.write_text(updated, encoding="utf-8")

gradle = ROOT / "build.gradle"
build, changed = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                         "version = '1.89.0'", gradle.read_text(encoding="utf-8"), count=1)
require(changed == 1, "cannot set Gradle release version")
gradle.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.88.0 — Live-Knotenprotokoll für sichere Mutagenanlagen.**",
    "**Aktueller Entwicklungsstand: 1.89.0 — Kupfererdung für die sichere Knotenrettung.**")
current = """## Aktueller Entwicklungsschritt — 1.89.0

- **Knotenrettung statt Stilllegung:** Geduckt mit Kupferbarren auf die Mutagen-Feldkontrollstation rechtsklicken. Aktive und ungepauste Quellen wechseln von AUSBREITUNG nach ANBAU. Das Item wird nicht verbraucht.
- **Weltheilung bleibt sicher:** Bereits sterilisierte oder nicht mehr aktive Quellen, Redstone-pausierte Knoten und ruhende Knoten bleiben unverändert. Auch der bestehende sichere Amethyst-Neustart und Not-Aus funktionieren weiter.
- **Eigene Forschung:** Die erste tatsächlich erfolgreiche Rettung schaltet den Fortschritt „Aus Gefahr wird Wachstum“ frei; bloßes Scannen oder erfolglose Interaktionen zählen nicht.
- **Spielwelt-Feedback:** Grüne Wachstumssporen, dezente Kristalllichter und ein Stationsklang zeigen die Umwandlung an. Die normale Diagnose erklärt die vier Stationsaktionen.
- **Performance:** Bereits geladener Radius 16 / Höhe ±8, maximal 24 visualisierte Knoten, einmaliger manueller Scan, keine zusätzlichen Ticker oder Chunk-Forceloads.
- **Prüfung:** Neue Regression für Quellregistrierung, sichere Redstone- und Moduswechsel, wiederverwendeten Tick-Aufruf, Forschung, Übersetzungen und sämtliche bestehenden Sicherheitsaktionen.

"""
require("## Aktueller Entwicklungsschritt — 1.88.0" in readme,
        "missing previous current section")
readme = readme.replace("## Aktueller Entwicklungsschritt — 1.88.0",
                        current + "## Aktueller Entwicklungsschritt — 1.88.0", 1)
release = """## Version 1.89.0 — Kupfererdung und Mutagen-Knotenrettung

- **Neuer kontrollierter Rettungspfad:** Kupferbarren plus Schleichen an der Kontrollstation wandelt aktive, unpausierte Ausbreitungsquellen in sichere Kultivierung um, statt sie zu zerstören oder stillzulegen.
- **Spielerfreundlich:** Keine Kupferkosten, keine Nebenwirkungen auf den Charakter, keine Wiederinfektion der geheilten Welt, keine Änderung ruhender oder Redstone-pausierter Knoten.
- **Forschung und sichtbare Spielrückmeldung:** Fortschritt „Aus Gefahr wird Wachstum“, begrenzte Partikeleffekte, eindeutige DE/EN-Meldungen und unterschiedliche Stationsklänge.
- **Technisch begrenzt:** Nur geladene Chunks und eine Node-Tick-Planung als gemeinsame Hilfsfunktion für Kupferrettung und Amethystneustart, keine neuen Dauerabfragen.
- **Qualitätsprüfung:** Regressionen plus kompletter Forge-Build, installierbare JAR und dedizierter Serverstart im GitHub-Actions-Workflow.

"""
require("## Version 1.88.0 —" in readme, "missing last release section")
readme = readme.replace("## Version 1.88.0 —",
                        release + "## Version 1.88.0 —", 1)
require("Aktueller Entwicklungsstand: 1.89.0" in readme,
        "current version headline update failed")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.89 copper-grounding rescue, research milestone, DE/EN, shared scheduling and bounded field feedback installed.")
