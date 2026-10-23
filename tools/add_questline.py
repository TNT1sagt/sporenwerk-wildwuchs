#!/usr/bin/env python3
"""Add the five-chapter, optional-mod-independent Sporenwerk progression for Forge 1.20.1."""
from pathlib import Path
import json, sys

ROOT = Path(sys.argv[1]).resolve()
RES = ROOT / "src/main/resources"

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip(), encoding="utf-8")

def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text(encoding="utf-8")
    if new in s:
        return
    if old not in s:
        raise SystemExit(f"Expected context not found in {rel}: {old[:120]!r}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# Add the narrative note as a real readable item; it is not a weapon or a punishment.
replace_once(
    "src/main/java/de/sporenwerk/registry/ModItems.java",
    "import de.sporenwerk.item.FeldhandbuchItem;",
    "import de.sporenwerk.item.FeldhandbuchItem;\nimport de.sporenwerk.item.VerwitterteNotizItem;"
)
replace_once(
    "src/main/java/de/sporenwerk/registry/ModItems.java",
    'public static final RegistryObject<Item> FELDHANDBUCH = ITEMS.register("feldhandbuch", () -> new FeldhandbuchItem(new Item.Properties().stacksTo(1)));',
    'public static final RegistryObject<Item> FELDHANDBUCH = ITEMS.register("feldhandbuch", () -> new FeldhandbuchItem(new Item.Properties().stacksTo(1)));\n    public static final RegistryObject<Item> VERWITTERTE_NOTIZ = ITEMS.register("verwitterte_notiz", () -> new VerwitterteNotizItem(new Item.Properties().stacksTo(1)));'
)
replace_once(
    "src/main/java/de/sporenwerk/registry/ModCreativeTabs.java",
    "output.accept(ModItems.FELDHANDBUCH.get());",
    "output.accept(ModItems.FELDHANDBUCH.get());\n                        output.accept(ModItems.VERWITTERTE_NOTIZ.get());"
)

write("src/main/java/de/sporenwerk/item/VerwitterteNotizItem.java", '''
package de.sporenwerk.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/** A harmless, readable story artifact found very rarely on the Dämmerling. */
public final class VerwitterteNotizItem extends Item {
    public VerwitterteNotizItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, net.minecraft.world.entity.player.Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (player instanceof ServerPlayer serverPlayer) {
            serverPlayer.sendSystemMessage(Component.literal("— FELDPROTOKOLL 04 / HINTER DEM GLAS —")
                    .withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.BOLD));
            serverPlayer.sendSystemMessage(Component.literal("Das Beet war leer. Ich konnte trotzdem hören, wie jemand Erde glattstrich.")
                    .withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
            serverPlayer.sendSystemMessage(Component.literal("Im Fenster sah ich mich selbst am Beet stehen. Die Gestalt hielt die Gießkanne.")
                    .withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
            serverPlayer.sendSystemMessage(Component.literal("Ich hatte die Gießkanne seit Tagen nicht mehr benutzt.")
                    .withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
            serverPlayer.sendSystemMessage(Component.literal("Am Morgen waren die Fingerabdrücke auf der Innenseite der Scheibe.")
                    .withStyle(ChatFormatting.DARK_PURPLE));
            serverPlayer.sendSystemMessage(Component.literal("Unter dem letzten Abdruck stand: DU HAST MICH ANGEBAUT.")
                    .withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
        }
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Feldprotokoll 04").withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.ITALIC));
        tooltip.add(Component.literal("Die Schrift ist auf der Innenseite verwischt.").withStyle(ChatFormatting.GRAY));
    }
}
''')

write("src/main/resources/assets/sporenwerk/models/item/verwitterte_notiz.json", '''
{
  "parent": "minecraft:item/generated",
  "textures": { "layer0": "sporenwerk:item/verwitterte_notiz" }
}
''')

lang_path = RES / "assets/sporenwerk/lang/de_de.json"
lang = json.loads(lang_path.read_text(encoding="utf-8"))
lang.update({
    "item.sporenwerk.verwitterte_notiz": "Verwittertes Feldprotokoll",
    "advancements.sporenwerk.root.title": "Ein Stück Erde",
    "advancements.sporenwerk.root.description": "Finde Saatgut, pflanze Faserrohr und ernte zum ersten Mal.",
    "advancements.sporenwerk.first_crop.title": "Nichts verkommt",
    "advancements.sporenwerk.first_crop.description": "Gewinne Pflanzenreste und verarbeite sie zu Biomasse.",
    "advancements.sporenwerk.first_machine.title": "Die erste Maschine",
    "advancements.sporenwerk.first_machine.description": "Baue deine erste Maschine für eine kleine Produktionskette.",
    "advancements.sporenwerk.larger_harvest.title": "Eine größere Ernte",
    "advancements.sporenwerk.larger_harvest.description": "Stelle einen Feldsammler auf und baue die Erntekette aus.",
    "advancements.sporenwerk.field_behind_glass.title": "Das Feld hinter dem Glas",
    "advancements.sporenwerk.field_behind_glass.description": "Lies das seltene Feldprotokoll. Manche Dinge wachsen nicht im Beet."
})
lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Quest chapter one: both planting and a real harvest are required, in addition to seed access.
write("src/main/resources/data/sporenwerk/advancements/root.json", '''
{
  "display": {
    "icon": { "item": "sporenwerk:faserrohr_samen" },
    "title": { "translate": "advancements.sporenwerk.root.title" },
    "description": { "translate": "advancements.sporenwerk.root.description" },
    "background": "minecraft:textures/gui/advancements/backgrounds/husbandry.png",
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": false,
    "hidden": false
  },
  "criteria": {
    "find_seed": { "trigger": "minecraft:inventory_changed", "conditions": { "items": [{ "items": ["sporenwerk:faserrohr_samen"] }] } },
    "plant_crop": { "trigger": "minecraft:placed_block", "conditions": { "block": "sporenwerk:faserrohr" } },
    "harvest_crop": { "trigger": "minecraft:inventory_changed", "conditions": { "items": [{ "items": ["sporenwerk:faser"] }] } }
  },
  "requirements": [["find_seed"], ["plant_crop"], ["harvest_crop"]],
  "rewards": { "loot": ["sporenwerk:quests/ein_stueck_erde"] }
}
''')

write("src/main/resources/data/sporenwerk/advancements/first_crop.json", '''
{
  "parent": "sporenwerk:root",
  "display": {
    "icon": { "item": "sporenwerk:biomasse" },
    "title": { "translate": "advancements.sporenwerk.first_crop.title" },
    "description": { "translate": "advancements.sporenwerk.first_crop.description" },
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "get_remainders": { "trigger": "minecraft:inventory_changed", "conditions": { "items": [{ "items": ["sporenwerk:pflanzenreste"] }] } },
    "make_biomass": { "trigger": "minecraft:inventory_changed", "conditions": { "items": [{ "items": ["sporenwerk:biomasse"] }] } }
  },
  "requirements": [["get_remainders"], ["make_biomass"]],
  "rewards": { "loot": ["sporenwerk:quests/nichts_verkommt"] }
}
''')

write("src/main/resources/data/sporenwerk/advancements/first_machine.json", '''
{
  "parent": "sporenwerk:first_crop",
  "display": {
    "icon": { "item": "sporenwerk:saatgutpresse" },
    "title": { "translate": "advancements.sporenwerk.first_machine.title" },
    "description": { "translate": "advancements.sporenwerk.first_machine.description" },
    "frame": "goal",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "place_feldsammler": { "trigger": "minecraft:placed_block", "conditions": { "block": "sporenwerk:feldsammler" } },
    "place_press": { "trigger": "minecraft:placed_block", "conditions": { "block": "sporenwerk:saatgutpresse" } },
    "place_reactor": { "trigger": "minecraft:placed_block", "conditions": { "block": "sporenwerk:biomasse_bioreaktor" } }
  },
  "requirements": [["place_feldsammler", "place_press", "place_reactor"]],
  "rewards": { "loot": ["sporenwerk:quests/die_erste_maschine"] }
}
''')

write("src/main/resources/data/sporenwerk/advancements/larger_harvest.json", '''
{
  "parent": "sporenwerk:first_machine",
  "display": {
    "icon": { "item": "sporenwerk:feldsammler" },
    "title": { "translate": "advancements.sporenwerk.larger_harvest.title" },
    "description": { "translate": "advancements.sporenwerk.larger_harvest.description" },
    "frame": "goal",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "place_collector": { "trigger": "minecraft:placed_block", "conditions": { "block": "sporenwerk:feldsammler" } },
    "continue_harvest": { "trigger": "minecraft:inventory_changed", "conditions": { "items": [{ "items": ["sporenwerk:rotwurzel", "sporenwerk:filtermoos"] }] } }
  },
  "requirements": [["place_collector"], ["continue_harvest"]],
  "rewards": { "loot": ["sporenwerk:quests/eine_groessere_ernte"] }
}
''')

write("src/main/resources/data/sporenwerk/advancements/field_behind_glass.json", '''
{
  "parent": "sporenwerk:larger_harvest",
  "display": {
    "icon": { "item": "sporenwerk:verwitterte_notiz" },
    "title": { "translate": "advancements.sporenwerk.field_behind_glass.title" },
    "description": { "translate": "advancements.sporenwerk.field_behind_glass.description" },
    "frame": "challenge",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "find_field_report": { "trigger": "minecraft:inventory_changed", "conditions": { "items": [{ "items": ["sporenwerk:verwitterte_notiz"] }] } }
  },
  "rewards": { "loot": ["sporenwerk:quests/das_feld_hinter_dem_glas"] }
}
''')

def reward_table(name, entries):
    write("src/main/resources/data/sporenwerk/loot_tables/quests/" + name + ".json",
          json.dumps({"type":"minecraft:generic","pools":[{"rolls":1,"entries":[
              {"type":"minecraft:item","name":item,"functions":[{"function":"minecraft:set_count","count":count}]}
              for item,count in entries
          ]}]}, indent=2) + "\n")

reward_table("ein_stueck_erde", [("sporenwerk:bernsteinkappe_sporen",2),("sporenwerk:faserrohr_samen",2)])
reward_table("nichts_verkommt", [("sporenwerk:filtermoos_sporen",3),("sporenwerk:maschinenteil",1)])
reward_table("die_erste_maschine", [("sporenwerk:maschinenteil",2),("sporenwerk:filter",1)])
reward_table("eine_groessere_ernte", [("sporenwerk:rotwurzel_samen",3),("sporenwerk:filtermoos_sporen",3)])
reward_table("das_feld_hinter_dem_glas", [("sporenwerk:maschinenteil",3),("sporenwerk:filter",2)])

# The note is a rare Dämmerling drop. The creature remains weak and never summons reinforcements.
write("src/main/resources/data/sporenwerk/loot_tables/entities/daemmerling.json", '''
{
  "type": "minecraft:entity",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        { "type": "minecraft:item", "name": "sporenwerk:pflanzenreste",
          "functions": [ { "function": "minecraft:set_count", "count": { "min": 0.0, "max": 1.0 } } ] }
      ]
    },
    {
      "rolls": 1.0,
      "conditions": [{ "condition": "minecraft:random_chance", "chance": 0.18 }],
      "entries": [{ "type": "minecraft:item", "name": "sporenwerk:verwitterte_notiz" }]
    }
  ]
}
''')

# Pin version for this cohesive milestone.
build = ROOT / "build.gradle"
s = build.read_text(encoding="utf-8")
import re
s = re.sub(r"version = '[^']+'", "version = '1.1.0'", s, count=1)
build.write_text(s, encoding="utf-8")

readme = ROOT / "README.md"
s = readme.read_text(encoding="utf-8")
s += """
\n## Questline 1.1.0\nThe five chapter objectives are shipped as vanilla advancements, so there is no mandatory FTB Quests dependency. They award seeds, machine parts, and filters. The final chapter is unlocked by a rare, harmless narrative note dropped by the weak Dämmerling. FTB Quests remains optional; its native import file still needs validation against the exact modpack release.\n"""
readme.write_text(s, encoding="utf-8")
print("Added five progression chapters and the rare Field Report story item.")
