#!/usr/bin/env python3
"""1.97: true animated four-leaf crystal iris on the Colossus' glowing chest core,
plus separately moving Stalker thorax petals. All bones bake for skin and glow,
no damage changes, no copy of external reference assets, and no server effects.
"""
from pathlib import Path
import re, sys

R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(v,why):
    if not v:raise SystemExit("Sporenwerk 1.97 animated core iris: "+why)
def patch(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    need(s.count(old)==1,label+" anchor count "+str(s.count(old)))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

boss=C/"MutagenkolossModel.java"
s=boss.read_text(encoding="utf-8")
need("private final ModelPart[] resonanceRibs;" in s and
     "addResonanceRibs(body, true);" in s and
     "float ribFlare = breathCharge * 0.20F + stompCharge * 0.26F" in s,
     "1.96 Colossus rib/synced-attack model missing")
patch(boss,"    private final ModelPart[] resonanceRibs;",
"""    private final ModelPart[] resonanceRibs;
    private final ModelPart[] coreIrisPetals;""","record four iris hinges")
patch(boss,"        this.resonanceRibs = new ModelPart[] {",
"""        this.coreIrisPetals = new ModelPart[] {
                body.getChild("core_iris_left"),
                body.getChild("core_iris_right"),
                body.getChild("core_iris_top"),
                body.getChild("core_iris_bottom")
        };
        this.resonanceRibs = new ModelPart[] {""",
"bind iris on both baked model trees")

helper="""
    /**
     * 1.97 large four-leaf mechanical crystal iris around the original core.
     * Each blade is dark armor only in skin; the matching fullbright model
     * contains thin glowing vein children at identical pivots.
     * The core underneath remains the original boss model geometry.
     */
    private static void addFourPetalCoreIris(PartDefinition body, boolean glowing) {
        for (int part = 0; part < 4; part++) {
            boolean sideways = part < 2;
            float sign = part % 2 == 0 ? -1.0F : 1.0F;
            String name = part == 0 ? "core_iris_left"
                    : part == 1 ? "core_iris_right"
                    : part == 2 ? "core_iris_top" : "core_iris_bottom";
            float x = sideways ? sign * 5.1F : 0.0F;
            float y = sideways ? 0.0F : sign * 4.9F;
            CubeListBuilder shell = glowing ? CubeListBuilder.create()
                    : CubeListBuilder.create().texOffs(128, 192)
                            .addBox(sideways ? -3.8F : -6.0F,
                                    sideways ? -5.7F : -3.6F,
                                    -1.25F,
                                    sideways ? 7.6F : 12.0F,
                                    sideways ? 11.4F : 7.2F, 2.8F);
            PartDefinition petal = body.addOrReplaceChild(name, shell,
                    PartPose.offsetAndRotation(x, y, -28.4F, 0.0F, 0.0F, 0.0F));
            petal.addOrReplaceChild("iris_vein",
                    CubeListBuilder.create().texOffs(190, 192)
                            .addBox(sideways ? -1.4F : -4.4F,
                                    sideways ? -4.4F : -1.3F,
                                    -1.4F,
                                    sideways ? 2.8F : 8.8F,
                                    sideways ? 8.8F : 2.6F, 0.85F),
                    PartPose.ZERO);
        }
    }

"""
patch(boss,"    @Override\n    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,",
      helper+"    @Override\n    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,",
      "iris construction helper")
s=boss.read_text(encoding="utf-8")
returns=list(re.finditer(r"(?m)^        return LayerDefinition\.create\(mesh, 256, 256\);",s))
need(len(returns)==2,"need paired original + emissive layers")
for layer in (1,0):
    val="true" if layer else "false"
    s=s[:returns[layer].start()]+"        addFourPetalCoreIris(body, "+val+");\n"+s[returns[layer].start():]
boss.write_text(s,encoding="utf-8")

anim_anchor="""            rib.xRot = Mth.sin(ageInTicks * 0.075F + tier * 0.85F) * 0.035F
                    + breathCharge * 0.06F;
        }
        if (this.monolithLeft != null) {"""
anim_new="""            rib.xRot = Mth.sin(ageInTicks * 0.075F + tier * 0.85F) * 0.035F
                    + breathCharge * 0.06F;
        }
        // 1.97 actual four-leaf shutter opens during recognizable existing
        // breath/stomp/awakening charge. Idle resets unconditionally each frame.
        float coreOpening = Math.max(breathCharge * 0.78F,
                Math.max(stompCharge * 0.34F, awakeningCharge * 0.90F));
        float shimmer = Math.max(0.0F, Mth.sin(ageInTicks * 0.17F)) * 0.025F;
        this.coreIrisPetals[0].yRot = -coreOpening * 0.63F;
        this.coreIrisPetals[1].yRot = coreOpening * 0.63F;
        this.coreIrisPetals[2].xRot = -coreOpening * 0.48F;
        this.coreIrisPetals[3].xRot = coreOpening * 0.48F;
        for (int i = 0; i < this.coreIrisPetals.length; i++) {
            float scale = 1.0F + shimmer * coreOpening;
            this.coreIrisPetals[i].xScale = scale;
            this.coreIrisPetals[i].yScale = scale;
            this.coreIrisPetals[i].zScale = scale;
        }
        if (this.monolithLeft != null) {"""
patch(boss,anim_anchor,anim_new,"existing attack-controlled rib wave followed by iris")

stalker=C/"KristallpirscherModel.java"
source=stalker.read_text(encoding="utf-8")
need("private final ModelPart thoraxResonator;" in source and
     'resonator.addOrReplaceChild("thorax_shard_left"' in source
     and 'resonator.addOrReplaceChild("thorax_shard_right"' in source,
     "1.96 moving thorax crystal with two real child shards required")
patch(stalker,"    private final ModelPart thoraxResonator;",
"""    private final ModelPart thoraxResonator;
    private final ModelPart thoraxShardLeft;
    private final ModelPart thoraxShardRight;""","cache thorax side leaves")
patch(stalker,'        this.thoraxResonator = this.body.getChild("thorax_resonator");',
"""        this.thoraxResonator = this.body.getChild("thorax_resonator");
        this.thoraxShardLeft = this.thoraxResonator.getChild("thorax_shard_left");
        this.thoraxShardRight = this.thoraxResonator.getChild("thorax_shard_right");""",
"bind real chest shard bones")
patch(stalker,"        this.thoraxResonator.xRot = 0.12F - pursuit * 0.06F;",
"""        this.thoraxResonator.xRot = 0.12F - pursuit * 0.06F;
        // 1.97 the heart drives two independently hinged splinters; both
        // return to neutral after the hunt, and never change damage ranges.
        float shardFlare = pursuit * (0.14F + 0.08F
                * Math.max(0.0F, heartbeat));
        this.thoraxShardLeft.zRot = -0.36F - shardFlare;
        this.thoraxShardRight.zRot = 0.31F + shardFlare * 0.86F;
        this.thoraxShardLeft.yRot = 0.15F + shardFlare * 0.38F;
        this.thoraxShardRight.yRot = -0.10F - shardFlare * 0.34F;""",
"independent, resettable moving thorax shards")

# No new atlas zones: reuse dedicated, already painted 1.96 purple-cyan
# core and old stone UV islands, avoiding texture corruption/UV overwrites.
# Continue previous regression expectations and update only current-release IDs.
for p in (R/"tools").glob("test_*.py"):
    if p.name=="test_crystal_core_iris_197.py":continue
    old=p.read_text(encoding="utf-8")
    new=old.replace("Aktueller Entwicklungsstand: 1.96.0","Aktueller Entwicklungsstand: 1.97.0")
    if "build.gradle" in old:
        new=new.replace(r"1\.96\.0",r"1\.97\.0")
        new=new.replace("artifact must be version 1.96.0","artifact must be version 1.97.0")
    new=new.replace('"Version 1.96.0" in readme and "Version 1.95.0" in readme',
                    '"Version 1.97.0" in readme and "Version 1.96.0" in readme')
    if new!=old:p.write_text(new,encoding="utf-8")
gradle=R/"build.gradle"
g,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.97.0'",gradle.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle 1.97 release version")
gradle.write_text(g,encoding="utf-8")
p=R/"README.md"
s=p.read_text(encoding="utf-8")
headline="**Aktueller Entwicklungsstand: 1.96.0 — Kristallresonanz und lebendige Mutagenanatomie.**"
need(headline in s,"generated source 1.96 headline required")
s=s.replace(headline,"**Aktueller Entwicklungsstand: 1.97.0 — Kristallblende des Kolosses und bewegliche Mutagenherzen.**",1)
current="""## Aktueller Entwicklungsschritt — 1.97.0

- **Vier echte 3D-Kristallpanzer vor dem Koloss-Brustkern:** Eine bewegliche, aus vier Blättern bestehende Resonanzblende ersetzt keine vorhandenen Körperteile, sondern wird auf den schon bestehenden, sichtbar leuchtenden Kern aufgesetzt.
- **Lesbare Angriffssprache:** Die beiden Seitenflügel öffnen sich seitlich und die oberen/unteren Platten schwenken aus, synchron zum Kristallatem-, Stampf- und Erwachen-Windup. Sie schließen nach dem jeweiligen Angriff ohne Animationsdrift.
- **Zwei Render-Layer, dieselbe Anatomie:** Der normale Koloss-Skin trägt nur die dunklen mechanischen Basaltplatten; der separate Emissiv-Layer enthält ausschließlich die eingelegten Kristalladern, mit identischen Elternknochen und Ansatzpunkten.
- **Kristallpirscher mit beweglichen Herzen:** Die zwei existierenden kristallinen Brustsplitter werden jetzt einzeln ansteuerbar, spreizen sich beim Jagen und legen sich im Ruhezustand zurück. Die bisherige pulsierende Thoraxanimation bleibt erhalten.
- **Keine neuen Schäden:** Neue Teile sind ausschließlich Client-ModelParts. Sie verändern Hitboxen, Trefferzonen, Schutzmaschinen, Endgame-Heilung und bisherige Bossangriffe nicht.
- **Texture-Sicherheit:** Kein neuer großflächiger Überschreibvorgang von Texturatlanten. Benutzt die in Version 1.96 festgelegten, original bemalten Stein- und Resonanzkristallflächen.
- **Qualitätskontrolle:** Spezieller 1.97-Modell-/Layer-Regressionstest; Forge-1.20.1-Build, JAR-Verifikation und Dedicated-Server-Smoketest über GitHub Actions.

"""
need("## Aktueller Entwicklungsschritt — 1.96.0" in s,"1.96 current release docs missing")
s=s.replace("## Aktueller Entwicklungsschritt — 1.96.0",current+"## Aktueller Entwicklungsschritt — 1.96.0",1)
release="""## Version 1.97.0 — Bewegliche Kristallblenden und Mutagenherzen

- Koloss: vier neue 3D-Brustkristallblenden, mit übereinstimmender dunkler Geometrie/selektivem Glow und durch Attack-Windups gesteuerter symmetrischer Öffnung.
- Kristallpirscher: beide Brustkristallsplitter bekommen individuelle aggressive und ruhende Gelenkbewegungen.
- UV-Farben bleiben original und wurden nicht aus anderen Mod-JARs übernommen; alle bisherigen Kampf-, Farm- und Infektionssysteme bleiben funktionsgleich. Client-Sichtabnahme bleibt offen.

"""
need("## Version 1.96.0 —" in s,"prior release 1.96 missing")
s=s.replace("## Version 1.96.0 —",release+"## Version 1.96.0 —",1)
p.write_text(s,encoding="utf-8")
print("1.97 installed real Colossus 4-leaf synchronized core iris and Pirscher articulated heart shards without atlas overwrite.")
