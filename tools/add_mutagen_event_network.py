#!/usr/bin/env python3
"""Add bounded event-driven cache refresh for the Mutagen Containment Relay (1.44.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen event-driven containment network: " + message)


def insert_once(path, anchor, addition, label):
    content = path.read_text(encoding="utf-8")
    if anchor + addition in content:
        return
    require(anchor in content, "could not locate " + label)
    path.write_text(content.replace(anchor, anchor + addition, 1), encoding="utf-8")


# One source event refreshes nearby cached relays, prioritizing nearer horizontal
# rings and inspecting loaded chunks only. A hard per-event cap protects servers
# from a deliberately dense relay array; no ticker or recursive relay broadcast exists.
relay_path = SRC / "block/MutagenContainmentRelayBlock.java"
relay = relay_path.read_text(encoding="utf-8")
old_constant = "    public static final int VERTICAL_SCAN_RADIUS = 8;"
new_constant = old_constant + "\n    public static final int MAX_REFRESHED_RELAYS_PER_EVENT = 32;"
if new_constant not in relay:
    require(old_constant in relay, "could not locate relay scan radius constants")
    relay = relay.replace(old_constant, new_constant, 1)

method_anchor = "    private static boolean isRelevantInput(Block block) {"
method = """    /**
     * Refresh cached relay outputs after a real station/siren/ward/dampener state change.
     * Relays are processed nearest-first; unloaded chunks are never requested and the
     * fixed cap bounds work if a player builds an unusually dense network.
     */
    public static void refreshNearbyRelays(Level level, BlockPos sourcePos) {
        if (level.isClientSide) return;
        int radius = HORIZONTAL_SCAN_RADIUS;
        int radiusSquared = radius * radius;
        int refreshed = 0;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

        for (int ring = 0; ring <= radius && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; ring++) {
            for (int dx = -ring; dx <= ring && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; dx++) {
                for (int dz = -ring; dz <= ring && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != ring
                            || dx * dx + dz * dz > radiusSquared) continue;
                    int x = sourcePos.getX() + dx;
                    int z = sourcePos.getZ() + dz;
                    for (int dy = -VERTICAL_SCAN_RADIUS;
                         dy <= VERTICAL_SCAN_RADIUS && refreshed < MAX_REFRESHED_RELAYS_PER_EVENT; dy++) {
                        int y = sourcePos.getY() + dy;
                        if (y < level.getMinBuildHeight() || y >= level.getMaxBuildHeight()) continue;
                        cursor.set(x, y, z);
                        if (!level.hasChunkAt(cursor)) continue;
                        BlockState candidate = level.getBlockState(cursor);
                        if (!(candidate.getBlock() instanceof MutagenContainmentRelayBlock)) continue;

                        BlockPos relayPos = cursor.immutable();
                        int signal = evaluate(level, relayPos, candidate.getValue(MODE));
                        if (candidate.getValue(SIGNAL) != signal) {
                            level.setBlock(relayPos, candidate.setValue(SIGNAL, signal), 3);
                        }
                        refreshed++;
                    }
                }
            }
        }
    }

"""
if "public static void refreshNearbyRelays(" not in relay:
    require(method_anchor in relay, "could not locate relay input predicate")
    relay = relay.replace(method_anchor, method + method_anchor, 1)
require("MAX_REFRESHED_RELAYS_PER_EVENT = 32" in relay
        and "public static void refreshNearbyRelays(Level level, BlockPos sourcePos)" in relay,
        "bounded relay refresh method is incomplete")
relay_path.write_text(relay, encoding="utf-8")

# The field-station comparator is a cached output, so notify relays only when a
# user-triggered scan actually changes that output.
station_path = SRC / "block/MutagenFieldControlStationBlock.java"
insert_once(station_path,
    "            level.setBlock(pos, state.setValue(POWER, signal), 3);",
    "\n            MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);",
    "station comparator state update")

# Latched alarm escalation and player acknowledgement both alter the stored signal.
siren_path = SRC / "block/MutagenWarningSirenBlock.java"
siren = siren_path.read_text(encoding="utf-8")
neighbor_anchor = """        level.setBlock(pos, state.setValue(SIGNAL, liveSignal), 3);

        // Rising-severity tones are one-shot; same-tier increases and falling input are silent."""
neighbor_new = """        level.setBlock(pos, state.setValue(SIGNAL, liveSignal), 3);
        MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);

        // Rising-severity tones are one-shot; same-tier increases and falling input are silent."""
if neighbor_new not in siren:
    require(neighbor_anchor in siren, "could not locate siren escalation state update")
    siren = siren.replace(neighbor_anchor, neighbor_new, 1)
ack_anchor = """            level.setBlock(pos, state.setValue(SIGNAL, liveSignal), 3);
        }
        player.displayClientMessage("""
ack_new = """            level.setBlock(pos, state.setValue(SIGNAL, liveSignal), 3);
            MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);
        }
        player.displayClientMessage("""
if ack_new not in siren:
    require(ack_anchor in siren, "could not locate siren acknowledgement state update")
    siren = siren.replace(ack_anchor, ack_new, 1)
siren_path.write_text(siren, encoding="utf-8")

# Powered ward on/off transitions affect the relay's protective-device modes.
ward_path = SRC / "block/SporeWardBlock.java"
ward = ward_path.read_text(encoding="utf-8")
insert_once(ward_path,
    "            level.setBlock(pos, state.setValue(POWERED, powered), 3);",
    "\n            MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);",
    "Spore Ward powered transition")
insert_once(ward_path,
    "                level.setBlock(pos, state.setValue(POWERED, false), 3);",
    "\n                MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);",
    "Spore Ward scheduled shutdown")
ward = ward_path.read_text(encoding="utf-8")
require(ward.count("MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);") >= 2,
        "both Spore Ward power transitions must notify the network")

# Manual recharge and a real, charge-consuming counterpulse both change reserve output.
dampener_path = SRC / "block/MutagenResonanceDampenerBlock.java"
insert_once(dampener_path,
    "            level.setBlock(pos, state.setValue(CHARGE, MAX_CHARGE), 3);",
    "\n            MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);",
    "Resonance Dampener recharge")

entity_path = SRC / "entity/KristallpirscherEntity.java"
insert_once(entity_path,
    "            level().setBlock(pos, dampenerState.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1), 3);",
    "\n            de.sporenwerk.block.MutagenContainmentRelayBlock.refreshNearbyRelays(level(), pos);",
    "charge-consuming Kristallpirscher counterpulse")

# Advance the active artifact and current-version assertions; historical release notes remain.
updated_tests = 0
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "Aktueller Entwicklungsstand: 1.43.0" in line:
            lines[index] = line.replace("Aktueller Entwicklungsstand: 1.43.0",
                                        "Aktueller Entwicklungsstand: 1.44.0")
            line = lines[index]
            changed = True
        if r"1\.43\.0" not in line or "version" not in line.lower():
            continue
        newer = line.replace(r"1\.43\.0", r"1\.44\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.43.0" in lines[following] or "version must be 1.43.0" in lines[following]:
                lines[following] = lines[following].replace("1.43.0", "1.44.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")
        updated_tests += 1

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.44.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.44.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.44.0 — Ereignisgesteuerte Containment-Signalverteilung

- **Aktualisierte Relais ohne Polling:** Ein realer Zustandswechsel an Kontrollstation, Warnsirene, Sporenabwehr oder Resonanzdämpfer informiert nahe Containment-Relais über neue gespeicherte Werte.
- **Alarm hoch und quittiert runter:** Sireneneskalation und Spielerquittierung werden verteilt, sodass entfernte Relais nicht bis zur nächsten manuellen Interaktion mit veralteten Alarmwerten arbeiten.
- **Reserve in Echtzeit-Ereignissen:** Aufladung und Verbrauch eines Dämpfer-Gegenimpulses aktualisieren den Reserve-Ausgang des Relais.
- **Serverfreundlich begrenzt:** Die Verteilung läuft nur bei tatsächlichen Geräte-Zustandsänderungen, verarbeitet höchstens 32 Relais je Ereignis, priorisiert nähere Relais und prüft jeden Zugriff auf geladene Chunks. Es gibt keinen neuen Tick-Loop und kein erzwungenes Chunk-Laden.
- **Bestehende Verträge bleiben erhalten:** Stations-Comparator und Sirenen-Latch bleiben die Quelle ihrer jeweiligen Signale; Relais lesen diese gespeicherten Werte und verteilen nur ihren eigenen Ausgang.
- **Qualitätssicherung:** Regressionen prüfen alle Update-Trigger, den festen Arbeitsdeckel, Chunk-Sicherheit, bestehende Modi, Ressourcen und den 1.44.0-Versionsvertrag.

"""
if "## Version 1.44.0 — Ereignisgesteuerte Containment-Signalverteilung" not in readme:
    marker = "## Version 1.43.0 — Konfigurierbares Mutagen-Containment-Relais"
    index = readme.find(marker)
    require(index >= 0, "could not find 1.43.0 notes to preserve release history")
    readme = readme[:index] + section + readme[index:]
target = "**Aktueller Entwicklungsstand: 1.44.0 — ereignisgesteuerte Verteilung von Containment-Signalen.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], target, 1)
else:
    readme = target + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines:
    readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.44.0", 1)
else:
    readme = readme.replace(target, target + "\n\n## Aktueller Schwerpunkt — 1.44.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print(f"1.44.0 event-driven network updates generated; updated {updated_tests} active-version assertions.")
