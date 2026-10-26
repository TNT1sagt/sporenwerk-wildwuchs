#!/usr/bin/env python3
"""1.105 exact structural silhouette regression for Minecraft Forge client.

Confirms the generic zombie primitives are REPLACED (not just covered by
crystal art), that three independent main creature hierarchies retain all
previously animated bones, that real void gaps remain in ribcages, and the
Colossus skull is physically smaller while retaining both render layers.
"""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def rd(p):return p.read_text(encoding="utf-8")
def need(ok,m):
    if not ok:raise SystemExit("1.105 reference-mesh QA: "+m)
p=rd(C/"KristallpirscherModel.java")
d=rd(C/"DaemmerlingModel.java")
b=rd(C/"MutagenkolossModel.java")
def mark(name,s,spaced):
    if spaced:
        source='HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F)'
    else:
        source='HumanoidModel.createMesh(CubeDeformation.NONE,0.0F)'
    need(source in s,name+": retains vanilla-compatible pivot/animation skeleton")
    need('root.addOrReplaceChild("body"' in s,name+": new real torso not installed")
    need('root.addOrReplaceChild("head"' in s,name+": custom head missing")
    need('root.addOrReplaceChild("hat", CubeListBuilder.create(), PartPose.ZERO)' in s if spaced else
         'root.addOrReplaceChild("hat",CubeListBuilder.create(),PartPose.ZERO)' in s,
         name+": old stock zombie hat will visually hide custom face")
    for limb in ("left_arm","right_arm","left_leg","right_leg"):
        need('root.addOrReplaceChild("'+limb+'"' in s,
             name+": stock cuboid limb not replaced: "+limb)
    headpos=s.index('root.addOrReplaceChild("head"')
    need(headpos < s.index('PartDefinition body = root.getChild("body");') if spaced
         else headpos < s.index('PartDefinition body=root.getChild("body");'),
         name+": new bones must be constructed BEFORE growth children")
    need(s.count('root.addOrReplaceChild("body"')==1,
         name+": unexpectedly redefined torso")
    need(s.count('root.addOrReplaceChild("head"')==1,
         name+": unexpectedly redefined skull")
    need("setupAnim(" in s and "super.setupAnim(" in s,
         name+": stock motion needs to animate custom bones")
mark("Crystal Stalker",p,True)
mark("Dämmerling",d,False)

for token in (
    'addBox(-4.0F, 0.0F, -1.8F, 8.0F, 3.2F, 3.6F)',
    'addBox(-3.5F, 8.1F, -1.4F, 7.0F, 3.9F, 2.8F)',
    'addBox(-1.2F, 3.0F, -1.1F, 2.4F, 6.3F, 2.2F)',
    'addBox(-1.5F, -2.0F, -1.65F, 3.0F, 14.0F, 3.3F)',
    'addBox(-3.25F, -7.5F, -3.4F, 6.5F, 7.6F, 6.8F)',
    'addBox(-4.8F, -6.0F, -3.0F, 9.6F, 2.6F, 2.4F)',
    'addBox(-4.6F, -0.9F, -3.0F, 9.2F, 2.1F, 2.4F)',
    'addBox(-3.1F, 3.2F, -3.0F, 6.2F, 1.8F, 2.4F)',
    'addBox(-1.3F, -5.5F, 2.0F, 2.6F, 12.0F, 2.5F)',
    'addOrReplaceChild("back_crest"',
    'addOrReplaceChild("dorsal_fin_left"',
    'addOrReplaceChild("dorsal_fin_right"',
    'addOrReplaceChild("jaw_crystal"',
    'addOrReplaceChild("thorax_resonator"',
    'addOrReplaceChild("talon_a"',
    'addOrReplaceChild("talon_b"',
    "if (entity.isAggressive())",
    "this.thoraxResonator.xScale += fatigueBreath;",
):
    need(token in p,"Pirscher reference-void structure or previous anatomy lost: "+token)
need('addBox(-5.3F, -6.0F, -3.0F, 10.6F, 11.0F, 2.4F)' not in p,
     "flat filled mineral chest defeats open torso reference")
need('addBox(-4.5F, -5.5F, 2.0F, 9.0F, 12.0F, 2.5F)' not in p,
     "solid rear armor slab defeats porous reference")
for token in (
    'addBox(-3.3F,0.0F,-1.65F,6.6F,3.2F,3.3F)',
    'addBox(-1.0F,2.8F,-0.95F,2.0F,7.0F,1.9F)',
    'addBox(-1.35F,-2.0F,-1.4F,2.7F,13.8F,2.8F)',
    'addBox(-5.2F,-5.0F,-2.6F,10.4F,2.7F,5.2F)',
    'addBox(-4.5F,0.0F,-2.4F,9.0F,2.0F,4.8F)',
    'addBox(-3.0F,4.7F,-2.1F,6.0F,2.3F,4.2F)',
    'addOrReplaceChild("back_hook_left"',
    'addOrReplaceChild("back_hook_right"',
    'addOrReplaceChild("root_fingers"',
    'addOrReplaceChild("hollow_jaw"',
    "this.feedingJaw.xRot=0.22F+Math.max(0.0F,clawBeat)*0.26F;",
    "if(entity.isCropNibbling())",
):
    need(token in d,"Dämmerling bespoke woody skeleton or feed animation missing: "+token)
need('addBox(-5.2F,-5.0F,-2.6F,10.4F,12.0F,5.2F)' not in d,
     "solid wood torso must actually be removed")
for token in (
    'addBox(-7.6F, -6.8F, -9.3F, 15.2F, 12.0F, 15.1F)',
    'addBox(-5.5F, -2.0F, -16.0F, 11.0F, 6.0F, 9.0F)',
    'addBox(-4.8F, 3.0F, -14.8F, 9.6F, 2.5F, 8.5F)',
    'addBox(-20.0F, -8.0F, -26.0F, 40.0F, 20.0F, 52.0F)',
    'addOrReplaceChild("monolith_prism"',
    'addOrReplaceChild("stinger_bloom"',
    'String name = part == 0 ? "core_iris_left"',
    'body.getChild("core_iris_left")',
    'addFourPetalCoreIris(body, true);',
    'addFourPetalCoreIris(body, false);',
    'this.pawCrystalTips = new ModelPart[12];',
    'this.tailMid.xRot += 0.59F;',
    "this.monolithLeft.zRot",
    "this.armorFractureVeins = new ModelPart[]",
):
    need(token in b,"Colossus reference mass, skull or live crystal mesh missing: "+token)
need('addBox(-9.0F, -7.0F, -10.0F, 18.0F, 13.0F, 16.0F)' not in b,
     "oversized stock boss cube still under reference skull")
need(b.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "Colossus matched 256-pixel skin and emission hierarchy must survive")
for creature,dims in (("kristallpirscher",(128,128)),("daemmerling",(128,128)),
                      ("mutagenkoloss",(256,256))):
    for suffix in ("","_glow"):
        with Image.open(R/"src/main/resources/assets/sporenwerk/textures/entity"/
                        (creature+suffix+".png")) as im:
            need(im.size==dims,"original pixel atlas dimensions incorrect: "+creature+suffix)
for code in (p,d,b):
    for forbidden in ("getChunk(", "getChunkNow(", "setBlock(", "destroyBlock(",
                      "getEntitiesOfClass(", "PacketDistributor", "scheduleTick("):
        need(forbidden not in code,
             "client sculpture must not add server/world changes "+forbidden)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.105\.0['\"]",
               rd(R/"build.gradle")) is not None,"Forge version 1.105")
s=rd(R/"README.md")
need("Aktueller Entwicklungsstand: 1.105.0" in s and
     "Version 1.105.0" in s and "Version 1.104.0" in s,
     "current and previous release notes")
print("1.105 validated: 2 hollow original voxel humanoid meshes, custom limbs and head, smaller four-legged Colossus skull, preserved crystal bones, animation, pixel/glow atlases.")
