#!/usr/bin/env python3
"""Regression tests for operational Mutagen strength across Node modes (1.72.0)."""
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
        raise SystemExit("Operational Mutagen strength 1.72 regression: " + message)


nodes = read("src/main/java/de/sporenwerk/infection/MutationNodeData.java")
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
crop = read("src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java")

method_start = nodes.find("public int getOperationalFieldStrengthAt(")
require(method_start >= 0, "operational field-strength method missing")
method_end = nodes.find("\n    }", method_start)
require(method_end > method_start, "could not isolate operational field-strength method")
method = nodes[method_start:method_end]
for token in (
    "if (!entry.getValue()) continue;",
    "if (!level.hasChunkAt(origin)) continue;",
    "level.getBlockState(origin)",
    "source.is(ModBlocks.INFEKTIONSHERD.get())",
    "source.getValue(MutationNodeBlock.POWERED)",
    "source.getValue(MutationNodeBlock.MODE) == 2",
    "level.hasNeighborSignal(origin)",
    "int strength = horizontalSquared <= 4L && vertical <= 1 ? 3",
):
    require(token in method, "operational strength must honor real source state: " + token)
require("getChunk(" not in method and "getChunkNow(" not in method,
        "operational intensity must never force-load source chunks")
require("getOperationalFieldStrengthAt(" in field
        and "return MutationNodeData.get(serverLevel).getOperationalFieldStrengthAt(" in field,
        "all consumers must share the operational strength calculation")

for token in (
    "public static void cultivateNearbyCrops(",
    "empowerNearbyCrops(level, origin, random, 6)",
):
    require(token in field, "safe culture mode must still cultivate: " + token)
require("level.getBlockState(origin).getValue(MutationNodeBlock.MODE) != 0" in field,
        "contaminated terrain must stop spreading outside spread mode")
require("MutagenBloom.tryTrigger(level, pos, random)" in node
        and "if (mode == 0)" in node,
        "Bloom must remain exclusive to spread mode")
require("MutationField.mutagenStrengthAt(level, pos)" in crop
        and "state.setValue(MUTAGEN_LEVEL, activeMutagenStrength)" in crop,
        "crop phenotype blocks must use operational strength and reset when it is zero")

for filename, tooltip, cultivation, dormant, paused in (
    ("de_de.json", "KULTUR", "sichere Pflanzenmutation und Wachstum", "Feldstärke 0", "Feldstärke 0"),
    ("en_us.json", "CULTIVATION", "safe crop mutation and growth", "field strength 0", "field strength 0"),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    t = locale.get("tooltip.sporenwerk.infektionsherd", "")
    require(tooltip in t and "Redstone" in t, filename + " tooltip must explain cultivation and Redstone")
    require(cultivation in locale.get("message.sporenwerk.mutation.node_cultivation", ""),
            filename + " cultivation feedback must describe safe crop phenotype")
    require(dormant in locale.get("message.sporenwerk.mutation.node_dormant", ""),
            filename + " dormant feedback must report zero field strength")
    require(paused in locale.get("message.sporenwerk.mutation.node_paused", ""),
            filename + " Redstone feedback must report zero field strength")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.72\.0['\"]", build) is not None,
        "artifact must be version 1.72.0")
readme = read("README.md")
require("Version 1.72.0" in readme and "Version 1.71.0" in readme
        and "Aktueller Entwicklungsstand: 1.72.0" in readme,
        "release notes must retain current and previous release")
print("1.72 operational field strength, crop phenotype reset, safe culture tiers, source gating, chunk safety and translations passed.")
