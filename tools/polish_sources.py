#!/usr/bin/env python3
"""Apply V1.0.1 gameplay/UX polish to the supplied Sporenwerk project tree."""
from pathlib import Path
import re, subprocess, sys, textwrap, json

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"

def write(path, content):
    path = ROOT / path if not str(path).startswith(str(ROOT)) else Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")

def replace_once(path, old, new):
    p = ROOT / path
    s = p.read_text(encoding="utf-8")
    if new in s:
        return
    if old not in s:
        raise SystemExit(f"Patch context not found in {path}: {old[:90]!r}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# Repair source snapshots produced by the earlier prototype against Forge 47.2.
p = ROOT / "src/main/java/de/sporenwerk/skill/SkillData.java"
s = p.read_text(encoding="utf-8")
s = s.replace("import net.minecraft.util.datafix.DataFixTypes;", "")
s = re.sub(r"\s*private static final (?:SavedData\.)?Factory<SkillData> FACTORY = new (?:SavedData\.)?Factory<>\(SkillData::new, SkillData::load, DataFixTypes\.LEVEL\);\s*", "\n", s)
s = s.replace('return level.getServer().overworld().getDataStorage().computeIfAbsent(FACTORY, "sporenwerk_progression");', 'return level.getServer().overworld().getDataStorage().computeIfAbsent(SkillData::load, SkillData::new, "sporenwerk_progression");')
p.write_text(s, encoding="utf-8")

p = ROOT / "src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java"
s = p.read_text(encoding="utf-8")
s = s.replace("BlockPos.betweenClosed(pos.offset(-2, -1, -2), pos.offset(2, 1, 2))", "BlockPos.betweenClosed(getBlockPos().offset(-2, -1, -2), getBlockPos().offset(2, 1, 2))")
s = s.replace("target.equals(pos)", "target.equals(getBlockPos())")
if "private final int[] clientGuiData" not in s:
    marker = "    private int progress;\n    private int storedPoints;"
    insert = "    private int progress;\n    private int storedPoints;\n    private final int[] clientGuiData = new int[3];"
    if marker not in s: raise SystemExit("Machine progress fields not found")
    s = s.replace(marker, insert, 1)
if "public ItemStackHandler getItemHandler()" not in s:
    marker = "    @Override\n    public <T> LazyOptional<T> getCapability(Capability<T> capability, @Nullable Direction side) {"
    methods = '''    /** Access used by the real menu; all changes remain on the logical server. */
    public ItemStackHandler getItemHandler() { return inventory; }

    public int getGuiValue(int index) {
        if (index < 0 || index >= clientGuiData.length) return 0;
        if (level != null && level.isClientSide) return clientGuiData[index];
        return switch (index) {
            case 0 -> progressPercent();
            case 1 -> energyStorage.getEnergyStored() / 5;
            case 2 -> storedPoints / 50;
            default -> 0;
        };
    }

    public void setGuiValue(int index, int value) {
        if (index >= 0 && index < clientGuiData.length && level != null && level.isClientSide) {
            clientGuiData[index] = Math.max(0, value);
        }
    }

    private int progressPercent() {
        if (level == null || !(level instanceof ServerLevel serverLevel)) return 0;
        String id = getBlockState().getBlock().builtInRegistryHolder().key().location().getPath();
        int base = id.equals("feldsammler") ? 40 : id.equals("saatgutpresse") ? 60 : 80;
        int interval = SkillData.get(serverLevel).machineInterval(base);
        return Math.max(0, Math.min(100, progress * 100 / Math.max(1, interval)));
    }

'''
    if marker not in s: raise SystemExit("Machine capability method not found")
    s = s.replace(marker, methods + marker, 1)
p.write_text(s, encoding="utf-8")

# Minecraft 1.20.1 exposes AMBIENT_CAVE as a Holder in these Forge mappings.
p = ROOT / "src/main/java/de/sporenwerk/client/ClientHorrorEvents.java"
s = p.read_text(encoding="utf-8").replace("SoundEvents.AMBIENT_CAVE,", "SoundEvents.AMBIENT_CAVE.value(),")
p.write_text(s, encoding="utf-8")

# New output version.
p = ROOT / "build.gradle"
s = p.read_text(encoding="utf-8")
s = re.sub(r"version = '1\.0\.0'", "version = '1.0.1'", s, count=1)
p.write_text(s, encoding="utf-8")

replace_once("src/main/java/de/sporenwerk/Sporenwerk.java",
             "import de.sporenwerk.registry.ModItems;",
             "import de.sporenwerk.registry.ModItems;\nimport de.sporenwerk.registry.ModMenus;")
replace_once("src/main/java/de/sporenwerk/Sporenwerk.java",
             "ModCreativeTabs.TABS.register(modBus);",
             "ModCreativeTabs.TABS.register(modBus);\n        ModMenus.MENUS.register(modBus);")
replace_once("src/main/java/de/sporenwerk/registry/ModItems.java",
             "import de.sporenwerk.item.FeldwissenItem;",
             "import de.sporenwerk.item.FeldwissenItem;\nimport de.sporenwerk.item.FeldhandbuchItem;")
replace_once("src/main/java/de/sporenwerk/registry/ModItems.java",
             'public static final RegistryObject<Item> FELDWISSEN = ITEMS.register("feldwissen", () -> new FeldwissenItem(new Item.Properties().stacksTo(64)));',
             'public static final RegistryObject<Item> FELDWISSEN = ITEMS.register("feldwissen", () -> new FeldwissenItem(new Item.Properties().stacksTo(64)));\n    public static final RegistryObject<Item> FELDHANDBUCH = ITEMS.register("feldhandbuch", () -> new FeldhandbuchItem(new Item.Properties().stacksTo(1)));')
replace_once("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java",
             "output.accept(ModItems.FELDWISSEN.get());",
             "output.accept(ModItems.FELDWISSEN.get());\n                        output.accept(ModItems.FELDHANDBUCH.get());")

write("src/main/java/de/sporenwerk/registry/ModMenus.java", '''
package de.sporenwerk.registry;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.client.menu.MachineMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraftforge.common.extensions.IForgeMenuType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModMenus {
    public static final DeferredRegister<MenuType<?>> MENUS =
            DeferredRegister.create(ForgeRegistries.MENU_TYPES, Sporenwerk.MODID);
    public static final RegistryObject<MenuType<MachineMenu>> MACHINE = MENUS.register(
            "machine", () -> IForgeMenuType.create((id, playerInventory, data) ->
                    new MachineMenu(id, playerInventory, data.readBlockPos())));
    private ModMenus() {}
}
''')

write("src/main/java/de/sporenwerk/client/menu/MachineMenu.java", '''
package de.sporenwerk.client.menu;

import de.sporenwerk.block.entity.MachineBlockEntity;
import de.sporenwerk.registry.ModMenus;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraftforge.items.SlotItemHandler;

public final class MachineMenu extends AbstractContainerMenu {
    private final BlockPos pos;
    private final MachineBlockEntity machine;
    private final ContainerData data;

    public MachineMenu(int id, Inventory playerInventory, BlockPos pos) {
        super(ModMenus.MACHINE.get(), id);
        this.pos = pos;
        BlockEntity entity = playerInventory.player.level().getBlockEntity(pos);
        if (!(entity instanceof MachineBlockEntity blockEntity)) {
            throw new IllegalStateException("Sporenwerk machine missing at " + pos);
        }
        this.machine = blockEntity;
        this.data = new ContainerData() {
            @Override public int get(int index) { return machine.getGuiValue(index); }
            @Override public void set(int index, int value) { machine.setGuiValue(index, value); }
            @Override public int getCount() { return 3; }
        };
        for (int i = 0; i < 4; i++) addSlot(new SlotItemHandler(machine.getItemHandler(), i, 12 + i * 18, 38));
        for (int i = 0; i < 8; i++) addSlot(new SlotItemHandler(machine.getItemHandler(), i + 4,
                112 + (i % 4) * 18, 34 + (i / 4) * 18));
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                addSlot(new Slot(playerInventory, col + row * 9 + 9, 12 + col * 18, 130 + row * 18));
            }
        }
        for (int col = 0; col < 9; col++) addSlot(new Slot(playerInventory, col, 12 + col * 18, 188));
        addDataSlots(data);
    }

    public int progress() { return data.get(0); }
    public int energyFe() { return data.get(1) * 5; }
    public int storedPoints() { return data.get(2) * 50; }

    @Override
    public boolean stillValid(Player player) {
        return machine.getLevel() != null
                && player.distanceToSqr(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5) <= 64.0
                && !machine.isRemoved();
    }

    @Override
    public net.minecraft.world.item.ItemStack quickMoveStack(Player player, int index) {
        net.minecraft.world.item.ItemStack empty = net.minecraft.world.item.ItemStack.EMPTY;
        Slot slot = slots.get(index);
        if (slot == null || !slot.hasItem()) return empty;
        net.minecraft.world.item.ItemStack source = slot.getItem();
        net.minecraft.world.item.ItemStack original = source.copy();
        if (index < 12) {
            if (!moveItemStackTo(source, 12, slots.size(), true)) return empty;
        } else if (!moveItemStackTo(source, 0, 12, false)) {
            return empty;
        }
        if (source.isEmpty()) slot.set(net.minecraft.world.item.ItemStack.EMPTY);
        else slot.setChanged();
        return original;
    }
}
''')

write("src/main/java/de/sporenwerk/client/menu/MachineScreen.java", '''
package de.sporenwerk.client.menu;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraftforge.fml.ModList;

public final class MachineScreen extends AbstractContainerScreen<MachineMenu> {
    public MachineScreen(MachineMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        this.imageWidth = 208;
        this.imageHeight = 222;
        this.inventoryLabelY = 112;
        this.titleLabelY = 8;
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        int x = leftPos, y = topPos;
        g.fill(x, y, x + imageWidth, y + imageHeight, 0xFF141E1B);
        g.fill(x + 1, y + 1, x + imageWidth - 1, y + imageHeight - 1, 0xFF293831);
        g.fill(x + 4, y + 4, x + imageWidth - 4, y + 20, 0xFF101815);
        g.fill(x + 4, y + 23, x + 88, y + 60, 0xFF1A2923);
        g.fill(x + 98, y + 23, x + imageWidth - 6, y + 60, 0xFF1A2923);
        g.fill(x + 4, y + 65, x + imageWidth - 4, y + 108, 0xFF101815);
        g.fill(x + 4, y + 118, x + imageWidth - 4, y + imageHeight - 5, 0xFF1A2923);
        g.fill(x + 4, y + 21, x + imageWidth - 4, y + 22, 0xFFB77A35);
        for (int[] p : new int[][]{{6,25},{imageWidth-8,25},{6,120},{imageWidth-8,120}}) {
            g.fill(x + p[0], y + p[1], x + p[0] + 2, y + p[1] + 2, 0xFFDBB96B);
        }
        int barX = x + 12, barY = y + 80, barWidth = imageWidth - 24;
        g.fill(barX, barY, barX + barWidth, barY + 8, 0xFF050908);
        int fill = Math.max(0, Math.min(barWidth, barWidth * menu.progress() / 100));
        if (fill > 2) {
            g.fill(barX + 1, barY + 1, barX + fill - 1, barY + 7, 0xFF5E9B68);
            g.fill(barX + 1, barY + 1, barX + fill - 1, barY + 3, 0xFF95CB7C);
        }
        g.fill(barX, barY + 12, barX + barWidth, barY + 13, 0xFF34453D);
    }

    @Override
    protected void renderLabels(GuiGraphics g, int mouseX, int mouseY) {
        g.drawString(font, title, (imageWidth - font.width(title)) / 2, 8, 0xFFF1E5BD, false);
        g.drawString(font, Component.translatable("gui.sporenwerk.input"), 12, 25, 0xFFB8D0B2, false);
        g.drawString(font, Component.translatable("gui.sporenwerk.output"), 112, 20, 0xFFB8D0B2, false);
        g.drawString(font, Component.literal(menu.progress() >= 100 ? "BEREIT" : "ARBEITET " + menu.progress() + "%"),
                12, 70, 0xFFE7D9A5, false);
        if (ModList.get().isLoaded("mekanism")) {
            g.drawString(font, Component.literal("FE: " + menu.energyFe() + " / 100000"), 12, 94, 0xFF84D6C4, false);
        } else {
            g.drawString(font, Component.literal("Autonomer Betrieb"), 12, 94, 0xFF84D6C4, false);
        }
        g.drawString(font, Component.literal("Rohstoffwert: " + menu.storedPoints()), 12, 103, 0xFFB8D0B2, false);
        g.drawString(font, Component.translatable("container.inventory"), 12, inventoryLabelY, 0xFFF1E5BD, false);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        renderBackground(g);
        super.render(g, mouseX, mouseY, partialTick);
        renderTooltip(g, mouseX, mouseY);
    }
}
''')

write("src/main/java/de/sporenwerk/client/ClientModEvents.java", '''
package de.sporenwerk.client;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.client.menu.MachineScreen;
import de.sporenwerk.registry.ModMenus;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;

@Mod.EventBusSubscriber(modid = Sporenwerk.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ClientModEvents {
    private ClientModEvents() {}
    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> MenuScreens.register(ModMenus.MACHINE.get(), MachineScreen::new));
    }
}
''')

write("src/main/java/de/sporenwerk/block/MachineBlock.java", '''
package de.sporenwerk.block;

import de.sporenwerk.block.entity.MachineBlockEntity;
import de.sporenwerk.client.menu.MachineMenu;
import de.sporenwerk.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraftforge.network.NetworkHooks;
import org.jetbrains.annotations.Nullable;

public final class MachineBlock extends BaseEntityBlock {
    public MachineBlock(BlockBehaviour.Properties properties) { super(properties); }
    @Override public RenderShape getRenderShape(BlockState state) { return RenderShape.MODEL; }
    @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return ModBlockEntities.MACHINE.get().create(pos, state);
    }
    @Nullable @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide || type != ModBlockEntities.MACHINE.get()) return null;
        return (lvl, pos, st, be) -> MachineBlockEntity.serverTick(lvl, pos, st, (MachineBlockEntity) be);
    }
    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (!(player instanceof ServerPlayer serverPlayer) || !(level.getBlockEntity(pos) instanceof MachineBlockEntity)) {
            return InteractionResult.PASS;
        }
        MenuProvider provider = new SimpleMenuProvider(
                (windowId, inventory, p) -> new MachineMenu(windowId, inventory, pos), state.getBlock().getName());
        NetworkHooks.openScreen(serverPlayer, provider, buffer -> buffer.writeBlockPos(pos));
        return InteractionResult.CONSUME;
    }
}
''')

write("src/main/java/de/sporenwerk/item/FeldhandbuchItem.java", '''
package de.sporenwerk.item;

import de.sporenwerk.skill.SkillData;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.Style;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.server.level.ServerLevel;

/** In-game onboarding and clickable skill-tree panel without a hard dependency on another mod. */
public final class FeldhandbuchItem extends Item {
    public FeldhandbuchItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, net.minecraft.world.entity.player.Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(player instanceof ServerPlayer serverPlayer) || !(level instanceof ServerLevel serverLevel)) {
            return InteractionResultHolder.pass(stack);
        }
        SkillData data = SkillData.get(serverLevel);
        serverPlayer.sendSystemMessage(Component.literal("━━━━━━━━ SPORENWERK: WILDWUCHS ━━━━━━━━").withStyle(ChatFormatting.DARK_GREEN, ChatFormatting.BOLD));
        serverPlayer.sendSystemMessage(Component.literal("FELDHANDBUCH · Produktionsnotizen und Feldwissen").withStyle(ChatFormatting.GOLD));
        serverPlayer.sendSystemMessage(Component.literal("Feldwissen: " + data.knowledge() + "  |  Ernten: " + data.harvests() + "  |  Entdeckungen: " + data.discoveries()).withStyle(ChatFormatting.YELLOW));
        serverPlayer.sendSystemMessage(Component.literal("1 · ANBAU: Samen auf Ackerboden setzen. Licht und freie Fläche helfen den Pflanzen beim Wachsen.").withStyle(ChatFormatting.GRAY));
        serverPlayer.sendSystemMessage(Component.literal("2 · VERARBEITUNG: Ernte in das Maschinenfenster legen; Ausgaben kommen aus dem rechten Puffer.").withStyle(ChatFormatting.GRAY));
        serverPlayer.sendSystemMessage(Component.literal("3 · FELDSAMMLER: Samen in das passende Eingabefach legen. Erntet reife Mod-Pflanzen im 5×3×5-Radius und setzt sie zurück.").withStyle(ChatFormatting.GRAY));
        serverPlayer.sendSystemMessage(Component.literal("4 · BIOREAKTOR: Pflanzenreste einlegen. Biomasse und Rohstoffwert werden intern gepuffert.").withStyle(ChatFormatting.GRAY));
        serverPlayer.sendSystemMessage(Component.literal("5 · ENERGIE: Mit Mekanism können Universal-Kabel FE einspeisen; ohne Mekanism laufen die Maschinen autonom.").withStyle(ChatFormatting.GRAY));
        serverPlayer.sendSystemMessage(Component.literal("── VERBESSERUNGEN · Grüne Zeilen sind anklickbar ──").withStyle(ChatFormatting.DARK_AQUA));
        sendUpgrade(serverPlayer, data, SkillData.Branch.ANBAU, "ANBAU", "Jede Stufe erhöht zusätzlich die Chance auf einen Wachstumsimpuls.");
        sendUpgrade(serverPlayer, data, SkillData.Branch.ERNTE, "ERNTE", "Stufe 1: dauerhaft +1 Beute; spätere Stufen steigern Ertrag und Bonus-Ernten.");
        sendUpgrade(serverPlayer, data, SkillData.Branch.MASCHINEN, "MASCHINEN", "Jede Stufe verkürzt den Arbeitszyklus.");
        serverPlayer.sendSystemMessage(Component.literal("Fallback: /sporenwerk status · /sporenwerk upgrade anbau|ernte|maschinen").withStyle(ChatFormatting.DARK_GRAY));
        serverPlayer.sendSystemMessage(Component.literal("DAS FELD HINTER DEM GLAS: Manche Spuren sind auf der falschen Seite der Scheibe.").withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.ITALIC));
        return InteractionResultHolder.success(stack);
    }

    private static void sendUpgrade(ServerPlayer player, SkillData data, SkillData.Branch branch, String label, String detail) {
        int level = data.level(branch), cost = data.upgradeCost(branch);
        String command = "/sporenwerk upgrade " + branch.name().toLowerCase(java.util.Locale.ROOT);
        Component clickable = Component.literal("[ " + label + " " + level + "/10 · Kosten " + cost + " Feldwissen · VERBESSERN ]")
                .withStyle(Style.EMPTY.withColor(level >= 10 ? ChatFormatting.DARK_GRAY : ChatFormatting.GREEN)
                        .withBold(true)
                        .withClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, command))
                        .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, Component.literal(detail))));
        player.sendSystemMessage(clickable);
    }
}
''')

write("src/main/resources/data/sporenwerk/recipes/feldhandbuch.json", '''
{
  "type": "minecraft:crafting_shaped",
  "pattern": [" F ", "LBL", " F "],
  "key": {
    "F": { "item": "sporenwerk:faser" },
    "L": { "item": "minecraft:leather" },
    "B": { "item": "minecraft:book" }
  },
  "result": { "item": "sporenwerk:feldhandbuch", "count": 1 }
}
''')
for item in ("bernsteinkappe", "rotwurzel", "filtermoos"):
    write(f"src/main/resources/assets/sporenwerk/models/item/{item}.json", f'''
{{
  "parent": "minecraft:item/generated",
  "textures": {{ "layer0": "sporenwerk:item/{item}" }}
}}
''')
write("src/main/resources/assets/sporenwerk/models/item/feldhandbuch.json", '''
{
  "parent": "minecraft:item/generated",
  "textures": { "layer0": "sporenwerk:item/feldhandbuch" }
}
''')

lang_path = RES / "assets/sporenwerk/lang/de_de.json"
lang = json.loads(lang_path.read_text(encoding="utf-8"))
lang.update({
    "item.sporenwerk.feldhandbuch": "Feldhandbuch",
    "gui.sporenwerk.input": "EINGABE",
    "gui.sporenwerk.output": "PUFFERAUSGABE",
    "advancements.sporenwerk.root.title": "Sporenwerk: Wildwuchs",
    "advancements.sporenwerk.root.description": "Dein Feld beginnt mit einer Handvoll Samen.",
    "advancements.sporenwerk.first_crop.title": "Ein Stück Erde",
    "advancements.sporenwerk.first_crop.description": "Setze deine erste Faserrohr-Pflanze.",
    "advancements.sporenwerk.first_machine.title": "Die erste Maschine",
    "advancements.sporenwerk.first_machine.description": "Baue deine erste Produktionsmaschine."
})
lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
write("src/main/resources/data/sporenwerk/advancements/root.json", '''
{
  "display": {
    "icon": { "item": "sporenwerk:feldhandbuch" },
    "title": { "translate": "advancements.sporenwerk.root.title" },
    "description": { "translate": "advancements.sporenwerk.root.description" },
    "background": "minecraft:textures/gui/advancements/backgrounds/adventure.png",
    "frame": "task",
    "show_toast": false,
    "announce_to_chat": false,
    "hidden": false
  },
  "criteria": {
    "read_handbook": { "trigger": "minecraft:inventory_changed", "conditions": { "items": [{ "items": ["sporenwerk:feldhandbuch"] }] } }
  }
}
''')
write("src/main/resources/data/sporenwerk/advancements/first_crop.json", '''
{
  "parent": "sporenwerk:root",
  "display": {
    "icon": { "item": "sporenwerk:faserrohr_samen" },
    "title": { "translate": "advancements.sporenwerk.first_crop.title" },
    "description": { "translate": "advancements.sporenwerk.first_crop.description" },
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "plant_faserrohr": { "trigger": "minecraft:placed_block", "conditions": { "block": "sporenwerk:faserrohr" } }
  }
}
''')
write("src/main/resources/data/sporenwerk/advancements/first_machine.json", '''
{
  "parent": "sporenwerk:first_crop",
  "display": {
    "icon": { "item": "sporenwerk:feldsammler" },
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
  "requirements": [["place_feldsammler", "place_press", "place_reactor"]]
}
''')

subprocess.run([sys.executable, str(ROOT / "tools/generate_art.py"), str(ROOT)], check=True)
readme = ROOT / "README.md"
readme.write_text("""# Sporenwerk: Wildwuchs 1.0.1

Minecraft Java 1.20.1 · Forge 47.2.0 · Java 17

## Contents
- Four farmland crops with distinct staged 32x32 pixel-art textures.
- Three machines with a dedicated inventory screen, shift-click support, a progress bar, protected output slots and persistent buffers.
- Saatgutpresse converts harvests into seeds/spores; Biomasse-Bioreaktor consumes plant residue; Feldsammler harvests mature crops in its radius when matching seeds are stocked.
- Feldhandbuch: right-click for a German in-game guide, progression status and clickable upgrade purchases.
- Three persistent skill branches and advancement milestones; commands remain as a fallback.
- Rare local horror HUD/sound effects. The photo option is explicitly a current-view-only Minecraft framebuffer fallback.
- Optional Mekanism FE capability and conditional Botania/Mekanism recipes.

## Build
Use JDK 17 and Gradle 8.8, then run gradle --no-daemon clean build. The output is build/libs/sporenwerk-1.0.1.jar.

## Machine controls
Right-click a machine to open its panel. Put accepted inputs in the left slots, take outputs from the right compartment, and use shift-click to transfer matching items. The Feldsammler accepts seeds in the four input slots and checks a 5x3x5 area. With Mekanism installed, provide Forge Energy through compatible cables; without Mekanism the machines run autonomously.

## Skill tree
Right-click the Feldhandbuch. Click a green upgrade row to purchase it with Feldwissen. /sporenwerk status shows the full state; /sporenwerk upgrade anbau, ernte, or maschinen are text alternatives. Progress is saved in world data.

## Known limits
This is an improved V1.0.1, not a fully content-complete release: custom enemy AI, true alternate-angle photo rendering and native FTB Quests export are not implemented. No operating-system process is read, started or modified; no telemetry or desktop capture is used.
""", encoding="utf-8")
print(f"Polished project prepared at {ROOT}")
