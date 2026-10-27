#!/usr/bin/env python3
"""1.114: remove massive opaque base volumes hiding the detailed silhouette.

The 1.113 shoulder mantles and living crystal parts cannot be distinguished
while the original giant internal 3D body, two bulky crystal sleeves and a
wide horizontal bark chest *still fill their gaps*. This is a subtractive
retopology in the real Minecraft ModelPart geometry, not more add-on props.
Keep all animated bones, attack states, selective pixels and 1.20.1 APIs.
"""
from pathlib import Path
from PIL import Image
import re,sys

R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(ok,reason):
    if not ok:raise SystemExit("1.114 original Minecraft silhouette retopology: "+reason)
def replace(path,old,new,why,n=1):
    source=path.read_text(encoding="utf-8")
    need(source.count(old)==n,why+": found "+str(source.count(old))+" anchors, wanted "+str(n))
    path.write_text(source.replace(old,new,n),encoding="utf-8")

# COLOSSUS: the last three releases added physically distinct flanking
# basalt armor, but the original giant car-shaped chassis still occluded its
# negative space when viewed from an oblique camera angle. Make the *actual
# support body* slimmer, and let the four matte new plate parts define width.
B=C/"MutagenkolossModel.java"
b=B.read_text(encoding="utf-8")
need('addSegmentedBeastMantle(body, false);' in b
     and 'addSegmentedBeastMantle(body, true);' in b
     and 'paw.y = 12.0F - lift * 1.65F;' in b
     and 'this.tailTip.xRot += 0.14F;' in b,
     "requires 1.113 mantle, four grounded legs and live scorpion tail")
for old,new,why in (
    ("addBox(-17.5F, -9.5F, -23.0F, 35.0F, 10.5F, 23.0F)",
     "addBox(-12.5F, -9.5F, -23.0F, 25.0F, 10.5F, 23.0F)",
     "narrow inner shoulder support so separated plates read from outside"),
    ("addBox(-12.0F, -1.0F, -19.5F, 24.0F, 11.0F, 24.0F)",
     "addBox(-8.5F, -1.0F, -19.5F, 17.0F, 11.0F, 24.0F)",
     "pinched actual waist instead of continuous rock box"),
    ("addBox(-14.0F, -8.5F, 8.5F, 28.0F, 11.0F, 16.0F)",
     "addBox(-10.5F, -8.5F, 8.5F, 21.0F, 11.0F, 16.0F)",
     "shrink the unseen core under rear flank shells"),
    ("addBox(-8.5F, -1.5F, 4.0F, 17.0F, 7.0F, 6.5F)",
     "addBox(-5.5F, -1.5F, 4.0F, 11.0F, 7.0F, 6.5F)",
     "thin spine bridge, retain front-to-back body continuity"),
):
    replace(B,old,new,why)
# CRYSTAL STALKER: both 7.6-wide sleeves were creating a superhero/zombie
# shoulder silhouette even though the arms and chest are narrow. Replace
# the *old* solid shoulder guards, not the claws that depend on their pivots,
# with separated slim crystal ridges and a narrow lower wrist brace.
P=C/"KristallpirscherModel.java"
p=P.read_text(encoding="utf-8")
need('head.addOrReplaceChild("face_mandible_left"' in p
     and 'head.addOrReplaceChild("face_mandible_right"' in p
     and 'leg.addOrReplaceChild("crystal_hock"' in p
     and 'this.leftArm.xRot = 0.24F + quietStride * 0.17F;' in p,
     "requires new face/leg and neutral arm rigs")
replace(P,
"""CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-3.25F, -3.8F, -2.65F, 6.5F, 3.8F, 5.3F)
                        .texOffs(64, 48).addBox(-2.35F, 1.05F, -2.3F, 4.7F, 2.8F, 4.6F)
                        .texOffs(96, 48).addBox(-1.55F, 5.0F, -3.15F, 3.1F, 4.9F, 2.8F),""",
"""CubeListBuilder.create().texOffs(64, 48)
                        // Two exposed mineral ulna/radius ridges with actual
                        // air between them, not a single wide cubic sleeve.
                        .addBox(-3.1F, -3.0F, -2.8F, 2.1F, 8.5F, 3.7F)
                        .texOffs(64, 48)
                        .addBox(1.0F, -2.7F, -2.8F, 2.1F, 8.2F, 3.7F)
                        .texOffs(96, 48)
                        .addBox(-1.5F, 3.5F, -3.6F, 3.0F, 7.8F, 2.8F),""",
"cut away the giant solid Pirscher shoulder sleeves")
# DÄMMERLING: three wide 10/9/6 bars still read as a square chest.
# Shorten just the crossbars; retain the existing air gap and the genuine
# independently animated six root branches attached to body ribs.
D=C/"DaemmerlingModel.java"
d=D.read_text(encoding="utf-8")
need('body.addOrReplaceChild("hollow_chest"' in d
     and 'addOrReplaceChild("waist_root_left"' in d
     and 'addOrReplaceChild("waist_root_right"' in d
     and 'this.leftRibRoot.zRot' in d
     and 'this.rightRibRoot.zRot' in d,
     "need open chest and attached moving 1.113 lower roots")
replace(D,
    "addBox(-5.2F,-5.0F,-2.6F,10.4F,2.7F,5.2F)",
    "addBox(-3.7F,-5.0F,-2.6F,7.4F,2.7F,5.2F)",
    "thin the dark horror upper ribs")
replace(D,
    "addBox(-4.5F,0.0F,-2.4F,9.0F,2.0F,4.8F)",
    "addBox(-3.5F,0.0F,-2.4F,7.0F,2.0F,4.8F)",
    "thin the center of open rib cage")
# Keep all old regression checks *running*. Only their exact geometry
# coordinates are updated to match the now deliberately reduced voxels.
for path, pairs in (
    ("tools/test_client_silhouette_rebuild_110.py",(
        ("addBox(-17.5F, -9.5F, -23.0F, 35.0F, 10.5F, 23.0F)",
         "addBox(-12.5F, -9.5F, -23.0F, 25.0F, 10.5F, 23.0F)"),
        ("addBox(-14.0F, -8.5F, 8.5F, 28.0F, 11.0F, 16.0F)",
         "addBox(-10.5F, -8.5F, 8.5F, 21.0F, 11.0F, 16.0F)"),
    )),
    ("tools/test_reference_base_silhouettes_105.py",(
        ("addBox(-5.2F,-5.0F,-2.6F,10.4F,2.7F,5.2F)",
         "addBox(-3.7F,-5.0F,-2.6F,7.4F,2.7F,5.2F)"),
        ("addBox(-4.5F,0.0F,-2.4F,9.0F,2.0F,4.8F)",
         "addBox(-3.5F,0.0F,-2.4F,7.0F,2.0F,4.8F)"),
    )),
):
    file=R/path
    source=file.read_text(encoding="utf-8")
    for old,new in pairs:
        need(source.count(old)==1,"existing pinned historical box "+path+" "+old)
        source=source.replace(old,new,1)
    file.write_text(source,encoding="utf-8")

T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for creature,pixels in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(creature+suffix+".png")) as im:
            need(im.size==(pixels,pixels),"valid original Minecraft texels "+creature+suffix)

for test in (R/"tools").glob("test_*.py"):
    if test.name=="test_original_silhouette_cleanup_114.py":continue
    s=test.read_text(encoding="utf-8")
    t=s.replace("Aktueller Entwicklungsstand: 1.113.0","Aktueller Entwicklungsstand: 1.114.0")
    if "build.gradle" in s:
        t=t.replace(r"1\.113\.0",r"1\.114\.0").replace(
            "artifact must be version 1.113.0","artifact must be version 1.114.0")
    t=t.replace('"Version 1.113.0" in readme and "Version 1.112.0" in readme',
                '"Version 1.114.0" in readme and "Version 1.113.0" in readme')
    if t!=s:test.write_text(t,encoding="utf-8")
g=R/"build.gradle"
s,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.114.0'",g.read_text(encoding="utf-8"),count=1)
need(n==1,"single ForgeGradle release")
g.write_text(s,encoding="utf-8")
f=R/"README.md";s=f.read_text(encoding="utf-8")
s,n=re.subn(r"\*\*Aktueller Entwicklungsstand: 1\.113\.0[^\n]*\*\*",
            "**Aktueller Entwicklungsstand: 1.114.0 — Weniger Blockkörper: echter schmaler Basaltkern, offene Kristallarme, dünne Wurzelrippen.**",s,count=1)
need(n==1,"previous 1.113 heading")
section="""## Aktueller Entwicklungsschritt — 1.114.0

- **Weniger aufgesetzte Deko, mehr ehrliche Geometrie:** Die Client-Bilder hatten einen blockigen Koloss und Zombie-Silhouetten gezeigt. 1.113 hatte zwar neue Panzer hinzugefügt, aber breite ursprüngliche Basismassen ließen sie noch im Kasten verschwinden. Die alten Basisquader sind jetzt verkleinert statt einfach mit noch mehr Details überdeckt.
- **Koloss:** Der echte Kernrumpf wurde quer von 35 auf 25 Modellpixel an der Schulter, von 24 auf 17 an der Taille und von 28 auf 21 am Hinterkörper reduziert. Vier dunkle, freistehende Basaltpanzer aus 1.113 und vier bodennahe Beine definieren jetzt die Breite; ein schmaler Wirbelsäulenverbinder erhält die körperliche Einheit. Gesicht, Brustiris, Endstachel und selektive Leuchteffekte bleiben erhalten.
- **Kristallpirscher:** Der ursprüngliche, klotzige 7.6-Pixel-breite Kristallärmel des Zombie-Arms ist entfernt. An seiner Stelle liegen zwei schmale, voneinander getrennte mineralische Knochenleisten mit 2 Pixel Luftspalt und schmaler Handgelenkspanzerung. Die zwei animierten Krallen je Arm, die Kopfmaske, die Jagdpose und die gebogenen Beine bleiben an ihren Knoten.
- **Dämmerling:** Die oberen und mittleren dunklen Rippenbalken der tatsächlich offenen Brust wurden von 10.4/9.0 auf 7.4/7.0 Pixel verschmälert; Wurzelrippen, Taille, Wurzelklauen und Farmhorror-Verhalten bleiben erhalten. Der sichtbare Hohlraum bleibt physisch offen.
- **Regressionen nicht deaktiviert:** Die beiden älteren Quellgeometrieprüfungen für 1.105 und 1.110 wurden auf die neuen absichtlich kleineren Quader angepasst; alle alten Animation-, Boss-, Gameplay- und Serverregeln bleiben aktiv. Ein neuer Regressionstest vermisst die verkleinerten Querschnitte und die offenen Arme.
- **Ingame-Bildprüfung fehlt noch:** Diese Quelltext-/Bauprüfung sagt nicht, dass das originale Referenzbild bereits exakt getroffen wird. Dafür werden wieder Screenshots aus Front, Profil und Dreiviertelansicht benötigt.

"""
need("## Aktueller Entwicklungsschritt — 1.113.0" in s,"previous dev section")
s=s.replace("## Aktueller Entwicklungsschritt — 1.113.0",
            section+"## Aktueller Entwicklungsschritt — 1.113.0",1)
release="""## Version 1.114.0 — Subtraktiver Mesh-Umbau statt weitere Deko

- Vier massive Chassis-Körperteile des Kolosses erheblich schmaler; die vorher gebauten getrennten Basaltmantel-Schalen bestimmen jetzt die Kontur.
- Kristallpirscher: alte würfelförmige massive Armguards durch zwei echte, 2 Pixel voneinander getrennte vertikale mineralische Leisten ersetzt.
- Dämmerling: zwei überbreite Querrippen reduziert, ohne die bestehenden animierten Wurzeln/Greifer abzutrennen.
- Minecraft 1.20.1, alle Schutz-/Mutagen-/Farm- und Kampfregeln unverändert. Referenzbild-Vergleich im Client weiterhin offen.

"""
need("## Version 1.113.0 —" in s,"previous release history")
s=s.replace("## Version 1.113.0 —",release+"## Version 1.113.0 —",1)
f.write_text(s,encoding="utf-8")
print("1.114: slim Colossus actual core, separated animated mineral arm ribs, narrower real horror ribcage.")
