#!/usr/bin/env python3
"""Regression tests for station containment audit reporting (1.41.0)."""
from pathlib import Path
import json, re, sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"
def require(ok, message):
    if not ok: raise SystemExit("Mutagen containment audit regression: " + message)
station = (SRC / "block/MutagenFieldControlStationBlock.java").read_text(encoding="utf-8")
for token in (
    "int poweredWards = 0, dampeners = 0, chargedDampeners = 0, availablePulses = 0;",
    "bs.is(ModBlocks.SPORENABWEHR.get())", "bs.hasProperty(SporeWardBlock.POWERED)",
    "bs.getValue(SporeWardBlock.POWERED)", "bs.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())",
    "bs.getValue(MutagenResonanceDampenerBlock.CHARGE)", "if (charge > 0) chargedDampeners++;",
    "availablePulses += charge;",
    "s.poweredWards(), s.chargedDampeners(), s.dampeners(), s.availablePulses()",
    "message.sporenwerk.fieldstation.containment", "private record Survey("):
    require(token in station, "station missing real-state containment counter: " + token)
require("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;" in station,
        "survey must continue skipping unloaded chunks")
require("getChunk(" not in station and "getChunkNow(" not in station,
        "containment audit must not force-load chunks")
require(station.index("Survey s = survey(serverLevel, pos);") < station.index("message.sporenwerk.fieldstation.containment"),
        "report must use the actual interaction-driven survey")
for filename in ("de_de.json", "en_us.json"):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    message = locale.get("message.sporenwerk.fieldstation.containment", "")
    require(bool(message) and message.count("%s") == 4,
            filename + " must expose all four containment counts")
build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.41\.0['\"]", build) is not None,
        "artifact must be version 1.41.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.41.0" in readme and "Version 1.40.0" in readme,
        "release notes must add 1.41.0 and preserve 1.40.0")
require("Aktueller Entwicklungsstand: 1.41.0" in readme,
        "current-version headline must be updated")
print("Containment scan, live ward state, real dampener charges, chunk safety, DE/EN text and 1.41.0 passed.")
