#!/usr/bin/env python3
"""1.68.0 adds an event-driven Colossus response signal to the Containment Relay."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.68: " + message)


def patch(source, old, new, sentinel, label):
    if sentinel in source:
        return source
    count = source.count(old)
    require(count == 1, f"{label}: expected one source anchor, got {count}")
    return source.replace(old, new, 1)


# Containment Relay mode 7 reports only actionable boss phases:
# 0 = no active response, 6 = exposed core, 10 = other attack wind-up, 15 = breath wind-up.
relay_path = SRC / "block/MutagenContainmentRelayBlock.java"
relay = relay_path.read_text(encoding="utf-8")
relay = patch(
    relay, "import de.sporenwerk.registry.ModBlocks;\n",
    "import de.sporenwerk.registry.ModBlocks;\n"
    "import de.sporenwerk.entity.MutagenkolossEntity;\n"
    "import net.minecraft.world.phys.AABB;\n",
    "import de.sporenwerk.entity.MutagenkolossEntity;",
    "boss response imports",
)
relay = patch(
    relay,
    'public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 6);',
    'public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 7);',
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 7)',
    "eight relay modes",
)
relay = patch(
    relay,
    "int mode = (state.getValue(MODE) + step) % 7;",
    "int mode = (state.getValue(MODE) + step) % 8;",
    "state.getValue(MODE) + step) % 8",
    "eight-mode selection",
)
relay = patch(
    relay,
    '            case 6 -> "message.sporenwerk.containment_relay.mode_margin";',
    '            case 6 -> "message.sporenwerk.containment_relay.mode_margin";\n'
    '            case 7 -> "message.sporenwerk.containment_relay.mode_boss";',
    'case 7 -> "message.sporenwerk.containment_relay.mode_boss"',
    "boss response mode name",
)
# Mode 6 is inverse safety; mode 7 uses phase-aware response colors.
color_start = "    private static ChatFormatting colorFor(int mode, int signal) {"
color_end = "\n    private static String modeKey(int mode) {"
start = relay.find(color_start)
require(start >= 0, "could not find relay color method")
end = relay.find(color_end, start)
require(end > start, "could not find relay mode-key method")
color_method = """    private static ChatFormatting colorFor(int mode, int signal) {
        if (mode == 6) {
            if (signal <= 3) return ChatFormatting.RED;
            if (signal <= 7) return ChatFormatting.YELLOW;
            return ChatFormatting.GREEN;
        }
        if (mode == 7) {
            if (signal >= 12) return ChatFormatting.RED;
            if (signal >= 8) return ChatFormatting.YELLOW;
            if (signal == 6) return ChatFormatting.AQUA;
            if (signal > 0) return ChatFormatting.YELLOW;
            return ChatFormatting.GREEN;
        }
        if ((mode == 3 || mode == 4 || mode == 5) && signal >= 11) return ChatFormatting.RED;
        if (signal >= 11) return ChatFormatting.RED;
        if (signal > 0) return ChatFormatting.YELLOW;
        return ChatFormatting.GREEN;
    }
"""
if "if (mode == 7)" not in relay[start:end]:
    relay = relay[:start] + color_method + relay[end:]

helper = """    /**
     * Read the current phase of living Colossi in a bounded loaded-entity view.
     * It is evaluated only on relay events/interactions, not from a permanent ticker.
     */
    private static int bossResponseSignal(Level level, BlockPos center) {
        AABB bounds = new AABB(
                center.getX() - HORIZONTAL_SCAN_RADIUS,
                center.getY() - VERTICAL_SCAN_RADIUS,
                center.getZ() - HORIZONTAL_SCAN_RADIUS,
                center.getX() + HORIZONTAL_SCAN_RADIUS + 1,
                center.getY() + VERTICAL_SCAN_RADIUS + 1,
                center.getZ() + HORIZONTAL_SCAN_RADIUS + 1);
        int strongest = 0;
        for (MutagenkolossEntity boss : level.getEntitiesOfClass(
                MutagenkolossEntity.class, bounds, entity -> entity.isAlive())) {
            double dx = boss.getX() - (center.getX() + 0.5D);
            double dz = boss.getZ() - (center.getZ() + 0.5D);
            if (dx * dx + dz * dz > HORIZONTAL_SCAN_RADIUS * HORIZONTAL_SCAN_RADIUS
                    || Math.abs(boss.getY() - center.getY()) > VERTICAL_SCAN_RADIUS) continue;

            int signal;
            if (boss.getAttackState() == MutagenkolossEntity.ATTACK_BREATH
                    && boss.getAttackTicks() > 0) {
                signal = 15;
            } else if (boss.isCoreExposed()) {
                signal = 6;
            } else if (boss.getAttackTicks() > 0) {
                signal = 10;
            } else {
                signal = 0;
            }
            strongest = Math.max(strongest, signal);
        }
        return strongest;
    }

"""
relay = patch(
    relay,
    "    private static int evaluate(Level level, BlockPos center, int mode) {",
    helper + "    private static int evaluate(Level level, BlockPos center, int mode) {",
    "private static int bossResponseSignal(Level level, BlockPos center)",
    "bounded boss-response evaluator",
)
relay = patch(
    relay,
    "            default -> Math.max(stationSignal, sirenSignal);",
    "            case 7 -> bossResponseSignal(level, center);\n"
    "            default -> Math.max(stationSignal, sirenSignal);",
    "case 7 -> bossResponseSignal(level, center)",
    "boss response comparator case",
)
relay_path.write_text(relay, encoding="utf-8")

# Eight modes x 16 cached signal values; the same pixel-art model is reused.
blockstate_path = ASSETS / "blockstates/mutagen_containment_relay.json"
blockstate_path.write_text(json.dumps({
    "variants": {
        f"mode={mode},signal={signal}": {"model": "sporenwerk:block/mutagen_containment_relay"}
        for mode in range(8) for signal in range(16)
    }
}, indent=2) + "\n", encoding="utf-8")
for filename, value in (
    ("de_de.json", "Kristallkoloss-Reaktion"),
    ("en_us.json", "Crystal Colossus response"),
):
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale["message.sporenwerk.containment_relay.mode_boss"] = value
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Boss phase transitions refresh nearby relay modes as events, never as a ticker.
entity_path = SRC / "entity/MutagenkolossEntity.java"
entity = entity_path.read_text(encoding="utf-8")
entity = patch(
    entity,
    "            if (this.coreExposureTicks == 0) {\n"
    "                this.entityData.set(CORE_EXPOSED, false);\n"
    "            } else if (this.coreExposureTicks % 6 == 0",
    "            if (this.coreExposureTicks == 0) {\n"
    "                this.entityData.set(CORE_EXPOSED, false);\n"
    "                // Refresh response relays when the exposure timer expires.\n"
    "                MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());\n"
    "            } else if (this.coreExposureTicks % 6 == 0",
    "// Refresh response relays when the exposure timer expires.",
    "exposed-core expiry refresh",
)
entity = patch(
    entity,
    "    }\n\n    private void emitWindupParticles() {\n",
    "        // Refresh response relays when the attack wind-up begins.\n"
    "        MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());\n"
    "    }\n\n    private void emitWindupParticles() {\n",
    "// Refresh response relays when the attack wind-up begins.",
    "attack-start relay refresh",
)
entity = patch(
    entity,
    "        this.entityData.set(ATTACK_STATE, ATTACK_IDLE);\n"
    "        this.entityData.set(ATTACK_TICKS, 0);\n"
    "    }\n\n"
    "    private void performStomp(float damage, double radius) {",
    "        this.entityData.set(ATTACK_STATE, ATTACK_IDLE);\n"
    "        this.entityData.set(ATTACK_TICKS, 0);\n"
    "        // Refresh response relays after the attack resolves.\n"
    "        MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());\n"
    "    }\n\n"
    "    private void performStomp(float damage, double radius) {",
    "// Refresh response relays after the attack resolves.",
    "attack-release relay refresh",
)
entity = patch(
    entity,
    "        this.coreExposureTicks = Math.max(this.coreExposureTicks, 60);\n"
    "        this.entityData.set(CORE_EXPOSED, true);\n",
    "        this.coreExposureTicks = Math.max(this.coreExposureTicks, 60);\n"
    "        this.entityData.set(CORE_EXPOSED, true);\n"
    "        // Let response relays observe the exposed-core counter window.\n"
    "        MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());\n",
    "// Let response relays observe the exposed-core counter window.",
    "parry-window relay refresh",
)
entity_path.write_text(entity, encoding="utf-8")

# If several threats stand near the player, preserve nearest-first order among them but
# stable-prioritize an interruptible Colossus so a paid shard cannot be spent on lesser mobs.
focus_path = SRC / "item/ResonanzfokusItem.java"
focus = focus_path.read_text(encoding="utf-8")
focus = patch(
    focus,
    "        targets.sort(Comparator.comparingDouble(target -> player.distanceToSqr(target)));\n",
    "        targets.sort(Comparator.comparingDouble(target -> player.distanceToSqr(target)));\n"
    "        targets.sort(Comparator.comparingInt(target -> target instanceof MutagenkolossEntity ? 0 : 1));\n",
    "targets.sort(Comparator.comparingInt(target -> target instanceof MutagenkolossEntity ? 0 : 1));",
    "boss-priority target ordering",
)
focus_path.write_text(focus, encoding="utf-8")

# Advance active-version assertions, preserving each test's feature-specific checks.
new_tests = {"test_boss_response_relay_168.py"}
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name in new_tests:
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.67.0",
                             "Aktueller Entwicklungsstand: 1.68.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.67\.0", r"1\.68\.0")
        updated = updated.replace("artifact must be version 1.67.0",
                                  "artifact must be version 1.68.0")
    updated = updated.replace(
        '"Version 1.67.0" in readme and "Version 1.66.0" in readme',
        '"Version 1.68.0" in readme and "Version 1.67.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

# Mode-count assertions in legacy and subsequent relay tests must now cover 128 states.
for test_name in (
    "test_mutagen_containment_relay.py",
    "test_field_intensity_relay_163.py",
    "test_field_response_relay_164.py",
    "test_containment_margin_relay_165.py",
):
    test_path = ROOT / "tools" / test_name
    if not test_path.exists():
        continue
    source = test_path.read_text(encoding="utf-8")
    for old, new in (
        ('IntegerProperty MODE = IntegerProperty.create("mode", 0, 6)',
         'IntegerProperty MODE = IntegerProperty.create("mode", 0, 7)'),
        ("int mode = (state.getValue(MODE) + step) % 7;",
         "int mode = (state.getValue(MODE) + step) % 8;"),
        ("len(variants) == 112", "len(variants) == 128"),
        ("for mode in range(7):", "for mode in range(8):"),
        ("all 7 MODE × 16 SIGNAL", "all 8 MODE × 16 SIGNAL"),
        ("seven modes × sixteen signal strengths", "eight modes × sixteen signal strengths"),
    ):
        if old in source and new not in source:
            source = source.replace(old, new, 1)
    if '"message.sporenwerk.containment_relay.mode_boss",' not in source:
        anchor = '"message.sporenwerk.containment_relay.mode_margin",'
        if anchor in source:
            source = source.replace(anchor, anchor + '\n        "message.sporenwerk.containment_relay.mode_boss",', 1)
    if '"case 7 -> bossResponseSignal(level, center)"' not in source and '"case 6 ->"' in source:
        source = source.replace('"case 6 ->",', '"case 6 ->",\n    "case 7 -> bossResponseSignal(level, center)",', 1)
    test_path.write_text(source, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.68.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle version to 1.68.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.68.0 — Boss-Reaktionssignal für Redstone und Fokus-Priorität

- **Achter Relaismodus:** „Kristallkoloss-Reaktion“ liefert einen Comparator-Wert für aktuelle Bossphasen: 15 während der Atem-Aufladung, 10 bei anderen Aufladeangriffen, 6 bei freigelegtem Kern und 0 ohne aktive Reaktion.
- **Ereignisgesteuerte Aktualisierung:** Angriffsbeginn, Angriffsabschluss, Fokus-Parade und Ende der Kernöffnung aktualisieren höchstens 32 nahe Relais. Keine neue Tick-Schleife und keine erzwungenen Chunk-Loads.
- **Fokus priorisiert den Boss:** Wenn der Koloss seinen Kristallatem auflädt, steht er vor gewöhnlichen Zielen in der Fokus-Auswahl. Ein teurer Resonanzsplitter wird nicht zuerst an drei näheren Nebengegnern verbraucht.
- **Signal-Farben:** Atem-Aufladung rot, andere Boss-Aufladung gelb, verwundbarer Kern cyan und keine aktive Reaktion grün.
- **Qualitätssicherung:** Regressionen prüfen 128 Relaiszustände, Bossphasen, Event-Refresh, geladene Chunks, Fokus-Priorität und DE/EN-Übersetzungen.

"""
if "## Version 1.68.0 — Boss-Reaktionssignal für Redstone und Fokus-Priorität" not in readme:
    marker = "## Version 1.67.0 — Resonanzfokus kann den Kristallatem parieren"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.67.0 release notes")
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.68.0 — Boss-Reaktionssignal und priorisierte Resonanzfokus-Parade.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus_heads = [line for line in readme.splitlines() if line.startswith("## Aktueller Entwicklungsschritt — ")]
if focus_heads:
    readme = readme.replace(focus_heads[0], "## Aktueller Entwicklungsschritt — 1.68.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.68.0 boss-response relay, event refresh, and focus-priority changes generated.")
