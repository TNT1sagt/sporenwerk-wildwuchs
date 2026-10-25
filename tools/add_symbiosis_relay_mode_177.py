#!/usr/bin/env python3
"""Add an event-driven symbiosis harvest comparator mode to the Mutagen Containment Relay (1.77.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Symbiosis relay 1.77: " + message)


def add_import(path, anchor, import_line):
    source = path.read_text(encoding="utf-8")
    if import_line in source:
        return
    require(anchor in source, "missing import anchor for " + import_line)
    path.write_text(source.replace(anchor, anchor + "\n" + import_line, 1), encoding="utf-8")


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# Add a new native comparator mode after all earlier relay modes have been installed.
relay_path = SRC / "block/MutagenContainmentRelayBlock.java"
for imp in (
    "import de.sporenwerk.infection.MutationField;",
    "import net.minecraft.world.level.block.CropBlock;",
    "import java.util.ArrayList;",
    "import java.util.HashMap;",
    "import java.util.List;",
    "import java.util.Map;",
):
    add_import(relay_path, "import de.sporenwerk.registry.ModBlocks;", imp)

relay = relay_path.read_text(encoding="utf-8")
mode_old = 'IntegerProperty MODE = IntegerProperty.create("mode", 0, 7);'
mode_new = 'IntegerProperty MODE = IntegerProperty.create("mode", 0, 8);'
if mode_new not in relay:
    require(mode_old in relay, "expected the current final relay to have modes 0–7")
    relay = relay.replace(mode_old, mode_new, 1)
cycle_old = "int mode = (state.getValue(MODE) + step) % 8;"
cycle_new = "int mode = (state.getValue(MODE) + step) % 9;"
if cycle_new not in relay:
    require(cycle_old in relay, "could not locate relay mode-cycle limit")
    relay = relay.replace(cycle_old, cycle_new, 1)

mode_key = '            case 7 -> "message.sporenwerk.containment_relay.mode_boss";'
mode_key_new = mode_key + '\n            case 8 -> "message.sporenwerk.containment_relay.mode_symbiosis";'
if "message.sporenwerk.containment_relay.mode_symbiosis" not in relay:
    require(mode_key in relay, "could not locate final boss mode in relay label switch")
    relay = relay.replace(mode_key, mode_key_new, 1)

# Only mode 8 collects crop data; the other eight modes keep their current cost and behavior.
eval_start = relay.find("private static int evaluate(")
require(eval_start >= 0, "could not locate relay evaluate method")
eval_text = relay[eval_start:]
counter_anchor = "        int counterpulses = 0;"
counter_add = counter_anchor + """
        int cropSpeciesMask = 0;
        Map<Long, Integer> cropKindsByPosition = new HashMap<>();
        List<BlockPos> matureCropPositions = new ArrayList<>();"""
if "Map<Long, Integer> cropKindsByPosition = new HashMap<>();" not in eval_text:
    require(counter_anchor in eval_text, "could not locate relay scan counters")
    eval_text = eval_text.replace(counter_anchor, counter_add, 1)

scan_anchor = "                    BlockState scanned = level.getBlockState(cursor);"
scan_add = scan_anchor + """
                    if (mode == 8) {
                        int cropKind = scanned.is(ModBlocks.FASERROHR.get()) ? 1
                                : scanned.is(ModBlocks.BERNSTEINKAPPE.get()) ? 2
                                : scanned.is(ModBlocks.ROTWURZEL.get()) ? 4
                                : scanned.is(ModBlocks.FILTERMOOS.get()) ? 8 : 0;
                        if (cropKind != 0) {
                            cropSpeciesMask |= cropKind;
                            cropKindsByPosition.put(cursor.asLong(), cropKind);
                            if (scanned.getBlock() instanceof CropBlock crop && crop.isMaxAge(scanned)) {
                                matureCropPositions.add(cursor.immutable());
                            }
                        }
                    }"""
if "cropKindsByPosition.put(cursor.asLong(), cropKind);" not in eval_text:
    require(scan_anchor in eval_text, "could not locate bounded relay scan block")
    eval_text = eval_text.replace(scan_anchor, scan_add, 1)

switch_anchor = "        return switch (mode) {"
readiness = """
        int symbiosisReadyCenters = 0;
        if (mode == 8 && Integer.bitCount(cropSpeciesMask) >= 3) {
            BlockPos.MutableBlockPos speciesProbe = new BlockPos.MutableBlockPos();
            int symbiosisRadiusSquared = 3 * 3;
            matureSearch:
            for (BlockPos maturePos : matureCropPositions) {
                int nearbySpeciesMask = 0;
                speciesSearch:
                for (int dx = -3; dx <= 3; dx++) {
                    for (int dz = -3; dz <= 3; dz++) {
                        if (dx * dx + dz * dz > symbiosisRadiusSquared) continue;
                        for (int dy = -1; dy <= 1; dy++) {
                            speciesProbe.set(maturePos.getX() + dx, maturePos.getY() + dy,
                                    maturePos.getZ() + dz);
                            nearbySpeciesMask |= cropKindsByPosition.getOrDefault(speciesProbe.asLong(), 0);
                            if (Integer.bitCount(nearbySpeciesMask) >= 3) break speciesSearch;
                        }
                    }
                }
                if (Integer.bitCount(nearbySpeciesMask) >= 3
                        && MutationField.mutagenStrengthAt(level, maturePos) >= 2) {
                    symbiosisReadyCenters++;
                    if (symbiosisReadyCenters >= 15) break matureSearch;
                }
            }
        }

"""
if "int symbiosisReadyCenters = 0;" not in eval_text:
    require(switch_anchor in eval_text, "could not locate relay result switch")
    eval_text = eval_text.replace(switch_anchor, readiness + switch_anchor, 1)
    eval_switch = eval_text.index(switch_anchor)
    default_at = eval_text.find("default ->", eval_switch)
    require(default_at >= 0, "could not locate relay result fallback")
    eval_text = eval_text[:default_at] + "            case 8 -> Math.min(15, symbiosisReadyCenters);\n" + eval_text[default_at:]

relay = relay[:eval_start] + eval_text
# Crop events need only refresh symbiosis relays; preserve the broader existing refresh path
# for alarms and boss phases, but avoid rescanning each nearby legacy relay per crop event.
symbiosis_refresh = """    /**
     * Recalculate only mode-8 symbiosis relays after a local crop change.
     * The spatial search is loaded-chunk-only and shares the existing event cap.
     */
    public static void refreshNearbySymbiosisRelays(Level level, BlockPos sourcePos) {
        if (level.isClientSide) return;
        int radius = HORIZONTAL_SCAN_RADIUS;
        int radiusSquared = radius * radius;
        int refreshed = 0;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

        for (int ring = 0; ring <= radius && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; ring++) {
            for (int dx = -ring; dx <= ring && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; dx++) {
                for (int dz = -ring; dz <= ring && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != ring
                            || dx * dx + dz * dz > radiusSquared) continue;
                    int x = sourcePos.getX() + dx;
                    int z = sourcePos.getZ() + dz;
                    if (!level.hasChunkAt(new BlockPos(x, sourcePos.getY(), z))) continue;
                    for (int dy = -VERTICAL_SCAN_RADIUS;
                         dy <= VERTICAL_SCAN_RADIUS && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; dy++) {
                        int y = sourcePos.getY() + dy;
                        if (y < level.getMinBuildHeight() || y >= level.getMaxBuildHeight()) continue;
                        cursor.set(x, y, z);
                        BlockState candidate = level.getBlockState(cursor);
                        if (!(candidate.getBlock() instanceof MutagenContainmentRelayBlock)
                                || candidate.getValue(MODE) != 8) continue;
                        BlockPos relayPos = cursor.immutable();
                        int signal = evaluate(level, relayPos, 8);
                        if (candidate.getValue(SIGNAL) != signal) {
                            level.setBlock(relayPos, candidate.setValue(SIGNAL, signal), 3);
                        }
                        refreshed++;
                    }
                }
            }
        }
    }

"""
if "public static void refreshNearbySymbiosisRelays(" not in relay:
    require_anchor = "    private static boolean isRelevantInput(Block block) {"
    if require_anchor not in relay:
        raise SystemExit("Symbiosis relay 1.77: could not locate relay refresh insertion point")
    relay = relay.replace(require_anchor, symbiosis_refresh + require_anchor, 1)

relay_path.write_text(relay, encoding="utf-8")
relay = relay_path.read_text(encoding="utf-8")
for token in (
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 8)',
    "(state.getValue(MODE) + step) % 9",
    'case 8 -> "message.sporenwerk.containment_relay.mode_symbiosis"',
    "cropKindsByPosition.put(cursor.asLong(), cropKind)",
    "crop.isMaxAge(scanned)",
    "Integer.bitCount(cropSpeciesMask) >= 3",
    "MutationField.mutagenStrengthAt(level, maturePos) >= 2",
    "case 8 -> Math.min(15, symbiosisReadyCenters)",
):
    require(token in relay, "relay readiness contract missing " + token)
require("getChunk(" not in relay and "getChunkNow(" not in relay,
        "symbiosis relay must never force-load chunks")
require("getTicker(" not in relay and "BlockEntityTicker" not in relay,
        "relay must remain event-driven without a ticker")

# Mode 8 outputs the number of mature harvest centers that actually satisfy the crop
# diversity + live tier-II/III field rule. Regenerate all legal MODE × SIGNAL blockstates.
blockstate_path = ASSETS / "blockstates/mutagen_containment_relay.json"
blockstate = {}
for mode in range(9):
    for signal in range(16):
        blockstate[f"mode={mode},signal={signal}"] = {
            "model": "sporenwerk:block/mutagen_containment_relay"
        }
blockstate_path.write_text(json.dumps({"variants": blockstate}, indent=2) + "\n", encoding="utf-8")

for locale, value in (
    ("de_de.json", "Symbiose-Erntebereitschaft"),
    ("en_us.json", "Symbiosis harvest readiness"),
):
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data["message.sporenwerk.containment_relay.mode_symbiosis"] = value
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Refresh existing relay outputs only on relevant crop events. This preserves the no-ticker
# architecture while ensuring a planted third species, a newly mature crop, or crop removal
# cannot leave the symbiosis comparator stuck on an old signal.
crop_path = SRC / "block/crop/AbstractSporeCropBlock.java"
for imp in (
    "import de.sporenwerk.block.MutagenContainmentRelayBlock;",
    "import de.sporenwerk.infection.MutagenSymbiosis;",
):
    add_import(crop_path, "package de.sporenwerk.block.crop;", imp)
crop = crop_path.read_text(encoding="utf-8")
place_anchor = "    @Override\n    public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {"
event_hooks = """    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean isMoving) {
        super.onPlace(state, level, pos, oldState, isMoving);
        if (!level.isClientSide && oldState.getBlock() != state.getBlock()
                && MutationField.mutagenStrengthAt(level, pos) >= 2
                && MutagenSymbiosis.countCropSpecies(level, pos) >= 3) {
            MutagenContainmentRelayBlock.refreshNearbySymbiosisRelays(level, pos);
        }
    }

    @Override
    public void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean isMoving) {
        super.onRemove(state, level, pos, newState, isMoving);
        if (!level.isClientSide && state.getBlock() != newState.getBlock()
                && MutationField.mutagenStrengthAt(level, pos) >= 2
                && MutagenSymbiosis.countCropSpecies(level, pos) >= 2) {
            MutagenContainmentRelayBlock.refreshNearbySymbiosisRelays(level, pos);
        }
    }

"""
if "MutagenSymbiosis.countCropSpecies(level, pos) >= 3" not in crop:
    require(place_anchor in crop, "could not locate crop random-tick method for event hooks")
    crop = crop.replace(place_anchor, event_hooks + place_anchor, 1)

tick_anchor = "        super.randomTick(state, level, pos, random);"
tick_add = """        int ageBeforeGrowth = state.getValue(CropBlock.AGE);
        super.randomTick(state, level, pos, random);
        BlockState afterGrowth = level.getBlockState(pos);
        if (!level.isClientSide && ageBeforeGrowth < getMaxAge()
                && afterGrowth.getBlock() == this
                && afterGrowth.getValue(CropBlock.AGE) == getMaxAge()
                && MutationField.mutagenStrengthAt(level, pos) >= 2
                && MutagenSymbiosis.countCropSpecies(level, pos) >= 3) {
            MutagenContainmentRelayBlock.refreshNearbySymbiosisRelays(level, pos);
        }"""
if "int ageBeforeGrowth = state.getValue(CropBlock.AGE);" not in crop:
    require(tick_anchor in crop, "could not locate crop growth update")
    crop = crop.replace(tick_anchor, tick_add, 1)
crop_path.write_text(crop, encoding="utf-8")
for token in (
    "public void onPlace(BlockState state, Level level, BlockPos pos",
    "public void onRemove(BlockState state, Level level, BlockPos pos",
    "int ageBeforeGrowth = state.getValue(CropBlock.AGE);",
    "MutagenContainmentRelayBlock.refreshNearbySymbiosisRelays(level, pos);",
):
    require(token in crop_path.read_text(encoding="utf-8"), "crop event refresh missing " + token)

# Preserve every older relay regression while raising its full mode × signal-state expectations.
for test_name in (
    "test_mutagen_containment_relay.py",
    "test_field_intensity_relay_163.py",
    "test_field_response_relay_164.py",
    "test_containment_margin_relay_165.py",
    "test_boss_response_relay_168.py",
):
    test_path = ROOT / "tools" / test_name
    if not test_path.exists():
        continue
    source = test_path.read_text(encoding="utf-8")
    for old, new in (
        ('IntegerProperty MODE = IntegerProperty.create("mode", 0, 7)',
         'IntegerProperty MODE = IntegerProperty.create("mode", 0, 8)'),
        ("int mode = (state.getValue(MODE) + step) % 8;",
         "int mode = (state.getValue(MODE) + step) % 9;"),
        ("len(variants) == 128", "len(variants) == 144"),
        ("for mode in range(8):", "for mode in range(9):"),
        ("all 8 MODE × 16 SIGNAL", "all 9 MODE × 16 SIGNAL"),
        ("eight modes × sixteen signals", "nine modes × sixteen signals"),
        ("eight modes × sixteen signal strengths", "nine modes × sixteen signal strengths"),
    ):
        if old in source and new not in source:
            source = source.replace(old, new, 1)
    test_path.write_text(source, encoding="utf-8")

# Advance all current-artifact assertions while retaining the release history.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_symbiosis_relay_mode_177.py":
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.76.0",
                               "Aktueller Entwicklungsstand: 1.77.0")
    updated = updated.replace(r"1\.76\.0", r"1\.77\.0")
    updated = updated.replace("artifact must be version 1.76.0",
                              "artifact must be version 1.77.0")
    updated = updated.replace(
        '"Version 1.76.0" in readme and "Version 1.75.0" in readme',
        '"Version 1.77.0" in readme and "Version 1.76.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.77.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Gradle artifact version")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.77.0

- **Symbiose als Redstone-Signal:** Das Containment-Relais erhält Modus 8 für die Zahl reifer Erntezentren, die drei Sporenwerk-Arten in unmittelbarer Nähe und ein aktives Mutagenfeld der Stufe II/III besitzen.
- **Direkte Farm-Automation:** Der Comparator gibt 0 aus, wenn keine passenden Erntezentren bereit sind, und 1–15 entsprechend der Zahl erkannter reifer Zentren (bei 15 gedeckelt). So können Sortierer, Lampen, Trichter-Taktung oder Farm-Stoppschaltungen reagieren.
- **Echte Laufzeitbedingungen:** Die Prüfung verwendet die vier registrierten Sporenwerk-Arten und die aktuelle Feldstärke, nicht bloß eine gespeicherte Feldfarbe oder globale Pflanzenzahl.
- **Ereignisgesteuert:** Pflanzen, reife Ernte und Pflanzenentfernung aktualisieren nahe Relais, ohne neue Dauer-Ticker einzubauen. Der Scan bleibt auf geladene Chunks begrenzt.
- **Qualitätssicherung:** Alle 144 Relais-Blockzustände, DE/EN-Beschriftung, Wachstums-/Pflanzenänderungsereignisse, Chunk-Sicherheit und Release-Metadaten werden geprüft.

"""
if "## Aktueller Entwicklungsschritt — 1.77.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.76.0"
    idx = readme.find(marker)
    require(idx >= 0, "could not find active 1.76 development section")
    readme = readme[:idx] + current + readme[idx:]

release = """## Version 1.77.0 — Symbiose-Ernte als Redstone-Signal

- **Neuer Containment-Relais-Modus 8:** Das Relais zählt bis zu 15 reife Sporenwerk-Erntezentren, die lokal mindestens drei verschiedene Kulturen und eine echte Feldstärke II/III besitzen.
- **Farmen lassen sich steuern:** Der Comparator-Wert kann als Erntereife-Signal für Sortierung, Lagerung, Beleuchtung, Farmstopp oder weitere Redstone-Schaltungen genutzt werden.
- **Aktualisierung bei relevanten Ereignissen:** Eine platzierte dritte Kulturart, der Reifeschritt einer passenden Pflanze und das Entfernen von Kulturen stoßen eine begrenzte Relais-Aktualisierung an. Es kommt kein globaler oder per-Block-Ticker hinzu.
- **Sicherheit und Lesbarkeit:** Der bestehende Relay-Scan bleibt geladen-chunk-basiert, das Blockmodell bleibt Minecraft-Pixelart, alle 9×16 Zustandskombinationen besitzen Modellzuordnungen und die neue Betriebsart ist auf Deutsch/Englisch beschriftet.

"""
if "## Version 1.77.0 — Symbiose-Ernte als Redstone-Signal" not in readme:
    marker = "## Version 1.76.0 —"
    idx = readme.find(marker)
    require(idx >= 0, "could not find historical 1.76 release section")
    readme = readme[:idx] + release + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.76.0 — Biodiversitätsdiagnose der Mutagen-Kontrollstation.**",
    "**Aktueller Entwicklungsstand: 1.77.0 — Symbiose-Ernte als Redstone-Signal.**")
require("Aktueller Entwicklungsstand: 1.77.0" in readme,
        "README current-version headline was not updated")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.77.0 generated: event-driven symbiosis harvest readiness now powers a new Containment Relay comparator mode.")
