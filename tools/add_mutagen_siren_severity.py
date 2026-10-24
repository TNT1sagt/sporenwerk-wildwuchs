#!/usr/bin/env python3
"""Give the Mutagen warning siren three visual/audio severity bands."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"
TEX = ASSETS / "textures/block"


# The siren stores the actual neighboring redstone strength, not just a boolean.
# Sound plays once when entering a higher risk band, never on every block update.
siren_java = """\
package de.sporenwerk.block;

import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;

public final class MutagenWarningSirenBlock extends Block {
    public static final IntegerProperty SIGNAL = IntegerProperty.create("signal", 0, 15);

    public MutagenWarningSirenBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(SIGNAL, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(SIGNAL);
    }

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos,
                                Block neighborBlock, BlockPos neighborPos, boolean moving) {
        if (level.isClientSide) return;
        int previousSignal = state.getValue(SIGNAL);
        int nextSignal = level.getBestNeighborSignal(pos);
        if (previousSignal == nextSignal) return;

        level.setBlock(pos, state.setValue(SIGNAL, nextSignal), 3);
        int previousBand = riskBand(previousSignal);
        int nextBand = riskBand(nextSignal);
        // Play only on activation or escalation. Falling/clearing risk never emits an alarm tone.
        if (nextBand > previousBand) {
            float pitch = switch (nextBand) {
                case 3 -> 0.55F;
                case 2 -> 0.82F;
                default -> 1.18F;
            };
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BELL.value(),
                    SoundSource.BLOCKS, 0.9F, pitch);
        }
    }

    /** 0 = clear, 1 = warning (1–4), 2 = elevated (5–10), 3 = critical (11–15). */
    public static int riskBand(int signal) {
        if (signal >= 11) return 3;
        if (signal >= 5) return 2;
        return signal > 0 ? 1 : 0;
    }
}
"""
siren_path = SRC / "block/MutagenWarningSirenBlock.java"
siren_path.write_text(siren_java, encoding="utf-8")

# Four explicit state families keep the signal understandable without a GUI:
# off, warning, elevated, critical. All 16 values have a model mapping.
blockstate = {"variants": {}}
for signal in range(16):
    model = (
        "sporenwerk:block/mutagen_warnsirene" if signal == 0 else
        "sporenwerk:block/mutagen_warnsirene_active" if signal <= 4 else
        "sporenwerk:block/mutagen_warnsirene_elevated" if signal <= 10 else
        "sporenwerk:block/mutagen_warnsirene_critical"
    )
    blockstate["variants"][f"signal={signal}"] = {"model": model}
(ASSETS / "blockstates/mutagen_warnsirene.json").write_text(
    json.dumps(blockstate, indent=2) + "\n", encoding="utf-8"
)

for model_name in ("mutagen_warnsirene_elevated", "mutagen_warnsirene_critical"):
    model = {"parent": "minecraft:block/cube_all",
             "textures": {"all": f"sporenwerk:block/{model_name}"}}
    model_path = ASSETS / f"models/block/{model_name}.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")

# Evolved textures are painted over the already generated alert texture to preserve
# the same industrial casing while changing the center lens and emergency markers.
TEX.mkdir(parents=True, exist_ok=True)
source_path = TEX / "mutagen_warnsirene_active.png"
if not source_path.is_file():
    raise SystemExit("The 1.29.0 warning siren texture must exist before severity tiers are applied")
with Image.open(source_path) as source:
    base = source.convert("RGBA")

elevated = base.copy()
d = ImageDraw.Draw(elevated)
d.rectangle((3, 5, 12, 11), fill=(143, 79, 28, 255), outline=(244, 174, 66, 255))
d.rectangle((4, 6, 11, 10), fill=(246, 152, 50, 255))
d.rectangle((5, 7, 10, 9), fill=(255, 224, 128, 255))
d.rectangle((0, 5, 1, 10), fill=(255, 172, 43, 255))
d.rectangle((14, 5, 15, 10), fill=(255, 172, 43, 255))
d.line([(5, 3), (7, 2), (9, 3)], fill=(255, 207, 94, 255), width=1)

critical = base.copy()
d = ImageDraw.Draw(critical)
d.rectangle((2, 4, 13, 12), fill=(84, 19, 29, 255), outline=(255, 71, 73, 255))
d.rectangle((4, 5, 11, 11), fill=(186, 30, 45, 255))
d.rectangle((5, 6, 10, 10), fill=(255, 62, 53, 255))
d.rectangle((6, 7, 9, 9), fill=(255, 240, 197, 255))
d.rectangle((0, 4, 1, 11), fill=(255, 48, 48, 255))
d.rectangle((14, 4, 15, 11), fill=(255, 48, 48, 255))
d.line([(4, 2), (6, 1), (8, 2), (10, 1), (12, 2)], fill=(255, 110, 94, 255), width=1)

for name, image in (("mutagen_warnsirene_elevated", elevated),
                    ("mutagen_warnsirene_critical", critical)):
    path = TEX / f"{name}.png"
    image.save(path, optimize=True)
    with Image.open(path) as check:
        rgba = check.convert("RGBA")
        if rgba.size != (16, 16) or any(px[3] != 255 for px in rgba.getdata()):
            raise SystemExit(f"{name} must be a fully opaque 16x16 texture")

# Extend the same art preview with both escalation states.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
anchor = '    ("mutagen_warnsirene_active", "Warnsirene AN"),'
addition = anchor + '\n' + \
    '    ("mutagen_warnsirene_elevated", "Warnsirene ERHÖHT"),\n' + \
    '    ("mutagen_warnsirene_critical", "Warnsirene KRITISCH"),'
if "mutagen_warnsirene_critical" not in preview:
    if anchor not in preview:
        raise SystemExit("Cannot add siren escalation art to the preview sheet")
    preview_path.write_text(preview.replace(anchor, addition, 1), encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.30.0'",
                       build_path.read_text(encoding="utf-8"), count=1)
if count != 1:
    raise SystemExit("Could not bump Gradle version to 1.30.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.30.0 — Eskalierende Mutagen-Warnsirene

- **Vier eindeutig sichtbare Zustände:** AUS, Warnung (Comparator-Signal 1–4), erhöht (5–10) und kritisch (11–15). Die Sirene speichert die empfangene Redstone-Stärke und bildet alle 16 Werte auf passende Blockmodelle ab.
- **Akustische Eskalation:** Beim Wechsel in eine höhere Gefahrenstufe ertönt ein Glockenton mit tieferer Tonhöhe für höhere Gefahr. Der Ton wird nur bei Aktivierung oder Eskalation abgespielt, nicht bei jedem Redstone-Update.
- **Direkt mit dem Comparator kombinierbar:** Der Ausgang der Mutagenfeld-Kontrollstation kann direkt in die Sirene geführt werden. Eine erneute Stationsmessung aktualisiert die Signalstärke und die Sirenenstufe.
- **Qualitätssicherung:** Regressionstests decken Grenzwerte, alle 16 Blockstates, Texturen, Blockmodelle, Rezept, Übersetzungen und Forge-JAR ab.

Automatische Tests ersetzen keinen manuellen Funktionstest des Comparator-/Sirenenaufbaus im Minecraft-Client.

"""
if "## Version 1.30.0 — Eskalierende Mutagen-Warnsirene" not in readme:
    marker = "## Version 1.29.0 — Redstone-Warnsirene"
    idx = readme.find(marker)
    if idx < 0:
        raise SystemExit("Cannot find 1.29.0 release notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.29.0 — Mutagenfelder mit Comparator und Warnsirene.**",
    "**Aktueller Entwicklungsstand: 1.30.0 — gestufte Mutagen-Warnsirene mit Alarm-Eskalation.**"
).replace("## Aktueller Schwerpunkt — 1.29.0", "## Aktueller Schwerpunkt — 1.30.0")
if "eskalierende Warntöne" not in readme[:2200]:
    readme = readme.replace(
        "- Die Mutagen-Warnsirene reagiert sichtbar und akustisch auf ein Redstone-Alarmsignal.",
        "- Die Mutagen-Warnsirene unterscheidet Warnung, erhöhte Gefahr und kritische Belastung visuell; Warntöne eskalieren nur bei einem Wechsel in eine höhere Stufe."
    )
readme_path.write_text(readme, encoding="utf-8")
print("Mutagen siren severity bands, escalation tones, texture/model mappings, and 1.30.0 release notes generated.")
