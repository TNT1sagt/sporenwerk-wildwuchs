#!/usr/bin/env python3
"""Let a powered Spore Ward intercept the exposure pulse of a Mutagen Bloom (1.40.0)."""
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
        raise SystemExit("Mutagen Bloom / Spore Ward synergy: " + message)


# Use the ward's real gameplay radius as the single source of truth.
ward_path = SRC / "block/SporeWardBlock.java"
ward = ward_path.read_text(encoding="utf-8")
for name, value in (("HORIZONTAL_RADIUS", 8), ("VERTICAL_RADIUS", 3)):
    private = f"private static final int {name} = {value};"
    public = f"public static final int {name} = {value};"
    if public not in ward:
        require(private in ward, f"could not locate Spore Ward {name} constant")
        ward = ward.replace(private, public, 1)
require("public static final BooleanProperty POWERED = BlockStateProperties.POWERED;" in ward,
        "powered state must remain explicit and server-synchronized")
ward_path.write_text(ward, encoding="utf-8")

bloom_path = SRC / "infection/MutagenBloom.java"
bloom = bloom_path.read_text(encoding="utf-8")
if "import de.sporenwerk.block.SporeWardBlock;" not in bloom:
    anchor = "import de.sporenwerk.registry.ModBlocks;"
    require(anchor in bloom, "could not locate MutagenBloom block imports")
    bloom = bloom.replace(anchor, "import de.sporenwerk.block.SporeWardBlock;\n" + anchor, 1)

# This bounded, loaded-chunk-only query is used only when a rare bloom event releases
# its exposure pulse. It never runs on the regular entity or world tick.
if "private static boolean isProtectedByPoweredWard(" not in bloom:
    anchor = "    private static void exposeNearbyPlayers(ServerLevel level, BlockPos origin) {"
    helper = """    /**
     * A powered Spore Ward intercepts bloom exposure within its normal protection volume.
     * The scan is bounded to one ward radius and never asks Minecraft to load a chunk.
     */
    private static boolean isProtectedByPoweredWard(ServerLevel level, BlockPos playerPos) {
        int radius = SporeWardBlock.HORIZONTAL_RADIUS;
        int radiusSquared = radius * radius;
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dz = -radius; dz <= radius; dz++) {
                if (dx * dx + dz * dz > radiusSquared) continue;
                for (int dy = -SporeWardBlock.VERTICAL_RADIUS;
                     dy <= SporeWardBlock.VERTICAL_RADIUS; dy++) {
                    BlockPos wardPos = playerPos.offset(dx, dy, dz);
                    if (!level.hasChunkAt(wardPos)) continue;
                    BlockState wardState = level.getBlockState(wardPos);
                    if (wardState.is(ModBlocks.SPORENABWEHR.get())
                            && wardState.hasProperty(SporeWardBlock.POWERED)
                            && wardState.getValue(SporeWardBlock.POWERED)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

"""
    require(anchor in bloom, "could not locate bloom exposure handler")
    bloom = bloom.replace(anchor, helper + anchor, 1)

# Inject the ward interception immediately after the discovery award. This anchor is
# intentionally smaller than the surrounding UI/mask block, which older patch revisions
# may format differently.
ward_interception = """            if (isProtectedByPoweredWard(level, player.blockPosition())) {
                player.displayClientMessage(
                        Component.translatable("message.sporenwerk.mutagen.bloom_warded")
                                .withStyle(ChatFormatting.AQUA), false);
                level.sendParticles(ParticleTypes.END_ROD,
                        player.getX(), player.getY() + 1.0D, player.getZ(),
                        8, 0.24D, 0.32D, 0.24D, 0.02D);
                continue;
            }

"""
if ward_interception not in bloom:
    award_anchor = "            awardBloomDiscovery(player);\n"
    require(award_anchor in bloom, "could not locate bloom discovery award")
    bloom = bloom.replace(award_anchor, award_anchor + ward_interception, 1)



# Keep the protection query constrained and the original mask/anchor systems intact.
for token in (
    "if (!level.hasChunkAt(wardPos)) continue;",
    "wardState.is(ModBlocks.SPORENABWEHR.get())",
    "wardState.getValue(SporeWardBlock.POWERED)",
    "isProtectedByPoweredWard(level, player.blockPosition())",
    "InfectionState.setLevel(player, InfectionState.level(player) + 1)",
    "MutationField.hasAnchor(level, player.blockPosition())",
    "awardBloomDiscovery(player)",
):
    require(token in bloom, "required interaction or safety guard missing: " + token)
bloom_path.write_text(bloom, encoding="utf-8")

# DE/EN feedback explains that the bloom was observed but its exposure was intercepted.
for filename, value in (
    ("de_de.json", "Sporenabwehr aktiv: Der Mutagenblüten-Ausbruch wurde abgefangen."),
    ("en_us.json", "Spore Ward active: the Mutagen Bloom exposure pulse was intercepted."),
):
    locale_path = ASSETS / "lang" / filename
    locale = json.loads(locale_path.read_text(encoding="utf-8"))
    locale["message.sporenwerk.mutagen.bloom_warded"] = value
    locale_path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Advance the generated mod and refresh only current-artifact assertions in earlier tests.
build_path = ROOT / "build.gradle"
build, count = re.subn(
    r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
    "version = '1.40.0'",
    build_path.read_text(encoding="utf-8"),
    count=1,
)
require(count == 1, "could not set Gradle artifact version to 1.40.0")
build_path.write_text(build, encoding="utf-8")

version_tests_updated = 0
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if r"1\.39\.0" not in line or "version" not in line.lower():
            continue
        updated_line = line.replace(r"1\.39\.0", r"1\.40\.0")
        if updated_line != line:
            lines[index] = updated_line
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.39.0" in lines[following] or "version must be 1.39.0" in lines[following]:
                lines[following] = lines[following].replace("1.39.0", "1.40.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")
        version_tests_updated += 1
require(version_tests_updated >= 1, "no existing current-version assertions were updated")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.40.0 — Mutagenblüte und Sporenabwehr im Zusammenspiel

- **Aktive Gegenmaßnahme:** Ein mit Redstone versorgter Sporenabwehrsender fängt den Expositionsimpuls einer Mutagenblüte innerhalb seiner tatsächlichen Schutzreichweite ab.
- **Klare Grenzen:** Die Abwehr verwendet dieselben 8 Blöcke horizontal und 3 vertikal wie der Dämmerling-Schutz. Die Abfrage läuft nur während des seltenen Blütenereignisses, ist räumlich begrenzt und überspringt nicht geladene Chunks.
- **Kein kostenloser Fortschrittsverlust:** Spieler können die erste Mutagenblüte weiterhin entdecken und die Forschungsbelohnung erhalten; der Sender verhindert die Infektion, nicht die Beobachtung.
- **Sichtbare Rückmeldung:** Geschützte Spieler erhalten eine eigene Meldung in Deutsch/Englisch und einen kurzen Partikeleffekt. Filtermaske, Mutationsanker, Erntebelohnung und Pflanzenwachstum bleiben erhalten.
- **Qualitätssicherung:** Regressionstests prüfen den tatsächlichen Powered-Zustand, den gemeinsamen Schutzradius, Chunk-Sicherheit, Meldungen, Fortschritt und die weiterhin aktive Gefahrenlogik.

"""
if "## Version 1.40.0 — Mutagenblüte und Sporenabwehr im Zusammenspiel" not in readme:
    marker = "## Version 1.39.0 — Resonanzrückkopplung gegen den Kristallpirscher"
    idx = readme.find(marker)
    require(idx >= 0, "could not find 1.39.0 release notes")
    readme = readme[:idx] + section + readme[idx:]

headline_lines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
require(len(headline_lines) >= 1, "could not locate the current development headline")
readme = readme.replace(
    headline_lines[0],
    "**Aktueller Entwicklungsstand: 1.40.0 — Mutagenblüten-Abwehr über den Redstone-Sporenabwehrsender.**",
    1,
)
readme, focus_count = re.subn(
    r"(?m)^## Aktueller Schwerpunkt — [0-9]+\.[0-9]+\.[0-9]+$",
    "## Aktueller Schwerpunkt — 1.40.0",
    readme,
    count=1,
)
require(focus_count == 1, "could not update the current focus heading")
readme_path.write_text(readme, encoding="utf-8")
print("1.40.0 powered Spore Ward / Mutagen Bloom synergy generated; legacy current-version checks updated.")
