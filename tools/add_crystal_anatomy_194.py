#!/usr/bin/env python3
"""1.94 in-game sculpt: real asymmetrical stalker fins and 12 articulated boss claw tips."""
from pathlib import Path
from PIL import Image, ImageDraw
import re, sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C = ROOT / "src/main/java/de/sporenwerk/client"
T = ROOT / "src/main/resources/assets/sporenwerk/textures/entity"
def need(ok, why):
    if not ok: raise SystemExit("Sporenwerk 1.94 sculpt: "+why)
def patch(path, a, b, why):
    s=path.read_text(encoding="utf-8")
    need(s.count(a)==1, why+" anchor "+str(s.count(a)))
    path.write_text(s.replace(a,b,1),encoding="utf-8")

stalker=C/"KristallpirscherModel.java"
p=stalker.read_text(encoding="utf-8")
need('PartDefinition crest = body.addOrReplaceChild("back_crest"' in p and
     "float sway = Mth.sin(ageInTicks * 0.073F) * 0.06F;" in p,
     "1.93 custom stalker model required")
patch(stalker,"    private final ModelPart headCrystal;",
"""    private final ModelPart headCrystal;
    private final ModelPart leftDorsalFin;
    private final ModelPart rightDorsalFin;
    private final ModelPart jawCrystal;""","fields")
patch(stalker,'        this.headCrystal = this.head.getChild("head_crystal");',
"""        this.headCrystal = this.head.getChild("head_crystal");
        this.leftDorsalFin = this.body.getChild("dorsal_fin_left");
        this.rightDorsalFin = this.body.getChild("dorsal_fin_right");
        this.jawCrystal = this.head.getChild("jaw_crystal");""","constructor")
geo = """
        // 1.94 unique dorsal fins with three tapered voxel tiers and basalt sockets.
        PartDefinition finLeft = body.addOrReplaceChild("dorsal_fin_left",
                CubeListBuilder.create().texOffs(64, 96)
                        .addBox(-2.5F, -8.0F, -2.0F, 5.0F, 9.0F, 4.0F)
                        .texOffs(80, 96).addBox(-1.75F, -14.0F, -1.5F, 3.5F, 6.5F, 3.0F)
                        .texOffs(96, 96).addBox(-1.0F, -19.0F, -0.9F, 2.0F, 5.5F, 1.8F),
                PartPose.offsetAndRotation(-4.2F, -4.0F, 2.5F, -0.18F, -0.13F, -0.52F));
        finLeft.addOrReplaceChild("root_socket",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-3.3F, -4.0F, -2.9F, 6.6F, 5.0F, 5.8F), PartPose.ZERO);
        PartDefinition finRight = body.addOrReplaceChild("dorsal_fin_right",
                CubeListBuilder.create().texOffs(64, 96)
                        .addBox(-3.0F, -10.0F, -2.3F, 6.0F, 11.0F, 4.6F)
                        .texOffs(80, 96).addBox(-2.0F, -18.0F, -1.6F, 4.0F, 8.5F, 3.2F)
                        .texOffs(96, 96).addBox(-1.1F, -25.0F, -1.0F, 2.2F, 7.5F, 2.0F),
                PartPose.offsetAndRotation(4.8F, -3.0F, 4.0F, 0.16F, 0.22F, 0.42F));
        finRight.addOrReplaceChild("root_socket",
                CubeListBuilder.create().texOffs(64, 48)
                        .addBox(-3.6F, -4.0F, -3.2F, 7.2F, 5.0F, 6.4F), PartPose.ZERO);
        head.addOrReplaceChild("jaw_crystal",
                CubeListBuilder.create().texOffs(80, 96)
                        .addBox(-2.2F, -1.0F, -5.8F, 4.4F, 4.0F, 4.5F)
                        .texOffs(96, 96).addBox(-1.0F, 2.0F, -6.6F, 2.0F, 4.8F, 3.0F),
                PartPose.offsetAndRotation(0.0F, 1.8F, -1.0F, -0.12F, 0.0F, -0.18F));
"""
anchor="        // Angular mineral pauldrons and long cyan talons, following arm bones."
patch(stalker,anchor,geo+"\n"+anchor,"new creature geometry")
anchor="""        this.headCrystal.xRot = -0.10F + Mth.sin(ageInTicks * 0.10F) * 0.06F;
        if (entity.isAggressive()) {"""
patch(stalker,anchor,"""        this.headCrystal.xRot = -0.10F + Mth.sin(ageInTicks * 0.10F) * 0.06F;
        // Absolute bone rotations: aggression cannot accumulate frame-to-frame.
        float finWave = Mth.sin(ageInTicks * 0.065F - 0.8F) * 0.045F;
        this.leftDorsalFin.zRot = -0.52F + finWave - pace * 0.035F;
        this.rightDorsalFin.zRot = 0.42F - finWave * 1.30F + pace * 0.05F;
        this.leftDorsalFin.xRot = -0.18F + Mth.sin(limbSwing * 0.56F) * pace * 0.055F;
        this.rightDorsalFin.xRot = 0.16F + Mth.sin(limbSwing * 0.56F + 0.9F) * pace * 0.060F;
        this.jawCrystal.xRot = -0.12F + Mth.sin(ageInTicks * 0.090F) * 0.025F;
        this.jawCrystal.zRot = -0.18F;
        if (entity.isAggressive()) {
            this.leftDorsalFin.zRot -= 0.12F;
            this.rightDorsalFin.zRot += 0.18F;
            this.jawCrystal.xRot += 0.14F;
        }
        if (entity.isAggressive()) {""","moving fins and jaw")

# New UV islands at y=96..127, safely away from vanilla 64x64 skin.
for name in ("kristallpirscher.png","kristallpirscher_glow.png"):
    tex=T/name
    im=Image.open(tex).convert("RGBA")
    need(im.size==(128,128),"stalker 128x128 atlas")
    d=ImageDraw.Draw(im)
    glow=name.endswith("_glow.png")
    if not glow: d.rectangle((64,96,127,127),fill=(23,36,56,255))
    for k in range(6):
        x=66+9*k
        if not glow:
            d.polygon(((x,119),(x+4,98),(x+8,122)),
                      fill=(50+9*k,51+5*k,123+15*k,255))
        d.line((x+4,101,x+5,115),
               fill=(49,237,247,255) if glow else (53,179+8*k,237,255),width=2)
    if not glow:
        d.polygon(((100,121),(104,101),(109,117),(105,125)),
                  fill=(173,72,237,255))
    else:
        d.line((104,105,106,120),fill=(229,107,255,255),width=2)
    im.save(tex,optimize=True)

# Faceted Colossus toes: each of four paw bones receives all 3 new children
# and existing heavy walk / stomp animation controls the whole mesh naturally.
boss=C/"MutagenkolossModel.java"
b=boss.read_text(encoding="utf-8")
need("private final ModelPart tailStinger;" in b and
     "private static void addGlowLeg(PartDefinition body" in b,
     "1.92 Colossus skin+glow rig required")
helper="""
    /** Extra voxel facet under each of the 12 old claw bones, not a new hitbox. */
    private static void addSiegeClawFacets(PartDefinition body, boolean glowing) {
        for (String legName : new String[] { "front_left", "front_right", "rear_left", "rear_right" }) {
            PartDefinition paw = body.getChild(legName).getChild("lower_leg").getChild("paw");
            for (int k = 0; k < 3; k++) {
                String clawName = k == 0 ? "claw_left" : k == 1 ? "claw_middle" : "claw_right";
                PartDefinition claw = paw.getChild(clawName);
                float x = k == 0 ? -4.9F : k == 1 ? 0.0F : 4.9F;
                float z = k == 1 ? -17.8F : -16.3F;
                float width = glowing ? 1.35F : 2.65F;
                float depth = glowing ? 3.8F : 4.8F;
                claw.addOrReplaceChild("faceted_tip",
                        CubeListBuilder.create().texOffs(glowing ? 224 : 176, glowing ? 44 : 100)
                                .addBox(-width / 2.0F, 0.0F, -depth / 2.0F,
                                        width, glowing ? 0.6F : 1.2F, depth)
                                .texOffs(glowing ? 224 : 176, glowing ? 44 : 100)
                                .addBox(-width * 0.30F, -0.28F, -depth / 2.0F - 1.4F,
                                        width * 0.60F, glowing ? 0.35F : 0.8F, 2.0F),
                        PartPose.offset(x, 0.25F, z));
            }
        }
    }

"""
modelAnchor="    @Override\n    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,"
patch(boss,modelAnchor,helper+modelAnchor,"shared boss faceted tips")
b=boss.read_text(encoding="utf-8")
returns=list(re.finditer(r"(?m)^        return LayerDefinition\.create\(mesh, 256, 256\);",b))
need(len(returns)==2,"boss still needs two separate model layers")
for idx in (1,0):
    val="true" if idx==1 else "false"
    b=b[:returns[idx].start()]+"        addSiegeClawFacets(body, "+val+");\n"+b[returns[idx].start():]
need(b.count("addSiegeClawFacets(body, true);")==1 and
     b.count("addSiegeClawFacets(body, false);")==1,
     "both skin and emissive paw facets required")
boss.write_text(b,encoding="utf-8")

for p in (ROOT/"tools").glob("test_*.py"):
    if p.name=="test_crystal_anatomy_194.py": continue
    s=p.read_text(encoding="utf-8")
    n=s.replace("Aktueller Entwicklungsstand: 1.93.0",
                "Aktueller Entwicklungsstand: 1.94.0")
    if "build.gradle" in s:
        n=n.replace(r"1\.93\.0",r"1\.94\.0")
        n=n.replace("artifact must be version 1.93.0",
                    "artifact must be version 1.94.0")
    n=n.replace('"Version 1.93.0" in readme and "Version 1.92.0" in readme',
                '"Version 1.94.0" in readme and "Version 1.93.0" in readme')
    if n!=s:p.write_text(n,encoding="utf-8")
gradle=ROOT/"build.gradle"
s,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.94.0'",gradle.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle 1.94.0")
gradle.write_text(s,encoding="utf-8")
readme=ROOT/"README.md"
s=readme.read_text(encoding="utf-8")
old="**Aktueller Entwicklungsstand: 1.93.0 — Kristallpirscher erhält ein eigenes animiertes 3D-Modell.**"
need(old in s,"generated source 1.93 release headline missing")
s=s.replace(old,"**Aktueller Entwicklungsstand: 1.94.0 — Feingliedrige Kristallanatomie für Pirscher und Koloss.**",1)
new="""## Aktueller Entwicklungsschritt — 1.94.0

- **Kristallpirscher: echte asymmetrische Rückenflossen.** Zwei verschieden lange, gestufte Kristallflossen mit mineralischen Fassungen folgen eigenen Modellknochen und fächern sich bei der Jagd auf.
- **Beweglicher Kieferkristall:** Eine weitere scharfkantige Struktur reagiert auf Laufen und Aggression; jeder Animationsdurchlauf setzt alle Gelenke neu.
- **Zwei neue UV-Bereiche:** Unterer Atlasbereich der bestehenden 128x128-Hauttextur. Die selektive Emissivschicht beleuchtet nur einzelne cyan-violette Kristalladern.
- **Kristallkoloss: zwölf echte facettierte Klauenspitzen.** Alle vier bestehenden Pfoten besitzen neue, zweistufige, keilförmige Minecraft-ModelParts unter ihren alten Klauenknochen. Gleiche Gelenkstruktur in Skin und Glow, unveränderte gewichtige Laufanimation.
- **Sicherheit:** Keine Änderungen an KI, Farm-Horror, Infektionsheilung, Redstone, Boss-Drops, Spielerhitboxen oder Server-Tickern. Gesonderter Quellcode-/Pixel-Regressionstest und voller Forge- und Server-Build.

"""
need("## Aktueller Entwicklungsschritt — 1.93.0" in s,"prior README section missing")
s=s.replace("## Aktueller Entwicklungsschritt — 1.93.0",new+"## Aktueller Entwicklungsschritt — 1.93.0",1)
release="""## Version 1.94.0 — Lebendige Kristallanatomie

- Kristallpirscher mit zwei asymmetrischen, unabhängig animierten Rückenflossen und einem neuen kristallinen Kieferorgan, ergänzt um original Cyan-Magenta-Pixelmaterial.
- Kristallkoloss mit zwölf zweistufigen, facettierten Kristallklauen, verankert in vier bestehenden animierten Pfoten und deren Leucht-Layer.
- Die Darstellung ist Minecraft-Modellgeometrie, kein reines Bild. Forge-/Server-Prüfung und spätere Client-Sichtabnahme sind getrennte Tests.

"""
need("## Version 1.93.0 —" in s,"old release notes missing")
s=s.replace("## Version 1.93.0 —",release+"## Version 1.93.0 —",1)
readme.write_text(s,encoding="utf-8")
print("Sporenwerk 1.94 stalker fin and jaw animation, matching new pixel atlas and 12 Colossus faceted toes applied.")
