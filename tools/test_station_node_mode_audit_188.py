#!/usr/bin/env python3
"""1.88.0 regression: Mutagen station source modes, saved data and safe interventions."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Station node modes 1.88 regression: " + message)


station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
start = station.index("private static Survey survey(ServerLevel level, BlockPos center)")
scan = station[start:]
report = station[station.index("public InteractionResult use("):start]
for token in (
    "int spreadNodes = 0, cultivatedNodes = 0, dormantNodes = 0;",
    "int pausedNodes = 0, inactiveNodes = 0;",
    "MutationNodeData nodeAuditData = MutationNodeData.get(level);",
    "BlockState bs = level.getBlockState(cursor);",
    "bs.getBlock() instanceof MutationNodeBlock",
    "if (!nodeAuditData.isActive(cursor))",
    "inactiveNodes++;",
    "bs.getValue(MutationNodeBlock.POWERED)",
    "pausedNodes++;",
    "bs.getValue(MutationNodeBlock.MODE)",
    "nodeMode == 0) spreadNodes++",
    "nodeMode == 1) cultivatedNodes++",
    "else dormantNodes++",
    "int spreadNodes, int cultivatedNodes, int dormantNodes, int pausedNodes, int inactiveNodes",
    "spreadNodes, cultivatedNodes, dormantNodes, pausedNodes, inactiveNodes);",
):
    require(token in scan, "live node counting missing " + token)
require(scan.index("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;")
        < scan.index("BlockState bs = level.getBlockState(cursor);"),
        "node inspection must occur after existing loaded-chunk safety check")
require(scan.count("for (int dx = -HORIZONTAL_SCAN_RADIUS") == 1,
        "node count must reuse the single existing scan instead of adding another")
for token in (
    '"message.sporenwerk.fieldstation.node_modes"',
    "s.spreadNodes(), s.cultivatedNodes(), s.dormantNodes()",
    "s.pausedNodes(), s.inactiveNodes()",
    '"message.sporenwerk.fieldstation.node_warning"',
    '"message.sporenwerk.fieldstation.node_farming"',
    '"message.sporenwerk.fieldstation.node_quiet"',
    "Survey s = survey(serverLevel, pos);",
    "int silenced = emergencyShutdown(serverLevel, pos);",
    "int restarted = restartSafeCultivation(serverLevel, pos);",
):
    require(token in report, "report/countermeasure branch missing " + token)
require(report.index("int restarted = restartSafeCultivation(serverLevel, pos);")
        < report.index("int silenced = emergencyShutdown(serverLevel, pos);")
        < report.index("Survey s = survey(serverLevel, pos);"),
        "scan report must not interfere with safe restart and emergency stop")

for forbidden in ("getChunk(", "getChunkNow(", "destroyBlock("):
    require(forbidden not in station, "the station may not mutate terrain or force-load")
require("private static int comparatorSignal(Survey s)" in station,
        "cached comparator must continue working")
require('getOperationalFieldStrengthAt(' in read("src/main/java/de/sporenwerk/infection/MutationNodeData.java"),
        "mode-sensitive endgame source model must remain functional")
for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    for suffix in ("node_modes", "node_warning", "node_farming", "node_quiet"):
        require("message.sporenwerk.fieldstation." + suffix in data,
                f"{locale} missing node status text {suffix}")
    require(data["message.sporenwerk.fieldstation.node_modes"].count("%s") == 5,
            f"{locale} must display all five mode counters")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.88\.0['\"]", build),
        "version 1.88.0 missing")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.88.0" in readme and
        "Version 1.88.0" in readme and "Version 1.87.0" in readme,
        "current version and historical release missing")
print("1.88 loaded node audit, mode classification, 1.87 controls, translated reports and release contracts passed.")
