#!/usr/bin/env python3
"""Add a crafted Resonance Spore Capsule linking crop care and dampener maintenance (1.75.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Resonance Spore Capsule 1.75: " + message)


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


# Register a survival craftable consumable: one use advances a crop by up to two stages,
# or restores exactly one charge in a Resonance Dampener. It never changes terrain spread.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
import_line = "import de.sporenwerk.item.ResonanzsporenKapselItem;"
if import_line not in items:
    anchor = "import net.minecraft.world.item.Item;"
    require(anchor in items, "ModItems Item import anchor missing")
    items = items.replace(anchor, import_line + "\n" + anchor, 1)
registration = '    public static final RegistryObject<Item> RESONANZSPORENKAPSEL = ITEMS.register("resonanzsporen_kapsel", () -> new ResonanzsporenKapselItem(new Item.Properties().stacksTo(16)));'
if registration not in items:
    anchor = '    public static final RegistryObject<Item> LEUCHTENDER_KRISTALLKERN = ITEMS.register("leuchtender_kristallkern", () -> new LeuchtenderKristallkernItem(new Item.Properties().stacksTo(1)));'
    require(anchor in items, "Luminous Crystal Core registration missing")
    items = items.replace(anchor, anchor + "\n" + registration, 1)
items_path.write_text(items, encoding="utf-8")
require("RESONANZSPORENKAPSEL" in items_path.read_text(encoding="utf-8"),
        "capsule registration missing")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
creative_entry = "output.accept(ModItems.RESONANZSPORENKAPSEL.get());"
if creative_entry not in creative:
    anchor = "output.accept(ModItems.LEUCHTENDER_KRISTALLKERN.get());"
    require(anchor in creative, "core relic creative-tab anchor missing")
    creative_path.write_text(creative.replace(anchor, anchor + "\n                        " + creative_entry, 1), encoding="utf-8")

java = r"""
package de.sporenwerk.item;

import de.sporenwerk.block.crop.AbstractSporeCropBlock;
import de.sporenwerk.infection.MutationField;
import de.sporenwerk.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Precision field consumable: safely accelerates Sporenwerk crops or replenishes
 * one Resonance Dampener charge. The dampener interaction is handled by the block.
 */
public final class ResonanzsporenKapselItem extends Item {
    public ResonanzsporenKapselItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        BlockState state = level.getBlockState(pos);
        if (!(state.getBlock() instanceof AbstractSporeCropBlock crop)) return InteractionResult.PASS;
        if (context.getPlayer() == null) return InteractionResult.PASS;
        if (level.isClientSide) return InteractionResult.SUCCESS;

        int age = state.getValue(CropBlock.AGE);
        if (age >= crop.getMaxAge()) {
            if (context.getPlayer() != null) {
                context.getPlayer().displayClientMessage(Component.translatable(
                        "message.sporenwerk.resonanzkapsel.crop_mature").withStyle(ChatFormatting.GRAY), true);
            }
            return InteractionResult.CONSUME;
        }

        int nextAge = Math.min(crop.getMaxAge(), age + 2);
        BlockState updated = state.setValue(CropBlock.AGE, nextAge);
        int operationalStrength = MutationField.mutagenStrengthAt(level, pos);
        if (operationalStrength > state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL)) {
            updated = updated.setValue(AbstractSporeCropBlock.MUTAGEN_LEVEL, operationalStrength);
        }
        level.setBlock(pos, updated, 3);

        if (context.getPlayer() != null) {
            ItemStack held = context.getItemInHand();
            if (!context.getPlayer().getAbilities().instabuild) held.shrink(1);
            context.getPlayer().displayClientMessage(Component.translatable(
                    "message.sporenwerk.resonanzkapsel.crop_grown", nextAge, crop.getMaxAge())
                    .withStyle(ChatFormatting.GREEN), true);
        }
        if (level instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(ParticleTypes.HAPPY_VILLAGER,
                    pos.getX() + 0.5D, pos.getY() + 0.65D, pos.getZ() + 0.5D,
                    8, 0.22D, 0.2D, 0.22D, 0.015D);
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    pos.getX() + 0.5D, pos.getY() + 0.55D, pos.getZ() + 0.5D,
                    4, 0.12D, 0.14D, 0.12D, 0.012D);
        }
        level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME,
                SoundSource.BLOCKS, 0.45F, 1.4F);
        return InteractionResult.CONSUME;
    }
}
"""
write("src/main/java/de/sporenwerk/item/ResonanzsporenKapselItem.java", java)

# Dampener blocks handle their own right-click before Item.useOn. Add an explicit branch there,
# keeping the charge mutation, comparator output, and relay refresh in the same transaction.
dampener_path = SRC / "block/MutagenResonanceDampenerBlock.java"
dampener = dampener_path.read_text(encoding="utf-8")
anchor = """        if (held.is(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get())) {"""
branch = """        if (held.is(ModItems.RESONANZSPORENKAPSEL.get())) {
            if (currentCharge >= MAX_CHARGE) {
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.resonanzkapsel.dampener_full", currentCharge, MAX_CHARGE)
                        .withStyle(ChatFormatting.GRAY), false);
                return InteractionResult.CONSUME;
            }
            int nextCharge = currentCharge + 1;
            level.setBlock(pos, state.setValue(CHARGE, nextCharge), 3);
            MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);
            if (!player.getAbilities().instabuild) held.shrink(1);
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.resonanzkapsel.dampener_recharged", nextCharge, MAX_CHARGE)
                    .withStyle(ChatFormatting.LIGHT_PURPLE), false);
            if (level instanceof ServerLevel serverLevel) {
                serverLevel.sendParticles(ParticleTypes.END_ROD,
                        pos.getX() + 0.5D, pos.getY() + 0.9D, pos.getZ() + 0.5D,
                        12, 0.2D, 0.22D, 0.2D, 0.018D);
            }
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.BLOCKS, 0.7F, 0.95F);
            return InteractionResult.CONSUME;
        }
        if (held.is(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get())) {"""
if "held.is(ModItems.RESONANZSPORENKAPSEL.get())" not in dampener:
    require(anchor in dampener, "could not locate dampener charge interaction")
    dampener = dampener.replace(anchor, branch, 1)
    dampener_path.write_text(dampener, encoding="utf-8")
require("held.is(ModItems.RESONANZSPORENKAPSEL.get())" in dampener_path.read_text(encoding="utf-8"),
        "dampener capsule branch was not installed")

# Shape and recipe: rare symbiosis plus Mutagen spores are turned into a finite resource
# with two clear uses. A recipe advancement grants a real progression breadcrumb.
write("src/main/resources/data/sporenwerk/recipes/resonanzsporen_kapsel.json", json.dumps({
    "type": "minecraft:crafting_shaped",
    "pattern": [" S ", "MBM", " R "],
    "key": {
        "S": {"item": "sporenwerk:symbiosemyzel"},
        "M": {"item": "sporenwerk:mutagene_sporen"},
        "B": {"item": "minecraft:bone_meal"},
        "R": {"item": "minecraft:redstone"}
    },
    "result": {"item": "sporenwerk:resonanzsporen_kapsel", "count": 2}
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/data/sporenwerk/advancements/recipes/misc/resonanzsporen_kapsel.json", json.dumps({
    "parent": "minecraft:recipes/root",
    "rewards": {"recipes": ["sporenwerk:resonanzsporen_kapsel"]},
    "criteria": {
        "has_symbiosis": {"trigger": "minecraft:inventory_changed",
                          "conditions": {"items": [{"items": ["sporenwerk:symbiosemyzel"]}]}},
        "has_spores": {"trigger": "minecraft:inventory_changed",
                       "conditions": {"items": [{"items": ["sporenwerk:mutagene_sporen"]}]}},
        "has_the_recipe": {"trigger": "minecraft:recipe_unlocked",
                           "conditions": {"recipe": "sporenwerk:resonanzsporen_kapsel"}}
    },
    "requirements": [["has_symbiosis"], ["has_spores"], ["has_the_recipe"]]
}, ensure_ascii=False, indent=2) + "\n")

# Transparent 16x16 pixel item: sealed dark glass with a cyan pulse, amber spore and bright core.
image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.polygon([(4, 1), (11, 1), (14, 4), (14, 11), (11, 14), (4, 14), (1, 11), (1, 4)],
             fill=(21, 26, 39, 255))
draw.polygon([(4, 2), (11, 2), (13, 4), (13, 11), (11, 13), (4, 13), (2, 11), (2, 4)],
             fill=(36, 87, 107, 255))
draw.rectangle((4, 3, 11, 4), fill=(49, 181, 194, 255))
draw.rectangle((3, 5, 4, 10), fill=(24, 129, 154, 255))
draw.rectangle((11, 5, 12, 10), fill=(17, 98, 133, 255))
draw.polygon([(5, 6), (8, 4), (11, 7), (10, 10), (7, 11), (4, 9)],
             fill=(54, 226, 236, 255))
draw.polygon([(6, 6), (8, 5), (10, 7), (8, 9), (6, 8)],
             fill=(209, 255, 244, 255))
draw.point((4, 5), fill=(245, 199, 100, 255))
draw.point((5, 4), fill=(255, 227, 142, 255))
draw.point((10, 11), fill=(93, 255, 236, 255))
draw.rectangle((5, 12, 10, 12), fill=(17, 54, 69, 255))
texture_path = ASSETS / "textures/item/resonanzsporen_kapsel.png"
texture_path.parent.mkdir(parents=True, exist_ok=True)
image.save(texture_path, optimize=True)
write("src/main/resources/assets/sporenwerk/models/item/resonanzsporen_kapsel.json", """
{
  "parent": "minecraft:item/generated",
  "textures": { "layer0": "sporenwerk:item/resonanzsporen_kapsel" }
}
""")

for locale, values in {
    "de_de.json": {
        "item.sporenwerk.resonanzsporen_kapsel": "Resonanzsporen-Kapsel",
        "tooltip.sporenwerk.resonanzsporen_kapsel.1": "Präzise Kulturhilfe aus Symbiosemyzel und mutagenen Sporen.",
        "tooltip.sporenwerk.resonanzsporen_kapsel.2": "Rechtsklick auf Sporenwerk-Pflanze: +2 Wachstumsstufen. Auf Resonanzdämpfer: +1 Ladung. Bei reifer Pflanze oder vollem Dämpfer wird nichts verbraucht.",
        "message.sporenwerk.resonanzkapsel.crop_mature": "Die Pflanze ist bereits reif; die Kapsel bleibt erhalten.",
        "message.sporenwerk.resonanzkapsel.crop_grown": "Resonanzimpuls fördert das Wachstum: Stufe %s/%s.",
        "message.sporenwerk.resonanzkapsel.dampener_full": "Resonanzdämpfer ist voll geladen (%s/%s); die Kapsel bleibt erhalten.",
        "message.sporenwerk.resonanzkapsel.dampener_recharged": "Kapsel übertragen: Dämpferladung %s/%s.",
        "advancements.sporenwerk.resonanzsporen_kapsel.title": "Biologische Gegenladung",
        "advancements.sporenwerk.resonanzsporen_kapsel.description": "Stelle eine Resonanzsporen-Kapsel her."
    },
    "en_us.json": {
        "item.sporenwerk.resonanzsporen_kapsel": "Resonance Spore Capsule",
        "tooltip.sporenwerk.resonanzsporen_kapsel.1": "Precision cultivation aid made from Symbiosis Mycelium and Mutagen spores.",
        "tooltip.sporenwerk.resonanzsporen_kapsel.2": "Right-click a Sporenwerk crop: +2 growth stages. On a Resonance Dampener: +1 charge. Nothing is consumed on mature crops or full dampeners.",
        "message.sporenwerk.resonanzkapsel.crop_mature": "This crop is already mature; the capsule was preserved.",
        "message.sporenwerk.resonanzkapsel.crop_grown": "Resonance pulse accelerates growth: stage %s/%s.",
        "message.sporenwerk.resonanzkapsel.dampener_full": "Resonance Dampener is full (%s/%s); the capsule was preserved.",
        "message.sporenwerk.resonanzkapsel.dampener_recharged": "Capsule transferred: dampener charge %s/%s.",
        "advancements.sporenwerk.resonanzsporen_kapsel.title": "Biological Countercharge",
        "advancements.sporenwerk.resonanzsporen_kapsel.description": "Craft a Resonance Spore Capsule."
    }
}.items():
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Keep the generated visual QA sheet tied to the exact PNG delivered in the JAR.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
if '"resonanzsporen_kapsel"' not in preview:
    anchor = '"leuchtender_kristallkern",'
    require(anchor in preview, "visual QA sheet is missing the 1.74 core icon")
    preview_path.write_text(preview.replace(anchor, anchor + ' "resonanzsporen_kapsel",', 1),
                            encoding="utf-8")

# Advance older version contracts so the complete regression suite describes the current artifact.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_resonanzsporen_kapsel_175.py":
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.74.0",
                               "Aktueller Entwicklungsstand: 1.75.0")
    updated = updated.replace(r"1\.74\.0", r"1\.75\.0")
    updated = updated.replace("artifact must be version 1.74.0",
                              "artifact must be version 1.75.0")
    updated = updated.replace(
        '"Version 1.74.0" in readme and "Version 1.73.0" in readme',
        '"Version 1.75.0" in readme and "Version 1.74.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.75.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Gradle artifact version")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.75.0 — Resonanzsporen-Kapsel für Kultur und Containment

- **Ökologie wird zur Wartungsressource:** Symbiosemyzel und mutagene Sporen lassen sich mit Knochenmehl und Redstone zu zwei Resonanzsporen-Kapseln verarbeiten.
- **Gezielte Pflanzenpflege:** Rechtsklick auf eine unreife Sporenwerk-Pflanze erhöht ihr Wachstum um bis zu zwei Stufen. Die operative Mutagenfeldstärke wird bei Bedarf sofort im sichtbaren Phänotyp berücksichtigt; Terrain-Ausbreitung wird nicht ausgelöst.
- **Reparatur statt Einweg-Sonderfall:** Rechtsklick auf einen Resonanzdämpfer stellt genau eine Ladung wieder her und aktualisiert gekoppelte Containment-Relais. Bei voller Ladung wird keine Kapsel verbraucht.
- **Spielklare Darstellung:** Eigenes 16×16-Item-Artwork, Modell, Tooltip, DE/EN-Meldungen und Rezept-Advancement sind enthalten und werden im visuellen QA-Bogen geprüft.
- **Regressionen:** Tests sichern Eingabekosten, Wachstumskappung, Mutagen-Phänotyp, Dämpfer-Ladung, Comparator-/Relay-Aktualisierung, volle Zustände, Rezept und Versionsmetadaten.

"""
current = """## Aktueller Entwicklungsschritt — 1.75.0

- **Sporenpflege:** Die neue Resonanzsporen-Kapsel beschleunigt kontrolliert das Wachstum unreifer Sporenwerk-Pflanzen.
- **Containment-Wartung:** Dieselbe Kapsel lädt Resonanzdämpfer um eine Stufe nach, ohne bei vollem Gerät verbraucht zu werden. Verbundene Relais erhalten ein Update.
- **Kreislauf:** Seltenes Symbiosemyzel und mutagene Sporen aus der Feldernte werden zu einer handlichen Ressource für Farmen und Sicherheitsanlagen.
- **Qualität:** Eigene Itemtextur, Crafting-Rezept, Übersetzungen, Advancement, Regressionen, Forge-JAR- und Serverstartprüfung.

"""
if "## Version 1.75.0 — Resonanzsporen-Kapsel für Kultur und Containment" not in readme:
    marker = "## Version 1.74.0 — Leuchtender Kristallkern als Bossreliquie"
    index = readme.find(marker)
    require(index >= 0, "could not find 1.74 release section")
    readme = readme[:index] + release + readme[index:]
if "## Aktueller Entwicklungsschritt — 1.75.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.74.0"
    index = readme.find(marker)
    require(index >= 0, "could not find 1.74 current development section")
    readme = readme[:index] + current + readme[index:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.74.0 — Leuchtender Kristallkern als aktive Bossreliquie.**",
    "**Aktueller Entwicklungsstand: 1.75.0 — Resonanzsporen-Kapsel für Kultur und Containment.**")
require("Aktueller Entwicklungsstand: 1.75.0" in readme,
        "README current version headline was not updated")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.75.0 generated: crop growth and Dampener charge maintenance now share a craftable Resonance Spore Capsule.")
