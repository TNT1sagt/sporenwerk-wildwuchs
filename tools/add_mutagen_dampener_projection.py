#!/usr/bin/env python3
"""Add on-demand, visible protection-volume diagnostics to the Mutagen Resonance Dampener (1.37.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen dampener protection visualization: " + message)


# Keep the visualized dimensions and the server-side protection check tied to the same constants.
block_java = """\
package de.sporenwerk.block;

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
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * An always-on resonance device that suppresses the Kristallpirscher pulse
 * inside a bounded cuboid. Right-clicking briefly reveals that exact volume.
 *
 * The outline is emitted only on player request: there is no BlockEntity,
 * per-tick scan, or chunk-loading side effect.
 */
public final class MutagenResonanceDampenerBlock extends Block {
    public static final int HORIZONTAL_RADIUS = 6;
    public static final int VERTICAL_RADIUS = 2;

    public MutagenResonanceDampenerBlock(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }

        player.displayClientMessage(
                Component.translatable(
                        "message.sporenwerk.dampener.protection_volume",
                        HORIZONTAL_RADIUS, VERTICAL_RADIUS
                ).withStyle(ChatFormatting.AQUA),
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
     * Draws a temporary cuboid marker: 13x5x13 blocks, matching the mob's
     * loaded-block scan exactly. The 20 marker clusters are emitted only after
     * an explicit interaction, keeping ordinary gameplay free of particle loops.
     */
    private static void revealProtectionVolume(ServerLevel level, BlockPos center) {
        double x = center.getX() + 0.5D;
        double z = center.getZ() + 0.5D;
        double lowerY = center.getY() - VERTICAL_RADIUS + 0.5D;
        double upperY = center.getY() + VERTICAL_RADIUS + 0.5D;
        double middleY = center.getY() + 0.5D;
        int[] signs = {-1, 1};

        // Eight corners at the top and bottom planes.
        for (double y : new double[]{lowerY, upperY}) {
            for (int sx : signs) {
                for (int sz : signs) {
                    marker(level, x + sx * HORIZONTAL_RADIUS, y,
                            z + sz * HORIZONTAL_RADIUS, 3);
                }
            }

            // Midpoints of all four sides make the horizontal footprint readable.
            marker(level, x, y, z - HORIZONTAL_RADIUS, 4);
            marker(level, x, y, z + HORIZONTAL_RADIUS, 4);
            marker(level, x - HORIZONTAL_RADIUS, y, z, 4);
            marker(level, x + HORIZONTAL_RADIUS, y, z, 4);
        }

        // Midpoints on the four vertical edges make the ±2 block height explicit.
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
block_path = SRC / "block/MutagenResonanceDampenerBlock.java"
block_path.write_text(block_java, encoding="utf-8")

# Ensure the monster queries the exact same dimensions that the block visualizes.
entity_path = SRC / "entity/KristallpirscherEntity.java"
entity = entity_path.read_text(encoding="utf-8")
import_line = "import de.sporenwerk.block.MutagenResonanceDampenerBlock;"
if import_line not in entity:
    package_line = "package de.sporenwerk.entity;"
    require(package_line in entity, "entity package declaration missing")
    entity = entity.replace(package_line, package_line + "\n\n" + import_line, 1)
old_min = "origin.offset(-6, -2, -6)"
old_max = "origin.offset(6, 2, 6)"
new_min = ("origin.offset(-MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS, "
           "-MutagenResonanceDampenerBlock.VERTICAL_RADIUS, "
           "-MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS)")
new_max = ("origin.offset(MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS, "
           "MutagenResonanceDampenerBlock.VERTICAL_RADIUS, "
           "MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS)")
if new_min not in entity:
    require(old_min in entity, "existing protection scan minimum not found")
    entity = entity.replace(old_min, new_min, 1)
if new_max not in entity:
    require(old_max in entity, "existing protection scan maximum not found")
    entity = entity.replace(old_max, new_max, 1)
require("if (!level().hasChunkAt(pos)) continue;" in entity,
        "protection scan must continue skipping unloaded chunks")
entity_path.write_text(entity, encoding="utf-8")

# Add a translatable on-demand status line in both supported locales.
for filename, message in {
    "de_de.json": "Schutzbereich: horizontal ±%s Blöcke, vertikal ±%s Blöcke. Die Leuchtpunkte zeigen die Grenzen.",
    "en_us.json": "Protection volume: ±%s blocks horizontally, ±%s vertically. The glowing markers show the boundary."
}.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data["message.sporenwerk.dampener.protection_volume"] = message
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.37.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Gradle version to 1.37.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.37.0 — Sichtbarer Schutzbereich des Resonanzdämpfers

- **Nach Bedarf sichtbar:** Rechtsklick auf den Resonanzdämpfer zeigt eine kurze Diagnose und zeichnet die Grenzen des Schutzvolumens mit cyan-weißen Lichtpunkten nach.
- **Exakte Abmessungen:** Die Anzeige entspricht dem tatsächlichen Schutzcheck des Kristallpirschers: horizontal ±6 Blöcke, vertikal ±2 Blöcke (13×5×13 Blockpositionen).
- **Keine dauerhafte Last:** Die Markierung wird nur nach Spielerinteraktion erzeugt. Der Dämpfer benötigt weiterhin weder Block-Entity noch Tick-Schleife; der Schutzcheck überspringt ungeladene Chunks.
- **Wartbare Abstimmung:** Visualisierung und Serverprüfung verwenden dieselben Konstanten, damit spätere Reichweitenänderungen nicht auseinanderlaufen. Deutsche und englische Diagnosemeldungen sind enthalten.

"""
if "## Version 1.37.0 — Sichtbarer Schutzbereich des Resonanzdämpfers" not in readme:
    marker = "## Version 1.36.0 — Kristallpirscher-Beute und Resonanzforschung"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.36.0 release notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.36.0 — Kristallpirscher-Beute speist die Resonanzforschung.**",
    "**Aktueller Entwicklungsstand: 1.37.0 — sichtbarer Schutzbereich des Resonanzdämpfers.**"
).replace("## Aktueller Schwerpunkt — 1.36.0", "## Aktueller Schwerpunkt — 1.37.0")
readme_path.write_text(readme, encoding="utf-8")
print("Dampener protection-volume visualization, shared range constants, DE/EN status messages, and 1.37.0 generated.")
