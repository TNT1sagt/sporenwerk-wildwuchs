#!/usr/bin/env python3
"""Add active-field strength tiers and crop-specific mutation phenotypes."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")

def replace_once(path, old, new, label):
    p = ROOT / path
    source = p.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Mutagen phenotype patch cannot locate {label} in {path}")
    p.write_text(source.replace(old, new, 1), encoding="utf-8")

def method_end(source, signature):
    start = source.find(signature)
    if start < 0:
        raise SystemExit(f"Cannot locate Java method: {signature}")
    opening = source.find("{", start + len(signature))
    if opening < 0:
        raise SystemExit(f"Cannot locate method body: {signature}")
    depth = 0
    for i in range(opening, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise SystemExit(f"Unclosed method body: {signature}")

# Active saved sources determine the strongest tier overlapping a position.
nodes_path = "src/main/java/de/sporenwerk/infection/MutationNodeData.java"
nodes = read(nodes_path)
strength_signature = "public int getFieldStrengthAt(BlockPos target, int radius, int halfHeight)"
if strength_signature not in nodes:
    anchor = "public boolean hasActiveFieldAt(BlockPos target, int radius, int halfHeight)"
    end = method_end(nodes, anchor)
    strength_method = """

    public int getFieldStrengthAt(BlockPos target, int radius, int halfHeight) {
        int best = 0;
        for (Map.Entry<Long, Boolean> entry : nodes.entrySet()) {
            if (!entry.getValue()) continue;
            BlockPos origin = BlockPos.of(entry.getKey());
            long dx = (long) target.getX() - origin.getX();
            long dz = (long) target.getZ() - origin.getZ();
            long horizontalSquared = dx * dx + dz * dz;
            int vertical = Math.abs(target.getY() - origin.getY());
            if (horizontalSquared > (long) radius * radius || vertical > halfHeight) continue;

            int strength = horizontalSquared <= 4L && vertical <= 1 ? 3
                    : horizontalSquared <= 25L && vertical <= 2 ? 2 : 1;
            best = Math.max(best, strength);
            if (best == 3) return 3;
        }
        return best;
    }"""
    nodes_path_full = ROOT / nodes_path
    nodes_path_full.write_text(nodes[:end] + strength_method + nodes[end:], encoding="utf-8")

# Shared intensity query respects inactive sources and sterilizing anchors.
field_path = "src/main/java/de/sporenwerk/infection/MutationField.java"
field = read(field_path)
if "public static int mutagenStrengthAt(Level level, BlockPos target)" not in field:
    anchor = "    public static boolean insideBounds(BlockPos origin, BlockPos target) {"
    method = """    public static int mutagenStrengthAt(Level level, BlockPos target) {
        if (!(level instanceof ServerLevel serverLevel) || hasAnchor(serverLevel, target)) return 0;
        return MutationNodeData.get(serverLevel).getFieldStrengthAt(target, RADIUS, INFECTION_HALF_HEIGHT);
    }

"""
    if anchor not in field:
        raise SystemExit("Cannot locate MutationField bounds method for strength query")
    field_path_full = ROOT / field_path
    field_path_full.write_text(field.replace(anchor, method + anchor, 1), encoding="utf-8")
    field = read(field_path)

# Existing callers now share exactly the same active/inactive/healed-field definition.
old_active = """    public static boolean isInActiveMutagenField(Level level, BlockPos target) {
        if (!(level instanceof ServerLevel serverLevel)) return false;
        return MutationNodeData.get(serverLevel).hasActiveFieldAt(target, RADIUS, INFECTION_HALF_HEIGHT)
                && !hasAnchor(serverLevel, target);
    }"""
new_active = """    public static boolean isInActiveMutagenField(Level level, BlockPos target) {
        return mutagenStrengthAt(level, target) > 0;
    }"""
replace_once(field_path, old_active, new_active, "shared active-field predicate")

# Plant growth accelerates with local strength, but not inside an anchor's sterile zone.
field = read(field_path)
growth_old = "            if (random.nextFloat() < 0.20F) level.setBlock(pos, crop.getStateForAge(crop.getAge(state) + 1), 2);"
growth_new = """            int strength = mutagenStrengthAt(level, pos);
            float growthChance = strength >= 3 ? 0.40F : strength == 2 ? 0.30F : 0.20F;
            if (strength > 0 && random.nextFloat() < growthChance) {
                level.setBlock(pos, crop.getStateForAge(crop.getAge(state) + 1), 2);
            }"""
replace_once(field_path, growth_old, growth_new, "mutagen-strength growth chance")

# Manual harvesting has four distinct, source-driven phenotypes:
# fiber cane gains deterministic yield; redroot can form extra tubers; amber caps can overproduce;
# filter moss sheds extra plant residue. The spore rate scales with field strength.
crop_path = "src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java"
crop = read(crop_path)
for imp in ("import de.sporenwerk.registry.ModBlocks;",):
    if imp not in crop:
        package_line = "package de.sporenwerk.block.crop;"
        if package_line not in crop:
            raise SystemExit("Cannot locate crop package declaration")
        crop = crop.replace(package_line, package_line + "\n\n" + imp, 1)
crop_path_full = ROOT / crop_path
crop_path_full.write_text(crop, encoding="utf-8")
drop_line = "Block.popResource(level, pos, new ItemStack(produceItem(), produceCount));"
mutated_drop = """int mutagenStrength = MutationField.mutagenStrengthAt(level, pos);
        int mutationBonus = 0;
        if (mutagenStrength >= 2) {
            if (this == ModBlocks.FASERROHR.get()) {
                mutationBonus = mutagenStrength - 1;
            } else if (this == ModBlocks.ROTWURZEL.get()
                    && level.random.nextFloat() < (mutagenStrength >= 3 ? 0.45F : 0.20F)) {
                mutationBonus++;
            } else if (this == ModBlocks.BERNSTEINKAPPE.get() && mutagenStrength >= 3
                    && level.random.nextFloat() < 0.25F) {
                mutationBonus++;
            }
        }
        Block.popResource(level, pos, new ItemStack(produceItem(), produceCount() + mutationBonus));
        if (this == ModBlocks.FILTERMOOS.get() && mutagenStrength >= 2
                && level.random.nextFloat() < (mutagenStrength >= 3 ? 0.55F : 0.30F)) {
            Block.popResource(level, pos, new ItemStack(ModItems.PFLANZENRESTE.get()));
        }"""
crop = read(crop_path)
if "int mutagenStrength = MutationField.mutagenStrengthAt(level, pos);" not in crop:
    if drop_line not in crop:
        raise SystemExit("Cannot locate manual crop harvest output")
    crop = crop.replace(drop_line, mutated_drop, 1)
spore_old = """if (MutationField.isInActiveMutagenField(level, pos) && level.random.nextFloat() < 0.22F) {"""
spore_new = """if (mutagenStrength > 0 && level.random.nextFloat() <
                (mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F)) {"""
replace_once(crop_path, spore_old, spore_new, "strength-dependent mutagenic spore chance")

# The automated collector applies the same phenotype rules. It preflights these adjusted stacks
# alongside residue and mutagenic spores before spending energy or consuming a crop.
be_path = "src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java"
be = read(be_path)
output_anchor = "            ItemStack output = new ItemStack(produce, amount);"
output_patch = """            int mutagenStrength = MutationField.mutagenStrengthAt(level, target);
            var mutationCropState = level.getBlockState(target);
            if (mutagenStrength >= 2) {
                if (mutationCropState.is(de.sporenwerk.registry.ModBlocks.FASERROHR.get())) {
                    amount += mutagenStrength - 1;
                } else if (mutationCropState.is(de.sporenwerk.registry.ModBlocks.ROTWURZEL.get())
                        && level.random.nextFloat() < (mutagenStrength >= 3 ? 0.45F : 0.20F)) {
                    amount++;
                } else if (mutationCropState.is(de.sporenwerk.registry.ModBlocks.BERNSTEINKAPPE.get())
                        && mutagenStrength >= 3 && level.random.nextFloat() < 0.25F) {
                    amount++;
                }
            }
            ItemStack output = new ItemStack(produce, amount);"""
if "var mutationCropState = level.getBlockState(target);" not in be:
    if output_anchor not in be:
        raise SystemExit("Cannot locate field-collector stack creation")
    be = be.replace(output_anchor, output_patch, 1)
residue_old = "            boolean yieldsResidue = level.random.nextFloat() < 0.35F;"
residue_new = """            boolean filterMossPhenotype = mutationCropState.is(
                    de.sporenwerk.registry.ModBlocks.FILTERMOOS.get()) && mutagenStrength >= 2;
            float residueChance = filterMossPhenotype
                    ? (mutagenStrength >= 3 ? 0.70F : 0.55F) : 0.35F;
            boolean yieldsResidue = level.random.nextFloat() < residueChance;"""
if residue_old in be:
    be = be.replace(residue_old, residue_new, 1)
elif residue_new not in be:
    raise SystemExit("Cannot locate collector residue chance")
spore_old_machine = """            boolean yieldsMutagenSpores = MutationField.isInActiveMutagenField(level, target)
                    && level.random.nextFloat() < 0.22F;"""
spore_new_machine = """            boolean yieldsMutagenSpores = mutagenStrength > 0
                    && level.random.nextFloat() <
                    (mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F);"""
if spore_old_machine in be:
    be = be.replace(spore_old_machine, spore_new_machine, 1)
elif spore_new_machine not in be:
    raise SystemExit("Cannot locate collector mutagen-spore chance")
(ROOT / be_path).write_text(be, encoding="utf-8")

# The older collector test asserted a literal 35% value at the call site. Preserve its
# baseline contract while allowing Filtermoos to scale residue odds with field strength.
machine_test_path = ROOT / "tools/test_machine_farming_loop.py"
if machine_test_path.is_file():
    machine_test = machine_test_path.read_text(encoding="utf-8")
    old_assertion = """require("boolean yieldsResidue = level.random.nextFloat() < 0.35F;" in be,
        "the field collector must produce residue with the same 35% chance as crop loot")"""
    new_assertion = """require("float residueChance = " in be
        and "boolean yieldsResidue = level.random.nextFloat() < residueChance;" in be
        and "0.35F" in be,
        "the collector must preserve the 35% baseline and scale Filtermoos residue by phenotype")"""
    if old_assertion in machine_test:
        machine_test = machine_test.replace(old_assertion, new_assertion, 1)
    elif new_assertion not in machine_test:
        raise SystemExit("Cannot update farming-loop regression for the phenotype-aware residue chance")
    old_field_assertion = """require("MutationField.isInActiveMutagenField(level, target)" in be,
        "automated fields must award the same controlled mutagen by-product")"""
    new_field_assertion = """require("MutationField.mutagenStrengthAt(level, target)" in be
        and "mutagenStrength > 0" in be,
        "automated fields must use the saved-source intensity and healing-zone rules")"""
    if old_field_assertion in machine_test:
        machine_test = machine_test.replace(old_field_assertion, new_field_assertion, 1)
    elif new_field_assertion not in machine_test:
        raise SystemExit("Cannot update collector regression for the shared field-strength query")
    machine_test_path.write_text(machine_test, encoding="utf-8")

# Source-level regression suite verifies tier boundaries, sterile suppression, crop traits and
# the collector's atomic output reservation, so the patch fails closed if upstream code drifts.
write("tools/test_mutagen_phenotypes.py", r'''
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Mutagen phenotype regression: " + message)
nodes = read("src/main/java/de/sporenwerk/infection/MutationNodeData.java")
field = read("src/main/java/de/sporenwerk/infection/MutationField.java")
crop = read("src/main/java/de/sporenwerk/block/crop/AbstractSporeCropBlock.java")
machine = read("src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java")
require("getFieldStrengthAt(BlockPos target, int radius, int halfHeight)" in nodes,
        "strength must come from persisted active sources")
require("horizontalSquared <= 4L && vertical <= 1 ? 3" in nodes
        and "horizontalSquared <= 25L && vertical <= 2 ? 2 : 1" in nodes,
        "three field tiers must have deterministic spatial boundaries")
require("hasAnchor(serverLevel, target)) return 0" in field
        and "return mutagenStrengthAt(level, target) > 0" in field,
        "anchors and stopped sources must suppress mutation tiers")
require("strength >= 3 ? 0.40F : strength == 2 ? 0.30F : 0.20F" in field,
        "crop growth acceleration must scale with field intensity")
for token in ("ModBlocks.FASERROHR.get()", "ModBlocks.ROTWURZEL.get()",
              "ModBlocks.BERNSTEINKAPPE.get()", "ModBlocks.FILTERMOOS.get()"):
    require(token in crop, "manual phenotype missing for " + token)
require("produceCount() + mutationBonus" in crop
        and "ModItems.PFLANZENRESTE.get()" in crop,
        "manual crop yields must differ by phenotype")
require("mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F" in crop,
        "manual spore rate must scale with field strength")
require("var mutationCropState = level.getBlockState(target);" in machine
        and "amount += mutagenStrength - 1;" in machine,
        "automated collector must apply crop-specific yield bonuses")
require("canFitOutputs(output, residue, mutagenSpores)" in machine
        and "insertOutputs(output, residue, mutagenSpores)" in machine,
        "phenotype items must stay in the atomic output-buffer transaction")
require("0.70F : 0.55F) : 0.35F" in machine,
        "filter-moss phenotype must improve automated residue production")
require("mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F" in machine,
        "automated mutagen spore output must use the same tier odds as manual harvest")
print("Active field strength tiers, crop-specific phenotypes, anchor suppression, and collector transactions passed.")
''')

# Bump the actual mod version after all earlier patch scripts have run.
build_path = ROOT / "build.gradle"
build = build_path.read_text(encoding="utf-8")
build = re.sub(r"version = '[^']+'", "version = '1.9.0'", build, count=1)
build_path.write_text(build, encoding="utf-8")
readme = ROOT / "README.md"
doc = readme.read_text(encoding="utf-8")
doc += """

## 1.9.0 — Mutagen field strength and crop phenotypes
- Mutagen fields now have three spatial strength tiers, based on distance and vertical separation from an active saved source. Sterile anchors and deactivated fields grant no mutation tier.
- Stronger fields accelerate Sporenwerk crop growth more often. Harvest traits are crop-specific: Faserrohr gains guaranteed fiber yield, Rotwurzel can form extra roots, Bernsteinkappe can overproduce at peak strength, and Filtermoos yields extra plant residue.
- Mutagenic spore odds scale with local strength (12%, 22%, 35%). Manual harvesting and the automated Field Collector share the crop-yield rules; the collector still reserves every possible output before it spends energy or consumes a crop.
- Regression checks cover spatial tier boundaries, anchor suppression, manual and automated phenotypes, and atomic machine output.
"""
readme.write_text(doc, encoding="utf-8")
print("Installed Sporenwerk 1.9.0 mutagen field strength tiers and crop phenotypes.")
