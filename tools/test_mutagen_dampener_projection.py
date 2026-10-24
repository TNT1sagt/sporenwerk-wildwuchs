#!/usr/bin/env python3
"""Regression tests for the visible, on-demand Resonance Dampener protection volume (1.37.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen dampener protection visualization regression: " + message)


block = read("src/main/java/de/sporenwerk/block/MutagenResonanceDampenerBlock.java")
entity = read("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")
for token in (
    "public static final int HORIZONTAL_RADIUS = 6;",
    "public static final int VERTICAL_RADIUS = 2;",
    "InteractionResult use(",
    "Component.translatable(",
    '"message.sporenwerk.dampener.status"',
    "revealProtectionVolume(serverLevel, pos)",
    "level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME",
    "private static void revealProtectionVolume(ServerLevel level, BlockPos center)",
    "private static void marker(ServerLevel level, double x, double y, double z, int count)",
    "ParticleTypes.END_ROD",
):
    require(token in block, "dampener must provide visible on-demand boundary/status: " + token)
require(block.count("marker(level,") >= 6,
        "protection volume outline must include corners, side midpoints, and vertical edges")
require("onPlace(" not in block and "tick(" not in block and "BlockEntityTicker" not in block and "new BlockEntity" not in block,
        "protection preview must not create a permanent block tick or block entity")

for token in (
    "MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS",
    "MutagenResonanceDampenerBlock.VERTICAL_RADIUS",
    "if (!level().hasChunkAt(pos)) continue;",
    "if (!dampenerState.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())) continue;",
):
    require(token in entity, "server protection scan must share dimensions and stay chunk safe: " + token)
require("origin.offset(-6, -2, -6)" not in entity and "origin.offset(6, 2, 6)" not in entity,
        "entity must not retain divergent hard-coded scan limits")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "protection preview/scan must not force-load chunks")

for filename, expected in {
    "de_de.json": "Schutzbereich horizontal",
    "en_us.json": "Protection volume: ±%s horizontal",
}.items():
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(expected in locale.get("message.sporenwerk.dampener.protection_volume", ""),
            filename + " missing protection status text")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.37\.0['\"]", build) is not None,
        "artifact must be version 1.37.0")
readme = read("README.md")
require("Version 1.37.0" in readme and "Version 1.36.0" in readme,
        "release notes must preserve the previous 1.36.0 loot/research milestone")
print("Visible protection volume, shared server range, localized status, no permanent ticker, chunk safety, and 1.37.0 passed.")
