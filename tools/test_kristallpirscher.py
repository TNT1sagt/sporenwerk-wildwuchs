#!/usr/bin/env python3
"""Regression tests for the Kristallpirscher's bounded Tier-III spawn gate and counterplay."""
from pathlib import Path
import json
import re
import sys
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(ok, message):
    if not ok:
        raise SystemExit("Kristallpirscher regression: " + message)


entities = read("src/main/java/de/sporenwerk/registry/ModEntities.java")
events = read("src/main/java/de/sporenwerk/registry/ModEntityEvents.java")
entity = read("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java")
renderer = read("src/main/java/de/sporenwerk/client/KristallpirscherRenderer.java")
client_events = read("src/main/java/de/sporenwerk/client/ClientModEvents.java")
items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")

for token in (
    'register("kristallpirscher"',
    "MobCategory.MONSTER",
    "EntityType<KristallpirscherEntity>",
):
    require(token in entities, "entity registration missing " + token)
for token in (
    "event.put(ModEntities.KRISTALLPIRSCHER.get()",
    "Attributes.MAX_HEALTH, 18.0D",
    "Attributes.ATTACK_DAMAGE, 3.0D",
    "Attributes.MOVEMENT_SPEED, 0.24D",
    "isTierThreeMutagenSoil(level, pos)",
    "level.getMaxLocalRawBrightness(pos) < 7",
    "soil.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL) >= 3",
):
    require(token in events, "attribute/spawn gate missing " + token)
require("getBlockState(pos.below())" in events and "getChunk(" not in events
        and "getChunkNow(" not in events, "spawn gate must read only local blocks and not force-load chunks")
for token in (
    "boolean doHurtTarget(Entity target)",
    "MobEffects.POISON, 80, 0",
    "ModItems.SPORENFILTERMASKE.get()",
    "head.hurtAndBreak(1, player",
    "tickCount % 100 == 0",
    "isOnHighTierSoil()",
    "heal(1.0F)",
):
    require(token in entity, "combat/counterplay behavior missing " + token)
require("textures/entity/kristallpirscher.png" in renderer
        and "KristallpirscherRenderer::new" in client_events,
        "renderer must be registered against its own custom texture")
require('register("kristallpirscher_spawn_egg"' in items
        and "output.accept(ModItems.KRISTALLPIRSCHER_SPAWN_EGG.get())" in creative,
        "spawn egg must be registered and reachable in the creative tab")
require("ForgeSpawnEggItem(ModEntities.KRISTALLPIRSCHER" in items,
        "spawn egg must lazily resolve the entity type after registries are bound")

biome = json.loads((RES / "data/sporenwerk/forge/biome_modifier/kristallpirscher.json").read_text(encoding="utf-8"))
require(biome["type"] == "forge:add_spawns"
        and biome["spawners"][0]["type"] == "sporenwerk:kristallpirscher"
        and biome["spawners"][0]["weight"] == 1
        and biome["spawners"][0]["minCount"] == 1
        and biome["spawners"][0]["maxCount"] == 1,
        "natural spawning should be rare and use the custom hotspot placement gate")
loot = json.loads((RES / "data/sporenwerk/loot_tables/entities/kristallpirscher.json").read_text(encoding="utf-8"))
require(any(entry.get("name") == "sporenwerk:pflanzenreste"
            for pool in loot["pools"] for entry in pool["entries"]),
        "loot should include small organic residue")
shard_pools = [pool for pool in loot["pools"]
               if any(entry.get("name") == "sporenwerk:kristallpirscher_resonanzsplitter"
                      for entry in pool.get("entries", []))]
require(len(shard_pools) == 1 and not shard_pools[0].get("conditions"),
        "each Kristallpirscher should yield guaranteed resonance shards")
require(any(any(cond.get("condition") == "minecraft:random_chance" and cond.get("chance") == 0.25
                for cond in pool.get("conditions", []))
            and any(entry.get("name") == "sporenwerk:mutagenkernkristall" for entry in pool["entries"])
            for pool in loot["pools"]),
        "Mutagen core crystal must remain a rare drop")
advancement = json.loads((RES / "data/sporenwerk/advancements/monsters/kristallpirscher.json").read_text(encoding="utf-8"))
require(advancement["parent"] == "minecraft:adventure/kill_a_mob"
        and "defeat_kristallpirscher" in advancement["criteria"],
        "defeating the creature should grant a dedicated advancement")

texture_path = ASSETS / "textures/entity/kristallpirscher.png"
with Image.open(texture_path) as source:
    texture = source.convert("RGBA")
require(texture.size == (64, 64), "entity skin must use the standard 64x64 humanoid UV")
require(all(px[3] == 255 for px in texture.getdata()), "entity skin must be fully opaque")
require(len(set(texture.getdata())) >= 18, "entity skin must have a readable pixel-art palette")
require(any(px[1] > 180 and px[2] > 160 for px in texture.getdata()),
        "skin must contain its visible cyan crystal highlights")

for name, values in {
    "de_de.json": ("Kristallpirscher", "Kristallpirscher-Spawn-Ei", "Jäger des Hochmutagens"),
    "en_us.json": ("Crystal Stalker", "Crystal Stalker Spawn Egg", "Hunter of High Mutagen"),
}.items():
    data = json.loads((ASSETS / "lang" / name).read_text(encoding="utf-8"))
    require(all(any(value in text for text in data.values()) for value in values),
            name + " missing creature/egg/advancement localization")

preview = read("tools/make_art_preview.py")
require("kristallpirscher.png" in preview, "art preview must include the custom entity skin")
build = read("build.gradle")
require(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.38\.0['\"]", build) is not None,
        "artifact must be version 1.38.0")
readme = read("README.md")
require("Version 1.38.0" in readme and "Version 1.37.0" in readme,
        "release notes must preserve the 1.36.0 history")
print("Kristallpirscher registration, hotspot-only spawning, mask counterplay, loot, advancement, texture, locales, and version passed.")
