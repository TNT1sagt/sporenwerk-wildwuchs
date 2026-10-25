#!/usr/bin/env python3
"""1.63.0 adds a direct Mutagen field-intensity mode to the Containment Relay."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Containment Relay field intensity 1.63: " + message)


def replace_once(path, old, new, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return
    count = source.count(old)
    require(count == 1, f"{label}: expected exactly one source anchor, got {count}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


relay_path = SRC / "block/MutagenContainmentRelayBlock.java"
relay = relay_path.read_text(encoding="utf-8")

# The new mode reads the real terrain/crop states within the relay's existing bounded,
# loaded-chunk-only survey. It does not depend on a previous station scan or introduce a ticker.
import_anchor = "import de.sporenwerk.registry.ModBlocks;"
import_line = "import de.sporenwerk.block.crop.AbstractSporeCropBlock;"
if import_line not in relay:
    require(import_anchor in relay, "could not locate relay block import anchor")
    relay = relay.replace(import_anchor, import_line + "\n" + import_anchor, 1)
    relay_path.write_text(relay, encoding="utf-8")

replace_once(
    relay_path,
    'public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 3);',
    'public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 4);',
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 4)',
    "five relay modes",
)
replace_once(
    relay_path,
    "int mode = (state.getValue(MODE) + step) % 4;",
    "int mode = (state.getValue(MODE) + step) % 5;",
    "state.getValue(MODE) + step) % 5",
    "five-mode cycling",
)
replace_once(
    relay_path,
    '            case 3 -> "message.sporenwerk.containment_relay.mode_gap";',
    '            case 3 -> "message.sporenwerk.containment_relay.mode_gap";\n'
    '            case 4 -> "message.sporenwerk.containment_relay.mode_intensity";',
    'case 4 -> "message.sporenwerk.containment_relay.mode_intensity"',
    "field-intensity mode label",
)
replace_once(
    relay_path,
    "        if (mode == 3 && signal >= 15) return ChatFormatting.RED;",
    "        if ((mode == 3 || mode == 4) && signal >= 11) return ChatFormatting.RED;",
    "if ((mode == 3 || mode == 4) && signal >= 11)",
    "danger color for field-intensity mode",
)
replace_once(
    relay_path,
    "     * Mode 3: containment gap; a tier-III hotspot without both device types outputs 15.\n",
    "     * Mode 3: containment gap; a tier-III hotspot without both device types outputs 15.\n"
    "     * Mode 4: live terrain intensity from contaminated soil and mutated crops; no station scan required.\n",
    "Mode 4: live terrain intensity",
    "mode documentation",
)
replace_once(
    relay_path,
    "        int counterpulses = 0;\n        BlockPos.MutableBlockPos cursor",
    "        int counterpulses = 0;\n"
    "        int tierOneSoil = 0, tierTwoSoil = 0, tierThreeSoil = 0, mutatedCrops = 0;\n"
    "        BlockPos.MutableBlockPos cursor",
    "int tierOneSoil = 0, tierTwoSoil = 0, tierThreeSoil = 0, mutatedCrops = 0;",
    "field intensity counters",
)

scan_anchor = """                    if (scanned.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                            && scanned.hasProperty(MutagenResonanceDampenerBlock.CHARGE)) {
                        counterpulses += scanned.getValue(MutagenResonanceDampenerBlock.CHARGE);
                    }"""
scan_addition = scan_anchor + """
                    if (scanned.is(ModBlocks.MUTAGEN_BODEN.get())
                            && scanned.hasProperty(InfestedTerrainBlock.MUTAGEN_LEVEL)) {
                        int tier = scanned.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL);
                        if (tier == 1) tierOneSoil++;
                        else if (tier == 2) tierTwoSoil++;
                        else if (tier >= 3) tierThreeSoil++;
                    }
                    if (scanned.getBlock() instanceof AbstractSporeCropBlock
                            && scanned.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            && scanned.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0) {
                        mutatedCrops++;
                    }"""
replace_once(
    relay_path,
    scan_anchor,
    scan_addition,
    "int tier = scanned.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL);",
    "live terrain and crop survey",
)

replace_once(
    relay_path,
    "            case 3 -> {\n"
    "                if (stationSignal >= 11 && (poweredWards == 0 || counterpulses == 0)) yield 15;\n"
    "                if (stationSignal >= 11) yield 5;\n"
    "                if (criticalSirens > 0) yield 15;\n"
    "                if (sirenSignal > 0 || stationSignal >= 5) yield 10;\n"
    "                yield 0;\n"
    "            }\n"
    "            default -> Math.max(stationSignal, sirenSignal);",
    "            case 3 -> {\n"
    "                if (stationSignal >= 11 && (poweredWards == 0 || counterpulses == 0)) yield 15;\n"
    "                if (stationSignal >= 11) yield 5;\n"
    "                if (criticalSirens > 0) yield 15;\n"
    "                if (sirenSignal > 0 || stationSignal >= 5) yield 10;\n"
    "                yield 0;\n"
    "            }\n"
    "            case 4 -> {\n"
    "                if (tierThreeSoil > 0) yield Math.min(15, 11 + Math.min(4, (tierThreeSoil - 1) / 4));\n"
    "                if (tierTwoSoil > 0) yield Math.min(10, 7 + Math.min(3, (tierTwoSoil - 1) / 8));\n"
    "                if (tierOneSoil > 0) yield Math.min(6, 3 + Math.min(3, (tierOneSoil - 1) / 16));\n"
    "                if (mutatedCrops > 0) yield 2;\n"
    "                yield 0;\n"
    "            }\n"
    "            default -> Math.max(stationSignal, sirenSignal);",
    "case 4 -> {\n                if (tierThreeSoil > 0)",
    "field intensity output bands",
)
# Five modes × sixteen comparator values are valid blockstates; the relay's appearance stays stable.
blockstate_path = ASSETS / "blockstates/mutagen_containment_relay.json"
blockstate = {
    "variants": {
        f"mode={mode},signal={signal}": {
            "model": "sporenwerk:block/mutagen_containment_relay"
        }
        for mode in range(5)
        for signal in range(16)
    }
}
blockstate_path.write_text(json.dumps(blockstate, indent=2) + "\n", encoding="utf-8")

for filename, key, value in (
    ("de_de.json", "message.sporenwerk.containment_relay.mode_intensity", "Mutagen-Feldstärke"),
    ("en_us.json", "message.sporenwerk.containment_relay.mode_intensity", "Mutagen field intensity"),
):
    locale_path = ASSETS / "lang" / filename
    locale = json.loads(locale_path.read_text(encoding="utf-8"))
    locale[key] = value
    locale_path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Update the pre-existing relay contract too: it must now recognize all five modes.
legacy_test_path = ROOT / "tools/test_mutagen_containment_relay.py"
legacy_test = legacy_test_path.read_text(encoding="utf-8")
legacy_updates = (
    ('IntegerProperty MODE = IntegerProperty.create("mode", 0, 3)',
     'IntegerProperty MODE = IntegerProperty.create("mode", 0, 4)'),
    ("int mode = (state.getValue(MODE) + step) % 4;",
     "int mode = (state.getValue(MODE) + step) % 5;"),
    ("len(variants) == 64", "len(variants) == 80"),
    ("for mode in range(4):", "for mode in range(5):"),
    ("all 4 MODE × 16 SIGNAL", "all 5 MODE × 16 SIGNAL"),
)
for old, new in legacy_updates:
    if new not in legacy_test:
        require(old in legacy_test, "could not migrate existing relay test contract: " + old)
        legacy_test = legacy_test.replace(old, new)
if "case 4 ->" not in legacy_test:
    anchor = '    "case 3 -> {",'
    require(anchor in legacy_test, "could not extend existing mode contract list")
    legacy_test = legacy_test.replace(anchor, anchor + '\n    "case 4 -> {",', 1)
if '"message.sporenwerk.containment_relay.mode_intensity"' not in legacy_test:
    anchor = '"message.sporenwerk.containment_relay.mode_gap",'
    require(anchor in legacy_test, "could not extend relay locale assertions")
    legacy_test = legacy_test.replace(anchor, anchor + '\n        "message.sporenwerk.containment_relay.mode_intensity",', 1)
legacy_test_path.write_text(legacy_test, encoding="utf-8")

# Bring active artifact assertions and README headline forward, while retaining release history.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.62.0",
                             "Aktueller Entwicklungsstand: 1.63.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.62\.0", r"1\.63\.0")
        updated = updated.replace("artifact must be version 1.62.0",
                                  "artifact must be version 1.63.0")
    updated = updated.replace(
        '"Version 1.62.0" in readme and "Version 1.61.0" in readme',
        '"Version 1.63.0" in readme and "Version 1.62.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.63.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.63.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.63.0 — Live-Feldstärke für das Containment-Relais

- **Neuer fünfter Modus:** Das Relais kann direkt die tatsächliche Mutagen-Feldstärke in seiner bestehenden Scanreichweite als Comparator-Signal ausgeben. Ein vorheriger Kontrollstations-Scan ist dafür nicht nötig.
- **Unterscheidbare Stufen:** Mutagenboden der Stufen I, II und III erzeugt getrennte Signalbereiche; besonders starke Stufe-III-Hotspots reichen bis 15. Mutagenaktive Pflanzen werden als niedrige Aktivität sichtbar.
- **Echte Weltwerte statt veralteter Cache:** Der Modus liest beim ohnehin ausgelösten Relais-Scan aktuelle Blockzustände. Damit können Redstone-Anlagen auf lokale Feldveränderungen reagieren, sobald das Relais ausgelöst oder ein relevantes Nachbar-Update empfangen wird.
- **Chunk- und Performancegrenzen bleiben erhalten:** Der bestehende begrenzte Radius, die Prüfung geladener Chunks und das ereignisgesteuerte Design bleiben bestehen; es wird kein eigener Ticker hinzugefügt.
- **Regressionen:** Prüfungen decken alle 80 Modus-/Signal-Blockstates, die neuen Feldstärkebänder, DE/EN-Anzeige, Chunk-Sicherheit und die übrigen vier Relaismodi ab.

Die Feldmessung erfolgt über das Relais; die Kontrollstation, Sirenen, Schutzsender, Resonanzdämpfer und bestehenden Containment-Modi bleiben nutzbar.

"""
if "## Version 1.63.0 — Live-Feldstärke für das Containment-Relais" not in readme:
    marker = "## Version 1.62.0 — Panzerplatten für Schulter und Hinterhand"
    idx = readme.find(marker)
    if idx < 0:
        idx = readme.find("\n## ")
        if idx >= 0:
            idx += 1
        else:
            idx = len(readme)
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.63.0 — direkter Feldstärke-Comparator-Modus im Mutagen-Containment-Relais.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus = [line for line in readme.splitlines() if line.startswith("## Aktueller Entwicklungsschritt — ")]
if focus:
    readme = readme.replace(focus[0], "## Aktueller Entwicklungsschritt — 1.63.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Mutagen Containment Relay 1.63.0 live field intensity generated.")
