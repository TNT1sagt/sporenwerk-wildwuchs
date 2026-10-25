#!/usr/bin/env python3
"""Regression tests for 1.48.0 Symbiosemyzel processing and local field defense feedback."""
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
        raise SystemExit("Symbiosis lifecycle regression: " + message)


machine = read("src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java")
branch_start = machine.find("} else if (input.is(ModItems.SYMBIOSEMYZEL.get())) {")
require(branch_start >= 0, "bioreactor must recognize Symbiosemyzel input")
branch_end = machine.find("} else progress = 0;", branch_start)
require(branch_end > branch_start, "Symbiosemyzel process branch must terminate cleanly")
branch = machine[branch_start:branch_end]
for token in (
    "new ItemStack(ModItems.MUTAGENEXTRAKT.get())",
    "canFitOutput(extract)",
    "consumePower(180)",
    "insertOutput(extract)",
    "inventory.extractItem(0, 1, false)",
    "storedPoints = Math.min(1_000_000, storedPoints + 25)",
    "skills.addCraft()",
    "setChanged()",
):
    require(token in branch, "bioreactor Symbiosemyzel process missing " + token)
require(branch.index("canFitOutput(extract)") < branch.index("consumePower(180)")
        < branch.index("inventory.extractItem(0, 1, false)"),
        "output capacity and power must be verified before consuming the input")
require(branch.index("insertOutput(extract)") < branch.index("inventory.extractItem(0, 1, false)"),
        "the input must only be consumed after output insertion succeeds")

item = read("src/main/java/de/sporenwerk/item/SymbiosemyzelItem.java")
require("tooltip.sporenwerk.symbiosemyzel.4" in item,
        "Symbiosemyzel tooltip must describe the bioreactor use")

ward = read("src/main/java/de/sporenwerk/block/SporeWardBlock.java")
for token in (
    'getLong("SporenwerkWardRepelledUntil")',
    'putLong("SporenwerkWardRepelledUntil", repelUntil)',
    "previousRepelUntil <= level.getGameTime()",
    "level.sendParticles(ParticleTypes.WARPED_SPORE",
):
    require(token in ward, "Ward repulsion feedback missing " + token)
require(ward.index("previousRepelUntil <= level.getGameTime()")
        < ward.index("level.sendParticles(ParticleTypes.WARPED_SPORE"),
        "repulsion particles must only appear on the transition into the repel grace period")

entity = read("src/main/java/de/sporenwerk/entity/DaemmerlingEntity.java")
require("private boolean isRepelledBySporeWard()" in entity,
        "Dämmerling must keep the shared ward repulsion predicate")
require("|| mob.isRepelledBySporeWard()" in entity
        and "&& !mob.isRepelledBySporeWard()" in entity,
        "both starting and continuing Dämmerling goals must honor ward repulsion")

scanner = read("src/main/java/de/sporenwerk/item/FeldscannerItem.java")
for token in (
    "Map<Long, Integer> cropKindsByPosition = new HashMap<>()",
    "List<BlockPos> clusterCandidates = new ArrayList<>()",
    "cropKindsByPosition.put(cursor.asLong(), cropKind)",
    "crop.isMaxAge(state)",
    "MutagenSymbiosis.HORIZONTAL_RADIUS",
    "MutagenSymbiosis.VERTICAL_RADIUS",
    "hasLocalSymbiosisCluster(cropKindsByPosition, candidate)",
    "Map<Long, Integer> cropKindsByPosition,",
    "BlockPos.asLong(",
    "survey.symbiosisCluster()",
    "message.sporenwerk.scanner.survey.symbiosis_found",
    "message.sporenwerk.scanner.survey.symbiosis_not_confirmed",
):
    require(token in scanner, "exact cluster diagnostics missing " + token)
helper_start = scanner.find("private static boolean hasLocalSymbiosisCluster(")
helper_end = scanner.find("private static void reportAreaSurvey(", helper_start)
require(helper_start >= 0 and helper_end > helper_start,
        "could not isolate the bounded in-memory cluster helper")
helper = scanner[helper_start:helper_end]
require("level.getBlockState(" not in helper
        and "getChunk(" not in helper and "getChunkNow(" not in helper,
        "local cluster confirmation must use scan data only, without more world reads or chunk loading")
require("level.hasChunkAt(cursor)" in scanner,
        "the original survey must still skip unloaded chunks")

for locale in ("de_de.json", "en_us.json"):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    for key in (
        "tooltip.sporenwerk.symbiosemyzel.4",
        "message.sporenwerk.scanner.survey.symbiosis_found",
        "message.sporenwerk.scanner.survey.symbiosis_not_confirmed",
    ):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.48\.0['\"]", build) is not None,
        "artifact must be version 1.48.0")
readme = read("README.md")
require("Version 1.48.0" in readme and "Version 1.47.0" in readme,
        "release notes must add 1.48.0 while preserving 1.47.0")
require("Aktueller Entwicklungsstand: 1.48.0" in readme,
        "README current development headline is stale")
print("Symbiosemyzel bioreactor transaction, one-shot ward feedback, local loaded-only cluster logic and localization passed.")
