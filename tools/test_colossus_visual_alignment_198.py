#!/usr/bin/env python3
"""1.98 *visual alignment* regression: compatible skin+emissive roots, iris forward
of chest crystal, framed opening, smooth charge and no gameplay changes."""
from pathlib import Path
import re, sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
M=R/"src/main/java/de/sporenwerk/client/MutagenkolossModel.java"
S=M.read_text(encoding="utf-8")
def need(ok,why):
    if not ok:raise SystemExit("1.98 Colossus in-game visual QA: "+why)

# Verify both baked body ModelParts have identical position, not merely matching
# names. Version 1.97's original +9 glow root placed every effect 13 px too low.
section0,section1=S.split("    public static LayerDefinition createGlowLayer()",1)
pivot_pat=r'PartDefinition body = root\.addOrReplaceChild\("body",[\s\S]{0,900}?PartPose\.offset\(([-\d.]+)F, ([-\d.]+)F, ([-\d.]+)F\)'
m0=re.search(pivot_pat,section0)
m1=re.search(pivot_pat,section1)
need(m0 is not None and m1 is not None,"must parse two baked body root poses")
p0=tuple(float(v) for v in m0.groups())
p1=tuple(float(v) for v in m1.groups())
need(p0==(0.0,-4.0,0.0) and p1==p0,
     "opaque and glow body roots are MISALIGNED: "+str((p0,p1)))
need("PartPose.offset(0.0F, 9.0F, 0.0F)" not in
     section1[:section1.index("return LayerDefinition.create(mesh, 256, 256);")],
     "bad +9 pixel glow-body root survived")

for n in ("core_iris_left","core_iris_right","core_iris_top","core_iris_bottom"):
    need('body.getChild("'+n+'")' in S,"real 3D hinge missing "+n)
for token in (
    "private final ModelPart[] coreIrisPetals;",
    "private static void addFourPetalCoreIris(PartDefinition body, boolean glowing)",
    "addFourPetalCoreIris(body, false);",
    "addFourPetalCoreIris(body, true);",
    "float irisProgress = Math.max(breathCharge * 0.78F,",
    "irisProgress = Mth.clamp(irisProgress, 0.0F, 1.0F);",
    "float coreOpening = irisProgress * irisProgress * (3.0F - 2.0F * irisProgress);",
    "this.coreIrisPetals[0].yRot = -coreOpening * 0.63F;",
    "this.coreIrisPetals[1].yRot = coreOpening * 0.63F;",
    "this.coreIrisPetals[2].xRot = -coreOpening * 0.48F;",
    "this.coreIrisPetals[3].xRot = coreOpening * 0.48F;",
    "for (int corner = 0; corner < 4; corner++)",
    'String edgeName = "iris_rim_" + corner;',
    'rim.addOrReplaceChild("gem_edge"',
    "CubeListBuilder rimShell = glowing ? CubeListBuilder.create()",
    "PartPose.offset(sx * 9.4F, sy * 8.6F, -37.9F)",
):
    need(token in S,"existing or improved iris/rim feature missing: "+token)
need(S.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "opaque and glow 256x256 layers must remain separate")
need(S.count("addFourPetalCoreIris(body, false);")==1 and
     S.count("addFourPetalCoreIris(body, true);")==1,
     "identical iris architecture must be baked on both layers")

# The front of the chest glow crystal is -37.1 pixels relative to body; the
# iris shell pivots must be more negative (forward) than the brightest tip.
m=re.search(r'PartPose\.offsetAndRotation\(x, y, ([-\d.]+)F, 0\.0F, 0\.0F, 0\.0F\)',S)
need(m is not None,"physical iris hinge pose missing")
iris_z=float(m.group(1))
need(iris_z <= -38.0 and iris_z > -41.0,
     "four leaves must be IN FRONT of the core, not sunk into torso: "+str(iris_z))
need(iris_z < -37.1,"true iris silhouette must be visible against glowing core")
need("part == 0 ? \"core_iris_left\"" in S,"not a decorative static texture")

# Multiple old systems stay alive while the small model fix changes no server.
for token in (
    "private final ModelPart[] resonanceRibs;",
    "this.stingerProngs[0].zRot",
    "this.pawCrystalTips = new ModelPart[12];",
    "this.monolithLeft.zRot",
    "this.tailMid.xRot += 0.59F;",
    "this.crystalCrownLeft.zRot",
    "this.lowerJaw.xRot",
):
    need(token in S,"legacy Colossus boss anatomy/animation missing: "+token)
for forbidden in ("getChunk(", "getChunkNow(", "getEntitiesOfClass(", "serverLevel.",
                  "destroyBlock(", "setBlock(", "teleportTo(", ".hurt(", "PacketDistributor"):
    need(forbidden not in S,"visual repair may not mutate game/server: "+forbidden)
b=(R/"build.gradle").read_text(encoding="utf-8")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.98\.0['\"]",b) is not None,
     "Forge Gradle version must package 1.98.0")
r=(R/"README.md").read_text(encoding="utf-8")
need("Aktueller Entwicklungsstand: 1.98.0" in r
     and "Version 1.98.0" in r and "Version 1.97.0" in r,
     "new/current release notes needed")
print("1.98 verified: identical model-space roots (-4), front-mounted smooth iris, four framed rim gems, preserved attacks and animation integrity.")
