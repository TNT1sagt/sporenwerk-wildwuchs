#!/usr/bin/env python3
"""Sporenwerk 1.86: Dämmerling eye-contact reaction and measured horror counterplay.

The weak crop predator freezes for a short moment when a targeted player
truly looks at it in the dark. It then has a cooldown and can resume pursuit.
Uses an ordinary bounded Zombie AI Goal; no new mob tick, world search or
client-only damage logic.
"""
from pathlib import Path
import re
import json
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Dämmerling watched-stalk 1.86: " + message)


def insert_once(path, anchor, replacement, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return
    require(source.count(anchor) == 1,
            label + " source anchor count must be exactly 1, got " + str(source.count(anchor)))
    path.write_text(source.replace(anchor, replacement, 1), encoding="utf-8")


entity_path = SRC / "entity/DaemmerlingEntity.java"
entity = entity_path.read_text(encoding="utf-8")
imports = (
    ("import net.minecraft.network.chat.Component;", "import net.minecraft.core.BlockPos;"),
    ("import net.minecraft.core.particles.ParticleTypes;", "import net.minecraft.core.BlockPos;"),
    ("import net.minecraft.server.level.ServerLevel;", "import net.minecraft.core.BlockPos;"),
    ("import net.minecraft.sounds.SoundEvents;", "import net.minecraft.core.BlockPos;"),
    ("import net.minecraft.sounds.SoundSource;", "import net.minecraft.core.BlockPos;"),
    ("import net.minecraft.world.entity.player.Player;", "import net.minecraft.world.entity.monster.Zombie;"),
    ("import net.minecraft.world.phys.Vec3;", "import net.minecraft.world.level.Level;"),
)
for statement, anchor in imports:
    if statement not in entity:
        require(anchor in entity, "Java import location not found: " + anchor)
        entity = entity.replace(anchor, anchor + "\n" + statement, 1)
entity_path.write_text(entity, encoding="utf-8")

goal_anchor = """        super.registerGoals();
        this.goalSelector.addGoal(4, new BloomScentGoal(this));
        this.goalSelector.addGoal(5, new CropThreatGoal(this));"""
goal_new = """        super.registerGoals();
        // 1.86 staring at the Dämmerling briefly interrupts its hostile pursuit.
        // Priority one preempts Zombie melee movement but never replaces targeting.
        this.goalSelector.addGoal(1, new WatchedStillnessGoal(this));
        this.goalSelector.addGoal(4, new BloomScentGoal(this));
        this.goalSelector.addGoal(5, new CropThreatGoal(this));"""
insert_once(entity_path, goal_anchor, goal_new,
            "this.goalSelector.addGoal(1, new WatchedStillnessGoal(this))",
            "watch-oriented AI goal registration")

crop_anchor = """    private static final class CropThreatGoal extends Goal {"""
watch_goal = """    /**
     * Horror encounter / counterplay: a Dämmerling becomes unnervingly still
     * while the player looks directly into its eyes. Looking away releases it.
     *
     * A hard 30-tick cap plus a 100-tick cooldown prevents permanent stunlock.
     * It works only against its CURRENT combat target, with a true line of sight,
     * within twelve blocks and low light. Spectators and creative players do not
     * interrupt monster AI. No new paths, chunks, scans or damage are involved.
     */
    private static final class WatchedStillnessGoal extends Goal {
        private static final double MAX_WATCH_DISTANCE_SQUARED = 12.0D * 12.0D;
        private static final int MAX_FREEZE_TICKS = 30;
        private static final int RESET_COOLDOWN_TICKS = 100;
        private final DaemmerlingEntity mob;
        private Player watcher;
        private int freezeTicks;
        private int nextAllowedTick;
        private int nextSightCheck;

        private WatchedStillnessGoal(DaemmerlingEntity mob) {
            this.mob = mob;
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (mob.level().isClientSide || !mob.isAlive()
                    || mob.tickCount < nextAllowedTick || mob.tickCount < nextSightCheck) return false;
            nextSightCheck = mob.tickCount + 5;
            if (!(mob.getTarget() instanceof Player player) || !isPlayerWatching(player)) return false;
            watcher = player;
            return true;
        }

        @Override
        public boolean canContinueToUse() {
            return freezeTicks < MAX_FREEZE_TICKS && watcher != null
                    && mob.getTarget() == watcher && isPlayerWatching(watcher);
        }

        @Override
        public void start() {
            freezeTicks = 0;
            mob.getNavigation().stop();
            if (!(mob.level() instanceof ServerLevel serverLevel) || watcher == null) return;
            serverLevel.sendParticles(ParticleTypes.REVERSE_PORTAL,
                    mob.getX(), mob.getEyeY(), mob.getZ(),
                    8, 0.24D, 0.22D, 0.24D, 0.015D);
            serverLevel.playSound(null, mob.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, 0.42F, 0.50F);
            long now = serverLevel.getGameTime();
            long until = watcher.getPersistentData().getLong("SporenwerkDaemmerlingStareUntil");
            if (now >= until || until - now > 1200L) {
                watcher.getPersistentData().putLong("SporenwerkDaemmerlingStareUntil", now + 200L);
                watcher.displayClientMessage(Component.translatable(
                        "message.sporenwerk.daemmerling.stare"), true);
            }
        }

        @Override
        public void tick() {
            freezeTicks++;
            mob.getNavigation().stop();
            mob.setZza(0.0F);
            mob.setXxa(0.0F);
            if (watcher != null) {
                mob.getLookControl().setLookAt(watcher, 30.0F, 30.0F);
            }
        }

        @Override
        public void stop() {
            mob.getNavigation().stop();
            watcher = null;
            freezeTicks = 0;
            nextAllowedTick = mob.tickCount + RESET_COOLDOWN_TICKS;
        }

        private boolean isPlayerWatching(Player player) {
            if (player == null || !player.isAlive() || player.isSpectator()
                    || player.isCreative() || mob.distanceToSqr(player) > MAX_WATCH_DISTANCE_SQUARED)
                return false;
            if (mob.level().getMaxLocalRawBrightness(mob.blockPosition()) >= 8) return false;
            if (!mob.getSensing().hasLineOfSight(player)) return false;
            Vec3 towardsMob = mob.getEyePosition().subtract(player.getEyePosition());
            if (towardsMob.lengthSqr() < 1.0E-5D) return false;
            return player.getLookAngle().normalize().dot(towardsMob.normalize()) > 0.93D;
        }
    }

""" + crop_anchor
insert_once(entity_path, crop_anchor, watch_goal,
            "private static final class WatchedStillnessGoal extends Goal",
            "real eye-contact test and capped AI interruption")

entity = entity_path.read_text(encoding="utf-8")
require("this.goalSelector.addGoal(5, new CropThreatGoal(this))" in entity,
        "original crop-protection AI was unexpectedly removed")
require("getChunk(" not in entity and "getChunkNow(" not in entity,
        "Dämmerling eye-contact logic must not force-load terrain")

for locale, value in (
    ("de_de.json", "Der Dämmerling erstarrt, solange du ihn ansiehst. Doch nicht für lange ..."),
    ("en_us.json", "The Dämmerling freezes under your gaze. But not for long ..."),
):
    lang_path = ASSETS / "lang" / locale
    lang = json.loads(lang_path.read_text(encoding="utf-8"))
    lang["message.sporenwerk.daemmerling.stare"] = value
    lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Advance current-version assertions while keeping historical release contracts.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_daemmerling_watched_stillness_186.py":
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.85.0",
                             "Aktueller Entwicklungsstand: 1.86.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.85\.0", r"1\.86\.0")
        updated = updated.replace("artifact must be version 1.85.0",
                                  "artifact must be version 1.86.0")
    updated = updated.replace(
        '"Version 1.85.0" in readme and "Version 1.84.0" in readme',
        '"Version 1.86.0" in readme and "Version 1.85.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

gradle = ROOT / "build.gradle"
build, updated = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                         "version = '1.86.0'", gradle.read_text(encoding="utf-8"), count=1)
require(updated == 1, "could not set Forge version 1.86.0")
gradle.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.86.0

- **Dämmerling reagiert auf Blickkontakt:** Wer dem Dämmerling nachts im Dunkeln direkt in die Augen sieht und sein aktuelles Angriffsziel ist, kann ihn kurzzeitig zum Stehen bringen. Der Mob verfolgt den Spieler dabei mit seinem Blick statt sich auf ihn zuzubewegen.
- **Echte Gefahr nach dem Stillstand:** Spätestens nach 30 Ticks (1,5 Sekunden) endet die Starre; anschließend verhindern 100 Ticks Abklingzeit eine endlose Stilllegung durch ständigen Blickkontakt. Wegschauen beendet die Starre sofort.
- **Kein unfairer Fernstopp:** Nur Spieler im Abstand von höchstens 12 Blöcken mit echter Sichtlinie und Blickrichtung auf den Mob lösen die Reaktion aus. Kreativ- und Zuschauermodus werden ignoriert.
- **Horror-Feedback:** Ein kurzer violetter Partikelimpuls, ein tiefes Kristallklirren und eine spielerbezogen gedrosselte Aktionsleistenmeldung machen die Begegnung verständlich, ohne den Bildschirm permanent mit Text zu füllen.
- **Farm- und Kampfregeln bleiben:** Normales Zombie-Targeting, schwache Dämmerling-Schadenswerte, langsame dunkle Pflanzenangriffe, beleuchtete oder abgeschirmte Beete, Mutagenblüten und Sporenabwehr bleiben unverändert.
- **Performance und Sicherheit:** Ein priorisiertes Standard-Zombie-KI-Ziel statt eines zusätzlichen Entity-Tickers. Sichttests sind auf den aktuellen Angriffsspieler, 12 Blöcke, 5-Tick-Prüfintervalle und eine kurze Ereignisdauer begrenzt.
- **Qualität:** Regression prüft KI-Prioritäten, Dot-Product-Sichtprüfung, Zielprüfung, Timeouts, Erhaltung bestehender Ziele und DE/EN-Texte. Der vollständige Forge-Build und dedizierte Serverstart prüfen die Integration.

"""
if "## Aktueller Entwicklungsschritt — 1.86.0" not in readme:
    anchor = "## Aktueller Entwicklungsschritt — 1.85.0"
    require(anchor in readme, "previous current development section missing")
    readme = readme.replace(anchor, current + anchor, 1)
release = """## Version 1.86.0 — Dämmerling: Starr vor Angst oder auf der Lauer?

- **Eigenständiges Monsterverhalten:** Der Dämmerling bricht seine Jagd kurz ab, wenn sein aktuelles Ziel ihn im Dunkeln direkt anschaut. Sobald der Spieler den Blick abwendet, setzt die Verfolgung wieder ein.
- **Begrenzte Ausweichmechanik:** Maximal 30 Ticks Starre, dann 100 Ticks Immunität gegen den Effekt. Keine ständige Unterbrechung durch Spieler, die die Kreatur ununterbrochen fixieren.
- **Faire Sichtprüfung:** Zwölf Blöcke Reichweite, echte Sichtlinie, normiertes Blickrichtungs-Skalarprodukt größer als 0,93, lebende Survival-Spieler und niedrige Umgebungshelligkeit.
- **Unheimliches Feedback:** Ein Partikelimpuls, gedämpftes Amethystgeräusch und selten eingeblendeter Aktionstext vermitteln, dass die Kreatur den Blick wahrnimmt.
- **Bestehende Systeme intakt:** Das vorherige CropThreatGoal bleibt auf Priorität 5, Zombie-Angriff und vorhandene Ernte-/Schutzlogik bleiben im Code. Keine neuen Spawnregeln, Chunk-Forceloads oder dauerhaft laufenden Umweltabfragen.
- **Qualitätsnachweis:** Eigenständige Regression zu Blickkontakt, Cooldown, KI-Interaktion, vorhandenen Pflanzenregeln und Übersetzungen sowie Forge-Kompilierung und dedizierter Serverstart. Eine visuelle Client-Kontrolle steht weiterhin aus.

"""
if "## Version 1.86.0 — Dämmerling: Starr vor Angst oder auf der Lauer?" not in readme:
    anchor = "## Version 1.85.0 —"
    require(anchor in readme, "previous 1.85 release notes missing")
    readme = readme.replace(anchor, release + anchor, 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.85.0 — lebendige Horror- und Kulturfelder mit eigenem Ambiente.**",
    "**Aktueller Entwicklungsstand: 1.86.0 — Dämmerling mit dynamischem Blickkontakt-Verhalten.**")
require("Aktueller Entwicklungsstand: 1.86.0" in readme,
        "README headline missing 1.86.0")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.86.0: true-gaze, line-of-sight Dämmerling pause with cooldown, horror feedback and preserved crop behaviour.")
