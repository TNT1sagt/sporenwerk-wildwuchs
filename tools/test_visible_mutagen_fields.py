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
require("MUTAGEN_BODEN" in blocks and ".lightLevel(state -> 4)" in blocks, "infected terrain must have a low glow")
visual = read("src/main/java/de/sporenwerk/client/MutagenFieldVisuals.java")
for token in ("@Mod.EventBusSubscriber", "TickEvent.LevelTickEvent", "ModBlocks.MUTAGEN_BODEN.get()", "ParticleTypes.WARPED_SPORE", "ParticleTypes.SOUL_FIRE_FLAME", "ParticleTypes.PORTAL", "ParticleTypes.END_ROD", "mutagenLevel >= 2", "mutagenLevel >= 3", "0.42F", "0.16F", "AbstractSporeCropBlock.MUTAGEN_LEVEL", "level.getGameTime() % 10L", "int particleBudget = 24", "particleBudget--", "dy = -2; dy <= 2 && particleBudget > 0"):
    require(token in visual, "client visuals missing " + token)
scanner = read("src/main/java/de/sporenwerk/item/FeldscannerItem.java")
for token in ("public InteractionResultHolder<ItemStack> use(Level level", "MutationNodeData.get(serverLevel)", "MutationField.mutagenStrengthAt(serverLevel, target)", "infectedTerrain++", "mutatedPlants++", "message.sporenwerk.scanner.survey"):
    require(token in scanner, "area survey missing " + token)
for locale in ("de_de.json", "en_us.json"):
    data = json.loads((root / "src/main/resources/assets/sporenwerk/lang" / locale).read_text(encoding="utf-8"))
    require(bool(data.get("message.sporenwerk.scanner.survey", "").strip()), locale + " missing area-survey text")
require("Version 1.13.0" in read("README.md"), "release notes missing 1.13.0")
print("Visible field glow/particles and bounded scanner area survey passed.")
