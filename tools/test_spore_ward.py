#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
from PIL import Image
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]

def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Spore Ward regression: " + message)

blocks = read("src/main/java/de/sporenwerk/registry/ModBlocks.java")
require("SPORENABWEHR" in blocks and 'register("sporenabwehr"' in blocks, "ward must be registered")
ward = read("src/main/java/de/sporenwerk/block/SporeWardBlock.java")
for token in ("BlockStateProperties.POWERED", "level.hasNeighborSignal(pos)",
              "REFRESH_TICKS = 10", "HORIZONTAL_RADIUS = 8", "VERTICAL_RADIUS = 3",
              "getEntitiesOfClass(DaemmerlingEntity.class, area)",
              'putLong("SporenwerkWardRepelledUntil", repelUntil)',
              "level.scheduleTick(pos, this, REFRESH_TICKS)"):
    require(token in ward, "ward behavior missing " + token)
entity = read("src/main/java/de/sporenwerk/entity/DaemmerlingEntity.java")
for token in ("isRepelledBySporeWard()", 'getLong("SporenwerkWardRepelledUntil")',
              "new BloomScentGoal(this)", "new CropThreatGoal(this)"):
    require(token in entity, "Dämmerling counterplay missing " + token)
require("!mob.isRepelledBySporeWard()" in entity, "ward must stop ongoing mob goals, not only block new starts")

recipe = json.loads(read("src/main/resources/data/sporenwerk/recipes/sporenabwehr.json"))
require(recipe["result"]["item"] == "sporenwerk:sporenabwehr", "recipe must create the ward")
for ingredient in ("minecraft:iron_ingot", "minecraft:redstone", "sporenwerk:sporenresistenter_block",
                   "sporenwerk:filtermoos", "sporenwerk:mutagene_sporen"):
    require(any(x.get("item") == ingredient for x in recipe["key"].values()), "ward recipe missing " + ingredient)
state = json.loads(read("src/main/resources/assets/sporenwerk/blockstates/sporenabwehr.json"))
require(state["variants"]["powered=false"]["model"] == "sporenwerk:block/sporenabwehr"
        and state["variants"]["powered=true"]["model"] == "sporenwerk:block/sporenabwehr_active",
        "powered state must switch to a distinct model")
for filename in ("sporenabwehr.png", "sporenabwehr_active.png"):
    with Image.open(root / "src/main/resources/assets/sporenwerk/textures/block" / filename) as im:
        require(im.size == (16, 16), filename + " must be 16x16")
        require(all(px[3] == 255 for px in im.convert("RGBA").getdata()),
                filename + " must be opaque for a cube face")
for locale in ("de_de.json", "en_us.json"):
    data = json.loads(read("src/main/resources/assets/sporenwerk/lang/" + locale))
    for key in ("block.sporenwerk.sporenabwehr", "item.sporenwerk.sporenabwehr",
                "tooltip.sporenwerk.sporenabwehr.1", "tooltip.sporenwerk.sporenabwehr.2"):
        require(bool(data.get(key, "").strip()), locale + " missing " + key)
require("Version 1.17.0" in read("README.md"), "release notes missing 1.17.0")
require(re.search(r"version\s*=\s*['\"]1\.17\.0['\"]", read("build.gradle")) is not None,
        "artifact version must be 1.17.0")
print("Redstone Spore Ward, powered visual state, bounded repel pulse, recipe and Dämmerling AI checks passed.")
