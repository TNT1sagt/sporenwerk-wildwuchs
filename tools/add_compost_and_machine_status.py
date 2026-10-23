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

# The bioreactor turns processed biomass into a tangible growing resource.
be_path = SRC / "block/entity/MachineBlockEntity.java"
be = be_path.read_text(encoding="utf-8")
old_branch = '''} else if (input.is(ModItems.BIOMASSE.get())) {
            ItemStack medicine = new ItemStack(ModItems.WURZELKONZENTRAT.get());
            if (!canFitOutput(medicine) || !consumePower(80)) { progress = 0; return; }
            progress = 0;
            if (!insertOutput(medicine)) return;
            inventory.extractItem(0, 1, false);
            storedPoints = Math.min(1_000_000, storedPoints + 10);
            skills.addCraft();
            setChanged();
        } else progress = 0;'''
new_branch = '''} else if (input.is(ModItems.BIOMASSE.get())) {
            ItemStack compost = new ItemStack(ModItems.MYZELKOMPOST.get(), 2);
            if (!canFitOutput(compost) || !consumePower(80)) { progress = 0; return; }
            progress = 0;
            if (!insertOutput(compost)) return;
            inventory.extractItem(0, 1, false);
            storedPoints = Math.min(1_000_000, storedPoints + 10);
            skills.addCraft();
            setChanged();
        } else progress = 0;'''
if old_branch in be:
    be = be.replace(old_branch,new_branch,1)
elif "new ItemStack(ModItems.MYZELKOMPOST.get(), 2)" not in be:
    raise SystemExit("Could not update the bioreactor's second production step")
be_path.write_text(be,encoding="utf-8")

# Keep the mechanical contract test aligned with the named bioreactor output.
test_path = ROOT / "tools/test_machine_io_contract.py"
if test_path.exists():
    ts = test_path.read_text(encoding="utf-8")
    ts = ts.replace("ModItems.WURZELKONZENTRAT.get()", "ModItems.MYZELKOMPOST.get()")
    ts = ts.replace("biomass processing must return a usable Rotwurzel-Konzentrat item",
                    "biomass processing must return usable Myzelkompost")
    test_path.write_text(ts,encoding="utf-8")


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
    "gui.sporenwerk.machine.input_count": "Eingabe %s",
    "gui.sporenwerk.machine.output_count": "Puffer %s/512",
    "gui.sporenwerk.machine.status.idle": "WARTE AUF ZUTATEN",
    "gui.sporenwerk.machine.status.running": "PRODUKTION LÄUFT",
    "gui.sporenwerk.machine.status.power": "FE NACHLADEN",
    "gui.sporenwerk.machine.status.output": "AUSGABEPUFFER VOLL",
    "gui.sporenwerk.machine.status.ready": "ZYKLUS ABGESCHLOSSEN",
    "gui.sporenwerk.machine.status.scanning": "FELD WIRD GEPRÜFT"
})
de_path.write_text(json.dumps(de, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

en_path = ASSETS / "lang/en_us.json"
en = json.loads(en_path.read_text(encoding="utf-8"))
en.update({
    "item.sporenwerk.myzelkompost": "Mycelium Compost",
    "tooltip.sporenwerk.myzelkompost.effect": "Fertilizes a plant like bone meal.",
    "tooltip.sporenwerk.myzelkompost.source": "Pressed from plant residue and biomass.",
    "gui.sporenwerk.machine.input_count": "Input %s",
    "gui.sporenwerk.machine.output_count": "Buffer %s/512",
    "gui.sporenwerk.machine.status.idle": "WAITING FOR INPUT",
    "gui.sporenwerk.machine.status.running": "PROCESSING",
    "gui.sporenwerk.machine.status.power": "NEEDS FE",
    "gui.sporenwerk.machine.status.output": "OUTPUT BUFFER FULL",
    "gui.sporenwerk.machine.status.ready": "CYCLE COMPLETE",
    "gui.sporenwerk.machine.status.scanning": "SCANNING FIELD"
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

    public String machineType() {
        return machine.getBlockState().getBlock().builtInRegistryHolder().key().location().getPath();
    }

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
        if (machineType().equals("feldsammler")) return "scanning";
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
new = '''        g.drawString(font, Component.translatable("gui.sporenwerk.machine.input_count", menu.inputItemCount()),
                12, 62, 0xFFB8D0B2, false);
        g.drawString(font, Component.translatable("gui.sporenwerk.machine.output_count", menu.outputItemCount()),
                112, 62, 0xFFB8D0B2, false);
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

# Source-level regression test for the end-to-end crop-waste loop and optional integration boundaries.
test_script = r'''#!/usr/bin/env python3
from pathlib import Path
import json, sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
res = root / "src/main/resources"
src = root / "src/main/java/de/sporenwerk"

def require(ok, message):
    if not ok:
        raise SystemExit("Crop-loop regression: " + message)

expected_ages = {"faserrohr": 5, "bernsteinkappe": 3, "rotwurzel": 7, "filtermoos": 4}
for crop, age in expected_ages.items():
    loot = json.loads((res / f"data/sporenwerk/loot_tables/blocks/{crop}.json").read_text(encoding="utf-8"))
    residue = [pool for pool in loot.get("pools", [])
               if any(entry.get("name") == "sporenwerk:pflanzenreste" for entry in pool.get("entries", []))]
    require(residue, f"{crop} must yield occasional plant residue")
    require(any(any(cond.get("condition") == "minecraft:block_state_property"
                    and cond.get("properties", {}).get("age") == str(age)
                    for cond in pool.get("conditions", []))
                for pool in residue), f"{crop} residue must only drop at maturity")

compost_recipe = json.loads((res / "data/sporenwerk/recipes/myzelkompost.json").read_text(encoding="utf-8"))
require(compost_recipe.get("type") == "minecraft:crafting_shapeless", "compost recipe should be shapeless")
ingredients = [x.get("item") for x in compost_recipe.get("ingredients", [])]
require(ingredients.count("sporenwerk:pflanzenreste") == 2 and "sporenwerk:biomasse" in ingredients,
        "compost recipe must consume two residue and one biomass")
require(compost_recipe.get("result", {}).get("item") == "sporenwerk:myzelkompost",
        "compost recipe must produce Myzelkompost")

compost_item = (src / "item/MyzelkompostItem.java").read_text(encoding="utf-8")
require("extends BoneMealItem" in compost_item, "Myzelkompost must use vanilla fertilizer targeting/behavior")
be = (src / "block/entity/MachineBlockEntity.java").read_text(encoding="utf-8")
require("new ItemStack(ModItems.MYZELKOMPOST.get(), 2)" in be,
        "bioreactor biomass stage must output a usable fertilizer")
require("consumePower(80)" in be, "bioreactor's biomass stage must follow the FE policy")
menu = (src / "client/menu/MachineMenu.java").read_text(encoding="utf-8")
screen = (src / "client/menu/MachineScreen.java").read_text(encoding="utf-8")
for token in ["inputItemCount()", "outputItemCount()", "statusKey()", "outputBufferFull()"]:
    require(token in menu, f"machine screen state is missing {token}")
require("gui.sporenwerk.machine.status." in screen, "machine UI must show a translated actionable state")

de = json.loads((res / "assets/sporenwerk/lang/de_de.json").read_text(encoding="utf-8"))
en = json.loads((res / "assets/sporenwerk/lang/en_us.json").read_text(encoding="utf-8"))
for lang, name in [(de, "de_de"), (en, "en_us")]:
    require("item.sporenwerk.myzelkompost" in lang, f"{name} translation must include Myzelkompost")
    require("gui.sporenwerk.machine.status.scanning" in lang, f"{name} translation must include collector scanning status")

mods = (res / "META-INF/mods.toml").read_text(encoding="utf-8")
require('modId="mekanism"\n    mandatory=true' not in mods and 'modId="botania"\n    mandatory=true' not in mods,
        "Mekanism/Botania must not become hard dependencies")
for name in ["feldsammler_mekanism.json", "saatgutpresse_mekanism.json", "bioreaktor_mekanism.json",
             "feldsammler_botania.json", "saatgutpresse_botania.json", "bioreaktor_botania.json",
             "botania_mana_infused_filter.json"]:
    path = res / "data/sporenwerk/recipes" / name
    require(path.is_file(), f"optional compatibility recipe is missing: {name}")
    recipe = json.loads(path.read_text(encoding="utf-8"))
    require(recipe.get("type") == "forge:conditional", f"{name} must be conditionally registered")

quests = root / "extras/ftbquests/config/ftbquests/quests/chapters/sporenwerk_wildwuchs.snbt"
require(quests.is_file(), "optional FTB Quests import chapter is missing")
quest_text = quests.read_text(encoding="utf-8")
for title in ["Ein Stück Erde", "Nichts verkommt", "Die erste Maschine", "Eine größere Ernte", "Das Feld hinter dem Glas"]:
    require(title in quest_text, "FTB Quests chapter is missing: " + title)

config = (src / "SporenwerkConfig.java").read_text(encoding="utf-8")
horror = (src / "client/ClientHorrorEvents.java").read_text(encoding="utf-8")
require('.define("enablePhotoEvent", false)' in config, "photo fallback must default to disabled")
require("mc.getMainRenderTarget()" in horror, "photo fallback must capture only the Minecraft render target")
require("INGAME-FOTO_FALLBACK_" in horror, "fallback filename must be clear and unique")
print("Crop-loop, UI, optional-integration, quest, and horror-safety tests passed.")
'''

write("tools/test_crop_loop.py", test_script)

# Player-facing documentation: list usable systems and state limitations plainly.
write("README.md", '''
# Sporenwerk: Wildwuchs 1.2.0

**Minecraft Java Edition 1.20.1 · Forge 47.2.x · Java 17**

Sporenwerk is a farming and small-factory progression mod with a quiet psychological-horror layer. The core loop is designed around planting, harvesting, recycling by-products, improving machines and earning Field Knowledge. Combat remains weak and infrequent.

## Installation

1. Install Minecraft Java 1.20.1 with Forge 47.x and Java 17.
2. Download the built JAR named sporenwerk-1.2.0.jar.
3. Put the JAR into the instance's mods folder and launch the Forge profile.
4. Optional: import extras/ftbquests/config/ftbquests/quests/chapters/sporenwerk_wildwuchs.snbt into the matching FTB Quests config directory. Back up the existing quest config first. FTB Quests is not required to launch the mod.

## Farming loop

- **Faserrohr** is the quick fiber crop; **Bernsteinkappe** grows in fewer stages; **Rotwurzel** takes longer and supports the medicine loop; **Filtermoos** supports filters and decontamination recipes.
- Mature crops drop their primary produce and seeds. Mature harvests have a 35% chance to yield **Pflanzenreste**.
- Plant residue can be pressed or processed into **Biomasse**. Two residues plus one biomass craft into two **Myzelkompost**.
- Myzelkompost uses vanilla bone-meal targeting and can fertilize both Sporenwerk and vanilla plants.
- Rotwurzel, sugar and a glass bottle craft **Rotwurzel-Konzentrat**. It restores 4 health points (two hearts), has a five-second cooldown and returns an empty bottle.

## The three machines

Right-click any machine to open its custom inventory screen. Input slots are on the left; output buffers are on the right. Shift-click is supported. Buffers are stored in block-entity NBT and retain normal stack sizes; production does not spawn a cloud of item entities.

- **Feldsammler:** scans a 5×3×5 area, harvests mature Sporenwerk plants, adds yield according to the harvest branch, and resets the plant to its first growth stage when matching seed is supplied. Without matching seed, it removes the harvested crop.
- **Saatgutpresse:** converts harvests into matching seeds/spores and can turn plant residue into biomass.
- **Biomasse-Bioreaktor:** processes residue into biomass and biomass into two units of Myzelkompost. Its internal production value is kept in the machine rather than emitted as items.

Machine tooltips list the accepted inputs. The GUI shows input/output totals, progress, FE information and a translated machine state.

## Field Knowledge and upgrades

Field Knowledge comes from mature harvesting, first-time crop discovery, crafting and machine processing—not from kills. It and the three upgrade levels are saved in world SavedData.

- **Anbau:** each level increases the chance of a bonus vanilla growth tick, up to the configured cap.
- **Ernte:** the first level permanently adds one extra unit of produce; later levels increase that bonus and eventually add seed bonuses.
- **Maschinen:** reduces machine cycle times, with a minimum cycle length so the server cannot get stuck in an excessive tick loop.

Craft and use the **Feldhandbuch** to open the three-branch skill-tree screen. The server validates every purchase and persists the result. The commands /sporenwerk status and /sporenwerk upgrade anbau|ernte|maschinen are text fallbacks.

## Mekanism and Botania

Both integrations are optional; there is no hard runtime dependency on either mod.

- **Mekanism:** machines expose Forge Energy receive capability so Universal Cables can charge their internal FE buffer. When Mekanism is installed, production consumes FE; without Mekanism, the base progression remains self-contained and machines run autonomously. The external energy endpoint is receive-only.
- **Botania:** conditional Botania recipes are registered only when Botania is present, including a Mana Infusion path for filter material and alternate machine crafting recipes. The machines do not directly consume Mana from Mana Pools.

The normal crafting recipes remain available with neither integration installed.

## Quests and horror

The five optional FTB Quests chapters are: *Ein Stück Erde*, *Nichts verkommt*, *Die erste Maschine*, *Eine größere Ernte* and *Das Feld hinter dem Glas*. The data bundle targets the classic Forge 1.20.1 quest layout; verify it in a copy of the target modpack before publishing a pack.

Horror is local and non-destructive: a rare blank HUD rectangle appears twice, a quiet offset ambient sound can play, and an optional photo fallback can save the current Minecraft framebuffer. The fallback does **not** create a new camera angle or composite an avatar/creature and is disabled by default.

## Configuration and files

- Client config: config/sporenwerk-client.toml.
- World progression: the world's data/sporenwerk_progression.dat.
- Photo fallback: screenshots/sporenwerk/INGAME-FOTO_FALLBACK_*.png.
- The mod sends no telemetry and does not read, start or stop OS processes; it does not capture the desktop, camera or microphone.

## Build and validation

Build with JDK 17 and Gradle 8.8 using gradle --no-daemon clean build. The output is build/libs/sporenwerk-1.2.0.jar.

The automated pipeline validates JSON/model texture references, machine item/energy capability boundaries, crop-waste/compost production, localization, optional recipe conditions, quest content, and dedicated-server startup without Mekanism or Botania. This is not a substitute for graphical-client testing with the exact target modpack.

## Explicit limitations

- No seasons or crop-crossbreeding in this version.
- The photo feature is only a labeled current-view fallback, not the requested alternate-angle screenshot event.
- The creature uses a weak, familiar zombie-like AI rather than custom combat behavior.
- FTB Quests data must still be previewed against the exact FTB Quests build used by a pack.
''')
print("Generated German V1.2.0 README and crop-loop regression tests.")

print("Sporenwerk 1.2.0 compost loop and machine status UI generated.")
