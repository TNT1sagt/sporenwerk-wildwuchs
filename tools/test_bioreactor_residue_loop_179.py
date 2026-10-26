#!/usr/bin/env python3
"""Regression tests for the automated plant-residue -> biomass -> compost loop (1.79.0)."""
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
        raise SystemExit("Bioreactor residue loop 1.79 regression: " + message)


machine = read("src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java")
token = "else if (input.is(ModItems.PFLANZENRESTE.get()))"
require(token in machine, "Biomass Bioreactor must accept plant residue")
marker = "final int residueBatchSize = 4"
require(marker in machine, "plant-residue processing batch is missing")
marker_index = machine.index(marker)
start = machine.rfind(token, 0, marker_index)
end = machine.find("} else if (input.is(ModItems.BIOMASSE.get()))", marker_index)
require(start >= 0 and end > marker_index, "could not isolate the residue-refining transaction")
branch = machine[start:end]
for item in (
    "final int residueBatchEnergy = 60",
    "input.getCount() < residueBatchSize",
    "new ItemStack(ModItems.BIOMASSE.get())",
    "canFitOutput(biomass)",
    "consumePower(residueBatchEnergy)",
    "insertOutput(biomass)",
    "inventory.extractItem(0, residueBatchSize, false)",
    "storedPoints = Math.min(1_000_000, storedPoints + 12)",
    "skills.addCraft()",
    "setChanged()",
):
    require(item in branch, "residue-refining transaction is missing " + item)
ordered = (
    "input.getCount() < residueBatchSize",
    "canFitOutput(biomass)",
    "consumePower(residueBatchEnergy)",
    "insertOutput(biomass)",
    "inventory.extractItem(0, residueBatchSize, false)",
)
positions = [branch.index(item) for item in ordered]
require(positions == sorted(positions),
        "batch size/output/power/insertion checks must precede residue consumption")
require("new ItemStack(ModItems.MYZELKOMPOST.get(), 2)" in machine
        and "consumePower(80)" in machine,
        "existing biomass -> two compost process must stay intact")
require(machine.index("else if (input.is(ModItems.PFLANZENRESTE.get()))")
        < machine.index("else if (input.is(ModItems.BIOMASSE.get()))"),
        "residue refining must precede the biomass-to-compost stage in the same process chain")

tooltip = read("src/main/java/de/sporenwerk/client/PflanzenresteTooltipEvents.java")
for token in (
    '@Mod.EventBusSubscriber(modid = "sporenwerk", bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)',
    "public static void onItemTooltip(ItemTooltipEvent event)",
    "event.getItemStack().is(ModItems.PFLANZENRESTE.get())",
    'Component.translatable("tooltip.sporenwerk.pflanzenreste.refining")',
    'Component.translatable("tooltip.sporenwerk.pflanzenreste.loop")',
):
    require(token in tooltip, "plant-residue tooltip event is missing " + token)
for locale, values in (
    ("de_de.json", (
        "4 Pflanzenreste + 60 FE ergeben 1 Biomasse",
        "zu 2 Myzelkompost weiterverarbeitet",
    )),
    ("en_us.json", (
        "4 plant residues + 60 FE refine into 1 Biomass",
        "processed into 2 Mycelium Compost",
    )),
):
    lang = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    for key, expected in zip(
        ("tooltip.sporenwerk.pflanzenreste.refining", "tooltip.sporenwerk.pflanzenreste.loop"),
        values
    ):
        require(expected in lang.get(key, ""), locale + " lacks " + key)

for crop in ("faserrohr", "bernsteinkappe", "rotwurzel", "filtermoos"):
    loot = json.loads((ROOT / f"src/main/resources/data/sporenwerk/loot_tables/blocks/{crop}.json").read_text(encoding="utf-8"))
    require(any(any(entry.get("name") == "sporenwerk:pflanzenreste" for entry in pool.get("entries", []))
                for pool in loot.get("pools", [])),
            crop + " must retain its plant-residue farm output")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.79\.0['\"]", build) is not None,
        "artifact must be version 1.79.0")
readme = read("README.md")
require("Version 1.79.0" in readme and "Version 1.78.0" in readme
        and "Aktueller Entwicklungsstand: 1.79.0" in readme,
        "release history must preserve 1.78 and identify current version")
print("1.79 automated residue-to-biomass refining, biomass-to-compost stage, transaction guards, tooltip and release metadata passed.")
