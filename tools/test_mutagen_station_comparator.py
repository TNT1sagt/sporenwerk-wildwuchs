#!/usr/bin/env python3
"""Regression tests for the Mutagen Field Control Station redstone hazard output."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen station comparator regression: " + message)


station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
for token in (
    'IntegerProperty.create("power", 0, 15)',
    "registerDefaultState(defaultBlockState().setValue(POWER, 0))",
    "builder.add(POWER)",
    "boolean hasAnalogOutputSignal(BlockState state)",
    "int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos)",
    "return state.getValue(POWER)",
    "private static int comparatorSignal(Survey s)",
    "if (s.highSoil() > 0)",
    "11 + Math.min(4, (s.highSoil() - 1) / 4)",
    "if (s.soil() > 0)",
    "4 + Math.min(6, s.soil() / 8)",
    "if (s.crops() > 0) return 3",
    "return 0",
    "int signal = comparatorSignal(s)",
    "state.setValue(POWER, signal)",
    "message.sporenwerk.fieldstation.comparator",
    "HORIZONTAL_SCAN_RADIUS = 16",
    "VERTICAL_SCAN_RADIUS = 8",
):
    require(token in station, "station is missing comparator behavior: " + token)

# The scan must remain interaction-driven. The output method may only read POWER.
output_start = station.index("public int getAnalogOutputSignal")
output_end = station.index("\n    }", output_start)
output_method = station[output_start:output_end]
require("survey(" not in output_method and "getBlockState(" not in output_method,
        "comparator polling must not trigger a world scan")

states = json.loads((ASSETS / "blockstates/mutagenfeld_kontrollstation.json").read_text(encoding="utf-8"))
variants = states["variants"]
require(len(variants) == 16, "all 16 power property values must be defined")
for power in range(16):
    key = f"power={power}"
    require(key in variants, f"missing blockstate variant {key}")
    require(variants[key]["model"] == "sporenwerk:block/mutagenfeld_kontrollstation",
            f"power state {power} should preserve the station model")

recipe = json.loads((RES / "data/sporenwerk/recipes/mutagenfeld_kontrollstation.json").read_text(encoding="utf-8"))
require(recipe["result"]["item"] == "sporenwerk:mutagenfeld_kontrollstation",
        "the station recipe must remain available after adding POWER")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    message = data.get("message.sporenwerk.fieldstation.comparator", "")
    require("%s/15" in message and "Comparator" in message or "%s/15" in message and "comparator" in message,
            locale + " must explain the hazard output")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.30\.0['\"]", build) is not None,
        "artifact must be version 1.30.0")
readme = read("README.md")
require("Version 1.30.0" in readme and "Version 1.29.0" in readme,
        "release notes must add 1.30.0 and preserve 1.29.0")

print("Mutagen station comparator output, cached scan behavior, all blockstate values, locales, and version passed.")
