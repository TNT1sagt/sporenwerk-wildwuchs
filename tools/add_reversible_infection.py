#!/usr/bin/env python3
"""Install state-preserving, bounded terrain infection and deterministic local restoration."""
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

def replace_once(rel, old, new, label):
    path = ROOT / rel
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Reversible infection patch cannot find {label} in {rel}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")

# Register a non-item terrain state that remembers precisely which ordinary block it replaced.
replace_once(
    "src/main/java/de/sporenwerk/registry/ModBlocks.java",
    "import de.sporenwerk.block.MutationAnchorBlock;",
    "import de.sporenwerk.block.MutationAnchorBlock;\nimport de.sporenwerk.block.InfestedTerrainBlock;",
    "terrain block import"
)
block_marker = '''    public static final RegistryObject<Block> SPORENRESISTENTER_BLOCK = BLOCKS.register("sporenresistenter_block",
            () -> new Block(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE)
                    .strength(4.0f, 9.0f).requiresCorrectToolForDrops().sound(SoundType.GLASS)));'''
block_addition = block_marker + '''

    /** Internal terrain replacement. Its block entity stores the exact original BlockState and seed origin. */
    public static final RegistryObject<Block> MUTAGEN_BODEN = BLOCKS.register("mutagen_boden",
            () -> new InfestedTerrainBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PURPLE)
                    .strength(1.8f, 5.0f).requiresCorrectToolForDrops().sound(SoundType.FUNGUS)));'''
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java", block_marker, block_addition, "terrain block registration")

# Register the block-entity type on the mod bus alongside the other deferred registers.
# Extend the existing entity registry rather than replacing the machine entity entry.
registry_path = SRC / "registry/ModBlockEntities.java"
registry_source = registry_path.read_text(encoding="utf-8")
if "import de.sporenwerk.block.entity.InfestedTerrainBlockEntity;" not in registry_source:
    machine_import = "import de.sporenwerk.block.entity.MachineBlockEntity;"
    if machine_import in registry_source:
        registry_source = registry_source.replace(
            machine_import,
            machine_import + "\nimport de.sporenwerk.block.entity.InfestedTerrainBlockEntity;", 1)
    else:
        marker = "import de.sporenwerk.Sporenwerk;"
        if marker not in registry_source:
            raise SystemExit("Cannot locate ModBlockEntities import section")
        registry_source = registry_source.replace(
            marker, marker + "\nimport de.sporenwerk.block.entity.InfestedTerrainBlockEntity;", 1)
if "MUTAGEN_BODEN" not in registry_source:
    field = """
    public static final RegistryObject<BlockEntityType<InfestedTerrainBlockEntity>> MUTAGEN_BODEN =
            BLOCK_ENTITIES.register("mutagen_boden",
                    () -> BlockEntityType.Builder.of(InfestedTerrainBlockEntity::new,
                            ModBlocks.MUTAGEN_BODEN.get()).build(null));

"""
    marker = "    private ModBlockEntities()"
    index = registry_source.rfind(marker)
    if index < 0:
        index = registry_source.rfind("}")
    if index < 0:
        raise SystemExit("Cannot locate ModBlockEntities class body")
    registry_source = registry_source[:index] + field + registry_source[index:]
registry_path.write_text(registry_source, encoding="utf-8")

# Keep the existing machine registry hookup and add ours only if it is not already present.
sporenwerk_path = SRC / "Sporenwerk.java"
sporenwerk_source = sporenwerk_path.read_text(encoding="utf-8")
if "import de.sporenwerk.registry.ModBlockEntities;" not in sporenwerk_source:
    import_anchor = "import de.sporenwerk.registry.ModEntities;"
    if import_anchor not in sporenwerk_source:
        raise SystemExit("Cannot locate mod entity registry import")
    sporenwerk_source = sporenwerk_source.replace(
        import_anchor, import_anchor + "\nimport de.sporenwerk.registry.ModBlockEntities;", 1)
if "ModBlockEntities.BLOCK_ENTITIES.register(modBus);" not in sporenwerk_source:
    register_anchor = "ModEntities.ENTITIES.register(modBus);"
    if register_anchor not in sporenwerk_source:
        raise SystemExit("Cannot locate ModEntities registry hookup")
    sporenwerk_source = sporenwerk_source.replace(
        register_anchor,
        register_anchor + "\n        ModBlockEntities.BLOCK_ENTITIES.register(modBus);", 1)
sporenwerk_path.write_text(sporenwerk_source, encoding="utf-8")


write("src/main/java/de/sporenwerk/block/entity/InfestedTerrainBlockEntity.java", """
package de.sporenwerk.block.entity;

import de.sporenwerk.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.entity.BlockEntity;

/**
 * State-preserving infection record. Only non-container terrain is converted, so restoring
 * the saved BlockState returns the block's properties (e.g. snowy grass) without data loss.
 */
public final class InfestedTerrainBlockEntity extends BlockEntity {
    private CompoundTag originalStateTag = new CompoundTag();
    private long originPosition;
    private boolean initialized;

    public InfestedTerrainBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.MUTAGEN_BODEN.get(), pos, state);
    }

    public void initialize(BlockState originalState, BlockPos origin) {
        this.originalStateTag = NbtUtils.writeBlockState(originalState);
        this.originPosition = origin.asLong();
        this.initialized = true;
        setChanged();
    }

    public boolean hasOriginalState() {
        return initialized && !originalStateTag.isEmpty();
    }

    public BlockPos origin() {
        return initialized ? BlockPos.of(originPosition) : getBlockPos();
    }

    public BlockState originalState() {
        if (!hasOriginalState() || level == null) return Blocks.DIRT.defaultBlockState();
        return NbtUtils.readBlockState(level.holderLookup(Registries.BLOCK), originalStateTag);
    }

    @Override
    protected void saveAdditional(CompoundTag tag) {
        super.saveAdditional(tag);
        tag.put("OriginalState", originalStateTag.copy());
        tag.putLong("InfectionOrigin", originPosition);
        tag.putBoolean("Initialized", initialized);
    }

    @Override
    public void load(CompoundTag tag) {
        super.load(tag);
        originalStateTag = tag.getCompound("OriginalState").copy();
        originPosition = tag.getLong("InfectionOrigin");
        initialized = tag.getBoolean("Initialized");
    }
}
""")

write("src/main/java/de/sporenwerk/infection/MutationAnchorData.java", """
package de.sporenwerk.infection;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.saveddata.SavedData;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Persists anchor coordinates and deterministic restoration cursors per dimension.
 * A compact registry avoids scanning thousands of positions for every infected block tick.
 */
public final class MutationAnchorData extends SavedData {
    private static final String DATA_NAME = "sporenwerk_mutation_anchors";
    public static final int FIELD_RADIUS = 8;
    public static final int FIELD_HALF_HEIGHT = 12;
    public static final int SWEEP_VOLUME = 17 * 17 * 25;
    public static final int SWEEP_BATCH = 192;
    private final Map<Long, Integer> anchors = new LinkedHashMap<>();

    public static MutationAnchorData get(ServerLevel level) {
        return level.getDataStorage().computeIfAbsent(
                MutationAnchorData::load, MutationAnchorData::new, DATA_NAME);
    }

    public static MutationAnchorData load(CompoundTag tag) {
        MutationAnchorData data = new MutationAnchorData();
        ListTag entries = tag.getList("Anchors", Tag.TAG_COMPOUND);
        for (int i = 0; i < entries.size(); i++) {
            CompoundTag entry = entries.getCompound(i);
            data.anchors.put(entry.getLong("Pos"),
                    Math.floorMod(entry.getInt("Cursor"), SWEEP_VOLUME));
        }
        return data;
    }

    public void register(BlockPos pos) {
        long packed = pos.asLong();
        if (!anchors.containsKey(packed)) {
            anchors.put(packed, 0);
            setDirty();
        }
    }

    public void unregister(BlockPos pos) {
        if (anchors.remove(pos.asLong()) != null) setDirty();
    }

    public boolean containsAnchorWithin(BlockPos target) {
        for (long packed : anchors.keySet()) {
            BlockPos anchor = BlockPos.of(packed);
            long dx = (long) target.getX() - anchor.getX();
            long dz = (long) target.getZ() - anchor.getZ();
            if (dx * dx + dz * dz <= (long) FIELD_RADIUS * FIELD_RADIUS
                    && Math.abs(target.getY() - anchor.getY()) <= FIELD_HALF_HEIGHT) return true;
        }
        return false;
    }

    /** Returns the current scan cursor, then advances it for the next scheduled anchor tick. */
    public int takeSweepStart(BlockPos anchor) {
        long packed = anchor.asLong();
        int start = anchors.getOrDefault(packed, 0);
        if (!anchors.containsKey(packed)) anchors.put(packed, start);
        anchors.put(packed, (start + SWEEP_BATCH) % SWEEP_VOLUME);
        setDirty();
        return start;
    }

    @Override
    public CompoundTag save(CompoundTag tag) {
        ListTag entries = new ListTag();
        for (Map.Entry<Long, Integer> entry : anchors.entrySet()) {
            CompoundTag value = new CompoundTag();
            value.putLong("Pos", entry.getKey());
            value.putInt("Cursor", entry.getValue());
            entries.add(value);
        }
        tag.put("Anchors", entries);
        return tag;
    }
}
""")

# Replace the first-pass field helper with bounded, source-aware spread and a guaranteed sweep cure.
write("src/main/java/de/sporenwerk/infection/MutationField.java", """
package de.sporenwerk.infection;

import de.sporenwerk.block.entity.InfestedTerrainBlockEntity;
import de.sporenwerk.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.entity.BlockEntity;

/** All terrain spread is source-bound. A seed cannot infect outside its finite 8 x 7 x 8 field. */
public final class MutationField {
    public static final int RADIUS = 8;
    public static final int INFECTION_HALF_HEIGHT = 3;
    private MutationField() {}

    public static boolean insideBounds(BlockPos origin, BlockPos target) {
        long dx = (long) target.getX() - origin.getX();
        long dz = (long) target.getZ() - origin.getZ();
        return dx * dx + dz * dz <= (long) RADIUS * RADIUS
                && Math.abs(target.getY() - origin.getY()) <= INFECTION_HALF_HEIGHT;
    }

    public static boolean hasAnchor(ServerLevel level, BlockPos target) {
        return MutationAnchorData.get(level).containsAnchorWithin(target);
    }

    public static boolean hasImmuneBoundary(ServerLevel level, BlockPos pos) {
        if (level.getBlockState(pos).is(ModBlocks.SPORENRESISTENTER_BLOCK.get())) return true;
        for (Direction direction : Direction.values()) {
            if (level.getBlockState(pos.relative(direction)).is(ModBlocks.SPORENRESISTENTER_BLOCK.get())) return true;
        }
        return false;
    }

    private static boolean isConvertibleTerrain(BlockState state) {
        // This explicit whitelist excludes containers, ores, machines, crops, fluids and player-built redstone.
        return state.is(Blocks.DIRT) || state.is(Blocks.GRASS_BLOCK)
                || state.is(Blocks.COARSE_DIRT) || state.is(Blocks.ROOTED_DIRT)
                || state.is(Blocks.STONE) || state.is(Blocks.COBBLESTONE)
                || state.is(Blocks.MOSS_BLOCK) || state.is(Blocks.MYCELIUM)
                || state.is(Blocks.PODZOL) || state.is(Blocks.DEEPSLATE)
                || state.is(Blocks.COBBLED_DEEPSLATE);
    }

    private static boolean infect(ServerLevel level, BlockPos target, BlockPos origin) {
        if (!insideBounds(origin, target) || hasAnchor(level, target)
                || hasImmuneBoundary(level, target)) return false;
        BlockState original = level.getBlockState(target);
        if (!isConvertibleTerrain(original)) return false;
        if (!level.setBlock(target, ModBlocks.MUTAGEN_BODEN.get().defaultBlockState(), 3)) return false;

        BlockEntity blockEntity = level.getBlockEntity(target);
        if (!(blockEntity instanceof InfestedTerrainBlockEntity record)) {
            // Fail closed: never leave terrain overwritten if its restoration record failed to initialize.
            level.setBlock(target, original, 3);
            return false;
        }
        record.initialize(original, origin);
        level.sendBlockUpdated(target, original,
                ModBlocks.MUTAGEN_BODEN.get().defaultBlockState(), 3);
        return true;
    }

    public static void spreadFromNode(ServerLevel level, BlockPos origin, RandomSource random) {
        if (!level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get()) || hasAnchor(level, origin)) return;
        int start = random.nextInt(6);
        int created = 0;
        for (int i = 0; i < 6 && created < 2; i++) {
            Direction direction = Direction.from3DDataValue((start + i) % 6);
            if (infect(level, origin.relative(direction), origin)) created++;
        }
        empowerNearbyCrops(level, origin, random, 3);
        exposeNearbyPlayers(level, origin);
    }

    public static void spreadFromInfectedBlock(ServerLevel level, BlockPos pos,
                                               BlockPos origin, RandomSource random) {
        if (!insideBounds(origin, pos)
                || !level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || hasAnchor(level, pos)) return;
        int start = random.nextInt(6);
        for (int i = 0; i < 6; i++) {
            Direction direction = Direction.from3DDataValue((start + i) % 6);
            if (infect(level, pos.relative(direction), origin)) break;
        }
    }

    /** Restores a bounded deterministic slice each tick; every cell is examined in a full sweep. */
    public static void healArea(ServerLevel level, BlockPos anchor, RandomSource random) {
        MutationAnchorData data = MutationAnchorData.get(level);
        data.register(anchor);
        int start = data.takeSweepStart(anchor);
        for (int i = 0; i < MutationAnchorData.SWEEP_BATCH; i++) {
            int index = (start + i) % MutationAnchorData.SWEEP_VOLUME;
            int dx = index % 17 - 8;
            int dz = (index / 17) % 17 - 8;
            int dy = index / (17 * 17) - 12;
            if (dx * dx + dz * dz > 64) continue;
            BlockPos pos = anchor.offset(dx, dy, dz);
            if (!level.getBlockState(pos).is(ModBlocks.MUTAGEN_BODEN.get())) continue;
            BlockEntity blockEntity = level.getBlockEntity(pos);
            if (!(blockEntity instanceof InfestedTerrainBlockEntity record) || !record.hasOriginalState()) continue;
            BlockState original = record.originalState();
            level.setBlock(pos, original, 3);
        }
        healNearbyPlayers(level, anchor);
    }

    public static void healNearbyPlayers(ServerLevel level, BlockPos origin) {
        for (Player player : level.getEntitiesOfClass(Player.class,
                new net.minecraft.world.phys.AABB(origin).inflate(RADIUS, MutationAnchorData.FIELD_HALF_HEIGHT, RADIUS))) {
            if (Math.abs(player.getY() - origin.getY()) > MutationAnchorData.FIELD_HALF_HEIGHT) continue;
            int infection = InfectionState.level(player);
            if (infection > 0 && player.tickCount % 40 == 0) InfectionState.cure(player, 2);
        }
    }

    private static void exposeNearbyPlayers(ServerLevel level, BlockPos origin) {
        for (Player player : level.getEntitiesOfClass(Player.class,
                new net.minecraft.world.phys.AABB(origin).inflate(RADIUS, INFECTION_HALF_HEIGHT, RADIUS))) {
            if (player.isCreative() || player.isSpectator()
                    || Math.abs(player.getY() - origin.getY()) > INFECTION_HALF_HEIGHT) continue;
            if (player.tickCount % 100 == 0 && !hasAnchor(level, player.blockPosition())) {
                InfectionState.setLevel(player, InfectionState.level(player) + 1);
            }
        }
    }

    private static void empowerNearbyCrops(ServerLevel level, BlockPos origin, RandomSource random, int attempts) {
        for (int i = 0; i < attempts; i++) {
            int dx = random.nextInt(RADIUS * 2 + 1) - RADIUS;
            int dz = random.nextInt(RADIUS * 2 + 1) - RADIUS;
            int dy = random.nextInt(INFECTION_HALF_HEIGHT * 2 + 1) - INFECTION_HALF_HEIGHT;
            if (dx * dx + dz * dz > RADIUS * RADIUS) continue;
            BlockPos pos = origin.offset(dx, dy, dz);
            BlockState state = level.getBlockState(pos);
            if (!(state.getBlock() instanceof CropBlock crop) || crop.isMaxAge(state)) continue;
            if (!(state.is(ModBlocks.FASERROHR.get()) || state.is(ModBlocks.BERNSTEINKAPPE.get())
                    || state.is(ModBlocks.ROTWURZEL.get()) || state.is(ModBlocks.FILTERMOOS.get()))) continue;
            if (random.nextFloat() < 0.20F) level.setBlock(pos, crop.getStateForAge(crop.getAge(state) + 1), 2);
        }
    }
}
""")

write("src/main/java/de/sporenwerk/block/InfestedTerrainBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.block.entity.InfestedTerrainBlockEntity;
import de.sporenwerk.infection.MutationField;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** The visible infected terrain replacement; a valid restoration record is required to spread. */
public final class InfestedTerrainBlock extends BaseEntityBlock {
    public InfestedTerrainBlock(Properties properties) { super(properties); }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new InfestedTerrainBlockEntity(pos, state);
    }

    @Override
    public RenderShape getRenderShape(BlockState state) { return RenderShape.MODEL; }

    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean moving) {
        super.onPlace(state, level, pos, oldState, moving);
        if (oldState.getBlock() != this) level.scheduleTick(pos, this, 40);
    }

    @Override
    public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        BlockEntity blockEntity = level.getBlockEntity(pos);
        if (blockEntity instanceof InfestedTerrainBlockEntity record && record.hasOriginalState()) {
            MutationField.spreadFromInfectedBlock(level, pos, record.origin(), random);
        }
        if (level.getBlockState(pos).is(this)) level.scheduleTick(pos, this, 40);
    }

    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }

    @Override
    public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        tick(state, level, pos, random);
    }
}
""")

write("src/main/java/de/sporenwerk/block/MutationNodeBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.infection.MutationField;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Player-placed infection origin. It repeatedly expands only inside its hard spatial envelope. */
public final class MutationNodeBlock extends Block {
    public MutationNodeBlock(Properties properties) { super(properties); }

    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean moving) {
        super.onPlace(state, level, pos, oldState, moving);
        if (oldState.getBlock() != this) level.scheduleTick(pos, this, 20);
    }

    @Override
    public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        MutationField.spreadFromNode(level, pos, random);
        if (level.getBlockState(pos).is(this)) level.scheduleTick(pos, this, 20);
    }

    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }

    @Override
    public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        MutationField.spreadFromNode(level, pos, random);
    }
}
""")

write("src/main/java/de/sporenwerk/block/MutationAnchorBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.infection.MutationAnchorData;
import de.sporenwerk.infection.MutationField;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Finite cure field: restores terrain blocks over a deterministic sweep and heals nearby players. */
public final class MutationAnchorBlock extends Block {
    public MutationAnchorBlock(Properties properties) { super(properties); }

    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean moving) {
        super.onPlace(state, level, pos, oldState, moving);
        if (level instanceof ServerLevel serverLevel) {
            MutationAnchorData.get(serverLevel).register(pos);
            level.scheduleTick(pos, this, 20);
        }
    }

    @Override
    public void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moving) {
        if (state.getBlock() != newState.getBlock() && level instanceof ServerLevel serverLevel) {
            MutationAnchorData.get(serverLevel).unregister(pos);
        }
        super.onRemove(state, level, pos, newState, moving);
    }

    @Override
    public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        MutationAnchorData.get(level).register(pos);
        MutationField.healArea(level, pos, random);
        if (level.getBlockState(pos).is(this)) level.scheduleTick(pos, this, 20);
    }

    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }

    @Override
    public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        MutationAnchorData.get(level).register(pos);
        MutationField.healArea(level, pos, random);
    }
}
""")

# Terrain model and texture. Keep the infection visually distinct without using a high-frequency animation.
write("src/main/resources/assets/sporenwerk/blockstates/mutagen_boden.json", """
{
  "variants": {
    "": { "model": "sporenwerk:block/mutagen_boden" }
  }
}
""")
write("src/main/resources/assets/sporenwerk/models/block/mutagen_boden.json", """
{
  "parent": "minecraft:block/cube_all",
  "textures": { "all": "sporenwerk:block/mutagen_boden" }
}
""")
write("src/main/resources/data/sporenwerk/loot_tables/blocks/mutagen_boden.json", """
{
  "type": "minecraft:block",
  "pools": []
}
""")

texture_dir = ASSETS / "textures/block"
texture_dir.mkdir(parents=True, exist_ok=True)
image = Image.new("RGBA", (16, 16), (31, 35, 34, 255))
draw = ImageDraw.Draw(image)
# Deep soil body with unmistakable mint/purple veins, cracks and spore nodes.
draw.rectangle((0, 0, 15, 15), fill=(31, 35, 34, 255))
for y in (2, 7, 12):
    draw.line((0, y, 15, y), fill=(48, 52, 47, 255), width=1)
draw.polygon([(1, 1), (5, 0), (8, 3), (6, 5), (3, 4)], fill=(107, 48, 119, 255))
draw.polygon([(9, 5), (12, 3), (15, 6), (14, 9), (11, 8)], fill=(90, 51, 119, 255))
draw.line([(1, 10), (4, 8), (7, 10), (9, 13), (13, 11), (15, 14)], fill=(74, 191, 146, 255), width=2)
draw.rectangle((4, 8, 5, 9), fill=(160, 242, 185, 255))
draw.rectangle((10, 12, 11, 13), fill=(160, 242, 185, 255))
draw.rectangle((13, 2, 14, 3), fill=(209, 125, 226, 255))
image.save(texture_dir / "mutagen_boden.png", optimize=True)

# Survival acquisition and hard-counterplay are part of the feature, not creative-only decoration.
recipes = {
    "infektionsherd": {
        "type": "minecraft:crafting_shaped", "pattern": ["MAM", "RCR", " M "],
        "key": {"M": {"item": "sporenwerk:myzelkompost"}, "A": {"item": "minecraft:amethyst_shard"},
                "R": {"item": "sporenwerk:rotwurzel"}, "C": {"item": "sporenwerk:filtermoos"}},
        "result": {"item": "sporenwerk:infektionsherd", "count": 1}
    },
    "mutationsanker": {
        "type": "minecraft:crafting_shaped", "pattern": ["FAF", "AIA", "FAF"],
        "key": {"F": {"item": "sporenwerk:filtermoos"}, "A": {"item": "minecraft:amethyst_shard"},
                "I": {"item": "minecraft:iron_ingot"}},
        "result": {"item": "sporenwerk:mutationsanker", "count": 1}
    },
    "sporenresistenter_block": {
        "type": "minecraft:crafting_shaped", "pattern": ["ISI", "SFS", "ISI"],
        "key": {"I": {"item": "minecraft:iron_ingot"}, "S": {"item": "minecraft:stone_bricks"},
                "F": {"item": "sporenwerk:filtermoos"}},
        "result": {"item": "sporenwerk:sporenresistenter_block", "count": 4}
    }
}
for name, recipe in recipes.items():
    write(f"src/main/resources/data/sporenwerk/recipes/{name}.json",
          json.dumps(recipe, ensure_ascii=False, indent=2) + "\n")

# Clear player-facing contract in both languages.
for filename, entries in [
    ("de_de.json", {
        "block.sporenwerk.mutagen_boden": "Mutagenbefallener Boden",
        "tooltip.sporenwerk.infektionsherd": "Infiziert angrenzendes Terrain. Die Ausbreitung endet nach 8 Blöcken horizontal und 3 Blöcken nach oben/unten.",
        "tooltip.sporenwerk.mutationsanker": "Stellt den ursprünglichen Blockzustand wieder her: Radius 8, 12 Blöcke nach oben und unten. Die Heilung benötigt Zeit.",
        "tooltip.sporenwerk.sporenresistenter_block": "Kann als Barriere genutzt werden. Angrenzende Blöcke werden nicht infiziert.",
        "message.sporenwerk.mutation.restored": "Mutagenblock wiederhergestellt."
    }),
    ("en_us.json", {
        "block.sporenwerk.mutagen_boden": "Mutagen-Infested Terrain",
        "tooltip.sporenwerk.infektionsherd": "Infects adjacent terrain. Spread ends after 8 horizontal blocks and 3 blocks up/down.",
        "tooltip.sporenwerk.mutationsanker": "Restores original block states: radius 8 and 12 blocks up/down. Healing takes time.",
        "tooltip.sporenwerk.sporenresistenter_block": "Can form a boundary. Adjacent blocks are not infected.",
        "message.sporenwerk.mutation.restored": "Mutagen block restored."
    })
]:
    path = RES / "assets/sporenwerk/lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

write("tools/test_reversible_infection.py", r'''
from pathlib import Path
import json, sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Reversible infection regression: " + message)
be = read("src/main/java/de/sporenwerk/block/entity/InfestedTerrainBlockEntity.java")
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
anchors = read("src/main/java/de/sporenwerk/infection/MutationAnchorData.java")
node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
anchor = read("src/main/java/de/sporenwerk/block/MutationAnchorBlock.java")
blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
registration = read("src/main/java/de/sporenwerk/registry/ModBlockEntities.java")
require("NbtUtils.writeBlockState(originalState)" in be, "exact original BlockState must be serialized")
require("NbtUtils.readBlockState" in be and "InfectionOrigin" in be, "original state and infection source must survive reload")
require("isConvertibleTerrain" in field and "Blocks.GRASS_BLOCK" in field and "Blocks.COBBLESTONE" in field,
        "spread must have a defined safe terrain whitelist")
require("insideBounds(origin, target)" in field and "HALF_HEIGHT = 3" in field, "infection must remain inside its source envelope")
require("hasAnchor(level, target)" in field and "hasImmuneBoundary(level, target)" in field,
        "healing fields and resistant block barriers must stop spread")
require("level.setBlock(pos, original, 3)" in field, "healing must restore the exact saved terrain state")
require("SWEEP_BATCH = 192" in anchors and "takeSweepStart" in field, "restoration must systematically cover the entire defined volume")
require("register(pos)" in anchor and "unregister(pos)" in anchor, "anchor positions must persist and update when placed/removed")
require("scheduleTick(pos, this, 20)" in node and "spreadFromNode" in node, "source node must start and maintain infection")
require("ModBlocks.MUTAGEN_BODEN.get()" in registration and "BLOCK_ENTITIES.register(modBus)" in read("src/main/java/de/sporenwerk/Sporenwerk.java"),
        "infested terrain block entity must be registered")
for name in ("infektionsherd", "mutationsanker", "sporenresistenter_block"):
    json.loads((root / f"src/main/resources/data/sporenwerk/recipes/{name}.json").read_text(encoding="utf-8"))
for path in ("blockstates/mutagen_boden.json", "models/block/mutagen_boden.json"):
    json.loads((root / "src/main/resources/assets/sporenwerk" / path).read_text(encoding="utf-8"))
loot = json.loads(read("src/main/resources/data/sporenwerk/loot_tables/blocks/mutagen_boden.json"))
require(loot.get("pools") == [], "internal infested terrain must not drop a fake copy of the replaced block")
print("Reversible terrain state, bounded spread, immune barriers, persistent anchors, recipes and resources passed.")
''')

write("tools/test_mutation_containment.py", r'''
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Mutation/containment regression: " + message)
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
anchors = read("src/main/java/de/sporenwerk/infection/MutationAnchorData.java")
node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
anchor = read("src/main/java/de/sporenwerk/block/MutationAnchorBlock.java")
events = read("src/main/java/de/sporenwerk/infection/InfectionEvents.java")
blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
require("RADIUS = 8" in field and "INFECTION_HALF_HEIGHT = 3" in field
        and "FIELD_HALF_HEIGHT = 12" in anchors, "infection and healing bounds must be explicit")
require("hasAnchor(level, target)" in field, "healing anchors must suppress infection inside their field")
require("hasImmuneBoundary(level, target)" in field and "SPORENRESISTENTER_BLOCK" in field,
        "immune boundary blocks must be recognized by terrain conversion")
require("spreadFromNode(level, pos, random)" in node and "empowerNearbyCrops" in field
        and "crop.getStateForAge" in field, "the mutagen node must drive real crop effects")
require("MutationField.healArea(level, pos, random)" in anchor
        and "InfectionState.cure(player, 2)" in field, "anchor must reverse terrain infection and cure players")
require("MobEffects.WEAKNESS" not in events, "mutation progression must not punish the player with weakness")
for name in ("INFEKTIONSHERD", "MUTATION_ANCHOR", "SPORENRESISTENTER_BLOCK", "MUTAGEN_BODEN"):
    require(name in blocks, name + " block registration missing")
print("Mutation perks, bounded fields, healing anchors, immune boundaries and terrain registrations passed.")
''')

# This source snapshot is the actual project that ForgeGradle builds in CI.
build = ROOT / "build.gradle"
build_text = build.read_text(encoding="utf-8")
build_text = re.sub(r"version = '[^']+'", "version = '1.5.0'", build_text, count=1)
build.write_text(build_text, encoding="utf-8")
readme = ROOT / "README.md"
readme_text = readme.read_text(encoding="utf-8")
readme_text += """

## 1.5.0 — reversible, bounded terrain infection
- Mutagen Nodes actively infect connected terrain inside a hard 8-block horizontal radius and a 7-block vertical band (3 blocks up/down from the source).
- Infested terrain records the exact original BlockState and source position in its block entity. The whitelist excludes ores, containers, machines, crops, fluids and redstone components.
- A Mutation Anchor restores saved terrain states through a persistent deterministic sweep covering radius 8 and 12 blocks above/below. Anchor coordinates and scan progress are saved per dimension.
- Spore-Resistant Blocks stop conversion across boundaries when used as a continuous barrier; the source field remains bounded even without walls.
- Mutagen Node, Mutation Anchor and Spore-Resistant Block have survival recipes. A destroyed source stops further expansion; a placed anchor can reverse an existing field.
"""
readme.write_text(readme_text, encoding="utf-8")
print("Installed reversible bounded terrain infection for Sporenwerk 1.5.0.")
