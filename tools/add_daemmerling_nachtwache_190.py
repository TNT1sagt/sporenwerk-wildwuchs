#!/usr/bin/env python3
"""Sporenwerk 1.90: telegraphed Dämmerling crop raids, portable lantern defense and station scouting.

Only the already-running CropThreatGoal performs the new proximity checks.
The station reports nearby Dämmerlinge only on normal interaction; no entity
tickers, biome-wide searching, chunk forcing or involuntary player penalties.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"
DATA = ROOT / "src/main/resources/data/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.90 farm-horror warning: " + message)


def patch_once(path, original, modified, label):
    old = path.read_text(encoding="utf-8")
    if modified in old:
        return
    require(old.count(original) == 1,
            label + ": expected exactly one anchor, got " + str(old.count(original)))
    path.write_text(old.replace(original, modified, 1), encoding="utf-8")


entity_path = SRC / "entity/DaemmerlingEntity.java"
entity = entity_path.read_text(encoding="utf-8")
require("private static final class WatchedStillnessGoal extends Goal" in entity
        and "private static final class CropThreatGoal extends Goal" in entity
        and "this.goalSelector.addGoal(5, new CropThreatGoal(this))" in entity,
        "1.86 gaze behavior and original crop threat must be present")

# The existing 30-tick crop nibble now warns at two predictable moments,
# and carries a lantern-rescue check only while right next to the crop.
old_chew = """            if (mob.distanceToSqr(tx, ty, tz) <= 2.4D) {
                mob.getNavigation().stop();
                if (++chewTicks >= 30) {
                    // No crop drops: this is an atmospheric threat, not a loot farm.
                    mob.level().destroyBlock(target, false, mob);
                    target = null;
                    nextAllowedTick = mob.tickCount + 100;
                }
            } else {"""
new_chew = """            if (mob.distanceToSqr(tx, ty, tz) <= 2.4D) {
                mob.getNavigation().stop();
                // Check at most once in five nearby attack ticks, never during
                // the wider crop-search scans. Held lanterns are not consumed.
                if (chewTicks % 5 == 0) {
                    Player guard = findLanternGuard(target);
                    if (guard != null) {
                        repelFromLantern(guard, target);
                        nextAllowedTick = mob.tickCount + 120;
                        target = null;
                        chewTicks = 0;
                        return;
                    }
                }
                if (chewTicks == 8 || chewTicks == 20) {
                    emitRaidWarning(target, chewTicks == 20);
                }
                if (++chewTicks >= 30) {
                    // Re-check at the actual bite: light, wards or terrain may
                    // have changed during the telegraph window.
                    if (mob.level().hasChunkAt(target)
                            && isMatureCrop(target) && !isProtected(target)) {
                        // No crop drops: atmospheric threat, not a loot farm.
                        mob.level().destroyBlock(target, false, mob);
                    }
                    target = null;
                    nextAllowedTick = mob.tickCount + 100;
                }
            } else {"""
patch_once(entity_path, old_chew, new_chew, "safe warning and rescue during crop nibble")

# All called methods are inside CropThreatGoal, and the original WatchedStillness
# AI remains untouched. Only soul lanterns are valid to make the defense a
# distinctive Sporenwerk survival technique, not a general torch exploit.
anchor = """        private void moveToTarget() {
            if (target != null) mob.getNavigation().moveTo("""
insertion = """        /**
         * Mobile crop ward: one SOUL_LANTERN in either hand, within four blocks.
         * This only cancels a crop raid; it does not remove the mob's normal
         * player combat target or alter world blocks.
         */
        private Player findLanternGuard(BlockPos cropPos) {
            for (Player nearby : mob.level().getEntitiesOfClass(Player.class,
                    new net.minecraft.world.phys.AABB(cropPos).inflate(4.0D, 2.5D, 4.0D))) {
                if (!nearby.isAlive() || nearby.isSpectator()) continue;
                if (nearby.getMainHandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)
                        || nearby.getOffhandItem().is(net.minecraft.world.item.Items.SOUL_LANTERN)) {
                    return nearby;
                }
            }
            return null;
        }

        private void repelFromLantern(Player player, BlockPos cropPos) {
            if (!(mob.level() instanceof ServerLevel level)) return;
            level.sendParticles(ParticleTypes.HAPPY_VILLAGER,
                    cropPos.getX() + 0.5D, cropPos.getY() + 0.75D,
                    cropPos.getZ() + 0.5D, 9, 0.28D, 0.32D, 0.28D, 0.015D);
            level.sendParticles(ParticleTypes.REVERSE_PORTAL,
                    mob.getX(), mob.getEyeY(), mob.getZ(),
                    8, 0.20D, 0.18D, 0.20D, 0.02D);
            level.playSound(null, cropPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, 0.42F, 1.45F);
            long now = level.getGameTime();
            long until = player.getPersistentData().getLong("SporenwerkLanternGuardUntil");
            if (now >= until || until - now > 1200L) {
                player.getPersistentData().putLong("SporenwerkLanternGuardUntil", now + 140L);
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.daemmerling.lantern_rescue"), true);
            }
            // Grant research only when a raid was genuinely stopped.
            if (player instanceof net.minecraft.server.level.ServerPlayer serverPlayer) {
                var milestone = level.getServer().getAdvancements().getAdvancement(
                        new net.minecraft.resources.ResourceLocation("sporenwerk", "nachtwache"));
                if (milestone != null) {
                    serverPlayer.getAdvancements().award(milestone, "protected_crop");
                }
            }
        }

        private void emitRaidWarning(BlockPos cropPos, boolean urgent) {
            if (!(mob.level() instanceof ServerLevel level)) return;
            double x = cropPos.getX() + 0.5D;
            double y = cropPos.getY() + 0.66D;
            double z = cropPos.getZ() + 0.5D;
            level.sendParticles(ParticleTypes.REVERSE_PORTAL,
                    x, y, z, urgent ? 13 : 7,
                    0.22D, 0.26D, 0.22D, 0.008D);
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME,
                    x, y + 0.12D, z, urgent ? 6 : 3,
                    0.24D, 0.20D, 0.24D, 0.004D);
            level.playSound(null, cropPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, urgent ? 0.62F : 0.36F,
                    urgent ? 0.45F : 0.67F);
        }

""" + anchor
patch_once(entity_path, anchor, insertion, "crop-defense methods, research and horror telegraph")

# Late safety hardening: only inspect loaded crop positions. If a target chunk
# unloads during navigation, the attack will stop without forcing it back.
mature_old = """        private boolean isMatureCrop(BlockPos pos) {
            BlockState state = mob.level().getBlockState(pos);"""
mature_new = """        private boolean isMatureCrop(BlockPos pos) {
            if (!mob.level().hasChunkAt(pos)) return false;
            BlockState state = mob.level().getBlockState(pos);"""
patch_once(entity_path, mature_old, mature_new, "loaded-chunk guard on mature crop check")
protected_old = """        private boolean isProtected(BlockPos cropPos) {
            if (mob.level().getMaxLocalRawBrightness(cropPos) >= 7) return true;
            for (BlockPos pos : BlockPos.betweenClosed(cropPos.offset(-3, -1, -3),
                    cropPos.offset(3, 1, 3))) {
                if (mob.level().getBlockState(pos).is(ModBlocks.FELDSAMMLER.get())) return true;
            }"""
protected_new = """        private boolean isProtected(BlockPos cropPos) {
            if (!mob.level().hasChunkAt(cropPos)) return true;
            if (mob.level().getMaxLocalRawBrightness(cropPos) >= 7) return true;
            for (BlockPos pos : BlockPos.betweenClosed(cropPos.offset(-3, -1, -3),
                    cropPos.offset(3, 1, 3))) {
                if (!mob.level().hasChunkAt(pos)) continue;
                if (mob.level().getBlockState(pos).is(ModBlocks.FELDSAMMLER.get())) return true;
            }"""
patch_once(entity_path, protected_old, protected_new, "cross-chunk crop-protection guard")

station_path = SRC / "block/MutagenFieldControlStationBlock.java"
station = station_path.read_text(encoding="utf-8")
require("int converted = convertSpreadToCultivation(serverLevel, pos)" in station
        and "Survey s = survey(serverLevel, pos);" in station,
        "1.89 source control and normal scan missing")
report_anchor = """        Survey s = survey(serverLevel, pos);"""
report = report_anchor + """
        // 1.90: manual nearby-creature check, NOT an always-on entity scanner.
        int lurkingDaemmerlinge = serverLevel.getEntitiesOfClass(
                de.sporenwerk.entity.DaemmerlingEntity.class,
                new net.minecraft.world.phys.AABB(pos).inflate(
                        HORIZONTAL_SCAN_RADIUS, VERTICAL_SCAN_RADIUS, HORIZONTAL_SCAN_RADIUS),
                mob -> mob.isAlive()).size();
        player.displayClientMessage(Component.translatable(
                lurkingDaemmerlinge > 0
                        ? "message.sporenwerk.fieldstation.daemmerling_alert"
                        : "message.sporenwerk.fieldstation.daemmerling_clear",
                lurkingDaemmerlinge).withStyle(
                        lurkingDaemmerlinge > 0 ? ChatFormatting.GOLD : ChatFormatting.GRAY), false);"""
patch_once(station_path, report_anchor, report, "manual Dämmerling risk audit")
station = station_path.read_text(encoding="utf-8")
require(station.count("getEntitiesOfClass(") == 1
        and "getTicker(" not in station and "getChunk(" not in station,
        "station cannot add a permanent mob scan or chunk-loading")

for locale, additions in (
    ("de_de.json", {
        "message.sporenwerk.daemmerling.lantern_rescue":
            "Das Seelenlicht vertreibt den Dämmerling vom Beet!",
        "message.sporenwerk.fieldstation.daemmerling_alert":
            "Nachtwache: %s Dämmerlinge im Stationsbereich! Reife, dunkle Beete sichern; eine Seelenlaterne in der Hand stoppt Fraßversuche.",
        "message.sporenwerk.fieldstation.daemmerling_clear":
            "Nachtwache: %s Dämmerlinge im Stationsbereich erkannt. Aktuell kein Feindkontakt.",
        "advancement.sporenwerk.nachtwache.title": "Licht gegen den Wildwuchs",
        "advancement.sporenwerk.nachtwache.description":
            "Halte bei einem echten Dämmerling-Überfall eine Seelenlaterne und rette ein reifes Beet."
    }),
    ("en_us.json", {
        "message.sporenwerk.daemmerling.lantern_rescue":
            "The soul lantern drives the Dämmerling away from the crop!",
        "message.sporenwerk.fieldstation.daemmerling_alert":
            "Night watch: %s Dämmerlinge near the station! Protect mature dark crops; hold a soul lantern to interrupt raids.",
        "message.sporenwerk.fieldstation.daemmerling_clear":
            "Night watch: %s nearby Dämmerlinge detected. No nearby contact for now.",
        "advancement.sporenwerk.nachtwache.title": "Light Against the Wildgrowth",
        "advancement.sporenwerk.nachtwache.description":
            "Save a mature field from an actual Dämmerling raid while holding a soul lantern."
    }),
):
    p = ASSETS / "lang" / locale
    lang = json.loads(p.read_text(encoding="utf-8"))
    lang.update(additions)
    p.write_text(json.dumps(lang, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

adv_path = DATA / "advancements/nachtwache.json"
adv_path.parent.mkdir(parents=True, exist_ok=True)
adv_path.write_text(json.dumps({
    "display": {
        "icon": {"item": "minecraft:soul_lantern"},
        "title": {"translate": "advancement.sporenwerk.nachtwache.title"},
        "description": {"translate": "advancement.sporenwerk.nachtwache.description"},
        "frame": "task", "show_toast": True,
        "announce_to_chat": True, "hidden": False
    },
    "criteria": {"protected_crop": {"trigger": "minecraft:impossible"}},
    "requirements": [["protected_crop"]]
}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Upgrade rolling current version expectations in existing tests.
for path in (ROOT / "tools").glob("test_*.py"):
    if path.name == "test_daemmerling_nachtwache_190.py":
        continue
    source = path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.89.0",
                             "Aktueller Entwicklungsstand: 1.90.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.89\.0", r"1\.90\.0")
        updated = updated.replace("artifact must be version 1.89.0",
                                  "artifact must be version 1.90.0")
    updated = updated.replace(
        '"Version 1.89.0" in readme and "Version 1.88.0" in readme',
        '"Version 1.90.0" in readme and "Version 1.89.0" in readme')
    if updated != source:
        path.write_text(updated, encoding="utf-8")

gradle_path = ROOT / "build.gradle"
gradle, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                        "version = '1.90.0'", gradle_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "cannot bump Gradle version")
gradle_path.write_text(gradle, encoding="utf-8")
readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
headline = "**Aktueller Entwicklungsstand: 1.89.0 — Kupfererdung für die sichere Knotenrettung.**"
require(headline in readme, "1.89 release headline missing")
readme = readme.replace(headline,
                        "**Aktueller Entwicklungsstand: 1.90.0 — Dämmerling-Nachtwache und gefährdete Felder.**", 1)
new_section = """## Aktueller Entwicklungsschritt — 1.90.0

- **Farm-Horror mit klarer Vorwarnung:** Der Dämmerling gibt beim Angriff auf ein reifes Beet zweimal aufsteigende Geistersporen und leise Kristallklänge ab, bevor der bestehende 30-Tick-Fraß endet. Erst zum tatsächlichen Biss wird der Pflanzenzustand nochmals überprüft.
- **Neue aktive Gegenwehr:** Wer innerhalb von vier Blöcken eine Seelenlaterne in Haupt- oder Nebenhand trägt, kann den bereits angefangenen Fraßversuch unterbrechen. Die Laterne wird nicht verbraucht; der Dämmerling gibt den Angriff auf das Beet für 120 Ticks auf. Spielerjagd und die übrige KI bleiben unverändert.
- **Eigenständige Forschungsbelohnung:** Die erste echte Rettung über eine getragene Seelenlaterne schaltet den Fortschritt „Licht gegen den Wildwuchs“ frei. Bloßes Halten der Laterne genügt nicht.
- **Feldstation als Nachtwache:** Der normale Kontrollstationsbericht zählt lebende Dämmerlinge im geladenen Stationsumfeld und empfiehlt bei Gefahr reife Beete zu beleuchten oder mit Seelenlicht zu schützen. Notabschaltung, Amethyst- und Kupferaktionen bleiben getrennt.
- **Sicheres und sparsames Verhalten:** Laternenprüfung nur im bestehenden CropThreatGoal und höchstens alle fünf Fraß-Ticks. Keine neuen Mob- oder Stationsticker, keine entladenen Chunks und keine neuen Weltänderungen außer der bisherigen seltenen Pflanzenbedrohung.
- **Prüfung:** Neue Regression für beide Fraßwarnungen, Lantern-Geste, Erfolgs-Advancement, Stationsmeldung, ältere KI und alle Sicherheitsgrenzen; Forge-Build, JAR und Server-Smoke-Test im Workflow.

"""
require("## Aktueller Entwicklungsschritt — 1.89.0" in readme,
        "prior current development section missing")
readme = readme.replace("## Aktueller Entwicklungsschritt — 1.89.0",
                        new_section + "## Aktueller Entwicklungsschritt — 1.89.0", 1)
release = """## Version 1.90.0 — Die Nachtwache: Dämmerling und Feld-Horror

- **Neue Horrorphase:** Zwei deutliche Sporen- und Klangwarnungen bei einer tatsächlich begonnenen Dämmerling-Fraßattacke.
- **Mobile Verteidigung:** Seelenlaterne in Haupt- oder Nebenhand, nahe beim bedrohten Beet, stoppt die Angriffsabsicht; 120 Ticks Pause vor neuer Futtersuche, ohne Inventarverbrauch.
- **Forschung, nicht bloße Dekoration:** Nur erfolgreich verhinderte Überfälle bringen den Fortschritt „Licht gegen den Wildwuchs“; die Feldkontrollstation bietet zugleich eine lokale Kreaturenwarnung.
- **Welt- und Spielerschutz:** Dunkle Farmen bleiben gefährlich, beleuchtete und geschützte Felder bleiben sicher. Die normale Monster-KI wird nicht durch einen globalen Pacifier ersetzt.
- **Technische Verträglichkeit:** Existing crops, player-facing localization, entity tick budget, saved Mutagen source registry, world-healing and three safe station gestures are preserved.

"""
require("## Version 1.89.0 —" in readme, "prior release section missing")
readme = readme.replace("## Version 1.89.0 —",
                        release + "## Version 1.89.0 —", 1)
readme_path.write_text(readme, encoding="utf-8")

print("Sporenwerk 1.90: Dämmerling farm telegraph, soul lantern rescue, night-watch advancement and station danger report integrated.")
