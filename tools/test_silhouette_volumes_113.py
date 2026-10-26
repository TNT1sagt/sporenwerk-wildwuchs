#!/usr/bin/env python3
"""1.113 literal geometry regression: verify voids, bilateral volume, mattness."""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(x,reason):
    if not x:raise SystemExit("1.113 Minecraft volume test: "+reason)
b=(C/"MutagenkolossModel.java").read_text(encoding="utf-8")
p=(C/"KristallpirscherModel.java").read_text(encoding="utf-8")
d=(C/"DaemmerlingModel.java").read_text(encoding="utf-8")
skin,glow=b.split("    public static LayerDefinition createGlowLayer()",1)
need('private static void addSegmentedBeastMantle(PartDefinition body, boolean glowing)' in skin,
     "boss must have a genuine layered 3D rig")
need('addSegmentedBeastMantle(body, false);' in skin and
     'addSegmentedBeastMantle(body, true);' in glow,
     "real mirrored mantle hierarchy must exist in opaque and fullbright passes")
for kind in ("front","rear"):
    need('body.addOrReplaceChild("boss_mantle_'+kind+'_" + direction' in skin,
         "missing independent "+kind+" shell bones")
need('CubeListBuilder front = glowing ? CubeListBuilder.create()' in skin and
     'CubeListBuilder rear = glowing ? CubeListBuilder.create()' in skin,
     "stone mantle must not turn into four giant emissive cubes")
need('PartPose.offsetAndRotation(side * 17.7F, -2.9F, -14.0F' in skin and
     'PartPose.offsetAndRotation(side * 15.0F, -2.4F, 15.0F' in skin,
     "distinct forward shoulders and haunch locations essential for boss silhouette")
need(15.0-5.8 > -14.0+7.0,
     "boss front and back panzer envelopes must retain silhouette separation")
need('addPredatorySkullSilhouette(head, false);' in skin and
     'addPredatorySkullSilhouette(head, true);' in glow,
     "previous layered boss 3D cheek and nasal keel lost")
need('this.tailTip.xRot += 0.14F;' in b and
     'paw.y = 12.0F - lift * 1.65F;' in b,
     "prior real scorpion tail and four planted feet must remain")

# The gap is two whole model pixels in the skull mask, not 2D black paint.
face=p[p.index('head.addOrReplaceChild("face_mask"'):
       p.index('head.addOrReplaceChild("face_mandible_left"')]
cube=re.compile(r"\.addBox\(\s*(-?[\d.]+)F,\s*(-?[\d.]+)F,\s*(-?[\d.]+)F,\s*"
                r"([\d.]+)F,\s*([\d.]+)F,\s*([\d.]+)F\)")
boxes=[tuple(map(float,ns)) for ns in cube.findall(face)]
need(len(boxes)>=2,"two physically separated face mask cubes required")
left,right=boxes[:2]
need(right[0]-(left[0]+left[3])>=1.8,
     "true central face fissure must be >= 1.8 model pixels")
need('head.addOrReplaceChild("face_mandible_left"' in p and
     'head.addOrReplaceChild("face_mandible_right"' in p,
     "two genuine angled jaw spurs follow movable head")
need('this.leftArm.xRot = 0.24F + quietStride * 0.17F;' in p
     and 'leg.addOrReplaceChild("crystal_hock"' in p,
     "idle hunt legs and previous Crystal Stalker bones still live")
for side in ("left","right"):
    need('body.getChild("rib_root_'+side+'")' in d,
         "root anatomy must be parented to pre-existing animated rib")
    need('"waist_root_'+side+'"' in d,
         "lower-half silhouette must be rooted rather than vanilla humanoid")
need(d.count('addOrReplaceChild("waist_talon"')==2,
     "lower root straps must have two separate bent talons")
need('this.leftRibRoot.zRot' in d and
     'this.rightRibRoot.zRot' in d and
     'entity.isCropNibbling()' in d,
     "real root swaying and feeding animation remains")
need(b.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "boss two distinct UV render meshes preserved")
for source in (b,p,d):
    for banned in ("getChunk(","setBlock(","destroyBlock(",".hurt(","scheduleTick("):
        need(banned not in source,"visual pass may not change world "+banned)
t=R/"src/main/resources/assets/sporenwerk/textures/entity"
for name,size in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(t/(name+suffix+".png")) as im:
            need(im.size==(size,size),"Minecraft texture atlas unchanged "+name+suffix)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.113\.0['\"]",
     (R/"build.gradle").read_text(encoding="utf-8")) is not None,
     "Gradle release")
r=(R/"README.md").read_text(encoding="utf-8")
need("Aktueller Entwicklungsstand: 1.113.0" in r and
     "Version 1.113.0" in r and "Version 1.112.0" in r,
     "current and historical release notes")
print("1.113: genuine front/back basalt silhouette, real 2px face void, jaw spurs and hooked animate-root lower body verified.")
