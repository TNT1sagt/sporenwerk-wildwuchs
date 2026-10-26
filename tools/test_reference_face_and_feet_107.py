#!/usr/bin/env python3
"""1.107 real reference-anatomy proportions and old-state preservation.

Ensure dark Colossus face no longer sticks out outside downsized skull, and
its emission is reduced to transparent tiny rune strips; ensure two real toes
per leg are created by existing Forge leg loops, not decorative fake sprites.
"""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def rd(p):return p.read_text(encoding="utf-8")
def need(ok,msg):
    if not ok:raise SystemExit("Sporenwerk 1.107 anatomy regression: "+msg)
B=rd(C/"MutagenkolossModel.java")
P=rd(C/"KristallpirscherModel.java")
D=rd(C/"DaemmerlingModel.java")
need(B.count("    public static LayerDefinition createGlowLayer()")==1,"Boss distinct skin/glow bones required")
skin,glow=B.split("    public static LayerDefinition createGlowLayer()",1)
need('addBox(-7.6F, -6.8F, -9.3F, 15.2F, 12.0F, 15.1F)' in skin,"small 1.105 head retained")
for name in ("brow_armor_left","brow_armor_right","cheek_armor_left","cheek_armor_right"):
    need('head.addOrReplaceChild("'+name+'"' in skin,"opaque skull plate missing "+name)
    need('head.addOrReplaceChild("'+name+'"' in glow,"matched emblem bone missing "+name)

# Check symmetrical x spans for actual main layer plate, excluding eye
# coverage which was separately calculated and tested since 1.106.
def firstbox(source,name):
    section=source.split('head.addOrReplaceChild("'+name+'"',1)
    need(len(section)==2,"model part missing "+name)
    match=re.search(r'\.addBox\(([-\d.]+)F,\s*([-\d.]+)F,\s*([-\d.]+)F,\s*'
                    r'([-\d.]+)F,\s*([-\d.]+)F,\s*([-\d.]+)F\)',
                    section[1][:230])
    need(match is not None,"first cube not parseable "+name)
    return tuple(float(x) for x in match.groups())
for prefix in ("brow_armor","cheek_armor"):
    L=firstbox(skin,prefix+"_left")
    Q=firstbox(skin,prefix+"_right")
    need(L[0]>=-7.6 and L[0]+L[3]<=7.6 and
         Q[0]>=-7.6 and Q[0]+Q[3]<=7.6,
         prefix+" dark armor exceeds new skull")
    need(abs(L[0]+Q[0]+L[3])<0.01 and L[3:]==Q[3:],
         prefix+" left/right opaque face plates not mirrored")
    Lg=firstbox(glow,prefix+"_left")
    Rg=firstbox(glow,prefix+"_right")
    need(abs(Lg[0]+Rg[0]+Lg[3])<0.01,"glow rune not mirrored "+prefix)
    need(Lg[3]*Lg[4]*Lg[5] < L[3]*L[4]*L[5]*0.02,
         "fullbright "+prefix+" must be narrow carved lines not giant emissive basalt")
    need(Lg[0]>=-7.6 and Rg[0]+Rg[3]<=7.6,
         "emissive sliver outside skull x-span")
for token in (
 'addBox(-6.4F, -8.55F, -10.9F, 5.45F, 1.7F, 4.1F)',
 'addBox(0.95F, -8.55F, -10.9F, 5.45F, 1.7F, 4.1F)',
 'addBox(-6.35F, 1.95F, -11.95F, 3.75F, 2.55F, 3.0F)',
 'addBox(2.60F, 1.95F, -11.95F, 3.75F, 2.55F, 3.0F)',
):
    need(token in skin,"secondary slate plates should stay close to face "+token)
for token in (
    'head.addOrReplaceChild("eye_left"',
    'head.addOrReplaceChild("eye_right"',
    'addBox(-6.15F, -4.8F, -9.95F, 3.2F, 2.5F, 0.9F)',
    'addBox(2.95F, -4.8F, -9.95F, 3.2F, 2.5F, 0.9F)',
    'addFourPetalCoreIris(body, true);',
    'addFourPetalCoreIris(body, false);',
    'addOrReplaceChild("stinger_bloom"',
    'addBattleWearVeins(body, true);',
    'addBattleWearVeins(body, false);',
):
    need(token in B,"boss tracked eye, iris, stinger or cracked armor lost "+token)
need(B.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "opaque and narrow emissive boss trees share 256x256 UV")

for part,oldwide,news,claws in (
    (P,'addBox(-2.0F, 1.0F, -2.9F, 4.0F, 9.0F, 1.5F)',
     'addBox(-1.35F, 1.0F, -2.45F, 2.7F, 9.0F, 1.35F)',
     ('front_talon_left','front_talon_right')),
    (D,'addBox(-2.1F,2.0F,-2.8F,4.2F,8.9F,2.4F)',
     'addBox(-1.45F,2.0F,-2.5F,2.9F,8.9F,1.5F)',
     ('bark_tine_left','bark_tine_right')),
):
    need(oldwide not in part and news in part,
         "old wide shin box not narrowed to body "+oldwide)
    need("for (PartDefinition leg : new PartDefinition[]" in part,
         "both new feet must follow real humanoid leg ModelParts")
    for name in claws:
        need('leg.addOrReplaceChild("'+name+'"' in part,
             "both mirrored feet require independent 3D voxel claws: "+name)
    for forbidden in ("getChunk(", "setBlock(", "destroyBlock(", ".hurt(",
                      "getEntitiesOfClass(", "scheduleTick("):
        need(forbidden not in part,"client-only geometric feet must not touch gameplay "+forbidden)

need('addOrReplaceChild("dorsal_fin_left"' in P and
     'addOrReplaceChild("dorsal_fin_right"' in P and
     'addOrReplaceChild("thorax_resonator"' in P and
     'this.rightTalonB.zRot' in P,
     "Pirscher keeps mobile crystal fins, chest and hunt claws")
need('body.addOrReplaceChild("rib_root_left"' in D and
     'body.addOrReplaceChild("rib_root_right"' in D and
     'this.feedingJaw.xRot=0.22F+' in D,
     "Dämmerling preserves rooted chest, real biting jaw and root sway")
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for name,w in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    with Image.open(T/(name+".png")) as skinpng, Image.open(T/(name+"_glow.png")) as gl:
        need(skinpng.size==(w,w) and gl.size==(w,w),
             "each pair of Minecraft pixel and selective emission atlases must match")
        need(gl.convert("RGBA").getpixel((0,0))[3]==0,
             "no flat fullbright overlays across all painted faces")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.107\.0['\"]",rd(R/"build.gradle")),
     "ForgeGradle release")
documentation=rd(R/"README.md")
need("Aktueller Entwicklungsstand: 1.107.0" in documentation and
     "Version 1.107.0" in documentation and "Version 1.106.0" in documentation,
     "current release and previous history")
print("1.107 passed: boss mirrored in-skull rock and tiny selective glow veins; thin stalker/wood shins, both genuine 3D claw pairs on each walking leg.")
