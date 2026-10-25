#!/usr/bin/env python3
"""Give successful Spore Ward protection its own one-time field-research route (1.78.0)."""
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
        raise SystemExit("Bloom ward research 1.78: " + message)


def add_import(path, anchor, import_line):
    source = path.read_text(encoding="utf-8")
    if import_line in source:
        return
    require(anchor in source, "missing import anchor for " + import_line)
    path.write_text(source.replace(anchor, anchor + "\n" + import_line, 1), encoding="utf-8")


# The Ward path should reward actual successful interception, never merely placing a block.
bloom_path = SRC / "infection/MutagenBloom.java"
for imp in (
    "import net.minecraft.advancements.Advancement;",
    "import net.minecraft.resources.ResourceLocation;",
    "import net.minecraft.server.level.ServerPlayer;",
):
    add_import(bloom_path, "import net.minecraft.server.level.ServerLevel;", imp)

bloom = bloom_path.read_text(encoding="utf-8")
helper_anchor = "    private static void exposeNearbyPlayers(ServerLevel level, BlockPos origin) {"
helper = """    /**
     * Reward field research only when a real bloom pulse is intercepted by a powered Ward.
     * Advancement rewards are per-player and one-time; the event itself remains unchanged.
     */
    private static void awardBloomWardResearch(Player player) {
        if (!(player instanceof ServerPlayer serverPlayer)) return;
        var server = serverPlayer.getServer();
        Advancement research = server == null ? null : server.getAdvancements().getAdvancement(
                new ResourceLocation("sporenwerk", "fieldwork/bloom_warded"));
        if (research != null) {
            serverPlayer.getAdvancements().award(research, "bloom_warded");
        }
    }

"""
if "private static void awardBloomWardResearch(" not in bloom:
    require(helper_anchor in bloom, "could not locate Bloom exposure handler")
    bloom = bloom.replace(helper_anchor, helper + helper_anchor, 1)

ward_anchor = """            if (isProtectedByPoweredWard(level, player.blockPosition())) {
                player.displayClientMessage("""
ward_add = """            if (isProtectedByPoweredWard(level, player.blockPosition())) {
                awardBloomWardResearch(player);
                player.displayClientMessage("""
if "awardBloomWardResearch(player);" not in bloom:
    require(ward_anchor in bloom, "could not locate successful powered-Ward interception branch")
    bloom = bloom.replace(ward_anchor, ward_add, 1)
bloom_path.write_text(bloom, encoding="utf-8")
bloom = bloom_path.read_text(encoding="utf-8")
require("private static void awardBloomWardResearch(Player player)" in bloom
        and 'new ResourceLocation("sporenwerk", "fieldwork/bloom_warded")' in bloom
        and 'award(research, "bloom_warded")' in bloom
        and "awardBloomWardResearch(player);" in bloom,
        "Ward research reward must be wired into the actual interception path")

advancement = {
    "parent": "sporenwerk:first_mutagen_bloom",
    "display": {
        "icon": {"item": "sporenwerk:sporenabwehr"},
        "title": {"translate": "advancements.sporenwerk.bloom_warded.title"},
        "description": {"translate": "advancements.sporenwerk.bloom_warded.description"},
        "frame": "goal",
        "show_toast": True,
        "announce_to_chat": False,
        "hidden": False
    },
    "criteria": {"bloom_warded": {"trigger": "minecraft:impossible"}},
    "requirements": [["bloom_warded"]],
    "rewards": {"loot": ["sporenwerk:quests/bloom_warded"]}
}
adv_path = RES / "data/sporenwerk/advancements/fieldwork/bloom_warded.json"
adv_path.parent.mkdir(parents=True, exist_ok=True)
adv_path.write_text(json.dumps(advancement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Ward-based research differs from the finite-charge Dampener route: its reward is field
# knowledge and renewable mycelium compost, supporting the ecology/farming progression.
loot = {
    "type": "minecraft:generic",
    "pools": [
        {"rolls": 1.0, "entries": [{
            "type": "minecraft:item", "name": "sporenwerk:feldwissen",
            "functions": [{"function": "minecraft:set_count", "count": 2}]
        }]},
        {"rolls": 1.0, "entries": [{
            "type": "minecraft:item", "name": "sporenwerk:myzelkompost"
        }]}
    ]
}
loot_path = RES / "data/sporenwerk/loot_tables/quests/bloom_warded.json"
loot_path.parent.mkdir(parents=True, exist_ok=True)
loot_path.write_text(json.dumps(loot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for locale, data_values in {
    "de_de.json": {
        "advancements.sporenwerk.bloom_warded.title": "Leise Wurzeln",
        "advancements.sporenwerk.bloom_warded.description": "Lass eine aktive Sporenabwehr den Expositionsimpuls einer Mutagenblüte abfangen und sichere die erste Feldforschungsbelohnung."
    },
    "en_us.json": {
        "advancements.sporenwerk.bloom_warded.title": "Quiet Roots",
        "advancements.sporenwerk.bloom_warded.description": "Let a powered Spore Ward intercept a Mutagen Bloom exposure pulse and secure the first field-research reward."
    }
}.items():
    locale_path = ASSETS / "lang" / locale
    locale_data = json.loads(locale_path.read_text(encoding="utf-8"))
    locale_data.update(data_values)
    locale_path.write_text(json.dumps(locale_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Advance the artifact and current-version regression contracts, retaining historical releases.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_bloom_ward_research_178.py":
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.77.0",
                               "Aktueller Entwicklungsstand: 1.78.0")
    if "build.gradle" in original:
        updated = updated.replace(r"1\.77\.0", r"1\.78\.0")
        updated = updated.replace("artifact must be version 1.77.0",
                                  "artifact must be version 1.78.0")
    updated = updated.replace(
        '"Version 1.77.0" in readme and "Version 1.76.0" in readme',
        '"Version 1.78.0" in readme and "Version 1.77.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.78.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Forge artifact version")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current = """## Aktueller Entwicklungsschritt — 1.78.0

- **Zweite Schutzroute:** Eine aktive Sporenabwehr schützt nicht nur vor dem Blütenimpuls, sondern dokumentiert den tatsächlichen Abfang als eigenständigen Forschungsfortschritt.
- **Forschungsbelohnung nur bei Erfolg:** Die neue Advancement wird ausschließlich dann vergeben, wenn eine Mutagenblüte ausgelöst wurde und die Sporenabwehr den Impuls für diesen Spieler tatsächlich abfängt. Reines Platzieren oder Einschalten reicht nicht.
- **Neue Fortschrittsverzweigung:** „Leise Wurzeln“ gewährt einmalig zwei Feldwissen und einen Myzelkompost. Die bestehende Route „Stiller Ausbruch“ für den ladungsverbrauchenden Resonanzdämpfer bleibt getrennt.
- **Ökologie + Containment:** Der Belohnungspfad verbindet den Blüten-Event, die echte Ward-Reichweite, den Forschungsbaum und die bestehende Farm-/Kompostproduktion.
- **Sicherer Ablauf:** Serverseitige Vergabe, vorhandener Blüten-Cooldown und bestehende Chunk-Grenzen bleiben erhalten; kein zusätzlicher Tick-Loop.
- **Qualität:** Advancement-Schema, Loot-Tabelle, deutsche/englische Texte, bestehende Dämpfer- und Ward-Regressionen, Forge-JAR und dedizierter Serverstart werden geprüft.

"""
if "## Aktueller Entwicklungsschritt — 1.78.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.77.0"
    require(marker in readme, "could not find active 1.77 development section")
    readme = readme.replace(marker, current + marker, 1)
release = """## Version 1.78.0 — Forschungszweig für abgefangene Mutagenblüten

- **Neue Feldforschungs-Advancement „Leise Wurzeln“:** Eine aktive Sporenabwehr meldet den Spielerfortschritt erst, wenn sie einen realen Mutagenblüten-Expositionsimpuls abfängt.
- **Einmalige Belohnung:** Zwei Feldwissen und ein Myzelkompost verbinden die sichere Verteidigungsstrategie mit weiterer Forschung und der ökologischen Produktionskette.
- **Getrennter Schutzpfad:** Die bisherige Dämpfer-Advancement „Stiller Ausbruch“ bleibt an den tatsächlichen Verbrauch einer endlichen Resonanzdämpfer-Ladung gekoppelt.
- **Keine Gratisbelohnung beim Aufstellen:** Der Trigger sitzt im serverseitigen Schutz-Zweig der echten Blüten-Expositionsroutine; Einschalten, Platzieren oder bloßes Beobachten reicht nicht.
- **Qualitätssicherung:** Tests verifizieren Advancement-Kriterium, Loot-Inhalte, Sprachdateien, Dämpfer-Gegenpfad und vollständigen Forge-Serverstart.

"""
if "## Version 1.78.0 — Forschungszweig für abgefangene Mutagenblüten" not in readme:
    marker = "## Version 1.77.0 —"
    require(marker in readme, "could not find release 1.77 marker")
    readme = readme.replace(marker, release + marker, 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.77.0 — Symbiose-Ernte als Redstone-Signal.**",
    "**Aktueller Entwicklungsstand: 1.78.0 — Forschungszweig für abgefangene Mutagenblüten.**")
require("Aktueller Entwicklungsstand: 1.78.0" in readme,
        "README current-version headline was not updated")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.78.0 generated: successful Spore Ward bloom interception now unlocks a separate one-time research and ecology reward path.")
