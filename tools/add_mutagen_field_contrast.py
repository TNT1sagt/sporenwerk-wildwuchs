#!/usr/bin/env python3
"""Make Mutagen field strength readable through distinct pixel art, light, and particles."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"
TEXTURES = ASSETS / "textures/block"


# Glow follows the synchronized strength stored in the server-updated blockstate.
blocks_path = SRC / "registry/ModBlocks.java"
blocks = blocks_path.read_text(encoding="utf-8")
old_light = ".lightLevel(state -> 4)"
new_light = (
    ".lightLevel(state -> switch "
    "(state.getValue(de.sporenwerk.block.InfestedTerrainBlock.MUTAGEN_LEVEL)) "
    "{ case 1 -> 5; case 2 -> 9; case 3 -> 13; default -> 0; })"
)
if new_light not in blocks:
    if old_light not in blocks:
        raise SystemExit("Cannot install strength-dependent Mutagen soil lighting")
    blocks_path.write_text(blocks.replace(old_light, new_light, 1), encoding="utf-8")


def speckle(image: Image.Image, colors, a: int, b: int, modulus: int) -> None:
    pixels = image.load()
    for y in range(16):
        for x in range(16):
            if (x * a + y * b) % modulus in (0, 1):
                pixels[x, y] = colors[(x + y) % len(colors)]


# Tier I: living mycelium — moss-dark soil, branching acid-green filaments, and spores.
tier1 = Image.new("RGBA", (16, 16), (20, 36, 28, 255))
speckle(tier1, [(29, 49, 34, 255), (39, 62, 39, 255), (25, 44, 32, 255)], 3, 5, 11)
d = ImageDraw.Draw(tier1)
d.polygon([(0, 0), (4, 0), (3, 3), (0, 5)], fill=(34, 54, 35, 255))
d.polygon([(10, 10), (15, 9), (15, 15), (12, 14)], fill=(31, 50, 34, 255))
d.line([(0, 12), (3, 10), (5, 11), (7, 8), (10, 9), (12, 5), (15, 4)],
       fill=(105, 201, 62, 255), width=1)
d.line([(5, 11), (5, 14), (8, 15)], fill=(83, 166, 54, 255), width=1)
d.line([(10, 9), (11, 12), (14, 13)], fill=(83, 166, 54, 255), width=1)
for x, y in [(3, 10), (7, 8), (12, 5), (5, 14), (14, 13)]:
    d.rectangle((x, y, x, y), fill=(198, 245, 101, 255))
d.point((1, 2), fill=(99, 160, 73, 255))
d.point((14, 1), fill=(70, 122, 59, 255))

# Tier II: unstable fracture field — violet-black crust with hot orange/magenta ruptures.
tier2 = Image.new("RGBA", (16, 16), (28, 20, 36, 255))
speckle(tier2, [(43, 28, 52, 255), (36, 25, 45, 255), (53, 27, 57, 255)], 5, 7, 13)
d = ImageDraw.Draw(tier2)
d.polygon([(0, 0), (5, 1), (4, 4), (1, 6), (0, 4)], fill=(48, 28, 54, 255))
d.polygon([(9, 9), (12, 7), (15, 9), (15, 15), (11, 14)], fill=(43, 25, 48, 255))
d.line([(0, 2), (3, 4), (3, 7), (7, 8), (8, 11), (12, 12), (15, 15)],
       fill=(222, 55, 185, 255), width=2)
d.line([(0, 13), (4, 11), (6, 8), (9, 6), (10, 3), (14, 1)],
       fill=(255, 112, 58, 255), width=1)
d.line([(7, 8), (10, 9), (13, 7), (15, 8)], fill=(255, 157, 71, 255), width=1)
d.line([(3, 7), (1, 9), (1, 11)], fill=(171, 51, 155, 255), width=1)
for x, y in [(3, 4), (7, 8), (10, 3), (12, 12), (13, 7)]:
    d.rectangle((x, y, min(15, x + 1), min(15, y + 1)), fill=(255, 177, 83, 255))

# Tier III: crystalline rupture — deep teal plates, cyan edges, and near-white cores.
tier3 = Image.new("RGBA", (16, 16), (9, 29, 39, 255))
speckle(tier3, [(14, 43, 52, 255), (12, 35, 47, 255), (21, 54, 61, 255)], 7, 3, 12)
d = ImageDraw.Draw(tier3)
d.polygon([(1, 0), (5, 2), (4, 5), (1, 4)], fill=(18, 67, 78, 255), outline=(49, 205, 230, 255))
d.polygon([(9, 0), (13, 1), (15, 4), (12, 6), (9, 4)], fill=(13, 55, 69, 255), outline=(44, 190, 223, 255))
d.polygon([(2, 8), (6, 6), (9, 9), (7, 13), (3, 12)], fill=(13, 57, 68, 255), outline=(49, 220, 238, 255))
d.polygon([(10, 8), (13, 6), (15, 9), (14, 13), (11, 15), (9, 12)],
          fill=(16, 67, 77, 255), outline=(67, 229, 244, 255))
d.line([(0, 6), (3, 7), (5, 5), (7, 7), (9, 6)], fill=(42, 177, 211, 255), width=1)
d.line([(5, 2), (7, 4), (7, 7), (10, 9)], fill=(102, 239, 248, 255), width=1)
d.line([(0, 15), (3, 13), (7, 14), (9, 12)], fill=(39, 178, 205, 255), width=1)
for x, y in [(3, 2), (11, 2), (6, 9), (12, 10), (5, 11), (13, 13)]:
    d.point((x, y), fill=(232, 255, 255, 255))
d.point((8, 1), fill=(122, 90, 194, 255))
d.point((1, 14), fill=(83, 93, 195, 255))

TEXTURES.mkdir(parents=True, exist_ok=True)
for tier, image in {1: tier1, 2: tier2, 3: tier3}.items():
    path = TEXTURES / f"mutagen_boden_strength{tier}.png"
    image.save(path, optimize=True)
    with Image.open(path) as check:
        rgba = check.convert("RGBA")
        if rgba.size != (16, 16) or any(pixel[3] != 255 for pixel in rgba.getdata()):
            raise SystemExit(f"Mutagen field tier {tier} texture must be opaque 16x16")

# Make the synchronized blockstate-to-model contract explicit.
(ASSETS / "blockstates/mutagen_boden.json").write_text(json.dumps({
    "variants": {
        f"mutagen_level={tier}": {
            "model": "sporenwerk:block/mutagen_boden" if tier == 0
                     else f"sporenwerk:block/mutagen_boden_strength{tier}"
        } for tier in range(4)
    }
}, indent=2) + "\n", encoding="utf-8")
for tier in range(1, 4):
    model_path = ASSETS / f"models/block/mutagen_boden_strength{tier}.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps({
        "parent": "minecraft:block/cube_all",
        "textures": {"all": f"sporenwerk:block/mutagen_boden_strength{tier}"}
    }, indent=2) + "\n", encoding="utf-8")

# Field tier I stays spore-led; tier II adds instability flicker; tier III adds crystal sparks.
visual_path = SRC / "client/MutagenFieldVisuals.java"
visual = visual_path.read_text(encoding="utf-8")
if "import de.sporenwerk.block.InfestedTerrainBlock;" not in visual:
    visual = visual.replace(
        "import de.sporenwerk.Sporenwerk;",
        "import de.sporenwerk.Sporenwerk;\nimport de.sporenwerk.block.InfestedTerrainBlock;",
        1
    )
branch_old = "if (state.is(ModBlocks.MUTAGEN_BODEN.get())) {"
branch_new = """if (state.is(ModBlocks.MUTAGEN_BODEN.get())) {
                        int fieldTier = state.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL);
                        float sporeChance = fieldTier == 1 ? 0.30F
                                : fieldTier == 2 ? 0.38F
                                : fieldTier >= 3 ? 0.46F : 0.08F;"""
if branch_new not in visual:
    if branch_old not in visual:
        raise SystemExit("Cannot add tier-aware Mutagen soil particles")
    visual = visual.replace(branch_old, branch_new, 1)
if "level.random.nextFloat() < sporeChance" not in visual:
    if "level.random.nextFloat() < 0.42F" not in visual:
        raise SystemExit("Cannot tune base Mutagen spore probability")
    visual = visual.replace("level.random.nextFloat() < 0.42F",
                            "level.random.nextFloat() < sporeChance", 1)
if "fieldTier >= 2 && particleBudget > 0 && level.random.nextFloat() < (fieldTier >= 3 ? 0.24F : 0.10F)" not in visual:
    old = "if (particleBudget > 0 && level.random.nextFloat() < 0.16F) {"
    if old not in visual:
        raise SystemExit("Cannot add tier-gated Mutagen soul-fire particles")
    visual = visual.replace(old,
        "if (fieldTier >= 2 && particleBudget > 0 && level.random.nextFloat() < (fieldTier >= 3 ? 0.24F : 0.10F)) {", 1)
if "fieldTier >= 2 && particleBudget > 0 && level.random.nextFloat() < (fieldTier >= 3 ? 0.16F : 0.06F)" not in visual:
    old = "if (particleBudget > 0 && level.random.nextFloat() < 0.05F) {"
    if old not in visual:
        raise SystemExit("Cannot add tier-gated Mutagen portal particles")
    visual = visual.replace(old,
        "if (fieldTier >= 2 && particleBudget > 0 && level.random.nextFloat() < (fieldTier >= 3 ? 0.16F : 0.06F)) {", 1)
endrod = """                        if (fieldTier >= 3 && particleBudget > 0 && level.random.nextFloat() < 0.12F) {
                            level.addParticle(ParticleTypes.END_ROD,
                                    pos.getX() + 0.25D + level.random.nextDouble() * 0.5D,
                                    pos.getY() + 0.72D + level.random.nextDouble() * 0.42D,
                                    pos.getZ() + 0.25D + level.random.nextDouble() * 0.5D,
                                    0.0D, 0.016D, 0.0D);
                            particleBudget--;
                        }
"""
crop_anchor = "                    } else if (state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)) {"
if "fieldTier >= 3 && particleBudget > 0 && level.random.nextFloat() < 0.12F" not in visual:
    if crop_anchor not in visual:
        raise SystemExit("Cannot add tier-III crystal sparks to Mutagen soil")
    visual = visual.replace(crop_anchor, endrod + crop_anchor, 1)
visual_path.write_text(visual, encoding="utf-8")

# Show the three tier identities next to each other in the pixel-art QA sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = '    ("mutagen_boden_side", "Boden-Seite"),'
addon = anchor + '\n' + \
    '    ("mutagen_boden_strength1", "Feld I — Myzel"),\n' + \
    '    ("mutagen_boden_strength2", "Feld II — Risse"),\n' + \
    '    ("mutagen_boden_strength3", "Feld III — Kristall"),'
if "mutagen_boden_strength3" not in preview:
    if anchor not in preview:
        raise SystemExit("Cannot add Mutagen tier signatures to the art preview")
    preview_path.write_text(preview.replace(anchor, addon, 1), encoding="utf-8")

# Advance the generated mod and preserve the existing 1.26.0 history.
build_path = ROOT / "build.gradle"
build = build_path.read_text(encoding="utf-8")
build, count = re.subn(
    r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
    "version = '1.27.0'",
    build,
    count=1
)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.27.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
heading = "## Version 1.27.0 — Mutagenfelder mit eindeutigen Stufensignaturen"
section = """## Version 1.27.0 — Mutagenfelder mit eindeutigen Stufensignaturen

- **Drei klar verschiedene Pixelmuster:** Stufe I zeichnet grüne Myzeladern in dunklem Moosboden, Stufe II zeigt magenta-orange Bruchrisse und Stufe III cyanweiße Kristallplatten mit hellen Kernen. Die Muster unterscheiden sich in Form und Farbpalette, nicht nur in der Helligkeit.
- **Licht folgt der Feldstärke:** Die synchronisierte Bodenstufe steuert die Lichtabgabe (Stufe I: 5, Stufe II: 9, Stufe III: 13). Inaktive/restliche Felder leuchten nicht weiter.
- **Eigene Partikelsprache:** Jede Stufe behält ihre Sporen; ab Stufe II erscheinen häufiger Portalflimmern und Seelenfeuer, Stufe III ergänzt kristallartige Endstab-Funken. Alle Effekte teilen weiter ein festes Partikelbudget.
- **Qualitätssicherung:** Die QA-Vorschau zeigt alle drei Bodentexturen direkt nebeneinander. Regressionstests prüfen Blockstate-Modellzuordnung, deckende 16×16-Texturen, Pixelunterschiede, Lichtstufen, Partikellogik und Release-Version.

Automatische Prüfungen ersetzen keinen manuellen Sichttest im Minecraft-Client.

"""
if heading not in readme:
    marker = "## Version 1.26.0 — Mutagen-Kontrollstation"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.26.0 release notes to preserve release history")
    readme = readme[:idx] + section + readme[idx:]
readme_path.write_text(readme, encoding="utf-8")
print("Mutagen field tier signatures, light levels, particle effects, and 1.27.0 release notes generated.")
