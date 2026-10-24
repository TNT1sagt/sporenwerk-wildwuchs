#!/usr/bin/env python3
"""Add an on-demand containment audit to the Mutagen Field Control Station (1.41.0)."""
from pathlib import Path
import re, sys, json
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"
def require(condition, message):
    if not condition: raise SystemExit("Mutagen containment audit: " + message)
station_path = SRC / "block/MutagenFieldControlStationBlock.java"
station = station_path.read_text(encoding="utf-8")
old = "int soil = 0, highSoil = 0, crops = 0, standard = 0, reinforced = 0, advanced = 0;"
new = old + "\n        int poweredWards = 0, dampeners = 0, chargedDampeners = 0, availablePulses = 0;"
if new not in station:
    require(old in station, "could not extend survey counters")
    station = station.replace(old, new, 1)
old = """                        stabilizers.add(cursor.immutable());
                    }
                }
            }
        }
        int networkMembers = 0;"""
new = """                        stabilizers.add(cursor.immutable());
                    }
                    if (bs.is(ModBlocks.SPORENABWEHR.get())
                            && bs.hasProperty(SporeWardBlock.POWERED)
                            && bs.getValue(SporeWardBlock.POWERED)) {
                        poweredWards++;
                    }
                    if (bs.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                            && bs.hasProperty(MutagenResonanceDampenerBlock.CHARGE)) {
                        int charge = bs.getValue(MutagenResonanceDampenerBlock.CHARGE);
                        dampeners++;
                        if (charge > 0) chargedDampeners++;
                        availablePulses += charge;
                    }
                }
            }
        }
        int networkMembers = 0;"""
if new not in station:
    require(old in station, "could not locate bounded survey loop")
    station = station.replace(old, new, 1)
old = "return new Survey(soil, highSoil, crops, standard, reinforced, advanced, networkMembers);"
new = "return new Survey(soil, highSoil, crops, standard, reinforced, advanced, networkMembers, poweredWards, dampeners, chargedDampeners, availablePulses);"
if new not in station:
    require(old in station, "could not extend Survey result")
    station = station.replace(old, new, 1)
old = "private record Survey(int soil, int highSoil, int crops, int standard, int reinforced, int advanced, int networkMembers) {}"
new = "private record Survey(int soil, int highSoil, int crops, int standard, int reinforced, int advanced, int networkMembers, int poweredWards, int dampeners, int chargedDampeners, int availablePulses) {}"
if new not in station:
    require(old in station, "could not extend Survey record")
    station = station.replace(old, new, 1)
anchor = '        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.loaded_chunks_only").withStyle(ChatFormatting.DARK_GRAY), false);'
report = '        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.containment", s.poweredWards(), s.chargedDampeners(), s.dampeners(), s.availablePulses()).withStyle(ChatFormatting.GREEN), false);'
if report not in station:
    require(anchor in station, "could not locate existing station status report")
    station = station.replace(anchor, report + "\n" + anchor, 1)
require("SporeWardBlock.POWERED" in station and "MutagenResonanceDampenerBlock.CHARGE" in station,
        "report must read actual ward state and dampener charge")
require("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;" in station,
        "survey must continue skipping unloaded chunks")
station_path.write_text(station, encoding="utf-8")
for filename, key, value in (
    ("de_de.json", "message.sporenwerk.fieldstation.containment",
     "Containment im Scanbereich — Sporenabwehr aktiv: %s; Resonanzdämpfer geladen: %s/%s; verfügbare Gegenimpulse: %s."),
    ("en_us.json", "message.sporenwerk.fieldstation.containment",
     "Containment devices in scan area — powered Spore Wards: %s; charged Resonance Dampeners: %s/%s; counterpulses available: %s."),
):
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    if locale.get(key) != value:
        locale[key] = value
        path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
updated_tests = 0
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if r"1\.40\.0" not in line or "version" not in line.lower(): continue
        newer = line.replace(r"1\.40\.0", r"1\.41\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.40.0" in lines[following] or "version must be 1.40.0" in lines[following]:
                lines[following] = lines[following].replace("1.40.0", "1.41.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")
        updated_tests += 1
build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.41.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.41.0")
build_path.write_text(build, encoding="utf-8")
readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.41.0 — Containment-Audit der Mutagenfeld-Kontrollstation

- **Ein gemeinsamer Anlagenbericht:** Ein manueller Stationsscan erfasst nun zusätzlich eingeschaltete Sporenabwehrsender, alle Resonanzdämpfer im Scanbereich, wie viele davon noch Ladung haben und wie viele Gegenimpulse insgesamt verfügbar sind.
- **Echte Zustände statt Schätzungen:** Die Anzeige liest den Redstone-Zustand der Sporenabwehr und die gespeicherte Ladung jedes Resonanzdämpfers. Ein leerer Dämpfer zählt nicht als geladen.
- **Keine neue Dauerlast:** Die Zahlen werden im vorhandenen begrenzten Stationsscan gesammelt. Unloaded Chunks werden weiter übersprungen; Comparator-Abfragen starten keinen Scan und Geräte werden nicht automatisch aktiviert oder aufgeladen.
- **Aufbauhilfe statt falscher Garantie:** Der Bericht zählt Geräte im Stationsbereich. Er behauptet nicht, dass jede Abwehr gerade jedes Mutagenfeld abdeckt. Warnsirene, Comparator, Netzwerkstabilisatoren, Sporenabwehr und Resonanzdämpfer bleiben einzeln kombinierbar.
- **Qualitätssicherung:** Regressionen prüfen geladene/ungeladene Dämpfer, Powered-Status, DE/EN-Meldungen, bounded scan und den Versionsvertrag; danach folgen Ressourcenprüfung, Forge-Build, JAR-Prüfung und Server-Smoke-Test.

"""
if "## Version 1.41.0 — Containment-Audit der Mutagenfeld-Kontrollstation" not in readme:
    marker = "## Version 1.40.0 — Mutagenblüte und Sporenabwehr im Zusammenspiel"
    index = readme.find(marker)
    require(index >= 0, "could not find 1.40.0 notes to preserve release history")
    readme = readme[:index] + section + readme[index:]
target = "**Aktueller Entwicklungsstand: 1.41.0 — Containment-Audit für Mutagenfeld-Anlagen.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines: readme = readme.replace(headlines[0], target, 1)
else: readme = target + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines: readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.41.0", 1)
else: readme = readme.replace(target, target + "\n\n## Aktueller Schwerpunkt — 1.41.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print(f"1.41.0 containment audit generated; updated {updated_tests} active-version assertions.")
