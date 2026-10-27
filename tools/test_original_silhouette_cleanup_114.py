#!/usr/bin/env python3
"""Sporenwerk 1.114 verifies subtraction, proportions and negative space."""
from pathlib import Path
from PIL import Image
import re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(v,m):
    if not v:raise SystemExit("1.114 original silhouette QA: "+m)
b=(C/"MutagenkolossModel.java").read_text(encoding="utf-8")
p=(C/"KristallpirscherModel.java").read_text(encoding="utf-8")
d=(C/"DaemmerlingModel.java").read_text(encoding="utf-8")
skin,glow=b.split("    public static LayerDefinition createGlowLayer()",1)
for old in ("addBox(-17.5F, -9.5F, -23.0F, 35.0F, 10.5F, 23.0F)",
            "addBox(-12.0F, -1.0F, -19.5F, 24.0F, 11.0F, 24.0F)",
            "addBox(-14.0F, -8.5F, 8.5F, 28.0F, 11.0F, 16.0F)"):
    need(old not in skin,"huge original stone body still filling silhouette "+old)
widths={"shoulder":("addBox(-12.5F, -9.5F, -23.0F, 25.0F, 10.5F, 23.0F)",25.0),
        "waist":("addBox(-8.5F, -1.0F, -19.5F, 17.0F, 11.0F, 24.0F)",17.0),
        "rear":("addBox(-10.5F, -8.5F, 8.5F, 21.0F, 11.0F, 16.0F)",21.0),
        "spine":("addBox(-5.5F, -1.5F, 4.0F, 11.0F, 7.0F, 6.5F)",11.0)}
for label,(token,width) in widths.items():need(token in skin,"new skinny "+label+" body box absent")
need(widths["waist"][1]<widths["shoulder"][1]
     and widths["waist"][1]<widths["rear"][1],"body must have pinched silhouette")
need('addSegmentedBeastMantle(body, false);' in skin
     and 'addSegmentedBeastMantle(body, true);' in glow,
     "existing paired matte 1.113 shoulder armor must remain")
need("paw.y = 12.0F - lift * 1.65F;" in b and
     'PartPose.offsetAndRotation(x, y + 10.0F, -24.6F' in b,
     "real planted leg and inset core must not regress")

start=p.index('PartDefinition growth = arm.addOrReplaceChild(name,')
end=p.index('growth.addOrReplaceChild("talon_a"',start)
growth=p[start:end]
cube=re.compile(r"\.addBox\(\s*(-?[\d.]+)F,\s*(-?[\d.]+)F,\s*(-?[\d.]+)F,\s*"
                r"([\d.]+)F,\s*([\d.]+)F,\s*([\d.]+)F\s*\)")
boxes=[tuple(map(float,m)) for m in cube.findall(growth)]
need(len(boxes)==3,"2 independent long bones plus one wrist bridge required")
left,right,bridge=boxes
need(right[0]-(left[0]+left[3])>=1.8,
     "genuine air must separate oversized shoulder sleeve bones")
need(max(left[3],right[3])<2.5 and bridge[3]<=3.0,
     "old super-wide arms must be narrower in actual geometry")
need('growth.addOrReplaceChild("talon_a"' in p
     and 'growth.addOrReplaceChild("talon_b"' in p
     and 'this.leftArm.xRot = 0.24F + quietStride * 0.17F;' in p,
     "two real talons + idle arms remain")

need('addBox(-3.7F,-5.0F,-2.6F,7.4F,2.7F,5.2F)' in d
     and 'addBox(-3.5F,0.0F,-2.4F,7.0F,2.0F,4.8F)' in d,
     "thin real woody ribcage missing")
need('addBox(-5.2F,-5.0F,-2.6F,10.4F,2.7F,5.2F)' not in d,
     "old giant bark shoulder plate still visible")
need('addOrReplaceChild("waist_root_left"' in d
     and 'addOrReplaceChild("waist_root_right"' in d
     and 'entity.isCropNibbling()' in d,
     "real lower-root forest horror and crop animation must persist")
for src in (b,p,d):
    for bad in ("getChunk(","setBlock(","destroyBlock(",".hurt(","scheduleTick("):
        need(bad not in src,"client-only change may not mutate gameplay "+bad)
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
for n,w in (("mutagenkoloss",256),("kristallpirscher",128),("daemmerling",128)):
    for suffix in ("","_glow"):
        with Image.open(T/(n+suffix+".png")) as im:
            need(im.size==(w,w),"Minecraft texture lost "+n+suffix)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.114\.0['\"]",
     (R/"build.gradle").read_text(encoding="utf-8")) is not None,"Gradle release")
doc=(R/"README.md").read_text(encoding="utf-8")
need("Aktueller Entwicklungsstand: 1.114.0" in doc
     and "Version 1.114.0" in doc
     and "Version 1.113.0" in doc,"README release history")
print("1.114 verified: actually reduced boss core, two gapped mineral bones and narrower real bark chest.")
