#!/usr/bin/env python3
"""Regression coverage for Sporenwerk 1.51.0 resonance counterplay."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Resonance counterplay regression: " + message)


stalker = read("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")
for token in (
    "import de.sporenwerk.infection.FilterMossSymbiosis;",
    "resonanceWindup <= 0",
    "resonanceCooldown > 0",
    "public boolean disruptResonance()",
    "resonanceWindup = 0;",
    "resonanceCooldown = RESONANCE_COOLDOWN_TICKS;",
    "FilterMossSymbiosis.protects(level(), player.blockPosition())",
    "ParticleTypes.CRIT",
    "ParticleTypes.END_ROD",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
):
    require(token in stalker, "Crystal Stalker interruption/protection contract missing " + token)
pulse_start = stalker.index("// Recheck proximity and equipment at release")
pulse_end = stalker.index("resonanceCooldown = RESONANCE_COOLDOWN_TICKS;", pulse_start)
release = stalker[pulse_start:pulse_end]
require("FilterMossSymbiosis.protects(level(), player.blockPosition())" in release,
        "Filtermoos must intercept the released pulse")
nearby_start = stalker.index("private List<Player> nearbyUnprotectedPlayers()")
nearby_end = stalker.index("private static boolean isWearingSporeMask", nearby_start)
nearby = stalker[nearby_start:nearby_end]
require("FilterMossSymbiosis.protects" not in nearby,
        "expensive Filtermoos probes must not run in the Stalker windup tick loop")
require("getChunk(" not in stalker and "getChunkNow(" not in stalker,
        "resonance defense must not force-load chunks")

focus = read("src/main/java/de/sporenwerk/item/ResonanzfokusItem.java")
for token in (
    "((KristallpirscherEntity) target).disruptResonance()",
    "interrupted ? 9.0F : 5.0F",
    "interrupted ? 100 : 40",
    "interrupted ? 1.25D : 0.9D",
    "MobEffects.DAMAGE_RESISTANCE",
    "awardCounterpulseResearch(serverPlayer)",
    "new ResourceLocation(\"sporenwerk\", \"monsters/resonance_parry\")",
    "message.sporenwerk.resonanzfokus.counterpulse",
    "tooltip.sporenwerk.resonanzfokus.3",
):
    require(token in focus, "Resonanzfokus timed-parry behavior missing " + token)
require(focus.index("boolean interrupted = stalker && ((KristallpirscherEntity) target).disruptResonance();")
        < focus.index("target.hurt(player.damageSources().magic(), damage)"),
        "parry state must be detected before damage and bonuses are computed")
require("player.getCooldowns().addCooldown(this, COOLDOWN_TICKS)" in focus,
        "the normal focus cooldown must remain in force after a successful parry")
require("consumeResonanceShard(player)" in focus,
        "a successful focus pulse must retain its single-shard resource cost")

adv = json.loads(read("src/main/resources/data/sporenwerk/advancements/monsters/resonance_parry.json"))
require(adv["parent"] == "sporenwerk:monsters/kristallpirscher_resonanzsplitter"
        and adv["criteria"]["counterpulse_interrupted"]["trigger"] == "minecraft:impossible"
        and adv["requirements"] == [["counterpulse_interrupted"]],
        "parry research must be awarded only by the real interruption event")
require(adv["rewards"]["loot"] == ["sporenwerk:quests/resonance_parry"],
        "parry research must grant its unique one-time reward")
loot = json.loads(read("src/main/resources/data/sporenwerk/loot_tables/quests/resonance_parry.json"))
names = [entry.get("name") for pool in loot["pools"] for entry in pool["entries"]]
require(names.count("sporenwerk:mutagenextrakt") == 1
        and names.count("sporenwerk:sporenfiltereinsatz") == 1,
        "reward must contain Mutagen Extract and the filter cartridge")
filter_pool = next(pool for pool in loot["pools"]
                   if any(e.get("name") == "sporenwerk:sporenfiltereinsatz" for e in pool["entries"]))
entry = next(e for e in filter_pool["entries"] if e.get("name") == "sporenwerk:sporenfiltereinsatz")
count = next((f.get("count") for f in entry.get("functions", [])
              if f.get("function") == "minecraft:set_count"), None)
require(count == 2, "parry reward should provide exactly two replacement cartridges")

for filename in ("de_de.json", "en_us.json"):
    lang = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    for key in (
        "tooltip.sporenwerk.resonanzfokus.3",
        "message.sporenwerk.resonanzfokus.counterpulse",
        "advancements.sporenwerk.resonance_parry.title",
        "advancements.sporenwerk.resonance_parry.description",
    ):
        require(bool(lang.get(key, "").strip()), filename + " missing " + key)

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.51\.0['\"]", build) is not None,
        "artifact must be version 1.51.0")
readme = read("README.md")
require("Version 1.51.0" in readme and "Version 1.50.0" in readme,
        "release notes must preserve 1.50.0 history")
require("Aktueller Entwicklungsstand: 1.51.0" in readme,
        "current README release headline is stale")
print("Resonance windup parry, Filtermoos pulse buffer, one-time research reward, DE/EN strings and release contract passed.")
