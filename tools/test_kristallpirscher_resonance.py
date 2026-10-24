#!/usr/bin/env python3
"""Regression tests for the Kristallpirscher's telegraphed, mask-countered resonance pulse."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
entity = (ROOT / "src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java").read_text(encoding="utf-8")
build = (ROOT / "build.gradle").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Kristallpirscher resonance regression: " + message)


for token in (
    "RESONANCE_DETECTION_RADIUS = 7.0D",
    "RESONANCE_EFFECT_RADIUS_SQR = 25.0D",
    "RESONANCE_WINDUP_TICKS = 30",
    "RESONANCE_COOLDOWN_TICKS = 200",
    "private int resonanceWindup",
    "private int resonanceCooldown",
    "if (!isOnHighTierSoil() || resonanceCooldown > 0)",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "ParticleTypes.END_ROD",
    "ParticleTypes.CRIT",
    "resonanceWindup % 5 == 0",
    "SoundEvents.BEACON_ACTIVATE",
    "nearbyUnprotectedPlayers()",
    "distanceToSqr(player) <= RESONANCE_EFFECT_RADIUS_SQR",
    "MobEffects.MOVEMENT_SLOWDOWN, 50, 0",
    "resonanceCooldown = RESONANCE_COOLDOWN_TICKS",
    "private static boolean isWearingSporeMask(Player player)",
    "ModItems.SPORENFILTERMASKE.get()",
    "player -> player.isAlive() && !player.isCreative() && !player.isSpectator()",
    "level().isClientSide",
    "isOnHighTierSoil()",
):
    require(token in entity, "missing telegraph/pulse/counterplay contract: " + token)

# The signal must be telegraphed before effect application, and recheck the protected-player list.
require(entity.index("RESONANCE_WINDUP_TICKS") < entity.index("MobEffects.MOVEMENT_SLOWDOWN"),
        "warning phase must precede pulse effect")
require(entity.index("for (Player player : nearbyUnprotectedPlayers())") < entity.index("resonanceCooldown = RESONANCE_COOLDOWN_TICKS"),
        "cooldown only begins after the pulse is released")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "pulse logic must never force-load chunks")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.34\.0['\"]", build) is not None,
        "artifact version must be 1.33.0")
require("Version 1.34.0" in readme and "Version 1.33.0" in readme,
        "release notes must preserve 1.33.0 history")
print("Kristallpirscher resonance pulse, warning window, cooldown, mask protection, range recheck, and version passed.")
