#!/usr/bin/env python3
"""Regression tests for the charged Resonance Dampener counterpulse (1.39.0)."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Resonance counterpulse regression: " + message)


entity = read("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")
method_start = entity.find("private boolean isResonanceDamped()")
require(method_start >= 0, "could not find the resonance-blocking method")
charge_guard = entity.find("if (charge <= 0) continue;", method_start)
charge_spend = entity.find(
    "level().setBlock(pos, dampenerState.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1), 3);",
    method_start,
)
counter_hit = entity.find("hurt(level().damageSources().magic(), 2.0F);", method_start)
slow = entity.find("addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 0));", method_start)
impact = entity.find("serverLevel.sendParticles(ParticleTypes.CRIT", method_start)
return_true = entity.find("return true;", method_start)
require(0 <= charge_guard < charge_spend < impact < counter_hit < slow < return_true,
        "counterpulse must happen after a positive charge is consumed and before the block result returns")
require(entity.count("hurt(level().damageSources().magic(), 2.0F);") == 1,
        "one block event must create only one counterpulse hit")
require("if (!level().hasChunkAt(pos)) continue;" in entity,
        "dampener scan must skip unloaded chunks")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "counterpulse must not load chunks")
require("resonanceCooldown = RESONANCE_COOLDOWN_TICKS;" in entity,
        "the existing anti-spam cooldown must remain")
require("new BlockEntity" not in entity and "BlockEntityTicker" not in entity,
        "counterpulse must not add a ticking block entity")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.39\.0['\"]", build) is not None,
        "artifact must be version 1.39.0")
readme = read("README.md")
require("Version 1.39.0" in readme and "Version 1.38.0" in readme,
        "release notes must preserve the charge-management milestone")
workflow = read(".github/workflows/build.yml")
require("Build Sporenwerk 1.39.0 for Forge 1.20.1" in workflow,
        "CI workflow must target version 1.39.0")
print("Counterpulse damage, visible impact, short slow, charge gating, chunk safety, cooldown, and 1.39.0 passed.")
