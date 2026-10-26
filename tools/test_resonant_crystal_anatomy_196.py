#!/usr/bin/env python3
"""1.96 regression: true six-plate Colossus resonance cage and original Minecraft UVs,
plus newly modeled animated Kristallpirscher heart. No gameplay/world mutations."""
from pathlib import Path
from PIL import Image
import re,sys

R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
T=R/"src/main/resources/assets/sporenwerk/textures/entity"
def read(p): return p.read_text(encoding="utf-8")
def need(ok,reason):
    if not ok: raise SystemExit("Sporenwerk 1.96 resonance regression: "+reason)
b=read(C/"MutagenkolossModel.java")
p=read(C/"KristallpirscherModel.java")
boss=read(R/"src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java")

for token in (
    "private final ModelPart[] resonanceRibs;",
    "this.resonanceRibs = new ModelPart[]",
    'body.getChild("resonance_rib_left_0")',
    'body.getChild("resonance_rib_left_1")',
    'body.getChild("resonance_rib_left_2")',
    'body.getChild("resonance_rib_right_0")',
    'body.getChild("resonance_rib_right_1")',
    'body.getChild("resonance_rib_right_2")',
    "private static void addResonanceRibs(PartDefinition body, boolean glowing)",
    'String name = "resonance_rib_"',
    'rib.addOrReplaceChild("crystal_core", crystal, PartPose.ZERO);',
    "addResonanceRibs(body, false);",
    "addResonanceRibs(body, true);",
    "float ribFlare = breathCharge * 0.20F + stompCharge * 0.26F",
    "float lag = (2 - tier) * 0.10F;",
    "rib.zRot = sign * (0.12F + Math.max(0.0F, ribFlare - lag));",
    "Mth.sin(ageInTicks * 0.075F + tier * 0.85F)",
    "int crystalState = entity.getAttackState();",
    "int remaining = Math.max(0, entity.getAttackTicks());",
    "this.stingerProngs[0].zRot",
    "this.monolithLeft.zRot",
    "this.monolithRight.zRot",
    "this.pawCrystalTips = new ModelPart[12];",
    "this.tailMid.xRot += 0.59F;",
):
    need(token in b,"boss rib hierarchy or old animated crystals missing: "+token)
need(b.count("addResonanceRibs(body, false);")==1
     and b.count("addResonanceRibs(body, true);")==1,
     "six matching crystal ribs required in skin and emissive layers")
need(b.count("return LayerDefinition.create(mesh, 256, 256);")==2,
     "vanilla-compatible skin + glow atlas resolution must stay 256x256")
need(b.count('addOrReplaceChild("crystal_core"')==1,
     "each rib should have one narrow shared crystal child in helper")
need("CubeListBuilder basalt = glowing ? CubeListBuilder.create()" in b
     and "CubeListBuilder crystal = CubeListBuilder.create()" in b,
     "never make basalt armor fullbright")

for token in (
    "private final ModelPart thoraxResonator;",
    'this.thoraxResonator = this.body.getChild("thorax_resonator");',
    'body.addOrReplaceChild("thorax_resonator"',
    'resonator.addOrReplaceChild("thorax_shard_left"',
    'resonator.addOrReplaceChild("thorax_shard_right"',
    "float heartbeat = Mth.sin(ageInTicks * (0.105F + pursuit * 0.075F));",
    "float resonanceScale = 1.0F + (0.035F + pursuit * 0.075F)",
    "this.thoraxResonator.xScale = resonanceScale;",
    "this.thoraxResonator.yScale = resonanceScale;",
    "this.thoraxResonator.zScale = resonanceScale;",
    "this.thoraxResonator.xRot = 0.12F - pursuit * 0.06F;",
    "float pursuit = entity.isAggressive() ? 1.0F : 0.0F;",
    "this.leftTalonA.xRot",
    "this.rightTalonB.zRot",
    "LayerDefinition.create(mesh, 128, 128)",
):
    need(token in p,"stalker hunter chest and original animation missing: "+token)

for name in ("mutagenkoloss.png","mutagenkoloss_glow.png"):
    with Image.open(T/name) as img: tex=img.convert("RGBA")
    need(tex.size==(256,256),name+" original 256x256 must be preserved")
    if name.endswith("_glow.png"):
        # In new UV strip only thin cyan crystal veins are guaranteed fullbright.
        need(tex.getpixel((194,201))[3]>0,
             "resonator glow has no core vein pixel")
        need(tex.getpixel((200,216))[1]>150,
             "resonator glow must contain teal highlights")
    else:
        need(tex.getpixel((129,193))[3]==255,
             "resonator dark basalt skin UV must remain opaque")
        need(tex.getpixel((192,218))[3]==255,
             "original purple crystal rib skin must be visible")
        need(tex.getpixel((194,201))[1]>100,
             "resonant cyan cracks must be actually painted")

for v in ("getChunk(", "getChunkNow(", "setBlock(", "destroyBlock(", ".hurt(",
          "serverLevel.", "getEntitiesOfClass("):
    need(v not in b and v not in p,
         "models must never alter server/world state or scan entities: "+v)
for line in ("private static final int STOMP_WINDUP = 42;",
             "private static final int BREATH_WINDUP = 48;",
             "private static final int AWAKENING_WINDUP = 36;"):
    need(line in boss,"rib phase must match server-authoritative windup: "+line)
readme=read(R/"README.md")
need("Aktueller Entwicklungsstand: 1.96.0" in readme and
     "Version 1.96.0" in readme and "Version 1.95.0" in readme,
     "current/prior release documentation missing")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.96\.0['\"]",
               read(R/"build.gradle")) is not None,
     "Gradle artifact version not updated")
print("1.96 six articulated ribs in skin/glow, staggered 3D attack opening, original UVs and Pirscher beating crystal organ passed.")
