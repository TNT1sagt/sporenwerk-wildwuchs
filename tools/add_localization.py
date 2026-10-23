#!/usr/bin/env python3
"""Add localized English fallback and machine tooltips for Sporenwerk 1.1.5."""
from pathlib import Path
import json, re, sys

root = Path(sys.argv[1]).resolve()
res = root / "src/main/resources/assets/sporenwerk/lang"
# Ensure machine block items really use the tooltip-enabled item class.
def write(rel, content):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip(), encoding="utf-8")

write("src/main/java/de/sporenwerk/registry/ModBlocks.java", '''
package de.sporenwerk.registry;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.block.MachineBlock;
import de.sporenwerk.block.crop.BernsteinkappeBlock;
import de.sporenwerk.block.crop.FaserrohrBlock;
import de.sporenwerk.block.crop.FiltermoosBlock;
import de.sporenwerk.block.crop.RotwurzelBlock;
import de.sporenwerk.item.MachineBlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModBlocks {
    public static final DeferredRegister<Block> BLOCKS =
            DeferredRegister.create(ForgeRegistries.BLOCKS, Sporenwerk.MODID);

    public static final RegistryObject<Block> FASERROHR = BLOCKS.register("faserrohr",
            () -> new FaserrohrBlock(BlockBehaviour.Properties.of().mapColor(MapColor.PLANT)
                    .noCollission().randomTicks().instabreak().sound(SoundType.CROP)));
    public static final RegistryObject<Block> BERNSTEINKAPPE = BLOCKS.register("bernsteinkappe",
            () -> new BernsteinkappeBlock(BlockBehaviour.Properties.of().mapColor(MapColor.PLANT)
                    .noCollission().randomTicks().instabreak().sound(SoundType.FUNGUS)));
    public static final RegistryObject<Block> ROTWURZEL = BLOCKS.register("rotwurzel",
            () -> new RotwurzelBlock(BlockBehaviour.Properties.of().mapColor(MapColor.PLANT)
                    .noCollission().randomTicks().instabreak().sound(SoundType.CROP)));
    public static final RegistryObject<Block> FILTERMOOS = BLOCKS.register("filtermoos",
            () -> new FiltermoosBlock(BlockBehaviour.Properties.of().mapColor(MapColor.PLANT)
                    .noCollission().randomTicks().instabreak().sound(SoundType.MOSS)));

    public static final RegistryObject<Block> FELDSAMMLER = machine("feldsammler", MapColor.METAL);
    public static final RegistryObject<Block> SAATGUTPRESSE = machine("saatgutpresse", MapColor.COLOR_BROWN);
    public static final RegistryObject<Block> BIOMASSE_BIOREAKTOR = machine("biomasse_bioreaktor", MapColor.COLOR_GREEN);

    private static RegistryObject<Block> machine(String name, MapColor color) {
        RegistryObject<Block> block = BLOCKS.register(name, () -> new MachineBlock(
                BlockBehaviour.Properties.of().mapColor(color).strength(2.0f).sound(SoundType.METAL)
                        .requiresCorrectToolForDrops()));
        ModItems.ITEMS.register(name, () -> new MachineBlockItem(block.get(), name, new Item.Properties()));
        return block;
    }

    private ModBlocks() {}
}
''')

# Give Rotwurzel a modest, tangible use in the early-game medicine loop.
p = root / "src/main/java/de/sporenwerk/registry/ModItems.java"
s = p.read_text(encoding="utf-8")
if "WURZELKONZENTRAT" not in s:
    s = s.replace(
        "import de.sporenwerk.item.FeldhandbuchItem;",
        "import de.sporenwerk.item.FeldhandbuchItem;\nimport de.sporenwerk.item.WurzelkonzentratItem;"
    )
    marker = 'public static final RegistryObject<Item> ROTWURZEL = basic("rotwurzel");'
    if marker not in s:
        raise SystemExit("Could not add Wurzelkonzentrat item registration")
    s = s.replace(marker, marker + '\n    public static final RegistryObject<Item> WURZELKONZENTRAT = ITEMS.register("wurzelkonzentrat", () -> new WurzelkonzentratItem(new Item.Properties().stacksTo(16)));', 1)
    p.write_text(s, encoding="utf-8")

write("src/main/java/de/sporenwerk/item/WurzelkonzentratItem.java", '''
package de.sporenwerk.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/** Early-game field medicine: modest healing, cooldown, and an empty bottle returned on use. */
public final class WurzelkonzentratItem extends Item {
    public WurzelkonzentratItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, net.minecraft.world.entity.player.Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.getHealth() >= player.getMaxHealth()) {
            return InteractionResultHolder.fail(stack);
        }
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(player instanceof ServerPlayer serverPlayer)) return InteractionResultHolder.pass(stack);

        player.heal(4.0F);
        player.getCooldowns().addCooldown(this, 100);
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
            ItemStack bottle = new ItemStack(Items.GLASS_BOTTLE);
            if (!player.getInventory().add(bottle)) player.spawnAtLocation(bottle);
        }
        serverPlayer.displayClientMessage(Component.literal("Rotwurzel-Konzentrat: 2 Herzen regeneriert.")
                .withStyle(ChatFormatting.RED), true);
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.wurzelkonzentrat.heal")
                .withStyle(ChatFormatting.RED));
        tooltip.add(Component.translatable("tooltip.sporenwerk.wurzelkonzentrat.cooldown")
                .withStyle(ChatFormatting.GRAY));
    }
}
''')

write("src/main/resources/assets/sporenwerk/models/item/wurzelkonzentrat.json", '''
{
  "parent": "minecraft:item/generated",
  "textures": { "layer0": "sporenwerk:item/wurzelkonzentrat" }
}
''')

write("src/main/resources/data/sporenwerk/recipes/wurzelkonzentrat.json", '''
{
  "type": "minecraft:crafting_shaped",
  "pattern": [" R ", " S ", " B "],
  "key": {
    "R": { "item": "sporenwerk:rotwurzel" },
    "S": { "item": "minecraft:sugar" },
    "B": { "item": "minecraft:glass_bottle" }
  },
  "result": { "item": "sporenwerk:wurzelkonzentrat", "count": 1 }
}
''')

de_path = res / "de_de.json"
de = json.loads(de_path.read_text(encoding="utf-8"))
de.update({
  "tooltip.sporenwerk.machine.feldsammler.line1": "Erntet reife Sporenwerk-Pflanzen im 5×3×5-Bereich.",
  "tooltip.sporenwerk.machine.feldsammler.line2": "Passende Samen in den ersten vier Eingabefächern ermöglichen Nachpflanzung.",
  "tooltip.sporenwerk.machine.feldsammler.line3": "Ernten werden im internen Ausgabepuffer gestapelt.",
  "tooltip.sporenwerk.machine.saatgutpresse.line1": "Verarbeitet Ernteprodukte zu passenden Samen und Sporen.",
  "tooltip.sporenwerk.machine.saatgutpresse.line2": "Lege Ernte in ein Eingabefach und sammle die Ausgabe rechts.",
  "tooltip.sporenwerk.machine.saatgutpresse.line3": "Der Puffer bleibt auch nach dem Weltneustart erhalten.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line1": "Verarbeitet Pflanzenreste und Biomasse zu weiterem Rohstoff.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line2": "Der interne Rohstoffwert wird gespeichert, statt Items zu spammen.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line3": "Mit Mekanism kann die Maschine FE aus Universal-Kabeln annehmen.",
  "tooltip.sporenwerk.machine.buffer": "Rechtsklick öffnet Inventar und Fortschritt."
})
de_path.write_text(json.dumps(de, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

en = {
  "itemGroup.sporenwerk": "Sporenwerk: Wildgrowth",
  "item.sporenwerk.faser": "Fiber",
  "item.sporenwerk.bernsteinkappe": "Ambercap",
  "item.sporenwerk.rotwurzel": "Redroot",
  "item.sporenwerk.wurzelkonzentrat": "Redroot Concentrate",
  "tooltip.sporenwerk.wurzelkonzentrat.heal": "Restores 2 hearts.",
  "tooltip.sporenwerk.wurzelkonzentrat.cooldown": "5-second cooldown. Returns an empty glass bottle.",
  "item.sporenwerk.filtermoos": "Filter Moss",
  "item.sporenwerk.faserrohr_samen": "Fiber Reed Seeds",
  "item.sporenwerk.bernsteinkappe_sporen": "Ambercap Spores",
  "item.sporenwerk.rotwurzel_samen": "Redroot Seeds",
  "item.sporenwerk.filtermoos_sporen": "Filter Moss Spores",
  "item.sporenwerk.pflanzenreste": "Plant Residue",
  "item.sporenwerk.biomasse": "Biomass",
  "item.sporenwerk.feldwissen": "Field Knowledge",
  "item.sporenwerk.maschinenteil": "Machine Part",
  "item.sporenwerk.filter": "Filter",
  "item.sporenwerk.feldhandbuch": "Field Handbook",
  "item.sporenwerk.verwitterte_notiz": "Weathered Field Report",
  "item.sporenwerk.daemmerling_spawn_egg": "Dämmerling Spawn Egg",
  "block.sporenwerk.faserrohr": "Fiber Reed",
  "block.sporenwerk.bernsteinkappe": "Ambercap",
  "block.sporenwerk.rotwurzel": "Redroot",
  "block.sporenwerk.filtermoos": "Filter Moss",
  "block.sporenwerk.feldsammler": "Field Collector",
  "block.sporenwerk.saatgutpresse": "Seed Press",
  "block.sporenwerk.biomasse_bioreaktor": "Biomass Bioreactor",
  "entity.sporenwerk.daemmerling": "Dämmerling",
  "gui.sporenwerk.input": "INPUT",
  "gui.sporenwerk.output": "BUFFER OUTPUT",
  "gui.sporenwerk.skill_title": "Field Handbook — Skill Tree",
  "advancements.sporenwerk.root.title": "A Patch of Earth",
  "advancements.sporenwerk.root.description": "Find seeds, plant Fiber Reed, and harvest your first fiber.",
  "advancements.sporenwerk.first_crop.title": "Nothing Goes to Waste",
  "advancements.sporenwerk.first_crop.description": "Turn plant residue into biomass.",
  "advancements.sporenwerk.first_machine.title": "The First Machine",
  "advancements.sporenwerk.first_machine.description": "Build a machine for your first production chain.",
  "advancements.sporenwerk.larger_harvest.title": "A Bigger Harvest",
  "advancements.sporenwerk.larger_harvest.description": "Set up the Field Collector and expand production.",
  "advancements.sporenwerk.field_behind_glass.title": "The Field Behind the Glass",
  "advancements.sporenwerk.field_behind_glass.description": "Read the rare report. Some things don't grow in beds.",
  "tooltip.sporenwerk.machine.feldsammler.line1": "Harvests mature Sporenwerk crops in a 5×3×5 area.",
  "tooltip.sporenwerk.machine.feldsammler.line2": "Matching seeds in the first four input slots enable replanting.",
  "tooltip.sporenwerk.machine.feldsammler.line3": "Harvests stack in the internal output buffer.",
  "tooltip.sporenwerk.machine.saatgutpresse.line1": "Processes harvests into matching seeds and spores.",
  "tooltip.sporenwerk.machine.saatgutpresse.line2": "Place a harvest in an input slot and collect output on the right.",
  "tooltip.sporenwerk.machine.saatgutpresse.line3": "The buffer persists across world restarts.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line1": "Processes plant residue and biomass into more raw material.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line2": "Internal production value is stored instead of spawning item spam.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line3": "With Mekanism installed, the machine accepts FE from Universal Cables.",
  "tooltip.sporenwerk.machine.buffer": "Right-click to open inventory and progress."
}
(res / "en_us.json").write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build = root / "build.gradle"
s = build.read_text(encoding="utf-8")
s = re.sub(r"version = '[^']+'", "version = '1.1.5'", s, count=1)
build.write_text(s, encoding="utf-8")

readme = root / "README.md"
s = readme.read_text(encoding="utf-8")
s = s.replace("1.1.2", "1.1.5").replace("V1.1.2", "V1.1.5")
s += "\n\n## English localization and tooltips\nVersion 1.1.5 includes en_us fallback strings and first-use tooltips for all three machines.\n"
readme.write_text(s, encoding="utf-8")
print("Added en_us localization and machine tooltips.")
