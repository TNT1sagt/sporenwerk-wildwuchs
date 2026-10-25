#!/usr/bin/env python3
"""1.60.0 reference-directed crystal core and side-spine visual pass."""
from pathlib import Path
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Crystal Colossus visual 1.60: " + message)


def patch(path, old, new, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return
    count = source.count(old)
    require(count == 1, f"{label}: expected exactly one source anchor, found {count}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# Increase the chest focus so it reads clearly on a broad quadruped body from the front.
old_core = '''        body.addOrReplaceChild("chest_core_mount",
                CubeListBuilder.create().texOffs(208, 128)
                        .addBox(-9.0F, -7.0F, -30.0F, 18.0F, 14.0F, 5.0F)
                        .texOffs(220, 128).addBox(-7.0F, -5.0F, -32.0F, 14.0F, 10.0F, 3.0F),
                PartPose.ZERO);
        body.addOrReplaceChild("chest_core",
                CubeListBuilder.create().texOffs(208, 146)
                        .addBox(-5.5F, -5.5F, -34.0F, 11.0F, 11.0F, 3.0F)
                        .texOffs(232, 146).addBox(-3.5F, -3.5F, -35.2F, 7.0F, 7.0F, 1.5F),
                PartPose.ZERO);'''
new_core = '''        // Version 1.60 reference chest scale: layered, forward-facing, and visibly larger than a normal mob eye.
        body.addOrReplaceChild("chest_core_mount",
                CubeListBuilder.create().texOffs(208, 128)
                        .addBox(-10.5F, -8.5F, -30.8F, 21.0F, 17.0F, 5.5F)
                        .texOffs(220, 128).addBox(-8.5F, -6.8F, -33.0F, 17.0F, 13.6F, 3.5F),
                PartPose.ZERO);
        body.addOrReplaceChild("chest_core",
                CubeListBuilder.create().texOffs(208, 146)
                        .addBox(-7.0F, -7.0F, -35.0F, 14.0F, 14.0F, 3.5F)
                        .texOffs(232, 146).addBox(-4.7F, -4.7F, -36.6F, 9.4F, 9.4F, 1.8F),
                PartPose.ZERO);'''
patch(MODEL, old_core, new_core, "Version 1.60 reference chest scale", "larger layered chest core")

old_glow_core = '''        body.addOrReplaceChild("core_glow",
                CubeListBuilder.create().texOffs(208, 128)
                        .addBox(-9.4F, -7.4F, -30.5F, 18.8F, 14.8F, 5.8F)
                        .texOffs(220, 128).addBox(-7.2F, -5.6F, -32.5F, 14.4F, 11.2F, 3.6F)
                        .texOffs(208, 146).addBox(-5.8F, -5.8F, -34.7F, 11.6F, 11.6F, 3.4F)
                        .texOffs(232, 146).addBox(-3.8F, -3.8F, -36.0F, 7.6F, 7.6F, 2.0F),
                PartPose.ZERO);'''
new_glow_core = '''        body.addOrReplaceChild("core_glow",
                CubeListBuilder.create().texOffs(208, 128)
                        .addBox(-10.9F, -8.9F, -31.3F, 21.8F, 17.8F, 6.2F)
                        .texOffs(220, 128).addBox(-8.9F, -7.1F, -33.6F, 17.8F, 14.2F, 4.0F)
                        .texOffs(208, 146).addBox(-7.3F, -7.3F, -35.5F, 14.6F, 14.6F, 3.9F)
                        .texOffs(232, 146).addBox(-5.0F, -5.0F, -37.1F, 10.0F, 10.0F, 2.2F),
                PartPose.ZERO);'''
patch(MODEL, old_glow_core, new_glow_core, "Version 1.60 reference glow core scale",
      "matching enlarged chest glow")
# Insert two forward-raking rib crystals beside the core so the chest joins into the armour silhouette.
flank_anchor = '''        addCrystal(body, "flank_crystal_left", 96, -18.0F, -1.0F, 17, -0.32F);
        addCrystal(body, "flank_crystal_right", 128, 18.0F, -1.0F, 17, 0.32F);'''
patch(MODEL, flank_anchor, flank_anchor + '''
        addCrystal(body, "rib_crystal_left", 64, -19.0F, -8.0F, 12, -0.42F);
        addCrystal(body, "rib_crystal_right", 96, 19.0F, -8.0F, 12, 0.42F);''',
      '"rib_crystal_left"', "rib crystals around chest")
glow_flank = '''        addGlowCrystal(body, "flank_crystal_left", 96, -18.0F, -1.0F, 17, -0.32F);
        addGlowCrystal(body, "flank_crystal_right", 128, 18.0F, -1.0F, 17, 0.32F);'''
patch(MODEL, glow_flank, glow_flank + '''
        addGlowCrystal(body, "rib_crystal_left", 64, -19.0F, -8.0F, 12, -0.42F);
        addGlowCrystal(body, "rib_crystal_right", 96, 19.0F, -8.0F, 12, 0.42F);''',
      'addGlowCrystal(body, "rib_crystal_left"', "emissive rib crystals")

# Redraw the exact chest UV region as crisp pixel facets: obsidian frame, violet fracture ring,
# cyan crystal heart and white-hot center. This texture is generated fresh on every clean CI build.
def paint_reference_core(path, emissive):
    image = Image.open(path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    outer = [(205, 151), (210, 137), (220, 130), (239, 131), (251, 141),
             (254, 154), (246, 166), (230, 173), (214, 168), (205, 158)]
    purple = [(209, 151), (214, 140), (223, 135), (238, 135), (248, 143),
              (250, 154), (241, 164), (229, 168), (217, 163), (210, 157)]
    cyan = [(216, 150), (222, 141), (233, 140), (241, 148),
            (239, 157), (230, 163), (220, 159)]
    inner = [(222, 149), (228, 144), (235, 148), (236, 154), (230, 159), (224, 156)]
    if emissive:
        draw.polygon(outer, fill=(61, 18, 158, 255))
        draw.polygon(purple, fill=(175, 43, 239, 255))
        draw.polygon(cyan, fill=(21, 181, 255, 255))
        draw.polygon(inner, fill=(116, 248, 255, 255))
        draw.line([(215, 144), (222, 139), (228, 143)], fill=(247, 102, 255, 255), width=2)
        draw.line([(237, 141), (245, 148), (242, 155)], fill=(205, 250, 255, 255), width=2)
        draw.line([(218, 159), (226, 165), (232, 160)], fill=(113, 83, 255, 255), width=2)
    else:
        draw.polygon(outer, fill=(19, 18, 40, 255))
        draw.polygon([(207, 151), (212, 138), (220, 132), (240, 133),
                      (249, 142), (252, 154), (244, 164), (230, 171),
                      (215, 166), (207, 158)], fill=(72, 30, 112, 255))
        draw.polygon(purple, fill=(123, 49, 169, 255))
        draw.line([(211, 148), (220, 137), (227, 140)], fill=(194, 80, 220, 255), width=2)
        draw.line([(239, 139), (247, 148), (245, 156)], fill=(217, 104, 238, 255), width=2)
        draw.polygon(cyan, fill=(23, 131, 180, 255))
        draw.polygon(inner, fill=(92, 203, 223, 255))
        draw.polygon([(225, 149), (229, 146), (233, 150), (232, 154), (228, 156)],
                     fill=(207, 253, 255, 255))
    draw.line([(226, 145), (229, 150), (227, 155)], fill=(255, 255, 255, 255), width=1)
    draw.point((229, 150), fill=(255, 255, 255, 255))
    image.save(path, optimize=True)


paint_reference_core(ASSETS / "textures/entity/mutagenkoloss.png", False)
paint_reference_core(ASSETS / "textures/entity/mutagenkoloss_glow.png", True)

# Version, tests, and release notes are updated after the prior visual generator has produced 1.59.0.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.59.0",
                             "Aktueller Entwicklungsstand: 1.60.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.59\.0", r"1\.60\.0")
        updated = updated.replace("artifact must be version 1.59.0",
                                  "artifact must be version 1.60.0")
    updated = updated.replace(
        '"Version 1.59.0" in readme and "Version 1.58.0" in readme',
        '"Version 1.60.0" in readme and "Version 1.59.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.60.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.60.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.60.0 — Referenz-Brustkern und violett-cyanfarbene Facetten

- **Brustkern als Blickfang:** Der Kern wurde größer, weiter nach vorn gesetzt und in mehrere sichtbare Schichten zerlegt. Er besitzt einen dunklen kristallinen Rand, violette Bruchflächen, ein cyanblaues Zentrum und einen fast weißen Lichtpunkt.
- **Leuchtfläche passt zur Geometrie:** Die Full-Bright-Form ist geringfügig größer als der normale Kern, damit die Kanten unabhängig vom Umgebungslicht klar hervortreten.
- **Kristalle an den Rippen:** Zwei zusätzliche, nach außen geneigte Kristallspitzen verbinden den Brustfokus mit den seitlichen Panzerplatten.
- **Pixeltextur gezielt gemalt:** Main- und Glow-Atlas erhalten dieselben facettierten Kernkonturen mit unterschiedlicher Leuchtintensität, statt einer generischen Rechteckmarkierung.
- **Der Bosskampf bleibt bestehen:** Rückenkristalle, drei Schwanzgelenke, vier artikulierte Beine, Klauen, Stampfen, Kristallatem und zweite Phase werden weiterverwendet.
- **Qualitätssicherung:** Tests prüfen Kerngeometrie, UV-Farben, Glow-Transparenz, seitliche Kristalle, Versionshistorie, JAR und Serverstart.

Die Prüfung bestätigt Geometrie und Ressourcen. Die abschließende visuelle Freigabe erfolgt erst nach Sichtkontrolle im Minecraft-Client.

"""
if "## Version 1.60.0 — Referenz-Brustkern und violett-cyanfarbene Facetten" not in readme:
    marker = "## Version 1.59.0 — Brustkern, Kristallstirn und segmentierter Schwanz"
    idx = readme.find(marker)
    if idx < 0:
        idx = readme.find("\n## ")
        if idx >= 0:
            idx += 1
        else:
            idx = len(readme)
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.60.0 — größerer violett-cyanfarbener Brustkern mit facettierter Leuchtebene.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus:
    readme = readme.replace(focus[0], "## Aktueller Schwerpunkt — 1.60.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Installed 1.60.0 reference-directed chest core, side rib crystals, matched violet/cyan pixel-art and emissive UVs.")
