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
# A rare condensate is the material bridge from dangerous blooms to deployable containment.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
if "import de.sporenwerk.item.MutagenCoreCrystalItem;" not in items:
    anchor = "import de.sporenwerk.item.MutageneSporenItem;"
    if anchor not in items:
        raise SystemExit("Cannot locate MutageneSporenItem import for the bloom core")
    items = items.replace(anchor, anchor + "\\nimport de.sporenwerk.item.MutagenCoreCrystalItem;", 1)
core_anchor = '    public static final RegistryObject<Item> MUTAGENE_SPOREN = ITEMS.register("mutagene_sporen", () -> new MutageneSporenItem(new Item.Properties().stacksTo(64)));'
if "MUTAGENKERNKRISTALL" not in items:
    if core_anchor not in items:
        raise SystemExit("Cannot locate mutagen-spore item registration for core crystal")
    items = items.replace(core_anchor, core_anchor + '\\n    public static final RegistryObject<Item> MUTAGENKERNKRISTALL = ITEMS.register("mutagenkernkristall", () -> new MutagenCoreCrystalItem(new Item.Properties().stacksTo(16)));', 1)
items_path.write_text(items, encoding="utf-8")

write("src/main/java/de/sporenwerk/item/MutagenCoreCrystalItem.java", """
package de.sporenwerk.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/** Rare condensed field residue used to build a local Mutagen Bloom stabilizer. */
public final class MutagenCoreCrystalItem extends Item {
    public MutagenCoreCrystalItem(Properties properties) { super(properties); }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagenkernkristall.1").withStyle(ChatFormatting.LIGHT_PURPLE));
        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagenkernkristall.2").withStyle(ChatFormatting.GRAY));
        super.appendHoverText(stack, level, tooltip, flag);
    }
}
""")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
if "output.accept(ModItems.MUTAGENKERNKRISTALL.get());" not in creative:
    anchor = "output.accept(ModItems.MUTAGENE_SPOREN.get());"
    if anchor not in creative:
        raise SystemExit("Cannot locate Mutagen Spores creative entry for the core crystal")
    creative = creative.replace(anchor, anchor + "\\n                        output.accept(ModItems.MUTAGENKERNKRISTALL.get());", 1)
creative_path.write_text(creative, encoding="utf-8")

write("src/main/java/de/sporenwerk/infection/MutagenBloom.java", """
package de.sporenwerk.infection;

import de.sporenwerk.registry.ModBlocks;
import de.sporenwerk.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.advancements.Advancement;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.entity.item.ItemEntity;
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

        releaseHarvestableSpores(level, origin, random);
        releaseCondensedCore(level, origin, random);
        accelerateCrops(level, origin, random);
        exposeNearbyPlayers(level, origin);
    }

    /**
     * A mature bloom deposits a small, collectible sample at its source.
     * The node cooldown bounds the reward; the exposure pulse remains the cost.
     */
    private static void releaseHarvestableSpores(ServerLevel level, BlockPos origin, RandomSource random) {
        int count = random.nextFloat() < 0.20F ? 2 : 1;
        ItemStack spores = new ItemStack(ModItems.MUTAGENE_SPOREN.get(), count);
        double x = origin.getX() + 0.5D;
        double y = origin.getY() + 0.8D;
        double z = origin.getZ() + 0.5D;
        level.addFreshEntity(new ItemEntity(level, x, y, z, spores));
    }

    /** Rare collectible catalyst, bounded by the per-node bloom cooldown. */
    private static void releaseCondensedCore(ServerLevel level, BlockPos origin, RandomSource random) {
        if (random.nextFloat() >= 0.12F) return;
        ItemStack core = new ItemStack(ModItems.MUTAGENKERNKRISTALL.get());
        double x = origin.getX() + 0.72D;
        double y = origin.getY() + 0.82D;
        double z = origin.getZ() + 0.68D;
        level.addFreshEntity(new ItemEntity(level, x, y, z, core));
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

    private static void awardBloomDiscovery(Player player) {
        if (!(player instanceof ServerPlayer serverPlayer)) return;
        var server = serverPlayer.getServer();
        if (server == null) return;
        Advancement discovery = server.getAdvancements().getAdvancement(
                new ResourceLocation("sporenwerk", "first_mutagen_bloom"));
        if (discovery != null) serverPlayer.getAdvancements().award(discovery, "witness_bloom");
    }

    private static void exposeNearbyPlayers(ServerLevel level, BlockPos origin) {
        AABB bounds = new AABB(origin).inflate(MutationField.RADIUS, MutationField.INFECTION_HALF_HEIGHT, MutationField.RADIUS);
        long now = level.getGameTime();
        for (Player player : level.getEntitiesOfClass(Player.class, bounds)) {
            if (player.isCreative() || player.isSpectator()
                    || Math.abs(player.getY() - origin.getY()) > MutationField.INFECTION_HALF_HEIGHT
                    || MutationField.hasAnchor(level, player.blockPosition())) continue;

            awardBloomDiscovery(player);
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

# Witnessing a dangerous tier-3 bloom becomes a one-time survival milestone with a modest research reward.
write("src/main/resources/data/sporenwerk/advancements/first_mutagen_bloom.json", """
{
  "parent": "sporenwerk:mutagen_laboratory",
  "display": {
    "icon": { "item": "sporenwerk:mutagene_sporen" },
    "title": { "translate": "advancements.sporenwerk.first_mutagen_bloom.title" },
    "description": { "translate": "advancements.sporenwerk.first_mutagen_bloom.description" },
    "frame": "challenge",
    "show_toast": true,
    "announce_to_chat": false
  },
  "criteria": {
    "witness_bloom": { "trigger": "minecraft:impossible" }
  },
  "requirements": [["witness_bloom"]],
  "rewards": { "loot": ["sporenwerk:quests/first_mutagen_bloom"] }
}
""")
write("src/main/resources/data/sporenwerk/loot_tables/quests/first_mutagen_bloom.json", """
{
  "type": "minecraft:generic",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        { "type": "minecraft:item", "name": "sporenwerk:feldwissen", "functions": [{ "function": "minecraft:set_count", "count": 3 }] },
        { "type": "minecraft:item", "name": "sporenwerk:myzelkompost", "functions": [{ "function": "minecraft:set_count", "count": 2 }] }
      ]
    }
  ]
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


# A recent bloom leaves a bounded scent trail. Existing Dämmerlinge investigate it,
# then fall back to their mature-crop threat behavior near the field.
node_data_path = SRC / "infection/MutationNodeData.java"
node_data = node_data_path.read_text(encoding="utf-8")
if "public BlockPos nearestRecentBloom(" not in node_data:
    anchor = "    @Override\n    public CompoundTag save(CompoundTag tag) {"
    method = """
    /**
     * Finds the nearest still-fresh bloom among active sources. Only registered sources
     * are queried; this does not scan a volume of blocks or the full world.
     */
    public BlockPos nearestRecentBloom(BlockPos center, int radius, long gameTime, long scentTicks) {
        long bestDistance = Long.MAX_VALUE;
        long radiusSquared = (long) radius * radius;
        BlockPos best = null;
        for (Map.Entry<Long, Boolean> entry : nodes.entrySet()) {
            if (!entry.getValue()) continue;
            long lastBloom = lastBlooms.getOrDefault(entry.getKey(), -24000L);
            if (lastBloom < 0L || gameTime < lastBloom || gameTime - lastBloom > scentTicks) continue;
            BlockPos candidate = BlockPos.of(entry.getKey());
            long dx = (long) candidate.getX() - center.getX();
            long dy = (long) candidate.getY() - center.getY();
            long dz = (long) candidate.getZ() - center.getZ();
            if (dx * dx + dz * dz > radiusSquared || Math.abs(dy) > 8L) continue;
            long distance = dx * dx + dy * dy + dz * dz;
            if (distance < bestDistance) {
                bestDistance = distance;
                best = candidate;
            }
        }
        return best;
    }

"""
    if anchor not in node_data:
        raise SystemExit("Cannot locate MutationNodeData save method for bloom scent query")
    node_data = node_data.replace(anchor, method + anchor, 1)
node_data_path.write_text(node_data, encoding="utf-8")

entity_path = SRC / "entity/DaemmerlingEntity.java"
entity = entity_path.read_text(encoding="utf-8")
if "import de.sporenwerk.infection.MutationNodeData;" not in entity:
    anchor = "import de.sporenwerk.registry.ModBlocks;"
    if anchor not in entity:
        raise SystemExit("Cannot locate Dämmerling imports")
    entity = entity.replace(anchor, anchor + "\nimport de.sporenwerk.infection.MutationNodeData;\nimport net.minecraft.server.level.ServerLevel;", 1)
if "new BloomScentGoal(this)" not in entity:
    anchor = "        this.goalSelector.addGoal(5, new CropThreatGoal(this));"
    if anchor not in entity:
        raise SystemExit("Cannot locate Dämmerling crop-threat goal")
    entity = entity.replace(anchor, "        this.goalSelector.addGoal(4, new BloomScentGoal(this));\n" + anchor, 1)
if "private static final class BloomScentGoal extends Goal" not in entity:
    anchor = "    private static final class CropThreatGoal extends Goal {"
    goal = """
    /**
     * Briefly investigates a recently bloomed tier-3 field. The goal yields within
     * three blocks so the lower-priority crop goal can take over naturally.
     */
    private static final class BloomScentGoal extends Goal {
        private static final int SEARCH_RADIUS = 24;
        private static final long SCENT_TICKS = 2400L;
        private final DaemmerlingEntity mob;
        private BlockPos target;

        private BloomScentGoal(DaemmerlingEntity mob) {
            this.mob = mob;
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (!mob.isAlive() || mob.getTarget() != null) return false;
            target = findTarget();
            return target != null && outsideArrivalRange(target);
        }

        @Override
        public boolean canContinueToUse() {
            if (!mob.isAlive() || mob.getTarget() != null) return false;
            target = findTarget();
            return target != null && outsideArrivalRange(target);
        }

        @Override
        public void start() {
            moveToBloom();
        }

        @Override
        public void tick() {
            if (target == null) return;
            mob.getLookControl().setLookAt(target.getX() + 0.5D, target.getY() + 0.5D, target.getZ() + 0.5D);
            if (mob.getNavigation().isDone()) moveToBloom();
        }

        @Override
        public void stop() {
            mob.getNavigation().stop();
            target = null;
        }

        private BlockPos findTarget() {
            if (!(mob.level() instanceof ServerLevel serverLevel)) return null;
            BlockPos bloom = MutationNodeData.get(serverLevel).nearestRecentBloom(
                    mob.blockPosition(), SEARCH_RADIUS, serverLevel.getGameTime(), SCENT_TICKS);
            if (bloom == null || mob.getNavigation().createPath(bloom.above(), 0) == null) return null;
            return bloom;
        }

        private boolean outsideArrivalRange(BlockPos bloom) {
            return mob.distanceToSqr(bloom.getX() + 0.5D, bloom.getY() + 1.0D,
                    bloom.getZ() + 0.5D) > 9.0D;
        }

        private void moveToBloom() {
            if (target != null) {
                mob.getNavigation().moveTo(target.getX() + 0.5D, target.getY() + 1.0D,
                        target.getZ() + 0.5D, 0.78D);
            }
        }
    }

"""
    if anchor not in entity:
        raise SystemExit("Cannot locate Dämmerling crop-threat goal declaration")
    entity = entity.replace(anchor, goal + anchor, 1)
entity_path.write_text(entity, encoding="utf-8")

# Player-facing text is available in both supported languages.
translations = {
    "de_de.json": {
        "message.sporenwerk.mutagen.bloom": "MUTAGENBLÜTE! Die Feldspitze beschleunigt Pflanzen, setzt aber einen gefährlichen Expositionsimpuls frei.",
        "advancements.sporenwerk.first_mutagen_bloom.title": "Das Feld atmet",
        "advancements.sporenwerk.first_mutagen_bloom.description": "Erlebe deine erste Mutagenblüte und sichere ein Feldprotokoll."
    },
    "en_us.json": {
        "message.sporenwerk.mutagen.bloom": "MUTAGEN BLOOM! Peak field intensity accelerates crops but releases a dangerous exposure pulse.",
        "advancements.sporenwerk.first_mutagen_bloom.title": "The Field Breathes",
        "advancements.sporenwerk.first_mutagen_bloom.description": "Witness your first Mutagen Bloom and secure a field report."
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
build, count = re.subn(r"version\s*=\s*['\"][^'\"]+['\"]", "version = '1.16.0'", build, count=1)
if count != 1:
    raise SystemExit("Could not bump build.gradle to version 1.16.0")
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
    readme = section + readme

bloom_scent_heading = "## Version 1.16.0 — Dämmerling und Mutagenblüten"
bloom_scent_section = """## Version 1.16.0 — Dämmerling und Mutagenblüten

- **Feldreaktion:** Eine Mutagenblüte hinterlässt eine begrenzte Duftspur. Bereits vorhandene Dämmerlinge in bis zu 24 Blöcken Entfernung können sie untersuchen.
- **Druck auf Forschungsanlagen:** Nach der Ankunft am Feld übernimmt die bestehende KI zur Bedrohung reifer Sporenwerk-Pflanzen. Beleuchtung, Zäune und Feldsammler bleiben Gegenmaßnahmen; die Blüte erzeugt keine zusätzlichen Gegner.
- **Begrenzte KI-Arbeit:** Die Suche prüft nur die gespeicherten aktiven Feldherde und akzeptiert Blüten höchstens 2.400 Ticks lang. Der Dämmerling respektiert den Navigationspfad und kehrt im Nahbereich zur bisherigen Pflanzen-KI zurück.
- **Persistente Daten:** Der Duft basiert auf dem pro Herd gespeicherten Blütezeitpunkt; er wird nach einem Neustart nicht durch einen statischen Speicher verloren.
- **Qualitätssicherung:** Neue Vertragsprüfungen decken Suchradius, Duftzeitfenster, Wegfindung und Übergabe an die Pflanzenbedrohung ab. Danach folgen Ressourcenvalidierung, Forge-Build, JAR-Prüfung und dedizierter Serverstart.

Der Server-Smoke-Test ersetzt keinen manuellen Test im laufenden Minecraft-Client.

"""
if bloom_scent_heading not in readme:
    readme = bloom_scent_section + readme
readme_path.write_text(readme, encoding="utf-8")

print("Installed Sporenwerk 1.16.0 bloom scent and Dämmerling research-facility pressure.")
