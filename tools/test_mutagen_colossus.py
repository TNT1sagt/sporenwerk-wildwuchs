#!/usr/bin/env python3
"""Regression tests for the 1.55.0 animated Crystal Colossus boss."""
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


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen Colossus regression: " + message)


entities = read("src/main/java/de/sporenwerk/registry/ModEntities.java")
events = read("src/main/java/de/sporenwerk/registry/ModEntityEvents.java")
entity = read("src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java")
ritual = read("src/main/java/de/sporenwerk/entity/MutagenkolossRitual.java")
model = read("src/main/java/de/sporenwerk/client/MutagenkolossModel.java")
renderer = read("src/main/java/de/sporenwerk/client/MutagenkolossRenderer.java")
client = read("src/main/java/de/sporenwerk/client/ClientModEvents.java")
items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")

for token in (
    'register("mutagenkoloss"',
    "EntityType<MutagenkolossEntity>",
    "MobCategory.MONSTER",
    ".sized(3.6F, 3.35F)",
    ".fireImmune()",
):
    require(token in entities, "boss registration missing " + token)
for token in (
    "createMutagenkolossAttributes",
    "Attributes.MAX_HEALTH, 260.0D",
    "Attributes.ATTACK_DAMAGE, 16.0D",
    "Attributes.ARMOR, 18.0D",
    "Attributes.KNOCKBACK_RESISTANCE, 0.95D",
):
    require(token in events, "boss attribute contract missing " + token)
for token in (
    "ATTACK_STOMP", "ATTACK_BREATH", "ATTACK_AWAKENING",
    "STOMP_WINDUP = 42", "BREATH_WINDUP = 48",
    "performStomp(", "performCrystalBreath(",
    "this.getHealth() <= this.getMaxHealth() * 0.5F",
    "this.secondPhaseTriggered = true",
    "this.bossEvent.setProgress(", "bossEvent.addPlayer(player)",
    "bossEvent.removePlayer(player)", "isPersistenceRequired()", "removeWhenFarAway(",
    "tag.putBoolean(\"SporenwerkPhaseTwo\"",
):
    require(token in entity, "boss combat/persistence contract missing " + token)
require("damageSources().mobAttack(this)" in entity and "victim.knockback(" in entity,
        "attacks must apply server-authoritative damage and knockback")
require("getEntitiesOfClass(LivingEntity.class" in entity,
        "boss attacks must resolve real entity targets")
require("this.entityData.set(ATTACK_STATE, state)" in entity
        and "EntityDataSerializers.INT" in entity,
        "attack state must synchronize for client-side animations")

for token in (
    "event.getEntity() instanceof ServerPlayer",
    "!player.isShiftKeyDown()", "held.getCount() < 3",
    "ModItems.MUTAGENKERNKRISTALL.get()",
    "InfestedTerrainBlock.MUTAGEN_LEVEL",
    "getValue(InfestedTerrainBlock.MUTAGEN_LEVEL) < 3",
    "level.noCollision(boss)",
    "held.shrink(3)",
    "event.setCancellationResult(InteractionResult.SUCCESS)",
    "Nothing was consumed",
):
    if token == "Nothing was consumed":
        continue
    require(token in ritual, "Survival summon ritual missing " + token)
require("if (!level.noCollision(boss))" in ritual
        and ritual.index("if (!level.noCollision(boss))") < ritual.index("held.shrink(3)"),
        "ritual must validate boss collision before consuming any crystals")
require("event.getLevel().isClientSide" in ritual,
        "ritual must only spawn the boss on the server")

for token in (
    "createBodyLayer()", "createGlowLayer()", "setupAnim(",
    "spine_0", "spine_6", "tail_tip", "front_left", "rear_right",
    "ATTACK_STOMP", "ATTACK_BREATH", "ATTACK_AWAKENING",
    "Mth.sin(", "renderToBuffer(",
):
    require(token in model, "custom model/animation missing " + token)
require("MutagenkolossModel.LAYER_LOCATION" in client
        and "MutagenkolossModel.GLOW_LAYER_LOCATION" in client
        and "MutagenkolossRenderer::new" in client,
        "custom main/glow model layers and renderer must be registered")
require("textures/entity/mutagenkoloss.png" in renderer
        and "textures/entity/mutagenkoloss_glow.png" in renderer
        and "RenderType.eyes(GLOW_TEXTURE)" in renderer
        and "0xF000F0" in renderer,
        "separate full-bright crystal glow pass must be wired into renderer")
require("MUTAGENKOLOSS_HERZ" in items and "MUTAGENKOLOSS_SPAWN_EGG" in items
        and "output.accept(ModItems.MUTAGENKOLOSS_SPAWN_EGG.get())" in creative,
        "boss heart and spawn egg must be registered and discoverable")

loot = json.loads((RES / "data/sporenwerk/loot_tables/entities/mutagenkoloss.json").read_text(encoding="utf-8"))
all_entries = [entry for pool in loot["pools"] for entry in pool["entries"]]
require(any(entry.get("name") == "sporenwerk:mutagenkoloss_herz" for entry in all_entries),
        "boss must drop its unique heart")
require(any(entry.get("name") == "sporenwerk:mutagenkernkristall" for entry in all_entries),
        "boss should yield core crystals")
advancement = json.loads((RES / "data/sporenwerk/advancements/monsters/mutagenkoloss.json").read_text(encoding="utf-8"))
require(advancement["criteria"]["defeat_mutagenkoloss"]["conditions"]["entity"]["type"] == "sporenwerk:mutagenkoloss",
        "dedicated boss-kill advancement missing")
for path in (
    RES / "assets/sporenwerk/models/item/mutagenkoloss_herz.json",
    RES / "assets/sporenwerk/models/item/mutagenkoloss_spawn_egg.json",
):
    json.loads(path.read_text(encoding="utf-8"))

skin = ASSETS / "textures/entity/mutagenkoloss.png"
with Image.open(skin) as image:
    rgba = image.convert("RGBA")
require(rgba.size == (256, 256), "boss texture must use its custom 256x256 UV atlas")
require(all(pixel[3] == 255 for pixel in rgba.getdata()), "boss base texture must be opaque")
require(len(set(rgba.getdata())) >= 48, "boss texture must contain detailed pixel-art facets")
require(any(p[1] > 180 and p[2] > 200 for p in rgba.getdata()),
        "base texture must contain bright cyan crystal facets")
glow = ASSETS / "textures/entity/mutagenkoloss_glow.png"
with Image.open(glow) as image:
    glow_rgba = image.convert("RGBA")
require(glow_rgba.size == (256, 256), "emissive atlas must match the model's UV size")
alpha_values = [p[3] for p in glow_rgba.getdata()]
require(alpha_values.count(0) > 50000 and alpha_values.count(255) > 500,
        "glow atlas must be transparent outside luminous regions and opaque on crystal geometry")
heart = ASSETS / "textures/item/mutagenkoloss_herz.png"
with Image.open(heart) as image:
    heart_rgba = image.convert("RGBA")
require(heart_rgba.size == (16, 16), "boss reward icon must be a Minecraft-sized 16x16 sprite")
require(any(p[3] == 0 for p in heart_rgba.getdata())
        and any(p[0] > 100 and p[2] > 180 for p in heart_rgba.getdata()),
        "boss reward icon must have transparent background and luminous crystal pixels")

for locale, expected in (
    ("de_de.json", ("Kristallkoloss", "Herz des Kristallkolosses", "Mutagenboden Stufe III")),
    ("en_us.json", ("Crystal Colossus", "Crystal Colossus Heart", "Tier III Mutagen soil")),
):
    data = json.loads((ASSETS / "lang" / locale).read_text(encoding="utf-8"))
    text_values = " ".join(str(value) for value in data.values())
    require(all(value in text_values for value in expected), locale + " is missing boss/ritual localization")

preview = read("tools/make_art_preview.py")
require("MUTAGENKOLOSS PIXEL ART" in preview
        and "mutagenkoloss_glow.png" in preview,
        "visual QA sheet must show the new boss texture and emissive atlas")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.55\.0['\"]", build) is not None,
        "artifact must be version 1.55.0")
readme = read("README.md")
require("Version 1.55.0" in readme and "Version 1.54.0" in readme
        and "Aktueller Entwicklungsstand: 1.55.0" in readme,
        "release notes and current version must be updated without losing history")
print("Crystal Colossus registration, model, glow layer, synchronized animations, attacks, ritual, loot, pixel art, locales and release contracts passed.")
