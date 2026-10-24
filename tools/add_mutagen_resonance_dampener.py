#!/usr/bin/env python3
"""Add a craftable, chunk-safe Mutagen Resonance Dampener for 1.34.0."""
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


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def require_anchor(text, anchor, label):
    if anchor not in text:
        raise SystemExit(f"Cannot add Mutagen Resonance Dampener: missing {label} anchor")


def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    require_anchor(text, old, label)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Register the block and its placeable item beside the Mutagen Field Control Station.
blocks_path = SRC / "registry/ModBlocks.java"
blocks = blocks_path.read_text(encoding="utf-8")
if "MUTAGEN_RESONANZDAEMPFER" not in blocks:
    station_import = "import de.sporenwerk.block.MutagenFieldControlStationBlock;"
    require_anchor(blocks, station_import, "control-station import")
    blocks = blocks.replace(
        station_import,
        station_import + "\nimport de.sporenwerk.block.MutagenResonanceDampenerBlock;",
        1
    )
    station_block = """    public static final RegistryObject<Block> MUTAGENFELD_KONTROLLSTATION = BLOCKS.register("mutagenfeld_kontrollstation",
            () -> new MutagenFieldControlStationBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(4.5f, 9.0f).requiresCorrectToolForDrops().sound(SoundType.AMETHYST)));"""
    dampener_block = station_block + """

    public static final RegistryObject<Block> MUTAGEN_RESONANZDAEMPFER = BLOCKS.register("mutagen_resonanzdaempfer",
            () -> new MutagenResonanceDampenerBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(4.5f, 9.0f).requiresCorrectToolForDrops().lightLevel(state -> 7)
                    .sound(SoundType.AMETHYST)));"""
    require_anchor(blocks, station_block, "control-station block registration")
    blocks = blocks.replace(station_block, dampener_block, 1)

    station_item = '        ModItems.ITEMS.register("mutagenfeld_kontrollstation", () -> new net.minecraft.world.item.BlockItem(MUTAGENFELD_KONTROLLSTATION.get(), new Item.Properties()));'
    dampener_item = station_item + '\n        ModItems.ITEMS.register("mutagen_resonanzdaempfer", () -> new net.minecraft.world.item.BlockItem(MUTAGEN_RESONANZDAEMPFER.get(), new Item.Properties()));'
    require_anchor(blocks, station_item, "control-station block item")
    blocks = blocks.replace(station_item, dampener_item, 1)
    blocks_path.write_text(blocks, encoding="utf-8")

write("src/main/java/de/sporenwerk/block/MutagenResonanceDampenerBlock.java", """
package de.sporenwerk.block;

import net.minecraft.world.level.block.Block;

/**
 * A costly, always-on resonator that dampens Kristallpirscher pulses nearby.
 * Its light and ring pattern mark the protected construction area.
 */
public final class MutagenResonanceDampenerBlock extends Block {
    public MutagenResonanceDampenerBlock(Properties properties) {
        super(properties);
    }
}
""")

# The cube-column model keeps normal collision/selection and uses its own high-contrast pixel art.
write("src/main/resources/assets/sporenwerk/blockstates/mutagen_resonanzdaempfer.json", """
{
  "variants": {
    "": { "model": "sporenwerk:block/mutagen_resonanzdaempfer" }
  }
}
""")
write("src/main/resources/assets/sporenwerk/models/block/mutagen_resonanzdaempfer.json", """
{
  "parent": "minecraft:block/cube_column",
  "textures": {
    "end": "sporenwerk:block/mutagen_resonanzdaempfer_top",
    "side": "sporenwerk:block/mutagen_resonanzdaempfer_side"
  }
}
""")
write("src/main/resources/assets/sporenwerk/models/item/mutagen_resonanzdaempfer.json", """
{
  "parent": "sporenwerk:block/mutagen_resonanzdaempfer"
}
""")

# Draw an unmistakable 16x16 pixel-art tuning device: concentric cyan resonance rings,
# a warm copper frame, and a dark crystalline housing. No external images are required.
TEXTURES.mkdir(parents=True, exist_ok=True)

def top_texture():
    im = Image.new("RGBA", (16, 16), (20, 34, 39, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 15, 15), fill=(32, 48, 51, 255), outline=(12, 24, 29, 255))
    d.rectangle((1, 1, 14, 14), fill=(25, 40, 44, 255), outline=(143, 105, 61, 255))
    d.rectangle((3, 3, 12, 12), fill=(12, 27, 34, 255), outline=(50, 117, 119, 255))
    d.rectangle((5, 5, 10, 10), fill=(30, 113, 117, 255), outline=(61, 217, 201, 255))
    d.rectangle((4, 4, 11, 11), outline=(39, 88, 91, 255))
    d.rectangle((6, 6, 9, 9), fill=(43, 209, 197, 255))
    d.line([(6, 4), (9, 4)], fill=(78, 167, 156, 255), width=1)
    d.point((5, 8), fill=(120, 243, 216, 255))
    d.point((10, 8), fill=(120, 243, 216, 255))
    d.rectangle((7, 7, 8, 8), fill=(224, 255, 218, 255))
    # The four copper terminals make the top readable at Minecraft's native pixel scale.
    for x, y in ((2, 2), (12, 2), (2, 12), (12, 12)):
        d.rectangle((x, y, x+1, y+1), fill=(198, 140, 72, 255))
    d.line([(1, 7), (3, 7), (4, 8), (3, 9), (1, 9)], fill=(66, 195, 190, 255), width=1)
    d.line([(14, 7), (12, 7), (11, 8), (12, 9), (14, 9)], fill=(66, 195, 190, 255), width=1)
    return im

def side_texture():
    im = Image.new("RGBA", (16, 16), (20, 31, 36, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 15, 15), fill=(29, 43, 47, 255), outline=(11, 21, 27, 255))
    d.rectangle((1, 1, 14, 3), fill=(55, 69, 69, 255))
    d.rectangle((1, 12, 14, 14), fill=(35, 46, 47, 255))
    d.rectangle((2, 4, 13, 11), fill=(16, 30, 36, 255), outline=(139, 97, 59, 255))
    d.rectangle((4, 5, 11, 10), fill=(27, 84, 91, 255), outline=(54, 167, 166, 255))
    d.rectangle((5, 6, 10, 9), fill=(27, 135, 136, 255))
    d.rectangle((6, 7, 9, 8), fill=(72, 232, 210, 255))
    d.point((7, 7), fill=(236, 255, 212, 255))
    d.point((8, 8), fill=(236, 255, 212, 255))
    # Fine parallel bars suggest a calibrated dampening coil.
    for x in (2, 4, 11, 13):
        d.line([(x, 5), (x, 10)], fill=(196, 142, 77, 255), width=1)
    d.line([(3, 2), (12, 2)], fill=(76, 199, 188, 255), width=1)
    d.line([(3, 13), (12, 13)], fill=(76, 199, 188, 255), width=1)
    return im

for filename, image in (
    ("mutagen_resonanzdaempfer_top.png", top_texture()),
    ("mutagen_resonanzdaempfer_side.png", side_texture()),
):
    path = TEXTURES / filename
    image.save(path, optimize=True)
    with Image.open(path) as check:
        rgba = check.convert("RGBA")
        if rgba.size != (16, 16) or any(pixel[3] != 255 for pixel in rgba.getdata()):
            raise SystemExit(f"{filename} must be a fully opaque 16x16 block texture")
        if len(set(rgba.getdata())) < 12:
            raise SystemExit(f"{filename} has insufficient pixel-art contrast")

# Put the dampener directly into the existing creative tab near the control station.
replace_once(
    SRC / "registry/ModCreativeTabs.java",
    "output.accept(ModBlocks.MUTAGENFELD_KONTROLLSTATION.get());",
    "output.accept(ModBlocks.MUTAGENFELD_KONTROLLSTATION.get());\n                        output.accept(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get());",
    "control station creative-tab entry"
)

# The dampener needs no tile entity or recurring ticker. The hostile mob queries this
# bounded area only when beginning a pulse and once at release (not on every tick).
entity_path = SRC / "entity/KristallpirscherEntity.java"
entity = entity_path.read_text(encoding="utf-8")
if "private boolean isResonanceDamped()" not in entity:
    start = """        if (resonanceWindup <= 0) {
            resonanceWindup = RESONANCE_WINDUP_TICKS;"""
    replacement = """        if (resonanceWindup <= 0) {
            if (isResonanceDamped()) return;
            resonanceWindup = RESONANCE_WINDUP_TICKS;"""
    require_anchor(entity, start, "resonance windup start")
    entity = entity.replace(start, replacement, 1)

    release_anchor = """        serverLevel.sendParticles(ParticleTypes.CRIT,
                getX(), getY() + 0.65D, getZ(), 24, 0.7D, 0.25D, 0.7D, 0.07D);"""
    release_replacement = """        // A dampener installed during the windup can still cancel the pulse at release.
        if (isResonanceDamped()) {
            resonanceWindup = 0;
            return;
        }
        serverLevel.sendParticles(ParticleTypes.CRIT,
                getX(), getY() + 0.65D, getZ(), 24, 0.7D, 0.25D, 0.7D, 0.07D);"""
    require_anchor(entity, release_anchor, "resonance pulse release")
    entity = entity.replace(release_anchor, release_replacement, 1)

    method_anchor = """    private boolean isOnHighTierSoil() {
        BlockState soil = level().getBlockState(blockPosition().below());"""
    method_replacement = """    /**
     * Check a small loaded-block area only when starting or releasing a pulse.
     * No per-tick block scan and no chunk forcing: unloaded positions are skipped.
     */
    private boolean isResonanceDamped() {
        BlockPos origin = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(
                origin.offset(-6, -2, -6), origin.offset(6, 2, 6))) {
            if (!level().hasChunkAt(pos)) continue;
            if (level().getBlockState(pos).is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())) {
                return true;
            }
        }
        return false;
    }

    private boolean isOnHighTierSoil() {
        BlockState soil = level().getBlockState(blockPosition().below());"""
    require_anchor(entity, method_anchor, "high-tier soil predicate")
    entity = entity.replace(method_anchor, method_replacement, 1)
    entity_path.write_text(entity, encoding="utf-8")

# Survival crafting: a costly field-engineering countermeasure uses crystal and calibrated coils.
write("src/main/resources/data/sporenwerk/recipes/mutagen_resonanzdaempfer.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["IRI", "ACA", "IRI"],
  "key": {
    "I": {"item": "minecraft:iron_ingot"},
    "R": {"item": "minecraft:redstone"},
    "A": {"item": "minecraft:amethyst_block"},
    "C": {"item": "sporenwerk:mutagenkernkristall"}
  },
  "result": {"item": "sporenwerk:mutagen_resonanzdaempfer", "count": 1}
}
""")
write("src/main/resources/data/sporenwerk/advancements/recipes/misc/mutagen_resonanzdaempfer.json", """
{
  "parent": "minecraft:recipes/root",
  "rewards": {"recipes": ["sporenwerk:mutagen_resonanzdaempfer"]},
  "criteria": {
    "has_iron": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:iron_ingot"]}]}
    },
    "has_redstone": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:redstone"]}]}
    },
    "has_amethyst": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:amethyst_block"]}]}
    },
    "has_mutagen_core": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["sporenwerk:mutagenkernkristall"]}]}
    }
  },
  "requirements": [["has_iron"], ["has_redstone"], ["has_amethyst"], ["has_mutagen_core"]]
}
""")
write("src/main/resources/data/sporenwerk/loot_tables/blocks/mutagen_resonanzdaempfer.json", """
{
  "type": "minecraft:block",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        { "type": "minecraft:item", "name": "sporenwerk:mutagen_resonanzdaempfer" }
      ]
    }
  ]
}
""")

# Preserve DE/EN locale files and add distinct block/item names.
for filename, values in {
    "de_de.json": {
        "block.sporenwerk.mutagen_resonanzdaempfer": "Mutagen-Resonanzdämpfer",
        "item.sporenwerk.mutagen_resonanzdaempfer": "Mutagen-Resonanzdämpfer"
    },
    "en_us.json": {
        "block.sporenwerk.mutagen_resonanzdaempfer": "Mutagen Resonance Dampener",
        "item.sporenwerk.mutagen_resonanzdaempfer": "Mutagen Resonance Dampener"
    }
}.items():
    locale_path = ASSETS / "lang" / filename
    locale = json.loads(locale_path.read_text(encoding="utf-8"))
    locale.update(values)
    locale_path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Add both faces to the pixel-art contact sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = '    ("sporenabwehr_active", "Sporenabwehr AN"),'
addition = anchor + '\n' + \
    '    ("mutagen_resonanzdaempfer_top", "Resonanzdämpfer oben"),\n' + \
    '    ("mutagen_resonanzdaempfer_side", "Resonanzdämpfer Seite"),'
if "mutagen_resonanzdaempfer_top" not in preview:
    require_anchor(preview, anchor, "spore-ward preview entry")
    preview_path.write_text(preview.replace(anchor, addition, 1), encoding="utf-8")

# Advance the release without deleting previous history.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.34.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.34.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.34.0 — Mutagen-Resonanzdämpfer: technische Gegenwehr

- **Baubare Schutzzone:** Der herstellbare Resonanzdämpfer erzeugt Licht und markiert einen Bereich, in dem der Kristallpirscher seinen Resonanzimpuls nicht beginnen oder freisetzen kann.
- **Knappe, sichere Abfragen:** Der Gegner prüft den kleinen Schutzbereich nur beim Start und am Ende der Warnphase. Nicht geladene Chunks werden übersprungen; das Gerät erzwingt keine Chunk-Ladung und benötigt keinen tickenden Block-Entity-Prozess.
- **Reaktive Gegenwehr:** Wird der Dämpfer während der 30-Tick-Aufladung aufgestellt, bricht er den Impuls beim Auslösen ab. Spieler können also auf die Warnung reagieren, statt schon beim Windup festgelegt zu sein.
- **Survival-Fortschritt:** Das Rezept verlangt Eisen, Redstone, einen Amethystblock und einen Mutagenkernkristall. Eigene Blocktexturen, Modell, Loot-Tabelle, Fortschrittsfreigabe, DE/EN-Namen und Regressionstests sind enthalten.

"""
if "## Version 1.34.0 — Mutagen-Resonanzdämpfer" not in readme:
    marker = "## Version 1.33.0 — Kristallpirscher: Resonanzimpuls"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.33.0 resonance release notes")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.33.0 — telegraphierter Resonanzimpuls des Kristallpirschers.**",
    "**Aktueller Entwicklungsstand: 1.34.0 — baubare Resonanzdämpfung für Hochmutagen-Anlagen.**"
).replace("## Aktueller Schwerpunkt — 1.33.0", "## Aktueller Schwerpunkt — 1.34.0")
readme_path.write_text(readme, encoding="utf-8")

print("Mutagen Resonance Dampener block, pixel art, recipe, chunk-safe pulse suppression, locale, and 1.34.0 notes generated.")
