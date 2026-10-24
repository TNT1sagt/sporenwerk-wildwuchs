#!/usr/bin/env python3
"""Regression tests for the 1.47.0 Symbiosemyzel research chain and biodiversity survey."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Symbiosis research progression regression: " + message)


recipe = json.loads(read("src/main/resources/data/sporenwerk/recipes/sporenfiltereinsatz_mutagen.json"))
recipe_ingredients = {entry["item"] for entry in recipe.get("ingredients", [])}
for ingredient in (
    "sporenwerk:sporenfiltereinsatz_verstaerkt",
    "sporenwerk:mutagenextrakt",
    "minecraft:amethyst_shard",
    "sporenwerk:symbiosemyzel",
):
    require(ingredient in recipe_ingredients, "highest-tier filter recipe missing " + ingredient)
require(recipe["result"]["item"] == "sporenwerk:sporenfiltereinsatz_mutagen",
        "the ecological upgrade must still craft the mutagenic cartridge")

unlock = json.loads(read("src/main/resources/data/sporenwerk/advancements/recipes/misc/sporenfiltereinsatz_mutagen.json"))
require(unlock["parent"] == "sporenwerk:mutagen_laboratory",
        "filter progression must remain attached to laboratory research")
require(unlock["criteria"]["discover_mutagen_extract"]["conditions"]["items"][0]["items"]
        == ["sporenwerk:mutagenextrakt"],
        "laboratory extract remains a required research discovery")
require(unlock["criteria"]["discover_symbiosis_mycelium"]["trigger"] == "minecraft:inventory_changed"
        and unlock["criteria"]["discover_symbiosis_mycelium"]["conditions"]["items"][0]["items"]
        == ["sporenwerk:symbiosemyzel"],
        "Symbiosemyzel must be a real discovery criterion")
require(unlock["requirements"] == [["discover_mutagen_extract"], ["discover_symbiosis_mycelium"]],
        "both research discoveries must be required, not alternatives")
require(unlock["rewards"]["recipes"] == ["sporenwerk:sporenfiltereinsatz_mutagen"],
        "the advancement must unlock the intended recipe")

scanner = read("src/main/java/de/sporenwerk/item/FeldscannerItem.java")
for token in (
    "int cropSpecies)",
    "boolean hasFiberCrop = false",
    "boolean hasAmberCrop = false",
    "boolean hasRootCrop = false",
    "boolean hasFilterMossCrop = false",
    "state.is(ModBlocks.FASERROHR.get())",
    "state.is(ModBlocks.BERNSTEINKAPPE.get())",
    "state.is(ModBlocks.ROTWURZEL.get())",
    "state.is(ModBlocks.FILTERMOOS.get())",
    "int cropSpecies = (hasFiberCrop ? 1 : 0)",
    "survey.cropSpecies()",
    "message.sporenwerk.scanner.survey.biodiversity",
):
    require(token in scanner, "field scanner biodiversity reporting missing " + token)
require("level.hasChunkAt(cursor)" in scanner
        and "getChunk(" not in scanner and "getChunkNow(" not in scanner,
        "biodiversity reporting must continue to skip unloaded chunks and avoid forced loading")
require("scheduleTick(" not in scanner and "getTicker(" not in scanner,
        "the area survey must remain interaction-driven")
require("The research unlock is tied to the full advancement" not in scanner,
        "scanner Java should not contain documentation-only claims unrelated to behavior")

symbiosis_item = read("src/main/java/de/sporenwerk/item/SymbiosemyzelItem.java")
require("tooltip.sporenwerk.symbiosemyzel.3" in symbiosis_item,
        "Symbiosemyzel tooltip must explain its high-tier filter use")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    for key in (
        "tooltip.sporenwerk.symbiosemyzel.3",
        "message.sporenwerk.scanner.survey.biodiversity",
        "advancements.sporenwerk.filter_mutagen_research.description",
    ):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)

old_filter_test = read("tools/test_filter_maintenance.py")
require("sporenfiltereinsatz_mutagen.json" in old_filter_test,
        "existing filter maintenance contract test must continue to run")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.47\.0['\"]", build) is not None,
        "artifact must be version 1.47.0")
readme = read("README.md")
require("Version 1.47.0" in readme and "Version 1.46.0" in readme,
        "release notes must add 1.47.0 while preserving 1.46.0")
require("Aktueller Entwicklungsstand: 1.47.0" in readme,
        "README current development headline is stale")
print("Mutagenic cartridge ingredients, dual research unlock, biodiversity diagnostics, chunk safety and DE/EN text passed.")
