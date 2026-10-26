#!/usr/bin/env python3
"""1.90 regression: Dämmerling farm raid telegraphs, soul lantern rescue and bounded night-watch station."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, reason):
    if not ok:
        raise SystemExit("Sporenwerk 1.90 Dämmerling night watch: " + reason)


entity = read("src/main/java/de/sporenwerk/entity/DaemmerlingEntity.java")
station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
crop_index = entity.index("private static final class CropThreatGoal extends Goal")
crop = entity[crop_index:]
gaze_index = entity.index("private static final class WatchedStillnessGoal extends Goal")
gaze = entity[gaze_index:crop_index]
require("this.goalSelector.addGoal(1, new WatchedStillnessGoal(this))" in entity
        and "this.goalSelector.addGoal(5, new CropThreatGoal(this))" in entity
        and "mob.getTarget() == watcher" in gaze,
        "original pursuit gaze and crop-goal priorities must remain")

for token in (
    "if (mob.distanceToSqr(tx, ty, tz) <= 2.4D)",
    "if (chewTicks % 5 == 0)",
    "Player guard = findLanternGuard(target);",
    "repelFromLantern(guard, target);",
    "nextAllowedTick = mob.tickCount + 120;",
    "if (chewTicks == 8 || chewTicks == 20)",
    "emitRaidWarning(target, chewTicks == 20);",
    "if (++chewTicks >= 30)",
    "mob.level().hasChunkAt(target)",
    "isMatureCrop(target) && !isProtected(target)",
    "mob.level().destroyBlock(target, false, mob);",
    "private Player findLanternGuard(BlockPos cropPos)",
    "new net.minecraft.world.phys.AABB(cropPos).inflate(4.0D, 2.5D, 4.0D)",
    "nearby.isSpectator()",
    "nearby.getMainHandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)",
    "nearby.getOffhandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)",
    "private void repelFromLantern(Player player, BlockPos cropPos)",
    'getLong("SporenwerkLanternGuardUntil")',
    'putLong("SporenwerkLanternGuardUntil", now + 140L)',
    "message.sporenwerk.daemmerling.lantern_rescue",
    '"sporenwerk", "nachtwache"',
    'serverPlayer.getAdvancements().award(milestone, "protected_crop")',
    "private void emitRaidWarning(BlockPos cropPos, boolean urgent)",
    "ParticleTypes.REVERSE_PORTAL",
    "ParticleTypes.SOUL_FIRE_FLAME",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "if (!mob.level().hasChunkAt(pos)) return false;",
    "if (!mob.level().hasChunkAt(cropPos)) return true;",
    "if (!mob.level().hasChunkAt(pos)) continue;",
    "getMaxLocalRawBrightness(cropPos) >= 7",
    "ModBlocks.FELDSAMMLER.get()",
    "mob.getNavigation().createPath(candidate, 0) == null",
):
    require(token in crop, "crop-raid warning, rescue or loaded chunk guard missing: " + token)
require(crop.index("if (chewTicks % 5 == 0)") < crop.index("if (chewTicks == 8 || chewTicks == 20)")
        < crop.index("if (++chewTicks >= 30)"),
        "player rescue and both warnings must precede final crop destruction")
require(crop.index("mob.level().hasChunkAt(target)") < crop.index("mob.level().destroyBlock(target, false, mob);"),
        "biting may not load a missing crop chunk")
require(crop.count("getEntitiesOfClass(") == 1,
        "mobile lantern rescue may not add continuous entity searches")
for forbidden in ("getChunk(", "getChunkNow(", "setTarget(null)", "player.hurt(", ".shrink("):
    require(forbidden not in crop and forbidden not in gaze,
            "farm-horror logic may not bypass player safety or loaded chunks: " + forbidden)
require("this.goalSelector.addGoal(5, new CropThreatGoal(this))" in entity
        and "getMaxLocalRawBrightness(cropPos) >= 7" in entity,
        "existing light/collector protections must remain")

report_start = station.index("public InteractionResult use(")
scan_start = station.index("private static Survey survey(", report_start)
report = station[report_start:scan_start]
for token in (
    "Survey s = survey(serverLevel, pos);",
    "int lurkingDaemmerlinge = serverLevel.getEntitiesOfClass(",
    "de.sporenwerk.entity.DaemmerlingEntity.class",
    "HORIZONTAL_SCAN_RADIUS, VERTICAL_SCAN_RADIUS, HORIZONTAL_SCAN_RADIUS",
    "mob -> mob.isAlive()).size();",
    '"message.sporenwerk.fieldstation.daemmerling_alert"',
    '"message.sporenwerk.fieldstation.daemmerling_clear"',
    "int converted = convertSpreadToCultivation(serverLevel, pos);",
    "int restarted = restartSafeCultivation(serverLevel, pos);",
    "int silenced = emergencyShutdown(serverLevel, pos);",
):
    require(token in report, "station control/night watch coexistence missing: " + token)
require(report.index("int silenced = emergencyShutdown(serverLevel, pos);")
        < report.index("Survey s = survey(serverLevel, pos);")
        < report.index("int lurkingDaemmerlinge = serverLevel.getEntitiesOfClass("),
        "night watch must only scan on ordinary manual diagnosis")
require(station.count("getEntitiesOfClass(") == 1
        and station.count("scheduleTick(") == 1
        and "getTicker(" not in station
        and "getChunk(" not in station and "getChunkNow(" not in station,
        "manual station scans must remain bounded and node tick scheduler untouched")
require("private static int comparatorSignal(Survey s)" in station,
        "station comparator contract must stay unchanged")

research = json.loads(read("src/main/resources/data/sporenwerk/advancements/nachtwache.json"))
require(research["criteria"]["protected_crop"]["trigger"] == "minecraft:impossible"
        and research["requirements"] == [["protected_crop"]],
        "advancement must not auto-grant on merely holding a lantern")
require(research["display"]["icon"]["item"] == "minecraft:soul_lantern",
        "night-watch advancement must have soul lantern icon")
for locale in ("de_de.json", "en_us.json"):
    language = json.loads(read("src/main/resources/assets/sporenwerk/lang/" + locale))
    for token in (
        "message.sporenwerk.daemmerling.lantern_rescue",
        "message.sporenwerk.fieldstation.daemmerling_alert",
        "message.sporenwerk.fieldstation.daemmerling_clear",
        "advancement.sporenwerk.nachtwache.title",
        "advancement.sporenwerk.nachtwache.description",
    ):
        require(language.get(token), locale + " missing text: " + token)
    for key in ("daemmerling_alert", "daemmerling_clear"):
        require("%s" in language["message.sporenwerk.fieldstation." + key],
                locale + " station must display actual creature count")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.90\.0['\"]", read("build.gradle")),
        "version 1.90.0 is required")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.90.0" in readme
        and "Version 1.90.0" in readme and "Version 1.89.0" in readme,
        "new and old releases must be documented")
print("1.90 telegraphed crop raids, lantern counterplay, progression, stations, safe chunk access and legacy behavior passed.")
