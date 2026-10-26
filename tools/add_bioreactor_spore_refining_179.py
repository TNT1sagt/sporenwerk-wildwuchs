#!/usr/bin/env python3
"""Add a balanced Mutagene Sporen refining route to the Biomass Bioreactor (1.79.0)."""
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
        raise SystemExit("Spore refining 1.79: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# Mutagene Sporen already come from mature, mutagenically active crops and Mutagen Blooms.
# Let players refine four collected spores into one Mutagen Extract, so production can continue
# even before a rare Symbiosemyzel harvest. The original 180 FE mycelium process stays superior.
machine_path = SRC / "block/entity/MachineBlockEntity.java"
machine = machine_path.read_text(encoding="utf-8")
if "else if (input.is(ModItems.MUTAGENE_SPOREN.get()))" not in machine:
    machine_tail = """            inventory.extractItem(0, 1, false);
            storedPoints = Math.min(1_000_000, storedPoints + 10);
            skills.addCraft();
            setChanged();
        } else if (input.is(ModItems.SYMBIOSEMYZEL.get())) {
            ItemStack extract = new ItemStack(ModItems.MUTAGENEXTRAKT.get());
            if (!canFitOutput(extract) || !consumePower(180)) { progress = 0; return; }
            progress = 0;
            if (!insertOutput(extract)) return;
            inventory.extractItem(0, 1, false);
            storedPoints = Math.min(1_000_000, storedPoints + 25);
            skills.addCraft();
            setChanged();
        } else progress = 0;"""
    machine_tail_new = """            inventory.extractItem(0, 1, false);
            storedPoints = Math.min(1_000_000, storedPoints + 10);
            skills.addCraft();
            setChanged();
        } else if (input.is(ModItems.SYMBIOSEMYZEL.get())) {
            ItemStack extract = new ItemStack(ModItems.MUTAGENEXTRAKT.get());
            if (!canFitOutput(extract) || !consumePower(180)) { progress = 0; return; }
            progress = 0;
            if (!insertOutput(extract)) return;
            inventory.extractItem(0, 1, false);
            storedPoints = Math.min(1_000_000, storedPoints + 25);
            skills.addCraft();
            setChanged();
        } else if (input.is(ModItems.MUTAGENE_SPOREN.get())) {
            final int sporeBatchSize = 4;
            final int sporeBatchEnergy = 240;
            if (input.getCount() < sporeBatchSize) { progress = 0; return; }
            ItemStack extract = new ItemStack(ModItems.MUTAGENEXTRAKT.get());
            if (!canFitOutput(extract) || !consumePower(sporeBatchEnergy)) { progress = 0; return; }
            progress = 0;
            if (!insertOutput(extract)) return;
            inventory.extractItem(0, sporeBatchSize, false);
            storedPoints = Math.min(1_000_000, storedPoints + 18);
            skills.addCraft();
            setChanged();
        } else progress = 0;"""
    replace_once(machine_path, machine_tail, machine_tail_new, "final bioreactor processing branch")

machine = machine_path.read_text(encoding="utf-8")
spore_branch_start = machine.find("else if (input.is(ModItems.MUTAGENE_SPOREN.get()))")
require(spore_branch_start >= 0, "Mutagene Sporen refining branch was not added")
spore_branch_end = machine.find("} else progress = 0;", spore_branch_start)
require(spore_branch_end > spore_branch_start, "spore refining branch does not end cleanly")
branch = machine[spore_branch_start:spore_branch_end]
require(branch.index("input.getCount() < sporeBatchSize") < branch.index("canFitOutput(extract)")
        < branch.index("consumePower(sporeBatchEnergy)")
        < branch.index("insertOutput(extract)")
        < branch.index("inventory.extractItem(0, sporeBatchSize, false)"),
        "spores must be validated, then output and power secured before the input is consumed")

# Explain the alternative production route on the actual inventory item, not only in the README.
item_path = SRC / "item/MutageneSporenItem.java"
item = item_path.read_text(encoding="utf-8")
tooltip_anchor = '        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagene_sporen.2").withStyle(ChatFormatting.AQUA));'
tooltip_addition = tooltip_anchor + '\n        tooltip.add(Component.translatable("tooltip.sporenwerk.mutagene_sporen.3").withStyle(ChatFormatting.GREEN));'
replace_once(item_path, tooltip_anchor, tooltip_addition, "mutagene spore tooltip")

for locale, value in (
    ("de_de.json", "Im Biomasse-Bioreaktor: 4 Sporen + 240 FE ergeben 1 Mutagenextrakt."),
    ("en_us.json", "In the Biomass Bioreactor: 4 spores + 240 FE refine into 1 Mutagen Extract."),
):
    locale_path = ASSETS / "lang" / locale
    data = json.loads(locale_path.read_text(encoding="utf-8"))
    data["tooltip.sporenwerk.mutagene_sporen.3"] = value
    locale_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Move current-version regression contracts forward but preserve the entire release history.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_bioreactor_spore_refining_179.py":
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.78.0",
                               "Aktueller Entwicklungsstand: 1.79.0")
    if "build.gradle" in original:
        updated = updated.replace(r"1\.78\.0", r"1\.79\.0")
        updated = updated.replace("artifact must be version 1.78.0",
                                  "artifact must be version 1.79.0")
    updated = updated.replace(
        '"Version 1.78.0" in readme and "Version 1.77.0" in readme',
        '"Version 1.79.0" in readme and "Version 1.78.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.79.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Forge artifact version")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.79.0

- **Zweiter Weg zum Mutagenextrakt:** Der Biomasse-Bioreaktor veredelt jetzt vier Mutagene Sporen zu einem Mutagenextrakt für 240 FE. Das ergänzt den seltenen Symbiosemyzel-Prozess mit 180 FE, ersetzt ihn aber nicht.
- **Feldwirtschaft wird zur industriellen Versorgung:** Mutagene Sporen aus reifen mutagenaktiven Kulturen und Mutagenblüten können in einem kontrollierten Produktionsschritt zu einem Laborzwischenprodukt werden.
- **Saubere Eingangs-/Ausgangsgrenze:** Weniger als vier Sporen, fehlender Ausgabepuffer oder fehlende Energie lösen keinen Teilverbrauch aus. Der Eingang wird erst entfernt, nachdem die Ausgabekapazität und Energie geprüft und das Produkt eingefügt wurden.
- **Hilfreiche Item-Erklärung:** Tooltip, deutsche/englische Texte und Release-Notizen nennen Menge, Energiepreis und Zielprodukt.
- **Qualität:** Neue Regression prüft den Produktionszweig, Reihenfolge der Transaktion, Erhalt des Myzel-Rezepts und alle Release-Metadaten; vollständiger Forge-Build und Serverstart laufen im Workflow.

"""
if "## Aktueller Entwicklungsschritt — 1.79.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.78.0"
    require(marker in readme, "could not find current 1.78 development section")
    readme = readme.replace(marker, current + marker, 1)

release = """## Version 1.79.0 — Mutagene Sporen im Biomasse-Bioreaktor veredeln

- **Alternativer Extraktpfad:** Vier Mutagene Sporen werden für 240 FE zu einem Mutagenextrakt verarbeitet. Das ermöglicht weitere Laborproduktion auch dann, wenn gerade kein Symbiosemyzel verfügbar ist.
- **Balance zwischen den Pfaden:** Ein Symbiosemyzel liefert weiterhin einen Extrakt für 180 FE; die Sporenroute benötigt eine größere Feldernte und mehr Energie.
- **Transaktionsschutz:** Bei weniger als vier Sporen, vollem Ausgabepuffer oder fehlender Energie wird kein Eingabestapel verbraucht. Die Verarbeitung nutzt die vorhandenen Maschineninventare und erzeugt keine losen Drop-Entitäten.
- **Ökologie, Maschine und Forschung:** Mutagenaktive Kulturen und Blüten liefern Feldmaterial, das der Bioreaktor in den vorhandenen Mutagenextrakt-Kreislauf einspeist.
- **Qualitätssicherung:** Regression prüft Menge, Energie, Reihenfolge von Einfügen und Verbrauch, Erhalt des Symbiosemyzel-Prozesses, Itemhinweise, DE/EN-Texte und Release-Metadaten.

"""
if "## Version 1.79.0 — Mutagene Sporen im Biomasse-Bioreaktor veredeln" not in readme:
    marker = "## Version 1.78.0 —"
    require(marker in readme, "could not find 1.78 release section")
    readme = readme.replace(marker, release + marker, 1)

readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.78.0 — Forschungszweig für abgefangene Mutagenblüten.**",
    "**Aktueller Entwicklungsstand: 1.79.0 — Mutagene Sporen im Biomasse-Bioreaktor veredeln.**")
require("Aktueller Entwicklungsstand: 1.79.0" in readme,
        "README current-version headline was not updated")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.79.0 generated: Mutagene Sporen now provide a balanced, transactional alternative route to Mutagen Extract in the Biomass Bioreactor.")
