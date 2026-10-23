#!/usr/bin/env python3
"""Harden machine automation/energy contracts for Forge 47.x / MC 1.20.1."""
from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
be_path = root / "src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java"
s = be_path.read_text(encoding="utf-8")

old = "private final LazyOptional<IItemHandler> itemHandler = LazyOptional.of(() -> inventory);"
new = """private final LazyOptional<IItemHandler> itemHandler = LazyOptional.of(() -> new IItemHandler() {
        @Override public int getSlots() { return inventory.getSlots(); }

        @Override public ItemStack getStackInSlot(int slot) {
            return inventory.getStackInSlot(slot);
        }

        /** Automation may feed the four recipe inputs, but must never insert into output slots. */
        @Override public ItemStack insertItem(int slot, ItemStack stack, boolean simulate) {
            if (slot < 0 || slot >= 4) return stack;
            return inventory.insertItem(slot, stack, simulate);
        }

        /** Hoppers and pipes may extract finished output only, preserving input buffers. */
        @Override public ItemStack extractItem(int slot, int amount, boolean simulate) {
            if (slot < 4 || slot >= inventory.getSlots()) return ItemStack.EMPTY;
            return inventory.extractItem(slot, amount, simulate);
        }

        @Override public int getSlotLimit(int slot) {
            return slot < 0 || slot >= inventory.getSlots() ? 0 : inventory.getSlotLimit(slot);
        }

        @Override public boolean isItemValid(int slot, ItemStack stack) {
            return slot >= 0 && slot < 4 && inventory.isItemValid(slot, stack);
        }
    });"""
if old in s:
    s = s.replace(old, new, 1)
elif "Automation may feed the four recipe inputs" not in s:
    raise SystemExit("Could not find the current item-handler capability declaration")

# Explicitly separate internal extraction from the receive-only external Forge Energy endpoint.
# Match the anonymous EnergyStorage body by braces instead of assuming field order/format.
energy_pos = s.find("new EnergyStorage(")
if energy_pos < 0:
    raise SystemExit("Internal EnergyStorage initializer not found")
energy_open = s.find("{", energy_pos)
if energy_open < 0:
    raise SystemExit("Internal EnergyStorage body not found")
depth = 0
energy_close = -1
for index in range(energy_open, len(s)):
    if s[index] == "{":
        depth += 1
    elif s[index] == "}":
        depth -= 1
        if depth == 0:
            energy_close = index
            break
if energy_close < 0:
    raise SystemExit("Internal EnergyStorage body is unbalanced")
internal_energy = s[energy_pos:energy_close + 1]
if re.search(r"canExtract\s*\(\s*\)\s*\{\s*return false;\s*\}", internal_energy):
    internal_energy = re.sub(
        r"@Override\s+public boolean canExtract\s*\(\s*\)\s*\{\s*return false;\s*\}",
        "@Override public boolean canExtract() { return true; }",
        internal_energy,
        count=1,
    )
elif "canExtract() { return true; }" not in internal_energy:
    relative_open = energy_open - energy_pos
    internal_energy = internal_energy[:relative_open + 1] + "\n        @Override public boolean canExtract() { return true; }\n" + internal_energy[relative_open + 1:]
s = s[:energy_pos] + internal_energy + s[energy_close + 1:]

# The Forge capability exposed to cables is a separate read-only adapter.
cap_start = s.find("private final LazyOptional<IEnergyStorage> energyCapability")
if cap_start < 0:
    raise SystemExit("External Forge Energy capability declaration not found")
external_window = s[cap_start:cap_start + 2400]
if "extractEnergy(int maxExtract, boolean simulate) { return 0; }" not in external_window:
    raise SystemExit("External FE adapter is not receive-only")
if "canExtract() { return false; }" not in external_window:
    raise SystemExit("External FE adapter must refuse extraction")


be_path.write_text(s, encoding="utf-8")

# Large production worlds can exceed a vanilla container-data short. Split Feldwissen
# across three non-negative 15-bit fields so the skill-tree UI stays correct up to 2 billion.
skill_menu_path = root / "src/main/java/de/sporenwerk/client/menu/SkillTreeMenu.java"
if skill_menu_path.exists():
    sm = skill_menu_path.read_text(encoding="utf-8")
    replacements = [
        ("new SimpleContainerData(10)", "new SimpleContainerData(12)"),
        ("case 0 -> skills.knowledge();", "case 0 -> skills.knowledge() & 0x7FFF;"),
        ("case 9 -> (int) Math.min(32767, skills.crafts());\n                    default -> 0;",
         "case 9 -> (int) Math.min(32767, skills.crafts());\n                    case 10 -> (skills.knowledge() >>> 15) & 0x7FFF;\n                    case 11 -> (skills.knowledge() >>> 30) & 0x1;\n                    default -> 0;"),
        ("@Override public int getCount() { return 10; }", "@Override public int getCount() { return 12; }"),
        ("public int knowledge() { return data.get(0); }",
         "public int knowledge() { return (data.get(0) & 0x7FFF) | ((data.get(10) & 0x7FFF) << 15) | ((data.get(11) & 0x1) << 30); }"),
    ]
    for old_text, new_text in replacements:
        if new_text not in sm:
            if old_text not in sm:
                raise SystemExit("Could not apply large-Feldwissen sync fix: " + old_text)
            sm = sm.replace(old_text, new_text, 1)
    skill_menu_path.write_text(sm, encoding="utf-8")
else:
    raise SystemExit("SkillTreeMenu.java not found while applying Feldwissen sync fix")

# Update delivered version after machine/art patches.
build = root / "build.gradle"
bs = build.read_text(encoding="utf-8")
bs = re.sub(r"version = '[^']+'", "version = '1.1.8'", bs, count=1)
build.write_text(bs, encoding="utf-8")

readme = root / "README.md"
rs = readme.read_text(encoding="utf-8")
rs = rs.replace("1.1.6", "1.1.8").replace("1.1.7", "1.1.8").replace("V1.1.6", "V1.1.8").replace("V1.1.7", "V1.1.8")
rs += """

## 1.1.8 — production reliability and large-balance progression
The public Forge item capability accepts inserts only in input slots 0–3 and allows automated extraction only from output slots 4–11. The player GUI retains manual access. Internal FE storage can drain power while the external endpoint stays receive-only. The skill-tree screen also transports large Feldwissen values over multiple safe 15-bit fields instead of overflowing vanilla container data.
"""
readme.write_text(rs, encoding="utf-8")

# A lightweight source-level regression test runs on every build before ForgeGradle.
test_script = r'''#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
p = root / "src/main/java/de/sporenwerk/block/entity/MachineBlockEntity.java"
s = p.read_text(encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit("Machine/progression contract regression: " + message)

def anonymous_body(source, marker, constructor):
    field = source.find(marker)
    if field < 0:
        return None
    obj = source.find(constructor, field)
    if obj < 0:
        return None
    opening = source.find("{", obj)
    if opening < 0:
        return None
    depth = 0
    for i in range(opening, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[opening:i + 1]
    return None

require("new ItemStackHandler(12)" in s, "machine inventory must have 12 slots (4 input + 8 output)")
handler = anonymous_body(s, "private final LazyOptional<IItemHandler> itemHandler", "new IItemHandler()")
require(handler is not None, "automation handler must be a distinct adapter, not the raw player inventory")
require("slot < 4" in handler, "automation insertion must be restricted to input slots 0–3")
require("slot >= 4" in handler, "automation extraction must be restricted to output slots 4–11")
require("inventory.insertItem(slot, stack, simulate)" in handler, "valid input must be delegated to the recipe handler")
require("inventory.extractItem(slot, amount, simulate)" in handler, "output extraction must delegate to persistent inventory")

energy = anonymous_body(s, "new EnergyStorage(", "new EnergyStorage(")
external = anonymous_body(s, "private final LazyOptional<IEnergyStorage> energyCapability", "new IEnergyStorage()")
require(energy is not None and "canExtract() { return true; }" in energy, "internal FE storage must be drainable by processors")
require(external is not None, "external Forge Energy adapter must exist")
require("extractEnergy(int maxExtract, boolean simulate) { return 0; }" in external, "external cables must not extract energy")
require("canExtract() { return false; }" in external, "external Forge Energy endpoint must remain receive-only")
require("private boolean consumePower(int cost)" in s and "energyStorage.extractEnergy(cost, false)" in s,
        "machine production must consume internal FE when the optional power integration is active")
require("invalidateCaps()" in s and "itemHandler.invalidate()" in s and "energyCapability.invalidate()" in s,
        "optional capabilities must be invalidated")

skill_path = root / "src/main/java/de/sporenwerk/client/menu/SkillTreeMenu.java"
skill = skill_path.read_text(encoding="utf-8")
require("new SimpleContainerData(12)" in skill and "getCount() { return 12; }" in skill,
        "client/server data slots must include the two Feldwissen high words")
require("case 10 -> (skills.knowledge() >>> 15) & 0x7FFF;" in skill,
        "Feldwissen middle word must be synced without signed-short overflow")
require("case 11 -> (skills.knowledge() >>> 30) & 0x1;" in skill,
        "Feldwissen high bit must be synced")
require("((data.get(10) & 0x7FFF) << 15)" in skill and "((data.get(11) & 0x1) << 30)" in skill,
        "client must reconstruct large Feldwissen balances")
print("Machine/progression contract tests passed.")
'''

(root / "tools/test_machine_io_contract.py").write_text(test_script, encoding="utf-8")
print("Hardened machine IO and energy contracts; updated project to 1.1.7.")
