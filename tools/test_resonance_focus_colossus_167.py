#!/usr/bin/env python3
"""Regression tests for the 1.67.0 Resonance Focus Colossus parry."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Resonance Focus Colossus parry 1.67: " + message)


entity = (SRC / "entity/MutagenkolossEntity.java").read_text(encoding="utf-8")
focus = (SRC / "item/ResonanzfokusItem.java").read_text(encoding="utf-8")
for token in (
    "public boolean interruptBreathWithResonance()",
    "this.getAttackState() != ATTACK_BREATH",
    "this.attackTicksLeft < 8",
    "this.attackTicksLeft = 0;",
    "this.attackCooldown = Math.max(this.attackCooldown, 90);",
    "this.entityData.set(ATTACK_STATE, ATTACK_IDLE);",
    "this.coreExposureTicks = Math.max(this.coreExposureTicks, 60);",
    "this.entityData.set(CORE_EXPOSED, true);",
    "ParticleTypes.END_ROD",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
):
    require(token in entity, "missing server-side Colossus parry contract: " + token)

for token in (
    "import de.sporenwerk.entity.MutagenkolossEntity;",
    "targets.addAll(serverLevel.getEntitiesOfClass(MutagenkolossEntity.class",
    "entity.getAttackState() == MutagenkolossEntity.ATTACK_BREATH",
    "entity.getAttackTicks() >= 8",
    "colossus.interruptBreathWithResonance()",
    "message.sporenwerk.resonanzfokus.colossus_interrupted",
    "private static boolean consumeResonanceShard(Player player)",
    "player.getCooldowns().addCooldown(this, COOLDOWN_TICKS)",
):
    require(token in focus, "missing Resonance Focus interaction: " + token)
use_start = focus.index("public InteractionResultHolder<ItemStack> use(")
consume_start = focus.index("private static boolean consumeResonanceShard(Player player)", use_start)
use_method = focus[use_start:consume_start]
require(use_method.index("if (targets.isEmpty())") < use_method.index("if (!consumeResonanceShard(player))")
        < use_method.index("colossus.interruptBreathWithResonance()"),
        "target selection and shard transaction must precede the countermeasure")
require("getChunk(" not in use_method and "getChunkNow(" not in use_method,
        "Resonance Focus may not force-load chunks")

for filename, expected_tooltip, expected_message in (
    ("de_de.json",
     "Verbraucht 1 Resonanzsplitter; trifft bis zu 3 Gegner in 5,5 Blöcken. Unterbricht den Kristallatem während der Aufladung und legt den Kern frei. Abklingzeit: 4 s.",
     "Kristallatem unterbrochen! Der Kern ist jetzt verwundbar."),
    ("en_us.json",
     "Consumes 1 Resonance Shard; reaches up to 3 threats within 5.5 blocks. Interrupts the charging crystal breath and exposes the core. Cooldown: 4 s.",
     "Crystal breath interrupted! The core is exposed."),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(locale.get("tooltip.sporenwerk.resonanzfokus.2") == expected_tooltip,
            filename + " must document the new focus option")
    require(locale.get("message.sporenwerk.resonanzfokus.colossus_interrupted") == expected_message,
            filename + " must acknowledge a successful parry")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.67\.0['\"]", build) is not None,
        "artifact must be version 1.67.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.67.0" in readme and "Version 1.66.0" in readme
        and "Aktueller Entwicklungsstand: 1.67.0" in readme,
        "release notes must retain current and previous version")
print("1.67 focus targeting, shard cost, breath interruption window, exposed-core timer, feedback, localization and version assertions passed.")
