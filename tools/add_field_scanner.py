#!/usr/bin/env python3
"""Add a survival-craftable field scanner and verify its field-reading contract."""
from pathlib import Path
from PIL import Image, ImageDraw
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve()
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def replace_once(rel, old, new, label):
    path = ROOT / rel
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Cannot apply {label}: expected source context not found in {rel}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# Register the portable analysis instrument only after the mutagen research chain exists.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
if "import de.sporenwerk.item.FeldscannerItem;" not in items:
    anchor = "import de.sporenwerk.item.MutageneSporenItem;"
    if anchor not in items:
        raise SystemExit("Cannot locate the Mutagenic Spores item import for the field scanner")
    items = items.replace(anchor, anchor + "\nimport de.sporenwerk.item.FeldscannerItem;", 1)
field_anchor = '    public static final RegistryObject<Item> MUTAGENE_SPOREN = ITEMS.register("mutagene_sporen", () -> new MutageneSporenItem(new Item.Properties().stacksTo(64)));'
field = '    public static final RegistryObject<Item> FELDSCANNER = ITEMS.register("feldscanner", () -> new FeldscannerItem(new Item.Properties().stacksTo(1)));'
if "FELDSCANNER" not in items:
    if field_anchor not in items:
        raise SystemExit("Cannot locate Mutagenic Spores registration for the field scanner")
    items = items.replace(field_anchor, field_anchor + "\n" + field, 1)
items_path.write_text(items, encoding="utf-8")

# Include the scanner beside the research tools in the existing creative catalogue.
creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
if "output.accept(ModItems.FELDSCANNER.get());" not in creative:
    anchor = "output.accept(ModItems.MUTAGENE_SPOREN.get());"
    if anchor not in creative:
        raise SystemExit("Cannot locate Mutagenic Spores in the creative catalogue")
    creative = creative.replace(anchor, anchor + "\n                        output.accept(ModItems.FELDSCANNER.get());", 1)
creative_path.write_text(creative, encoding="utf-8")

write("src/main/java/de/sporenwerk/item/FeldscannerItem.java", """
package de.sporenwerk.item;

import de.sporenwerk.infection.MutationField;
import de.sporenwerk.infection.MutationAnchorData;
import de.sporenwerk.infection.MutationNodeData;
import de.sporenwerk.registry.ModBlocks;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/**
 * Handheld, non-destructive instrument for reading the mod's authoritative field data.
 * The scan runs on the server so client-side guesses cannot report stale or fake intensity.
 */
public final class FeldscannerItem extends Item {
    public FeldscannerItem(Properties properties) { super(properties); }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (!(level instanceof ServerLevel serverLevel)) return InteractionResult.PASS;

        Player player = context.getPlayer();
        if (player == null) return InteractionResult.PASS;

        BlockPos pos = context.getClickedPos();
        BlockState state = serverLevel.getBlockState(pos);
        Component reading;

        if (state.is(ModBlocks.INFEKTIONSHERD.get())) {
            boolean active = MutationNodeData.get(serverLevel).isActive(pos);
            if (active) {
                int strength = MutationField.mutagenStrengthAt(serverLevel, pos);
                reading = Component.translatable("message.sporenwerk.scanner.node_active",
                        strength, MutationField.RADIUS, MutationField.INFECTION_HALF_HEIGHT)
                        .withStyle(ChatFormatting.LIGHT_PURPLE);
            } else {
                reading = Component.translatable("message.sporenwerk.scanner.node_inactive")
                        .withStyle(ChatFormatting.GRAY);
            }
        } else if (state.is(ModBlocks.MUTATION_ANCHOR.get())) {
            reading = Component.translatable("message.sporenwerk.scanner.anchor",
                    MutationAnchorData.FIELD_RADIUS, MutationAnchorData.FIELD_HALF_HEIGHT)
                    .withStyle(ChatFormatting.AQUA);
        } else if (state.is(ModBlocks.SPORENRESISTENTER_BLOCK.get())) {
            reading = Component.translatable("message.sporenwerk.scanner.barrier")
                    .withStyle(ChatFormatting.GREEN);
        } else if (state.is(ModBlocks.MUTAGEN_BODEN.get())) {
            int strength = MutationField.mutagenStrengthAt(serverLevel, pos);
            String key = strength > 0
                    ? "message.sporenwerk.scanner.terrain_active"
                    : "message.sporenwerk.scanner.terrain_cooling";
            reading = Component.translatable(key, strength)
                    .withStyle(strength > 0 ? ChatFormatting.RED : ChatFormatting.GRAY);
        } else {
            int strength = MutationField.mutagenStrengthAt(serverLevel, pos);
            if (strength > 0) {
                reading = Component.translatable("message.sporenwerk.scanner.field", strength)
                        .withStyle(strength >= 3 ? ChatFormatting.LIGHT_PURPLE
                                : strength == 2 ? ChatFormatting.GOLD : ChatFormatting.YELLOW);
            } else {
                reading = Component.translatable("message.sporenwerk.scanner.clean")
                        .withStyle(ChatFormatting.GRAY);
            }
        }

        player.displayClientMessage(reading, false);
        return InteractionResult.SUCCESS;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip,
                                TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.feldscanner.1")
                .withStyle(ChatFormatting.AQUA));
        tooltip.add(Component.translatable("tooltip.sporenwerk.feldscanner.2")
                .withStyle(ChatFormatting.GRAY));
        super.appendHoverText(stack, level, tooltip, flag);
    }
}
""")

# Survival recipe: modest iron/copper/redstone hardware with a glass readout and real extract.
write("src/main/resources/data/sporenwerk/recipes/feldscanner.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": [
    " C ",
    "RGM",
    " I "
  ],
  "key": {
    "C": { "item": "minecraft:copper_ingot" },
    "R": { "item": "minecraft:redstone" },
    "G": { "item": "minecraft:glass_pane" },
    "M": { "item": "sporenwerk:mutagenextrakt" },
    "I": { "item": "minecraft:iron_ingot" }
  },
  "result": {
    "item": "sporenwerk:feldscanner",
    "count": 1
  }
}
""")
write("src/main/resources/assets/sporenwerk/models/item/feldscanner.json", """
{
  "parent": "minecraft:item/generated",
  "textures": {
    "layer0": "sporenwerk:item/feldscanner"
  }
}
""")

# Deliberately hand-authored 16x16 pixel art: no smooth gradients or oversized item render.
texture_path = ASSETS / "textures/item/feldscanner.png"
texture_path.parent.mkdir(parents=True, exist_ok=True)
image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
ink = (25, 32, 29, 255)
edge = (68, 82, 69, 255)
steel = (132, 145, 128, 255)
highlight = (190, 199, 168, 255)
screen_dark = (18, 49, 43, 255)
screen = (40, 125, 104, 255)
signal = (121, 232, 181, 255)
amber = (224, 174, 67, 255)
red = (164, 55, 59, 255)
# Chunky casing / grip
draw.polygon([(5, 1), (10, 1), (13, 4), (13, 11), (11, 14),
              (10, 15), (5, 15), (3, 13), (2, 11), (2, 4)], fill=ink)
draw.polygon([(5, 2), (10, 2), (12, 4), (12, 11), (10, 13),
              (5, 13), (3, 11), (3, 4)], fill=edge)
draw.rectangle((4, 3, 10, 4), fill=steel)
draw.rectangle((4, 5, 11, 9), fill=screen_dark)
draw.rectangle((5, 6, 10, 8), fill=screen)
draw.rectangle((5, 6, 6, 6), fill=signal)
draw.rectangle((7, 7, 10, 7), fill=signal)
draw.rectangle((5, 8, 8, 8), fill=(30, 91, 77, 255))
# Calibration marks and one amber warning lamp
draw.rectangle((4, 10, 5, 10), fill=highlight)
draw.rectangle((7, 10, 9, 10), fill=steel)
draw.rectangle((10, 10, 10, 10), fill=amber)
draw.rectangle((5, 12, 9, 12), fill=ink)
draw.rectangle((6, 13, 8, 14), fill=steel)
draw.rectangle((7, 13, 7, 13), fill=red)
image.save(texture_path, optimize=True)

# Both locales are mandatory: missing translations are treated as a release defect.
translations = {
    "de_de.json": {
        "item.sporenwerk.feldscanner": "Feldscanner",
        "tooltip.sporenwerk.feldscanner.1": "Rechtsklick auf einen Block, um ihn zu analysieren.",
        "tooltip.sporenwerk.feldscanner.2": "Liest den gespeicherten Zustand des Mutagenfeldes.",
        "message.sporenwerk.scanner.node_active": "Mutagenherd: AKTIV. Feldstärke %1$s/3; Radius %2$s, Höhe ±%3$s.",
        "message.sporenwerk.scanner.node_inactive": "Mutagenherd: INAKTIV. Keine Mutagenboni; bestehender Befall wird zurückgeführt.",
        "message.sporenwerk.scanner.anchor": "Mutationsanker: Heilzone aktiv (Radius %1$s, Höhe ±%2$s); unterdrückt Mutagenwirkung.",
        "message.sporenwerk.scanner.barrier": "Sporenresistenter Block erkannt. Er kann die direkte Ausbreitung begrenzen.",
        "message.sporenwerk.scanner.terrain_active": "Infizierter Boden erkannt. Aktive Feldstärke an dieser Position: %1$s/3.",
        "message.sporenwerk.scanner.terrain_cooling": "Rückführungsmarkierter Boden: Aktive Mutagenwirkung ist hier nicht mehr nachweisbar.",
        "message.sporenwerk.scanner.field": "Feldsignal erkannt: Stärke %1$s/3. Feldgebundene Pflanzenboni und Exposition sind aktiv.",
        "message.sporenwerk.scanner.clean": "Kein aktives Mutagenfeld am Ziel. Keine feldgebundenen Boni erkannt."
    },
    "en_us.json": {
        "item.sporenwerk.feldscanner": "Field Scanner",
        "tooltip.sporenwerk.feldscanner.1": "Right-click a block to analyze it.",
        "tooltip.sporenwerk.feldscanner.2": "Reads the authoritative stored state of a mutagen field.",
        "message.sporenwerk.scanner.node_active": "Mutagen node: ACTIVE. Field strength %1$s/3; radius %2$s, height ±%3$s.",
        "message.sporenwerk.scanner.node_inactive": "Mutagen node: INACTIVE. No mutagen bonuses; existing spread is being restored.",
        "message.sporenwerk.scanner.anchor": "Mutation anchor: healing zone active (radius %1$s, height ±%2$s); suppresses mutagen effects.",
        "message.sporenwerk.scanner.barrier": "Spore-resistant block detected. It can limit direct spread.",
        "message.sporenwerk.scanner.terrain_active": "Infested terrain detected. Active field strength here: %1$s/3.",
        "message.sporenwerk.scanner.terrain_cooling": "Restoration-marked terrain: no active mutagen effect is detected here.",
        "message.sporenwerk.scanner.field": "Field signal detected: strength %1$s/3. Field crop bonuses and exposure are active.",
        "message.sporenwerk.scanner.clean": "No active mutagen field at the target. No field-based bonuses detected."
    }
}
for locale, entries in translations.items():
    path = RES / "assets/sporenwerk/lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Bump the built artefact version and put the new feature at the head of the release notes.
build_path = ROOT / "build.gradle"
build_source = build_path.read_text(encoding="utf-8")
build_source, count = re.subn(r"version\s*=\s*['\"][^'\"]+['\"]",
                              "version = '1.12.0'", build_source, count=1)
if count != 1:
    raise SystemExit("Could not bump build.gradle to version 1.12.0")
build_path.write_text(build_source, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
heading = "## Version 1.12.0 — Feldscanner und Feldanalyse"
if heading not in readme:
    marker_match = re.search(r"^##\s+(?:Version\s+)?1\.7\.0\b.*$", readme, flags=re.MULTILINE)
    section = """## Version 1.12.0 — Feldscanner und Feldanalyse

- **Feldscanner:** Neues craftbares Survival-Werkzeug mit eigener 16×16-Pixeltextur.
- **Aussagekräftige Messungen:** Rechtsklick auf Blöcke meldet aktive oder inaktive Mutagenherde, Feldstärke, Heilanker, resistente Barrieren sowie frisch befallenen oder bereits abklingenden Boden.
- **Serverautorität:** Der Scanner liest denselben gespeicherten Quellstatus und dieselbe Feldstärke, die Pflanzenmutation und Terrain-Ausbreitung steuern; er erfindet keine clientseitigen Werte.
- **Spielintegration:** Rezept aus Kupfer, Redstone, Glasscheibe, Eisen und Mutagenextrakt, Eintrag im Kreativkatalog und vollständige deutsche/englische Texte.
- **Release-QA:** Eigener Feldscanner-Vertragstest, Prüfung von Modell/Textur/Rezept/Übersetzungen, Forge-Build, JAR-Inhalt und dedizierter Serverstart.

Wie bei den vorherigen Versionen ersetzt der automatisierte Server-Smoke-Test keinen vollständigen manuellen Sicht- und Funktionstest im Minecraft-Client.

"""

    if marker_match:
        readme = readme[:marker_match.start()] + section + readme[marker_match.start():]
    else:
        # The phenotype generator may create a compact history without a 1.7.0 heading.
        # Never abort the entire Forge build over release-note formatting.
        readme = section + readme
readme_path.write_text(readme, encoding="utf-8")

# Create a reproducible source/resource contract test inside the generated project.
write("tools/test_field_scanner.py", r'''
#!/usr/bin/env python3
"""Contract tests for field scanner registration, readings, recipe, art, and locale coverage."""
from pathlib import Path
from PIL import Image
import json
import re
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
src = root / "src/main/java/de/sporenwerk"
res = root / "src/main/resources"
assets = res / "assets/sporenwerk"

def require(condition, message):
    if not condition:
        raise SystemExit("Field scanner contract: " + message)

items = (src / "registry/ModItems.java").read_text(encoding="utf-8")
creative = (src / "registry/ModCreativeTabs.java").read_text(encoding="utf-8")
scanner_path = src / "item/FeldscannerItem.java"
scanner = scanner_path.read_text(encoding="utf-8")
field = (src / "infection/MutationField.java").read_text(encoding="utf-8")

require('register("feldscanner"' in items and "FeldscannerItem" in items,
        "field scanner must be registered as a real item")
require("output.accept(ModItems.FELDSCANNER.get())" in creative,
        "scanner must appear in the existing creative catalogue")
require("InteractionResult useOn(UseOnContext context)" in scanner,
        "right-click block analysis must use Minecraft's interaction API")
require("if (level.isClientSide) return InteractionResult.SUCCESS;" in scanner,
        "world reads must not be guessed on the client")
require("MutationField.mutagenStrengthAt(serverLevel, pos)" in scanner,
        "scan must reuse server-authoritative saved field strength")
for token in (
    "MutationNodeData.get(serverLevel).isActive(pos)",
    "MutationAnchorData.FIELD_RADIUS, MutationAnchorData.FIELD_HALF_HEIGHT",
    "ModBlocks.INFEKTIONSHERD.get()",
    "ModBlocks.MUTATION_ANCHOR.get()",
    "ModBlocks.SPORENRESISTENTER_BLOCK.get()",
    "ModBlocks.MUTAGEN_BODEN.get()",
    "message.sporenwerk.scanner.terrain_active",
    "message.sporenwerk.scanner.terrain_cooling",
    "message.sporenwerk.scanner.clean",
):
    require(token in scanner, "scanner is missing a specific reading path: " + token)
require("getFieldStrengthAt(target" not in scanner,
        "scanner should not duplicate or fork the authoritative field calculation")

recipe_path = res / "data/sporenwerk/recipes/feldscanner.json"
recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
require(recipe["type"] == "minecraft:crafting_shaped", "scanner needs a survival crafting recipe")
require(recipe["result"]["item"] == "sporenwerk:feldscanner", "recipe must output the scanner")
for ingredient in ("minecraft:copper_ingot", "minecraft:redstone", "minecraft:glass_pane",
                   "sporenwerk:mutagenextrakt", "minecraft:iron_ingot"):
    require(any(v.get("item") == ingredient for v in recipe["key"].values()),
            "scanner recipe is missing " + ingredient)

model_path = assets / "models/item/feldscanner.json"
model = json.loads(model_path.read_text(encoding="utf-8"))
require(model["textures"]["layer0"] == "sporenwerk:item/feldscanner",
        "item model must reference the scanner sprite")
texture_path = assets / "textures/item/feldscanner.png"
require(texture_path.is_file(), "scanner PNG is missing")
with Image.open(texture_path) as image:
    rgba = image.convert("RGBA")
    require(rgba.size == (16, 16), "scanner sprite must be a Minecraft-style 16x16 tile")
    pixels = list(rgba.getdata())
    require(any(p[3] == 0 for p in pixels) and any(p[3] == 255 for p in pixels),
            "scanner sprite must have both transparent background and opaque pixels")
    require(len({p[:3] for p in pixels if p[3]}) >= 5,
            "scanner sprite must have a readable, multi-tone pixel palette")

required_keys = {
    "item.sporenwerk.feldscanner",
    "tooltip.sporenwerk.feldscanner.1",
    "tooltip.sporenwerk.feldscanner.2",
    "message.sporenwerk.scanner.node_active",
    "message.sporenwerk.scanner.node_inactive",
    "message.sporenwerk.scanner.anchor",
    "message.sporenwerk.scanner.barrier",
    "message.sporenwerk.scanner.terrain_active",
    "message.sporenwerk.scanner.terrain_cooling",
    "message.sporenwerk.scanner.field",
    "message.sporenwerk.scanner.clean",
}
for locale in ("de_de.json", "en_us.json"):
    path = assets / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(required_keys - set(data))
    require(not missing, f"{locale} is missing translations: {', '.join(missing)}")
    require(all(data[key].strip() for key in required_keys), f"{locale} contains empty scanner translations")

build = (root / "build.gradle").read_text(encoding="utf-8")
version_match = re.search(r"version\s*=\s*['\"](\d+)\.(\d+)\.(\d+)['\"]", build)
require(version_match is not None and tuple(int(part) for part in version_match.groups()) >= (1, 12, 0), "generated build version must include 1.12.0 or newer")
print("Field scanner registration, server-authoritative readings, recipe, 16x16 pixel art, locales, and version passed.")
''')

print("Added the server-authoritative Sporenwerk field scanner, recipe, 16x16 sprite, translations, regression test, and version 1.12.0 notes.")
