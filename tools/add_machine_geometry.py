#!/usr/bin/env python3
"""Build distinct 3D block geometry and pixel-art machine panels for Sporenwerk."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, re, sys

ROOT = Path(sys.argv[1]).resolve()
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"
TEX = ASSETS / "textures/block"

DARK = (16, 24, 21, 255)
FRAME = (32, 45, 39, 255)
STEEL = (63, 83, 73, 255)
HIGHLIGHT = (131, 155, 135, 255)
GOLD = (221, 176, 76, 255)
GREEN = (95, 164, 91, 255)
MINT = (126, 225, 180, 255)
AMBER = (224, 139, 45, 255)
CREAM = (245, 222, 157, 255)
TEAL = (52, 155, 146, 255)
PALE_TEAL = (137, 224, 202, 255)
RED = (177, 62, 64, 255)

def box(draw, coords, fill, outline=None):
    draw.rectangle(coords, fill=fill, outline=outline)

def line(draw, coords, fill, width=1):
    draw.line(coords, fill=fill, width=width, joint="curve")

def save_panel(name, draw_func):
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw_func(ImageDraw.Draw(image))
    TEX.mkdir(parents=True, exist_ok=True)
    image.save(TEX / f"{name}_panel.png", optimize=True)

def collector_panel(d):
    # Bezeled optical panel, crop signal, and paired collector arms.
    box(d, (1, 1, 30, 30), DARK, GOLD)
    box(d, (3, 3, 28, 28), FRAME, HIGHLIGHT)
    box(d, (5, 5, 26, 18), (17, 37, 27, 255), STEEL)
    # Three rising crop/field pulses.
    for idx, yy in enumerate((14, 11, 8)):
        xx = 9 + idx * 3
        line(d, [(xx, yy + 4), (xx + 2, yy + 1), (xx + 4, yy + 4)], GREEN, 2)
    line(d, [(8, 16), (24, 16)], MINT, 1)
    # Feed and return rails.
    box(d, (6, 21, 25, 25), (22, 31, 26, 255), DARK)
    box(d, (8, 22, 13, 24), GREEN)
    box(d, (15, 22, 20, 24), GOLD)
    box(d, (22, 22, 24, 24), MINT)
    for x in (4, 27):
        box(d, (x, 5, x + 1, 6), CREAM)
        box(d, (x, 25, x + 1, 26), CREAM)

def press_panel(d):
    # Amber hydraulic press with a visible platen and a seed puck.
    box(d, (1, 1, 30, 30), DARK, GOLD)
    box(d, (3, 3, 28, 28), (54, 42, 31, 255), STEEL)
    box(d, (6, 5, 25, 11), (26, 29, 26, 255), GOLD)
    box(d, (9, 6, 22, 9), AMBER, DARK)
    box(d, (12, 6, 19, 8), CREAM)
    line(d, [(7, 13), (24, 13)], HIGHLIGHT, 2)
    box(d, (10, 14, 21, 20), (35, 43, 35, 255), DARK)
    # Pressed seed/flake emblem.
    d.polygon([(13, 16), (16, 14), (19, 16), (18, 19), (14, 19)], fill=AMBER)
    box(d, (15, 16, 17, 17), CREAM)
    box(d, (7, 22, 24, 25), DARK, GOLD)
    for x in (9, 13, 17, 21):
        box(d, (x, 23, x + 1, 24), AMBER if x != 17 else CREAM)
    for x in (4, 27):
        box(d, (x, 5, x + 1, 6), CREAM)
        box(d, (x, 25, x + 1, 26), CREAM)

def reactor_panel(d):
    # A lit culture vessel framed by pipes and calibration markings.
    box(d, (1, 1, 30, 30), DARK, PALE_TEAL)
    box(d, (3, 3, 28, 28), (22, 44, 42, 255), STEEL)
    box(d, (7, 5, 24, 23), (15, 31, 32, 255), PALE_TEAL)
    box(d, (9, 8, 22, 21), (29, 91, 78, 255), TEAL)
    # Fluid level with pixel bubbles.
    box(d, (10, 15, 21, 20), GREEN)
    box(d, (10, 13, 21, 14), PALE_TEAL)
    for x, y in ((12, 10), (17, 9), (20, 12), (15, 16), (19, 18)):
        box(d, (x, y, x + 1, y + 1), CREAM if y < 12 else MINT)
    # Pressure stripe and lower reagent status.
    box(d, (5, 24, 26, 26), DARK, TEAL)
    box(d, (7, 25, 15, 25), PALE_TEAL)
    box(d, (18, 25, 24, 25), GREEN)
    for x in (4, 27):
        box(d, (x, 5, x + 1, 6), PALE_TEAL)
        box(d, (x, 25, x + 1, 26), PALE_TEAL)

save_panel("feldsammler", collector_panel)
save_panel("saatgutpresse", press_panel)
save_panel("biomasse_bioreaktor", reactor_panel)

def face(texture):
    return {"texture": texture, "uv": [0, 0, 16, 16]}

def element(from_, to, *, down="#bottom", up="#top", north="#front", south="#back", west="#side", east="#side"):
    return {
        "from": from_,
        "to": to,
        "faces": {
            "down": face(down),
            "up": face(up),
            "north": face(north),
            "south": face(south),
            "west": face(west),
            "east": face(east)
        }
    }

def machine_model(name):
    side="#side"; front="#front"; back="#back"; top="#top"; bottom="#bottom"; panel="#panel"
    elements = [
        # Skirt/base and main chassis.
        element([0,0,0], [16,2,16], down=bottom, up=side, north=side, south=side, west=side, east=side),
        element([1,1,1], [15,14,15], down=bottom, up=top, north=front, south=back, west=side, east=side),
        # Raised top ring gives the body a readable silhouette in third person.
        element([1,13,1], [15,15,15], down=side, up=top, north=side, south=back, west=side, east=side),
        # The front plate sits slightly proud of the body.
        element([4,5,0], [12,11,2], down=side, up=side, north=panel, south=side, west=side, east=side),
        # Feet/brackets separate the device from a featureless full-cube outline.
        element([2,0,2], [5,3,5], down=bottom, up=side, north=side, south=side, west=side, east=side),
        element([11,0,2], [14,3,5], down=bottom, up=side, north=side, south=side, west=side, east=side),
        element([2,0,11], [5,3,14], down=bottom, up=side, north=side, south=side, west=side, east=side),
        element([11,0,11], [14,3,14], down=bottom, up=side, north=side, south=side, west=side, east=side),
    ]
    if name == "feldsammler":
        # Wide collector arms are visible from either side.
        elements.extend([
            element([0,5,4], [2,9,12], down=side, up=top, north=side, south=side, west=back, east=side),
            element([14,5,4], [16,9,12], down=side, up=top, north=side, south=side, west=side, east=back),
            element([5,15,5], [11,16,11], down=side, up=top, north=top, south=side, west=side, east=side),
            element([7,3,0], [9,5,2], down=side, up=top, north=panel, south=side, west=side, east=side),
        ])
    elif name == "saatgutpresse":
        # Raised press head and center ram distinguish it from the collector.
        elements.extend([
            element([4,13,4], [12,16,12], down=side, up=top, north=panel, south=back, west=side, east=side),
            element([7,14,2], [9,16,5], down=side, up=top, north=panel, south=side, west=side, east=side),
            element([5,4,0], [11,5,2], down=side, up=top, north=top, south=side, west=side, east=side),
        ])
    elif name == "biomasse_bioreaktor":
        # Culture vessel projects from the front with pipes on both sides.
        elements.extend([
            element([4,3,0], [12,12,4], down=side, up=top, north=panel, south=side, west=top, east=top),
            element([5,12,0], [11,14,3], down=side, up=top, north=top, south=side, west=side, east=side),
            element([0,4,5], [2,12,7], down=side, up=side, north=side, south=side, west=top, east=side),
            element([14,4,5], [16,12,7], down=side, up=side, north=side, south=side, west=side, east=top),
        ])

    textures = {
        "front": f"sporenwerk:block/{name}",
        "panel": f"sporenwerk:block/{name}_panel",
        "side": f"sporenwerk:block/{name}_side",
        "back": f"sporenwerk:block/{name}_back",
        "top": f"sporenwerk:block/{name}_top",
        "bottom": f"sporenwerk:block/{name}_bottom",
        "particle": f"sporenwerk:block/{name}"
    }
    return {"ambientocclusion": True, "textures": textures, "elements": elements}

for name in ("feldsammler", "saatgutpresse", "biomasse_bioreaktor"):
    model_path = ASSETS / "models/block" / f"{name}.json"
    model = machine_model(name)
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    item_path = ASSETS / "models/item" / f"{name}.json"
    item_path.write_text(json.dumps({"parent": f"sporenwerk:block/{name}"}, indent=2) + "\n", encoding="utf-8")

    # Every model texture must exist before we ask Gradle to build the JAR.
    for texture in model["textures"].values():
        tex_path = ASSETS / "textures" / (texture.split(":",1)[1] + ".png")
        if not tex_path.is_file():
            raise SystemExit(f"Missing machine texture: {tex_path}")
    for el in model["elements"]:
        for side_data in el["faces"].values():
            if side_data["texture"].lstrip("#") not in model["textures"]:
                raise SystemExit(f"Unknown texture binding in {name}: {side_data['texture']}")

# Validate JSON and version metadata after all models have been written.
for path in (ASSETS/"models/block").glob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))
build=ROOT/"build.gradle"
build_text=build.read_text(encoding="utf-8")
build_text=re.sub(r"version = '[^']+'", "version = '1.1.9'", build_text, count=1)
build.write_text(build_text, encoding="utf-8")
readme=ROOT/"README.md"
readme_text=readme.read_text(encoding="utf-8").replace("1.1.8","1.1.9").replace("V1.1.8","V1.1.9")
readme_text += """

## 1.1.9 — distinct machine silhouettes
Machines now use multi-element 3D block models instead of a single cube. The field collector has side arms, the seed press has an elevated ram, and the bioreactor has a raised culture vessel and pipework. Each keeps its own front panel and separate face textures.
"""
readme.write_text(readme_text,encoding="utf-8")
print("Wrote distinct 3D machine geometry and per-machine control panels.")
