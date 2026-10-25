#!/usr/bin/env python3
"""Extend Mutagen Bloom ecology with Crystal Stalker scent tracking and scanner diagnostics (1.54.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen Bloom ecology: " + message)


def add_import(path, anchor, import_line, label):
    source = path.read_text(encoding="utf-8")
    if import_line in source:
        return
    require(anchor in source, "could not locate import anchor for " + label)
    path.write_text(source.replace(anchor, anchor + "\n" + import_line, 1), encoding="utf-8")


# Expose only bounded, recent bloom-source counts from saved data. The scanner can use
# the same timestamp map that drives Dämmerling scent without another world-block scan.
nodes_path = SRC / "infection/MutationNodeData.java"
nodes = nodes_path.read_text(encoding="utf-8")
if "public int countRecentBlooms(" not in nodes:
    anchor = "    @Override\n    public CompoundTag save(CompoundTag tag) {"
    method = """    /**
     * Counts recent, active bloom sources in a bounded scanner volume.
     * Only the saved source map is queried; no world blocks or chunks are loaded.
     */
    public int countRecentBlooms(BlockPos center, int radius, int verticalRadius,
                                 long gameTime, long scentTicks) {
        int count = 0;
        long radiusSquared = (long) radius * radius;
        for (Map.Entry<Long, Boolean> entry : nodes.entrySet()) {
            if (!entry.getValue()) continue;
            long lastBloom = lastBlooms.getOrDefault(entry.getKey(), -24000L);
            if (lastBloom < 0L || gameTime < lastBloom || gameTime - lastBloom > scentTicks) continue;
            BlockPos candidate = BlockPos.of(entry.getKey());
            long dx = (long) candidate.getX() - center.getX();
            long dy = (long) candidate.getY() - center.getY();
            long dz = (long) candidate.getZ() - center.getZ();
            if (dx * dx + dz * dz > radiusSquared || Math.abs(dy) > verticalRadius) continue;
            count++;
        }
        return count;
    }

"""
    require(anchor in nodes, "could not locate saved-data serializer")
    nodes = nodes.replace(anchor, method + anchor, 1)
    nodes_path.write_text(nodes, encoding="utf-8")
require("public int countRecentBlooms(" in nodes,
        "saved-data bloom source counter was not installed")

# Crystal Stalkers now investigate the same temporary scent trail as Dämmerlinge.
# Existing combat targets retain priority, pathfinding must succeed, and scent-map queries
# occur at most once every 20 ticks per idle stalker.
entity_path = SRC / "entity/KristallpirscherEntity.java"
for anchor, import_line, label in (
    ("import de.sporenwerk.registry.ModBlocks;",
     "import de.sporenwerk.infection.MutationNodeData;", "saved bloom registry"),
    ("import net.minecraft.server.level.ServerLevel;",
     "import net.minecraft.world.entity.ai.goal.Goal;", "entity goal base"),
    ("import net.minecraft.world.entity.ai.goal.Goal;",
     "import java.util.EnumSet;", "goal flags"),
):
    add_import(entity_path, anchor, import_line, label)

entity = entity_path.read_text(encoding="utf-8")
if "new BloomScentGoal(this)" not in entity:
    anchor = """    public KristallpirscherEntity(EntityType<? extends Zombie> type, Level level) {
        super(type, level);
    }"""
    require(anchor in entity, "could not locate Crystal Stalker constructor")
    entity = entity.replace(anchor, anchor[:-1] +
        "        this.goalSelector.addGoal(4, new BloomScentGoal(this));\n    }", 1)
if "private static final class BloomScentGoal extends Goal" not in entity:
    anchor = "    private boolean isOnHighTierSoil() {"
    goal = """    /**
     * Investigates a recent tier-III field bloom when no combat target is active.
     * Search is throttled to every 20 ticks; the saved registry, not a block-volume scan,
     * supplies the scent position. Existing target/combat goals always take priority.
     */
    private static final class BloomScentGoal extends Goal {
        private static final int SEARCH_RADIUS = 24;
        private static final int SEARCH_INTERVAL_TICKS = 20;
        private static final long SCENT_TICKS = 2400L;
        private final KristallpirscherEntity mob;
        private BlockPos target;
        private long nextScentCheck;

        private BloomScentGoal(KristallpirscherEntity mob) {
            this.mob = mob;
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (!mob.isAlive() || mob.getTarget() != null
                    || mob.tickCount % SEARCH_INTERVAL_TICKS != 0) return false;
            target = findTarget();
            return target != null && outsideArrivalRange(target);
        }

        @Override
        public boolean canContinueToUse() {
            if (!mob.isAlive() || mob.getTarget() != null || target == null) return false;
            long now = mob.level().getGameTime();
            if (now >= nextScentCheck) {
                BlockPos refreshed = findTarget();
                nextScentCheck = now + SEARCH_INTERVAL_TICKS;
                if (refreshed == null) return false;
                target = refreshed;
            }
            return outsideArrivalRange(target);
        }

        @Override
        public void start() {
            nextScentCheck = mob.level().getGameTime() + SEARCH_INTERVAL_TICKS;
            moveToBloom();
        }

        @Override
        public void tick() {
            if (target == null) return;
            mob.getLookControl().setLookAt(target.getX() + 0.5D,
                    target.getY() + 0.5D, target.getZ() + 0.5D);
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
            return mob.distanceToSqr(bloom.getX() + 0.5D,
                    bloom.getY() + 1.0D, bloom.getZ() + 0.5D) > 9.0D;
        }

        private void moveToBloom() {
            if (target != null) {
                mob.getNavigation().moveTo(target.getX() + 0.5D,
                        target.getY() + 1.0D, target.getZ() + 0.5D, 0.92D);
            }
        }
    }

"""
    require(anchor in entity, "could not locate Crystal Stalker field predicate")
    entity = entity.replace(anchor, goal + anchor, 1)
entity_path.write_text(entity, encoding="utf-8")

# Add recent bloom scent to the EXISTING bounded handheld scanner survey. This is a count
# of recently bloomed active field sources, not a claim that every source is in line of sight.
scanner_path = SRC / "item/FeldscannerItem.java"
scanner = scanner_path.read_text(encoding="utf-8")
if "int recentBloomSources) {}" not in scanner:
    old_record = "int protectiveFilterMoss) {}"
    require(old_record in scanner, "AreaSurvey must retain the mature Filtermoos counter")
    scanner = scanner.replace(old_record, "int protectiveFilterMoss, int recentBloomSources) {}", 1)

old_return = "maxRelaySignal, maxStationSignal, nearbyPirscher, cropSpecies, symbiosisCluster, protectiveFilterMoss);"
new_return = """maxRelaySignal, maxStationSignal, nearbyPirscher, cropSpecies, symbiosisCluster,
                protectiveFilterMoss, nodeData.countRecentBlooms(origin, AREA_SCAN_RADIUS,
                        AREA_SCAN_VERTICAL_RADIUS, level.getGameTime(), 2400L));"""
if new_return not in scanner:
    require(old_return in scanner, "could not locate current AreaSurvey construction")
    scanner = scanner.replace(old_return, new_return, 1)

report_anchor = """        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.scanner.survey.filtermoos", survey.protectiveFilterMoss())
                .withStyle(survey.protectiveFilterMoss() > 0 ? ChatFormatting.GREEN : ChatFormatting.GRAY), false);"""
report_addition = report_anchor + """
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.scanner.survey.recent_blooms", survey.recentBloomSources())
                .withStyle(survey.recentBloomSources() > 0 ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.GRAY), false);"""
if report_addition not in scanner:
    require(report_anchor in scanner, "could not locate Filtermoos survey report")
    scanner = scanner.replace(report_anchor, report_addition, 1)
scanner_path.write_text(scanner, encoding="utf-8")

for locale, value in (
    ("de_de.json", "Jüngste Mutagenblüten im Messbereich (letzte 2.400 Ticks): %s. Kristallpirscher und Dämmerlinge können der Duftspur folgen."),
    ("en_us.json", "Recent Mutagen Blooms in survey area (last 2,400 ticks): %s. Crystal Stalkers and Dämmerlings may follow the scent."),
):
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data["message.sporenwerk.scanner.survey.recent_blooms"] = value
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Keep prior scanner schema contracts aligned with the appended additive field.
for test_name in ("test_mutagen_symbiosis_progression.py", "test_mutagen_symbiosis_lifecycle.py",
                  "test_multisystem_field_tools.py", "test_filtermoos_ecosystem.py"):
    path = ROOT / "tools" / test_name
    if not path.exists():
        continue
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        "int protectiveFilterMoss) {}",
        "int protectiveFilterMoss, int recentBloomSources) {}")
    # Older regression contracts express the full AreaSurvey tail as a quoted token.
    source = source.replace(
        '"int cropSpecies, boolean symbiosisCluster, int protectiveFilterMoss)"',
        '"int cropSpecies, boolean symbiosisCluster, int protectiveFilterMoss, int recentBloomSources)"')
    path.write_text(source, encoding="utf-8")

# Advance the release contract, without rewriting the historical release notes.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.53.0",
                             "Aktueller Entwicklungsstand: 1.54.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.53\.0", r"1\.54\.0")
        updated = updated.replace("artifact must be version 1.53.0",
                                  "artifact must be version 1.54.0")
    updated = updated.replace(
        '"Version 1.53.0" in readme and "Version 1.52.0" in readme',
        '"Version 1.54.0" in readme and "Version 1.53.0" in readme')
    updated = updated.replace(
        "release notes must preserve previous release history",
        "release notes must preserve previous release history")
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.54.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.54.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.54.0 — Blütenduft für den Kristallpirscher und Feldscanner

- **Kreaturenökologie:** Ein Kristallpirscher ohne aktives Kampfziel kann eine junge Mutagenblüten-Duftspur aus bis zu 24 Blöcken Entfernung untersuchen. Er nutzt denselben persistenten Quellzeitstempel wie Dämmerlinge; normale Kampfziele haben immer Vorrang.
- **Ein echtes Zeitfenster:** Duftspuren halten höchstens 2.400 Ticks. Die KI sucht nur alle 20 Ticks erneut, benötigt einen gültigen Navigationspfad und beendet die Untersuchung im Nahbereich.
- **Scanner mit Ereignisgedächtnis:** Der Feldscanner meldet nun auch, wie viele aktive Quellen im Messgebiet in den letzten 2.400 Ticks geblüht haben. Das ist eine Quellenzählung, kein Versprechen, dass ein bestimmter Gegner bereits unterwegs ist.
- **Ein gemeinsamer Datenfluss:** Kreaturen-KI und Scanner lesen den vorhandenen gespeicherten Blütenzeitpunkt. Es kommt weder ein globaler Welt-Scan noch ein zusätzlicher Entity-/Block-Ticker hinzu.
- **Qualitätssicherung:** Neue Regressionen prüfen Duft-Gültigkeit, Combat-Priorität, begrenzte Suchfrequenz, Wegfindung, Scannerfelder, DE/EN-Texte, Forge-Build, JAR und Server-Smoke-Test.

"""
if "## Version 1.54.0 — Blütenduft für den Kristallpirscher" not in readme:
    marker = "## Version 1.53.0 — Mutagenblüten melden sich im Containment-Netz"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.53.0 notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.54.0 — Blütenduft, Kristallpirscher-KI und Scannerdiagnose.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines:
    readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.54.0", 1)
else:
    readme = readme.replace(headline, headline + "\n\n## Aktueller Schwerpunkt — 1.54.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Installed 1.54.0 shared bloom-scent behavior for Kristallpirscher plus scanner scent diagnostics.")
