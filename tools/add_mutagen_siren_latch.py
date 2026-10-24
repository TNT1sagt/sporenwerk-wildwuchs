#!/usr/bin/env python3
"""Latch the highest Mutagen siren severity until a player acknowledges it."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


JAVA = """\
package de.sporenwerk.block;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Redstone siren that remembers the strongest observed signal until acknowledged.
 * A lower input cannot silently hide a previously observed critical alarm.
 */
public final class MutagenWarningSirenBlock extends Block {
    public static final IntegerProperty SIGNAL = IntegerProperty.create("signal", 0, 15);

    public MutagenWarningSirenBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(SIGNAL, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(SIGNAL);
    }

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos,
                                Block neighborBlock, BlockPos neighborPos, boolean moving) {
        if (level.isClientSide) return;
        int latchedSignal = state.getValue(SIGNAL);
        int liveSignal = level.getBestNeighborSignal(pos);

        // Latch upward only. Signal decay is intentionally ignored until player acknowledgement.
        if (liveSignal <= latchedSignal) return;

        int previousBand = riskBand(latchedSignal);
        int nextBand = riskBand(liveSignal);
        level.setBlock(pos, state.setValue(SIGNAL, liveSignal), 3);

        // Rising-severity tones are one-shot; same-tier increases and falling input are silent.
        if (nextBand > previousBand) {
            float pitch = switch (nextBand) {
                case 3 -> 0.55F;
                case 2 -> 0.82F;
                default -> 1.18F;
            };
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BELL.value(),
                    SoundSource.BLOCKS, 0.9F, pitch);
        }
    }

    /**
     * Right-click acknowledges the incident peak and synchronizes the display to
     * the current live signal. An active input remains visible; an inactive input clears.
     */
    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;

        int liveSignal = level.getBestNeighborSignal(pos);
        if (state.getValue(SIGNAL) != liveSignal) {
            level.setBlock(pos, state.setValue(SIGNAL, liveSignal), 3);
        }
        player.displayClientMessage(
                Component.translatable("message.sporenwerk.warnsirene.acknowledged", liveSignal)
                        .withStyle(ChatFormatting.YELLOW),
                false
        );
        return InteractionResult.CONSUME;
    }

    /** 0 = clear, 1 = warning (1–4), 2 = elevated (5–10), 3 = critical (11–15). */
    public static int riskBand(int signal) {
        if (signal >= 11) return 3;
        if (signal >= 5) return 2;
        return signal > 0 ? 1 : 0;
    }
}
"""
siren_path = SRC / "block/MutagenWarningSirenBlock.java"
siren_path.write_text(JAVA, encoding="utf-8")

# Add acknowledgement instructions to DE/EN without erasing prior language entries.
for filename, message in {
    "de_de.json": "Sirene quittiert: aktuelles Redstone-Signal %s/15; gespeicherter Spitzenwert zurückgesetzt.",
    "en_us.json": "Siren acknowledged: current redstone signal %s/15; stored peak reset."
}.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data["message.sporenwerk.warnsirene.acknowledged"] = message
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Advance the artifact version.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.31.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.31.0")
build_path.write_text(build, encoding="utf-8")

# Preserve all release history and document the operational contract.
readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.31.0 — Quittierbare, gespeicherte Sirenenalarme

- **Spitzenwert bleibt sichtbar:** Die Sirene speichert den höchsten empfangenen Redstone-Wert. Fällt das Signal von kritisch auf einen niedrigeren Wert oder verschwindet es ganz, verschwindet der Alarm nicht unbemerkt.
- **Spieler-Quittierung:** Rechtsklick quittiert den gespeicherten Spitzenwert und synchronisiert die Anzeige mit der aktuell anliegenden Redstone-Stärke. Liegt weiterhin Gefahr an, bleibt sie sichtbar; liegt kein Signal an, wird die Sirene zurückgesetzt.
- **Keine zusätzliche Audio-Last:** Glockentöne werden nur beim Wechsel in eine höhere Gefahrenstufe abgespielt. Das Fallen des Signals und normale Updates bleiben stumm.
- **Qualitätssicherung:** Regressionstests prüfen Latch-Verhalten, manuelle Quittierung, alle 16 Blockstates, Texturen, Übersetzungen und den vollständigen Forge-Build samt Server-Smoke-Test.

"""
if "## Version 1.31.0 — Quittierbare, gespeicherte Sirenenalarme" not in readme:
    marker = "## Version 1.30.0 — Eskalierende Mutagen-Warnsirene"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.30.0 release notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.30.0 — gestufte Mutagen-Warnsirene mit Alarm-Eskalation.**",
    "**Aktueller Entwicklungsstand: 1.31.0 — gespeicherte Mutagen-Alarme mit Spieler-Quittierung.**"
).replace("## Aktueller Schwerpunkt — 1.30.0", "## Aktueller Schwerpunkt — 1.31.0")
readme_path.write_text(readme, encoding="utf-8")
print("Mutagen siren peak latch, player acknowledgement, localization, and version 1.31.0 generated.")
