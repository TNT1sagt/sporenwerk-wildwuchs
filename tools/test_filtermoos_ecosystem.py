#!/usr/bin/env python3
"""Regression coverage for the 1.49.0 living Filtermoos ecosystem and player protection."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Filtermoos ecosystem regression: " + message)


helper = read("src/main/java/de/sporenwerk/infection/FilterMossSymbiosis.java")
for token in (
    "HORIZONTAL_RADIUS = 3",
    "VERTICAL_RADIUS = 1",
    "MIN_MUTAGEN_LEVEL = 2",
    "level.hasChunkAt(origin)",
    "level.hasChunkAt(probe)",
    "ModBlocks.FILTERMOOS.get()",
    "AbstractSporeCropBlock.MUTAGEN_LEVEL",
    "crop.isMaxAge(state)",
    "boolean protects(Level level, BlockPos origin)",
):
    require(token in helper, "shared protection predicate missing " + token)
require("getChunk(" not in helper and "getChunkNow(" not in helper,
        "Filtermoos must not force-load chunks")
require("scheduleTick(" not in helper and "getTicker(" not in helper,
        "Filtermoos protection must not use a block ticker")

entity = read("src/main/java/de/sporenwerk/entity/DaemmerlingEntity.java")
require("FilterMossSymbiosis.protects(mob.level(), cropPos)" in entity,
        "Dämmerling crop targeting must respect the living Filtermoos halo")
require("if (!mob.level().hasChunkAt(pos)) continue;" in entity,
        "existing collector deterrence scan must skip unloaded chunks")
require("mob.level().getMaxLocalRawBrightness(cropPos) >= 7" in entity
        and "ModBlocks.FELDSAMMLER.get()" in entity,
        "Filtermoos should supplement, not replace, light and machine protection")

events = read("src/main/java/de/sporenwerk/infection/InfectionEvents.java")
require("fieldExposurePulse && FilterMossSymbiosis.protects(level, player.blockPosition())" in events,
        "the same Filtermoos predicate must intercept real field exposure pulses")
require("message.sporenwerk.filtermoos.field_buffered" in events
        and "ParticleTypes.WARPED_SPORE" in events,
        "player protection needs visible localized feedback")
require("serverPlayer.serverLevel().sendParticles" in events,
        "buffer particles must be sent from the authoritative server level")
require('new ResourceLocation("sporenwerk", "filtermoos_bastion")' in events
        and 'award(milestone, "filtermoos_intercepts_exposure")' in events,
        "the milestone must be awarded by actual exposure interception")
protected_branch = events.find("if (fieldExposurePulse && FilterMossSymbiosis.protects")
mask_branch = events.find("} else if (fieldExposurePulse) {", protected_branch)
require(protected_branch >= 0 and mask_branch > protected_branch,
        "Filtermoos protection must be checked before mask wear or infection escalation")
require("mask.hurtAndBreak(1" in events and "InfectionState.setLevel(player, infection + 1)" in events,
        "unprotected field exposure and normal mask durability behavior must remain intact")

scanner = read("src/main/java/de/sporenwerk/item/FeldscannerItem.java")
for token in (
    "int protectiveFilterMoss)",
    "int protectiveFilterMoss = 0",
    "state.is(ModBlocks.FILTERMOOS.get())",
    "state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) >= 2",
    "filterCrop.isMaxAge(state)",
    "protectiveFilterMoss++",
    "survey.protectiveFilterMoss()",
    "message.sporenwerk.scanner.survey.filtermoos",
):
    require(token in scanner, "scanner Filtermoos diagnostic missing " + token)
require("level.hasChunkAt(cursor)" in scanner
        and "getChunk(" not in scanner and "getChunkNow(" not in scanner,
        "survey must stay loaded-chunk-only")

adv = json.loads(read("src/main/resources/data/sporenwerk/advancements/filtermoos_bastion.json"))
require(adv["parent"] == "sporenwerk:mutagen_laboratory"
        and adv["criteria"]["filtermoos_intercepts_exposure"]["trigger"] == "minecraft:impossible"
        and adv["requirements"] == [["filtermoos_intercepts_exposure"]],
        "research milestone must use the real, programmatically awarded exposure-interception criterion")
require(adv["rewards"]["loot"] == ["sporenwerk:quests/filtermoos_bastion"],
        "milestone must award its dedicated one-time loot table")
loot = json.loads(read("src/main/resources/data/sporenwerk/loot_tables/quests/filtermoos_bastion.json"))
require(any(entry.get("name") == "sporenwerk:sporenfiltereinsatz"
            for pool in loot["pools"] for entry in pool["entries"]),
        "living-filter milestone should provide replacement filter cartridges")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    for key in (
        "message.sporenwerk.filtermoos.field_buffered",
        "message.sporenwerk.scanner.survey.filtermoos",
        "advancements.sporenwerk.filtermoos_bastion.title",
        "advancements.sporenwerk.filtermoos_bastion.description",
    ):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.49\.0['\"]", build) is not None,
        "artifact must be version 1.49.0")
readme = read("README.md")
require("Version 1.49.0" in readme and "Version 1.48.0" in readme,
        "release notes must add 1.49.0 while preserving 1.48.0")
require("Aktueller Entwicklungsstand: 1.49.0" in readme,
        "README current development headline is stale")
print("Mature Filtermoos aura, Dämmerling crop deterrence, exposure interception, one-time research reward, scanner count and DE/EN text passed.")
