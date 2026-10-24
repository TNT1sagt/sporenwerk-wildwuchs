#!/usr/bin/env python3
"""Add visible infection ambience and an area-survey mode to the field scanner."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve()
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")

# Infected soil is the physical footprint of a live infection. A low light emission
# makes it readable in caves without replacing the block's Minecraft-style texture.
blocks_path = SRC / "registry/ModBlocks.java"
blocks = blocks_path.read_text(encoding="utf-8")
old = ".strength(1.8f, 5.0f).requiresCorrectToolForDrops().sound(SoundType.FUNGUS)))"
new = ".strength(1.8f, 5.0f).lightLevel(state -> 4).requiresCorrectToolForDrops().sound(SoundType.FUNGUS)))"
if ".lightLevel(state -> 4)" not in blocks:
    if old not in blocks:
        raise SystemExit("Cannot find MUTAGEN_BODEN properties for visible field glow")
    blocks = blocks.replace(old, new, 1)
blocks_path.write_text(blocks, encoding="utf-8")

# Persist the server-authoritative field strength in the terrain block state so the
# renderer can show three unmistakable contamination stages without client guesses.
terrain_path = SRC / "block/InfestedTerrainBlock.java"
terrain = terrain_path.read_text(encoding="utf-8")
if "public static final IntegerProperty MUTAGEN_LEVEL" not in terrain:
    terrain = terrain.replace(
        "import net.minecraft.world.level.block.state.BlockState;",
        "import net.minecraft.world.level.block.state.BlockState;\n"
        "import net.minecraft.world.level.block.state.StateDefinition;\n"
        "import net.minecraft.world.level.block.state.properties.IntegerProperty;",
        1)
    terrain = terrain.replace(
        "public final class InfestedTerrainBlock extends BaseEntityBlock {\n"
        "    public InfestedTerrainBlock(Properties properties) { super(properties); }",
        "public final class InfestedTerrainBlock extends BaseEntityBlock {\n"
        "    public static final IntegerProperty MUTAGEN_LEVEL = IntegerProperty.create(\"mutagen_level\", 0, 3);\n"
        "    public InfestedTerrainBlock(Properties properties) {\n"
        "        super(properties);\n"
        "        registerDefaultState(defaultBlockState().setValue(MUTAGEN_LEVEL, 0));\n"
        "    }\n\n"
        "    @Override\n"
        "    protected void createBlockStateDefinition(StateDefinition.Builder<net.minecraft.world.level.block.Block, BlockState> builder) {\n"
        "        builder.add(MUTAGEN_LEVEL);\n"
        "    }",
        1)
    terrain = terrain.replace(
        "    public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {\n"
        "        BlockEntity blockEntity = level.getBlockEntity(pos);",
        "    public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {\n"
        "        int strength = MutationField.mutagenStrengthAt(level, pos);\n"
        "        if (state.getValue(MUTAGEN_LEVEL) != strength) {\n"
        "            level.setBlock(pos, state.setValue(MUTAGEN_LEVEL, strength), 3);\n"
        "            state = level.getBlockState(pos);\n"
        "        }\n"
        "        BlockEntity blockEntity = level.getBlockEntity(pos);",
        1)
    if "public static final IntegerProperty MUTAGEN_LEVEL" not in terrain or "MutationField.mutagenStrengthAt(level, pos)" not in terrain:
        raise SystemExit("Could not install synchronized terrain strength tiers")
    terrain_path.write_text(terrain, encoding="utf-8")

# Build dedicated block textures for each strength. The base remains recognizable, while
# higher tiers gain increasingly bright, denser veins instead of relying on particles alone.
texture_dir = ASSETS / "textures/block"
base_texture = Image.open(texture_dir / "mutagen_boden.png").convert("RGBA")
tier_styles = {
    1: ((65, 222, 170, 255), (148, 70, 210, 255)),
    2: ((255, 170, 55, 255), (225, 67, 180, 255)),
    3: ((75, 245, 255, 255), (238, 245, 255, 255)),
}
for tier, (vein, core) in tier_styles.items():
    image = base_texture.copy()
    draw = ImageDraw.Draw(image)
    if tier == 1:
        draw.line([(0, 11), (4, 8), (7, 10), (10, 6), (15, 8)], fill=vein, width=1)
        draw.point((7, 10), fill=core)
        draw.point((11, 6), fill=core)
    elif tier == 2:
        draw.line([(0, 4), (4, 7), (7, 5), (10, 9), (15, 5)], fill=vein, width=2)
        draw.line([(1, 13), (5, 11), (8, 13), (12, 11), (15, 13)], fill=core, width=1)
        for px, py in ((3, 6), (7, 5), (10, 9), (13, 6)):
            draw.rectangle((px, py, px + 1, py + 1), fill=core)
    else:
        draw.line([(0, 3), (4, 6), (7, 3), (10, 7), (15, 4)], fill=vein, width=2)
        draw.line([(0, 12), (4, 9), (7, 12), (11, 9), (15, 12)], fill=core, width=2)
        for px, py in ((2, 2), (5, 7), (8, 4), (11, 8), (14, 6), (4, 13), (9, 11), (13, 13)):
            draw.rectangle((px, py, min(15, px + 1), min(15, py + 1)), fill=core)
    image.save(texture_dir / f"mutagen_boden_strength{tier}.png", optimize=True)

blockstates_path = ASSETS / "blockstates/mutagen_boden.json"
blockstates_path.write_text(json.dumps({
    "variants": {
        f"mutagen_level={tier}": {
            "model": "sporenwerk:block/mutagen_boden" if tier == 0
                     else f"sporenwerk:block/mutagen_boden_strength{tier}"
        } for tier in range(4)
    }
}, indent=2) + "\n", encoding="utf-8")
for tier in range(1, 4):
    model_path = ASSETS / f"models/block/mutagen_boden_strength{tier}.json"
    model_path.write_text(json.dumps({
        "parent": "minecraft:block/cube_all",
        "textures": {"all": f"sporenwerk:block/mutagen_boden_strength{tier}"}
    }, indent=2) + "\n", encoding="utf-8")

# These are cosmetic client particles only, based on synchronized infected-terrain
# and crop states. No client-side code changes the world or calculates game mechanics.
write("src/main/java/de/sporenwerk/client/MutagenFieldVisuals.java", """
package de.sporenwerk.client;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.block.crop.AbstractSporeCropBlock;
import de.sporenwerk.registry.ModBlocks;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = Sporenwerk.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class MutagenFieldVisuals {
    private MutagenFieldVisuals() {}

    @SubscribeEvent
    public static void onLevelTick(TickEvent.LevelTickEvent event) {
        if (event.phase != TickEvent.Phase.END || !(event.level instanceof ClientLevel level)) return;
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.level != level || minecraft.player == null) return;
        if (level.getGameTime() % 10L != 0L) return;

        int particleBudget = 24;
        BlockPos center = minecraft.player.blockPosition();
        for (int dx = -8; dx <= 8 && particleBudget > 0; dx++) {
            for (int dz = -8; dz <= 8 && particleBudget > 0; dz++) {
                if (dx * dx + dz * dz > 64) continue;
                for (int dy = -2; dy <= 2 && particleBudget > 0; dy++) {
                    BlockPos pos = center.offset(dx, dy, dz);
                    BlockState state = level.getBlockState(pos);
                    if (state.is(ModBlocks.MUTAGEN_BODEN.get())) {
                        // A dense turquoise spore plume makes the contaminated footprint
                        // readable at a glance instead of relying on the scanner.
                        if (particleBudget > 0 && level.random.nextFloat() < 0.42F) {
                            level.addParticle(ParticleTypes.WARPED_SPORE,
                                    pos.getX() + 0.15D + level.random.nextDouble() * 0.7D,
                                    pos.getY() + 1.01D,
                                    pos.getZ() + 0.15D + level.random.nextDouble() * 0.7D,
                                    (level.random.nextDouble() - 0.5D) * 0.012D,
                                    0.008D + level.random.nextDouble() * 0.012D,
                                    (level.random.nextDouble() - 0.5D) * 0.012D);
                            particleBudget--;
                        }
                        // High-contrast cyan-blue sparks provide a second, unmistakable
                        // particle signature for Mutagen rather than ordinary ambient spores.
                        if (particleBudget > 0 && level.random.nextFloat() < 0.16F) {
                            level.addParticle(ParticleTypes.SOUL_FIRE_FLAME,
                                    pos.getX() + 0.18D + level.random.nextDouble() * 0.64D,
                                    pos.getY() + 0.88D + level.random.nextDouble() * 0.22D,
                                    pos.getZ() + 0.18D + level.random.nextDouble() * 0.64D,
                                    (level.random.nextDouble() - 0.5D) * 0.006D,
                                    0.012D + level.random.nextDouble() * 0.018D,
                                    (level.random.nextDouble() - 0.5D) * 0.006D);
                            particleBudget--;
                        }
                        if (particleBudget > 0 && level.random.nextFloat() < 0.05F) {
                            level.addParticle(ParticleTypes.PORTAL,
                                    pos.getX() + 0.2D + level.random.nextDouble() * 0.6D,
                                    pos.getY() + 0.8D + level.random.nextDouble() * 0.35D,
                                    pos.getZ() + 0.2D + level.random.nextDouble() * 0.6D,
                                    0.0D, 0.015D, 0.0D);
                            particleBudget--;
                        }
                    } else if (state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)) {
                        int mutagenLevel = state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL);
                        if (mutagenLevel > 0 && particleBudget > 0
                                && level.random.nextFloat() < 0.08F + mutagenLevel * 0.04F) {
                            level.addParticle(ParticleTypes.WARPED_SPORE,
                                    pos.getX() + 0.2D + level.random.nextDouble() * 0.6D,
                                    pos.getY() + 0.5D + level.random.nextDouble() * 0.6D,
                                    pos.getZ() + 0.2D + level.random.nextDouble() * 0.6D,
                                    (level.random.nextDouble() - 0.5D) * 0.008D,
                                    0.006D + level.random.nextDouble() * 0.01D,
                                    (level.random.nextDouble() - 0.5D) * 0.008D);
                            particleBudget--;
                        }
                        // Tier 2 gains a drifting portal shimmer; tier 3 adds bright end-rod sparks.
                        if (mutagenLevel >= 2 && particleBudget > 0 && level.random.nextFloat() < 0.10F) {
                            level.addParticle(ParticleTypes.PORTAL,
                                    pos.getX() + 0.2D + level.random.nextDouble() * 0.6D,
                                    pos.getY() + 0.55D + level.random.nextDouble() * 0.55D,
                                    pos.getZ() + 0.2D + level.random.nextDouble() * 0.6D,
                                    0.0D, 0.012D + level.random.nextDouble() * 0.01D, 0.0D);
                            particleBudget--;
                        }
                        if (mutagenLevel >= 3 && particleBudget > 0 && level.random.nextFloat() < 0.08F) {
                            level.addParticle(ParticleTypes.END_ROD,
                                    pos.getX() + 0.25D + level.random.nextDouble() * 0.5D,
                                    pos.getY() + 0.55D + level.random.nextDouble() * 0.45D,
                                    pos.getZ() + 0.25D + level.random.nextDouble() * 0.5D,
                                    (level.random.nextDouble() - 0.5D) * 0.008D,
                                    0.012D + level.random.nextDouble() * 0.018D,
                                    (level.random.nextDouble() - 0.5D) * 0.008D);
                            particleBudget--;
                        }
                    }
                }
            }
        }
    }
}
""")

# Keep block-click details and add air-click area survey to the same portable instrument.
scanner_path = SRC / "item/FeldscannerItem.java"
scanner = scanner_path.read_text(encoding="utf-8")
for imp in (
    "import de.sporenwerk.block.crop.AbstractSporeCropBlock;",
    "import net.minecraft.world.InteractionHand;",
    "import net.minecraft.world.InteractionResultHolder;"
):
    if imp not in scanner:
        anchor = "import de.sporenwerk.infection.MutationField;"
        if anchor not in scanner:
            raise SystemExit("Cannot locate Feldscanner imports")
        scanner = scanner.replace(anchor, anchor + "\n" + imp, 1)

if "public InteractionResultHolder<ItemStack> use(Level level" not in scanner:
    anchor = "    @Override\n    public InteractionResult useOn(UseOnContext context) {"
    survey = """
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(level instanceof ServerLevel serverLevel)) return InteractionResultHolder.pass(stack);

        BlockPos center = player.blockPosition();
        int activeNodes = 0, inactiveNodes = 0, infectedTerrain = 0, activeTerrain = 0, mutatedPlants = 0, strongestField = 0;
        int tier1Plants = 0, tier2Plants = 0, tier3Plants = 0, anchors = 0;
        MutationNodeData nodeData = MutationNodeData.get(serverLevel);

        // Survey only a 12-block radius and a narrow vertical slice; never scan the whole world.
        for (int dx = -12; dx <= 12; dx++) {
            for (int dz = -12; dz <= 12; dz++) {
                if (dx * dx + dz * dz > 144) continue;
                for (int dy = -4; dy <= 4; dy++) {
                    BlockPos target = center.offset(dx, dy, dz);
                    BlockState targetState = serverLevel.getBlockState(target);
                    if (targetState.is(ModBlocks.INFEKTIONSHERD.get())) {
                        if (nodeData.isActive(target)) {
                            activeNodes++;
                            strongestField = Math.max(strongestField,
                                    MutationField.mutagenStrengthAt(serverLevel, target));
                        } else {
                            inactiveNodes++;
                        }
                    }
                    if (targetState.is(ModBlocks.MUTAGEN_BODEN.get())) {
                        infectedTerrain++;
                        if (MutationField.mutagenStrengthAt(serverLevel, target) > 0) activeTerrain++;
                    }
                    if (targetState.is(ModBlocks.MUTATION_ANCHOR.get())) anchors++;
                    if (targetState.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)) {
                        int cropTier = targetState.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL);
                        if (cropTier > 0) mutatedPlants++;
                        if (cropTier == 1) tier1Plants++;
                        else if (cropTier == 2) tier2Plants++;
                        else if (cropTier == 3) tier3Plants++;
                    }
                }
            }
        }
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey",
                activeNodes, inactiveNodes, infectedTerrain, mutatedPlants, strongestField)
                .withStyle(strongestField >= 3 ? ChatFormatting.LIGHT_PURPLE
                        : strongestField == 2 ? ChatFormatting.GOLD
                        : strongestField == 1 ? ChatFormatting.YELLOW : ChatFormatting.GRAY), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey_detail",
                activeTerrain, tier1Plants, tier2Plants, tier3Plants, anchors)
                .withStyle(tier3Plants > 0 ? ChatFormatting.LIGHT_PURPLE
                        : tier2Plants > 0 ? ChatFormatting.GOLD
                        : tier1Plants > 0 ? ChatFormatting.YELLOW : ChatFormatting.AQUA), false);

        // Turn raw counts into a practical next action instead of leaving players to guess.
        String adviceKey;
        ChatFormatting adviceColor;
        if (tier3Plants > 0) {
            adviceKey = "critical";
            adviceColor = ChatFormatting.LIGHT_PURPLE;
        } else if (activeNodes > 0 && anchors == 0) {
            adviceKey = "uncontained";
            adviceColor = ChatFormatting.RED;
        } else if (activeTerrain > 0 && anchors > 0) {
            adviceKey = "anchored";
            adviceColor = ChatFormatting.GREEN;
        } else if (infectedTerrain > 0 && activeNodes == 0) {
            adviceKey = "residual";
            adviceColor = ChatFormatting.GOLD;
        } else if (activeNodes > 0) {
            adviceKey = "active";
            adviceColor = ChatFormatting.YELLOW;
        } else {
            adviceKey = "stable";
            adviceColor = ChatFormatting.GRAY;
        }
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.scanner.advice." + adviceKey).withStyle(adviceColor), false);
        return InteractionResultHolder.sidedSuccess(stack, false);
    }

"""
    if anchor not in scanner:
        raise SystemExit("Cannot locate Feldscanner block-click method")
    scanner = scanner.replace(anchor, survey + anchor, 1)
scanner_path.write_text(scanner, encoding="utf-8")

for locale, message in (
    ("de_de.json", "Feldanalyse (12 Blöcke): aktive/inaktive Herde %1$s/%2$s; verseuchter Boden %3$s; mutierte Pflanzen %4$s; Spitzenstärke %5$s/3."),
    ("en_us.json", "Field survey (12 blocks): active/inactive nodes %1$s/%2$s; infested terrain %3$s; mutated crops %4$s; peak strength %5$s/3.")
):
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data["message.sporenwerk.scanner.survey"] = message
    if locale == "de_de.json":
        data["message.sporenwerk.scanner.survey_detail"] = "Risiko-Profil: aktiver Boden %1$s; Pflanzen Stufe I/II/III %2$s/%3$s/%4$s; Heilanker %5$s."
        data.update({
            "message.sporenwerk.scanner.advice.critical": "WARNUNG: Mutationsstufe III erkannt. Filtermaske tragen und Feld sofort absichern.",
            "message.sporenwerk.scanner.advice.uncontained": "WARNUNG: Aktiver Herd ohne Heilanker im Scanbereich. Heilanker setzen oder Feld verlassen.",
            "message.sporenwerk.scanner.advice.anchored": "EINDÄMMUNG: Aktiver Boden und Heilanker erkannt. Prüfe, ob sich ihre Wirkbereiche überlappen.",
            "message.sporenwerk.scanner.advice.residual": "RESTBEFALL: Kein aktiver Herd erkannt, aber Boden bleibt befallen. Heilanker zur Wiederherstellung nutzen.",
            "message.sporenwerk.scanner.advice.active": "AKTIVES FELD: Schutzkleidung nutzen und Mutagenstärke regelmäßig prüfen.",
            "message.sporenwerk.scanner.advice.stable": "KEINE AKUTE GEFAHR ERKANNT: Im Scanbereich wurde kein aktiver Mutagenherd gefunden."
        })
    else:
        data["message.sporenwerk.scanner.survey_detail"] = "Risk profile: active terrain %1$s; crops tier I/II/III %2$s/%3$s/%4$s; healing anchors %5$s."
        data.update({
            "message.sporenwerk.scanner.advice.critical": "WARNING: Tier III mutation detected. Wear a filter mask and secure the field immediately.",
            "message.sporenwerk.scanner.advice.uncontained": "WARNING: Active node with no healing anchor in scan range. Place an anchor or leave the field.",
            "message.sporenwerk.scanner.advice.anchored": "CONTAINMENT: Active terrain and a healing anchor detected. Check that their effective areas overlap.",
            "message.sporenwerk.scanner.advice.residual": "RESIDUAL INFECTION: No active node detected, but terrain remains infected. Use a healing anchor to restore it.",
            "message.sporenwerk.scanner.advice.active": "ACTIVE FIELD: Use protective gear and monitor Mutagen strength regularly.",
            "message.sporenwerk.scanner.advice.stable": "NO IMMEDIATE THREAT DETECTED: No active Mutagen node was found in scan range."
        })
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build_path = ROOT / "build.gradle"
build = build_path.read_text(encoding="utf-8")
build, count = re.subn(r"version\s*=\s*['\"][^'\"]+['\"]", "version = '1.13.0'", build, count=1)
if count != 1:
    raise SystemExit("Could not bump build.gradle to version 1.13.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
heading = "## Version 1.13.0 — Sichtbare Mutagenfelder und Feldanalyse"
section = """## Version 1.13.0 — Sichtbare Mutagenfelder und Feldanalyse

- **Sichtbarer Befall:** Mutagenboden hat drei server-synchronisierte Stärke-Stufen mit eigenen, zunehmend hellen Texturen und Adern; seine Stufe wird aus der tatsächlichen Feldstärke aktiver Herde aktualisiert. Mutierte Pflanzen ergänzen dies mit Sporen bei Stufe 1, Portal-Schimmer ab Stufe 2 und hellen Endstab-Funken auf Stufe 3. Alle Partikeleffekte teilen sich ein festes Budget.
- **Scanner mit zwei Modi:** Rechtsklick auf einen Block untersucht Herd, Heilanker, Barriere oder Boden. Rechtsklick in die Luft analysiert einen 12-Block-Radius und meldet aktive/inaktive Herde, befallenen und aktiven Boden, Pflanzen in Mutationsstufe I/II/III sowie vorhandene Heilanker. Die Werte stammen aus Serverdaten und zeigen, ob eine Anlage Ertrag, Gefahr oder Eindämmung priorisieren sollte.
- **Release-Prüfung:** Eigener Test für Lichtlevel, Partikel-Event, Scanner-Modi und Übersetzungen, dazu Forge-Build, JAR-Validierung und Server-Smoke-Test.

Automatische CI-Tests ersetzen keinen manuellen Sichttest im Minecraft-Client.

"""
if heading not in readme:
    readme = section + readme
readme_path.write_text(readme, encoding="utf-8")
print("Added visible mutagen field ambience and scanner area survey for Sporenwerk 1.13.0.")
