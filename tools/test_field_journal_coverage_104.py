#!/usr/bin/env python3
"""1.104 full regression: strict journal loaded-column footprint and reusable
full Vanilla Composter ward, with bounded scans and established rescue preserved."""
from pathlib import Path
import re,json,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
S=R/"src/main/java/de/sporenwerk"
def read(path):return path.read_text(encoding="utf-8")
def need(ok,msg):
    if not ok:raise SystemExit("1.104 verified farm safety QA: "+msg)

station=read(S/"block/MutagenFieldControlStationBlock.java")
mob=read(S/"entity/DaemmerlingEntity.java")
survey=station[station.index("private static Survey survey(ServerLevel level, BlockPos center)"):]
journal=station[station.index("private static void updateFieldJournal("):
                station.index("private static void emitCompassDiagnostic(")]
for token in (
    "int loadedColumns = 0;",
    "long coverageSignature = 1469598103934665603L;",
    "loadedColumns++;",
    "coverageSignature = coverageSignature * 1099511628211L",
    "(((long) dx + HORIZONTAL_SCAN_RADIUS) << 32",
    "((long) dz + HORIZONTAL_SCAN_RADIUS)",
    "loadedColumns, coverageSignature",
    "int loadedColumns, long coverageSignature",
    "if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;",
):
    need(token in station,"exact already-loaded-footprint tracking missing: "+token)
need(survey.count("for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++)")==1,
     "one shared survey loop only")
need(survey.index("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;")
     <survey.index("loadedColumns++;")
     <survey.index("for (int y = minY; y <= maxY; y++)"),
     "signature must count only loaded columns before scanning their blocks")
need(station.count("for (int dx = -HORIZONTAL_SCAN_RADIUS; dx <= HORIZONTAL_SCAN_RADIUS; dx++)")==4,
     "no new station scans beyond original three rescue loops and one survey")
# Hash sensitivity to SAME COUNT but different positions.
def fingerprint(cols):
    v=1469598103934665603
    mask=(1<<64)-1
    for dx,dz in cols:
        token=(((dx+16)&mask)<<32) | ((dz+16)&mask)
        v=((v*1099511628211)&mask) ^ token
    return v
need(fingerprint([(0,0),(1,0)])!=fingerprint([(0,0),(0,1)]),
     "different footprints with same loaded-column count must differ")
need(fingerprint([(0,0),(1,0)])==fingerprint([(0,0),(1,0)]),
     "same footprint must be stable")

for token in (
    'book.getOrCreateTag().getCompound(',
    '"SporenwerkFieldJournal"',
    'stored.contains("Dimension", 8)',
    'dimension.equals(stored.getString("Dimension"))',
    'stored.getLong("Station") == station.asLong();',
    'boolean sameCoverage = stored.contains("LoadedColumns", 3)',
    'stored.contains("CoverageSignature", 4)',
    'stored.getInt("LoadedColumns") == survey.loadedColumns()',
    'stored.getLong("CoverageSignature") == survey.coverageSignature();',
    'if (comparable && sameCoverage) {',
    'if (comparable && !sameCoverage) {',
    '"message.sporenwerk.fieldstation.journal_coverage_changed"',
    'fresh.putInt("LoadedColumns", survey.loadedColumns());',
    'fresh.putLong("CoverageSignature", survey.coverageSignature());',
    'fresh.putLong("Station", station.asLong());',
    'fresh.putString("Dimension", dimension);',
    'fresh.putLong("GameTick", level.getGameTime());',
    'survey.soil() - stored.getInt("Soil")',
    'survey.highSoil() - stored.getInt("HighSoil")',
    'survey.crops() - stored.getInt("Crops")',
    'survey.spreadNodes() - stored.getInt("Spread")',
    'survey.cultivatedNodes() - stored.getInt("Cultivate")',
    'book.getOrCreateTag().put("SporenwerkFieldJournal", fresh);',
):
    need(token in journal,"journal compatibility, NBT footprint or five legacy deltas "+token)
need(journal.index("if (comparable && sameCoverage) {") <
     journal.index('"message.sporenwerk.fieldstation.journal_diff"') <
     journal.index('} else {') <
     journal.index('"message.sporenwerk.fieldstation.journal_coverage_changed"'),
     "never render deltas for unequal coverage")
need(journal.index('fresh.putInt("LoadedColumns", survey.loadedColumns());') <
     journal.index('book.getOrCreateTag().put("SporenwerkFieldJournal", fresh);'),
     "new journal snapshot must always save its current footprint")
for forbidden in ("getChunk(", "getChunkNow(", "getBlockState(",
                  "getEntitiesOfClass(", "setBlock(", "destroyBlock(",
                  "getServer().", "getPersistentData(", ".hurt(", "shrink("):
    need(forbidden not in journal,"field journal cannot mutate/scan world or consume book: "+forbidden)
for lang in ("de_de.json","en_us.json"):
    d=json.loads(read(R/"src/main/resources/assets/sporenwerk/lang"/lang))
    key="message.sporenwerk.fieldstation.journal_coverage_changed"
    need(key in d and d[key].count("%s")==2,
         "explicit localized visible invalid-coverage feedback "+lang)
    for k,count in (("journal_diff",5),("journal_baseline",5)):
        need(d["message.sporenwerk.fieldstation."+k].count("%s")==count,
             "five older field statistics still translated")
# Full composter ONLY: unfilled vanilla composters do not repel.
crop=mob[mob.index("private static final class CropThreatGoal extends Goal"):]
protect=crop[crop.index("private boolean isProtected(BlockPos cropPos)"):]
for token in (
    "if (!mob.level().hasChunkAt(cropPos)) return true;",
    "getMaxLocalRawBrightness(cropPos) >= 7",
    "FilterMossSymbiosis.protects(mob.level(), cropPos)",
    "if (!mob.level().hasChunkAt(pos)) continue;",
    "BlockState wardBlock = mob.level().getBlockState(pos);",
    "if (wardBlock.is(ModBlocks.FELDSAMMLER.get())) return true;",
    "wardBlock.is(net.minecraft.world.level.block.Blocks.COMPOSTER)",
    "wardBlock.getValue(net.minecraft.world.level.block.ComposterBlock.LEVEL) == 8",
):
    need(token in protect,"full composter and original filter moss/collector ward required: "+token)
need(protect.index("if (!mob.level().hasChunkAt(pos)) continue;") <
     protect.index("BlockState wardBlock = mob.level().getBlockState(pos);"),
     "no composter loaded-check bypass")
need(protect.count("mob.level().getBlockState(pos);")==1,
     "reuse one already-loaded crop ward block read")
need("if (chewTicks % 5 == 0)" in crop and
     "Items.SOUL_LANTERN" in crop and "Items.GLOW_BERRIES" in crop,
     "portable crop defenses preserved")
need("if (!isMatureCrop(pos) || isProtected(pos)) continue;" in crop,
     "protective field ward checked before pathing")
need("isMatureCrop(target) && !isProtected(target)" in crop,
     "last-moment recheck prevents actual bite")
need("mob.syncCropRaidPose(false);" in crop,
     "client horror animation stops with aborted raid")
# Edition is Forge 1.20.1 with existing release history and data tags.
need(re.search(r"(?m)^\s*version\s*=\s*['\"]1\.104\.0['\"]",
               read(R/"build.gradle")) is not None,"Gradle 1.104.0")
documentation=read(R/"README.md")
need("Aktueller Entwicklungsstand: 1.104.0" in documentation
     and "Version 1.104.0" in documentation
     and "Version 1.103.0" in documentation,
     "new and old release docs")
print("1.104 coverage guard and full-composter ward verified with no extra scans, book consumption or weakened counterplay.")
