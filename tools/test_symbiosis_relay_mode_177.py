#!/usr/bin/env python3
"""Regression tests for the symbiosis harvest readiness comparator mode (1.77.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Symbiosis relay 1.77 regression: " + message)


relay = read("src/main/java/de/sporenwerk/block/MutagenContainmentRelayBlock.java")
for token in (
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 8)',
    "(state.getValue(MODE) + step) % 9",
    'case 8 -> "message.sporenwerk.containment_relay.mode_symbiosis"',
    'case 8 -> Math.min(15, symbiosisReadyCenters)',
    "Map<Long, Integer> cropKindsByPosition = new HashMap<>();",
    "List<BlockPos> matureCropPositions = new ArrayList<>();",
    "scanned.is(ModBlocks.FASERROHR.get()) ? 1",
    "scanned.is(ModBlocks.BERNSTEINKAPPE.get()) ? 2",
    "scanned.is(ModBlocks.ROTWURZEL.get()) ? 4",
    "scanned.is(ModBlocks.FILTERMOOS.get()) ? 8 : 0",
    "crop.isMaxAge(scanned)",
    "Integer.bitCount(cropSpeciesMask) >= 3",
    "Integer.bitCount(nearbySpeciesMask) >= 3",
    "MutationField.mutagenStrengthAt(level, maturePos) >= 2",
    "symbiosisReadyCenters >= 15",
    "MAX_REFRESHED_RELAYS_PER_EVENT",
    "public static void refreshNearbyRelays(Level level, BlockPos sourcePos)",
):
    require(token in relay, "comparator readiness contract missing: " + token)
require("getChunk(" not in relay and "getChunkNow(" not in relay,
        "relay must not force-load chunks")
require("getTicker(" not in relay and "BlockEntityTicker" not in relay,
        "relay must not add a ticking block entity")

state = json.loads((ASSETS / "blockstates/mutagen_containment_relay.json").read_text(encoding="utf-8"))
variants = state.get("variants", {})
require(len(variants) == 144, "expected 9 relay modes × 16 comparator levels")
for mode in range(9):
    for signal in range(16):
        key = f"mode={mode},signal={signal}"
        require(variants.get(key, {}).get("model") == "sporenwerk:block/mutagen_containment_relay",
                "missing or incorrect relay state " + key)
model = json.loads((ASSETS / "models/block/mutagen_containment_relay.json").read_text(encoding="utf-8"))
require(model.get("parent") == "minecraft:block/cube_column",
        "relay must retain the existing Minecraft cube-column model")

crop = read("src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java")
for token in (
    "MutagenSymbiosis.countCropSpecies(level, pos) >= 3",
    "MutagenSymbiosis.countCropSpecies(level, pos) >= 2",
    "int ageBeforeGrowth = state.getValue(CropBlock.AGE);",
    "afterGrowth.getValue(CropBlock.AGE) == getMaxAge()",
    "MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos)",
    "public void onPlace(BlockState state, Level level, BlockPos pos",
    "public void onRemove(BlockState state, Level level, BlockPos pos",
):
    require(token in crop, "crop event refresh contract missing: " + token)

for locale, expected in (
    ("de_de.json", "Symbiose-Erntebereitschaft"),
    ("en_us.json", "Symbiosis harvest readiness"),
):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    require(data.get("message.sporenwerk.containment_relay.mode_symbiosis") == expected,
            locale + " lacks the mode-8 label")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.77\.0['\"]", build) is not None,
        "artifact must be version 1.77.0")
readme = read("README.md")
require("Version 1.77.0" in readme and "Version 1.76.0" in readme
        and "Aktueller Entwicklungsstand: 1.77.0" in readme,
        "release notes must preserve 1.76 and identify the current version")
print("1.77 symbiosis comparator mode, all 144 blockstates, event refresh, loaded-chunk safety, locale and release metadata passed.")
