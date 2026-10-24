#!/usr/bin/env python3
"""Regression tests for Kristallpirscher resonance shard progression (1.36.0)."""
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
        raise SystemExit("Kristallpirscher resonance shard regression: " + message)


items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
require("KRISTALLPIRSCHER_RESONANZSPLITTER" in items
        and 'register("kristallpirscher_resonanzsplitter"' in items,
        "resonance shard must be registered as a stackable item")
require("output.accept(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get())" in creative,
        "resonance shard must appear in the creative tab")

loot = json.loads((RES / "data/sporenwerk/loot_tables/entities/kristallpirscher.json").read_text(encoding="utf-8"))
shard_name = "sporenwerk:kristallpirscher_resonanzsplitter"
shard_pools = [
    pool for pool in loot["pools"]
    if any(entry.get("name") == shard_name for entry in pool.get("entries", []))
]
require(len(shard_pools) == 1, "each Kristallpirscher death should have exactly one guaranteed shard pool")
shard_entry = next(entry for entry in shard_pools[0]["entries"] if entry["name"] == shard_name)
count_fn = next((fn for fn in shard_entry.get("functions", []) if fn.get("function") == "minecraft:set_count"), None)
require(count_fn is not None and count_fn["count"] == {"min": 1.0, "max": 3.0},
        "shard drop should yield 1–3 items without a random chance gate")
require(any(any(cond.get("condition") == "minecraft:random_chance" and cond.get("chance") == 0.25
                for cond in pool.get("conditions", []))
            and any(entry.get("name") == "sporenwerk:mutagenkernkristall" for entry in pool["entries"])
            for pool in loot["pools"]),
        "rare Mutagen core crystal drop should remain at 25 percent")

model = json.loads((ASSETS / "models/item/kristallpirscher_resonanzsplitter.json").read_text(encoding="utf-8"))
require(model["parent"] == "minecraft:item/generated"
        and model["textures"]["layer0"] == "sporenwerk:item/kristallpirscher_resonanzsplitter",
        "item model must point to its dedicated texture")
with Image.open(ASSETS / "textures/item/kristallpirscher_resonanzsplitter.png") as source:
    texture = source.convert("RGBA")
require(texture.size == (16, 16), "resonance shard icon must be 16×16")
require(any(px[3] == 0 for px in texture.getdata()), "item icon should keep a transparent background")
require(len(set(texture.getdata())) >= 8, "shard icon must have readable pixel-art colors")
require("kristallpirscher_resonanzsplitter" in read("tools/make_art_preview.py"),
        "art QA preview must include the new item")

recipe = json.loads((RES / "data/sporenwerk/recipes/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(recipe["result"]["item"] == "sporenwerk:mutagen_resonanzdaempfer",
        "recipe must still produce the dampener")
ingredients = {entry["item"] for entry in recipe["key"].values()}
require({"minecraft:iron_ingot", "minecraft:redstone", "minecraft:amethyst_block",
         "sporenwerk:mutagenkernkristall", shard_name}.issubset(ingredients),
        "dampener must require the shard in addition to the original four ingredients")
require(recipe["pattern"] == ["ISI", "RCA", "ISI"],
        "dampener pattern must place shard tuning plates on both ends")

recipe_adv = json.loads((RES / "data/sporenwerk/advancements/recipes/misc/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require("has_resonance_shard" in recipe_adv["criteria"]
        and ["has_resonance_shard"] in recipe_adv["requirements"],
        "dampener recipe unlock must include the shard")

adv = json.loads((RES / "data/sporenwerk/advancements/monsters/kristallpirscher_resonanzsplitter.json").read_text(encoding="utf-8"))
require(adv["parent"] == "sporenwerk:monsters/kristallpirscher"
        and "recover_resonance_shard" in adv["criteria"]
        and adv["display"]["icon"]["item"] == shard_name,
        "first-recovery research advancement must depend on the Crystal Stalker milestone")

for filename, expected in {
    "de_de.json": ("Kristallpirscher-Resonanzsplitter", "Das Echo zerlegt"),
    "en_us.json": ("Crystal Stalker Resonance Shard", "Echo Recovered")
}.items():
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(any(value in locale.values() for value in expected), filename + " missing shard/research text")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.36\.0['\"]", build) is not None,
        "artifact must be version 1.36.0")
readme = read("README.md")
require("Version 1.36.0" in readme and "Version 1.35.0" in readme,
        "release notes must preserve the previous 1.35.0 dampener-feedback milestone")
print("Kristallpirscher guaranteed shard drop, rare core crystal, dampener recipe chain, advancement, icon, locales and 1.36.0 passed.")
