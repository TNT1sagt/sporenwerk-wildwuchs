#!/usr/bin/env python3
"""Add Symbiosemyzel bioprocessing, precise cluster diagnostics, and first-contact ward feedback (1.48.0)."""
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
        raise SystemExit("Symbiosis lifecycle: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# 1) Give the rare ecological by-product a renewable industrial route.
# The input is removed only after output capacity and energy have both been secured.
machine_path = SRC / "block/entity/MachineBlockEntity.java"
machine_tail = """            inventory.extractItem(0, 1, false);
            storedPoints = Math.min(1_000_000, storedPoints + 10);
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
        } else progress = 0;"""
replace_once(machine_path, machine_tail, machine_tail_new, "bioreactor biomass branch ending")

# Describe the bioreactor's extract conversion in the item itself.
item_path = SRC / "item/SymbiosemyzelItem.java"
tooltip_anchor = """        tooltip.add(Component.translatable("tooltip.sporenwerk.symbiosemyzel.3")
                .withStyle(ChatFormatting.LIGHT_PURPLE));"""
tooltip_addition = tooltip_anchor + """
        tooltip.add(Component.translatable("tooltip.sporenwerk.symbiosemyzel.4")
                .withStyle(ChatFormatting.GREEN));"""
replace_once(item_path, tooltip_anchor, tooltip_addition, "Symbiosemyzel bioprocess tooltip")
for locale, key, value in (
    ("de_de.json", "tooltip.sporenwerk.symbiosemyzel.4",
     "Im Biomasse-Bioreaktor wird ein Symbiosemyzel mit 180 FE zu einem Mutagenextrakt veredelt."),
    ("en_us.json", "tooltip.sporenwerk.symbiosemyzel.4",
     "The Biomass Bioreactor refines one Symbiosis Mycelium into one Mutagen Extract for 180 FE."),
):
    locale_path = ASSETS / "lang" / locale
    locale_data = json.loads(locale_path.read_text(encoding="utf-8"))
    locale_data[key] = value
    locale_path.write_text(json.dumps(locale_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 2) Emit a restrained one-time spore burst when a powered ward first repels a Dämmerling.
# Ward ticks continue to refresh the grace timer but no longer spam particles every ten ticks.
ward_path = SRC / "block/SporeWardBlock.java"
ward = ward_path.read_text(encoding="utf-8")
for import_line in ("import net.minecraft.core.particles.ParticleTypes;",):
    if import_line not in ward:
        anchor = "import net.minecraft.core.BlockPos;"
        require(anchor in ward, "could not locate Spore Ward particle import anchor")
        ward = ward.replace(anchor, anchor + "\n" + import_line, 1)
old_ward_loop = """        for (DaemmerlingEntity mob : level.getEntitiesOfClass(DaemmerlingEntity.class, area)) {
            if (mob.isAlive()) {
                mob.getPersistentData().putLong("SporenwerkWardRepelledUntil", repelUntil);
            }
        }"""
new_ward_loop = """        for (DaemmerlingEntity mob : level.getEntitiesOfClass(DaemmerlingEntity.class, area)) {
            if (mob.isAlive()) {
                long previousRepelUntil = mob.getPersistentData().getLong("SporenwerkWardRepelledUntil");
                mob.getPersistentData().putLong("SporenwerkWardRepelledUntil", repelUntil);
                if (previousRepelUntil <= level.getGameTime()) {
                    level.sendParticles(ParticleTypes.WARPED_SPORE,
                            mob.getX(), mob.getY() + 0.8D, mob.getZ(),
                            10, 0.24D, 0.32D, 0.24D, 0.012D);
                }
            }
        }"""
if new_ward_loop not in ward:
    require(old_ward_loop in ward, "could not locate Dämmerling ward refresh loop")
    ward = ward.replace(old_ward_loop, new_ward_loop, 1)
ward_path.write_text(ward, encoding="utf-8")

# 3) Upgrade the scanner from an area-wide crop-species total to an exact, bounded local
# cluster check. Crop positions are collected during the original scan; neighborhood checks
# use only this in-memory map, so they do not read additional world blocks or load chunks.
scanner_path = SRC / "item/FeldscannerItem.java"
scanner = scanner_path.read_text(encoding="utf-8")
imports = (
    "import de.sporenwerk.infection.MutagenSymbiosis;",
    "import java.util.ArrayList;",
    "import java.util.HashMap;",
    "import java.util.List;",
    "import java.util.Map;",
)
for import_line in imports:
    if import_line not in scanner:
        anchor = "import de.sporenwerk.registry.ModBlocks;"
        require(anchor in scanner, "could not locate Feldscanner import anchor")
        scanner = scanner.replace(anchor, anchor + "\n" + import_line, 1)
scanner_path.write_text(scanner, encoding="utf-8")

replace_once(
    scanner_path,
    "int cropSpecies, boolean symbiosisCluster) {}",
    "int cropSpecies, boolean symbiosisCluster) {}",
    "AreaSurvey record",
)
# If this is the 1.47 schema, append the local-cluster boolean; otherwise fail closed.
scanner = scanner_path.read_text(encoding="utf-8")
old_record = "int nearbyPirscher, int cropSpecies) {}"
new_record = "int nearbyPirscher, int cropSpecies, boolean symbiosisCluster) {}"
if new_record not in scanner:
    require(old_record in scanner, "AreaSurvey schema must include the 1.47 crop-species total")
    scanner = scanner.replace(old_record, new_record, 1)
scanner_path.write_text(scanner, encoding="utf-8")

# Create in-memory crop-position data and a list of fully inspectable candidate centers.
scanner = scanner_path.read_text(encoding="utf-8")
vars_old = """        boolean hasFiberCrop = false;
        boolean hasAmberCrop = false;
        boolean hasRootCrop = false;
        boolean hasFilterMossCrop = false;"""
vars_new = vars_old + """
        Map<Long, Integer> cropKindsByPosition = new HashMap<>();
        List<BlockPos> clusterCandidates = new ArrayList<>();"""
if vars_new not in scanner:
    require(vars_old in scanner, "could not locate 1.47 crop species flags")
    scanner = scanner.replace(vars_old, vars_new, 1)
scanner_path.write_text(scanner, encoding="utf-8")

# The existing four species flags remain the human-readable area total. Record each crop
# for exact local clustering and check only centers whose radius fits inside the scan bounds.
scanner = scanner_path.read_text(encoding="utf-8")
crop_probe_anchor = """                    if (state.getBlock() instanceof AbstractSporeCropBlock
                            && state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            && state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0) {
                        mutatedCrops++;
                    }"""
crop_probe_addition = """                    int cropKind = state.is(ModBlocks.FASERROHR.get()) ? 1
                            : state.is(ModBlocks.BERNSTEINKAPPE.get()) ? 2
                            : state.is(ModBlocks.ROTWURZEL.get()) ? 3
                            : state.is(ModBlocks.FILTERMOOS.get()) ? 4 : 0;
                    if (cropKind > 0) {
                        cropKindsByPosition.put(cursor.asLong(), cropKind);
                        if (state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                                && state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) >= 2
                                && Math.abs(cursor.getX() - origin.getX())
                                        <= AREA_SCAN_RADIUS - MutagenSymbiosis.HORIZONTAL_RADIUS
                                && Math.abs(cursor.getZ() - origin.getZ())
                                        <= AREA_SCAN_RADIUS - MutagenSymbiosis.HORIZONTAL_RADIUS
                                && Math.abs(cursor.getY() - origin.getY())
                                        <= AREA_SCAN_VERTICAL_RADIUS - MutagenSymbiosis.VERTICAL_RADIUS) {
                            clusterCandidates.add(cursor.immutable());
                        }
                    }
""" + crop_probe_anchor
if crop_probe_addition not in scanner:
    require(crop_probe_anchor in scanner, "could not locate crop mutation count for cluster candidates")
    scanner = scanner.replace(crop_probe_anchor, crop_probe_addition, 1)
scanner_path.write_text(scanner, encoding="utf-8")

# Add the cluster boolean to the same survey result. The total species count remains independent.
scanner = scanner_path.read_text(encoding="utf-8")
cluster_calc_old = """        int cropSpecies = (hasFiberCrop ? 1 : 0) + (hasAmberCrop ? 1 : 0)
                + (hasRootCrop ? 1 : 0) + (hasFilterMossCrop ? 1 : 0);
        int nearbyPirscher = level.getEntitiesOfClass(KristallpirscherEntity.class,"""
cluster_calc_new = """        int cropSpecies = (hasFiberCrop ? 1 : 0) + (hasAmberCrop ? 1 : 0)
                + (hasRootCrop ? 1 : 0) + (hasFilterMossCrop ? 1 : 0);
        boolean symbiosisCluster = false;
        for (BlockPos candidate : clusterCandidates) {
            if (hasLocalSymbiosisCluster(cropKindsByPosition, candidate)) {
                symbiosisCluster = true;
                break;
            }
        }
        int nearbyPirscher = level.getEntitiesOfClass(KristallpirscherEntity.class,"""
if cluster_calc_new not in scanner:
    require(cluster_calc_old in scanner, "could not locate crop species summary")
    scanner = scanner.replace(cluster_calc_old, cluster_calc_new, 1)
old_return = "                maxRelaySignal, maxStationSignal, nearbyPirscher, cropSpecies);"
new_return = "                maxRelaySignal, maxStationSignal, nearbyPirscher, cropSpecies, symbiosisCluster);"
if new_return not in scanner:
    require(old_return in scanner, "could not locate AreaSurvey return construction")
    scanner = scanner.replace(old_return, new_return, 1)
scanner_path.write_text(scanner, encoding="utf-8")

# Insert a pure in-memory neighborhood check immediately before the report method.
scanner = scanner_path.read_text(encoding="utf-8")
helper_anchor = "    private static void reportAreaSurvey(Player player, AreaSurvey survey) {"
helper = """    private static boolean hasLocalSymbiosisCluster(Map<Long, Integer> cropKindsByPosition,
                                                     BlockPos center) {
        boolean[] seenSpecies = new boolean[5];
        int distinctSpecies = 0;
        int radius = MutagenSymbiosis.HORIZONTAL_RADIUS;
        int vertical = MutagenSymbiosis.VERTICAL_RADIUS;
        int radiusSquared = radius * radius;
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dz = -radius; dz <= radius; dz++) {
                if (dx * dx + dz * dz > radiusSquared) continue;
                for (int dy = -vertical; dy <= vertical; dy++) {
                    int kind = cropKindsByPosition.getOrDefault(BlockPos.asLong(
                            center.getX() + dx, center.getY() + dy, center.getZ() + dz), 0);
                    if (kind > 0 && !seenSpecies[kind]) {
                        seenSpecies[kind] = true;
                        if (++distinctSpecies >= 3) return true;
                    }
                }
            }
        }
        return false;
    }

"""
if helper not in scanner:
    require(helper_anchor in scanner, "could not locate scanner report method for cluster helper")
    scanner = scanner.replace(helper_anchor, helper + helper_anchor, 1)
scanner_path.write_text(scanner, encoding="utf-8")

report_anchor = """        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey.biodiversity",
                survey.cropSpecies()).withStyle(survey.cropSpecies() >= 3
                        ? ChatFormatting.GREEN : ChatFormatting.GRAY), false);"""
report_addition = report_anchor + """
        player.displayClientMessage(Component.translatable(survey.symbiosisCluster()
                ? "message.sporenwerk.scanner.survey.symbiosis_found"
                : "message.sporenwerk.scanner.survey.symbiosis_not_confirmed")
                .withStyle(survey.symbiosisCluster() ? ChatFormatting.GREEN : ChatFormatting.GRAY), false);"""
replace_once(scanner_path, report_anchor, report_addition, "local symbiosis cluster report")

for locale, entries in {
    "de_de.json": {
        "message.sporenwerk.scanner.survey.symbiosis_found": "Lokaler Symbiose-Cluster bestätigt: Mindestens drei Arten wachsen dicht beieinander auf Mutagenboden der Stufe II/III.",
        "message.sporenwerk.scanner.survey.symbiosis_not_confirmed": "Kein passender Symbiose-Cluster im vollständig erfassten Innenbereich bestätigt."
    },
    "en_us.json": {
        "message.sporenwerk.scanner.survey.symbiosis_found": "Local symbiosis cluster confirmed: at least three species grow close together on tier-II/III Mutagen soil.",
        "message.sporenwerk.scanner.survey.symbiosis_not_confirmed": "No qualifying symbiosis cluster confirmed within the fully sampled interior."
    }
}.items():
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Bump active assertions while preserving all historical version notes.
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "Aktueller Entwicklungsstand: 1.47.0" in line:
            lines[index] = line.replace("Aktueller Entwicklungsstand: 1.47.0",
                                        "Aktueller Entwicklungsstand: 1.48.0")
            changed = True
            line = lines[index]
        if r"1\.47\.0" not in line or "version" not in line.lower():
            continue
        newer = line.replace(r"1\.47\.0", r"1\.48\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.47.0" in lines[following] or "version must be 1.47.0" in lines[following]:
                lines[following] = lines[following].replace("1.47.0", "1.48.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.48.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.48.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.48.0 — Bioreaktor-Kreislauf und reaktive Sporenabwehr

- **Neue Produktionsoption:** Ein Symbiosemyzel wird im Biomasse-Bioreaktor für 180 FE in ein Mutagenextrakt umgewandelt. Pufferplatz und Energie werden vor dem Verbrauch des Eingangs gesichert; das Item wird erst nach erfolgreicher Ausgabe entfernt.
- **Gegnerabwehr mit sichtbarer Rückmeldung:** Ein powered Sporenabwehrsender markiert einen erstmals abgewehrten Dämmerling mit einem einzelnen Sporenpartikelausbruch. Der zehn-Tick-Refresh verlängert den Schutzzeitraum, ohne Partikel in jedem Tick erneut zu spammen.
- **Lokaler Cluster statt bloßer Gesamtzahl:** Der Feldscanner bestätigt einen passenden Dreier-Cluster nur dann, wenn drei Arten in der gemeinsamen begrenzten Nachbarschaft eines mindestens auf Stufe II mutierten Erntepunkts gefunden werden. Er wertet dafür die bereits geladenen Scan-Daten aus, ohne weitere Weltblöcke anzufragen.
- **Spielleistung und Sicherheit:** Die Clusterzentren liegen vollständig innerhalb des gescannten Innenbereichs; ungeladene Chunks werden weiter übersprungen. Keine neue Tick-Schleife und keine erzwungene Chunk-Ladung.
- **Qualitätssicherung:** Regressionen prüfen die Bioreaktor-Transaktion, einmaliges Ward-Feedback, lokale Clusterzählung, Texte sowie Forge-Build, installierbare JAR und Server-Smoke-Test.

"""
if "## Version 1.48.0 — Bioreaktor-Kreislauf und reaktive Sporenabwehr" not in readme:
    marker = "## Version 1.47.0 — Symbiose-Forschung und Filter-Endstufe"
    index = readme.find(marker)
    require(index >= 0, "could not locate 1.47.0 release notes")
    readme = readme[:index] + section + readme[index:]
headline = "**Aktueller Entwicklungsstand: 1.48.0 — Bioreaktor-Veredelung, reaktive Sporenabwehr und lokale Symbiose-Erkennung.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
old_focus = """## Aktueller Schwerpunkt — 1.47.0

- Biodiversität verbindet Feldwirtschaft und High-End-Atemschutz: Symbiosemyzel ist jetzt eine erforderliche Zutat für den mutagenen Filtereinsatz der höchsten Stufe.
- Die Rezeptfreigabe erfordert zwei reale Forschungsfunde, statt nur einen allgemeinen Laborfortschritt.
- Der Feldscanner zeigt, wie viele verschiedene Sporenwerk-Pflanzenarten im gescannten Gesamtbereich vorkommen, und erklärt die engere Clusterbedingung für Symbiosemyzel.
- Die neue Diagnose bleibt ein einmaliger, geladene-Chunks-respektierender Scan ohne Tick-Schleife.
- Release-QA umfasst Rezept- und Forschungslogik, DE/EN-Texte, Forge-Build, installierbare JAR und dedizierten Serverstart."""
new_focus = """## Aktueller Schwerpunkt — 1.48.0

- Symbiosemyzel kann jetzt in zwei Produktionspfaden eingesetzt werden: als gezielte Einzelladungs-Wartung eines Resonanzdämpfers und als Bioreaktor-Zutat für Mutagenextrakt.
- Der Feldscanner unterscheidet zwischen bloßer Artenvielfalt im Bereich und einem tatsächlich bestätigten lokalen Dreier-Cluster.
- Ein abgewehrter Dämmerling erhält eine einzelne sichtbare Rückmeldung statt einer Partikelwiederholung bei jedem Ward-Refresh.
- Alle neuen Abfragen bleiben begrenzt, ereignisgesteuert und ohne Chunk-Force-Loading.
- Die Release-Pipeline prüft Produktions-Transaktionen, Schutzfeedback, Clusterlogik, Forge-Build, installierbare JAR und Serverstart."""
if old_focus in readme:
    readme = readme.replace(old_focus, new_focus, 1)
else:
    focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
    if focus_lines:
        readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.48.0", 1)
readme_path.write_text(readme, encoding="utf-8")

print("Sporenwerk 1.48.0 generated: Symbiosemyzel bioprocess, one-shot ward repulsion feedback, and local cluster diagnostics.")
