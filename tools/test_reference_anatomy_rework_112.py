#!/usr/bin/env python3
"""Sporenwerk 1.112 guard: not a decorative screenshot-only model."""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(ok,s):
    if not ok:raise SystemExit("1.112 geometry integrity: "+s)
def rd(n):return (C/n).read_text(encoding="utf-8")
b=rd("MutagenkolossModel.java")
p=rd("KristallpirscherModel.java")
d=rd("DaemmerlingModel.java")
skin,glow=b.split("    public static LayerDefinition createGlowLayer()",1)
need('private static void addPredatorySkullSilhouette(PartDefinition head, boolean glowing)' in skin,
     "missing real shared new boss skull helper")
need('addPredatorySkullSilhouette(head, false);' in skin
     and 'addPredatorySkullSilhouette(head, true);' in glow,
     "boss face must attach to exactly both opaque/glowing baked hierarchies")
for part in ("boss_zygoma_left","boss_zygoma_right","boss_nasal_keel"):
    need('head.addOrReplaceChild("'+part+'"' in skin,
         "boss jaw stone part missing "+part)
need('CubeListBuilder left = glowing ? CubeListBuilder.create()' in skin
     and 'CubeListBuilder right = glowing ? CubeListBuilder.create()' in skin
     and 'CubeListBuilder nasal = glowing ? CubeListBuilder.create()' in skin,
     "new basalt must be matte, not fullbright cyan rock")
need('head.addOrReplaceChild("lower_jaw"' in skin
     and 'head.addOrReplaceChild("lower_jaw"' in glow
     and "this.lowerJaw.xRot" in b,"old animating real jaw retained")
need('this.tail.xRot += 0.38F;' in b
     and 'this.tailMid.xRot += 0.59F;' in b
     and 'this.tailTip.xRot += 0.78F;' in b,
     "original synchronized triple tail rig preserved")
for tok in ('this.tail.xRot += 0.10F;',
            'this.tailMid.xRot += 0.13F;',
            'this.tailTip.xRot += 0.14F;',
            'this.tailStinger.xRot = 0.62F'):
    need(tok in b,"enhanced 3D sting curl lost "+tok)
need('this.tailStinger = this.tailTip.hasChild("stinger_bloom")' in b
     and b.count('addOrReplaceChild("stinger_bloom"')==2,
     "stinger must be real part in both render trees")
need('PartPose.offsetAndRotation(x, y + 10.0F, -24.6F' in b
     and 'PartPose.offset(sx * 9.4F, sy * 8.6F + 10.0F, -23.9F)' in b,
     "new face cannot regress correct inset iris/core")
need('leg.addOrReplaceChild("crystal_hock"' in p
     and 'leg.addOrReplaceChild("crystal_heel_hook"' in p,
     "two connected crystalline digitigrade feet missing")
need('root.getChild("left_leg"), root.getChild("right_leg")' in p
     and 'this.leftArm.xRot = 0.24F + quietStride * 0.17F;' in p,
     "both gait bones and non-zombie arm pose preserved")
for side in ("left","right"):
    need('body.getChild("rib_root_'+side+'").addOrReplaceChild("rib_fork"' in d,
         "Horror fork must grow from existing animated "+side+" chest rib")
    need('Hook.addOrReplaceChild("branch_'+side+'_outer"' in d,
         "prior multi-branch antler cannot be removed")
need("entity.isCropNibbling()" in d and
     'body.addOrReplaceChild("hollow_chest"' in d,
     "old field-horror and hollow ribcage must survive")
need(b.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "boss skin/emissive tree count changed")
for code in (b,p,d):
    for bad in ("getChunk(","getChunkNow(","setBlock(","destroyBlock(",".hurt(","scheduleTick("):
        need(bad not in code,"client visual update may not edit world "+bad)
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for n,dim in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(n+suffix+".png")) as im:
            need(im.size==(dim,dim),"UV texels must remain original "+n+suffix)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.112\.0['\"]",
     (R/"build.gradle").read_text(encoding="utf-8")) is not None,
     "Gradle 1.112 artifact version")
readme=(R/"README.md").read_text(encoding="utf-8")
need("Aktueller Entwicklungsstand: 1.112.0" in readme
     and "Version 1.112.0" in readme and "Version 1.111.0" in readme,
     "release history must survive")
print("1.112: visible Minecraft boss skull, matte/glow parity, triple scorpion tail, jointed hunter legs and moving root ribs verified.")
