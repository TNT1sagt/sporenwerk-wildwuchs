#!/usr/bin/env python3
"""Add the first server-authoritative infection progression and three meaningful choices."""
from pathlib import Path
import json, re, sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip(), encoding="utf-8")

def insert_once(path, old, new, label):
    p = ROOT / path
    s = p.read_text(encoding="utf-8")
    if new in s:
        return
    if old not in s:
        raise SystemExit(f"Cannot install infection system ({label}): context missing in {path}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# Register three real items. They all use the same server-side infection state.
items_path = "src/main/java/de/sporenwerk/registry/ModItems.java"
p = ROOT / items_path
s = p.read_text(encoding="utf-8")
for import_line in [
    "import de.sporenwerk.item.InfectionSerumItem;",
    "import de.sporenwerk.item.InfectionEmbraceItem;",
    "import de.sporenwerk.item.SterileCoreItem;"
]:
    if import_line not in s:
        anchor = "import de.sporenwerk.item.WurzelkonzentratItem;"
        if anchor not in s:
            anchor = "import de.sporenwerk.item.FeldhandbuchItem;"
        if anchor not in s:
            raise SystemExit("Cannot locate ModItems import anchor")
        s = s.replace(anchor, anchor + "\n" + import_line, 1)
if "INFECTION_SERUM" not in s:
    lines = s.splitlines()
    index = next((i + 1 for i, line in enumerate(lines) if "WURZELKONZENTRAT" in line), None)
    if index is None:
        index = next((i + 1 for i, line in enumerate(lines) if "MYZELKOMPOST" in line), None)
    if index is None:
        raise SystemExit("Cannot locate item registration anchor")
    lines[index:index] = [
        '    public static final RegistryObject<Item> INFECTION_SERUM = ITEMS.register("infektionsserum", () -> new InfectionSerumItem(new Item.Properties().stacksTo(16)));',
        '    public static final RegistryObject<Item> INFECTION_EMBRACE = ITEMS.register("infektionshingabe", () -> new InfectionEmbraceItem(new Item.Properties().stacksTo(1)));',
        '    public static final RegistryObject<Item> STERILE_CORE = ITEMS.register("steriler_kern", () -> new SterileCoreItem(new Item.Properties().stacksTo(1)));'
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Surface items in survival/creative inventory.
creative_path = SRC / "registry/ModCreativeTabs.java"
cs = creative_path.read_text(encoding="utf-8")
if "ModItems.INFECTION_SERUM.get()" not in cs:
    marker = next((m for m in [
        "output.accept(ModItems.WURZELKONZENTRAT.get());",
        "output.accept(ModItems.MYZELKOMPOST.get());",
        "output.accept(ModItems.FELDHANDBUCH.get());"
    ] if m in cs), None)
    if marker is None:
        raise SystemExit("Cannot locate creative tab insertion point for infection items")
    cs = cs.replace(marker, marker + "\n                        output.accept(ModItems.INFECTION_SERUM.get());\n                        output.accept(ModItems.INFECTION_EMBRACE.get());\n                        output.accept(ModItems.STERILE_CORE.get());", 1)
    creative_path.write_text(cs, encoding="utf-8")

write("src/main/java/de/sporenwerk/infection/InfectionWorldData.java", """
package de.sporenwerk.infection;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.saveddata.SavedData;

/** Persistent world-level endgame flag. Once sterilized, passive infection stops permanently. */
public final class InfectionWorldData extends SavedData {
    private static final String DATA_NAME = "sporenwerk_infection";
    private boolean sterilized;

    public static InfectionWorldData get(ServerLevel level) {
        ServerLevel overworld = level.getServer().overworld();
        return overworld.getDataStorage().computeIfAbsent(
                InfectionWorldData::load, InfectionWorldData::new, DATA_NAME);
    }

    public static InfectionWorldData load(CompoundTag tag) {
        InfectionWorldData data = new InfectionWorldData();
        data.sterilized = tag.getBoolean("Sterilized");
        return data;
    }

    public boolean isSterilized() { return sterilized; }

    public void sterilize() {
        if (!sterilized) {
            sterilized = true;
            setDirty();
        }
    }

    @Override
    public CompoundTag save(CompoundTag tag) {
        tag.putBoolean("Sterilized", sterilized);
        return tag;
    }
}
""")

write("src/main/java/de/sporenwerk/infection/InfectionState.java", """
package de.sporenwerk.infection;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.player.Player;

/** All player infection state is persisted in player NBT and changed on the logical server. */
public final class InfectionState {
    private static final String LEVEL = "SporenwerkInfection";
    private static final String SURRENDERED = "SporenwerkSurrendered";

    private InfectionState() {}

    public static int level(Player player) {
        return Math.max(0, Math.min(100, player.getPersistentData().getInt(LEVEL)));
    }

    public static void setLevel(Player player, int value) {
        player.getPersistentData().putInt(LEVEL, Math.max(0, Math.min(100, value)));
    }

    public static boolean surrendered(Player player) {
        return player.getPersistentData().getBoolean(SURRENDERED);
    }

    public static void surrender(Player player) {
        player.getPersistentData().putBoolean(SURRENDERED, true);
        setLevel(player, 100);
    }

    public static void cure(Player player, int amount) {
        setLevel(player, level(player) - Math.max(0, amount));
        if (level(player) == 0) {
            player.getPersistentData().remove(SURRENDERED);
        }
    }

    public static void clear(Player player) {
        setLevel(player, 0);
        player.getPersistentData().remove(SURRENDERED);
    }
}
""")

write("src/main/java/de/sporenwerk/infection/InfectionEvents.java", """
package de.sporenwerk.infection;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.DaemmerlingEntity;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Server-authoritative exposure: the rare Dämmerling is dangerous in darkness, not a constant debuff. */
@Mod.EventBusSubscriber(modid = Sporenwerk.MODID)
public final class InfectionEvents {
    private InfectionEvents() {}

    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || !(event.player.level() instanceof ServerLevel level)) return;
        Player player = event.player;
        if (player.isCreative() || player.isSpectator() || player.tickCount % 20 != 0) return;

        InfectionWorldData world = InfectionWorldData.get(level);
        int infection = InfectionState.level(player);
        if (world.isSterilized()) {
            if (infection > 0 && player.tickCount % 100 == 0) InfectionState.cure(player, 5);
            return;
        }

        boolean exposed = level.getMaxLocalRawBrightness(player.blockPosition()) < 8
                && !level.getEntitiesOfClass(DaemmerlingEntity.class,
                    player.getBoundingBox().inflate(6.0D), entity -> entity.isAlive()).isEmpty();

        if (exposed && player.tickCount % 100 == 0) {
            InfectionState.setLevel(player, infection + (InfectionState.surrendered(player) ? 2 : 1));
        } else if (!exposed && !InfectionState.surrendered(player)
                && infection > 0 && level.getMaxLocalRawBrightness(player.blockPosition()) >= 12
                && player.tickCount % 200 == 0) {
            InfectionState.cure(player, 1);
        }

        infection = InfectionState.level(player);
        if (infection >= 60) {
            player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 0, true, false, true));
        }
        if (InfectionState.surrendered(player) && infection >= 70) {
            player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 260, 0, true, false, false));
            player.addEffect(new MobEffectInstance(MobEffects.DIG_SPEED, 80, 0, true, false, true));
        }
    }
}
""")

write("src/main/java/de/sporenwerk/item/InfectionSerumItem.java", """
package de.sporenwerk.item;

import de.sporenwerk.infection.InfectionState;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

public final class InfectionSerumItem extends Item {
    public InfectionSerumItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        int before = InfectionState.level(player);
        if (before == 0) {
            player.displayClientMessage(Component.translatable("message.sporenwerk.infection.clean"), true);
            return InteractionResultHolder.fail(stack);
        }
        InfectionState.cure(player, 35);
        if (!player.getAbilities().instabuild) stack.shrink(1);
        if (player instanceof ServerPlayer serverPlayer) {
            serverPlayer.displayClientMessage(Component.translatable("message.sporenwerk.infection.cured",
                    Math.max(0, before - InfectionState.level(player))).withStyle(ChatFormatting.GREEN), true);
        }
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.infektionsserum").withStyle(ChatFormatting.GREEN));
    }
}
""")

write("src/main/java/de/sporenwerk/item/InfectionEmbraceItem.java", """
package de.sporenwerk.item;

import de.sporenwerk.infection.InfectionState;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

public final class InfectionEmbraceItem extends Item {
    public InfectionEmbraceItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        InfectionState.surrender(player);
        if (!player.getAbilities().instabuild) stack.shrink(1);
        player.displayClientMessage(Component.translatable("message.sporenwerk.infection.surrender")
                .withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.BOLD), false);
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.infektionshingabe").withStyle(ChatFormatting.DARK_PURPLE));
    }
}
""")

write("src/main/java/de/sporenwerk/item/SterileCoreItem.java", """
package de.sporenwerk.item;

import de.sporenwerk.infection.InfectionState;
import de.sporenwerk.infection.InfectionWorldData;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

public final class SterileCoreItem extends Item {
    public SterileCoreItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(level instanceof ServerLevel serverLevel)) return InteractionResultHolder.fail(stack);
        InfectionWorldData data = InfectionWorldData.get(serverLevel);
        if (data.isSterilized()) {
            player.displayClientMessage(Component.translatable("message.sporenwerk.infection.stopped").withStyle(ChatFormatting.GREEN), true);
            return InteractionResultHolder.fail(stack);
        }
        data.sterilize();
        if (!player.getAbilities().instabuild) stack.shrink(1);
        for (ServerPlayer online : serverLevel.getServer().getPlayerList().getPlayers()) {
            InfectionState.clear(online);
            online.displayClientMessage(Component.translatable("message.sporenwerk.infection.world_stopped")
                    .withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD), false);
        }
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.steriler_kern").withStyle(ChatFormatting.AQUA));
    }
}
""")

# Item models.
for item in ["infektionsserum", "infektionshingabe", "steriler_kern"]:
    write(f"src/main/resources/assets/sporenwerk/models/item/{item}.json", json.dumps({
        "parent": "minecraft:item/generated",
        "textures": {"layer0": f"sporenwerk:item/{item}"}
    }, ensure_ascii=False, indent=2) + "\n")

# Distinct, legible 32px icons (serum vial, spore-heart, sterile crystalline core).
tex = ASSETS / "textures/item"
tex.mkdir(parents=True, exist_ok=True)
def icon_vial(path, fill, cap):
    im = Image.new("RGBA", (32,32), (0,0,0,0)); d = ImageDraw.Draw(im)
    d.rectangle((12,4,19,7), fill=(28,34,34,255)); d.rectangle((11,7,20,10), fill=cap)
    d.rectangle((10,10,21,26), fill=(25,37,35,255)); d.rectangle((12,12,19,24), fill=(180,204,190,220))
    d.rectangle((12,18,19,24), fill=fill); d.rectangle((14,13,15,16), fill=(244,249,226,255))
    d.rectangle((9,15,10,22), fill=(25,37,35,255)); d.rectangle((21,15,22,22), fill=(25,37,35,255))
    im.save(path, optimize=True)
icon_vial(tex / "infektionsserum.png", (103,199,130,255), (228,211,155,255))
icon_vial(tex / "infektionshingabe.png", (134,66,151,255), (64,39,75,255))
im = Image.new("RGBA",(32,32),(0,0,0,0)); d=ImageDraw.Draw(im)
d.polygon([(16,3),(25,9),(28,18),(20,27),(12,28),(4,19),(7,9)], fill=(22,49,57,255))
d.polygon([(16,6),(22,10),(24,17),(19,23),(13,24),(8,18),(10,11)], fill=(68,179,190,255))
d.polygon([(16,9),(20,13),(19,18),(15,21),(11,17),(12,13)], fill=(211,244,220,255))
d.rectangle((15,2,17,5), fill=(232,250,230,255)); d.rectangle((24,18,27,20), fill=(144,225,211,255))
im.save(tex / "steriler_kern.png", optimize=True)

# Recipes: serum is renewable through the farm loop; surrender is a conscious crafted choice;
# sterile core is an expensive, one-time world-ending technology.
write("src/main/resources/data/sporenwerk/recipes/infektionsserum.json", """
{
  "type": "minecraft:crafting_shapeless",
  "ingredients": [
    { "item": "sporenwerk:rotwurzel" },
    { "item": "sporenwerk:filtermoos" },
    { "item": "minecraft:glass_bottle" }
  ],
  "result": { "item": "sporenwerk:infektionsserum", "count": 1 }
}
""")
write("src/main/resources/data/sporenwerk/recipes/infektionshingabe.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": [" R ", "RMR", " R "],
  "key": {
    "R": { "item": "sporenwerk:rotwurzel" },
    "M": { "item": "sporenwerk:myzelkompost" }
  },
  "result": { "item": "sporenwerk:infektionshingabe", "count": 1 }
}
""")
write("src/main/resources/data/sporenwerk/recipes/steriler_kern.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["DMD", "RFR", "DMD"],
  "key": {
    "D": { "item": "minecraft:diamond" },
    "M": { "item": "sporenwerk:myzelkompost" },
    "R": { "item": "sporenwerk:rotwurzel" },
    "F": { "item": "sporenwerk:filtermoos" }
  },
  "result": { "item": "sporenwerk:steriler_kern", "count": 1 }
}
""")

# Localization.
for filename, entries in [
    ("de_de.json", {
        "item.sporenwerk.infektionsserum": "Infektionsserum",
        "item.sporenwerk.infektionshingabe": "Herz der Hingabe",
        "item.sporenwerk.steriler_kern": "Steriler Kern",
        "tooltip.sporenwerk.infektionsserum": "Senkt die Infektion um 35 Stufen. Kann den Weg zurück ermöglichen.",
        "tooltip.sporenwerk.infektionshingabe": "Gib dich der Infektion hin. Setzt den Befall auf 100 und öffnet ihre Vorteile.",
        "tooltip.sporenwerk.steriler_kern": "Ein Endgame-Artefakt: stoppt die passive Infektionsausbreitung dauerhaft in dieser Welt.",
        "message.sporenwerk.infection.clean": "Du bist nicht infiziert.",
        "message.sporenwerk.infection.cured": "Infektion um %s Stufen gesenkt.",
        "message.sporenwerk.infection.surrender": "Du hörst auf, dich zu wehren. Die Sporen antworten.",
        "message.sporenwerk.infection.stopped": "Die Infektion wurde in dieser Welt bereits gestoppt.",
        "message.sporenwerk.infection.world_stopped": "Die Ausbreitung ist gestoppt. Was du geworden bist, bleibt deine Entscheidung."
    }),
    ("en_us.json", {
        "item.sporenwerk.infektionsserum": "Infection Serum",
        "item.sporenwerk.infektionshingabe": "Heart of Surrender",
        "item.sporenwerk.steriler_kern": "Sterile Core",
        "tooltip.sporenwerk.infektionsserum": "Reduces infection by 35 stages. It can open the road back.",
        "tooltip.sporenwerk.infektionshingabe": "Surrender to the infection. Sets infection to 100 and unlocks its benefits.",
        "tooltip.sporenwerk.steriler_kern": "An endgame artifact that permanently stops passive infection spread in this world.",
        "message.sporenwerk.infection.clean": "You are not infected.",
        "message.sporenwerk.infection.cured": "Infection reduced by %s stages.",
        "message.sporenwerk.infection.surrender": "You stop resisting. The spores answer.",
        "message.sporenwerk.infection.stopped": "Infection has already been stopped in this world.",
        "message.sporenwerk.infection.world_stopped": "The spread is stopped. What you have become remains your choice."
    })
]:
    path = RES / "assets/sporenwerk/lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Source-level contract test; CI checks persistence, server authority, and all three routes.
write("tools/test_infection_system.py", r'''
from pathlib import Path
import json, sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(rel): return (root / rel).read_text(encoding="utf-8")
def require(ok, msg):
    if not ok: raise SystemExit("Infection system regression: " + msg)
state = read("src/main/java/de/sporenwerk/infection/InfectionState.java")
world = read("src/main/java/de/sporenwerk/infection/InfectionWorldData.java")
events = read("src/main/java/de/sporenwerk/infection/InfectionEvents.java")
serum = read("src/main/java/de/sporenwerk/item/InfectionSerumItem.java")
surrender = read("src/main/java/de/sporenwerk/item/InfectionEmbraceItem.java")
core = read("src/main/java/de/sporenwerk/item/SterileCoreItem.java")
items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
require("getPersistentData()" in state and "SporenwerkInfection" in state, "player infection must persist")
require("SporenwerkSurrendered" in state, "surrender route must be persistent")
require("computeIfAbsent" in world and "setDirty()" in world and 'putBoolean("Sterilized"' in world,
        "endgame sterilization must survive world restarts")
require("TickEvent.Phase.END" in events and "ServerLevel" in events, "infection progression must be server-authoritative")
require("DaemmerlingEntity.class" in events and "getMaxLocalRawBrightness" in events,
        "exposure must be contextual and tied to darkness and the threat")
require("InfectionState.cure(player, 35)" in serum, "serum must provide a real cure action")
require("InfectionState.surrender(player)" in surrender, "surrender item must change the player's route")
require("data.sterilize()" in core and "InfectionState.clear(online)" in core,
        "sterile core must stop the world infection and clear online players")
for name in ("INFECTION_SERUM", "INFECTION_EMBRACE", "STERILE_CORE"):
    require(name in items, name + " must be registered")
for recipe in ("infektionsserum", "infektionshingabe", "steriler_kern"):
    json.loads((root / f"src/main/resources/data/sporenwerk/recipes/{recipe}.json").read_text(encoding="utf-8"))
print("Infection progression, choice items, world persistence, and recipe checks passed.")
''')
print("Installed Sporenwerk infection progression v0: exposure, cure, surrender, and world sterilization.")
