#!/usr/bin/env python3
"""Add localized English fallback and machine tooltips for Sporenwerk 1.1.3."""
from pathlib import Path
import json, re, sys

root = Path(sys.argv[1]).resolve()
res = root / "src/main/resources/assets/sporenwerk/lang"
de_path = res / "de_de.json"
de = json.loads(de_path.read_text(encoding="utf-8"))
de.update({
  "tooltip.sporenwerk.machine.feldsammler.line1": "Erntet reife Sporenwerk-Pflanzen im 5×3×5-Bereich.",
  "tooltip.sporenwerk.machine.feldsammler.line2": "Passende Samen in den ersten vier Eingabefächern ermöglichen Nachpflanzung.",
  "tooltip.sporenwerk.machine.feldsammler.line3": "Ernten werden im internen Ausgabepuffer gestapelt.",
  "tooltip.sporenwerk.machine.saatgutpresse.line1": "Verarbeitet Ernteprodukte zu passenden Samen und Sporen.",
  "tooltip.sporenwerk.machine.saatgutpresse.line2": "Lege Ernte in ein Eingabefach und sammle die Ausgabe rechts.",
  "tooltip.sporenwerk.machine.saatgutpresse.line3": "Der Puffer bleibt auch nach dem Weltneustart erhalten.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line1": "Verarbeitet Pflanzenreste und Biomasse zu weiterem Rohstoff.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line2": "Der interne Rohstoffwert wird gespeichert, statt Items zu spammen.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line3": "Mit Mekanism kann die Maschine FE aus Universal-Kabeln annehmen.",
  "tooltip.sporenwerk.machine.buffer": "Rechtsklick öffnet Inventar und Fortschritt."
})
de_path.write_text(json.dumps(de, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

en = {
  "itemGroup.sporenwerk": "Sporenwerk: Wildgrowth",
  "item.sporenwerk.faser": "Fiber",
  "item.sporenwerk.bernsteinkappe": "Ambercap",
  "item.sporenwerk.rotwurzel": "Redroot",
  "item.sporenwerk.filtermoos": "Filter Moss",
  "item.sporenwerk.faserrohr_samen": "Fiber Reed Seeds",
  "item.sporenwerk.bernsteinkappe_sporen": "Ambercap Spores",
  "item.sporenwerk.rotwurzel_samen": "Redroot Seeds",
  "item.sporenwerk.filtermoos_sporen": "Filter Moss Spores",
  "item.sporenwerk.pflanzenreste": "Plant Residue",
  "item.sporenwerk.biomasse": "Biomass",
  "item.sporenwerk.feldwissen": "Field Knowledge",
  "item.sporenwerk.maschinenteil": "Machine Part",
  "item.sporenwerk.filter": "Filter",
  "item.sporenwerk.feldhandbuch": "Field Handbook",
  "item.sporenwerk.verwitterte_notiz": "Weathered Field Report",
  "item.sporenwerk.daemmerling_spawn_egg": "Dämmerling Spawn Egg",
  "block.sporenwerk.faserrohr": "Fiber Reed",
  "block.sporenwerk.bernsteinkappe": "Ambercap",
  "block.sporenwerk.rotwurzel": "Redroot",
  "block.sporenwerk.filtermoos": "Filter Moss",
  "block.sporenwerk.feldsammler": "Field Collector",
  "block.sporenwerk.saatgutpresse": "Seed Press",
  "block.sporenwerk.biomasse_bioreaktor": "Biomass Bioreactor",
  "entity.sporenwerk.daemmerling": "Dämmerling",
  "gui.sporenwerk.input": "INPUT",
  "gui.sporenwerk.output": "BUFFER OUTPUT",
  "gui.sporenwerk.skill_title": "Field Handbook — Skill Tree",
  "advancements.sporenwerk.root.title": "A Patch of Earth",
  "advancements.sporenwerk.root.description": "Find seeds, plant Fiber Reed, and harvest your first fiber.",
  "advancements.sporenwerk.first_crop.title": "Nothing Goes to Waste",
  "advancements.sporenwerk.first_crop.description": "Turn plant residue into biomass.",
  "advancements.sporenwerk.first_machine.title": "The First Machine",
  "advancements.sporenwerk.first_machine.description": "Build a machine for your first production chain.",
  "advancements.sporenwerk.larger_harvest.title": "A Bigger Harvest",
  "advancements.sporenwerk.larger_harvest.description": "Set up the Field Collector and expand production.",
  "advancements.sporenwerk.field_behind_glass.title": "The Field Behind the Glass",
  "advancements.sporenwerk.field_behind_glass.description": "Read the rare report. Some things don't grow in beds.",
  "tooltip.sporenwerk.machine.feldsammler.line1": "Harvests mature Sporenwerk crops in a 5×3×5 area.",
  "tooltip.sporenwerk.machine.feldsammler.line2": "Matching seeds in the first four input slots enable replanting.",
  "tooltip.sporenwerk.machine.feldsammler.line3": "Harvests stack in the internal output buffer.",
  "tooltip.sporenwerk.machine.saatgutpresse.line1": "Processes harvests into matching seeds and spores.",
  "tooltip.sporenwerk.machine.saatgutpresse.line2": "Place a harvest in an input slot and collect output on the right.",
  "tooltip.sporenwerk.machine.saatgutpresse.line3": "The buffer persists across world restarts.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line1": "Processes plant residue and biomass into more raw material.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line2": "Internal production value is stored instead of spawning item spam.",
  "tooltip.sporenwerk.machine.biomasse_bioreaktor.line3": "With Mekanism installed, the machine accepts FE from Universal Cables.",
  "tooltip.sporenwerk.machine.buffer": "Right-click to open inventory and progress."
}
(res / "en_us.json").write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build = root / "build.gradle"
s = build.read_text(encoding="utf-8")
s = re.sub(r"version = '[^']+'", "version = '1.1.3'", s, count=1)
build.write_text(s, encoding="utf-8")

readme = root / "README.md"
s = readme.read_text(encoding="utf-8")
s = s.replace("1.1.2", "1.1.3").replace("V1.1.2", "V1.1.3")
s += "\n\n## English localization and tooltips\nVersion 1.1.3 includes en_us fallback strings and first-use tooltips for all three machines.\n"
readme.write_text(s, encoding="utf-8")
print("Added en_us localization and machine tooltips.")
