#!/usr/bin/env python3
"""Add local biodiversity readiness and actionable symbiosis advice to the Mutagen Field Control Station (1.76.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Field-station biodiversity 1.76: " + message)


def replace_once(path, old, new, label):
    content = path.read_text(encoding="utf-8")
    if new in content:
        return
    require(old in content, "could not locate " + label)
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


station_path = SRC / "block/MutagenFieldControlStationBlock.java"
station = station_path.read_text(encoding="utf-8")
for imp, anchor in (
    ("import de.sporenwerk.infection.MutationField;", "import de.sporenwerk.registry.ModBlocks;"),
    ("import net.minecraft.world.level.block.CropBlock;", "import net.minecraft.world.level.block.Block;"),
    ("import java.util.HashMap;", "import java.util.ArrayList;"),
    ("import java.util.Map;", "import java.util.List;"),
):
    if imp not in station:
        require(anchor in station, "missing Java import anchor " + anchor)
        station = station.replace(anchor, anchor + "\n" + imp, 1)
station_path.write_text(station, encoding="utf-8")

station = station_path.read_text(encoding="utf-8")
counter_anchor = """        int soil = 0, highSoil = 0, crops = 0, standard = 0, reinforced = 0, advanced = 0;
        int poweredWards = 0, dampeners = 0, chargedDampeners = 0, availablePulses = 0;"""
counter_add = counter_anchor + """
        int cropSpeciesMask = 0;
        int matureCrops = 0;
        int symbiosisReadyCrops = 0;
        Map<Long, Integer> cropKindsByPosition = new HashMap<>();
        List<BlockPos> matureCropPositions = new ArrayList<>();"""
replace_once(station_path, counter_anchor, counter_add, "bounded survey counters")

crop_counter = "                    if (bs.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL) && bs.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0) crops++;"
crop_add = crop_counter + """
                    int cropKind = bs.is(ModBlocks.FASERROHR.get()) ? 1
                            : bs.is(ModBlocks.BERNSTEINKAPPE.get()) ? 2
                            : bs.is(ModBlocks.ROTWURZEL.get()) ? 4
                            : bs.is(ModBlocks.FILTERMOOS.get()) ? 8 : 0;
                    if (cropKind != 0) {
                        cropSpeciesMask |= cropKind;
                        cropKindsByPosition.put(cursor.asLong(), cropKind);
                        if (bs.getBlock() instanceof CropBlock cropBlock && cropBlock.isMaxAge(bs)) {
                            matureCrops++;
                            matureCropPositions.add(cursor.immutable());
                        }
                    }"""
replace_once(station_path, crop_counter, crop_add, "crop diversity collection")

network_anchor = "        int networkMembers = 0;"
biodiversity = """        // Reuse the bounded scan snapshot to find mature harvest centers with at least
        // three distinct species within the same 7x3x7 neighbourhood as MutagenSymbiosis.
        // Only those candidates need a live operational field-strength query.
        BlockPos.MutableBlockPos speciesProbe = new BlockPos.MutableBlockPos();
        int symbiosisRadiusSquared = 3 * 3;
        for (BlockPos maturePos : matureCropPositions) {
            int nearbySpeciesMask = 0;
            speciesSearch:
            for (int dx = -3; dx <= 3; dx++) {
                for (int dz = -3; dz <= 3; dz++) {
                    if (dx * dx + dz * dz > symbiosisRadiusSquared) continue;
                    for (int dy = -1; dy <= 1; dy++) {
                        speciesProbe.set(maturePos.getX() + dx, maturePos.getY() + dy,
                                maturePos.getZ() + dz);
                        nearbySpeciesMask |= cropKindsByPosition.getOrDefault(speciesProbe.asLong(), 0);
                        if (Integer.bitCount(nearbySpeciesMask) >= 3) break speciesSearch;
                    }
                }
            }
            if (Integer.bitCount(nearbySpeciesMask) >= 3
                    && MutationField.mutagenStrengthAt(level, maturePos) >= 2) {
                symbiosisReadyCrops++;
            }
        }

"""
if "int symbiosisRadiusSquared = 3 * 3;" not in station_path.read_text(encoding="utf-8"):
    replace_once(station_path, network_anchor, biodiversity + network_anchor,
                 "local biodiversity readiness analysis")

old_return = "return new Survey(soil, highSoil, crops, standard, reinforced, advanced, networkMembers, poweredWards, dampeners, chargedDampeners, availablePulses, sirenSignals, criticalSirenSignals, highestSirenSignal);"
new_return = "return new Survey(soil, highSoil, crops, standard, reinforced, advanced, networkMembers, poweredWards, dampeners, chargedDampeners, availablePulses, sirenSignals, criticalSirenSignals, highestSirenSignal, Integer.bitCount(cropSpeciesMask), matureCrops, symbiosisReadyCrops);"
new_return = "return new Survey(soil, highSoil, crops, standard, reinforced, advanced, networkMembers, poweredWards, dampeners, chargedDampeners, availablePulses, Integer.bitCount(cropSpeciesMask), matureCrops, symbiosisReadyCrops);"
replace_once(station_path, old_return, new_return, "survey record result")
old_record = "private record Survey(int soil, int highSoil, int crops, int standard, int reinforced, int advanced, int networkMembers, int poweredWards, int dampeners, int chargedDampeners, int availablePulses, int sirenSignals, int criticalSirenSignals, int highestSirenSignal) {}"
new_record = "private record Survey(int soil, int highSoil, int crops, int standard, int reinforced, int advanced, int networkMembers, int poweredWards, int dampeners, int chargedDampeners, int availablePulses, int sirenSignals, int criticalSirenSignals, int highestSirenSignal, int cropSpecies, int matureCrops, int symbiosisReadyCrops) {}"
new_record = "private record Survey(int soil, int highSoil, int crops, int standard, int reinforced, int advanced, int networkMembers, int poweredWards, int dampeners, int chargedDampeners, int availablePulses, int cropSpecies, int matureCrops, int symbiosisReadyCrops) {}"
replace_once(station_path, old_record, new_record, "survey result schema")

report_anchor = '        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.crops", s.crops()).withStyle(ChatFormatting.GREEN), false);'
report = report_anchor + """
        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.biodiversity",
                s.cropSpecies(), s.matureCrops()).withStyle(ChatFormatting.GREEN), false);
        if (s.symbiosisReadyCrops() > 0) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.symbiosis_ready", s.symbiosisReadyCrops())
                    .withStyle(ChatFormatting.LIGHT_PURPLE), false);
        } else {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.symbiosis_advice")
                    .withStyle(ChatFormatting.YELLOW), false);
        }"""
replace_once(station_path, report_anchor, report, "biodiversity status and guidance")
station = station_path.read_text(encoding="utf-8")
for token in ("MutationField.mutagenStrengthAt(level, maturePos) >= 2",
              "level.hasChunkAt(new BlockPos(x, minY, z))",
              "cropKindsByPosition.getOrDefault(speciesProbe.asLong(), 0)",
              "Integer.bitCount(nearbySpeciesMask) >= 3",
              "s.symbiosisReadyCrops()"):
    require(token in station, "station biodiversity contract missing " + token)
require("getChunk(" not in station and "getChunkNow(" not in station,
        "biodiversity audit must never force-load chunks")

for locale, values in {
    "de_de.json": {
        "message.sporenwerk.fieldstation.biodiversity": "Kulturvielfalt: %s Sporenwerk-Arten | reife Pflanzen: %s.",
        "message.sporenwerk.fieldstation.symbiosis_ready": "Symbiose-Ernte möglich: %s reife Pflanzen liegen in einer artenreichen Kultur mit aktivem Mutagenfeld II/III. Reife Pflanzen ernten, dann Resonanzsporen-Kapseln aus Symbiosemyzel, mutagenen Sporen, Knochenmehl und Redstone herstellen.",
        "message.sporenwerk.fieldstation.symbiosis_advice": "Noch kein reifer Symbiose-Erntebereich im Scan erkannt. Mindestens drei Sporenwerk-Arten dicht beieinander pflanzen und ein aktives Mutagenfeld der Stufe II/III sicherstellen."
    },
    "en_us.json": {
        "message.sporenwerk.fieldstation.biodiversity": "Crop diversity: %s Sporenwerk species | mature crops: %s.",
        "message.sporenwerk.fieldstation.symbiosis_ready": "Symbiosis harvest opportunity: %s mature crops sit in a diverse crop cluster with an active tier-II/III Mutagen field. Harvest mature crops, then craft Resonance Spore Capsules from Symbiosis Mycelium, Mutagen spores, bone meal and redstone.",
        "message.sporenwerk.fieldstation.symbiosis_advice": "No mature symbiosis harvest zone detected in this scan. Plant at least three Sporenwerk crop species close together and ensure an active tier-II/III Mutagen field."
    }
}.items():
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Advance active-version assertions. Historical release coverage remains in each test;
# only assertions that specifically identify the current artifact/README move forward.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_fieldstation_biodiversity_176.py":
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.75.0",
                               "Aktueller Entwicklungsstand: 1.76.0")
    updated = updated.replace(r"1\.75\.0", r"1\.76\.0")
    updated = updated.replace("artifact must be version 1.75.0",
                              "artifact must be version 1.76.0")
    updated = updated.replace(
        '"Version 1.75.0" in readme and "Version 1.74.0" in readme',
        '"Version 1.76.0" in readme and "Version 1.75.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.76.0'", (ROOT / "build.gradle").read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Gradle artifact version")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.76.0 — Biodiversitätsdiagnose der Mutagen-Kontrollstation

- **Artenzahl statt bloßer Pflanzenmenge:** Die manuelle Stationserhebung zählt die vier Sporenwerk-Kulturarten sowie reife Pflanzen innerhalb des bestehenden Scanbereichs.
- **Tatsächliche Symbiose-Gelegenheit:** Der Bericht prüft das bekannte 7×3×7-Nachbarschaftsmuster, mindestens drei verschiedene Arten, eine reife Erntepflanze und ein aktuell wirksames Mutagenfeld der Stärke II/III. Er schätzt nicht anhand bloßer Bodenzahlen.
- **Konkrete Handlungsempfehlung:** Bei geeigneten Erntezentren erklärt die Station, wie durch Ernte Symbiosemyzel für Resonanzsporen-Kapseln gewonnen werden kann. Andernfalls nennt sie die fehlenden Voraussetzungen.
- **Einmaliger, sicherer Scan:** Biodiversitätsnachbarschaften werden aus dem bereits erfassten Speicherbild gezählt; nur passende reife Kandidaten erhalten eine aktuelle Feldstärkeabfrage. Nicht geladene Chunks werden übersprungen und kein Ticker wird ergänzt.
- **Qualitätssicherung:** Tests decken Arten-Bitmaske, lokale Nachbarschaft, Reifegrad, live Feldstärke, DE/EN-Empfehlungen, Versionsmetadaten und die unveränderte Containment-Erhebung ab.

"""
current = """## Aktueller Entwicklungsschritt — 1.76.0

- **Bessere Feldkontrolle:** Die Kontrollstation meldet jetzt Kulturvielfalt und reife Pflanzen, nicht nur die Zahl mutagenaktiver Pflanzen.
- **Symbiose-Diagnose:** Reife Erntezentren werden gegen die echte lokale Artenvielfalt und aktuelle Feldstärke II/III geprüft.
- **Direkte Lernhilfe:** Die Station erklärt, wie aus einer passenden Kultur Symbiosemyzel und danach Resonanzsporen-Kapseln gewonnen werden können.
- **Containment bleibt bounded:** Bestehender Scanradius, geladene Chunks, Stabilisatornetz, Sporenabwehr und Dämpferbericht bleiben erhalten.

"""
if "## Version 1.76.0 — Biodiversitätsdiagnose der Mutagen-Kontrollstation" not in readme:
    marker = "## Version 1.75.0 — Resonanzsporen-Kapsel für Kultur und Containment"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.75 release heading")
    readme = readme[:idx] + release + readme[idx:]
if "## Aktueller Entwicklungsschritt — 1.76.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.75.0"
    idx = readme.find(marker)
    require(idx >= 0, "could not find current 1.75 development section")
    readme = readme[:idx] + current + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.75.0 — Resonanzsporen-Kapsel für Kultur und Containment.**",
    "**Aktueller Entwicklungsstand: 1.76.0 — Biodiversitätsdiagnose der Mutagen-Kontrollstation.**")
require("Aktueller Entwicklungsstand: 1.76.0" in readme,
        "README current version headline was not updated")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.76.0 generated: the Mutagen Field Control Station detects mature, locally diverse harvest centers with a live tier-II/III field and provides capsule-production advice.")
