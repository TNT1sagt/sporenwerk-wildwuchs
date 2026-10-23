#!/usr/bin/env python3
"""Add a craftable spore-filter helmet and integrate its finite protection into field exposure."""
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

def replace_once(path, old, new, label):
    p = ROOT / path
    source = p.read_text(encoding="utf-8")
    if new in source:
        return source
    if old not in source:
        raise SystemExit(f"Spore filter patch cannot locate {label} in {path}")
    source = source.replace(old, new, 1)
    p.write_text(source, encoding="utf-8")
    return source

# Register a true equippable helmet. It is also the replaceable filter: each intercepted
# field exposure consumes durability, so protection is renewable but not permanent.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
if "import net.minecraft.world.item.ArmorItem;" not in items:
    anchor = "import net.minecraft.world.item.Item;"
    if anchor not in items:
        raise SystemExit("Cannot locate Item import in ModItems")
    items = items.replace(anchor, anchor + "\nimport net.minecraft.world.item.ArmorItem;", 1)
if "SPORENFILTERMASKE" not in items:
    anchor = '    public static final RegistryObject<Item> FELDSCANNER = ITEMS.register("feldscanner", () -> new FeldscannerItem(new Item.Properties().stacksTo(1)));'
    field = '    public static final RegistryObject<Item> SPORENFILTERMASKE = ITEMS.register("sporenfiltermaske", () -> new ArmorItem(de.sporenwerk.item.SporeFilterMaterial.MATERIAL, ArmorItem.Type.HELMET, new Item.Properties()));'
    if anchor not in items:
        raise SystemExit("Cannot locate field scanner registration for the spore filter helmet")
    items = items.replace(anchor, anchor + "\n" + field, 1)
items_path.write_text(items, encoding="utf-8")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
if "output.accept(ModItems.SPORENFILTERMASKE.get());" not in creative:
    anchor = "output.accept(ModItems.FELDSCANNER.get());"
    if anchor not in creative:
        raise SystemExit("Cannot locate field scanner in creative tab")
    creative_path.write_text(creative.replace(anchor, anchor + "\n                        output.accept(ModItems.SPORENFILTERMASKE.get());", 1), encoding="utf-8")

write("src/main/java/de/sporenwerk/item/SporeFilterMaterial.java", """
package de.sporenwerk.item;

import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Ingredient;
import net.minecraft.world.item.Items;

/** Lightweight, repairable filter-weave armor material tuned for a single helmet. */
public enum SporeFilterMaterial implements ArmorMaterial {
    MATERIAL;

    @Override
    public int getDurabilityForType(ArmorItem.Type type) {
        return type.getDurability(13);
    }

    @Override
    public int getDefenseForType(ArmorItem.Type type) {
        return switch (type) {
            case HELMET -> 2;
            case CHESTPLATE, LEGGINGS, BOOTS -> 0;
        };
    }

    @Override public int getEnchantmentValue() { return 12; }
    @Override public SoundEvent getEquipSound() { return SoundEvents.ARMOR_EQUIP_LEATHER; }
    @Override public Ingredient getRepairIngredient() { return Ingredient.of(Items.LEATHER); }
    @Override public String getName() { return "sporenwerk:sporenfilter"; }
    @Override public float getToughness() { return 0.0F; }
    @Override public float getKnockbackResistance() { return 0.0F; }
}
""")

# The mask is protected at the center seam with a glass/metal viewport and distinct filter pads.
icon_path = ASSETS / "textures/item/sporenfiltermaske.png"
icon_path.parent.mkdir(parents=True, exist_ok=True)
im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
ink=(24,31,29,255); edge=(57,73,63,255); cloth=(91,112,81,255)
light=(157,178,126,255); glass=(44,119,116,255); glow=(120,218,183,255)
metal=(142,150,130,255); rust=(178,90,57,255)
d.polygon([(3,3),(12,3),(14,6),(13,11),(10,14),(6,14),(3,11),(2,6)], fill=ink)
d.polygon([(4,4),(11,4),(12,6),(12,10),(9,12),(6,12),(4,10),(3,6)], fill=cloth)
d.rectangle((4,5,11,8), fill=edge)
d.rectangle((5,5,10,7), fill=glass)
d.point((6,5), fill=glow); d.point((9,6), fill=glow)
d.rectangle((3,8,4,10), fill=metal); d.rectangle((11,8,12,10), fill=metal)
d.rectangle((2,7,3,8), fill=rust); d.rectangle((12,7,13,8), fill=rust)
d.rectangle((5,10,10,11), fill=ink)
d.rectangle((6,10,7,10), fill=light); d.rectangle((8,10,9,10), fill=light)
im.save(icon_path, optimize=True)
write("src/main/resources/assets/sporenwerk/models/item/sporenfiltermaske.json", """
{
  "parent": "minecraft:item/generated",
  "textures": {
    "layer0": "sporenwerk:item/sporenfiltermaske"
  }
}
""")

# Minecraft armor layer texture (64x32), kept deliberately pixelated and transparent off-mask.
armor_path = ASSETS / "textures/models/armor/sporenfilter_layer_1.png"
armor_path.parent.mkdir(parents=True, exist_ok=True)
armor = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
ad = ImageDraw.Draw(armor)
# Vanilla helmet UV island occupies the head region in the upper-left quarter of layer 1.
ad.rectangle((1,1,14,7), fill=ink)
ad.rectangle((2,2,13,6), fill=cloth)
ad.rectangle((3,4,12,6), fill=edge)
ad.rectangle((4,4,11,5), fill=glass)
ad.point((5,4), fill=glow); ad.point((10,5), fill=glow)
ad.rectangle((2,6,3,7), fill=metal); ad.rectangle((12,6,13,7), fill=metal)
ad.rectangle((6,6,9,7), fill=ink)
armor.save(armor_path, optimize=True)

write("src/main/resources/data/sporenwerk/recipes/sporenfiltermaske.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": [
    "LLL",
    "FIF",
    " C "
  ],
  "key": {
    "L": { "item": "minecraft:leather" },
    "F": { "item": "sporenwerk:filtermoos" },
    "I": { "item": "minecraft:copper_ingot" },
    "C": { "item": "minecraft:charcoal" }
  },
  "result": {
    "item": "sporenwerk:sporenfiltermaske",
    "count": 1
  }
}
""")

# Field exposure is calculated on the server. A worn mask intercepts the next exposure pulse
# and takes durability damage; the cooldown remains longer so the filter meaningfully protects.
field_path = SRC / "infection/MutationField.java"
field = field_path.read_text(encoding="utf-8")
for imp in (
    "import de.sporenwerk.registry.ModItems;",
    "import net.minecraft.world.entity.EquipmentSlot;"
):
    if imp not in field:
        anchor = "import de.sporenwerk.registry.ModBlocks;"
        if anchor not in field:
            raise SystemExit("Cannot locate MutationField imports")
        field = field.replace(anchor, anchor + "\n" + imp, 1)
old_exposure = """            if (now >= nextExposure && !hasAnchor(level, player.blockPosition())) {
                InfectionState.setLevel(player, InfectionState.level(player) + 1);
                player.getPersistentData().putLong("SporenwerkControlledExposureAt", now + 100);
            }"""
new_exposure = """            if (now >= nextExposure && !hasAnchor(level, player.blockPosition())) {
                net.minecraft.world.item.ItemStack mask = player.getItemBySlot(EquipmentSlot.HEAD);
                if (mask.is(ModItems.SPORENFILTERMASKE.get())) {
                    mask.hurtAndBreak(1, player, entity -> entity.broadcastBreakEvent(EquipmentSlot.HEAD));
                    player.getPersistentData().putLong("SporenwerkControlledExposureAt", now + 300);
                } else {
                    InfectionState.setLevel(player, InfectionState.level(player) + 1);
                    player.getPersistentData().putLong("SporenwerkControlledExposureAt", now + 100);
                }
            }"""
if new_exposure not in field:
    if old_exposure not in field:
        raise SystemExit("Could not find server-authoritative field exposure pulse")
    field = field.replace(old_exposure, new_exposure, 1)
field_path.write_text(field, encoding="utf-8")

# Locales are merged, never overwritten; both German and English stay complete.
for locale, entries in (
    ("de_de.json", {
        "item.sporenwerk.sporenfiltermaske": "Sporenfiltermaske",
        "tooltip.sporenwerk.sporenfiltermaske.1": "Trage sie im Kopf-Slot, um Mutagen-Exposition abzufangen.",
        "tooltip.sporenwerk.sporenfiltermaske.2": "Jeder abgefangene Feldimpuls verbraucht Filterhaltbarkeit. Mit Leder reparierbar."
    }),
    ("en_us.json", {
        "item.sporenwerk.sporenfiltermaske": "Spore Filter Mask",
        "tooltip.sporenwerk.sporenfiltermaske.1": "Wear in the helmet slot to intercept mutagen exposure.",
        "tooltip.sporenwerk.sporenfiltermaske.2": "Each intercepted field pulse consumes durability. Repair with leather."
    })
):
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build_path = ROOT / "build.gradle"
build = build_path.read_text(encoding="utf-8")
build, count = re.subn(r"version\s*=\s*['\"][^'\"]+['\"]", "version = '1.14.0'", build, count=1)
if count != 1:
    raise SystemExit("Could not bump build.gradle to version 1.14.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
heading = "## Version 1.14.0 — Sporenfilter und Expositionsschutz"
section = """## Version 1.14.0 — Sporenfilter und Expositionsschutz

- **Sporenfiltermaske:** Herstellbarer Helm mit eigener Pixeltextur, passendem Rüstungs-Layer, zwei Sprachen und Reparatur mit Leder.
- **Echte Feld-Gegenmaßnahme:** Die Maske fängt Feld-Expositionsimpulse ab, statt Infektion nur nachträglich zu heilen. Jeder abgefangene Impuls verbraucht Haltbarkeit; ohne Maske bleibt die bisherige Feldgefahr bestehen.
- **Balance und Persistenz:** Der Schutz greift direkt in die serverseitige Expositionslogik ein und speichert den verlängerten Expositions-Cooldown im Spieler-NBT. Clienteffekte können die Mechanik nicht vortäuschen.
- **Release-QA:** Test für Rüstungsregistrierung, Rezept, Texturen, Lokalisierung und die echte Expositionsverzweigung; anschließend Ressourcenprüfung, Forge-Build, JAR-Validierung und dedizierter Serverstart.

Automatische CI-Tests ersetzen keinen manuellen Sichttest im Minecraft-Client.

"""
if heading not in readme:
    readme = section + readme
readme_path.write_text(readme, encoding="utf-8")

write("tools/test_spore_filter.py", r'''
from pathlib import Path
import json, sys
from PIL import Image
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
src = root / "src/main/java/de/sporenwerk"
assets = root / "src/main/resources/assets/sporenwerk"
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Spore filter regression: " + message)
items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
require("SPORENFILTERMASKE" in items and "ArmorItem.Type.HELMET" in items,
        "mask must be a registered, wearable helmet")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
require("output.accept(ModItems.SPORENFILTERMASKE.get())" in creative,
        "mask must appear in the creative catalogue")
material = read("src/main/java/de/sporenwerk/item/SporeFilterMaterial.java")
for token in ("implements ArmorMaterial", "getDurabilityForType", "getDefenseForType",
              "getRepairIngredient", "getEquipSound", "getKnockbackResistance"):
    require(token in material, "armor material is missing " + token)
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
require("player.getItemBySlot(EquipmentSlot.HEAD)" in field
        and "mask.is(ModItems.SPORENFILTERMASKE.get())" in field,
        "wearing the mask must be checked in authoritative field exposure")
require("mask.hurtAndBreak(1, player" in field
        and 'putLong("SporenwerkControlledExposureAt", now + 300)' in field
        and 'putLong("SporenwerkControlledExposureAt", now + 100)' in field,
        "mask must consume durability and preserve the shorter unprotected exposure cadence")
recipe = json.loads((root / "src/main/resources/data/sporenwerk/recipes/sporenfiltermaske.json").read_text(encoding="utf-8"))
require(recipe["result"]["item"] == "sporenwerk:sporenfiltermaske", "survival recipe must output the mask")
for ingredient in ("minecraft:leather", "sporenwerk:filtermoos", "minecraft:copper_ingot", "minecraft:charcoal"):
    require(any(entry.get("item") == ingredient for entry in recipe["key"].values()),
            "mask recipe missing ingredient " + ingredient)
model = json.loads((assets / "models/item/sporenfiltermaske.json").read_text(encoding="utf-8"))
require(model["textures"]["layer0"] == "sporenwerk:item/sporenfiltermaske", "item model texture path is wrong")
for rel, size in (("textures/item/sporenfiltermaske.png", (16,16)),
                  ("textures/models/armor/sporenfilter_layer_1.png", (64,32))):
    with Image.open(assets / rel) as image:
        require(image.size == size, rel + " has unexpected dimensions")
for locale in ("de_de.json","en_us.json"):
    data = json.loads((assets / "lang" / locale).read_text(encoding="utf-8"))
    require(all(data.get(key, "").strip() for key in (
        "item.sporenwerk.sporenfiltermaske",
        "tooltip.sporenwerk.sporenfiltermaske.1",
        "tooltip.sporenwerk.sporenfiltermaske.2")), locale + " missing mask translations")
require("Version 1.14.0" in read("README.md"), "release notes missing version 1.14.0")
print("Wearable spore-filter helmet, recipe, pixel textures, durability-based field protection and locales passed.")
''')

print("Installed Sporenwerk 1.14.0 spore-filter helmet and server-authoritative field protection.")
