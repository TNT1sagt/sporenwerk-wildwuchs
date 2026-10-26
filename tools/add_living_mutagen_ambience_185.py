#!/usr/bin/env python3
"""Sporenwerk 1.85: player-local, mode-aware ambient field pulses at existing node ticks.

Spread nodes whisper at night; controlled cultivation has benign living-spore
feedback. Dormant/redstone-paused nodes emit nothing. All new effects are server
controlled, loaded-chunk safe, limited by a per-player cooldown and non-gameplay.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
NODE = SRC / "block/MutationNodeBlock.java"


def require(condition, message):
    if not condition:
        raise SystemExit("Living Mutagen Fields 1.85: " + message)


def replace_once(path, old, new, purpose):
    original = path.read_text(encoding="utf-8")
    if new in original:
        return
    require(original.count(old) == 1,
            purpose + ": expected one known source anchor; found " + str(original.count(old)))
    path.write_text(original.replace(old, new, 1), encoding="utf-8")


# Only the scheduled server-side node tick creates ambience, never random tick or
# client tick. The existing POWERED, MODE and active-node guards remain ahead of it.
tick_anchor = """        int mode = state.getValue(MODE);
        if (mode == 0) {
            MutationField.spreadFromNode(level, pos, random);
            MutagenBloom.tryTrigger(level, pos, random);"""
tick_new = """        int mode = state.getValue(MODE);
        // 1.85 atmosphere belongs to the existing active scheduled tick only.
        emitLivingFieldAmbience(level, pos, random, mode);
        if (mode == 0) {
            MutationField.spreadFromNode(level, pos, random);
            MutagenBloom.tryTrigger(level, pos, random);"""
replace_once(NODE, tick_anchor, tick_new, "active scheduled-node atmosphere hook")

# The cooldown is stored per player, not statically per JVM: works in multiplayer,
# does not leak worlds and limits overlapping nodes to a single nearby pulse.
# Preserve node modes: mode 0 is threatening at night, mode 1 peaceful day/night,
# and mode 2 (plus redstone-paused nodes) cannot reach this method.
helper_anchor = """    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }"""
helper = """    /**
     * 1.85 ambient-only Mutagen behavior. Never converts terrain, exposes players,
     * changes farm outputs or spawns mobs. The existing tick guards prevent dormant
     * and redstone-paused nodes from reaching this method.
     *
     * A player's saved next-pulse time prevents 30 adjacent nodes from generating
     * 30 separate sound and particle events in one facility.
     */
    private static void emitLivingFieldAmbience(ServerLevel level, BlockPos pos,
                                                 RandomSource random, int mode) {
        if (mode != 0 && mode != 1) return;
        long dayTime = level.getDayTime() % 24000L;
        if (mode == 0 && (dayTime < 13000L || dayTime >= 23000L)) return;
        if (random.nextInt(mode == 0 ? 9 : 20) != 0) return;
        long now = level.getGameTime();
        for (Player nearby : level.getEntitiesOfClass(Player.class,
                new AABB(pos).inflate(10.0D, 4.0D, 10.0D))) {
            if (nearby.isSpectator()) continue;
            long nextPulse = nearby.getPersistentData().getLong("SporenwerkAmbientPulseUntil");
            if (nextPulse > now && nextPulse - now < 1200L) continue;
            nearby.getPersistentData().putLong("SporenwerkAmbientPulseUntil",
                    now + (mode == 0 ? 440L : 700L));
            double x = pos.getX() + 0.5D;
            double y = pos.getY() + 0.72D;
            double z = pos.getZ() + 0.5D;
            if (mode == 0) {
                // The hostile field briefly "reaches" out as asymmetrical curling spore
                // streamers. All positions are purely visual particle coordinates.
                level.sendParticles(ParticleTypes.WARPED_SPORE,
                        x, y + 0.45D, z, 18, 1.5D, 0.45D, 1.5D, 0.018D);
                level.sendParticles(ParticleTypes.REVERSE_PORTAL,
                        x, y + 0.30D, z, 9, 1.2D, 0.30D, 1.2D, 0.008D);
                for (int i = 0; i < 8; i++) {
                    double angle = i * (Math.PI * 2.0D / 8.0D)
                            + now * 0.004D;
                    double radius = 1.2D + (i % 3) * 0.64D;
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME,
                            x + Math.cos(angle) * radius,
                            y + 0.06D + (i % 2) * 0.24D,
                            z + Math.sin(angle) * radius,
                            1, 0.0D, 0.05D, 0.0D, 0.004D);
                }
                level.playSound(null, pos, SoundEvents.RESPAWN_ANCHOR_AMBIENT,
                        SoundSource.AMBIENT, 0.30F, 0.48F + random.nextFloat() * 0.12F);
            } else {
                // Cultivation is recognizably alive, but never tries to mimic a threat.
                level.sendParticles(ParticleTypes.HAPPY_VILLAGER,
                        x, y + 0.52D, z, 8, 0.88D, 0.25D, 0.88D, 0.012D);
                level.sendParticles(ParticleTypes.WARPED_SPORE,
                        x, y + 0.38D, z, 10, 1.15D, 0.36D, 1.15D, 0.010D);
                level.sendParticles(ParticleTypes.END_ROD,
                        x, y + 0.58D, z, 4, 0.62D, 0.28D, 0.62D, 0.008D);
                level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME,
                        SoundSource.AMBIENT, 0.22F, 1.28F + random.nextFloat() * 0.18F);
            }
            // One emission per scheduled node tick, even in multiplayer groups.
            return;
        }
    }

""" + helper_anchor
replace_once(NODE, helper_anchor, helper, "bounded mode-aware atmosphere implementation")

node = NODE.read_text(encoding="utf-8")
for token in (
    "emitLivingFieldAmbience(level, pos, random, mode)",
    'getLong("SporenwerkAmbientPulseUntil")',
    "ParticleTypes.SOUL_FIRE_FLAME",
    "ParticleTypes.HAPPY_VILLAGER",
    "SoundEvents.RESPAWN_ANCHOR_AMBIENT",
):
    require(token in node, "missing node atmosphere contract: " + token)
require("getChunk(" not in node and "getChunkNow(" not in node,
        "ambient fields may not force-load chunks")

# Update active-version assertions without rewriting historical release tests.
for path in (ROOT / "tools").glob("test_*.py"):
    if path.name == "test_living_mutagen_ambience_185.py":
        continue
    before = path.read_text(encoding="utf-8")
    after = before.replace("Aktueller Entwicklungsstand: 1.84.0",
                           "Aktueller Entwicklungsstand: 1.85.0")
    if "build.gradle" in before:
        after = after.replace(r"1\.84\.0", r"1\.85\.0")
        after = after.replace("artifact must be version 1.84.0",
                              "artifact must be version 1.85.0")
    after = after.replace(
        '"Version 1.84.0" in readme and "Version 1.83.0" in readme',
        '"Version 1.85.0" in readme and "Version 1.84.0" in readme')
    if after != before:
        path.write_text(after, encoding="utf-8")

gradle = ROOT / "build.gradle"
build, n = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                   "version = '1.85.0'", gradle.read_text(encoding="utf-8"), count=1)
require(n == 1, "could not advance Forge artifact version to 1.85.0")
gradle.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.85.0

- **Lebendige Horror-Mutagenfelder:** Mutagenknoten im SPREAD-Modus können nachts selten einen flüsternden Feldimpuls abgeben. Aufsteigende Sporen, spiralig gesetzte Seelenflammen und rückwärts strömende Portalpartikel erzeugen ein unheimliches Umgebungsbild mit tiefem Resonanzton.
- **Feldwirtschaft behält ihre Identität:** CULTIVATION erzeugt stattdessen sanfte grüne Partikel, Sporen und leises Kristallklingen, ohne Spieler zu gefährden oder die sicheren Mutagen-Farmregeln zu umgehen.
- **Echte Ruhe bleibt ruhig:** DORMANT und durch Redstone pausierte Knoten bleiben vollständig still, weil die Effekte nur im bestehenden aktiven, geplanten Server-Tick auftreten.
- **Multiplayer und Leistung:** Ein gespeicherter Cooldown pro Spieler begrenzt wiederholte Impulse aus dicht nebeneinander stehenden Knoten. Der Knoten prüft die Anwesenheit von Spielern nur nach seltener Zufallsauswahl; es gibt keine zusätzliche Hintergrundtick-Logik und keine Chunk-Forceloads.
- **Integrierte Atmosphäre:** Die Effekte ergänzen die bereits unterschiedlichen Minecraft-Blockmodelle, Mutagenblüten und Feldwarngeräte. Bestehende Ausbreitungs-, Mutations-, Ernte- und Heilungsmechaniken bleiben unverändert.
- **Qualitätsprüfung:** Separate Regression prüft die aktiven Knotenmodi, Nachtbedingung, Partikel, Sounds, Multiplayer-Cooldown, Inaktivität und alte Sicherheitsregeln; kompletter Forge-Build und dedizierter Serverstart prüfen die technische Integration.

"""
if "## Aktueller Entwicklungsschritt — 1.85.0" not in readme:
    anchor = "## Aktueller Entwicklungsschritt — 1.84.0"
    require(anchor in readme, "missing 1.84 development step")
    readme = readme.replace(anchor, current + anchor, 1)
release = """## Version 1.85.0 — Lebendige Mutagenfelder bei Nacht

- **Atmosphärische Mutagenquelle:** SPREAD-Knoten können nachts ein kurzes, hörbares und sichtbares Horror-Ereignis auslösen: wirbelnde Sporen, Seelenflammen-Tendrils, Portal-Partikel und ein tiefes Summen.
- **Sanfter Kulturmodus:** CULTIVATION verwendet stattdessen freundliche Wachstums-Partikel und ein gedämpftes Amethystklingen. Die funktionale Abgrenzung von kontrollierter Farm und gefährlichem Wildfeld ist weiter auch ohne Scanner sichtbar.
- **Redstone- und Notabschaltung respektiert:** Der vorhandene aktive Knoten-Tick entscheidet über die Effekte. DORMANT-, Redstone- und inaktive Knoten lösen keine Atmosphäre aus.
- **Vorsichtige Begrenzung:** Seltene serverseitige Trigger, nur bei Spielern in unmittelbarer Nähe, pro Spieler bis zu 22/35 Sekunden Abstand und ein einziger ausgelöster Impuls pro Knotentick. Keine Spawns, Exposition, Terrainveränderung, Scannerpflicht oder zusätzlichen Chunkzugriffe.
- **Qualitätssicherung:** Neue Regression für Modusverhalten, Nachtfilter, Cooldown, Partikel und Sound, unveränderte Ausbreitung/Kultivierung und Versionsstand sowie vollständiger Forge-Build und dedizierter Serverstart. Die optische Wirkung benötigt zusätzlich einen Minecraft-Client-Sichttest.

"""
if "## Version 1.85.0 — Lebendige Mutagenfelder bei Nacht" not in readme:
    anchor = "## Version 1.84.0 —"
    require(anchor in readme, "missing 1.84 release notes")
    readme = readme.replace(anchor, release + anchor, 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.84.0 — Mutagen-Notabschaltung über die Feldkontrollstation.**",
    "**Aktueller Entwicklungsstand: 1.85.0 — lebendige Horror- und Kulturfelder mit eigenem Ambiente.**")
require("Aktueller Entwicklungsstand: 1.85.0" in readme,
        "README current version missing")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.85.0: server-side night horror pulses, benign cultivation ambience, player cooldowns and strict dormant/redstone guards.")
