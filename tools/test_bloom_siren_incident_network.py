#!/usr/bin/env python3
"""Regression contract for 1.53.0 Mutagen Bloom incident signalling."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Bloom siren incident regression: " + message)


siren = read("src/main/java/de/sporenwerk/block/MutagenWarningSirenBlock.java")
for token in (
    "public static boolean raiseBloomIncident(Level level, BlockPos pos, int incidentSignal)",
    "if (level.isClientSide || incidentSignal <= 0 || !level.hasChunkAt(pos)) return false;",
    "int next = Math.max(previous, Math.min(15, incidentSignal));",
    "if (riskBand(next) > riskBand(previous))",
    "MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);",
    "public static int riskBand(int signal)",
    "level.getBestNeighborSignal(pos)",
):
    require(token in siren, "latched incident/siren contract missing " + token)
require("player.getServer()" not in siren,
        "incident reporting should not couple siren state to a player/server session")

bloom = read("src/main/java/de/sporenwerk/infection/MutagenBloom.java")
for token in (
    "import de.sporenwerk.block.MutagenWarningSirenBlock;",
    "BLOOM_SIREN_RADIUS = 12",
    "BLOOM_SIREN_VERTICAL_RADIUS = 6",
    "MAX_BLOOM_SIRENS = 4",
    "BLOOM_INCIDENT_SIGNAL = 12",
    "private static int announceBloomToSirens(ServerLevel level, BlockPos origin)",
    "MutagenWarningSirenBlock.raiseBloomIncident(",
    "if (!level.hasChunkAt(cursor)) continue;",
    "announceBloomToSirens(level, origin);",
):
    require(token in bloom, "Mutagen Bloom siren reporting is missing " + token)
require("getChunk(" not in bloom and "getChunkNow(" not in bloom,
        "Bloom incident scan must never force-load chunks")

announce_start = bloom.index("private static int announceBloomToSirens")
announce_end = bloom.index("private static void exposeNearbyPlayers", announce_start)
announce = bloom[announce_start:announce_end]
require("for (int ring = 0; ring <= radius && announced < MAX_BLOOM_SIRENS; ring++)" in announce
        and "announced < MAX_BLOOM_SIRENS" in announce,
        "nearest-first incident fan-out must have a hard four-siren limit")
require(announce.index("if (!level.hasChunkAt(cursor)) continue;")
        < announce.index("MutagenWarningSirenBlock.raiseBloomIncident("),
        "the loaded-chunk guard must precede reads and siren updates")

trigger = bloom.index("public static void tryTrigger")
claim = bloom.index("claimBloom(origin, level.getGameTime(), COOLDOWN_TICKS)", trigger)
announce_call = bloom.index("announceBloomToSirens(level, origin);", trigger)
exposure_call = bloom.index("exposeNearbyPlayers(level, origin);", trigger)
require(claim < announce_call < exposure_call,
        "siren incidents must occur only after the persistent bloom cooldown is claimed")
require("releaseHarvestableSpores(level, origin, random)" in bloom
        and "accelerateCrops(level, origin, random)" in bloom,
        "existing bloom rewards and crop effects must remain intact")

relay = read("src/main/java/de/sporenwerk/block/MutagenContainmentRelayBlock.java")
require("public static void refreshNearbyRelays(Level level, BlockPos sourcePos)" in relay
        and "MAX_REFRESHED_RELAYS_PER_EVENT = 32" in relay
        and "if (!level.hasChunkAt(cursor)) continue;" in relay,
        "incident propagation must use the bounded, chunk-safe relay network")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads(read("src/main/resources/assets/sporenwerk/lang/" + locale))
    require(data.get("message.sporenwerk.warnsirene.acknowledged", "").strip(),
            locale + " lost the existing manual acknowledgement message")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.53\.0['\"]", build) is not None,
        "artifact must be version 1.53.0")
readme = read("README.md")
require("Version 1.53.0" in readme and "Version 1.52.0" in readme,
        "release notes must preserve previous release history")
require("Aktueller Entwicklungsstand: 1.53.0" in readme,
        "README current-version headline must be updated")
print("Bloom event -> critical siren -> bounded relay propagation, acknowledgement preservation and DE/EN passed.")
