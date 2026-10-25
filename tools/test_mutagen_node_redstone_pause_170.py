#!/usr/bin/env python3
"""Regression tests for Redstone pause/resume of controlled Mutagen Nodes (1.70.0)."""
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
        raise SystemExit("Mutagen Node Redstone pause 1.70 regression: " + message)


node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
for token in (
    "BlockStateProperties.POWERED",
    "BooleanProperty POWERED",
    "builder.add(POWERED)",
    "this.registerDefaultState(this.stateDefinition.any().setValue(POWERED, false))",
    "public void neighborChanged(",
    "boolean powered = level.hasNeighborSignal(pos)",
    "level.setBlock(pos, updated, 3)",
    "if (!powered) level.scheduleTick(pos, this, 1)",
    "if (powered || state.getValue(POWERED)) return;",
    "if (state.getValue(POWERED) || level.hasNeighborSignal(pos)) return;",
    "MutationNodeData.get(serverLevel).activate(pos)",
    "MutationNodeData.get(level).isActive(pos)",
    "MutationNodeData.get(serverLevel).unregister(pos)",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "ParticleTypes.SMOKE",
    "ParticleTypes.END_ROD",
    "message.sporenwerk.mutation.node_paused",
    "message.sporenwerk.mutation.node_resumed",
):
    require(token in node, "Redstone-controlled node behavior missing: " + token)

require(field.count("level.hasNeighborSignal(origin)") == 2,
        "both fresh infection and existing infected terrain must stop while their source is powered")
require(field.count("MutationNodeData.get(level).isActive(origin)") == 2,
        "both spread paths must preserve the sterile-core source activation gate")
require("if (!insideBounds(origin, pos)" in field and "hasAnchor(level, pos)" in field,
        "bounded spread and healing-anchor protection must remain in place")

blockstate = json.loads((ASSETS / "blockstates/infektionsherd.json").read_text(encoding="utf-8"))
require(blockstate["variants"].get("powered=false", {}).get("model") == "sporenwerk:block/infektionsherd",
        "unpowered blockstate must preserve the normal node model")
require(blockstate["variants"].get("powered=true", {}).get("model") == "sporenwerk:block/infektionsherd_paused",
        "powered blockstate must use the unmistakable paused model")
model = json.loads((ASSETS / "models/block/infektionsherd_paused.json").read_text(encoding="utf-8"))
require(model.get("parent") == "minecraft:block/cube_all"
        and model.get("textures", {}).get("all") == "sporenwerk:block/infektionsherd_paused",
        "paused model texture reference is invalid")

with Image.open(ASSETS / "textures/block/infektionsherd_paused.png") as source:
    paused = source.convert("RGBA")
with Image.open(ASSETS / "textures/block/infektionsherd.png") as source:
    active = source.convert("RGBA")
require(paused.size == (16, 16) and active.size == (16, 16),
        "active and paused node textures must both be 16x16")
require(all(p[3] == 255 for p in paused.getdata()),
        "paused world texture must be opaque")
difference = sum(1 for a, b in zip(paused.getdata(), active.getdata()) if a[:3] != b[:3]) / 256.0
require(difference >= 0.55, f"active and paused textures are too similar ({difference:.0%} pixels differ)")
red_signature = sum(1 for r, g, b, a in paused.getdata() if r > 120 and r > g * 1.55 and r > b * 1.25)
require(red_signature >= 8, "paused texture must visibly signal a redstone lock")
preview = read("tools/make_art_preview.py")
require("infektionsherd_paused" in preview, "visual QA sheet is missing the paused node texture")

for filename, tooltip_key, paused_key, resumed_key in (
    ("de_de.json", "Beschleunigt Sporenwerk-Pflanzen", "Mutagenherd pausiert", "Mutagenherd wieder aktiv"),
    ("en_us.json", "Accelerates Sporenwerk crops", "Mutagen Node paused", "Mutagen Node resumed"),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    tooltip = locale.get("tooltip.sporenwerk.infektionsherd", "")
    require(tooltip_key in tooltip and "Redstone" in tooltip,
            filename + " is missing Redstone instructions in the node tooltip")
    require(paused_key in locale.get("message.sporenwerk.mutation.node_paused", ""),
            filename + " is missing pause confirmation")
    require(resumed_key in locale.get("message.sporenwerk.mutation.node_resumed", ""),
            filename + " is missing resume confirmation")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.70\.0['\"]", build) is not None,
        "artifact must be version 1.70.0")
readme = read("README.md")
require("Version 1.70.0" in readme and "Version 1.69.0" in readme
        and "Aktueller Entwicklungsstand: 1.70.0" in readme,
        "release notes must describe 1.70.0 and preserve 1.69.0")
print("1.70 Redstone pause, reactivation, source-bound spread gating, blockstate, pixel-art contrast and DE/EN feedback passed.")
