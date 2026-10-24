#!/usr/bin/env python3
"""Add a redstone-driven warning siren that pairs with the Mutagen hazard comparator."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def replace_once(path, old, new, label):
    content = path.read_text(encoding="utf-8")
    if new in content:
        return
    if old not in content:
        raise SystemExit(f"Cannot add Mutagen warning siren: expected {label} anchor was not found")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


# Register a dedicated redstone device beside the existing control station.
replace_once(
    SRC / "registry/ModBlocks.java",
    "import de.sporenwerk.block.MutagenFieldControlStationBlock;",
    "import de.sporenwerk.block.MutagenFieldControlStationBlock;\nimport de.sporenwerk.block.MutagenWarningSirenBlock;",
    "control-station import"
)
station_registration = """    public static final RegistryObject<Block> MUTAGENFELD_KONTROLLSTATION = BLOCKS.register("mutagenfeld_kontrollstation",
            () -> new MutagenFieldControlStationBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(4.5f, 9.0f).requiresCorrectToolForDrops().sound(SoundType.AMETHYST)));"""
siren_registration = """    public static final RegistryObject<Block> MUTAGEN_WARNSIRENE = BLOCKS.register("mutagen_warnsirene",
            () -> new MutagenWarningSirenBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_RED)
                    .strength(3.5f, 6.0f).requiresCorrectToolForDrops().sound(SoundType.METAL)));"""
replace_once(SRC / "registry/ModBlocks.java", station_registration,
             station_registration + "\n\n" + siren_registration, "control-station block registration")

station_item = '        ModItems.ITEMS.register("mutagenfeld_kontrollstation", () -> new net.minecraft.world.item.BlockItem(MUTAGENFELD_KONTROLLSTATION.get(), new Item.Properties()));'
siren_item = '        ModItems.ITEMS.register("mutagen_warnsirene", () -> new net.minecraft.world.item.BlockItem(MUTAGEN_WARNSIRENE.get(), new Item.Properties()));'
replace_once(SRC / "registry/ModBlocks.java", station_item,
             station_item + "\n" + siren_item, "control-station block item")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
anchor = "output.accept(ModBlocks.MUTAGENFELD_KONTROLLSTATION.get());"
addition = "output.accept(ModBlocks.MUTAGEN_WARNSIRENE.get());"
if addition not in creative:
    if anchor not in creative:
        raise SystemExit("Cannot locate the control station creative-tab entry")
    creative_path.write_text(creative.replace(anchor, anchor + "\n                        " + addition, 1), encoding="utf-8")

write("src/main/java/de/sporenwerk/block/MutagenWarningSirenBlock.java", """
package de.sporenwerk.block;

import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;

/**
 * Compact redstone alarm for Mutagen facilities.
 * It plays a single warning tone only when the input changes from off to on.
 */
public final class MutagenWarningSirenBlock extends Block {
    public static final BooleanProperty POWERED = BooleanProperty.create("powered");

    public MutagenWarningSirenBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(POWERED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(POWERED);
    }

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos,
                                Block neighborBlock, BlockPos neighborPos, boolean moving) {
        if (level.isClientSide) return;
        boolean inputPowered = level.hasNeighborSignal(pos);
        boolean wasPowered = state.getValue(POWERED);
        if (inputPowered == wasPowered) return;

        level.setBlock(pos, state.setValue(POWERED, inputPowered), 3);
        // Rising-edge only: changes to an already active comparator signal do not spam audio.
        if (inputPowered) {
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BELL.value(),
                    SoundSource.BLOCKS, 0.9F, 0.62F);
        }
    }
}
""")

# Separate inactive and active full-cube models make the redstone state obvious.
blockstates = {
    "variants": {
        "powered=false": {"model": "sporenwerk:block/mutagen_warnsirene"},
        "powered=true": {"model": "sporenwerk:block/mutagen_warnsirene_active"}
    }
}
write("src/main/resources/assets/sporenwerk/blockstates/mutagen_warnsirene.json",
      json.dumps(blockstates, indent=2) + "\n")
for model_name, texture_name in (
    ("mutagen_warnsirene", "mutagen_warnsirene"),
    ("mutagen_warnsirene_active", "mutagen_warnsirene_active")
):
    write(f"src/main/resources/assets/sporenwerk/models/block/{model_name}.json",
          json.dumps({"parent": "minecraft:block/cube_all",
                      "textures": {"all": f"sporenwerk:block/{texture_name}"}}, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/item/mutagen_warnsirene.json",
      json.dumps({"parent": "sporenwerk:block/mutagen_warnsirene"}, indent=2) + "\n")

# Hand-built opaque 16x16 Minecraft pixel textures, one for idle and a visually distinct alarm.
tex_dir = ASSETS / "textures/block"
tex_dir.mkdir(parents=True, exist_ok=True)

def make_siren(active):
    image = Image.new("RGBA", (16, 16), (30, 36, 35, 255))
    d = ImageDraw.Draw(image)
    d.rectangle((1, 1, 14, 14), fill=(40, 49, 46, 255), outline=(101, 113, 103, 255))
    d.rectangle((2, 2, 13, 3), fill=(63, 75, 66, 255))
    d.rectangle((3, 5, 12, 12), fill=(18, 24, 25, 255), outline=(94, 106, 99, 255))
    d.rectangle((4, 6, 11, 10), fill=(116, 47, 37, 255) if active else (111, 91, 41, 255))
    d.rectangle((5, 5, 10, 6), fill=(221, 78, 51, 255) if active else (184, 145, 59, 255))
    d.rectangle((6, 7, 9, 9), fill=(255, 192, 94, 255) if active else (224, 183, 82, 255))
    d.rectangle((2, 12, 13, 13), fill=(31, 39, 37, 255))
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        d.point((x, y), fill=(195, 166, 91, 255))
    if active:
        d.rectangle((0, 6, 1, 9), fill=(255, 64, 40, 255))
        d.rectangle((14, 6, 15, 9), fill=(255, 64, 40, 255))
        d.point((7, 4), fill=(255, 236, 162, 255))
        d.point((8, 4), fill=(255, 236, 162, 255))
    else:
        d.point((7, 4), fill=(148, 138, 94, 255))
    return image

for name, active in (("mutagen_warnsirene", False), ("mutagen_warnsirene_active", True)):
    path = tex_dir / f"{name}.png"
    make_siren(active).save(path, optimize=True)
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
        if rgba.size != (16, 16) or any(px[3] != 255 for px in rgba.getdata()):
            raise SystemExit(f"{name} texture must be an opaque 16x16 PNG")

# Survival recipe: redstone drives the alarm; copper and a note block form the housing/resonator.
write("src/main/resources/data/sporenwerk/recipes/mutagen_warnsirene.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["CRC", "RNR", "CRC"],
  "key": {
    "C": {"item": "minecraft:copper_ingot"},
    "R": {"item": "minecraft:redstone"},
    "N": {"item": "minecraft:note_block"}
  },
  "result": {"item": "sporenwerk:mutagen_warnsirene", "count": 1}
}
""")
write("src/main/resources/data/sporenwerk/advancements/recipes/misc/mutagen_warnsirene.json", """
{
  "parent": "minecraft:recipes/root",
  "rewards": {"recipes": ["sporenwerk:mutagen_warnsirene"]},
  "criteria": {
    "has_copper": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:copper_ingot"]}]}
    },
    "has_redstone": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:redstone"]}]}
    },
    "has_note_block": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:note_block"]}]}
    }
  },
  "requirements": [["has_copper"], ["has_redstone"], ["has_note_block"]]
}
""")

# Add localizations without dropping existing keys.
for filename, values in {
    "de_de.json": {
        "block.sporenwerk.mutagen_warnsirene": "Mutagen-Warnsirene",
        "item.sporenwerk.mutagen_warnsirene": "Mutagen-Warnsirene"
    },
    "en_us.json": {
        "block.sporenwerk.mutagen_warnsirene": "Mutagen Warning Siren",
        "item.sporenwerk.mutagen_warnsirene": "Mutagen Warning Siren"
    }
}.items():
    locale_path = ASSETS / "lang" / filename
    data = json.loads(locale_path.read_text(encoding="utf-8"))
    data.update(values)
    locale_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Make both visual states visible in the generated art QA sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
preview_anchor = '    ("sporenabwehr_active", "Sporenabwehr AN"),'
preview_addition = preview_anchor + '\n' + \
    '    ("mutagen_warnsirene", "Warnsirene AUS"),\n' + \
    '    ("mutagen_warnsirene_active", "Warnsirene AN"),'
if "mutagen_warnsirene_active" not in preview:
    if preview_anchor not in preview:
        raise SystemExit("Cannot locate the active Spore Ward entry in art preview")
    preview_path.write_text(preview.replace(preview_anchor, preview_addition, 1), encoding="utf-8")

# The workflow already runs the 1.28.0 comparator patch directly before this patch.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.29.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.29.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.29.0 — Redstone-Warnsirene

- **Alarmgerät:** Die neue craftbare Mutagen-Warnsirene reagiert auf Redstone-Eingänge und zeigt den Zustand über zwei eigenständige Pixeltexturen (Aus/Alarm) an.
- **Warnton ohne Spam:** Der Signalwechsel von AUS auf AN spielt einen kurzen Warnton. Solange das Eingangssignal aktiv bleibt, wird der Ton nicht bei jeder Nachbaraktualisierung erneut ausgelöst.
- **Zusammenspiel mit der Kontrollstation:** Verbinde den Comparator-Ausgang der Mutagenfeld-Kontrollstation über Redstone-Staub mit der Sirene. Nach einem Stationsscan mit Gefahrenwert über 0 wird die Sirene ausgelöst.
- **Survival und Qualitätssicherung:** Rezept, Fortschrittsfreigabe, deutsche/englische Namen, blockstate/model mapping, deckende 16×16-Texturen und Regressionstests sind enthalten.

Der Warnton löst einmal beim Einschalten aus; die Sirene spielt keine Endlosschleife. Automatische Tests ersetzen keinen manuellen Funktionstest im Minecraft-Client.

"""
if "## Version 1.29.0 — Redstone-Warnsirene" not in readme:
    marker = "## Version 1.28.0 — Redstone-Gefahrenausgang der Kontrollstation"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.28.0 release notes to preserve version history")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.28.0 — Mutagenfelder, die sich unterscheiden und automatisieren lassen.**",
    "**Aktueller Entwicklungsstand: 1.29.0 — Mutagenfelder mit Comparator und Warnsirene.**"
).replace("## Aktueller Schwerpunkt — 1.28.0", "## Aktueller Schwerpunkt — 1.29.0")
if "Mutagen-Warnsirene" not in readme[:2000]:
    readme = readme.replace(
        "- Ein Scan an der Mutagenfeld-Kontrollstation aktualisiert einen Comparator-Gefahrenwert von 0 bis 15, ohne Welt-Scans bei jedem Redstone-Tick auszulösen.",
        "- Ein Scan an der Mutagenfeld-Kontrollstation aktualisiert einen Comparator-Gefahrenwert von 0 bis 15, ohne Welt-Scans bei jedem Redstone-Tick auszulösen.\n- Die Mutagen-Warnsirene reagiert sichtbar und akustisch auf ein Redstone-Alarmsignal."
    )
readme_path.write_text(readme, encoding="utf-8")
print("Mutagen warning siren, recipes, pixel textures, localization, tests hooks, and version 1.29.0 generated.")
