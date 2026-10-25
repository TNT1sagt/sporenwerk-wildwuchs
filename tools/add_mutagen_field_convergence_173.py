#!/usr/bin/env python3
"""Add bounded Mutagen field convergence where two operational fields overlap (1.73.0)."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen field convergence 1.73: " + message)


node_data_path = SRC / "infection/MutationNodeData.java"
node_data = node_data_path.read_text(encoding="utf-8")
start = node_data.find("    public int getOperationalFieldStrengthAt(")
require(start >= 0, "could not locate operational field-strength calculation")
end = node_data.find("\n    }", start)
require(end > start, "could not isolate operational field-strength calculation")
end += len("\n    }")
method = node_data[start:end]

if "int overlappingSources = 0;" not in method:
    method = """    public int getOperationalFieldStrengthAt(ServerLevel level, BlockPos target,
                                              int radius, int halfHeight) {
        int best = 0;
        int overlappingSources = 0;
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
            overlappingSources++;
            // Two sources with a strong local field already reach the cap. Otherwise keep
            // counting: a second weaker source can still create the convergence bonus.
            if (best == 3 && overlappingSources >= 2) return 3;
        }
        if (best == 0) return 0;
        return overlappingSources >= 2 ? Math.min(3, best + 1) : best;
    }"""
    node_data = node_data[:start] + method + node_data[end:]
    node_data_path.write_text(node_data, encoding="utf-8")

require("int overlappingSources = 0;" in method,
        "overlap-source counter was not installed")
require("overlappingSources++;" in method,
        "each operational source that reaches the target must count once")
require("return overlappingSources >= 2 ? Math.min(3, best + 1) : best;" in method,
        "two fields must add one intensity tier, capped at three")
require("source.getValue(MutationNodeBlock.MODE) == 2" in method
        and "source.getValue(MutationNodeBlock.POWERED)" in method
        and "level.hasNeighborSignal(origin)" in method,
        "dormant and Redstone-locked sources must not contribute")
require("if (!level.hasChunkAt(origin)) continue;" in method
        and "getChunk(" not in method and "getChunkNow(" not in method,
        "source strength may inspect loaded chunks only")

# Keep historical ecology tests focused on the methods they cover, rather than banning
# legitimate source-state reads used by the newer operational-intensity API.
ecology_test = ROOT / "tools/test_bloom_ecology.py"
if ecology_test.exists():
    text = ecology_test.read_text(encoding="utf-8")
    old_check = '''require("level.getBlockState(" not in nodes and "getChunk(" not in nodes and "getChunkNow(" not in nodes,
        "saved bloom source queries must not read world blocks or load chunks")'''
    new_check = '''for signature in (
    "public BlockPos nearestRecentBloom(",
    "public int countRecentBlooms(",
):
    start = nodes.find(signature)
    require(start >= 0, "saved bloom source query is missing " + signature)
    end = nodes.find("\\\\n    }", start)
    require(end > start, "could not isolate saved bloom source query " + signature)
    body = nodes[start:end]
    require("level.getBlockState(" not in body and "getChunk(" not in body
            and "getChunkNow(" not in body,
            "saved bloom scent queries must use persistent timestamps only: " + signature)'''
    if old_check in text:
        text = text.replace(old_check, new_check, 1)
        ecology_test.write_text(text, encoding="utf-8")
    else:
        # The root test file may already have been narrowed before the workflow copied it.
        require("public BlockPos nearestRecentBloom(" in text
                and "public int countRecentBlooms(" in text
                and "getChunkNow(" in text
                and "saved bloom" in text,
                "historical bloom-query test is neither old nor safely scoped")

new_test = "test_mutagen_field_convergence_173.py"
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == new_test:
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.72.0",
                               "Aktueller Entwicklungsstand: 1.73.0")
    if "build.gradle" in original:
        updated = updated.replace(r"1\.72\.0", r"1\.73\.0")
        updated = updated.replace("artifact must be version 1.72.0",
                                  "artifact must be version 1.73.0")
    updated = updated.replace(
        '"Version 1.72.0" in readme and "Version 1.71.0" in readme',
        '"Version 1.73.0" in readme and "Version 1.72.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.73.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.73.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.73.0 — Resonanzverdichtung überlappender Mutagenfelder

- **Feldüberlappung hat einen Gameplay-Effekt:** Wenn mindestens zwei aktive Quellen denselben Ort innerhalb ihrer Reichweite erreichen, steigt dessen effektive Mutagenstärke um eine Stufe, höchstens bis Stufe III.
- **Mehr als ein visueller Trick:** Pflanzenphänotypen, Ernteboni, Feldscanner und Mutagenblüten lesen weiterhin dieselbe operative Stärke. In Überschneidungszonen können deshalb sichtbare Hochstufen und seltene Blüten entstehen, ohne dass ein zusätzlicher Block-Ticker nötig ist.
- **Die Betriebsmodi bleiben maßgeblich:** Ruhende, entfernte, nicht registrierte oder per Redstone gesperrte Quellen tragen nichts zur Feldverdichtung bei. Kulturquellen zählen dagegen weiter als sichere Pflanzungsfelder, nicht als Terrain-Ausbreitung.
- **Chunk-sicher:** Quellen werden nur dann abgefragt, wenn ihr Chunk bereits geladen ist; die vorhandene Feldreichweite und vertikale Grenze bleiben unverändert.
- **Qualitätssicherung:** Tests sichern Quellenüberlappung, Stärke-Obergrenze, Modus-/Redstone-Gates, Chunk-Grenze, historische Duft-Abfragen und die aktiven Versionsmetadaten.

"""
current = """## Aktueller Entwicklungsschritt — 1.73.0

- **Resonanzverdichtung:** Die Stärke an einer Position wird aus allen dort wirksamen, tatsächlich aktiven Quellen ermittelt. Ab zwei überlappenden Quellen kommt eine Stufe hinzu, gedeckelt auf III.
- **Ökologie und Darstellung verbunden:** Stärkestufen fließen in die vorhandenen Pflanzenphänotypen, den Feldscanner, Ernte und Mutagenblüten ein.
- **Keine Geisterquellen:** Ruhende und Redstone-gesperrte Herde werden bei der Ermittlung ausgeschlossen; nicht geladene Quell-Chunks werden nicht geladen.
- **Regressionen getrennt nach Verantwortung:** Die alten Dufttests prüfen nur die gespeicherten Duftabfragen, während die neuen Feldtests tatsächliche Betriebszustände und Überlappung prüfen.

"""
if "## Version 1.73.0 — Resonanzverdichtung überlappender Mutagenfelder" not in readme:
    marker = "## Version 1.72.0 — Mutagenstärke folgt dem Betriebsmodus"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate 1.72 release heading to preserve history")
    readme = readme[:idx] + release + readme[idx:]
if "## Aktueller Entwicklungsschritt — 1.73.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.72.0"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate current 1.72 development section")
    readme = readme[:idx] + current + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.72.0 — Mutagenstärke folgt dem Betriebsmodus.**",
    "**Aktueller Entwicklungsstand: 1.73.0 — Resonanzverdichtung überlappender Mutagenfelder.**")
require("Aktueller Entwicklungsstand: 1.73.0" in readme,
        "README headline was not advanced")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.73.0 generated: overlapping active fields amplify Mutagen strength, while old bloom scent tests are narrowed to their intended methods.")
