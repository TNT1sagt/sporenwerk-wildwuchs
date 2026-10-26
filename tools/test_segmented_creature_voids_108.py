#!/usr/bin/env python3
"""1.108 assert real negative gaps in source-defined Forge ModelParts.

Produces an additional schematic geometry cross-section PNG sourced from the
CURRENT Java cube coordinates (not concept art, not a Minecraft screenshot).
The visual QA card lets a human see whether monster silhouette changes are
real rather than a painted 2D line on top of a continuous giant cuboid.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def rd(p):return p.read_text(encoding="utf-8")
def need(ok,what):
    if not ok:raise SystemExit("1.108 genuine mesh gap QA: "+what)
P=rd(C/"KristallpirscherModel.java")
B=rd(C/"MutagenkolossModel.java")
D=rd(C/"DaemmerlingModel.java")
cuboid=re.compile(r"\.addBox\(\s*(-?[\d.]+)F,\s*(-?[\d.]+)F,\s*(-?[\d.]+)F,\s*"
                  r"([\d.]+)F,\s*([\d.]+)F,\s*([\d.]+)F\s*\)")
def boxes(txt):
    return [tuple(map(float,m.groups())) for m in cuboid.finditer(txt)]
def gap_x(a,b):
    # Non-overlapping intervals in local x coordinates; epsilon for voxel precision.
    return b[0] - (a[0] + a[3])
# Exact named ModelPart blocks: preserve parent/child pivot structure.
p_begin=P.index('PartDefinition crest = body.addOrReplaceChild("back_crest"')
p_end=P.index('crest.addOrReplaceChild("crest_side_shard"',p_begin)
back=P[p_begin:p_end];q=boxes(back)
need(len(q)==3,"crystal back MUST be three separate 3D cuboids")
q=sorted(q,key=lambda box:box[0])
need(gap_x(q[0],q[1]) >= 1.0 and gap_x(q[1],q[2]) >= 1.0,
     "crystal back must have two gaps >= one Minecraft pixel, not overlap")
need(q[1][4]>q[0][4] and q[1][4]>q[2][4],
     "middle thorn must be tallest and retain irregular silhouette")
need("this.backCrest.xRot = -0.20F + sway;" in P
     and 'this.backCrest = this.body.getChild("back_crest");' in P
     and 'crest.addOrReplaceChild("crest_side_shard"' in P,
     "old articulated side crystal must remain child of new open crest")
for term in ('addOrReplaceChild("dorsal_fin_left"',
             'addOrReplaceChild("dorsal_fin_right"',
             'addOrReplaceChild("thorax_resonator"',
             'addOrReplaceChild("front_talon_left"',
             'addOrReplaceChild("front_talon_right"'):
    need(term in P,"missing 1.94-1.107 existing Kristallpirscher anatomy "+term)
need(".addBox(-5.0F, -15.0F, 1.5F, 10.0F, 17.0F, 5.0F)" not in P,
     "old giant solid back slab must actually disappear")

main,glow=B.split("    public static LayerDefinition createGlowLayer()",1)
mono=[]
for side in ("left","right"):
    start=main.index('body.addOrReplaceChild("monolith_'+side+'"')
    end=main.index('fin_'+side+'.addOrReplaceChild("monolith_prism"',start)
    item=main[start:end]
    bs=boxes(item)
    need(len(bs)==4,side+" boss monolith should have two side rails, rear bridge and cap")
    rail=sorted(bs[:2],key=lambda box:box[0])
    need(gap_x(rail[0],rail[1]) >= 3.0,
         "visible through-slot at front of "+side+" boss monolith absent")
    need(bs[2][2]>=2.0 and bs[2][5]<=2.5,
         "rear bridge must be behind front slit, not fill it from viewer")
    need(bs[3][1]<rail[0][1] and bs[3][4]<=8.0,
         "short top cap must not erase gap on entire boss monolith")
    mono.append((side,bs))
    need('body.addOrReplaceChild("monolith_'+side+'"' in glow,
         "paired glow layer missing "+side+" hierarchy")
    need('fin_'+side+'.addOrReplaceChild("monolith_prism"' in main and
         'fin_'+side+'.addOrReplaceChild("monolith_prism"' in glow,
         "crystal spire still must be in both glow/skin layer trees")
need(mono[0][1]==mono[1][1],
     "two basalt columns must be same shape while mirroring via part pivots")
for s in ('this.monolithLeft.zRot','this.monolithRight.zRot',
          'addOrReplaceChild("stinger_bloom"',
          'addFourPetalCoreIris(body, true);',
          'addFourPetalCoreIris(body, false);',
          'addBattleWearVeins(body, true);',
          'addBattleWearVeins(body, false);'):
    need(s in B,"Colossus real attack rig and glow elements preserved "+s)
need(B.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "separate correctly sized opaque/transparent boss trees")
need("addBox(-5.5F, -17.0F, -5.0F, 11.0F, 18.0F, 10.0F)" not in B,
     "continuous old basalt monolith still in model")

hand_start=D.index('PartDefinition guard=arm.addOrReplaceChild("root_fingers"')
hand_end=D.index('guard.addOrReplaceChild("left_finger"',hand_start)
hand=boxes(D[hand_start:hand_end])
need(len(hand)==3,"real Dämmerling hand must be two root rods plus bridge")
rails=sorted(hand[:2],key=lambda box:box[0])
need(gap_x(rails[0],rails[1])>=1.0,
     "root palm remains solid mitten: need actual air between fingers")
need(hand[2][1]>=4.0 and hand[2][4]<=1.5,
     "only a narrow low bridge may join split palm bones")
for term in (
    'guard.addOrReplaceChild("left_finger"',
    'guard.addOrReplaceChild("right_finger"',
    'this.leftClaws.xRot=-0.65F+',
    'this.rightClaws.xRot=-0.69F-',
    'body.addOrReplaceChild("rib_root_left"',
    'body.addOrReplaceChild("rib_root_right"',
    'leg.addOrReplaceChild("bark_tine_left"',
    'leg.addOrReplaceChild("bark_tine_right"'):
    need(term in D,"old farm horror expressive bones must survive "+term)
need("addBox(-2.3F,0.0F,-1.8F,4.6F,5.6F,3.6F)" not in D,
     "old root mitten still exists")
for code in (P,B,D):
    for illegal in ("getChunk(", "getEntitiesOfClass(", "setBlock(",
                    "destroyBlock(", "scheduleTick(", ".hurt("):
        need(illegal not in code,
             "client geometry must not cause server load or gameplay "+illegal)

# Draw static orthographic FRONT geometry slices read from CURRENT Java. A
# deliberately labeled x/y cuboid projection, NOT an actual Minecraft render.
out=R/"qa-output"
out.mkdir(parents=True,exist_ok=True)
im=Image.new("RGB",(1120,385),(14,17,24))
draw=ImageDraw.Draw(im)
labels=[
    ("KRISTALLPIRSCHER / Rücken",q,(80,210,235),(-7.0,7.0,-24.5,4.0)),
    ("KRISTALLKOLOSS / Monolith",mono[0][1][:2],(145,96,191),(-7.0,7.0,-19.0,4.0)),
    ("DÄMMERLING / Wurzelhand",hand,(107,153,107),(-3.2,3.2,-0.8,6.5)),
]
for col,(name,geometry,color,(xmin,xmax,ymin,ymax)) in enumerate(labels):
    left=20+col*370
    draw.rounded_rectangle((left,55,left+351,319),radius=8,fill=(24,30,39))
    draw.text((left+12,65),name,fill=(239,240,245))
    area=(left+24,94,left+330,286)
    scalex=(area[2]-area[0])/(xmax-xmin)
    scaley=(area[3]-area[1])/(ymax-ymin)
    for (x,y,z,w,h,depth) in geometry:
        r=(area[0]+(x-xmin)*scalex,
           area[1]+(y-ymin)*scaley,
           area[0]+(x+w-xmin)*scalex,
           area[1]+(y+h-ymin)*scaley)
        draw.rectangle(r,fill=color,outline=(225,231,244),width=1)
    draw.text((left+15,296),"Quelle: echte ModelPart.addBox-Werte",fill=(170,179,191))
draw.text((20,15),"SPORENWERK 1.108   |   SCHEMATISCHE 3D-KNOCHENQUERSCHNITTE",fill=(242,244,248))
draw.text((20,338),"Nur Quellgeometrie, keine In-Game-Ansicht und KEIN Nachweis exakter Referenzbild-Treue.",fill=(221,183,123))
draw.text((20,360),"Frontansicht der ausgewählten Würfel. Animation, zusätzliche Kinder und Rotation nicht dargestellt.",fill=(165,173,186))
output=out/"reference-creature-mesh-108.png"
im.save(output,optimize=True)
need(output.stat().st_size>1500,"schematic source-derived PNG generated")

for name,sz in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    folder=R/"src/main/resources/assets/sporenwerk/textures/entity"
    for suffix in ("","_glow"):
        with Image.open(folder/(name+suffix+".png")) as tex:
            need(tex.size==(sz,sz),"Minecraft skin/emissive atlas "+name+suffix)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.108\.0['\"]",
               rd(R/"build.gradle")) is not None,"Gradle release version")
readme=rd(R/"README.md")
need("Aktueller Entwicklungsstand: 1.108.0" in readme and
     "Version 1.108.0" in readme and "Version 1.107.0" in readme,
     "README new and previous release sections")
print("1.108 source geometry, true split crystal/rock/root silhouettes, original animation bones and source-derived QA PNG passed.")
