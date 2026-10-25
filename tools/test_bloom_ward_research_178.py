#!/usr/bin/env python3
"""Regression tests for the Spore Ward's bloom-interception research branch (1.78.0)."""
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
        raise SystemExit("Bloom Ward research 1.78 regression: " + message)


bloom = read("src/main/java/de/sporenwerk/infection/MutagenBloom.java")
for token in (
    "private static void awardBloomWardResearch(Player player)",
    'new ResourceLocation("sporenwerk", "fieldwork/bloom_warded")',
    'award(research, "bloom_warded")',
    "if (isProtectedByPoweredWard(level, player.blockPosition()))",
    "awardBloomWardResearch(player);",
    "isProtectedByPoweredWard(level, player.blockPosition())",
    "if (spendDampenerCharge(level, player))",
):
    require(token in bloom, "Ward-to-research route missing " + token)
ward_start = bloom.index("if (isProtectedByPoweredWard(level, player.blockPosition()))")
ward_end = bloom.index("if (spendDampenerCharge(level, player))", ward_start)
ward_branch = bloom[ward_start:ward_end]
require("awardBloomWardResearch(player);" in ward_branch,
        "Ward reward must be awarded inside the successful protection branch")
require(ward_branch.index("awardBloomWardResearch(player);")
        < ward_branch.index("player.displayClientMessage"),
        "research must be credited as part of successful interception")
helper_start = bloom.index("private static void awardBloomWardResearch(Player player)")
helper_end = bloom.index("\n    }", helper_start)
helper = bloom[helper_start:helper_end]
require("player instanceof ServerPlayer serverPlayer" in helper
        and "server.getAdvancements().getAdvancement" in helper,
        "reward must be server-side and resolve a real advancement")
require("getChunk(" not in bloom and "getChunkNow(" not in bloom,
        "Ward research must not force-load chunks")

adv = json.loads(read("src/main/resources/data/sporenwerk/advancements/fieldwork/bloom_warded.json"))
require(adv["parent"] == "sporenwerk:first_mutagen_bloom"
        and adv["display"]["icon"]["item"] == "sporenwerk:sporenabwehr"
        and adv["criteria"]["bloom_warded"]["trigger"] == "minecraft:impossible"
        and adv["requirements"] == [["bloom_warded"]]
        and adv["rewards"]["loot"] == ["sporenwerk:quests/bloom_warded"],
        "Ward field research advancement schema is incorrect")
loot = json.loads(read("src/main/resources/data/sporenwerk/loot_tables/quests/bloom_warded.json"))
rewards = {}
for pool in loot["pools"]:
    for entry in pool["entries"]:
        item = entry["name"]
        count = entry.get("functions", [{}])[0].get("count", 1)
        rewards[item] = rewards.get(item, 0) + count
require(rewards == {"sporenwerk:feldwissen": 2, "sporenwerk:myzelkompost": 1},
        "Ward research reward must contain exactly two field knowledge and one mycelium compost")

damp_adv = json.loads(read("src/main/resources/data/sporenwerk/advancements/fieldwork/bloom_dampened.json"))
require(damp_adv["rewards"]["loot"] == ["sporenwerk:quests/bloom_dampened"]
        and 'awardBloomDampenerResearch(player);' in bloom
        and "if (spendDampenerCharge(level, player))" in bloom,
        "finite-charge Dampener research route must remain separate and intact")

for locale, keys in (
    ("de_de.json", ("Leise Wurzeln", "aktive Sporenabwehr", "Mutagenblüte")),
    ("en_us.json", ("Quiet Roots", "powered Spore Ward", "Mutagen Bloom")),
):
    lang = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    title = lang.get("advancements.sporenwerk.bloom_warded.title", "")
    desc = lang.get("advancements.sporenwerk.bloom_warded.description", "")
    require(title and desc, locale + " lacks Ward research translations")
    require(all(term.casefold() in (title + " " + desc).casefold() for term in keys),
            locale + " translations must explain the safe bloom interception")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.78\.0['\"]", build) is not None,
        "artifact must be version 1.78.0")
readme = read("README.md")
require("Version 1.78.0" in readme and "Version 1.77.0" in readme
        and "Aktueller Entwicklungsstand: 1.78.0" in readme,
        "release notes must preserve 1.77 and identify current version")
print("1.78 successful Ward interception research, server-side award, separate Dampener path, reward loot and DE/EN metadata passed.")
