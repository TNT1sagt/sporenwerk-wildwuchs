#!/usr/bin/env python3
"""Contracts for filter cartridges, Mutagen Bloom stabilization, resources and research progression."""
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
require("MUTAGENFELD_STABILISATOR" in blocks
        and 'register("mutagenfeld_stabilisator"' in blocks
        and "MutagenFieldStabilizerBlock" in blocks,
        "Mutagen Field Stabilizer must be registered as a block")
require('ModItems.ITEMS.register("mutagenfeld_stabilisator"' in blocks
        and "output.accept(ModBlocks.MUTAGENFELD_STABILISATOR.get())" in creative,
        "field stabilizer needs a placeable BlockItem and creative catalogue entry")
require("MUTAGENKERNKRISTALL" in items and 'register("mutagenkernkristall"' in items,
        "rare bloom core must be registered")

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
    "int before = mask.getDamageValue()",
    "if (before <= 0)",
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
    "mutagenfeld_stabilisator.json": ("sporenwerk:mutagenfeld_stabilisator",
                                       ("minecraft:iron_ingot", "minecraft:redstone", "sporenwerk:sporenresistenter_block",
                                        "sporenwerk:mutagenkernkristall", "sporenwerk:mutagenextrakt")),
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
for name in ("sporenfilterwartungstisch_top", "sporenfilterwartungstisch_side",
             "mutagenfeld_stabilisator_top", "mutagenfeld_stabilisator_side"):
    with Image.open(assets / f"textures/block/{name}.png") as image:
        rgba = image.convert("RGBA")
        require(rgba.size == (16, 16), name + " must be 16x16")
        require(all(px[3] == 255 for px in rgba.getdata()), name + " must be opaque")

for name in ("sporenfiltereinsatz_verstaerkt", "sporenfiltereinsatz_mutagen", "mutagenkernkristall"):
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
        "item.sporenwerk.mutagenkernkristall",
        "tooltip.sporenwerk.mutagenkernkristall.1",
        "tooltip.sporenwerk.mutagenkernkristall.2",
        "block.sporenwerk.mutagenfeld_stabilisator",
        "item.sporenwerk.mutagenfeld_stabilisator",
        "tooltip.sporenwerk.mutagenfeld_stabilisator.1",
        "tooltip.sporenwerk.mutagenfeld_stabilisator.2",
        "message.sporenwerk.mutagen.stabilized",
        "advancements.sporenwerk.mutagen_stabilizer.title",
        "advancements.sporenwerk.mutagen_stabilizer.description",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.basic",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.reinforced",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.mutagen",
        "tooltip.sporenwerk.sporenfilterwartungstisch.1",
        "tooltip.sporenwerk.sporenfilterwartungstisch.2",
        "message.sporenwerk.filterbench.hold_cartridge",
        "message.sporenwerk.filterbench.repaired",
        "message.sporenwerk.filterbench.research_required",
        "advancements.sporenwerk.filter_mutagen_research.title",
        "advancements.sporenwerk.filter_mutagen_research.description",
    ):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)

# Mutagenic tier is both recipe-book locked and server-side effect locked until research.
cartridge = read("src/main/java/de/sporenwerk/item/SporeFilterCartridgeItem.java")
require("MUTAGENIC_REPAIR_AMOUNT = 143" in cartridge
        and "requiresMutagenResearch()" in cartridge
        and 'new ResourceLocation("sporenwerk", "mutagen_laboratory")' in cartridge
        and "getOrStartProgress(research).isDone()" in cartridge
        and "!hasMutagenResearch(player)" in cartridge
        and "message.sporenwerk.filterbench.research_required" in cartridge,
        "mutagen cartridge must require the completed server-side Mutagen Laboratory advancement")
bench = read("src/main/java/de/sporenwerk/block/SporeFilterMaintenanceBlock.java")
require("cartridge.requiresMutagenResearch()" in bench
        and "SporeFilterCartridgeItem.hasMutagenResearch(player)" in bench
        and "message.sporenwerk.filterbench.research_required" in bench,
        "maintenance bench must enforce the same research gate")
research_unlock = json.loads(read("src/main/resources/data/sporenwerk/advancements/recipes/misc/sporenfiltereinsatz_mutagen.json"))
require(research_unlock["parent"] == "sporenwerk:mutagen_laboratory"
        and research_unlock["criteria"]["discover_mutagen_extract"]["trigger"] == "minecraft:inventory_changed"
        and research_unlock["rewards"]["recipes"] == ["sporenwerk:sporenfiltereinsatz_mutagen"],
        "mutagenic cartridge recipe must unlock from Mutagen Laboratory research")
require(research_unlock["criteria"]["discover_mutagen_extract"]["conditions"]["items"][0]["items"]
        == ["sporenwerk:mutagenextrakt"],
        "Mutagen Extract discovery must be the unlock trigger")
# The rare core unlocks the stabilizer recipe and the placed block protects nearby workers.
advancement = json.loads(read("src/main/resources/data/sporenwerk/advancements/recipes/misc/mutagenfeld_stabilisator.json"))
require(advancement["parent"] == "sporenwerk:first_mutagen_bloom"
        and advancement["criteria"]["find_condensed_core"]["trigger"] == "minecraft:inventory_changed"
        and advancement["criteria"]["find_condensed_core"]["conditions"]["items"][0]["items"] == ["sporenwerk:mutagenkernkristall"]
        and advancement["rewards"]["recipes"] == ["sporenwerk:mutagenfeld_stabilisator"],
        "collecting the rare bloom core must unlock the stabilizer recipe")
stabilizer_state = json.loads((assets / "blockstates/mutagenfeld_stabilisator.json").read_text(encoding="utf-8"))
require(stabilizer_state["variants"][""]["model"] == "sporenwerk:block/mutagenfeld_stabilisator",
        "stabilizer blockstate must point to the registered model")
stabilizer_model = json.loads((assets / "models/block/mutagenfeld_stabilisator.json").read_text(encoding="utf-8"))
require(stabilizer_model["parent"] == "minecraft:block/cube_column"
        and stabilizer_model["textures"]["end"] == "sporenwerk:block/mutagenfeld_stabilisator_top"
        and stabilizer_model["textures"]["side"] == "sporenwerk:block/mutagenfeld_stabilisator_side",
        "stabilizer must use its own top and side textures")
bloom = read("src/main/java/de/sporenwerk/infection/MutagenBloom.java")
require("hasNearbyStabilizer(level, player.blockPosition())" in bloom
        and "level.getBlockState(probe).is(ModBlocks.MUTAGENFELD_STABILISATOR.get())" in bloom
        and "message.sporenwerk.mutagen.stabilized" in bloom,
        "stabilizer must prevent the bloom exposure pulse within the bounded local radius")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.22\.0['\"]", build) is not None,
        "root Gradle project version must be 1.22.0")
require("Version 1.22.0" in read("README.md"), "1.22.0 release notes are missing")
preview = read("tools/make_art_preview.py")
require("sporenfilterwartungstisch_top" in preview
        and "sporenfiltereinsatz_mutagen" in preview,
        "art preview must show the new maintenance assets")
print("Filter bench, three cartridge qualities, upgrade recipes, block models/textures, tooltips and locales passed.")
