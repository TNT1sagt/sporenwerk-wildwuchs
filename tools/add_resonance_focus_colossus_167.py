#!/usr/bin/env python3
"""1.67.0 lets the shard-powered Resonance Focus interrupt the Colossus crystal breath."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.67: " + message)


def patch(source, old, new, sentinel, label):
    if sentinel in source:
        return source
    count = source.count(old)
    require(count == 1, f"{label}: expected exactly one source anchor, got {count}")
    return source.replace(old, new, 1)


# A successful parry is only possible during the clearly telegraphed breath wind-up.
# It stops the attack, starts a short cooldown, and exposes the core for counterdamage.
entity_path = SRC / "entity/MutagenkolossEntity.java"
entity = entity_path.read_text(encoding="utf-8")
interrupt_method = """    /**
     * Interrupt a telegraphed crystal breath with a focused resonance pulse.
     * The method is called server-side after the player's shard has been consumed.
     */
    public boolean interruptBreathWithResonance() {
        if (this.level().isClientSide
                || this.getAttackState() != ATTACK_BREATH
                || this.attackTicksLeft < 8) return false;

        this.attackTicksLeft = 0;
        this.attackCooldown = Math.max(this.attackCooldown, 90);
        this.entityData.set(ATTACK_STATE, ATTACK_IDLE);
        this.entityData.set(ATTACK_TICKS, 0);
        this.coreExposureTicks = Math.max(this.coreExposureTicks, 60);
        this.entityData.set(CORE_EXPOSED, true);

        if (this.level() instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    this.getX(), this.getY() + 2.15D, this.getZ(), 28,
                    0.48D, 0.42D, 0.48D, 0.035D);
            serverLevel.sendParticles(ParticleTypes.CRIT,
                    this.getX(), this.getY() + 1.95D, this.getZ(), 18,
                    0.35D, 0.32D, 0.35D, 0.025D);
        }
        this.level().playSound(null, this.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME,
                SoundSource.HOSTILE, 1.2F, 0.72F);
        return true;
    }

"""
entity = patch(
    entity,
    "    public int getAttackTicks() { return this.entityData.get(ATTACK_TICKS); }\n",
    "    public int getAttackTicks() { return this.entityData.get(ATTACK_TICKS); }\n\n" + interrupt_method,
    "public boolean interruptBreathWithResonance()",
    "server-authoritative breath parry",
)
entity_path.write_text(entity, encoding="utf-8")

focus_path = SRC / "item/ResonanzfokusItem.java"
focus = focus_path.read_text(encoding="utf-8")
focus = patch(
    focus,
    "import de.sporenwerk.entity.KristallpirscherEntity;\n",
    "import de.sporenwerk.entity.KristallpirscherEntity;\n"
    "import de.sporenwerk.entity.MutagenkolossEntity;\n",
    "import de.sporenwerk.entity.MutagenkolossEntity;",
    "focus Colossus target import",
)
stalker_targets = """        targets.addAll(serverLevel.getEntitiesOfClass(KristallpirscherEntity.class,
                player.getBoundingBox().inflate(PULSE_RADIUS), entity -> entity.isAlive()));
"""
focus = patch(
    focus,
    stalker_targets,
    stalker_targets + """        targets.addAll(serverLevel.getEntitiesOfClass(MutagenkolossEntity.class,
                player.getBoundingBox().inflate(PULSE_RADIUS),
                entity -> entity.isAlive()
                        && entity.getAttackState() == MutagenkolossEntity.ATTACK_BREATH
                        && entity.getAttackTicks() >= 8));
""",
    "targets.addAll(serverLevel.getEntitiesOfClass(MutagenkolossEntity.class",
    "only interruptible Colossus wind-ups become focus targets",
)
loop_anchor = """            if (affected >= MAX_TARGETS) break;
            boolean stalker = target instanceof KristallpirscherEntity;
"""
loop_new = """            if (affected >= MAX_TARGETS) break;
            if (target instanceof MutagenkolossEntity colossus
                    && colossus.interruptBreathWithResonance()) {
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.resonanzfokus.colossus_interrupted")
                        .withStyle(ChatFormatting.AQUA), false);
                affected++;
                continue;
            }
            boolean stalker = target instanceof KristallpirscherEntity;
"""
focus = patch(
    focus, loop_anchor, loop_new,
    "colossus.interruptBreathWithResonance()",
    "focus parry result and counterattack window",
)
focus_path.write_text(focus, encoding="utf-8")

for filename, locale in (
    ("de_de.json", {
        "tooltip.sporenwerk.resonanzfokus.2": "Verbraucht 1 Resonanzsplitter; trifft bis zu 3 Gegner in 5,5 Blöcken. Unterbricht den Kristallatem während der Aufladung und legt den Kern frei. Abklingzeit: 4 s.",
        "message.sporenwerk.resonanzfokus.colossus_interrupted": "Kristallatem unterbrochen! Der Kern ist jetzt verwundbar.",
    }),
    ("en_us.json", {
        "tooltip.sporenwerk.resonanzfokus.2": "Consumes 1 Resonance Shard; reaches up to 3 threats within 5.5 blocks. Interrupts the charging crystal breath and exposes the core. Cooldown: 4 s.",
        "message.sporenwerk.resonanzfokus.colossus_interrupted": "Crystal breath interrupted! The core is exposed.",
    }),
):
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(locale)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

new_tests = {"test_resonance_focus_colossus_167.py"}
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name in new_tests:
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.66.0",
                             "Aktueller Entwicklungsstand: 1.67.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.66\.0", r"1\.67\.0")
        updated = updated.replace("artifact must be version 1.66.0",
                                  "artifact must be version 1.67.0")
    updated = updated.replace(
        '"Version 1.66.0" in readme and "Version 1.65.0" in readme',
        '"Version 1.67.0" in readme and "Version 1.66.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.67.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.67.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.67.0 — Resonanzfokus kann den Kristallatem parieren

- **Aktive Gegenmaßnahme:** Der Resonanzfokus erkennt den telegraphierten Kristallatem des Kristallkolosses im Nahbereich und unterbricht ihn, solange noch mindestens acht Wind-up-Ticks verbleiben.
- **Bezahlte Parieraktion:** Der erfolgreiche Einsatz verbraucht den vorhandenen Resonanzsplitter und startet die reguläre Fokus-Abklingzeit; ohne passende Situation wird der Koloss nicht als Fokusziel ausgewählt.
- **Konterfenster:** Nach der Unterbrechung wird der Kern 60 Ticks freigelegt, die Rücken-/Kern-Glow-Animation reagiert darauf und der Koloss erhält eine kurze Angriffspause.
- **Mehr als eine Abwehrstrategie:** Spieler können den Strahl weiterhin mit einem platzierten, geladenen Dämpfer abfangen oder den Fokus im richtigen Moment selbst einsetzen.
- **Regressionen:** Neue Prüfungen sichern Wind-up-Grenze, Zustands-Synchronisierung, Splitterverbrauch, Kernfenster und DE/EN-Rückmeldung.

"""
if "## Version 1.67.0 — Resonanzfokus kann den Kristallatem parieren" not in readme:
    marker = "## Version 1.66.0 — Kristallatem abfangen und Sicherheitsreserve richtig markieren"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.66.0 release notes")
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.67.0 — Resonanzfokus-Parade und verwundbarer Kristallkern.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus_heads = [line for line in readme.splitlines() if line.startswith("## Aktueller Entwicklungsschritt — ")]
if focus_heads:
    readme = readme.replace(focus_heads[0], "## Aktueller Entwicklungsschritt — 1.67.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.67.0 Resonance Focus parry and exposed-core counterplay generated.")
