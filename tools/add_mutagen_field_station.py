#!/usr/bin/env python3
"""Add the Mutagen Field Control Station with bounded, server-authoritative survey."""
from pathlib import Path
import json, re, sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve()
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")

def replace_once(rel, old, new, label):
    path = ROOT / rel
    content = path.read_text(encoding="utf-8")
    if new in content:
        return
    if old not in content:
        raise SystemExit(f"Field-station patch cannot find {label} in {rel}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")

replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
    "import de.sporenwerk.block.MutagenFieldStabilizerBlock;",
    "import de.sporenwerk.block.MutagenFieldStabilizerBlock;\nimport de.sporenwerk.block.MutagenFieldControlStationBlock;",
    "stabilizer import")
advanced = """    public static final RegistryObject<Block> MUTAGENFELD_STABILISATOR_HOCHENTWICKELT = BLOCKS.register("mutagenfeld_stabilisator_hochentwickelt",
            () -> new MutagenFieldStabilizerBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PURPLE)
                    .strength(6.0f, 15.0f).requiresCorrectToolForDrops().sound(SoundType.AMETHYST),
                    MutagenFieldStabilizerBlock.ADVANCED_RADIUS));"""
station = """    public static final RegistryObject<Block> MUTAGENFELD_KONTROLLSTATION = BLOCKS.register("mutagenfeld_kontrollstation",
            () -> new MutagenFieldControlStationBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(4.5f, 9.0f).requiresCorrectToolForDrops().sound(SoundType.AMETHYST)));"""
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java", advanced, advanced + "\n\n" + station, "advanced stabilizer")
advanced_item = '        ModItems.ITEMS.register("mutagenfeld_stabilisator_hochentwickelt", () -> new net.minecraft.world.item.BlockItem(MUTAGENFELD_STABILISATOR_HOCHENTWICKELT.get(), new Item.Properties()));'
station_item = '        ModItems.ITEMS.register("mutagenfeld_kontrollstation", () -> new net.minecraft.world.item.BlockItem(MUTAGENFELD_KONTROLLSTATION.get(), new Item.Properties()));'
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java", advanced_item, advanced_item + "\n" + station_item, "advanced stabilizer item")
creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
anchor = "output.accept(ModBlocks.MUTAGENFELD_STABILISATOR_HOCHENTWICKELT.get());"
addition = "output.accept(ModBlocks.MUTAGENFELD_KONTROLLSTATION.get());"
if addition not in creative:
    if anchor not in creative: raise SystemExit("Cannot locate advanced stabilizer in creative tab")
    creative = creative.replace(anchor, anchor + "\n                        " + addition, 1)
creative_path.write_text(creative, encoding="utf-8")

write("src/main/java/de/sporenwerk/block/MutagenFieldControlStationBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.block.crop.AbstractSporeCropBlock;
import de.sporenwerk.registry.ModBlocks;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import java.util.ArrayList;
import java.util.List;

/** On-demand field monitoring. It only reads loaded chunks and is not tick-driven. */
public final class MutagenFieldControlStationBlock extends Block {
    public static final int HORIZONTAL_SCAN_RADIUS = 16;
    public static final int VERTICAL_SCAN_RADIUS = 8;

    public MutagenFieldControlStationBlock(Properties properties) { super(properties); }

    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (!(level instanceof ServerLevel serverLevel)) return InteractionResult.CONSUME;
        Survey s = survey(serverLevel, pos);
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.header").withStyle(ChatFormatting.AQUA), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.soil", s.soil(), s.highSoil()).withStyle(ChatFormatting.LIGHT_PURPLE), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.crops", s.crops()).withStyle(ChatFormatting.GREEN), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.stabilizers", s.standard(), s.reinforced(), s.advanced()).withStyle(ChatFormatting.GOLD), false);
        if (s.networkMembers() > 0) {
            player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.network_active", s.networkMembers()).withStyle(ChatFormatting.AQUA), false);
        } else {
            player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.network_inactive").withStyle(ChatFormatting.GRAY), false);
        }
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.loaded_chunks_only").withStyle(ChatFormatting.DARK_GRAY), false);
        level.playSound(null, pos, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 0.3F, 1.35F);
        return InteractionResult.CONSUME;
    }

    private static Survey survey(ServerLevel level, BlockPos center) {
        int soil = 0, highSoil = 0, crops = 0, standard = 0, reinforced = 0, advanced = 0;
        List<BlockPos> stabilizers = new ArrayList<>();
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        int minY = Math.max(level.getMinBuildHeight(), center.getY() - VERTICAL_SCAN_RADIUS);
        int maxY = Math.min(level.getMaxBuildHeight() - 1, center.getY() + VERTICAL_SCAN_RADIUS);
        int radiusSquared = HORIZONTAL_SCAN_RADIUS * HORIZONTAL_SCAN_RADIUS;
        for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++) {
            for (int dz = -HORIZONTAL_SCAN_RADIUS; dz <= HORIZONTAL_SCAN_RADIUS; dz++) {
                if (dx * dx + dz * dz > radiusSquared) continue;
                int x = center.getX() + dx, z = center.getZ() + dz;
                if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;
                for (int y = minY; y <= maxY; y++) {
                    cursor.set(x, y, z);
                    BlockState bs = level.getBlockState(cursor);
                    if (bs.is(ModBlocks.MUTAGEN_BODEN.get())) {
                        soil++;
                        if (bs.hasProperty(InfestedTerrainBlock.MUTAGEN_LEVEL) && bs.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL) >= 3) highSoil++;
                    }
                    if (bs.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL) && bs.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0) crops++;
                    if (bs.getBlock() instanceof MutagenFieldStabilizerBlock stabilizer) {
                        if (stabilizer.protectionRadius() <= MutagenFieldStabilizerBlock.STANDARD_RADIUS) standard++;
                        else if (stabilizer.protectionRadius() <= MutagenFieldStabilizerBlock.REINFORCED_RADIUS) reinforced++;
                        else advanced++;
                        stabilizers.add(cursor.immutable());
                    }
                }
            }
        }
        int networkMembers = 0;
        for (BlockPos stabilizerPos : stabilizers) if (hasLinkedStabilizer(level, stabilizerPos)) networkMembers++;
        return new Survey(soil, highSoil, crops, standard, reinforced, advanced, networkMembers);
    }

    private static boolean hasLinkedStabilizer(ServerLevel level, BlockPos center) {
        int radius = MutagenFieldStabilizerBlock.NETWORK_LINK_RADIUS;
        int vertical = MutagenFieldStabilizerBlock.NETWORK_VERTICAL_LINK_RADIUS;
        int radiusSquared = radius * radius;
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dy = -vertical; dy <= vertical; dy++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    if (dx == 0 && dy == 0 && dz == 0 || dx * dx + dz * dz > radiusSquared) continue;
                    BlockPos probe = center.offset(dx, dy, dz);
                    if (!level.hasChunkAt(probe)) continue;
                    if (level.getBlockState(probe).getBlock() instanceof MutagenFieldStabilizerBlock) return true;
                }
            }
        }
        return false;
    }

    private record Survey(int soil, int highSoil, int crops, int standard, int reinforced, int advanced, int networkMembers) {}
}
""")

# Dedicated, opaque 16x16 block faces in a restrained industrial research style.
tex = ASSETS / "textures/block"
tex.mkdir(parents=True, exist_ok=True)
top = Image.new("RGBA", (16, 16), (26, 41, 39, 255))
d = ImageDraw.Draw(top)
d.rectangle((0,0,15,15), outline=(10,20,23,255))
d.rectangle((1,1,14,14), outline=(72,106,91,255))
d.rectangle((3,3,12,12), fill=(13,25,30,255), outline=(105,150,127,255))
d.rectangle((4,4,11,5), fill=(40,87,76,255))
d.rectangle((4,6,7,10), fill=(42,216,174,255))
d.rectangle((8,6,11,7), fill=(166,84,204,255))
d.rectangle((8,8,11,10), fill=(40,120,104,255))
d.rectangle((4,11,11,11), fill=(193,212,152,255))
for p in ((2,2),(13,2),(2,13),(13,13)): d.point(p, fill=(208,179,102,255))
top.save(tex / "mutagenfeld_kontrollstation_top.png", optimize=True)
side = Image.new("RGBA", (16,16), (29,44,42,255))
d = ImageDraw.Draw(side)
d.rectangle((0,0,15,15), outline=(10,20,23,255))
d.rectangle((1,1,14,14), fill=(38,57,52,255), outline=(92,122,94,255))
d.rectangle((2,3,13,12), fill=(17,29,33,255), outline=(65,94,81,255))
d.rectangle((3,4,12,5), fill=(74,115,92,255))
d.rectangle((3,6,5,10), fill=(37,155,128,255))
d.rectangle((6,6,7,10), fill=(20,58,54,255))
d.rectangle((8,6,12,7), fill=(123,73,155,255))
d.rectangle((8,8,12,10), fill=(38,93,80,255))
for p in ((2,2),(13,2),(2,13),(13,13)): d.point(p, fill=(204,175,98,255))
side.save(tex / "mutagenfeld_kontrollstation_side.png", optimize=True)

write("src/main/resources/assets/sporenwerk/blockstates/mutagenfeld_kontrollstation.json", json.dumps({"variants":{"":{"model":"sporenwerk:block/mutagenfeld_kontrollstation"}}}, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/block/mutagenfeld_kontrollstation.json", json.dumps({
    "parent":"minecraft:block/cube_column",
    "textures":{"end":"sporenwerk:block/mutagenfeld_kontrollstation_top","side":"sporenwerk:block/mutagenfeld_kontrollstation_side"}
}, indent=2) + "\n")
write("src/main/resources/assets/sporenwerk/models/item/mutagenfeld_kontrollstation.json", json.dumps({"parent":"sporenwerk:block/mutagenfeld_kontrollstation"}, indent=2) + "\n")
write("src/main/resources/data/sporenwerk/recipes/mutagenfeld_kontrollstation.json", """
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["ARA", "ESE", "ARA"],
  "key": {
    "A": {"item": "minecraft:amethyst_shard"},
    "R": {"item": "minecraft:redstone"},
    "E": {"item": "sporenwerk:mutagenextrakt"},
    "S": {"item": "sporenwerk:mutagenfeld_stabilisator_hochentwickelt"}
  },
  "result": {"item": "sporenwerk:mutagenfeld_kontrollstation", "count": 1}
}
""")
write("src/main/resources/data/sporenwerk/advancements/mutagen_field_station_unlock.json", """
{
  "parent": "sporenwerk:mutagen_laboratory",
  "display": {
    "icon": {"item": "sporenwerk:mutagenfeld_kontrollstation"},
    "title": {"translate": "advancements.sporenwerk.mutagen_field_station.title"},
    "description": {"translate": "advancements.sporenwerk.mutagen_field_station.description"},
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "acquire_advanced_stabilizer": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["sporenwerk:mutagenfeld_stabilisator_hochentwickelt"]}]}
    },
    "acquire_mutagen_extract": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["sporenwerk:mutagenextrakt"]}]}
    }
  },
  "requirements": [["acquire_advanced_stabilizer", "acquire_mutagen_extract"]],
  "rewards": {"recipes": ["sporenwerk:mutagenfeld_kontrollstation"]}
}
""")

locales = {
 "de_de.json": {
  "block.sporenwerk.mutagenfeld_kontrollstation":"Mutagenfeld-Kontrollstation",
  "item.sporenwerk.mutagenfeld_kontrollstation":"Mutagenfeld-Kontrollstation",
  "advancements.sporenwerk.mutagen_field_station.title":"Feldüberwachung",
  "advancements.sporenwerk.mutagen_field_station.description":"Schalte eine Kontrollstation für die Mutagen-Forschungsanlage frei.",
  "message.sporenwerk.fieldstation.header":"Mutagenfeld-Kontrolle — Scanbereich: Radius 16, Höhe ±8",
  "message.sporenwerk.fieldstation.soil":"Mutagenboden: %s Blöcke | Stärke-III-Hotspots: %s",
  "message.sporenwerk.fieldstation.crops":"Mutagenaktive Pflanzen: %s",
  "message.sporenwerk.fieldstation.stabilizers":"Stabilisatoren I / II / III: %s / %s / %s",
  "message.sporenwerk.fieldstation.network_active":"Stabilisatornetz aktiv: %s verbundene Stabilisatoren.",
  "message.sporenwerk.fieldstation.network_inactive":"Kein verbundenes Stabilisatornetz im Scanbereich.",
  "message.sporenwerk.fieldstation.loaded_chunks_only":"Nur bereits geladene Chunks werden erfasst."
 },
 "en_us.json": {
  "block.sporenwerk.mutagenfeld_kontrollstation":"Mutagen Field Control Station",
  "item.sporenwerk.mutagenfeld_kontrollstation":"Mutagen Field Control Station",
  "advancements.sporenwerk.mutagen_field_station.title":"Field Surveillance",
  "advancements.sporenwerk.mutagen_field_station.description":"Unlock a monitoring station for the Mutagen research facility.",
  "message.sporenwerk.fieldstation.header":"Mutagen Field Survey — Radius 16, height ±8",
  "message.sporenwerk.fieldstation.soil":"Mutagen soil: %s blocks | Strength-III hotspots: %s",
  "message.sporenwerk.fieldstation.crops":"Mutagen-active crops: %s",
  "message.sporenwerk.fieldstation.stabilizers":"Stabilizers I / II / III: %s / %s / %s",
  "message.sporenwerk.fieldstation.network_active":"Stabilizer network active: %s connected stabilizers.",
  "message.sporenwerk.fieldstation.network_inactive":"No linked stabilizer network in scan range.",
  "message.sporenwerk.fieldstation.loaded_chunks_only":"Only already-loaded chunks are surveyed."
 }
}
for filename, additions in locales.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
if "mutagenfeld_kontrollstation_top" not in preview:
    anchor = '    ("sporenfilterwartungstisch_side", "Filtertisch Seite"),'
    add = anchor + '\n    ("mutagenfeld_kontrollstation_top", "Mutagenstation oben"),\n    ("mutagenfeld_kontrollstation_side", "Mutagenstation Seite"),'
    if anchor not in preview: raise SystemExit("Cannot find texture anchor in art preview")
    preview_path.write_text(preview.replace(anchor, add, 1), encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]", "version = '1.26.0'", build_path.read_text(encoding="utf-8"), count=1)
if count != 1: raise SystemExit("Could not bump build.gradle to 1.26.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
heading = "## Version 1.26.0 — Mutagen-Kontrollstation"
section = """## Version 1.26.0 — Mutagen-Kontrollstation

- **Gemeinsame Forschungsstation:** Rechtsklick liefert eine Übersicht über Mutagenboden, Stärke-III-Hotspots, mutagenaktive Pflanzen sowie Stabilisatoren der Stufen I–III.
- **Netzwerkstatus:** Die Station meldet, wie viele Stabilisatoren im Scanbereich einem verbundenen Schutznetz angehören. Die Verknüpfung verwendet dieselben Reichweiten wie die Feldabschirmung.
- **Begrenzter Scan:** Die Abfrage reicht 16 Blöcke horizontal und 8 Blöcke vertikal. Es werden nur bereits geladene Chunks ausgewertet; es gibt keine dauernde Tick-Abfrage und kein erzwungenes Nachladen.
- **Forschung und Pixelgrafik:** Ein eigener Bauplan, eine Forschungsfreigabe, deutsche/englische Statusmeldungen und getrennte 16×16-Texturen für Ober- und Seitenflächen sind integriert.

Der Forge-Build und die automatisierten Ressourcenkontrakte prüfen die Integration. Ein manueller Sicht- und Funktionstest im echten Minecraft-Client bleibt erforderlich.

"""
if heading not in readme:
    marker = "## Version 1.25.0 — Vernetzte Feldstabilisierung"
    idx = readme.find(marker)
    readme = (readme[:idx] + section + readme[idx:]) if idx >= 0 else (section + readme)
readme_path.write_text(readme, encoding="utf-8")
print("Mutagen Field Control Station and version 1.26.0 generated.")
