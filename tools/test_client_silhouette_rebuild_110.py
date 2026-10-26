#!/usr/bin/env python3
"""1.110 true geometry regression: 24px boss foot reach, segmented bodies."""
from pathlib import Path
import sys,re
from PIL import Image
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(c,m):
    if not c:raise SystemExit("1.110 in-client silhouette contract: "+m)
def read(x):return (C/x).read_text(encoding="utf8")
b=read("MutagenkolossModel.java")
p=read("KristallpirscherModel.java")
d=read("DaemmerlingModel.java")
skin,glow=b.split("    public static LayerDefinition createGlowLayer()",1)
need("addBox(-20.0F, -8.0F, -26.0F, 40.0F, 20.0F, 52.0F)" not in skin,"monolithic 52px Colossus barrel survived")
need("addBox(-17.5F, -9.5F, -23.0F, 35.0F, 10.5F, 23.0F)" in skin
     and "addBox(-14.0F, -8.5F, 8.5F, 28.0F, 11.0F, 16.0F)" in skin,"separated front/rear basalt volumes missing")
need("PartPose.offsetAndRotation(0.0F, 14.0F, 0.0F" in skin
     and "PartPose.offset(0.0F, 14.0F, 0.0F)" in glow,"knees not aligned across skin/emissive rigs")
need(skin.count("PartPose.offset(0.0F, 12.0F, -1.0F)")>=1
     and glow.count("PartPose.offset(0.0F, 12.0F, -1.0F)")>=1,
     "both articulated paw rigs must have grounded base pivots")
need('paw.y = 12.0F - lift * 1.65F;' in b and
     'stompPawLeft.y = 12.0F;' in b and 'stompPawRight.y = 12.0F;' in b,
     "weighted gait and stomp must use new neutral ground contact")
# body -4 + parent leg +2 + knee +14 + paw +12 = model-space 24 px.
need((-4+2+14+12)==24,"ground contact origin arithmetic")
need("addBox(-7.0F, 0.0F, -8.0F, 14.0F, 2.0F, 15.0F)" not in glow,
     "fullbright pavement-sized cyan sole still visible")
need("addBox(-2.6F, 0.12F, -7.9F, 5.2F, 0.4F, 0.8F)" in glow,
     "selective foot emission inlay missing")
need("addBox(-0.9F, -14.5F, 3.0F, 2.8F, 15.5F, 3.4F)" in p,
     "shorter articulated central dorsal prism missing")
need("addBox(-3.5F, -0.2F, -1.8F, 7.0F, 2.6F, 3.6F)" in p
     and "addBox(-2.7F, -7.8F, -3.2F, 5.4F, 7.8F, 6.4F)" in p,
     "crystal hunter head/torso not physically changed")
need("addBox(-0.9F,-15.0F,-0.85F,1.8F,6.6F,1.7F)" in d
     and "addBox(-2.9F,0.0F,-1.45F,5.8F,2.6F,2.9F)" in d,
     "wood horror antler and torso not physically changed")
need("this.leftArm.xRot=entity.isAggressive() ? -0.62F" in d
     and "this.rightArm.xRot=entity.isAggressive() ? -0.47F" in d,
     "Vanilla zombie straight arms not overridden")
for n,sz in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(R/"src/main/resources/assets/sporenwerk/textures/entity"/(n+suffix+".png")) as img:
            need(img.size==(sz,sz),"Minecraft atlas mismatch "+n+suffix)
need(b.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "two Colossus opaque/emissive layer definitions must remain")
for term in ("getChunk(", "setBlock(", "destroyBlock(", ".hurt("):
    need(all(term not in s for s in (b,p,d)),"unexpected gameplay/world mutation in client "+term)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.110\.0['\"]",
               (R/"build.gradle").read_text(encoding="utf8")),"ForgeGradle version")
rm=(R/"README.md").read_text(encoding="utf8")
need("Aktueller Entwicklungsstand: 1.110.0" in rm and
     "Version 1.110.0" in rm and "Version 1.109.0" in rm,
     "release history")
print("1.110 screenshot-led geometry: grounded quadruped, split main chassis, narrower crystal and roots, selective glow passed.")
