#!/usr/bin/env python3
"""Add a redstone-powered Spore Ward that protects research farms from Dämmerlinge."""
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

def replace_once(rel, old, new, label):
    path = ROOT / rel
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Spore Ward patch cannot locate {label} in {rel}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")

replace_once(
    "src/main/java/de/sporenwerk/registry/ModBlocks.java",
    "import de.sporenwerk.block.MutationAnchorBlock;",
    "import de.sporenwerk.block.MutationAnchorBlock;\nimport de.sporenwerk.block.SporeWardBlock;",
    "block class import"
)
ward_registration = """    public static final RegistryObject<Block> SPORENABWEHR = BLOCKS.register("sporenabwehr",
            () -> new SporeWardBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(2.5f).requiresCorrectToolForDrops().sound(SoundType.COPPER)));"""
block_anchor = """    public static final RegistryObject<Block> SPORENRESISTENTER_BLOCK = BLOCKS.register("sporenresistenter_block",
            () -> new Block(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE)
                    .strength(4.0f, 9.0f).requiresCorrectToolForDrops().sound(SoundType.GLASS)));"""
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
             block_anchor, block_anchor + "\n\n" + ward_registration, "resistant-block registration point")
replace_once(
    "src/main/java/de/sporenwerk/registry/ModBlocks.java",
    '        ModItems.ITEMS.register("sporenresistenter_block", () -> new net.minecraft.world.item.BlockItem(SPORENRESISTENTER_BLOCK.get(), new Item.Properties()));',
    '        ModItems.ITEMS.register("sporenresistenter_block", () -> new net.minecraft.world.item.BlockItem(SPORENRESISTENTER_BLOCK.get(), new Item.Properties()));\n        ModItems.ITEMS.register("sporenabwehr", () -> new net.minecraft.world.item.BlockItem(SPORENABWEHR.get(), new Item.Properties()));',
    "ward inventory item"
)
replace_once(
    "src/main/java/de/sporenwerk/registry/ModCreativeTabs.java",
    "output.accept(ModBlocks.SPORENRESISTENTER_BLOCK.get());",
    "output.accept(ModBlocks.SPORENRESISTENTER_BLOCK.get());\n                        output.accept(ModBlocks.SPORENABWEHR.get());",
    "creative catalogue ward entry"
)

write("src/main/java/de/sporenwerk/block/SporeWardBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.entity.DaemmerlingEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.AABB;

/** Redstone-powered crop-defense emitter with a bounded, refreshed repulsion pulse. */
public final class SporeWardBlock extends Block {
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;
    private static final int HORIZONTAL_RADIUS = 8;
    private static final int VERTICAL_RADIUS = 3;
    private static final int REFRESH_TICKS = 10;
    private static final int REPULSE_GRACE_TICKS = 30;

    public SporeWardBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(POWERED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(POWERED);
    }

    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean moving) {
        super.onPlace(state, level, pos, oldState, moving);
        if (oldState.getBlock() != this) refreshPower(level, pos);
    }

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos,
                                Block sourceBlock, BlockPos sourcePos, boolean moving) {
        super.neighborChanged(state, level, pos, sourceBlock, sourcePos, moving);
        if (!level.isClientSide) refreshPower(level, pos);
    }

    private void refreshPower(Level level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (!state.is(this)) return;
        boolean powered = level.hasNeighborSignal(pos);
        if (state.getValue(POWERED) != powered) {
            level.setBlock(pos, state.setValue(POWERED, powered), 3);
            state = level.getBlockState(pos);
        }
        if (powered && !level.isClientSide) level.scheduleTick(pos, this, REFRESH_TICKS);
    }

    @Override
    public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (!state.is(this) || !state.getValue(POWERED) || !level.hasNeighborSignal(pos)) {
            if (state.is(this) && state.getValue(POWERED)) {
                level.setBlock(pos, state.setValue(POWERED, false), 3);
            }
            return;
        }

        long repelUntil = level.getGameTime() + REPULSE_GRACE_TICKS;
        AABB area = new AABB(pos).inflate(HORIZONTAL_RADIUS, VERTICAL_RADIUS, HORIZONTAL_RADIUS);
        for (DaemmerlingEntity mob : level.getEntitiesOfClass(DaemmerlingEntity.class, area)) {
            if (mob.isAlive()) {
                mob.getPersistentData().putLong("SporenwerkWardRepelledUntil", repelUntil);
            }
        }
        level.scheduleTick(pos, this, REFRESH_TICKS);
    }
}
""")

entity_path = SRC / "entity/DaemmerlingEntity.java"
entity = entity_path.read_text(encoding="utf-8")
if "private boolean isRepelledBySporeWard()" not in entity:
    anchor = "    @Override\n    protected void registerGoals() {"
    method = """    private boolean isRepelledBySporeWard() {
        return getPersistentData().getLong("SporenwerkWardRepelledUntil") > level().getGameTime();
    }

"""
    if anchor not in entity:
        raise SystemExit("Cannot locate Dämmerling goal registration for ward predicate")
    entity = entity.replace(anchor, method + anchor, 1)

# Guard both starts/continuations of the Mutagen Bloom scent goal.
entity = entity.replace(
    "if (!mob.isAlive() || mob.getTarget() != null) return false;",
    "if (!mob.isAlive() || mob.getTarget() != null || mob.isRepelledBySporeWard()) return false;"
)
entity = entity.replace(
    "return target != null && mob.isAlive() && mob.getTarget() == null\n                    && !isProtected(target) && isMatureCrop(target);",
    "return target != null && mob.isAlive() && mob.getTarget() == null\n                    && !mob.isRepelledBySporeWard()\n                    && !isProtected(target) && isMatureCrop(target);"
)
entity = entity.replace(
    "if (!mob.isAlive() || mob.getTarget() != null\n                    || mob.tickCount < nextAllowedTick || mob.tickCount < nextSearchTick) return false;",
    "if (!mob.isAlive() || mob.getTarget() != null || mob.isRepelledBySporeWard()\n                    || mob.tickCount < nextAllowedTick || mob.tickCount < nextSearchTick) return false;"
)
if "mob.isRepelledBySporeWard()" not in entity:
    raise SystemExit("Could not wire the ward into Dämmerling AI goals")
entity_path.write_text(entity, encoding="utf-8")

write("src/main/resources/assets/sporenwerk/blockstates/sporenabwehr.json", json.dumps({
    "variants": {
        "powered=false": {"model": "sporenwerk:block/sporenabwehr"},
        "powered=true": {"model": "sporenwerk:block/sporenabwehr_active"}
    }
}, ensure_ascii=False, indent=2) + "\n")
for model, texture in (("sporenabwehr", "sporenabwehr"), ("sporenabwehr_active", "sporenabwehr_active")):
    write(f"src/main/resources/assets/sporenwerk/models/block/{model}.json",
          json.dumps({"parent": "minecraft:block/cube_all",
                      "textures": {"all": f"sporenwerk:block/{texture}"}}, ensure_ascii=False, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/item/sporenabwehr.json",
      json.dumps({"parent": "sporenwerk:block/sporenabwehr"}, ensure_ascii=False, indent=2) + "\n")

texture_dir = ASSETS / "textures/block"
texture_dir.mkdir(parents=True, exist_ok=True)
def ward_texture(path, powered):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    edge = (18, 30, 34, 255)
    base = (38, 65, 69, 255)
    metal = (90, 123, 124, 255)
    glow = (81, 216, 183, 255) if powered else (74, 93, 94, 255)
    glow_hi = (202, 255, 222, 255) if powered else (129, 145, 145, 255)
    d.rectangle((0, 0, 15, 15), fill=edge)
    d.rectangle((1, 1, 14, 14), fill=base)
    d.rectangle((3, 2, 12, 3), fill=metal)
    d.rectangle((2, 5, 13, 10), fill=edge)
    d.rectangle((3, 6, 12, 9), fill=glow)
    d.rectangle((5, 4, 10, 11), outline=metal)
    d.rectangle((4, 12, 11, 13), fill=metal)
    d.rectangle((6, 14, 9, 14), fill=glow_hi)
    if powered:
        d.point((3, 4), fill=glow_hi)
        d.point((12, 4), fill=glow_hi)
        d.point((3, 11), fill=glow_hi)
        d.point((12, 11), fill=glow_hi)
    else:
        d.line((4, 7, 11, 8), fill=glow_hi)
    if any(px[3] != 255 for px in im.getdata()):
        raise SystemExit("Spore Ward world texture must be fully opaque")
    im.save(path, optimize=True)
ward_texture(texture_dir / "sporenabwehr.png", False)
ward_texture(texture_dir / "sporenabwehr_active.png", True)

write("src/main/resources/data/sporenwerk/recipes/sporenabwehr.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["IRI", "SFM", "IRI"],
  "key": {
    "I": { "item": "minecraft:iron_ingot" },
    "R": { "item": "minecraft:redstone" },
    "S": { "item": "sporenwerk:sporenresistenter_block" },
    "F": { "item": "sporenwerk:filtermoos" },
    "M": { "item": "sporenwerk:mutagene_sporen" }
  },
  "result": { "item": "sporenwerk:sporenabwehr", "count": 1 }
}
""")

translations = {
    "de_de.json": {
        "block.sporenwerk.sporenabwehr": "Sporenabwehrsender",
        "item.sporenwerk.sporenabwehr": "Sporenabwehrsender",
        "tooltip.sporenwerk.sporenabwehr.1": "Mit Redstone aktivieren. Reichweite: 8 Blöcke horizontal, 3 vertikal.",
        "tooltip.sporenwerk.sporenabwehr.2": "Hält Dämmerlinge von Mutagenblüten und Sporenwerk-Kulturen fern."
    },
    "en_us.json": {
        "block.sporenwerk.sporenabwehr": "Spore Ward Emitter",
        "item.sporenwerk.sporenabwehr": "Spore Ward Emitter",
        "tooltip.sporenwerk.sporenabwehr.1": "Power with redstone. Range: 8 blocks horizontally, 3 vertically.",
        "tooltip.sporenwerk.sporenabwehr.2": "Repels Dämmerlinge from Mutagen Blooms and Sporenwerk crops."
    }
}
for filename, additions in translations.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build_path = ROOT / "build.gradle"
build = build_path.read_text(encoding="utf-8")
build, count = re.subn(r"version\s*=\s*['\"][^'\"]+['\"]", "version = '1.18.0'", build, count=1)
if count != 1:
    raise SystemExit("Could not bump build.gradle to version 1.18.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
heading = "## Version 1.18.0 — Scanner-Warnungen und Redstone-Sporeabwehr"
section = """## Version 1.18.0 — Scanner-Warnungen und Redstone-Sporeabwehr

- **Scanner mit Handlungsempfehlungen:** Nach den Messwerten ordnet der Feldscanner die Lage ein: Mutationsstufe III, aktives Feld ohne Heilanker, Feld mit Anker, Restbefall oder keine akute Gefahr. Jede Meldung nennt einen konkreten nächsten Schritt und ist auf Deutsch und Englisch verfügbar.
- **Neue Verteidigungsanlage:** Der Sporenabwehrsender ist ein platzierbarer Block mit unterscheidbarer inaktiver/aktiver Pixeltextur und einem sichtbaren powered-Blockzustand.
- **Redstone-Steuerung:** Ein Redstone-Signal aktiviert den Sender. In 8 Blöcken horizontal und ±3 vertikal erneuert er alle 10 Ticks eine kurze Abwehrmarkierung für vorhandene Dämmerlinge.
- **Gezielte Gegenmaßnahme:** Während die Abwehr aktiv ist, brechen Dämmerlinge ihre Duftsuche nach Mutagenblüten und ihre Suche nach Sporenwerk-Kulturen ab. Der Sender erzeugt keine neuen Kreaturen und verhindert nicht den Kampf gegen Spieler.
- **Survival-Rezept:** Eisen, Redstone, Sporenresistenter Block, Filtermoos und mutagene Sporen verknüpfen die Anlage mit vorhandener Feldforschung und Ernte.
- **Qualitätssicherung:** Tests prüfen Blockzustand, Rezept, Texturdeckkraft, Redstone-Tick, Begrenzungen und beide KI-Ziele. Danach folgen Ressourcenvalidierung, Forge-Build, JAR-Prüfung und dedizierter Serverstart.

Der Server-Smoke-Test ersetzt keinen manuellen Test im laufenden Minecraft-Client.

"""
if heading not in readme:
    readme = section + readme
readme_path.write_text(readme, encoding="utf-8")
print("Installed Sporenwerk 1.18.0 redstone-powered Dämmerling ward and actionable field-scanner guidance.")
