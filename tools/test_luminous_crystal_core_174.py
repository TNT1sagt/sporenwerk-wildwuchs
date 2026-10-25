#!/usr/bin/env python3
"""Regression tests for the Luminous Crystal Core relic and boss counterplay (1.74.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit("Luminous Crystal Core 1.74 regression: " + message)


items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
item = read("src/main/java/de/sporenwerk/item/LeuchtenderKristallkernItem.java")
boss = read("src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java")
for token in (
    "LEUCHTENDER_KRISTALLKERN",
    'ITEMS.register("leuchtender_kristallkern"',
    "new LeuchtenderKristallkernItem",
):
    require(token in items, "registry missing " + token)
require("ModItems.LEUCHTENDER_KRISTALLKERN.get()" in creative,
        "Luminous Crystal Core must be available in the creative tab")

for token in (
    "PULSE_RADIUS = 8.0D",
    "MAX_TARGETS = 4",
    "COOLDOWN_TICKS = 200",
    "getEntitiesOfClass(MutagenkolossEntity.class",
    "getEntitiesOfClass(KristallpirscherEntity.class",
    "getEntitiesOfClass(DaemmerlingEntity.class",
    "player.hasLineOfSight(target)",
    "player.distanceToSqr(target) > PULSE_RADIUS * PULSE_RADIUS",
    "targets.sort(Comparator.comparingDouble",
    "boss.disruptWithResonancePulse()",
    "player.damageSources().magic()",
    "player.getCooldowns().addCooldown(this, COOLDOWN_TICKS)",
    "message.sporenwerk.leuchtkern.used",
    "appendHoverText(",
):
    require(token in item, "active relic contract missing: " + token)
require("level.isClientSide" in item and "instanceof ServerLevel" in item,
        "pulse damage and target selection must remain server authoritative")
require("held.shrink" not in item and "consume(" not in item,
        "reusable relic must not consume itself")

for token in (
    "public boolean disruptWithResonancePulse()",
    "state != ATTACK_STOMP && state != ATTACK_BREATH",
    "this.attackTicksLeft = 0",
    "this.entityData.set(ATTACK_TICKS, 0)",
    "this.entityData.set(ATTACK_STATE, ATTACK_IDLE)",
    "this.attackCooldown = Math.max(this.attackCooldown, 80)",
):
    require(token in boss, "Colossus attack interrupt missing: " + token)
method_start = boss.find("public boolean disruptWithResonancePulse()")
method_end = boss.find("\n    }", method_start)
method = boss[method_start:method_end]
require("getAttackState()" in method and "ATTACK_AWAKENING" not in method,
        "pulse should interrupt only telegraphed stomp/breath wind-ups, not awakening")
require("if (this.level().isClientSide || this.attackTicksLeft <= 0) return false;" in method,
        "no-op when no wind-up exists")

loot = json.loads((RES / "data/sporenwerk/loot_tables/entities/mutagenkoloss.json").read_text(encoding="utf-8"))
require(any(entry.get("name") == "sporenwerk:leuchtender_kristallkern"
            for pool in loot["pools"] for entry in pool["entries"]),
        "Colossus loot table must award the Luminous Crystal Core")
advancement = json.loads((RES / "data/sporenwerk/advancements/monsters/leuchtender_kristallkern.json").read_text(encoding="utf-8"))
require(advancement["display"]["icon"]["item"] == "sporenwerk:leuchtender_kristallkern",
        "core discovery must have a dedicated advancement")
require(advancement["criteria"]["claim_core"]["trigger"] == "minecraft:inventory_changed",
        "advancement must trigger on taking the actual item")

model = json.loads((ASSETS / "models/item/leuchtender_kristallkern.json").read_text(encoding="utf-8"))
require(model["parent"] == "minecraft:item/generated"
        and model["textures"]["layer0"] == "sporenwerk:item/leuchtender_kristallkern",
        "item model must point to the real icon")
texture = ASSETS / "textures/item/leuchtender_kristallkern.png"
with Image.open(texture) as source:
    image = source.convert("RGBA")
require(image.size == (16, 16), "Luminous Crystal Core must be a native 16x16 item texture")
pixels = list(image.getdata())
require(sum(1 for p in pixels if p[3] == 0) >= 60,
        "icon should retain transparent pixels around the crystal silhouette")
require(len(set(pixels)) >= 10, "icon needs enough visible pixel-art facets")
require(any(r > 200 and g > 235 and b > 235 and a > 0 for r, g, b, a in pixels),
        "icon must contain the white-hot luminous core")
require(any(g > 190 and b > 220 and a > 0 for r, g, b, a in pixels),
        "icon must contain recognizable cyan crystal facets")

for locale in ("de_de.json", "en_us.json"):
    lang = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    for key in ("item.sporenwerk.leuchtender_kristallkern",
                "tooltip.sporenwerk.leuchtender_kristallkern.1",
                "tooltip.sporenwerk.leuchtender_kristallkern.2",
                "message.sporenwerk.leuchtkern.no_target",
                "message.sporenwerk.leuchtkern.used",
                "advancements.sporenwerk.leuchtkern.title",
                "advancements.sporenwerk.leuchtkern.description"):
        require(lang.get(key, "").strip(), f"{locale} missing {key}")
    require("%s" in lang["message.sporenwerk.leuchtkern.used"],
            f"{locale} must report pulse and interrupt counts")

preview = read("tools/make_art_preview.py")
require('"leuchtender_kristallkern"' in preview,
        "visual QA sheet must include the exact item icon")

build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.74\.0['\"]", build) is not None,
        "artifact must be version 1.74.0")
readme = read("README.md")
require("Version 1.74.0" in readme and "Version 1.73.0" in readme
        and "Aktueller Entwicklungsstand: 1.74.0" in readme,
        "release notes must preserve 1.73 and identify current release")
print("1.74 Luminous Crystal Core registration, pulse, boss attack interruption, loot, 16x16 art, DE/EN text, advancement and version contracts passed.")
