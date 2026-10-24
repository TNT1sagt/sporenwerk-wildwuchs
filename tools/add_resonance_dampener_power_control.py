#!/usr/bin/env python3
"""Make the Mutagen Resonance Dampener a redstone-controlled active shield (1.36.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"
TEXTURES = ASSETS / "textures/block"


def require_anchor(text, anchor, label):
    if anchor not in text:
        raise SystemExit(f"Cannot add powered resonance dampener: missing {label} anchor")


def update_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    require_anchor(text, old, label)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# A physical redstone input powers the shield. No block-entity ticker is needed.
write_class = """\
package de.sporenwerk.block;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;

/**
 * Redstone-controlled resonance shield. An unpowered unit is an inert, low-light
 * instrument; redstone activates the resonator and its field-suppression capability.
 */
public final class MutagenResonanceDampenerBlock extends Block {
    public static final BooleanProperty POWERED = BooleanProperty.create("powered");

    public MutagenResonanceDampenerBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(POWERED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(POWERED);
    }

    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos,
                        BlockState oldState, boolean moving) {
        super.onPlace(state, level, pos, oldState, moving);
        updatePower(state, level, pos);
    }

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos,
                                Block neighborBlock, BlockPos neighborPos, boolean moving) {
        updatePower(state, level, pos);
    }

    private void updatePower(BlockState state, Level level, BlockPos pos) {
        if (level.isClientSide) return;
        boolean powered = level.hasNeighborSignal(pos);
        if (state.getValue(POWERED) != powered) {
            level.setBlock(pos, state.setValue(POWERED, powered), 3);
        }
    }
}
"""
(SRC / "block/MutagenResonanceDampenerBlock.java").write_text(write_class, encoding="utf-8")

# The registry controls light based on the synchronized POWERED property.
blocks_path = SRC / "registry/ModBlocks.java"
blocks = blocks_path.read_text(encoding="utf-8")
old_light = ".strength(4.5f, 9.0f).requiresCorrectToolForDrops().lightLevel(state -> 7)"
new_light = ".strength(4.5f, 9.0f).requiresCorrectToolForDrops().lightLevel(state -> state.getValue(MutagenResonanceDampenerBlock.POWERED) ? 10 : 0)"
if old_light in blocks:
    blocks_path.write_text(blocks.replace(old_light, new_light, 1), encoding="utf-8")
elif new_light not in blocks:
    raise SystemExit("Cannot make resonance-dampener light level follow its powered state")

# Give the blockstate a separate model per redstone state. The item remains the idle model.
write = lambda rel, content: (ROOT / rel).parent.mkdir(parents=True, exist_ok=True) or (ROOT / rel).write_text(content.lstrip(), encoding="utf-8")
write("src/main/resources/assets/sporenwerk/blockstates/mutagen_resonanzdaempfer.json", """
{
  "variants": {
    "powered=false": { "model": "sporenwerk:block/mutagen_resonanzdaempfer" },
    "powered=true": { "model": "sporenwerk:block/mutagen_resonanzdaempfer_active" }
  }
}
""")
write("src/main/resources/assets/sporenwerk/models/block/mutagen_resonanzdaempfer_active.json", """
{
  "parent": "minecraft:block/cube_column",
  "textures": {
    "end": "sporenwerk:block/mutagen_resonanzdaempfer_top_active",
    "side": "sporenwerk:block/mutagen_resonanzdaempfer_side_active"
  }
}
""")
write("src/main/resources/assets/sporenwerk/models/item/mutagen_resonanzdaempfer.json", """
{
  "parent": "sporenwerk:block/mutagen_resonanzdaempfer"
}
""")

# Paint brighter active textures from the already validated idle textures.
def active_top():
    path = TEXTURES / "mutagen_resonanzdaempfer_top.png"
    with Image.open(path) as source:
        im = source.convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle((3, 3, 12, 12), outline=(83, 240, 217, 255), width=1)
    d.rectangle((4, 4, 11, 11), outline=(56, 171, 169, 255), width=1)
    d.rectangle((5, 5, 10, 10), fill=(48, 156, 155, 255), outline=(113, 255, 222, 255))
    d.rectangle((6, 6, 9, 9), fill=(94, 250, 215, 255))
    d.rectangle((7, 7, 8, 8), fill=(255, 255, 219, 255))
    for x, y in ((2, 2), (12, 2), (2, 12), (12, 12)):
        d.point((x, y), fill=(255, 215, 123, 255))
    d.line([(1, 6), (3, 6)], fill=(112, 255, 230, 255), width=1)
    d.line([(12, 9), (14, 9)], fill=(112, 255, 230, 255), width=1)
    return im

def active_side():
    path = TEXTURES / "mutagen_resonanzdaempfer_side.png"
    with Image.open(path) as source:
        im = source.convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle((2, 4, 13, 11), fill=(28, 57, 64, 255), outline=(61, 217, 201, 255))
    d.rectangle((4, 5, 11, 10), fill=(35, 139, 143, 255), outline=(87, 246, 215, 255))
    d.rectangle((5, 6, 10, 9), fill=(50, 193, 184, 255))
    d.rectangle((6, 7, 9, 8), fill=(126, 255, 225, 255))
    d.point((7, 7), fill=(255, 255, 220, 255))
    d.point((8, 8), fill=(255, 255, 220, 255))
    for x in (2, 4, 11, 13):
        d.line([(x, 5), (x, 10)], fill=(242, 187, 105, 255), width=1)
    d.line([(3, 2), (12, 2)], fill=(122, 255, 221, 255), width=1)
    d.line([(3, 13), (12, 13)], fill=(122, 255, 221, 255), width=1)
    return im

for name, image in (
    ("mutagen_resonanzdaempfer_top_active.png", active_top()),
    ("mutagen_resonanzdaempfer_side_active.png", active_side()),
):
    path = TEXTURES / name
    image.save(path, optimize=True)
    with Image.open(path) as check:
        rgba = check.convert("RGBA")
        if rgba.size != (16, 16) or any(px[3] != 255 for px in rgba.getdata()):
            raise SystemExit(f"{name} must be an opaque 16x16 PNG")
        if len(set(rgba.getdata())) < 12:
            raise SystemExit(f"{name} lacks visible active-state contrast")

# Only an ACTIVE dampener suppresses the hostile resonance pulse.
entity_path = SRC / "entity/KristallpirscherEntity.java"
entity = entity_path.read_text(encoding="utf-8")
if "import de.sporenwerk.block.MutagenResonanceDampenerBlock;" not in entity:
    require_anchor(entity, "import de.sporenwerk.block.MutagenResonanceDampenerBlock;" if False else "import de.sporenwerk.block.InfestedTerrainBlock;",
                   "Kristallpirscher block imports")
    entity = entity.replace(
        "import de.sporenwerk.block.InfestedTerrainBlock;",
        "import de.sporenwerk.block.InfestedTerrainBlock;\nimport de.sporenwerk.block.MutagenResonanceDampenerBlock;",
        1
    )
old_check = "if (level().getBlockState(pos).is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())) {"
new_check = """BlockState dampenerState = level().getBlockState(pos);
            if (dampenerState.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                    && dampenerState.getValue(MutagenResonanceDampenerBlock.POWERED)) {"""
if old_check in entity:
    entity = entity.replace(old_check, new_check, 1)
elif new_check not in entity:
    raise SystemExit("Cannot require the resonance dampener to be powered before suppressing a pulse")
entity_path.write_text(entity, encoding="utf-8")

# Add both active faces to the visual contact sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = '    ("mutagen_resonanzdaempfer_side", "Resonanzdämpfer Seite"),'
addition = anchor + '\n' + \
    '    ("mutagen_resonanzdaempfer_top_active", "Resonanzdämpfer AN oben"),\n' + \
    '    ("mutagen_resonanzdaempfer_side_active", "Resonanzdämpfer AN Seite"),'
if "mutagen_resonanzdaempfer_top_active" not in preview:
    require_anchor(preview, anchor, "dampener visual preview entries")
    preview_path.write_text(preview.replace(anchor, addition, 1), encoding="utf-8")

# Update existing dampener regression to expect the powered state and two-model mapping.
test_path = ROOT / "tools/test_mutagen_resonance_dampener.py"
test = test_path.read_text(encoding="utf-8")
test = test.replace(
    'require(state["variants"][""]["model"] == "sporenwerk:block/mutagen_resonanzdaempfer",\n        "blockstate must point to dampener model")',
    'require(state["variants"]["powered=false"]["model"] == "sporenwerk:block/mutagen_resonanzdaempfer"\n        and state["variants"]["powered=true"]["model"] == "sporenwerk:block/mutagen_resonanzdaempfer_active",\n        "both redstone states must map to separate dampener models")'
)
test_path.write_text(test, encoding="utf-8")

# Version and release notes.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.36.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.36.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """- **Redstone-Schaltung:** Der Mutagen-Resonanzdämpfer unterdrückt Kristallpirscher-Impulse nur, wenn Redstone anliegt. Ohne Signal bleibt er dunkel und inaktiv.
- **AUS/AN visuell unterscheidbar:** Eigene Modell-/Texturkombinationen zeigen den Zustand; der aktive Dämpfer leuchtet und sein Resonanzkern hebt sich deutlich ab.
- **Chunk-sichere Gegenwehr:** Der Schutzbereich wird nur beim Beginn und Ende der Warnphase geprüft. Beim Einschalten direkt neben bestehendem Redstone wird der Zustand sofort synchronisiert.
- **Fortschrittspfad erhalten:** Das Rezept verlangt weiterhin den vom Kristallpirscher fallengelassenen Resonanzsplitter zusätzlich zu Eisen, Redstone, Amethyst und Mutagenkernkristall.

"""
if "## Version 1.36.0 — Kristallpirscher-Beute und Resonanzforschung" in readme:
    marker = "## Version 1.36.0 — Kristallpirscher-Beute und Resonanzforschung"
    idx = readme.find(marker) + len(marker)
    # Insert the dampener bullets into the existing 1.36.0 section, never create a duplicate version heading.
    next_heading = readme.find("\n## Version ", idx)
    if next_heading < 0:
        next_heading = len(readme)
    if "Redstone-Schaltung" not in readme[idx:next_heading]:
        readme = readme[:idx] + "\n\n" + section + readme[idx:next_heading].lstrip("\n") + readme[next_heading:]
else:
    raise SystemExit("Cannot find existing 1.36.0 resonance-shard release notes")
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.36.0 — Kristallpirscher-Beute speist die Resonanzforschung.**",
    "**Aktueller Entwicklungsstand: 1.36.0 — Resonanzsplitter-Fortschritt und redstone-gesteuerter Dämpfer.**"
)
readme_path.write_text(readme, encoding="utf-8")
print("Resonance dampener is now redstone-controlled with distinct off/on models, conditional light, active-only suppression, and 1.36.0 notes.")
