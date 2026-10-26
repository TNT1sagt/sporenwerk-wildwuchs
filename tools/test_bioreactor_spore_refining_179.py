#!/usr/bin/env python3
"""Regression tests for the Mutagene Sporen refinery route in the Biomass Bioreactor (1.79.0)."""
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
        raise SystemExit("Bioreactor spore refining 1.79 regression: " + message)


machine = read("src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java")
token = "else if (input.is(ModItems.MUTAGENE_SPOREN.get()))"
require(token in machine, "Biomass Bioreactor must accept Mutagene Sporen")
start = machine.index(token)
end = machine.find("} else progress = 0;", start)
require(end > start, "spore refinery branch must terminate cleanly")
branch = machine[start:end]
for item in (
    "final int sporeBatchSize = 4",
    "final int sporeBatchEnergy = 240",
    "input.getCount() < sporeBatchSize",
    "new ItemStack(ModItems.MUTAGENEXTRAKT.get())",
    "canFitOutput(extract)",
    "consumePower(sporeBatchEnergy)",
    "insertOutput(extract)",
    "inventory.extractItem(0, sporeBatchSize, false)",
    "storedPoints = Math.min(1_000_000, storedPoints + 18)",
    "skills.addCraft()",
    "setChanged()",
):
    require(item in branch, "spore refinery is missing transaction contract " + item)
order = (
    "input.getCount() < sporeBatchSize",
    "canFitOutput(extract)",
    "consumePower(sporeBatchEnergy)",
    "insertOutput(extract)",
    "inventory.extractItem(0, sporeBatchSize, false)",
)
positions = [branch.index(item) for item in order]
require(positions == sorted(positions),
        "incomplete batches, output space, energy and output insertion must be validated before consuming spores")
require("else if (input.is(ModItems.SYMBIOSEMYZEL.get()))" in machine
        and "consumePower(180)" in machine,
        "the more efficient Symbiosemyzel refinery route must remain available")

item = read("src/main/java/de/sporenwerk/item/MutageneSporenItem.java")
require('tooltip.add(Component.translatable("tooltip.sporenwerk.mutagene_sporen.3")' in item,
        "Mutagene Sporen tooltip must explain the new refining route")
for locale, expected in (
    ("de_de.json", "4 Sporen + 240 FE ergeben 1 Mutagenextrakt"),
    ("en_us.json", "4 spores + 240 FE refine into 1 Mutagen Extract"),
):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    require(expected in data.get("tooltip.sporenwerk.mutagene_sporen.3", ""),
            locale + " lacks the exact spore refinery instructions")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.79\.0['\"]", build) is not None,
        "artifact must be version 1.79.0")
readme = read("README.md")
require("Version 1.79.0" in readme and "Version 1.78.0" in readme
        and "Aktueller Entwicklungsstand: 1.79.0" in readme,
        "release history must preserve 1.78 and identify current version")
print("1.79 Biomass Bioreactor spore refining, bounded input transaction, Symbiosemyzel path, tooltip and release metadata passed.")
