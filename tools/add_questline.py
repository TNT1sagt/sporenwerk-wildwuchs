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
    'public static final RegistryObject<Item> FELDHANDBUCH = ITEMS.register("feldhandbuch",\n            () -> new FeldhandbuchItem(new Item.Properties().stacksTo(1)));',
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


# Make Feldwissen a usable reward item: right-click converts one token to ten persistent knowledge points.
write("src/main/java/de/sporenwerk/item/FeldwissenItem.java", '''
package de.sporenwerk.item;

import de.sporenwerk.skill.SkillData;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

public final class FeldwissenItem extends Item {
    public static final int VALUE = 10;

    public FeldwissenItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, net.minecraft.world.entity.player.Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(player instanceof ServerPlayer serverPlayer) || !(level instanceof ServerLevel serverLevel)) {
            return InteractionResultHolder.pass(stack);
        }
        SkillData data = SkillData.get(serverLevel);
        data.addKnowledge(VALUE);
        if (!serverPlayer.getAbilities().instabuild) stack.shrink(1);
        serverPlayer.displayClientMessage(Component.literal("+10 Feldwissen · Gesamt: " + data.knowledge())
                .withStyle(ChatFormatting.GREEN), true);
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Beim Benutzen in 10 Feldwissen umwandeln.").withStyle(ChatFormatting.GREEN));
        tooltip.add(Component.literal("Wissen bleibt in den Weltdaten gespeichert.").withStyle(ChatFormatting.GRAY));
    }
}
''')

# Optional native FTB Quests chapter. It is distributed separately so installing the mod JAR
# never overwrites or mutates any existing modpack quest configuration.
write("extras/ftbquests/config/ftbquests/quests/chapters/sporenwerk_wildwuchs.snbt", '''
{
  default_hide_dependency_lines: false
  default_quest_shape: ""
  filename: "sporenwerk_wildwuchs"
  icon: "sporenwerk:feldhandbuch"
  id: "53504F52454E0001"
  images: []
  order_index: 0
  quest_links: []
  quests: [
    {
      id: "53504F52454E0101"
      shape: "hexagon"
      size: 1.5d
      title: "&2Ein Stück Erde"
      subtitle: "Saatgut finden, die erste Pflanze setzen und die erste Faser ernten."
      tasks: [
        { id: "53504F52454E1001", type: "item", item: "sporenwerk:faserrohr_samen", count: 2L }
        { id: "53504F52454E1002", type: "item", item: "sporenwerk:faser", count: 1L }
      ]
      rewards: [
        { id: "53504F52454E2001", type: "item", item: { Count: 2, id: "sporenwerk:bernsteinkappe_sporen", tag: { Damage: 0 } } }
        { id: "53504F52454E2002", type: "item", item: { Count: 1, id: "sporenwerk:feldwissen", tag: { Damage: 0 } } }
      ]
      x: 0.0d
      y: 0.0d
    }
    {
      dependencies: ["53504F52454E0101"]
      id: "53504F52454E0102"
      title: "&eNichts verkommt"
      subtitle: "Verarbeite Pflanzenreste zu Biomasse und starte die Saatgutkette."
      tasks: [
        { id: "53504F52454E1003", type: "item", item: "sporenwerk:pflanzenreste", count: 2L }
        { id: "53504F52454E1004", type: "item", item: "sporenwerk:biomasse", count: 1L }
      ]
      rewards: [
        { id: "53504F52454E2003", type: "item", item: { Count: 3, id: "sporenwerk:filtermoos_sporen", tag: { Damage: 0 } } }
        { id: "53504F52454E2004", type: "item", item: { Count: 1, id: "sporenwerk:feldwissen", tag: { Damage: 0 } } }
      ]
      x: 2.0d
      y: 0.0d
    }
    {
      dependencies: ["53504F52454E0102"]
      id: "53504F52454E0103"
      title: "&6Die erste Maschine"
      subtitle: "Baue die Saatgutpresse und füttere deine erste Produktionskette."
      tasks: [
        { id: "53504F52454E1005", type: "item", item: "sporenwerk:saatgutpresse", count: 1L }
        { id: "53504F52454E1006", type: "item", item: "sporenwerk:maschinenteil", count: 2L }
      ]
      rewards: [
        { id: "53504F52454E2005", type: "item", item: { Count: 2, id: "sporenwerk:maschinenteil", tag: { Damage: 0 } } }
        { id: "53504F52454E2006", type: "item", item: { Count: 1, id: "sporenwerk:feldwissen", tag: { Damage: 0 } } }
      ]
      x: 4.0d
      y: 0.0d
    }
    {
      dependencies: ["53504F52454E0103"]
      id: "53504F52454E0104"
      title: "&aEine größere Ernte"
      subtitle: "Richte den Feldsammler ein und versorge ihn mit passenden Samen."
      tasks: [
        { id: "53504F52454E1007", type: "item", item: "sporenwerk:feldsammler", count: 1L }
        { id: "53504F52454E1008", type: "item", item: "sporenwerk:faserrohr_samen", count: 4L }
      ]
      rewards: [
        { id: "53504F52454E2007", type: "item", item: { Count: 3, id: "sporenwerk:rotwurzel_samen", tag: { Damage: 0 } } }
        { id: "53504F52454E2008", type: "item", item: { Count: 2, id: "sporenwerk:feldwissen", tag: { Damage: 0 } } }
      ]
      x: 6.0d
      y: 0.0d
    }
    {
      dependencies: ["53504F52454E0104"]
      id: "53504F52454E0105"
      shape: "hexagon"
      title: "&5Das Feld hinter dem Glas"
      subtitle: "Finde das seltene Feldprotokoll. Es stammt von der falschen Seite der Scheibe."
      tasks: [
        { id: "53504F52454E1009", type: "item", item: "sporenwerk:verwitterte_notiz", count: 1L }
      ]
      rewards: [
        { id: "53504F52454E2009", type: "item", item: { Count: 2, id: "sporenwerk:filter", tag: { Damage: 0 } } }
        { id: "53504F52454E2010", type: "item", item: { Count: 3, id: "sporenwerk:maschinenteil", tag: { Damage: 0 } } }
        { id: "53504F52454E2011", type: "item", item: { Count: 2, id: "sporenwerk:feldwissen", tag: { Damage: 0 } } }
      ]
      x: 8.0d
      y: 0.0d
    }
  ]
  title: "&2Sporenwerk: Wildwuchs"
}
''')

write("extras/ftbquests/README.md", '''
# Sporenwerk: Wildwuchs — optionaler FTB-Quests-Import

Ziel: Minecraft Java 1.20.1 / Forge 47.x / eine passende FTB-Quests-Version für Minecraft 1.20.1.

## Import
1. Sichere deinen bestehenden Ordner config/ftbquests/quests.
2. Kopiere die Datei config/ftbquests/quests/chapters/sporenwerk_wildwuchs.snbt aus diesem Paket an denselben relativen Ort in deiner Instanz oder deinem Modpack.
3. Starte die Welt bzw. den Server. Bei einer laufenden Instanz kann ein Administrator /ftbquests reload ausführen.
4. Öffne das Questbuch und prüfe die fünf Kapitelziele und Belohnungen.

Die Datei enthält ein einzelnes Kapitel und 26 eindeutige IDs. Sie legt keine Gruppenregistrierung an und überschreibt nicht deine bestehende chapter_groups.snbt. Die Questdatei ist eine optionale Ergänzung; Sporenwerk selbst benötigt FTB Quests nicht zum Start. Prüfe die Datei vor einer Veröffentlichung im konkreten Modpack mit der installierten FTB-Quests-Version.
''')

# Validate SNBT identity format and uniqueness before building the modpack bundle.
quest_path = ROOT / "extras/ftbquests/config/ftbquests/quests/chapters/sporenwerk_wildwuchs.snbt"
snbt = quest_path.read_text(encoding="utf-8")
import re
ids = re.findall(r'\bid: "([0-9A-F]{16})"', snbt)
if len(ids) != 26 or len(ids) != len(set(ids)):
    raise SystemExit(f"FTB Quests ID check failed: {len(ids)} IDs, {len(set(ids))} unique")
print(f"Optional FTB Quests chapter written; {len(ids)} unique IDs validated.")


# FTB Quests 1.20.1 stores quest titles/subtitles in lang/de_de.snbt and item stacks as item compounds.
quest_path = ROOT / "extras/ftbquests/config/ftbquests/quests/chapters/sporenwerk_wildwuchs.snbt"
snbt = quest_path.read_text(encoding="utf-8")
snbt = snbt.replace('icon: "sporenwerk:feldhandbuch"', 'icon: { id: "sporenwerk:feldhandbuch" }')
snbt = re.sub(r'item: "([^"]+)", count: (\d+L)', r'item: { id: "\1", count: \2 }', snbt)
snbt = re.sub(r'item: \{ Count: (\d+), id: "([^"]+)", tag: \{ Damage: 0 \} \}', r'item: { count: \1, id: "\2" }', snbt)
snbt = re.sub(r'^\s*(?:title|subtitle): "[^"]*"\s*\n', '', snbt, flags=re.M)
quest_path.write_text(snbt, encoding="utf-8")

write("extras/ftbquests/config/ftbquests/quests/lang/de_de.snbt", '''
{
  chapter.53504F52454E0001.title: "&2Sporenwerk: Wildwuchs"
  quest.53504F52454E0101.title: "&2Ein Stück Erde"
  quest.53504F52454E0101.quest_subtitle: "Saatgut finden, die erste Pflanze setzen und die erste Faser ernten."
  quest.53504F52454E0102.title: "&eNichts verkommt"
  quest.53504F52454E0102.quest_subtitle: "Verarbeite Pflanzenreste zu Biomasse und starte die Saatgutkette."
  quest.53504F52454E0103.title: "&6Die erste Maschine"
  quest.53504F52454E0103.quest_subtitle: "Baue die Saatgutpresse und füttere deine erste Produktionskette."
  quest.53504F52454E0104.title: "&aEine größere Ernte"
  quest.53504F52454E0104.quest_subtitle: "Richte den Feldsammler ein und versorge ihn mit passenden Samen."
  quest.53504F52454E0105.title: "&5Das Feld hinter dem Glas"
  quest.53504F52454E0105.quest_subtitle: "Finde das seltene Feldprotokoll. Es stammt von der falschen Seite der Scheibe."
}
''')

readme_path = ROOT / "extras/ftbquests/README.md"
readme_text = readme_path.read_text(encoding="utf-8")
if "lang/de_de.snbt" not in readme_text:
    readme_text += """
\n## Übersetzungen
Kopiere zusätzlich lang/de_de.snbt in config/ftbquests/quests/lang/de_de.snbt. FTB Quests 1.20.1 speichert Kapitel-/Questtitel und Untertitel in diesem Lokalisierungsfile; die SNBT-Kapiteldatei enthält IDs, Aufgaben, Abhängigkeiten und Belohnungen.
"""
    readme_path.write_text(readme_text, encoding="utf-8")
