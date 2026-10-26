#!/usr/bin/env python3
"""Sporenwerk 1.106 actual geometry regression, not image similarity claims.

The prior release reduced the boss skull but did not realign original glow eyes.
This verifies both eyes lie INSIDE the new head's x-range and are symmetric,
and that old stalker shoulder bricks were physically replaced by open faceted
sections, and farm roots have independent animation bones.
"""
from pathlib import Path
import re,sys
from PIL import Image
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def load(x):return x.read_text(encoding="utf-8")
def need(ok,msg):
    if not ok:raise SystemExit("1.106 reference geometry QA: "+msg)
B=load(C/"MutagenkolossModel.java")
P=load(C/"KristallpirscherModel.java")
D=load(C/"DaemmerlingModel.java")
main,glow=B.split("    public static LayerDefinition createGlowLayer()",1)
need('addBox(-7.6F, -6.8F, -9.3F, 15.2F, 12.0F, 15.1F)' in main,
     "boss 1.105 reduced skull should not regress")
def eye(name):
    piece=glow.split('head.addOrReplaceChild("'+name+'"',1)
    need(len(piece)==2,name+" emissive head bone missing")
    m=re.search(r"\.addBox\(([-\d.]+)F,\s*([-\d.]+)F,\s*([-\d.]+)F,\s*"
                r"([-\d.]+)F,\s*([-\d.]+)F,\s*([-\d.]+)F\)",
                piece[1][:240])
    need(m is not None,name+" emissive box missing")
    return tuple(float(x) for x in m.groups())
left=eye("eye_left")
right=eye("eye_right")
need(left[0]>=-7.6 and left[0]+left[3]<=7.6,
     "left eye floats outside smaller 15.2-pixel skull")
need(right[0]>=-7.6 and right[0]+right[3]<=7.6,
     "right eye floats outside smaller 15.2-pixel skull")
need(abs(left[0]+right[0]+left[3])<0.05 and left[0]<0<right[0],
     "eyes must be mirror-paired, not offset into cheeks")
need(left[1:]==right[1:],
     "both eyes must share y,z and physical dimensions")
need(left[2]+left[5]>-9.4 and left[2]<-9.3,
     "emissive eyes must meet real front face of boss skull")
need('addBox(-8.18F, -8.72F, -14.38F, 8.36F, 4.24F, 8.36F)' not in glow,
     "obsolete oversized glowing brow left floating outside new head")
need('addBox(-0.18F, -8.72F, -14.38F, 8.36F, 4.24F, 8.36F)' not in glow,
     "obsolete oversized glowing brow right floating outside new head")
for token in (
    'this.tailMid.xRot += 0.59F;',
    'PartDefinition head = body.addOrReplaceChild("head",',
    'addFourPetalCoreIris(body, true);',
    'addFourPetalCoreIris(body, false);',
    'addBattleWearVeins(body, true);',
    'addBattleWearVeins(body, false);',
    'addOrReplaceChild("stinger_bloom"',
    'private final ModelPart[] resonanceRibs;',
    'this.pawCrystalTips = new ModelPart[12];',
):
    need(token in B,"retain boss's tail, core, paws, battle cracks, both layers "+token)
need(B.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "two original separately UV-mapped Colossus skin/glow layers")
need('addBox(-3.8F, -4.0F, -2.8F, 7.6F, 10.0F, 6.2F)' not in P,
     "oversized solid shoulder cube still hides stalker silhouette")
for token in (
    'addBox(-3.25F, -3.8F, -2.65F, 6.5F, 3.8F, 5.3F)',
    'addBox(-2.35F, 1.05F, -2.3F, 4.7F, 2.8F, 4.6F)',
    'addBox(-1.55F, 5.0F, -3.15F, 3.1F, 4.9F, 2.8F)',
    'addOrReplaceChild("dorsal_fin_left"',
    'addOrReplaceChild("dorsal_fin_right"',
    'addOrReplaceChild("thorax_resonator"',
    'addOrReplaceChild("talon_a"',
    'addOrReplaceChild("talon_b"',
):
    need(token in P,"stalker segmented crystalline arms or original bone lost "+token)
for token in (
    "private final ModelPart leftRibRoot,rightRibRoot;",
    'this.leftRibRoot = this.body.getChild("rib_root_left");',
    'this.rightRibRoot = this.body.getChild("rib_root_right");',
    'body.addOrReplaceChild("rib_root_left"',
    'body.addOrReplaceChild("rib_root_right"',
    'this.leftRibRoot.zRot=-0.27F+pulse*0.075F+stride*0.035F;',
    'this.rightRibRoot.zRot=0.23F-pulse*0.063F-stride*0.025F;',
    'this.leftRibRoot.xRot-=0.18F+clawBeat*0.075F;',
    'this.rightRibRoot.xRot-=0.13F-clawBeat*0.055F;',
    'if(entity.isCropNibbling())',
    'this.feedingJaw.xRot=0.22F+Math.max(0.0F,clawBeat)*0.26F;',
    'addOrReplaceChild("back_hook_left"',
    'addOrReplaceChild("back_hook_right"',
):
    need(token in D,"Dämmerling living extra roots, crop reaction or old horror rig missing "+token)
for creature,dim in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    tex=R/"src/main/resources/assets/sporenwerk/textures/entity"
    with Image.open(tex/(creature+".png")) as skin, Image.open(tex/(creature+"_glow.png")) as effect:
        need(skin.size==(dim,dim) and effect.size==(dim,dim),
             "pixel-compatible matched atlas "+creature)
        rgba=effect.convert("RGBA")
        need(rgba.getpixel((0,0))[3]==0,
             "glowing mask must not make whole creature fullbright "+creature)
for s in (B,P,D):
    for forbidden in ("getChunk(", "getEntitiesOfClass(", "setBlock(", "destroyBlock(",
                      ".hurt(", "scheduleTick("):
        need(forbidden not in s,"renderer/model must never run server gameplay "+forbidden)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.106\.0['\"]",load(R/"build.gradle")),
     "Gradle version")
doc=load(R/"README.md")
need("Aktueller Entwicklungsstand: 1.106.0" in doc
     and "Version 1.106.0" in doc and "Version 1.105.0" in doc,
     "current and previous release documentation")
print("1.106 real Minecraft: mirrored in-skull glowing eyes, segmented Stalker shoulder, breathing root tendrils and all core abilities retain geometry.")
