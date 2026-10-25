#!/usr/bin/env python3
"""1.66.0 lets charged resonance dampeners intercept Colossus breath and fixes margin colors."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
ASSETS = ROOT / "src/main/resources/assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Sporenwerk 1.66: " + message)


def patch(source, old, new, sentinel, label):
    if sentinel in source:
        return source
    count = source.count(old)
    require(count == 1, f"{label}: expected exactly one source anchor, got {count}")
    return source.replace(old, new, 1)


# 1) Wire the existing finite-charge Resonance Dampener into the boss's actual breath path.
entity_path = SRC / "entity/MutagenkolossEntity.java"
entity = entity_path.read_text(encoding="utf-8")
imports = (
    "import de.sporenwerk.block.MutagenContainmentRelayBlock;",
    "import de.sporenwerk.block.MutagenResonanceDampenerBlock;",
    "import de.sporenwerk.registry.ModBlocks;",
    "import net.minecraft.world.level.block.state.BlockState;",
)
for line in imports:
    if line not in entity:
        anchor = "package de.sporenwerk.entity;\n"
        require(anchor in entity, "entity package declaration missing while adding dampener imports")
        entity = entity.replace(anchor, anchor + "\n" + line, 1)

breath_anchor = """        Vec3 direction = this.getLookAngle().normalize();
        Vec3 origin = this.position().add(0.0D, 2.15D, 0.0D).add(direction.scale(1.2D));
        if (this.level() instanceof ServerLevel serverLevel) {"""
breath_replacement = """        Vec3 direction = this.getLookAngle().normalize();
        Vec3 origin = this.position().add(0.0D, 2.15D, 0.0D).add(direction.scale(1.2D));
        if (this.level() instanceof ServerLevel serverLevel
                && interceptCrystalBreath(serverLevel, origin, direction)) {
            for (Player player : this.level().getEntitiesOfClass(Player.class,
                    this.getBoundingBox().inflate(24.0D))) {
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.colossus.breath_intercepted"), true);
            }
            return;
        }
        if (this.level() instanceof ServerLevel serverLevel) {"""
entity = patch(
    entity, breath_anchor, breath_replacement,
    "interceptCrystalBreath(serverLevel, origin, direction)",
    "charged-dampener interception hook"
)

helper = """    /**
     * A charged Dampener placed directly against the projected breath path absorbs one breath.
     * The scan is deliberately short and bounded; unloaded chunks are never queried.
     */
    private boolean interceptCrystalBreath(ServerLevel level, Vec3 origin, Vec3 direction) {
        for (int step = 1; step <= 16; step++) {
            BlockPos center = BlockPos.containing(origin.add(direction.scale(step)));
            for (BlockPos.MutableBlockPos candidate : BlockPos.betweenClosed(
                    center.offset(-1, -1, -1), center.offset(1, 1, 1))) {
                if (!level.hasChunkAt(candidate)) continue;
                BlockState state = level.getBlockState(candidate);
                if (!state.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                        || !state.hasProperty(MutagenResonanceDampenerBlock.CHARGE)
                        || state.getValue(MutagenResonanceDampenerBlock.CHARGE) <= 0) continue;

                BlockPos dampenerPos = candidate.immutable();
                int charge = state.getValue(MutagenResonanceDampenerBlock.CHARGE);
                level.setBlock(dampenerPos,
                        state.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1), 3);
                MutagenContainmentRelayBlock.refreshNearbyRelays(level, dampenerPos);
                level.sendParticles(ParticleTypes.END_ROD,
                        dampenerPos.getX() + 0.5D, dampenerPos.getY() + 0.8D,
                        dampenerPos.getZ() + 0.5D, 18, 0.3D, 0.3D, 0.3D, 0.035D);
                level.sendParticles(ParticleTypes.CRIT,
                        dampenerPos.getX() + 0.5D, dampenerPos.getY() + 0.65D,
                        dampenerPos.getZ() + 0.5D, 10, 0.24D, 0.24D, 0.24D, 0.025D);
                level.playSound(null, dampenerPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                        SoundSource.BLOCKS, 1.0F, 0.72F);
                return true;
            }
        }
        return false;
    }

"""
helper_anchor = "    @Override\n    public void addAdditionalSaveData(CompoundTag tag) {"
if "private boolean interceptCrystalBreath(ServerLevel level, Vec3 origin, Vec3 direction)" not in entity:
    require(entity.count(helper_anchor) == 1, "cannot locate entity persistence methods for interception helper")
    entity = entity.replace(helper_anchor, helper + helper_anchor, 1)
entity_path.write_text(entity, encoding="utf-8")

for filename, value in (
    ("de_de.json", "Resonanzdämpfer hat den Kristallatem abgefangen! Eine Ladung wurde verbraucht."),
    ("en_us.json", "Resonance Dampener intercepted the crystal breath! One charge was consumed."),
):
    path = ASSETS / "lang" / filename
    locale = json.loads(path.read_text(encoding="utf-8"))
    locale["message.sporenwerk.colossus.breath_intercepted"] = value
    path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 2) Mode 6 is a safety margin, not a threat value: invert player-facing color thresholds.
relay_path = SRC / "block/MutagenContainmentRelayBlock.java"
relay = relay_path.read_text(encoding="utf-8")
color_start = "    private static ChatFormatting colorFor(int mode, int signal) {"
color_end = "\n    private static String modeKey(int mode) {"
start = relay.find(color_start)
require(start >= 0, "could not find relay colorFor method")
end = relay.find(color_end, start)
require(end > start, "could not find relay modeKey after colorFor")
color_method = """    private static ChatFormatting colorFor(int mode, int signal) {
        if (mode == 6) {
            if (signal <= 3) return ChatFormatting.RED;
            if (signal <= 7) return ChatFormatting.YELLOW;
            return ChatFormatting.GREEN;
        }
        if ((mode == 3 || mode == 4 || mode == 5) && signal >= 11) return ChatFormatting.RED;
        if (signal >= 11) return ChatFormatting.RED;
        if (signal > 0) return ChatFormatting.YELLOW;
        return ChatFormatting.GREEN;
    }
"""
current_color = relay[start:end]
if "if (mode == 6)" not in current_color:
    relay = relay[:start] + color_method + relay[end:]
relay_path.write_text(relay, encoding="utf-8")

# Promote all active-version assertions in the generated test suite only after patches are installed.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_boss_breath_dampener_166.py":
        continue
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.65.0",
                             "Aktueller Entwicklungsstand: 1.66.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.65\.0", r"1\.66\.0")
        updated = updated.replace("artifact must be version 1.65.0",
                                  "artifact must be version 1.66.0")
    updated = updated.replace(
        '"Version 1.65.0" in readme and "Version 1.64.0" in readme',
        '"Version 1.66.0" in readme and "Version 1.65.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.66.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Gradle artifact version to 1.66.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.66.0 — Kristallatem abfangen und Sicherheitsreserve richtig markieren

- **Taktische Boss-Abwehr:** Ein geladener Resonanzdämpfer, der direkt an der Atembahn steht, kann den Kristallatem des Kolosses einmalig abfangen. Die Anlage verbraucht genau eine ihrer drei Ladungen.
- **Echte Anlagen-Integration:** Beim Abfangen werden die Ladungsstufe, Comparator-Ausgabe und nahen Containment-Relais sofort aktualisiert. Partikel, Klang und eine DE/EN-Meldung bestätigen den Schutz.
- **Endliche Gegenmaßnahme:** Ein leerer Dämpfer blockt nichts. Der Scan ist auf die Atemstrecke begrenzt und liest keine ungeladenen Chunks.
- **Korrigierte Sicherheitssignale:** Modus 6 färbt niedrige Sicherheitsreserven rot, mittlere gelb und hohe grün; die Gefahr-Modi behalten ihre bisherige Farbskala.
- **Regressionen:** Neue Tests prüfen das Abfangen, den echten Ladungsverbrauch, Relay-Refresh, Chunk-Sicherheit, Übersetzungen und die inverse Farblogik.

"""
if "## Version 1.66.0 — Kristallatem abfangen und Sicherheitsreserve richtig markieren" not in readme:
    marker = "## Version 1.65.0 — Überladener Kristallkern und Containment-Sicherheitspuffer"
    idx = readme.find(marker)
    require(idx >= 0, "could not find prior 1.65.0 release notes")
    readme = readme[:idx] + release + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.66.0 — Kristallatem-Abwehr und korrekte Sicherheitsreserve.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus = [line for line in readme.splitlines() if line.startswith("## Aktueller Entwicklungsschritt — ")]
if focus:
    readme = readme.replace(focus[0], "## Aktueller Entwicklungsschritt — 1.66.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.66.0 dampener interception and containment-margin colors generated.")
