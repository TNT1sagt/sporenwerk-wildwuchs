#!/usr/bin/env python3
"""1.64.0 adds an integrated residual-threat mode to the Mutagen Containment Relay."""
from pathlib import Path
import json
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Containment Relay residual threat 1.64: " + message)


def replace(source, old, new, sentinel, label):
    if sentinel in source:
        return source
    count = source.count(old)
    require(count == 1, f"{label}: expected exactly one source anchor, got {count}")
    return source.replace(old, new, 1)


relay_path = SRC / "block/MutagenContainmentRelayBlock.java"
relay = relay_path.read_text(encoding="utf-8")

relay = replace(
    relay,
    'public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 4);',
    'public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 5);',
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 5)',
    "six relay modes",
)
relay = replace(
    relay,
    "int mode = (state.getValue(MODE) + step) % 5;",
    "int mode = (state.getValue(MODE) + step) % 6;",
    "state.getValue(MODE) + step) % 6",
    "six-mode cycling",
)
relay = replace(
    relay,
    '            case 4 -> "message.sporenwerk.containment_relay.mode_intensity";',
    '            case 4 -> "message.sporenwerk.containment_relay.mode_intensity";\n'
    '            case 5 -> "message.sporenwerk.containment_relay.mode_residual";',
    'case 5 -> "message.sporenwerk.containment_relay.mode_residual"',
    "residual threat label",
)
relay = replace(
    relay,
    "        if ((mode == 3 || mode == 4) && signal >= 11) return ChatFormatting.RED;",
    "        if ((mode == 3 || mode == 4 || mode == 5) && signal >= 11) return ChatFormatting.RED;",
    "if ((mode == 3 || mode == 4 || mode == 5) && signal >= 11)",
    "residual threat warning color",
)
relay = replace(
    relay,
    "     * Mode 4: live terrain intensity from contaminated soil and mutated crops; no station scan required.\n",
    "     * Mode 4: live terrain intensity from contaminated soil and mutated crops; no station scan required.\n"
    "     * Mode 5: estimated residual threat after nearby powered wards and remaining dampener charges.\n",
    "Mode 5: estimated residual threat",
    "mode documentation",
)
switch_anchor = "            default -> Math.max(stationSignal, sirenSignal);"
switch_case = """            case 5 -> {
                int fieldThreat = 0;
                if (tierThreeSoil > 0) {
                    fieldThreat = Math.min(15, 11 + Math.min(4, (tierThreeSoil - 1) / 4));
                } else if (tierTwoSoil > 0) {
                    fieldThreat = Math.min(10, 7 + Math.min(3, (tierTwoSoil - 1) / 8));
                } else if (tierOneSoil > 0) {
                    fieldThreat = Math.min(6, 3 + Math.min(3, (tierOneSoil - 1) / 16));
                } else if (mutatedCrops > 0) {
                    fieldThreat = 2;
                }
                int rawThreat = Math.max(Math.max(stationSignal, sirenSignal), fieldThreat);
                int protectionBuffer = Math.min(12,
                        poweredWards * 4 + Math.min(3, counterpulses) * 3);
                yield rawThreat == 0 ? 0 : Math.max(1, rawThreat - protectionBuffer);
            }
            default -> Math.max(stationSignal, sirenSignal);"""
relay = replace(relay, switch_anchor, switch_case, "case 5 -> {\n                int fieldThreat", "residual threat output mode")
relay_path.write_text(relay, encoding="utf-8")

# Keep the visual appearance stable across every legal mode/signal combination.
blockstate_path = ASSETS / "blockstates/mutagen_containment_relay.json"
blockstate_path.write_text(json.dumps({
    "variants": {
        f"mode={mode},signal={signal}": {"model": "sporenwerk:block/mutagen_containment_relay"}
        for mode in range(6) for signal in range(16)
    }
}, indent=2) + "\n", encoding="utf-8")

for filename, value in (
    ("de_de.json", "Restgefahr nach Schutzmaßnahmen"),
    ("en_us.json", "Residual threat after protection"),
):
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale["message.sporenwerk.containment_relay.mode_residual"] = value
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Migrate the two existing relay tests instead of leaving stale four-/five-mode assertions.
legacy_path = ROOT / "tools/test_mutagen_containment_relay.py"
legacy = legacy_path.read_text(encoding="utf-8")
for old, new in (
    ('IntegerProperty MODE = IntegerProperty.create("mode", 0, 4)',
     'IntegerProperty MODE = IntegerProperty.create("mode", 0, 5)'),
    ("int mode = (state.getValue(MODE) + step) % 5;",
     "int mode = (state.getValue(MODE) + step) % 6;"),
    ("len(variants) == 80", "len(variants) == 96"),
    ("for mode in range(5):", "for mode in range(6):"),
    ("all 5 MODE × 16 SIGNAL", "all 6 MODE × 16 SIGNAL"),
):
    if new not in legacy:
        require(old in legacy, "could not migrate legacy relay test: " + old)
        legacy = legacy.replace(old, new, 1)
if '"case 5 ->"' not in legacy:
    anchor = '    "case 4 ->",'
    if anchor not in legacy:
        anchor = '    "case 4 -> {",'
    require(anchor in legacy, "could not add residual mode to relay contract test")
    legacy = legacy.replace(anchor, anchor + '\n    "case 5 ->",', 1)
if '"message.sporenwerk.containment_relay.mode_residual"' not in legacy:
    anchor = '"message.sporenwerk.containment_relay.mode_intensity",'
    require(anchor in legacy, "could not extend localized relay mode assertions")
    legacy = legacy.replace(anchor, anchor + '\n        "message.sporenwerk.containment_relay.mode_residual",', 1)
legacy_path.write_text(legacy, encoding="utf-8")

# Keep the original field intensity test relevant while the combined mode gets its own test.
intensity_path = ROOT / "tools/test_field_intensity_relay_163.py"
intensity = intensity_path.read_text(encoding="utf-8")
for old, new in (
    ('IntegerProperty MODE = IntegerProperty.create("mode", 0, 4)',
     'IntegerProperty MODE = IntegerProperty.create("mode", 0, 5)'),
    ("int mode = (state.getValue(MODE) + step) % 5;",
     "int mode = (state.getValue(MODE) + step) % 6;"),
    ("len(variants) == 80", "len(variants) == 96"),
    ("for mode in range(5):", "for mode in range(6):"),
    ("five modes × sixteen signals", "six modes × sixteen signals"),
):
    if new not in intensity:
        require(old in intensity, "could not migrate field-intensity test: " + old)
        intensity = intensity.replace(old, new, 1)
intensity_path.write_text(intensity, encoding="utf-8")
print("Containment Relay six-mode residual threat logic generated.")
