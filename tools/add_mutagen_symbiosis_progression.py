#!/usr/bin/env python3
"""Link field biodiversity to endgame filter crafting and improve scanner ecology reporting (1.47.0)."""
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
        raise SystemExit("Symbiosis research chain: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# A lab-grade replacement cartridge now consumes the ecological resource introduced in 1.46.
# Retaining the existing components keeps the upgrade chain intact instead of replacing it.
recipe_path = RES / "data/sporenwerk/recipes/sporenfiltereinsatz_mutagen.json"
recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
require(recipe.get("type") == "minecraft:crafting_shapeless", "mutagenic cartridge must remain shapeless")
ingredients = recipe.setdefault("ingredients", [])
symbiosis_ingredient = {"item": "sporenwerk:symbiosemyzel"}
if symbiosis_ingredient not in ingredients:
    ingredients.append(symbiosis_ingredient)
require(recipe.get("result", {}).get("item") == "sporenwerk:sporenfiltereinsatz_mutagen",
        "mutagenic cartridge recipe output changed unexpectedly")
recipe_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Recipe-book discovery requires both laboratory extract and a real Symbiosemyzel find.
unlock_path = RES / "data/sporenwerk/advancements/recipes/misc/sporenfiltereinsatz_mutagen.json"
unlock = json.loads(unlock_path.read_text(encoding="utf-8"))
require(unlock.get("parent") == "sporenwerk:mutagen_laboratory",
        "mutagenic cartridge research must remain under the laboratory milestone")
criteria = unlock.setdefault("criteria", {})
criteria.setdefault("discover_mutagen_extract", {
    "trigger": "minecraft:inventory_changed",
    "conditions": {"items": [{"items": ["sporenwerk:mutagenextrakt"]}]}
})
criteria["discover_symbiosis_mycelium"] = {
    "trigger": "minecraft:inventory_changed",
    "conditions": {"items": [{"items": ["sporenwerk:symbiosemyzel"]}]}
}
unlock["requirements"] = [["discover_mutagen_extract"], ["discover_symbiosis_mycelium"]]
unlock["rewards"] = {"recipes": ["sporenwerk:sporenfiltereinsatz_mutagen"]}
unlock_path.write_text(json.dumps(unlock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# The Symbiosemyzel item now documents its two existing uses plus the new high-tier cartridge.
item_path = SRC / "item/SymbiosemyzelItem.java"
item_source = item_path.read_text(encoding="utf-8")
tooltip_anchor = """        tooltip.add(Component.translatable("tooltip.sporenwerk.symbiosemyzel.2")
                .withStyle(ChatFormatting.AQUA));"""
tooltip_addition = tooltip_anchor + """
        tooltip.add(Component.translatable("tooltip.sporenwerk.symbiosemyzel.3")
                .withStyle(ChatFormatting.LIGHT_PURPLE));"""
replace_once(item_path, tooltip_anchor, tooltip_addition, "Symbiosemyzel tooltip")

# Extend the existing action-driven scan with the number of distinct crop species observed
# across its surveyed area. This is an area total, not a promise that a local cluster qualifies.
scanner_path = SRC / "item/FeldscannerItem.java"
scanner = scanner_path.read_text(encoding="utf-8")
replace_once(
    scanner_path,
    "int maxRelaySignal, int maxStationSignal, int nearbyPirscher) {}",
    "int maxRelaySignal, int maxStationSignal, int nearbyPirscher, int cropSpecies) {}",
    "AreaSurvey record"
)
replace_once(
    scanner_path,
    "        int mutatedCrops = 0;",
    """        int mutatedCrops = 0;
        boolean hasFiberCrop = false;
        boolean hasAmberCrop = false;
        boolean hasRootCrop = false;
        boolean hasFilterMossCrop = false;""",
    "area survey crop counters"
)
scanner = scanner_path.read_text(encoding="utf-8")
species_probe = """                    if (state.is(ModBlocks.FASERROHR.get())) hasFiberCrop = true;
                    else if (state.is(ModBlocks.BERNSTEINKAPPE.get())) hasAmberCrop = true;
                    else if (state.is(ModBlocks.ROTWURZEL.get())) hasRootCrop = true;
                    else if (state.is(ModBlocks.FILTERMOOS.get())) hasFilterMossCrop = true;
"""
if species_probe not in scanner:
    anchor = """                    if (state.getBlock() instanceof AbstractSporeCropBlock
                            && state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            && state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0) {
                        mutatedCrops++;
                    }"""
    require(anchor in scanner, "could not locate crop mutation count in the field scanner")
    scanner_path.write_text(scanner.replace(anchor, species_probe + anchor, 1), encoding="utf-8")

replace_once(
    scanner_path,
    "        int nearbyPirscher = level.getEntitiesOfClass(KristallpirscherEntity.class,",
    """        int cropSpecies = (hasFiberCrop ? 1 : 0) + (hasAmberCrop ? 1 : 0)
                + (hasRootCrop ? 1 : 0) + (hasFilterMossCrop ? 1 : 0);
        int nearbyPirscher = level.getEntitiesOfClass(KristallpirscherEntity.class,""",
    "crop-species survey total"
)
replace_once(
    scanner_path,
    "                maxRelaySignal, maxStationSignal, nearbyPirscher);",
    "                maxRelaySignal, maxStationSignal, nearbyPirscher, cropSpecies);",
    "AreaSurvey construction"
)
report_anchor = """        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey.crops",
                survey.mutatedCrops()).withStyle(ChatFormatting.GOLD), false);"""
report_addition = report_anchor + """
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey.biodiversity",
                survey.cropSpecies()).withStyle(survey.cropSpecies() >= 3
                        ? ChatFormatting.GREEN : ChatFormatting.GRAY), false);"""
replace_once(scanner_path, report_anchor, report_addition, "biodiversity scanner report")

# DE/EN translations make the exact condition clear without suggesting a distant crop is nearby.
for locale, entries in {
    "de_de.json": {
        "tooltip.sporenwerk.symbiosemyzel.3": "Forschungszutat für den mutagenen Filtereinsatz der höchsten Stufe.",
        "message.sporenwerk.scanner.survey.biodiversity": "Arten im gesamten Messbereich: %1$s/4. Symbiosemyzel braucht mindestens drei Arten dicht beieinander in Feldstufe II oder III.",
        "advancements.sporenwerk.filter_mutagen_research.description": "Sichere Mutagenextrakt und Symbiosemyzel, um den höchsten Filtereinsatz freizuschalten."
    },
    "en_us.json": {
        "tooltip.sporenwerk.symbiosemyzel.3": "Research ingredient for the highest-tier Mutagenic Filter Cartridge.",
        "message.sporenwerk.scanner.survey.biodiversity": "Species across the full survey area: %1$s/4. Symbiosis Mycelium needs at least three species close together in a tier-II or tier-III field.",
        "advancements.sporenwerk.filter_mutagen_research.description": "Secure Mutagen Extract and Symbiosis Mycelium to unlock the highest-tier filter cartridge."
    }
}.items():
    locale_path = ASSETS / "lang" / locale
    locale_data = json.loads(locale_path.read_text(encoding="utf-8"))
    locale_data.update(entries)
    locale_path.write_text(json.dumps(locale_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Keep legacy current-version assertions aligned while retaining historical release notes.
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "Aktueller Entwicklungsstand: 1.46.0" in line:
            lines[index] = line.replace("Aktueller Entwicklungsstand: 1.46.0",
                                        "Aktueller Entwicklungsstand: 1.47.0")
            changed = True
            line = lines[index]
        if r"1\.46\.0" not in line or "version" not in line.lower():
            continue
        newer = line.replace(r"1\.46\.0", r"1\.47\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.46.0" in lines[following] or "version must be 1.46.0" in lines[following]:
                lines[following] = lines[following].replace("1.46.0", "1.47.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.47.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.47.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.47.0 — Symbiose-Forschung und Filter-Endstufe

- **Ökologie wird zur Ausrüstungsprogression:** Der mutagene Filtereinsatz der höchsten Stufe benötigt jetzt Symbiosemyzel zusätzlich zu verstärktem Einsatz, Mutagenextrakt und Amethystsplitter.
- **Echte Forschungsfreigabe:** Der Rezeptfortschritt verlangt sowohl Mutagenextrakt als auch einen Fund Symbiosemyzel. Das Item erklärt nun seine Rolle in Landwirtschaft, Dämpferwartung und Atemschutz.
- **Mehr Erkenntnis aus dem Feldscanner:** Der Umgebungsbericht zählt die vier Sporenwerk-Pflanzenarten im gesamten Messbereich und nennt ausdrücklich, dass drei verschiedene Arten dicht beieinander in Feldstufe II/III wachsen müssen. Der Wert ist ein Bereichsgesamtwert, kein falsches Versprechen über einen lokalen Cluster.
- **Bestehende Balance bleibt erhalten:** Filterhaltbarkeit, serverseitige Forschungsprüfung und übrige Komponenten der Upgrade-Kette bleiben unverändert; nur die höchste Rezeptstufe bekommt die neue ökologische Zutat.
- **Qualitätssicherung:** Regressionen prüfen Rezeptbestandteile und AND-Freigabe, Scannerzählung, Ressourcenreferenzen sowie DE/EN-Hinweise. Forge-Build, JAR-Prüfung und dedizierter Serverstart bleiben Pflicht.

"""
if "## Version 1.47.0 — Symbiose-Forschung und Filter-Endstufe" not in readme:
    marker = "## Version 1.46.0 — Mutagen-Symbiose und nachhaltige Resonanzpflege"
    index = readme.find(marker)
    require(index >= 0, "could not locate 1.46.0 release notes")
    readme = readme[:index] + section + readme[index:]
headline = "**Aktueller Entwicklungsstand: 1.47.0 — Symbiose-Forschung, Filter-Endstufe und Biodiversitätsdiagnose.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
old_focus = """## Aktueller Schwerpunkt — 1.46.0

- Artenvielfalt wird zur Spielmechanik: Drei verschiedene Sporenwerk-Pflanzen in einem begrenzten Cluster können unter Mutagenstufe II/III Symbiosemyzel erzeugen.
- Manuelle Ernte und Feldsammler verwenden dieselbe Regel; der Maschinenpuffer reserviert den Bonusfund, bevor Energie oder Pflanzenzustand verändert werden.
- Symbiosemyzel verbindet Landwirtschaft und Abwehrtechnik, indem es bei Resonanzdämpfern eine einzelne Ladung wiederherstellt und gespeicherte Relais-Signale aktualisieren lässt.
- Forschungsfortschritt, Tooltipps, Item-Textur, DE/EN-Texte und Vorschau machen die neue Schleife auffindbar und verständlich.
- Die Release-Pipeline prüft Artenzählung, Feldstärkeschwellen, atomare Ausgabe, Dämpfer- und Relaisverhalten, Forge-Build, JAR und dedizierten Serverstart."""
new_focus = """## Aktueller Schwerpunkt — 1.47.0

- Biodiversität verbindet Feldwirtschaft und High-End-Atemschutz: Symbiosemyzel ist jetzt eine erforderliche Zutat für den mutagenen Filtereinsatz der höchsten Stufe.
- Die Rezeptfreigabe erfordert zwei reale Forschungsfunde, statt nur einen allgemeinen Laborfortschritt.
- Der Feldscanner zeigt, wie viele verschiedene Sporenwerk-Pflanzenarten im gescannten Gesamtbereich vorkommen, und erklärt die engere Clusterbedingung für Symbiosemyzel.
- Die neue Diagnose bleibt ein einmaliger, geladene-Chunks-respektierender Scan ohne Tick-Schleife.
- Release-QA umfasst Rezept- und Forschungslogik, DE/EN-Texte, Forge-Build, installierbare JAR und dedizierten Serverstart."""
if old_focus in readme:
    readme = readme.replace(old_focus, new_focus, 1)
else:
    focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
    if focus_lines:
        readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.47.0", 1)
readme_path.write_text(readme, encoding="utf-8")

print("Sporenwerk 1.47.0 generated: Symbiosemyzel-gated filter progression, AND-based research unlock, and biodiversity scanner diagnosis.")
