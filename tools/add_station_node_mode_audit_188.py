#!/usr/bin/env python3
"""Sporenwerk 1.88.0: on-demand node operating-state audit in the Mutagen control station.

Count loaded, active SPREAD/CULTIVATION/DORMANT/REDSTONE-PAUSED sources and
inactivated sources while the station performs its already bounded survey.
Nothing is toggled or reactivated; old manual emergency/restart actions remain.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen node state audit 1.88: " + message)


def replace_once(path, old, new, reason):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(source.count(old) == 1, reason + ": expected exactly one source anchor")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


station_path = SRC / "block/MutagenFieldControlStationBlock.java"
station = station_path.read_text(encoding="utf-8")
require("import de.sporenwerk.infection.MutationNodeData;" in station,
        "the existing 1.87 safe-restart module must already import MutationNodeData")

# Reuse the existing station survey, which visits only the already-loaded chunk
# columns in a 16-block circular radius and a +/-8 height band. The source data
# lookup is done only when an encountered block IS a MutationNodeBlock.
survey_anchor = "    private static Survey survey(ServerLevel level, BlockPos center) {"
node_counts = """    private static Survey survey(ServerLevel level, BlockPos center) {
        // 1.88: all five buckets are mutually exclusive and updated only on a manual scan.
        int spreadNodes = 0, cultivatedNodes = 0, dormantNodes = 0;
        int pausedNodes = 0, inactiveNodes = 0;
        MutationNodeData nodeAuditData = MutationNodeData.get(level);"""
replace_once(station_path, survey_anchor, node_counts,
             "survey counters and shared saved-data handle")

block_anchor = """                    BlockState bs = level.getBlockState(cursor);"""
block_add = block_anchor + """
                    // 1.88 node audit: source identity first, then persisted activity and mode.
                    if (bs.getBlock() instanceof MutationNodeBlock) {
                        if (!nodeAuditData.isActive(cursor)) {
                            inactiveNodes++;
                        } else if (bs.getValue(MutationNodeBlock.POWERED)) {
                            pausedNodes++;
                        } else {
                            int nodeMode = bs.getValue(MutationNodeBlock.MODE);
                            if (nodeMode == 0) spreadNodes++;
                            else if (nodeMode == 1) cultivatedNodes++;
                            else dormantNodes++;
                        }
                    }"""
replace_once(station_path, block_anchor, block_add,
             "count operating states inside the existing loaded-chunk pass")

station = station_path.read_text(encoding="utf-8")
# Late patches have already extended the Survey record many times. Extend its
# existing constructor/record together rather than depending on historical fields.
constructor_pattern = re.compile(r"(?m)^(\s*return new Survey\()([^\n;]+)(\);\s*)$")
constructor_matches = list(constructor_pattern.finditer(station))
require(len(constructor_matches) == 1, "expected one survey constructor, found " + str(len(constructor_matches)))
append_names = ", spreadNodes, cultivatedNodes, dormantNodes, pausedNodes, inactiveNodes"
if append_names not in constructor_matches[0].group(0):
    station = constructor_pattern.sub(lambda m: m.group(1) + m.group(2) +
                                      append_names + m.group(3), station, count=1)

record_pattern = re.compile(r"(?m)^(\s*private record Survey\()([^\n)]+)(\)\s*\{\s*\})")
record_matches = list(record_pattern.finditer(station))
require(len(record_matches) == 1, "expected exactly one record definition")
record_add = ", int spreadNodes, int cultivatedNodes, int dormantNodes, int pausedNodes, int inactiveNodes"
if record_add not in record_matches[0].group(0):
    station = record_pattern.sub(lambda m: m.group(1) + m.group(2) +
                                 record_add + m.group(3), station, count=1)

station_path.write_text(station, encoding="utf-8")

# The normal report shows five distinct operational buckets. Do not alter
# comparator scoring: it is intentionally the cached hazard reading from the
# original survey, not a continuous node-monitoring timer.
report_anchor = """        Survey s = survey(serverLevel, pos);"""
report_add = report_anchor + """
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.fieldstation.node_modes",
                s.spreadNodes(), s.cultivatedNodes(), s.dormantNodes(),
                s.pausedNodes(), s.inactiveNodes()).withStyle(
                        s.spreadNodes() > 0 ? ChatFormatting.RED
                                : s.cultivatedNodes() > 0 ? ChatFormatting.GREEN
                                : ChatFormatting.GRAY), false);
        String nodeAdvice = s.spreadNodes() > 0
                ? "message.sporenwerk.fieldstation.node_warning"
                : s.cultivatedNodes() > 0
                ? "message.sporenwerk.fieldstation.node_farming"
                : "message.sporenwerk.fieldstation.node_quiet";
        player.displayClientMessage(Component.translatable(nodeAdvice)
                .withStyle(s.spreadNodes() > 0 ? ChatFormatting.GOLD : ChatFormatting.AQUA), false);"""
replace_once(station_path, report_anchor, report_add,
             "normal station report: five node states and actionable guidance")

station = station_path.read_text(encoding="utf-8")
require("private static int emergencyShutdown(" in station
        and "private static int restartSafeCultivation(" in station,
        "the existing emergency stop and safe restarter must remain")
require("getChunk(" not in station and "getChunkNow(" not in station,
        "node audit must never force-load world chunks")
require(station.index("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;")
        < station.index("BlockState bs = level.getBlockState(cursor);"),
        "world state must only be read in loaded station scan columns")

for locale, entries in (
    ("de_de.json", {
        "message.sporenwerk.fieldstation.node_modes":
            "Mutagenquellen: AUSBREITUNG %s | ANBAU %s | RUHE %s | Redstone-Pause %s | inaktiv %s.",
        "message.sporenwerk.fieldstation.node_warning":
            "WARNUNG: Aktive Ausbreitungsquellen erkannt. Mit geducktem Rechtsklick die Notabschaltung auslösen.",
        "message.sporenwerk.fieldstation.node_farming":
            "Kontrollierter Betrieb: Anbauknoten aktiv, keine unpausierte Ausbreitungsquelle im geladenen Scan erkannt.",
        "message.sporenwerk.fieldstation.node_quiet":
            "Keine aktiven, ungepausten Mutagenquellen im geladenen Scan erkannt."
    }),
    ("en_us.json", {
        "message.sporenwerk.fieldstation.node_modes":
            "Mutagen sources: SPREAD %s | CULTIVATE %s | DORMANT %s | Redstone-paused %s | inactive %s.",
        "message.sporenwerk.fieldstation.node_warning":
            "WARNING: active spreading nodes detected. Sneak-right-click to trigger emergency shutdown.",
        "message.sporenwerk.fieldstation.node_farming":
            "Controlled operation: cultivation active; no unpaused spreading node found in the loaded scan.",
        "message.sporenwerk.fieldstation.node_quiet":
            "No unpaused active Mutagen sources detected in the loaded scan."
    }),
):
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Extend only the current-version test expectations. Historical milestones stay.
for path in (ROOT / "tools").glob("test_*.py"):
    if path.name == "test_station_node_mode_audit_188.py":
        continue
    source = path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.87.0",
                             "Aktueller Entwicklungsstand: 1.88.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.87\.0", r"1\.88\.0")
        updated = updated.replace("artifact must be version 1.87.0",
                                  "artifact must be version 1.88.0")
    updated = updated.replace(
        '"Version 1.87.0" in readme and "Version 1.86.0" in readme',
        '"Version 1.88.0" in readme and "Version 1.87.0" in readme')
    if updated != source:
        path.write_text(updated, encoding="utf-8")

gradle = ROOT / "build.gradle"
build, changed = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                         "version = '1.88.0'", gradle.read_text(encoding="utf-8"), count=1)
require(changed == 1, "unable to set artifact to version 1.88.0")
gradle.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.88.0

- **Mutagen-Knotenprotokoll:** Die Feldkontrollstation zählt beim normalen Rechtsklick fünf tatsächlich unterschiedliche Betriebszustände: ungebremste AUSBREITUNG, sicherer ANBAU, RUHE, Redstone-pausierte Quellen und gespeicherte inaktive/sterilisierte Quellen.
- **Quellen statt Bodenfarben:** Der neue Bericht prüft die echte aktive Knotenregistrierung aus den gespeicherten Welt-Daten. Damit werden endgültig inaktive Quellen nicht fälschlich als aktive Gefahr angezeigt.
- **Handlungsempfehlung:** Bei aktiv ausbreitenden Knoten erscheint eine deutliche Warnung mit Notabschaltungshinweis. Sind nur kontrollierte Anbauknoten aktiv, wird dies als kontrollierter Betrieb gemeldet; sonst zeigt die Station einen Ruhehinweis.
- **Sicheres System:** Kein Neustart und keine Blockänderung beim Scan; der bestehende Comparator-Ausgang, Not-Aus per Schleichen und sichere Neustart mit Amethystscherbe bleiben unverändert. Redstone-Pause und die globale Endspiel-Heilung werden respektiert.
- **Performance und Sicherheit:** Die fünf Zähler werden innerhalb des bereits bestehenden manuellen Stationsscans erfasst – kein zweiter Flächenscan, kein neuer Dauer-Ticker, keine Chunk-Forceloads. Nur geladene Blöcke im bekannten Radius 16 und Höhe ±8 werden untersucht.
- **Qualitätsprüfung:** Eigene Regression für alle fünf Kategorien, gespeicherte Aktivität, Warntexte, Loaded-Chunk-Grenzen, bestehende Steuerfunktionen und Versionsdaten; vollständiger Forge-Build und dedizierter Serverstart prüfen die Integration.

"""
if "## Aktueller Entwicklungsschritt — 1.88.0" not in readme:
    anchor = "## Aktueller Entwicklungsschritt — 1.87.0"
    require(anchor in readme, "previous 1.87 development notes absent")
    readme = readme.replace(anchor, current + anchor, 1)
release = """## Version 1.88.0 — Live-Knotenprotokoll der Mutagen-Kontrollstation

- **Fünf Betriebszustände:** Die Kontrollstation unterscheidet beim normalen Scan AUSBREITUNG, ANBAU, RUHE, Redstone-Pause und endgültig inaktive Quellen. Die Ergebnisse stammen aus echten Blockzuständen und gespeicherter Quellregistrierung.
- **Verständlicher Alarm:** Nur tatsächlich aktive, nicht pausierte Ausbreitungsquellen lösen die rote Warnung aus. Anlagen mit ausschließlich sicheren Kulturen bekommen eine grüne Betriebsrückmeldung, stillgelegte Anlagen eine ruhige Diagnose.
- **Endspiel bleibt geschützt:** Sterilisierte Quellen erscheinen als inaktiv. Diagnose und Anzeige ändern weder gespeicherte Registrierung noch Blockzustände, Stabilisatoren, Ernte oder Sicherheitsmechaniken.
- **Bereits vorhandener Scan:** Die Auswertung nutzt exakt denselben geladenen 16-Blöcke-Radius/±8-Höhen-Bereich wie Forschung, Biodiversität und Notabschaltung. Ein Comparator löst weiterhin keinen zusätzlichen Scan aus.
- **Nachvollziehbar auf DE/EN:** Übersetzte Quellenzählung und konkrete Handlungsanweisungen. Notabschaltung (Schleichen) und sicherer Wiederanlauf (Schleichen plus Amethyst) bleiben erhalten.
- **Regression und Build:** Tests für Kategorisierung, Aktivitätsprüfung, Loaded-Chunk-Guards, Quellenzählung, Warnung, alte Steuermodi und Textressourcen; vollständige Forge-Kompilierung, JAR- und Dedicated-Server-Prüfung.

"""
if "## Version 1.88.0 — Live-Knotenprotokoll der Mutagen-Kontrollstation" not in readme:
    anchor = "## Version 1.87.0 —"
    require(anchor in readme, "previous 1.87 release missing")
    readme = readme.replace(anchor, release + anchor, 1)
old_headline = "**Aktueller Entwicklungsstand: 1.87.0 — sicherer Wiederanlauf kontrollierter Mutagenfarmen.**"
require(old_headline in readme, "could not locate current README headline")
readme = readme.replace(old_headline,
                        "**Aktueller Entwicklungsstand: 1.88.0 — Live-Knotenprotokoll für sichere Mutagenanlagen.**", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.88.0: source-mode audit integrated into existing station scan, categorized alarms and live-source safety checks.")
