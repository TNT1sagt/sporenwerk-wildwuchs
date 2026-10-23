#!/usr/bin/env python3
from pathlib import Path
import json, sys
from PIL import Image
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
src = root / "src/main/java/de/sporenwerk"
assets = root / "src/main/resources/assets/sporenwerk"
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Spore filter regression: " + message)
items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
require("SPORENFILTERMASKE" in items and "SporeFilterMaskItem" in items, "mask must be a registered wearable helmet")
mask_item = read("src/main/java/de/sporenwerk/item/SporeFilterMaskItem.java")
require("appendHoverText" in mask_item and "tooltip.sporenwerk.sporenfiltermaske.1" in mask_item
        and "tooltip.sporenwerk.sporenfiltermaske.2" in mask_item,
        "mask must show its protective function in the in-game tooltip")
require("output.accept(ModItems.SPORENFILTERMASKE.get())" in read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java"), "mask missing creative tab")
material = read("src/main/java/de/sporenwerk/item/SporeFilterMaterial.java")
for token in ("implements ArmorMaterial", "getDurabilityForType", "getDefenseForType", "getRepairIngredient", "getEquipSound", "getKnockbackResistance"):
    require(token in material, "armor material is missing " + token)
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
require("player.getItemBySlot(EquipmentSlot.HEAD)" in field and "mask.is(ModItems.SPORENFILTERMASKE.get())" in field, "field exposure must check the mask")
require("mask.hurtAndBreak(1, player" in field and 'putLong("SporenwerkControlledExposureAt", now + 300)' in field and 'putLong("SporenwerkControlledExposureAt", now + 100)' in field, "mask must consume durability and use separate exposure cadence")
recipe = json.loads((root / "src/main/resources/data/sporenwerk/recipes/sporenfiltermaske.json").read_text(encoding="utf-8"))
require(recipe["result"]["item"] == "sporenwerk:sporenfiltermaske", "recipe must output mask")
for ingredient in ("minecraft:leather", "sporenwerk:filtermoos", "minecraft:copper_ingot", "minecraft:charcoal"):
    require(any(x.get("item") == ingredient for x in recipe["key"].values()), "recipe missing " + ingredient)
model = json.loads((assets / "models/item/sporenfiltermaske.json").read_text(encoding="utf-8"))
require(model["textures"]["layer0"] == "sporenwerk:item/sporenfiltermaske", "item model texture incorrect")
for rel, expected in (("textures/item/sporenfiltermaske.png", (16,16)), ("textures/models/armor/sporenfilter_layer_1.png", (64,32))):
    with Image.open(assets / rel) as im: require(im.size == expected, rel + " dimensions incorrect")
for locale in ("de_de.json","en_us.json"):
    d=json.loads((assets / "lang" / locale).read_text(encoding="utf-8"))
    for key in ("item.sporenwerk.sporenfiltermaske","tooltip.sporenwerk.sporenfiltermaske.1","tooltip.sporenwerk.sporenfiltermaske.2"):
        require(bool(d.get(key,"").strip()), locale + " missing " + key)
require("Version 1.14.0" in read("README.md"), "release notes missing version")
print("Wearable spore-filter helmet, recipe, textures, durability protection and locales passed.")
