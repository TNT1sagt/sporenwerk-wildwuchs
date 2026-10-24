#!/usr/bin/env python3
"""Give the Mutagen Field Control Station a bounded, cached comparator hazard output."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require_anchor(text: str, anchor: str, label: str) -> None:
    if anchor not in text:
        raise SystemExit(f"Cannot patch {label}: expected source anchor was not found")


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    require_anchor(text, old, label)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


station_path = SRC / "block/MutagenFieldControlStationBlock.java"
station = station_path.read_text(encoding="utf-8")

# Cache the last on-demand scan result in a blockstate property. A comparator reads
# that property cheaply; it never launches an expensive world scan every redstone tick.
if "public static final IntegerProperty POWER" not in station:
    station = station.replace(
        "import net.minecraft.world.level.block.state.BlockState;",
        "import net.minecraft.world.level.block.state.BlockState;\n"
        "import net.minecraft.world.level.block.state.StateDefinition;\n"
        "import net.minecraft.world.level.block.state.properties.IntegerProperty;",
        1
    )
    station = station.replace(
        "public final class MutagenFieldControlStationBlock extends Block {\n"
        "    public static final int HORIZONTAL_SCAN_RADIUS = 16;\n"
        "    public static final int VERTICAL_SCAN_RADIUS = 8;\n\n"
        "    public MutagenFieldControlStationBlock(Properties properties) { super(properties); }",
        """public final class MutagenFieldControlStationBlock extends Block {
    public static final int HORIZONTAL_SCAN_RADIUS = 16;
    public static final int VERTICAL_SCAN_RADIUS = 8;
    public static final IntegerProperty POWER = IntegerProperty.create("power", 0, 15);

    public MutagenFieldControlStationBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(POWER, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(POWER);
    }

    @Override
    public boolean hasAnalogOutputSignal(BlockState state) {
        return true;
    }

    @Override
    public int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos) {
        return state.getValue(POWER);
    }""",
        1
    )
    if "public static final IntegerProperty POWER" not in station or "hasAnalogOutputSignal" not in station:
        raise SystemExit("Could not install comparator output state on the Mutagen Field Control Station")

# Determine a stable severity reading from the exact same bounded survey shown to players:
# 0 = no detected Mutagen; 3 = mutated crops only; 4..10 = ordinary contaminated soil;
# 11..15 = strength-III hotspots, increasing with hotspot count.
if "private static int comparatorSignal(Survey s)" not in station:
    station = station.replace(
        "    private static Survey survey(ServerLevel level, BlockPos center) {",
        """    private static int comparatorSignal(Survey s) {
        if (s.highSoil() > 0) {
            return Math.min(15, 11 + Math.min(4, (s.highSoil() - 1) / 4));
        }
        if (s.soil() > 0) {
            return Math.min(10, 4 + Math.min(6, s.soil() / 8));
        }
        if (s.crops() > 0) return 3;
        return 0;
    }

    private static Survey survey(ServerLevel level, BlockPos center) {""",
        1
    )
if "int signal = comparatorSignal(s);" not in station:
    station = station.replace(
        "        Survey s = survey(serverLevel, pos);",
        """        Survey s = survey(serverLevel, pos);
        int signal = comparatorSignal(s);
        if (state.getValue(POWER) != signal) {
            // Block update flags notify nearby comparators; the full scan happens only
            // on player interaction, never as part of redstone polling.
            level.setBlock(pos, state.setValue(POWER, signal), 3);
        }""",
        1
    )
if "message.sporenwerk.fieldstation.comparator" not in station:
    station = station.replace(
        '        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.header").withStyle(ChatFormatting.AQUA), false);',
        '        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.header").withStyle(ChatFormatting.AQUA), false);\n'
        '        player.displayClientMessage(Component.translatable("message.sporenwerk.fieldstation.comparator", signal).withStyle(ChatFormatting.RED), false);',
        1
    )
if ("comparatorSignal(Survey s)" not in station
        or "state.setValue(POWER, signal)" not in station
        or "message.sporenwerk.fieldstation.comparator" not in station):
    raise SystemExit("Mutagen field comparator integration is incomplete")
station_path.write_text(station, encoding="utf-8")

# A blockstate property must define every possible value, even though all values share
# the same visible block model; POWER is a redstone output, not an animated texture.
blockstate_path = ASSETS / "blockstates/mutagenfeld_kontrollstation.json"
blockstate = {
    "variants": {
        f"power={power}": {"model": "sporenwerk:block/mutagenfeld_kontrollstation"}
        for power in range(16)
    }
}
blockstate_path.write_text(json.dumps(blockstate, indent=2) + "\n", encoding="utf-8")

locales = {
    "de_de.json": {
        "message.sporenwerk.fieldstation.comparator":
            "Redstone-Gefahrenwert: %s/15 — Comparator-Ausgang aktualisiert."
    },
    "en_us.json": {
        "message.sporenwerk.fieldstation.comparator":
            "Redstone hazard signal: %s/15 — comparator output updated."
    }
}
for filename, additions in locales.items():
    locale_path = ASSETS / "lang" / filename
    data = json.loads(locale_path.read_text(encoding="utf-8"))
    data.update(additions)
    locale_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Advance the generated mod after the 1.27.0 field-contrast patch.
build_path = ROOT / "build.gradle"
build, count = re.subn(
    r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
    "version = '1.28.0'",
    build_path.read_text(encoding="utf-8"),
    count=1
)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.28.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
heading = "## Version 1.28.0 — Redstone-Gefahrenausgang der Kontrollstation"
section = """## Version 1.28.0 — Redstone-Gefahrenausgang der Kontrollstation

- **Comparator-Ausgang:** Rechtsklick aktualisiert den zwischengespeicherten Gefahrenwert der Kontrollstation. Ein Comparator kann damit Warnlampen, Türen oder andere Redstone-Schaltungen ansteuern.
- **Eindeutige Signalstufen:** 0 bedeutet kein erfasster Befall, 3 steht für mutagenaktive Pflanzen ohne erfassten Mutagenboden, 4–10 skaliert mit normalem Mutagenboden und 11–15 mit der Anzahl der Stärke-III-Hotspots.
- **Keine Dauerbelastung:** Der aufwendige, begrenzte Scan wird ausschließlich bei der Interaktion ausgeführt. Comparator-Abfragen lesen nur die gespeicherte Blockzustandszahl und lösen keine Welt-Scans aus.
- **Qualitätssicherung:** Regressionstests prüfen alle 16 Blockstate-Varianten, den Comparator-Vertrag, die deutsche/englische Meldung, die Wertebereiche und den JAR-Inhalt.

Der Gefahrenausgang ist eine Momentaufnahme des letzten Stationsscans. Nach einer Feldveränderung muss erneut gescannt werden, damit der Redstone-Wert aktualisiert wird. Automatische Prüfungen ersetzen keinen manuellen Test im Minecraft-Client.

"""
if heading not in readme:
    marker = "## Version 1.27.0 — Mutagenfelder mit eindeutigen Stufensignaturen"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.27.0 release notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
readme_path.write_text(readme, encoding="utf-8")
print("Mutagen Field Control Station comparator output and version 1.28.0 generated.")
