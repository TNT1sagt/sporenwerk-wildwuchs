#!/usr/bin/env python3
"""Sporenwerk 1.97 skin/glow mirror: non-damaging animated four-leaf chest iris
and hunter's independent beating heart splinters. All model-only APIs."""
from pathlib import Path
import re, sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def read(p):return p.read_text(encoding="utf-8")
def need(v,msg):
    if not v:raise SystemExit("1.97 crystal heart model regression: "+msg)
b=read(C/"MutagenkolossModel.java")
p=read(C/"KristallpirscherModel.java")
boss=read(R/"src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java")
for token in (
    "private final ModelPart[] coreIrisPetals;",
    "this.coreIrisPetals = new ModelPart[]",
    'body.getChild("core_iris_left")',
    'body.getChild("core_iris_right")',
    'body.getChild("core_iris_top")',
    'body.getChild("core_iris_bottom")',
    "private static void addFourPetalCoreIris(PartDefinition body, boolean glowing)",
    'String name = part == 0 ? "core_iris_left"',
    ': part == 1 ? "core_iris_right"',
    '"core_iris_top" : "core_iris_bottom";',
    'petal.addOrReplaceChild("iris_vein"',
    "CubeListBuilder shell = glowing ? CubeListBuilder.create()",
    "new ModelPart[] {",
    "addFourPetalCoreIris(body, false);",
    "addFourPetalCoreIris(body, true);",
    "float coreOpening = Math.max(breathCharge * 0.78F,",
    "Math.max(stompCharge * 0.34F, awakeningCharge * 0.90F));",
    "this.coreIrisPetals[0].yRot = -coreOpening * 0.63F;",
    "this.coreIrisPetals[1].yRot = coreOpening * 0.63F;",
    "this.coreIrisPetals[2].xRot = -coreOpening * 0.48F;",
    "this.coreIrisPetals[3].xRot = coreOpening * 0.48F;",
    "this.coreIrisPetals[i].xScale = scale;",
    "this.coreIrisPetals[i].yScale = scale;",
    "this.coreIrisPetals[i].zScale = scale;",
    "Mth.sin(ageInTicks * 0.17F)",
    "private final ModelPart[] resonanceRibs;",
    "float ribFlare = breathCharge * 0.20F",
    "this.stingerProngs[0].zRot",
    "this.monolithLeft.zRot",
    "this.monolithRight.zRot",
):
    need(token in b,"missing actual paired iris geometry, pose or legacy boss anim: "+token)
need(b.count("addFourPetalCoreIris(body, false);")==1
     and b.count("addFourPetalCoreIris(body, true);")==1,
     "each layer must bake its own four identical iris hinge bones")
need(b.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "vanilla-sized 256x256 skin/glow texture atlases required")
need(b.index('this.coreIrisPetals = new ModelPart[]')<
     b.index('this.resonanceRibs = new ModelPart[]'),
     "new model joints must initialize before or with established ribs")
for token in (
    "private final ModelPart thoraxShardLeft;",
    "private final ModelPart thoraxShardRight;",
    'this.thoraxResonator.getChild("thorax_shard_left")',
    'this.thoraxResonator.getChild("thorax_shard_right")',
    'resonator.addOrReplaceChild("thorax_shard_left"',
    'resonator.addOrReplaceChild("thorax_shard_right"',
    "float shardFlare = pursuit * (0.14F + 0.08F",
    "this.thoraxShardLeft.zRot = -0.36F - shardFlare;",
    "this.thoraxShardRight.zRot = 0.31F + shardFlare * 0.86F;",
    "this.thoraxShardLeft.yRot = 0.15F + shardFlare * 0.38F;",
    "this.thoraxShardRight.yRot = -0.10F - shardFlare * 0.34F;",
    "this.thoraxResonator.xScale = resonanceScale;",
    "this.thoraxResonator.yScale = resonanceScale;",
    "this.thoraxResonator.zScale = resonanceScale;",
    "float pursuit = entity.isAggressive() ? 1.0F : 0.0F;",
    "this.leftTalonA.xRot",
    "this.rightTalonB.zRot",
):
    need(token in p,"missing original and 1.97 stalker pulse/shard details: "+token)
for v in ("getChunk(", "getChunkNow(", "setBlock(", "destroyBlock(", ".hurt(",
          "getEntitiesOfClass(", "ServerLevel", "PacketDistributor"):
    need(v not in b and v not in p,
         "client-side visual mesh must be world-independent: "+v)
for x in ("private static final int STOMP_WINDUP = 42;",
          "private static final int BREATH_WINDUP = 48;",
          "private static final int AWAKENING_WINDUP = 36;"):
    need(x in boss,"core iris charge timings must match the server's real attack duration: "+x)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.97\.0['\"]",
               read(R/"build.gradle")) is not None,
     "Gradle must package version 1.97.0")
readme=read(R/"README.md")
need("Aktueller Entwicklungsstand: 1.97.0" in readme
     and "Version 1.97.0" in readme
     and "Version 1.96.0" in readme,
     "current and previous release documentation")
print("1.97 verified 4 matching Colossus shutter meshes, attack-linked synchronized openness and hunter heart 2-petal animation without world mutations.")
