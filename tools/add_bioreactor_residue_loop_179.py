#!/usr/bin/env python3
"""Close the automated crop-residue -> biomass -> mycelium-compost production loop (1.79.0)."""
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
        raise SystemExit("Bioreactor residue loop 1.79: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# A field collector already buffers mature-crop plant residue instead of spawning items.
# The Biomass Bioreactor now recovers four residues into one Biomass stack, which its
# existing 80-FE process can refine into two Myzelkompost. This creates an automated
# crop-waste -> biomass -> fertilizer loop without bypassing the existing second stage.
machine_path = SRC / "block/entity/MachineBlockEntity.java"
machine = machine_path.read_text(encoding="utf-8")
if "final int residueBatchSize = 4" not in machine:
    biomass_anchor = "} else if (input.is(ModItems.BIOMASSE.get())) {"
    residue_branch = """} else if (input.is(ModItems.PFLANZENRESTE.get())) {
            final int residueBatchSize = 4;
            final int residueBatchEnergy = 60;
            if (input.getCount() < residueBatchSize) { progress = 0; return; }
            ItemStack biomass = new ItemStack(ModItems.BIOMASSE.get());
            if (!canFitOutput(biomass) || !consumePower(residueBatchEnergy)) { progress = 0; return; }
            progress = 0;
            if (!insertOutput(biomass)) return;
            inventory.extractItem(0, residueBatchSize, false);
            storedPoints = Math.min(1_000_000, storedPoints + 12);
            skills.addCraft();
            setChanged();
        """ + biomass_anchor
    replace_once(machine_path, biomass_anchor, residue_branch,
                 "Biomass branch to insert the residue-refining transaction")

machine = machine_path.read_text(encoding="utf-8")
require("final int residueBatchSize = 4" in machine,
        "residue-to-biomass branch was not installed")
residue_index = machine.index("final int residueBatchSize = 4")
branch_start = machine.rfind("else if (input.is(ModItems.PFLANZENRESTE.get()))", 0, residue_index)
branch_end = machine.find(biomass_anchor, residue_index)
require(branch_start >= 0 and branch_end > residue_index,
        "could not isolate residue refining from the original Biomasse branch")
branch = machine[branch_start:branch_end]
for token in (
    "input.getCount() < residueBatchSize",
    "final int residueBatchEnergy = 60",
    "new ItemStack(ModItems.BIOMASSE.get())",
    "canFitOutput(biomass)",
    "consumePower(residueBatchEnergy)",
    "insertOutput(biomass)",
    "inventory.extractItem(0, residueBatchSize, false)",
    "storedPoints = Math.min(1_000_000, storedPoints + 12)",
):
    require(token in branch, "residue-refining transaction missing " + token)
ordered = (
    "input.getCount() < residueBatchSize",
    "canFitOutput(biomass)",
    "consumePower(residueBatchEnergy)",
    "insertOutput(biomass)",
    "inventory.extractItem(0, residueBatchSize, false)",
)
positions = [branch.index(token) for token in ordered]
require(positions == sorted(positions),
        "validate batch size/output/power and insert output before consuming residues")
require("new ItemStack(ModItems.MYZELKOMPOST.get(), 2)" in machine
        and "consumePower(80)" in machine,
        "existing Biomasse -> two Myzelkompost refining stage must remain intact")

# Add a client-side tooltip through Forge's event bus without replacing the already-registered item.
# The custom residue item ID and its existing item model remain unchanged.
tooltip_path = SRC / "client/PflanzenresteTooltipEvents.java"
tooltip_path.parent.mkdir(parents=True, exist_ok=True)
tooltip_path.write_text("""\
package de.sporenwerk.client;

import de.sporenwerk.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.entity.player.ItemTooltipEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Shows the two-stage automated residue path on the existing Pflanzenreste inventory item. */
@Mod.EventBusSubscriber(modid = "sporenwerk", bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class PflanzenresteTooltipEvents {
    private PflanzenresteTooltipEvents() {}

    @SubscribeEvent
    public static void onItemTooltip(ItemTooltipEvent event) {
        if (!event.getItemStack().is(ModItems.PFLANZENRESTE.get())) return;
        event.getToolTip().add(Component.translatable("tooltip.sporenwerk.pflanzenreste.refining")
                .withStyle(ChatFormatting.GREEN));
        event.getToolTip().add(Component.translatable("tooltip.sporenwerk.pflanzenreste.loop")
                .withStyle(ChatFormatting.GRAY));
    }
}
""", encoding="utf-8")

# Keep user-facing instructions in the actual Minecraft resource translations.
for locale, entries in (
    ("de_de.json", {
        "tooltip.sporenwerk.pflanzenreste.refining": "Biomasse-Bioreaktor: 4 Pflanzenreste + 60 FE ergeben 1 Biomasse.",
        "tooltip.sporenwerk.pflanzenreste.loop": "Biomasse wird dort weiter zu 2 Myzelkompost verarbeitet."
    }),
    ("en_us.json", {
        "tooltip.sporenwerk.pflanzenreste.refining": "Biomass Bioreactor: 4 plant residues + 60 FE refine into 1 Biomass.",
        "tooltip.sporenwerk.pflanzenreste.loop": "Biomass can then be processed into 2 Mycelium Compost."
    }),
):
    locale_path = ASSETS / "lang" / locale
    locale_data = json.loads(locale_path.read_text(encoding="utf-8"))
    locale_data.update(entries)
    locale_path.write_text(json.dumps(locale_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Move current-version regression contracts forward but keep historical releases intact.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_bioreactor_residue_loop_179.py":
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
require(count == 1, "could not advance the Forge artifact version")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.79.0

- **Automatisierte Verwertung von Pflanzenresten:** Der Biomasse-Bioreaktor wandelt vier Pflanzenreste für 60 FE in eine Biomasse um. Das erweitert die bestehende Verarbeitung von Biomasse zu zwei Myzelkompost für 80 FE.
- **Geschlossener Farmkreislauf:** Der Feldsammler liefert bei reifen Kulturen gelegentlich Pflanzenreste; der Bioreaktor macht daraus Biomasse und anschließend Dünger. Das ergänzt die Handwerksrezeptur, ohne sie zu entfernen.
- **Saubere Transaktion:** Weniger als vier Reste, ein voller Ausgabepuffer oder fehlende Energie verbrauchen keine Eingabe. Das Produkt wird eingefügt, bevor die Reste aus dem Eingabestapel entfernt werden.
- **Erklärtes Item:** Pflanzenreste haben einen deutschen und englischen Tooltip, der Menge, Energiepreis und nächsten Verarbeitungsschritt nennt.
- **Qualität:** Regression prüft beide Bioreaktor-Stufen, Reihenfolge der Transaktion, Übersetzungen, Itemregistrierung und Release-Metadaten; Forge-Build und dedizierter Serverstart laufen im Workflow.

"""
if "## Aktueller Entwicklungsschritt — 1.79.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.78.0"
    require(marker in readme, "could not find current 1.78 development section")
    readme = readme.replace(marker, current + marker, 1)
release = """## Version 1.79.0 — Automatischer Pflanzenreste-Kreislauf

- **Neue Bioreaktor-Stufe:** Vier Pflanzenreste werden mit 60 FE zu einer Biomasse veredelt.
- **Weiter zur Düngung:** Die bestehende Biomasse-Verarbeitung erzeugt zwei Myzelkompost für 80 FE. Beide Schritte lassen sich mit dem Feldsammler zu einer automatisierten Rückführung verbinden.
- **Keine Teilverluste:** Zu kleine Stapel, fehlender Ausgabepuffer oder unzureichende Energie verbrauchen keinen Eingabestapel. Das Ergebnis wird erst eingefügt, bevor vier Reste entfernt werden.
- **Entdeckbarkeit:** Der Pflanzenreste-Tooltip erklärt den neuen Verarbeitungspfad auf Deutsch und Englisch.
- **Qualitätssicherung:** Neue Regression prüft das Eingabebündel, Energie, Ausgabereihenfolge, die bestehende Kompoststufe, beide Übersetzungen sowie den vollständigen Forge-Build und Serverstart.

"""
if "## Version 1.79.0 — Automatischer Pflanzenreste-Kreislauf" not in readme:
    marker = "## Version 1.78.0 —"
    require(marker in readme, "could not find 1.78 release section")
    readme = readme.replace(marker, release + marker, 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.78.0 — Forschungszweig für abgefangene Mutagenblüten.**",
    "**Aktueller Entwicklungsstand: 1.79.0 — Automatischer Pflanzenreste-Kreislauf.**")
require("Aktueller Entwicklungsstand: 1.79.0" in readme,
        "README current-version headline was not updated")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.79.0 generated: crop residues are now refined into Biomass and the existing Biomass -> Myzelkompost process completes the automated farm loop.")
