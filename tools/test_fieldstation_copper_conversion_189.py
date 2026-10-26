#!/usr/bin/env python3
"""1.89 regression: copper Mutagen conversion, saved-world safety and research feedback."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.89 copper rescue regression: " + message)


station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
start = station.index("public InteractionResult use(")
conversion_start = station.index("private static int convertSpreadToCultivation(", start)
restart_start = station.index("private static int restartSafeCultivation(", conversion_start)
shutdown_start = station.index("private static int emergencyShutdown(", restart_start)
survey_start = station.index("private static Survey survey(", shutdown_start)
control = station[start:conversion_start]
conversion = station[conversion_start:restart_start]
restart_and_helper = station[restart_start:shutdown_start]
survey = station[survey_start:]

for token in (
    "player.isShiftKeyDown()",
    "player.getItemInHand(hand).is(Items.COPPER_INGOT)",
    "int converted = convertSpreadToCultivation(serverLevel, pos);",
    "message.sporenwerk.fieldstation.copper_done",
    "message.sporenwerk.fieldstation.copper_none",
    "message.sporenwerk.fieldstation.copper_guard",
    "SoundEvents.BEACON_ACTIVATE",
    "player instanceof net.minecraft.server.level.ServerPlayer",
    "getAdvancement(",
    'new net.minecraft.resources.ResourceLocation(',
    '"sporenwerk", "knotenrettung"',
    'serverPlayer.getAdvancements().award(advancement, "converted");',
    "int restarted = restartSafeCultivation(serverLevel, pos);",
    "int silenced = emergencyShutdown(serverLevel, pos);",
    "Survey s = survey(serverLevel, pos);",
    "message.sporenwerk.fieldstation.copper_usage",
):
    require(token in control, "control gestures, milestone and discovery: " + token)
require(control.index("Items.COPPER_INGOT") < control.index("Items.AMETHYST_SHARD")
        < control.index("int silenced = emergencyShutdown(serverLevel, pos);")
        < control.index("Survey s = survey(serverLevel, pos);"),
        "copper, amethyst, emergency and read-only report branches must remain separate")

for token in (
    "int minY = Math.max(level.getMinBuildHeight(), center.getY() - VERTICAL_SCAN_RADIUS)",
    "int maxY = Math.min(level.getMaxBuildHeight() - 1, center.getY() + VERTICAL_SCAN_RADIUS)",
    "int radiusSq = HORIZONTAL_SCAN_RADIUS * HORIZONTAL_SCAN_RADIUS;",
    "if (dx * dx + dz * dz > radiusSq) continue;",
    "if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;",
    "BlockState state = level.getBlockState(cursor);",
    "state.getBlock() instanceof MutationNodeBlock nodeBlock",
    "state.getValue(MutationNodeBlock.MODE) != 0",
    "state.getValue(MutationNodeBlock.POWERED)",
    "level.hasNeighborSignal(cursor)",
    "MutationNodeData.get(level)",
    "!nodes.isActive(cursor)",
    "state.setValue(MutationNodeBlock.MODE, 1)",
    "level.setBlock(cursor, cultivated, 3);",
    "scheduleSafeCultivationTick(level, cursor, nodeBlock, cultivated);",
    "if (feedback++ < 24)",
    "ParticleTypes.HAPPY_VILLAGER",
    "ParticleTypes.END_ROD",
    "return converted;",
):
    require(token in conversion, "missing guarded source-only conversion: " + token)
require(conversion.index("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;")
        < conversion.index("BlockState state = level.getBlockState(cursor);")
        < conversion.index("!nodes.isActive(cursor)")
        < conversion.index("state.setValue(MutationNodeBlock.MODE, 1)"),
        "conversion must guard chunk and stored activity before changing state")
for forbidden in ("getChunk(", "getChunkNow(", "destroyBlock(", "removeBlock(",
                  "shrink(", "registerIfMissing(", "setValue(MutationNodeBlock.MODE, 0)",
                  "getEntitiesOfClass(", "getTicker("):
    require(forbidden not in conversion, "dangerous operation in conversion: " + forbidden)
require("if (converted > 0" in control and "if (advancement != null)" in control,
        "research milestone may only be granted on successful conversion")
require("private static void scheduleSafeCultivationTick(" in restart_and_helper
        and "level.scheduleTick(cursor.immutable(), nodeBlock, 1);" in restart_and_helper
        and station.count("scheduleTick(") == 1,
        "1.87 restart and 1.89 conversion must share one node-only scheduling site")
require("private static int emergencyShutdown(" in station
        and "private static int comparatorSignal(Survey s)" in station
        and "MutationNodeData nodeAuditData = MutationNodeData.get(level);" in survey,
        "old emergency control, comparator and live audit must remain")
require('IntegerProperty.create("mode", 0, 2)' in node
        and "else if (mode == 1)" in node
        and "if (powered || state.getValue(POWERED)) return;" in node,
        "safe cultivation and paused behavior must remain available")

advancement = json.loads(read("src/main/resources/data/sporenwerk/advancements/knotenrettung.json"))
require(advancement["criteria"]["converted"]["trigger"] == "minecraft:impossible",
        "the milestone must only be granted manually after actual conversion")
require(advancement["requirements"] == [["converted"]], "one success unlocks milestone")
require(advancement["display"]["icon"]["item"] == "minecraft:copper_ingot",
        "Milestone icon missing")

for locale in ("de_de.json", "en_us.json"):
    language = json.loads(read("src/main/resources/assets/sporenwerk/lang/" + locale))
    for key in ("copper_usage", "copper_done", "copper_none", "copper_guard"):
        require(language.get("message.sporenwerk.fieldstation." + key),
                locale + " missing player-facing localization " + key)
    for key in ("advancement.sporenwerk.knotenrettung.title",
                "advancement.sporenwerk.knotenrettung.description"):
        require(language.get(key), locale + " missing advancement text " + key)
    require("%s" in language["message.sporenwerk.fieldstation.copper_done"],
            locale + " must report the actual number of rescued nodes")

require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.89\.0['\"]", read("build.gradle")),
        "build artifact version must be 1.89.0")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.89.0" in readme and
        "Version 1.89.0" in readme and "Version 1.88.0" in readme,
        "current and previous release notes missing")
print("1.89 copper rescue, cured-world guards, paused-node protection, research advancement and prior station controls passed.")
