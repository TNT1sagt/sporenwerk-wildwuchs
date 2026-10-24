#!/usr/bin/env python3
"""Add a three-grade cartridge economy and a placeable Spore Filter Maintenance Bench."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")

def replace_once(rel, old, new, label):
    path = ROOT / rel
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Filter maintenance patch cannot locate {label} in {rel}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")

# Tiered cartridges reuse the same item implementation; their repair capacity is data on each registered item.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
basic_line = '    public static final RegistryObject<Item> SPORENFILTEREINSATZ = ITEMS.register("sporenfiltereinsatz", () -> new de.sporenwerk.item.SporeFilterCartridgeItem(new Item.Properties().stacksTo(16)));'
basic_tier_line = '    public static final RegistryObject<Item> SPORENFILTEREINSATZ = ITEMS.register("sporenfiltereinsatz", () -> new de.sporenwerk.item.SporeFilterCartridgeItem(60, new Item.Properties().stacksTo(16)));'
if basic_line in items:
    items = items.replace(basic_line, basic_tier_line, 1)
if "SPORENFILTEREINSATZ_VERSTAERKT" not in items:
    if basic_tier_line not in items:
        raise SystemExit("Cannot find base filter cartridge registration")
    advanced = basic_tier_line + """
    public static final RegistryObject<Item> SPORENFILTEREINSATZ_VERSTAERKT = ITEMS.register("sporenfiltereinsatz_verstaerkt", () -> new de.sporenwerk.item.SporeFilterCartridgeItem(100, new Item.Properties().stacksTo(16)));
    public static final RegistryObject<Item> SPORENFILTEREINSATZ_MUTAGEN = ITEMS.register("sporenfiltereinsatz_mutagen", () -> new de.sporenwerk.item.SporeFilterCartridgeItem(143, new Item.Properties().stacksTo(16)));"""
    items = items.replace(basic_tier_line, advanced, 1)
items_path.write_text(items, encoding="utf-8")

# Upgrade the cartridge implementation without changing the already-tested hand-use fallback.
cartridge_path = "src/main/java/de/sporenwerk/item/SporeFilterCartridgeItem.java"
cartridge = read(cartridge_path)
if "import net.minecraft.advancements.Advancement;" not in cartridge:
    cartridge = cartridge.replace(
        "import de.sporenwerk.registry.ModItems;",
        "import de.sporenwerk.registry.ModItems;\nimport net.minecraft.advancements.Advancement;\nimport net.minecraft.resources.ResourceLocation;\nimport net.minecraft.server.level.ServerPlayer;"
    )
filter_test_path = ROOT / "tools/test_spore_filter.py"
filter_test = filter_test_path.read_text(encoding="utf-8")
old_test_token = '"mask.setDamageValue(Math.max(0, before - REPAIR_AMOUNT))"'
new_test_token = '"mask.setDamageValue(Math.max(0, before - repairAmount))"'
if old_test_token in filter_test:
    filter_test = filter_test.replace(old_test_token, new_test_token, 1)
elif new_test_token not in filter_test:
    raise SystemExit("Cannot update the filter regression test for tiered repair amounts")
filter_test_path.write_text(filter_test, encoding="utf-8")
old_ctor = """    public static final int REPAIR_AMOUNT = 60;

    public SporeFilterCartridgeItem(Properties properties) {
        super(properties);
    }"""
new_ctor = """    public static final int REPAIR_AMOUNT = 60;
    public static final int MUTAGENIC_REPAIR_AMOUNT = 143;
    private final int repairAmount;

    public SporeFilterCartridgeItem(int repairAmount, Properties properties) {
        super(properties);
        this.repairAmount = Math.max(1, repairAmount);
    }

    public int repairAmount() {
        return repairAmount;
    }

    public boolean requiresMutagenResearch() {
        return repairAmount >= MUTAGENIC_REPAIR_AMOUNT;
    }

    public static boolean hasMutagenResearch(Player player) {
        if (!(player instanceof ServerPlayer serverPlayer)) return false;
        var server = serverPlayer.getServer();
        if (server == null) return false;
        Advancement research = server.getAdvancements().getAdvancement(
                new ResourceLocation("sporenwerk", "mutagen_laboratory"));
        return research != null && serverPlayer.getAdvancements().getOrStartProgress(research).isDone();
    }"""
if old_ctor in cartridge:
    cartridge = cartridge.replace(old_ctor, new_ctor, 1)
elif "private final int repairAmount;" not in cartridge:
    raise SystemExit("Cannot update the cartridge tier constructor")
cartridge = cartridge.replace("Math.min(REPAIR_AMOUNT, before)", "Math.min(repairAmount, before)")
cartridge = cartridge.replace("Math.max(0, before - REPAIR_AMOUNT)", "Math.max(0, before - repairAmount)")

# A mutagenic cartridge must not provide its repair before laboratory research.
if "message.sporenwerk.filterbench.research_required" not in cartridge:
    cartridge_gate_anchor = "        if (mask.getDamageValue() <= 0) {"
    cartridge_gate = """        if (requiresMutagenResearch() && !level.isClientSide && !hasMutagenResearch(player)) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.filterbench.research_required").withStyle(ChatFormatting.LIGHT_PURPLE), true);
            return InteractionResultHolder.fail(cartridge);
        }

"""
    if cartridge_gate_anchor not in cartridge:
        raise SystemExit("Cannot locate cartridge durability guard for research gating")
    cartridge = cartridge.replace(cartridge_gate_anchor, cartridge_gate + cartridge_gate_anchor, 1)
old_tooltip = """        tooltip.add(Component.translatable("tooltip.sporenwerk.sporenfiltereinsatz.2")
                .withStyle(ChatFormatting.GRAY));"""
new_tooltip = """        String quality = repairAmount >= 143 ? "mutagen"
                : repairAmount >= 100 ? "reinforced" : "basic";
        tooltip.add(Component.translatable("tooltip.sporenwerk.sporenfiltereinsatz.quality." + quality)
                .withStyle(repairAmount >= 143 ? ChatFormatting.LIGHT_PURPLE
                        : repairAmount >= 100 ? ChatFormatting.GOLD : ChatFormatting.GRAY));
        tooltip.add(Component.translatable("tooltip.sporenwerk.sporenfiltereinsatz.2", repairAmount)
                .withStyle(ChatFormatting.GRAY));"""
if old_tooltip in cartridge:
    cartridge = cartridge.replace(old_tooltip, new_tooltip, 1)
elif "tooltip.sporenwerk.sporenfiltereinsatz.quality." not in cartridge:
    raise SystemExit("Cannot find cartridge tooltip for tier descriptions")
(ROOT / cartridge_path).write_text(cartridge, encoding="utf-8")

# Give higher filter qualities their own icons rather than reusing the basic sprite.
item_texture_dir = ASSETS / "textures/item"
item_texture_dir.mkdir(parents=True, exist_ok=True)

def cartridge_icon(filename, casing, core, accents):
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outline = (23, 30, 28, 255)
    draw.rectangle((4, 1, 11, 14), fill=outline)
    draw.rectangle((5, 2, 10, 13), fill=casing)
    draw.rectangle((6, 3, 9, 4), fill=accents[0])
    draw.rectangle((6, 5, 9, 10), fill=core)
    draw.rectangle((6, 11, 9, 12), fill=accents[1])
    draw.rectangle((3, 4, 4, 11), fill=accents[0])
    draw.rectangle((11, 4, 12, 11), fill=accents[0])
    draw.point((7, 6), fill=accents[1])
    draw.point((8, 8), fill=accents[1])
    image.save(item_texture_dir / f"{filename}.png", optimize=True)
    write(f"src/main/resources/assets/sporenwerk/models/item/{filename}.json", json.dumps({
        "parent": "minecraft:item/generated",
        "textures": {"layer0": f"sporenwerk:item/{filename}"}
    }, ensure_ascii=False, indent=2) + "\n")

cartridge_icon("sporenfiltereinsatz_verstaerkt", (122, 103, 48, 255),
               (46, 87, 67, 255), ((224, 178, 72, 255), (137, 234, 179, 255)))
cartridge_icon("sporenfiltereinsatz_mutagen", (81, 51, 107, 255),
               (118, 49, 145, 255), ((171, 109, 228, 255), (130, 255, 219, 255)))

# Add the workstation as an ordinary solid block; the station handles repair server-side and has no client-only state.
replace_once(
    "src/main/java/de/sporenwerk/registry/ModBlocks.java",
    "import de.sporenwerk.block.SporeWardBlock;",
    "import de.sporenwerk.block.SporeWardBlock;\nimport de.sporenwerk.block.SporeFilterMaintenanceBlock;\nimport de.sporenwerk.block.MutagenFieldStabilizerBlock;",
    "maintenance block import"
)
ward_registration = """    public static final RegistryObject<Block> SPORENABWEHR = BLOCKS.register("sporenabwehr",
            () -> new SporeWardBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(2.5f).requiresCorrectToolForDrops().sound(SoundType.COPPER)));"""
bench_registration = """    public static final RegistryObject<Block> SPORENFILTERWARTUNGSTISCH = BLOCKS.register("sporenfilterwartungstisch",
            () -> new SporeFilterMaintenanceBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_GRAY)
                    .strength(2.5f).requiresCorrectToolForDrops().sound(SoundType.COPPER)));"""
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             ward_registration, ward_registration + "\n\n" + bench_registration,
             "Spore Ward block registration")
stabilizer_registration = """    public static final RegistryObject<Block> MUTAGENFELD_STABILISATOR = BLOCKS.register("mutagenfeld_stabilisator",
            () -> new MutagenFieldStabilizerBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(4.0f, 9.0f).requiresCorrectToolForDrops().sound(SoundType.GLASS)));"""
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             bench_registration, bench_registration + "\n\n" + stabilizer_registration,
             "field stabilizer block registration")
reinforced_registration = """    public static final RegistryObject<Block> MUTAGENFELD_STABILISATOR_VERSTAERKT = BLOCKS.register("mutagenfeld_stabilisator_verstaerkt",
            () -> new MutagenFieldStabilizerBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLUE)
                    .strength(5.0f, 12.0f).requiresCorrectToolForDrops().sound(SoundType.AMETHYST),
                    MutagenFieldStabilizerBlock.REINFORCED_RADIUS));"""
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             stabilizer_registration, stabilizer_registration + "\n\n" + reinforced_registration,
             "reinforced field stabilizer registration")
advanced_registration = """    public static final RegistryObject<Block> MUTAGENFELD_STABILISATOR_HOCHENTWICKELT = BLOCKS.register("mutagenfeld_stabilisator_hochentwickelt",
            () -> new MutagenFieldStabilizerBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PURPLE)
                    .strength(6.0f, 15.0f).requiresCorrectToolForDrops().sound(SoundType.AMETHYST),
                    MutagenFieldStabilizerBlock.ADVANCED_RADIUS));"""
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             reinforced_registration, reinforced_registration + "\n\n" + advanced_registration,
             "advanced field stabilizer registration")
ward_item = '        ModItems.ITEMS.register("sporenabwehr", () -> new net.minecraft.world.item.BlockItem(SPORENABWEHR.get(), new Item.Properties()));'
bench_item = '        ModItems.ITEMS.register("sporenfilterwartungstisch", () -> new net.minecraft.world.item.BlockItem(SPORENFILTERWARTUNGSTISCH.get(), new Item.Properties()));'
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             ward_item, ward_item + "\n" + bench_item, "Spore Ward item registration")
stabilizer_item = '        ModItems.ITEMS.register("mutagenfeld_stabilisator", () -> new net.minecraft.world.item.BlockItem(MUTAGENFELD_STABILISATOR.get(), new Item.Properties()));'
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             bench_item, bench_item + "\n" + stabilizer_item, "field stabilizer inventory item")
reinforced_item = '        ModItems.ITEMS.register("mutagenfeld_stabilisator_verstaerkt", () -> new net.minecraft.world.item.BlockItem(MUTAGENFELD_STABILISATOR_VERSTAERKT.get(), new Item.Properties()));'
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             stabilizer_item, stabilizer_item + "\n" + reinforced_item, "reinforced field stabilizer inventory item")
advanced_item = '        ModItems.ITEMS.register("mutagenfeld_stabilisator_hochentwickelt", () -> new net.minecraft.world.item.BlockItem(MUTAGENFELD_STABILISATOR_HOCHENTWICKELT.get(), new Item.Properties()));'
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             reinforced_item, reinforced_item + "\n" + advanced_item, "advanced field stabilizer inventory item")

# Add the new consumables and bench to the existing catalogue.
creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
basic_creative = "output.accept(ModItems.SPORENFILTEREINSATZ.get());"
if basic_creative not in creative:
    raise SystemExit("Cannot locate base cartridge in creative tab")
if "output.accept(ModItems.SPORENFILTEREINSATZ_VERSTAERKT.get());" not in creative:
    creative = creative.replace(basic_creative, basic_creative + """
                        output.accept(ModItems.SPORENFILTEREINSATZ_VERSTAERKT.get());
                        output.accept(ModItems.SPORENFILTEREINSATZ_MUTAGEN.get());""", 1)
if "output.accept(ModBlocks.SPORENFILTERWARTUNGSTISCH.get());" not in creative:
    ward_creative = "output.accept(ModBlocks.SPORENABWEHR.get());"
    if ward_creative not in creative:
        raise SystemExit("Cannot locate Spore Ward creative tab entry")
    creative = creative.replace(ward_creative, ward_creative + "\n                        output.accept(ModBlocks.SPORENFILTERWARTUNGSTISCH.get());", 1)
if "output.accept(ModBlocks.MUTAGENFELD_STABILISATOR.get());" not in creative:
    stabilizer_creative = "output.accept(ModBlocks.SPORENFILTERWARTUNGSTISCH.get());"
    if stabilizer_creative not in creative:
        raise SystemExit("Cannot locate maintenance bench for stabilizer creative entry")
    creative = creative.replace(stabilizer_creative, stabilizer_creative + "\n                        output.accept(ModBlocks.MUTAGENFELD_STABILISATOR.get());", 1)
if "output.accept(ModBlocks.MUTAGENFELD_STABILISATOR_VERSTAERKT.get());" not in creative:
    anchor = "output.accept(ModBlocks.MUTAGENFELD_STABILISATOR.get());"
    if anchor not in creative:
        raise SystemExit("Cannot locate base stabilizer entry for reinforced tier")
    creative = creative.replace(anchor, anchor + "\n                        output.accept(ModBlocks.MUTAGENFELD_STABILISATOR_VERSTAERKT.get());", 1)
if "output.accept(ModBlocks.MUTAGENFELD_STABILISATOR_HOCHENTWICKELT.get());" not in creative:
    anchor = "output.accept(ModBlocks.MUTAGENFELD_STABILISATOR_VERSTAERKT.get());"
    if anchor not in creative:
        raise SystemExit("Cannot locate reinforced stabilizer entry for advanced tier")
    creative = creative.replace(anchor, anchor + "\n                        output.accept(ModBlocks.MUTAGENFELD_STABILISATOR_HOCHENTWICKELT.get());", 1)
creative_path.write_text(creative, encoding="utf-8")

write("src/main/java/de/sporenwerk/block/SporeFilterMaintenanceBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.item.SporeFilterCartridgeItem;
import de.sporenwerk.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** Dedicated station for safely servicing a worn Spore Filter Mask with tiered cartridges. */
public final class SporeFilterMaintenanceBlock extends Block {
    public SporeFilterMaintenanceBlock(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        ItemStack cartridgeStack = player.getItemInHand(hand);
        if (!(cartridgeStack.getItem() instanceof SporeFilterCartridgeItem cartridge)) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.filterbench.hold_cartridge").withStyle(ChatFormatting.YELLOW), true);
            return InteractionResult.SUCCESS;
        }

        if (cartridge.requiresMutagenResearch() && !SporeFilterCartridgeItem.hasMutagenResearch(player)) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.filterbench.research_required").withStyle(ChatFormatting.LIGHT_PURPLE), true);
            return InteractionResult.SUCCESS;
        }

        ItemStack mask = player.getItemBySlot(EquipmentSlot.HEAD);
        if (!mask.is(ModItems.SPORENFILTERMASKE.get())) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.sporenfilter.mask_required").withStyle(ChatFormatting.RED), true);
            return InteractionResult.SUCCESS;
        }
        int before = mask.getDamageValue();
        if (before <= 0) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.sporenfilter.full").withStyle(ChatFormatting.GRAY), true);
            return InteractionResult.SUCCESS;
        }

        int restored = Math.min(cartridge.repairAmount(), before);
        mask.setDamageValue(Math.max(0, before - cartridge.repairAmount()));
        if (!player.getAbilities().instabuild) cartridgeStack.shrink(1);
        level.playSound(null, pos, SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 0.65F, 1.15F);
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.filterbench.repaired", restored).withStyle(ChatFormatting.AQUA), true);
        return InteractionResult.SUCCESS;
    }
}
""")

write("src/main/java/de/sporenwerk/block/MutagenFieldStabilizerBlock.java", """
package de.sporenwerk.block;

import net.minecraft.world.level.block.Block;

/** Solid containment component that attenuates high-intensity Mutagen Bloom exposure nearby. */
public final class MutagenFieldStabilizerBlock extends Block {
    public static final int STANDARD_RADIUS = 4;
    public static final int REINFORCED_RADIUS = 8;
    public static final int ADVANCED_RADIUS = 12;
    public static final int MAX_RADIUS = ADVANCED_RADIUS;
    private final int protectionRadius;

    public MutagenFieldStabilizerBlock(Properties properties) {
        this(properties, STANDARD_RADIUS);
    }

    public MutagenFieldStabilizerBlock(Properties properties, int protectionRadius) {
        super(properties);
        this.protectionRadius = Math.max(1, protectionRadius);
    }

    public int protectionRadius() {
        return protectionRadius;
    }
}
""")

# A placed stabilizer provides bounded, local counterplay to the exposure part of a bloom.
bloom_path = SRC / "infection/MutagenBloom.java"
bloom_source = bloom_path.read_text(encoding="utf-8")
if "import de.sporenwerk.block.MutagenFieldStabilizerBlock;" not in bloom_source:
    bloom_source = bloom_source.replace("import de.sporenwerk.registry.ModBlocks;", "import de.sporenwerk.registry.ModBlocks;\nimport de.sporenwerk.block.MutagenFieldStabilizerBlock;", 1)
if "private static boolean hasNearbyStabilizer(ServerLevel level, BlockPos center)" not in bloom_source:
    anchor = "    private static void exposeNearbyPlayers(ServerLevel level, BlockPos origin) {"
    helper = """    /**
     * Bounded local scan. Horizontal range follows the placed tier; vertical range is half as tall.
     * Never asks Minecraft to load a chunk as a side effect of a protection check.
     */
    private static boolean hasNearbyStabilizer(ServerLevel level, BlockPos center) {
        for (int dx = -MutagenFieldStabilizerBlock.MAX_RADIUS; dx <= MutagenFieldStabilizerBlock.MAX_RADIUS; dx++) {
            for (int dy = -MutagenFieldStabilizerBlock.MAX_RADIUS / 2; dy <= MutagenFieldStabilizerBlock.MAX_RADIUS / 2; dy++) {
                for (int dz = -MutagenFieldStabilizerBlock.MAX_RADIUS; dz <= MutagenFieldStabilizerBlock.MAX_RADIUS; dz++) {
                    BlockPos probe = center.offset(dx, dy, dz);
                    if (!level.hasChunkAt(probe)) continue;
                    if (!(level.getBlockState(probe).getBlock() instanceof MutagenFieldStabilizerBlock stabilizer)) continue;
                    int radius = stabilizer.protectionRadius();
                    if (dx * dx + dz * dz <= radius * radius && Math.abs(dy) <= Math.max(2, radius / 2)) return true;
                }
            }
        }
        return false;
    }

"""
    if anchor not in bloom_source:
        raise SystemExit("Cannot locate bloom exposure method for the stabilizer hook")
    bloom_source = bloom_source.replace(anchor, helper + anchor, 1)
exposure_anchor = """            player.displayClientMessage(Component.translatable("message.sporenwerk.mutagen.bloom")
                    .withStyle(ChatFormatting.LIGHT_PURPLE), false);"""
stabilizer_guard = exposure_anchor + """
            if (hasNearbyStabilizer(level, player.blockPosition())) {
                player.displayClientMessage(Component.translatable("message.sporenwerk.mutagen.stabilized")
                        .withStyle(ChatFormatting.AQUA), true);
                continue;
            }"""
if "message.sporenwerk.mutagen.stabilized" not in bloom_source:
    if exposure_anchor not in bloom_source:
        raise SystemExit("Cannot locate bloom warning for stabilizer protection")
    bloom_source = bloom_source.replace(exposure_anchor, stabilizer_guard, 1)
bloom_path.write_text(bloom_source, encoding="utf-8")

# The workstation's top and side are distinct opaque 16x16 block-face textures.
texture_dir = ASSETS / "textures/block"
texture_dir.mkdir(parents=True, exist_ok=True)
ink = (24, 31, 29, 255)
steel = (78, 91, 86, 255)
metal = (130, 145, 132, 255)
light = (180, 193, 164, 255)
green = (77, 157, 105, 255)
violet = (121, 62, 151, 255)
aqua = (111, 226, 187, 255)

top = Image.new("RGBA", (16, 16), steel)
d = ImageDraw.Draw(top)
d.rectangle((0, 0, 15, 2), fill=ink)
d.rectangle((0, 13, 15, 15), fill=ink)
d.rectangle((1, 3, 14, 12), fill=metal)
d.rectangle((2, 4, 13, 11), fill=ink)
d.rectangle((3, 5, 12, 10), fill=(39, 51, 47, 255))
d.rectangle((4, 6, 6, 9), fill=green)
d.rectangle((7, 6, 9, 9), fill=aqua)
d.rectangle((10, 6, 11, 9), fill=violet)
d.point((4, 5), fill=light)
top.save(texture_dir / "sporenfilterwartungstisch_top.png", optimize=True)

side = Image.new("RGBA", (16, 16), ink)
d = ImageDraw.Draw(side)
d.rectangle((1, 1, 14, 4), fill=metal)
d.rectangle((2, 2, 13, 3), fill=steel)
d.rectangle((1, 5, 14, 12), fill=(48, 60, 55, 255))
d.rectangle((2, 6, 13, 11), fill=steel)
d.rectangle((3, 7, 5, 10), fill=violet)
d.rectangle((6, 7, 9, 10), fill=aqua)
d.rectangle((10, 7, 12, 10), fill=green)
d.rectangle((1, 13, 14, 14), fill=metal)
d.rectangle((2, 14, 4, 15), fill=ink)
d.rectangle((11, 14, 13, 15), fill=ink)
side.save(texture_dir / "sporenfilterwartungstisch_side.png", optimize=True)

write("src/main/resources/assets/sporenwerk/blockstates/sporenfilterwartungstisch.json", json.dumps({
    "variants": {"": {"model": "sporenwerk:block/sporenfilterwartungstisch"}}
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/block/sporenfilterwartungstisch.json", json.dumps({
    "parent": "minecraft:block/cube_column",
    "textures": {
        "end": "sporenwerk:block/sporenfilterwartungstisch_top",
        "side": "sporenwerk:block/sporenfilterwartungstisch_side"
    }
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/item/sporenfilterwartungstisch.json", json.dumps({
    "parent": "sporenwerk:block/sporenfilterwartungstisch"
}, ensure_ascii=False, indent=2) + "\n")

# A crisp crystal sprite and opaque block faces are authored as real 16x16 pixel textures.
core_icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
d = ImageDraw.Draw(core_icon)
core_outline = (25, 24, 36, 255)
violet_core = (103, 54, 145, 255)
violet_light = (185, 127, 226, 255)
teal_light = (131, 247, 220, 255)
d.polygon([(7, 0), (11, 2), (15, 7), (12, 12), (8, 15), (3, 12), (0, 7), (3, 3)], fill=core_outline)
d.polygon([(7, 2), (10, 3), (13, 7), (11, 11), (8, 13), (4, 11), (2, 7), (4, 4)], fill=violet_core)
d.polygon([(7, 2), (10, 3), (8, 7), (4, 5)], fill=violet_light)
d.polygon([(8, 7), (13, 7), (11, 11), (8, 13)], fill=(69, 155, 151, 255))
d.point((5, 6), fill=teal_light)
d.point((9, 4), fill=(234, 216, 255, 255))
core_icon.save(item_texture_dir / "mutagenkernkristall.png", optimize=True)
write("src/main/resources/assets/sporenwerk/models/item/mutagenkernkristall.json", json.dumps({
    "parent": "minecraft:item/generated",
    "textures": {"layer0": "sporenwerk:item/mutagenkernkristall"}
}, ensure_ascii=False, indent=2) + "\n")

stabilizer_top = Image.new("RGBA", (16, 16), (30, 48, 51, 255))
d = ImageDraw.Draw(stabilizer_top)
d.rectangle((0, 0, 15, 15), outline=(15, 25, 29, 255), width=2)
d.rectangle((2, 2, 13, 13), fill=(59, 89, 92, 255))
d.rectangle((4, 4, 11, 11), fill=(27, 39, 46, 255))
d.polygon([(7, 4), (9, 5), (11, 8), (9, 11), (7, 12), (5, 9), (5, 7)], fill=violet_core)
d.point((7, 5), fill=teal_light)
d.point((8, 8), fill=violet_light)
stabilizer_top.save(texture_dir / "mutagenfeld_stabilisator_top.png", optimize=True)

stabilizer_side = Image.new("RGBA", (16, 16), (19, 30, 35, 255))
d = ImageDraw.Draw(stabilizer_side)
d.rectangle((1, 1, 14, 4), fill=(107, 135, 136, 255))
d.rectangle((2, 2, 13, 3), fill=(57, 84, 88, 255))
d.rectangle((1, 5, 14, 12), fill=(35, 51, 59, 255))
d.rectangle((2, 6, 13, 11), fill=(60, 91, 91, 255))
d.rectangle((4, 7, 11, 10), fill=(25, 36, 43, 255))
d.rectangle((6, 7, 9, 10), fill=violet_core)
d.point((7, 7), fill=teal_light)
d.rectangle((1, 13, 14, 14), fill=(115, 145, 144, 255))
d.rectangle((2, 14, 4, 15), fill=(17, 28, 31, 255))
d.rectangle((11, 14, 13, 15), fill=(17, 28, 31, 255))
stabilizer_side.save(texture_dir / "mutagenfeld_stabilisator_side.png", optimize=True)

reinforced_top = Image.new("RGBA", (16, 16), (26, 37, 52, 255))
d = ImageDraw.Draw(reinforced_top)
d.rectangle((0, 0, 15, 15), outline=(12, 20, 31, 255), width=2)
d.rectangle((2, 2, 13, 13), fill=(53, 80, 113, 255))
d.rectangle((3, 3, 12, 12), outline=(137, 190, 229, 255), width=1)
d.rectangle((5, 5, 10, 10), fill=(28, 43, 65, 255))
d.polygon([(7, 4), (9, 5), (11, 8), (9, 11), (7, 12), (5, 9), (5, 7)], fill=violet_light)
d.point((7, 5), fill=(213, 246, 255, 255))
d.point((8, 8), fill=teal_light)
reinforced_top.save(texture_dir / "mutagenfeld_stabilisator_verstaerkt_top.png", optimize=True)

reinforced_side = Image.new("RGBA", (16, 16), (16, 27, 43, 255))
d = ImageDraw.Draw(reinforced_side)
d.rectangle((1, 1, 14, 4), fill=(126, 164, 199, 255))
d.rectangle((2, 2, 13, 3), fill=(49, 76, 106, 255))
d.rectangle((1, 5, 14, 12), fill=(33, 52, 77, 255))
d.rectangle((2, 6, 13, 11), fill=(57, 86, 118, 255))
d.rectangle((4, 7, 11, 10), fill=(15, 26, 42, 255))
d.rectangle((6, 7, 9, 10), fill=violet_light)
d.point((7, 7), fill=(213, 246, 255, 255))
d.rectangle((1, 13, 14, 14), fill=(132, 177, 212, 255))
d.rectangle((2, 14, 4, 15), fill=(12, 22, 34, 255))
d.rectangle((11, 14, 13, 15), fill=(12, 22, 34, 255))
reinforced_side.save(texture_dir / "mutagenfeld_stabilisator_verstaerkt_side.png", optimize=True)

advanced_top = Image.new("RGBA", (16, 16), (34, 20, 43, 255))
d = ImageDraw.Draw(advanced_top)
d.rectangle((0, 0, 15, 15), outline=(15, 9, 22, 255), width=2)
d.rectangle((2, 2, 13, 13), fill=(83, 43, 91, 255))
d.rectangle((3, 3, 12, 12), outline=(210, 128, 215, 255), width=1)
d.rectangle((5, 5, 10, 10), fill=(37, 20, 47, 255))
d.polygon([(7, 4), (9, 5), (11, 8), (9, 11), (7, 12), (5, 9), (5, 7)], fill=(205, 67, 190, 255))
d.point((7, 5), fill=(255, 202, 255, 255))
d.point((8, 8), fill=(113, 255, 222, 255))
advanced_top.save(texture_dir / "mutagenfeld_stabilisator_hochentwickelt_top.png", optimize=True)

advanced_side = Image.new("RGBA", (16, 16), (23, 15, 30, 255))
d = ImageDraw.Draw(advanced_side)
d.rectangle((1, 1, 14, 4), fill=(173, 107, 177, 255))
d.rectangle((2, 2, 13, 3), fill=(76, 43, 87, 255))
d.rectangle((1, 5, 14, 12), fill=(49, 28, 57, 255))
d.rectangle((2, 6, 13, 11), fill=(89, 49, 99, 255))
d.rectangle((4, 7, 11, 10), fill=(25, 15, 32, 255))
d.rectangle((6, 7, 9, 10), fill=(205, 67, 190, 255))
d.point((7, 7), fill=(255, 202, 255, 255))
d.point((8, 9), fill=(113, 255, 222, 255))
d.rectangle((1, 13, 14, 14), fill=(189, 122, 190, 255))
d.rectangle((2, 14, 4, 15), fill=(18, 10, 24, 255))
d.rectangle((11, 14, 13, 15), fill=(18, 10, 24, 255))
advanced_side.save(texture_dir / "mutagenfeld_stabilisator_hochentwickelt_side.png", optimize=True)

write("src/main/resources/assets/sporenwerk/blockstates/mutagenfeld_stabilisator.json", json.dumps({
    "variants": {"": {"model": "sporenwerk:block/mutagenfeld_stabilisator"}}
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/block/mutagenfeld_stabilisator.json", json.dumps({
    "parent": "minecraft:block/cube_column",
    "textures": {
        "end": "sporenwerk:block/mutagenfeld_stabilisator_top",
        "side": "sporenwerk:block/mutagenfeld_stabilisator_side"
    }
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/item/mutagenfeld_stabilisator.json", json.dumps({
    "parent": "sporenwerk:block/mutagenfeld_stabilisator"
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/blockstates/mutagenfeld_stabilisator_verstaerkt.json", json.dumps({
    "variants": {"": {"model": "sporenwerk:block/mutagenfeld_stabilisator_verstaerkt"}}
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/block/mutagenfeld_stabilisator_verstaerkt.json", json.dumps({
    "parent": "minecraft:block/cube_column",
    "textures": {
        "end": "sporenwerk:block/mutagenfeld_stabilisator_verstaerkt_top",
        "side": "sporenwerk:block/mutagenfeld_stabilisator_verstaerkt_side"
    }
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/item/mutagenfeld_stabilisator_verstaerkt.json", json.dumps({
    "parent": "sporenwerk:block/mutagenfeld_stabilisator_verstaerkt"
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/blockstates/mutagenfeld_stabilisator_hochentwickelt.json", json.dumps({
    "variants": {"": {"model": "sporenwerk:block/mutagenfeld_stabilisator_hochentwickelt"}}
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/block/mutagenfeld_stabilisator_hochentwickelt.json", json.dumps({
    "parent": "minecraft:block/cube_column",
    "textures": {
        "end": "sporenwerk:block/mutagenfeld_stabilisator_hochentwickelt_top",
        "side": "sporenwerk:block/mutagenfeld_stabilisator_hochentwickelt_side"
    }
}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/item/mutagenfeld_stabilisator_hochentwickelt.json", json.dumps({
    "parent": "sporenwerk:block/mutagenfeld_stabilisator_hochentwickelt"
}, ensure_ascii=False, indent=2) + "\n")

# Tiered recipes form a real upgrade chain rather than three unrelated free refills.
write("src/main/resources/data/sporenwerk/recipes/sporenfiltereinsatz_verstaerkt.json", """
{
  "type": "minecraft:crafting_shapeless",
  "ingredients": [
    { "item": "sporenwerk:sporenfiltereinsatz" },
    { "item": "sporenwerk:mutagenextrakt" },
    { "item": "minecraft:copper_ingot" }
  ],
  "result": { "item": "sporenwerk:sporenfiltereinsatz_verstaerkt", "count": 1 }
}
""")
write("src/main/resources/data/sporenwerk/recipes/sporenfiltereinsatz_mutagen.json", """
{
  "type": "minecraft:crafting_shapeless",
  "ingredients": [
    { "item": "sporenwerk:sporenfiltereinsatz_verstaerkt" },
    { "item": "sporenwerk:mutagenextrakt" },
    { "item": "minecraft:amethyst_shard" }
  ],
  "result": { "item": "sporenwerk:sporenfiltereinsatz_mutagen", "count": 1 }
}
""")
write("src/main/resources/data/sporenwerk/recipes/sporenfilterwartungstisch.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["ITI", "CWF", "IRI"],
  "key": {
    "I": { "item": "minecraft:iron_ingot" },
    "T": { "item": "minecraft:crafting_table" },
    "C": { "item": "minecraft:copper_ingot" },
    "W": { "item": "sporenwerk:sporenresistenter_block" },
    "F": { "item": "sporenwerk:filtermoos" },
    "R": { "item": "minecraft:redstone" }
  },
  "result": { "item": "sporenwerk:sporenfilterwartungstisch", "count": 1 }
}
""")

# The mutagenic cartridge is a research-gated recipe, not just another material upgrade.
write("src/main/resources/data/sporenwerk/advancements/recipes/misc/sporenfiltereinsatz_mutagen.json", """
{
  "parent": "sporenwerk:mutagen_laboratory",
  "display": {
    "icon": { "item": "sporenwerk:sporenfiltereinsatz_mutagen" },
    "title": { "translate": "advancements.sporenwerk.filter_mutagen_research.title" },
    "description": { "translate": "advancements.sporenwerk.filter_mutagen_research.description" },
    "frame": "goal",
    "show_toast": true,
    "announce_to_chat": false,
    "hidden": true
  },
  "criteria": {
    "discover_mutagen_extract": {
      "trigger": "minecraft:inventory_changed",
      "conditions": { "items": [{ "items": ["sporenwerk:mutagenextrakt"] }] }
    }
  },
  "requirements": [["discover_mutagen_extract"]],
  "rewards": { "recipes": ["sporenwerk:sporenfiltereinsatz_mutagen"] }
}
""")

write("src/main/resources/data/sporenwerk/recipes/mutagenfeld_stabilisator.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["IRI", "SKS", "IMI"],
  "key": {
    "I": { "item": "minecraft:iron_ingot" },
    "R": { "item": "minecraft:redstone" },
    "S": { "item": "sporenwerk:sporenresistenter_block" },
    "K": { "item": "sporenwerk:mutagenkernkristall" },
    "M": { "item": "sporenwerk:mutagenextrakt" }
  },
  "result": { "item": "sporenwerk:mutagenfeld_stabilisator", "count": 1 }
}
""")

write("src/main/resources/data/sporenwerk/advancements/recipes/misc/mutagenfeld_stabilisator.json", """
{
  "parent": "sporenwerk:first_mutagen_bloom",
  "display": {
    "icon": { "item": "sporenwerk:mutagenfeld_stabilisator" },
    "title": { "translate": "advancements.sporenwerk.mutagen_stabilizer.title" },
    "description": { "translate": "advancements.sporenwerk.mutagen_stabilizer.description" },
    "frame": "goal",
    "show_toast": true,
    "announce_to_chat": false,
    "hidden": true
  },
  "criteria": {
    "find_condensed_core": {
      "trigger": "minecraft:inventory_changed",
      "conditions": { "items": [{ "items": ["sporenwerk:mutagenkernkristall"] }] }
    }
  },
  "requirements": [["find_condensed_core"]],
  "rewards": { "recipes": ["sporenwerk:mutagenfeld_stabilisator"] }
}
""")
write("src/main/resources/data/sporenwerk/recipes/mutagenfeld_stabilisator_verstaerkt.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["ACA", "KSK", "ARA"],
  "key": {
    "A": { "item": "minecraft:amethyst_shard" },
    "C": { "item": "minecraft:copper_ingot" },
    "K": { "item": "sporenwerk:mutagenkernkristall" },
    "S": { "item": "sporenwerk:mutagenfeld_stabilisator" },
    "R": { "item": "minecraft:redstone" }
  },
  "result": { "item": "sporenwerk:mutagenfeld_stabilisator_verstaerkt", "count": 1 }
}
""")
write("src/main/resources/data/sporenwerk/advancements/recipes/misc/mutagenfeld_stabilisator_verstaerkt.json", """
{
  "parent": "sporenwerk:recipes/misc/mutagenfeld_stabilisator",
  "display": {
    "icon": { "item": "sporenwerk:mutagenfeld_stabilisator_verstaerkt" },
    "title": { "translate": "advancements.sporenwerk.reinforced_mutagen_stabilizer.title" },
    "description": { "translate": "advancements.sporenwerk.reinforced_mutagen_stabilizer.description" },
    "frame": "goal",
    "show_toast": true,
    "announce_to_chat": false,
    "hidden": true
  },
  "criteria": {
    "acquire_stabilizer": {
      "trigger": "minecraft:inventory_changed",
      "conditions": { "items": [{ "items": ["sporenwerk:mutagenfeld_stabilisator"] }] }
    }
  },
  "requirements": [["acquire_stabilizer"]],
  "rewards": { "recipes": ["sporenwerk:mutagenfeld_stabilisator_verstaerkt"] }
}
""")
write("src/main/resources/data/sporenwerk/recipes/mutagenfeld_stabilisator_hochentwickelt.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["NEN", "KSK", " M "],
  "key": {
    "N": { "item": "minecraft:netherite_ingot" },
    "E": { "item": "minecraft:ender_eye" },
    "K": { "item": "sporenwerk:mutagenkernkristall" },
    "S": { "item": "sporenwerk:mutagenfeld_stabilisator_verstaerkt" },
    "M": { "item": "sporenwerk:mutagenextrakt" }
  },
  "result": { "item": "sporenwerk:mutagenfeld_stabilisator_hochentwickelt", "count": 1 }
}
""")
write("src/main/resources/data/sporenwerk/advancements/recipes/misc/mutagenfeld_stabilisator_hochentwickelt.json", """
{
  "parent": "sporenwerk:recipes/misc/mutagenfeld_stabilisator_verstaerkt",
  "display": {
    "icon": { "item": "sporenwerk:mutagenfeld_stabilisator_hochentwickelt" },
    "title": { "translate": "advancements.sporenwerk.advanced_mutagen_stabilizer.title" },
    "description": { "translate": "advancements.sporenwerk.advanced_mutagen_stabilizer.description" },
    "frame": "challenge",
    "show_toast": true,
    "announce_to_chat": false,
    "hidden": true
  },
  "criteria": {
    "acquire_reinforced_stabilizer": {
      "trigger": "minecraft:inventory_changed",
      "conditions": { "items": [{ "items": ["sporenwerk:mutagenfeld_stabilisator_verstaerkt"] }] }
    }
  },
  "requirements": [["acquire_reinforced_stabilizer"]],
  "rewards": { "recipes": ["sporenwerk:mutagenfeld_stabilisator_hochentwickelt"] }
}
""")

# Extend both locales without deleting existing field/scanner/filter strings.
locale_additions = {
    "de_de.json": {
        "item.sporenwerk.sporenfiltereinsatz_verstaerkt": "Verstärkter Sporenfiltereinsatz",
        "item.sporenwerk.sporenfiltereinsatz_mutagen": "Mutagener Sporenfiltereinsatz",
        "block.sporenwerk.sporenfilterwartungstisch": "Sporenfilter-Wartungstisch",
        "item.sporenwerk.sporenfilterwartungstisch": "Sporenfilter-Wartungstisch",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.basic": "Qualität I – Standardfilter",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.reinforced": "Qualität II – Verstärkter Filter",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.mutagen": "Qualität III – Mutagener Filter",
        "tooltip.sporenwerk.sporenfiltereinsatz.2": "Stellt bis zu %s Haltbarkeit wieder her.",
        "tooltip.sporenwerk.sporenfilterwartungstisch.1": "Rechtsklick mit einem Filtereinsatz, während die Maske getragen wird.",
        "tooltip.sporenwerk.sporenfilterwartungstisch.2": "Verstärkte und mutagene Einsätze stellen mehr Haltbarkeit wieder her.",
        "message.sporenwerk.filterbench.hold_cartridge": "Halte einen Sporenfiltereinsatz in der Hand.",
        "message.sporenwerk.filterbench.repaired": "Wartung abgeschlossen: %s Haltbarkeit wiederhergestellt.",
        "message.sporenwerk.filterbench.research_required": "Schließe zuerst die Mutagenlabor-Forschung ab.",
        "advancements.sporenwerk.filter_mutagen_research.title": "Mutagenfilter-Protokoll",
        "advancements.sporenwerk.filter_mutagen_research.description": "Entdecke Mutagenextrakt, um den mutagenen Filtereinsatz freizuschalten.",
        "item.sporenwerk.mutagenkernkristall": "Kondensierter Mutagenkern",
        "tooltip.sporenwerk.mutagenkernkristall.1": "Seltenes Nebenprodukt einer Mutagenblüte.",
        "tooltip.sporenwerk.mutagenkernkristall.2": "Kernstück für einen lokalen Feldstabilisator.",
        "block.sporenwerk.mutagenfeld_stabilisator": "Mutagenfeld-Stabilisator",
        "item.sporenwerk.mutagenfeld_stabilisator": "Mutagenfeld-Stabilisator",
        "block.sporenwerk.mutagenfeld_stabilisator_verstaerkt": "Verstärkter Mutagenfeld-Stabilisator",
        "item.sporenwerk.mutagenfeld_stabilisator_verstaerkt": "Verstärkter Mutagenfeld-Stabilisator",
        "tooltip.sporenwerk.mutagenfeld_stabilisator_verstaerkt.1": "Dämpft Blütenimpulse im horizontalen Radius von 8 Blöcken.",
        "tooltip.sporenwerk.mutagenfeld_stabilisator_verstaerkt.2": "Ein Upgrade für größere Mutagen-Forschungsanlagen.",
        "advancements.sporenwerk.reinforced_mutagen_stabilizer.title": "Verstärkte Feldstabilisierung",
        "advancements.sporenwerk.reinforced_mutagen_stabilizer.description": "Baue einen Standard-Stabilisator und sichere einen weiteren Mutagenkern.",
        "block.sporenwerk.mutagenfeld_stabilisator_hochentwickelt": "Hochleistungs-Mutagenfeld-Stabilisator",
        "item.sporenwerk.mutagenfeld_stabilisator_hochentwickelt": "Hochleistungs-Mutagenfeld-Stabilisator",
        "tooltip.sporenwerk.mutagenfeld_stabilisator_hochentwickelt.1": "Dämpft Blütenimpulse im horizontalen Radius von 12 Blöcken.",
        "tooltip.sporenwerk.mutagenfeld_stabilisator_hochentwickelt.2": "Hochentwickelte Abschirmung für großflächige Forschungsanlagen.",
        "advancements.sporenwerk.advanced_mutagen_stabilizer.title": "Hochleistungs-Feldstabilisierung",
        "advancements.sporenwerk.advanced_mutagen_stabilizer.description": "Baue einen verstärkten Stabilisator und erschließe die nächste Abschirmstufe.",
        "tooltip.sporenwerk.mutagenfeld_stabilisator.1": "Dämpft den Mutagenblüten-Impuls im Umkreis von 4 Blöcken.",
        "tooltip.sporenwerk.mutagenfeld_stabilisator.2": "Passive Stabilisierung nahe deiner Forschungsanlage.",
        "message.sporenwerk.mutagen.stabilized": "Der Feldstabilisator dämpft den Blütenimpuls.",
        "advancements.sporenwerk.mutagen_stabilizer.title": "Feldstabilisierung",
        "advancements.sporenwerk.mutagen_stabilizer.description": "Berge einen kondensierten Mutagenkern und schalte den Feldstabilisator frei."
    },
    "en_us.json": {
        "item.sporenwerk.sporenfiltereinsatz_verstaerkt": "Reinforced Spore Filter Cartridge",
        "item.sporenwerk.sporenfiltereinsatz_mutagen": "Mutagenic Spore Filter Cartridge",
        "block.sporenwerk.sporenfilterwartungstisch": "Spore Filter Maintenance Bench",
        "item.sporenwerk.sporenfilterwartungstisch": "Spore Filter Maintenance Bench",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.basic": "Quality I — Standard filter",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.reinforced": "Quality II — Reinforced filter",
        "tooltip.sporenwerk.sporenfiltereinsatz.quality.mutagen": "Quality III — Mutagenic filter",
        "tooltip.sporenwerk.sporenfiltereinsatz.2": "Restores up to %s durability.",
        "tooltip.sporenwerk.sporenfilterwartungstisch.1": "Right-click with a filter cartridge while wearing the mask.",
        "tooltip.sporenwerk.sporenfilterwartungstisch.2": "Reinforced and Mutagen cartridges restore more durability.",
        "message.sporenwerk.filterbench.hold_cartridge": "Hold a Spore Filter Cartridge in your hand.",
        "message.sporenwerk.filterbench.repaired": "Maintenance complete: restored %s durability.",
        "message.sporenwerk.filterbench.research_required": "Complete the Mutagen Laboratory research first.",
        "advancements.sporenwerk.filter_mutagen_research.title": "Mutagen Filter Protocol",
        "advancements.sporenwerk.filter_mutagen_research.description": "Discover Mutagen Extract to unlock the Mutagenic Filter Cartridge.",
        "item.sporenwerk.mutagenkernkristall": "Condensed Mutagen Core",
        "tooltip.sporenwerk.mutagenkernkristall.1": "Rare residue left by a Mutagen Bloom.",
        "tooltip.sporenwerk.mutagenkernkristall.2": "Core component for a local field stabilizer.",
        "block.sporenwerk.mutagenfeld_stabilisator": "Mutagen Field Stabilizer",
        "item.sporenwerk.mutagenfeld_stabilisator": "Mutagen Field Stabilizer",
        "block.sporenwerk.mutagenfeld_stabilisator_verstaerkt": "Reinforced Mutagen Field Stabilizer",
        "item.sporenwerk.mutagenfeld_stabilisator_verstaerkt": "Reinforced Mutagen Field Stabilizer",
        "tooltip.sporenwerk.mutagenfeld_stabilisator_verstaerkt.1": "Dampens bloom pulses within an 8-block horizontal radius.",
        "tooltip.sporenwerk.mutagenfeld_stabilisator_verstaerkt.2": "An upgrade for larger Mutagen research facilities.",
        "advancements.sporenwerk.reinforced_mutagen_stabilizer.title": "Reinforced Field Stabilization",
        "advancements.sporenwerk.reinforced_mutagen_stabilizer.description": "Build a standard stabilizer and secure another Mutagen Core.",
        "block.sporenwerk.mutagenfeld_stabilisator_hochentwickelt": "High-Capacity Mutagen Field Stabilizer",
        "item.sporenwerk.mutagenfeld_stabilisator_hochentwickelt": "High-Capacity Mutagen Field Stabilizer",
        "tooltip.sporenwerk.mutagenfeld_stabilisator_hochentwickelt.1": "Dampens bloom pulses within a 12-block horizontal radius.",
        "tooltip.sporenwerk.mutagenfeld_stabilisator_hochentwickelt.2": "Advanced containment for large research facilities.",
        "advancements.sporenwerk.advanced_mutagen_stabilizer.title": "High-Capacity Field Stabilization",
        "advancements.sporenwerk.advanced_mutagen_stabilizer.description": "Build a reinforced stabilizer to unlock the next containment tier.",
        "tooltip.sporenwerk.mutagenfeld_stabilisator.1": "Dampens the Mutagen Bloom pulse within 4 blocks.",
        "tooltip.sporenwerk.mutagenfeld_stabilisator.2": "Passive stabilization for nearby research facilities.",
        "message.sporenwerk.mutagen.stabilized": "The field stabilizer dampens the bloom pulse.",
        "advancements.sporenwerk.mutagen_stabilizer.title": "Field Stabilization",
        "advancements.sporenwerk.mutagen_stabilizer.description": "Recover a condensed Mutagen Core to unlock the field stabilizer."
    }
}
for filename, additions in locale_additions.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Keep the generated visual QA sheet useful for all new game-ready assets.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
if "sporenfilterwartungstisch_top" not in preview:
    preview = preview.replace(
        '    ("sporenabwehr_active", "Sporenabwehr AN"),',
        '    ("sporenabwehr_active", "Sporenabwehr AN"),\n    ("sporenfilterwartungstisch_top", "Filtertisch oben"),\n    ("sporenfilterwartungstisch_side", "Filtertisch Seite"),',
        1,
    )
if '"mutagenfeld_stabilisator_top"' not in preview:
    preview = preview.replace(
        '    ("sporenfilterwartungstisch_side", "Filtertisch Seite"),',
        '    ("sporenfilterwartungstisch_side", "Filtertisch Seite"),\n    ("mutagenfeld_stabilisator_top", "Stabilisator oben"),\n    ("mutagenfeld_stabilisator_side", "Stabilisator Seite"),',
        1,
    )
if '"mutagenfeld_stabilisator_verstaerkt_top"' not in preview:
    preview = preview.replace(
        '    ("mutagenfeld_stabilisator_side", "Stabilisator Seite"),',
        '    ("mutagenfeld_stabilisator_side", "Stabilisator Seite"),\n    ("mutagenfeld_stabilisator_verstaerkt_top", "Verstärkter Stabilisator oben"),\n    ("mutagenfeld_stabilisator_verstaerkt_side", "Verstärkter Stabilisator Seite"),',
        1,
    )
if '"mutagenfeld_stabilisator_hochentwickelt_top"' not in preview:
    preview = preview.replace(
        '    ("mutagenfeld_stabilisator_verstaerkt_side", "Verstärkter Stabilisator Seite"),',
        '    ("mutagenfeld_stabilisator_verstaerkt_side", "Verstärkter Stabilisator Seite"),\n    ("mutagenfeld_stabilisator_hochentwickelt_top", "Hochleistungs-Stabilisator oben"),\n    ("mutagenfeld_stabilisator_hochentwickelt_side", "Hochleistungs-Stabilisator Seite"),',
        1,
    )
preview = preview.replace("W, H = 1400, 1320", "W, H = 1400, 1440")
preview = preview.replace("panel(24, 365, 1352, 210, \"OPAQUE MINECRAFT BLOCK FACES (16x16)\")",
                          "panel(24, 365, 1352, 320, \"OPAQUE MINECRAFT BLOCK FACES (16x16)\")")
preview = preview.replace("y = 392 + row*82", "y = 392 + row*78")
preview = preview.replace('panel(24, 580, 1352, 200, "CROP GROWTH STAGES / CUTOUT")',
                          'panel(24, 695, 1352, 200, "CROP GROWTH STAGES / CUTOUT")')
preview = preview.replace("y = 625", "y = 740")
preview = preview.replace('draw.text((x, 606), name.upper()', 'draw.text((x, 721), name.upper()')
preview = preview.replace('panel(24, 795, 1352, 185, "LIVE MUTAGEN PHENOTYPES — MATURE PLANTS")',
                          'panel(24, 910, 1352, 185, "LIVE MUTAGEN PHENOTYPES — MATURE PLANTS")')
preview = preview.replace('draw.text((x, 817), name.upper()', 'draw.text((x, 932), name.upper()')
preview = preview.replace("x + strength*67, 838", "x + strength*67, 953")
preview = preview.replace('panel(24, 995, 1352, 295, "ITEM ICONS AND MUTAGEN RESEARCH")',
                          'panel(24, 1110, 1352, 295, "ITEM ICONS AND MUTAGEN RESEARCH")')
preview = preview.replace('35 + col*150, 1022 + row*84', '35 + col*150, 1137 + row*84')
if '"sporenfiltereinsatz_verstaerkt"' not in preview:
    preview = preview.replace('"mutagenprobe", "mutagenextrakt", "mutagene_sporen", "feldscanner"',
                              '"mutagenprobe", "mutagenextrakt", "mutagene_sporen", "feldscanner",\n    "sporenfiltereinsatz", "sporenfiltereinsatz_verstaerkt", "sporenfiltereinsatz_mutagen", "mutagenkernkristall"')
preview_path.write_text(preview, encoding="utf-8")

# This is the final patch in CI, so it owns the current artifact version.
build_path = ROOT / "build.gradle"
build = build_path.read_text(encoding="utf-8")
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]", "version = '1.24.0'", build, count=1)
if count != 1:
    raise SystemExit("Could not bump build.gradle to version 1.24.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
previous_heading = "## Version 1.22.0 — Feldstabilisierung und Mutagenkern"
previous_section = """## Version 1.22.0 — Feldstabilisierung und Mutagenkern

- **Sporenfilter-Wartungstisch:** Eine platzierbare Station repariert die getragene Maske serverseitig mit Filtereinsätzen.
- **Drei Filterqualitäten:** Standard (60 Haltbarkeit), verstärkt (100) und mutagen (143). Die Einsatzqualität steht im Tooltip.
- **Upgrade-Kette und Forschung:** Kupfer, Mutagenextrakt und Amethyst verbinden die drei Filterstufen. Der mutagene Einsatz wird erst nach der Mutagenlabor-Entdeckung im Rezeptbuch freigegeben.
- **Kondensierter Mutagenkern:** Eine Stärke-3-Mutagenblüte hat 12 % Chance, einen sammelbaren Kern zu hinterlassen.
- **Mutagenfeld-Stabilisator:** Der Grundblock aus dem Kern dämpft den Blüten-Expositionsimpuls im horizontalen Radius von 4 Blöcken. Das Rezept wird nach dem Einsammeln eines Kerns freigeschaltet.
- **Erste Mutagenblüte:** Das Advancement „Das Feld atmet“ vergibt einmalig 3 Feldwissen und 2 Myzelkompost.

Der automatische Serverstart bestätigt die technische Startfähigkeit, ersetzt aber keinen manuellen Sicht- und Funktionstest im Minecraft-Client.

"""
if previous_heading not in readme:
    readme = previous_section + readme
previous_heading_123 = "## Version 1.23.0 — Mehrstufige Feldstabilisierung"
previous_section_123 = """## Version 1.23.0 — Mehrstufige Feldstabilisierung

- **Stabilisator Stufe I:** Schutz vor dem Blütenimpuls im horizontalen Radius von 4 Blöcken.
- **Verstärkter Stabilisator Stufe II:** Eigener blau-metallischer Block mit 8 Blöcken horizontalem Radius und bis zu 4 Blöcken Höhenunterschied.
- **Upgrade-Forschung:** Der zweite Bauplan wird nach Erwerb der Grundstufe freigeschaltet. Das Upgrade verlangt einen zusätzlichen Mutagenkern, Amethyst, Kupfer und Redstone.
- **Filterwartung:** Der Sporenfilter-Wartungstisch, drei Filterqualitäten und die serverseitige Forschungsfreigabe bleiben Bestandteil der Version.
- **Kondensierter Mutagenkern und erste Blüte:** Die seltene Kernbelohnung, das einmalige Feldprotokoll und der gespeicherte Cooldown bleiben erhalten.

Die automatischen Tests, der Forge-Build, die JAR-Prüfung und der dedizierte Serverstart waren erfolgreich; ein manueller Sichttest im Minecraft-Client bleibt separat erforderlich.

"""
if previous_heading_123 not in readme:
    readme = previous_section_123 + readme
heading = "## Version 1.24.0 — Hochleistungs-Feldstabilisierung"
section = """## Version 1.24.0 — Hochleistungs-Feldstabilisierung

- **Sporenfilter-Wartungstisch:** Neue platzierbare Station mit eigener 16×16-Pixeltextur für Ober- und Seitenflächen. Rechtsklick mit einem Filtereinsatz wartet die getragene Maske direkt serverseitig.
- **Drei Filterqualitäten:** Standard (60 Haltbarkeit), verstärkt (100) und mutagen (143, eine vollständige Maskenreparatur). Die Qualität steht im Tooltip; die Haltbarkeitsanzeige der Maske bleibt grün/gelb/rot.
- **Echte Upgrade-Kette:** Standardeinsatz → verstärkter Einsatz mit Mutagenextrakt und Kupfer → mutagener Einsatz mit weiterem Extrakt und Amethyst. Der Wartungstisch wird aus Eisen, Kupfer, Redstone, Filtermoos, einem resistenten Block und einem Werktisch hergestellt.
- **Mutagene Forschungsfreigabe:** Der mutagene Einsatz wird erst nach der Mutagenlabor-Entdeckung im Rezeptbuch freigeschaltet. Sowohl die direkte Reparatur als auch die Wartungsstation prüfen serverseitig, ob das Forschungs-Advancement abgeschlossen ist.
- **Kondensierter Mutagenkern:** Eine Stärke-3-Mutagenblüte hinterlässt mit 12 % Chance einen einsammelbaren Kern; der gespeicherte Cooldown begrenzt die Ereignisfrequenz pro Feld.
- **Stabilisator Stufe III:** Ein eigener violett-magenta Kristallblock dämpft Blütenimpulse im horizontalen Radius von 12 Blöcken und bis zu 6 Blöcken Höhenunterschied.
- **Forschung statt Gratis-Upgrade:** Der Hochleistungs-Bauplan wird erst freigegeben, wenn ein verstärkter Stabilisator ins Inventar gelangt. Das Rezept verlangt den Stabilisator der Stufe II, zwei Netherite-Barren, zwei Enderaugen, zwei Mutagenkernkristalle und Mutagenextrakt.
- **Ressourcen und Darstellung:** Die neue Stufe hat eine eigene Blockregistrierung, 16×16-Texturen für Ober- und Seitenflächen, Blockstate, Modelle, Itemeintrag, zweisprachige Beschreibungen und eine Forschungsfreigabe im Rezeptbuch.
- **Effizienter begrenzter Scan:** Der Suchbereich reicht nun bis zum maximalen Radius der höchsten Stufe. Er prüft geladene Chunks, erzwingt keine Chunk-Ladevorgänge und übernimmt den Radius der tatsächlich platzierten Stabilisatorstufe.
- **Bestehende Progression bleibt erhalten:** Die Standard- und verstärkte Stufe, der seltene Mutagenkern, das Sporenfilter-Wartungssystem und ihre Forschungsfreigaben bleiben kompatibel.
- **Rezeptfreigabe durch Entdeckung:** Das Rezept für den Stabilisator erscheint, sobald der Spieler einen kondensierten Mutagenkern einsammelt. Eigene Pixelgrafiken, Blockmodelle, Übersetzungen und Regressionstests decken die vollständige Kette ab.
- **Erste Mutagenblüte:** Wer eine gefährliche Blüte erstmals erlebt, erhält das Advancement „Das Feld atmet“ und ein einmaliges Feldprotokoll mit 3 Feldwissen und 2 Myzelkompost. Die Belohnung wird nur einmal pro Spieler vergeben.
- **Sicherer Betrieb:** Einsatzverbrauch nur bei erfolgreicher Wartung; volle Masken verbrauchen keinen Filter. Kreativspieler verbrauchen keine Einsätze. Handbedienung bleibt als alternative Reparaturmethode verfügbar.
- **Qualitätssicherung:** Neue Verträge prüfen Registrierungen, Upgrade-Rezepte, Tisch-Blockstates/Modelle/Texturen, alle Übersetzungen und die Haltbarkeitswerte. Die Vorschau zeigt die zusätzlichen Texturen und Item-Icons.

Der automatische Serverstart bestätigt die technische Startfähigkeit, ersetzt aber keinen manuellen Sicht- und Funktionstest im Minecraft-Client.

"""
if heading not in readme:
    readme = section + readme
readme_path.write_text(readme, encoding="utf-8")
print("Installed Sporenwerk 1.24.0 with three-tier Mutagen Field Stabilization.")
