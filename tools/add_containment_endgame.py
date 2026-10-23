#!/usr/bin/env python3
"""Make the Sterile Core an endgame reset while allowing deliberately placed post-game fields."""
from pathlib import Path
import json, re, sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")

def replace_once(path, old, new, label):
    source_path = ROOT / path
    source = source_path.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Endgame containment patch cannot find {label} in {path}")
    source_path.write_text(source.replace(old, new, 1), encoding="utf-8")

write("src/main/java/de/sporenwerk/infection/MutationNodeData.java", """
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
 * Persistent node authority for each dimension. The Sterile Core deactivates existing
 * sources; a node deliberately placed after the ending is registered active again.
 */
public final class MutationNodeData extends SavedData {
    private static final String DATA_NAME = "sporenwerk_mutation_nodes";
    private final Map<Long, Boolean> nodes = new LinkedHashMap<>();

    public static MutationNodeData get(ServerLevel level) {
        return level.getDataStorage().computeIfAbsent(
                MutationNodeData::load, MutationNodeData::new, DATA_NAME);
    }

    public static MutationNodeData load(CompoundTag tag) {
        MutationNodeData data = new MutationNodeData();
        ListTag entries = tag.getList("Nodes", Tag.TAG_COMPOUND);
        for (int i = 0; i < entries.size(); i++) {
            CompoundTag entry = entries.getCompound(i);
            data.nodes.put(entry.getLong("Pos"), entry.getBoolean("Active"));
        }
        return data;
    }

    /** Explicit player placement always authorizes this source, even after the world ending. */
    public void activate(BlockPos pos) {
        nodes.put(pos.asLong(), true);
        setDirty();
    }

    /** Upgrade-safe registration for a node that predates this saved registry. */
    public void registerIfMissing(BlockPos pos, boolean active) {
        long packed = pos.asLong();
        if (!nodes.containsKey(packed)) {
            nodes.put(packed, active);
            setDirty();
        }
    }

    public boolean contains(BlockPos pos) {
        return nodes.containsKey(pos.asLong());
    }

    public boolean isActive(BlockPos pos) {
        return nodes.getOrDefault(pos.asLong(), false);
    }

    public void unregister(BlockPos pos) {
        if (nodes.remove(pos.asLong()) != null) setDirty();
    }

    /** This is the global endgame action: every already-known source becomes inert. */
    public void deactivateAll() {
        boolean changed = false;
        for (Map.Entry<Long, Boolean> entry : nodes.entrySet()) {
            if (entry.getValue()) {
                entry.setValue(false);
                changed = true;
            }
        }
        if (changed) setDirty();
    }

    @Override
    public CompoundTag save(CompoundTag tag) {
        ListTag entries = new ListTag();
        for (Map.Entry<Long, Boolean> entry : nodes.entrySet()) {
            CompoundTag value = new CompoundTag();
            value.putLong("Pos", entry.getKey());
            value.putBoolean("Active", entry.getValue());
            entries.add(value);
        }
        tag.put("Nodes", entries);
        return tag;
    }
}
""")

# A node placed after the endgame is an explicit, controllable reintroduction.
write("src/main/java/de/sporenwerk/block/MutationNodeBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.infection.InfectionWorldData;
import de.sporenwerk.infection.MutationField;
import de.sporenwerk.infection.MutationNodeData;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Player-placed mutagen source. Every activation remains inside its finite spatial envelope. */
public final class MutationNodeBlock extends Block {
    public MutationNodeBlock(Properties properties) { super(properties); }

    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean moving) {
        super.onPlace(state, level, pos, oldState, moving);
        if (level instanceof ServerLevel serverLevel && oldState.getBlock() != this) {
            MutationNodeData.get(serverLevel).activate(pos);
            level.scheduleTick(pos, this, 20);
        }
    }

    @Override
    public void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moving) {
        if (state.getBlock() != newState.getBlock() && level instanceof ServerLevel serverLevel) {
            MutationNodeData.get(serverLevel).unregister(pos);
        }
        super.onRemove(state, level, pos, newState, moving);
    }

    private void registerLegacySource(ServerLevel level, BlockPos pos) {
        MutationNodeData data = MutationNodeData.get(level);
        data.registerIfMissing(pos, !InfectionWorldData.get(level).isSterilized());
    }

    @Override
    public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        registerLegacySource(level, pos);
        if (MutationNodeData.get(level).isActive(pos)) {
            MutationField.spreadFromNode(level, pos, random);
            if (level.getBlockState(pos).is(this)) level.scheduleTick(pos, this, 20);
        }
    }

    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }

    @Override
    public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        registerLegacySource(level, pos);
        if (MutationNodeData.get(level).isActive(pos)) MutationField.spreadFromNode(level, pos, random);
    }
}
""")

# Infected terrain restores itself when its originating source is removed or deactivated.
entity_path = SRC / "block/InfestedTerrainBlock.java"
entity_source = entity_path.read_text(encoding="utf-8")
if "import de.sporenwerk.infection.MutationNodeData;" not in entity_source:
    entity_source = entity_source.replace(
        "import de.sporenwerk.infection.MutationField;",
        "import de.sporenwerk.infection.MutationField;\nimport de.sporenwerk.infection.MutationNodeData;", 1)
if "import de.sporenwerk.infection.InfectionWorldData;" not in entity_source:
    entity_source = entity_source.replace(
        "import de.sporenwerk.infection.MutationNodeData;",
        "import de.sporenwerk.infection.MutationNodeData;\nimport de.sporenwerk.infection.InfectionWorldData;", 1)
old_tick = """        if (blockEntity instanceof InfestedTerrainBlockEntity record && record.hasOriginalState()) {
            MutationField.spreadFromInfectedBlock(level, pos, record.origin(), random);
        }
        if (level.getBlockState(pos).is(this)) level.scheduleTick(pos, this, 40);"""
new_tick = """        if (blockEntity instanceof InfestedTerrainBlockEntity record && record.hasOriginalState()) {
            BlockPos origin = record.origin();
            MutationNodeData nodeData = MutationNodeData.get(level);
            if (!nodeData.contains(origin)) {
                boolean sourceStillExists = level.getBlockState(origin).is(
                        de.sporenwerk.registry.ModBlocks.INFEKTIONSHERD.get());
                if (!sourceStillExists) {
                    level.setBlock(pos, record.originalState(), 3);
                    return;
                }
                nodeData.registerIfMissing(origin, !InfectionWorldData.get(level).isSterilized());
            }
            if (!nodeData.isActive(origin)) {
                level.setBlock(pos, record.originalState(), 3);
                return;
            }
            MutationField.spreadFromInfectedBlock(level, pos, origin, random);
        }
        if (level.getBlockState(pos).is(this)) level.scheduleTick(pos, this, 40);"""
if new_tick not in entity_source:
    if old_tick not in entity_source:
        raise SystemExit("Endgame containment patch cannot locate infected terrain tick")
    entity_source = entity_source.replace(old_tick, new_tick, 1)
entity_path.write_text(entity_source, encoding="utf-8")

# Source-aware checks apply to both the root tick and every infested neighbor.
field_path = SRC / "infection/MutationField.java"
field_source = field_path.read_text(encoding="utf-8")
field_source = field_source.replace(
    "if (!level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get()) || hasAnchor(level, origin)) return;",
    "if (!level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())\n"
    "                || !MutationNodeData.get(level).isActive(origin) || hasAnchor(level, origin)) return;")
field_source = field_source.replace(
    "if (!insideBounds(origin, pos)\n"
    "                || !level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())\n"
    "                || hasAnchor(level, pos)) return;",
    "if (!insideBounds(origin, pos)\n"
    "                || !level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())\n"
    "                || !MutationNodeData.get(level).isActive(origin)\n"
    "                || hasAnchor(level, pos)) return;")
field_path.write_text(field_source, encoding="utf-8")

# The Sterile Core is the actual endgame switch across every loaded dimension.
core_path = SRC / "item/SterileCoreItem.java"
core_source = core_path.read_text(encoding="utf-8")
if "import de.sporenwerk.infection.MutationNodeData;" not in core_source:
    core_source = core_source.replace(
        "import de.sporenwerk.infection.InfectionWorldData;",
        "import de.sporenwerk.infection.InfectionWorldData;\nimport de.sporenwerk.infection.MutationNodeData;", 1)
needle = """        data.sterilize();
        if (!player.getAbilities().instabuild) stack.shrink(1);"""
replacement = """        data.sterilize();
        // Stop every pre-existing source. New nodes placed intentionally after this point
        // register as controlled sources and remain bounded by the Mutagen Node envelope.
        for (ServerLevel dimension : serverLevel.getServer().getAllLevels()) {
            MutationNodeData.get(dimension).deactivateAll();
        }
        if (!player.getAbilities().instabuild) stack.shrink(1);"""
if replacement not in core_source:
    if needle not in core_source:
        raise SystemExit("Endgame containment patch cannot locate sterile-core action")
    core_source = core_source.replace(needle, replacement, 1)
core_path.write_text(core_source, encoding="utf-8")

# The world ending prevents ambient exposure, not deliberate controlled mutation fields.
events_path = SRC / "infection/InfectionEvents.java"
events_source = events_path.read_text(encoding="utf-8")
old_sterile_branch = """        if (world.isSterilized()) {
            if (infection > 0 && player.tickCount % 100 == 0) InfectionState.cure(player, 5);
            return;
        }"""
new_sterile_branch = """        if (world.isSterilized()) {
            // Wild exposure has ended. Do not auto-cure the player here: a deliberately
            // placed post-ending Mutagen Node can still grant mutation progression.
            return;
        }"""
if new_sterile_branch not in events_source:
    if old_sterile_branch not in events_source:
        raise SystemExit("Containment endgame patch cannot locate sterile world player tick branch")
    events_source = events_source.replace(old_sterile_branch, new_sterile_branch, 1)
events_path.write_text(events_source, encoding="utf-8")


write("tools/test_containment_endgame.py", r'''
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Containment endgame regression: " + message)
nodes = read("src/main/java/de/sporenwerk/infection/MutationNodeData.java")
block = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
terrain = read("src/main/java/de/sporenwerk/block/InfestedTerrainBlock.java")
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
core = read("src/main/java/de/sporenwerk/item/SterileCoreItem.java")
require("deactivateAll()" in nodes and 'value.putBoolean("Active"' in nodes, "source activation state must persist")
require("MutationNodeData.get(serverLevel).activate(pos)" in block, "newly placed sources must explicitly reactivate")
require("registerIfMissing(pos, !InfectionWorldData.get(level).isSterilized())" in block,
        "legacy sources must not reactivate automatically after the ending")
require("MutationNodeData.get(level).isActive(origin)" in field, "terrain spread must require an active source")
require("level.setBlock(pos, record.originalState(), 3)" in terrain,
        "terrain owned by a stopped source must restore its saved original state")
require("serverLevel.getServer().getAllLevels()" in core and "MutationNodeData.get(dimension).deactivateAll()" in core,
        "Sterile Core must deactivate all known sources in every loaded dimension")
require("InfectionWorldData.get(level).isSterilized()" in terrain,
        "unregistered pre-existing sources in a sterilized world must remain inert")
events = read("src/main/java/de/sporenwerk/infection/InfectionEvents.java")
require("Wild exposure has ended." in events and "InfectionState.cure(player, 5)" not in events,
        "global sterilization must stop ambient exposure without cancelling controlled post-ending mutation progression")
print("Endgame sterilization, delayed terrain restoration, and deliberate post-ending source activation passed.")
''')

build = ROOT / "build.gradle"
build_text = build.read_text(encoding="utf-8")
build_text = re.sub(r"version = '[^']+'", "version = '1.6.0'", build_text, count=1)
build.write_text(build_text, encoding="utf-8")
readme = ROOT / "README.md"
readme_text = readme.read_text(encoding="utf-8")
readme_text += """

## 1.6.0 — endgame sterilization and controlled reintroduction
- The Sterile Core deactivates all registered Mutagen Nodes in every loaded dimension and keeps that source state across restarts.
- Infested terrain whose source is stopped restores its recorded original BlockState as its scheduled tick runs; containers and other non-whitelisted blocks are never converted.
- A Mutagen Node deliberately placed after the ending is explicitly activated again, but remains bound to its own 8-block horizontal / 3-block vertical envelope. This makes post-game controlled test plots possible without reopening ambient spread.
- Legacy, unregistered nodes do not reactivate by themselves after the world has been sterilized.
"""
readme.write_text(readme_text, encoding="utf-8")
print("Installed Sporenwerk 1.6.0 endgame sterilization and controlled mutagen reintroduction.")
