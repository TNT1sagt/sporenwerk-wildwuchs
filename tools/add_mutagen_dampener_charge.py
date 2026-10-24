#!/usr/bin/env python3
"""Add finite Resonance Dampener charge, shard recharging, charge-state art, and comparator output (1.38.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"
BLOCK_TEXTURES = ASSETS / "textures/block"


def require(condition, message):
    if not condition:
        raise SystemExit("Resonance Dampener charge generation: " + message)


block_java = """\
package de.sporenwerk.block;

import de.sporenwerk.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Finite-capacity resonance shielding. Each suppressed Kristallpirscher pulse
 * consumes one of three charges. A Resonance Shard fully recharges the device.
 *
 * The protection boundary is visualized only on player request. The block has
 * no BlockEntity or ticker, and its comparator output mirrors remaining charge.
 */
public final class MutagenResonanceDampenerBlock extends Block {
    public static final int HORIZONTAL_RADIUS = 6;
    public static final int VERTICAL_RADIUS = 2;
    public static final int MAX_CHARGE = 3;
    public static final IntegerProperty CHARGE = IntegerProperty.create("charge", 0, MAX_CHARGE);

    public MutagenResonanceDampenerBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(CHARGE, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(CHARGE);
    }

    @Override
    public boolean hasAnalogOutputSignal(BlockState state) {
        return true;
    }

    /** One charge maps to five comparator strength; full capacity outputs 15. */
    @Override
    public int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos) {
        return state.getValue(CHARGE) * 5;
    }

    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }

        ItemStack held = player.getItemInHand(hand);
        int currentCharge = state.getValue(CHARGE);
        if (held.is(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get())) {
            if (currentCharge >= MAX_CHARGE) {
                player.displayClientMessage(
                        Component.translatable("message.sporenwerk.dampener.already_full",
                                currentCharge, MAX_CHARGE).withStyle(ChatFormatting.AQUA),
                        false
                );
                return InteractionResult.CONSUME;
            }

            level.setBlock(pos, state.setValue(CHARGE, MAX_CHARGE), 3);
            if (!player.getAbilities().instabuild) {
                held.shrink(1);
            }
            player.displayClientMessage(
                    Component.translatable("message.sporenwerk.dampener.recharged", MAX_CHARGE)
                            .withStyle(ChatFormatting.AQUA),
                    false
            );
            if (level instanceof ServerLevel serverLevel) {
                serverLevel.sendParticles(ParticleTypes.END_ROD,
                        pos.getX() + 0.5D, pos.getY() + 1.0D, pos.getZ() + 0.5D,
                        18, 0.28D, 0.3D, 0.28D, 0.025D);
            }
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.BLOCKS, 0.85F, 1.35F);
            return InteractionResult.CONSUME;
        }

        player.displayClientMessage(
                Component.translatable("message.sporenwerk.dampener.status",
                        currentCharge, MAX_CHARGE, HORIZONTAL_RADIUS, VERTICAL_RADIUS,
                        getAnalogOutputSignal(state, level, pos)).withStyle(ChatFormatting.AQUA),
                false
        );
        if (level instanceof ServerLevel serverLevel) {
            revealProtectionVolume(serverLevel, pos);
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.BLOCKS, 0.55F, 1.12F);
        }
        return InteractionResult.CONSUME;
    }

    /**
     * Draws a temporary cuboid marker: 13x5x13 block positions, matching the
     * Kristallpirscher's loaded-block scan exactly. Emitted only after interaction.
     */
    private static void revealProtectionVolume(ServerLevel level, BlockPos center) {
        double x = center.getX() + 0.5D;
        double z = center.getZ() + 0.5D;
        double lowerY = center.getY() - VERTICAL_RADIUS + 0.5D;
        double upperY = center.getY() + VERTICAL_RADIUS + 0.5D;
        double middleY = center.getY() + 0.5D;
        int[] signs = {-1, 1};

        for (double y : new double[]{lowerY, upperY}) {
            for (int sx : signs) {
                for (int sz : signs) {
                    marker(level, x + sx * HORIZONTAL_RADIUS, y,
                            z + sz * HORIZONTAL_RADIUS, 3);
                }
            }
            marker(level, x, y, z - HORIZONTAL_RADIUS, 4);
            marker(level, x, y, z + HORIZONTAL_RADIUS, 4);
            marker(level, x - HORIZONTAL_RADIUS, y, z, 4);
            marker(level, x + HORIZONTAL_RADIUS, y, z, 4);
        }

        for (int sx : signs) {
            for (int sz : signs) {
                marker(level, x + sx * HORIZONTAL_RADIUS, middleY,
                        z + sz * HORIZONTAL_RADIUS, 3);
            }
        }
    }

    private static void marker(ServerLevel level, double x, double y, double z, int count) {
        level.sendParticles(ParticleTypes.END_ROD, x, y, z, count,
                0.045D, 0.045D, 0.045D, 0.005D);
    }
}
"""
(SRC / "block/MutagenResonanceDampenerBlock.java").write_text(block_java, encoding="utf-8")

# A suppressing device must have charge. Consuming one charge is the only point at
# which it plays the block feedback, and the surrounding loaded-only scan stays bounded.
entity_path = SRC / "entity/KristallpirscherEntity.java"
entity = entity_path.read_text(encoding="utf-8")
method_start = entity.find("    private boolean isResonanceDamped() {")
require(method_start >= 0, "could not find existing dampener scan")
method_end = entity.find("\n    private boolean isOnHighTierSoil()", method_start)
require(method_end > method_start, "could not find end of dampener scan")
method = """    private boolean isResonanceDamped() {
        BlockPos origin = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(
                origin.offset(-MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS,
                        -MutagenResonanceDampenerBlock.VERTICAL_RADIUS,
                        -MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS),
                origin.offset(MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS,
                        MutagenResonanceDampenerBlock.VERTICAL_RADIUS,
                        MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS))) {
            if (!level().hasChunkAt(pos)) continue;

            BlockState dampenerState = level().getBlockState(pos);
            if (!dampenerState.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())) continue;
            int charge = dampenerState.getValue(MutagenResonanceDampenerBlock.CHARGE);
            if (charge <= 0) continue;

            // The device protects exactly one pulse per charge; comparator output updates too.
            level().setBlock(pos, dampenerState.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1), 3);
            BlockPos dampenerPos = pos.immutable();
            if (level() instanceof ServerLevel serverLevel) {
                serverLevel.sendParticles(ParticleTypes.END_ROD,
                        dampenerPos.getX() + 0.5D, dampenerPos.getY() + 1.0D,
                        dampenerPos.getZ() + 0.5D, 12, 0.28D, 0.24D, 0.28D, 0.025D);
                level().playSound(null, dampenerPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                        SoundSource.BLOCKS, 0.75F, 1.25F);
            }
            return true;
        }
        return false;
    }
"""
entity = entity[:method_start] + method + entity[method_end:]
require("MutagenResonanceDampenerBlock.CHARGE" in entity,
        "entity must reference the shared charge property")
require("if (!level().hasChunkAt(pos)) continue;" in entity,
        "entity scan must not force-load chunks")
entity_path.write_text(entity, encoding="utf-8")

# Replace one default cube with four honest states. The models share the side texture,
# while the top sprite makes zero/one/two/three charges immediately distinguishable.
blockstate = {
    "variants": {
        "charge=0": {"model": "sporenwerk:block/mutagen_resonanzdaempfer"},
        "charge=1": {"model": "sporenwerk:block/mutagen_resonanzdaempfer_charge1"},
        "charge=2": {"model": "sporenwerk:block/mutagen_resonanzdaempfer_charge2"},
        "charge=3": {"model": "sporenwerk:block/mutagen_resonanzdaempfer_charge3"},
    }
}
(ASSETS / "blockstates/mutagen_resonanzdaempfer.json").write_text(
    json.dumps(blockstate, indent=2) + "\n", encoding="utf-8"
)
for charge in range(4):
    model_name = "mutagen_resonanzdaempfer" if charge == 0 else f"mutagen_resonanzdaempfer_charge{charge}"
    top_name = "mutagen_resonanzdaempfer_top" if charge == 0 else f"mutagen_resonanzdaempfer_charge{charge}"
    model = {
        "parent": "minecraft:block/cube_column",
        "textures": {
            "end": f"sporenwerk:block/{top_name}",
            "side": "sporenwerk:block/mutagen_resonanzdaempfer_side"
        }
    }
    (ASSETS / f"models/block/{model_name}.json").write_text(
        json.dumps(model, indent=2) + "\n", encoding="utf-8"
    )
(ASSETS / "models/item/mutagen_resonanzdaempfer.json").write_text(
    json.dumps({"parent": "sporenwerk:block/mutagen_resonanzdaempfer"}, indent=2) + "\n",
    encoding="utf-8"
)

# Render four high-contrast 16x16 tops. Uncharged is dark; higher charge gets progressively
# brighter cyan/ice facets, without changing the muted copper and charcoal device frame.
BLOCK_TEXTURES.mkdir(parents=True, exist_ok=True)
def top_texture(charge):
    im = Image.new("RGBA", (16, 16), (20, 34, 39, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 15, 15), fill=(32, 48, 51, 255), outline=(12, 24, 29, 255))
    d.rectangle((1, 1, 14, 14), fill=(25, 40, 44, 255), outline=(143, 105, 61, 255))
    d.rectangle((3, 3, 12, 12), fill=(12, 27, 34, 255), outline=(50, 91, 94, 255))

    centers = [
        ((10, 24, 29, 255), (27, 42, 46, 255), (54, 73, 75, 255)),
        ((17, 53, 60, 255), (28, 92, 99, 255), (78, 160, 157, 255)),
        ((20, 100, 105, 255), (37, 154, 156, 255), (89, 228, 211, 255)),
        ((29, 155, 157, 255), (55, 217, 205, 255), (225, 255, 229, 255)),
    ]
    dark, core, highlight = centers[charge]
    d.rectangle((4, 4, 11, 11), fill=dark, outline=(39, 88, 91, 255))
    d.rectangle((5, 5, 10, 10), fill=core, outline=highlight)
    d.rectangle((6, 6, 9, 9), fill=core)
    d.line([(6, 4), (9, 4)], fill=highlight, width=1)
    d.point((5, 8), fill=highlight)
    d.point((10, 8), fill=highlight)
    d.rectangle((7, 7, 8, 8), fill=highlight)
    for x, y in ((2, 2), (12, 2), (2, 12), (12, 12)):
        d.rectangle((x, y, x+1, y+1), fill=(198, 140, 72, 255))
    d.line([(1, 7), (3, 7), (4, 8), (3, 9), (1, 9)],
           fill=(66, 195 + 12*charge, 190 + 15*charge, 255), width=1)
    d.line([(14, 7), (12, 7), (11, 8), (12, 9), (14, 9)],
           fill=(66, 195 + 12*charge, 190 + 15*charge, 255), width=1)
    # Small metal service marks add readable material variation in every charge stage.
    # Their muted colors preserve the four charge-specific core palettes.
    for xy, color in (
        ((4, 2), (79, 83, 76, 255)),
        ((5, 2), (113, 86, 57, 255)),
        ((10, 2), (45, 72, 70, 255)),
        ((11, 2), (93, 72, 50, 255)),
        ((4, 13), (56, 67, 72, 255)),
        ((5, 13), (84, 107, 98, 255)),
        ((10, 13), (48, 63, 68, 255)),
        ((11, 13), (128, 97, 62, 255)),
    ):
        d.point(xy, fill=color)

    if charge >= 2:
        d.point((7, 3), fill=highlight)
        d.point((8, 3), fill=highlight)
        d.point((7, 12), fill=highlight)
        d.point((8, 12), fill=highlight)
    if charge >= 3:
        d.point((3, 7), fill=(235, 255, 242, 255))
        d.point((12, 7), fill=(235, 255, 242, 255))
        d.line([(6, 2), (9, 2)], fill=(225, 255, 229, 255), width=1)
    return im

for charge in range(4):
    name = "mutagen_resonanzdaempfer_top" if charge == 0 else f"mutagen_resonanzdaempfer_charge{charge}"
    path = BLOCK_TEXTURES / f"{name}.png"
    image = top_texture(charge)
    image.save(path, optimize=True)
    with Image.open(path) as check:
        rgba = check.convert("RGBA")
        require(rgba.size == (16, 16), f"{name} must be 16x16")
        require(all(px[3] == 255 for px in rgba.getdata()), f"{name} must be opaque")
        require(len(set(rgba.getdata())) >= 12, f"{name} must have enough pixel-art contrast")

# The existing visual contact sheet now shows each charge state next to the dampener side.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = '    ("mutagen_resonanzdaempfer_top", "Resonanzdämpfer oben"),'
addition = anchor + "\n" + "\n".join([
    '    ("mutagen_resonanzdaempfer_charge1", "Dämpfer Ladung 1/3"),',
    '    ("mutagen_resonanzdaempfer_charge2", "Dämpfer Ladung 2/3"),',
    '    ("mutagen_resonanzdaempfer_charge3", "Dämpfer Ladung 3/3"),',
])
if "mutagen_resonanzdaempfer_charge3" not in preview:
    require(anchor in preview, "dampener top preview entry missing")
    preview_path.write_text(preview.replace(anchor, addition, 1), encoding="utf-8")

# Localization includes status, refilling, and full-device no-waste feedback.
for filename, values in {
    "de_de.json": {
        "message.sporenwerk.dampener.status": "Ladung %s/%s Impulse. Schutzbereich horizontal ±%s, vertikal ±%s Blöcke. Comparator: %s/15.",
        "message.sporenwerk.dampener.recharged": "Resonanzdämpfer aufgeladen: %s/3 Impulse verfügbar.",
        "message.sporenwerk.dampener.already_full": "Resonanzdämpfer ist bereits vollständig geladen (%s/%s); der Splitter bleibt erhalten."
    },
    "en_us.json": {
        "message.sporenwerk.dampener.status": "Charge %s/%s pulses. Protection volume: ±%s horizontal, ±%s vertical blocks. Comparator: %s/15.",
        "message.sporenwerk.dampener.recharged": "Resonance Dampener recharged: %s/3 pulses available.",
        "message.sporenwerk.dampener.already_full": "Resonance Dampener is already full (%s/%s); the shard was not consumed."
    }
}.items():
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale.update(values)
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Release version and history.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.38.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Gradle version to 1.38.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.38.0 — Ladungsmanagement und Redstone-Ausgang

- **Drei echte Ladungen:** Der Dämpfer startet leer und verbraucht genau eine Ladung pro abgewehrtem Resonanzimpuls. Ein unaufgeladener Block blockiert nichts mehr versehentlich.
- **Beute wird zu Betriebsmittel:** Rechtsklick mit einem Kristallpirscher-Resonanzsplitter füllt das Gerät auf 3/3 auf. Bei voller Ladung wird kein Splitter verbraucht; in Kreativ bleibt der Gegenstand erhalten.
- **Redstone-Integration:** Der Comparator gibt 0, 5, 10 oder 15 aus und zeigt damit die verbleibenden Impuls-Abwehrungen. Die Signaländerung folgt dem gespeicherten Blockzustand.
- **Lesbare Zustände:** Vier eigene Top-Texturen kennzeichnen 0/3 bis 3/3. Die Rechtsklick-Diagnose nennt Ladung, Schutzbereich und Comparator-Wert.
- **Sicher und sparsam:** Der Block bleibt ohne BlockEntity und Tick-Schleife. Nur ein tatsächlich geladener Dämpfer kann einen Impuls abfangen; die begrenzte Chunk-sichere Suche verbraucht eine Ladung genau einmal pro blockiertem Angriff.

"""
if "## Version 1.38.0 — Ladungsmanagement und Redstone-Ausgang" not in readme:
    marker = "## Version 1.37.0 — Sichtbarer Schutzbereich des Resonanzdämpfers"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.37.0 protection-volume history")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.37.0 — sichtbarer Schutzbereich des Resonanzdämpfers.**",
    "**Aktueller Entwicklungsstand: 1.38.0 — Ladungsmanagement und Comparator für den Resonanzdämpfer.**"
).replace("## Aktueller Schwerpunkt — 1.37.0", "## Aktueller Schwerpunkt — 1.38.0")
readme_path.write_text(readme, encoding="utf-8")
print("Finite dampener charge, one-charge pulse suppression, shard refill, comparator output, charge-state block models, DE/EN text, and 1.38.0 generated.")
