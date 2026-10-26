#!/usr/bin/env python3
"""Sporenwerk 1.91: Dämmerling true crop-raid state, player warnings and field-station threat count."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"

def patch(path, old, new, label):
    s = path.read_text(encoding="utf-8")
    if new in s: return
    if s.count(old) != 1:
        raise SystemExit("1.91 " + label + " missing unique anchor: " + str(s.count(old)))
    path.write_text(s.replace(old, new, 1), encoding="utf-8")

mob_path = SRC / "entity/DaemmerlingEntity.java"
mob = mob_path.read_text(encoding="utf-8")
assert "private void emitRaidWarning(BlockPos cropPos, boolean urgent)" in mob

patch(mob_path, "    private static final class CropThreatGoal extends Goal {",
"""    // Server-observed state for a manual station diagnostic, never client-polled.
    private boolean raidingCrops;

    public boolean isRaidingCrops() { return this.raidingCrops; }

    private static final class CropThreatGoal extends Goal {""", "raid marker declaration")
patch(mob_path, """        public void start() {
            chewTicks = 0;
            moveToTarget();
        }""", """        public void start() {
            chewTicks = 0;
            // Walking toward a field is not yet a live crop raid.
            mob.raidingCrops = false;
            moveToTarget();
        }""", "raid start")
patch(mob_path, """            if (mob.distanceToSqr(tx, ty, tz) <= 2.4D) {
                mob.getNavigation().stop();""",
"""            if (mob.distanceToSqr(tx, ty, tz) <= 2.4D) {
                mob.getNavigation().stop();
                mob.raidingCrops = true;""", "actual crop nibble")
patch(mob_path, """            } else {
                chewTicks = 0;
                if (mob.getNavigation().isDone()) moveToTarget();
            }""",
"""            } else {
                mob.raidingCrops = false;
                chewTicks = 0;
                if (mob.getNavigation().isDone()) moveToTarget();
            }""", "approach is not actively chewing")

patch(mob_path, """        public void stop() {
            mob.getNavigation().stop();
            target = null;
            chewTicks = 0;
        }""", """        public void stop() {
            mob.getNavigation().stop();
            mob.raidingCrops = false;
            target = null;
            chewTicks = 0;
        }""", "raid stop")
patch(mob_path, """                        repelFromLantern(guard, target);
                        nextAllowedTick = mob.tickCount + 120;
                        target = null;""", """                        repelFromLantern(guard, target);
                        nextAllowedTick = mob.tickCount + 120;
                        mob.raidingCrops = false;
                        target = null;""", "lantern successful defense")
patch(mob_path, """                    target = null;
                    nextAllowedTick = mob.tickCount + 100;""", """                    mob.raidingCrops = false;
                    target = null;
                    nextAllowedTick = mob.tickCount + 100;""", "bite resolution")
patch(mob_path, """            level.playSound(null, cropPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, urgent ? 0.62F : 0.36F,
                    urgent ? 0.45F : 0.67F);
        }""",
"""            level.playSound(null, cropPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, urgent ? 0.62F : 0.36F,
                    urgent ? 0.45F : 0.67F);
            if (!urgent) {
                // Only a genuine crop raid can warn nearby players. Per-player
                // 200-tick cooldown avoids spam from multiple Dämmerlinge.
                long now = level.getGameTime();
                for (Player nearby : level.getEntitiesOfClass(Player.class,
                        new net.minecraft.world.phys.AABB(cropPos).inflate(12.0D, 4.0D, 12.0D))) {
                    if (nearby.isSpectator()) continue;
                    long until = nearby.getPersistentData().getLong("SporenwerkRaidAlertUntil");
                    if (now < until && until - now < 1200L) continue;
                    nearby.getPersistentData().putLong("SporenwerkRaidAlertUntil", now + 200L);
                    nearby.displayClientMessage(Component.translatable(
                            "message.sporenwerk.daemmerling.raid_warning"), true);
                }
            }
        }""", "nearby player warning")
station_path = SRC / "block/MutagenFieldControlStationBlock.java"
patch(station_path, """        int lurkingDaemmerlinge = serverLevel.getEntitiesOfClass(
                de.sporenwerk.entity.DaemmerlingEntity.class,
                new net.minecraft.world.phys.AABB(pos).inflate(
                        HORIZONTAL_SCAN_RADIUS, VERTICAL_SCAN_RADIUS, HORIZONTAL_SCAN_RADIUS),
                mob -> mob.isAlive()).size();""",
"""        java.util.List<de.sporenwerk.entity.DaemmerlingEntity> localDaemmerlinge =
                serverLevel.getEntitiesOfClass(
                        de.sporenwerk.entity.DaemmerlingEntity.class,
                        new net.minecraft.world.phys.AABB(pos).inflate(
                                HORIZONTAL_SCAN_RADIUS, VERTICAL_SCAN_RADIUS, HORIZONTAL_SCAN_RADIUS),
                        mob -> mob.isAlive());
        int lurkingDaemmerlinge = localDaemmerlinge.size();
        long activeRaids = localDaemmerlinge.stream().filter(
                de.sporenwerk.entity.DaemmerlingEntity::isRaidingCrops).count();""",
"one manual mob query, two threat counters")
patch(station_path, """                lurkingDaemmerlinge).withStyle(
                        lurkingDaemmerlinge > 0 ? ChatFormatting.GOLD : ChatFormatting.GRAY), false);""",
"""                lurkingDaemmerlinge).withStyle(
                        lurkingDaemmerlinge > 0 ? ChatFormatting.GOLD : ChatFormatting.GRAY), false);
        if (activeRaids > 0L) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.daemmerling_raids", activeRaids)
                    .withStyle(ChatFormatting.RED), false);
        }""", "urgent ongoing raids")
station = station_path.read_text(encoding="utf-8")
assert station.count("getEntitiesOfClass(") == 1 and "getTicker(" not in station

# Update one original 1.90 assertion to reflect list reuse without dropping coverage.
legacy = ROOT / "tools/test_daemmerling_nachtwache_190.py"
s = legacy.read_text(encoding="utf-8")
assert '    "int lurkingDaemmerlinge = serverLevel.getEntitiesOfClass(",' in s
s = s.replace('    "int lurkingDaemmerlinge = serverLevel.getEntitiesOfClass(",',
              '    "int lurkingDaemmerlinge = localDaemmerlinge.size();",', 1)
assert '    "mob -> mob.isAlive()).size();",' in s
s = s.replace('    "mob -> mob.isAlive()).size();",',
              '    "mob -> mob.isAlive());",', 1)
assert 'require(crop.count("getEntitiesOfClass(") == 1,' in s
s = s.replace('require(crop.count("getEntitiesOfClass(") == 1,',
              'require(crop.count("getEntitiesOfClass(") == 2,', 1)

assert '< report.index("int lurkingDaemmerlinge = serverLevel.getEntitiesOfClass(")' in s
s = s.replace('< report.index("int lurkingDaemmerlinge = serverLevel.getEntitiesOfClass(")',
              '< report.index("java.util.List<de.sporenwerk.entity.DaemmerlingEntity> localDaemmerlinge =")', 1)
legacy.write_text(s, encoding="utf-8")

for name, translations in (
    ("de_de.json", {
        "message.sporenwerk.colossus.arrival": "Der Boden hallt. Etwas Gewaltiges erwacht unter den Kristallen ...",
        "message.sporenwerk.daemmerling.raid_warning":
            "Etwas nagt an deinen Pflanzen! Halte eine Seelenlaterne bereit.",
        "message.sporenwerk.fieldstation.daemmerling_raids":
            "ACHTUNG: %s Dämmerlinge greifen gerade Pflanzen an. Sichere die bedrohten Felder!"
    }),
    ("en_us.json", {
        "message.sporenwerk.colossus.arrival": "The ground echoes. Something enormous stirs beneath the crystals ...",
        "message.sporenwerk.daemmerling.raid_warning":
            "Something is gnawing at your crops! Prepare a soul lantern.",
        "message.sporenwerk.fieldstation.daemmerling_raids":
            "WARNING: %s Dämmerlinge are currently raiding crops. Protect your fields!"
    }),
):
    path = ASSETS / "lang" / name
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj.update(translations)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Historical regression feature contracts stay, only active-version selectors move.
for p in (ROOT / "tools").glob("test_*.py"):
    if p.name == "test_colossus_arrival_raid_191.py": continue
    before = p.read_text(encoding="utf-8")
    after = before.replace("Aktueller Entwicklungsstand: 1.90.0",
                           "Aktueller Entwicklungsstand: 1.91.0")
    if "build.gradle" in before:
        after = after.replace(r"1\.90\.0", r"1\.91\.0")
        after = after.replace("artifact must be version 1.90.0",
                              "artifact must be version 1.91.0")
    after = after.replace('"Version 1.90.0" in readme and "Version 1.89.0" in readme',
                          '"Version 1.91.0" in readme and "Version 1.90.0" in readme')
    if after != before: p.write_text(after, encoding="utf-8")
gradle_path = ROOT / "build.gradle"
gradle, n = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                    "version = '1.91.0'", gradle_path.read_text(encoding="utf-8"), count=1)
assert n == 1
gradle_path.write_text(gradle, encoding="utf-8")
readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
old_source_headline = "**Aktueller Entwicklungsstand: 1.90.0 — Dämmerling-Nachtwache und gefährdete Felder.**"
assert old_source_headline in readme, "source README headline from the 1.90 patch changed unexpectedly"
readme = readme.replace(
    old_source_headline,
    "**Aktueller Entwicklungsstand: 1.91.0 — Koloss-Auftritt und lebendige Nachtwache.**", 1)
current = """## Aktueller Entwicklungsschritt — 1.91.0

- **Auftritt des Kristallkolosses:** Einmalig drei wachsende Kristall- und Sporenringe mit gestaffelten Klängen und lokaler Spielerwarnung; sie sind rein visuell und bleiben von schädlichen Stampfringen getrennt.
- **Gespeicherte Szene:** Jede erreichte Phase wird in der Boss-NBT gespeichert. Nach Weltneustart wiederholt sich ein vollständiger Auftritt nicht.
- **Horror an echten Farmen:** Der Dämmerling meldet einen bereits begonnenen Überfall über eine spielerbezogen gedrosselte Warnung bei der bestehenden Fraß-Vorwarnung, ohne neue KI-Scans im Leerlauf.
- **Kontrollstation warnt präzise:** Neben nahe gelegenen Kreaturen zählt der Stationsbericht tatsächliche laufende Pflanzenüberfälle aus derselben einzigen Entity-Abfrage.
- **Alte Technik bleibt:** Dämmerling-Blickkontakt, Seelenlaterne, Filtermoos, Koloss-Kernöffnung und Ausweichringe, Not-Aus, Amethystneustart und Kupfererdung bleiben unverändert.
- **Performance:** Kein zusätzlicher Dauer-Ticker, keine Chunk-Forceloads. Eigene Regression und vollständiger Forge-/Server-Build im Workflow.

"""
assert "## Aktueller Entwicklungsschritt — 1.90.0" in readme
readme = readme.replace("## Aktueller Entwicklungsschritt — 1.90.0",
                        current + "## Aktueller Entwicklungsschritt — 1.90.0", 1)
release = """## Version 1.91.0 — Kristallkoloss-Auftritt und echte Nachtwache

- Bossankunft: drei abgestufte, nicht-schädigende Ringe und Resonanzklänge mit synchronisierten Server-Partikeln; persistenter Fortschritt in der Boss-NBT.
- Farm-Horror: Frühwarnung nur bei tatsächlichem Dämmerling-Fraß, mit Spieler-Cooldown gegen Meldungsspam.
- Mehrwert der Feldstation: Ein einziger manueller Entity-Scan meldet anwesende Dämmerlinge und aktive Überfälle separat; kein periodischer Alarm.
- Bisherige Bedrohungen, schützende Gegenmaßnahmen und Forschungswege bleiben bestehen. Forge-Build, JAR-Test und Dedicated-Server-Start prüfen die Integration.

"""
assert "## Version 1.90.0 —" in readme
readme = readme.replace("## Version 1.90.0 —", release + "## Version 1.90.0 —", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.91: true raid state, bounded warning, manual station audit, localization and release metadata installed.")
