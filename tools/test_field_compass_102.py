#!/usr/bin/env python3
"""1.102 exact survival field-compass and Dämmerling bite structural regression.

Station targeting is read-only, bounded to already loaded chunks and excludes
dormant, cultivated, cured and Redstone-paused sources. New monster animations
only use an existing client-synchronized crop raid flag.
"""
from pathlib import Path
import json,re,sys

R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC=R/"src/main/java/de/sporenwerk"
def txt(path):return path.read_text(encoding="utf-8")
def need(ok, why):
    if not ok:raise SystemExit("Sporenwerk 1.102 field compass regression: "+why)
station=txt(SRC/"block/MutagenFieldControlStationBlock.java")
mob=txt(SRC/"entity/DaemmerlingEntity.java")
model=txt(SRC/"client/DaemmerlingModel.java")
renderer=txt(SRC/"client/DaemmerlingRenderer.java")

for signature in (
  "int nearestSpreadDx = 0, nearestSpreadDy = 0, nearestSpreadDz = 0;",
  "int nearestSpreadDistanceSq = -1;",
  "nearestSpreadDistanceSq,",
  "int nearestSpreadDx, int nearestSpreadDy, int nearestSpreadDz, int nearestSpreadDistanceSq",
  "int deltaY = y - center.getY();",
  "int distSq = dx * dx + dz * dz + deltaY * deltaY;",
  "if (nearestSpreadDistanceSq < 0 || distSq < nearestSpreadDistanceSq)",
  "nearestSpreadDx = dx;",
  "nearestSpreadDy = deltaY;",
  "nearestSpreadDz = dz;",
  "s.nearestSpreadDistanceSq() >= 0",
  "s.nearestSpreadDx(), s.nearestSpreadDy(), s.nearestSpreadDz()",
  "Math.round(Math.sqrt(s.nearestSpreadDistanceSq()))",
  'player.getItemInHand(hand).is(Items.COMPASS)',
  '"message.sporenwerk.fieldstation.compass_danger"',
  '"message.sporenwerk.fieldstation.compass_clear"',
  '"message.sporenwerk.fieldstation.compass_hint"',
  "emitCompassDiagnostic(serverLevel, pos, threat);",
  "private static void emitCompassDiagnostic(ServerLevel level, BlockPos center, boolean threat)",
):
    need(signature in station,"nearest spread and optional compass diagnostic: "+signature)
need(station.count("Survey s = survey(serverLevel, pos);")==1,
     "single pre-existing bounded station scan must serve report and compass")
need(station.count("for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++)")==4,
     "do not introduce fifth loaded-column scan (shutdown, restart, copper, survey)")
# A fourth survey may have additional board/signal loop in historical module?
survey=station[station.index("private static Survey survey(ServerLevel level, BlockPos center)"):]
need(survey.count("for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++)")==1,
     "bearing must use existing one survey loop")
need(survey.index("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;") <
     survey.index("BlockState bs = level.getBlockState(cursor);") <
     survey.index("if (bs.getBlock() instanceof MutationNodeBlock)") <
     survey.index("int distSq = dx * dx + dz * dz + deltaY * deltaY;"),
     "unloaded columns and unrelated blocks must never be compass targets")
need(survey.index("if (!nodeAuditData.isActive(cursor))") <
     survey.index("bs.getValue(MutationNodeBlock.POWERED)") <
     survey.index("if (nodeMode == 0) {") <
     survey.index("int distSq = dx * dx + dz * dz + deltaY * deltaY;"),
     "inactive, Redstone-paused and non-spread nodes MUST be excluded")
method=station[station.index("private static void emitCompassDiagnostic("):
               station.index("private static Survey survey(")]
for forbidden in ("setBlock(", "scheduleTick(", "destroyBlock(", "getChunk(", "getChunkNow(",
                  "getEntitiesOfClass(", "setValue(", ".hurt("):
    need(forbidden not in method,"pure visual compass may not mutate or scan: "+forbidden)
use=station[station.index("public InteractionResult use("):
            station.index("private static int convertSpreadToCultivation(")]
need(use.index("Items.COPPER_INGOT")<use.index("Items.AMETHYST_SHARD")<
     use.index("int silenced = emergencyShutdown(serverLevel, pos);")<
     use.index("Survey s = survey(serverLevel, pos);")<
     use.index("Items.COMPASS"),
     "old protected station control gestures must run first")
need(use.index("Items.COMPASS")<use.index("message.sporenwerk.fieldstation.header"),
     "compass must not duplicate long normal survey readout")
for suffix in ("compass_danger","compass_clear","compass_hint"):
    for lang in ("de_de.json","en_us.json"):
        data=json.loads(txt(R/"src/main/resources/assets/sporenwerk/lang"/lang))
        need("message.sporenwerk.fieldstation."+suffix in data,
             lang+" localized compass "+suffix)
        if suffix=="compass_danger":
            need(data["message.sporenwerk.fieldstation."+suffix].count("%s")==4,
                 lang+" relative x/y/z and integer distance")

for token in (
  "private final ModelPart feedingJaw;",
  'this.feedingJaw = this.head.getChild("hollow_jaw");',
  'head.addOrReplaceChild("hollow_jaw"',
  "this.feedingJaw.xRot=0.02F;",
  "if(entity.isCropNibbling()) {",
  "float clawBeat=Mth.sin(ageInTicks*0.52F);",
  "this.feedingJaw.xRot=0.22F+Math.max(0.0F,clawBeat)*0.26F;",
  "this.leftClaws.xRot=-0.65F+clawBeat*0.18F;",
  "this.rightClaws.xRot=-0.69F-clawBeat*0.18F;",
  "LayerDefinition.create(mesh,128,128)",
):
    need(token in model,"actual joint-bound synchronized jaw: "+token)
for token in (
  "if (entity.isCropNibbling()) {",
  "float bitePulse=0.08F+0.12F*",
  "pulse=Math.min(1.0F,pulse+bitePulse);",
  "RenderType.eyes(GLOW)",
  "textures/entity/daemmerling_glow.png",
):
    need(token in renderer,"actual selectively brighter eyes while feeding: "+token)
need("public boolean isCropNibbling() { return this.entityData.get(RAIDING_CROPS_VISUAL); }" in mob,
     "server-authoritative client synced state required")
for path in (SRC/"client/DaemmerlingModel.java",SRC/"client/DaemmerlingRenderer.java"):
    content=txt(path)
    for forbidden in ("getChunk(", "getEntitiesOfClass(", "setBlock(", "destroyBlock(",
                      "scheduleTick(", ".hurt(", "PacketDistributor"):
        need(forbidden not in content,"client shading must stay visual only "+forbidden)
gradle=txt(R/"build.gradle")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.102\.0['\"]",gradle),
     "ForgeGradle 1.102.0 version")
readme=txt(R/"README.md")
need("Aktueller Entwicklungsstand: 1.102.0" in readme and
     "Version 1.102.0" in readme and "Version 1.101.0" in readme,
     "current and previous README release must exist")
print("1.102 compass: one loaded-chunk station scan, four signed direction/distance outputs, safe action order and synchronized 3D Dämmerling jaw glow verified.")
