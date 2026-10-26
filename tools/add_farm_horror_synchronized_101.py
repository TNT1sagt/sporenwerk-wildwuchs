#!/usr/bin/env python3
"""Sporenwerk 1.101: synced Dämmerling crop-chew pose + visible mutagen node mode rings.

The existing true server-side raiding marker is now also a SynchedEntityData
boolean for a client animation (no new AI/scan or world mutation). The model
uses it for a low, asymmetrically pawing pose during a real field raid, returning
to the original stalker stance after a lantern or glow-berry rescue.

The existing server-side manual Mutagen Node mode switch gains distinctly
recognizable temporary spore rings for spreading, cultivation and dormancy.
No scanner needed; paused and ordinary world ticks are unchanged.
"""
from pathlib import Path
import re, sys

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
SRC=ROOT/"src/main/java/de/sporenwerk"
MOB=SRC/"entity/DaemmerlingEntity.java"
MODEL=SRC/"client/DaemmerlingModel.java"
NODE=SRC/"block/MutationNodeBlock.java"

def need(ok,reason):
    if not ok:raise SystemExit("Sporenwerk 1.101 synchronized farm horror: "+reason)
def patch(path,old,new,name):
    s=path.read_text(encoding="utf-8")
    need(s.count(old)==1,name+": expected one anchor, got "+str(s.count(old)))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

entity=MOB.read_text(encoding="utf-8")
need("private boolean raidingCrops;" in entity and
     "public boolean isRaidingCrops() { return this.raidingCrops; }" in entity,
     "1.91 real raid status and manual station monitoring required")
need("if (chewTicks % 5 == 0)" in entity and
     "Items.GLOW_BERRIES" in entity and "Items.SOUL_LANTERN" in entity,
     "1.100 berry distraction and lantern safety required")
patch(MOB,"import net.minecraft.core.BlockPos;",
"""import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;""",
"Forge vanilla 1.20.1 entity data imports")
patch(MOB,"    private boolean raidingCrops;",
"""    private static final EntityDataAccessor<Boolean> RAIDING_CROPS_VISUAL =
            SynchedEntityData.defineId(DaemmerlingEntity.class, EntityDataSerializers.BOOLEAN);
    private boolean raidingCrops;""","client-readable tracked raid visual marker")
patch(MOB,"    public boolean isRaidingCrops() { return this.raidingCrops; }",
"""    public boolean isRaidingCrops() { return this.raidingCrops; }

    // Only render information is synchronized; the station still uses
    // authoritative server-side true raid state. No gameplay is client-driven.
    public boolean isCropNibbling() { return this.entityData.get(RAIDING_CROPS_VISUAL); }

    private void syncCropRaidPose(boolean eating) {
        if (this.entityData.get(RAIDING_CROPS_VISUAL) != eating) {
            this.entityData.set(RAIDING_CROPS_VISUAL, eating);
        }
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(RAIDING_CROPS_VISUAL, false);
    }""","synchronize boolean only when raiding status actually changes")

# Preserve old 1.91 explicit boolean marker and new client status in lockstep.
s=MOB.read_text(encoding="utf-8")
trueCount=s.count("mob.raidingCrops = true;")
falseCount=s.count("mob.raidingCrops = false;")
need(trueCount==1 and falseCount>=4,
     "expect one actual nibble and at least four clearing paths, got "+str((trueCount,falseCount)))
s=s.replace("mob.raidingCrops = true;","mob.raidingCrops = true;\n                mob.syncCropRaidPose(true);")
# Match indentation of existing state changes, respecting start, stop, guard and bite.
s=re.sub(r"(?m)^([ \t]*)mob\.raidingCrops = false;$",
         r"\1mob.raidingCrops = false;\n\1mob.syncCropRaidPose(false);",s)
need(s.count("mob.syncCropRaidPose(false);")==falseCount,
     "every escape/repel/bite must clear client raid state")
MOB.write_text(s,encoding="utf-8")

# Crop-raiding actively moves existing four rooted fingers and articulated
# body while it approaches no new scan or nonvisual player effects.
m=MODEL.read_text(encoding="utf-8")
need("this.body.xRot=0.23F+" in m and
     'this.leftClaws.zRot=-0.14F-stride*0.09F;' in m and
     "if(entity.isAggressive())" in m,
     "1.100 actual Daemmerling custom mesh and swing required")
patch(MODEL,
"""        this.headRoot.zRot=0.32F+pulse*0.04F;
        if(entity.isAggressive()) {""",
"""        this.headRoot.zRot=0.32F+pulse*0.04F;
        // 1.101: the frightening crop nibble is a real pose and is driven
        // by one existing server-authoritative AI state, not guessed from
        // client distance or permanently looping ambient particles.
        if(entity.isCropNibbling()) {
            float clawBeat=Mth.sin(ageInTicks*0.52F);
            this.body.xRot+=0.43F;
            this.head.xRot+=0.31F;
            this.leftArm.xRot=-1.13F+clawBeat*0.13F;
            this.rightArm.xRot=-1.27F-clawBeat*0.13F;
            this.leftClaws.xRot=-0.65F+clawBeat*0.18F;
            this.rightClaws.xRot=-0.69F-clawBeat*0.18F;
            this.leftClaws.zRot=-0.24F;
            this.rightClaws.zRot=0.24F;
            this.leftHook.zRot-=0.08F;
            this.rightHook.zRot+=0.09F;
        }
        if(entity.isAggressive()) {""",
"actual sync-driven bent-over crop feeding animation")
# IMPORTANT: the base ZombieModel gait remains; the aggressive branch is
# target-specific and does not animate a crop goal because getTarget()==null.

node=NODE.read_text(encoding="utf-8")
need('int nextMode = (state.getValue(MODE) + 1) % 3;' in node and
     "serverLevel.sendParticles(particle, pos.getX() + 0.5D" in node and
     "new AABB(pos).inflate(10.0D, 5.0D, 10.0D)" in node,
     "mode-aware manual node toggle and nearby player feedback required")
patch(NODE,
"""            serverLevel.sendParticles(particle, pos.getX() + 0.5D, pos.getY() + 0.8D,
                    pos.getZ() + 0.5D, 12, 0.24D, 0.2D, 0.24D, 0.012D);""",
"""            serverLevel.sendParticles(particle, pos.getX() + 0.5D, pos.getY() + 0.8D,
                    pos.getZ() + 0.5D, 12, 0.24D, 0.2D, 0.24D, 0.012D);
            // A small one-shot boundary signature when a human cycles the
            // node's mode. There is no always-on scanner, task or extra tick.
            emitModeSelectionRing(serverLevel, pos, nextMode);""",
"one-time three distinct node mode rings")
patch(NODE,
"""    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }""",
"""    /**
     * 1.101 mode-feedback ring for manual interaction only. Infected spread,
     * safe cultivation and dormant containment all look different immediately,
     * even without a scanner. No block changes, no chunk searches.
     */
    private static void emitModeSelectionRing(ServerLevel level, BlockPos pos, int mode) {
        if (mode < 0 || mode > 2) return;
        double x=pos.getX()+0.5D;
        double y=pos.getY()+0.65D;
        double z=pos.getZ()+0.5D;
        for (int sample=0;sample<12;sample++) {
            double angle=sample*Math.PI/6.0D;
            double radius=mode==0?2.15D:mode==1?1.65D:1.05D;
            double px=x+Math.cos(angle)*radius;
            double pz=z+Math.sin(angle)*radius;
            level.sendParticles(mode==0 ? ParticleTypes.REVERSE_PORTAL
                            : mode==1 ? ParticleTypes.HAPPY_VILLAGER : ParticleTypes.SMOKE,
                    px,y+(sample%3)*0.13D,pz,
                    1,0.0D,0.04D,0.0D,0.008D);
            if (sample%3==0 && mode!=2) {
                level.sendParticles(mode==0 ? ParticleTypes.SOUL_FIRE_FLAME : ParticleTypes.END_ROD,
                        px,y+0.35D,pz,
                        1,0.0D,0.04D,0.0D,0.008D);
            }
        }
    }

    @Override
    public boolean isRandomlyTicking(BlockState state) { return true; }""",
"mutagen rings show original 3 operating modes without scanner")

for path in (ROOT/"tools").glob("test_*.py"):
    if path.name=="test_farm_horror_synchronized_101.py":continue
    old=path.read_text(encoding="utf-8")
    new=old.replace("Aktueller Entwicklungsstand: 1.100.0",
                    "Aktueller Entwicklungsstand: 1.101.0")
    if "build.gradle" in old:
        new=new.replace(r"1\.100\.0",r"1\.101\.0")
        new=new.replace("artifact must be version 1.100.0",
                        "artifact must be version 1.101.0")
    new=new.replace('"Version 1.100.0" in readme and "Version 1.99.0" in readme',
                    '"Version 1.101.0" in readme and "Version 1.100.0" in readme')
    if new!=old:path.write_text(new,encoding="utf-8")
gradle=ROOT/"build.gradle";old=gradle.read_text(encoding="utf-8")
new,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
              "version = '1.101.0'",old,count=1)
need(n==1,"Gradle version 1.101.0")
gradle.write_text(new,encoding="utf-8")
p=ROOT/"README.md";readme=p.read_text(encoding="utf-8")
oldHead="**Aktueller Entwicklungsstand: 1.100.0 — Eigene Schattenkreatur und Feld-Lockköder.**"
need(oldHead in readme,"1.100 generated source headline")
readme=readme.replace(oldHead,
    "**Aktueller Entwicklungsstand: 1.101.0 — Sichtbare Dämmerling-Fraßbewegung und eindeutige Mutagen-Modusringe.**",1)
step="""## Aktueller Entwicklungsschritt — 1.101.0

- Der Dämmerling verwendet seine bereits existierende serverseitige echte Fraßzustandsmarkierung jetzt zugleich als synchronisierte visuelle Client-Information. Nur bei tatsächlichem Knabbern am Beet beugt er sich tief herunter und greift rhythmisch mit den beiden unterschiedlich langen Wurzelhänden zu.
- Die Darstellung kehrt automatisch zur normalen Gang-/Jagdpose zurück, wenn er vertrieben wurde, das Feld verlässt oder den Fraß beendet. Das gilt sowohl für Seelenlaternen als auch für neue Leuchtbeeren.
- Kein weiterer Scan und keine Gameplay-Änderungen durch diese Synchronisation: alter Serverboolean und Feldstations-Diagnose bleiben zuständig, während nur ein zusätzlicher SynchedEntityData-Boolean das Aussehen steuert. Keine neuen Pakete pro Frame.
- Mutagenknoten zeigen beim manuellen Moduswechsel drei klar unterschiedliche, kurz sichtbare Kreissignaturen: weit ausgreifende violette Portalsporen für aktive Verbreitung, ruhige grüne Wachstumsringe für sichere Kultivierung und eine kleine graue Rauchsignatur für Ruhe.
- Die Ringanimation wird ausschließlich durch das ohnehin bestehende rechtsklickgesteuerte Moduswechsel-Ereignis ausgelöst. Es gibt keine neuen Tick-Events, Chunkzwangsladungen, Spielerfolgen, angegriffenen Pflanzen oder scannergebundene Sichtbarkeit.
- Dedizierter Regressionstest umfasst synchronisierte Fraßzustände und alle Abbruchpfade, echte eigene Modellgelenke, drei Feldsignaturen, Redstone- und Inaktivitätslogik sowie alle alten Schutzmöglichkeiten.

"""
need("## Aktueller Entwicklungsschritt — 1.100.0" in readme,"previous development step missing")
readme=readme.replace("## Aktueller Entwicklungsschritt — 1.100.0",
                      step+"## Aktueller Entwicklungsschritt — 1.100.0",1)
release="""## Version 1.101.0 — Lebendige Fraßanimation und sichtbare Mutagenkontrolle

- Echte vom Server synchronisierte Dämmerling-Fraßpose mit gekrümmtem Rücken, wechselnden Klauen und markant geöffneten Schulterwurzeln, aktiv nur während realer Beetangriffe.
- Sofort sichtbare, modusabhängige Mutagen-Ringe beim Rechtsklick auf den Infektionsherd: bedrohliche Ausbreitung, friedlicher Kulturmodus oder Ruhe.
- Kein Scanner zum Erkennen nötig, keine neuen Gameplay-Nachteile, keine neuen permanenten Entity- oder Block-Ticker. Alle Schutzmaschinen, Heil- und Kontrollmöglichkeiten bleiben erhalten.
- CI testet Forge 1.20.1 und die Sicherheit im dedizierten Server. Ein optischer Minecraft-Client-Test bleibt ausstehend.

"""
need("## Version 1.100.0 —" in readme,"prior release documentation")
readme=readme.replace("## Version 1.100.0 —",release+"## Version 1.100.0 —",1)
p.write_text(readme,encoding="utf-8")
print("1.101 server-synced feeding pose, automatic decay on guard+crop completion, and 3 manual node mode rings installed.")
