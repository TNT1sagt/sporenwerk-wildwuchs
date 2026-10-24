#!/usr/bin/env python3
"""Regression tests for visually distinct Mutagen field tiers."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen field contrast regression: " + message)


build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.27\.0['\"]", build) is not None,
        "the release must be version 1.27.0")

blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
for token in (
    ".lightLevel(state -> switch (state.getValue(de.sporenwerk.block.InfestedTerrainBlock.MUTAGEN_LEVEL))",
    "case 1 -> 5",
    "case 2 -> 9",
    "case 3 -> 13",
    "default -> 0",
):
    require(token in blocks, "field-tier lighting missing " + token)

terrain = read("src/main/java/de/sporenwerk/block/InfestedTerrainBlock.java")
for token in (
    "IntegerProperty MUTAGEN_LEVEL",
    "IntegerProperty.create(\"mutagen_level\", 0, 3)",
    "MutationField.mutagenStrengthAt(level, pos)",
    "state.setValue(MUTAGEN_LEVEL, strength)",
):
    require(token in terrain, "server-synchronized field tier missing " + token)

state_data = json.loads((ASSETS / "blockstates/mutagen_boden.json").read_text(encoding="utf-8"))
for tier in range(4):
    expected = ("sporenwerk:block/mutagen_boden" if tier == 0
                else f"sporenwerk:block/mutagen_boden_strength{tier}")
    require(state_data["variants"].get(f"mutagen_level={tier}", {}).get("model") == expected,
            f"strength {tier} does not point to its intended model")

images = []
for tier in range(1, 4):
    model = json.loads((ASSETS / f"models/block/mutagen_boden_strength{tier}.json").read_text(encoding="utf-8"))
    require(model["parent"] == "minecraft:block/cube_all"
            and model["textures"]["all"] == f"sporenwerk:block/mutagen_boden_strength{tier}",
            f"tier {tier} model texture mapping is incorrect")
    with Image.open(ASSETS / f"textures/block/mutagen_boden_strength{tier}.png") as source:
        image = source.convert("RGBA")
    require(image.size == (16, 16), f"tier {tier} texture must be 16x16")
    require(all(pixel[3] == 255 for pixel in image.getdata()), f"tier {tier} texture must be fully opaque")
    require(len(set(image.getdata())) >= 10, f"tier {tier} texture must contain real pixel-art detail")
    images.append(image)

for left in range(3):
    for right in range(left + 1, 3):
        a = list(images[left].getdata())
        b = list(images[right].getdata())
        difference = sum(1 for x, y in zip(a, b) if x[:3] != y[:3]) / 256.0
        require(difference >= 0.65,
                f"tiers {left + 1} and {right + 1} are too visually similar ({difference:.0%} different pixels)")

green_signature = sum(1 for r, g, b, _ in images[0].getdata() if g > r * 1.30 and g > b * 1.05 and g > 75)
hot_signature = sum(1 for r, g, b, _ in images[1].getdata()
                    if (r > 150 and b > 125 and g < 165) or (r > 185 and 70 < g < 180 and b < 130))
crystal_signature = sum(1 for r, g, b, _ in images[2].getdata()
                        if g > r * 1.20 and b > r * 1.40 and g > 110 and b > 130)
bright_cores = sum(1 for r, g, b, _ in images[2].getdata() if r + g + b > 630)
require(green_signature >= 8, "tier I needs an unmistakable acid-green mycelium signature")
require(hot_signature >= 8, "tier II needs clearly visible magenta/orange fracture colors")
require(crystal_signature >= 8 and bright_cores >= 2,
        "tier III needs cyan crystal edges and near-white cores")

visual = read("src/main/java/de/sporenwerk/client/MutagenFieldVisuals.java")
for token in (
    "import de.sporenwerk.block.InfestedTerrainBlock;",
    "int fieldTier = state.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL)",
    "float sporeChance",
    "fieldTier >= 2",
    "fieldTier >= 3",
    "ParticleTypes.WARPED_SPORE",
    "ParticleTypes.SOUL_FIRE_FLAME",
    "ParticleTypes.PORTAL",
    "ParticleTypes.END_ROD",
    "int particleBudget = 24",
    "particleBudget--",
):
    require(token in visual, "tier-aware field visuals missing " + token)

preview = read("tools/make_art_preview.py")
for tier in range(1, 4):
    require(f"mutagen_boden_strength{tier}" in preview,
            f"art QA preview is missing Mutagen field tier {tier}")
readme = read("README.md")
require("Version 1.27.0" in readme and "Version 1.26.0" in readme,
        "new release notes must preserve the 1.26.0 history")
print("Distinct Mutagen field textures, lighting, particles, model mapping, preview, and release history passed.")
