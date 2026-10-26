#!/usr/bin/env python3
"""Sporenwerk 1.107: real anatomical face/foot proportions after skull+limb redesign.

Fix 1.105/1.106 anatomical debt in genuine Minecraft client ModelPart geometry:
- dark Koloss brow/cheek *opaque* boxes were still 1.64 broad and long after
  the skull shrank; trim them to match its actual face.
- thin, selectively luminous etched eyebrow lines must not cover the entire
  original basalt plates in the fullbright mesh.
- stalker shin armor still had wider cube than its replacement long leg;
  narrow it and give each leg individually modeled, split forward toe crystals.
- Dämmerling thick zombie-width shin armor similarly replaced by slender wood
  and two small roots per foot.
No hitbox, entity AI, damage, spawn, world data, drop or art copy is touched.
"""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(good,why):
    if not good:raise SystemExit("1.107 original geometry proportions: "+why)
def once(source,a,b,name):
    count=source.count(a)
    need(count==1,name+" matching "+str(count))
    return source.replace(a,b,1)

# The older 1.64 armor dimensions on the *opaque* model still protruded
# past the smaller 1.105 head. Edged layered slate remains, but correctly
# matches a lower skull and exposes the inset paired eyes of 1.106.
B=C/"MutagenkolossModel.java"
source=B.read_text(encoding="utf-8")
need(source.count("    public static LayerDefinition createGlowLayer()")==1,
     "separate Forge skin and emission layers required")
opaque,fullbright=source.split("    public static LayerDefinition createGlowLayer()",1)
need('addBox(-7.6F, -6.8F, -9.3F, 15.2F, 12.0F, 15.1F)' in opaque,
     "1.105 smaller skull required")
for original,new,label in [
 ("addBox(-8.0F, -8.6F, -14.2F, 8.0F, 4.0F, 8.0F)",
  "addBox(-7.05F, -7.15F, -11.2F, 7.05F, 2.30F, 5.4F)","left basalt brow"),
 ("addBox(0.0F, -8.6F, -14.2F, 8.0F, 4.0F, 8.0F)",
  "addBox(0.0F, -7.15F, -11.2F, 7.05F, 2.30F, 5.4F)","right basalt brow"),
 ("addBox(-7.0F, -10.0F, -12.7F, 6.0F, 2.0F, 5.0F)",
  "addBox(-6.4F, -8.55F, -10.9F, 5.45F, 1.7F, 4.1F)","left eyebrow crest"),
 ("addBox(1.0F, -10.0F, -12.7F, 6.0F, 2.0F, 5.0F)",
  "addBox(0.95F, -8.55F, -10.9F, 5.45F, 1.7F, 4.1F)","right eyebrow crest"),
 ("addBox(-8.0F, -1.0F, -14.8F, 5.0F, 5.0F, 5.0F)",
  "addBox(-7.05F, -0.9F, -11.5F, 4.45F, 4.7F, 4.2F)","left basalt cheek"),
 ("addBox(3.0F, -1.0F, -14.8F, 5.0F, 5.0F, 5.0F)",
  "addBox(2.60F, -0.9F, -11.5F, 4.45F, 4.7F, 4.2F)","right basalt cheek"),
 ("addBox(-7.0F, 2.0F, -16.0F, 4.0F, 3.0F, 3.0F)",
  "addBox(-6.35F, 1.95F, -11.95F, 3.75F, 2.55F, 3.0F)","left cheek ridge"),
 ("addBox(3.0F, 2.0F, -16.0F, 4.0F, 3.0F, 3.0F)",
  "addBox(2.60F, 1.95F, -11.95F, 3.75F, 2.55F, 3.0F)","right cheek ridge"),
]:
    opaque=once(opaque,original,new,label)
# Emissive spots shrink to shallow, mirror-paired narrow etch marks. The
# 1.106 fullbright eye cubes remain untouched: blue/magenta runes stay narrow.
for original,new,label in [
 ("addBox(-7.10F, -8.1F, -12.8F, 7.25F, 3.65F, 7.1F)",
  "addBox(-6.2F, -6.05F, -11.42F, 4.9F, 0.50F, 0.34F)","left narrow glow brow"),
 ("addBox(-0.15F, -8.1F, -12.8F, 7.25F, 3.65F, 7.1F)",
  "addBox(1.3F, -6.05F, -11.42F, 4.9F, 0.50F, 0.34F)","right narrow glow brow"),
 ("addBox(-7.12F, -10.12F, -12.86F, 6.24F, 2.12F, 5.24F)",
  "addBox(-5.3F, -8.82F, -10.95F, 3.25F, 0.34F, 0.33F)","left upper eyebrow rune"),
 ("addBox(0.88F, -10.12F, -12.86F, 6.24F, 2.12F, 5.24F)",
  "addBox(2.05F, -8.82F, -10.95F, 3.25F, 0.34F, 0.33F)","right upper eyebrow rune"),
 ("addBox(-8.18F, -1.12F, -14.98F, 5.24F, 5.24F, 5.24F)",
  "addBox(-6.60F, 0.1F, -11.83F, 2.65F, 1.0F, 0.37F)","left cheek etch"),
 ("addBox(2.88F, -1.12F, -14.98F, 5.24F, 5.24F, 5.24F)",
  "addBox(3.95F, 0.1F, -11.83F, 2.65F, 1.0F, 0.37F)","right cheek etch"),
 ("addBox(-7.12F, 1.88F, -16.18F, 4.24F, 3.12F, 3.24F)",
  "addBox(-6.1F, 2.75F, -12.22F, 1.75F, 0.95F, 0.35F)","left lower cheek rune"),
 ("addBox(2.88F, 1.88F, -16.18F, 4.24F, 3.12F, 3.24F)",
  "addBox(4.35F, 2.75F, -12.22F, 1.75F, 0.95F, 0.35F)","right lower cheek rune"),
]:
    fullbright=once(fullbright,original,new,label)
B.write_text(opaque+"    public static LayerDefinition createGlowLayer()"+fullbright,encoding="utf-8")

P=C/"KristallpirscherModel.java"
p=P.read_text(encoding="utf-8")
need('addOrReplaceChild("shin_crystal"' in p and
     'addBox(-1.4F, 0.0F, -1.6F, 2.8F, 12.0F, 3.2F)' in p,
     "1.105 long slim leg still present")
p=once(p,
"""                            .addBox(-2.0F, 1.0F, -2.9F, 4.0F, 9.0F, 1.5F),
                    PartPose.ZERO);""",
"""                            .addBox(-1.35F, 1.0F, -2.45F, 2.7F, 9.0F, 1.35F),
                    PartPose.ZERO);
            // Distinct claws at the base of EACH existing walking leg,
            // directly connected to the leg pivot (not a floating texture).
            leg.addOrReplaceChild("front_talon_left",
                    CubeListBuilder.create().texOffs(96, 96)
                            .addBox(-0.65F, -0.6F, -3.5F, 1.3F, 1.7F, 4.2F),
                    PartPose.offsetAndRotation(-0.95F, 10.8F, -0.5F, -0.14F, 0.09F, -0.13F));
            leg.addOrReplaceChild("front_talon_right",
                    CubeListBuilder.create().texOffs(80, 96)
                            .addBox(-0.60F, -0.6F, -3.9F, 1.2F, 1.8F, 4.6F),
                    PartPose.offsetAndRotation(0.95F, 10.7F, -0.4F, -0.18F, -0.07F, 0.16F));""",
"two 3D foot talons for each slender crystal stalker leg")
P.write_text(p,encoding="utf-8")

D=C/"DaemmerlingModel.java"
d=D.read_text(encoding="utf-8")
need('addOrReplaceChild("bark_shin"' in d and
     'addBox(-1.3F,0.0F,-1.45F,2.6F,12.0F,2.9F)' in d,
     "1.105 thin Dämmerling leg required")
d=once(d,
"""                            .addBox(-2.1F,2.0F,-2.8F,4.2F,8.9F,2.4F),PartPose.ZERO);""",
"""                            .addBox(-1.45F,2.0F,-2.5F,2.9F,8.9F,1.5F),PartPose.ZERO);
            // Slender roots reach forward from the foot and follow the
            // vanilla-derived articulated walking rig automatically.
            leg.addOrReplaceChild("bark_tine_left",
                    CubeListBuilder.create().texOffs(64,0)
                            .addBox(-0.6F,-0.4F,-3.4F,1.2F,1.35F,4.0F),
                    PartPose.offsetAndRotation(-0.85F,10.8F,-0.45F,-0.12F,0.07F,-0.14F));
            leg.addOrReplaceChild("bark_tine_right",
                    CubeListBuilder.create().texOffs(96,0)
                            .addBox(-0.55F,-0.4F,-3.7F,1.1F,1.5F,4.4F),
                    PartPose.offsetAndRotation(0.85F,10.75F,-0.5F,-0.15F,-0.07F,0.16F));""",
"thin bark shins and asymmetrical clawed foot roots")
D.write_text(d,encoding="utf-8")

T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for name,size in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(name+suffix+".png")) as im:
            need(im.size==(size,size),name+" original pixel skin/glow dimensions")

# Rolling version requirements only. All old skeletal names, attacks and
# opaque/transparent skin invariants remain checked by existing tests.
for test in (R/"tools").glob("test_*.py"):
    if test.name=="test_reference_face_and_feet_107.py":continue
    old=test.read_text(encoding="utf-8")
    new=old.replace("Aktueller Entwicklungsstand: 1.106.0",
                    "Aktueller Entwicklungsstand: 1.107.0")
    if "build.gradle" in old:
        new=new.replace(r"1\.106\.0",r"1\.107\.0")
        new=new.replace("artifact must be version 1.106.0","artifact must be version 1.107.0")
    new=new.replace('"Version 1.106.0" in readme and "Version 1.105.0" in readme',
                    '"Version 1.107.0" in readme and "Version 1.106.0" in readme')
    if new!=old:test.write_text(new,encoding="utf-8")

gradle=R/"build.gradle";g,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                     "version = '1.107.0'",gradle.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle 1.107");gradle.write_text(g,encoding="utf-8")
readme=R/"README.md";s=readme.read_text(encoding="utf-8")
oldh="**Aktueller Entwicklungsstand: 1.106.0 — Korrekte Koloss-Leuchtaugen und feineres 3D-Kreaturenskelett.**"
need(oldh in s,"1.106 generated readme headline")
s=s.replace(oldh,"**Aktueller Entwicklungsstand: 1.107.0 — Koloss-Gesichtspanzer und eigenständige Kristall-/Wurzelfüße.**",1)
section="""## Aktueller Entwicklungsschritt — 1.107.0

- **Koloss: dunkle Basalt-Stirn und Wangen endlich passend zum kleineren Schädel:** Die Körpergeometrie aus 1.105 wurde kleiner, doch die alten großen 1.64-Panzerplatten standen weiterhin weit über den Kopf hinaus. Jetzt sind beide Stirnplatten und beide Wangenpanzer tatsächlich verkleinert, geometrisch gespiegelt und näher an den Kopf gerückt. Die Augen aus 1.106 bleiben davor lesbar.
- **Keine vollleuchtenden Gesichtspanzer mehr:** Die gegenüberliegenden emissiven Stirn- und Wangenquader waren immer noch fast so breit und dick wie die früheren Steinplatten. Sie wurden durch deutlich dünnere, gezielt positionierte Lichtrunen ersetzt. Der Basalt bleibt im regulären und der Kristallschimmer im selektiven Leucht-Layer.
- **Kristallpirscher bekommt echte gespaltene Kristallfüße:** Die 1.93-Schienenplatten waren weiterhin breiter als die neuen 1.105-Skelettbeine. Jede Beinschiene wird enger an das Bein angepasst und erhält vorne zwei unterschiedlich lange, eigene 3D-Krallen. Diese bewegen sich automatisch mit den vorhandenen Lauf- und Hinkanimationen.
- **Dämmerling bekommt lange Wurzelzehen:** Die ebenfalls überbreiten Schienbeinplatten wurden schmaler, und an jedem Fuß befinden sich nun zwei eigene, leicht asymmetrische verholzte Zehen. Dies ist optisch eine Wurzelkreatur, nicht nur ein Zombie mit dunkler Textur.
- **Sichtqualität vor Blinddekoration:** Kein generischer neuer Kristallschmuck, keine nicht-minecraftartigen 3D-Dateien. Ausschließlich überarbeitete bestehende Voxelgeometrie mit bereits gültigen 128/256-Minecraft-Pixelatlanten, keine aus fremden Mods kopierten Ressourcen.
- **Gameplay unberührt:** Kein Scanner, KI-/Server-Ticker, Schaden, Spielerfolgen, Infektionsausbreitung oder Blockmanipulation durch diese rein clientseitigen Modellteile.
- **Referenzprüfung weiter notwendig:** Die zwei Schichten beim Koloss, die Klauen an beiden Laufbeinen und die gesamte Silhouette müssen anhand echter Screenshots mit den Originalbildern verglichen werden.

"""
need("## Aktueller Entwicklungsschritt — 1.106.0" in s,"prior readme heading")
s=s.replace("## Aktueller Entwicklungsschritt — 1.106.0",
            section+"## Aktueller Entwicklungsschritt — 1.106.0",1)
release="""## Version 1.107.0 — Tatsächliche Silhouettenkorrektur bis zu den Füßen

- Koloss: Die bislang zu groß gebliebenen opaken Basalt-Brauen und Wangen nach der 1.105-Schädelverkleinerung geometrisch an den kleineren Kopf angepasst. Riesige Leuchtplatten durch dünne, selektive Stirn- und Wangenrisse ersetzt.
- Kristallpirscher: Schmale Schienbeinpanzer und pro Bein zwei echte Kristall-Fußkrallen statt überbreitem generischem Schienbeinwürfel.
- Dämmerling: Schmalere Holzschienen und pro Bein zwei asymmetrische echte Wurzelzehen. Alle bisherigen Bewegungs-/Fraß-/Jagd-Animationen bleiben erhalten.
- Forge-1.20.1-Regression, installierbare JAR und Dedicated-Server-Test automatisiert; endgültige Pixel-/Silhouettenvergleichbarkeit wird erst im Minecraft-Client bestätigt.

"""
need("## Version 1.106.0 —" in s,"previous release heading")
s=s.replace("## Version 1.106.0 —",release+"## Version 1.106.0 —",1)
readme.write_text(s,encoding="utf-8")
print("1.107 real 3D: smaller mirrored boss basalt face, thin emitter runes, split crystal toe claws and wooden root feet installed.")
