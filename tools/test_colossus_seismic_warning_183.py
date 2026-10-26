#!/usr/bin/env python3
"""Regression for Crystal Colossus seismic warnings and jump-counterable impact (1.83.0)."""
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def require(ok, description):
    if not ok:
        raise SystemExit("Seismic warning 1.83 regression: " + description)


entity = read("src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java")
model = read("src/main/java/de/sporenwerk/client/MutagenkolossModel.java")
windup_at = entity.index("private void emitWindupParticles()")
release_at = entity.index("private void releaseAttack(int state)", windup_at)
stomp_at = entity.index("private void performStomp(float damage, double radius)", release_at)
breath_at = entity.index("private void performCrystalBreath()", stomp_at)
windup = entity[windup_at:release_at]
stomp = entity[stomp_at:breath_at]
for token in (
    "if (state == ATTACK_STOMP || state == ATTACK_AWAKENING)",
    "this.attackTicksLeft > 0 && this.attackTicksLeft % 12 == 0",
    "state == ATTACK_AWAKENING ? 7.2D : 5.8D",
    "emitGroundRing(serverLevel, radius, false)",
    "this.attackTicksLeft == 12",
    "SoundEvents.AMETHYST_BLOCK_CHIME",
    "private void emitGroundRing(ServerLevel serverLevel, double radius, boolean impact)",
    "final int samples = impact ? 32 : 24",
    "ParticleTypes.REVERSE_PORTAL",
    "ParticleTypes.END_ROD",
):
    require(token in windup, "danger zone warning must be visible and correctly timed: " + token)
for token in (
    "emitGroundRing(serverLevel, radius * 0.54D, true);",
    "emitGroundRing(serverLevel, radius, true);",
    "double dx = victim.getX() - this.getX();",
    "double dz = victim.getZ() - this.getZ();",
    "dx * dx + dz * dz > radius * radius",
    "if (!victim.onGround()) continue;",
    "victim.hurt(this.damageSources().mobAttack(this), damage);",
    "victim.knockback(1.65D, this.getX() - victim.getX(), this.getZ() - victim.getZ());",
    "damage > 15.0F",
):
    require(token in stomp, "shockwave hit test or original combat must remain: " + token)

hit_start = stomp.index("for (LivingEntity victim : victims)")
hit_end = stomp.index("victim.hurt(", hit_start)
require(stomp.index("dx * dx + dz * dz > radius * radius", hit_start) < hit_end
        and stomp.index("if (!victim.onGround()) continue;", hit_start) < hit_end,
        "circle and jump evasion checks must run before damage and knockback")
require(stomp.index("AABB area = this.getBoundingBox().inflate(radius, 2.6D, radius);") >= 0,
        "retain the cheap broad-phase entity area query")
require("performStomp(empowered ? 18.0F : 14.0F, empowered ? 7.2D : 5.8D)" in entity,
        "original normal and awakening damage/radius must remain intact")
require("private void performCrystalBreath()" in entity
        and "this.attackCooldown = 128;" in entity,
        "do not alter the existing breath attack and cooldown")
for forbidden in ("setBlock(", "destroyBlock(", "getChunk(", "getChunkNow("):
    require(forbidden not in windup + stomp,
            "visual shockwave must not mutate blocks or force-load chunks: " + forbidden)

require("animateWeightedLeg(this.frontLeft" in model and "this.lowerJaw.xRot" in model
        and "this.crystalCrownLeft.zRot" in model,
        "retain 1.80 crown, 1.81 jaw and 1.82 weighted gait")
for texture in ("mutagenkoloss.png", "mutagenkoloss_glow.png"):
    path = ASSETS / "textures/entity" / texture
    require(path.is_file(), "missing original Colossus atlas: " + texture)
    with Image.open(path) as im:
        require(im.size == (256, 256), "Atlas must retain 256px UV layout: " + texture)

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.83\.0['\"]", build),
        "Gradle artifact must be version 1.83.0")
readme = read("README.md")
require("Aktueller Entwicklungsstand: 1.83.0" in readme
        and "Version 1.83.0" in readme and "Version 1.82.0" in readme,
        "version metadata and release history must remain coherent")
print("1.83 stomp warning rings, distinct awakening radius, jump counterplay, circular area, impact effects, no terrain edits and release contracts passed.")
