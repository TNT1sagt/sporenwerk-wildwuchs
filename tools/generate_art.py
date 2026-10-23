#!/usr/bin/env python3
"""Sporenwerk cohesive hand-drawn pixel art; accepts the unpacked project directory."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw
import json
P = Path(sys.argv[1]).resolve()
T = P / "src/main/resources/assets/sporenwerk/textures"
OUT=(19,31,29,255); MET=(54,72,68,255); HI=(117,143,129,255); LOW=(35,48,44,255)
CREAM=(235,222,170,255); PAPER=(211,195,139,255)
MOSS=(73,126,76,255); MH=(126,174,92,255); MD=(39,86,57,255)
AM=(238,164,48,255); AH=(255,218,105,255); AD=(174,83,29,255)
RED=(181,48,60,255); RH=(239,100,83,255); RD=(105,36,48,255)
TEAL=(76,166,155,255); TH=(164,231,199,255)
def new(): return Image.new("RGBA",(32,32),(0,0,0,0))
def save(im, folder, name):
 # Vanilla block/crop models use a 0..16 UV square. Keep world-face textures at exactly 16x16;
 # higher-resolution block PNGs would sample only their upper-left quadrant at runtime.
 if folder == "block" and im.size != (16,16):
  im = im.resize((16,16), Image.Resampling.NEAREST)
 p=T/folder/(name+".png"); p.parent.mkdir(parents=True,exist_ok=True); im.save(p,optimize=True)
def r(d,b,c,o=None): d.rectangle(b,fill=c,outline=o)
def ln(d,p,c,w=1): d.line(p,fill=c,width=w,joint="curve")
def crop_mush(stage):
 im=new();d=ImageDraw.Draw(im)
 top=[14,8,5][stage]; r(d,(14,top+6,20,28),CREAM,OUT); r(d,(18,top+8,20,27),PAPER)
 caps=[[(10,18),(12,15),(15,14),(19,14),(22,16),(24,19),(23,21),(9,21)],
 [(7,15),(9,11),(13,8),(18,7),(22,9),(25,12),(27,16),(25,19),(7,19)],
 [(4,15),(6,10),(10,7),(15,5),(20,6),(25,9),(28,13),(29,16),(26,19),(6,19)]]
 d.polygon(caps[stage],fill=AD)
 if stage==0: d.polygon([(11,17),(14,15),(19,15),(22,17),(22,19),(10,19)],fill=AM)
 elif stage==1: d.polygon([(8,14),(12,10),(17,8),(21,10),(25,14),(25,16),(8,16)],fill=AM); d.polygon([(11,12),(15,9),(19,9),(22,12),(19,13),(13,13)],fill=AH)
 else: d.polygon([(5,14),(9,10),(14,7),(19,7),(24,10),(28,14),(27,16),(6,16)],fill=AM); d.polygon([(10,12),(14,8),(19,8),(23,11),(21,12),(14,12)],fill=AH)
 if stage==2:
  for b in [(12,10,13,10),(18,8,19,8),(24,12,25,12)]: r(d,b,CREAM)
 save(im,"block",f"bernsteinkappe_stage{stage}")
def crop_reed(stage):
 im=new();d=ImageDraw.Draw(im)
 ln(d,[(16,31),(16,4 if stage==2 else 7 if stage==1 else 15)],MD,4)
 if stage>=1:
  ln(d,[(16,24),(8,15)],MOSS,4);ln(d,[(16,20),(24,11)],MOSS,4);ln(d,[(16,27),(24,23)],MOSS,3)
  r(d,(7,13,11,16),MH);r(d,(21,10,26,13),MH)
 else: ln(d,[(16,24),(11,18)],MOSS,3)
 if stage==2:
  ln(d,[(16,17),(10,8)],MOSS,3);r(d,(13,4,18,7),PAPER);r(d,(14,9,18,12),MH);r(d,(10,8,12,10),(175,192,94,255))
 save(im,"block",f"faserrohr_stage{stage}")
def crop_root(stage):
 im=new();d=ImageDraw.Draw(im)
 ln(d,[(16,16),(16,7)],MD,3);ln(d,[(16,13),(8,8)],MD,3);ln(d,[(16,11),(23,6)],MD,3)
 d.polygon([(14,11),(10,5),(6,5),(7,10),(13,14)],fill=MOSS);d.polygon([(17,10),(21,3),(26,4),(26,9),(19,14)],fill=MH)
 if stage>=1:
  d.polygon([(13,15),(19,15),(22,19),(21,25),(17,30),(13,26),(11,21)],fill=RD);d.polygon([(14,16),(18,16),(20,20),(18,25),(16,27),(14,23),(13,20)],fill=RED)
 if stage==2: r(d,(14,18,15,21),RH);r(d,(13,22,14,23),(255,139,99,255))
 save(im,"block",f"rotwurzel_stage{stage}")
def crop_moss(stage):
 im=new();d=ImageDraw.Draw(im)
 for b in [(11,24,19,28),(7,21,13,25),(17,21,24,26)]: r(d,b,MD)
 if stage>=1:
  for b in [(4,18,10,22),(10,17,16,22),(17,17,23,22),(22,20,27,24),(12,13,19,18)]: r(d,b,MOSS)
 if stage==2:
  for b in [(3,16,8,19),(8,13,13,17),(13,10,18,15),(18,13,23,17),(23,16,28,20),(9,20,14,23),(17,20,22,23)]: r(d,b,MH)
  for b in [(7,15,8,16),(12,12,13,13),(17,11,18,12),(22,14,23,15),(25,17,26,18)]: r(d,b,TH)
 ln(d,[(6,27),(13,29),(21,28),(26,25)],MD,2); save(im,"block",f"filtermoos_stage{stage}")
def machine_base():
 im=new();d=ImageDraw.Draw(im);r(d,(1,1,30,30),OUT);r(d,(3,3,28,28),LOW);r(d,(4,4,27,27),MET)
 ln(d,[(5,5),(26,5)],HI,2);ln(d,[(5,6),(5,25)],HI);ln(d,[(6,26),(26,26)],OUT,2);ln(d,[(26,7),(26,24)],OUT,2)
 for x,y in [(4,4),(25,4),(4,25),(25,25)]: r(d,(x,y,x+2,y+2),OUT);r(d,(x,y,x+1,y+1),CREAM)
 r(d,(7,8,9,24),LOW);r(d,(22,8,24,24),LOW); return im,d
def machine(name,kind):
 im,d=machine_base()
 if kind=="field":
  r(d,(10,9,21,21),OUT);r(d,(11,10,20,20),(43,68,57,255));r(d,(12,11,19,19),(26,46,40,255));r(d,(14,13,17,17),MH);r(d,(15,14,16,16),TH);r(d,(11,23,20,25),LOW);ln(d,[(13,23),(13,27),(10,29)],MH,2);ln(d,[(19,23),(19,27),(22,29)],MH,2);r(d,(14,24,17,25),CREAM)
 elif kind=="press":
  r(d,(10,8,21,22),OUT);r(d,(11,9,20,21),(79,70,54,255));r(d,(12,10,19,15),AD);r(d,(13,11,18,14),AM);r(d,(14,12,16,13),AH);r(d,(14,15,17,17),HI);r(d,(12,18,19,20),LOW);r(d,(11,22,20,24),CREAM);ln(d,[(12,25),(19,25)],AH,2)
 else:
  r(d,(10,8,21,23),OUT);r(d,(11,9,20,22),(21,46,42,255));r(d,(12,10,19,20),(44,91,63,255));d.polygon([(12,16),(14,13),(17,15),(19,12),(20,20),(12,20)],fill=MH);r(d,(14,11,16,12),TH);r(d,(17,17,19,19),TEAL);r(d,(13,4,18,7),OUT);r(d,(14,5,17,6),TH);ln(d,[(16,6),(18,4)],RH);r(d,(13,24,18,26),LOW);r(d,(15,26,16,29),HI)
 save(im,"block",{"field":"feldsammler","press":"saatgutpresse","reactor":"biomasse_bioreaktor"}[kind]);save(im,"item",{"field":"feldsammler","press":"saatgutpresse","reactor":"biomasse_bioreaktor"}[kind])
def icon(name,kind):
 im=new();d=ImageDraw.Draw(im)
 if kind=="fiber":
  d.polygon([(8,24),(12,5),(19,3),(24,19),(20,27),(13,29)],fill=OUT);d.polygon([(10,22),(14,7),(18,6),(22,19),(19,25),(14,27)],fill=CREAM);ln(d,[(14,23),(17,8)],(255,246,200,255),2);ln(d,[(18,25),(20,18)],PAPER,2)
 elif kind=="cap":
  d.polygon([(8,18),(10,11),(15,7),(21,8),(25,13),(26,18),(22,22),(10,22)],fill=OUT);d.polygon([(10,17),(13,12),(17,9),(21,11),(24,15),(23,18),(11,19)],fill=AM);d.polygon([(13,14),(16,10),(19,10),(21,13),(18,14)],fill=AH);r(d,(14,21,19,28),CREAM,OUT);r(d,(17,22,19,27),PAPER)
 elif kind=="root":
  d.polygon([(13,6),(18,6),(21,11),(20,18),(17,27),(14,30),(11,22),(10,14)],fill=OUT);d.polygon([(14,7),(17,7),(19,12),(18,18),(15,26),(13,22),(12,14)],fill=RED);ln(d,[(14,10),(14,16)],RH,2);ln(d,[(14,7),(13,3)],MD,2);ln(d,[(14,6),(9,4)],MOSS,2);ln(d,[(15,5),(19,2)],MH,2)
 elif kind=="moss":
  d.polygon([(6,19),(7,12),(12,8),(17,10),(20,6),(26,10),(27,18),(23,24),(14,27),(8,24)],fill=OUT)
  for b,c in [((8,16,15,22),MD),((12,11,18,19),MOSS),((18,12,24,20),MH),((10,20,20,25),MOSS),((21,18,25,22),MD)]:r(d,b,c)
  for x,y in [(11,13),(16,9),(21,10),(23,14),(17,17)]:r(d,(x,y,x+1,y+1),TH)
 elif kind=="seed":
  for b in [(8,12,12,17),(13,7,17,12),(19,10,23,15),(11,19,15,24),(18,20,22,25)]:r(d,b,OUT)
  for b in [(9,12,11,16),(14,7,16,11),(20,10,22,14),(12,19,14,23),(19,20,21,24)]:r(d,b,AM)
  for b in [(9,12,9,13),(14,7,14,8),(20,10,20,11),(12,19,12,20)]:r(d,b,AH)
 elif kind=="spores":
  d.polygon([(13,17),(15,11),(18,11),(20,17),(18,21),(15,21)],fill=OUT);d.polygon([(15,16),(16,13),(18,16),(17,19)],fill=AM)
  for x,y in [(7,9),(11,6),(21,7),(25,12),(22,23),(12,25),(6,20),(18,4)]:r(d,(x,y,x+1,y+1),AH)
  r(d,(8,28,24,29),AD);r(d,(11,27,21,27),AM)
 elif kind=="filter":
  r(d,(6,4,25,27),OUT);r(d,(8,6,23,25),HI);r(d,(10,8,21,23),LOW);r(d,(12,10,19,21),(26,62,53,255));r(d,(13,11,18,19),TEAL);ln(d,[(13,12),(17,12)],TH,2);r(d,(15,15,17,17),MH)
 elif kind=="biomass":
  d.polygon([(7,9),(14,5),(24,8),(27,17),(22,26),(11,27),(5,19)],fill=OUT);d.polygon([(9,10),(14,7),(23,10),(25,17),(21,24),(12,25),(7,19)],fill=MD);d.polygon([(12,11),(17,9),(21,12),(23,17),(19,20),(13,20),(10,16)],fill=MH)
  for x,y in [(13,12),(18,11),(20,16),(15,18)]:r(d,(x,y,x+1,y+1),TH)
 elif kind=="waste":
  d.polygon([(6,23),(9,14),(14,10),(16,16),(21,7),(25,10),(23,20),(17,26)],fill=OUT);d.polygon([(8,22),(11,15),(14,13),(16,19),(21,9),(23,11),(21,20),(17,24)],fill=PAPER);d.polygon([(7,14),(9,10),(14,12),(12,16)],fill=MOSS);d.polygon([(18,9),(20,5),(25,7),(23,12)],fill=MH);ln(d,[(9,21),(22,15)],AD,2);ln(d,[(10,23),(23,17)],CREAM)
 elif kind=="knowledge":
  r(d,(6,3,26,29),OUT);r(d,(8,4,24,28),(74,92,65,255));r(d,(10,6,22,26),PAPER);r(d,(12,8,20,11),MD);r(d,(12,14,20,15),MET);r(d,(12,18,19,19),MET);r(d,(12,22,17,23),MET);r(d,(10,6,11,26),AD);r(d,(13,8,14,10),AH)
 elif kind=="gear":
  import math
  pts=[]; cx=cy=16
  for i in range(32):
   a=-math.pi/2+i*math.pi/16;rad=12 if i%4 in (0,1) else 9;pts.append((round(cx+math.cos(a)*rad),round(cy+math.sin(a)*rad)))
  d.polygon(pts,fill=OUT);pts=[]
  for i in range(32):
   a=-math.pi/2+i*math.pi/16;rad=10 if i%4 in (0,1) else 7;pts.append((round(cx+math.cos(a)*rad),round(cy+math.sin(a)*rad)))
  d.polygon(pts,fill=HI);d.ellipse((12,12,20,20),fill=OUT);d.ellipse((14,14,18,18),fill=AM)
 elif kind=="book":
  d.polygon([(5,5),(16,7),(16,28),(5,26)],fill=OUT);d.polygon([(17,7),(27,4),(27,25),(17,28)],fill=OUT);d.polygon([(7,7),(15,9),(15,25),(7,23)],fill=(64,93,64,255));d.polygon([(18,9),(25,6),(25,23),(18,25)],fill=(72,111,76,255));ln(d,[(16,8),(16,28)],CREAM);ln(d,[(8,11),(13,12)],AH);ln(d,[(19,11),(23,9)],AH);ln(d,[(20,20),(20,14)],TH,2);d.polygon([(20,17),(17,13),(17,11),(21,14)],fill=MH);d.polygon([(20,15),(23,11),(25,11),(23,15)],fill=MOSS);r(d,(9,17,13,18),PAPER);r(d,(9,20,13,21),PAPER)
 elif kind=="note":
  d.polygon([(6,4),(22,4),(27,9),(27,27),(6,27)],fill=OUT)
  d.polygon([(8,6),(21,6),(25,10),(25,25),(8,25)],fill=PAPER)
  d.polygon([(21,6),(21,10),(25,10)],fill=(154,137,92,255))
  ln(d,[(11,12),(21,12)],MET,1);ln(d,[(11,15),(20,15)],MET,1);ln(d,[(11,18),(17,18)],MET,1)
  ln(d,[(11,21),(18,19)],RD,1);r(d,(19,18,20,19),RED);r(d,(21,17,22,18),RD)
 else: raise ValueError(kind)
 save(im,"item",name)
def entity_skin():
 im=Image.new("RGBA",(64,64),(35,49,39,255));d=ImageDraw.Draw(im)
 # head UV: damp bark, pale moss mottling and two tiny red eyes
 r(d,(0,0,31,15),(26,40,34,255));r(d,(8,0,15,7),(52,79,57,255));r(d,(8,8,15,15),(74,94,70,255))
 r(d,(9,10,10,11),(225,67,60,255));r(d,(13,10,14,11),(225,67,60,255));r(d,(10,13,13,13),(18,26,23,255));r(d,(11,14,12,14),(149,48,55,255))
 r(d,(1,3,3,5),(106,139,81,255));r(d,(18,2,21,4),(72,115,73,255));r(d,(18,8,23,14),(40,62,47,255))
 # torso / front panel and a cracked amber seed core
 r(d,(16,16,39,31),(32,47,39,255));r(d,(20,20,27,31),(54,78,56,255));r(d,(21,21,26,25),(25,37,30,255))
 r(d,(22,22,25,24),(174,83,29,255));r(d,(23,22,24,23),(255,193,74,255));r(d,(21,26,26,27),(120,149,86,255))
 r(d,(32,20,39,31),(25,38,31,255));r(d,(34,23,37,27),(72,105,68,255))
 # sleeves / legs: weathered dark cloth and root-like strips
 for b in [(40,20,43,31),(44,20,47,31),(48,20,51,31),(52,20,55,31),(4,20,7,31),(8,20,11,31),(12,20,15,31),(0,20,3,31)]:
  r(d,b,(38,58,44,255))
 for pts in [[(41,22),(42,25),(41,29)],[(45,21),(46,25),(45,29)],[(49,22),(50,26),(49,30)],[(53,22),(54,25),(53,29)],[(5,22),(6,26),(5,30)],[(9,22),(10,25),(9,29)]]:
  ln(d,pts,(114,151,77,255),1)
 r(d,(4,24,7,25),(76,45,42,255));r(d,(44,27,47,28),(105,42,47,255))
 # olive plates on the upper back and shoulders
 r(d,(32,8,39,15),(42,64,45,255));r(d,(40,8,47,15),(30,47,36,255));r(d,(48,8,55,15),(56,81,52,255))
 r(d,(20,16,27,19),(49,74,52,255));r(d,(28,16,35,19),(39,58,43,255))
 path=T/"entity";path.mkdir(parents=True,exist_ok=True);im.save(path/"daemmerling.png",optimize=True)

entity_skin()

for i in range(3): crop_mush(i);crop_reed(i);crop_root(i);crop_moss(i)
machine("feldsammler","field");machine("saatgutpresse","press");machine("biomasse_bioreaktor","reactor")
for n,k in {"faser":"fiber","bernsteinkappe":"cap","rotwurzel":"root","filtermoos":"moss","faserrohr_samen":"seed","bernsteinkappe_sporen":"spores","rotwurzel_samen":"seed","filtermoos_sporen":"spores","pflanzenreste":"waste","biomasse":"biomass","feldwissen":"knowledge","maschinenteil":"gear","filter":"filter","feldhandbuch":"book","verwitterte_notiz":"note"}.items(): icon(n,k)
print("Sporenwerk 32x32 pixel-art resources regenerated.")


def machine_surfaces_and_models():
    """Give the machines actual front/side/top faces and a rotatable world model."""
    names = [
        ("feldsammler", "field"),
        ("saatgutpresse", "press"),
        ("biomasse_bioreaktor", "reactor"),
    ]
    for name, kind in names:
        side = Image.new("RGBA", (32, 32), MET)
        d = ImageDraw.Draw(side)
        r(d, (1, 1, 30, 30), OUT)
        r(d, (3, 3, 28, 28), LOW)
        r(d, (4, 4, 27, 27), MET)
        # A few inset plates keep side faces readable from a distance.
        r(d, (6, 6, 25, 25), (43, 57, 51, 255), OUT)
        ln(d, [(7, 7), (24, 7)], HI)
        ln(d, [(7, 8), (7, 23)], HI)
        ln(d, [(8, 24), (24, 24)], LOW, 2)
        for x, y in [(4,4), (25,4), (4,25), (25,25)]:
            r(d, (x, y, x+2, y+2), OUT)
            r(d, (x, y, x+1, y+1), CREAM)
        if kind == "field":
            r(d, (10, 9, 21, 21), OUT)
            r(d, (12, 11, 19, 19), (23, 39, 34, 255))
            for y in [12, 15, 18]:
                ln(d, [(13, y), (18, y)], MH, 2)
            r(d, (9, 9, 10, 20), HI)
            r(d, (21, 9, 22, 20), LOW)
            r(d, (14, 23, 17, 25), TH)
        elif kind == "press":
            d.ellipse((9, 8, 22, 21), fill=OUT)
            d.ellipse((11, 10, 20, 19), fill=HI)
            d.ellipse((14, 13, 17, 16), fill=OUT)
            ln(d, [(15, 7), (20, 12)], AM, 2)
            r(d, (12, 22, 19, 24), AD)
            r(d, (14, 22, 17, 23), AH)
        else:
            r(d, (9, 7, 22, 24), OUT)
            r(d, (11, 9, 20, 22), (24, 53, 45, 255))
            for x, col in [(13, MOSS), (16, MH), (19, TEAL)]:
                r(d, (x, 11, x+1, 20), col)
            r(d, (12, 12, 13, 14), TH)
            r(d, (17, 15, 18, 17), CREAM)
        save(side, "block", name + "_side")

        top = Image.new("RGBA", (32, 32), MET)
        t = ImageDraw.Draw(top)
        r(t, (1, 1, 30, 30), OUT)
        r(t, (3, 3, 28, 28), LOW)
        r(t, (4, 4, 27, 27), MET)
        ln(t, [(5, 5), (26, 5)], HI, 2)
        ln(t, [(5, 6), (5, 25)], HI)
        for x, y in [(4,4), (25,4), (4,25), (25,25)]:
            r(t, (x, y, x+2, y+2), OUT)
            r(t, (x, y, x+1, y+1), CREAM)
        r(t, (7, 7, 24, 24), (35, 48, 43, 255), OUT)
        if kind == "field":
            r(t, (9, 9, 22, 22), OUT)
            r(t, (11, 11, 20, 20), (29, 54, 42, 255))
            ln(t, [(13, 13), (18, 18)], MH, 2)
            ln(t, [(18, 13), (13, 18)], MOSS, 2)
            r(t, (14, 14, 17, 17), TH)
        elif kind == "press":
            t.ellipse((9, 9, 22, 22), fill=OUT)
            t.ellipse((11, 11, 20, 20), fill=HI)
            t.ellipse((14, 14, 17, 17), fill=AD)
            r(t, (14, 6, 17, 9), CREAM)
            r(t, (14, 22, 17, 25), CREAM)
            r(t, (6, 14, 9, 17), CREAM)
            r(t, (22, 14, 25, 17), CREAM)
        else:
            r(t, (9, 8, 22, 23), OUT)
            r(t, (11, 10, 20, 21), (24, 54, 44, 255))
            for x in [12, 16, 20]:
                ln(t, [(x, 11), (x, 20)], MH if x != 16 else TH, 2)
            r(t, (14, 13, 18, 17), AM)
        save(top, "block", name + "_top")

        model_dir = P / "src/main/resources/assets/sporenwerk/models"
        block_models = model_dir / "block"
        item_models = model_dir / "item"
        block_states = P / "src/main/resources/assets/sporenwerk/blockstates"
        block_models.mkdir(parents=True, exist_ok=True)
        item_models.mkdir(parents=True, exist_ok=True)
        block_states.mkdir(parents=True, exist_ok=True)

        block_model = {
            "parent": "minecraft:block/cube",
            "textures": {
                "particle": f"sporenwerk:block/{name}_side",
                "down": f"sporenwerk:block/{name}_side",
                "up": f"sporenwerk:block/{name}_top",
                "north": f"sporenwerk:block/{name}",
                "south": f"sporenwerk:block/{name}_side",
                "east": f"sporenwerk:block/{name}_side",
                "west": f"sporenwerk:block/{name}_side",
            }
        }
        (block_models / f"{name}.json").write_text(json.dumps(block_model, indent=2) + "\n", encoding="utf-8")
        (item_models / f"{name}.json").write_text(json.dumps({"parent": f"sporenwerk:block/{name}"}, indent=2) + "\n", encoding="utf-8")

        states = {"variants": {
            "facing=north": {"model": f"sporenwerk:block/{name}"},
            "facing=east": {"model": f"sporenwerk:block/{name}", "y": 90},
            "facing=south": {"model": f"sporenwerk:block/{name}", "y": 180},
            "facing=west": {"model": f"sporenwerk:block/{name}", "y": 270}
        }}
        (block_states / f"{name}.json").write_text(json.dumps(states, indent=2) + "\n", encoding="utf-8")

machine_surfaces_and_models()
print("Sporenwerk 32x32 pixel art, layered machine faces and directional model states generated.")
