#!/usr/bin/env python3
"""Regression contract for 1.52.0 Bloom/Dampener/Containment interaction."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Bloom/Dampener counterplay regression: " + message)


bloom = read("src/main/java/de/sporenwerk/infection/MutagenBloom.java")
for token in (
    "import de.sporenwerk.block.MutagenResonanceDampenerBlock;",
    "private static BlockPos nearestChargedDampener(ServerLevel level, BlockPos target)",
    "MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS",
    "MutagenResonanceDampenerBlock.VERTICAL_RADIUS",
    "if (!level.hasChunkAt(candidate)) continue;",
    "candidateState.getValue(MutagenResonanceDampenerBlock.CHARGE) <= 0",
    "private static boolean spendDampenerCharge(ServerLevel level, Player player)",
    "state.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1)",
    "MutagenContainmentRelayBlock.refreshNearbyRelays(level, dampenerPos)",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "message.sporenwerk.mutagen.bloom_dampened",
    "awardBloomDampenerResearch(player)",
    'new ResourceLocation(\"sporenwerk\", \"fieldwork/bloom_dampened\")',
    'award(research, \"bloom_dampened\")',
):
    require(token in bloom, "missing server-side gameplay contract: " + token)
require("getChunk(" not in bloom and "getChunkNow(" not in bloom,
        "Bloom counterplay must never force-load chunks")

helper_start = bloom.index("private static BlockPos nearestChargedDampener")
helper_end = bloom.index("private static void exposeNearbyPlayers", helper_start)
helper = bloom[helper_start:helper_end]
require(helper.index("if (!level.hasChunkAt(candidate)) continue;")
        < helper.index("level.getBlockState(candidate)"),
        "loaded-chunk guard must precede every candidate block read")
require("if (distanceSquared < bestDistance)" in helper,
        "the nearest charged device must be selected deterministically")
require(helper.index("level.setBlock(dampenerPos,") 
        < helper.index("MutagenContainmentRelayBlock.refreshNearbyRelays(level, dampenerPos);"),
        "relay outputs must be refreshed after charge is actually consumed")

exposure_start = bloom.index("private static void exposeNearbyPlayers")
exposure = bloom[exposure_start:]
require(exposure.index("awardBloomDiscovery(player)")
        < exposure.index("isProtectedByPoweredWard(level, player.blockPosition())")
        < exposure.index("spendDampenerCharge(level, player)")
        < exposure.index("ItemStack mask = player.getItemBySlot(EquipmentSlot.HEAD)")
        < exposure.index("InfectionState.setLevel(player, InfectionState.level(player) + 1)"),
        "discovery -> free powered ward -> finite dampener -> mask/infection order must be preserved")
require("if (spendDampenerCharge(level, player)) {\n                continue;" in exposure,
        "successful dampening must skip exposure escalation and mask durability wear")
require("accelerateCrops(level, origin, random)" in bloom
        and "releaseHarvestableSpores(level, origin, random)" in bloom,
        "existing bloom crop benefit and collectible reward must remain intact")

dampener = read("src/main/java/de/sporenwerk/block/MutagenResonanceDampenerBlock.java")
require("public static final int HORIZONTAL_RADIUS = 6;" in dampener
        and "public static final int VERTICAL_RADIUS = 2;" in dampener
        and 'IntegerProperty CHARGE = IntegerProperty.create(\"charge\", 0, MAX_CHARGE)' in dampener,
        "counterplay must reuse the actual finite dampener properties/range")

adv = json.loads(read("src/main/resources/data/sporenwerk/advancements/fieldwork/bloom_dampened.json"))
require(adv["parent"] == "sporenwerk:first_mutagen_bloom"
        and adv["criteria"]["bloom_dampened"]["trigger"] == "minecraft:impossible"
        and adv["requirements"] == [["bloom_dampened"]]
        and adv["rewards"]["loot"] == ["sporenwerk:quests/bloom_dampened"],
        "the discovery must be tied to a real one-time research award")
loot = json.loads(read("src/main/resources/data/sporenwerk/loot_tables/quests/bloom_dampened.json"))
reward_names = [entry.get("name") for pool in loot["pools"] for entry in pool["entries"]]
require(reward_names.count("sporenwerk:feldwissen") == 1
        and reward_names.count("sporenwerk:mutagene_sporen") == 1,
        "reward must remain a bounded amount of field knowledge and mutagen spores")
field_knowledge_pool = next(pool for pool in loot["pools"]
                            if any(entry.get("name") == "sporenwerk:feldwissen" for entry in pool["entries"]))
field_knowledge = next(entry for entry in field_knowledge_pool["entries"]
                       if entry.get("name") == "sporenwerk:feldwissen")
count = next((fn.get("count") for fn in field_knowledge.get("functions", [])
              if fn.get("function") == "minecraft:set_count"), None)
require(count == 2, "research reward must give exactly two field-knowledge items")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads(read("src/main/resources/assets/sporenwerk/lang/" + locale))
    for key in ("message.sporenwerk.mutagen.bloom_dampened",
                "advancements.sporenwerk.bloom_dampened.title",
                "advancements.sporenwerk.bloom_dampened.description"):
        require(data.get(key, "").strip(), locale + " is missing " + key)

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.51\.0['\"]", build) is not None,
        "artifact must be version 1.51.0")
readme = read("README.md")
require("Version 1.51.0" in readme and "Version 1.50.0" in readme,
        "release notes must preserve previous release history")
require("Aktueller Entwicklungsstand: 1.51.0" in readme,
        "README current-version headline must be updated")
print("Bloom Dampener interception, finite charge, relays, discovery reward, loaded-chunk guard and DE/EN passed.")
