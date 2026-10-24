#!/usr/bin/env python3
"""Regression tests for a latched Mutagen siren with player acknowledgement."""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
siren = ROOT / "src/main/java/de/sporenwerk/block/MutagenWarningSirenBlock.java"
source = siren.read_text(encoding="utf-8")
if "int latchedSignal = state.getValue(SIGNAL)" not in source:
    raise SystemExit("Mutagen siren latch regression: missing latched signal state")
if "int liveSignal = level.getBestNeighborSignal(pos)" not in source:
    raise SystemExit("Mutagen siren latch regression: missing live redstone signal")
if "if (liveSignal <= latchedSignal) return;" not in source:
    raise SystemExit("Mutagen siren latch regression: falling signal must not clear alarm")
if "InteractionResult use(" not in source or "int liveSignal = level.getBestNeighborSignal(pos)" not in source:
    raise SystemExit("Mutagen siren latch regression: missing acknowledgement interaction")
if 'Component.translatable("message.sporenwerk.warnsirene.acknowledged", liveSignal)' not in source:
    raise SystemExit("Mutagen siren latch regression: acknowledgement result must show live signal")
if "level.setBlock(pos, state.setValue(SIGNAL, liveSignal), 3)" not in source:
    raise SystemExit("Mutagen siren latch regression: acknowledgement must update latched display")
if source.count("level.playSound(") != 1:
    raise SystemExit("Mutagen siren latch regression: sound must remain a single guarded call")
print("Mutagen siren latch source contract passed.")
