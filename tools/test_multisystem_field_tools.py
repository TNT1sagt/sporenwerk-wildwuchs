#!/usr/bin/env python3
"""Regression coverage for Sporenwerk 1.45.0 cross-system diagnostics and counterplay."""
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
        raise SystemExit("Multi-system field tools regression: " + message)


scanner = read("src/main/java/de/sporenwerk/item/FeldscannerItem.java")
for token in (
    "AREA_SCAN_RADIUS = 8",
    "AREA_SCAN_VERTICAL_RADIUS = 4",
    "InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand)",
    "private record AreaSurvey(",
    "private static AreaSurvey surveyArea(ServerLevel level, BlockPos origin)",
    "MutationNodeData.get(level)",
    "state.is(ModBlocks.INFEKTIONSHERD.get())",
    "state.is(ModBlocks.MUTATION_ANCHOR.get())",
    "message.sporenwerk.scanner.survey.nodes",
    "message.sporenwerk.scanner.survey.guidance.uncontained",
    "level.hasChunkAt(cursor)",
    "level.getMinBuildHeight()",
    "level.getMaxBuildHeight() - 1",
    "state.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL)",
    "state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL)",
    "ModBlocks.SPORENABWEHR.get()",
    "SporeWardBlock.POWERED",
    "MutagenResonanceDampenerBlock.CHARGE",
    "MutagenWarningSirenBlock.SIGNAL",
    "MutagenContainmentRelayBlock.MODE",
    "MutagenContainmentRelayBlock.SIGNAL",
    "MutagenFieldControlStationBlock.POWER",
    "KristallpirscherEntity.class",
    "message.sporenwerk.scanner.survey.guidance.critical",
    "message.sporenwerk.scanner.survey.loaded",
):
    require(token in scanner, "scanner contract missing: " + token)
require(scanner.count("public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand)") == 1,
        "area scanning must extend the existing air-use action, not duplicate it")
require("getChunk(" not in scanner and "getChunkNow(" not in scanner,
        "scanner must not force-load chunks")
require("scheduleTick(" not in scanner and "getTicker(" not in scanner,
        "the survey must be action-driven, not tick-driven")
require("message.sporenwerk.scanner.device.ward" in scanner
        and "message.sporenwerk.scanner.device.dampener" in scanner
        and "message.sporenwerk.scanner.device.siren" in scanner
        and "message.sporenwerk.scanner.device.relay" in scanner
        and "message.sporenwerk.scanner.device.station" in scanner,
        "targeted readings must cover every existing containment hardware type")

# Item feedback is gameplay, not just translated claims: confirm it really removes both effects.
medicine = read("src/main/java/de/sporenwerk/item/WurzelkonzentratItem.java")
require("player.removeEffect(MobEffects.POISON)" in medicine
        and "player.removeEffect(MobEffects.MOVEMENT_SLOWDOWN)" in medicine,
        "Rotwurzel concentrate must remove poison and resonance slowdown")
require("&& !player.hasEffect(MobEffects.POISON)" in medicine
        and "&& !player.hasEffect(MobEffects.MOVEMENT_SLOWDOWN)" in medicine,
        "Rotwurzel concentrate must remove poison and resonance slowdown")
require("message.sporenwerk.wurzelkonzentrat.cured_both" in medicine
        and "message.sporenwerk.wurzelkonzentrat.healed" in medicine,
        "medicine feedback must describe the outcome that actually occurred")
require("Component.literal(\"Rotwurzel-Konzentrat: 2 Herzen regeneriert.\")" not in medicine,
        "medicine must not keep hard-coded German-only feedback")

# Bloom reward, exposure, and cooldown remain intact; the cue is an extra event signal.
bloom = read("src/main/java/de/sporenwerk/infection/MutagenBloom.java")
require("SoundEvents.AMETHYST_BLOCK_CHIME" in bloom
        and "SoundSource.BLOCKS" in bloom,
        "Mutagen Bloom needs the additional audible event cue")
for token in ("COOLDOWN_TICKS = 12000L", "releaseHarvestableSpores(level, origin, random)",
              "releaseCondensedCore(level, origin, random)", "accelerateCrops(level, origin, random)",
              "exposeNearbyPlayers(level, origin)"):
    require(token in bloom, "existing bloom gameplay contract changed: " + token)

for filename in ("de_de.json", "en_us.json"):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    for key in (
        "tooltip.sporenwerk.feldscanner.3",
        "message.sporenwerk.scanner.survey.header",
        "message.sporenwerk.scanner.survey.nodes",
        "message.sporenwerk.scanner.survey.guidance.uncontained",
        "message.sporenwerk.scanner.survey.fields",
        "message.sporenwerk.scanner.survey.crops",
        "message.sporenwerk.scanner.survey.devices",
        "message.sporenwerk.scanner.survey.threats",
        "message.sporenwerk.scanner.survey.loaded",
        "message.sporenwerk.scanner.survey.guidance.critical",
        "message.sporenwerk.scanner.device.ward",
        "message.sporenwerk.scanner.device.dampener",
        "message.sporenwerk.scanner.device.siren",
        "message.sporenwerk.scanner.device.relay",
        "message.sporenwerk.scanner.device.station",
        "message.sporenwerk.wurzelkonzentrat.cured_both",
        "message.sporenwerk.wurzelkonzentrat.cured_poison",
        "message.sporenwerk.wurzelkonzentrat.cured_slowdown",
        "message.sporenwerk.wurzelkonzentrat.healed",
    ):
        require(bool(locale.get(key, "").strip()), filename + " is missing " + key)

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.45\.0['\"]", build) is not None,
        "artifact must be version 1.45.0")
readme = read("README.md")
require("Version 1.45.0" in readme and "Version 1.44.0" in readme,
        "release notes must add 1.45.0 while preserving 1.44.0 history")
require("Aktueller Entwicklungsstand: 1.45.0" in readme,
        "current README development headline is stale")
print("Multi-system scanner, bounded loaded-chunk survey, device readings, localized Rotwurzel counterplay, Mutagen Bloom cue and 1.45.0 contract passed.")
