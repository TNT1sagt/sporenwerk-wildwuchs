#!/usr/bin/env python3
"""Regression coverage for operational Mutagen field convergence (1.73.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen field convergence 1.73 regression: " + message)


nodes = read("src/main/java/de/sporenwerk/infection/MutationNodeData.java")
start = nodes.find("public int getOperationalFieldStrengthAt(")
end = nodes.find("\n    }", start)
require(start >= 0 and end > start, "operational field-strength method is missing")
method = nodes[start:end]
for token in (
    "int best = 0;",
    "int overlappingSources = 0;",
    "if (!entry.getValue()) continue;",
    "if (!level.hasChunkAt(origin)) continue;",
    "level.getBlockState(origin)",
    "source.is(ModBlocks.INFEKTIONSHERD.get())",
    "source.getValue(MutationNodeBlock.POWERED)",
    "source.getValue(MutationNodeBlock.MODE) == 2",
    "level.hasNeighborSignal(origin)",
    "if (horizontalSquared > (long) radius * radius || vertical > halfHeight) continue;",
    "overlappingSources++;",
    "if (best == 3 && overlappingSources >= 2) return 3;",
    "return overlappingSources >= 2 ? Math.min(3, best + 1) : best;",
):
    require(token in method, "field convergence contract missing: " + token)
require("getChunk(" not in method and "getChunkNow(" not in method,
        "field-strength queries must not force-load chunks")
require("getOperationalFieldStrengthAt(" in read("src/main/java/de/sporenwerk/infection/MutationField.java"),
        "the shared MutationField API must use operational field strength")

# All consumer systems must keep using the single shared strength calculation.
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
crop = read("src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java")
scanner = read("src/main/java/de/sporenwerk/item/FeldscannerItem.java")
for source, token, label in (
    (field, "return MutationNodeData.get(serverLevel).getOperationalFieldStrengthAt(", "field/area queries"),
    (crop, "MutationField.mutagenStrengthAt(level, pos)", "crop phenotype"),
    (scanner, "MutationField.mutagenStrengthAt(", "scanner block survey"),
):
    require(token in source, label + " must remain tied to the shared operational intensity")

# The historical scent APIs may inspect saved timestamps and packed positions, but must
# not be changed into world-block scans when newer operational field APIs are added.
for signature in ("public BlockPos nearestRecentBloom(", "public int countRecentBlooms("):
    a = nodes.find(signature)
    b = nodes.find("\n    }", a)
    require(a >= 0 and b > a, "historical bloom query is missing: " + signature)
    body = nodes[a:b]
    require("level.getBlockState(" not in body and "getChunk(" not in body and "getChunkNow(" not in body,
            "historical bloom query must remain saved-data-only: " + signature)

for filename, keys in (
    ("de_de.json", ("tooltip.sporenwerk.infektionsherd", "message.sporenwerk.mutation.node_cultivation",
                    "message.sporenwerk.mutation.node_dormant")),
    ("en_us.json", ("tooltip.sporenwerk.infektionsherd", "message.sporenwerk.mutation.node_cultivation",
                    "message.sporenwerk.mutation.node_dormant")),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    for key in keys:
        require(locale.get(key, "").strip(), filename + " is missing operational mode feedback: " + key)
    require("Redstone" in locale["tooltip.sporenwerk.infektionsherd"],
            filename + " must document the Redstone lock")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.73\.0['\"]", build) is not None,
        "artifact must be version 1.73.0")
readme = read("README.md")
require("Version 1.73.0" in readme and "Version 1.72.0" in readme
        and "Aktueller Entwicklungsstand: 1.73.0" in readme,
        "release notes must retain 1.72 and identify the current version")
print("1.73 overlap amplification, source-state gates, strength cap, shared consumers, chunk safety and locale contracts passed.")
