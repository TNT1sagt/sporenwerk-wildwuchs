#!/usr/bin/env python3
"""Add the Kristallpirscher, a high-tier Mutagen hunter with mask counterplay."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def require_anchor(text, anchor, label):
    if anchor not in text:
        raise SystemExit(f"Cannot add Kristallpirscher: missing {label} anchor")


def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    require_anchor(text, old, label)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Entity registry: the stalker is a separate type and never reuses the Dämmerling ID.
entities_path = SRC / "registry/ModEntities.java"
entities = entities_path.read_text(encoding="utf-8")
if "KRISTALLPIRSCHER" not in entities:
    require_anchor(entities, "import de.sporenwerk.entity.DaemmerlingEntity;",
                   "Dämmerling entity import")
    entities = entities.replace(
        "import de.sporenwerk.entity.DaemmerlingEntity;",
        "import de.sporenwerk.entity.DaemmerlingEntity;\n"
        "import de.sporenwerk.entity.KristallpirscherEntity;",
        1
    )
    anchor = """                    .build("daemmerling"));"""
    add = anchor + """

    public static final RegistryObject<EntityType<KristallpirscherEntity>> KRISTALLPIRSCHER =
            ENTITIES.register("kristallpirscher", () -> EntityType.Builder
                    .of(KristallpirscherEntity::new, MobCategory.MONSTER)
                    .sized(0.72F, 2.05F)
                    .clientTrackingRange(10)
                    .build("kristallpirscher"));"""
    require_anchor(entities, anchor, "Dämmerling entity registration")
    entities = entities.replace(anchor, add, 1)
    entities_path.write_text(entities, encoding="utf-8")

# Hostile mob: the Spore Filter Mask is real counterplay and loses durability on blocked hits.
write("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java", """
package de.sporenwerk.entity;

import de.sporenwerk.block.InfestedTerrainBlock;
import de.sporenwerk.registry.ModBlocks;
import de.sporenwerk.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A field-born predator that appears only on strength-III Mutagen soil.
 * Unprotected hits inflict a short poison effect; a Spore Filter Mask blocks it
 * but consumes a little filter durability. The creature slowly heals on its home field.
 */
public final class KristallpirscherEntity extends Zombie {
    public KristallpirscherEntity(EntityType<? extends Zombie> type, Level level) {
        super(type, level);
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide && tickCount % 100 == 0 && isOnHighTierSoil() && getHealth() < getMaxHealth()) {
            heal(1.0F);
        }
    }

    @Override
    public boolean doHurtTarget(Entity target) {
        boolean hit = super.doHurtTarget(target);
        if (!hit || !(target instanceof Player player)) return hit;

        ItemStack head = player.getItemBySlot(EquipmentSlot.HEAD);
        if (head.is(ModItems.SPORENFILTERMASKE.get())) {
            head.hurtAndBreak(1, player, wearer -> wearer.broadcastBreakEvent(EquipmentSlot.HEAD));
        } else {
            player.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 0), this);
        }
        return true;
    }

    private boolean isOnHighTierSoil() {
        BlockState soil = level().getBlockState(blockPosition().below());
        return soil.is(ModBlocks.MUTAGEN_BODEN.get())
                && soil.hasProperty(InfestedTerrainBlock.MUTAGEN_LEVEL)
                && soil.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL) >= 3;
    }
}
""")

# Add the mob's attributes and a narrow spawn rule: only dark Tier-III Mutagen hotspots.
events_path = SRC / "registry/ModEntityEvents.java"
events = events_path.read_text(encoding="utf-8")
imports = [
    ("import de.sporenwerk.Sporenwerk;",
     "import de.sporenwerk.Sporenwerk;\nimport de.sporenwerk.block.InfestedTerrainBlock;\nimport de.sporenwerk.registry.ModBlocks;\nimport net.minecraft.core.BlockPos;\nimport net.minecraft.world.level.ServerLevelAccessor;\nimport net.minecraft.world.level.block.state.BlockState;"),
]
for old, new in imports:
    if "import de.sporenwerk.block.InfestedTerrainBlock;" not in events:
        require_anchor(events, old, "entity event imports")
        events = events.replace(old, new, 1)

anchor = "        event.put(ModEntities.DAEMMERLING.get(), attributes);"
addition = anchor + """
        event.put(ModEntities.KRISTALLPIRSCHER.get(), Zombie.createAttributes()
                .add(Attributes.MAX_HEALTH, 18.0D)
                .add(Attributes.ATTACK_DAMAGE, 3.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.24D)
                .add(Attributes.FOLLOW_RANGE, 24.0D)
                .add(Attributes.ARMOR, 2.0D)
                .build());"""
if "event.put(ModEntities.KRISTALLPIRSCHER.get()" not in events:
    require_anchor(events, anchor, "Dämmerling attribute binding")
    events = events.replace(anchor, addition, 1)

spawn_anchor = """                SpawnPlacementRegisterEvent.Operation.REPLACE);
    }
}"""
spawn_add = """                SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(ModEntities.KRISTALLPIRSCHER.get(), SpawnPlacements.Type.ON_GROUND,
                Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) ->
                        level.getMaxLocalRawBrightness(pos) < 7
                                && isTierThreeMutagenSoil(level, pos)
                                && Monster.checkMonsterSpawnRules(ModEntities.KRISTALLPIRSCHER.get(), level, reason, pos, random),
                SpawnPlacementRegisterEvent.Operation.REPLACE);
    }

    private static boolean isTierThreeMutagenSoil(ServerLevelAccessor level, BlockPos pos) {
        BlockState soil = level.getBlockState(pos.below());
        return soil.is(ModBlocks.MUTAGEN_BODEN.get())
                && soil.hasProperty(InfestedTerrainBlock.MUTAGEN_LEVEL)
                && soil.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL) >= 3;
    }
}"""
if "isTierThreeMutagenSoil" not in events:
    require_anchor(events, spawn_anchor, "spawn placement method end")
    events = events.replace(spawn_anchor, spawn_add, 1)
events_path.write_text(events, encoding="utf-8")

# Separate renderer and texture: same robust vanilla model layer, distinct body UV artwork.
write("src/main/java/de/sporenwerk/client/KristallpirscherRenderer.java", """
package de.sporenwerk.client;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.KristallpirscherEntity;
import net.minecraft.client.model.ZombieModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.resources.ResourceLocation;

public final class KristallpirscherRenderer extends HumanoidMobRenderer<KristallpirscherEntity, ZombieModel<KristallpirscherEntity>> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(Sporenwerk.MODID, "textures/entity/kristallpirscher.png");

    public KristallpirscherRenderer(EntityRendererProvider.Context context) {
        super(context, new ZombieModel<>(context.bakeLayer(ModelLayers.ZOMBIE)), 0.55F);
    }

    @Override
    public ResourceLocation getTextureLocation(KristallpirscherEntity entity) {
        return TEXTURE;
    }
}
""")

client_path = SRC / "client/ClientModEvents.java"
client = client_path.read_text(encoding="utf-8")
if "KristallpirscherRenderer" not in client:
    require_anchor(client, "import de.sporenwerk.client.DaemmerlingRenderer;",
                   "Dämmerling renderer import")
    client = client.replace(
        "import de.sporenwerk.client.DaemmerlingRenderer;",
        "import de.sporenwerk.client.DaemmerlingRenderer;\n"
        "import de.sporenwerk.client.KristallpirscherRenderer;",
        1
    )
if "ModEntities.KRISTALLPIRSCHER.get(), KristallpirscherRenderer::new" not in client:
    anchor = "event.registerEntityRenderer(ModEntities.DAEMMERLING.get(), DaemmerlingRenderer::new);"
    require_anchor(client, anchor, "Dämmerling renderer registration")
    client = client.replace(anchor, anchor + "\n"
        "        event.registerEntityRenderer(ModEntities.KRISTALLPIRSCHER.get(), KristallpirscherRenderer::new);", 1)
client_path.write_text(client, encoding="utf-8")

# Spawn egg and creative tab visibility.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
if "KRISTALLPIRSCHER_SPAWN_EGG" not in items:
    lines = items.splitlines()
    for index, line in enumerate(lines):
        if "DAEMMERLING_SPAWN_EGG" in line and "public static final RegistryObject<Item>" in line:
            lines.insert(index + 1, '    public static final RegistryObject<Item> KRISTALLPIRSCHER_SPAWN_EGG = ITEMS.register("kristallpirscher_spawn_egg", () -> new SpawnEggItem(ModEntities.KRISTALLPIRSCHER.get(), 0x142D38, 0x36E0D1, new Item.Properties()));')
            break
    else:
        raise SystemExit("Cannot add Kristallpirscher: Dämmerling spawn egg declaration was not found")
    items_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

replace_once(SRC / "registry/ModCreativeTabs.java",
             "output.accept(ModItems.DAEMMERLING_SPAWN_EGG.get());",
             "output.accept(ModItems.DAEMMERLING_SPAWN_EGG.get());\n                        output.accept(ModItems.KRISTALLPIRSCHER_SPAWN_EGG.get());",
             "creative tab spawn egg")

write("src/main/resources/assets/sporenwerk/models/item/kristallpirscher_spawn_egg.json", """
{
  "parent": "minecraft:item/template_spawn_egg"
}
""")

# Only Tier III Mutagen soil can host natural spawns; no broad population increase.
write("src/main/resources/data/sporenwerk/forge/biome_modifier/kristallpirscher.json", """
{
  "type": "forge:add_spawns",
  "biomes": "#minecraft:is_overworld",
  "spawners": [
    { "type": "sporenwerk:kristallpirscher", "weight": 1, "minCount": 1, "maxCount": 1 }
  ]
}
""")

write("src/main/resources/data/sporenwerk/loot_tables/entities/kristallpirscher.json", """
{
  "type": "minecraft:entity",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        {
          "type": "minecraft:item",
          "name": "sporenwerk:pflanzenreste",
          "functions": [
            { "function": "minecraft:set_count", "count": { "min": 0.0, "max": 2.0 } }
          ]
        }
      ]
    },
    {
      "rolls": 1.0,
      "conditions": [
        { "condition": "minecraft:random_chance", "chance": 0.25 }
      ],
      "entries": [
        { "type": "minecraft:item", "name": "sporenwerk:mutagenkernkristall" }
      ]
    }
  ]
}
""")

# The advancement is earned by defeating the creature; reward is descriptive, not power creep.
write("src/main/resources/data/sporenwerk/advancements/monsters/kristallpirscher.json", """
{
  "parent": "minecraft:adventure/kill_a_mob",
  "display": {
    "icon": { "item": "sporenwerk:mutagenkernkristall" },
    "title": { "translate": "advancements.sporenwerk.kristallpirscher.title" },
    "description": { "translate": "advancements.sporenwerk.kristallpirscher.description" },
    "frame": "challenge",
    "show_toast": true,
    "announce_to_chat": true,
    "hidden": false
  },
  "criteria": {
    "defeat_kristallpirscher": {
      "trigger": "minecraft:player_killed_entity",
      "conditions": {
        "entity": {
          "type": "sporenwerk:kristallpirscher"
        }
      }
    }
  },
  "requirements": [["defeat_kristallpirscher"]]
}
""")

# Distinct 64x64 zombie UV skin: dark mineral body, cyan glass eyes, crystal plates and glowing core.
def make_skin():
    image = Image.new("RGBA", (64, 64), (21, 36, 39, 255))
    d = ImageDraw.Draw(image)
    # Head UV: all faces use deep teal stone with several cracked facets.
    d.rectangle((0, 0, 31, 15), fill=(24, 43, 47, 255))
    d.rectangle((1, 2, 6, 7), fill=(38, 67, 72, 255))
    d.rectangle((17, 1, 23, 6), fill=(30, 55, 61, 255))
    d.rectangle((8, 8, 15, 15), fill=(18, 34, 41, 255))
    d.rectangle((9, 10, 10, 11), fill=(76, 255, 226, 255))
    d.rectangle((13, 10, 14, 11), fill=(76, 255, 226, 255))
    d.point((10, 10), fill=(255, 255, 219, 255))
    d.point((14, 10), fill=(255, 255, 219, 255))
    d.line([(4, 12), (7, 14), (9, 13)], fill=(54, 178, 167, 255), width=1)
    d.line([(20, 8), (23, 11), (22, 14)], fill=(61, 207, 194, 255), width=1)
    # Crystal crown along top/back UV, with sharp cyan facets.
    d.polygon([(4, 4), (6, 0), (9, 4)], fill=(33, 185, 177, 255))
    d.polygon([(12, 3), (15, 0), (17, 4)], fill=(70, 235, 211, 255))
    d.polygon([(21, 4), (24, 0), (27, 5)], fill=(28, 137, 146, 255))
    # Torso/front: dark armor ribs and a luminous core.
    d.rectangle((16, 16, 39, 31), fill=(20, 39, 46, 255))
    d.rectangle((20, 18, 27, 31), fill=(35, 68, 73, 255))
    d.rectangle((28, 18, 35, 31), fill=(25, 49, 56, 255))
    d.rectangle((22, 20, 25, 26), fill=(12, 25, 31, 255), outline=(58, 174, 165, 255))
    d.rectangle((23, 21, 24, 25), fill=(43, 219, 198, 255))
    d.rectangle((23, 22, 24, 23), fill=(228, 255, 225, 255))
    d.line([(18, 21), (20, 24), (18, 27)], fill=(64, 177, 158, 255), width=1)
    d.line([(36, 20), (34, 24), (37, 27)], fill=(51, 143, 151, 255), width=1)
    # Back, shoulders, arms: angular mineral plates and root-like cyan fissures.
    d.rectangle((32, 8, 39, 15), fill=(39, 76, 81, 255))
    d.rectangle((40, 8, 47, 15), fill=(20, 43, 51, 255))
    d.rectangle((48, 8, 55, 15), fill=(35, 67, 73, 255))
    d.polygon([(34, 8), (37, 5), (39, 9)], fill=(50, 198, 181, 255))
    d.polygon([(49, 9), (52, 5), (55, 10)], fill=(45, 160, 167, 255))
    for box in ((0, 20, 3, 31), (4, 20, 7, 31), (8, 20, 11, 31),
                (12, 20, 15, 31), (40, 20, 43, 31), (44, 20, 47, 31),
                (48, 20, 51, 31), (52, 20, 55, 31)):
        d.rectangle(box, fill=(28, 51, 58, 255))
    for pts in (
        [(1, 21), (3, 24), (2, 28), (3, 31)],
        [(5, 22), (6, 25), (5, 29)],
        [(9, 21), (10, 25), (9, 28)],
        [(13, 22), (14, 26), (13, 29)],
        [(41, 22), (42, 25), (41, 29)],
        [(45, 21), (46, 24), (45, 29)],
        [(49, 22), (50, 26), (49, 30)],
        [(53, 22), (54, 25), (53, 29)],
    ):
        d.line(pts, fill=(51, 202, 188, 255), width=1)
    # Legs: heavy dark plates with glowing shin seams.
    d.rectangle((0, 32, 15, 47), fill=(22, 39, 47, 255))
    d.rectangle((16, 32, 31, 47), fill=(30, 49, 57, 255))
    for x in (3, 7, 11, 19, 23, 27):
        d.rectangle((x, 34, x + 1, 44), fill=(39, 79, 85, 255))
        d.line([(x, 37), (x + 1, 39), (x, 42)], fill=(55, 185, 178, 255), width=1)
    # Lower UV area gets a repeatable cracked mineral pattern rather than flat filler.
    for x, y in ((35, 37), (43, 43), (51, 36), (59, 45), (37, 53), (47, 57), (57, 54)):
        d.polygon([(x, y), (x + 2, y - 3), (x + 4, y + 1), (x + 1, y + 3)],
                  fill=(34, 89, 95, 255))
        d.point((x + 2, y), fill=(77, 220, 201, 255))
    return image

entity_dir = ASSETS / "textures/entity"
entity_dir.mkdir(parents=True, exist_ok=True)
texture_path = entity_dir / "kristallpirscher.png"
make_skin().save(texture_path, optimize=True)
with Image.open(texture_path) as texture:
    rgba = texture.convert("RGBA")
    if rgba.size != (64, 64) or any(pixel[3] != 255 for pixel in rgba.getdata()):
        raise SystemExit("Kristallpirscher entity texture must be an opaque 64x64 PNG")

# German and English names plus a readable advancement.
for filename, entries in {
    "de_de.json": {
        "entity.sporenwerk.kristallpirscher": "Kristallpirscher",
        "item.sporenwerk.kristallpirscher_spawn_egg": "Kristallpirscher-Spawn-Ei",
        "advancements.sporenwerk.kristallpirscher.title": "Jäger des Hochmutagens",
        "advancements.sporenwerk.kristallpirscher.description": "Besiege einen Kristallpirscher im Einfluss eines Mutagenfelds."
    },
    "en_us.json": {
        "entity.sporenwerk.kristallpirscher": "Crystal Stalker",
        "item.sporenwerk.kristallpirscher_spawn_egg": "Crystal Stalker Spawn Egg",
        "advancements.sporenwerk.kristallpirscher.title": "Hunter of High Mutagen",
        "advancements.sporenwerk.kristallpirscher.description": "Defeat a Crystal Stalker under the influence of a Mutagen field."
    }
}.items():
    lang_path = ASSETS / "lang" / filename
    lang = json.loads(lang_path.read_text(encoding="utf-8"))
    lang.update(entries)
    lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Make the bespoke entity skin inspectable in the art QA contact sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = 'canvas.save(out, optimize=True)'
if "kristallpirscher.png" not in preview:
    require_anchor(preview, anchor, "art preview output")
    preview = preview.replace(
        anchor,
        """# Entity skin sample: show a magnified, nearest-neighbour view in the QA sheet.
entity_skin_path = assets/"textures/entity"/"kristallpirscher.png"
if entity_skin_path.exists():
    skin_preview = Image.open(entity_skin_path).convert("RGBA").resize((192, 192), Image.Resampling.NEAREST)
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(skin_preview, (1180, 70))
    draw = ImageDraw.Draw(canvas)
    draw.text((1180, 48), "KRISTALLPIRSCHER SKIN (64x64)", fill=(76, 235, 211), font=font)
""" + anchor,
        1
    )
    preview_path.write_text(preview, encoding="utf-8")

# Version and project history.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.32.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.32.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.32.0 — Kristallpirscher, Jäger der Hochmutagenfelder

- **Eigenständiger Gegner:** Der Kristallpirscher besitzt eine eigene Entity-ID, Spawn-Ei, 64×64-Pixeltextur, Renderer, Attribute, Loot-Tabelle und Fortschrittsziel.
- **Gezieltes Auftreten statt Gegnerflut:** Natürliches Spawnen ist auf dunkle Blöcke direkt über Mutagenboden der Stufe III begrenzt. In normalen Gebieten erzeugt er keine zusätzliche Monsterlast.
- **Kampf mit Konter:** Ungefilterte Treffer verursachen kurz Gift. Die Sporenfiltermaske blockt diesen Effekt, nutzt beim Abfangen aber Filterhaltbarkeit ab.
- **Feldgebundene Regeneration:** Auf Stufe-III-Mutagenboden regeneriert der Kristallpirscher langsam. Spieler können ihn dadurch aus der Hochrisikozone herauslocken.
- **Belohnung und Fortschritt:** Kleine Menge Pflanzenreste, selten ein Mutagenkernkristall und eine eigene Besieger-Auszeichnung. Deutsche und englische Texte sind enthalten.

Der Spawn-Check kontrolliert genau den Block unter der Spawnposition und lädt keine zusätzlichen Chunks. Regressionen prüfen Spawn-Gate, Masken-Kontersystem, Ressourcen, Textur und JAR.

"""
if "## Version 1.32.0 — Kristallpirscher" not in readme:
    marker = "## Version 1.31.0 — Quittierbare, gespeicherte Sirenenalarme"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.31.0 release notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.31.0 — gespeicherte Mutagen-Alarme mit Spieler-Quittierung.**",
    "**Aktueller Entwicklungsstand: 1.32.0 — Kristallpirscher und Hochmutagen-Gegnerökologie.**"
).replace("## Aktueller Schwerpunkt — 1.31.0", "## Aktueller Schwerpunkt — 1.32.0")
if "- Der Kristallpirscher erscheint nur nachts" not in readme[:2200]:
    readme = readme.replace(
        "- Die Mutagen-Warnsirene unterscheidet Warnung, erhöhte Gefahr und kritische Belastung visuell; Warntöne eskalieren nur bei einem Wechsel in eine höhere Stufe.",
        "- Die Mutagen-Warnsirene unterscheidet Warnung, erhöhte Gefahr und kritische Belastung visuell; Warntöne eskalieren nur bei einem Wechsel in eine höhere Stufe.\n- Der Kristallpirscher erscheint nur nachts in dunklen Hochmutagenfeldern und kann mit der Sporenfiltermaske bekämpft werden."
    )
readme_path.write_text(readme, encoding="utf-8")
print("Kristallpirscher entity, high-tier spawn gate, mask counterplay, texture, loot, advancement, and 1.32.0 generated.")

    items, count = re.subn(
        pattern,
        lambda match: match.group(1) + '\n    public static final RegistryObject<Item> KRISTALLPIRSCHER_SPAWN_EGG = ITEMS.register("kristallpirscher_spawn_egg", () -> new SpawnEggItem(ModEntities.KRISTALLPIRSCHER.get(), 0x142D38, 0x36E0D1, new Item.Properties()));',
        items,
        count=1
    )
    if count != 1:
        raise SystemExit("Cannot add Kristallpirscher: Dämmerling spawn egg declaration was not found")
    items_path.write_text(items, encoding="utf-8")
replace_once(SRC / "registry/ModCreativeTabs.java",
             "output.accept(ModItems.DAEMMERLING_SPAWN_EGG.get());",
             "output.accept(ModItems.DAEMMERLING_SPAWN_EGG.get());\n                        output.accept(ModItems.KRISTALLPIRSCHER_SPAWN_EGG.get());",
             "creative tab spawn egg")

write("src/main/resources/assets/sporenwerk/models/item/kristallpirscher_spawn_egg.json", """
{
  "parent": "minecraft:item/template_spawn_egg"
}
""")

# Only Tier III Mutagen soil can host natural spawns; no broad population increase.
write("src/main/resources/data/sporenwerk/forge/biome_modifier/kristallpirscher.json", """
{
  "type": "forge:add_spawns",
  "biomes": "#minecraft:is_overworld",
  "spawners": [
    { "type": "sporenwerk:kristallpirscher", "weight": 1, "minCount": 1, "maxCount": 1 }
  ]
}
""")

write("src/main/resources/data/sporenwerk/loot_tables/entities/kristallpirscher.json", """
{
  "type": "minecraft:entity",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        {
          "type": "minecraft:item",
          "name": "sporenwerk:pflanzenreste",
          "functions": [
            { "function": "minecraft:set_count", "count": { "min": 0.0, "max": 2.0 } }
          ]
        }
      ]
    },
    {
      "rolls": 1.0,
      "conditions": [
        { "condition": "minecraft:random_chance", "chance": 0.25 }
      ],
      "entries": [
        { "type": "minecraft:item", "name": "sporenwerk:mutagenkernkristall" }
      ]
    }
  ]
}
""")

# The advancement is earned by defeating the creature; reward is descriptive, not power creep.
write("src/main/resources/data/sporenwerk/advancements/monsters/kristallpirscher.json", """
{
  "parent": "minecraft:adventure/kill_a_mob",
  "display": {
    "icon": { "item": "sporenwerk:mutagenkernkristall" },
    "title": { "translate": "advancements.sporenwerk.kristallpirscher.title" },
    "description": { "translate": "advancements.sporenwerk.kristallpirscher.description" },
    "frame": "challenge",
    "show_toast": true,
    "announce_to_chat": true,
    "hidden": false
  },
  "criteria": {
    "defeat_kristallpirscher": {
      "trigger": "minecraft:player_killed_entity",
      "conditions": {
        "entity": {
          "type": "sporenwerk:kristallpirscher"
        }
      }
    }
  },
  "requirements": [["defeat_kristallpirscher"]]
}
""")

# Distinct 64x64 zombie UV skin: dark mineral body, cyan glass eyes, crystal plates and glowing core.
def make_skin():
    image = Image.new("RGBA", (64, 64), (21, 36, 39, 255))
    d = ImageDraw.Draw(image)
    # Head UV: all faces use deep teal stone with several cracked facets.
    d.rectangle((0, 0, 31, 15), fill=(24, 43, 47, 255))
    d.rectangle((1, 2, 6, 7), fill=(38, 67, 72, 255))
    d.rectangle((17, 1, 23, 6), fill=(30, 55, 61, 255))
    d.rectangle((8, 8, 15, 15), fill=(18, 34, 41, 255))
    d.rectangle((9, 10, 10, 11), fill=(76, 255, 226, 255))
    d.rectangle((13, 10, 14, 11), fill=(76, 255, 226, 255))
    d.point((10, 10), fill=(255, 255, 219, 255))
    d.point((14, 10), fill=(255, 255, 219, 255))
    d.line([(4, 12), (7, 14), (9, 13)], fill=(54, 178, 167, 255), width=1)
    d.line([(20, 8), (23, 11), (22, 14)], fill=(61, 207, 194, 255), width=1)
    # Crystal crown along top/back UV, with sharp cyan facets.
    d.polygon([(4, 4), (6, 0), (9, 4)], fill=(33, 185, 177, 255))
    d.polygon([(12, 3), (15, 0), (17, 4)], fill=(70, 235, 211, 255))
    d.polygon([(21, 4), (24, 0), (27, 5)], fill=(28, 137, 146, 255))
    # Torso/front: dark armor ribs and a luminous core.
    d.rectangle((16, 16, 39, 31), fill=(20, 39, 46, 255))
    d.rectangle((20, 18, 27, 31), fill=(35, 68, 73, 255))
    d.rectangle((28, 18, 35, 31), fill=(25, 49, 56, 255))
    d.rectangle((22, 20, 25, 26), fill=(12, 25, 31, 255), outline=(58, 174, 165, 255))
    d.rectangle((23, 21, 24, 25), fill=(43, 219, 198, 255))
    d.rectangle((23, 22, 24, 23), fill=(228, 255, 225, 255))
    d.line([(18, 21), (20, 24), (18, 27)], fill=(64, 177, 158, 255), width=1)
    d.line([(36, 20), (34, 24), (37, 27)], fill=(51, 143, 151, 255), width=1)
    # Back, shoulders, arms: angular mineral plates and root-like cyan fissures.
    d.rectangle((32, 8, 39, 15), fill=(39, 76, 81, 255))
    d.rectangle((40, 8, 47, 15), fill=(20, 43, 51, 255))
    d.rectangle((48, 8, 55, 15), fill=(35, 67, 73, 255))
    d.polygon([(34, 8), (37, 5), (39, 9)], fill=(50, 198, 181, 255))
    d.polygon([(49, 9), (52, 5), (55, 10)], fill=(45, 160, 167, 255))
    for box in ((0, 20, 3, 31), (4, 20, 7, 31), (8, 20, 11, 31),
                (12, 20, 15, 31), (40, 20, 43, 31), (44, 20, 47, 31),
                (48, 20, 51, 31), (52, 20, 55, 31)):
        d.rectangle(box, fill=(28, 51, 58, 255))
    for pts in (
        [(1, 21), (3, 24), (2, 28), (3, 31)],
        [(5, 22), (6, 25), (5, 29)],
        [(9, 21), (10, 25), (9, 28)],
        [(13, 22), (14, 26), (13, 29)],
        [(41, 22), (42, 25), (41, 29)],
        [(45, 21), (46, 24), (45, 29)],
        [(49, 22), (50, 26), (49, 30)],
        [(53, 22), (54, 25), (53, 29)],
    ):
        d.line(pts, fill=(51, 202, 188, 255), width=1)
    # Legs: heavy dark plates with glowing shin seams.
    d.rectangle((0, 32, 15, 47), fill=(22, 39, 47, 255))
    d.rectangle((16, 32, 31, 47), fill=(30, 49, 57, 255))
    for x in (3, 7, 11, 19, 23, 27):
        d.rectangle((x, 34, x + 1, 44), fill=(39, 79, 85, 255))
        d.line([(x, 37), (x + 1, 39), (x, 42)], fill=(55, 185, 178, 255), width=1)
    # Lower UV area gets a repeatable cracked mineral pattern rather than flat filler.
    for x, y in ((35, 37), (43, 43), (51, 36), (59, 45), (37, 53), (47, 57), (57, 54)):
        d.polygon([(x, y), (x + 2, y - 3), (x + 4, y + 1), (x + 1, y + 3)],
                  fill=(34, 89, 95, 255))
        d.point((x + 2, y), fill=(77, 220, 201, 255))
    return image

entity_dir = ASSETS / "textures/entity"
entity_dir.mkdir(parents=True, exist_ok=True)
texture_path = entity_dir / "kristallpirscher.png"
make_skin().save(texture_path, optimize=True)
with Image.open(texture_path) as texture:
    rgba = texture.convert("RGBA")
    if rgba.size != (64, 64) or any(pixel[3] != 255 for pixel in rgba.getdata()):
        raise SystemExit("Kristallpirscher entity texture must be an opaque 64x64 PNG")

# German and English names plus a readable advancement.
for filename, entries in {
    "de_de.json": {
        "entity.sporenwerk.kristallpirscher": "Kristallpirscher",
        "item.sporenwerk.kristallpirscher_spawn_egg": "Kristallpirscher-Spawn-Ei",
        "advancements.sporenwerk.kristallpirscher.title": "Jäger des Hochmutagens",
        "advancements.sporenwerk.kristallpirscher.description": "Besiege einen Kristallpirscher im Einfluss eines Mutagenfelds."
    },
    "en_us.json": {
        "entity.sporenwerk.kristallpirscher": "Crystal Stalker",
        "item.sporenwerk.kristallpirscher_spawn_egg": "Crystal Stalker Spawn Egg",
        "advancements.sporenwerk.kristallpirscher.title": "Hunter of High Mutagen",
        "advancements.sporenwerk.kristallpirscher.description": "Defeat a Crystal Stalker under the influence of a Mutagen field."
    }
}.items():
    lang_path = ASSETS / "lang" / filename
    lang = json.loads(lang_path.read_text(encoding="utf-8"))
    lang.update(entries)
    lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Make the bespoke entity skin inspectable in the art QA contact sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = 'canvas.save(out, optimize=True)'
if "kristallpirscher.png" not in preview:
    require_anchor(preview, anchor, "art preview output")
    preview = preview.replace(
        anchor,
        """# Entity skin sample: show a magnified, nearest-neighbour view in the QA sheet.
entity_skin_path = assets/"textures/entity"/"kristallpirscher.png"
if entity_skin_path.exists():
    skin_preview = Image.open(entity_skin_path).convert("RGBA").resize((192, 192), Image.Resampling.NEAREST)
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(skin_preview, (1180, 70))
    draw = ImageDraw.Draw(canvas)
    draw.text((1180, 48), "KRISTALLPIRSCHER SKIN (64x64)", fill=(76, 235, 211), font=font)
""" + anchor,
        1
    )
    preview_path.write_text(preview, encoding="utf-8")

# Version and project history.
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.32.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.32.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.32.0 — Kristallpirscher, Jäger der Hochmutagenfelder

- **Eigenständiger Gegner:** Der Kristallpirscher besitzt eine eigene Entity-ID, Spawn-Ei, 64×64-Pixeltextur, Renderer, Attribute, Loot-Tabelle und Fortschrittsziel.
- **Gezieltes Auftreten statt Gegnerflut:** Natürliches Spawnen ist auf dunkle Blöcke direkt über Mutagenboden der Stufe III begrenzt. In normalen Gebieten erzeugt er keine zusätzliche Monsterlast.
- **Kampf mit Konter:** Ungefilterte Treffer verursachen kurz Gift. Die Sporenfiltermaske blockt diesen Effekt, nutzt beim Abfangen aber Filterhaltbarkeit ab.
- **Feldgebundene Regeneration:** Auf Stufe-III-Mutagenboden regeneriert der Kristallpirscher langsam. Spieler können ihn dadurch aus der Hochrisikozone herauslocken.
- **Belohnung und Fortschritt:** Kleine Menge Pflanzenreste, selten ein Mutagenkernkristall und eine eigene Besieger-Auszeichnung. Deutsche und englische Texte sind enthalten.

Der Spawn-Check kontrolliert genau den Block unter der Spawnposition und lädt keine zusätzlichen Chunks. Regressionen prüfen Spawn-Gate, Masken-Kontersystem, Ressourcen, Textur und JAR.

"""
if "## Version 1.32.0 — Kristallpirscher" not in readme:
    marker = "## Version 1.31.0 — Quittierbare, gespeicherte Sirenenalarme"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.31.0 release notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.31.0 — gespeicherte Mutagen-Alarme mit Spieler-Quittierung.**",
    "**Aktueller Entwicklungsstand: 1.32.0 — Kristallpirscher und Hochmutagen-Gegnerökologie.**"
).replace("## Aktueller Schwerpunkt — 1.31.0", "## Aktueller Schwerpunkt — 1.32.0")
if "- Der Kristallpirscher erscheint nur nachts" not in readme[:2200]:
    readme = readme.replace(
        "- Die Mutagen-Warnsirene unterscheidet Warnung, erhöhte Gefahr und kritische Belastung visuell; Warntöne eskalieren nur bei einem Wechsel in eine höhere Stufe.",
        "- Die Mutagen-Warnsirene unterscheidet Warnung, erhöhte Gefahr und kritische Belastung visuell; Warntöne eskalieren nur bei einem Wechsel in eine höhere Stufe.\n- Der Kristallpirscher erscheint nur nachts in dunklen Hochmutagenfeldern und kann mit der Sporenfiltermaske bekämpft werden."
    )
readme_path.write_text(readme, encoding="utf-8")
print("Kristallpirscher entity, high-tier spawn gate, mask counterplay, texture, loot, advancement, and 1.32.0 generated.")
