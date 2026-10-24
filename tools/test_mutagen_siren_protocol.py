#!/usr/bin/env python3
"""Regression tests for the 1.42.0 siren-aware containment protocol."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen siren protocol regression: " + message)


station = (SRC / "block/MutagenFieldControlStationBlock.java").read_text(encoding="utf-8")
siren = (SRC / "block/MutagenWarningSirenBlock.java").read_text(encoding="utf-8")
for token in (
    "int sirenSignals = 0, criticalSirenSignals = 0, highestSirenSignal = 0;",
    "bs.is(ModBlocks.MUTAGEN_WARNSIRENE.get())",
    "bs.hasProperty(MutagenWarningSirenBlock.SIGNAL)",
    "bs.getValue(MutagenWarningSirenBlock.SIGNAL)",
    "MutagenWarningSirenBlock.riskBand(sirenSignal) == 3",
    "highestSirenSignal = Math.max(highestSirenSignal, sirenSignal)",
    "private static String containmentProtocolKey(Survey s)",
    "s.criticalSirenSignals() > 0",
    "s.sirenSignals() > 0",
    "s.poweredWards() == 0 && s.availablePulses() == 0",
    "message.sporenwerk.fieldstation.siren_audit",
    "message.sporenwerk.fieldstation.protocol.critical_siren",
    "message.sporenwerk.fieldstation.protocol.hotspot_unprotected",
    "ChatFormatting.RED",
    "ChatFormatting.GREEN",
):
    require(token in station, "station is missing siren/protocol logic: " + token)
require("public static int riskBand(int signal)" in siren,
        "the protocol must share the siren's source-of-truth severity bands")
require("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;" in station,
        "siren sampling must keep skipping unloaded chunks")
require("getChunk(" not in station and "getChunkNow(" not in station,
        "siren sampling must not force-load chunks")
for filename in ("de_de.json", "en_us.json"):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    report = locale.get("message.sporenwerk.fieldstation.siren_audit", "")
    require(report.count("%s") == 3, filename + " must report all three siren metrics")
    for suffix in (
        "critical_siren", "siren_signal", "hotspot_unprotected", "ward_missing",
        "reserve_empty", "verify_coverage", "mutagen_soil", "crop_activity", "clear"
    ):
        key = "message.sporenwerk.fieldstation.protocol." + suffix
        require(bool(locale.get(key, "").strip()), filename + " missing " + key)

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.42\.0['\"]", build) is not None,
        "artifact must be version 1.42.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.42.0" in readme and "Version 1.41.0" in readme
        and "Version 1.40.0" in readme,
        "release notes must add 1.42.0 and preserve previous milestones")
require("Aktueller Entwicklungsstand: 1.42.0" in readme,
        "current-version headline must be updated")
print("Siren signal sampling, severity priority, actionable protocol, loaded-chunk safety, DE/EN text and 1.42.0 passed.")
