#!/usr/bin/env python3
"""Add visible infection ambience and an area-survey mode to the field scanner."""
from pathlib import Path
import json
import re
import sys

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
                        }
                        if (particleBudget > 0 && level.random.nextFloat() < 0.05F) {
                            level.addParticle(ParticleTypes.PORTAL,
                                    pos.getX() + 0.2D + level.random.nextDouble() * 0.6D,
                                    pos.getY() + 0.8D + level.random.nextDouble() * 0.35D,
                                    pos.getZ() + 0.2D + level.random.nextDouble() * 0.6D,
                                    0.0D, 0.015D, 0.0D);
                        }
                    } else if (state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            && state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0
                            && particleBudget > 0 && level.random.nextFloat() < 0.12F) {
                        level.addParticle(ParticleTypes.WARPED_SPORE,
                                pos.getX() + 0.2D + level.random.nextDouble() * 0.6D,
                                pos.getY() + 0.5D + level.random.nextDouble() * 0.6D,
                                pos.getZ() + 0.2D + level.random.nextDouble() * 0.6D,
                                (level.random.nextDouble() - 0.5D) * 0.008D,
                                0.006D + level.random.nextDouble() * 0.01D,
                                (level.random.nextDouble() - 0.5D) * 0.008D);
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
        int activeNodes = 0, inactiveNodes = 0, infectedTerrain = 0, mutatedPlants = 0, strongestField = 0;
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
                    if (targetState.is(ModBlocks.MUTAGEN_BODEN.get())) infectedTerrain++;
                    if (targetState.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            && targetState.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0) mutatedPlants++;
                }
            }
        }
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey",
                activeNodes, inactiveNodes, infectedTerrain, mutatedPlants, strongestField)
                .withStyle(strongestField >= 3 ? ChatFormatting.LIGHT_PURPLE
                        : strongestField == 2 ? ChatFormatting.GOLD
                        : strongestField == 1 ? ChatFormatting.YELLOW : ChatFormatting.GRAY), false);
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

- **Sichtbarer Befall:** Infizierter Boden gibt schwaches Licht ab und wirbelt türkis-violette Sporenpartikel auf; mutierte Pflanzen bekommen zusätzliche Sporenmotes. Die Effekte hängen an synchronisierten Blockzuständen und verschwinden, wenn der Server den Boden zurückführt oder Pflanzen normalisiert.
- **Scanner mit zwei Modi:** Rechtsklick auf einen Block untersucht Herd, Heilanker, Barriere oder Boden. Rechtsklick in die Luft analysiert einen 12-Block-Radius und zählt aktive/inaktive Herde, befallenen Boden und mutierte Pflanzen; die Spitzenstärke stammt aus Serverdaten.
- **Release-Prüfung:** Eigener Test für Lichtlevel, Partikel-Event, Scanner-Modi und Übersetzungen, dazu Forge-Build, JAR-Validierung und Server-Smoke-Test.

Automatische CI-Tests ersetzen keinen manuellen Sichttest im Minecraft-Client.

"""
if heading not in readme:
    readme = section + readme
readme_path.write_text(readme, encoding="utf-8")
print("Added visible mutagen field ambience and scanner area survey for Sporenwerk 1.13.0.")
