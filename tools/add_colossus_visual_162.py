#!/usr/bin/env python3
"""1.62.0 broadens the Crystal Colossus silhouette with layered armor and emissive seams."""
from pathlib import Path
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Colossus visual 1.62: " + message)


def patch(path, old, new, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return
    count = source.count(old)
    require(count == 1, f"{label}: expected exactly one source anchor, found {count}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# Angular, overlapping plates widen the front shoulders and rear quarters.
# Insert before the two layer returns rather than depending on the position of prior crystal patches.
def insert_before_layer_return(path, layer_index, addition, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return
    returns = list(re.finditer(r"(?m)^\s*return LayerDefinition\.create\(mesh, 256, 256\);", source))
    require(len(returns) >= layer_index + 1,
            f"{label}: could not find model layer return {layer_index + 1}")
    at = returns[layer_index].start()
    path.write_text(source[:at] + addition + "\n" + source[at:], encoding="utf-8")


main_armor = '''        body.addOrReplaceChild("shoulder_armor_left",
                CubeListBuilder.create().texOffs(32, 224).addBox(-4.0F, -3.0F, -7.0F, 9.0F, 4.0F, 13.0F)
                        .texOffs(80, 224).addBox(-5.0F, -5.0F, -5.0F, 9.0F, 3.0F, 10.0F)
                        .texOffs(120, 224).addBox(-3.0F, -7.0F, -3.0F, 6.0F, 3.0F, 6.0F),
                PartPose.offsetAndRotation(-14.0F, -4.0F, -13.0F, 0.08F, 0.0F, -0.18F));
        body.addOrReplaceChild("shoulder_armor_right",
                CubeListBuilder.create().texOffs(32, 224).addBox(-5.0F, -3.0F, -7.0F, 9.0F, 4.0F, 13.0F)
                        .texOffs(80, 224).addBox(-4.0F, -5.0F, -5.0F, 9.0F, 3.0F, 10.0F)
                        .texOffs(120, 224).addBox(-3.0F, -7.0F, -3.0F, 6.0F, 3.0F, 6.0F),
                PartPose.offsetAndRotation(14.0F, -4.0F, -13.0F, 0.08F, 0.0F, 0.18F));
        body.addOrReplaceChild("haunch_armor_left",
                CubeListBuilder.create().texOffs(0, 204).addBox(-4.0F, -3.0F, -7.0F, 8.0F, 4.0F, 14.0F)
                        .texOffs(48, 204).addBox(-6.0F, -5.0F, -5.0F, 8.0F, 3.0F, 10.0F)
                        .texOffs(96, 204).addBox(-4.0F, -7.0F, -3.0F, 6.0F, 3.0F, 6.0F),
                PartPose.offsetAndRotation(-15.0F, -3.0F, 10.0F, 0.0F, 0.0F, -0.10F));
        body.addOrReplaceChild("haunch_armor_right",
                CubeListBuilder.create().texOffs(0, 204).addBox(-4.0F, -3.0F, -7.0F, 8.0F, 4.0F, 14.0F)
                        .texOffs(48, 204).addBox(-2.0F, -5.0F, -5.0F, 8.0F, 3.0F, 10.0F)
                        .texOffs(96, 204).addBox(-2.0F, -7.0F, -3.0F, 6.0F, 3.0F, 6.0F),
                PartPose.offsetAndRotation(15.0F, -3.0F, 10.0F, 0.0F, 0.0F, 0.10F));'''
insert_before_layer_return(MODEL, 0, main_armor,
    'CubeListBuilder.create().texOffs(32, 224).addBox(-4.0F, -3.0F, -7.0F, 9.0F, 4.0F, 13.0F)',
    "main armor silhouette")

glow_armor = '''        body.addOrReplaceChild("shoulder_armor_left",
                CubeListBuilder.create().texOffs(32, 224).addBox(-4.15F, -3.1F, -7.1F, 9.3F, 4.2F, 13.2F)
                        .texOffs(80, 224).addBox(-5.1F, -5.1F, -5.1F, 9.2F, 3.1F, 10.2F)
                        .texOffs(120, 224).addBox(-3.1F, -7.1F, -3.1F, 6.2F, 3.1F, 6.2F),
                PartPose.offsetAndRotation(-14.0F, -4.0F, -13.0F, 0.08F, 0.0F, -0.18F));
        body.addOrReplaceChild("shoulder_armor_right",
                CubeListBuilder.create().texOffs(32, 224).addBox(-5.15F, -3.1F, -7.1F, 9.3F, 4.2F, 13.2F)
                        .texOffs(80, 224).addBox(-4.1F, -5.1F, -5.1F, 9.2F, 3.1F, 10.2F)
                        .texOffs(120, 224).addBox(-3.1F, -7.1F, -3.1F, 6.2F, 3.1F, 6.2F),
                PartPose.offsetAndRotation(14.0F, -4.0F, -13.0F, 0.08F, 0.0F, 0.18F));
        body.addOrReplaceChild("haunch_armor_left",
                CubeListBuilder.create().texOffs(0, 204).addBox(-4.1F, -3.1F, -7.1F, 8.2F, 4.2F, 14.2F)
                        .texOffs(48, 204).addBox(-6.1F, -5.1F, -5.1F, 8.2F, 3.1F, 10.2F)
                        .texOffs(96, 204).addBox(-4.1F, -7.1F, -3.1F, 6.2F, 3.1F, 6.2F),
                PartPose.offsetAndRotation(-15.0F, -3.0F, 10.0F, 0.0F, 0.0F, -0.10F));
        body.addOrReplaceChild("haunch_armor_right",
                CubeListBuilder.create().texOffs(0, 204).addBox(-4.1F, -3.1F, -7.1F, 8.2F, 4.2F, 14.2F)
                        .texOffs(48, 204).addBox(-2.1F, -5.1F, -5.1F, 8.2F, 3.1F, 10.2F)
                        .texOffs(96, 204).addBox(-2.1F, -7.1F, -3.1F, 6.2F, 3.1F, 6.2F),
                PartPose.offsetAndRotation(15.0F, -3.0F, 10.0F, 0.0F, 0.0F, 0.10F));'''
insert_before_layer_return(MODEL, 1, glow_armor,
    'CubeListBuilder.create().texOffs(32, 224).addBox(-4.15F, -3.1F, -7.1F, 9.3F, 4.2F, 13.2F)',
    "emissive armor layer")

# Keep armor articulation subtle; the broad plates should follow the living body without wobbling.
field_anchor = '''    private final ModelPart shoulderCrystalRight;'''
field_new = '''    private final ModelPart shoulderCrystalRight;
    private final ModelPart shoulderArmorLeft;
    private final ModelPart shoulderArmorRight;
    private final ModelPart haunchArmorLeft;
    private final ModelPart haunchArmorRight;'''
patch(MODEL, field_anchor, field_new, "private final ModelPart shoulderArmorLeft;", "armor animation fields")

ctor_anchor = '''        this.shoulderCrystalRight = body.hasChild("shoulder_crystal_right") ? body.getChild("shoulder_crystal_right") : null;'''
ctor_new = ctor_anchor + '''
        this.shoulderArmorLeft = body.hasChild("shoulder_armor_left") ? body.getChild("shoulder_armor_left") : null;
        this.shoulderArmorRight = body.hasChild("shoulder_armor_right") ? body.getChild("shoulder_armor_right") : null;
        this.haunchArmorLeft = body.hasChild("haunch_armor_left") ? body.getChild("haunch_armor_left") : null;
        this.haunchArmorRight = body.hasChild("haunch_armor_right") ? body.getChild("haunch_armor_right") : null;'''
patch(MODEL, ctor_anchor, ctor_new, "this.shoulderArmorLeft =", "armor model references")

anim_anchor = '''        if (this.shoulderCrystalRight != null) {
            this.shoulderCrystalRight.zRot = 0.62F - ribSway;
        }'''
anim_new = anim_anchor + '''

        float armorShift = Mth.sin(ageInTicks * 0.048F) * 0.014F;
        if (this.shoulderArmorLeft != null) {
            this.shoulderArmorLeft.zRot = -0.18F + armorShift;
            this.shoulderArmorLeft.yRot = Mth.sin(ageInTicks * 0.035F) * 0.012F;
        }
        if (this.shoulderArmorRight != null) {
            this.shoulderArmorRight.zRot = 0.18F - armorShift;
            this.shoulderArmorRight.yRot = -Mth.sin(ageInTicks * 0.035F) * 0.012F;
        }
        if (this.haunchArmorLeft != null) {
            this.haunchArmorLeft.zRot = -0.10F + armorShift * 0.55F;
        }
        if (this.haunchArmorRight != null) {
            this.haunchArmorRight.zRot = 0.10F - armorShift * 0.55F;
        }'''
patch(MODEL, anim_anchor, anim_new, "float armorShift = Mth.sin", "armor articulation")

def paint_armor_atlas(path, emissive):
    image = Image.open(path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    if not emissive:
        # Shoulder plates: black-violet stone, stepped planes, and thin fracture highlights.
        draw.rectangle((32, 224, 75, 242), fill=(22, 21, 36, 255))
        draw.polygon([(34, 226), (42, 224), (59, 225), (72, 231), (67, 237),
                      (54, 241), (38, 238)], fill=(47, 37, 66, 255))
        draw.polygon([(37, 228), (45, 226), (53, 230), (48, 235), (39, 234)],
                     fill=(73, 46, 101, 255))
        draw.line([(55, 227), (60, 231), (66, 232), (62, 237)], fill=(135, 67, 174, 255), width=2)
        draw.line([(37, 237), (45, 239), (51, 236)], fill=(91, 52, 131, 255), width=1)

        draw.rectangle((80, 224, 118, 241), fill=(18, 18, 31, 255))
        draw.polygon([(82, 226), (92, 224), (113, 226), (116, 232), (108, 238),
                      (91, 239), (83, 234)], fill=(51, 39, 72, 255))
        draw.polygon([(86, 228), (94, 226), (101, 230), (96, 235), (87, 233)],
                     fill=(91, 47, 122, 255))
        draw.line([(101, 226), (105, 231), (112, 233)], fill=(150, 71, 185, 255), width=2)

        draw.rectangle((120, 224, 148, 240), fill=(24, 22, 39, 255))
        draw.polygon([(122, 226), (130, 224), (144, 228), (145, 234), (135, 239),
                      (124, 235)], fill=(71, 43, 93, 255))
        draw.line([(129, 227), (134, 231), (141, 232)], fill=(170, 86, 203, 255), width=2)

        # Hind-quarter plates are wider and darker to make the rear mass read as armored.
        draw.rectangle((0, 204, 45, 222), fill=(21, 20, 34, 255))
        draw.polygon([(2, 207), (11, 204), (34, 205), (43, 211), (39, 218),
                      (24, 221), (7, 217)], fill=(48, 38, 63, 255))
        draw.polygon([(5, 208), (14, 207), (23, 211), (19, 216), (7, 214)],
                     fill=(68, 43, 92, 255))
        draw.line([(25, 207), (29, 212), (38, 214), (33, 219)], fill=(131, 67, 168, 255), width=2)

        draw.rectangle((48, 204, 93, 222), fill=(19, 18, 31, 255))
        draw.polygon([(50, 207), (60, 204), (82, 206), (91, 211), (87, 218),
                      (70, 221), (53, 217)], fill=(45, 35, 60, 255))
        draw.polygon([(54, 208), (63, 207), (71, 211), (66, 216), (55, 215)],
                     fill=(75, 45, 99, 255))
        draw.line([(73, 207), (78, 212), (86, 214)], fill=(138, 69, 173, 255), width=2)

        draw.rectangle((96, 204, 126, 220), fill=(23, 21, 37, 255))
        draw.polygon([(98, 207), (107, 204), (121, 208), (123, 214), (113, 219),
                      (100, 216)], fill=(66, 42, 88, 255))
        draw.line([(106, 207), (111, 211), (119, 213)], fill=(157, 77, 190, 255), width=2)
    else:
        # Mostly transparent emissive atlas: narrow cyan edge-light, violet fractures, white glints.
        cyan = (45, 207, 255, 255)
        cyan_soft = (70, 161, 255, 255)
        violet = (151, 70, 255, 255)
        white = (214, 250, 255, 255)
        draw.line([(34, 225), (45, 225), (52, 228), (65, 229), (72, 233)], fill=cyan, width=2)
        draw.line([(36, 238), (47, 240), (54, 237), (62, 237), (67, 234)], fill=violet, width=1)
        draw.line([(57, 228), (61, 232), (66, 232)], fill=white, width=1)

        draw.line([(82, 225), (94, 225), (102, 228), (114, 229)], fill=cyan_soft, width=2)
        draw.line([(85, 236), (95, 238), (104, 235), (111, 234)], fill=violet, width=1)
        draw.point((104, 229), fill=white)

        draw.line([(122, 225), (132, 225), (141, 229)], fill=cyan, width=2)
        draw.line([(126, 235), (134, 237), (142, 233)], fill=violet, width=1)
        draw.point((137, 230), fill=white)

        draw.line([(2, 205), (14, 205), (24, 208), (39, 211)], fill=cyan_soft, width=2)
        draw.line([(5, 216), (17, 219), (28, 217), (36, 215)], fill=violet, width=1)
        draw.line([(28, 208), (32, 213), (38, 214)], fill=white, width=1)

        draw.line([(50, 205), (64, 205), (75, 208), (88, 211)], fill=cyan, width=2)
        draw.line([(53, 216), (65, 219), (76, 217), (86, 214)], fill=violet, width=1)
        draw.point((77, 209), fill=white)

        draw.line([(98, 205), (108, 205), (118, 209)], fill=cyan_soft, width=2)
        draw.line([(101, 215), (111, 218), (121, 214)], fill=violet, width=1)
        draw.point((114, 210), fill=white)
    image.save(path, optimize=True)


paint_armor_atlas(ASSETS / "textures/entity/mutagenkoloss.png", False)
paint_armor_atlas(ASSETS / "textures/entity/mutagenkoloss_glow.png", True)

# Promote version assertions to 1.62.0 after all prior visual patches are applied.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.61.0",
                             "Aktueller Entwicklungsstand: 1.62.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.61\.0", r"1\.62\.0")
        updated = updated.replace("artifact must be version 1.61.0",
                                  "artifact must be version 1.62.0")
    updated = updated.replace(
        '"Version 1.61.0" in readme and "Version 1.60.0" in readme',
        '"Version 1.62.0" in readme and "Version 1.61.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.62.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.62.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.62.0 — Panzerplatten für Schulter und Hinterhand

- **Silhouette statt bloßer Dekoration:** Vier neue, mehrlagige Panzergruppen verbreitern Schultern und Hinterhand. Jede Gruppe besteht aus drei versetzten Ebenen, damit die Rüstung wie gewachsene, kantige Kristallplatten wirkt.
- **Dunkles Violett statt Leuchtblock:** Die neue 256×256-Pixeltextur nutzt kohlschwarze Flächen, violette Facetten und pixelige Bruchkanten. Die Platten bleiben dunkel und passen zur schweren Kreatur.
- **Gezielte Full-Bright-Kanten:** Eine separate, transparente Glow-Textur fügt cyanfarbene Kanten und violette Risse hinzu; sie leuchtet nur an den Linien statt die komplette Panzerung flach auszuleuchten.
- **Bewegung im Körper:** Schulterplatten und Hinterhand reagieren mit kleiner Gegenbewegung auf die Idle-Animation. Die vorhandenen Attacken, Werte und Beschwörung bleiben unverändert.
- **Regressionen:** Neue Prüfungen sichern die vier Plattengruppen in Skin- und Glow-Layer, UV-Bereiche, Texturfarben, Glow-Transparenz und Versionskette ab.

Die tatsächliche Ähnlichkeit muss weiterhin anhand eines Screenshots im Minecraft-Client beurteilt werden; ein erfolgreicher Build allein belegt keine perfekte visuelle Übereinstimmung.

"""
if "## Version 1.62.0 — Panzerplatten für Schulter und Hinterhand" not in readme:
    marker = "## Version 1.61.0 — Pulsierender Kristallkern und resonierende Kristallrüstung"
    idx = readme.find(marker)
    if idx < 0:
        idx = readme.find("\n## ")
        if idx >= 0:
            idx += 1
        else:
            idx = len(readme)
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.62.0 — dunkle, mehrlagige Schulter- und Hinterhandpanzerung mit cyan-violetten Leuchtkanten.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus:
    readme = readme.replace(focus[0], "## Aktueller Schwerpunkt — 1.62.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Crystal Colossus armor silhouette 1.62.0 applied.")
