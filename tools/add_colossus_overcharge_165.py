#!/usr/bin/env python3
"""1.65.0 adds a counterplay window to the Colossus and a containment-margin relay mode."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.65: " + message)


def patch(source, old, new, sentinel, label):
    if sentinel in source:
        return source
    count = source.count(old)
    require(count == 1, f"{label}: expected one source anchor, got {count}")
    return source.replace(old, new, 1)


# Crystal Colossus: the crystal breath leaves the core overloaded for 90 ticks.
entity_path = SRC / "entity/MutagenkolossEntity.java"
entity = entity_path.read_text(encoding="utf-8")
entity = patch(
    entity,
    '    private static final EntityDataAccessor<Integer> ATTACK_TICKS =\n'
    '            SynchedEntityData.defineId(MutagenkolossEntity.class, EntityDataSerializers.INT);\n',
    '    private static final EntityDataAccessor<Integer> ATTACK_TICKS =\n'
    '            SynchedEntityData.defineId(MutagenkolossEntity.class, EntityDataSerializers.INT);\n'
    '    private static final EntityDataAccessor<Boolean> CORE_EXPOSED =\n'
    '            SynchedEntityData.defineId(MutagenkolossEntity.class, EntityDataSerializers.BOOLEAN);\n'
    '    private static final int CORE_EXPOSURE_DURATION = 90;\n',
    "CORE_EXPOSURE_DURATION = 90",
    "synced core exposure state",
)
entity = patch(
    entity,
    "    private int attackCooldown = 80;\n",
    "    private int attackCooldown = 80;\n    private int coreExposureTicks;\n",
    "private int coreExposureTicks;",
    "core exposure timer",
)
entity = patch(
    entity,
    "        this.entityData.define(ATTACK_STATE, ATTACK_IDLE);\n"
    "        this.entityData.define(ATTACK_TICKS, 0);\n",
    "        this.entityData.define(ATTACK_STATE, ATTACK_IDLE);\n"
    "        this.entityData.define(ATTACK_TICKS, 0);\n"
    "        this.entityData.define(CORE_EXPOSED, false);\n",
    "this.entityData.define(CORE_EXPOSED, false);",
    "synced core exposure default",
)
entity = patch(
    entity,
    "    public int getAttackTicks() { return this.entityData.get(ATTACK_TICKS); }\n",
    "    public int getAttackTicks() { return this.entityData.get(ATTACK_TICKS); }\n"
    "    public boolean isCoreExposed() { return this.entityData.get(CORE_EXPOSED); }\n",
    "public boolean isCoreExposed()",
    "client-readable core exposure state",
)
entity = patch(
    entity,
    "    @Override\n    public void tick() {\n",
    "    @Override\n"
    "    public boolean hurt(DamageSource source, float amount) {\n"
    "        if (this.isCoreExposed() && source.getEntity() != null) amount *= 1.30F;\n"
    "        return super.hurt(source, amount);\n"
    "    }\n\n"
    "    @Override\n"
    "    public void tick() {\n",
    "public boolean hurt(DamageSource source, float amount)",
    "overloaded-core damage window",
)
entity = patch(
    entity,
    "        if (this.level().isClientSide) return;\n\n"
    "        this.bossEvent.setProgress",
    "        if (this.level().isClientSide) return;\n\n"
    "        if (this.coreExposureTicks > 0) {\n"
    "            this.coreExposureTicks--;\n"
    "            if (this.coreExposureTicks == 0) {\n"
    "                this.entityData.set(CORE_EXPOSED, false);\n"
    "            } else if (this.coreExposureTicks % 6 == 0\n"
    "                    && this.level() instanceof ServerLevel exposureLevel) {\n"
    "                exposureLevel.sendParticles(ParticleTypes.END_ROD,\n"
    "                        this.getX(), this.getY() + 2.15D, this.getZ(), 5,\n"
    "                        0.28D, 0.18D, 0.28D, 0.012D);\n"
    "            }\n"
    "        }\n\n"
    "        this.bossEvent.setProgress",
    "this.coreExposureTicks % 6 == 0",
    "overcharge timer and visible feedback",
)
entity = patch(
    entity,
    "        } else if (state == ATTACK_BREATH) {\n"
    "            performCrystalBreath();\n"
    "            this.attackCooldown = 128;\n",
    "        } else if (state == ATTACK_BREATH) {\n"
    "            performCrystalBreath();\n"
    "            this.coreExposureTicks = CORE_EXPOSURE_DURATION;\n"
    "            this.entityData.set(CORE_EXPOSED, true);\n"
    "            for (Player player : this.level().getEntitiesOfClass(Player.class,\n"
    "                    this.getBoundingBox().inflate(24.0D))) {\n"
    "                player.displayClientMessage(\n"
    "                        Component.translatable(\"message.sporenwerk.colossus.core_exposed\"), true);\n"
    "            }\n"
    "            this.attackCooldown = 128;\n",
    "this.coreExposureTicks = CORE_EXPOSURE_DURATION;",
    "open exposed-core counterplay window",
)
entity = patch(
    entity,
    "        this.attackTicksLeft = 0;\n"
    "        this.entityData.set(ATTACK_STATE, ATTACK_IDLE);\n"
    "        this.entityData.set(ATTACK_TICKS, 0);\n",
    "        this.attackTicksLeft = 0;\n"
    "        this.coreExposureTicks = 0;\n"
    "        this.entityData.set(CORE_EXPOSED, false);\n"
    "        this.entityData.set(ATTACK_STATE, ATTACK_IDLE);\n"
    "        this.entityData.set(ATTACK_TICKS, 0);\n",
    "this.coreExposureTicks = 0;",
    "clear overcharge state on entity load",
)
entity_path.write_text(entity, encoding="utf-8")

model_path = SRC / "client/MutagenkolossModel.java"
model = model_path.read_text(encoding="utf-8")
model = patch(
    model,
    "        float pulseScale = 1.0F + 0.012F + heartbeat * 0.026F + afterBeat * 0.014F;\n",
    "        float overloadSurge = entity.isCoreExposed() ? 0.085F : 0.0F;\n"
    "        float pulseScale = 1.0F + 0.012F + heartbeat * 0.026F + afterBeat * 0.014F + overloadSurge;\n",
    "float overloadSurge = entity.isCoreExposed()",
    "visible overcharge core flare",
)
model = patch(
    model,
    "            float spinePulse = 1.0F + heartbeat * 0.018F;\n",
    "            float spinePulse = 1.0F + heartbeat * 0.018F\n"
    "                    + (entity.isCoreExposed() ? 0.055F : 0.0F);\n",
    "entity.isCoreExposed() ? 0.055F",
    "overcharge dorsal crystal flare",
)
model_path.write_text(model, encoding="utf-8")

for filename, value in (
    ("de_de.json", "Der Kristallkern ist überladen! Jetzt verursacht ihr 30 % mehr Schaden."),
    ("en_us.json", "The crystal core is overloaded! Strike now for 30% more damage."),
):
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale["message.sporenwerk.colossus.core_exposed"] = value
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Mode 6 expresses a 0-15 containment margin; 15 means no detected threat.
relay_path = SRC / "block/MutagenContainmentRelayBlock.java"
relay = relay_path.read_text(encoding="utf-8")
relay = patch(
    relay,
    'public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 5);',
    'public static final IntegerProperty MODE = IntegerProperty.create("mode", 0, 6);',
    'IntegerProperty MODE = IntegerProperty.create("mode", 0, 6)',
    "seven relay modes",
)
relay = patch(
    relay,
    "int mode = (state.getValue(MODE) + step) % 6;",
    "int mode = (state.getValue(MODE) + step) % 7;",
    "state.getValue(MODE) + step) % 7",
    "seven-mode cycling",
)
relay = patch(
    relay,
    '            case 5 -> "message.sporenwerk.containment_relay.mode_residual";',
    '            case 5 -> "message.sporenwerk.containment_relay.mode_residual";\n'
    '            case 6 -> "message.sporenwerk.containment_relay.mode_margin";',
    'case 6 -> "message.sporenwerk.containment_relay.mode_margin"',
    "containment margin mode label",
)
relay = patch(
    relay,
    "     * Mode 5: estimated residual threat after nearby powered wards and remaining dampener charges.\n",
    "     * Mode 5: estimated residual threat after nearby powered wards and remaining dampener charges.\n"
    "     * Mode 6: containment margin; higher comparator output means a larger safety buffer.\n",
    "Mode 6: containment margin",
    "mode documentation",
)
switch_anchor = "            default -> Math.max(stationSignal, sirenSignal);"
switch_case = """            case 6 -> {
                int fieldThreat = 0;
                if (tierThreeSoil > 0) {
                    fieldThreat = Math.min(15, 11 + Math.min(4, (tierThreeSoil - 1) / 4));
                } else if (tierTwoSoil > 0) {
                    fieldThreat = Math.min(10, 7 + Math.min(3, (tierTwoSoil - 1) / 8));
                } else if (tierOneSoil > 0) {
                    fieldThreat = Math.min(6, 3 + Math.min(3, (tierOneSoil - 1) / 16));
                } else if (mutatedCrops > 0) {
                    fieldThreat = 2;
                }
                int rawThreat = Math.max(Math.max(stationSignal, sirenSignal), fieldThreat);
                int protectionBuffer = Math.min(12,
                        poweredWards * 4 + Math.min(3, counterpulses) * 3);
                yield rawThreat == 0 ? 15
                        : Math.max(0, Math.min(15, 8 + protectionBuffer - rawThreat));
            }
            default -> Math.max(stationSignal, sirenSignal);"""
relay = patch(relay, switch_anchor, switch_case, "case 6 -> {\n                int fieldThreat", "containment margin comparator output")
relay_path.write_text(relay, encoding="utf-8")

blockstate_path = ASSETS / "blockstates/mutagen_containment_relay.json"
blockstate_path.write_text(json.dumps({
    "variants": {
        f"mode={mode},signal={signal}": {"model": "sporenwerk:block/mutagen_containment_relay"}
        for mode in range(7) for signal in range(16)
    }
}, indent=2) + "\n", encoding="utf-8")
for filename, value in (
    ("de_de.json", "Containment-Sicherheitspuffer"),
    ("en_us.json", "Containment margin"),
):
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale["message.sporenwerk.containment_relay.mode_margin"] = value
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for test_name in (
    "test_mutagen_containment_relay.py",
    "test_field_intensity_relay_163.py",
    "test_field_response_relay_164.py",
):
    test_path = ROOT / "tools" / test_name
    source = test_path.read_text(encoding="utf-8")
    for old, new in (
        ('IntegerProperty MODE = IntegerProperty.create("mode", 0, 5)',
         'IntegerProperty MODE = IntegerProperty.create("mode", 0, 6)'),
        ("int mode = (state.getValue(MODE) + step) % 6;",
         "int mode = (state.getValue(MODE) + step) % 7;"),
        ("len(variants) == 96", "len(variants) == 112"),
        ("for mode in range(6):", "for mode in range(7):"),
        ("all 6 MODE × 16 SIGNAL", "all 7 MODE × 16 SIGNAL"),
        ("six modes × sixteen signals", "seven modes × sixteen signals"),
    ):
        if new not in source and old in source:
            source = source.replace(old, new, 1)
    if '"message.sporenwerk.containment_relay.mode_margin",' not in source:
        anchor = '"message.sporenwerk.containment_relay.mode_residual",'
        if anchor in source:
            source = source.replace(anchor, anchor + '\n        "message.sporenwerk.containment_relay.mode_margin",', 1)
    if '"case 6 ->"' not in source and '"case 5 ->"' in source:
        source = source.replace('"case 5 ->",', '"case 5 ->",\n    "case 6 ->",', 1)
    test_path.write_text(source, encoding="utf-8")

# The older heartbeat regression must follow the extended pulse expression added above.
# Otherwise the feature is correct but the previous visual contract falsely rejects it.
heartbeat_test_path = ROOT / "tools/test_colossus_visual_161.py"
if heartbeat_test_path.exists():
    heartbeat_test = heartbeat_test_path.read_text(encoding="utf-8")
    old_pulse_contract = '"float pulseScale = 1.0F + 0.012F + heartbeat * 0.026F + afterBeat * 0.014F;",'
    new_pulse_contract = '"float pulseScale = 1.0F + 0.012F + heartbeat * 0.026F + afterBeat * 0.014F + overloadSurge;",'
    if old_pulse_contract in heartbeat_test:
        heartbeat_test = heartbeat_test.replace(old_pulse_contract, new_pulse_contract, 1)
        heartbeat_test_path.write_text(heartbeat_test, encoding="utf-8")
    else:
        require(new_pulse_contract in heartbeat_test,
                "could not migrate heartbeat regression to the overload pulse expression")

new_tests = {"test_colossus_overcharge_165.py", "test_containment_margin_relay_165.py"}
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name in new_tests:
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.64.0",
                             "Aktueller Entwicklungsstand: 1.65.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.64\.0", r"1\.65\.0")
        updated = updated.replace("artifact must be version 1.64.0",
                                  "artifact must be version 1.65.0")
    updated = updated.replace(
        '"Version 1.64.0" in readme and "Version 1.63.0" in readme',
        '"Version 1.65.0" in readme and "Version 1.64.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.65.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.65.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.65.0 — Überladener Kristallkern und Containment-Sicherheitspuffer

- **Boss-Gegenmaßnahme:** Nach dem Kristallatem ist der Kristallkern 90 Ticks lang überladen. Partikelfeedback und eine DE/EN-Actionbar-Meldung kündigen das Zeitfenster an.
- **Belohnung für gutes Timing:** Spieler- und Projektilschaden steigt während der Überladung um 30 %. Nach Ablauf endet der Bonus automatisch; ein neu geladener Boss startet ohne alten Überladungszustand.
- **Lesbare Animation:** Brustkern und dorsale Kristalle verstärken während des Fensters ihren Puls. Haut- und Full-Bright-Layer bleiben synchron.
- **Neuer Relaismodus 6:** „Containment-Sicherheitspuffer“ liefert einen Comparator-Wert von 0 bis 15. 15 bedeutet keine erkannte Gefahr; bei vorhandener Gefahr erhöhen mehr aktive Schutzressourcen den Sicherheitswert.
- **Begrenzte Diagnose:** Der Modus nutzt die bisherige geladene Umgebung; er führt keine dauerhafte Tick-Schleife und keine Chunk-Ladevorgänge ein.
- **Qualitätssicherung:** Regressionen prüfen Überladungsdauer, Schaden, sichtbare Animation, DE/EN-Texte, 112 Relaiszustände und den installierbaren Gesamtbuild.

"""
if "## Version 1.65.0 — Überladener Kristallkern und Containment-Sicherheitspuffer" not in readme:
    marker = "## Version 1.64.0 — Kopfpanzer des Kristallkolosses und Restgefahr-Signal"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.64.0 release section")
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.65.0 — überladener Kristallkern und Containment-Sicherheitspuffer.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus = [line for line in readme.splitlines() if line.startswith("## Aktueller Entwicklungsschritt — ")]
if focus:
    readme = readme.replace(focus[0], "## Aktueller Entwicklungsschritt — 1.65.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.65.0 overcharged core and containment margin generated.")
