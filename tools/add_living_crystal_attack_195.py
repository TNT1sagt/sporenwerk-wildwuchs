#!/usr/bin/env python3
"""1.95: living in-game crystal monster combat poses; all client ModelPart animation."""
from pathlib import Path
import re, sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
C=R/"src/main/java/de/sporenwerk/client"
def need(v,label):
    if not v:raise SystemExit("1.95 living crystal animation: "+label)
def patch(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    need(s.count(old)==1,label+" expected unique anchor, got "+str(s.count(old)))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

s=C/"KristallpirscherModel.java"
need("private final ModelPart leftDorsalFin;" in s.read_text(encoding="utf-8"),
     "existing 1.94 stalker bones required")
patch(s,"    private final ModelPart jawCrystal;",
"""    private final ModelPart jawCrystal;
    private final ModelPart leftTalonA;
    private final ModelPart leftTalonB;
    private final ModelPart rightTalonA;
    private final ModelPart rightTalonB;""","cache four talon fields")
patch(s,'        this.jawCrystal = this.head.getChild("jaw_crystal");',
"""        this.jawCrystal = this.head.getChild("jaw_crystal");
        this.leftTalonA = this.leftShoulder.getChild("talon_a");
        this.leftTalonB = this.leftShoulder.getChild("talon_b");
        this.rightTalonA = this.rightShoulder.getChild("talon_a");
        this.rightTalonB = this.rightShoulder.getChild("talon_b");""","bind existing talon joints")
patch(s,"""        } else {
            this.leftShoulder.xRot = -0.16F;
            this.rightShoulder.xRot = -0.16F;
        }
    }
}""",
"""        } else {
            this.leftShoulder.xRot = -0.16F;
            this.rightShoulder.xRot = -0.16F;
        }
        // 1.95 hard-edged, asymmetric pursuit posture; all poses reset per frame.
        float pursuit = entity.isAggressive() ? 1.0F : 0.0F;
        float stalkingStride = Mth.sin(limbSwing * 0.69F) * pace;
        this.body.xRot += pursuit * (0.14F + 0.055F * Math.abs(stalkingStride));
        this.head.xRot -= pursuit * 0.09F;
        this.leftArm.xRot = this.leftArm.xRot * (1.0F - pursuit * 0.23F)
                - pursuit * (0.29F + stalkingStride * 0.11F);
        this.rightArm.xRot = this.rightArm.xRot * (1.0F - pursuit * 0.23F)
                - pursuit * (0.43F - stalkingStride * 0.11F);
        this.leftArm.zRot = -0.10F - pursuit * 0.18F;
        this.rightArm.zRot = 0.10F + pursuit * 0.22F;
        float talonWave = Mth.sin(ageInTicks * 0.15F) * (0.03F + pursuit * 0.065F);
        this.leftTalonA.xRot = -0.20F + talonWave - pursuit * 0.15F;
        this.leftTalonB.xRot = -0.20F - talonWave - pursuit * 0.10F;
        this.rightTalonA.xRot = -0.20F - talonWave - pursuit * 0.21F;
        this.rightTalonB.xRot = -0.20F + talonWave - pursuit * 0.14F;
        this.leftTalonA.zRot = -0.12F - pursuit * 0.14F;
        this.leftTalonB.zRot = 0.13F + pursuit * 0.11F;
        this.rightTalonA.zRot = -0.12F - pursuit * 0.11F;
        this.rightTalonB.zRot = 0.13F + pursuit * 0.14F;
    }
}""","differentiated hunt, idle and talon posture")
r=C/"KristallpirscherRenderer.java"
patch(r,
"""            this.getParentModel().renderToBuffer(poseStack, vertex, 0xF000F0,
                    OverlayTexture.NO_OVERLAY, 1.0F, 1.0F, 1.0F, 1.0F);""",
"""            // Selective crystal veins brighten during hunt; opaque body stays dark.
            float pulse = 0.76F + 0.12F * (1.0F
                    + net.minecraft.util.Mth.sin(ageInTicks * 0.19F)) * 0.5F;
            if (entity.isAggressive()) pulse = Math.min(1.0F, pulse + 0.12F);
            this.getParentModel().renderToBuffer(poseStack, vertex, 0xF000F0,
                    OverlayTexture.NO_OVERLAY, pulse, pulse, pulse, 1.0F);""",
"selective breathing cyan/violet glow")

m=C/"MutagenkolossModel.java"
source=m.read_text(encoding="utf-8")
need("private static void addSiegeClawFacets(PartDefinition body, boolean glowing)" in source and
     "private final ModelPart tailStinger;" in source,
     "1.94 true in-game 12 claw facets and 3 stinger prongs needed")
patch(m,"    private final ModelPart tailStinger;",
"""    private final ModelPart tailStinger;
    private final ModelPart[] stingerProngs;
    private final ModelPart[] pawCrystalTips;""",
"register cached boss crystal bones")
anchor='        this.tailStinger = this.tailTip.hasChild("stinger_bloom") ? this.tailTip.getChild("stinger_bloom") : null;'
patch(m,anchor,anchor+"""
        // Cache 3 petals and 12 matching skin/glow paw bone tips at model bake.
        this.stingerProngs = new ModelPart[] {
                this.tailStinger.getChild("stinger_prong_left"),
                this.tailStinger.getChild("stinger_prong_right"),
                this.tailStinger.getChild("stinger_prong_top")
        };
        this.pawCrystalTips = new ModelPart[12];
        ModelPart[] facetLegs = { this.frontLeft, this.frontRight, this.rearLeft, this.rearRight };
        for (int leg = 0; leg < facetLegs.length; leg++) {
            ModelPart paw = facetLegs[leg].getChild("lower_leg").getChild("paw");
            for (int toe = 0; toe < 3; toe++) {
                String claw = toe == 0 ? "claw_left" : toe == 1 ? "claw_middle" : "claw_right";
                this.pawCrystalTips[leg * 3 + toe] = paw.getChild(claw).getChild("faceted_tip");
            }
        }""","prebind all stinger and paw bone children")

angle="""        // 1.95 windup-driven moving crystals, computed equally for both
        // glowing and textured models from synchronized existing attack states.
        int crystalState = entity.getAttackState();
        int remaining = Math.max(0, entity.getAttackTicks());
        float breathCharge = crystalState == MutagenkolossEntity.ATTACK_BREATH
                ? Mth.clamp((48.0F - remaining) / 48.0F, 0.0F, 1.0F) : 0.0F;
        float stompCharge = crystalState == MutagenkolossEntity.ATTACK_STOMP
                ? Mth.clamp((42.0F - remaining) / 42.0F, 0.0F, 1.0F) : 0.0F;
        float awakeningCharge = crystalState == MutagenkolossEntity.ATTACK_AWAKENING
                ? Mth.clamp((36.0F - remaining) / 36.0F, 0.0F, 1.0F) : 0.0F;
        float crystalTension = Math.max(stompCharge, awakeningCharge);
        if (this.monolithLeft != null) {
            this.monolithLeft.zRot -= crystalTension * 0.15F + breathCharge * 0.06F;
            this.monolithLeft.xRot -= breathCharge * 0.11F;
        }
        if (this.monolithRight != null) {
            this.monolithRight.zRot += crystalTension * 0.15F + breathCharge * 0.06F;
            this.monolithRight.xRot -= breathCharge * 0.11F;
        }
        // Three facets unfold and relax: no cumulative frame drift.
        float spread = 0.56F * breathCharge + 0.16F * awakeningCharge;
        this.stingerProngs[0].zRot = -0.56F - spread;
        this.stingerProngs[1].zRot = 0.56F + spread;
        this.stingerProngs[2].xRot = -0.52F - spread * 0.60F;
        for (int i = 0; i < this.pawCrystalTips.length; i++) {
            ModelPart tip = this.pawCrystalTips[i];
            float glint = 1.0F + Math.max(0.0F, Mth.sin(ageInTicks * 0.23F + i * 0.34F))
                    * crystalTension * 0.09F;
            tip.xScale = glint;
            tip.yScale = glint;
            tip.zScale = glint;
            tip.xRot = -crystalTension * 0.10F;
        }
"""
patch(m,"        this.head.zRot = -this.body.zRot * 0.60F;",
      angle+"        this.head.zRot = -this.body.zRot * 0.60F;",
      "boss attack state-linked crystal petals and monoliths")

for path in (R/"tools").glob("test_*.py"):
    if path.name=="test_living_crystal_attack_195.py":continue
    src=path.read_text(encoding="utf-8")
    updated=src.replace("Aktueller Entwicklungsstand: 1.94.0",
                        "Aktueller Entwicklungsstand: 1.95.0")
    if "build.gradle" in src:
        updated=updated.replace(r"1\.94\.0",r"1\.95\.0")
        updated=updated.replace("artifact must be version 1.94.0","artifact must be version 1.95.0")
    updated=updated.replace('"Version 1.94.0" in readme and "Version 1.93.0" in readme',
                            '"Version 1.95.0" in readme and "Version 1.94.0" in readme')
    if updated!=src:path.write_text(updated,encoding="utf-8")
p=R/"build.gradle"
s,n=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
            "version = '1.95.0'",p.read_text(encoding="utf-8"),count=1)
need(n==1,"Gradle 1.95 bump")
p.write_text(s,encoding="utf-8")
p=R/"README.md";s=p.read_text(encoding="utf-8")
old="**Aktueller Entwicklungsstand: 1.94.0 — Feingliedrige Kristallanatomie für Pirscher und Koloss.**"
need(old in s,"generated 1.94 source README current heading missing")
s=s.replace(old,"**Aktueller Entwicklungsstand: 1.95.0 — Kampfreaktive Kristallmonster-Animationen.**",1)
current="""## Aktueller Entwicklungsschritt — 1.95.0

- Kristallpirscher: Jagdhaltung mit vorgeneigtem Torso, ungleich weit ausgreifenden Armen und vier einzeln schwingenden Kristallklauen. Vorhandene Rückenflossen und Kieferkristall bleiben beweglich.
- Ruhestand und Angriff: alle Gelenke werden jedes Frame zurückgesetzt; keine akkumulierte Fehlrotation nach der Verfolgung. Die Humanoid-Laufanimation bleibt erhalten.
- Leuchten: Die vorhandene transparente Cyan-/Violett-Emissivmaske pulsiert etwas heller bei Aggression, dunkle Körperpanzer bleiben unbeeinflusst.
- Kristallkoloss: Drei echte Endstachel-Blätter öffnen sich während der synchronisierten Kristallatemphase. Zwei Rückenmonolithen spreizen sich beim Stampf-Windup, zwölf bereits modellierte Kristallklauen ziehen sich kurz zusammen.
- Die Animation verwendet vorhandenen Angriffszustand und synchronisierte Angriffsticker der Koloss-Entität. Keine zusätzlichen Server-Scans, Hitboxen, neuen Netzwerknachrichten oder Weltänderungen.
- Regressionstest prüft Geometrie, ModelPart-Referenzen, Pulsation, Zustandsübergänge, zwei Bossmodellschichten und Forge-/JAR-/Server-Verträglichkeit. Minecraft-Client-Sichtprüfung weiterhin offen.

"""
need("## Aktueller Entwicklungsschritt — 1.94.0" in s,"old 1.94 current section")
s=s.replace("## Aktueller Entwicklungsschritt — 1.94.0",
            current+"## Aktueller Entwicklungsschritt — 1.94.0",1)
release="""## Version 1.95.0 — Kristalljagd und resonante Angriffssprache

- Vier echte Stalker-Klauenknochen reagieren auf Jagdbewegungen; die asymmetrische Haltung und die Glühadern folgen dem Kampfzustand.
- Drei Koloss-Schwanzblätter, beide Rückenmonolithen und zwölf facettierte Zehen bekommen eigene Animationsantworten auf vorhandene Angriffsvorbereitungen.
- Ausschließlich bestehende synchronisierte Combat-States und clientseitige Geometrie verwendet; sämtliche Mutagen-, Farm- und Bossfunktionen erhalten.

"""
need("## Version 1.94.0 —" in s,"previous release heading")
s=s.replace("## Version 1.94.0 —",release+"## Version 1.94.0 —",1)
p.write_text(s,encoding="utf-8")
print("1.95 hunt pose, 4 talons, crystal glow pulse, and 3 boss tail petals + 12 staged claw windups installed.")
