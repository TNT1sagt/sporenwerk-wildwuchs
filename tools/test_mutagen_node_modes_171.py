#!/usr/bin/env python3
"""Regression tests for the three Mutagen Node operating modes (1.71.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen Node modes 1.71 regression: " + message)


node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
for token in (
    'IntegerProperty.create("mode", 0, 2)',
    'setValue(POWERED, false).setValue(MODE, 0)',
    'builder.add(POWERED, MODE)',
    'public InteractionResult use(',
    'int nextMode = (state.getValue(MODE) + 1) % 3',
    'case 1 -> "message.sporenwerk.mutation.node_cultivation"',
    'case 2 -> "message.sporenwerk.mutation.node_dormant"',
    'MutationField.cultivateNearbyCrops(level, pos, random)',
    'MutationField.spreadFromNode(level, pos, random)',
    'MutagenBloom.tryTrigger(level, pos, random)',
    'if (mode == 1)',
    'else if (mode == 1)',
    'if (state.getValue(POWERED) || level.hasNeighborSignal(pos)',
    'MutationNodeData.get(serverLevel).activate(pos)',
    'MutationNodeData.get(serverLevel).unregister(pos)',
):
    require(token in node, "missing operating-mode contract: " + token)

require("public static void cultivateNearbyCrops(" in field,
        "cultivation-only helper is missing")
cultivation = field[field.index("public static void cultivateNearbyCrops("):
                   field.index("public static void spreadFromNode(")]
for token in ("empowerNearbyCrops(level, origin, random, 6)",
              "hasAnchor(level, origin)", "level.hasNeighborSignal(origin)"):
    require(token in cultivation, "cultivation mode must remain contained: " + token)

node_guard = 'level.getBlockState(origin).getValue(MutationNodeBlock.MODE) != 0'
require(field.count(node_guard) == 2,
        "both source-origin and already-contaminated terrain paths must require spread mode")
require(field.count("level.hasNeighborSignal(origin)") >= 3,
        "Redstone must still suppress both spread paths")

blockstate = json.loads((ASSETS / "blockstates/infektionsherd.json").read_text(encoding="utf-8"))
variants = blockstate["variants"]
require(len(variants) == 6, "all three modes need powered and unpowered blockstate variants")
for mode, model in (
    (0, "sporenwerk:block/infektionsherd"),
    (1, "sporenwerk:block/infektionsherd_cultivation"),
    (2, "sporenwerk:block/infektionsherd_dormant"),
):
    require(variants.get(f"mode={mode},powered=false", {}).get("model") == model,
            f"mode {mode} must use its own unpowered model")
    require(variants.get(f"mode={mode},powered=true", {}).get("model")
            == "sporenwerk:block/infektionsherd_paused",
            f"Redstone must visually override mode {mode}")

for name in ("infektionsherd.png", "infektionsherd_cultivation.png",
             "infektionsherd_dormant.png", "infektionsherd_paused.png"):
    with Image.open(ASSETS / "textures/block" / name) as source:
        image = source.convert("RGBA")
    require(image.size == (16, 16), name + " must be proper 16x16 Minecraft pixel art")
    require(all(px[3] == 255 for px in image.getdata()), name + " must be opaque")
    require(len(set(image.getdata())) >= 8, name + " lacks visible pixel detail")

for left, right in (
    ("infektionsherd.png", "infektionsherd_cultivation.png"),
    ("infektionsherd_cultivation.png", "infektionsherd_dormant.png"),
    ("infektionsherd_dormant.png", "infektionsherd_paused.png"),
):
    with Image.open(ASSETS / "textures/block" / left) as f:
        a = f.convert("RGBA")
    with Image.open(ASSETS / "textures/block" / right) as f:
        b = f.convert("RGBA")
    difference = sum(1 for x, y in zip(a.getdata(), b.getdata())
                     if x[:3] != y[:3]) / 256.0
    require(difference >= 0.35, f"{left} and {right} look too similar ({difference:.0%})")

preview = read("tools/make_art_preview.py")
for name in ("infektionsherd_cultivation", "infektionsherd_dormant", "infektionsherd_paused"):
    require(name in preview, "visual QA sheet omits " + name)

for filename, expected in (
    ("de_de.json", ("Rechtsklick wechselt den Modus", "Mutagenherd: Kulturmodus", "Mutagenherd: ruhend")),
    ("en_us.json", ("Right-click to cycle modes", "Mutagen Node: cultivation mode", "Mutagen Node: dormant")),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(expected[0] in locale.get("tooltip.sporenwerk.infektionsherd", ""),
            filename + " is missing mode instructions")
    require(expected[1] in locale.get("message.sporenwerk.mutation.node_cultivation", ""),
            filename + " is missing cultivation feedback")
    require(expected[2] in locale.get("message.sporenwerk.mutation.node_dormant", ""),
            filename + " is missing dormant feedback")
    require(locale.get("message.sporenwerk.mutation.node_paused", "").strip(),
            filename + " must preserve Redstone pause feedback")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.71\.0['\"]", build) is not None,
        "artifact must be version 1.71.0")
readme = read("README.md")
require("Version 1.71.0" in readme and "Version 1.70.0" in readme
        and "Aktueller Entwicklungsstand: 1.71.0" in readme,
        "release notes must retain current and previous release")
print("1.71 modes, safe crop-only mode, source-gated terrain spread, Bloom event, six visuals and DE/EN messages passed.")
