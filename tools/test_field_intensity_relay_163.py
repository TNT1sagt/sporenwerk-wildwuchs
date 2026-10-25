#!/usr/bin/env python3
"""Regression tests for the live Mutagen field-intensity relay mode (1.63.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Containment Relay field intensity 1.63: " + message)


relay = (SRC / "block/MutagenContainmentRelayBlock.java").read_text(encoding="utf-8")
for token in (
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 4)',
    "int mode = (state.getValue(MODE) + step) % 5;",
    'case 4 -> "message.sporenwerk.containment_relay.mode_intensity";',
    "int tierOneSoil = 0, tierTwoSoil = 0, tierThreeSoil = 0, mutatedCrops = 0;",
    "scanned.is(ModBlocks.MUTAGEN_BODEN.get())",
    "scanned.hasProperty(InfestedTerrainBlock.MUTAGEN_LEVEL)",
    "scanned.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL)",
    "scanned.getBlock() instanceof AbstractSporeCropBlock",
    "scanned.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0",
    "if (tierThreeSoil > 0) yield Math.min(15, 11 + Math.min(4, (tierThreeSoil - 1) / 4));",
    "if (tierTwoSoil > 0) yield Math.min(10, 7 + Math.min(3, (tierTwoSoil - 1) / 8));",
    "if (tierOneSoil > 0) yield Math.min(6, 3 + Math.min(3, (tierOneSoil - 1) / 16));",
    "if (mutatedCrops > 0) yield 2;",
    "if (!level.hasChunkAt(new BlockPos(x, center.getY(), z))) continue;",
    "case 1 ->",
    "case 2 -> Math.min(15, counterpulses * 5)",
    "case 3 ->",
    "default -> Math.max(stationSignal, sirenSignal)",
):
    require(token in relay, "missing relay mode contract: " + token)
require("getChunk(" not in relay and "getChunkNow(" not in relay,
        "live field scan must not force-load chunks")
require("scheduleTick(" not in relay and "getTicker(" not in relay,
        "field scan must not introduce a permanent polling loop")

state = json.loads((ASSETS / "blockstates/mutagen_containment_relay.json").read_text(encoding="utf-8"))
variants = state.get("variants", {})
require(len(variants) == 80, "five modes × sixteen signals must yield 80 blockstate variants")
for mode in range(5):
    for signal in range(16):
        key = f"mode={mode},signal={signal}"
        require(variants.get(key, {}).get("model") == "sporenwerk:block/mutagen_containment_relay",
                "missing blockstate variant " + key)

for filename in ("de_de.json", "en_us.json"):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(bool(locale.get("message.sporenwerk.containment_relay.mode_intensity", "").strip()),
            filename + " missing field-intensity mode name")
    require(bool(locale.get("message.sporenwerk.containment_relay.mode_gap", "").strip()),
            filename + " must retain existing mode translations")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.63\.0['\"]", build) is not None,
        "artifact must be version 1.63.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.63.0" in readme and "Version 1.62.0" in readme
        and "Aktueller Entwicklungsstand: 1.63.0" in readme,
        "README must include current release and retain 1.62.0 history")
print("1.63 live field-intensity mode, five-mode cycling, tier outputs, 80 blockstates, chunk safety, translations and version checks passed.")
