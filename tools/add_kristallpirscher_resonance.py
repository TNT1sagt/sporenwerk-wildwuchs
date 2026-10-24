#!/usr/bin/env python3
"""Give the Kristallpirscher a telegraphed, field-bound resonance pulse (1.33.0)."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


entity = """\
package de.sporenwerk.entity;

import de.sporenwerk.block.InfestedTerrainBlock;
import de.sporenwerk.registry.ModBlocks;
import de.sporenwerk.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
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

import java.util.List;

/**
 * High-tier Mutagen predator. Its resonance pulse is telegraphed, bounded, and
 * disabled by the Spore Filter Mask, so the fight has clear warning and counterplay.
 */
public final class KristallpirscherEntity extends Zombie {
    private static final double RESONANCE_DETECTION_RADIUS = 7.0D;
    private static final double RESONANCE_EFFECT_RADIUS_SQR = 25.0D;
    private static final int RESONANCE_WINDUP_TICKS = 30;
    private static final int RESONANCE_COOLDOWN_TICKS = 200;

    private int resonanceWindup;
    private int resonanceCooldown;

    public KristallpirscherEntity(EntityType<? extends Zombie> type, Level level) {
        super(type, level);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) return;

        if (resonanceCooldown > 0) resonanceCooldown--;
        if (!(level() instanceof ServerLevel serverLevel)) return;

        if (tickCount % 100 == 0 && isOnHighTierSoil() && getHealth() < getMaxHealth()) {
            heal(1.0F);
        }

        // Resonance exists only while the hunter stands on a strength-III Mutagen field.
        // A mask wearer does not trigger it, and is never affected by the pulse.
        if (!isOnHighTierSoil() || resonanceCooldown > 0) {
            resonanceWindup = 0;
            return;
        }
        List<Player> exposedPlayers = nearbyUnprotectedPlayers();
        if (exposedPlayers.isEmpty()) {
            resonanceWindup = 0;
            return;
        }

        if (resonanceWindup <= 0) {
            resonanceWindup = RESONANCE_WINDUP_TICKS;
            level().playSound(null, blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, 0.75F, 0.68F);
        }

        resonanceWindup--;
        if (resonanceWindup > 0) {
            if (resonanceWindup % 5 == 0) {
                // Repeated visible sparks make the 1.5-second windup readable in combat.
                serverLevel.sendParticles(ParticleTypes.END_ROD,
                        getX(), getY() + 1.0D, getZ(), 3, 0.22D, 0.28D, 0.22D, 0.01D);
            }
            return;
        }

        serverLevel.sendParticles(ParticleTypes.CRIT,
                getX(), getY() + 0.65D, getZ(), 24, 0.7D, 0.25D, 0.7D, 0.07D);
        level().playSound(null, blockPosition(), SoundEvents.BEACON_ACTIVATE,
                SoundSource.HOSTILE, 0.9F, 0.72F);

        // Recheck proximity and equipment at release: dodging or equipping a mask works.
        for (Player player : nearbyUnprotectedPlayers()) {
            if (distanceToSqr(player) <= RESONANCE_EFFECT_RADIUS_SQR) {
                player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 50, 0), this);
            }
        }
        resonanceCooldown = RESONANCE_COOLDOWN_TICKS;
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

    private List<Player> nearbyUnprotectedPlayers() {
        return level().getEntitiesOfClass(Player.class,
                getBoundingBox().inflate(RESONANCE_DETECTION_RADIUS, 3.0D, RESONANCE_DETECTION_RADIUS),
                player -> player.isAlive() && !player.isCreative() && !player.isSpectator()
                        && !isWearingSporeMask(player));
    }

    private static boolean isWearingSporeMask(Player player) {
        return player.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.SPORENFILTERMASKE.get());
    }

    private boolean isOnHighTierSoil() {
        BlockState soil = level().getBlockState(blockPosition().below());
        return soil.is(ModBlocks.MUTAGEN_BODEN.get())
                && soil.hasProperty(InfestedTerrainBlock.MUTAGEN_LEVEL)
                && soil.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL) >= 3;
    }
}
"""
write("src/main/java/de/sporenwerk/entity/KristallpirscherEntity.java", entity)

# Update the release summary and keep prior milestone notes intact.
readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.33.0 — Kristallpirscher: Resonanzimpuls mit Gegenwehr

- **Lesbare Kampftelegraphie:** Auf Mutagenboden der Stufe III lädt der Kristallpirscher einen Resonanzimpuls 30 Ticks lang auf. Amethystklang und sichtbare Endstab-Partikel kündigen die Attacke an.
- **Ausweichfenster statt Überraschungsschaden:** Erst nach der Aufladephase löst der Impuls aus; Spieler können Distanz schaffen oder eine Sporenfiltermaske aufsetzen. Der Treffer verlangsamt ungeschützte Spieler kurz, verursacht aber keinen zusätzlichen direkten Schaden.
- **Feldgebundener Rhythmus:** Die Fähigkeit funktioniert nur, solange der Gegner auf Stufe-III-Mutagenboden steht. Danach gilt eine Abklingzeit von 200 Ticks. Die bestehende langsame Regeneration im Hochmutagenfeld bleibt erhalten.
- **Serverautorität:** Aufladung, Reichweitenprüfung, Maskenprüfung und Statuseffekt laufen serverseitig. Beim Auslösen werden Reichweite und Ausrüstung erneut geprüft; das Effektradiusquadrat ist auf 5 Blöcke begrenzt.

"""
if "## Version 1.33.0 — Kristallpirscher: Resonanzimpuls" not in readme:
    marker = "## Version 1.32.0 — Kristallpirscher"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.32.0 Kristallpirscher release notes")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.32.0 — Kristallpirscher und Hochmutagen-Gegnerökologie.**",
    "**Aktueller Entwicklungsstand: 1.33.0 — telegraphierter Resonanzimpuls des Kristallpirschers.**"
).replace("## Aktueller Schwerpunkt — 1.32.0", "## Aktueller Schwerpunkt — 1.33.0")
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.33.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.33.0")
build_path.write_text(build, encoding="utf-8")
readme_path.write_text(readme, encoding="utf-8")
print("Kristallpirscher resonance pulse, 30-tick warning, mask counterplay, server-side range recheck, and 1.33.0 notes generated.")
