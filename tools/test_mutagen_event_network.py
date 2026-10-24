#!/usr/bin/env python3
"""Regression tests for event-driven, bounded Containment Relay updates (1.44.0)."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Containment event routing regression: " + message)


relay = (SRC / "block/MutagenContainmentRelayBlock.java").read_text(encoding="utf-8")
station = (SRC / "block/MutagenFieldControlStationBlock.java").read_text(encoding="utf-8")
siren = (SRC / "block/MutagenWarningSirenBlock.java").read_text(encoding="utf-8")
ward = (SRC / "block/SporeWardBlock.java").read_text(encoding="utf-8")
dampener = (SRC / "block/MutagenResonanceDampenerBlock.java").read_text(encoding="utf-8")
pirscher = (SRC / "entity/KristallpirscherEntity.java").read_text(encoding="utf-8")

for token in (
    "MAX_REFRESHED_RELAYS_PER_EVENT = 32",
    "public static void refreshNearbyRelays(Level level, BlockPos sourcePos)",
    "if (level.isClientSide) return;",
    "for (int ring = 0; ring <= radius && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; ring++)",
    "level.hasChunkAt(cursor)",
    "refreshed >= MAX_REFRESHED_RELAYS_PER_EVENT",
    "int signal = evaluate(level, relayPos, candidate.getValue(MODE));",
    "level.setBlock(relayPos, candidate.setValue(SIGNAL, signal), 3)",
):
    require(token in relay, "relay event broadcaster is missing: " + token)
require("getChunk(" not in relay and "getChunkNow(" not in relay,
        "event routing must never force-load chunks")
require(relay.count("refreshNearbyRelays(") >= 1, "public refresh API missing")
require("MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);" in station,
        "station comparator changes must refresh cached relay outputs")
require(siren.count("MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);") >= 2,
        "siren escalation and acknowledgement must refresh relays")
require(ward.count("MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);") >= 2,
        "Spore Ward on/off transitions must refresh relays")
require("MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);" in dampener,
        "manual dampener recharge must refresh reserve output")
require("de.sporenwerk.block.MutagenContainmentRelayBlock.refreshNearbyRelays(level(), pos);" in pirscher,
        "charge-consuming counterpulse must refresh reserve output")
require("scheduleTick(" not in relay and "getTicker(" not in relay,
        "event-driven relay refresh must not add its own ticker")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.44\.0['\"]", build) is not None,
        "artifact must be version 1.44.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.44.0" in readme and "Version 1.43.0" in readme,
        "release notes must preserve 1.43.0 and add 1.44.0")
require("Aktueller Entwicklungsstand: 1.44.0" in readme,
        "current README development headline is stale")
print("Event-driven station/siren/ward/dampener notifications, 32-relay cap, loaded-chunk checks, no ticker and 1.44.0 passed.")
