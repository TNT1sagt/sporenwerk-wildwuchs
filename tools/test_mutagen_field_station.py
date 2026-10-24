#!/usr/bin/env python3
"""Regression tests for Mutagen Field Control Station behavior and assets."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
res = root / "src/main/resources"
assets = res / "assets/sporenwerk"

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen field station regression: " + message)

blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
station = read("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java")
stabilizer = read("src/main/java/de/sporenwerk/block/MutagenFieldStabilizerBlock.java")
require("MUTAGENFELD_KONTROLLSTATION" in blocks and 'register("mutagenfeld_kontrollstation"' in blocks
        and "MutagenFieldControlStationBlock" in blocks, "station block registration is missing")
require('ModItems.ITEMS.register("mutagenfeld_kontrollstation"' in blocks
        and "output.accept(ModBlocks.MUTAGENFELD_KONTROLLSTATION.get())" in creative,
        "station needs a placeable block item and creative entry")
for token in ("HORIZONTAL_SCAN_RADIUS = 16", "VERTICAL_SCAN_RADIUS = 8", "InteractionResult use(",
              "level.hasChunkAt(new BlockPos(x, minY, z))", "if (!level.hasChunkAt(probe)) continue;",
              "ModBlocks.MUTAGEN_BODEN.get()", "InfestedTerrainBlock.MUTAGEN_LEVEL",
              "AbstractSporeCropBlock.MUTAGEN_LEVEL", "MutagenFieldStabilizerBlock",
              "message.sporenwerk.fieldstation.network_active", "message.sporenwerk.fieldstation.network_inactive",
              "new Survey("):
    require(token in station, "missing scan/report behavior: " + token)
require("getChunk(" not in station and "getChunkNow(" not in station,
        "station must not force-load chunks")
require("NETWORK_LINK_RADIUS = 8" in stabilizer and "NETWORK_VERTICAL_LINK_RADIUS = 4" in stabilizer,
        "reported network limits must match the existing stabilizer contract")

state = json.loads((assets / "blockstates/mutagenfeld_kontrollstation.json").read_text(encoding="utf-8"))
require(state["variants"][""]["model"] == "sporenwerk:block/mutagenfeld_kontrollstation",
        "station blockstate points to the wrong model")
model = json.loads((assets / "models/block/mutagenfeld_kontrollstation.json").read_text(encoding="utf-8"))
require(model["parent"] == "minecraft:block/cube_column"
        and model["textures"]["end"] == "sporenwerk:block/mutagenfeld_kontrollstation_top"
        and model["textures"]["side"] == "sporenwerk:block/mutagenfeld_kontrollstation_side",
        "station must use the correct top/side textures")
item = json.loads((assets / "models/item/mutagenfeld_kontrollstation.json").read_text(encoding="utf-8"))
require(item["parent"] == "sporenwerk:block/mutagenfeld_kontrollstation",
        "station item model should inherit its block model")
for name in ("mutagenfeld_kontrollstation_top", "mutagenfeld_kontrollstation_side"):
    with Image.open(assets / f"textures/block/{name}.png") as im:
        rgba = im.convert("RGBA")
        require(rgba.size == (16, 16), name + " must be 16x16")
        require(all(px[3] == 255 for px in rgba.getdata()), name + " must be fully opaque")

recipe = json.loads((res / "data/sporenwerk/recipes/mutagenfeld_kontrollstation.json").read_text(encoding="utf-8"))
require(recipe["result"]["item"] == "sporenwerk:mutagenfeld_kontrollstation", "wrong recipe output")
ingredients = {entry["item"] for entry in recipe["key"].values()}
require({"minecraft:amethyst_shard", "minecraft:redstone", "sporenwerk:mutagenextrakt",
         "sporenwerk:mutagenfeld_stabilisator_hochentwickelt"}.issubset(ingredients),
        "recipe should require the highest stabilizer and Mutagen research materials")
advancement = json.loads((res / "data/sporenwerk/advancements/mutagen_field_station_unlock.json").read_text(encoding="utf-8"))
require(advancement["parent"] == "sporenwerk:mutagen_laboratory"
        and advancement["rewards"]["recipes"] == ["sporenwerk:mutagenfeld_kontrollstation"],
        "station recipe unlock must be tied to Mutagen Laboratory progress")
require(advancement["requirements"] == [["acquire_advanced_stabilizer", "acquire_mutagen_extract"]],
        "station unlock requires both advanced stabilizer and extract")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((assets / "lang" / locale).read_text(encoding="utf-8"))
    for key in ("block.sporenwerk.mutagenfeld_kontrollstation", "item.sporenwerk.mutagenfeld_kontrollstation",
                "advancements.sporenwerk.mutagen_field_station.title",
                "advancements.sporenwerk.mutagen_field_station.description",
                "message.sporenwerk.fieldstation.header", "message.sporenwerk.fieldstation.soil",
                "message.sporenwerk.fieldstation.crops", "message.sporenwerk.fieldstation.stabilizers",
                "message.sporenwerk.fieldstation.network_active", "message.sporenwerk.fieldstation.network_inactive",
                "message.sporenwerk.fieldstation.loaded_chunks_only"):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)
preview = read("tools/make_art_preview.py")
require("mutagenfeld_kontrollstation_top" in preview and "mutagenfeld_kontrollstation_side" in preview,
        "QA preview must include both station textures")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.27\.0['\"]", read("build.gradle")) is not None,
        "artifact must be version 1.27.0")
require("Version 1.27.0" in read("README.md") and "Version 1.26.0" in read("README.md"),
        "release notes must add 1.27.0 and preserve 1.26.0")
print("Mutagen Field Control Station scan, network status, research unlock, resources, textures and locales passed.")
