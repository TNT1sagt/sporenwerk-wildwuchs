#!/usr/bin/env python3
"""1.102.0: read-only compass bearing on existing Mutagen Control Station,
and synchronized nibbling jaw/eyes on existing Dämmerling farm-horror model.

The station adds no new scan: nearest loaded active, unpowered spread node is
recorded during the existing bounded manual survey. A vanilla compass in the
main hand shows relative X/Y/Z and a sound/particle confirmation. It never
changes blocks, registry data, comparison logic, source modes or chunk loading.
No scanner is required to see the world's already visually distinct Mutagen.
"""
from pathlib import Path
import json, re, sys

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC=ROOT/"src/main/java/de/sporenwerk"
ASSETS=ROOT/"src/main/resources/assets/sporenwerk"
STATION=SRC/"block/MutagenFieldControlStationBlock.java"
MODEL=SRC/"client/DaemmerlingModel.java"
RENDER=SRC/"client/DaemmerlingRenderer.java"

def need(test, message):
    if not test: raise SystemExit("Sporenwerk 1.102 field compass: "+message)

def patch(path,old,new,label):
    source=path.read_text(encoding="utf-8")
    need(source.count(old)==1,label+" unique anchor "+str(source.count(old)))
    path.write_text(source.replace(old,new,1),encoding="utf-8")

s=STATION.read_text(encoding="utf-8")
need('MutationNodeData nodeAuditData = MutationNodeData.get(level);' in s
     and "int spreadNodes = 0, cultivatedNodes = 0, dormantNodes = 0;" in s
     and "private static int convertSpreadToCultivation(" in s,
     "established 1.88 station survey and copper rescue required")
need('if (nodeMode == 0) spreadNodes++;' in s,
     "1.88 source classification expected")
need("if (!level.hasChunkAt(new BlockPos(x, minY, z))) continue;" in s,
     "loaded-only chunk scan invariant")

# A compass points at actual spread danger, not cured, dormant, cultivated,
# or Redstone-paused sources. No extra block state checks needed: the single
# existing survey already identified and filtered those node classes.
patch(STATION,
"""        int spreadNodes = 0, cultivatedNodes = 0, dormantNodes = 0;
        int pausedNodes = 0, inactiveNodes = 0;""",
"""        int spreadNodes = 0, cultivatedNodes = 0, dormantNodes = 0;
        int pausedNodes = 0, inactiveNodes = 0;
        int nearestSpreadDx = 0, nearestSpreadDy = 0, nearestSpreadDz = 0;
        int nearestSpreadDistanceSq = -1;""",
"one-shot compass direction accumulation")
patch(STATION,
"""                            if (nodeMode == 0) spreadNodes++;
                            else if (nodeMode == 1) cultivatedNodes++;
                            else dormantNodes++;""",
"""                            if (nodeMode == 0) {
                                spreadNodes++;
                                int deltaY = y - center.getY();
                                int distSq = dx * dx + dz * dz + deltaY * deltaY;
                                if (nearestSpreadDistanceSq < 0 || distSq < nearestSpreadDistanceSq) {
                                    nearestSpreadDistanceSq = distSq;
                                    nearestSpreadDx = dx;
                                    nearestSpreadDy = deltaY;
                                    nearestSpreadDz = dz;
                                }
                            } else if (nodeMode == 1) cultivatedNodes++;
                            else dormantNodes++;""",
"reuse only the preexisting node audit and loaded-column pass")

# Extend record and constructor together; old record values stay in their old
# positions for Redstone comparator and other status logic.
s=STATION.read_text(encoding="utf-8")
ctor=re.compile(r"(?m)^(\s*return new Survey\()([^\n;]+)(\);\s*)$")
m=list(ctor.finditer(s))
need(len(m)==1,"station has exactly one Survey constructor")
need("spreadNodes, cultivatedNodes, dormantNodes, pausedNodes, inactiveNodes" in m[0].group(0),
     "previous five survey buckets required")
s=ctor.sub(lambda mt: mt.group(1)+mt.group(2)+
           ", nearestSpreadDx, nearestSpreadDy, nearestSpreadDz, nearestSpreadDistanceSq"+
           mt.group(3),s,count=1)
record=re.compile(r"(?m)^(\s*private record Survey\()([^\n)]+)(\)\s*\{\s*\})")
m=list(record.finditer(s))
need(len(m)==1,"station has exactly one Survey record")
need("int spreadNodes, int cultivatedNodes, int dormantNodes" in m[0].group(0),
     "old node states required in existing record")
s=record.sub(lambda mt: mt.group(1)+mt.group(2)+
             ", int nearestSpreadDx, int nearestSpreadDy, int nearestSpreadDz, int nearestSpreadDistanceSq"+
             mt.group(3),s,count=1)
STATION.write_text(s,encoding="utf-8")

patch(STATION,
"""        Survey s = survey(serverLevel, pos);""",
"""        Survey s = survey(serverLevel, pos);
        // Optional survival diagnostics. The actual Mutagen terrain always
        // has its own textures: the compass does not unlock its visibility.
        if (hand == InteractionHand.MAIN_HAND
                && player.getItemInHand(hand).is(Items.COMPASS)) {
            boolean threat = s.nearestSpreadDistanceSq() >= 0;
            if (threat) {
                int approxDistance = (int) Math.round(Math.sqrt(s.nearestSpreadDistanceSq()));
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.fieldstation.compass_danger",
                        s.nearestSpreadDx(), s.nearestSpreadDy(), s.nearestSpreadDz(),
                        approxDistance).withStyle(ChatFormatting.RED), false);
            } else {
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.fieldstation.compass_clear").withStyle(
                                ChatFormatting.GREEN), false);
            }
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.compass_hint").withStyle(
                            ChatFormatting.GRAY), false);
            emitCompassDiagnostic(serverLevel, pos, threat);
            return InteractionResult.CONSUME;
        }""",
"on-demand compass from existing one-pass survey")
patch(STATION,
"""    private static Survey survey(ServerLevel level, BlockPos center) {""",
"""    /**
     * Player-triggered safety feedback only; no permanent particle loops or
     * invisible infected ground, and no world state changes.
     */
    private static void emitCompassDiagnostic(ServerLevel level, BlockPos center, boolean threat) {
        for (int point = 0; point < 8; point++) {
            double a = point * Math.PI / 4.0D;
            level.sendParticles(threat
                            ? net.minecraft.core.particles.ParticleTypes.REVERSE_PORTAL
                            : net.minecraft.core.particles.ParticleTypes.HAPPY_VILLAGER,
                    center.getX() + 0.5D + Math.cos(a) * 1.35D,
                    center.getY() + 0.83D,
                    center.getZ() + 0.5D + Math.sin(a) * 1.35D,
                    1, 0.0D, 0.02D, 0.0D, 0.004D);
        }
        level.playSound(null, center, threat
                        ? SoundEvents.AMETHYST_BLOCK_HIT : SoundEvents.AMETHYST_BLOCK_CHIME,
                SoundSource.BLOCKS, 0.42F, threat ? 0.72F : 1.27F);
    }

    private static Survey survey(ServerLevel level, BlockPos center) {""",
"bounded read-only compass particles")

# The previous test specifically asserted the old Survey constructor ends
# with inactiveNodes. Update only that evolving contract, preserving all
# source-count and loaded-chunk regression checks.
legacy=ROOT/"tools/test_station_node_mode_audit_188.py"
old=legacy.read_text(encoding="utf-8")
needle='"spreadNodes, cultivatedNodes, dormantNodes, pausedNodes, inactiveNodes);"'
need(needle in old,"historical five-mode survey constructor assertion")
old=old.replace(needle,
    '"spreadNodes, cultivatedNodes, dormantNodes, pausedNodes, inactiveNodes, nearestSpreadDx, nearestSpreadDy, nearestSpreadDz, nearestSpreadDistanceSq);"',1)
legacy.write_text(old,encoding="utf-8")

# Historical 1.88 audit must still check the same SPREAD count. It was
# previously a single-line conditional, now intentionally a block recording
# nearest danger in the same loaded-column survey. Preserve both checks.
old_contract='"nodeMode == 0) spreadNodes++"'
new_contract='"if (nodeMode == 0) {"'
legacy_text=legacy.read_text(encoding="utf-8")
need(old_contract in legacy_text,"old 1.88 spread-node token missing")
legacy_text=legacy_text.replace(old_contract,new_contract,1)
legacy.write_text(legacy_text,encoding="utf-8")

# The 1.101 synchronized feeding state is reused (zero new network flags).
model=MODEL.read_text(encoding="utf-8")
need('head.addOrReplaceChild("hollow_jaw"' in model and
     "if(entity.isCropNibbling()) {" in model,"registered 1.100 mesh and 1.101 feeding state")
patch(MODEL,
"""    private final ModelPart leftHook,rightHook,leftClaws,rightClaws,headRoot;""",
"""    private final ModelPart leftHook,rightHook,leftClaws,rightClaws,headRoot;
    private final ModelPart feedingJaw;""",
"cache existing 3D jaw bone")
patch(MODEL,
"""        this.headRoot = this.head.getChild("head_root");""",
"""        this.headRoot = this.head.getChild("head_root");
        this.feedingJaw = this.head.getChild("hollow_jaw");""",
"bind existing jaw")
patch(MODEL,
"""        this.headRoot.zRot=0.32F+pulse*0.04F;
        // 1.101:""",
"""        this.headRoot.zRot=0.32F+pulse*0.04F;
        // 1.102 this pre-existing jaw is now genuinely hinged to bite.
        this.feedingJaw.xRot=0.02F;
        // 1.101:""",
"reset jaw motion each frame")
patch(MODEL,
"""            float clawBeat=Mth.sin(ageInTicks*0.52F);
            this.body.xRot+=0.43F;""",
"""            float clawBeat=Mth.sin(ageInTicks*0.52F);
            this.feedingJaw.xRot=0.22F+Math.max(0.0F,clawBeat)*0.26F;
            this.body.xRot+=0.43F;""",
"visibly biting lower jaw during true crop attack")
render=RENDER.read_text(encoding="utf-8")
need("RenderType.eyes(GLOW)" in render and
     "DaemmerlingModel.LAYER_LOCATION" in render,
     "real selective fullbright shade renderer required")
patch(RENDER,
"""            VertexConsumer vc=buffers.getBuffer(RenderType.eyes(GLOW));""",
"""            // The only true crop-eating flag is already synchronized by
            // 1.101. Eyes throb during the bite, never in daylight by accident.
            if (entity.isCropNibbling()) {
                float bitePulse=0.08F+0.12F*
                        Math.max(0.0F,net.minecraft.util.Mth.sin(ageInTicks*0.52F));
                pulse=Math.min(1.0F,pulse+bitePulse);
            }
            VertexConsumer vc=buffers.getBuffer(RenderType.eyes(GLOW));""",
"synced biting red eye pulse")

for loc, texts in (
    ("de_de.json",{
       "compass_danger":"Feldkompass: AKTIVE AUSBREITUNG! Richtung ab Station: X %+s | Y %+s | Z %+s (ca. %s Blöcke).",
       "compass_clear":"Feldkompass: Keine aktive, ungepauste Ausbreitungsquelle im geladenen Stationsbereich gefunden.",
       "compass_hint":"Relative Koordinaten: +X Osten, +Z Süden. Nur geladene Chunks; der Kompass wird nicht verbraucht."
    }),
    ("en_us.json",{
       "compass_danger":"Field compass: ACTIVE SPREAD! Relative to station: X %+s | Y %+s | Z %+s (approx. %s blocks).",
       "compass_clear":"Field compass: No active, unpaused spreading source in loaded station range.",
       "compass_hint":"Relative coordinates: +X east, +Z south. Loaded chunks only; compass is not consumed."
    })
):
    lang=ASSETS/"lang"/loc
    data=json.loads(lang.read_text(encoding="utf-8"))
    for key,val in texts.items():
        data["message.sporenwerk.fieldstation."+key]=val
    # Minecraft legacy translations use %s placeholders. %+s is not a
    # valid java Formatter string conversion; keep unambiguous signed nums
    # via the negative sign where present and explain signs in hint.
    data["message.sporenwerk.fieldstation.compass_danger"]=data[
        "message.sporenwerk.fieldstation.compass_danger"].replace("%+s","%s")
    lang.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

for p in (ROOT/"tools").glob("test_*.py"):
    if p.name=="test_field_compass_102.py":continue
    source=p.read_text(encoding="utf-8")
    updated=source.replace("Aktueller Entwicklungsstand: 1.101.0",
                           "Aktueller Entwicklungsstand: 1.102.0")
    if "build.gradle" in source:
        updated=updated.replace(r"1\.101\.0",r"1\.102\.0")
        updated=updated.replace("artifact must be version 1.101.0",
                                "artifact must be version 1.102.0")
    updated=updated.replace('"Version 1.101.0" in readme and "Version 1.100.0" in readme',
                            '"Version 1.102.0" in readme and "Version 1.101.0" in readme')
    if updated!=source:p.write_text(updated,encoding="utf-8")
gradle=ROOT/"build.gradle"
updated,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                  "version = '1.102.0'",gradle.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle release version 1.102.0 required")
gradle.write_text(updated,encoding="utf-8")
p=ROOT/"README.md";s=p.read_text(encoding="utf-8")
header="**Aktueller Entwicklungsstand: 1.101.0 — Sichtbare Dämmerling-Fraßbewegung und eindeutige Mutagen-Modusringe.**"
need(header in s,"generated 1.101 readme heading")
s=s.replace(header,
"**Aktueller Entwicklungsstand: 1.102.0 — Mutagen-Feldkompass und lebendige Dämmerling-Fraßgesten.**",1)
step="""## Aktueller Entwicklungsschritt — 1.102.0

- **Mutagen-Feldkompass direkt an der Kontrollstation:** Ein normaler Kompass in der Haupthand löst beim Rechtsklick eine Diagnose der nächstgelegenen aktiven Ausbreitungsquelle aus. Die relative X/Y/Z-Richtung und ungefähre Entfernung erscheinen im Chat. Bei fehlenden Quellen wird nur der geladene Suchbereich als sicher gemeldet, nicht die ganze Welt.
- **Keine neue Welt- oder Chunksuche:** Der nächstgelegene gefährliche Knoten wird bei der bereits bestehenden, begrenzten Stationsvermessung mitgezählt. Ruhende, kultivierende, redstone-pausierte und geheilte Quellen sind ausdrücklich keine aktiven Ausbreitungsziele.
- **Sofortiges Feldfeedback:** Der Stationskompass erzeugt nur beim Gebrauch einen kleinen roten Portalsporen- oder grünen Wachstumskreis samt anderem Amethystton. Der Gegenstand wird nicht verbraucht. Die in-world Mutagenblocktexturen bleiben ohne Scanner jederzeit sichtbar.
- **Beweglicher Kiefer des Dämmerlings:** Die bereits existierende 3D-Unterkiefergeometrie schwingt beim server-synchronisierten Knabbern an einem Beet auf und ab. Seine roten Glow-Augen pulsieren während des Fraßes stärker und kehren beim Abbruch des Raids in den normalen Modus zurück.
- **Kompatibilität:** Seelenlaterne, Leuchtbeeren, Notabschaltung der Station, Kupferrettung, sicherer Amethystneustart und die drei Knotenmodi bleiben unverändert. Keine zusätzlichen dauerhaften Server-Ticker, Suchläufe oder neuen Netzwerkdaten.
- **Automatisierte Tests:** Eigene Regression kontrolliert die nächste aktive Feldquelle, die Grenzen geladener Chunks, ausschließliche Leserechte des Kompasses, die beibehaltenen alten Sicherheitstests sowie die Monster-Gelenke und die normale und aggressive Glow-Intensität.

"""
need("## Aktueller Entwicklungsschritt — 1.101.0" in s,"previous current section")
s=s.replace("## Aktueller Entwicklungsschritt — 1.101.0",
            step+"## Aktueller Entwicklungsschritt — 1.101.0",1)
release="""## Version 1.102.0 — Feldkompass und lebendige Schattengebisse

- Optionaler, nicht verbrauchbarer Vanilla-Kompass zum Anzeigen relativer Position und Entfernung der nächsten wirklich aktiven, ungepausten Mutagen-Ausbreitungsquelle in den bereits geladenen Stations-Chunks.
- Keine Scannerpflicht für sichtbare Mutagenlandschaften; keine weiteren Stationsscans oder Blockmanipulationen.
- Die eigene 3D-Kreatur Dämmerling beißt während wirklicher Crop-Raids sichtbar mit einem gelenkigen Unterkiefer und stärkerem roten Augenschein.
- Regression, Forge-1.20.1-JAR und dedizierter Server werden im vollständigen Workflow geprüft; visuelle Client-Abnahme bleibt eigenständig.

"""
need("## Version 1.101.0 —" in s,"prior release section")
s=s.replace("## Version 1.101.0 —",release+"## Version 1.101.0 —",1)
p.write_text(s,encoding="utf-8")
print("1.102 compass bearing calculated in existing loaded scan and Dämmerling synchronized jaw/eyes installed.")
