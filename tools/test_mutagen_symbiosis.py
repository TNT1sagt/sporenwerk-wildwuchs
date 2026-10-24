#!/usr/bin/env python3
"""Regression coverage for biodiversity-based Mutagen symbiosis and charge maintenance."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen symbiosis regression: " + message)


symbiosis = read("src/main/java/de/sporenwerk/infection/MutagenSymbiosis.java")
for token in (
    "HORIZONTAL_RADIUS = 3",
    "VERTICAL_RADIUS = 1",
    "REQUIRED_SPECIES = 3",
    "mutagenStrength < 2",
    "mutagenStrength >= 3 ? 0.28F : 0.12F",
    "level.hasChunkAt(origin)",
    "level.hasChunkAt(probe)",
    "ModBlocks.FASERROHR.get()",
    "ModBlocks.BERNSTEINKAPPE.get()",
    "ModBlocks.ROTWURZEL.get()",
    "ModBlocks.FILTERMOOS.get()",
    "countCropSpecies(Level level, BlockPos origin)",
):
    require(token in symbiosis, "symbiosis source-of-truth is missing " + token)
require("getChunk(" not in symbiosis and "getChunkNow(" not in symbiosis,
        "biodiversity scan must not force-load chunks")
require("scheduleTick(" not in symbiosis and "getTicker(" not in symbiosis,
        "biodiversity scan must only run during harvest")

crop = read("src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java")
require("MutagenSymbiosis.shouldYield(level, pos, mutagenStrength, level.random)" in crop
        and "ModItems.SYMBIOSEMYZEL.get()" in crop,
        "manual mature crop harvesting must share the biodiversity yield helper")

machine = read("src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java")
require("MutagenSymbiosis.shouldYield(" in machine
        and "level, target, mutagenStrength, level.random" in machine
        and "ModItems.SYMBIOSEMYZEL.get()" in machine,
        "automated Field Collector must use the same biodiversity rule")
require("canFitOutputs(output, residue, mutagenSpores, symbiosisMycelium)" in machine
        and "insertOutputs(output, residue, mutagenSpores, symbiosisMycelium)" in machine,
        "Symbiosemyzel must be reserved atomically before energy/crop mutation")

items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
require('register("symbiosemyzel"' in items and "SymbiosemyzelItem" in items,
        "Symbiosemyzel must be a registered custom item")
require("output.accept(ModItems.SYMBIOSEMYZEL.get())" in creative,
        "Symbiosemyzel must be discoverable in the creative catalogue")

item = read("src/main/java/de/sporenwerk/item/SymbiosemyzelItem.java")
require("tooltip.sporenwerk.symbiosemyzel.1" in item
        and "tooltip.sporenwerk.symbiosemyzel.2" in item,
        "item tooltip must teach the biodiversity and recharge uses")

dampener = read("src/main/java/de/sporenwerk/block/MutagenResonanceDampenerBlock.java")
require("held.is(ModItems.SYMBIOSEMYZEL.get())" in dampener
        and "int nextCharge = currentCharge + 1;" in dampener
        and "state.setValue(CHARGE, nextCharge)" in dampener,
        "Symbiosemyzel should restore exactly one charge")
require("if (currentCharge >= MAX_CHARGE)" in dampener
        and "held.shrink(1)" in dampener,
        "full dampeners must not consume Symbiosemyzel; successful refill must consume one item")
require("MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);" in dampener,
        "one-charge refills must update nearby cached relay signals")

advancement = json.loads(read("src/main/resources/data/sporenwerk/advancements/mutagen_symbiosis.json"))
require(advancement["parent"] == "sporenwerk:mutagen_laboratory"
        and advancement["criteria"]["discover_symbiosis"]["trigger"] == "minecraft:inventory_changed"
        and advancement["criteria"]["discover_symbiosis"]["conditions"]["items"][0]["items"] == ["sporenwerk:symbiosemyzel"],
        "symbiosis research milestone must unlock on the real item discovery")

with Image.open(ASSETS / "textures/item/symbiosemyzel.png") as image:
    rgba = image.convert("RGBA")
    pixels = list(rgba.getdata())
    require(rgba.size == (16, 16), "Symbiosemyzel texture must be 16x16")
    require(any(pixel[3] == 0 for pixel in pixels), "item sprite must have transparent background")
    require(len(set(pixels)) >= 8, "Symbiosemyzel sprite must contain readable pixel detail")
model = json.loads(read("src/main/resources/assets/sporenwerk/models/item/symbiosemyzel.json"))
require(model["textures"]["layer0"] == "sporenwerk:item/symbiosemyzel",
        "item model must point at the new sprite")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    for key in (
        "item.sporenwerk.symbiosemyzel",
        "tooltip.sporenwerk.symbiosemyzel.1",
        "tooltip.sporenwerk.symbiosemyzel.2",
        "message.sporenwerk.dampener.symbiosis_recharged",
        "advancements.sporenwerk.mutagen_symbiosis.title",
        "advancements.sporenwerk.mutagen_symbiosis.description",
    ):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)

preview = read("tools/make_art_preview.py")
require('"symbiosemyzel"' in preview, "visual QA sheet must include the new item")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.46\.0['\"]", build) is not None,
        "artifact must be version 1.46.0")
readme = read("README.md")
require("Version 1.46.0" in readme and "Version 1.45.0" in readme,
        "release notes must add 1.46.0 and preserve 1.45.0 history")
require("Aktueller Entwicklungsstand: 1.46.0" in readme,
        "README current version headline is stale")
print("Biodiversity thresholds, manual/automated crop yield, atomic buffer, dampener refills, relay refresh, research, artwork and localization passed.")
