#!/usr/bin/env python3
"""Add the first rare, weak Sporenwerk creature to the polished 1.20.1 source tree."""
from pathlib import Path
import json, re, sys

ROOT = Path(sys.argv[1]).resolve()
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip(), encoding="utf-8")

def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text(encoding="utf-8")
    if new in s:
        return
    if old not in s:
        raise SystemExit(f"Expected patch context not found in {rel}: {old[:100]!r}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# Register the entity in the normal Forge mod event bus.
replace_once(
    "src/main/java/de/sporenwerk/Sporenwerk.java",
    "import de.sporenwerk.registry.ModMenus;",
    "import de.sporenwerk.registry.ModMenus;\nimport de.sporenwerk.registry.ModEntities;"
)
replace_once(
    "src/main/java/de/sporenwerk/Sporenwerk.java",
    "ModMenus.MENUS.register(modBus);",
    "ModMenus.MENUS.register(modBus);\n        ModEntities.ENTITIES.register(modBus);"
)

write("src/main/java/de/sporenwerk/registry/ModEntities.java", '''
package de.sporenwerk.registry;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.DaemmerlingEntity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModEntities {
    public static final DeferredRegister<EntityType<?>> ENTITIES =
            DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, Sporenwerk.MODID);

    public static final RegistryObject<EntityType<DaemmerlingEntity>> DAEMMERLING =
            ENTITIES.register("daemmerling", () -> EntityType.Builder
                    .of(DaemmerlingEntity::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.95F)
                    .clientTrackingRange(8)
                    .build("daemmerling"));

    private ModEntities() {}
}
''')

write("src/main/java/de/sporenwerk/entity/DaemmerlingEntity.java", '''
package de.sporenwerk.entity;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.Level;

/**
 * Rare, weak, familiar Minecraft-style creature.
 * Uses vanilla zombie navigation but has four hearts, low damage, and no reinforcement logic.
 */
public final class DaemmerlingEntity extends Zombie {
    public DaemmerlingEntity(EntityType<? extends Zombie> type, Level level) {
        super(type, level);
    }
}
''')

write("src/main/java/de/sporenwerk/registry/ModEntityEvents.java", '''
package de.sporenwerk.registry;

import de.sporenwerk.Sporenwerk;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.event.entity.SpawnPlacementRegisterEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = Sporenwerk.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class ModEntityEvents {
    private ModEntityEvents() {}

    @SubscribeEvent
    public static void createAttributes(EntityAttributeCreationEvent event) {
        AttributeSupplier attributes = Zombie.createAttributes()
                .add(Attributes.MAX_HEALTH, 8.0D)
                .add(Attributes.ATTACK_DAMAGE, 1.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.18D)
                .add(Attributes.FOLLOW_RANGE, 14.0D)
                .build();
        event.put(ModEntities.DAEMMERLING.get(), attributes);
    }

    @SubscribeEvent
    public static void registerSpawnPlacement(SpawnPlacementRegisterEvent event) {
        event.register(ModEntities.DAEMMERLING.get(), SpawnPlacements.Type.ON_GROUND,
                Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) ->
                        level.getMaxLocalRawBrightness(pos) < 7
                                && Monster.checkMonsterSpawnRules(ModEntities.DAEMMERLING.get(), level, reason, pos, random),
                SpawnPlacementRegisterEvent.Operation.REPLACE);
    }
}
''')

write("src/main/java/de/sporenwerk/client/DaemmerlingRenderer.java", '''
package de.sporenwerk.client;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.DaemmerlingEntity;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.ZombieRenderer;
import net.minecraft.resources.ResourceLocation;

public final class DaemmerlingRenderer extends ZombieRenderer<DaemmerlingEntity> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(Sporenwerk.MODID, "textures/entity/daemmerling.png");

    public DaemmerlingRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public ResourceLocation getTextureLocation(DaemmerlingEntity entity) {
        return TEXTURE;
    }
}
''')

replace_once(
    "src/main/java/de/sporenwerk/client/ClientModEvents.java",
    "import de.sporenwerk.registry.ModMenus;",
    "import de.sporenwerk.registry.ModMenus;\nimport de.sporenwerk.registry.ModEntities;\nimport de.sporenwerk.client.DaemmerlingRenderer;\nimport net.minecraftforge.client.event.EntityRenderersEvent;"
)
p = SRC / "client/ClientModEvents.java"
s = p.read_text(encoding="utf-8")
if "registerDaemmerlingRenderer" not in s:
    end = s.rfind("}")
    if end < 0:
        raise SystemExit("ClientModEvents class closing brace not found")
    s = s[:end] + '''
    @SubscribeEvent
    public static void registerDaemmerlingRenderer(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModEntities.DAEMMERLING.get(), DaemmerlingRenderer::new);
    }
''' + s[end:]
    p.write_text(s, encoding="utf-8")

replace_once(
    "src/main/java/de/sporenwerk/registry/ModItems.java",
    "import de.sporenwerk.item.FeldhandbuchItem;",
    "import de.sporenwerk.item.FeldhandbuchItem;\nimport net.minecraft.world.item.SpawnEggItem;"
)
replace_once(
    "src/main/java/de/sporenwerk/registry/ModItems.java",
    'public static final RegistryObject<Item> FELDHANDBUCH = ITEMS.register("feldhandbuch", () -> new FeldhandbuchItem(new Item.Properties().stacksTo(1)));',
    'public static final RegistryObject<Item> FELDHANDBUCH = ITEMS.register("feldhandbuch", () -> new FeldhandbuchItem(new Item.Properties().stacksTo(1)));\n    public static final RegistryObject<Item> DAEMMERLING_SPAWN_EGG = ITEMS.register("daemmerling_spawn_egg", () -> new SpawnEggItem(ModEntities.DAEMMERLING.get(), 0x263D2D, 0xB23843, new Item.Properties()));'
)
replace_once(
    "src/main/java/de/sporenwerk/registry/ModCreativeTabs.java",
    "output.accept(ModItems.FELDHANDBUCH.get());",
    "output.accept(ModItems.FELDHANDBUCH.get());\n                        output.accept(ModItems.DAEMMERLING_SPAWN_EGG.get());"
)

write("src/main/resources/assets/sporenwerk/models/item/daemmerling_spawn_egg.json", '''
{
  "parent": "minecraft:item/template_spawn_egg"
}
''')

write("src/main/resources/data/sporenwerk/forge/biome_modifier/daemmerling.json", '''
{
  "type": "forge:add_spawns",
  "biomes": "#minecraft:is_overworld",
  "spawners": [
    { "type": "sporenwerk:daemmerling", "weight": 2, "minCount": 1, "maxCount": 1 }
  ]
}
''')

write("src/main/resources/data/sporenwerk/loot_tables/entities/daemmerling.json", '''
{
  "type": "minecraft:entity",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        { "type": "minecraft:item", "name": "sporenwerk:pflanzenreste",
          "functions": [ { "function": "minecraft:set_count", "count": { "min": 0.0, "max": 1.0 } } ] }
      ]
    }
  ]
}
''')

lang_path = RES / "assets/sporenwerk/lang/de_de.json"
lang = json.loads(lang_path.read_text(encoding="utf-8"))
lang["entity.sporenwerk.daemmerling"] = "Dämmerling"
lang["item.sporenwerk.daemmerling_spawn_egg"] = "Dämmerling-Spawn-Ei"
lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Version label and documentation now describe the additional entity.
build = ROOT / "build.gradle"
s = build.read_text(encoding="utf-8")
s = re.sub(r"version = '1\\.0\\.(?:0|1|2)'", "version = '1.0.2'", s, count=1)
if "version = '1.0.2'" not in s:
    s = re.sub(r"version = '[^']+'", "version = '1.0.2'", s, count=1)
build.write_text(s, encoding="utf-8")

readme = ROOT / "README.md"
s = readme.read_text(encoding="utf-8")
s = s.replace("Sporenwerk: Wildwuchs 1.0.1", "Sporenwerk: Wildwuchs 1.0.2")
s = s.replace("sporenwerk-1.0.1.jar", "sporenwerk-1.0.2.jar")
s = s.replace("Three persistent skill branches and advancement milestones;", "One rare, low-health Dämmerling (8 HP / 1 damage) with its own texture, night-biased Overworld spawns, and no reinforcement behavior.\n- Three persistent skill branches and advancement milestones;")
s = s.replace("This is an improved V1.0.1,", "This is an improved V1.0.2,")
s = s.replace("custom enemy AI, true alternate-angle photo rendering and native FTB Quests export are not implemented.", "Advanced custom enemy AI, true alternate-angle photo rendering and native FTB Quests export are not implemented.")
readme.write_text(s, encoding="utf-8")
print("Added the weak Dämmerling creature and bumped mod version to 1.0.2.")
