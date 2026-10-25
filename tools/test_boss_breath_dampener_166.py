#!/usr/bin/env python3
"""Regression tests for Colossus breath interception and containment-margin colors (1.66.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.66 counterplay: " + message)


entity = (SRC / "entity/MutagenkolossEntity.java").read_text(encoding="utf-8")
for token in (
    "import de.sporenwerk.block.MutagenContainmentRelayBlock;",
    "import de.sporenwerk.block.MutagenResonanceDampenerBlock;",
    "import de.sporenwerk.registry.ModBlocks;",
    "private boolean interceptCrystalBreath(ServerLevel level, Vec3 origin, Vec3 direction)",
    "interceptCrystalBreath(serverLevel, origin, direction)",
    "for (int step = 1; step <= 16; step++)",
    "center.offset(-1, -1, -1), center.offset(1, 1, 1)",
    "if (!level.hasChunkAt(candidate)) continue;",
    "state.getValue(MutagenResonanceDampenerBlock.CHARGE) <= 0",
    "state.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1)",
    "MutagenContainmentRelayBlock.refreshNearbyRelays(level, dampenerPos)",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "message.sporenwerk.colossus.breath_intercepted",
):
    require(token in entity, "missing breath-interception behavior: " + token)
helper_start = entity.index("private boolean interceptCrystalBreath")
helper_end = entity.index("@Override\n    public void addAdditionalSaveData", helper_start)
helper = entity[helper_start:helper_end]
require(helper.index("if (!level.hasChunkAt(candidate)) continue;")
        < helper.index("level.getBlockState(candidate)"),
        "loaded-chunk guard must precede every candidate block read")
require(helper.index("level.setBlock(dampenerPos,")
        < helper.index("MutagenContainmentRelayBlock.refreshNearbyRelays(level, dampenerPos);"),
        "the redstone network must refresh after charge consumption")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "boss counterplay must never force-load chunks")

relay = (SRC / "block/MutagenContainmentRelayBlock.java").read_text(encoding="utf-8")
start = relay.index("private static ChatFormatting colorFor(int mode, int signal)")
end = relay.index("private static String modeKey(int mode)", start)
colors = relay[start:end]
require("if (mode == 6)" in colors, "mode 6 needs its own inverse color scale")
require("if (signal <= 3) return ChatFormatting.RED;" in colors,
        "low safety margin must display red")
require("if (signal <= 7) return ChatFormatting.YELLOW;" in colors,
        "medium safety margin must display yellow")
require("return ChatFormatting.GREEN;" in colors,
        "high safety margin must display green")
require("if ((mode == 3 || mode == 4 || mode == 5) && signal >= 11)" in colors,
        "high-threat modes must retain their warning colors")

for filename, expected in (
    ("de_de.json", "Resonanzdämpfer hat den Kristallatem abgefangen! Eine Ladung wurde verbraucht."),
    ("en_us.json", "Resonance Dampener intercepted the crystal breath! One charge was consumed."),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(locale.get("message.sporenwerk.colossus.breath_intercepted") == expected,
            filename + " needs an explicit interception acknowledgement")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.66\.0['\"]", build) is not None,
        "artifact must be version 1.66.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.66.0" in readme and "Version 1.65.0" in readme
        and "Aktueller Entwicklungsstand: 1.66.0" in readme,
        "release notes must retain the current and previous release")
print("1.66 Dampener interception, finite charge, relay refresh, chunk safety, inverse colors, translations and version checks passed.")
