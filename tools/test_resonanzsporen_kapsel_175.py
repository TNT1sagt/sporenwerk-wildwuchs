#!/usr/bin/env python3
"""Regression tests for the Resonance Spore Capsule's farming/containment loop (1.75.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Resonance Spore Capsule 1.75 regression: " + message)


items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
item = read("src/main/java/de/sporenwerk/item/ResonanzsporenKapselItem.java")
dampener = read("src/main/java/de/sporenwerk/block/MutagenResonanceDampenerBlock.java")
for token in ('import de.sporenwerk.item.ResonanzsporenKapselItem;',
              'ITEMS.register("resonanzsporen_kapsel"',
              "new ResonanzsporenKapselItem(new Item.Properties().stacksTo(16))"):
    require(token in items, "item registration missing " + token)
require("output.accept(ModItems.RESONANZSPORNENKAPSEL.get())" in creative,
        "capsule missing from creative catalogue")

for token in (
    "state.getBlock() instanceof AbstractSporeCropBlock crop",
    "if (level.isClientSide) return InteractionResult.SUCCESS;",
    "int nextAge = Math.min(crop.getMaxAge(), age + 2)",
    "MutationField.mutagenStrengthAt(level, pos)",
    "AbstractSporeCropBlock.MUTAGEN_LEVEL",
    "if (!context.getPlayer().getAbilities().instabuild) held.shrink(1)",
    "message.sporenwerk.resonanzkapsel.crop_mature",
    "message.sporenwerk.resonanzkapsel.crop_grown",
    "ParticleTypes.HAPPY_VILLAGER",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
):
    require(token in item, "crop-use contract missing " + token)
require("if (age >= crop.getMaxAge())" in item,
        "mature crops must preserve the capsule")
require("ModBlocks.INFEKTIONSHERD" not in item and "spreadFromNode" not in item,
        "crop treatment must not trigger or expand terrain infection")

for token in (
    "held.is(ModItems.RESONANZSPORNENKAPSEL.get())",
    "if (currentCharge >= MAX_CHARGE)",
    "int nextCharge = currentCharge + 1",
    "state.setValue(CHARGE, nextCharge)",
    "MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos)",
    "held.shrink(1)",
    "message.sporenwerk.resonanzkapsel.dampener_full",
    "message.sporenwerk.resonanzkapsel.dampener_recharged",
):
    require(token in dampener, "dampener charge contract missing " + token)
branch_start = dampener.find("held.is(ModItems.RESONANZSPORNENKAPSEL.get())")
branch_end = dampener.find("if (held.is(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get()))", branch_start)
require(branch_start >= 0 and branch_end > branch_start, "capsule branch must be separate from rare-shard refill")
branch = dampener[branch_start:branch_end]
require(branch.index("if (currentCharge >= MAX_CHARGE)") < branch.index("held.shrink(1)"),
        "full dampener must be checked before item consumption")
require(branch.index("state.setValue(CHARGE, nextCharge)") < branch.index("held.shrink(1)"),
        "charge must be committed before spending the capsule")
require("getAnalogOutputSignal" not in branch and "setBlock(pos, state.setValue(CHARGE, MAX_CHARGE)" not in branch,
        "capsule restores exactly one charge rather than filling the full reservoir")

recipe = json.loads(read("src/main/resources/data/sporenwerk/recipes/resonanzsporen_kapsel.json"))
require(recipe["type"] == "minecraft:crafting_shaped"
        and recipe["pattern"] == [" S ", "MBM", " R "],
        "capsule recipe schema or shape changed")
require(recipe["result"] == {"item": "sporenwerk:resonanzsporen_kapsel", "count": 2},
        "recipe should create two capsules")
for key, name in (("S", "sporenwerk:symbiosemyzel"),
                  ("M", "sporenwerk:mutagene_sporen"),
                  ("B", "minecraft:bone_meal"),
                  ("R", "minecraft:redstone")):
    require(recipe["key"][key]["item"] == name, "recipe ingredient incorrect: " + key)
advancement = json.loads(read("src/main/resources/data/sporenwerk/advancements/recipes/misc/resonanzsporen_kapsel.json"))
require(advancement["rewards"]["recipes"] == ["sporenwerk:resonanzsporen_kapsel"],
        "recipe advancement must award the correct recipe")
require(advancement["criteria"]["has_the_recipe"]["conditions"]["recipe"] == "sporenwerk:resonanzsporen_kapsel",
        "recipe advancement recipe criterion missing")

model = json.loads(read("src/main/resources/assets/sporenwerk/models/item/resonanzsporen_kapsel.json"))
require(model["parent"] == "minecraft:item/generated"
        and model["textures"]["layer0"] == "sporenwerk:item/resonanzsporen_kapsel",
        "item model must link to the texture")
with Image.open(ASSETS / "textures/item/resonanzsporen_kapsel.png") as source:
    image = source.convert("RGBA")
pixels = list(image.getdata())
require(image.size == (16, 16), "capsule must use native 16x16 pixel art")
require(sum(1 for p in pixels if p[3] == 0) >= 20, "capsule sprite needs transparency")
require(len(set(pixels)) >= 10, "capsule sprite has insufficient facet contrast")
require(any(r > 200 and g > 180 and b < 190 and a > 0 for r, g, b, a in pixels),
        "capsule should carry a visible amber spore accent")
require(any(g > 190 and b > 200 and a > 0 for r, g, b, a in pixels),
        "capsule should carry a visible cyan resonance core")

for locale in ("de_de.json", "en_us.json"):
    lang = json.loads(read(f"src/main/resources/assets/sporenwerk/lang/{locale}"))
    for key in (
        "item.sporenwerk.resonanzsporen_kapsel",
        "tooltip.sporenwerk.resonanzsporen_kapsel.1",
        "tooltip.sporenwerk.resonanzsporen_kapsel.2",
        "message.sporenwerk.resonanzkapsel.crop_mature",
        "message.sporenwerk.resonanzkapsel.crop_grown",
        "message.sporenwerk.resonanzkapsel.dampener_full",
        "message.sporenwerk.resonanzkapsel.dampener_recharged",
        "advancements.sporenwerk.resonanzsporen_kapsel.title",
        "advancements.sporenwerk.resonanzsporen_kapsel.description",
    ):
        require(lang.get(key, "").strip(), f"{locale} missing {key}")

preview = read("tools/make_art_preview.py")
require('"resonanzsporen_kapsel"' in preview,
        "visual QA sheet must include the real capsule PNG")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.75\.0['\"]", build) is not None,
        "artifact must be version 1.75.0")
readme = read("README.md")
require("Version 1.75.0" in readme and "Version 1.74.0" in readme
        and "Aktueller Entwicklungsstand: 1.75.0" in readme,
        "release notes must preserve 1.74 and identify the current version")
print("1.75 capsule item, bounded crop growth, operational phenotype, atomic Dampener refill, relay refresh, recipe, art, locales and release metadata passed.")
