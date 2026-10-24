#!/usr/bin/env python3
"""Test redstone activation, active visuals, and powered-only pulse suppression."""
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
        raise SystemExit("Powered resonance dampener regression: " + message)


dampener = read("src/main/java/de/sporenwerk/block/MutagenResonanceDampenerBlock.java")
blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
entity = read("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")
for token in (
    'BooleanProperty.create("powered")',
    "registerDefaultState(defaultBlockState().setValue(POWERED, false))",
    "builder.add(POWERED)",
    "void neighborChanged(",
    "boolean powered = level.hasNeighborSignal(pos)",
    "state.setValue(POWERED, powered)",
    "if (level.isClientSide) return;",
):
    require(token in dampener, "missing redstone block state: " + token)
require("state.getValue(MutagenResonanceDampenerBlock.POWERED) ? 10 : 0" in blocks,
        "light must be conditional on the powered state")
require("dampenerState.getValue(MutagenResonanceDampenerBlock.POWERED)" in entity,
        "only powered dampeners may suppress the resonance pulse")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "powered-state lookup must remain chunk-safe")

states = json.loads((ASSETS / "blockstates/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(states["variants"]["powered=false"]["model"] == "sporenwerk:block/mutagen_resonanzdaempfer"
        and states["variants"]["powered=true"]["model"] == "sporenwerk:block/mutagen_resonanzdaempfer_active",
        "blockstate must map both powered values to distinct models")
for name, top, side in (
    ("mutagen_resonanzdaempfer", "mutagen_resonanzdaempfer_top", "mutagen_resonanzdaempfer_side"),
    ("mutagen_resonanzdaempfer_active", "mutagen_resonanzdaempfer_top_active", "mutagen_resonanzdaempfer_side_active"),
):
    model = json.loads((ASSETS / f"models/block/{name}.json").read_text(encoding="utf-8"))
    require(model["parent"] == "minecraft:block/cube_column"
            and model["textures"]["end"] == "sporenwerk:block/" + top
            and model["textures"]["side"] == "sporenwerk:block/" + side,
            name + " model must reference its matching top/side art")

for texture in (
    "mutagen_resonanzdaempfer_top",
    "mutagen_resonanzdaempfer_side",
    "mutagen_resonanzdaempfer_top_active",
    "mutagen_resonanzdaempfer_side_active",
):
    with Image.open(ASSETS / f"textures/block/{texture}.png") as src:
        image = src.convert("RGBA")
    require(image.size == (16, 16) and all(px[3] == 255 for px in image.getdata()),
            texture + " must be an opaque 16x16 texture")

preview = read("tools/make_art_preview.py")
require("mutagen_resonanzdaempfer_top_active" in preview
        and "mutagen_resonanzdaempfer_side_active" in preview,
        "art preview must show active dampener faces")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.36\.0['\"]", build) is not None,
        "artifact must be version 1.36.0")
readme = read("README.md")
require("Version 1.36.0" in readme and "Version 1.35.0" in readme,
        "release notes must preserve 1.35.0 history")
print("Powered resonance dampener state, conditional light, active-only suppression, models, textures and version passed.")
