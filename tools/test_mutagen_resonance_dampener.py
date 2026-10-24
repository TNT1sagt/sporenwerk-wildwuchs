#!/usr/bin/env python3
"""Regression tests for the craftable Mutagen Resonance Dampener."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen Resonance Dampener regression: " + message)


blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
dampener = read("src/main/java/de/sporenwerk/block/MutagenResonanceDampenerBlock.java")
entity = read("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")

for token in (
    "MUTAGEN_RESONANZDAEMPFER",
    'register("mutagen_resonanzdaempfer"',
    'ModItems.ITEMS.register("mutagen_resonanzdaempfer"',
):
    require(token in blocks, "block/item registration missing " + token)
require("output.accept(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())" in creative,
        "dampener must be in the creative tab")
require("extends Block" in dampener and "MutagenResonanceDampenerBlock(Properties properties)" in dampener,
        "dampener block class is missing")

for token in (
    "private boolean isResonanceDamped()",
    "if (isResonanceDamped()) {",
    "if (isResonanceDamped()) {",
    "origin.offset(-6, -2, -6)",
    "origin.offset(6, 2, 6)",
    "if (!level().hasChunkAt(pos)) continue;",
    "ModBlocks.MUTAGEN_RESONANZDAEMPFER.get()",
    "resonanceWindup = 0;",
):
    require(token in entity, "entity must detect/cancel dampened pulse: " + token)
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "dampener scan must not force-load chunks")

state = json.loads((ASSETS / "blockstates/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(state["variants"][""]["model"] == "sporenwerk:block/mutagen_resonanzdaempfer",
        "blockstate must point to dampener model")
model = json.loads((ASSETS / "models/block/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(model["parent"] == "minecraft:block/cube_column"
        and model["textures"]["end"] == "sporenwerk:block/mutagen_resonanzdaempfer_top"
        and model["textures"]["side"] == "sporenwerk:block/mutagen_resonanzdaempfer_side",
        "dampener model must map the top and side texture correctly")
item_model = json.loads((ASSETS / "models/item/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(item_model["parent"] == "sporenwerk:block/mutagen_resonanzdaempfer",
        "item model must use the dampener block model")

for name in ("mutagen_resonanzdaempfer_top", "mutagen_resonanzdaempfer_side"):
    with Image.open(ASSETS / f"textures/block/{name}.png") as source:
        image = source.convert("RGBA")
    require(image.size == (16, 16), name + " must be a 16x16 texture")
    require(all(px[3] == 255 for px in image.getdata()), name + " must be fully opaque")
    require(len(set(image.getdata())) >= 12, name + " must have enough readable pixel detail")

recipe = json.loads((RES / "data/sporenwerk/recipes/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(recipe["result"]["item"] == "sporenwerk:mutagen_resonanzdaempfer",
        "recipe must produce the dampener")
ingredients = {entry["item"] for entry in recipe["key"].values()}
require({"minecraft:iron_ingot", "minecraft:redstone", "minecraft:amethyst_block",
         "sporenwerk:mutagenkernkristall", "sporenwerk:kristallpirscher_resonanzsplitter"}.issubset(ingredients),
        "recipe must cost iron, redstone, amethyst, a Mutagen core crystal and resonance shards")
advancement = json.loads((RES / "data/sporenwerk/advancements/recipes/misc/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(advancement["rewards"]["recipes"] == ["sporenwerk:mutagen_resonanzdaempfer"]
        and len(advancement["requirements"]) == 5,
        "recipe unlock should require all five ingredients")
loot = json.loads((RES / "data/sporenwerk/loot_tables/blocks/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(any(entry.get("name") == "sporenwerk:mutagen_resonanzdaempfer"
            for pool in loot["pools"] for entry in pool["entries"]),
        "dampener block loot must drop itself")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    require(data.get("block.sporenwerk.mutagen_resonanzdaempfer", "").strip(),
            locale + " block translation missing")
    require(data.get("item.sporenwerk.mutagen_resonanzdaempfer", "").strip(),
            locale + " item translation missing")

preview = read("tools/make_art_preview.py")
require("mutagen_resonanzdaempfer_top" in preview and "mutagen_resonanzdaempfer_side" in preview,
        "both dampener faces must appear in the QA preview")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.36\.0['\"]", build) is not None,
        "artifact must be version 1.36.0")
readme = read("README.md")
require("Version 1.35.0" in readme and "Version 1.34.0" in readme,
        "release notes must preserve 1.34.0 history")
print("Mutagen Resonance Dampener registration, pulse suppression, chunk safety, recipes, loot, pixel art, locales and version passed.")
