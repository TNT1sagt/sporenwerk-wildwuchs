#!/usr/bin/env python3
"""Sporenwerk 1.91: three persistent non-damaging Crystal Colossus arrival pulses."""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
P = ROOT / "src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java"
s = P.read_text(encoding="utf-8")

def patch(old, new):
    global s
    if new in s: return
    assert s.count(old) == 1, ("Colossus arrival anchor", old[:120], s.count(old))
    s = s.replace(old, new, 1)

assert "private void emitGroundRing(ServerLevel serverLevel" in s
patch("    private boolean secondPhaseTriggered;", """    private boolean secondPhaseTriggered;
    // Persistent one-time introduction, executed on the existing server-side boss tick.
    private int arrivalPulseStage;""")
patch("""        this.bossEvent.setProgress(Math.max(0.0F, Math.min(1.0F, this.getHealth() / this.getMaxHealth())));
        if (this.attackCooldown > 0) this.attackCooldown--;""",
"""        this.bossEvent.setProgress(Math.max(0.0F, Math.min(1.0F, this.getHealth() / this.getMaxHealth())));
        if (this.arrivalPulseStage < 3 && this.tickCount % 20 == 0
                && this.level() instanceof ServerLevel arrivalLevel) {
            emitArrivalPulse(arrivalLevel, this.arrivalPulseStage);
            this.arrivalPulseStage++;
        }
        if (this.attackCooldown > 0) this.attackCooldown--;""")
patch("    private void beginAttack(int state, int duration) {", """    /**
     * Three purely visual arrival waves. Different from damaging stomp rings.
     * No camera manipulation, effects, terrain access or forced chunks.
     */
    private void emitArrivalPulse(ServerLevel level, int stage) {
        if (stage < 0 || stage > 2) return;
        double radius = 2.8D + stage * 1.6D;
        for (int sample = 0; sample < 24; sample++) {
            double angle = sample * Math.PI * 2.0D / 24.0D;
            double x = this.getX() + Math.cos(angle) * radius;
            double z = this.getZ() + Math.sin(angle) * radius;
            level.sendParticles(ParticleTypes.END_ROD, x, this.getY() + 0.35D, z,
                    1, 0.06D, 0.05D, 0.06D, 0.014D);
            if (sample % 2 == 0) {
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, x, this.getY() + 0.55D, z,
                        1, 0.08D, 0.14D, 0.08D, 0.007D);
            }
        }
        level.sendParticles(ParticleTypes.WARPED_SPORE,
                this.getX(), this.getY() + 2.7D, this.getZ(),
                10 + stage * 6, 1.0D, 0.6D, 1.0D, 0.018D);
        level.playSound(null, this.blockPosition(),
                stage == 2 ? SoundEvents.RESPAWN_ANCHOR_DEPLETE : SoundEvents.AMETHYST_BLOCK_CHIME,
                SoundSource.HOSTILE, 1.1F, stage == 2 ? 0.55F : 0.70F - stage * 0.10F);
        if (stage == 0) {
            for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class,
                    this.getBoundingBox().inflate(28.0D, 12.0D, 28.0D))) {
                if (!player.isSpectator()) {
                    player.displayClientMessage(Component.translatable(
                            "message.sporenwerk.colossus.arrival"), true);
                }
            }
        }
    }

    private void beginAttack(int state, int duration) {""")
patch('        tag.putBoolean("SporenwerkPhaseTwo", this.secondPhaseTriggered);',
      '        tag.putBoolean("SporenwerkPhaseTwo", this.secondPhaseTriggered);\n        tag.putInt("SporenwerkArrivalPulseStage", this.arrivalPulseStage);')
patch('        this.secondPhaseTriggered = tag.getBoolean("SporenwerkPhaseTwo");',
      '        this.secondPhaseTriggered = tag.getBoolean("SporenwerkPhaseTwo");\n        this.arrivalPulseStage = Math.max(0, Math.min(3, tag.getInt("SporenwerkArrivalPulseStage")));')
assert "getChunk(" not in s and "getChunkNow(" not in s
P.write_text(s, encoding="utf-8")
print("1.91 Colossus non-damaging 3-stage saved arrival installed.")
