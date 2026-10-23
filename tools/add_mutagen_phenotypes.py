#!/usr/bin/env python3
"""Add active-field strength tiers and crop-specific mutation phenotypes."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")

def replace_once(path, old, new, label):
    p = ROOT / path
    source = p.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Mutagen phenotype patch cannot locate {label} in {path}")
    p.write_text(source.replace(old, new, 1), encoding="utf-8")

def method_end(source, signature):
    start = source.find(signature)
    if start < 0:
        raise SystemExit(f"Cannot locate Java method: {signature}")
    opening = source.find("{", start + len(signature))
    if opening < 0:
        raise SystemExit(f"Cannot locate method body: {signature}")
    depth = 0
    for i in range(opening, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise SystemExit(f"Unclosed method body: {signature}")

from PIL import Image, ImageDraw

ASSETS = ROOT / "src/main/resources/assets/sporenwerk"
BLOCK_TEXTURES = ASSETS / "textures/block"

# World-face textures are deliberately opaque 16x16 RGBA images. Transparent item
# sprites must never be used on cube_all block faces: that produces invisible faces.
BLOCK_PALETTES = {
    "infektionsherd": {
        "edge": (28, 20, 35, 255), "base": (65, 43, 76, 255), "hi": (112, 74, 127, 255),
        "shade": (42, 28, 51, 255), "accent": (145, 59, 175, 255), "accent_hi": (207, 113, 221, 255),
    },
    "mutagen_boden": {
        "edge": (29, 25, 29, 255), "base": (72, 56, 46, 255), "hi": (113, 84, 65, 255),
        "shade": (43, 37, 36, 255), "accent": (125, 47, 145, 255), "accent_hi": (190, 81, 203, 255),
    },
    "mutationsanker": {
        "edge": (18, 34, 37, 255), "base": (47, 81, 79, 255), "hi": (104, 156, 146, 255),
        "shade": (28, 52, 53, 255), "accent": (54, 185, 179, 255), "accent_hi": (153, 243, 216, 255),
    },
    "sporenresistenter_block": {
        "edge": (36, 45, 49, 255), "base": (99, 113, 115, 255), "hi": (150, 167, 166, 255),
        "shade": (65, 77, 81, 255), "accent": (68, 147, 169, 255), "accent_hi": (161, 218, 219, 255),
    },
}

MACHINE_PALETTES = {
    "feldsammler": {
        "edge": (15, 24, 19, 255), "base": (42, 62, 43, 255), "mid": (59, 83, 52, 255),
        "hi": (128, 158, 96, 255), "shade": (26, 39, 29, 255), "screen": (15, 35, 26, 255),
        "accent": (108, 182, 83, 255), "glow": (169, 230, 133, 255), "metal": (89, 112, 87, 255),
    },
    "saatgutpresse": {
        "edge": (28, 23, 19, 255), "base": (76, 55, 37, 255), "mid": (111, 75, 42, 255),
        "hi": (170, 123, 64, 255), "shade": (46, 34, 25, 255), "screen": (29, 28, 22, 255),
        "accent": (211, 130, 43, 255), "glow": (255, 209, 105, 255), "metal": (133, 103, 67, 255),
    },
    "biomasse_bioreaktor": {
        "edge": (14, 29, 29, 255), "base": (30, 58, 55, 255), "mid": (39, 83, 76, 255),
        "hi": (90, 151, 132, 255), "shade": (20, 40, 40, 255), "screen": (12, 35, 36, 255),
        "accent": (48, 174, 158, 255), "glow": (147, 234, 210, 255), "metal": (70, 116, 109, 255),
    },
}

def _save_texture(name, image):
    BLOCK_TEXTURES.mkdir(parents=True, exist_ok=True)
    image.save(BLOCK_TEXTURES / (name + ".png"), optimize=True)

def _bevel(image, edge, base, hi, shade):
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, 15, 15), fill=edge)
    d.rectangle((1, 1, 14, 14), fill=base)
    d.line((1, 1, 14, 1), fill=hi)
    d.line((1, 1, 1, 14), fill=hi)
    d.line((14, 2, 14, 14), fill=shade)
    d.line((2, 14, 14, 14), fill=shade)
    return d

def _make_solid_block_face(name, face):
    p = BLOCK_PALETTES[name]
    image = Image.new("RGBA", (16, 16), p["base"])
    d = _bevel(image, p["edge"], p["base"], p["hi"], p["shade"])
    if face == "top":
        # Small hard-edged mineral/soil pixels, never anti-aliased or transparent.
        specks = [(3,3),(5,7),(11,3),(12,6),(4,11),(8,12),(12,10),(7,5),(10,8)]
        for i, (x,y) in enumerate(specks):
            d.point((x,y), fill=p["hi"] if i % 3 == 0 else p["shade"])
        if name == "mutagen_boden":
            d.polygon([(5,6),(7,4),(9,5),(10,8),(8,10),(6,9)], fill=p["accent"])
            d.rectangle((7,5,7,6), fill=p["accent_hi"])
            d.point((10,10), fill=p["accent_hi"])
        elif name == "infektionsherd":
            d.polygon([(5,10),(6,7),(8,5),(10,7),(11,10),(8,12)], fill=p["accent"])
            d.rectangle((7,7,8,9), fill=p["accent_hi"])
            d.point((10,6), fill=p["accent_hi"])
        elif name == "mutationsanker":
            d.rectangle((4,4,11,11), fill=p["edge"])
            d.rectangle((5,5,10,10), fill=p["accent"])
            d.polygon([(7,6),(8,5),(9,7),(9,9),(8,10),(7,8)], fill=p["accent_hi"])
            d.point((6,6), fill=p["hi"])
        else:
            d.rectangle((4,4,11,11), fill=p["shade"])
            for x,y in [(5,5),(9,6),(7,9),(10,10)]:
                d.point((x,y), fill=p["accent"])
            d.point((8,7), fill=p["accent_hi"])
    elif face == "side":
        for y in (4, 8, 12):
            d.line((2, y, 13, y), fill=p["shade"])
        if name in ("mutagen_boden", "infektionsherd"):
            d.line((4,3,6,5,5,7,8,9,8,12), fill=p["accent"])
            d.point((6,5), fill=p["accent_hi"])
            d.point((8,10), fill=p["accent_hi"])
            d.rectangle((10,4,11,5), fill=p["hi"])
        elif name == "mutationsanker":
            d.rectangle((4,3,11,11), fill=p["edge"])
            d.rectangle((5,4,10,10), fill=p["accent"])
            d.rectangle((6,5,9,8), fill=p["screen"] if "screen" in p else p["shade"])
            d.line((6,9,9,9), fill=p["accent_hi"])
        else:
            d.rectangle((4,4,10,10), fill=p["shade"])
            d.point((6,6), fill=p["accent_hi"])
            d.point((9,8), fill=p["accent"])
    else:
        d.rectangle((4,4,11,11), fill=p["shade"])
        d.line((5,5,10,10), fill=p["edge"])
        d.line((10,5,5,10), fill=p["edge"])
        d.point((3,3), fill=p["hi"])
        d.point((12,12), fill=p["shade"])
    return image

for _block_name in BLOCK_PALETTES:
    for _face in ("top", "side", "bottom"):
        _save_texture(f"{_block_name}_{_face}", _make_solid_block_face(_block_name, _face))
    # Keep the legacy atlas key valid and opaque in case another generated model references it.
    _save_texture(_block_name, _make_solid_block_face(_block_name, "side"))
    _block_model = {
        "parent": "minecraft:block/cube",
        "textures": {
            "top": f"sporenwerk:block/{_block_name}_top",
            "side": f"sporenwerk:block/{_block_name}_side",
            "bottom": f"sporenwerk:block/{_block_name}_bottom",
            "particle": f"sporenwerk:block/{_block_name}_side",
        },
    }
    write(f"src/main/resources/assets/sporenwerk/models/block/{_block_name}.json",
          __import__("json").dumps(_block_model, indent=2) + "\n")

def _make_machine_face(name, face):
    p = MACHINE_PALETTES[name]
    image = Image.new("RGBA", (16, 16), p["base"])
    d = _bevel(image, p["edge"], p["base"], p["hi"], p["shade"])
    # Opaque industrial chassis pixels; this texture is a cube face, not an item icon.
    for x,y in ((2,2),(13,2),(2,13),(13,13)):
        d.point((x,y), fill=p["glow"] if (x+y)%2 == 0 else p["edge"])
    if face == "front":
        d.rectangle((3,3,12,12), fill=p["shade"])
        d.rectangle((4,4,11,11), fill=p["mid"])
        d.rectangle((5,5,10,9), fill=p["screen"], outline=p["edge"])
        if name == "feldsammler":
            d.line((6,8,7,6,8,7,9,5), fill=p["accent"], width=1)
            d.point((7,6), fill=p["glow"])
            d.line((6,9,10,9), fill=p["glow"])
        elif name == "saatgutpresse":
            d.rectangle((7,4,8,7), fill=p["metal"])
            d.rectangle((6,7,9,8), fill=p["accent"])
            d.rectangle((7,5,7,6), fill=p["glow"])
        else:
            d.rectangle((6,5,9,8), fill=p["accent"])
            d.rectangle((7,6,8,7), fill=p["glow"])
            d.point((10,6), fill=p["glow"])
        d.rectangle((5,10,10,11), fill=p["edge"])
        for x in (6,8,10):
            d.point((x,10), fill=p["glow"] if name != "saatgutpresse" else p["accent"])
    elif face == "panel":
        d.rectangle((1,1,14,14), fill=p["edge"])
        d.rectangle((2,2,13,13), fill=p["metal"])
        d.rectangle((3,3,12,10), fill=p["screen"])
        if name == "feldsammler":
            d.line((4,8,6,6,8,7,10,4,11,5), fill=p["accent"], width=1)
            d.point((8,6), fill=p["glow"])
            d.line((4,9,11,9), fill=p["glow"])
        elif name == "saatgutpresse":
            d.rectangle((5,3,10,5), fill=p["accent"])
            d.rectangle((7,5,8,8), fill=p["metal"])
            d.rectangle((6,8,9,9), fill=p["glow"])
        else:
            d.rectangle((4,7,11,9), fill=p["accent"])
            d.rectangle((5,5,10,6), fill=p["glow"])
            for x,y in ((5,4),(9,4),(10,7),(7,8)):
                d.point((x,y), fill=p["glow"])
        d.rectangle((4,11,11,12), fill=p["shade"])
        for x in (5,7,9,11):
            d.point((x,12), fill=p["accent"] if x%2 else p["glow"])
    elif face == "side":
        d.rectangle((3,2,12,13), fill=p["shade"])
        d.rectangle((4,3,11,12), fill=p["base"])
        for y in (4,6,8,10,12):
            d.line((5,y,10,y), fill=p["metal"])
            d.point((11,y), fill=p["hi"])
        d.line((3,3,3,12), fill=p["hi"])
        d.line((12,3,12,12), fill=p["edge"])
    elif face == "back":
        d.rectangle((2,2,13,13), fill=p["shade"])
        d.rectangle((3,3,12,12), fill=p["mid"])
        d.rectangle((4,4,11,11), fill=p["edge"])
        d.rectangle((5,5,10,10), fill=p["base"])
        d.line((5,6,10,6), fill=p["metal"])
        d.line((5,9,10,9), fill=p["metal"])
        d.line((8,6,8,9), fill=p["metal"])
        d.point((4,4), fill=p["glow"])
        d.point((11,11), fill=p["glow"])
    elif face == "top":
        d.rectangle((2,2,13,13), fill=p["shade"])
        d.rectangle((3,3,12,12), fill=p["mid"])
        if name == "biomasse_bioreaktor":
            d.rectangle((5,4,10,11), fill=p["screen"])
            d.rectangle((6,8,9,10), fill=p["accent"])
            d.line((6,7,9,7), fill=p["glow"])
            d.point((7,5), fill=p["glow"])
            d.point((9,6), fill=p["glow"])
        elif name == "saatgutpresse":
            d.rectangle((4,4,11,11), fill=p["edge"])
            d.rectangle((6,5,9,10), fill=p["metal"])
            d.rectangle((7,7,8,8), fill=p["accent"])
        else:
            for y in (5,7,9,11):
                d.line((4,y,11,y), fill=p["metal"])
            d.point((6,4), fill=p["glow"])
            d.point((9,12), fill=p["glow"])
    elif face == "bottom":
        d.rectangle((2,2,13,13), fill=p["edge"])
        d.rectangle((3,3,12,12), fill=p["shade"])
        d.line((4,4,11,11), fill=p["base"])
        d.line((11,4,4,11), fill=p["base"])
        for x,y in ((4,4),(11,4),(4,11),(11,11)):
            d.point((x,y), fill=p["metal"])
    # Assert that alpha is solid. This is a block atlas contract, not an item-sprite contract.
    if any(pixel[3] != 255 for pixel in image.getdata()):
        raise SystemExit(f"Machine cube face {name}/{face} unexpectedly contains transparency")
    return image

for _machine_name in MACHINE_PALETTES:
    for _face in ("front", "panel", "side", "back", "top", "bottom"):
        _texture = _make_machine_face(_machine_name, _face)
        _save_texture(f"{_machine_name}{'_' + _face if _face != 'front' else ''}", _texture)

# Crops intentionally retain transparent backgrounds; Minecraft must render them in cutout.
# Forge 1.20.1 requires an explicit client render layer for custom BushBlock crop sprites.
client_path = ROOT / "src/main/java/de/sporenwerk/client/ClientModEvents.java"
client_source = client_path.read_text(encoding="utf-8")
if "import net.minecraft.client.renderer.ItemBlockRenderTypes;" not in client_source:
    anchor_import = "import de.sporenwerk.registry.ModMenus;"
    if anchor_import not in client_source:
        raise SystemExit("Cannot locate ClientModEvents imports for crop cutout registration")
    client_source = client_source.replace(
        anchor_import,
        anchor_import + "\nimport de.sporenwerk.registry.ModBlocks;\n"
        "import net.minecraft.client.renderer.ItemBlockRenderTypes;\n"
        "import net.minecraft.client.renderer.RenderType;",
        1,
    )
setup_old = "event.enqueueWork(() -> MenuScreens.register(ModMenus.MACHINE.get(), MachineScreen::new));"
setup_new = """event.enqueueWork(() -> {
            MenuScreens.register(ModMenus.MACHINE.get(), MachineScreen::new);
            ItemBlockRenderTypes.setRenderLayer(ModBlocks.FASERROHR.get(), RenderType.cutout());
            ItemBlockRenderTypes.setRenderLayer(ModBlocks.BERNSTEINKAPPE.get(), RenderType.cutout());
            ItemBlockRenderTypes.setRenderLayer(ModBlocks.ROTWURZEL.get(), RenderType.cutout());
            ItemBlockRenderTypes.setRenderLayer(ModBlocks.FILTERMOOS.get(), RenderType.cutout());
        });"""
if "ItemBlockRenderTypes.setRenderLayer(ModBlocks.FASERROHR.get(), RenderType.cutout())" not in client_source:
    if setup_old not in client_source:
        raise SystemExit("Cannot locate ClientModEvents setup hook for crop cutout render layer")
    client_source = client_source.replace(setup_old, setup_new, 1)
client_path.write_text(client_source, encoding="utf-8")

# Persistent crop appearance: strength is a real synced block-state property.
# It is recalculated by the server on crop random ticks so it falls back to normal after cure/source shutdown.
crop_base_rel = "src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java"
crop_java = read(crop_base_rel)
crop_imports = [
    "import net.minecraft.core.BlockPos;",
    "import net.minecraft.server.level.ServerLevel;",
    "import net.minecraft.util.RandomSource;",
    "import net.minecraft.world.level.block.Block;",
    "import net.minecraft.world.level.block.state.BlockState;",
    "import net.minecraft.world.level.block.state.StateDefinition;",
    "import net.minecraft.world.level.block.state.properties.IntegerProperty;",
    "import de.sporenwerk.infection.MutationField;",
]
for _imp in crop_imports:
    if _imp not in crop_java:
        _pkg = "package de.sporenwerk.block.crop;"
        if _pkg not in crop_java:
            raise SystemExit("Cannot locate crop base package for mutation property")
        crop_java = crop_java.replace(_pkg, _pkg + "\n\n" + _imp, 1)

_class_anchor = "public abstract class AbstractSporeCropBlock extends CropBlock {"
if "public static final IntegerProperty MUTAGEN_LEVEL" not in crop_java:
    if _class_anchor not in crop_java:
        raise SystemExit("Cannot locate AbstractSporeCropBlock declaration")
    crop_java = crop_java.replace(
        _class_anchor,
        _class_anchor + '\n    public static final IntegerProperty MUTAGEN_LEVEL = IntegerProperty.create("mutagen_level", 0, 3);',
        1,
    )

# Set the default state to unmutated without replacing CropBlock's default age.
_ctor_match = re.search(r"protected\s+AbstractSporeCropBlock\s*\([^)]*\)\s*\{", crop_java)
if not _ctor_match:
    raise SystemExit("Cannot locate AbstractSporeCropBlock constructor")
_ctor_start = _ctor_match.start()
_ctor_end = method_end(crop_java, "protected AbstractSporeCropBlock")
_ctor_body = crop_java[_ctor_start:_ctor_end]
if "setValue(MUTAGEN_LEVEL, 0)" not in _ctor_body:
    if "super(properties);" not in _ctor_body:
        raise SystemExit("Cannot locate crop super-constructor call")
    _ctor_body = _ctor_body.replace(
        "super(properties);",
        "super(properties);\n        registerDefaultState(defaultBlockState().setValue(MUTAGEN_LEVEL, 0));",
        1,
    )
    crop_java = crop_java[:_ctor_start] + _ctor_body + crop_java[_ctor_end:]

if "createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder)" not in crop_java:
    _ctor_end = method_end(crop_java, "protected AbstractSporeCropBlock")
    _state_methods = """

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(MUTAGEN_LEVEL);
    }

    /** Mature plants also tick so field strength changes are reflected without replanting. */
    @Override
    public boolean isRandomlyTicking(BlockState state) {
        return true;
    }
"""
    crop_java = crop_java[:_ctor_end] + _state_methods + crop_java[_ctor_end:]

_random_tick_call = "        super.randomTick(state, level, pos, random);"
_mutation_refresh = """        int activeMutagenStrength = MutationField.mutagenStrengthAt(level, pos);
        if (state.getValue(MUTAGEN_LEVEL) != activeMutagenStrength) {
            state = state.setValue(MUTAGEN_LEVEL, activeMutagenStrength);
            level.setBlock(pos, state, 2);
        }
        super.randomTick(state, level, pos, random);"""
if "int activeMutagenStrength = MutationField.mutagenStrengthAt(level, pos);" not in crop_java:
    if _random_tick_call not in crop_java:
        raise SystemExit("Cannot locate crop random-tick hook for visible mutation refresh")
    crop_java = crop_java.replace(_random_tick_call, _mutation_refresh, 1)
(ROOT / crop_base_rel).write_text(crop_java, encoding="utf-8")

# Build palette-shifted 16x16 alpha sprites. Their silhouettes remain voxel-pixel art;
# only the phenotype palette and small vein pixels change with local mutagen strength.
def _mutated_crop_sprite(source_path, crop_name, strength):
    with Image.open(source_path) as source:
        image = source.convert("RGBA")
    new_pixels = []
    for r, g, b, a in image.getdata():
        if a == 0:
            new_pixels.append((0, 0, 0, 0))
            continue
        if max(r, g, b) < 62:  # keep the one-pixel outline dark and readable
            new_pixels.append((max(8, r // 2), max(10, g // 2), max(12, b // 2), a))
        elif g >= r and g >= b:  # green leaves and stems
            if strength == 1:
                new_pixels.append((max(12, r // 2), min(255, g + 5), min(255, b + 42), a))
            elif strength == 2:
                new_pixels.append((min(255, r + 48), max(12, g // 2), min(255, b + 78), a))
            else:
                new_pixels.append((min(255, r + 82), max(8, g // 3), min(255, b + 120), a))
        elif r > g and g >= b and g > 80:  # amber caps and crimson roots
            if g >= 125:  # preserve the species' cap shape at low mutation
                if strength == 1:
                    new_pixels.append((r, min(255, g + 18), min(255, b + 42), a))
                elif strength == 2:
                    new_pixels.append((min(255, r * 2 // 3 + 25), min(255, g // 2 + 10), min(255, b + 95), a))
                else:
                    new_pixels.append((min(255, r * 4 // 5 + 18), min(255, g // 3 + 20), min(255, b + 145), a))
            elif strength == 1:
                new_pixels.append((min(255, r + 12), min(255, g + 30), min(255, b + 42), a))
            elif strength == 2:
                new_pixels.append((min(255, r * 4 // 5 + 30), max(12, g // 2), min(255, b + 85), a))
            else:
                new_pixels.append((min(255, r + 55), max(18, g // 2), min(255, b + 125), a))
        elif r > 175 and g > 145 and b > 115:  # pale mushroom stems and spore highlights
            if strength == 1:
                new_pixels.append((min(255, r - 8), min(255, g + 8), min(255, b + 28), a))
            elif strength == 2:
                new_pixels.append((min(255, r - 6), min(255, g + 2), 255, a))
            else:
                new_pixels.append((min(255, r - 18), 255, min(255, b + 36), a))
        else:
            if strength == 1:
                new_pixels.append((r, min(255, g + 8), min(255, b + 24), a))
            elif strength == 2:
                new_pixels.append((min(255, r + 35), max(8, g // 2), min(255, b + 70), a))
            else:
                new_pixels.append((min(255, r + 65), max(8, g // 3), min(255, b + 105), a))
    image.putdata(new_pixels)
    draw = ImageDraw.Draw(image)
    # Tiny, hard-edged field traces differ by plant so the variant is visible at 16x16.
    traces = {
        "faserrohr": [(13, 6), (11, 9), (15, 12)],
        "bernsteinkappe": [(8, 14), (15, 10), (22, 15)],
        "rotwurzel": [(14, 19), (16, 22), (14, 25)],
        "filtermoos": [(7, 18), (13, 14), (20, 18), (23, 21)],
    }.get(crop_name, [])
    trace_colors = {
        1: (81, 218, 181, 255),
        2: (220, 93, 242, 255),
        3: (111, 250, 229, 255),
    }
    for x, y in traces:
        if 0 <= x < 16 and 0 <= y < 16:
            pixel = image.getpixel((x, y))
            if pixel[3] > 0:
                draw.point((x, y), fill=trace_colors[strength])
    return image

_age_to_stage = {
    "faserrohr": [0, 1, 1, 2, 2, 2, 2, 2],
    "bernsteinkappe": [0, 1, 2, 2, 2, 2, 2, 2],
    "rotwurzel": [0, 0, 1, 1, 2, 2, 2, 2],
    "filtermoos": [0, 1, 2, 2, 2, 2, 2, 2],
}
for _crop_name, _age_stages in _age_to_stage.items():
    for _stage in range(3):
        _base_texture = BLOCK_TEXTURES / f"{_crop_name}_stage{_stage}.png"
        if not _base_texture.is_file():
            raise SystemExit(f"Missing source crop texture {_base_texture}")
        for _strength in range(1, 4):
            _mutant = _mutated_crop_sprite(_base_texture, _crop_name, _strength)
            _texture_name = f"{_crop_name}_stage{_stage}_mutagen{_strength}"
            _save_texture(_texture_name, _mutant)
            write(
                f"src/main/resources/assets/sporenwerk/models/block/{_texture_name}.json",
                json.dumps({
                    "parent": "minecraft:block/crop",
                    "textures": {"crop": f"sporenwerk:block/{_texture_name}"},
                }, indent=2) + "\n",
            )
    _variants = {}
    for _age, _stage in enumerate(_age_stages):
        for _strength in range(4):
            if _strength == 0:
                _model_name = f"{_crop_name}_stage{_stage}"
            else:
                _model_name = f"{_crop_name}_stage{_stage}_mutagen{_strength}"
            _variants[f"age={_age},mutagen_level={_strength}"] = {
                "model": f"sporenwerk:block/{_model_name}"
            }
    write(
        f"src/main/resources/assets/sporenwerk/blockstates/{_crop_name}.json",
        json.dumps({"variants": _variants}, indent=2) + "\n",
    )

# Active saved sources determine the strongest tier overlapping a position.
nodes_path = "src/main/java/de/sporenwerk/infection/MutationNodeData.java"
nodes = read(nodes_path)
strength_signature = "public int getFieldStrengthAt(BlockPos target, int radius, int halfHeight)"
if strength_signature not in nodes:
    anchor = "public boolean hasActiveFieldAt(BlockPos target, int radius, int halfHeight)"
    end = method_end(nodes, anchor)
    strength_method = """

    public int getFieldStrengthAt(BlockPos target, int radius, int halfHeight) {
        int best = 0;
        for (Map.Entry<Long, Boolean> entry : nodes.entrySet()) {
            if (!entry.getValue()) continue;
            BlockPos origin = BlockPos.of(entry.getKey());
            long dx = (long) target.getX() - origin.getX();
            long dz = (long) target.getZ() - origin.getZ();
            long horizontalSquared = dx * dx + dz * dz;
            int vertical = Math.abs(target.getY() - origin.getY());
            if (horizontalSquared > (long) radius * radius || vertical > halfHeight) continue;

            int strength = horizontalSquared <= 4L && vertical <= 1 ? 3
                    : horizontalSquared <= 25L && vertical <= 2 ? 2 : 1;
            best = Math.max(best, strength);
            if (best == 3) return 3;
        }
        return best;
    }"""
    nodes_path_full = ROOT / nodes_path
    nodes_path_full.write_text(nodes[:end] + strength_method + nodes[end:], encoding="utf-8")

# Shared intensity query respects inactive sources and sterilizing anchors.
field_path = "src/main/java/de/sporenwerk/infection/MutationField.java"
field = read(field_path)
if "public static int mutagenStrengthAt(Level level, BlockPos target)" not in field:
    anchor = "    public static boolean insideBounds(BlockPos origin, BlockPos target) {"
    method = """    public static int mutagenStrengthAt(Level level, BlockPos target) {
        if (!(level instanceof ServerLevel serverLevel) || hasAnchor(serverLevel, target)) return 0;
        return MutationNodeData.get(serverLevel).getFieldStrengthAt(target, RADIUS, INFECTION_HALF_HEIGHT);
    }

"""
    if anchor not in field:
        raise SystemExit("Cannot locate MutationField bounds method for strength query")
    field_path_full = ROOT / field_path
    field_path_full.write_text(field.replace(anchor, method + anchor, 1), encoding="utf-8")
    field = read(field_path)

# Existing callers now share exactly the same active/inactive/healed-field definition.
old_active = """    public static boolean isInActiveMutagenField(Level level, BlockPos target) {
        if (!(level instanceof ServerLevel serverLevel)) return false;
        return MutationNodeData.get(serverLevel).hasActiveFieldAt(target, RADIUS, INFECTION_HALF_HEIGHT)
                && !hasAnchor(serverLevel, target);
    }"""
new_active = """    public static boolean isInActiveMutagenField(Level level, BlockPos target) {
        return mutagenStrengthAt(level, target) > 0;
    }"""
replace_once(field_path, old_active, new_active, "shared active-field predicate")

# Plant growth accelerates with local strength, but not inside an anchor's sterile zone.
field = read(field_path)
growth_old = "            if (random.nextFloat() < 0.20F) level.setBlock(pos, crop.getStateForAge(crop.getAge(state) + 1), 2);"
growth_new = """            int strength = mutagenStrengthAt(level, pos);
            float growthChance = strength >= 3 ? 0.40F : strength == 2 ? 0.30F : 0.20F;
            if (strength > 0 && random.nextFloat() < growthChance) {
                level.setBlock(pos, crop.getStateForAge(crop.getAge(state) + 1), 2);
            }"""
replace_once(field_path, growth_old, growth_new, "mutagen-strength growth chance")

# Manual harvesting has four distinct, source-driven phenotypes:
# fiber cane gains deterministic yield; redroot can form extra tubers; amber caps can overproduce;
# filter moss sheds extra plant residue. The spore rate scales with field strength.
crop_path = "src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java"
crop = read(crop_path)
for imp in ("import de.sporenwerk.registry.ModBlocks;",):
    if imp not in crop:
        package_line = "package de.sporenwerk.block.crop;"
        if package_line not in crop:
            raise SystemExit("Cannot locate crop package declaration")
        crop = crop.replace(package_line, package_line + "\n\n" + imp, 1)
crop_path_full = ROOT / crop_path
crop_path_full.write_text(crop, encoding="utf-8")
drop_line = "Block.popResource(level, pos, new ItemStack(produceItem(), produceCount));"
mutated_drop = """int mutagenStrength = MutationField.mutagenStrengthAt(level, pos);
        int mutationBonus = 0;
        if (mutagenStrength >= 2) {
            if (this == ModBlocks.FASERROHR.get()) {
                mutationBonus = mutagenStrength - 1;
            } else if (this == ModBlocks.ROTWURZEL.get()
                    && level.random.nextFloat() < (mutagenStrength >= 3 ? 0.45F : 0.20F)) {
                mutationBonus++;
            } else if (this == ModBlocks.BERNSTEINKAPPE.get() && mutagenStrength >= 3
                    && level.random.nextFloat() < 0.25F) {
                mutationBonus++;
            }
        }
        Block.popResource(level, pos, new ItemStack(produceItem(), produceCount + mutationBonus));
        if (this == ModBlocks.FILTERMOOS.get() && mutagenStrength >= 2
                && level.random.nextFloat() < (mutagenStrength >= 3 ? 0.55F : 0.30F)) {
            Block.popResource(level, pos, new ItemStack(ModItems.PFLANZENRESTE.get()));
        }"""
crop = read(crop_path)
if "int mutagenStrength = MutationField.mutagenStrengthAt(level, pos);" not in crop:
    if drop_line not in crop:
        raise SystemExit("Cannot locate manual crop harvest output")
    crop = crop.replace(drop_line, mutated_drop, 1)
crop_path_full.write_text(crop, encoding="utf-8")
spore_old = """if (MutationField.isInActiveMutagenField(level, pos) && level.random.nextFloat() < 0.22F) {"""
spore_new = """if (mutagenStrength > 0 && level.random.nextFloat() <
                (mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F)) {"""
replace_once(crop_path, spore_old, spore_new, "strength-dependent mutagenic spore chance")

# The automated collector applies the same phenotype rules. It preflights these adjusted stacks
# alongside residue and mutagenic spores before spending energy or consuming a crop.
be_path = "src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java"
be = read(be_path)
output_anchor = "            ItemStack output = new ItemStack(produce, amount);"
output_patch = """            int mutagenStrength = MutationField.mutagenStrengthAt(level, target);
            var mutationCropState = level.getBlockState(target);
            if (mutagenStrength >= 2) {
                if (mutationCropState.is(de.sporenwerk.registry.ModBlocks.FASERROHR.get())) {
                    amount += mutagenStrength - 1;
                } else if (mutationCropState.is(de.sporenwerk.registry.ModBlocks.ROTWURZEL.get())
                        && level.random.nextFloat() < (mutagenStrength >= 3 ? 0.45F : 0.20F)) {
                    amount++;
                } else if (mutationCropState.is(de.sporenwerk.registry.ModBlocks.BERNSTEINKAPPE.get())
                        && mutagenStrength >= 3 && level.random.nextFloat() < 0.25F) {
                    amount++;
                }
            }
            ItemStack output = new ItemStack(produce, amount);"""
if "var mutationCropState = level.getBlockState(target);" not in be:
    if output_anchor not in be:
        raise SystemExit("Cannot locate field-collector stack creation")
    be = be.replace(output_anchor, output_patch, 1)
residue_old = "            boolean yieldsResidue = level.random.nextFloat() < 0.35F;"
residue_new = """            boolean filterMossPhenotype = mutationCropState.is(
                    de.sporenwerk.registry.ModBlocks.FILTERMOOS.get()) && mutagenStrength >= 2;
            float residueChance = filterMossPhenotype
                    ? (mutagenStrength >= 3 ? 0.70F : 0.55F) : 0.35F;
            boolean yieldsResidue = level.random.nextFloat() < residueChance;"""
if residue_old in be:
    be = be.replace(residue_old, residue_new, 1)
elif residue_new not in be:
    raise SystemExit("Cannot locate collector residue chance")
spore_old_machine = """            boolean yieldsMutagenSpores = MutationField.isInActiveMutagenField(level, target)
                    && level.random.nextFloat() < 0.22F;"""
spore_new_machine = """            boolean yieldsMutagenSpores = mutagenStrength > 0
                    && level.random.nextFloat() <
                    (mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F);"""
if spore_old_machine in be:
    be = be.replace(spore_old_machine, spore_new_machine, 1)
elif spore_new_machine not in be:
    raise SystemExit("Cannot locate collector mutagen-spore chance")
(ROOT / be_path).write_text(be, encoding="utf-8")

# The older collector test asserted a literal 35% value at the call site. Preserve its
# baseline contract while allowing Filtermoos to scale residue odds with field strength.
machine_test_path = ROOT / "tools/test_machine_farming_loop.py"
if machine_test_path.is_file():
    machine_test = machine_test_path.read_text(encoding="utf-8")
    old_assertion = """require("boolean yieldsResidue = level.random.nextFloat() < 0.35F;" in be,
        "the field collector must produce residue with the same 35% chance as crop loot")"""
    new_assertion = """require("float residueChance = " in be
        and "boolean yieldsResidue = level.random.nextFloat() < residueChance;" in be
        and "0.35F" in be,
        "the collector must preserve the 35% baseline and scale Filtermoos residue by phenotype")"""
    if old_assertion in machine_test:
        machine_test = machine_test.replace(old_assertion, new_assertion, 1)
    elif new_assertion not in machine_test:
        raise SystemExit("Cannot update farming-loop regression for the phenotype-aware residue chance")
    old_field_assertion = """require("MutationField.isInActiveMutagenField(level, target)" in be,
        "automated fields must award the same controlled mutagen by-product")"""
    new_field_assertion = """require("MutationField.mutagenStrengthAt(level, target)" in be
        and "mutagenStrength > 0" in be,
        "automated fields must use the saved-source intensity and healing-zone rules")"""
    if old_field_assertion in machine_test:
        machine_test = machine_test.replace(old_field_assertion, new_field_assertion, 1)
    elif new_field_assertion not in machine_test:
        raise SystemExit("Cannot update collector regression for the shared field-strength query")
    machine_test_path.write_text(machine_test, encoding="utf-8")

# Upgrade the previous milestone's assertions to the tiered field-strength contract.
# These tests are generated by add_mutagen_harvest.py earlier in the workflow.
old_harvest_test_path = ROOT / "tools/test_mutagen_harvest.py"
if old_harvest_test_path.is_file():
    harvest_test = old_harvest_test_path.read_text(encoding="utf-8")
    test_replacements = [
        (
            '''require("!hasAnchor(serverLevel, target)" in field, "healed zones must not produce mutagen spores")''',
            '''require("hasAnchor(serverLevel, target)) return 0" in field, "healed zones must not produce mutagen spores")'''
        ),
        (
            '''require("MutationField.isInActiveMutagenField(level, pos)" in crop
        and "level.random.nextFloat() < 0.22F" in crop,
        "manual crop harvest must give the controlled 22% bonus chance")''',
            '''require("MutationField.mutagenStrengthAt(level, pos)" in crop
        and "mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F" in crop,
        "manual crop harvest must scale its spore chance with the active field tier")'''
        ),
        (
            '''require("MutationField.isInActiveMutagenField(level, target)" in machine
        and "canFitOutputs(output, residue, mutagenSpores)" in machine
        and "insertOutputs(output, residue, mutagenSpores)" in machine,
        "automated harvest must share the bonus and buffer every possible result atomically")''',
            '''require("MutationField.mutagenStrengthAt(level, target)" in machine
        and "mutagenStrength > 0" in machine
        and "canFitOutputs(output, residue, mutagenSpores)" in machine
        and "insertOutputs(output, residue, mutagenSpores)" in machine,
        "automated harvest must share strength tiers and buffer every possible result atomically")'''
        )
    ]
    for old_assertion, new_assertion in test_replacements:
        if old_assertion in harvest_test:
            harvest_test = harvest_test.replace(old_assertion, new_assertion, 1)
        elif new_assertion not in harvest_test:
            raise SystemExit("Cannot update mutagen-harvest regression for strength-based phenotypes")
    old_harvest_test_path.write_text(harvest_test, encoding="utf-8")

# Source-level regression suite verifies tier boundaries, sterile suppression, crop traits and
# the collector's atomic output reservation, so the patch fails closed if upstream code drifts.
write("tools/test_mutagen_phenotypes.py", r'''
from pathlib import Path
import json, sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Mutagen phenotype regression: " + message)
nodes = read("src/main/java/de/sporenwerk/infection/MutationNodeData.java")
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
crop = read("src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java")
machine = read("src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java")
require("getFieldStrengthAt(BlockPos target, int radius, int halfHeight)" in nodes,
        "strength must come from persisted active sources")
require("horizontalSquared <= 4L && vertical <= 1 ? 3" in nodes
        and "horizontalSquared <= 25L && vertical <= 2 ? 2 : 1" in nodes,
        "three field tiers must have deterministic spatial boundaries")
require("hasAnchor(serverLevel, target)) return 0" in field
        and "return mutagenStrengthAt(level, target) > 0" in field,
        "anchors and stopped sources must suppress mutation tiers")
require("strength >= 3 ? 0.40F : strength == 2 ? 0.30F : 0.20F" in field,
        "crop growth acceleration must scale with field intensity")
for token in ("ModBlocks.FASERROHR.get()", "ModBlocks.ROTWURZEL.get()",
              "ModBlocks.BERNSTEINKAPPE.get()", "ModBlocks.FILTERMOOS.get()"):
    require(token in crop, "manual phenotype missing for " + token)
require("produceCount + mutationBonus" in crop
        and "ModItems.PFLANZENRESTE.get()" in crop,
        "manual crop yields must differ by phenotype")
require("mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F" in crop,
        "manual spore rate must scale with field strength")
require("var mutationCropState = level.getBlockState(target);" in machine
        and "amount += mutagenStrength - 1;" in machine,
        "automated collector must apply crop-specific yield bonuses")
require("canFitOutputs(output, residue, mutagenSpores)" in machine
        and "insertOutputs(output, residue, mutagenSpores)" in machine,
        "phenotype items must stay in the atomic output-buffer transaction")
require("0.70F : 0.55F) : 0.35F" in machine,
        "filter-moss phenotype must improve automated residue production")
require("mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F" in machine,
        "automated mutagen spore output must use the same tier odds as manual harvest")
require('IntegerProperty.create("mutagen_level", 0, 3)' in crop
        and "builder.add(MUTAGEN_LEVEL)" in crop
        and "activeMutagenStrength = MutationField.mutagenStrengthAt(level, pos)" in crop,
        "crop mutation appearance must be a server-synchronized field-strength state")
age_stages = {
    "faserrohr": [0,1,1,2,2,2,2,2],
    "bernsteinkappe": [0,1,2,2,2,2,2,2],
    "rotwurzel": [0,0,1,1,2,2,2,2],
    "filtermoos": [0,1,2,2,2,2,2,2],
}
for name, stages in age_stages.items():
    state = json.loads(read(f"src/main/resources/assets/sporenwerk/blockstates/{name}.json"))
    require(len(state["variants"]) == 32, name + " must define every crop age and mutation tier")
    for age, stage in enumerate(stages):
        for strength in range(4):
            variant = state["variants"].get(f"age={age},mutagen_level={strength}")
            require(variant is not None, f"{name} missing age={age}, mutagen_level={strength}")
            model_name = variant["model"].split(":", 1)[1]
            model_path = f"src/main/resources/assets/{model_name}.json"
            require((root / model_path).is_file(), name + " references missing variant model " + model_name)
            model = json.loads(read(model_path))
            expected_texture = (f"sporenwerk:block/{name}_stage{stage}" if strength == 0
                                else f"sporenwerk:block/{name}_stage{stage}_mutagen{strength}")
            require(model.get("textures", {}).get("crop") == expected_texture,
                    name + " mutation state must select its own stage texture")
print("Mutagen tiers, crop-specific yields, 128 visible age/mutation variants, and collector transactions passed.")
''')

# Bump the actual mod version after all earlier patch scripts have run.
build_path = ROOT / "build.gradle"
build = build_path.read_text(encoding="utf-8")
build = re.sub(r"version = '[^']+'", "version = '1.11.0'", build, count=1)
build_path.write_text(build, encoding="utf-8")
readme = ROOT / "README.md"
doc = readme.read_text(encoding="utf-8")
doc += """

## 1.11.0 — Visible mutagen crop phenotypes
- Mutagen fields now have three spatial strength tiers, based on distance and vertical separation from an active saved source. Sterile anchors and deactivated fields grant no mutation tier.
- Stronger fields accelerate Sporenwerk crop growth more often. Harvest traits are crop-specific: Faserrohr gains guaranteed fiber yield, Rotwurzel can form extra roots, Bernsteinkappe can overproduce at peak strength, and Filtermoos yields extra plant residue.
- Mutagenic spore odds scale with local strength (12%, 22%, 35%). Manual harvesting and the automated Field Collector share the crop-yield rules; the collector still reserves every possible output before it spends energy or consumes a crop.
- Cube faces now use opaque, 16x16 Minecraft block textures rather than transparent item sprites. The four custom crops explicitly use the cutout render layer so their transparent backgrounds render properly in-world. The texture QA sheet shows the actual block faces and no longer flags a spawn egg as a missing PNG.
- Each crop now stores a synced `mutagen_level` block state from 0 to 3. It selects a distinct 16x16 texture/model for each mutation tier, refreshes on server crop ticks, and returns to its normal sprite when the active field no longer covers it or a healing anchor suppresses the field.
- Regression checks cover model-to-texture references, opaque world-face textures, cutout crops, all 32 age/mutation variants per plant, synced state refresh, spatial tier boundaries, anchor suppression, manual and automated phenotypes, and atomic machine output.
"""
readme.write_text(doc, encoding="utf-8")
print("Installed Sporenwerk 1.11.0 Minecraft textures and visible mutagen crop phenotypes.")
