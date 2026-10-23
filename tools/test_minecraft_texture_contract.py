#!/usr/bin/env python3
"""Regression tests for Minecraft model references, opaque block faces, and cutout crops."""
from pathlib import Path
import json
import sys
from PIL import Image

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
assets = root / "src/main/resources/assets/sporenwerk"
textures = assets / "textures"
def require(condition, message):
    if not condition:
        raise SystemExit("Minecraft texture contract: " + message)

# Every blockstate must point to an actual model JSON.
for path in (assets / "blockstates").glob("*.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    for variant, state in data.get("variants", {}).items():
        values = state if isinstance(state, list) else [state]
        for value in values:
            model = value.get("model")
            if model and model.startswith("sporenwerk:"):
                model_path = assets / "models" / (model.split(":", 1)[1] + ".json")
                require(model_path.is_file(), f"{path.name}:{variant} points to missing model {model_path.name}")

# Resolve every mod-owned texture in every model, including crop sprites and block face variants.
for path in (assets / "models").rglob("*.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, texture in data.get("textures", {}).items():
        if isinstance(texture, str) and texture.startswith("sporenwerk:"):
            texture_path = textures / (texture.split(":", 1)[1] + ".png")
            require(texture_path.is_file(), f"{path.relative_to(assets)} references missing texture {texture_path.relative_to(textures)}")

# Cube/industrial faces must be complete opaque Minecraft tiles, not transparent item icons.
solid_faces = []
for name in ("infektionsherd", "mutagen_boden", "mutationsanker", "sporenresistenter_block"):
    for face in ("top", "side", "bottom"):
        solid_faces.append(f"{name}_{face}")
for name in ("feldsammler", "saatgutpresse", "biomasse_bioreaktor"):
    for face in ("", "_panel", "_side", "_back", "_top", "_bottom"):
        solid_faces.append(name + face)
for name in solid_faces:
    path = textures / "block" / (name + ".png")
    require(path.is_file(), f"missing solid world-face texture {name}.png")
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        require(rgba.size == (16, 16), f"{name}.png must be exactly 16x16, got {rgba.size}")
        require(all(pixel[3] == 255 for pixel in rgba.getdata()),
                f"{name}.png uses transparent pixels on a solid block face")

# Plant textures intentionally use alpha, therefore all four custom crops must use cutout rendering.
client = (root / "src/main/java/de/sporenwerk/client/ClientModEvents.java").read_text(encoding="utf-8")
require("ItemBlockRenderTypes.setRenderLayer" in client and "RenderType.cutout()" in client,
        "custom plants need Forge cutout render layers or transparent pixels render incorrectly")
for name in ("faserrohr", "bernsteinkappe", "rotwurzel", "filtermoos"):
    for stage in range(3):
        path = textures / "block" / f"{name}_stage{stage}.png"
        require(path.is_file(), f"missing crop stage {path.name}")
        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            require(rgba.size == (16, 16), f"{path.name} must be 16x16")
            require(any(pixel[3] == 0 for pixel in rgba.getdata()),
                    f"{path.name} should preserve its transparent background for cutout rendering")
require("ModBlocks.FASERROHR.get(), RenderType.cutout()" in client
        and "ModBlocks.BERNSTEINKAPPE.get(), RenderType.cutout()" in client
        and "ModBlocks.ROTWURZEL.get(), RenderType.cutout()" in client
        and "ModBlocks.FILTERMOOS.get(), RenderType.cutout()" in client,
        "each of the four custom crops must be registered for cutout rendering")
print("Minecraft block-face opacity, texture/model references, and crop cutout rendering passed.")
