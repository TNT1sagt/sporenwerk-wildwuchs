#!/usr/bin/env python3
"""Sporenwerk 1.91: persistent Colossus arrival, actual crop raids and player warnings."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def require(ok, why):
    if not ok:
        raise SystemExit("Sporenwerk 1.91 regression: " + why)

boss = read("src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java")
mob = read("src/main/java/de/sporenwerk/entity/DaemmerlingEntity.java")
station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
arrival = boss[boss.index("private void emitArrivalPulse(ServerLevel level, int stage)"):
               boss.index("private void beginAttack(", boss.index("private void emitArrivalPulse("))]
for token in (
    "private int arrivalPulseStage;",
    "this.arrivalPulseStage < 3 && this.tickCount % 20 == 0",
    "emitArrivalPulse(arrivalLevel, this.arrivalPulseStage);",
    "this.arrivalPulseStage++;",
    'tag.putInt("SporenwerkArrivalPulseStage", this.arrivalPulseStage);',
    'this.arrivalPulseStage = Math.max(0, Math.min(3, tag.getInt("SporenwerkArrivalPulseStage")));',
    "private void emitGroundRing(ServerLevel serverLevel",
    "private void performCrystalBreath()",
    "this.bossEvent.setProgress(",
    "this.attackTicksLeft",
    "private void exposeCoreFromCountermeasure()",
):
    require(token in boss, "persistent arrival or legacy boss combat missing: " + token)
for token in (
    "if (stage < 0 || stage > 2) return;",
    "double radius = 2.8D + stage * 1.6D;",
    "sample < 24",
    "ParticleTypes.END_ROD",
    "ParticleTypes.REVERSE_PORTAL",
    "ParticleTypes.WARPED_SPORE",
    "SoundEvents.RESPAWN_ANCHOR_DEPLETE",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "if (stage == 0)",
    "ServerPlayer.class",
    "player.isSpectator()",
    "message.sporenwerk.colossus.arrival",
):
    require(token in arrival, "staged no-damage boss entrance missing: " + token)
for forbidden in ("setBlock(", "destroyBlock(", "getChunk(", "getChunkNow(", ".hurt(",
                  ".knockback(", "addEffect(", "teleportTo(", "setCamera("):
    require(forbidden not in arrival,
            "Colossus arrival may only be audiovisual: " + forbidden)
require("tag.putBoolean(\"SporenwerkPhaseTwo\"" in boss
        and "this.entityData.set(ATTACK_STATE, ATTACK_IDLE)" in boss,
        "boss original persistence and combat state retained")

crop = mob[mob.index("private static final class CropThreatGoal extends Goal"):]
for token in (
    "private boolean raidingCrops;",
    "public boolean isRaidingCrops() { return this.raidingCrops; }",
    "this.goalSelector.addGoal(1, new WatchedStillnessGoal(this))",
    "this.goalSelector.addGoal(5, new CropThreatGoal(this))",
):
    require(token in mob, "Dämmerling true status or AI goal missing: " + token)
for token in (
    "mob.raidingCrops = true;",
    "mob.raidingCrops = false;",
    "if (mob.distanceToSqr(tx, ty, tz) <= 2.4D)",
    "if (chewTicks == 8 || chewTicks == 20)",
    "if (chewTicks % 5 == 0)",
    "Player guard = findLanternGuard(target);",
    "repelFromLantern(guard, target);",
    "private void emitRaidWarning(BlockPos cropPos, boolean urgent)",
    "new net.minecraft.world.phys.AABB(cropPos).inflate(12.0D, 4.0D, 12.0D)",
    "if (!urgent)",
    'getLong("SporenwerkRaidAlertUntil")',
    'putLong("SporenwerkRaidAlertUntil", now + 200L)',
    "message.sporenwerk.daemmerling.raid_warning",
    "mob.level().destroyBlock(target, false, mob)",
    "FilterMossSymbiosis.protects(mob.level(), cropPos)",
    "getMaxLocalRawBrightness(cropPos) >= 7",
):
    require(token in crop, "raid, lantern or night warning missing: " + token)
require(crop.index("mob.raidingCrops = true") > crop.index("if (mob.distanceToSqr(tx, ty, tz) <= 2.4D)"),
        "only close actual nibbling may signal an active raid")
require(crop.count("getEntitiesOfClass(") == 2,
        "only lantern defense and actual raid-warning may scan for nearby players")
for forbidden in ("getChunk(", "getChunkNow(", "setTarget(null)", "player.hurt(", ".shrink("):
    require(forbidden not in crop, "raids may not force-load or punish players: " + forbidden)

report = station[station.index("public InteractionResult use("):
                 station.index("private static Survey survey(")]
for token in (
    "Survey s = survey(serverLevel, pos);",
    "java.util.List<de.sporenwerk.entity.DaemmerlingEntity> localDaemmerlinge =",
    "int lurkingDaemmerlinge = localDaemmerlinge.size();",
    "long activeRaids = localDaemmerlinge.stream().filter(",
    "de.sporenwerk.entity.DaemmerlingEntity::isRaidingCrops).count();",
    '"message.sporenwerk.fieldstation.daemmerling_raids"',
    "if (activeRaids > 0L)",
    '"message.sporenwerk.fieldstation.daemmerling_alert"',
    '"message.sporenwerk.fieldstation.daemmerling_clear"',
    "int converted = convertSpreadToCultivation(serverLevel, pos);",
    "int restarted = restartSafeCultivation(serverLevel, pos);",
    "int silenced = emergencyShutdown(serverLevel, pos);",
):
    require(token in report, "manual station raid diagnosis or old safe controls missing: " + token)
require(report.index("int silenced = emergencyShutdown(serverLevel, pos);")
        < report.index("Survey s = survey(serverLevel, pos);")
        < report.index("java.util.List<de.sporenwerk.entity.DaemmerlingEntity> localDaemmerlinge ="),
        "station must only survey creatures during normal reporting")
require(station.count("getEntitiesOfClass(") == 1 and
        "getTicker(" not in station and
        station.count("scheduleTick(") == 1 and
        "getChunk(" not in station and "getChunkNow(" not in station,
        "single manual entity scan and shared cultivation scheduling required")
for locale in ("de_de.json", "en_us.json"):
    lang = json.loads(read("src/main/resources/assets/sporenwerk/lang/" + locale))
    for key in ("message.sporenwerk.colossus.arrival",
                "message.sporenwerk.daemmerling.raid_warning",
                "message.sporenwerk.fieldstation.daemmerling_raids"):
        require(lang.get(key, "").strip(), "missing "+ locale + " "+key)
    require("%s" in lang["message.sporenwerk.fieldstation.daemmerling_raids"],
            "must display real count of active raids")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.91\.0['\"]", read("build.gradle")),
        "1.91 release artifact missing")
readme=read("README.md")
require("Aktueller Entwicklungsstand: 1.91.0" in readme
        and "Version 1.91.0" in readme and "Version 1.90.0" in readme,
        "new and prior releases not documented")
print("1.91: saved three-stage Colossus arrival, audiovisual safety, true live raids, player cooldown, station one-scan and source safeguards passed.")
