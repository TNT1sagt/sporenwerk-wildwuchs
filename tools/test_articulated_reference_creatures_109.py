#!/usr/bin/env python3
"""Regression 1.109: verify actual articulated Minecraft model source."""
from pathlib import Path
import re
import sys
from PIL import Image

R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(ok,msg):
    if not ok:
        raise SystemExit("1.109 articulated model regression: "+msg)
def rd(path):
    return path.read_text(encoding="utf-8")

P=rd(C/"KristallpirscherModel.java")
B=rd(C/"MutagenkolossModel.java")
D=rd(C/"DaemmerlingModel.java")
stem=P[P.index('PartDefinition crest = body.addOrReplaceChild("back_crest"'):
       P.index('crest.addOrReplaceChild("crest_side_shard"')]
need('CubeListBuilder.create(),' in stem,
     "parent crest must be empty to avoid duplicate fixed crystal cubes")
cube=re.compile(r"\.addBox\(\s*(-?[\d.]+)F,\s*(-?[\d.]+)F,\s*(-?[\d.]+)F,\s*"
                r"([\d.]+)F,\s*([\d.]+)F,\s*([\d.]+)F\s*\)")
boxes=[]
for name in ("left","center","right"):
    tag='crest.addOrReplaceChild("crest_prong_'+name+'"'
    need(stem.count(tag)==1,"missing unique independent "+name+" prong")
    frag=stem.split(tag,1)[1].split("PartPose.ZERO);",1)[0]
    matches=cube.findall(frag)
    need(len(matches)==1,"one actual 3D cube per "+name+" articulated prong")
    boxes.append(tuple(map(float,matches[0])))
    need('this.crestProng'+name.title()+' = this.backCrest.getChild("crest_prong_'+name+'");' in P,
         name+" joint must be bound to actual baked ModelPart")
need('this.crestProngLeft.zRot =' in P and 'this.crestProngCenter.xRot =' in P
     and 'this.crestProngRight.zRot =' in P,
     "each crystal must have independent absolute frame animation")
left,center,right=boxes
need(center[0]-(left[0]+left[3])>=1.0
     and right[0]-(center[0]+center[3])>=1.0,
     "neutral-pose gaps between three crystal prongs >= one model pixel")
need(center[4]>left[4] and center[4]>right[4],
     "center prong taller than two side prongs")
need('this.backCrest.xRot = -0.20F + sway;' in P
     and 'crest.addOrReplaceChild("crest_side_shard"' in P
     and 'this.thoraxResonator.xScale' in P,
     "original shared back joint, side crystal and heartbeat preserved")

for name in ("left","right"):
    need('guard.addOrReplaceChild("'+name+'_finger"' in D,
         "open root hand must still have "+name+" moving finger")
need('this.leftClaws.yRot = -0.055F - nibbleSplay' in D
     and 'this.rightClaws.yRot = 0.055F + nibbleSplay' in D
     and 'entity.isCropNibbling() ? 0.16F : 0.0F' in D,
     "real crop state must open and neutralize both palms")
need('this.leftRibRoot.zRot=' in D and 'this.rightRibRoot.zRot=' in D,
     "earlier hanging root animations still present")

skin,glow=B.split("    public static LayerDefinition createGlowLayer()",1)
need(B.count('return LayerDefinition.create(mesh, 256, 256);')==2,
     "matched 256 pixel skin/glow models")
for tree in (skin,glow):
    for side in ("left","right"):
        need('body.addOrReplaceChild("monolith_'+side+'"' in tree
             and 'fin_'+side+'.addOrReplaceChild("monolith_prism"' in tree,
             "old twin hollow monolith and crystal child in both model trees")
need('this.monolithLeft.yRot = 0.016F + monolithBreath + breathCharge * 0.075F;' in B
     and 'this.monolithRight.yRot = -0.016F - monolithBreath - breathCharge * 0.075F;' in B,
     "boss mirrored monolith breathing must follow existing breath-charge")
need('this.head.zRot = -this.body.zRot * 0.60F;' in B
     and 'float breathCharge = crystalState == MutagenkolossEntity.ATTACK_BREATH' in B,
     "boss previous head and attack animations preserved")

for source in (P,B,D):
    for illegal in ("getChunk(", "setBlock(", "destroyBlock(", ".hurt(", "scheduleTick("):
        need(illegal not in source,"client animation must never mutate gameplay "+illegal)
for name,dimension in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(R/"src/main/resources/assets/sporenwerk/textures/entity"/(name+suffix+".png")) as tex:
            need(tex.size==(dimension,dimension),
                 "pixelated Minecraft model atlas incorrect for "+name+suffix)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.109\.0['\"]",
               rd(R/"build.gradle")) is not None,"Gradle artifact is 1.109.0")
readme=rd(R/"README.md")
need("Aktueller Entwicklungsstand: 1.109.0" in readme
     and "Version 1.109.0" in readme and "Version 1.108.0" in readme,
     "README release history")
print("1.109 real Minecraft articulated crystal/root/monolith geometry and state-linked animation passed.")
