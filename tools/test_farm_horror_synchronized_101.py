#!/usr/bin/env python3
"""Sporenwerk 1.101 regressions: synced true crop-raiding pose, all rescue/end
paths and three nonpersistent, scanner-free infection node selection rings."""
from pathlib import Path
import re,sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC=ROOT/"src/main/java/de/sporenwerk"
def read(p):return p.read_text(encoding="utf-8")
def need(ok,msg):
    if not ok:raise SystemExit("1.101 real field-horror QA: "+msg)
mob=read(SRC/"entity/DaemmerlingEntity.java")
model=read(SRC/"client/DaemmerlingModel.java")
node=read(SRC/"block/MutationNodeBlock.java")
for s in (
 "SynchedEntityData.defineId(DaemmerlingEntity.class, EntityDataSerializers.BOOLEAN)",
 "private static final EntityDataAccessor<Boolean> RAIDING_CROPS_VISUAL",
 "public boolean isCropNibbling() { return this.entityData.get(RAIDING_CROPS_VISUAL); }",
 "private void syncCropRaidPose(boolean eating)",
 "this.entityData.get(RAIDING_CROPS_VISUAL) != eating",
 "this.entityData.set(RAIDING_CROPS_VISUAL, eating);",
 "protected void defineSynchedData()",
 "super.defineSynchedData();",
 "this.entityData.define(RAIDING_CROPS_VISUAL, false);",
 "public boolean isRaidingCrops() { return this.raidingCrops; }",
 "mob.raidingCrops = true;",
 "mob.raidingCrops = false;",
 "mob.syncCropRaidPose(true);",
 "mob.syncCropRaidPose(false);",
):
    need(s in mob,"missing original server field state or synced client state "+s)
need(mob.count("mob.syncCropRaidPose(true);")==1,"one active feeding entry")
need(mob.count("mob.syncCropRaidPose(false);")==mob.count("mob.raidingCrops = false;"),
     "all states (walk/stop/bite/lantern/berry) must clear visual pose")
crop=mob[mob.index("private static final class CropThreatGoal extends Goal"):]
need(crop.index("mob.syncCropRaidPose(true);")<
     crop.index("if (++chewTicks >= 30)"),
     "client feeding only begins beside a real mature crop")
need("repelFromLantern(guard, target);" in crop and
     "Items.GLOW_BERRIES" in crop and "Items.SOUL_LANTERN" in crop and
     "mob.level().destroyBlock(target, false, mob);" in crop,
     "all existing counterplay retained")
need(crop.count("getEntitiesOfClass(")==2,
     "must reuse one guarded rescue scan and existing nearby player alert scan")
need("if (!mob.level().hasChunkAt(cropPos)) return true;" in crop,
     "must never load unsafe field chunks")
for s in (
 "if(entity.isCropNibbling()) {",
 "float clawBeat=Mth.sin(ageInTicks*0.52F);",
 "this.body.xRot+=0.43F;",
 "this.head.xRot+=0.31F;",
 "this.leftArm.xRot=-1.13F+clawBeat*0.13F;",
 "this.rightArm.xRot=-1.27F-clawBeat*0.13F;",
 "this.leftClaws.xRot=-0.65F+clawBeat*0.18F;",
 "this.rightClaws.xRot=-0.69F-clawBeat*0.18F;",
 "this.leftHook.zRot-=0.08F;",
 "this.rightHook.zRot+=0.09F;",
 "super.setupAnim(entity,limbSwing,limbSwingAmount,ageInTicks,netHeadYaw,headPitch)",
 "LayerDefinition.create(mesh,128,128)",
):
    need(s in model,"true voxel feeding animation missing: "+s)
for s in (
 "emitModeSelectionRing(serverLevel, pos, nextMode);",
 "private static void emitModeSelectionRing(ServerLevel level, BlockPos pos, int mode)",
 "if (mode < 0 || mode > 2) return;",
 "for (int sample=0;sample<12;sample++)",
 "double radius=mode==0?2.15D:mode==1?1.65D:1.05D;",
 "mode==0 ? ParticleTypes.REVERSE_PORTAL",
 "mode==1 ? ParticleTypes.HAPPY_VILLAGER : ParticleTypes.SMOKE",
 "mode==0 ? ParticleTypes.SOUL_FIRE_FLAME : ParticleTypes.END_ROD",
 "if (sample%3==0 && mode!=2)",
 'int nextMode = (state.getValue(MODE) + 1) % 3;',
 'case 1 -> "message.sporenwerk.mutation.node_cultivation"',
 'case 2 -> "message.sporenwerk.mutation.node_dormant"',
 "MutationField.spreadFromNode(level, pos, random);",
 "MutationField.cultivateNearbyCrops(level, pos, random);",
):
    need(s in node,"mode ring or protected active/dormant operation missing "+s)
need(node.count("emitModeSelectionRing(serverLevel, pos, nextMode);")==1,
     "mode ring only on manual switch, never on tick")
method=node[node.index("private static void emitModeSelectionRing("):
            node.index("public boolean isRandomlyTicking(")]
for bad in ("getChunk(", "getChunkNow(", "getEntitiesOfClass(", "setBlock(", "destroyBlock(", ".hurt(", "scheduleTick("):
    need(bad not in method,"ring must only be visual with no extra work: "+bad)
for bad in ("getChunk(", "getChunkNow(", "getEntitiesOfClass(", "setBlock(", "destroyBlock("):
    need(bad not in model,"client monster pose may never modify/load world: "+bad)
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.101\.0['\"]",
     read(ROOT/"build.gradle")) is not None,
     "release version must be 1.101")
readme=read(ROOT/"README.md")
need("Aktueller Entwicklungsstand: 1.101.0" in readme and
     "Version 1.101.0" in readme and "Version 1.100.0" in readme,
     "new and previous release documentation")
print("1.101 true server-synced biting pose, five safe clear paths, lantern/berry defenses and 3 visual node mode rings passed.")
