#!/usr/bin/env python3
"""Add a configurable, comparator-driven Mutagen Containment Relay (1.43.0)."""
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


def require(condition, message):
    if not condition:
        raise SystemExit("Mutagen Containment Relay: " + message)


def replace_once(path, old, new, label):
    content = path.read_text(encoding="utf-8")
    if new in content:
        return
    require(old in content, "could not locate " + label)
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


# Add the relay beside the siren so its source-of-truth block properties are available.
replace_once(SRC / "registry/ModBlocks.java",
    "import de.sporenwerk.block.MutagenWarningSirenBlock;",
    "import de.sporenwerk.block.MutagenWarningSirenBlock;\nimport de.sporenwerk.block.MutagenContainmentRelayBlock;",
    "siren import")

siren_registration = """    public static final RegistryObject<Block> MUTAGEN_WARNSIRENE = BLOCKS.register("mutagen_warnsirene",
            () -> new MutagenWarningSirenBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_RED)
                    .strength(3.5f, 6.0f).requiresCorrectToolForDrops().sound(SoundType.METAL)));"""
relay_registration = """    public static final RegistryObject<Block> MUTAGEN_CONTAINMENT_RELAY = BLOCKS.register("mutagen_containment_relay",
            () -> new MutagenContainmentRelayBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN)
                    .strength(4.0f, 7.0f).requiresCorrectToolForDrops().sound(SoundType.AMETHYST)));"""
replace_once(SRC / "registry/ModBlocks.java", siren_registration,
             siren_registration + "\n\n" + relay_registration, "siren block registration")

siren_item = '        ModItems.ITEMS.register("mutagen_warnsirene", () -> new net.minecraft.world.item.BlockItem(MUTAGEN_WARNSIRENE.get(), new Item.Properties()));'
relay_item = '        ModItems.ITEMS.register("mutagen_containment_relay", () -> new net.minecraft.world.item.BlockItem(MUTAGEN_CONTAINMENT_RELAY.get(), new Item.Properties()));'
replace_once(SRC / "registry/ModBlocks.java", siren_item,
             siren_item + "\n" + relay_item, "siren block item")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
creative_anchor = "output.accept(ModBlocks.MUTAGEN_WARNSIRENE.get());"
creative_addition = "output.accept(ModBlocks.MUTAGEN_CONTAINMENT_RELAY.get());"
if creative_addition not in creative:
    require(creative_anchor in creative, "could not locate siren creative-tab entry")
    creative_path.write_text(creative.replace(creative_anchor, creative_anchor + "\n                        " + creative_addition, 1), encoding="utf-8")

write_path = SRC / "block/MutagenContainmentRelayBlock.java"
write_path.parent.mkdir(parents=True, exist_ok=True)
write_path.write_text("""\
package de.sporenwerk.block;

import de.sporenwerk.registry.ModBlocks;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ComparatorBlock;
import net.minecraft.world.level.block.RedStoneRepeaterBlock;
import net.minecraft.world.level.block.RedStoneWireBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Configurable redstone relay for Mutagen facility automation.
 * It samples existing blocks on interaction or relevant neighbour changes;
 * there is no BlockEntity, ticker, or forced chunk load.
 */
public final class MutagenContainmentRelayBlock extends Block {
    public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 3);
    public static final IntegerProperty SIGNAL = IntegerProperty.create("signal", 0, 15);
    public static final int HORIZONTAL_SCAN_RADIUS = 16;
    public static final int VERTICAL_SCAN_RADIUS = 8;

    public MutagenContainmentRelayBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(MODE, 0).setValue(SIGNAL, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(MODE, SIGNAL);
    }

    @Override
    public boolean hasAnalogOutputSignal(BlockState state) {
        return true;
    }

    @Override
    public int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos) {
        return state.getValue(SIGNAL);
    }

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos,
                                Block neighborBlock, BlockPos neighborPos, boolean moving) {
        if (level.isClientSide || !isRelevantInput(neighborBlock)) return;
        int signal = evaluate(level, pos, state.getValue(MODE));
        if (state.getValue(SIGNAL) != signal) {
            level.setBlock(pos, state.setValue(SIGNAL, signal), 3);
        }
    }

    private static boolean isRelevantInput(Block block) {
        return block instanceof RedStoneWireBlock
                || block instanceof ComparatorBlock
                || block instanceof RedStoneRepeaterBlock
                || block instanceof MutagenFieldControlStationBlock
                || block instanceof MutagenWarningSirenBlock
                || block instanceof SporeWardBlock
                || block instanceof MutagenResonanceDampenerBlock;
    }

    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        int step = player.isShiftKeyDown() ? 3 : 1;
        int mode = (state.getValue(MODE) + step) % 4;
        int signal = evaluate(level, pos, mode);
        level.setBlock(pos, state.setValue(MODE, mode).setValue(SIGNAL, signal), 3);
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.containment_relay.status",
                Component.translatable(modeKey(mode)), signal).withStyle(colorFor(mode, signal)), false);
        return InteractionResult.CONSUME;
    }

    private static ChatFormatting colorFor(int mode, int signal) {
        if (mode == 3 && signal >= 15) return ChatFormatting.RED;
        if (signal >= 11) return ChatFormatting.RED;
        if (signal > 0) return ChatFormatting.YELLOW;
        return ChatFormatting.GREEN;
    }

    private static String modeKey(int mode) {
        return switch (mode) {
            case 1 -> "message.sporenwerk.containment_relay.mode_alarm";
            case 2 -> "message.sporenwerk.containment_relay.mode_reserve";
            case 3 -> "message.sporenwerk.containment_relay.mode_gap";
            default -> "message.sporenwerk.containment_relay.mode_overall";
        };
    }

    /**
     * Mode 0: highest cached station hazard or latched siren signal.
     * Mode 1: compact alarm tier (0/5/10/15) from station and siren status.
     * Mode 2: remaining Resonance Dampener charges, five comparator levels each.
     * Mode 3: containment gap; a tier-III hotspot without both device types outputs 15.
     */
    private static int evaluate(Level level, BlockPos center, int mode) {
        int stationSignal = 0;
        int sirenSignal = 0;
        int criticalSirens = 0;
        int poweredWards = 0;
        int counterpulses = 0;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        int minY = Math.max(level.getMinBuildHeight(), center.getY() - VERTICAL_SCAN_RADIUS);
        int maxY = Math.min(level.getMaxBuildHeight() - 1, center.getY() + VERTICAL_SCAN_RADIUS);
        int radiusSquared = HORIZONTAL_SCAN_RADIUS * HORIZONTAL_SCAN_RADIUS;

        for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++) {
            for (int dz = -HORIZONTAL_SCAN_RADIUS; dz <= HORIZONTAL_SCAN_RADIUS; dz++) {
                if (dx * dx + dz * dz > radiusSquared) continue;
                int x = center.getX() + dx;
                int z = center.getZ() + dz;
                if (!level.hasChunkAt(new BlockPos(x, center.getY(), z))) continue;
                for (int y = minY; y <= maxY; y++) {
                    cursor.set(x, y, z);
                    BlockState scanned = level.getBlockState(cursor);
                    if (scanned.is(ModBlocks.MUTAGENFELD_KONTROLLSTATION.get())
                            && scanned.hasProperty(MutagenFieldControlStationBlock.POWER)) {
                        stationSignal = Math.max(stationSignal, scanned.getValue(MutagenFieldControlStationBlock.POWER));
                    }
                    if (scanned.is(ModBlocks.MUTAGEN_WARNSIRENE.get())
                            && scanned.hasProperty(MutagenWarningSirenBlock.SIGNAL)) {
                        int stored = scanned.getValue(MutagenWarningSirenBlock.SIGNAL);
                        sirenSignal = Math.max(sirenSignal, stored);
                        if (MutagenWarningSirenBlock.riskBand(stored) == 3) criticalSirens++;
                    }
                    if (scanned.is(ModBlocks.SPORENABWEHR.get())
                            && scanned.hasProperty(SporeWardBlock.POWERED)
                            && scanned.getValue(SporeWardBlock.POWERED)) {
                        poweredWards++;
                    }
                    if (scanned.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                            && scanned.hasProperty(MutagenResonanceDampenerBlock.CHARGE)) {
                        counterpulses += scanned.getValue(MutagenResonanceDampenerBlock.CHARGE);
                    }
                }
            }
        }

        return switch (mode) {
            case 1 -> {
                if (criticalSirens > 0 || stationSignal >= 11) yield 15;
                if (sirenSignal >= 5 || stationSignal >= 5) yield 10;
                if (sirenSignal > 0 || stationSignal > 0) yield 5;
                yield 0;
            }
            case 2 -> Math.min(15, counterpulses * 5);
            case 3 -> {
                if (stationSignal >= 11 && (poweredWards == 0 || counterpulses == 0)) yield 15;
                if (stationSignal >= 11) yield 5;
                if (criticalSirens > 0) yield 15;
                if (sirenSignal > 0 || stationSignal >= 5) yield 10;
                yield 0;
            }
            default -> Math.max(stationSignal, sirenSignal);
        };
    }
}
""", encoding="utf-8")

# All mode/signal combinations share one unmistakable industrial pixel-art model.
blockstate_path = ASSETS / "blockstates/mutagen_containment_relay.json"
blockstate_path.parent.mkdir(parents=True, exist_ok=True)
variants = {}
for mode in range(4):
    for signal in range(16):
        variants[f"mode={mode},signal={signal}"] = {"model": "sporenwerk:block/mutagen_containment_relay"}
blockstate_path.write_text(json.dumps({"variants": variants}, indent=2) + "\n", encoding="utf-8")

(ASSETS / "models/block").mkdir(parents=True, exist_ok=True)
(ASSETS / "models/item").mkdir(parents=True, exist_ok=True)
(ASSETS / "models/block/mutagen_containment_relay.json").write_text(json.dumps({
    "parent": "minecraft:block/cube_column",
    "textures": {
        "end": "sporenwerk:block/mutagen_containment_relay_top",
        "side": "sporenwerk:block/mutagen_containment_relay_side"
    }
}, indent=2) + "\n", encoding="utf-8")
(ASSETS / "models/item/mutagen_containment_relay.json").write_text(json.dumps({
    "parent": "sporenwerk:block/mutagen_containment_relay"
}, indent=2) + "\n", encoding="utf-8")

TEXTURES.mkdir(parents=True, exist_ok=True)

def make_relay(top):
    im = Image.new("RGBA", (16, 16), (22, 34, 38, 255))
    d = ImageDraw.Draw(im)
    if top:
        d.rectangle((0, 0, 15, 15), fill=(29, 45, 48, 255), outline=(9, 18, 22, 255))
        d.rectangle((1, 1, 14, 14), fill=(21, 33, 38, 255), outline=(161, 119, 66, 255))
        d.rectangle((3, 3, 12, 12), fill=(13, 27, 35, 255), outline=(54, 148, 149, 255))
        d.rectangle((5, 5, 10, 10), fill=(32, 120, 123, 255), outline=(64, 225, 204, 255))
        d.line([(2, 7), (4, 7), (5, 8), (4, 9), (2, 9)], fill=(219, 169, 91, 255))
        d.line([(13, 7), (11, 7), (10, 8), (11, 9), (13, 9)], fill=(219, 169, 91, 255))
        d.line([(7, 2), (7, 4), (8, 5), (9, 4), (9, 2)], fill=(65, 195, 184, 255))
        d.line([(7, 13), (7, 11), (8, 10), (9, 11), (9, 13)], fill=(65, 195, 184, 255))
        d.rectangle((6, 6, 9, 9), fill=(50, 205, 189, 255))
        d.rectangle((7, 7, 8, 8), fill=(244, 255, 215, 255))
        for x, y in ((2, 2), (12, 2), (2, 12), (12, 12)):
            d.rectangle((x, y, x+1, y+1), fill=(196, 143, 76, 255))
    else:
        d.rectangle((0, 0, 15, 15), fill=(28, 42, 47, 255), outline=(9, 18, 22, 255))
        d.rectangle((1, 1, 14, 3), fill=(51, 66, 69, 255))
        d.rectangle((1, 12, 14, 14), fill=(36, 48, 51, 255))
        d.rectangle((2, 4, 13, 11), fill=(13, 26, 33, 255), outline=(155, 114, 65, 255))
        d.rectangle((4, 5, 11, 10), fill=(26, 76, 85, 255), outline=(53, 159, 159, 255))
        d.rectangle((5, 6, 10, 9), fill=(29, 126, 128, 255))
        d.rectangle((6, 7, 9, 8), fill=(75, 227, 206, 255))
        d.point((7, 7), fill=(241, 255, 222, 255))
        for x in (2, 4, 11, 13):
            d.line([(x, 5), (x, 10)], fill=(198, 145, 77, 255), width=1)
        d.line([(3, 2), (12, 2)], fill=(64, 198, 188, 255), width=1)
        d.line([(3, 13), (12, 13)], fill=(64, 198, 188, 255), width=1)
    return im

for name, image in (
    ("mutagen_containment_relay_top.png", make_relay(True)),
    ("mutagen_containment_relay_side.png", make_relay(False)),
):
    path = TEXTURES / name
    image.save(path, optimize=True)
    with Image.open(path) as check:
        rgba = check.convert("RGBA")
        require(rgba.size == (16, 16) and all(pixel[3] == 255 for pixel in rgba.getdata()),
                name + " must be an opaque 16x16 texture")
        require(len(set(rgba.getdata())) >= 12, name + " needs readable pixel-art contrast")

(RES / "data/sporenwerk/recipes").mkdir(parents=True, exist_ok=True)
(RES / "data/sporenwerk/recipes/mutagen_containment_relay.json").write_text("""\
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["IRI", "QMQ", "IRI"],
  "key": {
    "I": {"item": "minecraft:copper_ingot"},
    "R": {"item": "minecraft:redstone"},
    "Q": {"item": "minecraft:quartz"},
    "M": {"item": "sporenwerk:mutagenkernkristall"}
  },
  "result": {"item": "sporenwerk:mutagen_containment_relay", "count": 1}
}
""", encoding="utf-8")
(RES / "data/sporenwerk/loot_tables/blocks").mkdir(parents=True, exist_ok=True)
(RES / "data/sporenwerk/loot_tables/blocks/mutagen_containment_relay.json").write_text("""\
{
  "type": "minecraft:block",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        {"type": "minecraft:item", "name": "sporenwerk:mutagen_containment_relay"}
      ]
    }
  ]
}
""", encoding="utf-8")
(RES / "data/sporenwerk/advancements/recipes/misc").mkdir(parents=True, exist_ok=True)
(RES / "data/sporenwerk/advancements/recipes/misc/mutagen_containment_relay.json").write_text("""\
{
  "parent": "minecraft:recipes/root",
  "rewards": {"recipes": ["sporenwerk:mutagen_containment_relay"]},
  "criteria": {
    "has_copper": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:copper_ingot"]}]}
    },
    "has_redstone": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:redstone"]}]}
    },
    "has_quartz": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["minecraft:quartz"]}]}
    },
    "has_mutagen_core": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {"items": [{"items": ["sporenwerk:mutagenkernkristall"]}]}
    }
  },
  "requirements": [["has_copper"], ["has_redstone"], ["has_quartz"], ["has_mutagen_core"]]
}
""", encoding="utf-8")

for filename, additions in {
    "de_de.json": {
        "block.sporenwerk.mutagen_containment_relay": "Mutagen-Containment-Relais",
        "item.sporenwerk.mutagen_containment_relay": "Mutagen-Containment-Relais",
        "message.sporenwerk.containment_relay.mode_overall": "Gesamtrisiko",
        "message.sporenwerk.containment_relay.mode_alarm": "Alarmstufe",
        "message.sporenwerk.containment_relay.mode_reserve": "Gegenimpuls-Reserve",
        "message.sporenwerk.containment_relay.mode_gap": "Containment-Lücke",
        "message.sporenwerk.containment_relay.status": "Containment-Relais — Modus: %s; Comparator-Ausgang: %s/15. Rechtsklick wechselt den Modus, Schleichen + Rechtsklick schaltet zurück."
    },
    "en_us.json": {
        "block.sporenwerk.mutagen_containment_relay": "Mutagen Containment Relay",
        "item.sporenwerk.mutagen_containment_relay": "Mutagen Containment Relay",
        "message.sporenwerk.containment_relay.mode_overall": "Overall risk",
        "message.sporenwerk.containment_relay.mode_alarm": "Alarm tier",
        "message.sporenwerk.containment_relay.mode_reserve": "Counterpulse reserve",
        "message.sporenwerk.containment_relay.mode_gap": "Containment gap",
        "message.sporenwerk.containment_relay.status": "Containment Relay — mode: %s; comparator output: %s/15. Right-click advances the mode; sneak + right-click cycles backwards."
    }
}.items():
    locale_path = ASSETS / "lang" / filename
    locale = json.loads(locale_path.read_text(encoding="utf-8"))
    locale.update(additions)
    locale_path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Include the relay's custom art in the same generated QA preview as the other equipment.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
preview_anchor = '    ("mutagen_warnsirene_active", "Warnsirene AN"),'
preview_addition = preview_anchor + '\n' + \
    '    ("mutagen_containment_relay_top", "Containment-Relais oben"),\n' + \
    '    ("mutagen_containment_relay_side", "Containment-Relais Seite"),'
if "mutagen_containment_relay_top" not in preview:
    require(preview_anchor in preview, "could not locate siren art preview anchor")
    preview_path.write_text(preview.replace(preview_anchor, preview_addition, 1), encoding="utf-8")

# Keep the current README and active release assertions in sync, preserving historical notes.
updated_tests = 0
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "Aktueller Entwicklungsstand: 1.42.0" in line:
            lines[index] = line.replace("Aktueller Entwicklungsstand: 1.42.0",
                                        "Aktueller Entwicklungsstand: 1.43.0")
            line = lines[index]
            changed = True
        if r"1\.42\.0" not in line or "version" not in line.lower():
            continue
        newer = line.replace(r"1\.42\.0", r"1\.43\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.42.0" in lines[following] or "version must be 1.42.0" in lines[following]:
                lines[following] = lines[following].replace("1.42.0", "1.43.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")
        updated_tests += 1

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.43.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle version to 1.43.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.43.0 — Konfigurierbares Mutagen-Containment-Relais

- **Vier echte Comparator-Modi:** Gesamtrisiko (höchster Stations-/Sirenenwert), gestufter Alarm (0/5/10/15), verbleibende Resonanz-Gegenimpulse (fünf Signalstufen je Ladung) und Containment-Lücke (15 bei Stärke-III-Hotspot ohne beide Gegenmitteltypen).
- **Bedienbar im Spiel:** Rechtsklick schaltet den Modus vorwärts, Schleichen + Rechtsklick zurück. Die Station zeigt Modus und Ausgangswert direkt an.
- **Redstone-kompatibel:** Der Relay-Ausgang wird als gespeicherter Blockzustand bereitgestellt. Er aktualisiert sich nach manueller Abfrage und relevanten direkten Redstone-/Geräte-Nachbaränderungen, ohne Block-Entity oder Dauer-Ticker.
- **Begrenzte Abfrage:** Der Relay-Scan erfasst maximal 16 Blöcke horizontal und ±8 vertikal, prüft nur geladene Chunks und überschreibt weder den Stations-Comparator noch den gespeicherten Sirenenalarm.
- **Überlebensmodus und Art:** Eigenes Rezept, Loot-Tabelle, Forschungs-Rezeptfreigabe, hochkontrastige 16×16-Texturen, DE/EN-Meldungen sowie 64 gültige MODE/SIGNAL-Blockzustände.
- **Qualitätssicherung:** Regressionstests prüfen alle Modi, Redstone-Ausgang, Blockzustände, Texturen, Rezept, Chunk-Sicherheit und die Installations-JAR.

"""
if "## Version 1.43.0 — Konfigurierbares Mutagen-Containment-Relais" not in readme:
    marker = "## Version 1.42.0 — Sirenenprotokoll und Containment-Empfehlungen"
    index = readme.find(marker)
    require(index >= 0, "could not find 1.42.0 release notes to preserve history")
    readme = readme[:index] + section + readme[index:]
target = "**Aktueller Entwicklungsstand: 1.43.0 — konfigurierbares Redstone-Relais für Mutagen-Containment.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], target, 1)
else:
    readme = target + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines:
    readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.43.0", 1)
else:
    readme = readme.replace(target, target + "\n\n## Aktueller Schwerpunkt — 1.43.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print(f"1.43.0 Containment Relay generated; updated {updated_tests} active-version regression assertions.")
