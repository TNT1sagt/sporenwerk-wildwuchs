#!/usr/bin/env python3
"""Sporenwerk 1.96 - original in-game mutagen resonance anatomy.

Three staggered basalt/crystal ribs on each Colossus flank, correctly paired
with narrow emissive-only crystals in the existing skin/glow layer trees.
A beating crystalline thorax and two rib splinters on the Pirscher.
Existing synchronized boss attack states drive rib unfolding; aggressive
pursuit drives chest resonance. No world/AI changes or copied external assets.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import re, sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
T=R/"src/main/resources/assets/sporenwerk/textures/entity"

def need(ok, msg):
    if not ok: raise SystemExit("Sporenwerk 1.96 resonance: "+msg)

def patch(file, old, new, label):
    src=file.read_text(encoding="utf-8")
    need(src.count(old)==1,label+" expected unique anchor, found "+str(src.count(old)))
    file.write_text(src.replace(old,new,1),encoding="utf-8")

p=C/"KristallpirscherModel.java"
stalker=p.read_text(encoding="utf-8")
need("private final ModelPart rightTalonB;" in stalker and
     'this.body.getChild("dorsal_fin_left");' in stalker,
     "1.95 animated stalker and 1.94 fins must already exist")
patch(p,"    private final ModelPart rightTalonB;",
"""    private final ModelPart rightTalonB;
    private final ModelPart thoraxResonator;""","moving chest bone field")
patch(p,'        this.jawCrystal = this.head.getChild("jaw_crystal");',
"""        this.jawCrystal = this.head.getChild("jaw_crystal");
        this.thoraxResonator = this.body.getChild("thorax_resonator");""",
"custom chest bone binding")

stalker_geom="""
        // 1.96: the glowing mutant thorax is not painted flat on the old torso.
        // It is its own raised 3D organ, parented to the body's walking rig.
        PartDefinition resonator = body.addOrReplaceChild("thorax_resonator",
                CubeListBuilder.create().texOffs(72, 100)
                        .addBox(-3.0F, -3.9F, -2.1F, 6.0F, 7.8F, 3.4F)
                        .texOffs(100, 101)
                        .addBox(-1.9F, -5.2F, -2.6F, 3.8F, 3.0F, 2.5F),
                PartPose.offsetAndRotation(0.0F, -0.6F, -5.2F, 0.12F, 0.0F, 0.0F));
        resonator.addOrReplaceChild("thorax_shard_left",
                CubeListBuilder.create().texOffs(96, 96)
                        .addBox(-1.5F, -4.4F, -1.2F, 3.0F, 8.5F, 2.5F),
                PartPose.offsetAndRotation(-3.0F, 0.0F, -0.3F, -0.12F, 0.15F, -0.36F));
        resonator.addOrReplaceChild("thorax_shard_right",
                CubeListBuilder.create().texOffs(96, 96)
                        .addBox(-1.7F, -3.7F, -1.2F, 3.4F, 7.2F, 2.5F),
                PartPose.offsetAndRotation(3.0F, 0.5F, -0.3F, -0.06F, -0.10F, 0.31F));
"""
patch(p,'        body.addOrReplaceChild("mineral_chest",',
      stalker_geom+'\n        body.addOrReplaceChild("mineral_chest",',
      "new thorax 3D node and two attached gem shards")
# Existing end-of-frame 1.95 animation finishes on a unique talon pose.
patch(p,"        this.rightTalonB.zRot = 0.13F + pursuit * 0.14F;",
"""        this.rightTalonB.zRot = 0.13F + pursuit * 0.14F;
        // 1.96 independent, reversible crystal heartbeat; it brightens in
        // pursuit but has no hitbox, food, health or attack damage consequences.
        float heartbeat = Mth.sin(ageInTicks * (0.105F + pursuit * 0.075F));
        float resonanceScale = 1.0F + (0.035F + pursuit * 0.075F)
                * Math.max(0.0F, heartbeat);
        this.thoraxResonator.xScale = resonanceScale;
        this.thoraxResonator.yScale = resonanceScale;
        this.thoraxResonator.zScale = resonanceScale;
        this.thoraxResonator.xRot = 0.12F - pursuit * 0.06F;""",
"reversible chest pulse during pursuit")

boss=C/"MutagenkolossModel.java"
b=boss.read_text(encoding="utf-8")
need("private final ModelPart[] pawCrystalTips;" in b and
     "float crystalTension = Math.max(stompCharge, awakeningCharge);" in b,
     "1.95 cached boss paw/attack rig required")
patch(boss,"    private final ModelPart[] pawCrystalTips;",
"""    private final ModelPart[] pawCrystalTips;
    private final ModelPart[] resonanceRibs;""","cache six new ribs")
patch(boss,"        this.spines = new ModelPart[] {",
"""        // Match both layers. No lookups in render ticks.
        this.resonanceRibs = new ModelPart[] {
                body.getChild("resonance_rib_left_0"),
                body.getChild("resonance_rib_left_1"),
                body.getChild("resonance_rib_left_2"),
                body.getChild("resonance_rib_right_0"),
                body.getChild("resonance_rib_right_1"),
                body.getChild("resonance_rib_right_2")
        };
        this.spines = new ModelPart[] {""","bind actual rib parts on existing body")

helper="""
    /**
     * 1.96 six broad, articulated ribs around the old armored shoulders.
     * Dark stone is drawn ONLY in the ordinary skin; glow draws ONLY the
     * narrower amethyst/cyan core, with identical names and parent pivots.
     */
    private static void addResonanceRibs(PartDefinition body, boolean glowing) {
        for (int side = 0; side < 2; side++) {
            boolean left = side == 0;
            float sign = left ? -1.0F : 1.0F;
            for (int tier = 0; tier < 3; tier++) {
                String name = "resonance_rib_" + (left ? "left_" : "right_") + tier;
                float startX = left ? -8.5F : 0.0F;
                CubeListBuilder basalt = glowing ? CubeListBuilder.create()
                        : CubeListBuilder.create().texOffs(128, 192)
                                .addBox(startX, -2.8F, -2.5F, 8.5F, 5.6F, 5.0F)
                                .texOffs(158, 192)
                                .addBox(left ? -7.2F : 0.0F, -4.8F, -1.8F, 7.2F, 3.0F, 3.6F);
                PartDefinition rib = body.addOrReplaceChild(name, basalt,
                        PartPose.offsetAndRotation(sign * 19.4F, -2.6F,
                                -16.0F + tier * 12.0F, 0.0F, 0.0F, sign * 0.12F));
                CubeListBuilder crystal = CubeListBuilder.create().texOffs(190, 192)
                        .addBox(left ? -8.1F : 1.0F, -1.3F, -1.5F,
                                glowing ? 6.4F : 6.8F,
                                glowing ? 2.2F : 2.8F,
                                glowing ? 2.4F : 3.0F);
                rib.addOrReplaceChild("crystal_core", crystal, PartPose.ZERO);
            }
        }
    }

"""
patch(boss,"    @Override\n    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,",
      helper+"    @Override\n    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,",
      "original extra dorsal 3D ribs helper")
b=boss.read_text(encoding="utf-8")
returns=list(re.finditer(r"(?m)^        return LayerDefinition\.create\(mesh, 256, 256\);",b))
need(len(returns)==2,"two existing 256x256 layers required")
# Insert from end to front to preserve offsets.
for idx in (1,0):
    is_glow="true" if idx==1 else "false"
    b=b[:returns[idx].start()]+"        addResonanceRibs(body, "+is_glow+");\n"+b[returns[idx].start():]
need(b.count("addResonanceRibs(body, false);")==1
     and b.count("addResonanceRibs(body, true);")==1,
     "all six ribs must be in both skin/glow trees")
boss.write_text(b,encoding="utf-8")
patch(boss,
"""        float crystalTension = Math.max(stompCharge, awakeningCharge);""",
"""        float crystalTension = Math.max(stompCharge, awakeningCharge);
        // Six side ribs unfurl in a wave as the boss charges. The phase lag
        // travels from shoulders to haunches and returns to resting angle.
        float ribFlare = breathCharge * 0.20F + stompCharge * 0.26F
                + awakeningCharge * 0.37F;
        for (int ribIndex = 0; ribIndex < this.resonanceRibs.length; ribIndex++) {
            float sign = ribIndex < 3 ? -1.0F : 1.0F;
            int tier = ribIndex % 3;
            float lag = (2 - tier) * 0.10F;
            ModelPart rib = this.resonanceRibs[ribIndex];
            rib.zRot = sign * (0.12F + Math.max(0.0F, ribFlare - lag));
            rib.xRot = Mth.sin(ageInTicks * 0.075F + tier * 0.85F) * 0.035F
                    + breathCharge * 0.06F;
        }""",
"attack synchronized six lateral ribs")

# Original hand-authored Minecraft-style pixels on unused atlas strips.
# The glow remains selective rather than lighting basalt.
for filename in ("mutagenkoloss.png","mutagenkoloss_glow.png"):
    path=T/filename
    im=Image.open(path).convert("RGBA")
    need(im.size==(256,256),"boss texture 256x256 required")
    d=ImageDraw.Draw(im)
    glow=filename.endswith("_glow.png")
    if not glow:
        d.rectangle((128,192,218,222),fill=(25,24,42,255))
        for xx in range(131,214,12):
            d.polygon(((xx,214),(xx+5,194),(xx+9,217)),
                      fill=(47,41,73,255))
            d.line((xx+5,198,xx+6,213),fill=(57,116,155,255),width=2)
    else:
        # Do not fill the glow rectangle: untouched pixels stay transparent.
        for xx in range(131,214,12):
            d.line((xx+5,198,xx+6,213),fill=(41,229,245,255),width=2)
    # The 190+ rib core UV is violet edged with teal lightning.
    if not glow:
        d.rectangle((190,192,217,222),fill=(71,28,102,255))
    for k in range(4):
        x=192+k*6
        if not glow:
            d.polygon(((x,219),(x+2,194),(x+4,219)),
                      fill=(129+16*k,42+8*k,198+8*k,255))
        d.line((x+2,195,x+2,216),
               fill=(71,225,251,255) if glow else (93,184,242,255),width=2)
    im.save(path,optimize=True)

# The stalking chest reuses previously painted 128x128 crystalline pixel UV
# and glow strips rather than clearing other already-functional creature art.
for p in (R/"tools").glob("test_*.py"):
    if p.name=="test_resonant_crystal_anatomy_196.py":continue
    source=p.read_text(encoding="utf-8")
    updated=source.replace("Aktueller Entwicklungsstand: 1.95.0",
                           "Aktueller Entwicklungsstand: 1.96.0")
    if "build.gradle" in source:
        updated=updated.replace(r"1\.95\.0",r"1\.96\.0")
        updated=updated.replace("artifact must be version 1.95.0",
                                "artifact must be version 1.96.0")
    updated=updated.replace('"Version 1.95.0" in readme and "Version 1.94.0" in readme',
                            '"Version 1.96.0" in readme and "Version 1.95.0" in readme')
    if updated!=source:p.write_text(updated,encoding="utf-8")
p=R/"build.gradle"
old=p.read_text(encoding="utf-8")
new,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
              "version = '1.96.0'",old,count=1)
need(n==1,"Gradle 1.96.0 bump missing")
p.write_text(new,encoding="utf-8")
p=R/"README.md"
readme=p.read_text(encoding="utf-8")
headline="**Aktueller Entwicklungsstand: 1.95.0 — Kampfreaktive Kristallmonster-Animationen.**"
need(headline in readme,"generated 1.95 README headline missing")
readme=readme.replace(headline,
    "**Aktueller Entwicklungsstand: 1.96.0 — Kristallresonanz und lebendige Mutagenanatomie.**",1)
section="""## Aktueller Entwicklungsschritt — 1.96.0

- **Kristallkoloss mit sechs echten Resonanzrippen:** Drei unterschiedlich weit sitzende kristallene Rippen pro Körperseite brechen die alte einfache Seitensilhouette auf. Jedes Teil besitzt einen dunklen Basaltsockel und einen eigenen, deutlich schmaleren Leuchtkristall.
- **Synchronisierte Öffnungswelle:** Beim Stampf-, Atem- und Erwachens-Windup fächern sich die sechs Rippen zeitversetzt auf. Das normale Körpermodell und der bestehende Glow-Layer teilen vollständig dieselben Gelenke; im Leerlauf kehren sie in ihre Ruhehaltung zurück.
- **Kristallpirscher mit pulsierendem Brustkern:** Ein eigenes erhabenes Thoraxorgan und zwei daran befestigte Kristallspitzen sind echte Forge-Modellteile. Beim Jagen pulsiert der Körperkern sichtbar stärker, ohne Gameplayeffekt für den Spieler.
- **Eigenständige Pixelmaterialien:** Die 256×256-Haut- und Emissiv-PNGs des Kolosses erhalten neu gezeichnete violett-cyanfarbene Pixel für die Resonanzrippen; der restliche dunkle Panzer bleibt unbeleuchtet.
- **Sicherheit:** Keine Änderungen an KI, Infektionskontrolle, Spielerhitboxen, Boss-Schaden, Weltblöcken, neuen Tickern oder Netzwerkprotokollen. Die Animation läuft über bereits vorhandene Angriffszustände.
- **Qualität:** Eigene Regression für Modellbaum, sechs gepaarte Rippen, nur glühende Kernteile, Animationszustände und Texturatlanten. Forge-/Server-Tests bleiben Bestandteil des Workflows.

"""
need("## Aktueller Entwicklungsschritt — 1.95.0" in readme,"1.95 release section missing")
readme=readme.replace("## Aktueller Entwicklungsschritt — 1.95.0",
                      section+"## Aktueller Entwicklungsschritt — 1.95.0",1)
release="""## Version 1.96.0 — Resonanzrippen und pulsierendes Herz

- Sechs separat animierte Basalt-Kristallrippen mit eigener selektiver Leuchtgeometrie beim Kristallkoloss; Öffnung in unterschiedlichen Angriffswindups.
- Neuer Kristallpirscher-Brustresonator mit zwei seitlichen Kristallsplittern und pulsierender Verfolgungsanimation.
- Original-Minecraft-Modellgeometrie und eigene Pixeltexturen, ohne Änderungen am bisherigen Kampfverhalten. Visueller Minecraft-Client-Test weiterhin erforderlich.

"""
need("## Version 1.95.0 —" in readme,"history release 1.95 missing")
readme=readme.replace("## Version 1.95.0 —",release+"## Version 1.95.0 —",1)
p.write_text(readme,encoding="utf-8")
print("1.96 real animated Colossus rib cage and independent Pirscher beating crystalline thorax applied.")
