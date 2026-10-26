#!/usr/bin/env python3
"""Sporenwerk 1.85 regression: living night fields and tranquil controlled farms."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Living Mutagen Ambience 1.85 regression: " + message)


node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
scheduled = node[node.index("public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random)"):
                 node.index("public boolean isRandomlyTicking(BlockState state)")]
helper = scheduled[scheduled.index("private static void emitLivingFieldAmbience("):]
for phrase in (
    "if (powered || state.getValue(POWERED)) return;",
    "if (!MutationNodeData.get(level).isActive(pos)) return;",
    "emitLivingFieldAmbience(level, pos, random, mode);",
    "MutationField.spreadFromNode(level, pos, random);",
    "MutagenBloom.tryTrigger(level, pos, random);",
    "MutationField.cultivateNearbyCrops(level, pos, random);",
    "level.scheduleTick(pos, this, mode == 1 ? 40 : 20);",
):
    require(phrase in scheduled, "node must preserve scheduled fields and gated ambience: " + phrase)
require(scheduled.index("if (powered || state.getValue(POWERED)) return;")
        < scheduled.index("emitLivingFieldAmbience(level, pos, random, mode);"),
        "redstone pause must run before any atmosphere")
require(scheduled.index("if (!MutationNodeData.get(level).isActive(pos)) return;")
        < scheduled.index("emitLivingFieldAmbience(level, pos, random, mode);"),
        "inactive nodes must not emit atmosphere")
require(scheduled.index("int mode = state.getValue(MODE);")
        < scheduled.index("emitLivingFieldAmbience(level, pos, random, mode);")
        < scheduled.index("MutationField.spreadFromNode(level, pos, random);"),
        "atmosphere must never replace the existing terrain-spread logic")
for phrase in (
    "if (mode != 0 && mode != 1) return;",
    "long dayTime = level.getDayTime() % 24000L;",
    "if (mode == 0 && (dayTime < 13000L || dayTime >= 23000L)) return;",
    "random.nextInt(mode == 0 ? 9 : 20)",
    "new AABB(pos).inflate(10.0D, 4.0D, 10.0D)",
    "if (nearby.isSpectator()) continue;",
    'getLong("SporenwerkAmbientPulseUntil")',
    "if (nextPulse > now && nextPulse - now < 1200L) continue;",
    'putLong("SporenwerkAmbientPulseUntil"',
    "now + (mode == 0 ? 440L : 700L)",
    "ParticleTypes.WARPED_SPORE",
    "ParticleTypes.REVERSE_PORTAL",
    "ParticleTypes.SOUL_FIRE_FLAME",
    "ParticleTypes.HAPPY_VILLAGER",
    "ParticleTypes.END_ROD",
    "SoundEvents.RESPAWN_ANCHOR_AMBIENT",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "SoundSource.AMBIENT",
):
    require(phrase in helper, "missing rarity, ambience, mode or bounded multiplayer contract: " + phrase)
require(helper.count("return;") >= 4 and "for (int i = 0; i < 8; i++)" in helper,
        "client ambience must be short, bounded and per-player throttled")
random_tick = node[node.index("public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random)"):
                   node.rfind("\n}")]
require("emitLivingFieldAmbience" not in random_tick,
        "never run extra atmosphere from random node ticks")
for forbidden in ("getChunk(", "getChunkNow(", "setBlock(", "destroyBlock(", "hurt(", "addEffect("):
    require(forbidden not in helper,
            "ambient field effects must not change gameplay or force-load chunks: " + forbidden)
require("int nextMode = (state.getValue(MODE) + 1) % 3;" in node
        and "if (mode == 0)" in node and "else if (mode == 1)" in node,
        "original node mode transitions must remain available")
require('MutationNodeBlock.MODE, 2' in read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java"),
        "existing 1.84 station shutdown must remain intact")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.85\.0['\"]", build),
        "artifact must be version 1.85.0")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.85.0" in readme
        and "Version 1.85.0" in readme and "Version 1.84.0" in readme,
        "current and historical release notes must remain in place")
print("1.85 living Mutagen night pulse, quiet cultivation, player-specific throttling, protected inactive modes and release contracts passed.")
