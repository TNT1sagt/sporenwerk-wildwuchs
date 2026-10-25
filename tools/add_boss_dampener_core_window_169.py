#!/usr/bin/env python3
"""1.69.0 makes a successful Dampener breath interception expose the Colossus core."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.69: " + message)


def patch(source, old, new, sentinel, label):
    if sentinel in source:
        return source
    count = source.count(old)
    require(count == 1, f"{label}: expected one source anchor, got {count}")
    return source.replace(old, new, 1)


entity_path = SRC / "entity/MutagenkolossEntity.java"
entity = entity_path.read_text(encoding="utf-8")

# Both the charged placed Dampener and the Resonance Focus now share one
# server-authoritative visual/relay update for the short exposed-core window.
if "private void exposeCoreFromCountermeasure()" not in entity:
    focus_start = entity.find("public boolean interruptBreathWithResonance()")
    require(focus_start >= 0, "could not find existing Resonance Focus countermeasure")
    exposure_start = entity.find(
        "this.coreExposureTicks = Math.max(this.coreExposureTicks, 60);", focus_start)
    return_at = entity.find("        return true;", exposure_start)
    require(exposure_start >= 0 and return_at > exposure_start,
            "could not isolate focus core-exposure block")
    entity = (
        entity[:exposure_start]
        + "        this.exposeCoreFromCountermeasure();\n"
        + entity[return_at:]
    )

helper = """    /**
     * Shared feedback for a successful, server-authoritative countermeasure.
     * Refreshing nearby relays after setting CORE_EXPOSED lets automated bases
     * switch from a breath warning to the exposed-core signal immediately.
     */
    private void exposeCoreFromCountermeasure() {
        if (this.level().isClientSide) return;
        this.coreExposureTicks = Math.max(this.coreExposureTicks, 60);
        this.entityData.set(CORE_EXPOSED, true);
        MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());
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
    }

"""
entity = patch(
    entity,
    "    public boolean interruptBreathWithResonance() {",
    helper + "    public boolean interruptBreathWithResonance() {",
    "private void exposeCoreFromCountermeasure()",
    "shared countermeasure core-exposure feedback",
)

intercept_block = """        if (this.level() instanceof ServerLevel serverLevel
                && interceptCrystalBreath(serverLevel, origin, direction)) {
            for (Player player : this.level().getEntitiesOfClass(Player.class,
                    this.getBoundingBox().inflate(24.0D))) {
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.colossus.breath_intercepted"), true);
            }
            return;
        }"""
intercept_replacement = """        if (this.level() instanceof ServerLevel serverLevel
                && interceptCrystalBreath(serverLevel, origin, direction)) {
            this.exposeCoreFromCountermeasure();
            for (Player player : this.level().getEntitiesOfClass(Player.class,
                    this.getBoundingBox().inflate(24.0D))) {
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.colossus.breath_intercepted"), true);
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.colossus.core_exposed"), false);
            }
            return;
        }"""
entity = patch(
    entity, intercept_block, intercept_replacement,
    'player.displayClientMessage(Component.translatable(\n                        "message.sporenwerk.colossus.core_exposed"), false);',
    "Dampener interception must open the core and notify nearby players",
)
require("MutagenContainmentRelayBlock.refreshNearbyRelays(this.level(), this.blockPosition());"
        in entity, "shared exposure helper must refresh boss-response relays")
entity_path.write_text(entity, encoding="utf-8")

for filename, value in (
    ("de_de.json", "Der Dämpfer hat den Kristallatem abgefangen! Der Kristallkern ist verwundbar."),
    ("en_us.json", "The Dampener caught the crystal breath! The crystal core is exposed."),
):
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale["message.sporenwerk.colossus.core_exposed"] = value
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Preserve all historical regression suites while advancing the active build metadata.
new_tests = {"test_boss_dampener_core_window_169.py"}
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name in new_tests:
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.68.0",
                             "Aktueller Entwicklungsstand: 1.69.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.68\.0", r"1\.69\.0")
        updated = updated.replace("artifact must be version 1.68.0",
                                  "artifact must be version 1.69.0")
    updated = updated.replace(
        '"Version 1.68.0" in readme and "Version 1.67.0" in readme',
        '"Version 1.69.0" in readme and "Version 1.68.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.69.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle version to 1.69.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.69.0 — Dämpfer-Parade öffnet den Kristallkern

- **Mehr als Schadensvermeidung:** Fängt ein geladener Resonanzdämpfer den Kristallatem ab, wird der Kristallkern 60 Ticks lang verwundbar. Schutzanlagen erzeugen damit ein aktives Gegenangriffsfenster, statt nur Schaden zu verhindern.
- **Gemeinsame Gegenmaßnahme:** Resonanzfokus und platzierter Dämpfer verwenden denselben serverseitigen Effekt für Kernöffnung, Kristallpartikel, Klang und Relais-Aktualisierung.
- **Redstone reagiert sofort:** Der Boss-Reaktionsmodus wird nach dem Abfangen erneut ausgewertet und wechselt von der Atemwarnung zur Kernöffnung. Bestehende Ereignis- und Chunk-Grenzen bleiben bestehen.
- **Spielerfeedback:** Nahe Spieler erhalten eine lokale Bestätigung, dass der Atem abgefangen und der Kern freigelegt wurde.
- **Qualitätssicherung:** Regressionen prüfen Aufladungskosten, Reihenfolge des Abfangens, 60-Tick-Fenster, Relais-Aktualisierung und DE/EN-Texte.

"""
if "## Version 1.69.0 — Dämpfer-Parade öffnet den Kristallkern" not in readme:
    marker = "## Version 1.68.0 — Boss-Reaktionssignal für Redstone und Fokus-Priorität"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.68.0 release notes")
    readme = readme[:idx] + release + readme[idx:]

current = """## Aktueller Entwicklungsschritt — 1.69.0

- **Dämpfer als Gegenangriff:** Ein geladener Resonanzdämpfer, der den Kristallatem abfängt, legt den Kern für 60 Ticks frei. Die Gegenmaßnahme bleibt an den tatsächlichen Verbrauch einer Dämpferladung gebunden.
- **Gemeinsamer Kernöffnungs-Effekt:** Resonanzfokus und Dämpfer nutzen denselben serverseitigen Effekt für Partikel, Klang und Redstone-Relais-Refresh.
- **Live-Redstone-Rückmeldung:** Relais erkennen nach der abgefangenen Atemattacke den freigelegten Kern, sobald der Angriffszustand zurückgesetzt wurde.
- **Keine zusätzlichen Dauerabfragen:** Der bestehende begrenzte Scan und die Ereignisverteilung werden weiterverwendet; es gibt keinen neuen Tick-Loop und keine erzwungenen Chunk-Ladevorgänge.

"""
if "## Aktueller Entwicklungsschritt — 1.69.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.68.0"
    idx = readme.find(marker)
    require(idx >= 0, "could not find active 1.68.0 development section")
    readme = readme[:idx] + current + readme[idx:]

readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.68.0 — Boss-Reaktionssignal und priorisierte Resonanzfokus-Parade.**",
    "**Aktueller Entwicklungsstand: 1.69.0 — Dämpfer-Parade und verwundbarer Kristallkern.**")
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.69.0: Dampener interception now exposes the Colossus core and updates Redstone response relays.")
