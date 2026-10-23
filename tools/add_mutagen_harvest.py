#!/usr/bin/env python3
"""Make active Mutagen Nodes create a controlled crop by-product and close the reactor loop."""
from pathlib import Path
import json, re, sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")

def insert_after(path, anchor, addition, label):
    source_path = ROOT / path
    source = source_path.read_text(encoding="utf-8")
    if addition in source:
        return
    if anchor not in source:
        raise SystemExit(f"Mutagen harvest patch cannot locate {label} in {path}")
    source_path.write_text(source.replace(anchor, anchor + addition, 1), encoding="utf-8")

# Register the by-product in the same registry and inventory tab as the other mod resources.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
if "import de.sporenwerk.item.MutageneSporenItem;" not in items:
    anchor = "import de.sporenwerk.item.MutagenExtractItem;"
    if anchor not in items:
        raise SystemExit("Cannot locate MutagenExtractItem import")
    items = items.replace(anchor, anchor + "\nimport de.sporenwerk.item.MutageneSporenItem;", 1)
if "MUTAGENE_SPOREN" not in items:
    anchor = '    public static final RegistryObject<Item> MUTAGENEXTRAKT = ITEMS.register("mutagenextrakt", () -> new MutagenExtractItem(new Item.Properties().stacksTo(16)));'
    field = anchor + '\n    public static final RegistryObject<Item> MUTAGENE_SPOREN = ITEMS.register("mutagene_sporen", () -> new MutageneSporenItem(new Item.Properties().stacksTo(64)));'
    if anchor not in items:
        raise SystemExit("Cannot locate Mutagen Extract item registration")
    items = items.replace(anchor, field, 1)
items_path.write_text(items, encoding="utf-8")

write("src/main/java/de/sporenwerk/item/MutageneSporenItem.java", """
package de.sporenwerk.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/** A useful field by-product: active Mutagen Nodes provoke extra spores from mature crops. */
public final class MutageneSporenItem extends Item {
    public MutageneSporenItem(Properties properties) { super(properties); }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagene_sporen.1").withStyle(ChatFormatting.DARK_PURPLE));
        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagene_sporen.2").withStyle(ChatFormatting.AQUA));
    }
}
""")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
if "output.accept(ModItems.MUTAGENE_SPOREN.get());" not in creative:
    anchor = "output.accept(ModItems.MUTAGENEXTRAKT.get());"
    if anchor not in creative:
        raise SystemExit("Cannot locate Mutagen Extract in the creative catalogue")
    creative = creative.replace(anchor, anchor + "\n                        output.accept(ModItems.MUTAGENE_SPOREN.get());", 1)
creative_path.write_text(creative, encoding="utf-8")

# Persisted active-source registry is the authority for field membership; healed/stopped fields cannot yield spores.
nodes_path = SRC / "infection/MutationNodeData.java"
nodes = nodes_path.read_text(encoding="utf-8")
if "public boolean hasActiveFieldAt(BlockPos target, int radius, int halfHeight)" not in nodes:
    anchor = """    public boolean isActive(BlockPos pos) {
        return nodes.getOrDefault(pos.asLong(), false);
    }
"""
    method = anchor + """
    public boolean hasActiveFieldAt(BlockPos target, int radius, int halfHeight) {
        for (Map.Entry<Long, Boolean> entry : nodes.entrySet()) {
            if (!entry.getValue()) continue;
            BlockPos origin = BlockPos.of(entry.getKey());
            long dx = (long) target.getX() - origin.getX();
            long dz = (long) target.getZ() - origin.getZ();
            if (dx * dx + dz * dz <= (long) radius * radius
                    && Math.abs(target.getY() - origin.getY()) <= halfHeight) return true;
        }
        return false;
    }
"""
    if anchor not in nodes:
        raise SystemExit("Cannot locate active-node query in MutationNodeData")
    nodes_path.write_text(nodes.replace(anchor, method, 1), encoding="utf-8")

# Shared field predicate is used by manual crop drops and the automated collector.
field_path = SRC / "infection/MutationField.java"
field = field_path.read_text(encoding="utf-8")
if "import net.minecraft.world.level.Level;" not in field:
    anchor = "import net.minecraft.server.level.ServerLevel;"
    if anchor not in field: raise SystemExit("Cannot locate ServerLevel import in MutationField")
    field = field.replace(anchor, anchor + "\nimport net.minecraft.world.level.Level;", 1)
if "public static boolean isInActiveMutagenField(Level level, BlockPos target)" not in field:
    anchor = "    public static boolean insideBounds(BlockPos origin, BlockPos target) {"
    method = """    public static boolean isInActiveMutagenField(Level level, BlockPos target) {
        if (!(level instanceof ServerLevel serverLevel)) return false;
        return MutationNodeData.get(serverLevel).hasActiveFieldAt(target, RADIUS, INFECTION_HALF_HEIGHT)
                && !hasAnchor(serverLevel, target);
    }

"""
    if anchor not in field: raise SystemExit("Cannot locate MutationField bounds method")
    field = field.replace(anchor, method + anchor, 1)
field_path.write_text(field, encoding="utf-8")

# Manual harvesting gets a 22% extra-spore chance only inside an active Mutagen field.
crop_path = SRC / "block/crop/AbstractSporeCropBlock.java"
crop = crop_path.read_text(encoding="utf-8")
crop_imports = [
    "import de.sporenwerk.infection.MutationField;",
    "import de.sporenwerk.registry.ModItems;"
]
for imp in crop_imports:
    if imp not in crop:
        package_line = "package de.sporenwerk.block.crop;"
        if package_line not in crop: raise SystemExit("Cannot locate crop package declaration")
        crop = crop.replace(package_line, package_line + "\n\n" + imp, 1)
drop_line = "Block.popResource(level, pos, new ItemStack(produceItem(), produceCount));"
spore_drop = drop_line + """
        if (MutationField.isInActiveMutagenField(level, pos) && level.random.nextFloat() < 0.22F) {
            Block.popResource(level, pos, new ItemStack(ModItems.MUTAGENE_SPOREN.get()));
        }"""
if "ModItems.MUTAGENE_SPOREN.get()" not in crop:
    if drop_line not in crop:
        raise SystemExit("Cannot locate mature-crop produce drop for Mutagen by-product")
    crop = crop.replace(drop_line, spore_drop, 1)
crop_path.write_text(crop, encoding="utf-8")

# Automated harvest performs the same roll and reserves every possible output before taking power or changing a crop.
be_path = SRC / "block/entity/MachineBlockEntity.java"
be = be_path.read_text(encoding="utf-8")
for imp in ("import de.sporenwerk.infection.MutationField;",):
    if imp not in be:
        package_line = "package de.sporenwerk.block.entity;"
        if package_line not in be: raise SystemExit("Cannot locate MachineBlockEntity package declaration")
        be = be.replace(package_line, package_line + "\n\n" + imp, 1)

old_outputs = """            boolean yieldsResidue = level.random.nextFloat() < 0.35F;
            ItemStack residue = yieldsResidue
                    ? new ItemStack(ModItems.PFLANZENRESTE.get())
                    : ItemStack.EMPTY;
            if (!canFitOutputs(output, residue)) { progress = 0; return; }
            if (!consumePower(20)) { progress = 0; return; }
            if (!insertOutputs(output, residue)) { progress = 0; return; }"""
new_outputs = """            boolean yieldsResidue = level.random.nextFloat() < 0.35F;
            ItemStack residue = yieldsResidue
                    ? new ItemStack(ModItems.PFLANZENRESTE.get())
                    : ItemStack.EMPTY;
            boolean yieldsMutagenSpores = MutationField.isInActiveMutagenField(level, target)
                    && level.random.nextFloat() < 0.22F;
            ItemStack mutagenSpores = yieldsMutagenSpores
                    ? new ItemStack(ModItems.MUTAGENE_SPOREN.get())
                    : ItemStack.EMPTY;
            if (!canFitOutputs(output, residue, mutagenSpores)) { progress = 0; return; }
            if (!consumePower(20)) { progress = 0; return; }
            if (!insertOutputs(output, residue, mutagenSpores)) { progress = 0; return; }"""
if "boolean yieldsMutagenSpores" not in be:
    if old_outputs not in be:
        raise SystemExit("Cannot locate the atomic collector produce/residue transaction")
    be = be.replace(old_outputs, new_outputs, 1)

# Mutagen spores are a more efficient late-game feedstock: three spores make two extracts.
if "input.is(ModItems.MUTAGENE_SPOREN.get())" not in be:
    anchor = "} else if (input.is(ModItems.MUTAGENPROBE.get())) {"
    branch = """} else if (input.is(ModItems.MUTAGENE_SPOREN.get())) {
            ItemStack extract = new ItemStack(ModItems.MUTAGENEXTRAKT.get(), 2);
            if (input.getCount() < 3 || !canFitOutput(extract) || !consumePower(150)) { progress = 0; return; }
            progress = 0;
            if (!insertOutput(extract)) return;
            inventory.extractItem(0, 3, false);
            storedPoints = Math.min(1_000_000, storedPoints + 30);
            skills.addCraft();
            setChanged();
        """ + anchor
    if anchor not in be:
        raise SystemExit("Cannot locate Mutagen Probe bioreactor transaction")
    be = be.replace(anchor, branch, 1)
be_path.write_text(be, encoding="utf-8")

# Keep the farming-loop regression aligned with the third possible output.
machine_test = ROOT / "tools/test_machine_farming_loop.py"
if machine_test.is_file():
    test = machine_test.read_text(encoding="utf-8")
    test = test.replace("canFitOutputs(output, residue)", "canFitOutputs(output, residue, mutagenSpores)")
    test = test.replace("insertOutputs(output, residue)", "insertOutputs(output, residue, mutagenSpores)")
    if "yieldsMutagenSpores" not in test:
        test += """
require("MutationField.isInActiveMutagenField(level, target)" in be,
        "automated fields must award the same controlled mutagen by-product")
require("canFitOutputs(output, residue, mutagenSpores)" in be
        and "insertOutputs(output, residue, mutagenSpores)" in be,
        "the collector must reserve room for the optional third output before consuming the crop")
"""
    machine_test.write_text(test, encoding="utf-8")

# The first harvested mutagen spore also adds a survival advancement and modest progression reward.
write("src/main/resources/data/sporenwerk/advancements/mutation_harvest.json", """
{
  "parent": "sporenwerk:mutagen_laboratory",
  "display": {
    "icon": { "item": "sporenwerk:mutagene_sporen" },
    "title": { "translate": "advancements.sporenwerk.mutation_harvest.title" },
    "description": { "translate": "advancements.sporenwerk.mutation_harvest.description" },
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "harvest_mutagen_spores": {
      "trigger": "minecraft:inventory_changed",
      "conditions": { "items": [{ "items": ["sporenwerk:mutagene_sporen"] }] }
    }
  },
  "requirements": [["harvest_mutagen_spores"]],
  "rewards": { "loot": ["sporenwerk:quests/mutation_harvest"] }
}
""")
write("src/main/resources/data/sporenwerk/loot_tables/quests/mutation_harvest.json", """
{
  "type": "minecraft:generic",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        { "type": "minecraft:item", "name": "sporenwerk:feldwissen", "functions": [{ "function": "minecraft:set_count", "count": 2 }] },
        { "type": "minecraft:item", "name": "sporenwerk:myzelkompost", "functions": [{ "function": "minecraft:set_count", "count": 2 }] }
      ]
    }
  ]
}
""")

for filename, values in [
    ("de_de.json", {
        "item.sporenwerk.mutagene_sporen": "Mutagene Sporen",
        "tooltip.sporenwerk.mutagene_sporen.1": "Entstehen gelegentlich bei der Ernte innerhalb eines aktiven Mutagenfeldes.",
        "tooltip.sporenwerk.mutagene_sporen.2": "Drei Sporen ergeben im Bioreaktor zwei Extrakte.",
        "advancements.sporenwerk.mutation_harvest.title": "Ernte mit Nebenwirkung",
        "advancements.sporenwerk.mutation_harvest.description": "Ernte erstmals mutagene Sporen in einem kontrollierten Feld."
    }),
    ("en_us.json", {
        "item.sporenwerk.mutagene_sporen": "Mutagenic Spores",
        "tooltip.sporenwerk.mutagene_sporen.1": "Occasionally harvested inside an active Mutagen field.",
        "tooltip.sporenwerk.mutagene_sporen.2": "Three spores produce two extracts in the bioreactor.",
        "advancements.sporenwerk.mutation_harvest.title": "An Unusual Harvest",
        "advancements.sporenwerk.mutation_harvest.description": "Harvest Mutagenic Spores in a controlled field for the first time."
    })
]:
    lang_path = RES / "assets/sporenwerk/lang" / filename
    lang = json.loads(lang_path.read_text(encoding="utf-8"))
    lang.update(values)
    lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

write("src/main/resources/assets/sporenwerk/models/item/mutagene_sporen.json", json.dumps({
    "parent": "minecraft:item/generated",
    "textures": {"layer0": "sporenwerk:item/mutagene_sporen"}
}, ensure_ascii=False, indent=2) + "\n")

# Clustered violet/teal spore texture with a transparent background.
tex = ASSETS / "textures/item"
tex.mkdir(parents=True, exist_ok=True)
image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
d = ImageDraw.Draw(image)
outline = (29, 35, 39, 255)
violet = (104, 51, 127, 255)
bright = (183, 111, 204, 255)
mint = (143, 232, 184, 255)
gold = (232, 203, 123, 255)
for x, y, r in [(8,17,4),(15,12,5),(22,17,4),(13,21,4),(21,23,3)]:
    d.ellipse((x-r, y-r, x+r, y+r), fill=outline)
    d.ellipse((x-r+1, y-r+1, x+r-1, y+r-1), fill=violet)
    d.ellipse((x-r+2, y-r+2, x-r+4, y-r+4), fill=bright)
for x,y in [(8,7),(22,8),(26,13),(5,23),(17,5),(25,25)]:
    d.rectangle((x,y,x+1,y+1), fill=mint if (x+y)%2 else gold)
d.line([(9,27),(13,25),(17,27),(21,26)], fill=mint, width=2)
image.save(tex / "mutagene_sporen.png", optimize=True)

write("tools/test_mutagen_harvest.py", r'''
from pathlib import Path
import json, sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Mutagen harvest regression: " + message)
items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
nodes = read("src/main/java/de/sporenwerk/infection/MutationNodeData.java")
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
crop = read("src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java")
machine = read("src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java")
require("MUTAGENE_SPOREN" in items and 'register("mutagene_sporen"' in items, "mutagen-spore item must be registered")
require("hasActiveFieldAt" in nodes and "entry.getValue()" in nodes, "field membership must use persistent active sources")
require("!hasAnchor(serverLevel, target)" in field, "healed zones must not produce mutagen spores")
require("MutationField.isInActiveMutagenField(level, pos)" in crop
        and "level.random.nextFloat() < 0.22F" in crop,
        "manual crop harvest must give the controlled 22% bonus chance")
require("MutationField.isInActiveMutagenField(level, target)" in machine
        and "canFitOutputs(output, residue, mutagenSpores)" in machine
        and "insertOutputs(output, residue, mutagenSpores)" in machine,
        "automated harvest must share the bonus and buffer every possible result atomically")
require("input.is(ModItems.MUTAGENE_SPOREN.get())" in machine
        and "new ItemStack(ModItems.MUTAGENEXTRAKT.get(), 2)" in machine
        and "inventory.extractItem(0, 3, false)" in machine
        and "consumePower(150)" in machine,
        "three spores must convert into two extracts with a real energy/input transaction")
adv = json.loads(read("src/main/resources/data/sporenwerk/advancements/mutation_harvest.json"))
require("sporenwerk:mutagene_sporen" in str(adv), "mutation harvest advancement must track the by-product")
for name in ("de_de.json", "en_us.json"):
    lang = json.loads(read(f"src/main/resources/assets/sporenwerk/lang/{name}"))
    require("item.sporenwerk.mutagene_sporen" in lang, name + " is missing the item name")
json.loads(read("src/main/resources/assets/sporenwerk/models/item/mutagene_sporen.json"))
require((root / "src/main/resources/assets/sporenwerk/textures/item/mutagene_sporen.png").is_file(), "spore icon missing")
print("Active-field crop by-products, atomic automated output, and spore-to-extract recycling passed.")
''')

build = ROOT / "build.gradle"
version = build.read_text(encoding="utf-8")
version = re.sub(r"version = '[^']+'", "version = '1.8.0'", version, count=1)
build.write_text(version, encoding="utf-8")
readme = ROOT / "README.md"
doc = readme.read_text(encoding="utf-8")
doc += """

## 1.8.0 — Mutagen harvest and resource recycling
- Active Mutagen fields occasionally produce Mutagenic Spores from both manual harvest and the automated Field Collector. Healing anchors and stopped sources suppress the bonus.
- The automated collector preflights output space for produce, residue and spores before consuming energy or changing crop state.
- The biomass bioreactor converts three Mutagenic Spores into two Stabilized Mutagen Extract for 150 FE and 30 Feldwissen. This is the renewable, infection-dependent late-game route after the first extract unlocks the field.
- A vanilla advancement rewards the first successful Mutagenic Spore harvest without requiring FTB Quests.
"""
readme.write_text(doc, encoding="utf-8")
print("Installed Sporenwerk 1.8.0 mutagenic harvest and recycling.")
