#!/usr/bin/env python3
"""Version 1.82: weighted quadruped gait, individually flexing paws and inertial crystal tail.

Original procedural Forge ModelPart animation. Applies after the 1.81 jaw patch.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/main/java/de/sporenwerk/client/MutagenkolossModel.java"


def require(ok, label):
    if not ok:
        raise SystemExit("Weighted Colossus gait 1.82: " + label)


def replace_once(old, new, label):
    source = MODEL.read_text(encoding="utf-8")
    if new in source:
        return
    require(source.count(old) == 1, f"{label}: expected exactly one anchor, found {source.count(old)}")
    MODEL.write_text(source.replace(old, new, 1), encoding="utf-8")


# Skin and emissive models already contain matching four-leg rig chains:
# body -> leg -> lower_leg -> paw. Use the same helper for both so glow stays in place.
anim_anchor = """    @Override
    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,
                          float ageInTicks, float netHeadYaw, float headPitch) {"""
anim_helper = """    /**
     * A heavy, diagonal quadruped walking cycle: alternating stance and swing, flexed
     * knees and compensating paws. Base paw offsets are reset each frame, so previous
     * poses cannot accumulate or drift between idle and combat.
     */
    private static void animateWeightedLeg(ModelPart leg, float phase, float stride, boolean rearLeg) {
        float swing = Mth.sin(phase);
        float lift = Math.max(0.0F, Mth.cos(phase)) * stride;
        leg.xRot = swing * stride * (rearLeg ? 0.55F : 0.68F);
        ModelPart lowerLeg = leg.getChild("lower_leg");
        lowerLeg.xRot = Math.max(0.0F, -swing) * stride * (rearLeg ? 0.57F : 0.48F);
        ModelPart paw = lowerLeg.getChild("paw");
        paw.xRot = -leg.xRot * 0.38F - lowerLeg.xRot * 0.55F;
        paw.y = 6.0F - lift * 1.65F;
        paw.z = -1.0F - lift * 0.45F;
    }

""" + anim_anchor
replace_once(anim_anchor, anim_helper, "insert shared weighted walking animation")

old_gait = """        float gait = Mth.sin(limbSwing * 0.42F) * limbSwingAmount * 0.72F;
        this.body.xRot = Mth.sin(ageInTicks * 0.065F) * 0.018F;
        this.body.yRot = 0.0F;
        this.body.zRot = 0.0F;"""
new_gait = """        // 1.82 weighted traversal: diagonal legs step as pairs, not as rigid pendulums.
        float stride = Mth.clamp(limbSwingAmount, 0.0F, 1.0F);
        float stridePhase = limbSwing * 0.42F;
        this.body.xRot = Mth.sin(ageInTicks * 0.065F) * 0.018F;
        this.body.yRot = Mth.sin(stridePhase - 0.45F) * stride * 0.016F;
        this.body.zRot = Mth.sin(stridePhase) * stride * 0.026F;"""
replace_once(old_gait, new_gait, "replace simplistic swing with walking cycle")

old_legs = """        this.frontLeft.xRot = gait;
        this.frontRight.xRot = -gait;
        this.rearLeft.xRot = -gait;
        this.rearRight.xRot = gait;
        this.frontLeft.getChild("lower_leg").xRot = Math.max(0.0F, gait) * 0.55F;
        this.frontRight.getChild("lower_leg").xRot = Math.max(0.0F, -gait) * 0.55F;
        this.rearLeft.getChild("lower_leg").xRot = Math.max(0.0F, -gait) * 0.55F;
        this.rearRight.getChild("lower_leg").xRot = Math.max(0.0F, gait) * 0.55F;"""
new_legs = """        animateWeightedLeg(this.frontLeft, stridePhase, stride, false);
        animateWeightedLeg(this.frontRight, stridePhase + Mth.PI, stride, false);
        animateWeightedLeg(this.rearLeft, stridePhase + Mth.PI, stride, true);
        animateWeightedLeg(this.rearRight, stridePhase, stride, true);"""
replace_once(old_legs, new_legs, "install four individually articulated gait chains")

# The 1.59 patch created two additional independently animated tail segments.
# Only add bounded counter-sway; all original idle and boss recoil remain intact.
tail_anchor = """        this.tailTip.zRot = 0.0F;
        for (int i = 0; i < this.spines.length; i++) {"""
tail_new = """        this.tailTip.zRot = 0.0F;
        // 1.82 muscular counterbalance: delayed waves move through all three tail joints.
        this.tail.yRot += Mth.sin(stridePhase - 0.65F) * stride * 0.055F;
        this.tailMid.yRot += Mth.sin(stridePhase - 1.15F) * stride * 0.095F;
        this.tailTip.yRot += Mth.sin(stridePhase - 1.70F) * stride * 0.14F;
        for (int i = 0; i < this.spines.length; i++) {"""
replace_once(tail_anchor, tail_new, "three-stage tail walk counterbalance")

# Existing synchronized stomp states override the shoulder-leg rotation. The new paws
# must not inherit half-steps during a stationary attack preparation.
stomp_anchor = """        } else if (state == MutagenkolossEntity.ATTACK_BREATH) {
            this.head.xRot = -0.34F + Mth.sin(ageInTicks * 0.28F) * 0.04F;"""
stomp_new = """            // Keep both heavy front paws flat during the held stomp windup.
            ModelPart stompPawLeft = this.frontLeft.getChild("lower_leg").getChild("paw");
            ModelPart stompPawRight = this.frontRight.getChild("lower_leg").getChild("paw");
            stompPawLeft.xRot = -this.frontLeft.xRot * 0.46F;
            stompPawRight.xRot = -this.frontRight.xRot * 0.46F;
            stompPawLeft.y = 6.0F;
            stompPawRight.y = 6.0F;
            stompPawLeft.z = -1.0F;
            stompPawRight.z = -1.0F;
        } else if (state == MutagenkolossEntity.ATTACK_BREATH) {
            this.head.xRot = -0.34F + Mth.sin(ageInTicks * 0.28F) * 0.04F;"""
replace_once(stomp_anchor, stomp_new, "stabilize front paws for existing stomp attacks")

# Counter-balance the head after attack poses so the lateral rocking doesn't make the
# large cranial crown look disconnected. No extra tick loop, animation dependency or AI.
closing_anchor = """            for (ModelPart spine : this.spines) spine.zRot *= 1.9F;
        }
    }

    @Override"""
closing_new = """            for (ModelPart spine : this.spines) spine.zRot *= 1.9F;
        }
        // 1.82 neck counter-rotation: crest and jaw remain tied to the head's pivot.
        this.head.zRot = -this.body.zRot * 0.60F;
    }

    @Override"""
replace_once(closing_anchor, closing_new, "add head and crown counter-rotation")

# The 1.58 static regression tracked literal gait assignments: now the helper verifies
# all four loaded model leg chains instead, with the same geometry and moving pivots.
original_test = ROOT / "tools/test_mutagen_colossus.py"
if original_test.is_file():
    ts = original_test.read_text(encoding="utf-8")
    ts = ts.replace('    \'getChild("lower_leg").xRot\',',
                    '    \'leg.getChild("lower_leg")\', "lowerLeg.xRot",')
    original_test.write_text(ts, encoding="utf-8")

# Advance active-version contracts only; historical milestones and release notes survive.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_colossus_weighted_gait_182.py":
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.81.0",
                             "Aktueller Entwicklungsstand: 1.82.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.81\.0", r"1\.82\.0")
        updated = updated.replace("artifact must be version 1.81.0",
                                  "artifact must be version 1.82.0")
    updated = updated.replace(
        '"Version 1.81.0" in readme and "Version 1.80.0" in readme',
        '"Version 1.82.0" in readme and "Version 1.81.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

gradle = ROOT / "build.gradle"
current, n = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                     "version = '1.82.0'", gradle.read_text(encoding="utf-8"), count=1)
require(n == 1, "could not set Gradle artifact version")
gradle.write_text(current, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
current_notes = """## Aktueller Entwicklungsschritt — 1.82.0

- **Schwere vierbeinige Fortbewegung:** Diagonale Beinpaare des Kristallkolosses laufen in gegenläufigen Phasen; Oberschenkel, Unterschenkel und Tatzen besitzen eigene Bewegungsmuster.
- **Stand und Schwung statt Pendelgang:** Im Schwung wird eine Tatze leicht angehoben und nach vorn geführt. Während der Standphase bleibt sie näher am Boden. Die bisherigen starren Beinpendel sind ersetzt.
- **Körpergefühl:** Subtiles seitliches Schulterwiegen, Gegenrotation von Kopf und Kristallkrone sowie zeitversetzte Gegenschwünge in allen drei Schwanzsegmenten.
- **Kampf bleibt unterscheidbar:** Während des Stampfangriffs werden die Vorderpfoten unabhängig vom Laufschritt stabilisiert. Die bestehenden Biss-, Atem- und Erwachensanimationen sowie die Schadenswerte bleiben erhalten.
- **Technische Sicherheit:** Haut- und Glow-Modelle teilen sich die vorhandene Beinkette. Kein neuer Mob-Ticker, keine externen Animationsdateien und kein Chunk-Loading. Regressionen und vollständiger Forge-Build prüfen die Integration; ein Sichttest im Client steht aus.

"""
if "## Aktueller Entwicklungsschritt — 1.82.0" not in readme:
    anchor = "## Aktueller Entwicklungsschritt — 1.81.0"
    require(anchor in readme, "could not find the current 1.81 section")
    readme = readme.replace(anchor, current_notes + anchor, 1)
release_notes = """## Version 1.82.0 — Kristallkoloss: Gewicht in jedem Schritt

- **Neue Laufkinematik:** Vier individuelle Beinpfade mit gegenläufigen Diagonalphasen und differenziertem Schwung für Vorder- und Hinterbeine.
- **Bewegliche Tatzen:** Knie und Fußwinkel reagieren auf die Schrittphase; eine begrenzte vertikale und horizontale Tatzenkorrektur erzeugt erkennbare Stand-/Schwungphasen.
- **Verzögerte Masse:** Körperrollbewegung, korrigierende Kopfneigung und dreifach verzögerte Schwanzbewegung geben dem Kristallkoloss mehr körperliche Trägheit.
- **Saubere Boss-Posen:** Während des gehaltenen Stampfangriffs behalten die Vorderpfoten ihre aufgesetzte Position, statt ungewollt weiterzulaufen. Bestehende Angriffs- und Emissiv-Logik bleibt erhalten.
- **Prüfung:** Gesonderte Regression für Phasen, bewegte Tatzen, Schwanz, Stampfangriff, ModelPart-Hierarchie und Version; Forge-JAR und dedizierter Serverstart. Die tatsächliche visuelle Qualität erfordert weiterhin Client-Screenshots.

"""
if "## Version 1.82.0 — Kristallkoloss: Gewicht in jedem Schritt" not in readme:
    anchor = "## Version 1.81.0 —"
    require(anchor in readme, "could not find 1.81 release notes")
    readme = readme.replace(anchor, release_notes + anchor, 1)
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.81.0 — beweglicher Kristallkiefer und aufladender Kristallatem.**",
    "**Aktueller Entwicklungsstand: 1.82.0 — gewichtete Laufanimation und bewegliche Tatzen für den Kristallkoloss.**")
require("Aktueller Entwicklungsstand: 1.82.0" in readme, "README current version missing")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.82.0: weighted diagonal gait, independently flexed paws, body/head counterbalance, lagged tail and planted stomp feet.")
