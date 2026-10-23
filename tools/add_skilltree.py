#!/usr/bin/env python3
"""Replace the chat-based skill status with a server-authoritative native Minecraft screen."""
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

# The fourth data value is the high word of Field Knowledge; ContainerData transmits shorts.
# This keeps large values correct without a custom networking channel.
replace_once(
    "src/main/java/de/sporenwerk/registry/ModMenus.java",
    "import de.sporenwerk.client.menu.MachineMenu;",
    "import de.sporenwerk.client.menu.MachineMenu;\nimport de.sporenwerk.client.menu.SkillTreeMenu;"
)
replace_once(
    "src/main/java/de/sporenwerk/registry/ModMenus.java",
    '    private ModMenus() {}',
    '''    public static final RegistryObject<MenuType<SkillTreeMenu>> SKILL_TREE = MENUS.register(
            "skill_tree", () -> IForgeMenuType.create((id, playerInventory, data) ->
                    new SkillTreeMenu(id, playerInventory)));
    private ModMenus() {}'''
)

write("src/main/java/de/sporenwerk/client/menu/SkillTreeMenu.java", '''
package de.sporenwerk.client.menu;

import de.sporenwerk.registry.ModMenus;
import de.sporenwerk.skill.SkillData;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;

/**
 * Skill data is authoritative on the server. Only the selected branch index crosses
 * the vanilla container-button packet; costs and branch levels are rechecked server-side.
 */
public final class SkillTreeMenu extends AbstractContainerMenu {
    private final ContainerData data;

    public SkillTreeMenu(int id, Inventory playerInventory) {
        super(ModMenus.SKILL_TREE.get(), id);
        Player player = playerInventory.player;
        if (player instanceof ServerPlayer serverPlayer) {
            SkillData progress = SkillData.get(serverPlayer.serverLevel());
            this.data = new ContainerData() {
                @Override public int get(int index) {
                    int knowledge = progress.knowledge();
                    return switch (index) {
                        case 0 -> knowledge & 0xFFFF;
                        case 1 -> (knowledge >>> 16) & 0x7FFF;
                        case 2 -> progress.growthLevel();
                        case 3 -> progress.harvestLevel();
                        case 4 -> progress.machineLevel();
                        default -> 0;
                    };
                }
                @Override public void set(int index, int value) { }
                @Override public int getCount() { return 5; }
            };
        } else {
            this.data = new SimpleContainerData(5);
        }
        addDataSlots(data);
    }

    public int knowledge() {
        return (data.get(0) & 0xFFFF) | ((data.get(1) & 0x7FFF) << 16);
    }

    public int level(int branch) {
        return switch (branch) {
            case 0 -> data.get(2);
            case 1 -> data.get(3);
            case 2 -> data.get(4);
            default -> 0;
        };
    }

    public int cost(int branch) {
        int level = level(branch);
        return 10 + level * 15 + level * level * 2;
    }

    public boolean canBuy(int branch) {
        return level(branch) < 10 && knowledge() >= cost(branch);
    }

    public static SkillData.Branch branch(int index) {
        return switch (index) {
            case 0 -> SkillData.Branch.ANBAU;
            case 1 -> SkillData.Branch.ERNTE;
            case 2 -> SkillData.Branch.MASCHINEN;
            default -> null;
        };
    }

    @Override
    public boolean clickMenuButton(Player player, int buttonId) {
        if (!(player instanceof ServerPlayer serverPlayer)) return false;
        SkillData.Branch selected = branch(buttonId);
        if (selected == null) return false;

        SkillData progress = SkillData.get(serverPlayer.serverLevel());
        int cost = progress.upgradeCost(selected);
        if (progress.level(selected) >= 10) {
            serverPlayer.displayClientMessage(Component.literal("Dieser Zweig ist bereits vollständig erforscht."), true);
            return false;
        }
        if (!progress.buyUpgrade(selected)) {
            serverPlayer.displayClientMessage(Component.literal(
                    "Nicht genug Feldwissen: benötigt " + cost + ", vorhanden " + progress.knowledge() + "."), true);
            return false;
        }
        serverPlayer.displayClientMessage(Component.literal(
                "Forschung abgeschlossen: " + selected.name() + " " + progress.level(selected) + "/10."), true);
        return true;
    }

    @Override
    public boolean stillValid(Player player) {
        return player.isAlive();
    }
}
''')

write("src/main/java/de/sporenwerk/client/menu/SkillTreeScreen.java", '''
package de.sporenwerk.client.menu;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

public final class SkillTreeScreen extends AbstractContainerScreen<SkillTreeMenu> {
    private final Button[] purchaseButtons = new Button[3];

    public SkillTreeScreen(SkillTreeMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        this.imageWidth = 264;
        this.imageHeight = 180;
        this.inventoryLabelY = -1000;
        this.titleLabelY = -1000;
    }

    @Override
    protected void init() {
        super.init();
        for (int branch = 0; branch < 3; branch++) {
            final int branchId = branch;
            int cardX = leftPos + 7 + branch * 84;
            purchaseButtons[branch] = addRenderableWidget(Button.builder(
                    Component.literal("ERFORSCHEN"),
                    button -> {
                        if (minecraft != null && minecraft.gameMode != null) {
                            minecraft.gameMode.handleInventoryButtonClick(menu.containerId, branchId);
                        }
                    }).bounds(cardX + 3, topPos + 109, 74, 19).build());
        }
        updateButtons();
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        updateButtons();
    }

    private void updateButtons() {
        for (int branch = 0; branch < 3; branch++) {
            Button button = purchaseButtons[branch];
            if (button == null) continue;
            int level = menu.level(branch);
            int cost = menu.cost(branch);
            if (level >= 10) {
                button.setMessage(Component.literal("VOLLSTÄNDIG"));
                button.active = false;
            } else {
                button.setMessage(Component.literal("Lernen · " + cost + " FW"));
                button.active = menu.canBuy(branch);
            }
        }
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        int x = leftPos, y = topPos;
        g.fill(x - 1, y - 1, x + imageWidth + 1, y + imageHeight + 1, 0xFF080F0D);
        g.fill(x, y, x + imageWidth, y + imageHeight, 0xFF18231F);
        g.fill(x + 4, y + 4, x + imageWidth - 4, y + 35, 0xFF0D1512);
        g.fill(x + 5, y + 37, x + imageWidth - 5, y + 38, 0xFFB58C48);
        for (int branch = 0; branch < 3; branch++) {
            int cardX = x + 7 + branch * 84;
            int level = menu.level(branch);
            g.fill(cardX, y + 43, cardX + 80, y + 132, 0xFF202F28);
            g.fill(cardX, y + 43, cardX + 80, y + 44, 0xFF637A5E);
            g.fill(cardX, y + 43, cardX + 1, y + 132, 0xFF637A5E);
            g.fill(cardX + 79, y + 43, cardX + 80, y + 132, 0xFF637A5E);
            g.fill(cardX, y + 131, cardX + 80, y + 132, 0xFF637A5E);
            for (int pip = 0; pip < 10; pip++) {
                int px = cardX + 5 + pip * 7;
                int color = pip < level ? (branch == 0 ? 0xFF83C77D : branch == 1 ? 0xFFE5B558 : 0xFF75C8BF) : 0xFF101714;
                g.fill(px, y + 97, px + 5, y + 101, color);
                if (pip < level) g.fill(px, y + 97, px + 5, y + 98, 0xFFDCE8B7);
            }
        }
        g.fill(x + 7, y + 136, x + imageWidth - 7, y + 137, 0xFF485A4E);
        g.fill(x + 7, y + 166, x + imageWidth - 7, y + 167, 0xFF485A4E);
    }

    @Override
    protected void renderLabels(GuiGraphics g, int mouseX, int mouseY) {
        String title = "FELDWISSEN  //  FORSCHUNGSARCHIV";
        g.drawString(font, title, (imageWidth - font.width(title)) / 2, 9, 0xFFE4D6A9, false);
        g.drawString(font, Component.literal("Erfahrung aus Anbau, Entdeckungen und Produktion"), 9, 23, 0xFFA3B7A4, false);
        g.drawString(font, Component.literal("Verfügbar: " + menu.knowledge() + " Feldwissen"), 9, 45, 0xFFE7C56B, false);

        drawBranch(g, 0, "ANBAU", "Wachstumsimpulse", "Chance + " + (menu.level(0) * 10) + "%", 0xFF9DD18A);
        int harvestLevel = menu.level(1);
        int bonus = harvestLevel == 0 ? 0 : 1 + (harvestLevel - 1) / 3;
        drawBranch(g, 1, "ERNTE", "Grundbeute", "+" + bonus + " pro Ernte", 0xFFE9C16C);
        drawBranch(g, 2, "MASCHINEN", "Verarbeitungszeit", "−" + (menu.level(2) * 5) + " Ticks", 0xFF8BD4C6);

        g.drawString(font, Component.literal("Kosten steigen mit jeder Stufe. Jede Verbesserung gilt dauerhaft."), 9, 142, 0xFFB4C2B0, false);
        g.drawString(font, Component.literal("Esc schließt das Archiv  ·  Feldwissen erhältst du durch Ernte und Produktion."), 9, 154, 0xFF84978A, false);
        g.drawString(font, Component.literal("„Das Feld hinter dem Glas war gestern leer.“"), 9, 169, 0xFF9E779A, false);
    }

    private void drawBranch(GuiGraphics g, int branch, String name, String effect, String value, int accent) {
        int x = 7 + branch * 84;
        g.drawString(font, Component.literal(name), x + 5, 52, accent, false);
        g.drawString(font, Component.literal(effect), x + 5, 65, 0xFFB7C8B8, false);
        g.drawString(font, Component.literal(value), x + 5, 79, 0xFFE7E9D1, false);
        g.drawString(font, Component.literal("STUFE " + menu.level(branch) + " / 10"), x + 5, 88, 0xFF899E8D, false);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        renderBackground(g);
        super.render(g, mouseX, mouseY, partialTick);
        renderTooltip(g, mouseX, mouseY);
    }
}
''')

write("src/main/java/de/sporenwerk/item/FeldhandbuchItem.java", '''
package de.sporenwerk.item;

import de.sporenwerk.client.menu.SkillTreeMenu;
import de.sporenwerk.skill.SkillData;
import de.sporenwerk.registry.ModMenus;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraftforge.network.NetworkHooks;

/** Opens the native skill-tree interface from the crafted field handbook. */
public final class FeldhandbuchItem extends Item {
    public FeldhandbuchItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, net.minecraft.world.entity.player.Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(player instanceof ServerPlayer serverPlayer)) return InteractionResultHolder.pass(stack);

        NetworkHooks.openScreen(serverPlayer,
                new SimpleMenuProvider((id, inventory, owner) -> new SkillTreeMenu(id, inventory),
                        Component.literal("Sporenwerk  //  Feldwissen")),
                buffer -> { });
        return InteractionResultHolder.success(stack);
    }
}
''')

# Give each machine a unique short purpose line instead of using a generic machine screen.
replace_once(
    "src/main/java/de/sporenwerk/client/menu/MachineMenu.java",
    "    public int progress() { return data.get(0); }",
    '''    public String machineType() {
        return machine.getBlockState().getBlock().builtInRegistryHolder().key().location().getPath();
    }

    public int progress() { return data.get(0); }'''
)
replace_once(
    "src/main/java/de/sporenwerk/client/menu/MachineScreen.java",
    '        g.drawString(font, Component.translatable("gui.sporenwerk.input"), 12, 25, 0xFFB8D0B2, false);',
    '''        g.drawString(font, Component.translatable("gui.sporenwerk.input"), 12, 25, 0xFFB8D0B2, false);'''
)
# Insert a process-specific production label after the input/output labels.
replace_once(
    "src/main/java/de/sporenwerk/client/menu/MachineScreen.java",
    '        g.drawString(font, Component.translatable("gui.sporenwerk.output"), 112, 20, 0xFFB8D0B2, false);',
    '''        g.drawString(font, Component.translatable("gui.sporenwerk.output"), 112, 20, 0xFFB8D0B2, false);
        String process = switch (menu.machineType()) {
            case "feldsammler" -> "SAMMELT  /  PFLANZT NACH";
            case "saatgutpresse" -> "ERNTE  >  SAATGUT";
            case "biomasse_bioreaktor" -> "RESTE  >  BIOMASSE";
            default -> "PRODUKTIONSKETTE";
        };
        g.drawString(font, Component.literal(process), 12, 62, 0xFFE1C37A, false);'''
)

# Register the GUI on the client mod bus.
replace_once(
    "src/main/java/de/sporenwerk/client/ClientModEvents.java",
    "import de.sporenwerk.client.menu.MachineScreen;",
    "import de.sporenwerk.client.menu.MachineScreen;\nimport de.sporenwerk.client.menu.SkillTreeScreen;"
)
replace_once(
    "src/main/java/de/sporenwerk/client/ClientModEvents.java",
    "event.enqueueWork(() -> MenuScreens.register(ModMenus.MACHINE.get(), MachineScreen::new));",
    """event.enqueueWork(() -> {
            MenuScreens.register(ModMenus.MACHINE.get(), MachineScreen::new);
            MenuScreens.register(ModMenus.SKILL_TREE.get(), SkillTreeScreen::new);
        });"""
)

# Version bump and concise README claims.
p = ROOT / "build.gradle"
s = p.read_text(encoding="utf-8")
s = re.sub(r"version = '1\.0\.(?:0|1|2|3)'", "version = '1.0.3'", s, count=1)
if "version = '1.0.3'" not in s:
    s = re.sub(r"version = '[^']+'", "version = '1.0.3'", s, count=1)
p.write_text(s, encoding="utf-8")

readme = ROOT / "README.md"
s = readme.read_text(encoding="utf-8")
s = s.replace("Sporenwerk: Wildwuchs 1.0.2", "Sporenwerk: Wildwuchs 1.0.3")
s = s.replace("sporenwerk-1.0.2.jar", "sporenwerk-1.0.3.jar")
s = s.replace("Feldhandbuch: right-click for a German in-game guide, progression status and clickable upgrade purchases.", "Feldhandbuch: right-click to open a native skill-tree screen with three server-authoritative upgrade branches, live costs, levels, and effects.")
s = s.replace("This is an improved V1.0.2,", "This is an improved V1.0.3,")
readme.write_text(s, encoding="utf-8")

# Keep translations for the new screen.
lang_path = RES / "assets/sporenwerk/lang/de_de.json"
lang = json.loads(lang_path.read_text(encoding="utf-8"))
lang.update({
    "item.sporenwerk.feldhandbuch": "Feldhandbuch",
    "gui.sporenwerk.skilltree.title": "Feldwissen // Forschungsarchiv",
    "gui.sporenwerk.skilltree.buy": "Erforschen"
})
lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Added native skill-tree screen and distinct machine process labels.")
