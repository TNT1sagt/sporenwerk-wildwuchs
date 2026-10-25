#!/usr/bin/env python3
"""Add Redstone pause/resume and a clearly visible safe state to Mutagen Nodes (1.70.0)."""
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
        raise SystemExit("Mutagen Node Redstone pause 1.70: " + message)


def patch(path, old, new, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return source
    count = source.count(old)
    require(count == 1, f"{label}: expected one source anchor, got {count}")
    source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")
    return source


# Preserve persistent source activation and sterilization rules while giving the node a
# synchronised powered state. No new ticker is added: pause stops its scheduled ticks,
# and neighborChanged schedules one short wake-up when power is removed.
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
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.AABB;

public final class MutationNodeBlock extends Block {
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;

    public MutationNodeBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(POWERED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(POWERED);
    }

    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean moving) {
        super.onPlace(state, level, pos, oldState, moving);
        if (level instanceof ServerLevel serverLevel && oldState.getBlock() != this) {
            // A deliberately placed node is an intentional controlled seed, even after the ending.
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
        if (!powered) level.scheduleTick(pos, this, 1);
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

        if (MutationNodeData.get(level).isActive(pos)) {
            MutationField.spreadFromNode(level, pos, random);
            MutagenBloom.tryTrigger(level, pos, random);
            if (level.getBlockState(pos).is(this) && !level.hasNeighborSignal(pos)) {
                level.scheduleTick(pos, this, 20);
            }
        }
    }

    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }

    @Override
    public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        registerLegacySource(level, pos);
        if (state.getValue(POWERED) || level.hasNeighborSignal(pos)) return;
        if (MutationNodeData.get(level).isActive(pos)) {
            MutationField.spreadFromNode(level, pos, random);
        }
    }
}
""", encoding="utf-8")

# The signal must also suspend terrain blocks already growing from this source.
field_path = SRC / "infection/MutationField.java"
field = field_path.read_text(encoding="utf-8")
if "level.hasNeighborSignal(origin)" not in field:
    node_anchor = """        if (!level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || !MutationNodeData.get(level).isActive(origin) || hasAnchor(level, origin)) return;"""
    require(field.count(node_anchor) == 1, "could not locate active Mutation Node spread guard")
    field = field.replace(node_anchor, """        if (!level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || !MutationNodeData.get(level).isActive(origin)
                || level.hasNeighborSignal(origin) || hasAnchor(level, origin)) return;""", 1)
    terrain_anchor = """        if (!insideBounds(origin, pos)
                || !level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || !MutationNodeData.get(level).isActive(origin)
                || hasAnchor(level, pos)) return;"""
    require(field.count(terrain_anchor) == 1, "could not locate source-bound terrain spread guard")
    field = field.replace(terrain_anchor, """        if (!insideBounds(origin, pos)
                || !level.getBlockState(origin).is(ModBlocks.INFEKTIONSHERD.get())
                || !MutationNodeData.get(level).isActive(origin)
                || level.hasNeighborSignal(origin) || hasAnchor(level, pos)) return;""", 1)
    field_path.write_text(field, encoding="utf-8")
require(field.count("level.hasNeighborSignal(origin)") == 2,
        "both node expansion and existing infected terrain must respect the Redstone pause")

# A different block texture, rather than a scanner icon, communicates the paused state in-world.
texture_dir = ASSETS / "textures/block"
texture_dir.mkdir(parents=True, exist_ok=True)
paused = Image.new("RGBA", (16, 16), (27, 32, 36, 255))
d = ImageDraw.Draw(paused)
d.rectangle((0, 0, 15, 1), fill=(61, 72, 78, 255))
d.rectangle((0, 14, 15, 15), fill=(12, 16, 19, 255))
d.rectangle((1, 2, 14, 13), fill=(42, 48, 53, 255))
d.rectangle((2, 3, 13, 12), fill=(19, 23, 27, 255))
d.rectangle((3, 4, 12, 11), fill=(54, 61, 65, 255))
d.rectangle((4, 5, 11, 10), fill=(17, 20, 24, 255))
# The red interruption bar and heavy dark clamps read as a deliberate shut-off state.
d.rectangle((1, 7, 14, 9), fill=(137, 34, 42, 255))
d.rectangle((2, 6, 4, 10), fill=(91, 24, 31, 255))
d.rectangle((11, 6, 13, 10), fill=(91, 24, 31, 255))
d.rectangle((6, 4, 9, 11), fill=(21, 25, 29, 255))
d.rectangle((7, 5, 8, 10), fill=(223, 59, 61, 255))
d.rectangle((5, 7, 10, 9), fill=(244, 99, 73, 255))
d.point((7, 6), fill=(255, 190, 108, 255))
d.point((8, 10), fill=(150, 35, 45, 255))
paused_path = texture_dir / "infektionsherd_paused.png"
paused.save(paused_path, optimize=True)

with Image.open(paused_path) as source:
    image = source.convert("RGBA")
require(image.size == (16, 16), "paused node texture must be 16x16")
require(all(pixel[3] == 255 for pixel in image.getdata()), "paused node texture must be fully opaque")
base_path = texture_dir / "infektionsherd.png"
require(base_path.is_file(), "baseline Mutagen Node texture is missing")
with Image.open(base_path) as source:
    base = source.convert("RGBA")
difference = sum(1 for a, b in zip(image.getdata(), base.getdata()) if a[:3] != b[:3]) / 256.0
require(difference >= 0.55, f"paused texture is not different enough from active node ({difference:.0%})")
red_signature = sum(1 for r, g, b, a in image.getdata() if r > 120 and r > g * 1.55 and r > b * 1.25)
require(red_signature >= 8, "paused state needs an unmistakable red shut-off signature")

# The powered blockstate points to its own model while the inactive state preserves the old model.
blockstate_path = ASSETS / "blockstates/infektionsherd.json"
blockstate_path.write_text(json.dumps({
    "variants": {
        "powered=false": {"model": "sporenwerk:block/infektionsherd"},
        "powered=true": {"model": "sporenwerk:block/infektionsherd_paused"}
    }
}, indent=2) + "\n", encoding="utf-8")
(ASSETS / "models/block/infektionsherd_paused.json").write_text(json.dumps({
    "parent": "minecraft:block/cube_all",
    "textures": {"all": "sporenwerk:block/infektionsherd_paused"}
}, indent=2) + "\n", encoding="utf-8")

# Keep the pixel-art audit focused on actual world textures.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
preview_anchor = '    ("infektionsherd_top", "Mutagenherd"),'
preview_add = preview_anchor + '\n    ("infektionsherd_paused", "Mutagenherd — Redstone gesperrt"),'
if "infektionsherd_paused" not in preview:
    require(preview_anchor in preview, "could not find Mutagen Node in art preview list")
    preview_path.write_text(preview.replace(preview_anchor, preview_add, 1), encoding="utf-8")

# Update both languages. These messages are emitted by the block on an actual signal transition.
for filename, tooltip, paused_message, resumed_message in (
    ("de_de.json",
     "Beschleunigt Sporenwerk-Pflanzen im Radius von 8 Blöcken und ±3 Höhe. Redstone-Signal: pausiert die Ausbreitung vollständig; Signal entfernen setzt sie fort.",
     "Mutagenherd pausiert: keine neue Mutagenausbreitung.",
     "Mutagenherd wieder aktiv: kontrollierte Ausbreitung fortgesetzt."),
    ("en_us.json",
     "Accelerates Sporenwerk crops within an 8-block radius and ±3 height. Redstone signal: fully pauses spread; remove the signal to resume.",
     "Mutagen Node paused: no further Mutagen spread.",
     "Mutagen Node resumed: controlled spread continues."),
):
    lang_path = ASSETS / "lang" / filename
    locale = json.loads(lang_path.read_text(encoding="utf-8"))
    locale["tooltip.sporenwerk.infektionsherd"] = tooltip
    locale["message.sporenwerk.mutation.node_paused"] = paused_message
    locale["message.sporenwerk.mutation.node_resumed"] = resumed_message
    lang_path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# This milestone ships as 1.70.0 and updates all prior active-version contracts without
# rewriting the historical release descriptions.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.70.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.70.0")
build_path.write_text(build, encoding="utf-8")

new_test = "test_mutagen_node_redstone_pause_170.py"
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == new_test:
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.69.0",
                               "Aktueller Entwicklungsstand: 1.70.0")
    if "build.gradle" in original:
        updated = updated.replace(r"1\.69\.0", r"1\.70\.0")
        updated = updated.replace("artifact must be version 1.69.0",
                                  "artifact must be version 1.70.0")
    updated = updated.replace(
        '"Version 1.69.0" in readme and "Version 1.68.0" in readme',
        '"Version 1.70.0" in readme and "Version 1.69.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.70.0 — Redstone-Sperre für kontrollierte Mutagenherde

- **Feld auf Knopfdruck anhalten:** Ein Redstone-Signal pausiert den Mutagenherd, ohne ihn zu zerstören oder seinen persistenten Aktivierungsstatus zu verlieren. Wird das Signal entfernt, wird die Ausbreitung automatisch fortgesetzt.
- **Bereits befallener Boden stoppt mit:** Mutagenboden prüft weiterhin seine ursprüngliche Quelle. Solange diese Quelle mit Redstone gesperrt ist, entstehen keine neuen befallenen Nachbarblöcke.
- **Im Spiel deutlich sichtbar:** Der gesperrte Herd erhält ein eigenes dunkelmetallisches Pixelmuster mit rotem Sperrbalken, statt dass man einen Scanner zum Erkennen benötigt.
- **Rückmeldung und Grenzen:** Signalwechsel erzeugen Ton, Partikel und eine lokale Nachricht. Die 8-Block-Horizontalreichweite, die vertikale Begrenzung, Heilanker, immune Baublöcke und die Endgame-Sterilisierung bleiben erhalten.
- **Qualitätssicherung:** Regressionen prüfen beide Spread-Pfade, gespeicherten Herdstatus, Blockstate-Modellzuordnung, 16×16-Texturkontrast und deutsche/englische Meldungen.

"""
current = """## Aktueller Entwicklungsschritt — 1.70.0

- **Redstone-Kontrolle:** Der Mutagenherd lässt sich elektrisch anhalten und wieder starten. Ein pausierter Herd bleibt als solcher platziert und wird nicht als sterilisiert oder gelöscht missverstanden.
- **Saubere Stoppgrenze:** Auch bereits befallener Mutagenboden darf nicht weiterwachsen, solange die zugehörige Quelle Redstone-Strom erhält.
- **Minecraft-lesbarer Zustand:** Aktiv und pausiert besitzen unterschiedliche Blockmodelle/Texturen. Ton, Partikel und nahe Spieler erhalten beim Umschalten Feedback.
- **Kein neuer globaler Tick-Loop:** Die vorhandene begrenzte Quellen-Ticklogik wird weiterverwendet; beim Wiederanschalten wird genau ein neuer Tick geplant.

"""
if "## Version 1.70.0 — Redstone-Sperre für kontrollierte Mutagenherde" not in readme:
    marker = "## Version 1.69.0 — Dämpfer-Parade öffnet den Kristallkern"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate 1.69 release notes to preserve history")
    readme = readme[:idx] + release + readme[idx:]
if "## Aktueller Entwicklungsschritt — 1.70.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.69.0"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate current 1.69 development section")
    readme = readme[:idx] + current + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.69.0 — Dämpfer-Parade und verwundbarer Kristallkern.**",
    "**Aktueller Entwicklungsstand: 1.70.0 — Redstone-Sperre für kontrollierte Mutagenherde.**")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.70.0 generated: Redstone-paused Mutagen Nodes, source-bound terrain stop, distinct paused texture, DE/EN feedback and regressions.")
