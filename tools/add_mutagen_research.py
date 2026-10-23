#!/usr/bin/env python3
"""Add a functional mutagen research-to-production chain and first-discovery story beat."""
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

def replace_once(path, old, new, label):
    file = ROOT / path
    source = file.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Mutagen research patch cannot find {label} in {path}")
    file.write_text(source.replace(old, new, 1), encoding="utf-8")

# Register items into the existing registry rather than building a parallel registry.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
for imp in (
    "import de.sporenwerk.item.MutagenProbeItem;",
    "import de.sporenwerk.item.MutagenExtractItem;"
):
    if imp not in items:
        anchor = "import de.sporenwerk.item.SterileCoreItem;"
        if anchor not in items:
            raise SystemExit("Cannot find SterileCoreItem import to extend ModItems")
        items = items.replace(anchor, anchor + "\n" + imp, 1)
if "MUTAGENPROBE" not in items:
    anchor = '    public static final RegistryObject<Item> STERILE_CORE = ITEMS.register("steriler_kern", () -> new SterileCoreItem(new Item.Properties().stacksTo(1)));'
    fields = anchor + """
    public static final RegistryObject<Item> MUTAGENPROBE = ITEMS.register("mutagenprobe", () -> new MutagenProbeItem(new Item.Properties().stacksTo(16)));
    public static final RegistryObject<Item> MUTAGENEXTRAKT = ITEMS.register("mutagenextrakt", () -> new MutagenExtractItem(new Item.Properties().stacksTo(16)));"""
    if anchor not in items:
        raise SystemExit("Cannot locate Sterile Core item registration")
    items = items.replace(anchor, fields, 1)
items_path.write_text(items, encoding="utf-8")

# New items explain their role in the production chain directly to players.
write("src/main/java/de/sporenwerk/item/MutagenProbeItem.java", """
package de.sporenwerk.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/** Sealed farm-grown sample. It is an input for the biomass bioreactor. */
public final class MutagenProbeItem extends Item {
    public MutagenProbeItem(Properties properties) { super(properties); }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagenprobe.1").withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagenprobe.2").withStyle(ChatFormatting.DARK_PURPLE));
    }
}
""")
write("src/main/java/de/sporenwerk/item/MutagenExtractItem.java", """
package de.sporenwerk.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/** Stable concentrate used by controlled-field devices and the world-ending artifact. */
public final class MutagenExtractItem extends Item {
    public MutagenExtractItem(Properties properties) { super(properties); }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagenextrakt.1").withStyle(ChatFormatting.AQUA));
        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagenextrakt.2").withStyle(ChatFormatting.DARK_PURPLE));
    }
}
""")

# Make both resources available in the same mod tab as the infection tools.
creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
if "output.accept(ModItems.MUTAGENPROBE.get());" not in creative:
    anchor = "output.accept(ModBlocks.SPORENRESISTENTER_BLOCK.get());"
    addition = anchor + "\n                        output.accept(ModItems.MUTAGENPROBE.get());\n                        output.accept(ModItems.MUTAGENEXTRAKT.get());"
    if anchor not in creative:
        raise SystemExit("Cannot locate the end of the infection-tool creative-tab entries")
    creative = creative.replace(anchor, addition, 1)
creative_path.write_text(creative, encoding="utf-8")

# Models and distinctive handmade pixel-art item icons.
for name in ("mutagenprobe", "mutagenextrakt"):
    write(f"src/main/resources/assets/sporenwerk/models/item/{name}.json", json.dumps({
        "parent": "minecraft:item/generated",
        "textures": {"layer0": f"sporenwerk:item/{name}"}
    }, ensure_ascii=False, indent=2) + "\n")
tex = ASSETS / "textures/item"
tex.mkdir(parents=True, exist_ok=True)
def save_probe(name, liquid, cap, accent):
    image = Image.new("RGBA", (32,32), (0,0,0,0))
    d = ImageDraw.Draw(image)
    outline=(22,29,30,255); glass=(154,191,176,230); shadow=(43,58,56,255)
    d.rectangle((12,3,19,7), fill=outline)
    d.rectangle((11,6,20,10), fill=cap)
    d.rectangle((9,10,22,27), fill=outline)
    d.rectangle((11,12,20,25), fill=glass)
    d.rectangle((12,18,19,24), fill=liquid)
    d.rectangle((13,13,15,16), fill=(240,250,219,255))
    d.rectangle((8,14,9,22), fill=shadow)
    d.rectangle((22,14,23,22), fill=shadow)
    d.polygon([(16,10),(19,14),(17,17),(14,15)], fill=accent)
    d.rectangle((15,20,17,22), fill=accent)
    image.save(tex / f"{name}.png", optimize=True)
save_probe("mutagenprobe", (135,70,151,255), (176,119,190,255), (229,177,92,255))
save_probe("mutagenextrakt", (52,174,156,255), (197,163,78,255), (196,248,209,255))

# The sealed probe is crafted from farm products and mineral glasswork.
write("src/main/resources/data/sporenwerk/recipes/mutagenprobe.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": [" M ", "RAR", " F "],
  "key": {
    "M": { "item": "sporenwerk:myzelkompost" },
    "R": { "item": "sporenwerk:rotwurzel" },
    "A": { "item": "minecraft:amethyst_shard" },
    "F": { "item": "minecraft:glass_bottle" }
  },
  "result": { "item": "sporenwerk:mutagenprobe", "count": 1 }
}
""")

# Actual machine transaction: input is consumed only after output room and power are secured.
be_path = SRC / "block/entity/MachineBlockEntity.java"
be = be_path.read_text(encoding="utf-8")
if "input.is(ModItems.MUTAGENPROBE.get())" not in be:
    anchor = "} else if (input.is(ModItems.BIOMASSE.get())) {"
    branch = """} else if (input.is(ModItems.MUTAGENPROBE.get())) {
            ItemStack extract = new ItemStack(ModItems.MUTAGENEXTRAKT.get());
            if (!canFitOutput(extract) || !consumePower(120)) { progress = 0; return; }
            progress = 0;
            if (!insertOutput(extract)) return;
            inventory.extractItem(0, 1, false);
            storedPoints = Math.min(1_000_000, storedPoints + 25);
            skills.addCraft();
            setChanged();
        """ + anchor
    if anchor not in be:
        raise SystemExit("Cannot locate the bioreactor biomass recipe branch")
    be = be.replace(anchor, branch, 1)
be_path.write_text(be, encoding="utf-8")

# The stable extract now matters to the entire controlled-infection progression.
write("src/main/resources/data/sporenwerk/recipes/infektionsherd.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["MAM", "RER", " M "],
  "key": {
    "M": { "item": "sporenwerk:myzelkompost" },
    "A": { "item": "minecraft:amethyst_shard" },
    "R": { "item": "sporenwerk:rotwurzel" },
    "E": { "item": "sporenwerk:mutagenextrakt" }
  },
  "result": { "item": "sporenwerk:infektionsherd", "count": 1 }
}
""")
write("src/main/resources/data/sporenwerk/recipes/mutationsanker.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["FAF", "AEA", "FAF"],
  "key": {
    "F": { "item": "sporenwerk:filtermoos" },
    "A": { "item": "minecraft:amethyst_shard" },
    "E": { "item": "sporenwerk:mutagenextrakt" }
  },
  "result": { "item": "sporenwerk:mutationsanker", "count": 1 }
}
""")
write("src/main/resources/data/sporenwerk/recipes/steriler_kern.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["DMD", "REF", "DMD"],
  "key": {
    "D": { "item": "minecraft:diamond" },
    "M": { "item": "sporenwerk:myzelkompost" },
    "R": { "item": "sporenwerk:rotwurzel" },
    "E": { "item": "sporenwerk:mutagenextrakt" },
    "F": { "item": "sporenwerk:filtermoos" }
  },
  "result": { "item": "sporenwerk:steriler_kern", "count": 1 }
}
""")

# A vanilla advancement makes research progress visible without requiring FTB Quests.
write("src/main/resources/data/sporenwerk/advancements/mutagen_laboratory.json", """
{
  "parent": "sporenwerk:field_behind_glass",
  "display": {
    "icon": { "item": "sporenwerk:mutagenextrakt" },
    "title": { "translate": "advancements.sporenwerk.mutagen_laboratory.title" },
    "description": { "translate": "advancements.sporenwerk.mutagen_laboratory.description" },
    "frame": "goal",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "extract_mutagen": {
      "trigger": "minecraft:inventory_changed",
      "conditions": { "items": [{ "items": ["sporenwerk:mutagenextrakt"] }] }
    }
  },
  "requirements": [["extract_mutagen"]],
  "rewards": { "loot": ["sporenwerk:quests/mutagen_laboratory"] }
}
""")
write("src/main/resources/data/sporenwerk/loot_tables/quests/mutagen_laboratory.json", """
{
  "type": "minecraft:generic",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        { "type": "minecraft:item", "name": "sporenwerk:myzelkompost", "functions": [{ "function": "minecraft:set_count", "count": 3 }] },
        { "type": "minecraft:item", "name": "sporenwerk:feldwissen", "functions": [{ "function": "minecraft:set_count", "count": 2 }] }
      ]
    }
  ]
}
""")

# One-time discovery sequence. It persists in player NBT and never fires every time the item is picked up.
event_path = SRC / "infection/InfectionEvents.java"
event_source = event_path.read_text(encoding="utf-8")
imports = [
    "import de.sporenwerk.registry.ModItems;",
    "import net.minecraft.nbt.CompoundTag;",
    "import net.minecraft.network.chat.Component;",
    "import net.minecraft.server.level.ServerPlayer;",
    "import net.minecraft.sounds.SoundEvents;",
    "import net.minecraft.sounds.SoundSource;",
    "import net.minecraft.world.item.ItemStack;",
    "import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;",
    "import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;",
    "import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;"
]
for imp in imports:
    if imp not in event_source:
        anchor = "import de.sporenwerk.entity.DaemmerlingEntity;"
        if anchor not in event_source:
            raise SystemExit("Cannot locate InfectionEvents import section")
        event_source = event_source.replace(anchor, anchor + "\n" + imp, 1)

call = "        tickMutagenDiscovery(player, level);"
if call not in event_source:
    anchor = "        if (player.isCreative() || player.isSpectator() || player.tickCount % 20 != 0) return;"
    if anchor not in event_source:
        raise SystemExit("Cannot locate player tick gate for the discovery sequence")
    event_source = event_source.replace(anchor, anchor + "\n" + call, 1)

method = """
    private static void tickMutagenDiscovery(Player player, ServerLevel level) {
        CompoundTag data = player.getPersistentData();
        if (!data.getBoolean("SporenwerkMutagenDiscoveryStarted")) {
            boolean hasExtract = false;
            for (ItemStack stack : player.getInventory().items) {
                if (stack.is(ModItems.MUTAGENEXTRAKT.get())) {
                    hasExtract = true;
                    break;
                }
            }
            if (!hasExtract) return;
            data.putBoolean("SporenwerkMutagenDiscoveryStarted", true);
            data.putInt("SporenwerkMutagenDiscoveryStage", 0);
            data.putLong("SporenwerkMutagenDiscoveryAt", level.getGameTime());
            return;
        }

        int stage = data.getInt("SporenwerkMutagenDiscoveryStage");
        long now = level.getGameTime();
        if (now < data.getLong("SporenwerkMutagenDiscoveryAt")) return;

        if (stage == 0 && player instanceof ServerPlayer serverPlayer) {
            serverPlayer.connection.send(new ClientboundSetTitlesAnimationPacket(10, 60, 15));
            serverPlayer.connection.send(new ClientboundSetTitleTextPacket(
                    Component.translatable("title.sporenwerk.mutagen.discovery")));
            serverPlayer.connection.send(new ClientboundSetSubtitleTextPacket(
                    Component.translatable("subtitle.sporenwerk.mutagen.discovery")));
            data.putInt("SporenwerkMutagenDiscoveryStage", 1);
            data.putLong("SporenwerkMutagenDiscoveryAt", now + 60);
        } else if (stage == 1) {
            player.displayClientMessage(Component.translatable("message.sporenwerk.mutagen.discovery.log"), false);
            data.putInt("SporenwerkMutagenDiscoveryStage", 2);
            data.putLong("SporenwerkMutagenDiscoveryAt", now + 20);
        } else if (stage == 2) {
            player.playNotifySound(SoundEvents.AMETHYST_BLOCK_CHIME.value(), SoundSource.PLAYERS, 0.65F, 0.72F);
            player.displayClientMessage(Component.translatable("message.sporenwerk.mutagen.discovery.hint"), false);
            data.putInt("SporenwerkMutagenDiscoveryStage", 3);
        }
    }
"""
if "private static void tickMutagenDiscovery(Player player, ServerLevel level)" not in event_source:
    index = event_source.rfind("}")
    if index < 0: raise SystemExit("Cannot find InfectionEvents class end")
    event_source = event_source[:index] + method + "\n" + event_source[index:]
event_path.write_text(event_source, encoding="utf-8")

# Localize every new item and the discovery scene.
locales = {
    "de_de.json": {
        "item.sporenwerk.mutagenprobe": "Versiegelte Mutagenprobe",
        "item.sporenwerk.mutagenextrakt": "Stabilisiertes Mutagenextrakt",
        "tooltip.sporenwerk.mutagenprobe.1": "Eine Feldkultur aus Kompost und Wurzelgewebe.",
        "tooltip.sporenwerk.mutagenprobe.2": "Im Biomasse-Bioreaktor verarbeiten.",
        "tooltip.sporenwerk.mutagenextrakt.1": "Stabilisiert und für technische Anlagen geeignet.",
        "tooltip.sporenwerk.mutagenextrakt.2": "Bauteil für Mutagenherd, Mutationsanker und Sterilen Kern.",
        "advancements.sporenwerk.mutagen_laboratory.title": "Die Probe lebt",
        "advancements.sporenwerk.mutagen_laboratory.description": "Verarbeite deine erste Mutagenprobe zu stabilem Extrakt.",
        "title.sporenwerk.mutagen.discovery": "ERSTE MUTAGENKULTUR",
        "subtitle.sporenwerk.mutagen.discovery": "Das Extrakt reagiert auf deine Anwesenheit.",
        "message.sporenwerk.mutagen.discovery.log": "FELDPROTOKOLL 05: Die Probe ist nicht stabil. Sie versucht, sich mit etwas in der Nähe zu synchronisieren.",
        "message.sporenwerk.mutagen.discovery.hint": "Der Bioreaktor kann weitere Proben verarbeiten. Halte Mutagenherde in kontrollierten Bereichen."
    },
    "en_us.json": {
        "item.sporenwerk.mutagenprobe": "Sealed Mutagen Sample",
        "item.sporenwerk.mutagenextrakt": "Stabilized Mutagen Extract",
        "tooltip.sporenwerk.mutagenprobe.1": "A field culture made from compost and root tissue.",
        "tooltip.sporenwerk.mutagenprobe.2": "Process it in the Biomass Bioreactor.",
        "tooltip.sporenwerk.mutagenextrakt.1": "Stabilized and suitable for technical devices.",
        "tooltip.sporenwerk.mutagenextrakt.2": "Required for a Mutagen Node, Mutation Anchor and Sterile Core.",
        "advancements.sporenwerk.mutagen_laboratory.title": "The Sample Is Alive",
        "advancements.sporenwerk.mutagen_laboratory.description": "Process your first Mutagen Sample into a stable extract.",
        "title.sporenwerk.mutagen.discovery": "FIRST MUTAGEN CULTURE",
        "subtitle.sporenwerk.mutagen.discovery": "The extract reacts to your presence.",
        "message.sporenwerk.mutagen.discovery.log": "FIELD LOG 05: The sample is unstable. It is attempting to synchronize with something nearby.",
        "message.sporenwerk.mutagen.discovery.hint": "The bioreactor can process more samples. Keep Mutagen Nodes inside controlled areas."
    }
}
for filename, additions in locales.items():
    path = RES / "assets/sporenwerk/lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Regression tests follow actual production transactions, recipe gates, story trigger and localization.
write("tools/test_mutagen_research.py", r'''
from pathlib import Path
import json, sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Mutagen research regression: " + message)
items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
machine = read("src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java")
events = read("src/main/java/de/sporenwerk/infection/InfectionEvents.java")
blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
require("MUTAGENPROBE" in items and 'register("mutagenprobe"' in items, "probe must be registered")
require("MUTAGENEXTRAKT" in items and 'register("mutagenextrakt"' in items, "extract must be registered")
require("input.is(ModItems.MUTAGENPROBE.get())" in machine
        and "new ItemStack(ModItems.MUTAGENEXTRAKT.get())" in machine,
        "bioreactor must convert probe into extract")
require("consumePower(120)" in machine and "inventory.extractItem(0, 1, false)" in machine
        and "storedPoints = Math.min(1_000_000, storedPoints + 25)" in machine,
        "extract production must spend energy, consume input and award progress")
for name in ("mutagenprobe", "infektionsherd", "mutationsanker", "steriler_kern"):
    json.loads((root / f"src/main/resources/data/sporenwerk/recipes/{name}.json").read_text(encoding="utf-8"))
for name in ("mutagenprobe", "mutagenextrakt"):
    json.loads((root / f"src/main/resources/assets/sporenwerk/models/item/{name}.json").read_text(encoding="utf-8"))
    require((root / f"src/main/resources/assets/sporenwerk/textures/item/{name}.png").is_file(), name + " texture missing")
advancement = json.loads(read("src/main/resources/data/sporenwerk/advancements/mutagen_laboratory.json"))
require("sporenwerk:mutagenextrakt" in str(advancement), "research advancement must unlock on the extract")
require("tickMutagenDiscovery(player, level)" in events
        and "SporenwerkMutagenDiscoveryStarted" in events
        and "ClientboundSetTitleTextPacket" in events, "first-extract discovery sequence must be one-time and persistent")
require("mutagenextrakt" in read("src/main/resources/assets/sporenwerk/lang/de_de.json")
        and "mutagenextrakt" in read("src/main/resources/assets/sporenwerk/lang/en_us.json"),
        "both locale files must contain the new research items")
print("Mutagen sample-to-extract production, endgame recipe gates and first-discovery story event passed.")
''')

build = ROOT / "build.gradle"
build_text = build.read_text(encoding="utf-8")
build_text = re.sub(r"version = '[^']+'", "version = '1.7.0'", build_text, count=1)
build.write_text(build_text, encoding="utf-8")
readme = ROOT / "README.md"
doc = readme.read_text(encoding="utf-8")
doc += """

## 1.7.0 — Mutagen research and production chain
- Craft a sealed Mutagen Probe from Mycelium Compost, Rotwurzel, an Amethyst Shard and a glass bottle.
- Process the probe in the Biomass Bioreactor. Each cycle consumes one probe and 120 FE, produces one Stabilized Mutagen Extract and awards 25 Feldwissen.
- Stable extract is now required to craft a Mutagen Node, Mutation Anchor and Sterile Core. That ties controlled infection, local healing and the endgame into one material progression.
- The first time a player obtains extract, a persistent three-stage discovery sequence appears with a title, field-log message and sound cue. The sequence is not a camera-cutscene; it is an in-game narrative beat and plays only once per player.
- A vanilla advancement and reward crate record the first successful extraction. FTB Quests remains optional.
"""
readme.write_text(doc, encoding="utf-8")
print("Installed Sporenwerk 1.7.0 mutagen research and production chain.")
