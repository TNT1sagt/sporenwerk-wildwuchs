#!/usr/bin/env python3
"""1.103 structural safety regression: transferable real book-and-quill NBT
field observations and exactly two visual raid pulses, never extra tick loops."""
from pathlib import Path
import re,json,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC=R/"src/main/java/de/sporenwerk"
def rd(p):return p.read_text(encoding="utf-8")
def need(ok,m):
    if not ok:raise SystemExit("1.103 field journal QA: "+m)
station=rd(SRC/"block/MutagenFieldControlStationBlock.java")
mob=rd(SRC/"entity/DaemmerlingEntity.java")
control=station[station.index("public InteractionResult use("):
                station.index("private static int convertSpreadToCultivation(")]
for token in (
 "Survey s = survey(serverLevel, pos);",
 "hand == InteractionHand.MAIN_HAND",
 "player.getItemInHand(hand).is(Items.WRITABLE_BOOK)",
 "updateFieldJournal(serverLevel, pos, player, s);",
 "player.getItemInHand(hand).is(Items.COMPASS)",
 "int converted = convertSpreadToCultivation(serverLevel, pos);",
 "int restarted = restartSafeCultivation(serverLevel, pos);",
 "int silenced = emergencyShutdown(serverLevel, pos);",
 "message.sporenwerk.fieldstation.header",
):
    need(token in control,"old station actions + new item-specific journal "+token)
need(control.index("int converted = convertSpreadToCultivation(serverLevel, pos);")
     <control.index("int restarted = restartSafeCultivation(serverLevel, pos);")
     <control.index("int silenced = emergencyShutdown(serverLevel, pos);")
     <control.index("Survey s = survey(serverLevel, pos);")
     <control.index("Items.WRITABLE_BOOK")
     <control.index("Items.COMPASS")
     <control.index("message.sporenwerk.fieldstation.header"),
     "old rescue/stop routes must win, shared survey must run before journal")
need(station.count("Survey s = survey(serverLevel, pos);")==1,
     "do not scan twice for book or compass")
need(station.count("for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++)")==4,
     "one station survey + three pre-existing manual intervention loops only")
method=station[station.index("private static void updateFieldJournal("):
               station.index("private static void emitCompassDiagnostic(")]
for token in (
 'book.getOrCreateTag().getCompound(',
 '"SporenwerkFieldJournal"',
 'stored.contains("Dimension", 8)',
 'dimension.equals(stored.getString("Dimension"))',
 'stored.getLong("Station") == station.asLong()',
 'survey.soil() - stored.getInt("Soil")',
 'survey.highSoil() - stored.getInt("HighSoil")',
 'survey.crops() - stored.getInt("Crops")',
 'survey.spreadNodes() - stored.getInt("Spread")',
 'survey.cultivatedNodes() - stored.getInt("Cultivate")',
 'fresh.putString("Dimension", dimension);',
 'fresh.putLong("Station", station.asLong());',
 'fresh.putLong("GameTick", level.getGameTime());',
 'fresh.putInt("Soil", survey.soil());',
 'fresh.putInt("HighSoil", survey.highSoil());',
 'fresh.putInt("Crops", survey.crops());',
 'fresh.putInt("Spread", survey.spreadNodes());',
 'fresh.putInt("Cultivate", survey.cultivatedNodes());',
 'book.getOrCreateTag().put("SporenwerkFieldJournal", fresh);',
 'player.getInventory().setChanged();',
 'message.sporenwerk.fieldstation.journal_diff',
 'message.sporenwerk.fieldstation.journal_baseline',
 'message.sporenwerk.fieldstation.journal_hint',
):
    need(token in method,"journal compares safely and saves item-bound snapshot: "+token)
for forbidden in ("getChunk(", "getChunkNow(", "getEntitiesOfClass(",
                  "getBlockState(", "setBlock(", "destroyBlock(", "scheduleTick(",
                  "getPersistentData(", "getServer().", ".hurt(", "setPos(", "shrink("):
    need(forbidden not in method,"journal must never mutate/crawl world or player: "+forbidden)
need('book.shrink(' not in method and 'stack.shrink(' not in method,
     "book remains reusable")
for lang in ("de_de.json","en_us.json"):
    obj=json.loads(rd(R/"src/main/resources/assets/sporenwerk/lang"/lang))
    for k,n in (("journal_baseline",5),("journal_diff",5),("journal_hint",0)):
        key="message.sporenwerk.fieldstation."+k
        need(key in obj and obj[key].count("%s")==n,lang+" must translate five stats and hint "+k)

crop=mob[mob.index("private static final class CropThreatGoal extends Goal"):]
warning=crop[crop.index("private void emitRaidWarning("):
             crop.index("private boolean isMatureCrop(")]
for token in (
 "for (int sample = 0; sample < 12; sample++)",
 "double radius = urgent ? 1.35D : 0.72D;",
 "ParticleTypes.SOUL_FIRE_FLAME",
 "ParticleTypes.WARPED_SPORE",
 "level.sendParticles(urgent ? ParticleTypes.SOUL_FIRE_FLAME",
 "x + Math.cos(angle) * radius",
 "z + Math.sin(angle) * radius",
 "SoundEvents.AMETHYST_BLOCK_CHIME",
):
    need(token in warning,"two existing staged crop threat warnings "+token)
need(crop.count("emitRaidWarning(target, chewTicks == 20);")==1
     and crop.count("if (chewTicks == 8 || chewTicks == 20)")==1,
     "rings only at two existing raid moments")
for forbidden in ("setBlock(", "destroyBlock(", "getChunk(", "getEntitiesOfClass(",
                  "scheduleTick(", ".hurt(", "getEntities(", "spawn("):
    need(forbidden not in warning,"ring must be audiovisual only "+forbidden)
need("Items.GLOW_BERRIES" in crop and "Items.SOUL_LANTERN" in crop
     and "if (!mob.level().hasChunkAt(cropPos)) return true;" in crop,
     "counterplay and no unloaded chunk raids must survive")
need("mob.syncCropRaidPose(true);" in crop and "mob.syncCropRaidPose(false);" in crop,
     "1.101 synced crop pose must survive")
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.103\.0['\"]",rd(R/"build.gradle")) is not None,
     "Gradle 1.103.0")
readme=rd(R/"README.md")
need("Aktueller Entwicklungsstand: 1.103.0" in readme and
     "Version 1.103.0" in readme and "Version 1.102.0" in readme,
     "README release status and prior history")
print("1.103 passed: physical-book NBT journal, five same-station deltas, bounded single scan, old station actions, two safe no-damage raid warnings.")
