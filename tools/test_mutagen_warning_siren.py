#!/usr/bin/env python3
"""Regression tests for the redstone-driven Mutagen warning siren."""
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
        raise SystemExit("Mutagen warning siren regression: " + message)


blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
siren = read("src/main/java/de/sporenwerk/block/MutagenWarningSirenBlock.java")
for token in (
    "MUTAGEN_WARNSIRENE",
    'register("mutagen_warnsirene"',
    'ModItems.ITEMS.register("mutagen_warnsirene"',
    "MutagenWarningSirenBlock",
):
    require(token in blocks, "block/item registration missing " + token)
require("output.accept(ModBlocks.MUTAGEN_WARNSIRENE.get())" in creative,
        "warning siren must appear in the creative tab")

for token in (
    'BooleanProperty.create("powered")',
    "registerDefaultState(defaultBlockState().setValue(POWERED, false))",
    "builder.add(POWERED)",
    "void neighborChanged(",
    "if (level.isClientSide) return;",
    "boolean inputPowered = level.hasNeighborSignal(pos)",
    "boolean wasPowered = state.getValue(POWERED)",
    "if (inputPowered == wasPowered) return;",
    "level.setBlock(pos, state.setValue(POWERED, inputPowered), 3)",
    "if (inputPowered)",
    "SoundEvents.NOTE_BLOCK_BELL",
    "SoundSource.BLOCKS",
):
    require(token in siren, "missing edge-triggered siren behavior: " + token)
require(siren.count("level.playSound(") == 1,
        "one bell sound call is sufficient; avoid repetitive alarm loops")

states = json.loads((ASSETS / "blockstates/mutagen_warnsirene.json").read_text(encoding="utf-8"))
require(states["variants"]["powered=false"]["model"] == "sporenwerk:block/mutagen_warnsirene",
        "idle state must use its own model")
require(states["variants"]["powered=true"]["model"] == "sporenwerk:block/mutagen_warnsirene_active",
        "powered state must use its active model")
for name in ("mutagen_warnsirene", "mutagen_warnsirene_active"):
    model = json.loads((ASSETS / f"models/block/{name}.json").read_text(encoding="utf-8"))
    require(model["parent"] == "minecraft:block/cube_all"
            and model["textures"]["all"] == f"sporenwerk:block/{name}",
            name + " model points to the correct opaque texture")
    with Image.open(ASSETS / f"textures/block/{name}.png") as source:
        image = source.convert("RGBA")
    require(image.size == (16, 16), name + " must be 16x16")
    require(all(px[3] == 255 for px in image.getdata()), name + " must be fully opaque")
    require(len(set(image.getdata())) >= 8, name + " must have readable pixel details")

with Image.open(ASSETS / "textures/block/mutagen_warnsirene.png") as im:
    idle = list(im.convert("RGBA").getdata())
with Image.open(ASSETS / "textures/block/mutagen_warnsirene_active.png") as im:
    active = list(im.convert("RGBA").getdata())
require(sum(a[:3] != b[:3] for a, b in zip(idle, active)) >= 12,
        "active and idle siren art must be visibly distinct")

recipe = json.loads((RES / "data/sporenwerk/recipes/mutagen_warnsirene.json").read_text(encoding="utf-8"))
require(recipe["result"]["item"] == "sporenwerk:mutagen_warnsirene",
        "recipe output must be the warning siren")
ingredients = {entry["item"] for entry in recipe["key"].values()}
require({"minecraft:copper_ingot", "minecraft:redstone", "minecraft:note_block"}.issubset(ingredients),
        "recipe must use copper, redstone, and a note block")
advancement = json.loads((RES / "data/sporenwerk/advancements/recipes/misc/mutagen_warnsirene.json").read_text(encoding="utf-8"))
require(advancement["parent"] == "minecraft:recipes/root"
        and advancement["rewards"]["recipes"] == ["sporenwerk:mutagen_warnsirene"]
        and len(advancement["requirements"]) == 3,
        "recipe discovery advancement must unlock after all three ingredients are held")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    require(data.get("block.sporenwerk.mutagen_warnsirene", "").strip(), locale + " block name missing")
    require(data.get("item.sporenwerk.mutagen_warnsirene", "").strip(), locale + " item name missing")

preview = read("tools/make_art_preview.py")
require("mutagen_warnsirene" in preview and "mutagen_warnsirene_active" in preview,
        "art preview must show both siren states")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.29\.0['\"]", build) is not None,
        "artifact must be version 1.29.0")
readme = read("README.md")
require("Version 1.29.0" in readme and "Version 1.28.0" in readme,
        "release notes must preserve the 1.28.0 version history")
print("Mutagen warning siren registration, redstone edge behavior, sound, textures, recipe, locales, and version passed.")
