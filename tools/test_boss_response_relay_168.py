#!/usr/bin/env python3
"""Regression tests for the 1.68.0 boss-response Relay and Resonance Focus priority."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Boss response relay 1.68: " + message)


relay = (SRC / "block/MutagenContainmentRelayBlock.java").read_text(encoding="utf-8")
for token in (
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 7)',
    "int mode = (state.getValue(MODE) + step) % 8;",
    'case 7 -> "message.sporenwerk.containment_relay.mode_boss";',
    "private static int bossResponseSignal(Level level, BlockPos center)",
    "new AABB(",
    "level.getEntitiesOfClass(MutagenkolossEntity.class, bounds, entity -> entity.isAlive())",
    "boss.getAttackState() == MutagenkolossEntity.ATTACK_BREATH",
    "signal = 15;",
    "signal = 6;",
    "signal = 10;",
    "case 7 -> bossResponseSignal(level, center);",
    "if (mode == 7)",
    "if (signal >= 12) return ChatFormatting.RED;",
    "if (signal >= 8) return ChatFormatting.YELLOW;",
    "if (signal == 6) return ChatFormatting.AQUA;",
):
    require(token in relay, "missing boss-response relay contract: " + token)
require("getChunk(" not in relay and "getChunkNow(" not in relay,
        "boss-response mode must never force-load chunks")
require("getTicker(" not in relay and "scheduleTick(" not in relay,
        "boss-response mode must not add permanent polling")

variants = json.loads((ASSETS / "blockstates/mutagen_containment_relay.json").read_text(encoding="utf-8"))["variants"]
require(len(variants) == 128, "eight modes × sixteen signals must yield 128 variants")
for mode in range(8):
    for signal in range(16):
        key = f"mode={mode},signal={signal}"
        require(variants.get(key, {}).get("model") == "sporenwerk:block/mutagen_containment_relay",
                "missing relay blockstate " + key)

entity = (SRC / "entity/MutagenkolossEntity.java").read_text(encoding="utf-8")
for token in (
    "MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());",
    "private void emitWindupParticles()",
    "public boolean interruptBreathWithResonance()",
    "this.coreExposureTicks = Math.max(this.coreExposureTicks, 60);",
):
    require(token in entity, "boss phase change must refresh relays: " + token)
require(entity.count("MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());") >= 4,
        "attack start/release, parry and core-window expiry must refresh response relays")

focus = (SRC / "item/ResonanzfokusItem.java").read_text(encoding="utf-8")
distance_sort = "targets.sort(Comparator.comparingDouble(target -> player.distanceToSqr(target)));"
priority_sort = "targets.sort(Comparator.comparingInt(target -> target instanceof MutagenkolossEntity ? 0 : 1));"
require(distance_sort in focus and priority_sort in focus,
        "distance order must be stable and interrupted Colossus must be prioritized")
use_start = focus.index("public InteractionResultHolder<ItemStack> use(")
consume_start = focus.index("private static boolean consumeResonanceShard(Player player)", use_start)
use_method = focus[use_start:consume_start]
require(use_method.index(distance_sort) < use_method.index(priority_sort)
        < use_method.index("if (!consumeResonanceShard(player))"),
        "target priority must be selected before spending the shard")
require("getChunk(" not in use_method and "getChunkNow(" not in use_method,
        "focus target selection must not force-load chunks")

for filename, expected in (
    ("de_de.json", "Kristallkoloss-Reaktion"),
    ("en_us.json", "Crystal Colossus response"),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(locale.get("message.sporenwerk.containment_relay.mode_boss") == expected,
            filename + " missing localized response mode")
for filename, expected in (
    ("de_de.json", "Kristallatem unterbrochen! Der Kern ist jetzt verwundbar."),
    ("en_us.json", "Crystal breath interrupted! The core is exposed."),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(locale.get("message.sporenwerk.resonanzfokus.colossus_interrupted") == expected,
            filename + " missing focus counterplay confirmation")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.68\.0['\"]", build) is not None,
        "artifact must be version 1.68.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.68.0" in readme and "Version 1.67.0" in readme
        and "Aktueller Entwicklungsstand: 1.68.0" in readme,
        "release notes must contain current and previous release")
print("1.68 boss response phases, 128 variants, event refresh, focus priority, chunk bounds and localization passed.")
