#!/usr/bin/env python3
"""Connect crop biodiversity, field harvesting, and Resonance Dampener maintenance (1.46.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen symbiosis: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def add_import(path, anchor, import_line, label):
    source = path.read_text(encoding="utf-8")
    if import_line in source:
        return
    require(anchor in source, "could not locate import anchor for " + label)
    path.write_text(source.replace(anchor, anchor + "\n" + import_line, 1), encoding="utf-8")


# A single source of truth for the crop-diversity rule. All probes are bounded and loaded-only.
symbiosis_path = SRC / "infection/MutagenSymbiosis.java"
symbiosis_path.write_text("""\
package de.sporenwerk.infection;

import de.sporenwerk.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Crop biodiversity under a real Mutagen field occasionally forms Symbiosemyzel.
 * This is a harvest-time query only: no ticker, chunk loading, or persistent per-block data.
 */
public final class MutagenSymbiosis {
    public static final int HORIZONTAL_RADIUS = 3;
    public static final int VERTICAL_RADIUS = 1;
    private static final int REQUIRED_SPECIES = 3;

    private MutagenSymbiosis() {}

    public static boolean shouldYield(Level level, BlockPos origin, int mutagenStrength, RandomSource random) {
        if (level.isClientSide || mutagenStrength < 2 || !level.hasChunkAt(origin)) return false;
        if (countCropSpecies(level, origin) < REQUIRED_SPECIES) return false;
        float chance = mutagenStrength >= 3 ? 0.28F : 0.12F;
        return random.nextFloat() < chance;
    }

    /** Counts distinct Sporenwerk crop species in a 7x3x7 bounded cylindrical neighborhood. */
    public static int countCropSpecies(Level level, BlockPos origin) {
        if (!level.hasChunkAt(origin)) return 0;
        boolean fiber = false;
        boolean amber = false;
        boolean root = false;
        boolean filter = false;
        BlockPos.MutableBlockPos probe = new BlockPos.MutableBlockPos();
        int radiusSquared = HORIZONTAL_RADIUS * HORIZONTAL_RADIUS;

        for (int dx = -HORIZONTAL_RADIUS; dx <= HORIZONTAL_RADIUS; dx++) {
            for (int dz = -HORIZONTAL_RADIUS; dz <= HORIZONTAL_RADIUS; dz++) {
                if (dx * dx + dz * dz > radiusSquared) continue;
                for (int dy = -VERTICAL_RADIUS; dy <= VERTICAL_RADIUS; dy++) {
                    probe.set(origin.getX() + dx, origin.getY() + dy, origin.getZ() + dz);
                    if (!level.hasChunkAt(probe)) continue;
                    BlockState state = level.getBlockState(probe);
                    if (state.is(ModBlocks.FASERROHR.get())) fiber = true;
                    else if (state.is(ModBlocks.BERNSTEINKAPPE.get())) amber = true;
                    else if (state.is(ModBlocks.ROTWURZEL.get())) root = true;
                    else if (state.is(ModBlocks.FILTERMOOS.get())) filter = true;
                    int species = (fiber ? 1 : 0) + (amber ? 1 : 0) + (root ? 1 : 0) + (filter ? 1 : 0);
                    if (species >= REQUIRED_SPECIES) return species;
                }
            }
        }
        return (fiber ? 1 : 0) + (amber ? 1 : 0) + (root ? 1 : 0) + (filter ? 1 : 0);
    }
}
""", encoding="utf-8")

# Register and describe the new field by-product.
items_path = SRC / "registry/ModItems.java"
add_import(items_path, "import de.sporenwerk.item.MutagenCoreCrystalItem;",
           "import de.sporenwerk.item.SymbiosemyzelItem;", "Symbiosemyzel item")
item_anchor = '    public static final RegistryObject<Item> KRISTALLPIRSCHER_RESONANZSPLITTER = ITEMS.register("kristallpirscher_resonanzsplitter", () -> new Item(new Item.Properties().stacksTo(16)));'
item_registration = item_anchor + '\n    public static final RegistryObject<Item> SYMBIOSEMYZEL = ITEMS.register("symbiosemyzel", () -> new SymbiosemyzelItem(new Item.Properties().stacksTo(16)));'
replace_once(items_path, item_anchor, item_registration, "resonance shard item registration")

(SRC / "item/SymbiosemyzelItem.java").write_text("""\
package de.sporenwerk.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import java.util.List;

/** Rare fungal by-product of diverse crops growing in strong Mutagen fields. */
public final class SymbiosemyzelItem extends Item {
    public SymbiosemyzelItem(Properties properties) { super(properties); }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.symbiosemyzel.1")
                .withStyle(ChatFormatting.LIGHT_PURPLE));
        tooltip.add(Component.translatable("tooltip.sporenwerk.symbiosemyzel.2")
                .withStyle(ChatFormatting.AQUA));
        super.appendHoverText(stack, level, tooltip, flag);
    }
}
""", encoding="utf-8")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative_addition = "output.accept(ModItems.SYMBIOSEMYZEL.get());"
creative_anchor = "output.accept(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get());"
creative = creative_path.read_text(encoding="utf-8")
if creative_addition not in creative:
    require(creative_anchor in creative, "could not locate resonance shard creative entry")
    creative_path.write_text(creative.replace(creative_anchor, creative_anchor + "\n                        " + creative_addition, 1), encoding="utf-8")

# A distinct transparent 16x16 pixel icon: woven emerald threads surrounding a pale cyan seed.
item_texture_dir = ASSETS / "textures/item"
item_texture_dir.mkdir(parents=True, exist_ok=True)
texture = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(texture)
ink = (14, 28, 26, 255)
deep = (29, 66, 53, 255)
green = (62, 151, 95, 255)
bright = (132, 231, 144, 255)
cyan = (90, 219, 218, 255)
pale = (216, 255, 224, 255)
magenta = (218, 92, 203, 255)
draw.line([(2, 11), (4, 8), (4, 4), (7, 2), (10, 4), (10, 7), (13, 9), (13, 12)],
          fill=ink, width=3)
draw.line([(2, 11), (4, 8), (4, 4), (7, 2), (10, 4), (10, 7), (13, 9), (13, 12)],
          fill=green, width=1)
draw.line([(3, 12), (6, 10), (7, 7), (9, 9), (12, 7)], fill=bright, width=1)
draw.polygon([(7, 4), (9, 6), (8, 9), (6, 8), (5, 6)], fill=cyan, outline=ink)
draw.point((7, 6), fill=pale)
draw.point((8, 7), fill=pale)
draw.point((2, 6), fill=magenta)
draw.point((12, 4), fill=magenta)
draw.point((5, 13), fill=cyan)
# Additional high-contrast facets keep the icon readable at inventory scale.
draw.point((1, 10), fill=deep)
draw.point((11, 12), fill=deep)
draw.point((14, 8), fill=bright)
draw.point((7, 13), fill=(255, 205, 109, 255))
draw.point((13, 3), fill=(255, 205, 109, 255))
texture_path = item_texture_dir / "symbiosemyzel.png"
texture.save(texture_path, optimize=True)
with Image.open(texture_path) as check:
    rgba = check.convert("RGBA")
    require(rgba.size == (16, 16) and any(px[3] == 0 for px in rgba.getdata()),
            "Symbiosemyzel item art must be a 16x16 transparent pixel-art sprite")
    require(len(set(rgba.getdata())) >= 8, "Symbiosemyzel icon needs distinct pixel details")

(ASSETS / "models/item/symbiosemyzel.json").write_text(json.dumps({
    "parent": "minecraft:item/generated",
    "textures": {"layer0": "sporenwerk:item/symbiosemyzel"}
}, indent=2) + "\n", encoding="utf-8")

# Manual crop harvest: same server-side helper as the automated collector.
crop_path = SRC / "block/crop/AbstractSporeCropBlock.java"
add_import(crop_path, "import de.sporenwerk.infection.MutationField;",
           "import de.sporenwerk.infection.MutagenSymbiosis;", "crop symbiosis helper")
crop_anchor = """        if (mutagenStrength > 0 && level.random.nextFloat() <
                (mutagenStrength >= 3 ? 0.35F : mutagenStrength == 2 ? 0.22F : 0.12F)) {
            Block.popResource(level, pos, new ItemStack(ModItems.MUTAGENE_SPOREN.get()));
        }"""
crop_addition = crop_anchor + """
        if (MutagenSymbiosis.shouldYield(level, pos, mutagenStrength, level.random)) {
            Block.popResource(level, pos, new ItemStack(ModItems.SYMBIOSEMYZEL.get()));
        }"""
replace_once(crop_path, crop_anchor, crop_addition, "tier-based mutagen spore output")

# Automated harvesting mirrors the manual by-product and reserves it before spending energy
# or consuming the crop, preserving the collector's atomic output-buffer contract.
machine_path = SRC / "block/entity/MachineBlockEntity.java"
add_import(machine_path, "import de.sporenwerk.infection.MutationField;",
           "import de.sporenwerk.infection.MutagenSymbiosis;", "collector symbiosis helper")
machine_anchor = """            ItemStack mutagenSpores = yieldsMutagenSpores
                    ? new ItemStack(ModItems.MUTAGENE_SPOREN.get())
                    : ItemStack.EMPTY;"""
machine_addition = machine_anchor + """
            boolean yieldsSymbiosis = MutagenSymbiosis.shouldYield(
                    level, target, mutagenStrength, level.random);
            ItemStack symbiosisMycelium = yieldsSymbiosis
                    ? new ItemStack(ModItems.SYMBIOSEMYZEL.get())
                    : ItemStack.EMPTY;"""
replace_once(machine_path, machine_anchor, machine_addition, "collector Mutagen-spore output")
machine = machine_path.read_text(encoding="utf-8")
old_fit = "if (!canFitOutputs(output, residue, mutagenSpores))"
new_fit = "if (!canFitOutputs(output, residue, mutagenSpores, symbiosisMycelium))"
if old_fit in machine:
    machine = machine.replace(old_fit, new_fit, 1)
elif new_fit not in machine:
    require(False, "could not extend collector output-capacity preflight")
old_insert = "if (!insertOutputs(output, residue, mutagenSpores))"
new_insert = "if (!insertOutputs(output, residue, mutagenSpores, symbiosisMycelium))"
if old_insert in machine:
    machine = machine.replace(old_insert, new_insert, 1)
elif new_insert not in machine:
    require(False, "could not extend collector output transaction")
machine_path.write_text(machine, encoding="utf-8")

# Symbiosemyzel is a sustainable but much less efficient one-charge refill, compared with
# a rare Resonance Shard that restores the entire charge reservoir.
dampener_path = SRC / "block/MutagenResonanceDampenerBlock.java"
dampener = dampener_path.read_text(encoding="utf-8")
dampener_anchor = """        int currentCharge = state.getValue(CHARGE);
        if (held.is(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get())) {"""
dampener_branch = """        int currentCharge = state.getValue(CHARGE);
        if (held.is(ModItems.SYMBIOSEMYZEL.get())) {
            if (currentCharge >= MAX_CHARGE) {
                player.displayClientMessage(
                        Component.translatable("message.sporenwerk.dampener.already_full",
                                currentCharge, MAX_CHARGE).withStyle(ChatFormatting.AQUA),
                        false
                );
                return InteractionResult.CONSUME;
            }
            int nextCharge = currentCharge + 1;
            level.setBlock(pos, state.setValue(CHARGE, nextCharge), 3);
            MutagenContainmentRelayBlock.refreshNearbyRelays(level, pos);
            if (!player.getAbilities().instabuild) held.shrink(1);
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.dampener.symbiosis_recharged", nextCharge, MAX_CHARGE)
                    .withStyle(ChatFormatting.LIGHT_PURPLE), false);
            if (level instanceof ServerLevel serverLevel) {
                serverLevel.sendParticles(ParticleTypes.WARPED_SPORE,
                        pos.getX() + 0.5D, pos.getY() + 0.9D, pos.getZ() + 0.5D,
                        14, 0.22D, 0.25D, 0.22D, 0.018D);
            }
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.BLOCKS, 0.8F, 0.82F);
            return InteractionResult.CONSUME;
        }
        if (held.is(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get())) {"""
replace_once(dampener_path, dampener_anchor, dampener_branch, "dampener shard recharge branch")

# Give discovery a named research milestone; no extra reward item is conjured out of nowhere.
(RES / "data/sporenwerk/advancements/mutagen_symbiosis.json").write_text(json.dumps({
    "parent": "sporenwerk:mutagen_laboratory",
    "display": {
        "icon": {"item": "sporenwerk:symbiosemyzel"},
        "title": {"translate": "advancements.sporenwerk.mutagen_symbiosis.title"},
        "description": {"translate": "advancements.sporenwerk.mutagen_symbiosis.description"},
        "frame": "goal",
        "show_toast": True,
        "announce_to_chat": False
    },
    "criteria": {
        "discover_symbiosis": {
            "trigger": "minecraft:inventory_changed",
            "conditions": {"items": [{"items": ["sporenwerk:symbiosemyzel"]}]}
        }
    },
    "requirements": [["discover_symbiosis"]]
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

locales = {
    "de_de.json": {
        "item.sporenwerk.symbiosemyzel": "Symbiosemyzel",
        "tooltip.sporenwerk.symbiosemyzel.1": "Seltenes Nebenprodukt aus drei oder mehr Sporenwerk-Pflanzenarten in einem Mutagenfeld der Stufe II oder III.",
        "tooltip.sporenwerk.symbiosemyzel.2": "Rechtsklick auf einen Resonanzdämpfer: stellt eine Ladung wieder her. Bei voller Ladung wird nichts verbraucht.",
        "message.sporenwerk.dampener.symbiosis_recharged": "Symbiosemyzel eingewoben: Dämpferladung %1$s/%2$s.",
        "advancements.sporenwerk.mutagen_symbiosis.title": "Leben im Verbund",
        "advancements.sporenwerk.mutagen_symbiosis.description": "Ernte Symbiosemyzel aus artenreichen Mutagenfeldern."
    },
    "en_us.json": {
        "item.sporenwerk.symbiosemyzel": "Symbiosis Mycelium",
        "tooltip.sporenwerk.symbiosemyzel.1": "Rare by-product from three or more Sporenwerk crop species inside a tier-II or tier-III Mutagen field.",
        "tooltip.sporenwerk.symbiosemyzel.2": "Right-click a Resonance Dampener to restore one charge. At full charge, the item is not consumed.",
        "message.sporenwerk.dampener.symbiosis_recharged": "Symbiosis Mycelium woven in: dampener charge %1$s/%2$s.",
        "advancements.sporenwerk.mutagen_symbiosis.title": "Life in Combination",
        "advancements.sporenwerk.mutagen_symbiosis.description": "Harvest Symbiosis Mycelium from a biodiverse Mutagen field."
    }
}
for locale, additions in locales.items():
    path = ASSETS / "lang" / locale
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Include the item in the visual QA sheet, which is uploaded alongside the JAR.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
if '"symbiosemyzel"' not in preview:
    anchor = '    "sporenfiltereinsatz", "sporenfiltereinsatz_verstaerkt", "sporenfiltereinsatz_mutagen"'
    require(anchor in preview, "could not locate item list in visual QA preview")
    preview_path.write_text(preview.replace(anchor, anchor + ', "symbiosemyzel"', 1), encoding="utf-8")

# Expand existing atomic-output assertions for the additional candidate stack.
for test_path in (ROOT / "tools").glob("test_*.py"):
    text = test_path.read_text(encoding="utf-8")
    updated = text.replace("canFitOutputs(output, residue, mutagenSpores)",
                           "canFitOutputs(output, residue, mutagenSpores, symbiosisMycelium)")
    updated = updated.replace("insertOutputs(output, residue, mutagenSpores)",
                              "insertOutputs(output, residue, mutagenSpores, symbiosisMycelium)")
    if updated != text:
        test_path.write_text(updated, encoding="utf-8")

# Advance active release assertions without rewriting historical release notes.
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "Aktueller Entwicklungsstand: 1.45.0" in line:
            lines[index] = line.replace("Aktueller Entwicklungsstand: 1.45.0",
                                        "Aktueller Entwicklungsstand: 1.46.0")
            line = lines[index]
            changed = True
        if r"1\.45\.0" not in line or "version" not in line.lower():
            continue
        newer = line.replace(r"1\.45\.0", r"1\.46\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.45.0" in lines[following] or "version must be 1.45.0" in lines[following]:
                lines[following] = lines[following].replace("1.45.0", "1.46.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.46.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.46.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.46.0 — Mutagen-Symbiose und nachhaltige Resonanzpflege

- **Artenreiche Felder werden belohnt:** Bei der Ernte im aktiven Mutagenfeld der Stufe II oder III kann selten Symbiosemyzel entstehen, wenn in der begrenzten Nachbarschaft mindestens drei verschiedene Sporenwerk-Pflanzenarten wachsen.
- **Ein gemeinsamer Erntevertrag:** Manuelle Ernte und Feldsammler verwenden dieselbe serverseitige Biodiversitätsprüfung und dieselbe stufenabhängige Chance. Der Feldsammler reserviert Symbiosemyzel zusammen mit Produkt, Pflanzenresten und mutagenen Sporen, bevor er Energie verbraucht oder die Pflanze verändert.
- **Nützlich für die Abwehr:** Symbiosemyzel stellt bei einem Rechtsklick auf einen Resonanzdämpfer genau eine Ladung wieder her. Ein Kristallpirscher-Resonanzsplitter bleibt der schnellere Weg zur vollständigen Aufladung. Bei vollem Dämpfer wird kein Symbiosemyzel verbraucht.
- **Rückmeldung und Forschung:** Eigenes 16×16-Item-Artwork, Tooltip, deutsche/englische Texte und ein Forschungsfortschritt dokumentieren den Fund. Die visuelle QA-Vorschau zeigt das neue Item.
- **Ressourcengrenzen:** Die Biodiversitätsabfrage ist auf Radius 3 und Höhe ±1 begrenzt, überspringt ungeladene Chunks und läuft nur im Erntevorgang. Kein Block-Ticker und kein erzwungenes Chunk-Laden.
- **Qualitätssicherung:** Regressionen prüfen die Artenzählung, Chancen nach Feldstärke, identische manuelle/automatisierte Ernte, atomare Maschinenpufferreservierung, Dämpferladung, Relay-Aktualisierung, Texte und Ressourcen.

"""
if "## Version 1.46.0 — Mutagen-Symbiose und nachhaltige Resonanzpflege" not in readme:
    marker = "## Version 1.45.0 — Multi-System-Feldanalyse, Gegenmittel und Ereignisfeedback"
    index = readme.find(marker)
    require(index >= 0, "could not locate the 1.45.0 release notes")
    readme = readme[:index] + section + readme[index:]
headline = "**Aktueller Entwicklungsstand: 1.46.0 — Mutagen-Symbiose, artenreiche Ernte und nachhaltige Resonanzpflege.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
old_focus = """## Aktueller Schwerpunkt — 1.45.0

- Der Feldscanner analysiert sowohl einzelne Blöcke als auch einen lokalen Bereich über Mutagenboden, mutierte Pflanzen, Sporenabwehr, Dämpferladungen, Sirenen, Relais und nahe Kristallpirscher.
- Rotwurzel-Konzentrat heilt zwei Herzen und entfernt Gift sowie Resonanzverlangsamung; eine eigene Rückmeldung nennt die tatsächlich entfernten Effekte.
- Mutagenblüten haben zusätzlich zu den bestehenden Partikeln und Belohnungen ein akustisches Ereignissignal.
- Der Bereichsscan bleibt serverseitig, einmalig pro Interaktion, auf 17×9×17 Blöcke begrenzt und überspringt ungeladene Chunks.
- Die Release-Pipeline prüft Regressionen, übersetzte Texte, Forge-Build, installierbare JAR und den dedizierten Serverstart."""
new_focus = """## Aktueller Schwerpunkt — 1.46.0

- Artenvielfalt wird zur Spielmechanik: Drei verschiedene Sporenwerk-Pflanzen in einem begrenzten Cluster können unter Mutagenstufe II/III Symbiosemyzel erzeugen.
- Manuelle Ernte und Feldsammler verwenden dieselbe Regel; der Maschinenpuffer reserviert den Bonusfund, bevor Energie oder Pflanzenzustand verändert werden.
- Symbiosemyzel verbindet Landwirtschaft und Abwehrtechnik, indem es bei Resonanzdämpfern eine einzelne Ladung wiederherstellt und gespeicherte Relais-Signale aktualisieren lässt.
- Forschungsfortschritt, Tooltipps, Item-Textur, DE/EN-Texte und Vorschau machen die neue Schleife auffindbar und verständlich.
- Die Release-Pipeline prüft Artenzählung, Feldstärkeschwellen, atomare Ausgabe, Dämpfer- und Relaisverhalten, Forge-Build, JAR und dedizierten Serverstart."""
if old_focus in readme:
    readme = readme.replace(old_focus, new_focus, 1)
else:
    focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
    if focus_lines:
        readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.46.0", 1)
readme_path.write_text(readme, encoding="utf-8")

print("Sporenwerk 1.46.0 generated: biodiversity-based symbiosis resource, shared manual/automated harvest, and one-charge dampener refill.")
