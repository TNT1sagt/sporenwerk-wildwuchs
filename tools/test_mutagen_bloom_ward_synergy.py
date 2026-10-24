#!/usr/bin/env python3
"""Regression tests for the powered Spore Ward / Mutagen Bloom interaction (1.40.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen Bloom / Spore Ward synergy regression: " + message)


ward = read("src/main/java/de/sporenwerk/block/SporeWardBlock.java")
for token in (
    "public static final int HORIZONTAL_RADIUS = 8;",
    "public static final int VERTICAL_RADIUS = 3;",
    "public static final BooleanProperty POWERED = BlockStateProperties.POWERED;",
    "level.hasNeighborSignal(pos)",
    'putLong("SporenwerkWardRepelledUntil", repelUntil)',
):
    require(token in ward, "ward protection source of truth missing " + token)

bloom = read("src/main/java/de/sporenwerk/infection/MutagenBloom.java")
for token in (
    "private static boolean isProtectedByPoweredWard(ServerLevel level, BlockPos playerPos)",
    "SporeWardBlock.HORIZONTAL_RADIUS",
    "SporeWardBlock.VERTICAL_RADIUS",
    "if (!level.hasChunkAt(wardPos)) continue;",
    "wardState.is(ModBlocks.SPORENABWEHR.get())",
    "wardState.hasProperty(SporeWardBlock.POWERED)",
    "wardState.getValue(SporeWardBlock.POWERED)",
    "isProtectedByPoweredWard(level, player.blockPosition())",
    "message.sporenwerk.mutagen.bloom_warded",
    "ParticleTypes.END_ROD",
    "MutationField.hasAnchor(level, player.blockPosition())",
    "awardBloomDiscovery(player)",
    "InfectionState.setLevel(player, InfectionState.level(player) + 1)",
    "releaseHarvestableSpores(level, origin, random)",
    "accelerateCrops(level, origin, random)",
):
    require(token in bloom, "bloom interaction or preserved hazard/reward missing " + token)

helper_start = bloom.index("private static boolean isProtectedByPoweredWard")
helper_end = bloom.index("private static void exposeNearbyPlayers", helper_start)
helper = bloom[helper_start:helper_end]
require("for (int dx = -radius; dx <= radius; dx++)" in helper
        and "for (int dy = -SporeWardBlock.VERTICAL_RADIUS;" in helper,
        "ward check must remain bounded to the declared protection volume")
require(helper.index("if (!level.hasChunkAt(wardPos)) continue;")
        < helper.index("level.getBlockState(wardPos)"),
        "ward query must check chunk-loaded state before reading a block")
require("getChunk(" not in helper and "getChunkNow(" not in helper,
        "ward interaction must never force-load a chunk")

exposure = bloom[bloom.index("private static void exposeNearbyPlayers"): ]
require(exposure.index("awardBloomDiscovery(player)")
        < exposure.index("isProtectedByPoweredWard(level, player.blockPosition())")
        < exposure.index("InfectionState.setLevel(player, InfectionState.level(player) + 1)"),
        "protected players keep discovery credit while the ward skips infection")
require("message.sporenwerk.mutagen.bloom" in exposure,
        "unprotected bloom warning must remain")

for locale, expected in (
    ("de_de.json", "Sporenabwehr aktiv: Der Mutagenblüten-Ausbruch wurde abgefangen."),
    ("en_us.json", "Spore Ward active: the Mutagen Bloom exposure pulse was intercepted."),
):
    data = json.loads(read("src/main/resources/assets/sporenwerk/lang/" + locale))
    require(data.get("message.sporenwerk.mutagen.bloom_warded") == expected,
            locale + " must contain the new ward-interception feedback")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.40\.0['\"]", build) is not None,
        "artifact must be version 1.40.0")
readme = read("README.md")
require("Version 1.40.0" in readme and "Version 1.39.0" in readme,
        "release notes must preserve the prior counterpulse milestone")
require("Aktueller Entwicklungsstand: 1.40.0" in readme,
        "readme current-version headline must be updated")
print("Powered ward containment, shared radius, loaded-chunk safety, bloom rewards, discovery, locales and 1.40.0 passed.")
