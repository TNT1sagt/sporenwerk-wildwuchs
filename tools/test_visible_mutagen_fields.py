#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Visible mutagen field regression: " + message)
version_text = read("build.gradle")
version_match = re.search(r"version\s*=\s*['\"](\d+)\.(\d+)\.(\d+)['\"]", version_text)
require(version_match is not None and tuple(int(part) for part in version_match.groups()) >= (1, 13, 0),
        "build must remain on the visible-field milestone or newer")
blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
require("MUTAGEN_BODEN" in blocks and ".lightLevel(state -> switch (state.getValue(de.sporenwerk.block.InfestedTerrainBlock.MUTAGEN_LEVEL))" in blocks, "infected terrain light must follow its synchronized tier")
for token in ("case 1 -> 5", "case 2 -> 9", "case 3 -> 13", "default -> 0"):
    require(token in blocks, "dynamic terrain lighting missing " + token)
terrain = read("src/main/java/de/sporenwerk/block/InfestedTerrainBlock.java")
for token in ("IntegerProperty MUTAGEN_LEVEL", "IntegerProperty.create(\"mutagen_level\", 0, 3)", "registerDefaultState(defaultBlockState().setValue(MUTAGEN_LEVEL, 0))", "MutationField.mutagenStrengthAt(level, pos)", "state.setValue(MUTAGEN_LEVEL, strength)"):
    require(token in terrain, "terrain strength state missing " + token)
terrain_states = json.loads(read("src/main/resources/assets/sporenwerk/blockstates/mutagen_boden.json"))
for tier in range(4):
    model = terrain_states["variants"].get(f"mutagen_level={tier}", {}).get("model")
    expected = "sporenwerk:block/mutagen_boden" if tier == 0 else f"sporenwerk:block/mutagen_boden_strength{tier}"
    require(model == expected, f"terrain visual tier {tier} must map to {expected}")
    if tier:
        require((root / f"src/main/resources/assets/sporenwerk/models/block/mutagen_boden_strength{tier}.json").is_file(),
                f"terrain visual tier {tier} model is missing")
        require((root / f"src/main/resources/assets/sporenwerk/textures/block/mutagen_boden_strength{tier}.png").is_file(),
                f"terrain visual tier {tier} texture is missing")
visual = read("src/main/java/de/sporenwerk/client/MutagenFieldVisuals.java")
for token in ("@Mod.EventBusSubscriber", "TickEvent.LevelTickEvent", "ModBlocks.MUTAGEN_BODEN.get()", "ParticleTypes.WARPED_SPORE", "ParticleTypes.SOUL_FIRE_FLAME", "ParticleTypes.PORTAL", "ParticleTypes.END_ROD", "mutagenLevel >= 2", "mutagenLevel >= 3", "sporeChance", "0.30F", "0.24F", "fieldTier >= 2", "fieldTier >= 3", "AbstractSporeCropBlock.MUTAGEN_LEVEL", "level.getGameTime() % 10L", "int particleBudget = 24", "particleBudget--", "dy = -2; dy <= 2 && particleBudget > 0"):
    require(token in visual, "client visuals missing " + token)
scanner = read("src/main/java/de/sporenwerk/item/FeldscannerItem.java")
for token in (
    "public InteractionResultHolder<ItemStack> use(Level level",
    "private static final int AREA_SCAN_RADIUS = 8",
    "private static final int AREA_SCAN_VERTICAL_RADIUS = 4",
    "MutationNodeData.get(level)",
    "nodeData.isActive(cursor)",
    "MutationField.mutagenStrengthAt(level, cursor)",
    "activeNodes++", "inactiveNodes++", "strongestField =", "anchors++",
    "tierOneSoil++", "tierTwoSoil++", "tierThreeSoil++",
    "mutatedCrops++", "poweredWards++", "availableChargeUnits +=",
    "activeAlarms++", "criticalAlarms++", "activeRelays++",
    "level.hasChunkAt(cursor)",
    "message.sporenwerk.scanner.survey.nodes",
    "message.sporenwerk.scanner.survey.fields",
    "message.sporenwerk.scanner.survey.devices",
    "message.sporenwerk.scanner.survey.threats",
    "message.sporenwerk.scanner.survey.guidance.",
):
    require(token in scanner, "multi-system area survey missing " + token)
require(scanner.count("public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand)") == 1,
        "the existing air-use action must be extended without duplicate overrides")
for locale in ("de_de.json", "en_us.json"):
    data = json.loads((root / "src/main/resources/assets/sporenwerk/lang" / locale).read_text(encoding="utf-8"))
    for key in (
        "message.sporenwerk.scanner.survey.header", "message.sporenwerk.scanner.survey.nodes",
        "message.sporenwerk.scanner.survey.fields", "message.sporenwerk.scanner.survey.crops",
        "message.sporenwerk.scanner.survey.devices", "message.sporenwerk.scanner.survey.threats",
        "message.sporenwerk.scanner.survey.loaded",
        "message.sporenwerk.scanner.survey.guidance.pirscher",
        "message.sporenwerk.scanner.survey.guidance.uncontained",
        "message.sporenwerk.scanner.survey.guidance.critical",
        "message.sporenwerk.scanner.survey.guidance.elevated",
        "message.sporenwerk.scanner.survey.guidance.active",
        "message.sporenwerk.scanner.survey.guidance.clear",
    ):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)
require("Version 1.13.0" in read("README.md"), "release notes missing 1.13.0")
require("String guidanceKey" in scanner and "message.sporenwerk.scanner.survey.guidance." in scanner,
        "scanner must convert readings into actionable cross-system hazard advice")
print("Visible field glow/particles and chunk-safe multi-system scanner survey passed.")
