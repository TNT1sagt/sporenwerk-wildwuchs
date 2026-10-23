#!/usr/bin/env python3
"""Close the automated farming -> residue -> biomass/compost loop without item spam."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve()
be_path = ROOT / "src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java"
s = be_path.read_text(encoding="utf-8")

old = """            ItemStack output = new ItemStack(produce, amount);
            if (!canFitOutput(output)) { progress = 0; return; }
            if (!consumePower(20)) { progress = 0; return; }
            if (!insertOutput(output)) { progress = 0; return; }"""
new = """            ItemStack output = new ItemStack(produce, amount);
            // The automated collector mirrors the 35% mature-crop by-product chance from
            // block loot. Reserve space for both outputs before consuming power, seeds or crops.
            boolean yieldsResidue = level.random.nextFloat() < 0.35F;
            ItemStack residue = yieldsResidue
                    ? new ItemStack(ModItems.PFLANZENRESTE.get())
                    : ItemStack.EMPTY;
            if (!canFitOutputs(output, residue)) { progress = 0; return; }
            if (!consumePower(20)) { progress = 0; return; }
            if (!insertOutputs(output, residue)) { progress = 0; return; }"""
if new not in s:
    if old not in s:
        raise SystemExit("Could not locate the field-collector output transaction")
    s = s.replace(old, new, 1)

if "private boolean canFitOutputs(ItemStack... incomingStacks)" not in s:
    marker = "    private boolean canFitOutput(ItemStack incoming) {"
    helper = """    /**
     * Simulates a complete multi-item output transaction against the eight-slot output
     * buffer. This prevents an extra residue item from making a successful crop harvest
     * partially fail after the seed is consumed or the crop state is changed.
     */
    private boolean canFitOutputs(ItemStack... incomingStacks) {
        ItemStack[] preview = new ItemStack[inventory.getSlots() - 4];
        for (int i = 0; i < preview.length; i++) {
            preview[i] = inventory.getStackInSlot(i + 4).copy();
        }

        for (ItemStack incoming : incomingStacks) {
            if (incoming == null || incoming.isEmpty()) continue;
            int remaining = incoming.getCount();
            for (int i = 0; i < preview.length && remaining > 0; i++) {
                ItemStack current = preview[i];
                if (current.isEmpty()) {
                    int count = Math.min(remaining, incoming.getMaxStackSize());
                    preview[i] = incoming.copyWithCount(count);
                    remaining -= count;
                } else if (ItemStack.isSameItemSameTags(current, incoming)
                        && current.getCount() < current.getMaxStackSize()) {
                    int count = Math.min(remaining, current.getMaxStackSize() - current.getCount());
                    current.grow(count);
                    remaining -= count;
                }
            }
            if (remaining > 0) return false;
        }
        return true;
    }

    private boolean insertOutputs(ItemStack... incomingStacks) {
        if (!canFitOutputs(incomingStacks)) return false;
        for (ItemStack incoming : incomingStacks) {
            if (incoming != null && !incoming.isEmpty() && !insertOutput(incoming)) return false;
        }
        return true;
    }

"""
    if marker not in s:
        raise SystemExit("Could not locate output-buffer helper insertion point")
    s = s.replace(marker, helper + marker, 1)

be_path.write_text(s, encoding="utf-8")

# Regression test verifies both manual loot and automated collector share the by-product rate.
test = r'''#!/usr/bin/env python3
from pathlib import Path
import json, sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
res = root / "src/main/resources"
be = (root / "src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java").read_text(encoding="utf-8")

def require(ok, message):
    if not ok:
        raise SystemExit("Automated farming loop regression: " + message)

require("boolean yieldsResidue = level.random.nextFloat() < 0.35F;" in be,
        "the field collector must produce residue with the same 35% chance as crop loot")
require("canFitOutputs(output, residue)" in be and "insertOutputs(output, residue)" in be,
        "the collector must preflight and atomically buffer produce plus residue")
require("private boolean canFitOutputs(ItemStack... incomingStacks)" in be,
        "output preflight must account for both output types")
require("addFreshEntity" not in be and "popResource" not in be,
        "automation must use internal stacks instead of spawning loose item entities")
for crop in ("faserrohr", "bernsteinkappe", "rotwurzel", "filtermoos"):
    loot = json.loads((res / f"data/sporenwerk/loot_tables/blocks/{crop}.json").read_text(encoding="utf-8"))
    residue_pools = [
        pool for pool in loot.get("pools", [])
        if any(entry.get("name") == "sporenwerk:pflanzenreste" for entry in pool.get("entries", []))
    ]
    require(residue_pools, crop + " must produce plant residue when mature")
    require(any(any(cond.get("condition") == "minecraft:random_chance" and cond.get("chance") == 0.35
                    for cond in pool.get("conditions", [])) for pool in residue_pools),
            crop + " residue probability must remain 35%")
print("Automated crop/residue buffer transaction checks passed.")
'''
(ROOT / "tools/test_machine_farming_loop.py").write_text(test, encoding="utf-8")

# Version and player-facing notes.
build = ROOT / "build.gradle"
text = build.read_text(encoding="utf-8")
text = re.sub(r"version = '[^']+'", "version = '1.2.1'", text, count=1)
build.write_text(text, encoding="utf-8")

readme = ROOT / "README.md"
doc = readme.read_text(encoding="utf-8")
doc = re.sub(r"sporenwerk-[0-9]+\.[0-9]+\.[0-9]+\.jar", "sporenwerk-1.2.1.jar", doc)
doc += """

## 1.2.1 — automated crop-waste loop
The field collector now mirrors the mature-crop 35% plant-residue by-product chance. It preflights space for both the harvest and residue before consuming FE, seeds, or changing crop state, then stores both results in the internal output buffer. This keeps automated farms connected to the Myzelkompost chain without spawning loose item entities.
"""
readme.write_text(doc, encoding="utf-8")
print("Installed automated crop-residue output transaction and regression checks.")
