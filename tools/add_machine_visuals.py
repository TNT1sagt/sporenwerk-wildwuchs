#!/usr/bin/env python3
"""Give machines proper oriented blockstates and five distinct pixel-art faces."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, re, sys

ROOT = Path(sys.argv[1]).resolve()
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"
TEX = ASSETS / "textures/block"

PALETTE = {
    "feldsammler": ((36,68,48,255), (121,177,93,255), (217,177,83,255)),
    "saatgutpresse": ((67,49,36,255), (199,130,56,255), (248,202,97,255)),
    "biomasse_bioreaktor": ((24,55,52,255), (64,159,145,255), (151,220,183,255)),
}
OUT=(17,25,22,255)
STEEL=(65,83,74,255)
HILITE=(120,143,126,255)
SHADOW=(29,41,36,255)

def rect(d, box, color, outline=None):
    d.rectangle(box, fill=color, outline=outline)

def line(d, pts, color, width=1):
    d.line(pts, fill=color, width=width, joint="curve")

def save(im, name):
    TEX.mkdir(parents=True, exist_ok=True)
    im.save(TEX / name, optimize=True)

def create_face(machine, face):
    accent, glow, bright = PALETTE[machine]
    im=Image.new("RGBA",(32,32),OUT)
    d=ImageDraw.Draw(im)
    if face=="side":
        rect(d,(1,1,30,30),SHADOW,OUT)
        rect(d,(3,3,28,28),accent,OUT)
        line(d,[(4,5),(27,5)],HILITE,1)
        line(d,[(4,26),(27,26)],OUT,1)
        rect(d,(5,7,26,17),(30,43,37,255),OUT)
        rect(d,(6,8,25,16),accent)
        # Vent slats, with a warm metal warning stripe unique to each machine.
        for y in (9,11,13,15):
            line(d,[(8,y),(23,y)],glow,1)
        rect(d,(7,19,24,23),SHADOW,OUT)
        rect(d,(8,20,23,22),glow)
        rect(d,(10,21,21,21),bright)
        for x,y in ((4,4),(25,4),(4,25),(25,25)):
            rect(d,(x,y,x+2,y+2),OUT)
            rect(d,(x,y,x+1,y+1),bright)
        if machine=="feldsammler":
            line(d,[(26,8),(28,8),(28,23),(26,23)],bright,1)
            rect(d,(23,9,25,12),glow)
        elif machine=="saatgutpresse":
            rect(d,(13,7,18,17),STEEL,OUT)
            rect(d,(14,8,17,15),bright)
            line(d,[(11,17),(20,17)],OUT,2)
        else:
            rect(d,(9,8,22,17),STEEL,OUT)
            rect(d,(10,9,21,16),glow)
            for x,y in ((12,11),(16,13),(19,10),(18,15)):
                rect(d,(x,y,x+1,y+1),bright)
    elif face=="back":
        rect(d,(1,1,30,30),SHADOW,OUT)
        rect(d,(3,3,28,28),accent,OUT)
        line(d,[(4,4),(27,4)],HILITE,1)
        rect(d,(6,7,25,23),SHADOW,OUT)
        rect(d,(8,9,23,21),accent,OUT)
        # A small service hatch and four screw heads make the back recognizable.
        rect(d,(11,11,20,19),STEEL,OUT)
        rect(d,(12,12,19,18),accent)
        line(d,[(12,13),(19,13)],bright,1)
        line(d,[(12,16),(19,16)],glow,1)
        rect(d,(15,14,16,15),OUT)
        for x,y in ((7,8),(23,8),(7,22),(23,22)):
            rect(d,(x,y,x+1,y+1),bright)
    elif face=="top":
        rect(d,(1,1,30,30),OUT)
        rect(d,(3,3,28,28),STEEL,OUT)
        rect(d,(5,5,26,26),accent,OUT)
        line(d,[(5,5),(26,5)],HILITE,2)
        line(d,[(5,5),(5,26)],HILITE,1)
        rect(d,(8,8,23,23),SHADOW,OUT)
        rect(d,(9,9,22,22),glow,OUT)
        # Recessed service plate and central identifying stripe.
        rect(d,(11,11,20,20),accent,OUT)
        if machine=="feldsammler":
            line(d,[(12,18),(16,12),(20,18)],bright,2)
            line(d,[(13,19),(19,19)],glow,1)
        elif machine=="saatgutpresse":
            rect(d,(14,11,17,19),STEEL,OUT)
            rect(d,(15,12,16,18),bright)
            line(d,[(12,20),(19,20)],glow,1)
        else:
            rect(d,(12,12,19,19),glow,OUT)
            rect(d,(14,14,17,17),bright)
            for x,y in ((10,10),(21,10),(10,21),(21,21)):
                rect(d,(x,y,x+1,y+1),bright)
        for x,y in ((3,3),(26,3),(3,26),(26,26)):
            rect(d,(x,y,x+2,y+2),OUT)
            rect(d,(x,y,x+1,y+1),bright)
    elif face=="bottom":
        rect(d,(1,1,30,30),OUT)
        rect(d,(3,3,28,28),SHADOW,OUT)
        line(d,[(4,4),(27,27)],STEEL,2)
        line(d,[(27,4),(4,27)],STEEL,2)
        rect(d,(8,8,23,23),SHADOW,OUT)
        rect(d,(11,11,20,20),STEEL,OUT)
        for x,y in ((4,4),(25,4),(4,25),(25,25)):
            rect(d,(x,y,x+2,y+2),OUT)
            rect(d,(x,y,x+1,y+1),HILITE)
    save(im, f"{machine}_{face}.png")

def write_model(machine):
    model={
      "parent":"minecraft:block/cube",
      "textures":{
        "down":f"sporenwerk:block/{machine}_bottom",
        "up":f"sporenwerk:block/{machine}_top",
        "north":f"sporenwerk:block/{machine}",
        "east":f"sporenwerk:block/{machine}_side",
        "south":f"sporenwerk:block/{machine}_back",
        "west":f"sporenwerk:block/{machine}_side",
        "particle":f"sporenwerk:block/{machine}"
      }
    }
    (ASSETS/"models/block"/f"{machine}.json").write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
    # The inventory item uses the 3D cube model rather than a flat generated sprite.
    item={"parent":f"sporenwerk:block/{machine}"}
    (ASSETS/"models/item"/f"{machine}.json").write_text(json.dumps(item,indent=2)+"\n",encoding="utf-8")
    variants={}
    for facing,y in (("north",0),("east",90),("south",180),("west",270)):
        variants[f"facing={facing}"]={"model":f"sporenwerk:block/{machine}","y":y}
    (ASSETS/"blockstates"/f"{machine}.json").write_text(json.dumps({"variants":variants},indent=2)+"\n",encoding="utf-8")

for machine in PALETTE:
    for face in ("side","back","top","bottom"):
        create_face(machine,face)
    write_model(machine)

# Sanity-check the JSON and its 5-face texture references before Gradle runs.
for machine in PALETTE:
    state=json.loads((ASSETS/"blockstates"/f"{machine}.json").read_text(encoding="utf-8"))
    assert set(state["variants"]) == {"facing=north","facing=east","facing=south","facing=west"}
    model=json.loads((ASSETS/"models/block"/f"{machine}.json").read_text(encoding="utf-8"))
    for texture in model["textures"].values():
        path=ASSETS/"textures"/(texture.split(":",1)[1]+".png")
        if not path.is_file():
            raise SystemExit(f"Missing machine texture: {path}")
        
# Version bump to the geometry/UV correction.
build=ROOT/"build.gradle"
s=build.read_text(encoding="utf-8")
s=re.sub(r"version = '[^']+'", "version = '1.1.6'", s, count=1)
build.write_text(s,encoding="utf-8")
readme=ROOT/"README.md"
s=readme.read_text(encoding="utf-8")
s=s.replace("1.1.5","1.1.6").replace("V1.1.5","V1.1.6")
s += "\n\n## 1.1.6 machine visuals\nMachines have four facing variants. The front, side, back, top, and underside use separate pixel-art textures, so the display panel no longer repeats across every face. Placement rotation is reflected in the blockstate/model rotation.\\n"
readme.write_text(s,encoding="utf-8")
print("Generated unique oriented machine models and textures.")
