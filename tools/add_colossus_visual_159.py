#!/usr/bin/env python3
"""1.59.0 visual upgrade for the Crystal Colossus, applied after the 1.58.0 base generator."""
from pathlib import Path
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, msg):
    if not ok:
        raise SystemExit("Crystal Colossus 1.59: " + msg)


def patch(path, old, new, sentinel, label):
    src = path.read_text(encoding="utf-8")
    if sentinel in src:
        return
    n = src.count(old)
    require(n == 1, f"{label}: expected one anchor, found {n}")
    path.write_text(src.replace(old, new, 1), encoding="utf-8")


# A larger chest silhouette and side armour turn the body into a crystal-plated beast,
# with additional crystals on the head, shoulders and flanks.
neck = '''        body.addOrReplaceChild("neck",
                CubeListBuilder.create().texOffs(100, 0).addBox(-11.0F, -7.0F, -28.0F, 22.0F, 14.0F, 16.0F),
                PartPose.ZERO);'''
patch(MODEL, neck, neck + '''
        body.addOrReplaceChild("chest_core_mount",
                CubeListBuilder.create().texOffs(208, 128)
                        .addBox(-9.0F, -7.0F, -30.0F, 18.0F, 14.0F, 5.0F)
                        .texOffs(220, 128).addBox(-7.0F, -5.0F, -32.0F, 14.0F, 10.0F, 3.0F),
                PartPose.ZERO);
        body.addOrReplaceChild("chest_core",
                CubeListBuilder.create().texOffs(208, 146)
                        .addBox(-5.5F, -5.5F, -34.0F, 11.0F, 11.0F, 3.0F)
                        .texOffs(232, 146).addBox(-3.5F, -3.5F, -35.2F, 7.0F, 7.0F, 1.5F),
                PartPose.ZERO);
        body.addOrReplaceChild("armor_plate_left",
                CubeListBuilder.create().texOffs(152, 100)
                        .addBox(-6.0F, -5.0F, -11.0F, 6.0F, 12.0F, 24.0F),
                PartPose.offset(-16.0F, -2.0F, 0.0F));
        body.addOrReplaceChild("armor_plate_right",
                CubeListBuilder.create().texOffs(176, 100)
                        .addBox(0.0F, -5.0F, -11.0F, 6.0F, 12.0F, 24.0F),
                PartPose.offset(16.0F, -2.0F, 0.0F));
        addCrystal(body, "flank_crystal_left", 96, -18.0F, -1.0F, 17, -0.32F);
        addCrystal(body, "flank_crystal_right", 128, 18.0F, -1.0F, 17, 0.32F);''',
      '"chest_core_mount"', "chest core and flank armour")

horn = '''        head.addOrReplaceChild("horn_right",
                CubeListBuilder.create().texOffs(216, 0).addBox(-3.0F, -5.0F, -3.0F, 6.0F, 5.0F, 6.0F)
                        .texOffs(230, 0).addBox(-2.0F, -10.0F, -2.0F, 4.0F, 5.0F, 4.0F)
                        .texOffs(240, 0).addBox(-1.0F, -14.0F, -1.0F, 2.0F, 4.0F, 2.0F),
                PartPose.offsetAndRotation(7.5F, -2.0F, -4.0F, -0.25F, 0.0F, 0.38F));'''
patch(MODEL, horn, horn + '''
        head.addOrReplaceChild("jaw_armor",
                CubeListBuilder.create().texOffs(144, 52)
                        .addBox(-7.0F, 1.0F, -18.0F, 14.0F, 4.0F, 12.0F)
                        .texOffs(176, 100).addBox(-5.0F, 3.0F, -19.0F, 10.0F, 2.5F, 9.0F),
                PartPose.ZERO);
        addCrystal(head, "temple_crystal_left", 32, -9.0F, -5.0F, 13, -0.38F);
        addCrystal(head, "temple_crystal_right", 64, 9.0F, -5.0F, 13, 0.38F);''',
      '"temple_crystal_left"', "jaw and temple crystals")

shoulders = '''        body.addOrReplaceChild("shoulder_crystal_left",
                CubeListBuilder.create().texOffs(176, 100).addBox(-3.0F, -13.0F, -3.0F, 6.0F, 13.0F, 6.0F),
                PartPose.offsetAndRotation(-14.0F, -4.0F, -13.0F, 0.12F, 0.0F, -0.62F));
        body.addOrReplaceChild("shoulder_crystal_right",
                CubeListBuilder.create().texOffs(200, 100).addBox(-3.0F, -13.0F, -3.0F, 6.0F, 13.0F, 6.0F),
                PartPose.offsetAndRotation(14.0F, -4.0F, -13.0F, 0.12F, 0.0F, 0.62F));'''
patch(MODEL, shoulders, '''        addCrystal(body, "shoulder_crystal_left", 160, -15.0F, -13.0F, 19, -0.62F);
        addCrystal(body, "shoulder_crystal_right", 192, 15.0F, -13.0F, 19, 0.62F);''',
      'addCrystal(body, "shoulder_crystal_left"', "faceted shoulders")

# Give the tail three independent joints rather than one rigid rod.
patch(MODEL, '    private final ModelPart tail;\n    private final ModelPart tailTip;',
      '    private final ModelPart tail;\n    private final ModelPart tailMid;\n    private final ModelPart tailTip;',
      'private final ModelPart tailMid;', "tail field")
patch(MODEL, '        this.tail = body.getChild("tail");\n        this.tailTip = tail.getChild("tail_tip");',
      '        this.tail = body.getChild("tail");\n        this.tailMid = tail.getChild("tail_mid");\n        this.tailTip = tailMid.getChild("tail_tip");',
      'this.tailMid = tail.getChild("tail_mid");', "tail references")
old_tail = '''        PartDefinition tail = body.addOrReplaceChild("tail",
                CubeListBuilder.create().texOffs(0, 140).addBox(-7.0F, -6.0F, 0.0F, 14.0F, 12.0F, 18.0F),
                PartPose.offset(0.0F, 1.0F, 18.0F));
        tail.addOrReplaceChild("tail_tip",
                CubeListBuilder.create().texOffs(64, 140).addBox(-5.0F, -4.0F, 0.0F, 10.0F, 8.0F, 17.0F)
                        .texOffs(104, 140).addBox(-3.0F, -2.0F, 14.0F, 6.0F, 4.0F, 8.0F),
                PartPose.offset(0.0F, 0.0F, 16.0F));'''
new_tail = '''        PartDefinition tail = body.addOrReplaceChild("tail",
                CubeListBuilder.create().texOffs(0, 140)
                        .addBox(-8.0F, -6.0F, 0.0F, 16.0F, 12.0F, 20.0F)
                        .texOffs(48, 140).addBox(-8.5F, -4.5F, 3.0F, 17.0F, 9.0F, 14.0F),
                PartPose.offset(0.0F, 0.5F, 18.0F));
        PartDefinition tailMid = tail.addOrReplaceChild("tail_mid",
                CubeListBuilder.create().texOffs(80, 140)
                        .addBox(-6.0F, -4.8F, 0.0F, 12.0F, 9.6F, 18.0F),
                PartPose.offset(0.0F, 0.0F, 17.0F));
        PartDefinition tailTip = tailMid.addOrReplaceChild("tail_tip",
                CubeListBuilder.create().texOffs(128, 140)
                        .addBox(-4.4F, -3.5F, 0.0F, 8.8F, 7.0F, 16.0F)
                        .texOffs(160, 140).addBox(-2.5F, -2.2F, 13.0F, 5.0F, 4.4F, 10.0F),
                PartPose.offset(0.0F, 0.0F, 14.0F));
        addCrystal(tail, "tail_spine_0", 0, 0.0F, 5.0F, 15, -0.12F);
        addCrystal(tailMid, "tail_spine_1", 96, 0.0F, 5.0F, 13, 0.08F);
        addCrystal(tailTip, "tail_spine_2", 192, 0.0F, 4.0F, 10, 0.0F);'''
patch(MODEL, old_tail, new_tail, 'PartDefinition tailMid = tail.addOrReplaceChild("tail_mid"',
      "segmented tail geometry")
patch(MODEL, '''        this.tail.xRot = Mth.sin(ageInTicks * 0.06F) * 0.08F;
        this.tail.yRot = Mth.sin(ageInTicks * 0.045F) * 0.12F;
        this.tail.zRot = 0.0F;
        this.tailTip.xRot = Mth.sin(ageInTicks * 0.08F) * 0.09F;
        this.tailTip.yRot = Mth.sin(ageInTicks * 0.065F + 0.7F) * 0.16F;
        this.tailTip.zRot = 0.0F;''',
      '''        this.tail.xRot = Mth.sin(ageInTicks * 0.06F) * 0.055F;
        this.tail.yRot = Mth.sin(ageInTicks * 0.045F) * 0.10F;
        this.tail.zRot = 0.0F;
        this.tailMid.xRot = Mth.sin(ageInTicks * 0.075F + 0.4F) * 0.09F;
        this.tailMid.yRot = Mth.sin(ageInTicks * 0.065F + 0.8F) * 0.18F;
        this.tailMid.zRot = 0.0F;
        this.tailTip.xRot = Mth.sin(ageInTicks * 0.10F + 0.8F) * 0.13F;
        this.tailTip.yRot = Mth.sin(ageInTicks * 0.085F + 1.1F) * 0.23F;
        this.tailTip.zRot = 0.0F;''',
      "this.tailMid.xRot", "animated tail")
patch(MODEL, 'this.tailTip.yRot += Mth.sin(ageInTicks * 0.22F) * 0.08F;',
      'this.tailMid.yRot += Mth.sin(ageInTicks * 0.18F) * 0.07F;\n            this.tailTip.yRot += Mth.sin(ageInTicks * 0.22F) * 0.12F;',
      'this.tailTip.yRot += Mth.sin(ageInTicks * 0.22F) * 0.12F;', "tail recoil during breath")

# Build the glow geometry around the same model hierarchy and positions.
glow_mouth = '''        head.addOrReplaceChild("mouth_glow",
                CubeListBuilder.create().texOffs(200, 44).addBox(-4.0F, 2.5F, -17.8F, 8.0F, 1.2F, 1.0F),
                PartPose.ZERO);'''
patch(MODEL, glow_mouth, glow_mouth + '''
        addGlowCrystal(head, "temple_crystal_left", 32, -9.0F, -5.0F, 13, -0.38F);
        addGlowCrystal(head, "temple_crystal_right", 64, 9.0F, -5.0F, 13, 0.38F);''',
      'addGlowCrystal(head, "temple_crystal_left"', "glow temple crystals")
old_glow_tail = '''        PartDefinition tail = body.addOrReplaceChild("tail", CubeListBuilder.create(), PartPose.offset(0.0F, 1.0F, 18.0F));
        tail.addOrReplaceChild("tail_tip", CubeListBuilder.create().texOffs(224, 44)
                .addBox(-1.5F, -3.0F, 1.0F, 3.0F, 6.0F, 17.0F), PartPose.offset(0.0F, 0.0F, 16.0F));'''
new_glow_tail = '''        PartDefinition tail = body.addOrReplaceChild("tail", CubeListBuilder.create(), PartPose.offset(0.0F, 0.5F, 18.0F));
        PartDefinition tailMid = tail.addOrReplaceChild("tail_mid", CubeListBuilder.create(), PartPose.offset(0.0F, 0.0F, 17.0F));
        PartDefinition tailTip = tailMid.addOrReplaceChild("tail_tip", CubeListBuilder.create(), PartPose.offset(0.0F, 0.0F, 14.0F));
        addGlowCrystal(tail, "tail_spine_0", 0, 0.0F, 5.0F, 15, -0.12F);
        addGlowCrystal(tailMid, "tail_spine_1", 96, 0.0F, 5.0F, 13, 0.08F);
        addGlowCrystal(tailTip, "tail_spine_2", 192, 0.0F, 4.0F, 10, 0.0F);
        tail.addOrReplaceChild("tail_vein", CubeListBuilder.create().texOffs(208, 80)
                .addBox(-1.6F, -1.0F, 1.0F, 3.2F, 2.0F, 16.0F), PartPose.ZERO);
        tailMid.addOrReplaceChild("tail_mid_vein", CubeListBuilder.create().texOffs(208, 80)
                .addBox(-1.2F, -0.8F, 1.0F, 2.4F, 1.6F, 14.0F), PartPose.ZERO);
        tailTip.addOrReplaceChild("tail_tip_vein", CubeListBuilder.create().texOffs(208, 80)
                .addBox(-0.9F, -0.6F, 1.0F, 1.8F, 1.2F, 12.0F), PartPose.ZERO);'''
patch(MODEL, old_glow_tail, new_glow_tail,
      'PartDefinition tailMid = tail.addOrReplaceChild("tail_mid", CubeListBuilder.create()',
      "glow tail hierarchy")

old_core_glow = '''        body.addOrReplaceChild("core_glow",
                CubeListBuilder.create().texOffs(200, 0).addBox(-6.5F, -6.0F, -27.2F, 13.0F, 12.0F, 2.5F),
                PartPose.ZERO);'''
new_core_glow = '''        body.addOrReplaceChild("core_glow",
                CubeListBuilder.create().texOffs(208, 128)
                        .addBox(-9.4F, -7.4F, -30.5F, 18.8F, 14.8F, 5.8F)
                        .texOffs(220, 128).addBox(-7.2F, -5.6F, -32.5F, 14.4F, 11.2F, 3.6F)
                        .texOffs(208, 146).addBox(-5.8F, -5.8F, -34.7F, 11.6F, 11.6F, 3.4F)
                        .texOffs(232, 146).addBox(-3.8F, -3.8F, -36.0F, 7.6F, 7.6F, 2.0F),
                PartPose.ZERO);
        addGlowCrystal(body, "flank_crystal_left", 96, -18.0F, -1.0F, 17, -0.32F);
        addGlowCrystal(body, "flank_crystal_right", 128, 18.0F, -1.0F, 17, 0.32F);
        addGlowCrystal(body, "shoulder_crystal_left", 160, -15.0F, -13.0F, 19, -0.62F);
        addGlowCrystal(body, "shoulder_crystal_right", 192, 15.0F, -13.0F, 19, 0.62F);
        body.addOrReplaceChild("armor_plate_left_glow", CubeListBuilder.create().texOffs(208, 80)
                .addBox(-1.8F, -3.0F, -8.0F, 1.8F, 8.0F, 22.0F), PartPose.offset(-20.0F, -2.0F, 0.0F));
        body.addOrReplaceChild("armor_plate_right_glow", CubeListBuilder.create().texOffs(208, 80)
                .addBox(0.0F, -3.0F, -8.0F, 1.8F, 8.0F, 22.0F), PartPose.offset(20.0F, -2.0F, 0.0F));'''
patch(MODEL, old_core_glow, new_core_glow, 'addGlowCrystal(body, "flank_crystal_left"',
      "glow core and flanks")

# Draw matching pixel-art colour work into the chest-core UV area of both generated atlases.
def paint_core(path, glow):
    image = Image.open(path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    draw.polygon([(208, 139), (218, 130), (236, 130), (248, 139), (253, 153),
                  (242, 166), (226, 172), (212, 164), (205, 152)],
                 fill=(71, 24, 180, 255) if glow else (39, 24, 67, 255))
    draw.polygon([(211, 142), (220, 135), (235, 135), (246, 142), (249, 153),
                  (239, 162), (226, 167), (216, 160), (210, 152)],
                 fill=(40, 166, 252, 255) if glow else (115, 48, 202, 255))
    draw.polygon([(217, 145), (225, 139), (235, 145), (239, 153),
                  (230, 161), (220, 156)],
                 fill=(91, 236, 255, 255) if glow else (37, 184, 241, 255))
    draw.polygon([(221, 146), (226, 142), (232, 146), (234, 152),
                  (229, 157), (223, 154)],
                 fill=(236, 255, 255, 255) if glow else (143, 250, 255, 255))
    draw.point((226, 148), fill=(255, 255, 255, 255))
    image.save(path, optimize=True)


paint_core(ASSETS / "textures/entity/mutagenkoloss.png", False)
paint_core(ASSETS / "textures/entity/mutagenkoloss_glow.png", True)

# Advance the generated mod and existing regression contracts.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.58.0",
                             "Aktueller Entwicklungsstand: 1.59.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.58\.0", r"1\.59\.0")
        updated = updated.replace("artifact must be version 1.58.0",
                                  "artifact must be version 1.59.0")
    updated = updated.replace(
        '"Version 1.58.0" in readme and "Version 1.57.0" in readme',
        '"Version 1.59.0" in readme and "Version 1.58.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.59.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Gradle artifact version to 1.59.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.59.0 — Brustkern, Kristallstirn und segmentierter Schwanz

- **Gewaltiger Brustkern:** Eine mehrlagige Kristallfassung mit violettem Rand, cyanfarbener Mitte und weißen Bruchlichtern sitzt sichtbar im vorderen Panzer. Die Full-Bright-Ebene folgt den Kernschichten.
- **Kristalle an Kopf und Schultern:** Facettierte Schläfen- und Schulterkristalle ergänzen die Rückenstacheln; seitliche Panzerplatten und Flankenkristalle verbreitern die Silhouette.
- **Dreiteiliger Schwanz:** Grundsegment, bewegliches Mittelteil und verjüngte Spitze erhalten drei zusätzliche Rückensteine und leuchtende Adern.
- **Bewegung mit Gewicht:** Mittelteil und Spitze bewegen sich zeitversetzt zum Schwanzansatz; während des Kristallatems wird der Schwanz stärker zurückgezogen.
- **Bosskampf bleibt erhalten:** Vier artikulierte Läufe, drei Klauen je Fuß, Boss-Angriffe, zweite Phase und Survival-Beschwörung bleiben erhalten.
- **Qualitätssicherung:** Neue Tests prüfen Schwanzhierarchie/-animation, Brustkern-Texturen, Seiten-/Schläfenkristalle und passende Leuchtgeometrie.

Der Forge-Build prüft Struktur, Ressourcen und Serverstart. Die tatsächliche Silhouette und Leuchtwirkung müssen weiterhin am Minecraft-Client visuell kontrolliert werden.

"""
if "## Version 1.59.0 — Brustkern, Kristallstirn und segmentierter Schwanz" not in readme:
    marker = "## Version 1.58.0 — Facettierte Kristallspitzen und korrektes Leucht-UV"
    idx = readme.find(marker)
    if idx < 0:
        idx = readme.find("\n## ")
        if idx >= 0:
            idx += 1
        else:
            idx = len(readme)
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.59.0 — leuchtender Brustkern, Schläfenkristalle und segmentierter Kristallschwanz.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus:
    readme = readme.replace(focus[0], "## Aktueller Schwerpunkt — 1.59.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Installed 1.59.0 Crystal Colossus chest core, temple/shoulder/flank crystals, articulated tail, and aligned glow layers.")
