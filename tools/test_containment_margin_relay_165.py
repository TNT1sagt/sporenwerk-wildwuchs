#!/usr/bin/env python3
"""Regression tests for the containment-margin comparator mode (1.65.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Containment margin 1.65: " + message)


relay = (SRC / "block/MutagenContainmentRelayBlock.java").read_text(encoding="utf-8")
for token in (
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 6)',
    "int mode = (state.getValue(MODE) + step) % 7;",
    'case 6 -> "message.sporenwerk.containment_relay.mode_margin";',
    "int rawThreat = Math.max(Math.max(stationSignal, sirenSignal), fieldThreat);",
    "int protectionBuffer = Math.min(12,",
    "poweredWards * 4 + Math.min(3, counterpulses) * 3",
    "yield rawThreat == 0 ? 15",
    "Math.max(0, Math.min(15, 8 + protectionBuffer - rawThreat))",
    "if (!level.hasChunkAt(new BlockPos(x, center.getY(), z))) continue;",
):
    require(token in relay, "missing containment-margin behavior: " + token)
require("getChunk(" not in relay and "getChunkNow(" not in relay,
        "containment margin must not force-load chunks")
require("getTicker(" not in relay and "scheduleTick(" not in relay,
        "containment margin must not create permanent polling")

state = json.loads((ASSETS / "blockstates/mutagen_containment_relay.json").read_text(encoding="utf-8"))
variants = state.get("variants", {})
require(len(variants) == 112, "seven modes × sixteen signal strengths must yield 112 variants")
for mode in range(7):
    for signal in range(16):
        key = f"mode={mode},signal={signal}"
        require(variants.get(key, {}).get("model") == "sporenwerk:block/mutagen_containment_relay",
                "missing blockstate " + key)

for filename, expected in (
    ("de_de.json", "Containment-Sicherheitspuffer"),
    ("en_us.json", "Containment margin"),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(locale.get("message.sporenwerk.containment_relay.mode_margin") == expected,
            filename + " missing localized mode")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.65\.0['\"]", build) is not None,
        "artifact must be version 1.65.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.65.0" in readme and "Version 1.64.0" in readme
        and "Aktueller Entwicklungsstand: 1.65.0" in readme,
        "README must retain current and previous release")
print("1.65 containment margin, seven relay modes, 112 variants, loaded-chunk safety and localization passed.")
