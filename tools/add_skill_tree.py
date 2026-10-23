#!/usr/bin/env python3
"""Install the V1.1.0 fieldbook skill-tree screen into a prepared Sporenwerk source tree."""
from pathlib import Path
import json, re, sys

ROOT = Path(sys.argv[1]).resolve()
SRC = ROOT / "src/main/java/de/sporenwerk"
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

write("src/main/java/de/sporenwerk/client/menu/SkillTreeMenu.java", '''
package de.sporenwerk.client.menu;

import de.sporenwerk.registry.ModMenus;
import de.sporenwerk.skill.SkillData;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.level.Level;

public final class SkillTreeMenu extends AbstractContainerMenu {
    private final ContainerData data;

    /** Client-only constructor. The server synchronizes all values through ContainerData. */
    public SkillTreeMenu(int id, Inventory inventory) {
        this(id, inventory, new SimpleContainerData(10));
    }

    public SkillTreeMenu(int id, Inventory inventory, SkillData skills) {
        this(id, inventory, createData(skills));
    }

    private SkillTreeMenu(int id, Inventory inventory, ContainerData data) {
        super(ModMenus.FIELD_SKILLS.get(), id);
        this.data = data;
        addDataSlots(data);
    }

    private static ContainerData createData(SkillData skills) {
        return new ContainerData() {
            @Override public int get(int index) {
                return switch (index) {
                    case 0 -> skills.knowledge();
                    case 1 -> skills.level(SkillData.Branch.ANBAU);
                    case 2 -> skills.level(SkillData.Branch.ERNTE);
                    case 3 -> skills.level(SkillData.Branch.MASCHINEN);
                    case 4 -> skills.upgradeCost(SkillData.Branch.ANBAU);
                    case 5 -> skills.upgradeCost(SkillData.Branch.ERNTE);
                    case 6 -> skills.upgradeCost(SkillData.Branch.MASCHINEN);
                    case 7 -> (int) Math.min(32767, skills.harvests());
                    case 8 -> (int) Math.min(32767, skills.discoveries());
                    case 9 -> (int) Math.min(32767, skills.crafts());
                    default -> 0;
                };
            }
            @Override public void set(int index, int value) {}
            @Override public int getCount() { return 10; }
        };
    }

    public int knowledge() { return data.get(0); }
    public int growthLevel() { return data.get(1); }
    public int harvestLevel() { return data.get(2); }
    public int machineLevel() { return data.get(3); }
    public int growthCost() { return data.get(4); }
    public int harvestCost() { return data.get(5); }
    public int machineCost() { return data.get(6); }
    public int harvests() { return data.get(7); }
    public int discoveries() { return data.get(8); }
    public int crafts() { return data.get(9); }

    @Override public boolean stillValid(Player player) { return true; }
}
''')

# Register an actual menu for the portable handbook.
menus = ROOT / "src/main/java/de/sporenwerk/registry/ModMenus.java"
m = menus.read_text(encoding="utf-8")
if "FIELD_SKILLS" not in m:
    m = m.replace("import de.sporenwerk.client.menu.MachineMenu;", "import de.sporenwerk.client.menu.MachineMenu;\nimport de.sporenwerk.client.menu.SkillTreeMenu;")
    field = '''
    public static final RegistryObject<MenuType<SkillTreeMenu>> FIELD_SKILLS = MENUS.register(
            "field_skills", () -> IForgeMenuType.create((id, inventory, data) ->
                    new SkillTreeMenu(id, inventory)));
'''
    idx = m.rfind("    private ModMenus()")
    if idx < 0: raise SystemExit("Could not find ModMenus constructor")
    m = m[:idx] + field + m[idx:]
    menus.write_text(m, encoding="utf-8")

# Replace chat-only handbook with a portable screen.
write("src/main/java/de/sporenwerk/item/FeldhandbuchItem.java", '''
package de.sporenwerk.item;

import de.sporenwerk.client.menu.SkillTreeMenu;
import de.sporenwerk.skill.SkillData;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraftforge.network.NetworkHooks;

/** Opens the interactive field journal; purchases are validated on the server by Sporenwerk commands. */
public final class FeldhandbuchItem extends Item {
    public FeldhandbuchItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, net.minecraft.world.entity.player.Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(player instanceof ServerPlayer serverPlayer) || !(level instanceof ServerLevel serverLevel)) {
            return InteractionResultHolder.pass(stack);
        }
        NetworkHooks.openScreen(serverPlayer,
                new SimpleMenuProvider((id, inventory, p) ->
                        new SkillTreeMenu(id, inventory, SkillData.get(serverLevel)),
                        Component.translatable("gui.sporenwerk.skill_title")));
        return InteractionResultHolder.success(stack);
    }
}
''')

# Register the screen on the physical client only.
clientEvents = ROOT / "src/main/java/de/sporenwerk/client/ClientModEvents.java"
s = clientEvents.read_text(encoding="utf-8")
if "SkillTreeScreen" not in s:
    s = s.replace("import de.sporenwerk.client.menu.MachineScreen;", "import de.sporenwerk.client.menu.MachineScreen;\nimport de.sporenwerk.client.menu.SkillTreeScreen;")
    s = s.replace("MenuScreens.register(ModMenus.MACHINE.get(), MachineScreen::new);",
                  "MenuScreens.register(ModMenus.MACHINE.get(), MachineScreen::new);\n            MenuScreens.register(ModMenus.FIELD_SKILLS.get(), SkillTreeScreen::new);")
    clientEvents.write_text(s, encoding="utf-8")

write("src/main/java/de/sporenwerk/client/menu/SkillTreeScreen.java", '''
package de.sporenwerk.client.menu;

import de.sporenwerk.registry.ModBlocks;
import de.sporenwerk.registry.ModItems;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;

public final class SkillTreeScreen extends AbstractContainerScreen<SkillTreeMenu> {
    private Button growthButton;
    private Button harvestButton;
    private Button machineButton;

    private static final int PANEL = 0xF016211D;
    private static final int CARD = 0xFF25362F;
    private static final int CARD_EDGE = 0xFF59775F;
    private static final int GOLD = 0xFFE7C875;
    private static final int PALE = 0xFFE7E1C8;
    private static final int MINT = 0xFF98C99A;
    private static final int DIM = 0xFF9CA99B;

    public SkillTreeScreen(SkillTreeMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = 344;
        imageHeight = 222;
        titleLabelY = -100;
        inventoryLabelY = -100;
    }

    @Override
    protected void init() {
        super.init();
        int y = topPos + 167;
        growthButton = addRenderableWidget(Button.builder(buttonLabel(menu.growthLevel(), menu.growthCost()),
                b -> buy("anbau")).bounds(leftPos + 13, y, 98, 20).build());
        harvestButton = addRenderableWidget(Button.builder(buttonLabel(menu.harvestLevel(), menu.harvestCost()),
                b -> buy("ernte")).bounds(leftPos + 123, y, 98, 20).build());
        machineButton = addRenderableWidget(Button.builder(buttonLabel(menu.machineLevel(), menu.machineCost()),
                b -> buy("maschinen")).bounds(leftPos + 233, y, 98, 20).build());
    }

    private Component buttonLabel(int level, int cost) {
        return Component.literal(level >= 10 ? "MAXIMAL" : "Kaufen · " + cost + " Wissen");
    }

    private void buy(String branch) {
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.player != null) {
            // This calls the existing server command. The server rechecks level and available knowledge.
            minecraft.player.connection.sendCommand("sporenwerk upgrade " + branch);
        }
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        if (growthButton != null) growthButton.setMessage(buttonLabel(menu.growthLevel(), menu.growthCost()));
        if (harvestButton != null) harvestButton.setMessage(buttonLabel(menu.harvestLevel(), menu.harvestCost()));
        if (machineButton != null) machineButton.setMessage(buttonLabel(menu.machineLevel(), menu.machineCost()));
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        int x = leftPos, y = topPos;
        g.fill(x - 2, y - 2, x + imageWidth + 2, y + imageHeight + 2, 0xE6000000);
        g.fill(x, y, x + imageWidth, y + imageHeight, PANEL);
        g.fill(x + 2, y + 2, x + imageWidth - 2, y + 25, 0xFF101815);
        g.fill(x + 2, y + 25, x + imageWidth - 2, y + 26, 0xFF9B6C3A);
        g.fill(x + 11, y + 33, x + 113, y + 157, CARD);
        g.fill(x + 121, y + 33, x + 223, y + 157, CARD);
        g.fill(x + 231, y + 33, x + 333, y + 157, CARD);
        g.fill(x + 11, y + 33, x + 113, y + 35, CARD_EDGE);
        g.fill(x + 121, y + 33, x + 223, y + 35, 0xFFD19A48);
        g.fill(x + 231, y + 33, x + 333, y + 35, 0xFF70ADA4);
        g.fill(x + 11, y + 33, x + 13, y + 157, 0xFF17231E);
        g.fill(x + 121, y + 33, x + 123, y + 157, 0xFF17231E);
        g.fill(x + 231, y + 33, x + 233, y + 157, 0xFF17231E);

        drawLevelBar(g, x + 22, y + 117, menu.growthLevel(), CARD_EDGE);
        drawLevelBar(g, x + 132, y + 117, menu.harvestLevel(), 0xFFD19A48);
        drawLevelBar(g, x + 242, y + 117, menu.machineLevel(), 0xFF70ADA4);

        g.fill(x + 13, y + 195, x + imageWidth - 13, y + 196, 0xFF394C41);
        g.fill(x + 13, y + 199, x + 14 + Math.min(310, menu.knowledge() / 2), y + 201, 0xFF719A6A);
        g.renderItem(new ItemStack(ModItems.FASERROHR_SAMEN.get()), x + 22, y + 46);
        g.renderItem(new ItemStack(ModItems.ROTWURZEL_SAMEN.get()), x + 132, y + 46);
        g.renderItem(new ItemStack(ModBlocks.SAATGUTPRESSE.get()), x + 242, y + 46);
    }

    private void drawLevelBar(GuiGraphics g, int x, int y, int level, int color) {
        g.fill(x, y, x + 80, y + 6, 0xFF101815);
        int fill = Math.max(0, Math.min(80, level * 8));
        if (fill > 0) {
            g.fill(x + 1, y + 1, x + fill - 1, y + 5, color);
        }
    }

    @Override
    protected void renderLabels(GuiGraphics g, int mouseX, int mouseY) {
        g.drawCenteredString(font, Component.literal("FELDHANDBUCH  /  WISSENSBAUM"), imageWidth / 2, 8, GOLD);
        g.drawString(font, Component.literal("Feldwissen: " + menu.knowledge()), 14, 24, PALE);
        g.drawString(font, Component.literal("A"), 99, 43, MINT);
        g.drawString(font, Component.literal("ANBAU"), 38, 46, MINT);
        g.drawString(font, Component.literal("Schnelleres"), 22, 73, PALE);
        g.drawString(font, Component.literal("Wachstum"), 22, 84, PALE);
        g.drawString(font, Component.literal("+10 % Chance je Stufe"), 22, 101, DIM);
        g.drawString(font, Component.literal(menu.growthLevel() + " / 10"), 22, 129, PALE);

        g.drawString(font, Component.literal("B"), 209, 43, GOLD);
        g.drawString(font, Component.literal("ERNTE"), 148, 46, GOLD);
        g.drawString(font, Component.literal("Mehr Ertrag"), 132, 73, PALE);
        g.drawString(font, Component.literal("und Samen"), 132, 84, PALE);
        g.drawString(font, Component.literal("+1 Grundbeute ab Stufe 1"), 132, 101, DIM);
        g.drawString(font, Component.literal(menu.harvestLevel() + " / 10"), 132, 129, PALE);

        g.drawString(font, Component.literal("C"), 319, 43, 0xFF70D3C5);
        g.drawString(font, Component.literal("MASCHINEN"), 258, 46, 0xFF70D3C5);
        g.drawString(font, Component.literal("Kürzere Zyklen"), 242, 73, PALE);
        g.drawString(font, Component.literal("mehr Durchsatz"), 242, 84, PALE);
        g.drawString(font, Component.literal("-5 Ticks je Stufe"), 242, 101, DIM);
        g.drawString(font, Component.literal(menu.machineLevel() + " / 10"), 242, 129, PALE);

        g.drawString(font, Component.literal("Ernten " + menu.harvests() + "   ·   Entdeckungen " + menu.discoveries()
                + "   ·   Handwerk " + menu.crafts()), 14, 183, 0xFFB6C7B4);
        g.drawString(font, Component.literal("Fortschritt bleibt in den Weltdaten gespeichert."), 14, 207, DIM);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        renderBackground(g);
        super.render(g, mouseX, mouseY, partialTick);
        renderTooltip(g, mouseX, mouseY);
    }
}
''')

# Give every machine a compact, descriptive item tooltip for first-time discovery.
write("src/main/java/de/sporenwerk/registry/ModItems.java", '''
package de.sporenwerk.registry;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.item.FeldhandbuchItem;
import de.sporenwerk.item.FeldwissenItem;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import java.util.List;

public final class ModItems {
    public static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, Sporenwerk.MODID);

    public static final RegistryObject<Item> FASER = basic("faser");
    public static final RegistryObject<Item> BERNSTEINKAPPE = basic("bernsteinkappe");
    public static final RegistryObject<Item> ROTWURZEL = basic("rotwurzel");
    public static final RegistryObject<Item> FILTERMOOS = basic("filtermoos");
    public static final RegistryObject<Item> FASERROHR_SAMEN = ITEMS.register("faserrohr_samen",
            () -> new net.minecraft.world.item.ItemNameBlockItem(ModBlocks.FASERROHR.get(), new Item.Properties()));
    public static final RegistryObject<Item> BERNSTEINKAPPE_SPOREN = ITEMS.register("bernsteinkappe_sporen",
            () -> new net.minecraft.world.item.ItemNameBlockItem(ModBlocks.BERNSTEINKAPPE.get(), new Item.Properties()));
    public static final RegistryObject<Item> ROTWURZEL_SAMEN = ITEMS.register("rotwurzel_samen",
            () -> new net.minecraft.world.item.ItemNameBlockItem(ModBlocks.ROTWURZEL.get(), new Item.Properties()));
    public static final RegistryObject<Item> FILTERMOOS_SPOREN = ITEMS.register("filtermoos_sporen",
            () -> new net.minecraft.world.item.ItemNameBlockItem(ModBlocks.FILTERMOOS.get(), new Item.Properties()));
    public static final RegistryObject<Item> PFLANZENRESTE = basic("pflanzenreste");
    public static final RegistryObject<Item> BIOMASSE = basic("biomasse");
    public static final RegistryObject<Item> FELDWISSEN = ITEMS.register("feldwissen",
            () -> new FeldwissenItem(new Item.Properties().stacksTo(64)));
    public static final RegistryObject<Item> FELDHANDBUCH = ITEMS.register("feldhandbuch",
            () -> new FeldhandbuchItem(new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> MASCHINENTEIL = basic("maschinenteil");
    public static final RegistryObject<Item> FILTER = basic("filter");

    private static RegistryObject<Item> basic(String name) {
        return ITEMS.register(name, () -> new Item(new Item.Properties()));
    }
    private ModItems() {}
}
''')
# Restore spawn egg registration added by the Dämmerling step, because ModItems is rewritten.
replace_once("src/main/java/de/sporenwerk/registry/ModItems.java",
             "import net.minecraft.world.item.ItemStack;",
             "import net.minecraft.world.item.ItemStack;\nimport net.minecraft.world.item.SpawnEggItem;")
replace_once("src/main/java/de/sporenwerk/registry/ModItems.java",
             'public static final RegistryObject<Item> MASCHINENTEIL = basic("maschinenteil");',
             'public static final RegistryObject<Item> DAEMMERLING_SPAWN_EGG = ITEMS.register("daemmerling_spawn_egg", () -> new SpawnEggItem(ModEntities.DAEMMERLING.get(), 0x263D2D, 0xB23843, new Item.Properties()));\n    public static final RegistryObject<Item> MASCHINENTEIL = basic("maschinenteil");')

# Screen translations and creative tab.
lang_path = RES / "assets/sporenwerk/lang/de_de.json"
lang = json.loads(lang_path.read_text(encoding="utf-8"))
lang["gui.sporenwerk.skill_title"] = "Feldhandbuch – Wissensbaum"
lang["item.sporenwerk.feldhandbuch"] = "Feldhandbuch"
lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

p = ROOT / "build.gradle"
s = p.read_text(encoding="utf-8")
s = re.sub(r"version = '[^']+'", "version = '1.1.0'", s, count=1)
p.write_text(s, encoding="utf-8")

readme = ROOT / "README.md"
s = readme.read_text(encoding="utf-8")
s = s.replace("1.0.2", "1.1.0").replace("V1.0.2", "V1.1.0")
s += "\n\n## V1.1.0 Skill tree\nRight-click the Feldhandbuch to open the custom three-branch skill tree. Costs and levels are synced from the server. Upgrade buttons execute server commands which validate and save the purchase; world progression is not client-authored.\n"
readme.write_text(s, encoding="utf-8")
print("Installed the V1.1.0 skill-tree screen.")
