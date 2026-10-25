#!/usr/bin/env python3
"""Regression checks for the animated Crystal Colossus core pulse."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Colossus visual 1.61: " + message)


model = MODEL.read_text(encoding="utf-8")
for token in (
    "private final ModelPart chestCore;",
    "private final ModelPart chestGlow;",
    "this.chestCore = body.hasChild(\"chest_core\")",
    "this.chestGlow = body.hasChild(\"core_glow\")",
    "float heartbeat = Math.max(0.0F, Mth.sin(ageInTicks * 0.19F));",
    "float afterBeat = Math.max(0.0F, Mth.sin(ageInTicks * 0.19F + 1.35F));",
    "float pulseScale = 1.0F + 0.012F + heartbeat * 0.026F + afterBeat * 0.014F;",
    "this.chestCore.xScale = pulseScale;",
    "this.chestGlow.xScale = haloScale;",
    "MutagenkolossEntity.ATTACK_BREATH",
    "MutagenkolossEntity.ATTACK_AWAKENING",
    "float spinePulse = 1.0F + heartbeat * 0.018F;",
    "this.ribCrystalLeft.zRot = -0.42F + ribSway;",
    "this.shoulderCrystalRight.zRot = 0.62F - ribSway;",
):
    require(token in model, "missing pulse/armor animation contract: " + token)

require(model.count("this.chestCore.") >= 4 and model.count("this.chestGlow.") >= 4,
        "main core and glow core must both receive animated scaling/rotation")
require("this.spines[i].xScale = spinePulse" in model
        and "this.spines[i].yScale = spinePulse" in model,
        "spines must subtly resonate with the chest pulse")
build = (ROOT / "build.gradle").read_text(encoding="utf-8")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.61\.0['\"]", build) is not None,
        "artifact must be version 1.61.0")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("Version 1.61.0" in readme and "Version 1.60.0" in readme
        and "Aktueller Entwicklungsstand: 1.61.0" in readme,
        "README must retain the new release and previous version")
print("1.61 heartbeat, attack surges, glow-layer synchronization, dorsal resonance and version tests passed.")
