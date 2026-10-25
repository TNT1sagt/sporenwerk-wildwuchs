#!/usr/bin/env python3
"""Regression tests for the 1.69.0 Dampener-driven Colossus counterattack window."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Dampener core window 1.69: " + message)


entity = (SRC / "entity/MutagenkolossEntity.java").read_text(encoding="utf-8")
helper_start = entity.find("private void exposeCoreFromCountermeasure()")
require(helper_start >= 0, "shared countermeasure exposure helper is missing")
helper_end = entity.find("\n    }", helper_start)
require(helper_end > helper_start, "shared countermeasure exposure helper is malformed")
helper = entity[helper_start:helper_end + 6]
for token in (
    "if (this.level().isClientSide) return;",
    "this.coreExposureTicks = Math.max(this.coreExposureTicks, 60);",
    "this.entityData.set(CORE_EXPOSED, true);",
    "MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());",
    "ParticleTypes.END_ROD",
    "ParticleTypes.CRIT",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
):
    require(token in helper, "shared core-exposure helper missing: " + token)

focus_start = entity.find("public boolean interruptBreathWithResonance()")
focus_end = entity.find("\n    }", focus_start)
require(focus_start >= 0 and focus_end > focus_start, "Resonance Focus parry method missing")
require("this.exposeCoreFromCountermeasure();" in entity[focus_start:focus_end],
        "Focus parry must use the shared exposure effect")

intercept_start = entity.find('message.sporenwerk.colossus.breath_intercepted')
require(intercept_start >= 0, "Dampener interception feedback missing")
branch_start = entity.rfind("if (this.level() instanceof ServerLevel serverLevel", 0, intercept_start)
branch_end = entity.find("            return;", intercept_start)
require(branch_start >= 0 and branch_end > intercept_start, "could not isolate intercepted-breath branch")
branch = entity[branch_start:branch_end + len("            return;")]
for token in (
    "interceptCrystalBreath(serverLevel, origin, direction)",
    "this.exposeCoreFromCountermeasure();",
    "message.sporenwerk.colossus.breath_intercepted",
    "message.sporenwerk.colossus.core_exposed",
):
    require(token in branch, "intercepted breath must trigger the counter window: " + token)
require(branch.index("this.exposeCoreFromCountermeasure();")
        < branch.index("message.sporenwerk.colossus.core_exposed"),
        "relay/core update must happen before player confirmation")

scan_start = entity.find("private boolean interceptCrystalBreath(")
scan_end = entity.find("\n    }", scan_start)
require(scan_start >= 0 and scan_end > scan_start, "bounded Dampener interception scan missing")
scan = entity[scan_start:scan_end]
for token in (
    "for (int step = 1; step <= 16; step++)",
    "if (!level.hasChunkAt(candidate)) continue;",
    "state.getValue(MutagenResonanceDampenerBlock.CHARGE) <= 0",
    "level.setBlock(dampenerPos",
    "MutagenContainmentRelayBlock.refreshNearbyRelays(level, dampenerPos);",
    "return true;",
):
    require(token in scan, "existing finite-charge interception contract missing: " + token)
require("getChunk(" not in scan and "getChunkNow(" not in scan,
        "Dampener interception must never force-load chunks")

for filename, expected in (
    ("de_de.json", "Der Dämpfer hat den Kristallatem abgefangen! Der Kristallkern ist verwundbar."),
    ("en_us.json", "The Dampener caught the crystal breath! The crystal core is exposed."),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(locale.get("message.sporenwerk.colossus.core_exposed") == expected,
            filename + " missing localized counterattack feedback")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.69\.0['\"]", build) is not None,
        "artifact must be version 1.69.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.69.0" in readme and "Version 1.68.0" in readme
        and "Aktueller Entwicklungsstand: 1.69.0" in readme,
        "README must retain current and previous release")
print("1.69 Dampener charge, shared 60-tick core exposure, event refresh, player feedback and localization passed.")
