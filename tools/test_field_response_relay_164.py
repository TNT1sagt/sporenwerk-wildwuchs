#!/usr/bin/env python3
"""Regression tests for the integrated residual-threat relay mode (1.64.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Containment Relay residual threat 1.64: " + message)


relay = (SRC / "block/MutagenContainmentRelayBlock.java").read_text(encoding="utf-8")
for token in (
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 5)',
    "int mode = (state.getValue(MODE) + step) % 6;",
    'case 5 -> "message.sporenwerk.containment_relay.mode_residual";',
    "int rawThreat = Math.max(Math.max(stationSignal, sirenSignal), fieldThreat);",
    "int protectionBuffer = Math.min(12,",
    "poweredWards * 4 + Math.min(3, counterpulses) * 3",
    "yield rawThreat == 0 ? 0 : Math.max(1, rawThreat - protectionBuffer);",
    "if (tierThreeSoil > 0)",
    "if (tierTwoSoil > 0)",
    "if (tierOneSoil > 0)",
    "if (mutatedCrops > 0)",
    "if (!level.hasChunkAt(new BlockPos(x, center.getY(), z))) continue;",
    "case 4 ->",
    "default -> Math.max(stationSignal, sirenSignal)",
):
    require(token in relay, "missing residual-threat contract: " + token)
require("getChunk(" not in relay and "getChunkNow(" not in relay,
        "residual-threat sampling must not force-load chunks")
require("getTicker(" not in relay and "scheduleTick(" not in relay,
        "residual-threat mode must not add permanent polling")

state = json.loads((ASSETS / "blockstates/mutagen_containment_relay.json").read_text(encoding="utf-8"))
variants = state.get("variants", {})
require(len(variants) == 96, "six modes × sixteen signal strengths must yield 96 variants")
for mode in range(6):
    for signal in range(16):
        key = f"mode={mode},signal={signal}"
        require(variants.get(key, {}).get("model") == "sporenwerk:block/mutagen_containment_relay",
                "missing blockstate " + key)

for filename in ("de_de.json", "en_us.json"):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    for key in (
        "message.sporenwerk.containment_relay.mode_residual",
        "message.sporenwerk.containment_relay.mode_intensity",
        "message.sporenwerk.containment_relay.mode_gap",
    ):
        require(bool(locale.get(key, "").strip()), filename + " missing " + key)

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.64\.0['\"]", build) is not None,
        "artifact must be version 1.64.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.64.0" in readme and "Version 1.63.0" in readme
        and "Aktueller Entwicklungsstand: 1.64.0" in readme,
        "README must contain latest and previous release plus current headline")
print("1.64 residual threat bands, protection buffer, six modes, 96 blockstates, chunk safety, DE/EN and version checks passed.")
