#!/usr/bin/env python3
"""Regression tests for Sporenwerk 1.49.0 Resonanzfokus."""
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


def require(condition, message):
    if not condition:
        raise SystemExit("Resonanzfokus regression: " + message)


item = read("src/main/java/de/sporenwerk/item/ResonanzfokusItem.java")
for token in (
    "PULSE_RADIUS = 5.5D", "MAX_TARGETS = 3", "COOLDOWN_TICKS = 80",
    "DaemmerlingEntity.class", "KristallpirscherEntity.class",
    "player.hasLineOfSight(target)", "player.distanceToSqr(target) > PULSE_RADIUS * PULSE_RADIUS",
    "targets.sort(Comparator.comparingDouble", "if (affected >= MAX_TARGETS) break;",
    "target.hurt(player.damageSources().magic()", "MobEffects.MOVEMENT_SLOWDOWN",
    "target.knockback(0.9D", "ParticleTypes.WARPED_SPORE", "ParticleTypes.END_ROD",
    "SoundEvents.AMETHYST_BLOCK_CHIME", "player.getCooldowns().addCooldown(this, COOLDOWN_TICKS)",
    "message.sporenwerk.resonanzfokus.no_target",
    "message.sporenwerk.resonanzfokus.need_shard", "message.sporenwerk.resonanzfokus.used",
):
    require(token in item, "combat contract missing " + token)
use_start = item.index("public InteractionResultHolder<ItemStack> use(")
consume_start = item.index("private static boolean consumeResonanceShard(")
use_method = item[use_start:consume_start]
require(use_method.index("if (targets.isEmpty())") < use_method.index("if (!consumeResonanceShard(player))"),
        "target search must precede ammunition consumption")
require(use_method.index("if (!consumeResonanceShard(player))") < use_method.index("target.hurt("),
        "ammunition must be spent before the effect is applied")
require(".removeItem(slot, 1)" in item and "KRISTALLPIRSCHER_RESONANZSPLITTER.get()" in item,
        "exactly one existing resonance shard must be spent")
require("getEntitiesOfClass(" in use_method and "getChunk(" not in use_method and "getChunkNow(" not in use_method,
        "pulse must target nearby entities without requesting chunks")

items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
require("ResonanzfokusItem" in items and 'register("resonanzfokus"' in items,
        "Resonanzfokus must be registered")
require("output.accept(ModItems.RESONANZFOKUS.get())" in creative, "creative tab entry missing")

recipe = json.loads(read("src/main/resources/data/sporenwerk/recipes/resonanzfokus.json"))
require(recipe["type"] == "minecraft:crafting_shaped" and recipe["pattern"] == [" S ", "ARA", " C "],
        "shaped recipe schema incorrect")
require(recipe["result"] == {"item": "sporenwerk:resonanzfokus", "count": 1}, "recipe output incorrect")
require(recipe["key"]["S"]["item"] == "sporenwerk:kristallpirscher_resonanzsplitter",
        "recipe must use Crystal Stalker loot")
require(recipe["key"]["A"]["item"] == "minecraft:amethyst_shard"
        and recipe["key"]["R"]["item"] == "minecraft:redstone"
        and recipe["key"]["C"]["item"] == "minecraft:copper_ingot",
        "recipe needs amethyst, redstone and copper")
advancement = json.loads(read("src/main/resources/data/sporenwerk/advancements/recipes/misc/resonanzfokus.json"))
require(advancement["rewards"]["recipes"] == ["sporenwerk:resonanzfokus"]
        and "has_resonance_shard" in advancement["criteria"],
        "recipe-book unlock must depend on shard progression")

model = json.loads(read("src/main/resources/assets/sporenwerk/models/item/resonanzfokus.json"))
require(model["parent"] == "minecraft:item/generated"
        and model["textures"]["layer0"] == "sporenwerk:item/resonanzfokus", "item model reference incorrect")
with Image.open(ASSETS / "textures/item/resonanzfokus.png") as source:
    art = source.convert("RGBA")
    require(art.size == (16, 16), "texture must be 16x16")
    require(any(pixel[3] == 0 for pixel in art.getdata()), "texture must have transparent background")
    require(len(set(art.getdata())) >= 8, "texture must contain readable detail")
require('"resonanzfokus"' in read("tools/make_art_preview.py"), "art preview item missing")

for filename in ("de_de.json", "en_us.json"):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    for key in (
        "item.sporenwerk.resonanzfokus", "tooltip.sporenwerk.resonanzfokus.1",
        "tooltip.sporenwerk.resonanzfokus.2", "message.sporenwerk.resonanzfokus.no_target",
        "message.sporenwerk.resonanzfokus.need_shard", "message.sporenwerk.resonanzfokus.used",
    ):
        require(bool(locale.get(key, "").strip()), filename + " missing " + key)

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.49\.0['\"]", build) is not None,
        "artifact must be version 1.49.0")
readme = read("README.md")
require("Version 1.49.0" in readme and "Version 1.48.0" in readme,
        "release notes must add 1.49.0 and preserve 1.48.0")
require("Aktueller Entwicklungsstand: 1.49.0" in readme, "current version headline is stale")
print("Resonanzfokus target selection, resource spending, recipe, art, locales and version assertions passed.")
