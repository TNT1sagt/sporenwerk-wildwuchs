#!/usr/bin/env python3
"""1.87 regression: safely restart active, dormant Mutagen Nodes only."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def require(ok, msg):
    if not ok:
        raise SystemExit("Safe station restart 1.87 regression: " + msg)


station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
use_start = station.index("public InteractionResult use(")
resume_start = station.index("private static int restartSafeCultivation(", use_start)
shutdown_start = station.index("private static int emergencyShutdown(", resume_start)
use = station[use_start:resume_start]
resume = station[resume_start:shutdown_start]
for t in (
    "hand == InteractionHand.MAIN_HAND && player.isShiftKeyDown()",
    "player.getItemInHand(hand).is(Items.AMETHYST_SHARD)",
    "restartSafeCultivation(serverLevel, pos)",
    "message.sporenwerk.fieldstation.restart_done",
    "message.sporenwerk.fieldstation.restart_none",
    "message.sporenwerk.fieldstation.restart_guard",
    "int silenced = emergencyShutdown(serverLevel, pos);",
    "Survey s = survey(serverLevel, pos);",
    "message.sporenwerk.fieldstation.restart_usage",
):
    require(t in use, "safe restart, shutdown and report must coexist: " + t)
require(use.index("player.getItemInHand(hand).is(Items.AMETHYST_SHARD)")
        < use.index("int silenced = emergencyShutdown(serverLevel, pos);")
        < use.index("Survey s = survey(serverLevel, pos);"),
        "the three control station commands must remain distinct")

for t in (
    "private static int restartSafeCultivation(ServerLevel level, BlockPos center)",
    "HORIZONTAL_SCAN_RADIUS * HORIZONTAL_SCAN_RADIUS",
    "VERTICAL_SCAN_RADIUS",
    "if (dx * dx + dz * dz > radiusSq) continue;",
    "if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;",
    "BlockState state = level.getBlockState(cursor);",
    "state.getBlock() instanceof MutationNodeBlock nodeBlock",
    "state.getValue(MutationNodeBlock.MODE) != 2",
    "MutationNodeData.get(level)",
    "!nodes.isActive(cursor)",
    "state.setValue(MutationNodeBlock.MODE, 1)",
    "level.setBlock(cursor, cultivated, 3);",
    "if (!cultivated.getValue(MutationNodeBlock.POWERED)",
    "&& !level.hasNeighborSignal(cursor))",
    "level.scheduleTick(cursor.immutable(), nodeBlock, 1);",
    "ParticleTypes.HAPPY_VILLAGER",
    "if (feedback++ < 24)",
    "return restarted;",
):
    require(t in resume, "bounded safe reactivation missing: " + t)
require(resume.index("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;")
        < resume.index("BlockState state = level.getBlockState(cursor);")
        < resume.index("!nodes.isActive(cursor)")
        < resume.index("state.setValue(MutationNodeBlock.MODE, 1)"),
        "chunk safety, healed world guard and mode transition are ordered incorrectly")
for bad in ("getChunk(", "getChunkNow(", "setValue(MutationNodeBlock.MODE, 0)",
            "registerIfMissing(", "destroyBlock(", "shrink(", "getEntitiesOfClass("):
    require(bad not in resume, "unsafe side effect in restart: " + bad)
require('IntegerProperty.create("mode", 0, 2)' in node
        and "else if (mode == 1)" in node,
        "existing cultivation behavior must remain intact")
require("private static int emergencyShutdown(" in station
        and "private static Survey survey(" in station
        and "private static int comparatorSignal(Survey s)" in station,
        "existing diagnosis and shutdown must remain available")
for locale, values in (
    ("de_de.json", ("Amethystscherbe", "Kontrollierter Neustart", "Geheilte Quellen")),
    ("en_us.json", ("amethyst shard", "Controlled restart", "Cured sources")),
):
    lang = json.loads((ROOT / "src/main/resources/assets/sporenwerk/lang" / locale).read_text(encoding="utf-8"))
    for key, word in zip(("restart_usage", "restart_done", "restart_guard"), values):
        require(word in lang.get("message.sporenwerk.fieldstation." + key, ""),
                locale + ": missing " + key)
gradle = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.87\.0['\"]", gradle),
        "artifact must be version 1.87.0")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.87.0" in readme
        and "Version 1.87.0" in readme and "Version 1.86.0" in readme,
        "release metadata incorrect")
print("1.87 safe restart, no cured-node resurrection, redstone preservation, and three station actions passed.")
