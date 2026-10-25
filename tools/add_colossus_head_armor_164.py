#!/usr/bin/env python3
"""1.64.0 adds angular brow and cheek armor to the Crystal Colossus head."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Colossus head armor 1.64: " + message)


def replace_once(path, old, new, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return
    count = source.count(old)
    require(count == 1, f"{label}: expected exactly one source anchor, got {count}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


main_armor = '''        head.addOrReplaceChild("brow_armor_left",
                CubeListBuilder.create().texOffs(152, 68)
                        .addBox(-8.0F, -8.6F, -14.2F, 8.0F, 4.0F, 8.0F)
                        .texOffs(152, 84).addBox(-7.0F, -10.0F, -12.7F, 6.0F, 2.0F, 5.0F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 0.0F, 0.02F, 0.02F, -0.10F));
        head.addOrReplaceChild("brow_armor_right",
                CubeListBuilder.create().texOffs(184, 68)
                        .addBox(0.0F, -8.6F, -14.2F, 8.0F, 4.0F, 8.0F)
                        .texOffs(184, 84).addBox(1.0F, -10.0F, -12.7F, 6.0F, 2.0F, 5.0F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 0.0F, 0.02F, -0.02F, 0.10F));
        head.addOrReplaceChild("cheek_armor_left",
                CubeListBuilder.create().texOffs(216, 68)
                        .addBox(-8.0F, -1.0F, -14.8F, 5.0F, 5.0F, 5.0F)
                        .texOffs(216, 84).addBox(-7.0F, 2.0F, -16.0F, 4.0F, 3.0F, 3.0F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 0.0F, 0.0F, 0.0F, -0.06F));
        head.addOrReplaceChild("cheek_armor_right",
                CubeListBuilder.create().texOffs(216, 68)
                        .addBox(3.0F, -1.0F, -14.8F, 5.0F, 5.0F, 5.0F)
                        .texOffs(216, 84).addBox(3.0F, 2.0F, -16.0F, 4.0F, 3.0F, 3.0F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.06F));'''
replace_once(MODEL, '        head.addOrReplaceChild("horn_left",', main_armor + '\n        head.addOrReplaceChild("horn_left",',
             'head.addOrReplaceChild("brow_armor_left"', "main head armor")

glow_anchor = '''        head.addOrReplaceChild("mouth_glow",
                CubeListBuilder.create().texOffs(200, 44).addBox(-4.0F, 2.5F, -17.8F, 8.0F, 1.2F, 1.0F),
                PartPose.ZERO);'''
glow_addition = glow_anchor + '''
        head.addOrReplaceChild("brow_armor_left",
                CubeListBuilder.create().texOffs(152, 68)
                        .addBox(-8.18F, -8.72F, -14.38F, 8.36F, 4.24F, 8.36F)
                        .texOffs(152, 84).addBox(-7.12F, -10.12F, -12.86F, 6.24F, 2.12F, 5.24F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 0.0F, 0.02F, 0.02F, -0.10F));
        head.addOrReplaceChild("brow_armor_right",
                CubeListBuilder.create().texOffs(184, 68)
                        .addBox(-0.18F, -8.72F, -14.38F, 8.36F, 4.24F, 8.36F)
                        .texOffs(184, 84).addBox(0.88F, -10.12F, -12.86F, 6.24F, 2.12F, 5.24F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 0.0F, 0.02F, -0.02F, 0.10F));
        head.addOrReplaceChild("cheek_armor_left",
                CubeListBuilder.create().texOffs(216, 68)
                        .addBox(-8.18F, -1.12F, -14.98F, 5.24F, 5.24F, 5.24F)
                        .texOffs(216, 84).addBox(-7.12F, 1.88F, -16.18F, 4.24F, 3.12F, 3.24F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 0.0F, 0.0F, 0.0F, -0.06F));
        head.addOrReplaceChild("cheek_armor_right",
                CubeListBuilder.create().texOffs(216, 68)
                        .addBox(2.88F, -1.12F, -14.98F, 5.24F, 5.24F, 5.24F)
                        .texOffs(216, 84).addBox(2.88F, 1.88F, -16.18F, 4.24F, 3.12F, 3.24F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.06F));'''
replace_once(MODEL, glow_anchor, glow_addition, 'addBox(-8.18F, -8.72F, -14.38F', "head glow armor")

def paint_head_atlas(path, emissive):
    image = Image.open(path).convert("RGBA")
    d = ImageDraw.Draw(image)
    regions = [
        (152, 68, 178, 82),
        (152, 84, 178, 98),
        (184, 68, 210, 82),
        (184, 84, 210, 98),
        (216, 68, 243, 82),
        (216, 84, 243, 98),
    ]
    if not emissive:
        palette = [
            ((152, 68, 178, 82), (27, 23, 39, 255), (72, 42, 98, 255), (131, 64, 169, 255)),
            ((152, 84, 178, 98), (21, 21, 34, 255), (59, 38, 78, 255), (112, 55, 153, 255)),
            ((184, 68, 210, 82), (27, 23, 39, 255), (76, 44, 101, 255), (145, 68, 180, 255)),
            ((184, 84, 210, 98), (21, 21, 34, 255), (62, 39, 80, 255), (123, 58, 161, 255)),
            ((216, 68, 243, 82), (23, 21, 37, 255), (66, 40, 89, 255), (137, 64, 173, 255)),
            ((216, 84, 243, 98), (20, 20, 32, 255), (56, 36, 75, 255), (110, 54, 149, 255)),
        ]
        for (x1, y1, x2, y2), dark, violet, bright in palette:
            d.rectangle((x1, y1, x2, y2), fill=dark)
            d.polygon([(x1+2,y1+2),(x1+8,y1+1),(x1+14,y1+4),(x1+10,y1+8),(x1+3,y1+7)],
                      fill=violet)
            d.polygon([(x1+14,y1+4),(x1+21,y1+5),(x2-2,y1+8),(x2-5,y2-2),(x1+10,y1+8)],
                      fill=(43, 34, 58, 255))
            d.line([(x1+3,y1+2),(x1+8,y1+1),(x1+12,y1+4)],
                   fill=bright, width=1)
            d.line([(x1+15,y1+5),(x1+19,y1+8),(x2-3,y1+9)],
                   fill=(100, 62, 129, 255), width=1)
    else:
        cyan = (38, 207, 255, 255)
        violet = (171, 72, 255, 255)
        white = (216, 250, 255, 255)
        for x1, y1, x2, y2 in regions:
            d.line([(x1+2,y1+2),(x1+8,y1+1),(x1+12,y1+4)], fill=cyan, width=1)
            d.line([(x1+13,y1+5),(x1+17,y1+8),(x2-3,y1+9)], fill=violet, width=1)
            d.point((x1+9,y1+3), fill=white)
            d.point((x2-4,y2-3), fill=cyan)
    image.save(path, optimize=True)


paint_head_atlas(ASSETS / "textures/entity/mutagenkoloss.png", False)
paint_head_atlas(ASSETS / "textures/entity/mutagenkoloss_glow.png", True)

# Version is advanced only after all gameplay and visual patches have been applied.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.63.0",
                             "Aktueller Entwicklungsstand: 1.64.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.63\.0", r"1\.64\.0")
        updated = updated.replace("artifact must be version 1.63.0",
                                  "artifact must be version 1.64.0")
    updated = updated.replace(
        '"Version 1.63.0" in readme and "Version 1.62.0" in readme',
        '"Version 1.64.0" in readme and "Version 1.63.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.64.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.64.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.64.0 — Kopfpanzer des Kristallkolosses und Restgefahr-Signal

- **Mehr erkennbare Kopfpanzerung:** Vier kantige Brauen- und Wangenplatten ergänzen den Schädel. Die zusätzliche Geometrie sitzt auf dem beweglichen Kopf und folgt dessen Blickanimation.
- **Gezielte Kristallrisse:** Die dunklen violetten Platten erhalten schmale cyanfarbene und violette emissive Linien; das Glow-Atlas bleibt außerhalb der Risslinien transparent.
- **Neuer Relaismodus 5:** „Restgefahr nach Schutzmaßnahmen“ verrechnet die gemessene Feldstärke und gespeicherte Sirenen-/Stationswarnungen mit einem begrenzten Bereitschaftspuffer aus versorgten Sporenabwehrsendern und verbleibenden Resonanzdämpfer-Ladungen.
- **Redstone-fähige Diagnose:** Ein höherer Signalwert bedeutet höhere geschätzte Restgefahr. Die Zahl ist eine Bereichsdiagnose und ersetzt keine Prüfung tatsächlicher Schutzradien.
- **Qualitätssicherung:** Die Tests sichern den neuen Kopfpanzer in Haut- und Glow-Layer, die 96 Relais-Blockstates, die sechs Betriebsmodi und die Chunk-Sicherheit ab.

"""
if "## Version 1.64.0 — Kopfpanzer des Kristallkolosses und Restgefahr-Signal" not in readme:
    marker = "## Version 1.63.0 — Live-Feldstärke für das Containment-Relais"
    idx = readme.find(marker)
    if idx < 0:
        idx = readme.find("\n## ")
        if idx >= 0:
            idx += 1
        else:
            idx = len(readme)
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.64.0 — Kopfpanzerung des Kristallkolosses und integriertes Restgefahr-Relais.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus = [line for line in readme.splitlines() if line.startswith("## Aktueller Entwicklungsschritt — ")]
if focus:
    readme = readme.replace(focus[0], "## Aktueller Entwicklungsschritt — 1.64.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Crystal Colossus head armor and containment residual-threat relay generated for 1.64.0.")
