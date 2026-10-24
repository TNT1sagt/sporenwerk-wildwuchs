#!/usr/bin/env python3
"""Regression tests for visible, rate-limited Mutagen resonance dampener feedback."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
entity = (ROOT / "src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java").read_text(encoding="utf-8")
build = (ROOT / "build.gradle").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Resonance dampener feedback regression: " + message)


for token in (
    "if (isResonanceDamped()) {",
    "resonanceCooldown = RESONANCE_COOLDOWN_TICKS;",
    "resonanceWindup = 0;",
    "private boolean isResonanceDamped()",
    "if (!level().hasChunkAt(pos)) continue;",
    "if (level() instanceof ServerLevel serverLevel)",
    "serverLevel.sendParticles(ParticleTypes.END_ROD",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "SoundSource.BLOCKS, 0.75F, 1.25F",
    "ModBlocks.MUTAGEN_RESONANZDAEMPFER.get()",
):
    require(token in entity, "missing dampener suppression/feedback: " + token)

# Both the early block and the late (mid-windup placement) block must consume cooldown.
early = entity.index("if (isResonanceDamped()) {")
early_end = entity.index("resonanceWindup = RESONANCE_WINDUP_TICKS;", early)
early_block = entity[early:early_end]
require("resonanceCooldown = RESONANCE_COOLDOWN_TICKS;" in early_block,
        "already-built dampener must rate-limit blocked attempts")
release = entity.index("// A dampener installed during the windup")
release_end = entity.index("serverLevel.sendParticles(ParticleTypes.CRIT", release)
release_block = entity[release:release_end]
require("resonanceCooldown = RESONANCE_COOLDOWN_TICKS;" in release_block,
        "mid-windup dampener must rate-limit cancelled release")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "feedback must not force-load chunks")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.38\.0['\"]", build) is not None,
        "artifact must be version 1.38.0")
require("Version 1.38.0" in readme and "Version 1.37.0" in readme,
        "release notes must preserve 1.37.0 history")
print("Dampener feedback, one-shot audio, cooldown on both cancel paths, chunk safety, and 1.38.0 passed.")
