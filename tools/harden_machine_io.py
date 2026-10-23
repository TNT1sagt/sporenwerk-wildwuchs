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

# Explicitly separate internal extraction from the receive-only external Forge Energy capability.
energy_match = re.search(
    r"private final EnergyStorage energyStorage = new EnergyStorage\(.*?\)\s*\{.*?\n    \};",
    s,
    flags=re.DOTALL,
)
if energy_match is None:
    raise SystemExit("Internal EnergyStorage field could not be parsed")

internal_energy = energy_match.group(0)
if re.search(r"canExtract\s*\(\s*\)\s*\{\s*return false;\s*\}", internal_energy):
    internal_energy = re.sub(
        r"@Override\s+public boolean canExtract\s*\(\s*\)\s*\{\s*return false;\s*\}",
        "@Override public boolean canExtract() { return true; }",
        internal_energy,
        count=1,
    )
elif "canExtract() { return true; }" not in internal_energy:
    brace = internal_energy.find("{", internal_energy.find("new EnergyStorage"))
    if brace < 0:
        raise SystemExit("Could not locate internal EnergyStorage body")
    internal_energy = internal_energy[:brace + 1] + "\n        @Override public boolean canExtract() { return true; }\n" + internal_energy[brace + 1:]
s = s[:energy_match.start()] + internal_energy + s[energy_match.end():]

# Keep the external endpoint read-only; if a source snapshot resets it to a raw EnergyStorage
# wrapper, rebuild this field independently of the internal field's location.
external_match = re.search(
    r"private final LazyOptional<IEnergyStorage> energyCapability\s*=\s*LazyOptional\.of\(\(\) -> .*?\n    \}\);",
    s,
    flags=re.DOTALL,
)
if external_match is None:
    raise SystemExit("External Forge Energy capability could not be parsed")
external = external_match.group(0)
if "extractEnergy(int maxExtract, boolean simulate) { return 0; }" not in external:
    safe_external = """private final LazyOptional<IEnergyStorage> energyCapability = LazyOptional.of(() -> new IEnergyStorage() {
        @Override public int receiveEnergy(int maxReceive, boolean simulate) {
            return energyStorage.receiveEnergy(maxReceive, simulate);
        }
        @Override public int extractEnergy(int maxExtract, boolean simulate) { return 0; }
        @Override public int getEnergyStored() { return energyStorage.getEnergyStored(); }
        @Override public int getMaxEnergyStored() { return energyStorage.getMaxEnergyStored(); }
        @Override public boolean canExtract() { return false; }
        @Override public boolean canReceive() { return true; }
    });"""
    s = s[:external_match.start()] + safe_external + s[external_match.end():]
elif "canExtract() { return false; }" not in external:
    raise SystemExit("External FE endpoint does not declare receive-only behavior")

be_path.write_text(s, encoding="utf-8")

# Update delivered version after the art patch has set 1.1.6.
build = root / "build.gradle"
bs = build.read_text(encoding="utf-8")
bs = re.sub(r"version = '[^']+'", "version = '1.1.7'", bs, count=1)
build.write_text(bs, encoding="utf-8")

readme = root / "README.md"
rs = readme.read_text(encoding="utf-8")
rs = rs.replace("1.1.6", "1.1.7").replace("V1.1.6", "V1.1.7")
rs += """

## 1.1.7 — machine automation safety
The public Forge item capability now accepts items only in input slots 0–3 and allows automated extraction only from output slots 4–11. The player GUI still allows intentional manual input/output access. Internal FE storage can drain power for processing; the external Forge Energy capability remains receive-only. The CI contract test checks these boundaries.
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
        raise SystemExit("Machine contract regression: " + message)

require("new ItemStackHandler(12)" in s, "machine inventory must have 12 slots (4 input + 8 output)")
start = s.find("private final LazyOptional<IItemHandler> itemHandler")
end = s.find("private final EnergyStorage energyStorage", start)
require(start >= 0 and end > start, "automation handler declaration must be present before energy storage")
handler = s[start:end]
require("slot < 4" in handler, "automation insertion must be restricted to slots 0–3")
require("slot >= 4" in handler, "automation extraction must be restricted to output slots 4–11")
require("inventory.insertItem(slot, stack, simulate)" in handler, "valid input must be delegated to the recipe handler")
require("inventory.extractItem(slot, amount, simulate)" in handler, "output extraction must delegate to the persistent inventory")

energy_match = re.search(
    r"private final EnergyStorage energyStorage = new EnergyStorage\(.*?\)\s*\{.*?\n    \};",
    s,
    flags=re.DOTALL,
)
external_match = re.search(
    r"private final LazyOptional<IEnergyStorage> energyCapability\s*=\s*LazyOptional\.of\(\(\) -> .*?\n    \}\);",
    s,
    flags=re.DOTALL,
)
require(energy_match is not None, "internal EnergyStorage declaration must be present")
require(external_match is not None, "external FE capability declaration must be present")
internal = energy_match.group(0)
external = external_match.group(0)
require("canExtract() { return true; }" in internal, "internal FE storage must be drainable by machine processors")
require("extractEnergy(int maxExtract, boolean simulate) { return 0; }" in external, "external cables must not extract energy")
require("canExtract() { return false; }" in external, "external Forge Energy endpoint must stay receive-only")
require("private boolean consumePower(int cost)" in s, "machine production must retain the energy consumption gate")
require("invalidateCaps()" in s and "itemHandler.invalidate()" in s and "energyCapability.invalidate()" in s, "optional capabilities must be invalidated")

print("Machine contract tests passed: 12-slot inventory, safe automation I/O, receive-only FE endpoint.")
'''
(root / "tools/test_machine_io_contract.py").write_text(test_script, encoding="utf-8")
print("Hardened machine IO and energy contracts; updated project to 1.1.7.")
