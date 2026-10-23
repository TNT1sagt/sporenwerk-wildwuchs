#!/usr/bin/env python3
"""Add a persistent high-intensity Mutagen Bloom event with counterplay."""
from pathlib import Path
import json, re, sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")

# Persist the last bloom per source. A cooldown must survive save/reload and must not
# be stored in a static JVM map (which would break multiplayer and dimension isolation).
nodes_path = SRC / "infection/MutationNodeData.java"
nodes = nodes_path.read_text(encoding="utf-8")
if "private final Map<Long, Long> lastBlooms" not in nodes:
    anchor = "    private final Map<Long, Boolean> nodes = new LinkedHashMap<>();"
    if anchor not in nodes:
        raise SystemExit("Cannot locate persistent Mutagen Node registry")
    nodes = nodes.replace(anchor, anchor + "\n    private final Map<Long, Long> lastBlooms = new LinkedHashMap<>();", 1)
if 'data.lastBlooms.put(entry.getLong("Pos")' not in nodes:
    anchor = '            data.nodes.put(entry.getLong("Pos"), entry.getBoolean("Active"));'
    if anchor not in nodes:
        raise SystemExit("Cannot locate Mutagen Node saved-data loader")
    nodes = nodes.replace(anchor, anchor + '\n            data.lastBlooms.put(entry.getLong("Pos"), entry.contains("LastBloom") ? entry.getLong("LastBloom") : -24000L);', 1)
old_unregister = """    public void unregister(BlockPos pos) {
        if (nodes.remove(pos.asLong()) != null) setDirty();
    }"""
new_unregister = """    public void unregister(BlockPos pos) {
        boolean changed = nodes.remove(pos.asLong()) != null;
        changed |= lastBlooms.remove(pos.asLong()) != null;
        if (changed) setDirty();
    }"""
if new_unregister not in nodes:
    if old_unregister not in nodes:
        raise SystemExit("Cannot locate Mutagen Node unregister method")
    nodes = nodes.replace(old_unregister, new_unregister, 1)
if "public boolean claimBloom(BlockPos pos, long gameTime, long cooldownTicks)" not in nodes:
    anchor = "    @Override\n    public CompoundTag save(CompoundTag tag) {"
    method = """    /** Atomically claims a per-node bloom window, persisting it with the node registry. */
    public boolean claimBloom(BlockPos pos, long gameTime, long cooldownTicks) {
        long packed = pos.asLong();
        if (!isActive(pos)) return false;
        long last = lastBlooms.getOrDefault(packed, -cooldownTicks);
        if (gameTime - last < cooldownTicks) return false;
        lastBlooms.put(packed, gameTime);
        setDirty();
        return true;
    }

"""
    if anchor not in nodes:
        raise SystemExit("Cannot locate Mutagen Node save method")
    nodes = nodes.replace(anchor, method + anchor, 1)
if 'value.putLong("LastBloom"' not in nodes:
    anchor = '            value.putBoolean("Active", entry.getValue());'
    if anchor not in nodes:
        raise SystemExit("Cannot locate Mutagen Node saved-data serializer")
    nodes = nodes.replace(anchor, anchor + '\n            value.putLong("LastBloom", lastBlooms.getOrDefault(entry.getKey(), -24000L));', 1)
nodes_path.write_text(nodes, encoding="utf-8")

# The event is server authoritative. It rewards carefully managed tier-3 farms with crop growth,
# warns nearby players, and lets the existing filter mask intercept its exposure pulse.
write("src/main/java/de/sporenwerk/infection/MutagenBloom.java", """
package de.sporenwerk.infection;

import de.sporenwerk.registry.ModBlocks;
import de.sporenwerk.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

/** Periodic reward/risk event for the strongest active field tier. */
public final class MutagenBloom {
    public static final long COOLDOWN_TICKS = 12000L;
    private MutagenBloom() {}

    public static void tryTrigger(ServerLevel level, BlockPos origin, RandomSource random) {
        if (MutationField.mutagenStrengthAt(level, origin) < 3) return;
        if (!MutationNodeData.get(level).claimBloom(origin, level.getGameTime(), COOLDOWN_TICKS)) return;

        double x = origin.getX() + 0.5D;
        double y = origin.getY() + 0.9D;
        double z = origin.getZ() + 0.5D;
        level.sendParticles(ParticleTypes.WARPED_SPORE, x, y, z, 48, 1.3D, 0.45D, 1.3D, 0.035D);
        level.sendParticles(ParticleTypes.PORTAL, x, y, z, 20, 0.8D, 0.7D, 0.8D, 0.09D);

        accelerateCrops(level, origin, random);
        exposeNearbyPlayers(level, origin);
    }

    private static void accelerateCrops(ServerLevel level, BlockPos origin, RandomSource random) {
        int advanced = 0;
        for (int attempt = 0; attempt < 32 && advanced < 6; attempt++) {
            int dx = random.nextInt(MutationField.RADIUS * 2 + 1) - MutationField.RADIUS;
            int dz = random.nextInt(MutationField.RADIUS * 2 + 1) - MutationField.RADIUS;
            int dy = random.nextInt(7) - 3;
            if (dx * dx + dz * dz > MutationField.RADIUS * MutationField.RADIUS) continue;
            BlockPos target = origin.offset(dx, dy, dz);
            BlockState state = level.getBlockState(target);
            if (!(state.getBlock() instanceof CropBlock crop) || crop.isMaxAge(state)) continue;
            if (!(state.is(ModBlocks.FASERROHR.get()) || state.is(ModBlocks.BERNSTEINKAPPE.get())
                    || state.is(ModBlocks.ROTWURZEL.get()) || state.is(ModBlocks.FILTERMOOS.get()))) continue;
            if (random.nextFloat() < 0.65F) {
                level.setBlock(target, crop.getStateForAge(crop.getAge(state) + 1), 2);
                advanced++;
            }
        }
    }

    private static void exposeNearbyPlayers(ServerLevel level, BlockPos origin) {
        AABB bounds = new AABB(origin).inflate(MutationField.RADIUS, MutationField.INFECTION_HALF_HEIGHT, MutationField.RADIUS);
        long now = level.getGameTime();
        for (Player player : level.getEntitiesOfClass(Player.class, bounds)) {
            if (player.isCreative() || player.isSpectator()
                    || Math.abs(player.getY() - origin.getY()) > MutationField.INFECTION_HALF_HEIGHT
                    || MutationField.hasAnchor(level, player.blockPosition())) continue;

            player.displayClientMessage(Component.translatable("message.sporenwerk.mutagen.bloom")
                    .withStyle(ChatFormatting.LIGHT_PURPLE), false);
            ItemStack mask = player.getItemBySlot(EquipmentSlot.HEAD);
            if (mask.is(ModItems.SPORENFILTERMASKE.get())) {
                mask.hurtAndBreak(1, player, entity -> entity.broadcastBreakEvent(EquipmentSlot.HEAD));
                player.getPersistentData().putLong("SporenwerkControlledExposureAt", now + 300L);
            } else {
                InfectionState.setLevel(player, InfectionState.level(player) + 1);
                player.getPersistentData().putLong("SporenwerkControlledExposureAt", now + 100L);
            }
        }
    }
}
""")

# Invoke from the scheduled server tick. The persistent cooldown keeps one node from
# triggering on every tick and survives unloads/restarts.
node_path = SRC / "block/MutationNodeBlock.java"
node = node_path.read_text(encoding="utf-8")
if "import de.sporenwerk.infection.MutagenBloom;" not in node:
    anchor = "import de.sporenwerk.infection.MutationField;"
    if anchor not in node:
        raise SystemExit("Cannot locate MutationNodeBlock infection imports")
    node = node.replace(anchor, anchor + "\nimport de.sporenwerk.infection.MutagenBloom;", 1)
call = "MutagenBloom.tryTrigger(level, pos, random);"
if call not in node:
    anchor = "            MutationField.spreadFromNode(level, pos, random);"
    if anchor not in node:
        raise SystemExit("Cannot locate active Mutation Node scheduled-tick hook")
    node = node.replace(anchor, anchor + "\n            " + call, 1)
node_path.write_text(node, encoding="utf-8")

# Player-facing text is available in both supported languages.
translations = {
    "de_de.json": {
        "message.sporenwerk.mutagen.bloom": "MUTAGENBLÜTE! Die Feldspitze beschleunigt Pflanzen, setzt aber einen gefährlichen Expositionsimpuls frei."
    },
    "en_us.json": {
        "message.sporenwerk.mutagen.bloom": "MUTAGEN BLOOM! Peak field intensity accelerates crops but releases a dangerous exposure pulse."
    }
}
for filename, additions in translations.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Bump the produced artifact version after all earlier milestone generators have run.
build_path = ROOT / "build.gradle"
build = build_path.read_text(encoding="utf-8")
build, count = re.subn(r"version\s*=\s*['\"][^'\"]+['\"]", "version = '1.15.0'", build, count=1)
if count != 1:
    raise SystemExit("Could not bump build.gradle to version 1.15.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
heading = "## Version 1.15.0 — Mutagenblüte und Feldüberlastung"
section = """## Version 1.15.0 — Mutagenblüte und Feldüberlastung

- **Ereignis statt Dauergefahr:** Ein aktiver Feldherd kann nur bei Stärke 3 eine Mutagenblüte auslösen. Sie erzeugt sichtbare Sporen-/Portalpartikel und beschleunigt bis zu sechs nahe Sporenwerk-Pflanzen.
- **Risiko mit Gegenmaßnahme:** Spieler im Expositionsbereich erhalten einen zusätzlichen Infektionsimpuls. Die Sporenfiltermaske fängt diesen Puls ab und verliert Haltbarkeit; Heilanker schützen ihren Bereich weiterhin.
- **Serverautorität und Persistenz:** Jeder Herd besitzt einen gespeicherten Cooldown von 12.000 Ticks. Der Zeitstempel wird zusammen mit den pro Dimension gespeicherten Quellpositionen geladen/gespeichert; es gibt keine statischen globalen Timer und keine Client-gesteuerten Spielregeln.
- **Begrenzte Arbeit:** Ein Ereignis prüft höchstens 32 Pflanzenpositionen und verändert höchstens sechs passende Sporenwerk-Pflanzen. Die Effekte bleiben im Radius 8 und Höhenband ±3.
- **Qualitätssicherung:** Regressionen prüfen Stärkeschwelle, Persistenz, Cooldown, Schutzmaske, Anker, Wachstumslimit und deutsche/englische Texte; danach folgen JSON-/Texturprüfung, Forge-Build, JAR-Prüfung und dedizierter Serverstart.

Der automatische Server-Smoke-Test ersetzt keinen manuellen Test im laufenden Minecraft-Client.

"""
if heading not in readme:
    readme_path.write_text(section + readme, encoding="utf-8")
print("Installed persistent tier-3 Mutagen Bloom events and their mask/anchor counterplay.")
