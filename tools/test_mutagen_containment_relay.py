#!/usr/bin/env python3
"""Regression coverage for the 1.43.0 Mutagen Containment Relay."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"
SRC = ROOT / "src/main/java/de/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen Containment Relay regression: " + message)


blocks = (SRC / "registry/ModBlocks.java").read_text(encoding="utf-8")
creative = (SRC / "registry/ModCreativeTabs.java").read_text(encoding="utf-8")
relay = (SRC / "block/MutagenContainmentRelayBlock.java").read_text(encoding="utf-8")
for token in (
    'MUTAGEN_CONTAINMENT_RELAY = BLOCKS.register("mutagen_containment_relay"',
    'ModItems.ITEMS.register("mutagen_containment_relay"',
):
    require(token in blocks, "block/item registration missing: " + token)
require("output.accept(ModBlocks.MUTAGEN_CONTAINMENT_RELAY.get())" in creative,
        "relay missing from the Sporenwerk creative tab")
for token in (
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 3)',
    'IntegerProperty SIGNAL = IntegerProperty.create("signal", 0, 15)',
    "public boolean hasAnalogOutputSignal(BlockState state)",
    "return state.getValue(SIGNAL);",
    "int mode = (state.getValue(MODE) + step) % 4;",
    "player.isShiftKeyDown() ? 3 : 1",
    "case 1 -> {",
    "case 2 -> Math.min(15, counterpulses * 5)",
    "case 3 -> {",
    "stationSignal >= 11 && (poweredWards == 0 || counterpulses == 0)",
    "MutagenWarningSirenBlock.riskBand(stored) == 3",
    "private static boolean isRelevantInput(Block block)",
    "if (!level.hasChunkAt(new BlockPos(x, center.getY(), z))) continue;",
    "HORIZONTAL_SCAN_RADIUS = 16",
    "VERTICAL_SCAN_RADIUS = 8",
):
    require(token in relay, "relay contract missing: " + token)
require("getChunk(" not in relay and "getChunkNow(" not in relay,
        "relay must not force-load chunks")
require("BlockEntity" not in relay and "onLoad()" not in relay,
        "relay must remain ticker-free")

state = json.loads((ASSETS / "blockstates/mutagen_containment_relay.json").read_text(encoding="utf-8"))
variants = state.get("variants", {})
require(len(variants) == 64, "expected all 4 MODE × 16 SIGNAL blockstates")
for mode in range(4):
    for signal in range(16):
        key = f"mode={mode},signal={signal}"
        require(variants.get(key, {}).get("model") == "sporenwerk:block/mutagen_containment_relay",
                "missing or incorrect model variant " + key)
model = json.loads((ASSETS / "models/block/mutagen_containment_relay.json").read_text(encoding="utf-8"))
require(model.get("parent") == "minecraft:block/cube_column"
        and model["textures"]["end"] == "sporenwerk:block/mutagen_containment_relay_top"
        and model["textures"]["side"] == "sporenwerk:block/mutagen_containment_relay_side",
        "relay model must use the custom cube-column textures")
item = json.loads((ASSETS / "models/item/mutagen_containment_relay.json").read_text(encoding="utf-8"))
require(item.get("parent") == "sporenwerk:block/mutagen_containment_relay", "item model missing")
for name in ("mutagen_containment_relay_top", "mutagen_containment_relay_side"):
    with Image.open(ASSETS / f"textures/block/{name}.png") as image:
        rgba = image.convert("RGBA")
        require(rgba.size == (16, 16), name + " must be 16x16")
        require(all(pixel[3] == 255 for pixel in rgba.getdata()), name + " must be opaque")
        require(len(set(rgba.getdata())) >= 12, name + " lacks readable contrast")
recipe = json.loads((RES / "data/sporenwerk/recipes/mutagen_containment_relay.json").read_text(encoding="utf-8"))
require(recipe["result"]["item"] == "sporenwerk:mutagen_containment_relay", "recipe result is incorrect")
ingredients = {entry["item"] for entry in recipe["key"].values()}
require({"minecraft:copper_ingot", "minecraft:redstone", "minecraft:quartz",
         "sporenwerk:mutagenkernkristall"}.issubset(ingredients), "recipe must use containment engineering resources")
loot = json.loads((RES / "data/sporenwerk/loot_tables/blocks/mutagen_containment_relay.json").read_text(encoding="utf-8"))
require(any(entry.get("name") == "sporenwerk:mutagen_containment_relay"
            for pool in loot["pools"] for entry in pool["entries"]), "relay must drop itself")
advancement = json.loads((RES / "data/sporenwerk/advancements/recipes/misc/mutagen_containment_relay.json").read_text(encoding="utf-8"))
require(advancement["rewards"]["recipes"] == ["sporenwerk:mutagen_containment_relay"],
        "recipe advancement must unlock the relay")
preview = (ROOT / "tools/make_art_preview.py").read_text(encoding="utf-8")
require("mutagen_containment_relay_top" in preview and "mutagen_containment_relay_side" in preview,
        "both relay faces must appear in visual QA")
for locale_name in ("de_de.json", "en_us.json"):
    locale = json.loads((ASSETS / "lang" / locale_name).read_text(encoding="utf-8"))
    for key in (
        "block.sporenwerk.mutagen_containment_relay",
        "item.sporenwerk.mutagen_containment_relay",
        "message.sporenwerk.containment_relay.mode_overall",
        "message.sporenwerk.containment_relay.mode_alarm",
        "message.sporenwerk.containment_relay.mode_reserve",
        "message.sporenwerk.containment_relay.mode_gap",
        "message.sporenwerk.containment_relay.status",
    ):
        require(bool(locale.get(key, "").strip()), locale_name + " missing " + key)

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.43\.0['\"]", build) is not None,
        "artifact must be version 1.43.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.43.0" in readme and "Version 1.42.0" in readme,
        "release notes must add 1.43.0 and preserve 1.42.0 history")
require("Aktueller Entwicklungsstand: 1.43.0" in readme,
        "active README release headline missing")
print("Containment Relay modes, comparator output, 64 blockstates, assets, recipe, chunk-safety, DE/EN locales and version 1.43.0 passed.")
