#!/usr/bin/env python3
"""Add player-friendly mutation perks and controllable infection-field blocks."""
from pathlib import Path
import json, re, sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip(), encoding="utf-8")

def replace_once(rel, old, new, label):
    p = ROOT / rel
    s = p.read_text(encoding="utf-8")
    if new in s: return
    if old not in s: raise SystemExit(f"Mutation/containment patch: missing {label} in {rel}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# Dedicated registry is kept separate from existing content registration.
write("src/main/java/de/sporenwerk/infection/MutationField.java", """
package de.sporenwerk.infection;

import de.sporenwerk.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Bounded field rules. Radius is horizontal; height is deliberately bounded too. */
public final class MutationField {
    public static final int RADIUS = 8;
    public static final int HALF_HEIGHT = 12;
    private MutationField() {}

    public static boolean hasAnchor(ServerLevel level, BlockPos center) {
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int y = -HALF_HEIGHT; y <= HALF_HEIGHT; y += 3) {
            for (int x = -RADIUS; x <= RADIUS; x += 2) {
                for (int z = -RADIUS; z <= RADIUS; z += 2) {
                    if (x*x + z*z > RADIUS*RADIUS) continue;
                    cursor.set(center.getX()+x, center.getY()+y, center.getZ()+z);
                    if (level.getBlockState(cursor).is(ModBlocks.MUTATION_ANCHOR.get())) return true;
                }
            }
        }
        return false;
    }

    public static boolean hasImmuneBoundary(ServerLevel level, BlockPos pos) {
        // The special immune blocks form a physical boundary: an adjacent immune block
        // prevents a field seed from affecting blocks beyond that face.
        for (var direction : net.minecraft.core.Direction.values()) {
            if (level.getBlockState(pos.relative(direction)).is(ModBlocks.SPORENRESISTENTER_BLOCK.get())) return true;
        }
        return false;
    }

    public static void empowerNearbyCrops(ServerLevel level, BlockPos origin) {
        if (hasAnchor(level, origin)) return;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int y=-3; y<=3; y++) for (int x=-RADIUS; x<=RADIUS; x++) for (int z=-RADIUS; z<=RADIUS; z++) {
            if (x*x + z*z > RADIUS*RADIUS) continue;
            cursor.set(origin.getX()+x, origin.getY()+y, origin.getZ()+z);
            BlockState state = level.getBlockState(cursor);
            if (!(state.getBlock() instanceof CropBlock crop) || !state.isRandomlyTicking()) continue;
            if (crop.isMaxAge(state)) continue;
            // Mutagen accelerates only Sporenwerk crops; vanilla crops remain untouched.
            if (!(state.is(ModBlocks.FASERROHR.get()) || state.is(ModBlocks.BERNSTEINKAPPE.get())
                    || state.is(ModBlocks.ROTWURZEL.get()) || state.is(ModBlocks.FILTERMOOS.get()))) continue;
            if (level.random.nextFloat() < 0.20F) {
                level.setBlock(cursor, crop.getStateForAge(crop.getAge(state)+1), 2);
            }
        }
    }

    public static void healNearbyPlayers(ServerLevel level, BlockPos origin) {
        for (Player player : level.getEntitiesOfClass(Player.class,
                new net.minecraft.world.phys.AABB(origin).inflate(RADIUS, HALF_HEIGHT, RADIUS))) {
            if (Math.abs(player.getY() - origin.getY()) > HALF_HEIGHT) continue;
            if (player instanceof ServerPlayer) {
                int infection = InfectionState.level(player);
                if (infection > 0 && player.tickCount % 40 == 0) InfectionState.cure(player, 2);
            }
        }
    }

    public static boolean insideBounds(BlockPos origin, BlockPos target) {
        long dx = target.getX()-origin.getX(), dz = target.getZ()-origin.getZ();
        return dx*dx + dz*dz <= RADIUS*RADIUS
                && Math.abs(target.getY()-origin.getY()) <= HALF_HEIGHT;
    }
}
""")

write("src/main/java/de/sporenwerk/block/MutationNodeBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.infection.MutationField;
import de.sporenwerk.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** A portable seed for a deliberately bounded, farm-friendly mutagen field. */
public final class MutationNodeBlock extends Block {
    public MutationNodeBlock(Properties properties) { super(properties); }
    @Override public boolean isRandomlyTicking(BlockState state) { return true; }
    @Override public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (MutationField.hasAnchor(level, pos) || MutationField.hasImmuneBoundary(level, pos)) return;
        MutationField.empowerNearbyCrops(level, pos);
    }
}
""")

write("src/main/java/de/sporenwerk/block/MutationAnchorBlock.java", """
package de.sporenwerk.block;

import de.sporenwerk.infection.MutationField;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Creates a stable, finite healing zone: 8 blocks horizontally and 12 vertically. */
public final class MutationAnchorBlock extends Block {
    public MutationAnchorBlock(Properties properties) { super(properties); }
    @Override public boolean isRandomlyTicking(BlockState state) { return true; }
    @Override public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        MutationField.healNearbyPlayers(level, pos);
    }
}
""")

# Add registrations into the existing generated registries, which are written by the earlier pipeline.
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
"""import de.sporenwerk.block.MachineBlock;""",
"""import de.sporenwerk.block.MachineBlock;
import de.sporenwerk.block.MutationNodeBlock;
import de.sporenwerk.block.MutationAnchorBlock;""", "block imports")
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
"""    public static final RegistryObject<Block> BIOMASSE_BIOREAKTOR = machine("biomasse_bioreaktor", MapColor.COLOR_GREEN);""",
"""    public static final RegistryObject<Block> BIOMASSE_BIOREAKTOR = machine("biomasse_bioreaktor", MapColor.COLOR_GREEN);

    public static final RegistryObject<Block> INFEKTIONSHERD = BLOCKS.register("infektionsherd",
            () -> new MutationNodeBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PURPLE)
                    .strength(1.5f).randomTicks().sound(SoundType.FUNGUS)));
    public static final RegistryObject<Block> MUTATION_ANCHOR = BLOCKS.register("mutationsanker",
            () -> new MutationAnchorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(3.0f).requiresCorrectToolForDrops().randomTicks().sound(SoundType.AMETHYST)));
    public static final RegistryObject<Block> SPORENRESISTENTER_BLOCK = BLOCKS.register("sporenresistenter_block",
            () -> new Block(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE)
                    .strength(4.0f, 9.0f).requiresCorrectToolForDrops().sound(SoundType.GLASS)));""",
"block registrations")
# Each new block gets an inventory item, but only through the existing item registry.
replace_once("src/main/java/de/sporenwerk/registry/ModBlocks.java",
"""    private static RegistryObject<Block> machine(String name, MapColor color) {""",
"""    static {
        ModItems.ITEMS.register("infektionsherd", () -> new net.minecraft.world.item.BlockItem(INFEKTIONSHERD.get(), new Item.Properties()));
        ModItems.ITEMS.register("mutationsanker", () -> new net.minecraft.world.item.BlockItem(MUTATION_ANCHOR.get(), new Item.Properties()));
        ModItems.ITEMS.register("sporenresistenter_block", () -> new net.minecraft.world.item.BlockItem(SPORENRESISTENTER_BLOCK.get(), new Item.Properties()));
    }

    private static RegistryObject<Block> machine(String name, MapColor color) {""",
"block item registrations")
replace_once("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java",
"""import de.sporenwerk.registry.ModItems;""",
"""import de.sporenwerk.registry.ModItems;
import de.sporenwerk.registry.ModBlocks;""", "creative block imports")
replace_once("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java",
"""output.accept(ModItems.STERILE_CORE.get());""",
"""output.accept(ModItems.STERILE_CORE.get());
                        output.accept(ModBlocks.INFEKTIONSHERD.get());
                        output.accept(ModBlocks.MUTATION_ANCHOR.get());
                        output.accept(ModBlocks.SPORENRESISTENTER_BLOCK.get());""",
"creative catalogue")
# Client perks replace punitive weakness with benefits at clear tiers. These are bonuses, never debuffs.
events = SRC / "infection/InfectionEvents.java"
es = events.read_text(encoding="utf-8")
es = es.replace("""        if (infection >= 60) {
            player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 0, true, false, true));
        }
        if (InfectionState.surrendered(player) && infection >= 70) {
            player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 260, 0, true, false, false));
            player.addEffect(new MobEffectInstance(MobEffects.DIG_SPEED, 80, 0, true, false, true));
        }""", """        // Mutation is a progression reward, not a punishment. Serum can reverse it at any time.
        if (infection >= 20) {
            player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 260, 0, true, false, false));
        }
        if (infection >= 40) {
            player.addEffect(new MobEffectInstance(MobEffects.DIG_SPEED, 100, 0, true, false, true));
        }
        if (infection >= 60) {
            player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 100, 0, true, false, true));
        }
        if (infection >= 80) {
            player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 100, 0, true, false, true));
        }""")
events.write_text(es, encoding="utf-8")

# Portable item/block models and distinct pixel-art textures.
for item in ("infektionsherd", "mutationsanker", "sporenresistenter_block"):
    write(f"src/main/resources/assets/sporenwerk/models/item/{item}.json",
          json.dumps({"parent":"minecraft:item/generated","textures":{"layer0":f"sporenwerk:item/{item}"}}, indent=2)+"\n")
# Use explicit block models to keep the textures valid and predictable.
for block in ("infektionsherd", "mutationsanker", "sporenresistenter_block"):
    write(f"src/main/resources/assets/sporenwerk/blockstates/{block}.json",
          json.dumps({"variants":{"":{"model":f"sporenwerk:block/{block}"}}}, indent=2)+"\n")
    write(f"src/main/resources/assets/sporenwerk/models/block/{block}.json",
          json.dumps({"parent":"minecraft:block/cube_all","textures":{"all":f"sporenwerk:block/{block}"}}, indent=2)+"\n")
    write(f"src/main/resources/assets/sporenwerk/models/item/{block}.json",
          json.dumps({"parent":f"sporenwerk:block/{block}"}, indent=2)+"\n")

tex = ASSETS / "textures/block"; tex.mkdir(parents=True, exist_ok=True)
def draw_tile(name, base, accent, symbol):
    im=Image.new("RGBA",(16,16),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle((0,0,15,15),fill=base)
    for y in (1,5,10,14): d.line((0,y,15,y),fill=tuple(max(0,c-18) for c in base[:3])+(255,))
    d.polygon(symbol,fill=accent)
    im.save(tex/(name+".png"),optimize=True)
draw_tile("infektionsherd",(37,45,42,255),(171,82,190,255),[(8,1),(12,5),(10,8),(14,11),(8,15),(5,11),(7,8),(3,5)])
draw_tile("mutationsanker",(24,51,55,255),(112,230,206,255),[(8,1),(12,6),(10,8),(12,12),(8,15),(4,12),(6,8),(4,6)])
draw_tile("sporenresistenter_block",(75,103,119,255),(205,232,235,255),[(3,3),(12,3),(12,12),(3,12)])
# Block models use block textures; the inventory model must too.
for block in ("infektionsherd","mutationsanker","sporenresistenter_block"):
    write(f"src/main/resources/assets/sporenwerk/models/item/{block}.json",
          json.dumps({"parent":f"sporenwerk:block/{block}"}, indent=2)+"\n")

# Localized gameplay text, with no promise of terrain sterilization: this milestone contains a bounded field.
for filename, entries in [
 ("de_de.json", {
  "block.sporenwerk.infektionsherd":"Mutagenherd",
  "block.sporenwerk.mutationsanker":"Mutationsanker",
  "block.sporenwerk.sporenresistenter_block":"Sporenresistenter Block",
  "tooltip.sporenwerk.infektionsherd":"Beschleunigt Sporenwerk-Pflanzen in einem Radius von 8 Blöcken und ±3 Höhe.",
  "tooltip.sporenwerk.mutationsanker":"Heilt den Spieler im Radius 8; Höhe ±12. Unterdrückt Mutagenherde im selben Bereich.",
  "tooltip.sporenwerk.sporenresistenter_block":"Ein robuster Grenzbaustein für kontrollierte Versuchsanlagen.",
  "message.sporenwerk.mutation.field":"Mutagenfeld aktiv: kontrollierte Pflanzenmutation."
 }),
 ("en_us.json", {
  "block.sporenwerk.infektionsherd":"Mutagen Node",
  "block.sporenwerk.mutationsanker":"Mutation Anchor",
  "block.sporenwerk.sporenresistenter_block":"Spore-Resistant Block",
  "tooltip.sporenwerk.infektionsherd":"Accelerates Sporenwerk crops within an 8-block radius and ±3 height.",
  "tooltip.sporenwerk.mutationsanker":"Heals the player within radius 8 and ±12 height. Suppresses nearby mutagen nodes.",
  "tooltip.sporenwerk.sporenresistenter_block":"A durable boundary block for controlled test plots.",
  "message.sporenwerk.mutation.field":"Mutagen field active: controlled crop mutation."
 })
]:
    path=RES/"assets/sporenwerk/lang"/filename
    data=json.loads(path.read_text(encoding="utf-8")); data.update(entries)
    for block in ("infektionsherd","mutationsanker","sporenresistenter_block"):
        data[f"item.sporenwerk.{block}"]=entries[f"block.sporenwerk.{block}"]
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

write("tools/test_mutation_containment.py", r'''
from pathlib import Path
import json, sys
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
def read(p): return (root/p).read_text(encoding="utf-8")
def require(ok,msg):
    if not ok: raise SystemExit("Mutation/containment regression: "+msg)
state=read("src/main/java/de/sporenwerk/infection/MutationField.java")
node=read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
anchor=read("src/main/java/de/sporenwerk/block/MutationAnchorBlock.java")
events=read("src/main/java/de/sporenwerk/infection/InfectionEvents.java")
blocks=read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
require("RADIUS = 8" in state and "HALF_HEIGHT = 12" in state, "field radius and vertical bounds must be explicit")
require("hasAnchor(level, pos)" in node, "healing anchor must suppress nearby mutagen fields")
require("hasImmuneBoundary(level, pos)" in node and "SPORENRESISTENTER_BLOCK" in state, "immune boundary blocks must be recognized")
require("empowerNearbyCrops(level, pos)" in node and "crop.getStateForAge" in state, "mutagen node must have an actual farming effect")
require("healNearbyPlayers(level, pos)" in anchor and "InfectionState.cure(player, 2)" in state, "anchor must actively reduce player infection")
require("MobEffects.WEAKNESS" not in events, "mutation progression must not punish the player with weakness")
for name in ("INFEKTIONSHERD","MUTATION_ANCHOR","SPORENRESISTENTER_BLOCK"):
    require(name in blocks, name+" block registration missing")
for name in ("infektionsherd","mutationsanker","sporenresistenter_block"):
    json.loads((root/f"src/main/resources/assets/sporenwerk/blockstates/{name}.json").read_text(encoding="utf-8"))
    json.loads((root/f"src/main/resources/assets/sporenwerk/models/block/{name}.json").read_text(encoding="utf-8"))
print("Mutation perks, bounded field, anchor healing, immune-boundary, and block-resource checks passed.")
''')

# README is the player-facing contract: document precisely what exists now.
readme=ROOT/"README.md"; doc=readme.read_text(encoding="utf-8")
doc += """

## 1.4.0 — mutation fields and player agency
- Infection thresholds grant positive abilities (night vision, haste, speed, resistance); this system applies no weakness or other negative status as a price for choosing mutation.
- The Mutagen Node accelerates only Sporenwerk crops inside a bounded 8-block horizontal radius and 3-block vertical band.
- The Mutation Anchor gradually cures players in a bounded 8-block radius and 12-block vertical band, and suppresses nearby Mutagen Nodes. Serum remains available as a portable way back.
- Spore-Resistant Blocks can mark the boundary of controlled test plots. This milestone does not claim arbitrary terrain blocks are reversibly transformed; that requires state-preserving infection conversion and is a separate next milestone.
"""
readme.write_text(doc,encoding="utf-8")
build=ROOT/"build.gradle"; b=build.read_text(encoding="utf-8"); b=re.sub(r"version = '[^']+'","version = '1.4.0'",b,count=1); build.write_text(b,encoding="utf-8")
print("Installed mutation perks and bounded infection-field mechanics.")
