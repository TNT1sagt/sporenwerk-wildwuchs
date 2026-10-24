#!/usr/bin/env python3
"""Regression tests for finite Resonance Dampener charge and comparator output (1.38.0)."""
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
        raise SystemExit("Resonance Dampener charge regression: " + message)


block = read("src/main/java/de/sporenwerk/block/MutagenResonanceDampenerBlock.java")
entity = read("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")
for token in (
    "public static final int MAX_CHARGE = 3;",
    'IntegerProperty CHARGE = IntegerProperty.create("charge", 0, MAX_CHARGE)',
    "registerDefaultState(defaultBlockState().setValue(CHARGE, 0))",
    "builder.add(CHARGE)",
    "public boolean hasAnalogOutputSignal(BlockState state)",
    "return state.getValue(CHARGE) * 5;",
    "ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get()",
    "if (!player.getAbilities().instabuild)",
    "held.shrink(1)",
    "level.setBlock(pos, state.setValue(CHARGE, MAX_CHARGE), 3)",
    "revealProtectionVolume(serverLevel, pos)",
):
    require(token in block, "block must implement charge/recharge/comparator behavior: " + token)

for token in (
    "int charge = dampenerState.getValue(MutagenResonanceDampenerBlock.CHARGE)",
    "if (charge <= 0) continue;",
    "dampenerState.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1)",
    "level().setBlock(pos, dampenerState.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1), 3)",
    "if (!level().hasChunkAt(pos)) continue;",
    "resonanceCooldown = RESONANCE_COOLDOWN_TICKS;",
):
    require(token in entity, "entity must consume one loaded, available charge per blocked pulse: " + token)
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "charge scan must not force-load chunks")

states = json.loads((ASSETS / "blockstates/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))["variants"]
require(set(states) == {f"charge={charge}" for charge in range(4)},
        "blockstate must define each charge stage 0–3")
for charge in range(4):
    model_name = "mutagen_resonanzdaempfer" if charge == 0 else f"mutagen_resonanzdaempfer_charge{charge}"
    top_name = "mutagen_resonanzdaempfer_top" if charge == 0 else f"mutagen_resonanzdaempfer_charge{charge}"
    require(states[f"charge={charge}"]["model"] == f"sporenwerk:block/{model_name}",
            f"charge {charge} must point to its visual model")
    model = json.loads((ASSETS / f"models/block/{model_name}.json").read_text(encoding="utf-8"))
    require(model["textures"]["end"] == f"sporenwerk:block/{top_name}"
            and model["textures"]["side"] == "sporenwerk:block/mutagen_resonanzdaempfer_side",
            f"charge {charge} model must use its own top and common side texture")
    with Image.open(ASSETS / f"textures/block/{top_name}.png") as source:
        image = source.convert("RGBA")
    require(image.size == (16, 16) and all(px[3] == 255 for px in image.getdata()),
            f"charge {charge} texture must be an opaque 16×16 block face")
    require(len(set(image.getdata())) >= 12, f"charge {charge} texture must remain readable")
texture_bytes = []
for charge in range(4):
    top_name = "mutagen_resonanzdaempfer_top" if charge == 0 else f"mutagen_resonanzdaempfer_charge{charge}"
    texture_bytes.append((ASSETS / "textures" / "block" / f"{top_name}.png").read_bytes())
require(len(set(texture_bytes)) == 4,
        "all four charge tops must be visually distinct files")

item_model = json.loads((ASSETS / "models/item/mutagen_resonanzdaempfer.json").read_text(encoding="utf-8"))
require(item_model["parent"] == "sporenwerk:block/mutagen_resonanzdaempfer",
        "placed item model must use the uncharged state")
preview = read("tools/make_art_preview.py")
for token in ("mutagen_resonanzdaempfer_charge1", "mutagen_resonanzdaempfer_charge2", "mutagen_resonanzdaempfer_charge3"):
    require(token in preview, "visual QA sheet must include " + token)

for filename, keys in {
    "de_de.json": (
        "Ladung %s/%s Impulse",
        "Resonanzdämpfer aufgeladen",
        "der Splitter bleibt erhalten"
    ),
    "en_us.json": (
        "Charge %s/%s pulses",
        "Resonance Dampener recharged",
        "the shard was not consumed"
    ),
}.items():
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    for snippet in keys:
        require(any(snippet in value for value in locale.values()),
                f"{filename} missing charge/recharge text: {snippet}")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.38\.0['\"]", build) is not None,
        "artifact must be version 1.38.0")
readme = read("README.md")
require("Version 1.38.0" in readme and "Version 1.37.0" in readme,
        "release notes must preserve the previous protection-volume release")
print("Finite charge, shard refilling, comparator output, 0–3 blockstates, visuals, chunk safety, locales and 1.38.0 passed.")
