#!/usr/bin/env python3
"""Regression tests for local crop biodiversity readiness in the field station (1.76.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Field-station biodiversity 1.76 regression: " + message)


station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
for token in (
    "import de.sporenwerk.infection.MutationField;",
    "import net.minecraft.world.level.block.CropBlock;",
    "Map<Long, Integer> cropKindsByPosition = new HashMap<>();",
    "List<BlockPos> matureCropPositions = new ArrayList<>();",
    'bs.is(ModBlocks.FASERROHR.get()) ? 1',
    'bs.is(ModBlocks.BERNSTEINKAPPE.get()) ? 2',
    'bs.is(ModBlocks.ROTWURZEL.get()) ? 4',
    'bs.is(ModBlocks.FILTERMOOS.get()) ? 8 : 0',
    "cropBlock.isMaxAge(bs)",
    "Integer.bitCount(cropSpeciesMask)",
    "for (BlockPos maturePos : matureCropPositions)",
    "symbiosisRadiusSquared = 3 * 3",
    "cropKindsByPosition.getOrDefault(speciesProbe.asLong(), 0)",
    "Integer.bitCount(nearbySpeciesMask) >= 3",
    "MutationField.mutagenStrengthAt(level, maturePos) >= 2",
    "s.cropSpecies(), s.matureCrops()",
    "s.symbiosisReadyCrops()",
    "message.sporenwerk.fieldstation.symbiosis_ready",
    "message.sporenwerk.fieldstation.symbiosis_advice",
    "private record Survey(",
):
    require(token in station, "biodiversity readiness contract missing: " + token)
require("level.hasChunkAt(new BlockPos(x, minY, z))" in station,
        "station must preserve the existing loaded-chunk scan boundary")
require("getChunk(" not in station and "getChunkNow(" not in station,
        "station may not force-load chunks")
require("scheduleTick(" not in station and "getTicker(" not in station,
        "station remains on-demand and must not add periodic work")
require(station.index("int cropKind =") < station.index("int networkMembers ="),
        "species collection and readiness scan must live inside survey()")
require(station.index("if (Integer.bitCount(nearbySpeciesMask) >= 3")
        < station.index("MutationField.mutagenStrengthAt(level, maturePos) >= 2"),
        "live field strength should only be queried for a locally diverse mature candidate")

for filename in ("de_de.json", "en_us.json"):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    for key in (
        "message.sporenwerk.fieldstation.biodiversity",
        "message.sporenwerk.fieldstation.symbiosis_ready",
        "message.sporenwerk.fieldstation.symbiosis_advice",
    ):
        require(locale.get(key, "").strip(), filename + " is missing " + key)
    require(locale["message.sporenwerk.fieldstation.biodiversity"].count("%s") == 2,
            filename + " must report both species and mature-crop counts")
    require("%s" in locale["message.sporenwerk.fieldstation.symbiosis_ready"],
            filename + " must report the number of harvest centers")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.76\.0['\"]", build) is not None,
        "artifact must be version 1.76.0")
readme = read("README.md")
require("Version 1.76.0" in readme and "Version 1.75.0" in readme
        and "Aktueller Entwicklungsstand: 1.76.0" in readme,
        "release notes must preserve 1.75 and identify current release")
print("1.76 local biodiversity, mature crop center, live field strength, loaded-chunk safety, actionable capsule advice, locales and version contracts passed.")
