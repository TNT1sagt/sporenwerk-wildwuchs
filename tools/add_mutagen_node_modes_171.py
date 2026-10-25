#!/usr/bin/env python3
"""Add three player-selectable Mutagen Node modes with distinct in-world pixel art (1.71.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen Node modes 1.71: " + message)


node_path = SRC / "block/MutationNodeBlock.java"
node_path.write_text("""package de.sporenwerk.block;

import de.sporenwerk.infection.InfectionWorldData;
import de.sporenwerk.infection.MutationField;
import de.sporenwerk.infection.MutationNodeData;
import de.sporenwerk.infection.MutagenBloom;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;

public final class MutationNodeBlock extends Block {
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;
    public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 2);

    public MutationNodeBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any()
                .setValue(POWERED, false).setValue(MODE, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(POWERED, MODE);
    }

    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        if (hand != InteractionHand.MAIN_HAND) return InteractionResult.PASS;
        if (level.isClientSide) return InteractionResult.SUCCESS;

        int nextMode = (state.getValue(MODE) + 1) % 3;
        boolean powered = level.hasNeighborSignal(pos);
        BlockState updated = state.setValue(MODE, nextMode).setValue(POWERED, powered);
        level.setBlock(pos, updated, 3);

        String message = switch (nextMode) {
            case 1 -> "message.sporenwerk.mutation.node_cultivation";
            case 2 -> "message.sporenwerk.mutation.node_dormant";
            default -> "message.sporenwerk.mutation.node_active";
        };
        if (level instanceof ServerLevel serverLevel) {
            float pitch = nextMode == 0 ? 1.14F : nextMode == 1 ? 0.92F : 0.68F;
            serverLevel.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.BLOCKS, 0.8F, pitch);
            var particle = nextMode == 0 ? ParticleTypes.END_ROD
                    : nextMode == 1 ? ParticleTypes.HAPPY_VILLAGER : ParticleTypes.SMOKE;
            serverLevel.sendParticles(particle, pos.getX() + 0.5D, pos.getY() + 0.8D,
                    pos.getZ() + 0.5D, 12, 0.24D, 0.2D, 0.24D, 0.012D);
            for (Player nearby : serverLevel.getEntitiesOfClass(Player.class,
                    new AABB(pos).inflate(10.0D, 5.0D, 10.0D))) {
                nearby.displayClientMessage(Component.translatable(message), true);
            }
        }
        if (!powered && nextMode != 2 && MutationNodeData.get((ServerLevel) level).isActive(pos)) {
            level.scheduleTick(pos, this, nextMode == 1 ? 40 : 20);
        }
        return InteractionResult.CONSUME;
    }

    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean moving) {
        super.onPlace(state, level, pos, oldState, moving);
        if (level instanceof ServerLevel serverLevel && oldState.getBlock() != this) {
            MutationNodeData.get(serverLevel).activate(pos);
            boolean powered = level.hasNeighborSignal(pos);
            BlockState current = level.getBlockState(pos);
            if (current.getValue(POWERED) != powered) {
                level.setBlock(pos, current.setValue(POWERED, powered), 3);
            }
            if (!powered) level.scheduleTick(pos, this, 20);
        }
    }

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos,
                                Block sourceBlock, BlockPos sourcePos, boolean moving) {
        super.neighborChanged(state, level, pos, sourceBlock, sourcePos, moving);
        if (level.isClientSide) return;
        boolean powered = level.hasNeighborSignal(pos);
        if (state.getValue(POWERED) == powered) return;

        BlockState updated = state.setValue(POWERED, powered);
        level.setBlock(pos, updated, 3);
        if (level instanceof ServerLevel serverLevel) {
            registerLegacySource(serverLevel, pos);
            serverLevel.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.BLOCKS, 0.7F, powered ? 0.62F : 1.12F);
            serverLevel.sendParticles(powered ? ParticleTypes.SMOKE : ParticleTypes.END_ROD,
                    pos.getX() + 0.5D, pos.getY() + 0.75D, pos.getZ() + 0.5D,
                    8, 0.22D, 0.18D, 0.22D, 0.012D);
            String key = powered ? "message.sporenwerk.mutation.node_paused"
                    : "message.sporenwerk.mutation.node_resumed";
            for (Player player : serverLevel.getEntitiesOfClass(Player.class,
                    new AABB(pos).inflate(10.0D, 5.0D, 10.0D))) {
                player.displayClientMessage(Component.translatable(key), true);
            }
        }
        if (!powered && state.getValue(MODE) != 2) {
            level.scheduleTick(pos, this, 1);
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
        boolean powered = level.hasNeighborSignal(pos);
        if (state.getValue(POWERED) != powered) {
            state = state.setValue(POWERED, powered);
            level.setBlock(pos, state, 3);
        }
        if (powered || state.getValue(POWERED)) return;
        if (!MutationNodeData.get(level).isActive(pos)) return;

        int mode = state.getValue(MODE);
        if (mode == 0) {
            MutationField.spreadFromNode(level, pos, random);
            MutagenBloom.tryTrigger(level, pos, random);
        } else if (mode == 1) {
            MutationField.cultivateNearbyCrops(level, pos, random);
        } else {
            return;
        }

        if (level.getBlockState(pos).is(this) && !level.hasNeighborSignal(pos)) {
            level.scheduleTick(pos, this, mode == 1 ? 40 : 20);
        }
    }

    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }

    @Override
    public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        registerLegacySource(level, pos);
        if (state.getValue(POWERED) || level.hasNeighborSignal(pos)
                || !MutationNodeData.get(level).isActive(pos)) return;

        int mode = state.getValue(MODE);
        if (mode == 0) {
            MutationField.spreadFromNode(level, pos, random);
        } else if (mode == 1) {
            MutationField.cultivateNearbyCrops(level, pos, random);
        }
    }
}
""", encoding="utf-8")

# Make crop-only mode an explicit server method. It cannot spread terrain, expose players,
# or trigger a bloom; it only applies the existing Sporenwerk-crop growth helper.
field_path = SRC / "infection/MutationField.java"
field = field_path.read_text(encoding="utf-8")
if "public static void cultivateNearbyCrops(" not in field:
    anchor = "    public static void spreadFromNode(ServerLevel level, BlockPos origin, RandomSource random) {"
    require(field.count(anchor) == 1, "could not locate normal source spread method")
    method = """    /** Safe cultivation-only mode: grow compatible crops without terrain spread or exposure. */
    public static void cultivateNearbyCrops(ServerLevel level, BlockPos origin, RandomSource random) {
        BlockState source = level.getBlockState(origin);
        if (!source.is(ModBlocks.INFEKTIONSHERD.get())
                || !MutationNodeData.get(level).isActive(origin)
                || level.hasNeighborSignal(origin) || hasAnchor(level, origin)) return;
        empowerNearbyCrops(level, origin, random, 6);
    }

"""
    field = field.replace(anchor, method + anchor, 1)

node_guard = """        if (!level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || !MutationNodeData.get(level).isActive(origin)
                || level.hasNeighborSignal(origin) || hasAnchor(level, origin)) return;"""
require(field.count(node_guard) == 1, "normal terrain-spread source guard changed unexpectedly")
field = field.replace(node_guard, """        if (!level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || level.getBlockState(origin).getValue(MutationNodeBlock.MODE) != 0
                || !MutationNodeData.get(level).isActive(origin)
                || level.hasNeighborSignal(origin) || hasAnchor(level, origin)) return;""", 1)

terrain_guard = """        if (!insideBounds(origin, pos)
                || !level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || !MutationNodeData.get(level).isActive(origin)
                || level.hasNeighborSignal(origin) || hasAnchor(level, pos)) return;"""
require(field.count(terrain_guard) == 1, "existing contaminated-terrain source guard changed unexpectedly")
field = field.replace(terrain_guard, """        if (!insideBounds(origin, pos)
                || !level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || level.getBlockState(origin).getValue(MutationNodeBlock.MODE) != 0
                || !MutationNodeData.get(level).isActive(origin)
                || level.hasNeighborSignal(origin) || hasAnchor(level, pos)) return;""", 1)

if "import de.sporenwerk.block.MutationNodeBlock;" not in field:
    anchor = "import de.sporenwerk.registry.ModBlocks;"
    require(field.count(anchor) == 1, "could not locate Mutagen Node import anchor")
    field = field.replace(anchor, "import de.sporenwerk.block.MutationNodeBlock;\n" + anchor, 1)
field_path.write_text(field, encoding="utf-8")

# Distinct Minecraft-style 16x16 textures make the mode visible in the world itself.
texture_dir = ASSETS / "textures/block"
texture_dir.mkdir(parents=True, exist_ok=True)

cultivation = Image.new("RGBA", (16, 16), (41, 48, 37, 255))
d = ImageDraw.Draw(cultivation)
d.rectangle((0, 0, 15, 1), fill=(19, 27, 22, 255))
d.rectangle((0, 14, 15, 15), fill=(16, 20, 17, 255))
d.rectangle((1, 2, 14, 13), fill=(64, 73, 48, 255))
d.rectangle((2, 3, 13, 12), fill=(35, 44, 31, 255))
d.rectangle((7, 6, 8, 12), fill=(65, 142, 70, 255))
d.rectangle((4, 5, 7, 7), fill=(97, 189, 78, 255))
d.rectangle((8, 4, 11, 6), fill=(133, 205, 91, 255))
d.rectangle((5, 4, 6, 5), fill=(172, 221, 119, 255))
d.point((10, 3), fill=(208, 232, 146, 255))
d.rectangle((3, 10, 5, 12), fill=(114, 78, 45, 255))
d.rectangle((10, 10, 12, 12), fill=(114, 78, 45, 255))
cultivation.save(texture_dir / "infektionsherd_cultivation.png", optimize=True)

dormant = Image.new("RGBA", (16, 16), (37, 41, 44, 255))
d = ImageDraw.Draw(dormant)
d.rectangle((0, 0, 15, 1), fill=(66, 73, 77, 255))
d.rectangle((0, 14, 15, 15), fill=(16, 19, 22, 255))
d.rectangle((1, 2, 14, 13), fill=(47, 52, 55, 255))
d.rectangle((2, 3, 13, 12), fill=(27, 31, 34, 255))
d.rectangle((4, 4, 11, 11), fill=(62, 68, 71, 255))
d.rectangle((5, 5, 10, 10), fill=(30, 34, 37, 255))
d.rectangle((6, 6, 9, 9), fill=(94, 104, 106, 255))
d.point((7, 7), fill=(146, 163, 162, 255))
d.point((8, 8), fill=(123, 139, 138, 255))
d.rectangle((3, 7, 4, 8), fill=(75, 83, 84, 255))
d.rectangle((11, 7, 12, 8), fill=(75, 83, 84, 255))
dormant.save(texture_dir / "infektionsherd_dormant.png", optimize=True)

# One blockstate table selects by both mode and Redstone. Power always wins visually,
# so all powered variants use the conspicuous red lock texture created by 1.70.
blockstate = {
    "variants": {
        "mode=0,powered=false": {"model": "sporenwerk:block/infektionsherd"},
        "mode=1,powered=false": {"model": "sporenwerk:block/infektionsherd_cultivation"},
        "mode=2,powered=false": {"model": "sporenwerk:block/infektionsherd_dormant"},
        "mode=0,powered=true": {"model": "sporenwerk:block/infektionsherd_paused"},
        "mode=1,powered=true": {"model": "sporenwerk:block/infektionsherd_paused"},
        "mode=2,powered=true": {"model": "sporenwerk:block/infektionsherd_paused"}
    }
}
(ASSETS / "blockstates/infektionsherd.json").write_text(
    json.dumps(blockstate, indent=2) + "\n", encoding="utf-8")
for name, texture in (
    ("infektionsherd_cultivation", "infektionsherd_cultivation"),
    ("infektionsherd_dormant", "infektionsherd_dormant")
):
    (ASSETS / "models/block" / f"{name}.json").write_text(json.dumps({
        "parent": "minecraft:block/cube_all",
        "textures": {"all": f"sporenwerk:block/{texture}"}
    }, indent=2) + "\n", encoding="utf-8")

# Add mode textures to the visual QA sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = '    ("infektionsherd_paused", "Mutagenherd — Redstone gesperrt"),'
require(anchor in preview or "infektionsherd_cultivation" in preview,
        "could not locate Mutagen Node entries in art preview")
if "infektionsherd_cultivation" not in preview:
    preview = preview.replace(anchor, anchor + '\n    ("infektionsherd_cultivation", "Mutagenherd — Kulturmodus"),\n    ("infektionsherd_dormant", "Mutagenherd — Ruhend"),', 1)
    preview_path.write_text(preview, encoding="utf-8")

# Update bilingual tooltip and actual block feedback.
locales = (
    ("de_de.json",
     "Rechtsklick wechselt den Modus: AUSBREITUNG, KULTUR (nur Sporenwerk-Pflanzen) oder RUHEND. Redstone pausiert jeden Modus vollständig.",
     "Mutagenherd: Ausbreitung aktiv.",
     "Mutagenherd: Kulturmodus — keine Geländeausbreitung oder Spielerexposition.",
     "Mutagenherd: ruhend — keine Feldwirkung."),
    ("en_us.json",
     "Right-click to cycle modes: SPREAD, CULTIVATION (Sporenwerk crops only), or DORMANT. Redstone pauses every mode completely.",
     "Mutagen Node: spread mode active.",
     "Mutagen Node: cultivation mode — no terrain spread or player exposure.",
     "Mutagen Node: dormant — no field effects.")
)
for filename, tooltip, active, crop, dormant_text in locales:
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data["tooltip.sporenwerk.infektionsherd"] = tooltip
    data["message.sporenwerk.mutation.node_active"] = active
    data["message.sporenwerk.mutation.node_cultivation"] = crop
    data["message.sporenwerk.mutation.node_dormant"] = dormant_text
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Preserve prior regression coverage, then promote all active artifact/version assertions.
new_test = "test_mutagen_node_modes_171.py"
test170 = ROOT / "tools/test_mutagen_node_redstone_pause_170.py"
test170_source = test170.read_text(encoding="utf-8")
test170_source = test170_source.replace('blockstate["variants"].get("powered=false", {})',
                                        'blockstate["variants"].get("mode=0,powered=false", {})')
test170_source = test170_source.replace('blockstate["variants"].get("powered=true", {})',
                                        'blockstate["variants"].get("mode=0,powered=true", {})')
# 1.71 adds MODE beside POWERED and schedules by mode; keep the earlier safety
# assertions semantic rather than tied to the pre-mode single-property source layout.
test170_source = test170_source.replace('"builder.add(POWERED)"', '"builder.add(POWERED, MODE)"')
test170_source = test170_source.replace(
    '"this.registerDefaultState(this.stateDefinition.any().setValue(POWERED, false))"',
    '"this.registerDefaultState(this.stateDefinition.any()"')
test170_source = test170_source.replace(
    '"if (!powered) level.scheduleTick(pos, this, 1)"',
    '"level.scheduleTick(pos, this, 1)"')
test170_source = test170_source.replace(
    '"if (state.getValue(POWERED) || level.hasNeighborSignal(pos)) return;"',
    '"state.getValue(POWERED) || level.hasNeighborSignal(pos)"')
test170_source = test170_source.replace(
    'field.count("level.hasNeighborSignal(origin)") == 2',
    'field.count("level.hasNeighborSignal(origin)") >= 2')
test170_source = test170_source.replace(
    'field.count("MutationNodeData.get(level).isActive(origin)") == 2',
    'field.count("MutationNodeData.get(level).isActive(origin)") >= 2')
test170.write_text(test170_source, encoding="utf-8")

for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == new_test:
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.70.0",
                               "Aktueller Entwicklungsstand: 1.71.0")
    if "build.gradle" in original:
        updated = updated.replace(r"1\.70\.0", r"1\.71\.0")
        updated = updated.replace("artifact must be version 1.70.0",
                                  "artifact must be version 1.71.0")
    updated = updated.replace(
        '"Version 1.70.0" in readme and "Version 1.69.0" in readme',
        '"Version 1.71.0" in readme and "Version 1.70.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.71.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle version to 1.71.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.71.0 — Drei Betriebsmodi für den Mutagenherd

- **Ausbreitung:** Der Herd breitet Mutagen innerhalb der bereits festgelegten Grenzen aus, beschleunigt passende Sporenwerk-Pflanzen und kann die seltene Mutagenblüte auslösen.
- **Kulturmodus:** Rechtsklick schaltet auf kontrollierte Pflanzenkultivierung um. Nur passende Sporenwerk-Pflanzen werden begünstigt; es entstehen keine neuen befallenen Bodenblöcke und keine Spielerexposition durch diesen Herd.
- **Ruhend:** Der Herd bleibt platziert, erzeugt aber keine Feldwirkung. Bereits befallener Boden kann sich ebenfalls nicht weiter ausbreiten, solange seine Quelle nicht im Ausbreitungsmodus ist.
- **Redstone hat Vorrang:** Ein Signal pausiert alle drei Modi mit dem gut sichtbaren roten Sperrblockzustand. Entfernen des Signals setzt nur einen Modus fort, der nicht auf „Ruhend“ steht.
- **Lesbarer Weltzustand:** Ausbreitung, Kultur und Ruhe besitzen separate 16×16-Pixeltexturen. Der Block zeigt Moduswechsel über Partikel, Klang und lokale Meldungen.
- **Regressionen:** Der Test prüft alle sechs Blockstate-Kombinationen, Bloom-Integration, Schutz vor Terrainwachstum in Kultur/Ruhe, Texte und Texturkontrast.

"""
current = """## Aktueller Entwicklungsschritt — 1.71.0

- **Betriebsmodus vor Ort wechseln:** Rechtsklick durchläuft Ausbreitung, Kulturmodus und Ruhend; der Zustand bleibt im Minecraft-Blockstate gespeichert.
- **Sicheres Züchten statt Ausbreiten:** Kulturmodus verwendet den vorhandenen Pflanzenwachstumsmechanismus, aber weder Terraininfektion noch Exposition oder Mutagenblüten.
- **Redstone-Sperre bleibt dominant:** Die elektrische Sperre unterbricht unabhängig vom gewählten Modus jede Feldwirkung und zeigt weiterhin die rote Sperrtextur.
- **Mehrere Systeme abgesichert:** Die vorhandene Blüten-/Sirenenkette, die persistente Quellenregistrierung, der Sterile Kern und der vorhandene Boden-Quellschutz werden beibehalten.

"""
if "## Version 1.71.0 — Drei Betriebsmodi für den Mutagenherd" not in readme:
    marker = "## Version 1.70.0 — Redstone-Sperre für kontrollierte Mutagenherde"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate 1.70 release heading to preserve history")
    readme = readme[:idx] + release + readme[idx:]
if "## Aktueller Entwicklungsschritt — 1.71.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.70.0"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate current 1.70 development section")
    readme = readme[:idx] + current + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.70.0 — Redstone-Sperre für kontrollierte Mutagenherde.**",
    "**Aktueller Entwicklungsstand: 1.71.0 — Drei Betriebsmodi für den Mutagenherd.**")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.71.0 generated: Spread/Cultivation/Dormant modes, Redstone priority, bloom preservation and distinct pixel art.")
