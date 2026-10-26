#!/usr/bin/env python3
"""1.86 Dämmerling AI counterplay regression: visible gaze freeze with strict limits."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Dämmerling watched-stillness 1.86 regression: " + message)


entity = read("src/main/java/de/sporenwerk/entity/DaemmerlingEntity.java")
start = entity.index("private static final class WatchedStillnessGoal extends Goal")
end = entity.index("private static final class CropThreatGoal extends Goal", start)
goal = entity[start:end]
require("this.goalSelector.addGoal(1, new WatchedStillnessGoal(this))" in entity,
        "eye-contact counterplay goal must preempt Zombie combat movement")
require("this.goalSelector.addGoal(5, new CropThreatGoal(this))" in entity,
        "existing protected crop threat goal must remain intact")
for token in (
    "private static final double MAX_WATCH_DISTANCE_SQUARED = 12.0D * 12.0D;",
    "private static final int MAX_FREEZE_TICKS = 30;",
    "private static final int RESET_COOLDOWN_TICKS = 100;",
    "this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK))",
    "mob.tickCount < nextAllowedTick",
    "mob.tickCount < nextSightCheck",
    "nextSightCheck = mob.tickCount + 5;",
    "mob.getTarget() instanceof Player player",
    "mob.getTarget() == watcher",
    "freezeTicks < MAX_FREEZE_TICKS",
    "isPlayerWatching(watcher)",
    "mob.getNavigation().stop();",
    "mob.getLookControl().setLookAt(watcher",
    "mob.setZza(0.0F);",
    "mob.setXxa(0.0F);",
    "nextAllowedTick = mob.tickCount + RESET_COOLDOWN_TICKS;",
    "player.isSpectator()",
    "player.isCreative()",
    "mob.distanceToSqr(player) > MAX_WATCH_DISTANCE_SQUARED",
    "mob.level().getMaxLocalRawBrightness(mob.blockPosition()) >= 8",
    "mob.getSensing().hasLineOfSight(player)",
    "mob.getEyePosition().subtract(player.getEyePosition())",
    "towardsMob.lengthSqr() < 1.0E-5D",
    "player.getLookAngle().normalize().dot(towardsMob.normalize()) > 0.93D",
    "ParticleTypes.REVERSE_PORTAL",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    'getLong("SporenwerkDaemmerlingStareUntil")',
    'putLong("SporenwerkDaemmerlingStareUntil", now + 200L)',
    "message.sporenwerk.daemmerling.stare",
):
    require(token in goal, "missing guarded AI behaviour: " + token)
for forbidden in ("destroyBlock(", "setBlock(", "getChunk(", "getChunkNow(", "hurt(", "setTarget(null)"):
    require(forbidden not in goal, "watched AI must not mutate the world or erase zombie aggro: " + forbidden)
for token in ("crop.isMaxAge(state)",
              "getMaxLocalRawBrightness(cropPos) >= 7",
              "ModBlocks.FELDSAMMLER.get()",
              "createPath(candidate, 0) == null",
              "destroyBlock(target, false, mob)"):
    require(token in entity, "preserve original balanced crop predation: " + token)
for locale, needle in (
    ("de_de.json", "Der Dämmerling erstarrt"),
    ("en_us.json", "freezes under your gaze"),
):
    data = json.loads((ROOT / "src/main/resources/assets/sporenwerk/lang" / locale)
                      .read_text(encoding="utf-8"))
    require(needle in data.get("message.sporenwerk.daemmerling.stare", ""),
            "visible response must be localized: " + locale)
gradle = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.86\.0['\"]", gradle),
        "artifact version must be 1.86.0")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.86.0" in readme
        and "Version 1.86.0" in readme and "Version 1.85.0" in readme,
        "release history and current version required")
print("1.86 Dämmerling 12-block LOS gaze counterplay, anti-permastun cooldown, crop rules and localized horror feedback passed.")
