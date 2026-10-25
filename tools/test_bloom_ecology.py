#!/usr/bin/env python3
"""Regression coverage for the 1.54.0 Mutagen Bloom scent ecology."""
from pathlib import Path
import json
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen Bloom ecology regression: " + message)


nodes = read("src/main/java/de/sporenwerk/infection/MutationNodeData.java")
for token in (
    "public BlockPos nearestRecentBloom(BlockPos center, int radius, long gameTime, long scentTicks)",
    "public int countRecentBlooms(BlockPos center, int radius, int verticalRadius,",
    "lastBlooms.getOrDefault(entry.getKey(), -24000L)",
    "gameTime - lastBloom > scentTicks",
    "Math.abs(dy) > verticalRadius",
):
    require(token in nodes, "persistent source/scent API is missing " + token)
for signature in (
    "public BlockPos nearestRecentBloom(",
    "public int countRecentBlooms(",
):
    start = nodes.find(signature)
    require(start >= 0, "saved bloom source query is missing " + signature)
    end = nodes.find("\n    }", start)
    require(end > start, "could not isolate saved bloom source query " + signature)
    body = nodes[start:end]
    require("level.getBlockState(" not in body and "getChunk(" not in body
            and "getChunkNow(" not in body,
            "saved bloom scent queries must use persistent timestamps only: " + signature)

entity = read("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")
for token in (
    "this.goalSelector.addGoal(4, new BloomScentGoal(this));",
    "private static final class BloomScentGoal extends Goal",
    "SEARCH_RADIUS = 24",
    "SEARCH_INTERVAL_TICKS = 20",
    "SCENT_TICKS = 2400L",
    "mob.getTarget() != null",
    "MutationNodeData.get(serverLevel).nearestRecentBloom(",
    "mob.getNavigation().createPath(bloom.above(), 0) == null",
    "mob.getNavigation().moveTo(target.getX() + 0.5D",
    "return outsideArrivalRange(target);",
):
    require(token in entity, "Crystal Stalker bloom scent goal missing " + token)
goal = entity[entity.index("private static final class BloomScentGoal extends Goal"):]
require("mob.tickCount % SEARCH_INTERVAL_TICKS != 0" in goal,
        "idle scent discovery must not scan the saved registry every tick")
require("setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK))" in goal,
        "bloom investigation must use normal goal arbitration")
require(goal.index("mob.getTarget() != null") < goal.index("findTarget()"),
        "combat target must take precedence over investigating a bloom")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "scent navigation must not force-load chunks")

scanner = read("src/main/java/de/sporenwerk/item/FeldscannerItem.java")
for token in (
    "int recentBloomSources) {}",
    "nodeData.countRecentBlooms(origin, AREA_SCAN_RADIUS",
    "survey.recentBloomSources()",
    "message.sporenwerk.scanner.survey.recent_blooms",
    "AREA_SCAN_RADIUS",
    "AREA_SCAN_VERTICAL_RADIUS",
):
    require(token in scanner, "scanner recent-bloom diagnostic missing " + token)
require("scheduleTick(" not in scanner and "getTicker(" not in scanner,
        "scanner scent diagnosis must stay interaction-driven")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads(read("src/main/resources/assets/sporenwerk/lang/" + locale))
    require(data.get("message.sporenwerk.scanner.survey.recent_blooms", "").strip(),
            locale + " missing recent-bloom diagnostic")
    require("2.400" in data["message.sporenwerk.scanner.survey.recent_blooms"]
            if locale == "de_de.json"
            else "2,400" in data["message.sporenwerk.scanner.survey.recent_blooms"],
            locale + " must accurately describe the scent window")

readme = read("README.md")
require("Version 1.54.0" in readme and "Version 1.53.0" in readme,
        "release notes must preserve previous release history")
require("Aktueller Entwicklungsstand: 1.54.0" in readme,
        "README current-version headline must be updated")
print("Mutagen Bloom scent, Crystal Stalker goal arbitration, bounded queries, scanner diagnostics and DE/EN passed.")
