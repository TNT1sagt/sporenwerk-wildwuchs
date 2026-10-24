#!/usr/bin/env python3
"""Add siren-aware, actionable containment diagnostics to the Mutagen Field Control Station (1.42.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen siren protocol: " + message)


station_path = SRC / "block/MutagenFieldControlStationBlock.java"
station = station_path.read_text(encoding="utf-8")

# Keep the scan user-triggered and inside the existing radius; read the siren's
# latched SIGNAL directly so a severe historical event is not hidden by a lower
# current comparator value.
old_counts = "int poweredWards = 0, dampeners = 0, chargedDampeners = 0, availablePulses = 0;"
new_counts = old_counts + "\n        int sirenSignals = 0, criticalSirenSignals = 0, highestSirenSignal = 0;"
if new_counts not in station:
    require(old_counts in station, "could not extend existing containment-audit counters")
    station = station.replace(old_counts, new_counts, 1)

old_scan = """                        availablePulses += charge;
                    }
                }
            }
        }
        int networkMembers = 0;"""
new_scan = """                        availablePulses += charge;
                    }
                    if (bs.is(ModBlocks.MUTAGEN_WARNSIRENE.get())
                            && bs.hasProperty(MutagenWarningSirenBlock.SIGNAL)) {
                        int sirenSignal = bs.getValue(MutagenWarningSirenBlock.SIGNAL);
                        if (sirenSignal > 0) {
                            sirenSignals++;
                            highestSirenSignal = Math.max(highestSirenSignal, sirenSignal);
                            if (MutagenWarningSirenBlock.riskBand(sirenSignal) == 3) criticalSirenSignals++;
                        }
                    }
                }
            }
        }
        int networkMembers = 0;"""
if new_scan not in station:
    require(old_scan in station, "could not locate bounded survey loop for siren sampling")
    station = station.replace(old_scan, new_scan, 1)

old_return = "return new Survey(soil, highSoil, crops, standard, reinforced, advanced, networkMembers, poweredWards, dampeners, chargedDampeners, availablePulses);"
new_return = "return new Survey(soil, highSoil, crops, standard, reinforced, advanced, networkMembers, poweredWards, dampeners, chargedDampeners, availablePulses, sirenSignals, criticalSirenSignals, highestSirenSignal);"
if new_return not in station:
    require(old_return in station, "could not extend Survey return with siren data")
    station = station.replace(old_return, new_return, 1)

old_record = "private record Survey(int soil, int highSoil, int crops, int standard, int reinforced, int advanced, int networkMembers, int poweredWards, int dampeners, int chargedDampeners, int availablePulses) {}"
new_record = "private record Survey(int soil, int highSoil, int crops, int standard, int reinforced, int advanced, int networkMembers, int poweredWards, int dampeners, int chargedDampeners, int availablePulses, int sirenSignals, int criticalSirenSignals, int highestSirenSignal) {}"
if new_record not in station:
    require(old_record in station, "could not extend Survey record with siren data")
    station = station.replace(old_record, new_record, 1)

# The protocol deliberately checks latched siren incidents first, then hotspot
# severity and available countermeasures. Presence is not equated with actual
# physical coverage: the output explicitly tells players to verify placement.
helper_anchor = "    private static Survey survey(ServerLevel level, BlockPos center) {"
protocol_helper = """    private static String containmentProtocolKey(Survey s) {
        if (s.criticalSirenSignals() > 0) return "message.sporenwerk.fieldstation.protocol.critical_siren";
        if (s.sirenSignals() > 0) return "message.sporenwerk.fieldstation.protocol.siren_signal";
        if (s.highSoil() > 0) {
            if (s.poweredWards() == 0 && s.availablePulses() == 0)
                return "message.sporenwerk.fieldstation.protocol.hotspot_unprotected";
            if (s.poweredWards() == 0)
                return "message.sporenwerk.fieldstation.protocol.ward_missing";
            if (s.availablePulses() == 0)
                return "message.sporenwerk.fieldstation.protocol.reserve_empty";
            return "message.sporenwerk.fieldstation.protocol.verify_coverage";
        }
        if (s.soil() > 0) return "message.sporenwerk.fieldstation.protocol.mutagen_soil";
        if (s.crops() > 0) return "message.sporenwerk.fieldstation.protocol.crop_activity";
        return "message.sporenwerk.fieldstation.protocol.clear";
    }

"""
if protocol_helper not in station:
    require(helper_anchor in station, "could not locate survey helper insertion point")
    station = station.replace(helper_anchor, protocol_helper + helper_anchor, 1)

report_anchor = '        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.containment", s.poweredWards(), s.chargedDampeners(), s.dampeners(), s.availablePulses()).withStyle(ChatFormatting.GREEN), false);'
siren_line = '        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.siren_audit", s.sirenSignals(), s.criticalSirenSignals(), s.highestSirenSignal()).withStyle(ChatFormatting.GOLD), false);'
protocol_line = """        String protocolKey = containmentProtocolKey(s);
        ChatFormatting protocolColor = switch (protocolKey) {
            case "message.sporenwerk.fieldstation.protocol.critical_siren",
                 "message.sporenwerk.fieldstation.protocol.hotspot_unprotected" -> ChatFormatting.RED;
            case "message.sporenwerk.fieldstation.protocol.clear" -> ChatFormatting.GREEN;
            default -> ChatFormatting.YELLOW;
        };
        player.displayClientMessage(Component.translatable(protocolKey).withStyle(protocolColor), false);"""
if siren_line not in station:
    require(report_anchor in station, "could not locate existing containment-audit report")
    station = station.replace(report_anchor, report_anchor + "\n" + siren_line, 1)
if protocol_line not in station:
    require(siren_line in station, "could not locate siren audit line for protocol report")
    station = station.replace(siren_line, siren_line + "\n" + protocol_line, 1)

for token in (
    "ModBlocks.MUTAGEN_WARNSIRENE.get()",
    "MutagenWarningSirenBlock.SIGNAL",
    "MutagenWarningSirenBlock.riskBand(sirenSignal) == 3",
    "highestSirenSignal = Math.max(highestSirenSignal, sirenSignal)",
    "private static String containmentProtocolKey(Survey s)",
    "s.poweredWards() == 0 && s.availablePulses() == 0",
    "message.sporenwerk.fieldstation.siren_audit",
    "player.displayClientMessage(Component.translatable(protocolKey).withStyle(protocolColor), false);",
    "if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;",
):
    require(token in station, "required siren/protocol integration missing: " + token)
station_path.write_text(station, encoding="utf-8")

locale_additions = {
    "de_de.json": {
        "message.sporenwerk.fieldstation.siren_audit":
            "Sirenenprotokoll — gespeicherte Warnsignale: %s; kritisch (11–15): %s; höchster gespeicherter Wert: %s/15.",
        "message.sporenwerk.fieldstation.protocol.critical_siren":
            "Containment-Protokoll: KRITISCH — mindestens eine Sirene speichert ein kritisches Signal. Prüfe Ursache und Feldstatus.",
        "message.sporenwerk.fieldstation.protocol.siren_signal":
            "Containment-Protokoll: WARNUNG — eine Sirene speichert ein Warnsignal. Prüfe die Ursache und quittiere nach Behebung.",
        "message.sporenwerk.fieldstation.protocol.hotspot_unprotected":
            "Containment-Protokoll: HOHES RISIKO — Stärke-III-Hotspots erkannt; im Scanbereich wurden weder eingeschaltete Sporenabwehr noch Gegenimpuls-Ladung gefunden.",
        "message.sporenwerk.fieldstation.protocol.ward_missing":
            "Containment-Protokoll: UNVOLLSTÄNDIG — Stärke-III-Hotspots erkannt, aber kein eingeschalteter Sporenabwehrsender im Scanbereich.",
        "message.sporenwerk.fieldstation.protocol.reserve_empty":
            "Containment-Protokoll: RESERVE LEER — Stärke-III-Hotspots erkannt, aber keine Resonanz-Gegenimpulse verfügbar. Lade Dämpfer nach.",
        "message.sporenwerk.fieldstation.protocol.verify_coverage":
            "Containment-Protokoll: GEGENMITTEL VORHANDEN — Schutzgeräte und Gegenimpulse erkannt. Prüfe vor Ort, ob jeder Hotspot tatsächlich abgedeckt ist.",
        "message.sporenwerk.fieldstation.protocol.mutagen_soil":
            "Containment-Protokoll: MUTAGENBODEN — Kontamination erkannt, aber keine Stärke-III-Hotspots im geladenen Scanbereich gefunden.",
        "message.sporenwerk.fieldstation.protocol.crop_activity":
            "Containment-Protokoll: PFLANZENAKTIVITÄT — mutagene Pflanzen erkannt; Mutagenboden wurde im geladenen Scanbereich nicht gezählt.",
        "message.sporenwerk.fieldstation.protocol.clear":
            "Containment-Protokoll: RUHIG — keine Mutagenboden- oder mutagene Pflanzenaktivität im geladenen Scanbereich erkannt.",
    },
    "en_us.json": {
        "message.sporenwerk.fieldstation.siren_audit":
            "Siren protocol — stored warning signals: %s; critical (11–15): %s; highest stored value: %s/15.",
        "message.sporenwerk.fieldstation.protocol.critical_siren":
            "Containment protocol: CRITICAL — at least one siren retains a critical signal. Inspect the cause and field status.",
        "message.sporenwerk.fieldstation.protocol.siren_signal":
            "Containment protocol: WARNING — a siren retains a warning signal. Inspect the cause and acknowledge after resolution.",
        "message.sporenwerk.fieldstation.protocol.hotspot_unprotected":
            "Containment protocol: HIGH RISK — tier-III hotspots found, but no powered Spore Ward or counterpulse charge was found in the scan area.",
        "message.sporenwerk.fieldstation.protocol.ward_missing":
            "Containment protocol: INCOMPLETE — tier-III hotspots found, but no powered Spore Ward was found in the scan area.",
        "message.sporenwerk.fieldstation.protocol.reserve_empty":
            "Containment protocol: RESERVE EMPTY — tier-III hotspots found, but no Resonance counterpulses are available. Recharge the Dampeners.",
        "message.sporenwerk.fieldstation.protocol.verify_coverage":
            "Containment protocol: COUNTERMEASURES PRESENT — protection devices and counterpulses were found. Verify in-world that each hotspot is actually covered.",
        "message.sporenwerk.fieldstation.protocol.mutagen_soil":
            "Containment protocol: MUTAGEN SOIL — contamination detected, but no tier-III hotspots were found in the loaded scan area.",
        "message.sporenwerk.fieldstation.protocol.crop_activity":
            "Containment protocol: CROP ACTIVITY — mutagen-active crops found; Mutagen Soil was not counted in the loaded scan area.",
        "message.sporenwerk.fieldstation.protocol.clear":
            "Containment protocol: CLEAR — no Mutagen Soil or mutagen-active crop activity detected in the loaded scan area.",
    },
}
for filename, additions in locale_additions.items():
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale.update(additions)
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Move active-version assertions forward while retaining historical release checks.
updated_tests = 0
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "Aktueller Entwicklungsstand: 1.41.0" in line:
            lines[index] = line.replace("Aktueller Entwicklungsstand: 1.41.0",
                                        "Aktueller Entwicklungsstand: 1.42.0")
            line = lines[index]
            changed = True
        if r"1\.41\.0" not in line or "version" not in line.lower():
            continue
        newer = line.replace(r"1\.41\.0", r"1\.42\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.41.0" in lines[following] or "version must be 1.41.0" in lines[following]:
                lines[following] = lines[following].replace("1.41.0", "1.42.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")
        updated_tests += 1

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.42.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.42.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.42.0 — Sirenenprotokoll und Containment-Empfehlungen

- **Sirenen werden Teil der Diagnose:** Der Stationsscan erfasst die gespeicherten Warnsignale der Mutagen-Warnsirenen, die Anzahl kritischer Signale (11–15) und den höchsten gespeicherten Wert.
- **Konkrete Handlungshinweise:** Das Containment-Protokoll priorisiert kritische Sirenensignale, danach Stärke-III-Hotspots und die tatsächlich im Scanbereich vorhandenen Abwehrsender sowie verfügbaren Resonanz-Gegenimpulse.
- **Keine falsche Sicherheitsgarantie:** Geräte in Reichweite zu zählen beweist keine räumliche Abdeckung. Wenn Gegenmittel vorhanden sind, fordert die Diagnose ausdrücklich dazu auf, die Schutzvolumen am Feld zu prüfen.
- **Begrenzte Serverlast:** Alles läuft im vorhandenen manuellen, geladenen-Chunk-Scan. Es gibt keine zusätzlichen Tick-Scans und der bestehende Comparator-Gefahrenwert bleibt unverändert.
- **Qualitätssicherung:** Tests decken Sirenen-Signalstufen, Diagnose-Priorität, Ressourcenstatus, DE/EN-Texte, die bestehende Scanbegrenzung und den Versionsvertrag ab.

"""
if "## Version 1.42.0 — Sirenenprotokoll und Containment-Empfehlungen" not in readme:
    marker = "## Version 1.41.0 — Containment-Audit der Mutagenfeld-Kontrollstation"
    index = readme.find(marker)
    require(index >= 0, "could not find 1.41.0 notes to preserve release history")
    readme = readme[:index] + section + readme[index:]

target = "**Aktueller Entwicklungsstand: 1.42.0 — Sirenenprotokoll und handlungsorientierte Containment-Diagnose.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], target, 1)
else:
    readme = target + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines:
    readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.42.0", 1)
else:
    readme = readme.replace(target, target + "\n\n## Aktueller Schwerpunkt — 1.42.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print(f"1.42.0 siren-aware containment protocol generated; updated {updated_tests} active-version regression assertions.")
