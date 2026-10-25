#!/usr/bin/env python3
"""Connect Mutagen Bloom exposure, finite Resonance Dampener charge and live relay diagnostics (1.52.0)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Bloom/Dampener counterplay: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def add_import(path, anchor, import_line, label):
    source = path.read_text(encoding="utf-8")
    if import_line in source:
        return
    require(anchor in source, "could not locate import anchor for " + label)
    path.write_text(source.replace(anchor, anchor + "\n" + import_line, 1), encoding="utf-8")


# The enabled redstone Spore Ward is deliberately checked first by the existing bloom
# handler. Only when that free, powered protection is absent may finite dampener charge
# absorb one player-exposure pulse.
bloom_path = SRC / "infection/MutagenBloom.java"
for anchor, import_line, label in (
    ("import de.sporenwerk.registry.ModBlocks;", "import de.sporenwerk.block.MutagenResonanceDampenerBlock;", "dampener block"),
    ("import de.sporenwerk.registry.ModBlocks;", "import de.sporenwerk.block.MutagenContainmentRelayBlock;", "relay network"),
    ("import net.minecraft.advancements.Advancement;", "import net.minecraft.advancements.Advancement;", "Advancement"),
):
    if import_line == anchor:
        # Advancement is inserted below with a different import anchor when it is absent.
        continue
    add_import(bloom_path, anchor, import_line, label)
add_import(bloom_path, "import net.minecraft.server.level.ServerLevel;",
           "import net.minecraft.resources.ResourceLocation;", "research ResourceLocation")
add_import(bloom_path, "import net.minecraft.server.level.ServerLevel;",
           "import net.minecraft.server.level.ServerPlayer;", "research ServerPlayer")
add_import(bloom_path, "import net.minecraft.server.level.ServerLevel;",
           "import net.minecraft.sounds.SoundEvents;\nimport net.minecraft.sounds.SoundSource;", "dampener feedback sounds")

bloom = bloom_path.read_text(encoding="utf-8")
if "private static BlockPos nearestChargedDampener(" not in bloom:
    anchor = "    private static void exposeNearbyPlayers(ServerLevel level, BlockPos origin) {"
    helpers = """    /**
     * Find the nearest charged dampener whose actual protection volume contains the player.
     * The probe is bounded to the device range and skips unloaded chunks before reading state.
     */
    private static BlockPos nearestChargedDampener(ServerLevel level, BlockPos target) {
        int horizontalRadius = MutagenResonanceDampenerBlock.HORIZONTAL_RADIUS;
        int verticalRadius = MutagenResonanceDampenerBlock.VERTICAL_RADIUS;
        int bestDistance = Integer.MAX_VALUE;
        BlockPos nearest = null;

        for (int dx = -horizontalRadius; dx <= horizontalRadius; dx++) {
            for (int dz = -horizontalRadius; dz <= horizontalRadius; dz++) {
                int horizontalDistanceSquared = dx * dx + dz * dz;
                if (horizontalDistanceSquared > horizontalRadius * horizontalRadius) continue;
                for (int dy = -verticalRadius; dy <= verticalRadius; dy++) {
                    BlockPos candidate = target.offset(dx, dy, dz);
                    if (!level.hasChunkAt(candidate)) continue;
                    BlockState candidateState = level.getBlockState(candidate);
                    if (!candidateState.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                            || !candidateState.hasProperty(MutagenResonanceDampenerBlock.CHARGE)
                            || candidateState.getValue(MutagenResonanceDampenerBlock.CHARGE) <= 0) continue;

                    int distanceSquared = horizontalDistanceSquared + dy * dy;
                    if (distanceSquared < bestDistance) {
                        bestDistance = distanceSquared;
                        nearest = candidate.immutable();
                    }
                }
            }
        }
        return nearest;
    }

    /** Consume one finite pulse, refresh the relay network, and acknowledge the real interception. */
    private static boolean spendDampenerCharge(ServerLevel level, Player player) {
        BlockPos dampenerPos = nearestChargedDampener(level, player.blockPosition());
        if (dampenerPos == null) return false;

        BlockState state = level.getBlockState(dampenerPos);
        if (!state.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                || !state.hasProperty(MutagenResonanceDampenerBlock.CHARGE)) return false;
        int charge = state.getValue(MutagenResonanceDampenerBlock.CHARGE);
        if (charge <= 0) return false;

        level.setBlock(dampenerPos,
                state.setValue(MutagenResonanceDampenerBlock.CHARGE, charge - 1), 3);
        MutagenContainmentRelayBlock.refreshNearbyRelays(level, dampenerPos);
        level.sendParticles(ParticleTypes.END_ROD,
                dampenerPos.getX() + 0.5D, dampenerPos.getY() + 0.8D, dampenerPos.getZ() + 0.5D,
                14, 0.24D, 0.28D, 0.24D, 0.025D);
        level.sendParticles(ParticleTypes.CRIT,
                dampenerPos.getX() + 0.5D, dampenerPos.getY() + 0.65D, dampenerPos.getZ() + 0.5D,
                6, 0.18D, 0.2D, 0.18D, 0.025D);
        level.playSound(null, dampenerPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                SoundSource.BLOCKS, 0.8F, 1.45F);
        player.displayClientMessage(
                Component.translatable("message.sporenwerk.mutagen.bloom_dampened")
                        .withStyle(ChatFormatting.AQUA), false);
        awardBloomDampenerResearch(player);
        return true;
    }

    private static void awardBloomDampenerResearch(Player player) {
        if (!(player instanceof ServerPlayer serverPlayer)) return;
        var server = serverPlayer.getServer();
        Advancement research = server == null ? null : server.getAdvancements().getAdvancement(
                new ResourceLocation("sporenwerk", "fieldwork/bloom_dampened"));
        if (research != null) {
            serverPlayer.getAdvancements().award(research, "bloom_dampened");
        }
    }

"""
    require(anchor in bloom, "could not locate the Bloom player exposure handler")
    bloom = bloom.replace(anchor, helpers + anchor, 1)

# The ward's existing branch ends with continue, so charged devices are consulted only if
# the powered ward did not intercept the event. Insert before the unchanged mask/infection path.
dampener_hook = """            if (spendDampenerCharge(level, player)) {
                continue;
            }

"""
mask_anchor = "            ItemStack mask = player.getItemBySlot(EquipmentSlot.HEAD);"
if dampener_hook not in bloom:
    require(mask_anchor in bloom, "could not locate the original Bloom mask/exposure branch")
    bloom = bloom.replace(mask_anchor, dampener_hook + mask_anchor, 1)
require("private static BlockPos nearestChargedDampener(" in bloom
        and "MutagenContainmentRelayBlock.refreshNearbyRelays(level, dampenerPos);" in bloom
        and "if (spendDampenerCharge(level, player))" in bloom,
        "dampener protection and relay feedback were not fully applied")
bloom_path.write_text(bloom, encoding="utf-8")

# One-time research acknowledges a real charge-consuming save, not merely placing a device.
advancement = {
    "parent": "sporenwerk:first_mutagen_bloom",
    "display": {
        "icon": {"item": "sporenwerk:mutagen_resonanzdaempfer"},
        "title": {"translate": "advancements.sporenwerk.bloom_dampened.title"},
        "description": {"translate": "advancements.sporenwerk.bloom_dampened.description"},
        "frame": "goal",
        "show_toast": True,
        "announce_to_chat": False,
        "hidden": False
    },
    "criteria": {"bloom_dampened": {"trigger": "minecraft:impossible"}},
    "requirements": [["bloom_dampened"]],
    "rewards": {"loot": ["sporenwerk:quests/bloom_dampened"]}
}
adv_path = RES / "data/sporenwerk/advancements/fieldwork/bloom_dampened.json"
adv_path.parent.mkdir(parents=True, exist_ok=True)
adv_path.write_text(json.dumps(advancement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

loot = {
    "type": "minecraft:generic",
    "pools": [
        {"rolls": 1.0, "entries": [{
            "type": "minecraft:item", "name": "sporenwerk:feldwissen",
            "functions": [{"function": "minecraft:set_count", "count": 2}]
        }]},
        {"rolls": 1.0, "entries": [{
            "type": "minecraft:item", "name": "sporenwerk:mutagene_sporen"
        }]}
    ]
}
loot_path = RES / "data/sporenwerk/loot_tables/quests/bloom_dampened.json"
loot_path.parent.mkdir(parents=True, exist_ok=True)
loot_path.write_text(json.dumps(loot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for filename, entries in {
    "de_de.json": {
        "message.sporenwerk.mutagen.bloom_dampened": "Resonanzdämpfer aktiv: Blütenimpuls abgefangen; eine Ladung verbraucht.",
        "advancements.sporenwerk.bloom_dampened.title": "Stiller Ausbruch",
        "advancements.sporenwerk.bloom_dampened.description": "Fange mit einem geladenen Resonanzdämpfer den Expositionsimpuls einer Mutagenblüte ab."
    },
    "en_us.json": {
        "message.sporenwerk.mutagen.bloom_dampened": "Resonance Dampener active: bloom pulse intercepted; one charge consumed.",
        "advancements.sporenwerk.bloom_dampened.title": "Silent Bloom",
        "advancements.sporenwerk.bloom_dampened.description": "Use a charged Resonance Dampener to intercept a Mutagen Bloom exposure pulse."
    }
}.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(
    r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
    "version = '1.52.0'",
    build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set Forge artifact version to 1.52.0")
build_path.write_text(build, encoding="utf-8")

# Refresh only active-version contracts; historical release notes remain intact.
updated_tests = 0
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.51.0",
                             "Aktueller Entwicklungsstand: 1.52.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.51\.0", r"1\.52\.0")
        updated = updated.replace("artifact must be version 1.51.0",
                                  "artifact must be version 1.52.0")
    updated = updated.replace(
        '"Version 1.51.0" in readme and "Version 1.50.0" in readme',
        '"Version 1.52.0" in readme and "Version 1.51.0" in readme')
    updated = updated.replace(
        "release notes must add 1.51.0 while preserving 1.50.0",
        "release notes must add 1.52.0 while preserving 1.51.0")
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")
        updated_tests += 1

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.52.0 — Mutagenblüte, Resonanzdämpfer und Containment-Netz

- **Dämpfer als zweite Schutzlinie:** Eine aktive Sporenabwehr fängt den Blütenimpuls weiterhin zuerst kostenlos ab. Fehlt sie, kann ein geladener Resonanzdämpfer den Expositionsimpuls eines Spielers in seiner echten Schutzreichweite abfangen.
- **Endliche Energie bleibt relevant:** Pro tatsächlich abgefangenem Spielerimpuls wird genau eine Dämpferladung verbraucht. Eine leere oder zu weit entfernte Anlage schützt nicht; Sporenfiltermaske und Mutationsanker bleiben als Gegenmaßnahmen erhalten.
- **Das Netzwerk reagiert sofort:** Beim Ladungsverbrauch wird das nahe Containment-Relaisnetz aktualisiert. Ein analoger Ausgang kann den geänderten Ladungsstand dadurch ohne Warteschleife an die Redstone-Anlage weitergeben.
- **Lesbares Feedback:** Partikel, Amethystklang, DE/EN-Meldung und der Vergleicherausgang zeigen die verbrauchte Ladung. Die vorhandene Dämpfer-Textur spiegelt weiter den tatsächlichen Ladungsstand wider.
- **Einmalige Feldforschung:** Der erste echte Blütenimpuls, den ein Dämpfer abfängt, schaltet „Stiller Ausbruch“ frei und vergibt eine kleine Forschungsbelohnung.
- **Chunk- und Leistungsgrenzen:** Die Suche nutzt nur den vorhandenen begrenzten Dämpferradius, überspringt ungeladene Chunks und läuft nur beim seltenen Blütenereignis; es kommt weder ein Block-Ticker noch ein Chunk-Ladevorgang hinzu.
- **Qualitätssicherung:** Regressionen prüfen Priorität der Sporenabwehr, Ladungsverbrauch, Relaisaktualisierung, Fortschritt, DE/EN-Texte, Forge-JAR und dedizierten Serverstart.

"""
if "## Version 1.52.0 — Mutagenblüte, Resonanzdämpfer und Containment-Netz" not in readme:
    marker = "## Version 1.51.0 — Resonanzparade und lebender Schutz"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.51.0 notes to preserve release history")
    readme = readme[:idx] + section + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.52.0 — Mutagenblüten-Abwehr über den geladenen Resonanzdämpfer.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines:
    readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.52.0", 1)
else:
    readme = readme.replace(headline, headline + "\n\n## Aktueller Schwerpunkt — 1.52.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print(f"1.52.0 Bloom-Dampener protection generated; refreshed {updated_tests} active-version regression contracts.")
