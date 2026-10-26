#!/usr/bin/env python3
"""1.111 visible snout/heart depth and 3D branch acceptance."""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def check(v,s):
    if not v:raise SystemExit("1.111 client rig test: "+s)
b=(C/"MutagenkolossModel.java").read_text(encoding="utf8")
p=(C/"KristallpirscherModel.java").read_text(encoding="utf8")
d=(C/"DaemmerlingModel.java").read_text(encoding="utf8")
skin,glow=b.split("    public static LayerDefinition createGlowLayer()",1)
for source,name in ((skin,"chest_core_mount"),(skin,"chest_core"),(glow,"core_glow")):
    start=source.index('body.addOrReplaceChild("'+name+'"')
    check("PartPose.offset(0.0F, 10.0F, 14.0F));" in source[start:start+1300],
          name+" must be recessed in same local space")
check('PartPose.offsetAndRotation(x, y + 10.0F, -22.6F, 0.0F, 0.0F, 0.0F)' in b,
      "all iris leaves follow core")
check('PartPose.offset(0.0F, -5.0F, -20.0F)' in skin and
      "addBox(-5.5F, -2.0F, -16.0F, 11.0F, 6.0F, 9.0F)" in skin,
      "visible original muzzle/head rig preserved")
check((-20-16)<(-36.6+14)-10,"geometry: snout must protrude beyond crystal")
check(all('body.getChild("core_iris_'+x+'")' in b for x in ("left","right","top","bottom")),
      "all four actual movable core shutters preserved")
check("this.leftArm.xRot = 0.24F + quietStride * 0.17F;" in p and
      "this.rightArm.xRot = 0.14F - quietStride * 0.17F;" in p and
      'this.leftArm.xRot = this.leftArm.xRot * (1.0F - pursuit * 0.23F)' in p,
      "non-zombie idle and actual crystal stalker pursuit")
for side in ("left","right"):
    for kind in ("outer","inner"):
        check('Hook.addOrReplaceChild("branch_'+side+'_'+kind+'"' in d,
              "4 rooted Minecraft voxel antler forks required")
check("this.leftHook.zRot" in d and "this.rightHook.zRot" in d,
      "new branch children follow old root motions")
check("entity.isCropNibbling()" in d,"farm/horror pose remains")
for s in (b,p,d):
    for bad in ("getChunk(","setBlock(","destroyBlock(",".hurt(","scheduleTick("):
        check(bad not in s,"client rendering must not change world")
for name,dim in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(R/"src/main/resources/assets/sporenwerk/textures/entity"/(name+suffix+".png")) as im:
            check(im.size==(dim,dim),"pixel art/texture atlas preserved")
check(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.111\.0['\"]",
                (R/"build.gradle").read_text(encoding="utf8")) is not None,"Gradle release")
r=(R/"README.md").read_text(encoding="utf8")
check("Aktueller Entwicklungsstand: 1.111.0" in r
      and "Version 1.111.0" in r and "Version 1.110.0" in r,"release history")
print("1.111 model geometry/attack-root fork/atlas regression passed.")
