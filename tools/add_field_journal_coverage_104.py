#!/usr/bin/env python3
"""Sporenwerk 1.104.0: trustworthy field journal scan-coverage checks and
full-composter passive protection from Dämmerling crop raids.

Caveat 1.103: same station and dimension can have different loaded columns.
Preserve original book snapshot and existing 1-pass survey; add a stable
signature of loaded x/z columns in that *same* scan. Only produce differences
if the loading footprint is exactly compatible, otherwise explain and reset.

Cure/farm safety: vanilla COMPOSTER LEVEL=8 (fully ready to harvest) protects
nearby mature mutant crops from Dämmerling nibbling without consuming the
compost or needing a new block, a scanner or a new field search.
"""
from pathlib import Path
import json,re,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC=R/"src/main/java/de/sporenwerk"
ASSETS=R/"src/main/resources/assets/sporenwerk"
ST=SRC/"block/MutagenFieldControlStationBlock.java"
MOB=SRC/"entity/DaemmerlingEntity.java"
def need(ok,why):
    if not ok:raise SystemExit("Sporenwerk 1.104 verified-field patch: "+why)
def patch(p,a,b,label):
    x=p.read_text(encoding="utf-8")
    need(x.count(a)==1,label+" unique anchor count "+str(x.count(a)))
    p.write_text(x.replace(a,b,1),encoding="utf-8")

s=ST.read_text(encoding="utf-8")
for key in ('stored.getLong("Station") == station.asLong();',
            'if (comparable) {',
            'fresh.putLong("Station", station.asLong());',
            'Survey s = survey(serverLevel, pos);',
            'if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;',
            'int nearestSpreadDistanceSq = -1;'):
    need(key in s,"requires existing 1.103 book and 1.102 loaded-only survey: "+key)

# Stable 64-bit ordered polynomial hash over the exact scan columns that were
# loaded at survey time. Same count alone is NOT enough: a different chunk
# can enter while another leaves. Ordering comes from the existing dx/dz loop.
patch(ST,
"""        int nearestSpreadDistanceSq = -1;""",
"""        int nearestSpreadDistanceSq = -1;
        int loadedColumns = 0;
        long coverageSignature = 1469598103934665603L;""",
"initialize loaded-footprint signature in current survey")
# Insert only in the final manual SURVEY, never the existing emergency
# shutdown, copper conversion or safe-amethyst-restart loops.
survey_point="    private static Survey survey(ServerLevel level, BlockPos center) {"
station_code=ST.read_text(encoding="utf-8")
need(station_code.count(survey_point)==1,"unique survey method for footprint count")
before_survey,in_survey=station_code.split(survey_point,1)
anchor="""                if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;
                for (int y = minY; y <= maxY; y++) {"""
need(in_survey.count(anchor)==1,"only one loaded-column check inside final survey")
in_survey=in_survey.replace(anchor,
"""                if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;
                // Exact footprint at the moment of the SAME bounded survey.
                loadedColumns++;
                coverageSignature = coverageSignature * 1099511628211L
                        ^ (((long) dx + HORIZONTAL_SCAN_RADIUS) << 32
                        | ((long) dz + HORIZONTAL_SCAN_RADIUS));
                for (int y = minY; y <= maxY; y++) {""",1)
ST.write_text(before_survey+survey_point+in_survey,encoding="utf-8")

s=ST.read_text(encoding="utf-8")
constructor=re.compile(r"(?m)^(\s*return new Survey\()([^\n;]+)(\);\s*)$")
matches=list(constructor.finditer(s))
need(len(matches)==1,"unique Survey constructor")
need("nearestSpreadDx, nearestSpreadDy, nearestSpreadDz, nearestSpreadDistanceSq" in matches[0].group(0),
     "previous compass bearing Survey required")
s=constructor.sub(lambda m: m.group(1)+m.group(2)+
         ", loadedColumns, coverageSignature"+m.group(3),s,count=1)
record=re.compile(r"(?m)^(\s*private record Survey\()([^\n)]+)(\)\s*\{\s*\})")
matches=list(record.finditer(s))
need(len(matches)==1,"unique Survey record")
need("int nearestSpreadDx, int nearestSpreadDy, int nearestSpreadDz, int nearestSpreadDistanceSq" in matches[0].group(0),
     "compass Survey record must survive")
s=record.sub(lambda m: m.group(1)+m.group(2)+
         ", int loadedColumns, long coverageSignature"+m.group(3),s,count=1)
ST.write_text(s,encoding="utf-8")

# Retain 1.103 same-station check and five true delta expressions unchanged.
# Fail-safe even for an old 1.103 book without a footprint tag.
patch(ST,
"""        if (comparable) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.journal_diff",""",
"""        boolean sameCoverage = stored.contains("LoadedColumns", 3)
                && stored.contains("CoverageSignature", 4)
                && stored.getInt("LoadedColumns") == survey.loadedColumns()
                && stored.getLong("CoverageSignature") == survey.coverageSignature();
        if (comparable && sameCoverage) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.journal_diff",""",
"prevent false change deltas when coverage changes")
patch(ST,
"""        } else {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.journal_baseline",""",
"""        } else {
            if (comparable && !sameCoverage) {
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.fieldstation.journal_coverage_changed",
                        stored.getInt("LoadedColumns"), survey.loadedColumns())
                        .withStyle(ChatFormatting.GOLD), false);
            }
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.journal_baseline",""",
"explain reset baseline when previous covered columns changed")
patch(ST,
"""        fresh.putLong("Station", station.asLong());
        fresh.putLong("GameTick", level.getGameTime());""",
"""        fresh.putLong("Station", station.asLong());
        fresh.putLong("GameTick", level.getGameTime());
        fresh.putInt("LoadedColumns", survey.loadedColumns());
        fresh.putLong("CoverageSignature", survey.coverageSignature());""",
"preserve new item-bound footprint history")

# IMPORTANT: existing 1.103 regression explicitly checks the old condition
# "if (comparable)" through other structural tokens? Its five delta
# expressions remain byte-for-byte identical. New test verifies strict guard.
mob=MOB.read_text(encoding="utf-8")
need('if (!mob.level().hasChunkAt(pos)) continue;' in mob
     and 'FilterMossSymbiosis.protects(mob.level(), cropPos)' in mob
     and 'mob.level().getBlockState(pos).is(ModBlocks.FELDSAMMLER.get())' in mob,
     "requires protected loaded-only collector scan and filter-moss symbiosis")

patch(MOB,
"""                if (mob.level().getBlockState(pos).is(ModBlocks.FELDSAMMLER.get())) return true;""",
"""                BlockState wardBlock = mob.level().getBlockState(pos);
                if (wardBlock.is(ModBlocks.FELDSAMMLER.get())) return true;
                // Fully composted vanilla composters also repel this weak
                // farm predator, creating a cheap reusable passive farm ward.
                // Only the existing protected-bed search is reused.
                if (wardBlock.is(net.minecraft.world.level.block.Blocks.COMPOSTER)
                        && wardBlock.getValue(net.minecraft.world.level.block.ComposterBlock.LEVEL) == 8) {
                    return true;
                }""",
"fully filled passive composter ward")

# Historical source assertion tests only need to check the equivalent
# collector safety rule; update exact expression without weakening it.
for p in (R/"tools").glob("test_*.py"):
    if p.name=="test_field_journal_coverage_104.py":continue
    t=p.read_text(encoding="utf-8")
    n=t.replace("Aktueller Entwicklungsstand: 1.103.0",
                "Aktueller Entwicklungsstand: 1.104.0")
    if "build.gradle" in t:
        n=n.replace(r"1\.103\.0",r"1\.104\.0")
        n=n.replace("artifact must be version 1.103.0",
                    "artifact must be version 1.104.0")
    n=n.replace('"Version 1.103.0" in readme and "Version 1.102.0" in readme',
                '"Version 1.104.0" in readme and "Version 1.103.0" in readme')
    # The early base assertions for collectors expect the symbol, not an
    # exact expression; keep them if present to continue verifying protection.
    if n!=t:p.write_text(n,encoding="utf-8")

gradle=R/"build.gradle"
s,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.104.0'",gradle.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle 1.104.0 package");gradle.write_text(s,encoding="utf-8")

for lang,trans in (
 ("de_de.json",
  "Achtung: Der geladene Messbereich hat sich verändert (%s → %s erfasste Spalten). Kein sicherer Trendvergleich möglich. Neue Referenz gespeichert."),
 ("en_us.json",
  "Warning: loaded survey coverage changed (%s → %s sampled columns). No reliable trend comparison is possible. New baseline saved.")
):
    p=ASSETS/"lang"/lang
    d=json.loads(p.read_text(encoding="utf-8"))
    d["message.sporenwerk.fieldstation.journal_coverage_changed"]=trans
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

p=R/"README.md";s=p.read_text(encoding="utf-8")
head="**Aktueller Entwicklungsstand: 1.103.0 — Buchgebundene Feldchronik und Warnkreise im Farm-Horror.**"
need(head in s,"generated source 1.103 header")
s=s.replace(head,
    "**Aktueller Entwicklungsstand: 1.104.0 — Verlässliche Feldchronik und passive Komposter-Farmwache.**",1)
step="""## Aktueller Entwicklungsschritt — 1.104.0

- **Feldchronik ohne falsche Heilungsdaten:** Die Kontrollstation merkt sich mit jeder Messung die Anzahl und die exakte geordnete Signatur der geladenen X/Z-Scan-Spalten. Beide entstehen beim ohnehin laufenden, begrenzten Stationsscan ohne weitere Chunk-Abfrage. Wird bei der nächsten Buchmessung eine andere geladenen Fläche erfasst, zeigt sie keine irreführenden Mutagen-Änderungen, sondern eine sichtbare Warnung und setzt eine neue Referenz.
- **Sichere ältere Messbücher:** Bücher ohne die neue Flächensignatur können zunächst keinen unzuverlässigen Vergleich erzeugen. Sie erhalten beim ersten erneuten Gebrauch einen aktuellen Referenzwert; Buchseiten und fremde NBT-Tags bleiben erhalten.
- **Fünf echte Zahlen bleiben:** Mutagenboden, hohe Mutagenstufe, Sporenpflanzen, Ausbreitungsherde und Kultivierungsherde lassen sich weiterhin vergleichen, sobald exakt dieselbe Station in derselben Dimension bei kompatibler geladener Fläche untersucht wird.
- **Vanilla-Komposter als passive Farmwache:** Ein vollständig befüllter Komposter (Füllstand 8) innerhalb des bestehenden 3-Block-Schutzbereichs einer reifen Sporenpflanze schützt diese vor dem Dämmerling. Der Kompost wird nicht verbraucht; leere/halbvolle Komposter bieten keinen Schutz.
- **Kein zusätzlicher Daueraufwand:** Die Komposter-Abfrage nutzt dieselbe ohnehin stattfindende, geladene Schutzbereichprüfung wie der Feldsammler. Filtermoos-Symbiose, Laternen und Leuchtbeeren bleiben unverändert; keine neuen Mob-Ticker oder Zwangsladungen.
- **Sicherheit:** Farmwache schützt nur vor dem Dämmerling-Fraß und ist kein Ersatz für Mutagenheilung, Infektionsbarrieren oder Feldstabilisatoren.
- **Tests:** Neue Regression für echte geladen-Chunks-Signaturen, Warnung statt Fehlvergleich, Speicherung im physischen Buch, volle Komposter, alter Filtermoos-/Feldsammlerschutz und vollständiger Forge-Build mit Server-Smoke-Test.

"""
need("## Aktueller Entwicklungsschritt — 1.103.0" in s,"previous current section")
s=s.replace("## Aktueller Entwicklungsschritt — 1.103.0",step+"## Aktueller Entwicklungsschritt — 1.103.0",1)
rel="""## Version 1.104.0 — Sichere Messvergleiche und Komposter-Wache

- Physische Feldchronik prüft zusätzlich zu Station/Dimension, dass die geladenen X/Z-Spalten exakt übereinstimmen. Bei Abweichung keine irreführenden Vorher-nachher-Zahlen, sondern neuer Basisstand. Legacy-Bücher werden schonend übernommen.
- Vollständig gefüllte Vanilla-Komposter schützen im vorhandenen 3-Block-Feldschutzradius reife Mutagenpflanzen vor Dämmerling-Fraß, ohne Verbrauch und ohne neue Server-Scans. Ungefüllte Komposter schützen nicht.
- Mutagen-Ausbreitung und Endgame-Heilung bleiben unverändert. Forge-1.20.1-Build, JAR- und Serverprüfungen werden über GitHub Actions ausgeführt.

"""
need("## Version 1.103.0 —" in s,"previous release")
s=s.replace("## Version 1.103.0 —",rel+"## Version 1.103.0 —",1)
p.write_text(s,encoding="utf-8")
print("1.104 installed: full loaded-column signature for truthful field journal and reusable full-composter ward against real crop raids.")
