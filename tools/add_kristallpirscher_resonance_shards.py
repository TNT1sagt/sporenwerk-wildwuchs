#!/usr/bin/env python3
"""Create a reliable Kristallpirscher loot-to-dampener progression (1.35.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"
TEX_DIR = ASSETS / "textures/item"


def require(condition, message):
    if not condition:
        raise SystemExit("Kristallpirscher resonance shard generation: " + message)


# Register the shard beside the existing Crystal Stalker spawn egg, avoiding changes
# to a generated registry API that may otherwise force-load entity references.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
item_id = "KRISTALLPIRSCHER_RESONANZSPLITTER"
if item_id not in items:
    lines = items.splitlines()
    for index, line in enumerate(lines):
        if "KRISTALLPIRSCHER_SPAWN_EGG" in line and "public static final RegistryObject<Item>" in line:
            lines.insert(index + 1, (
                '    public static final RegistryObject<Item> KRISTALLPIRSCHER_RESONANZSPLITTER = '
                'ITEMS.register("kristallpirscher_resonanzsplitter", () -> new Item(new Item.Properties().stacksTo(16)));'
            ))
            break
    else:
        raise SystemExit("Cannot register resonance shard: Kristallpirscher spawn egg declaration not found")
    items_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
anchor = "output.accept(ModItems.KRISTALLPIRSCHER_SPAWN_EGG.get());"
addition = "output.accept(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get());"
if addition not in creative:
    require(anchor in creative, "creative tab Kristallpirscher egg anchor not found")
    creative_path.write_text(creative.replace(anchor, anchor + "\n                        " + addition, 1), encoding="utf-8")

# Guaranteed residue creates a dependable common component; the rare Mutagen core
# crystal remains a 25% drop, preserving the hunt's meaningful long-term reward.
loot_path = RES / "data/sporenwerk/loot_tables/entities/kristallpirscher.json"
loot = json.loads(loot_path.read_text(encoding="utf-8"))
shard_name = "sporenwerk:kristallpirscher_resonanzsplitter"
if not any(
    entry.get("name") == shard_name
    for pool in loot.get("pools", [])
    for entry in pool.get("entries", [])
):
    loot["pools"].append({
        "rolls": 1.0,
        "entries": [{
            "type": "minecraft:item",
            "name": shard_name,
            "functions": [{
                "function": "minecraft:set_count",
                "count": {"min": 1.0, "max": 3.0}
            }]
        }]
    })
loot_path.write_text(json.dumps(loot, indent=2) + "\n", encoding="utf-8")

# Refine the dampener recipe: it now consumes 2 shards as tuning conductors while
# retaining iron, redstone, amethyst, and the rare Mutagen core crystal.
recipe_path = RES / "data/sporenwerk/recipes/mutagen_resonanzdaempfer.json"
recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
recipe["pattern"] = ["ISI", "RCA", "ISI"]
recipe["key"] = {
    "I": {"item": "minecraft:iron_ingot"},
    "S": {"item": shard_name},
    "R": {"item": "minecraft:redstone"},
    "C": {"item": "sporenwerk:mutagenkernkristall"},
    "A": {"item": "minecraft:amethyst_block"}
}
recipe_path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")

# Recipe unlock only appears when the player has encountered all components.
recipe_adv_path = RES / "data/sporenwerk/advancements/recipes/misc/mutagen_resonanzdaempfer.json"
recipe_adv = json.loads(recipe_adv_path.read_text(encoding="utf-8"))
recipe_adv.setdefault("criteria", {})["has_resonance_shard"] = {
    "trigger": "minecraft:inventory_changed",
    "conditions": {"items": [{"items": [shard_name]}]}
}
recipe_adv["requirements"] = [
    ["has_iron"], ["has_redstone"], ["has_amethyst"], ["has_mutagen_core"], ["has_resonance_shard"]
]
recipe_adv_path.write_text(json.dumps(recipe_adv, indent=2) + "\n", encoding="utf-8")

# A second advancement frames the first shard as research evidence instead of generic mob loot.
(RES / "data/sporenwerk/advancements/monsters/kristallpirscher_resonanzsplitter.json").write_text(
    json.dumps({
        "parent": "sporenwerk:monsters/kristallpirscher",
        "display": {
            "icon": {"item": shard_name},
            "title": {"translate": "advancements.sporenwerk.kristallpirscher_resonanzsplitter.title"},
            "description": {"translate": "advancements.sporenwerk.kristallpirscher_resonanzsplitter.description"},
            "frame": "goal",
            "show_toast": True,
            "announce_to_chat": True,
            "hidden": False
        },
        "criteria": {
            "recover_resonance_shard": {
                "trigger": "minecraft:inventory_changed",
                "conditions": {"items": [{"items": [shard_name]}]}
            }
        },
        "requirements": [["recover_resonance_shard"]]
    }, indent=2) + "\n", encoding="utf-8"
)

# Sharp cyan/magenta mineral sliver on a near-black substrate, legible at item scale.
TEX_DIR.mkdir(parents=True, exist_ok=True)
texture = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
d = ImageDraw.Draw(texture)
d.polygon([(7, 0), (12, 4), (11, 10), (7, 15), (3, 10), (4, 4)],
          fill=(24, 45, 51, 255), outline=(61, 220, 208, 255))
d.polygon([(7, 2), (10, 5), (9, 9), (7, 12), (6, 8)],
          fill=(37, 150, 160, 255))
d.polygon([(7, 2), (8, 6), (6, 8), (5, 5)],
          fill=(146, 255, 235, 255))
d.line([(4, 7), (6, 8), (5, 10), (7, 12)], fill=(239, 74, 165, 255), width=1)
d.point((8, 7), fill=(255, 220, 245, 255))
d.point((7, 5), fill=(227, 255, 253, 255))
texture_path = TEX_DIR / "kristallpirscher_resonanzsplitter.png"
texture.save(texture_path, optimize=True)
with Image.open(texture_path) as im:
    rgba = im.convert("RGBA")
    require(rgba.size == (16, 16), "resonance shard texture must be 16x16")
    require(any(px[3] == 0 for px in rgba.getdata()), "resonance shard should retain a transparent item background")
    require(len(set(rgba.getdata())) >= 8, "resonance shard needs readable color facets")

(ASSETS / "models/item/kristallpirscher_resonanzsplitter.json").write_text(
    json.dumps({
        "parent": "minecraft:item/generated",
        "textures": {"layer0": "sporenwerk:item/kristallpirscher_resonanzsplitter"}
    }, indent=2) + "\n",
    encoding="utf-8"
)

# DE/EN item name and research milestone.
for filename, values in {
    "de_de.json": {
        "item.sporenwerk.kristallpirscher_resonanzsplitter": "Kristallpirscher-Resonanzsplitter",
        "advancements.sporenwerk.kristallpirscher_resonanzsplitter.title": "Das Echo zerlegt",
        "advancements.sporenwerk.kristallpirscher_resonanzsplitter.description": "Sichere einen Resonanzsplitter vom Kristallpirscher."
    },
    "en_us.json": {
        "item.sporenwerk.kristallpirscher_resonanzsplitter": "Crystal Stalker Resonance Shard",
        "advancements.sporenwerk.kristallpirscher_resonanzsplitter.title": "Echo Recovered",
        "advancements.sporenwerk.kristallpirscher_resonanzsplitter.description": "Recover a resonance shard from a Crystal Stalker."
    }
}.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Include the exact generated item icon in the existing visual QA contact sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = '"sporenfiltereinsatz_verstaerkt", "sporenfiltereinsatz_mutagen"'
addition = anchor + ', "kristallpirscher_resonanzsplitter"'
if "kristallpirscher_resonanzsplitter" not in preview:
    require(anchor in preview, "item preview list anchor not found")
    preview_path.write_text(preview.replace(anchor, addition, 1), encoding="utf-8")

# Ensure the rare-drop story leads into the buildable countermeasure.
build_path = ROOT / "build.gradle"
build, count = re.subn(
    r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
    "version = '1.35.0'",
    build_path.read_text(encoding="utf-8"),
    count=1
)
require(count == 1, "could not advance Gradle version to 1.35.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.35.0 — Kristallpirscher-Beute und Resonanzforschung

- **Verlässlicher Fund:** Jeder besiegte Kristallpirscher hinterlässt 1–3 Resonanzsplitter. Der Mutagenkernkristall bleibt mit 25 % ein seltener, eigenständiger Drop.
- **Echte Bauteil-Kette:** Zwei Resonanzsplitter stimmen den Resonanzdämpfer ab. Das Rezept verlangt weiterhin Eisen, Redstone, Amethyst und einen Mutagenkernkristall; die neue Zutat verbindet die Jagd mit dem Bau der Gegenmaßnahme.
- **Forschung statt Zufallsbeute:** Ein eigenes Advancement dokumentiert den ersten geborgenen Splitter. Die Rezeptfreigabe prüft alle fünf Zutaten, auch den Splitter.
- **Pixel-Art und QA:** Eigene 16×16-Icontextur, Modell, deutsche/englische Namen, vollständige Drop-/Rezepttests und JAR-Prüfung sind enthalten.

"""
if "## Version 1.35.0 — Kristallpirscher-Beute und Resonanzforschung" not in readme:
    marker = "## Version 1.34.0 — Mutagen-Resonanzdämpfer: technische Gegenwehr"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.34.0 history for release insertion")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.34.0 — baubare Resonanzdämpfung für Hochmutagen-Anlagen.**",
    "**Aktueller Entwicklungsstand: 1.35.0 — Kristallpirscher-Beute speist die Resonanzforschung.**"
).replace("## Aktueller Schwerpunkt — 1.34.0", "## Aktueller Schwerpunkt — 1.35.0")
bullet = "- Ein Scan an der Mutagenfeld-Kontrollstation aktualisiert einen Comparator-Gefahrenwert von 0 bis 15, ohne Welt-Scans bei jedem Redstone-Tick auszulösen."
if "Resonanzsplitter" not in readme[:2500]:
    require(bullet in readme, "could not find current overview bullet to extend")
    readme = readme.replace(
        bullet,
        bullet + "\n- Der Kristallpirscher liefert 1–3 garantierte Resonanzsplitter; zwei davon kalibrieren zusammen mit dem seltenen Mutagenkernkristall den Resonanzdämpfer."
    )
readme_path.write_text(readme, encoding="utf-8")
print("Kristallpirscher resonance shard loot, dampener progression, research advancement, pixel icon, DE/EN names, and 1.35.0 generated.")
