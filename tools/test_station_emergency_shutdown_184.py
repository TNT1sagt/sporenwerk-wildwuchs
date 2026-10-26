#!/usr/bin/env python3
"""Regression for bounded manual Mutagen Field Control Station emergency shutdown (1.84.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def require(ok, description):
    if not ok:
        raise SystemExit("Station shutdown 1.84 regression: " + description)


station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
use = station[station.index("public InteractionResult use("):station.index("private static int emergencyShutdown(")]
shutdown = station[station.index("private static int emergencyShutdown("):station.index("private static Survey survey(")]
for token in (
    "hand == InteractionHand.MAIN_HAND && player.isShiftKeyDown()",
    "emergencyShutdown(serverLevel, pos)",
    "message.sporenwerk.fieldstation.shutdown_none",
    "message.sporenwerk.fieldstation.shutdown_done",
    "message.sporenwerk.fieldstation.shutdown_hint",
    "SoundEvents.BEACON_DEACTIVATE",
    "Survey s = survey(serverLevel, pos);",
    "message.sporenwerk.fieldstation.shutdown_usage",
):
    require(token in use, "interaction, diagnostics or report hint missing: " + token)
require(use.index("if (hand == InteractionHand.MAIN_HAND && player.isShiftKeyDown())")
        < use.index("Survey s = survey(serverLevel, pos);"),
        "the emergency branch must run before ordinary station survey")

for token in (
    "private static int emergencyShutdown(ServerLevel level, BlockPos center)",
    "int minY = Math.max(level.getMinBuildHeight(), center.getY() - VERTICAL_SCAN_RADIUS)",
    "int maxY = Math.min(level.getMaxBuildHeight() - 1, center.getY() + VERTICAL_SCAN_RADIUS)",
    "int radiusSq = HORIZONTAL_SCAN_RADIUS * HORIZONTAL_SCAN_RADIUS;",
    "if (dx * dx + dz * dz > radiusSq) continue;",
    "if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;",
    "BlockState nodeState = level.getBlockState(cursor);",
    "nodeState.getBlock() instanceof MutationNodeBlock",
    "nodeState.getValue(MutationNodeBlock.MODE) == 2",
    "nodeState.setValue(MutationNodeBlock.MODE, 2)",
    "level.setBlock(cursor, nodeState.setValue(MutationNodeBlock.MODE, 2), 3);",
    "if (effects++ < 24)",
    "ParticleTypes.SMOKE",
    "return halted;",
):
    require(token in shutdown, "bounded and permanent stop missing: " + token)
require(shutdown.index("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;")
        < shutdown.index("BlockState nodeState = level.getBlockState(cursor);"),
        "all block lookups must follow a loaded-chunk check")
for forbidden in ("getChunk(", "getChunkNow(", "getEntitiesOfClass(", "MutationNodeData.get(", "destroyBlock(", "removeBlock("):
    require(forbidden not in shutdown, "emergency stop may not force-load, query entities or change registration: " + forbidden)
require("setValue(MutationNodeBlock.POWERED" not in shutdown,
        "emergency stop must preserve the redstone power property")
require('IntegerProperty.create("mode", 0, 2)' in node
        and "if (mode == 0)" in node and "else if (mode == 1)" in node
        and "if (powered || state.getValue(POWERED)) return;" in node,
        "existing nodes must respect DORMANT and redstone pause")
require("int nextMode = (state.getValue(MODE) + 1) % 3;" in node,
        "individual nodes must remain manually reactivatable")
require("Survey s = survey(serverLevel, pos);" in station
        and "private static int comparatorSignal(Survey s)" in station,
        "station hazard diagnostics and cached comparator signal must remain")

for locale, texts in (
    ("de_de.json", ("Geduckt rechtsklicken", "Notabschaltung ausgeführt", "Nur geladene Chunks")),
    ("en_us.json", ("sneak-right-click", "Emergency stop complete", "Loaded chunks only")),
):
    language = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    for key, text in zip((
        "message.sporenwerk.fieldstation.shutdown_usage",
        "message.sporenwerk.fieldstation.shutdown_done",
        "message.sporenwerk.fieldstation.shutdown_hint",
    ), texts):
        require(text in language.get(key, ""), f"{locale} missing {key}")

gradle = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.84\.0['\"]", gradle),
        "artifact must be version 1.84.0")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.84.0" in readme
        and "Version 1.84.0" in readme and "Version 1.83.0" in readme,
        "current and past releases must be present")
print("1.84 bounded loaded-chunk emergency shutdown, preserved node states and survey, DE/EN feedback and release metadata passed.")
