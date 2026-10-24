#!/usr/bin/env python3
"""Regression tests for the tiered redstone-driven Mutagen warning siren."""
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
    'IntegerProperty.create("signal", 0, 15)',
    "registerDefaultState(defaultBlockState().setValue(SIGNAL, 0))",
    "builder.add(SIGNAL)",
    "void neighborChanged(",
    "if (level.isClientSide) return;",
    "int latchedSignal = state.getValue(SIGNAL)",
    "int liveSignal = level.getBestNeighborSignal(pos)",
    "if (liveSignal <= latchedSignal) return;",
    "level.setBlock(pos, state.setValue(SIGNAL, liveSignal), 3)",
    "int previousBand = riskBand(latchedSignal)",
    "int nextBand = riskBand(liveSignal)",
    "if (nextBand > previousBand)",
    "InteractionResult use(",
    'Component.translatable("message.sporenwerk.warnsirene.acknowledged", liveSignal)',
    "public static int riskBand(int signal)",
    "if (signal >= 11) return 3",
    "if (signal >= 5) return 2",
    "return signal > 0 ? 1 : 0",
    "SoundEvents.NOTE_BLOCK_BELL.value()",
    "SoundSource.BLOCKS",
    "case 3 -> 0.55F",
    "case 2 -> 0.82F",
    "default -> 1.18F",
):
    require(token in siren, "missing severity/edge behavior: " + token)
require(siren.count("level.playSound(") == 1,
        "a single sound call should be guarded by severity escalation")

states = json.loads((ASSETS / "blockstates/mutagen_warnsirene.json").read_text(encoding="utf-8"))
require(len(states["variants"]) == 16, "all 16 comparator values need a blockstate")
for signal in range(16):
    expected = (
        "sporenwerk:block/mutagen_warnsirene" if signal == 0 else
        "sporenwerk:block/mutagen_warnsirene_active" if signal <= 4 else
        "sporenwerk:block/mutagen_warnsirene_elevated" if signal <= 10 else
        "sporenwerk:block/mutagen_warnsirene_critical"
    )
    actual = states["variants"].get(f"signal={signal}", {}).get("model")
    require(actual == expected, f"signal {signal} maps to {actual}, expected {expected}")

names = (
    "mutagen_warnsirene",
    "mutagen_warnsirene_active",
    "mutagen_warnsirene_elevated",
    "mutagen_warnsirene_critical",
)
images = []
for name in names:
    model = json.loads((ASSETS / f"models/block/{name}.json").read_text(encoding="utf-8"))
    require(model["parent"] == "minecraft:block/cube_all"
            and model["textures"]["all"] == f"sporenwerk:block/{name}",
            name + " model must point to its own full-cube texture")
    with Image.open(ASSETS / f"textures/block/{name}.png") as source:
        image = source.convert("RGBA")
    require(image.size == (16, 16), name + " must be 16x16")
    require(all(px[3] == 255 for px in image.getdata()), name + " must be fully opaque")
    require(len(set(image.getdata())) >= 8, name + " must have readable pixel detail")
    images.append(image)

for left in range(len(images)):
    for right in range(left + 1, len(images)):
        a, b = list(images[left].getdata()), list(images[right].getdata())
        difference = sum(x[:3] != y[:3] for x, y in zip(a, b))
        require(difference >= 10, f"{names[left]} and {names[right]} look too similar")

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
        "recipe discovery advancement must require all three ingredients")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    require(data.get("block.sporenwerk.mutagen_warnsirene", "").strip(), locale + " block name missing")
    require(data.get("item.sporenwerk.mutagen_warnsirene", "").strip(), locale + " item name missing")
    require(data.get("message.sporenwerk.warnsirene.acknowledged", "").strip(),
            locale + " acknowledgement message missing")

preview = read("tools/make_art_preview.py")
for name in ("mutagen_warnsirene", "mutagen_warnsirene_active",
             "mutagen_warnsirene_elevated", "mutagen_warnsirene_critical"):
    require(name in preview, "art preview missing " + name)
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.33\.0['\"]", build) is not None,
        "artifact must be version 1.33.0")
readme = read("README.md")
require("Version 1.33.0" in readme and "Version 1.32.0" in readme,
        "release notes must preserve the 1.32.0 version history")
print("Mutagen warning siren registration, all 16 input values, severity bands, escalation tones, textures, recipe, locales, and version passed.")
