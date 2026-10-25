#!/usr/bin/env python3
"""Make crop phenotype intensity obey Mutagen Node modes and Redstone containment (1.72.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Mode-aware Mutagen strength 1.72: " + message)


# Strength queries are used by crop visuals, harvest bonuses, field scans, and bloom gating.
# The registry only stores persistent source activation, so resolve the actual placed node
# before assigning strength. Unloaded chunks are skipped and never force-loaded.
node_data_path = SRC / "infection/MutationNodeData.java"
node_data = node_data_path.read_text(encoding="utf-8")
for imp in (
    "import de.sporenwerk.block.MutationNodeBlock;",
    "import de.sporenwerk.registry.ModBlocks;",
    "import net.minecraft.world.level.block.state.BlockState;",
):
    if imp not in node_data:
        anchor = "package de.sporenwerk.infection;"
        require(anchor in node_data, "could not locate MutationNodeData import area")
        node_data = node_data.replace(anchor, anchor + "\n\n" + imp, 1)

if "public int getOperationalFieldStrengthAt(" not in node_data:
    save_anchor = "    @Override\n    public CompoundTag save(CompoundTag tag)"
    require(node_data.count(save_anchor) == 1, "could not locate MutationNodeData save method")
    method = """    /**
     * Field intensity reflects actual play state, not merely the persisted source registry.
     * Cultivation mode (1) deliberately emits crop strength; dormant (2) and Redstone lock
     * emit none. The loaded-chunk guard prevents scanner/crop queries from loading terrain.
     */
    public int getOperationalFieldStrengthAt(ServerLevel level, BlockPos target,
                                              int radius, int halfHeight) {
        int best = 0;
        for (Map.Entry<Long, Boolean> entry : nodes.entrySet()) {
            if (!entry.getValue()) continue;
            BlockPos origin = BlockPos.of(entry.getKey());
            if (!level.hasChunkAt(origin)) continue;
            BlockState source = level.getBlockState(origin);
            if (!source.is(ModBlocks.INFEKTIONSHERD.get())) continue;
            if (source.getValue(MutationNodeBlock.POWERED)
                    || source.getValue(MutationNodeBlock.MODE) == 2
                    || level.hasNeighborSignal(origin)) continue;

            long dx = (long) target.getX() - origin.getX();
            long dz = (long) target.getZ() - origin.getZ();
            long horizontalSquared = dx * dx + dz * dz;
            int vertical = Math.abs(target.getY() - origin.getY());
            if (horizontalSquared > (long) radius * radius || vertical > halfHeight) continue;

            int strength = horizontalSquared <= 4L && vertical <= 1 ? 3
                    : horizontalSquared <= 25L && vertical <= 2 ? 2 : 1;
            best = Math.max(best, strength);
            if (best == 3) return 3;
        }
        return best;
    }

"""
    node_data = node_data.replace(save_anchor, method + save_anchor, 1)
node_data_path.write_text(node_data, encoding="utf-8")

# Switch all shared active-field queries to the operationally-aware calculation.
field_path = SRC / "infection/MutationField.java"
field = field_path.read_text(encoding="utf-8")
old = "return MutationNodeData.get(serverLevel).getFieldStrengthAt(target, RADIUS, INFECTION_HALF_HEIGHT);"
new = "return MutationNodeData.get(serverLevel).getOperationalFieldStrengthAt(\n                serverLevel, target, RADIUS, INFECTION_HALF_HEIGHT);"
if new not in field:
    require(field.count(old) == 1, "could not locate shared mutagen strength query")
    field = field.replace(old, new, 1)
field_path.write_text(field, encoding="utf-8")

# Update the player-facing description: cultivation keeps crop strength while never spreading terrain.
for filename, tooltip, cultivation, dormant, paused in (
    ("de_de.json",
     "Rechtsklick wechselt den Modus: AUSBREITUNG, KULTUR (sichere Mutagenstufen für Sporenwerk-Pflanzen) oder RUHEND. Redstone pausiert jeden Modus vollständig.",
     "Mutagenherd: Kulturmodus — sichere Pflanzenmutation und Wachstum, aber keine Terrainausbreitung, Spielerexposition oder Mutagenblüte.",
     "Mutagenherd: ruhend — Feldstärke 0; keine Feldwirkung.",
     "Mutagenherd pausiert: Feldstärke 0; Redstone stoppt Ausbreitung und Pflanzenmutagenität."),
    ("en_us.json",
     "Right-click to cycle modes: SPREAD, CULTIVATION (safe Mutagen tiers for Sporenwerk crops), or DORMANT. Redstone pauses every mode completely.",
     "Mutagen Node: cultivation mode — safe crop mutation and growth, with no terrain spread, player exposure, or Mutagen Bloom.",
     "Mutagen Node: dormant — field strength 0; no field effects.",
     "Mutagen Node paused: field strength 0; Redstone stops spread and crop mutation.")
):
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale["tooltip.sporenwerk.infektionsherd"] = tooltip
    locale["message.sporenwerk.mutation.node_cultivation"] = cultivation
    locale["message.sporenwerk.mutation.node_dormant"] = dormant
    locale["message.sporenwerk.mutation.node_paused"] = paused
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Promote active version checks without rewriting historical feature notes.
new_test = "test_mutagen_field_strength_modes_172.py"
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == new_test:
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.71.0",
                               "Aktueller Entwicklungsstand: 1.72.0")
    if "build.gradle" in original:
        updated = updated.replace(r"1\.71\.0", r"1\.72\.0")
        updated = updated.replace("artifact must be version 1.71.0",
                                  "artifact must be version 1.72.0")
    updated = updated.replace(
        '"Version 1.71.0" in readme and "Version 1.70.0" in readme',
        '"Version 1.72.0" in readme and "Version 1.71.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.72.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.72.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.72.0 — Mutagenstärke folgt dem Betriebsmodus

- **Kulturmodus erzeugt sichere Phänotypen:** Der aktive Mutagenherd liefert weiterhin echte Stärke-Stufen an Sporenwerk-Pflanzen, selbst wenn er auf Kultur statt Ausbreitung gestellt ist. Die bestehenden sichtbaren Pflanzenfarben und stufenabhängigen Ernteboni werden dadurch nutzbar, ohne den Boden zu infizieren oder Spieler zu exponieren.
- **Ruhend heißt wirklich ruhend:** Ein ruhender Herd liefert Feldstärke 0. Redstone setzt die Feldstärke ebenfalls auf 0, auch wenn der Herd und seine persistente Registrierung erhalten bleiben.
- **Bestehende Systeme synchronisiert:** Pflanzenvisualisierung, stufenabhängige Ernte, Feldscanner und Bloom-Freigabe verwenden dieselbe serverseitige Intensitätsabfrage; Pflanzen fallen bei ihren nächsten regulären Ticks auf die normale Mutagenstufe zurück.
- **Chunk-sicher:** Die Intensitätsabfrage berücksichtigt nur bereits geladene Quell-Chunks und erzwingt keine Chunk-Ladevorgänge.
- **Qualitätssicherung:** Tests prüfen die tatsächliche Quelle, Kultur-/Ruhend-/Redstone-Zustände, die vier Stufen, Anker-Unterdrückung, Chunk-Grenzen und deutsche/englische Rückmeldungen.

"""
current = """## Aktueller Entwicklungsschritt — 1.72.0

- **Sicherer Anbau mit echten Stufen:** Kulturmodus lässt die vorhandenen Mutagen-Phänotypen und stufenabhängigen Ernteboni arbeiten, während der Quellenmodus Terrain-Ausbreitung, Exposition und Mutagenblüten nicht auslöst.
- **Keine Geisterfelder:** Ruhend und Redstone-gesperrt liefern ab sofort keine Feldstärke mehr, obwohl die Quelle für später erhalten bleibt.
- **Einheitliche Auswertung:** Sichtbare Feld-/Pflanzenstufen, Ernte und Scanner nutzen dieselbe laufzeitbewusste Abfrage.
- **Leistungsgrenze:** Nur geladene Quell-Chunks werden gelesen; der bestehende Quellen-Tick und die bisherigen räumlichen Grenzen bleiben erhalten.

"""
if "## Version 1.72.0 — Mutagenstärke folgt dem Betriebsmodus" not in readme:
    marker = "## Version 1.71.0 — Drei Betriebsmodi für den Mutagenherd"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate 1.71 release heading")
    readme = readme[:idx] + release + readme[idx:]
if "## Aktueller Entwicklungsschritt — 1.72.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.71.0"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate current 1.71 development heading")
    readme = readme[:idx] + current + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.71.0 — Drei Betriebsmodi für den Mutagenherd.**",
    "**Aktueller Entwicklungsstand: 1.72.0 — Mutagenstärke folgt dem Betriebsmodus.**")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.72.0 generated: operational field strength respects spread/cultivation/dormant, Redstone lock and loaded-chunk boundaries.")
