#!/usr/bin/env python3
"""Regression tests for the Crystal Colossus overcharged-core counterplay window (1.65.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Colossus overcharge 1.65: " + message)


entity = (SRC / "entity/MutagenkolossEntity.java").read_text(encoding="utf-8")
model = (SRC / "client/MutagenkolossModel.java").read_text(encoding="utf-8")
for token in (
    "private static final EntityDataAccessor<Boolean> CORE_EXPOSED",
    "private static final int CORE_EXPOSURE_DURATION = 90;",
    "this.entityData.define(CORE_EXPOSED, false);",
    "public boolean isCoreExposed()",
    "this.coreExposureTicks = CORE_EXPOSURE_DURATION;",
    "this.entityData.set(CORE_EXPOSED, true);",
    "if (this.isCoreExposed() && source.getEntity() != null) amount *= 1.30F;",
    "if (this.coreExposureTicks == 0)",
    "this.entityData.set(CORE_EXPOSED, false);",
    "this.coreExposureTicks = 0;",
    "this.getBoundingBox().inflate(24.0D)",
    "message.sporenwerk.colossus.core_exposed",
    "exposureLevel.sendParticles(ParticleTypes.END_ROD",
):
    require(token in entity, "missing synced core exposure/damage contract: " + token)
require("if (this.level().isClientSide) return;" in entity,
        "server-authoritative boss update guard is required")
require("entity.isCoreExposed() ? 0.085F : 0.0F" in model,
        "chest core must visibly flare during exposure")
require("(entity.isCoreExposed() ? 0.055F : 0.0F)" in model,
        "dorsal crystals must resonate during exposure")

for filename, expected in (
    ("de_de.json", "Der Kristallkern ist überladen! Jetzt verursacht ihr 30 % mehr Schaden."),
    ("en_us.json", "The crystal core is overloaded! Strike now for 30% more damage."),
):
    locale = json.loads((ASSETS / "lang" / filename).read_text(encoding="utf-8"))
    require(locale.get("message.sporenwerk.colossus.core_exposed") == expected,
            filename + " needs the actionable overcharge warning")

build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.65\.0['\"]", build) is not None,
        "artifact must be version 1.65.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.65.0" in readme and "Version 1.64.0" in readme
        and "Aktueller Entwicklungsstand: 1.65.0" in readme,
        "release notes must retain current and previous release")
print("1.65 overcharge timing, synchronized state, 30% damage bonus, recovery, visible model flare and DE/EN warnings passed.")
