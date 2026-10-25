#!/usr/bin/env python3
"""Add mature-mutated Filtermoos companion protection, field buffering, and research feedback (1.50.0)."""
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
        raise SystemExit("Filtermoos ecosystem: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def add_import(path, anchor, import_line, label):
    source = path.read_text(encoding="utf-8")
    if import_line in source:
        return
    require(anchor in source, "could not locate import anchor for " + label)
    path.write_text(source.replace(anchor, anchor + "\n" + import_line, 1), encoding="utf-8")


# One bounded rule defines the living Filtermoos protection volume for both mobs and players.
helper_path = SRC / "infection/FilterMossSymbiosis.java"
helper_path.write_text("""\
package de.sporenwerk.infection;

import de.sporenwerk.block.crop.AbstractSporeCropBlock;
import de.sporenwerk.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Mature, tier-II/III Filtermoos forms a small living filtration halo.
 * Every probe checks chunk availability before reading a block; no ticker or forced chunk load.
 */
public final class FilterMossSymbiosis {
    public static final int HORIZONTAL_RADIUS = 3;
    public static final int VERTICAL_RADIUS = 1;
    public static final int MIN_MUTAGEN_LEVEL = 2;

    private FilterMossSymbiosis() {}

    public static boolean protects(Level level, BlockPos origin) {
        if (level == null || !level.hasChunkAt(origin)) return false;
        int radiusSquared = HORIZONTAL_RADIUS * HORIZONTAL_RADIUS;
        for (int dx = -HORIZONTAL_RADIUS; dx <= HORIZONTAL_RADIUS; dx++) {
            for (int dz = -HORIZONTAL_RADIUS; dz <= HORIZONTAL_RADIUS; dz++) {
                if (dx * dx + dz * dz > radiusSquared) continue;
                for (int dy = -VERTICAL_RADIUS; dy <= VERTICAL_RADIUS; dy++) {
                    BlockPos probe = origin.offset(dx, dy, dz);
                    if (!level.hasChunkAt(probe)) continue;
                    BlockState state = level.getBlockState(probe);
                    if (!state.is(ModBlocks.FILTERMOOS.get())
                            || !state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            || state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) < MIN_MUTAGEN_LEVEL) continue;
                    if (!(state.getBlock() instanceof CropBlock crop) || !crop.isMaxAge(state)) continue;
                    return true;
                }
            }
        }
        return false;
    }
}
""", encoding="utf-8")

# Dämmerlinge now recognize living high-tier Filtermoos as a companion defense for nearby crops.
entity_path = SRC / "entity/DaemmerlingEntity.java"
add_import(entity_path, "import de.sporenwerk.registry.ModBlocks;",
           "import de.sporenwerk.infection.FilterMossSymbiosis;", "Dämmerling Filtermoos protection")
replace_once(
    entity_path,
    "            if (mob.level().getMaxLocalRawBrightness(cropPos) >= 7) return true;\n            for (BlockPos pos : BlockPos.betweenClosed(cropPos.offset(-3, -1, -3),",
    "            if (mob.level().getMaxLocalRawBrightness(cropPos) >= 7) return true;\n"
    "            if (FilterMossSymbiosis.protects(mob.level(), cropPos)) return true;\n"
    "            for (BlockPos pos : BlockPos.betweenClosed(cropPos.offset(-3, -1, -3),",
    "natural Filtermoos protection in Dämmerling target selection"
)
# The existing collector scan must remain chunk-safe at chunk borders.
entity = entity_path.read_text(encoding="utf-8")
old_loop = """            for (BlockPos pos : BlockPos.betweenClosed(cropPos.offset(-3, -1, -3),
                    cropPos.offset(3, 1, 3))) {
                if (mob.level().getBlockState(pos).is(ModBlocks.FELDSAMMLER.get())) return true;
            }"""
new_loop = """            for (BlockPos pos : BlockPos.betweenClosed(cropPos.offset(-3, -1, -3),
                    cropPos.offset(3, 1, 3))) {
                if (!mob.level().hasChunkAt(pos)) continue;
                if (mob.level().getBlockState(pos).is(ModBlocks.FELDSAMMLER.get())) return true;
            }"""
if new_loop not in entity:
    require(old_loop in entity, "could not locate the existing collector deterrence scan")
    entity_path.write_text(entity.replace(old_loop, new_loop, 1), encoding="utf-8")

# Mutagen field exposure pulses are buffered by the same living halo. This only runs on the
# already-scheduled exposure pulse, not every player tick, and does not spend mask durability.
events_path = SRC / "infection/InfectionEvents.java"
for anchor, import_line, label in (
    ("import de.sporenwerk.registry.ModItems;", "import de.sporenwerk.infection.FilterMossSymbiosis;", "Filtermoos exposure helper"),
    ("import net.minecraft.network.chat.Component;", "import net.minecraft.advancements.Advancement;", "advancement lookup"),
    ("import net.minecraft.advancements.Advancement;", "import net.minecraft.resources.ResourceLocation;", "advancement location"),
    ("import net.minecraft.world.entity.player.Player;", "import net.minecraft.core.particles.ParticleTypes;", "filtration particle"),
    ("import net.minecraft.core.particles.ParticleTypes;", "import net.minecraft.server.level.ServerPlayer;", "server-side progression"),
):
    add_import(events_path, anchor, import_line, label)

events = events_path.read_text(encoding="utf-8")
old_pulse = """        if (fieldExposurePulse) {
            net.minecraft.world.item.ItemStack mask = player.getItemBySlot(EquipmentSlot.HEAD);"""
new_pulse = """        if (fieldExposurePulse && FilterMossSymbiosis.protects(level, player.blockPosition())) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.filtermoos.field_buffered")
                    .withStyle(ChatFormatting.GREEN), true);
            if (player instanceof ServerPlayer serverPlayer) {
                serverPlayer.serverLevel().sendParticles(ParticleTypes.WARPED_SPORE,
                        player.getX(), player.getY() + 0.8D, player.getZ(),
                        8, 0.22D, 0.28D, 0.22D, 0.01D);
                var server = serverPlayer.getServer();
                Advancement milestone = server == null ? null : server.getAdvancements().getAdvancement(
                        new ResourceLocation("sporenwerk", "filtermoos_bastion"));
                if (milestone != null) {
                    serverPlayer.getAdvancements().award(milestone, "filtermoos_intercepts_exposure");
                }
            }
        } else if (fieldExposurePulse) {
            net.minecraft.world.item.ItemStack mask = player.getItemBySlot(EquipmentSlot.HEAD);"""
replace_once(events_path, old_pulse, new_pulse, "mutagen field exposure pulse interception")

# The milestone is awarded by the gameplay event above, not by possessing an unrelated item.
advancement = {
    "parent": "sporenwerk:mutagen_laboratory",
    "display": {
        "icon": {"item": "sporenwerk:sporenfiltereinsatz"},
        "title": {"translate": "advancements.sporenwerk.filtermoos_bastion.title"},
        "description": {"translate": "advancements.sporenwerk.filtermoos_bastion.description"},
        "frame": "goal",
        "show_toast": True,
        "announce_to_chat": False,
        "hidden": False
    },
    "criteria": {
        "filtermoos_intercepts_exposure": {"trigger": "minecraft:impossible"}
    },
    "requirements": [["filtermoos_intercepts_exposure"]],
    "rewards": {"loot": ["sporenwerk:quests/filtermoos_bastion"]}
}
adv_path = RES / "data/sporenwerk/advancements/filtermoos_bastion.json"
adv_path.parent.mkdir(parents=True, exist_ok=True)
adv_path.write_text(json.dumps(advancement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
loot_path = RES / "data/sporenwerk/loot_tables/quests/filtermoos_bastion.json"
loot_path.parent.mkdir(parents=True, exist_ok=True)
loot = {
    "type": "minecraft:generic",
    "pools": [{
        "rolls": 1.0,
        "entries": [{
            "type": "minecraft:item",
            "name": "sporenwerk:sporenfiltereinsatz",
            "functions": [{"function": "minecraft:set_count", "count": 2}]
        }]
    }]
}
loot_path.write_text(json.dumps(loot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Report mature, tier-II/III Filtermoos already found inside the existing bounded field survey.
scanner_path = SRC / "item/FeldscannerItem.java"
add_import(scanner_path, "import de.sporenwerk.registry.ModBlocks;",
           "import net.minecraft.world.level.block.CropBlock;", "mature Filtermoos survey count")
scanner = scanner_path.read_text(encoding="utf-8")
old_record = "int nearbyPirscher, int cropSpecies, boolean symbiosisCluster) {}"
new_record = "int nearbyPirscher, int cropSpecies, boolean symbiosisCluster, int protectiveFilterMoss) {}"
if new_record not in scanner:
    require(old_record in scanner, "AreaSurvey must retain the 1.48.0 cluster field")
    scanner = scanner.replace(old_record, new_record, 1)
old_var = "        int mutatedCrops = 0;"
new_var = "        int mutatedCrops = 0;\n        int protectiveFilterMoss = 0;"
if new_var not in scanner:
    require(old_var in scanner, "could not locate survey crop counters")
    scanner = scanner.replace(old_var, new_var, 1)
crop_anchor = """                    if (state.getBlock() instanceof AbstractSporeCropBlock
                            && state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            && state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0) {
                        mutatedCrops++;
                    }"""
crop_addition = crop_anchor + """
                    if (state.is(ModBlocks.FILTERMOOS.get())
                            && state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            && state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) >= 2
                            && state.getBlock() instanceof CropBlock filterCrop
                            && filterCrop.isMaxAge(state)) {
                        protectiveFilterMoss++;
                    }"""
if crop_addition not in scanner:
    require(crop_anchor in scanner, "could not locate scanner crop mutation count")
    scanner = scanner.replace(crop_anchor, crop_addition, 1)
old_return = "maxRelaySignal, maxStationSignal, nearbyPirscher, cropSpecies, symbiosisCluster);"
new_return = "maxRelaySignal, maxStationSignal, nearbyPirscher, cropSpecies, symbiosisCluster, protectiveFilterMoss);"
if new_return not in scanner:
    require(old_return in scanner, "could not locate AreaSurvey construction")
    scanner = scanner.replace(old_return, new_return, 1)
scanner_path.write_text(scanner, encoding="utf-8")

report_anchor = """        player.displayClientMessage(Component.translatable(survey.symbiosisCluster()
                ? "message.sporenwerk.scanner.survey.symbiosis_found"
                : "message.sporenwerk.scanner.survey.symbiosis_not_confirmed")
                .withStyle(survey.symbiosisCluster() ? ChatFormatting.GREEN : ChatFormatting.GRAY), false);"""
report_addition = report_anchor + """
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.scanner.survey.filtermoos", survey.protectiveFilterMoss())
                .withStyle(survey.protectiveFilterMoss() > 0 ? ChatFormatting.GREEN : ChatFormatting.GRAY), false);"""
replace_once(scanner_path, report_anchor, report_addition, "Filtermoos survey report")

# DE/EN text emphasizes the actual conditions, range, and what is protected.
for locale, entries in {
    "de_de.json": {
        "message.sporenwerk.filtermoos.field_buffered": "Filtermoos-Symbiose abgefangen: Die Mutagen-Exposition wurde ohne Filterverschleiß unterdrückt.",
        "message.sporenwerk.scanner.survey.filtermoos": "Reife Filtermoos-Pflanzen der Mutagenstufe II/III: %1$s. Sie schützen Pflanzen und Spieler im Nahbereich.",
        "advancements.sporenwerk.filtermoos_bastion.title": "Ein lebender Filter",
        "advancements.sporenwerk.filtermoos_bastion.description": "Lass reifes, hochmutiertes Filtermoos eine Mutagen-Exposition abfangen."
    },
    "en_us.json": {
        "message.sporenwerk.filtermoos.field_buffered": "Filtermoos symbiosis intercepted the Mutagen exposure pulse without filter wear.",
        "message.sporenwerk.scanner.survey.filtermoos": "Mature tier-II/III Filtermoos plants: %1$s. They protect nearby crops and players.",
        "advancements.sporenwerk.filtermoos_bastion.title": "A Living Filter",
        "advancements.sporenwerk.filtermoos_bastion.description": "Let mature, highly mutated Filtermoos intercept a Mutagen exposure pulse."
    }
}.items():
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# The 1.47/1.48 scanner regression checks AreaSurvey's tail fields. Keep it aligned
# with the additive Filtermoos count without weakening any earlier assertions.
progression_test_path = ROOT / "tools/test_mutagen_symbiosis_progression.py"
if progression_test_path.is_file():
    progression_test = progression_test_path.read_text(encoding="utf-8")
    old_schema_token = '"int cropSpecies, boolean symbiosisCluster)"'
    new_schema_token = '"int cropSpecies, boolean symbiosisCluster, int protectiveFilterMoss)"'
    if old_schema_token in progression_test:
        progression_test = progression_test.replace(old_schema_token, new_schema_token, 1)
        progression_test_path.write_text(progression_test, encoding="utf-8")
    elif new_schema_token not in progression_test:
        raise SystemExit("Could not align the prior scanner regression with the additive Filtermoos survey field")

# Keep active-version test assertions current; historical release notes remain unchanged.
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "Aktueller Entwicklungsstand: 1.49.0" in line:
            lines[index] = line.replace("Aktueller Entwicklungsstand: 1.49.0",
                                        "Aktueller Entwicklungsstand: 1.50.0")
            changed = True
            line = lines[index]
        if r"1\.49\.0" not in line or "version" not in line.lower():
            continue
        newer = line.replace(r"1\.49\.0", r"1\.50\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.49.0" in lines[following] or "version must be 1.49.0" in lines[following]:
                lines[following] = lines[following].replace("1.49.0", "1.50.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.50.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.50.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.50.0 — Lebendes Filtermoos und natürliche Feldabwehr

- **Ökologische Begleitpflanze:** Ausgewachsenes Filtermoos mit Mutagenstufe II/III bildet einen begrenzten Schutzradius von drei Blöcken horizontal und einem vertikal. Innerhalb dieses Radius schützt es reife Sporenwerk-Pflanzen vor dem Dämmerling.
- **Überlebenshilfe im Feld:** Derselbe Filtermoos-Cluster fängt einen fälligen Mutagen-Expositionsimpuls ab, wenn ein Spieler nahe genug steht. Das verbraucht keine Haltbarkeit der Filtermaske; eine lokale Meldung und Sporenpartikel bestätigen den Schutz.
- **Nachvollziehbare Entdeckung:** Die erste tatsächlich abgefangene Exposition löst den Forschungsfortschritt „Ein lebender Filter“ aus und belohnt zwei gewöhnliche Filtereinsätze. Es gibt keine erfundene Belohnung beim bloßen Aufheben eines Gegenstands.
- **Scanner statt Rätselraten:** Der begrenzte Feldbericht zählt reife Filtermoos-Pflanzen der Stufe II/III im Messgebiet. Das ist ein Bereichsgesamtwert, keine Behauptung, dass jede gezählte Pflanze den Spieler oder ein Ziel gerade schützt.
- **Ressourcen- und Balancegrenzen:** Alle Filtermoos-Prüfungen ignorieren ungeladene Chunks; die Feldpulsprüfung läuft nur zu den ohnehin fälligen Expositionszeitpunkten. Keine neue Tick-Schleife und kein erzwungenes Chunk-Laden.
- **Qualitätssicherung:** Tests prüfen Alters- und Mutagenstufen, den gemeinsamen Schutzradius, Abfangen der Exposition, Maskenhaltbarkeit, Forschungsbelohnung, Scannerbericht, DE/EN-Texte, Forge-Build und Serverstart.

"""
if "## Version 1.50.0 — Lebendes Filtermoos und natürliche Feldabwehr" not in readme:
    marker = "## Version 1.49.0 — Resonanzfokus und aktive Gegenwehr"
    index = readme.find(marker)
    require(index >= 0, "could not locate the 1.49.0 Resonanzfokus release notes")
    readme = readme[:index] + section + readme[index:]
headline = "**Aktueller Entwicklungsstand: 1.50.0 — Lebendes Filtermoos, natürliche Pflanzenabwehr und Expositionsschutz.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
old_focus = """## Aktueller Schwerpunkt — 1.49.0

- Symbiosemyzel kann nun in zwei Produktionspfaden genutzt werden: als gezielte Einzelladungs-Wartung eines Resonanzdämpfers und als Bioreaktor-Zutat für Mutagenextrakt.
- Der Feldscanner unterscheidet zwischen Artenvielfalt im Bereich und einem tatsächlich bestätigten lokalen Dreier-Cluster um eine ausgewachsene Mutagenpflanze.
- Ein abgewehrter Dämmerling erhält eine einzelne sichtbare Rückmeldung statt Partikelwiederholung bei jedem Ward-Refresh.
- Alle neuen Abfragen bleiben begrenzt, ereignisgesteuert und ohne Chunk-Force-Loading.
- Die Release-Pipeline prüft Produktions-Transaktionen, Schutzfeedback, Clusterlogik, Forge-Build, installierbare JAR und Serverstart."""
new_focus = """## Aktueller Schwerpunkt — 1.50.0

- Reifes, hochmutiertes Filtermoos ist jetzt eine natürliche Begleitpflanze: Es schützt benachbarte reife Nutzpflanzen vor dem Dämmerling und kann einen fälligen Mutagen-Expositionsimpuls puffern.
- Dieselbe begrenzte Quellregel wird von Kreaturen-KI und Spielerüberleben verwendet, damit die Mechanik einheitlich bleibt.
- Der Feldscanner zeigt, wie viele ausgewachsene Filtermoos-Filterpflanzen der Stufe II/III im Messgebiet stehen.
- Die erste tatsächlich abgefangene Exposition schaltet Forschung frei und belohnt zwei Filtereinsätze.
- Alle Schutzabfragen sind chunk-sicher und verwenden keine neue Tick-Schleife."""
if old_focus in readme:
    readme = readme.replace(old_focus, new_focus, 1)
else:
    focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
    if focus_lines:
        focus_start = readme.find(focus_lines[0])
        focus_end = readme.find("\n## Version ", focus_start)
        require(focus_end >= 0, "could not locate release-history boundary after current focus section")
        readme = readme[:focus_start] + new_focus + "\n---\n\n" + readme[focus_end + 1:]
readme_path.write_text(readme, encoding="utf-8")

print("Sporenwerk 1.50.0 generated: Filtermoos companion defense, player exposure buffering, scanner diagnostics, and research reward.")
