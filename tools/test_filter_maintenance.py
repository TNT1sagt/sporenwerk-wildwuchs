#!/usr/bin/env python3
"""Contracts for Sporenwerk's maintenance bench and three-grade cartridge progression."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
src = root / "src/main/java/de/sporenwerk"
res = root / "src/main/resources"
assets = res / "assets/sporenwerk"

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit("Filter maintenance regression: " + message)

items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
for name, registry_id, repair in (
    ("SPORENFILTEREINSATZ", "sporenfiltereinsatz", 60),
    ("SPORENFILTEREINSATZ_VERSTAERKT", "sporenfiltereinsatz_verstaerkt", 100),
    ("SPORENFILTEREINSATZ_MUTAGEN", "sporenfiltereinsatz_mutagen", 143),
):
    require(name in items and f'register("{registry_id}"' in items, name + " is not registered")
    require(f"SporeFilterCartridgeItem({repair}," in items, name + " has the wrong repair capacity")
    require(f"output.accept(ModItems.{name}.get())" in creative, name + " is missing from creative tab")

require("SPORENFILTERWARTUNGSTISCH" in blocks
        and 'register("sporenfilterwartungstisch"' in blocks
        and "SporeFilterMaintenanceBlock" in blocks,
        "maintenance bench is not registered")
require('ModItems.ITEMS.register("sporenfilterwartungstisch"' in blocks,
        "maintenance bench must have a placeable block item")
require("output.accept(ModBlocks.SPORENFILTERWARTUNGSTISCH.get())" in creative,
        "maintenance bench is missing from creative tab")

cartridge = read("src/main/java/de/sporenwerk/item/SporeFilterCartridgeItem.java")
for token in (
    "private final int repairAmount",
    "public int repairAmount()",
    "Math.min(repairAmount, before)",
    "Math.max(0, before - repairAmount)",
    "tooltip.sporenwerk.sporenfiltereinsatz.quality.",
):
    require(token in cartridge, "tiered cartridge behavior is missing " + token)

bench = read("src/main/java/de/sporenwerk/block/SporeFilterMaintenanceBlock.java")
for token in (
    "InteractionResult use(BlockState state, Level level, BlockPos pos, Player player",
    "level.isClientSide",
    "instanceof SporeFilterCartridgeItem cartridge",
    "player.getItemBySlot(EquipmentSlot.HEAD)",
    "mask.getDamageValue() <= 0",
    "cartridge.repairAmount()",
    "if (!player.getAbilities().instabuild) cartridgeStack.shrink(1)",
    "message.sporenwerk.filterbench.repaired",
):
    require(token in bench, "maintenance bench is missing " + token)

recipes = {
    "sporenfiltereinsatz.json": ("sporenwerk:sporenfiltereinsatz",
                                  ("sporenwerk:mutagene_sporen", "sporenwerk:filtermoos", "minecraft:charcoal")),
    "sporenfiltereinsatz_verstaerkt.json": ("sporenwerk:sporenfiltereinsatz_verstaerkt",
                                             ("sporenwerk:sporenfiltereinsatz", "sporenwerk:mutagenextrakt", "minecraft:copper_ingot")),
    "sporenfiltereinsatz_mutagen.json": ("sporenwerk:sporenfiltereinsatz_mutagen",
                                          ("sporenwerk:sporenfiltereinsatz_verstaerkt", "sporenwerk:mutagenextrakt", "minecraft:amethyst_shard")),
    "sporenfilterwartungstisch.json": ("sporenwerk:sporenfilterwartungstisch",
                                        ("minecraft:iron_ingot", "minecraft:crafting_table", "minecraft:copper_ingot",
                                         "sporenwerk:sporenresistenter_block", "sporenwerk:filtermoos", "minecraft:redstone")),
}
for filename, (output, ingredients) in recipes.items():
    recipe = json.loads((res / "data/sporenwerk/recipes" / filename).read_text(encoding="utf-8"))
    require(recipe["result"]["item"] == output, filename + " has incorrect result")
    actual = {entry["item"] for entry in recipe.get("ingredients", [])}
    actual.update(entry["item"] for entry in recipe.get("key", {}).values())
    require(set(ingredients).issubset(actual), filename + " is missing required ingredients")

state = json.loads((assets / "blockstates/sporenfilterwartungstisch.json").read_text(encoding="utf-8"))
require(state["variants"][""]["model"] == "sporenwerk:block/sporenfilterwartungstisch",
        "bench blockstate must point to its model")
model = json.loads((assets / "models/block/sporenfilterwartungstisch.json").read_text(encoding="utf-8"))
require(model["parent"] == "minecraft:block/cube_column"
        and model["textures"]["end"] == "sporenwerk:block/sporenfilterwartungstisch_top"
        and model["textures"]["side"] == "sporenwerk:block/sporenfilterwartungstisch_side",
        "bench must use valid top/side face textures")
bench_item_model = json.loads((assets / "models/item/sporenfilterwartungstisch.json").read_text(encoding="utf-8"))
require(bench_item_model["parent"] == "sporenwerk:block/sporenfilterwartungstisch",
        "bench item model must use the block model")
for name in ("sporenfilterwartungstisch_top", "sporenfilterwartungstisch_side"):
    with Image.open(assets / f"textures/block/{name}.png") as image:
        rgba = image.convert("RGBA")
        require(rgba.size == (16, 16), name + " must be 16x16")
        require(all(px[3] == 255 for px in rgba.getdata()), name + " must be opaque")

for name in ("sporenfiltereinsatz_verstaerkt", "sporenfiltereinsatz_mutagen"):
    model = json.loads((assets / f"models/item/{name}.json").read_text(encoding="utf-8"))
    require(model["textures"]["layer0"] == f"sporenwerk:item/{name}", name + " model texture mismatch")
    with Image.open(assets / f"textures/item/{name}.png") as image:
        require(image.size == (16, 16) and image.convert("RGBA").getbbox() is not None,
                name + " texture must be a non-empty 16x16 sprite")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((assets / "lang" / locale).read_text(encoding="utf-8"))
    for key in (
        "item.sporenwerk.sporenfiltereinsatz_verstaerkt",
        "item.sporenwerk.sporenfiltereinsatz_mutagen",
        "block.sporenwerk.sporenfilterwartungstisch",
        "item.sporenwerk.sporenfilterwartungstisch",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.basic",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.reinforced",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.mutagen",
        "tooltip.sporenwerk.sporenfilterwartungstisch.1",
        "tooltip.sporenwerk.sporenfilterwartungstisch.2",
        "message.sporenwerk.filterbench.hold_cartridge",
        "message.sporenwerk.filterbench.repaired",
    ):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)

build = read("build.gradle")
require(re.search(r"version\s*=\s*['\"]1\.19\.0['\"]", build) is not None,
        "artifact version must be 1.19.0")
require("Version 1.19.0" in read("README.md"), "1.19.0 release notes are missing")
preview = read("tools/make_art_preview.py")
require("sporenfilterwartungstisch_top" in preview
        and "sporenfiltereinsatz_mutagen" in preview,
        "art preview must show the new maintenance assets")
print("Filter bench, three cartridge qualities, upgrade recipes, block models/textures, tooltips and locales passed.")
