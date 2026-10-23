#!/usr/bin/env python3
"""Add the first complete crop-waste -> compost -> crop-growth loop and clearer machine feedback."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, re, sys

ROOT = Path(sys.argv[1]).resolve()
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip(), encoding="utf-8")

def require_replace(path, old, new, label):
    p = ROOT / path
    s = p.read_text(encoding="utf-8")
    if new in s:
        return
    if old not in s:
        raise SystemExit(f"Cannot apply {label}: source context was not found in {path}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# --- Mycelium compost: a real reusable crop-growth item, not decorative loot. ---
item_path = SRC / "registry/ModItems.java"
s = item_path.read_text(encoding="utf-8")
if "MYZELKOMPOST" not in s:
    if "import de.sporenwerk.item.WurzelkonzentratItem;" in s:
        s = s.replace("import de.sporenwerk.item.WurzelkonzentratItem;",
                      "import de.sporenwerk.item.WurzelkonzentratItem;\nimport de.sporenwerk.item.MyzelkompostItem;", 1)
    elif "import de.sporenwerk.item.FeldhandbuchItem;" in s:
        s = s.replace("import de.sporenwerk.item.FeldhandbuchItem;",
                      "import de.sporenwerk.item.FeldhandbuchItem;\nimport de.sporenwerk.item.MyzelkompostItem;", 1)
    else:
        raise SystemExit("Could not find item import insertion point for Myzelkompost")
    lines = s.splitlines()
    insert_index = next((i + 1 for i, line in enumerate(lines) if "WURZELKONZENTRAT" in line), None)
    if insert_index is None:
        insert_index = next((i + 1 for i, line in enumerate(lines) if "PFLANZENRESTE" in line), None)
    if insert_index is None:
        raise SystemExit("Could not find item registration insertion point for Myzelkompost")
    lines.insert(insert_index, '    public static final RegistryObject<Item> MYZELKOMPOST = ITEMS.register("myzelkompost", () -> new MyzelkompostItem(new Item.Properties().stacksTo(64)));')
    item_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

write("src/main/java/de/sporenwerk/item/MyzelkompostItem.java", '''
package de.sporenwerk.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.BoneMealItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/**
 * Craftable farm by-product. Inherits vanilla bone-meal targeting and growth behavior,
 * so it can fertilize Sporenwerk crops and vanilla plants without custom world mutation.
 */
public final class MyzelkompostItem extends BoneMealItem {
    public MyzelkompostItem(Properties properties) { super(properties); }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.myzelkompost.effect")
                .withStyle(ChatFormatting.GREEN));
        tooltip.add(Component.translatable("tooltip.sporenwerk.myzelkompost.source")
                .withStyle(ChatFormatting.GRAY));
    }
}
''')

# The creative tab needs to surface the item naturally with crop-processing items.
creative_path = SRC / "registry/ModCreativeTabs.java"
cs = creative_path.read_text(encoding="utf-8")
if "ModItems.MYZELKOMPOST.get()" not in cs:
    markers = [
        "output.accept(ModItems.PFLANZENRESTE.get());",
        "output.accept(ModItems.WURZELKONZENTRAT.get());",
        "output.accept(ModItems.FELDHANDBUCH.get());"
    ]
    marker = next((m for m in markers if m in cs), None)
    if marker is None:
        raise SystemExit("Could not add Myzelkompost to the Sporenwerk creative tab")
    cs = cs.replace(marker, marker + "\n                        output.accept(ModItems.MYZELKOMPOST.get());", 1)
    creative_path.write_text(cs, encoding="utf-8")

write("src/main/resources/assets/sporenwerk/models/item/myzelkompost.json", '''
{
  "parent": "minecraft:item/generated",
  "textures": { "layer0": "sporenwerk:item/myzelkompost" }
}
''')

# Cohesive pixel-art icon: pressed compost cake, pale mycelium fibers, amber nutrient specks.
im = Image.new("RGBA", (32, 32), (0,0,0,0))
d = ImageDraw.Draw(im)
outline=(19,29,25,255); dark=(41,59,42,255); moss=(72,111,67,255)
green=(117,155,83,255); pale=(206,218,153,255); cream=(241,218,155,255)
amber=(221,157,58,255); rust=(136,83,44,255)
d.polygon([(5,17),(9,10),(15,8),(22,10),(27,16),(25,23),(20,27),(10,25)], fill=outline)
d.polygon([(7,17),(10,12),(15,10),(21,12),(25,17),(23,22),(19,25),(11,23)], fill=dark)
d.polygon([(8,16),(12,12),(17,12),(22,15),(23,18),(19,22),(12,21)], fill=moss)
d.polygon([(11,15),(14,13),(18,14),(20,17),(17,20),(13,19)], fill=green)
d.line([(9,18),(13,16),(16,18),(19,15),(22,18)], fill=pale, width=2)
d.rectangle((13,13,14,14), fill=cream)
d.rectangle((17,17,18,18), fill=amber)
d.rectangle((10,20,11,21), fill=rust)
d.rectangle((21,13,22,14), fill=amber)
for x,y in [(9,8),(13,6),(20,7),(24,10),(6,21),(25,21),(16,25)]:
    d.rectangle((x,y,x+1,y+1), fill=cream if y < 15 else green)
(ASSETS / "textures/item").mkdir(parents=True, exist_ok=True)
im.save(ASSETS / "textures/item/myzelkompost.png", optimize=True)

write("src/main/resources/data/sporenwerk/recipes/myzelkompost.json", '''
{
  "type": "minecraft:crafting_shapeless",
  "ingredients": [
    { "item": "sporenwerk:pflanzenreste" },
    { "item": "sporenwerk:pflanzenreste" },
    { "item": "sporenwerk:biomasse" }
  ],
  "result": { "item": "sporenwerk:myzelkompost", "count": 2 }
}
''')

# Mature crops sometimes provide waste; early immature harvests do not flood inventory with residue.
max_ages = {"faserrohr": 5, "bernsteinkappe": 3, "rotwurzel": 7, "filtermoos": 4}
for crop, age in max_ages.items():
    path = RES / f"data/sporenwerk/loot_tables/blocks/{crop}.json"
    loot = json.loads(path.read_text(encoding="utf-8"))
    already = any(
        any(e.get("name") == "sporenwerk:pflanzenreste" for e in pool.get("entries", []))
        for pool in loot.get("pools", [])
    )
    if not already:
        loot.setdefault("pools", []).append({
            "rolls": 1.0,
            "conditions": [
                {"condition": "minecraft:block_state_property", "block": f"sporenwerk:{crop}", "properties": {"age": str(age)}},
                {"condition": "minecraft:random_chance", "chance": 0.35}
            ],
            "entries": [{"type": "minecraft:item", "name": "sporenwerk:pflanzenreste"}]
        })
    path.write_text(json.dumps(loot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Localization and small recipe discovery hints.
de_path = ASSETS / "lang/de_de.json"
de = json.loads(de_path.read_text(encoding="utf-8"))
de.update({
    "item.sporenwerk.myzelkompost": "Myzelkompost",
    "tooltip.sporenwerk.myzelkompost.effect": "Düngt eine Pflanze wie Knochenmehl.",
    "tooltip.sporenwerk.myzelkompost.source": "Aus Pflanzenresten und Biomasse gepresst.",
    "gui.sporenwerk.machine.input_count": "Eingabe: %s Items",
    "gui.sporenwerk.machine.output_count": "Puffer: %s / 512 Items",
    "gui.sporenwerk.machine.status.idle": "WARTE AUF ZUTATEN",
    "gui.sporenwerk.machine.status.running": "PRODUKTION LÄUFT",
    "gui.sporenwerk.machine.status.power": "FE NACHLADEN",
    "gui.sporenwerk.machine.status.output": "AUSGABEPUFFER VOLL",
    "gui.sporenwerk.machine.status.ready": "ZYKLUS ABGESCHLOSSEN"
})
de_path.write_text(json.dumps(de, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

en_path = ASSETS / "lang/en_us.json"
en = json.loads(en_path.read_text(encoding="utf-8"))
en.update({
    "item.sporenwerk.myzelkompost": "Mycelium Compost",
    "tooltip.sporenwerk.myzelkompost.effect": "Fertilizes a plant like bone meal.",
    "tooltip.sporenwerk.myzelkompost.source": "Pressed from plant residue and biomass.",
    "gui.sporenwerk.machine.input_count": "Input: %s items",
    "gui.sporenwerk.machine.output_count": "Buffer: %s / 512 items",
    "gui.sporenwerk.machine.status.idle": "WAITING FOR INPUT",
    "gui.sporenwerk.machine.status.running": "PROCESSING",
    "gui.sporenwerk.machine.status.power": "NEEDS FE",
    "gui.sporenwerk.machine.status.output": "OUTPUT BUFFER FULL",
    "gui.sporenwerk.machine.status.ready": "CYCLE COMPLETE"
})
en_path.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# A five-chapter journal/advancement tree should teach the fertilizer loop, not just name it.
compost_advancement = {
    "parent": "sporenwerk:first_crop",
    "display": {
        "icon": {"item": "sporenwerk:myzelkompost"},
        "title": {"translate": "advancements.sporenwerk.compost_loop.title"},
        "description": {"translate": "advancements.sporenwerk.compost_loop.description"},
        "frame": "task",
        "show_toast": True,
        "announce_to_chat": False
    },
    "criteria": {
        "craft_compost": {
            "trigger": "minecraft:inventory_changed",
            "conditions": {"items": [{"items": ["sporenwerk:myzelkompost"]}]}
        },
        "use_compost": {
            "trigger": "minecraft:item_used_on_block",
            "conditions": {
                "item": {"items": ["sporenwerk:myzelkompost"]},
                "location": {"block": {"blocks": ["sporenwerk:faserrohr", "sporenwerk:bernsteinkappe", "sporenwerk:rotwurzel", "sporenwerk:filtermoos"]}}
            }
        }
    },
    "requirements": [["craft_compost"], ["use_compost"]],
    "rewards": {"loot": ["sporenwerk:quests/nichts_verkommt"]}
}
write("src/main/resources/data/sporenwerk/advancements/compost_loop.json",
      json.dumps(compost_advancement, ensure_ascii=False, indent=2) + "\n")
de.update({
    "advancements.sporenwerk.compost_loop.title": "Der Kreislauf schließt sich",
    "advancements.sporenwerk.compost_loop.description": "Stelle Myzelkompost her und dünge eine Nutzpflanze."
})
en.update({
    "advancements.sporenwerk.compost_loop.title": "Closing the Loop",
    "advancements.sporenwerk.compost_loop.description": "Craft mycelium compost and fertilize a crop."
})
de_path.write_text(json.dumps(de, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
en_path.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Add output/input counts and useful state text to the machine screen using the synced menu slots.
menu_path = SRC / "client/menu/MachineMenu.java"
ms = menu_path.read_text(encoding="utf-8")
if "public int inputItemCount()" not in ms:
    marker = "    public int progress() { return data.get(0); }"
    methods = '''    public int inputItemCount() {
        int count = 0;
        for (int i = 0; i < 4; i++) count += slots.get(i).getItem().getCount();
        return count;
    }

    public int outputItemCount() {
        int count = 0;
        for (int i = 4; i < 12; i++) count += slots.get(i).getItem().getCount();
        return count;
    }

    public int outputOccupiedSlots() {
        int count = 0;
        for (int i = 4; i < 12; i++) if (!slots.get(i).getItem().isEmpty()) count++;
        return count;
    }

    public boolean outputBufferFull() {
        for (int i = 4; i < 12; i++) {
            net.minecraft.world.item.ItemStack stack = slots.get(i).getItem();
            if (stack.isEmpty() || stack.getCount() < stack.getMaxStackSize()) return false;
        }
        return true;
    }

    public boolean hasMachineInput() { return inputItemCount() > 0; }

    public int requiredEnergy() {
        return switch (machineType()) {
            case "feldsammler" -> 20;
            case "saatgutpresse" -> 50;
            case "biomasse_bioreaktor" -> 80;
            default -> 0;
        };
    }

    public String statusKey() {
        if (outputBufferFull()) return "output";
        if (!hasMachineInput()) return "idle";
        if (net.minecraftforge.fml.ModList.get().isLoaded("mekanism") && energyFe() < requiredEnergy()) return "power";
        return progress() >= 100 ? "ready" : "running";
    }

'''
    if marker not in ms:
        raise SystemExit("Could not enhance machine menu: progress getter not found")
    ms = ms.replace(marker, methods + marker, 1)
    menu_path.write_text(ms, encoding="utf-8")

# Replace the previous fixed generic label with contextual machine text and real buffer counts.
screen_path = SRC / "client/menu/MachineScreen.java"
screen = screen_path.read_text(encoding="utf-8")
old = '''        g.drawString(font, Component.literal(menu.progress() >= 100 ? "BEREIT" : "ARBEITET " + menu.progress() + "%"),
                12, 70, 0xFFE7D9A5, false);'''
new = '''        g.drawString(font, Component.literal("INPUT " + menu.inputItemCount() + "  /  OUTPUT " + menu.outputItemCount() + "/512"),
                12, 62, 0xFFB8D0B2, false);
        String status = Component.translatable("gui.sporenwerk.machine.status." + menu.statusKey()).getString();
        g.drawString(font, Component.literal(status + " · " + menu.progress() + "%"),
                12, 70, menu.statusKey().equals("power") || menu.statusKey().equals("output") ? 0xFFE78E7D : 0xFFE7D9A5, false);'''
if old in screen:
    screen = screen.replace(old, new, 1)
elif 'menu.statusKey()' not in screen:
    raise SystemExit("Could not update machine screen status labels")
screen_path.write_text(screen, encoding="utf-8")

# Version and readme for this coherent gameplay milestone.
build = ROOT / "build.gradle"
bs = build.read_text(encoding="utf-8")
bs = re.sub(r"version = '[^']+'", "version = '1.2.0'", bs, count=1)
build.write_text(bs, encoding="utf-8")
readme = ROOT / "README.md"
rs = readme.read_text(encoding="utf-8")
rs = re.sub(r"1\.1\.\d+", "1.2.0", rs)
rs += """
\n## 1.2.0 — crop-waste loop and contextual machines
Mature crops have a 35% chance to yield plant residue, preserving higher value for harvested produce while making the by-product loop sustainable. Two residues plus one biomass craft into two Mycelium Compost. Myzelkompost inherits vanilla bone-meal behavior and can fertilize Sporenwerk or vanilla crops. The machine screen now reports input/output inventory totals and a contextual idle/processing/energy/buffer state.
"""
readme.write_text(rs, encoding="utf-8")

# Quick semantic checks catch accidental asset omissions before the full Forge build.
for rel in [
    "src/main/resources/assets/sporenwerk/models/item/myzelkompost.json",
    "src/main/resources/data/sporenwerk/recipes/myzelkompost.json",
    "src/main/resources/data/sporenwerk/advancements/compost_loop.json"
]:
    json.loads((ROOT / rel).read_text(encoding="utf-8"))
for crop, age in max_ages.items():
    loot=json.loads((RES/f"data/sporenwerk/loot_tables/blocks/{crop}.json").read_text(encoding="utf-8"))
    if not any(any(e.get("name")=="sporenwerk:pflanzenreste" for e in p.get("entries",[])) for p in loot.get("pools",[])):
        raise SystemExit(f"Missing crop-waste loot for {crop}")
if not (ASSETS/"textures/item/myzelkompost.png").is_file():
    raise SystemExit("Myzelkompost texture was not generated")
print("Sporenwerk 1.2.0 compost loop and machine status UI generated.")
