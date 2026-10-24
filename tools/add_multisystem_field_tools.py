#!/usr/bin/env python3
"""Add multi-system Mutagen field diagnostics, root medicine counterplay, and bloom feedback (1.45.0)."""
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
        raise SystemExit("Sporenwerk multi-system tools: " + message)


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


# 1) Expand the existing handheld scanner instead of adding yet another isolated tool.
scanner_path = SRC / "item/FeldscannerItem.java"
scanner = scanner_path.read_text(encoding="utf-8")
imports = [
    "import de.sporenwerk.block.InfestedTerrainBlock;",
    "import de.sporenwerk.block.MutagenContainmentRelayBlock;",
    "import de.sporenwerk.block.MutagenFieldControlStationBlock;",
    "import de.sporenwerk.block.MutagenResonanceDampenerBlock;",
    "import de.sporenwerk.block.MutagenWarningSirenBlock;",
    "import de.sporenwerk.block.SporeWardBlock;",
    "import de.sporenwerk.block.crop.AbstractSporeCropBlock;",
    "import de.sporenwerk.entity.KristallpirscherEntity;",
    "import net.minecraft.world.InteractionHand;",
    "import net.minecraft.world.InteractionResultHolder;",
    "import net.minecraft.world.phys.AABB;",
]
for import_line in imports:
    add_import(scanner_path, "import de.sporenwerk.registry.ModBlocks;", import_line, import_line)
scanner = scanner_path.read_text(encoding="utf-8")

area_methods = """\
    private static final int AREA_SCAN_RADIUS = 8;
    private static final int AREA_SCAN_VERTICAL_RADIUS = 4;

    private record AreaSurvey(int tierOneSoil, int tierTwoSoil, int tierThreeSoil,
                              int mutatedCrops, int poweredWards, int dampenerCount,
                              int availableChargeUnits, int activeAlarms, int criticalAlarms,
                              int activeRelays, int maxRelaySignal, int maxStationSignal,
                              int nearbyPirscher) {}

    /**
     * Right-clicking air performs one bounded, server-authoritative survey. It inspects
     * only loaded chunks and never runs from a ticker or requests chunk loading.
     */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(level instanceof ServerLevel serverLevel)) return InteractionResultHolder.pass(stack);

        AreaSurvey survey = surveyArea(serverLevel, player.blockPosition(), player);
        reportAreaSurvey(player, survey);
        return InteractionResultHolder.success(stack);
    }

    private static AreaSurvey surveyArea(ServerLevel level, BlockPos origin, Player player) {
        int tierOneSoil = 0;
        int tierTwoSoil = 0;
        int tierThreeSoil = 0;
        int mutatedCrops = 0;
        int poweredWards = 0;
        int dampenerCount = 0;
        int availableChargeUnits = 0;
        int activeAlarms = 0;
        int criticalAlarms = 0;
        int activeRelays = 0;
        int maxRelaySignal = 0;
        int maxStationSignal = 0;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

        int minY = Math.max(level.getMinBuildHeight(), origin.getY() - AREA_SCAN_VERTICAL_RADIUS);
        int maxY = Math.min(level.getMaxBuildHeight() - 1, origin.getY() + AREA_SCAN_VERTICAL_RADIUS);
        for (int dx = -AREA_SCAN_RADIUS; dx <= AREA_SCAN_RADIUS; dx++) {
            for (int dz = -AREA_SCAN_RADIUS; dz <= AREA_SCAN_RADIUS; dz++) {
                cursor.set(origin.getX() + dx, origin.getY(), origin.getZ() + dz);
                if (!level.hasChunkAt(cursor)) continue;
                for (int y = minY; y <= maxY; y++) {
                    cursor.set(origin.getX() + dx, y, origin.getZ() + dz);
                    BlockState state = level.getBlockState(cursor);

                    if (state.is(ModBlocks.MUTAGEN_BODEN.get())
                            && state.hasProperty(InfestedTerrainBlock.MUTAGEN_LEVEL)) {
                        int tier = state.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL);
                        if (tier == 1) tierOneSoil++;
                        else if (tier == 2) tierTwoSoil++;
                        else if (tier >= 3) tierThreeSoil++;
                    }
                    if (state.getBlock() instanceof AbstractSporeCropBlock
                            && state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)
                            && state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) > 0) {
                        mutatedCrops++;
                    }
                    if (state.is(ModBlocks.SPORENABWEHR.get())
                            && state.hasProperty(SporeWardBlock.POWERED)
                            && state.getValue(SporeWardBlock.POWERED)) {
                        poweredWards++;
                    }
                    if (state.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                            && state.hasProperty(MutagenResonanceDampenerBlock.CHARGE)) {
                        dampenerCount++;
                        availableChargeUnits += state.getValue(MutagenResonanceDampenerBlock.CHARGE);
                    }
                    if (state.is(ModBlocks.MUTAGEN_WARNSIRENE.get())
                            && state.hasProperty(MutagenWarningSirenBlock.SIGNAL)) {
                        int signal = state.getValue(MutagenWarningSirenBlock.SIGNAL);
                        if (signal > 0) activeAlarms++;
                        if (signal >= 11) criticalAlarms++;
                    }
                    if (state.is(ModBlocks.MUTAGEN_CONTAINMENT_RELAY.get())
                            && state.hasProperty(MutagenContainmentRelayBlock.SIGNAL)) {
                        int signal = state.getValue(MutagenContainmentRelayBlock.SIGNAL);
                        if (signal > 0) activeRelays++;
                        maxRelaySignal = Math.max(maxRelaySignal, signal);
                    }
                    if (state.is(ModBlocks.MUTAGENFELD_KONTROLLSTATION.get())
                            && state.hasProperty(MutagenFieldControlStationBlock.POWER)) {
                        maxStationSignal = Math.max(maxStationSignal,
                                state.getValue(MutagenFieldControlStationBlock.POWER));
                    }
                }
            }
        }

        int nearbyPirscher = level.getEntitiesOfClass(KristallpirscherEntity.class,
                new AABB(origin).inflate(AREA_SCAN_RADIUS, AREA_SCAN_VERTICAL_RADIUS, AREA_SCAN_RADIUS)).size();
        return new AreaSurvey(tierOneSoil, tierTwoSoil, tierThreeSoil, mutatedCrops,
                poweredWards, dampenerCount, availableChargeUnits, activeAlarms, criticalAlarms,
                activeRelays, maxRelaySignal, maxStationSignal, nearbyPirscher);
    }

    private static void reportAreaSurvey(Player player, AreaSurvey survey) {
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.scanner.survey.header", AREA_SCAN_RADIUS, AREA_SCAN_VERTICAL_RADIUS)
                .withStyle(ChatFormatting.AQUA), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey.fields",
                survey.tierOneSoil(), survey.tierTwoSoil(), survey.tierThreeSoil())
                .withStyle(survey.tierThreeSoil() > 0 ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.GREEN), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey.crops",
                survey.mutatedCrops()).withStyle(ChatFormatting.GOLD), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey.devices",
                survey.poweredWards(), survey.dampenerCount(), survey.availableChargeUnits(),
                survey.activeAlarms(), survey.criticalAlarms(), survey.activeRelays(),
                survey.maxRelaySignal(), survey.maxStationSignal())
                .withStyle(survey.criticalAlarms() > 0 ? ChatFormatting.RED : ChatFormatting.GRAY), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey.threats",
                survey.nearbyPirscher())
                .withStyle(survey.nearbyPirscher() > 0 ? ChatFormatting.RED : ChatFormatting.GRAY), false);
        player.displayClientMessage(Component.translatable("message.sporenwerk.scanner.survey.loaded")
                .withStyle(ChatFormatting.DARK_GRAY), false);

        String guidanceKey;
        ChatFormatting guidanceColor;
        if (survey.nearbyPirscher() > 0) {
            guidanceKey = "message.sporenwerk.scanner.survey.guidance.pirscher";
            guidanceColor = ChatFormatting.RED;
        } else if (survey.criticalAlarms() > 0
                || (survey.tierThreeSoil() > 0
                && (survey.poweredWards() == 0 || survey.availableChargeUnits() == 0))) {
            guidanceKey = "message.sporenwerk.scanner.survey.guidance.critical";
            guidanceColor = ChatFormatting.RED;
        } else if (survey.activeAlarms() > 0 || survey.tierTwoSoil() > 0) {
            guidanceKey = "message.sporenwerk.scanner.survey.guidance.elevated";
            guidanceColor = ChatFormatting.GOLD;
        } else if (survey.tierOneSoil() > 0 || survey.mutatedCrops() > 0
                || survey.poweredWards() > 0 || survey.dampenerCount() > 0) {
            guidanceKey = "message.sporenwerk.scanner.survey.guidance.active";
            guidanceColor = ChatFormatting.YELLOW;
        } else {
            guidanceKey = "message.sporenwerk.scanner.survey.guidance.clear";
            guidanceColor = ChatFormatting.GREEN;
        }
        player.displayClientMessage(Component.translatable(guidanceKey).withStyle(guidanceColor), false);
    }

"""
use_on_anchor = "    @Override\n    public InteractionResult useOn(UseOnContext context) {"
if "private record AreaSurvey(" not in scanner:
    require(use_on_anchor in scanner, "could not locate Feldscanner useOn method for area survey")
    scanner = scanner.replace(use_on_anchor, area_methods + use_on_anchor, 1)

# Add precise readings for existing containment hardware and crop phenotype states.
barrier_branch = """        } else if (state.is(ModBlocks.SPORENRESISTENTER_BLOCK.get())) {
            reading = Component.translatable("message.sporenwerk.scanner.barrier")
                    .withStyle(ChatFormatting.GREEN);
"""
hardware_branches = """        } else if (state.is(ModBlocks.SPORENABWEHR.get())
                && state.hasProperty(SporeWardBlock.POWERED)) {
            reading = Component.translatable("message.sporenwerk.scanner.device.ward",
                    Component.translatable(state.getValue(SporeWardBlock.POWERED)
                            ? "message.sporenwerk.scanner.state_on"
                            : "message.sporenwerk.scanner.state_off"))
                    .withStyle(state.getValue(SporeWardBlock.POWERED) ? ChatFormatting.GREEN : ChatFormatting.GRAY);
        } else if (state.is(ModBlocks.MUTAGEN_RESONANZDAEMPFER.get())
                && state.hasProperty(MutagenResonanceDampenerBlock.CHARGE)) {
            reading = Component.translatable("message.sporenwerk.scanner.device.dampener",
                    state.getValue(MutagenResonanceDampenerBlock.CHARGE))
                    .withStyle(state.getValue(MutagenResonanceDampenerBlock.CHARGE) > 0
                            ? ChatFormatting.AQUA : ChatFormatting.RED);
        } else if (state.is(ModBlocks.MUTAGEN_WARNSIRENE.get())
                && state.hasProperty(MutagenWarningSirenBlock.SIGNAL)) {
            int signal = state.getValue(MutagenWarningSirenBlock.SIGNAL);
            reading = Component.translatable("message.sporenwerk.scanner.device.siren", signal)
                    .withStyle(signal >= 11 ? ChatFormatting.RED : signal > 0 ? ChatFormatting.GOLD : ChatFormatting.GRAY);
        } else if (state.is(ModBlocks.MUTAGEN_CONTAINMENT_RELAY.get())
                && state.hasProperty(MutagenContainmentRelayBlock.SIGNAL)) {
            reading = Component.translatable("message.sporenwerk.scanner.device.relay",
                    state.getValue(MutagenContainmentRelayBlock.MODE),
                    state.getValue(MutagenContainmentRelayBlock.SIGNAL))
                    .withStyle(state.getValue(MutagenContainmentRelayBlock.SIGNAL) >= 11
                            ? ChatFormatting.RED : ChatFormatting.AQUA);
        } else if (state.is(ModBlocks.MUTAGENFELD_KONTROLLSTATION.get())
                && state.hasProperty(MutagenFieldControlStationBlock.POWER)) {
            int signal = state.getValue(MutagenFieldControlStationBlock.POWER);
            reading = Component.translatable("message.sporenwerk.scanner.device.station", signal)
                    .withStyle(signal >= 11 ? ChatFormatting.RED : signal > 0 ? ChatFormatting.GOLD : ChatFormatting.GRAY);
        } else if (state.getBlock() instanceof AbstractSporeCropBlock
                && state.hasProperty(AbstractSporeCropBlock.MUTAGEN_LEVEL)) {
            reading = Component.translatable("message.sporenwerk.scanner.crop_phenotype",
                    state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL))
                    .withStyle(state.getValue(AbstractSporeCropBlock.MUTAGEN_LEVEL) >= 3
                            ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.GREEN);
"""
if "message.sporenwerk.scanner.device.ward" not in scanner:
    require(barrier_branch in scanner, "could not locate scanner barrier branch")
    scanner = scanner.replace(barrier_branch, barrier_branch + hardware_branches, 1)

tooltip_anchor = """        tooltip.add(Component.translatable("tooltip.sporenwerk.feldscanner.2")
                .withStyle(ChatFormatting.GRAY));
"""
tooltip_addition = """        tooltip.add(Component.translatable("tooltip.sporenwerk.feldscanner.3")
                .withStyle(ChatFormatting.GRAY));
"""
if tooltip_addition.strip() not in scanner:
    require(tooltip_anchor in scanner, "could not locate scanner tooltip")
    scanner = scanner.replace(tooltip_anchor, tooltip_anchor + tooltip_addition, 1)
scanner_path.write_text(scanner, encoding="utf-8")


# 2) Rotwurzel concentrate becomes a direct answer to poison and resonance slowdown.
medicine_path = SRC / "item/WurzelkonzentratItem.java"
medicine = medicine_path.read_text(encoding="utf-8")
add_import(medicine_path, "import net.minecraft.world.item.Item;", 
           "import net.minecraft.world.effect.MobEffects;", "root concentrate effects import")
medicine = medicine_path.read_text(encoding="utf-8")
old_heal = "        player.heal(4.0F);"
new_heal = """        boolean curedPoison = player.removeEffect(MobEffects.POISON);
        boolean curedSlowdown = player.removeEffect(MobEffects.MOVEMENT_SLOWDOWN);
        player.heal(4.0F);"""
if "boolean curedPoison = player.removeEffect(MobEffects.POISON);" not in medicine:
    require(old_heal in medicine, "could not locate Rotwurzel healing action")
    medicine = medicine.replace(old_heal, new_heal, 1)
old_message = """        serverPlayer.displayClientMessage(Component.literal("Rotwurzel-Konzentrat: 2 Herzen regeneriert.")
                .withStyle(ChatFormatting.RED), true);"""
new_message = """        String feedbackKey = curedPoison && curedSlowdown
                ? "message.sporenwerk.wurzelkonzentrat.cured_both"
                : curedPoison ? "message.sporenwerk.wurzelkonzentrat.cured_poison"
                : curedSlowdown ? "message.sporenwerk.wurzelkonzentrat.cured_slowdown"
                : "message.sporenwerk.wurzelkonzentrat.healed";
        serverPlayer.displayClientMessage(Component.translatable(feedbackKey)
                .withStyle(ChatFormatting.RED), true);"""
if "message.sporenwerk.wurzelkonzentrat.cured_both" not in medicine:
    require(old_message in medicine, "could not locate Rotwurzel use feedback")
    medicine = medicine.replace(old_message, new_message, 1)
medicine_path.write_text(medicine, encoding="utf-8")


# 3) A Mutagen Bloom keeps its existing bounded particles/reward/cooldown but adds a clear
# audible confirmation to make the risky event easier to notice while exploring.
bloom_path = SRC / "infection/MutagenBloom.java"
add_import(bloom_path, "import net.minecraft.world.phys.AABB;",
           "import net.minecraft.sounds.SoundEvents;\nimport net.minecraft.sounds.SoundSource;",
           "Mutagen Bloom sound imports")
bloom = bloom_path.read_text(encoding="utf-8")
bloom_anchor = """        double x = origin.getX() + 0.5D;
        double y = origin.getY() + 0.9D;
        double z = origin.getZ() + 0.5D;
        level.sendParticles(ParticleTypes.WARPED_SPORE, x, y, z, 48, 1.3D, 0.45D, 1.3D, 0.035D);"""
bloom_new = """        double x = origin.getX() + 0.5D;
        double y = origin.getY() + 0.9D;
        double z = origin.getZ() + 0.5D;
        level.playSound(null, origin, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.1F, 0.55F);
        level.sendParticles(ParticleTypes.WARPED_SPORE, x, y, z, 48, 1.3D, 0.45D, 1.3D, 0.035D);"""
if "SoundEvents.AMETHYST_BLOCK_CHIME" not in bloom:
    require(bloom_anchor in bloom, "could not locate Mutagen Bloom visual event")
    bloom = bloom.replace(bloom_anchor, bloom_new, 1)
bloom_path.write_text(bloom, encoding="utf-8")


# Localize every new diagnostic/action message and keep the existing tooltip truthful.
translations = {
    "de_de.json": {
        "tooltip.sporenwerk.feldscanner.3": "Rechtsklick in die Luft: Umgebungsscan; Rechtsklick auf einen Block: Einzelmessung.",
        "message.sporenwerk.scanner.state_on": "AKTIV",
        "message.sporenwerk.scanner.state_off": "INAKTIV",
        "message.sporenwerk.scanner.crop_phenotype": "Mutagen-Phänotyp dieser Pflanze: Stufe %1$s/3.",
        "message.sporenwerk.scanner.device.ward": "Sporenabwehrsender: %1$s.",
        "message.sporenwerk.scanner.device.dampener": "Resonanzdämpfer: gespeicherte Gegenimpulse %1$s.",
        "message.sporenwerk.scanner.device.siren": "Warnsirene: gespeicherter Alarmwert %1$s/15.",
        "message.sporenwerk.scanner.device.relay": "Containment-Relais: Modus %1$s, gespeichertes Comparator-Signal %2$s/15.",
        "message.sporenwerk.scanner.device.station": "Kontrollstation: zuletzt gespeicherter Gefahrenwert %1$s/15.",
        "message.sporenwerk.scanner.survey.header": "UMGEBUNGSSCAN: Radius %1$s Blöcke, Höhe ±%2$s. Nur geladene Chunks.",
        "message.sporenwerk.scanner.survey.fields": "Mutagenboden nach Stufe — I: %1$s | II: %2$s | III: %3$s",
        "message.sporenwerk.scanner.survey.crops": "Mutierte Sporenwerk-Pflanzen im Messbereich: %1$s",
        "message.sporenwerk.scanner.survey.devices": "Aktive Abwehrsender: %1$s | Dämpfer: %2$s (Impulse: %3$s) | Sirenen: %4$s (kritisch: %5$s) | aktive Relais: %6$s (max. Signal: %7$s) | höchstes Stationssignal: %8$s",
        "message.sporenwerk.scanner.survey.threats": "Kristallpirscher im Nahbereich: %1$s",
        "message.sporenwerk.scanner.survey.loaded": "Begrenzter Einmalscan. Geräteanzahl beweist keine vollständige Schutzabdeckung.",
        "message.sporenwerk.scanner.survey.guidance.pirscher": "GEFAHR: Kristallpirscher erkannt. Deckung suchen und Resonanzschutz prüfen.",
        "message.sporenwerk.scanner.survey.guidance.critical": "KRITISCH: Alarm oder Stufe-III-Feld mit unzureichend erkannter Reserve. Schutzbereiche direkt prüfen.",
        "message.sporenwerk.scanner.survey.guidance.elevated": "ERHÖHT: Alarm oder Mutagen-Stufe II gefunden. Feldgrenzen und Atemschutz kontrollieren.",
        "message.sporenwerk.scanner.survey.guidance.active": "AKTIV: Mutagenboden, mutierte Pflanzen oder Schutzgeräte erkannt. Messung bei Änderungen wiederholen.",
        "message.sporenwerk.scanner.survey.guidance.clear": "KEIN AKTIVES SIGNAL im Messbereich erkannt. Der Scan erfasst nur geladene Chunks.",
        "message.sporenwerk.wurzelkonzentrat.cured_both": "Rotwurzel-Konzentrat: 2 Herzen geheilt, Gift und Resonanzverlangsamung entfernt.",
        "message.sporenwerk.wurzelkonzentrat.cured_poison": "Rotwurzel-Konzentrat: 2 Herzen geheilt, Gift entfernt.",
        "message.sporenwerk.wurzelkonzentrat.cured_slowdown": "Rotwurzel-Konzentrat: 2 Herzen geheilt, Resonanzverlangsamung entfernt.",
        "message.sporenwerk.wurzelkonzentrat.healed": "Rotwurzel-Konzentrat: 2 Herzen geheilt.",
        "tooltip.sporenwerk.wurzelkonzentrat.heal": "Stellt 2 Herzen wieder her und entfernt Gift oder Resonanzverlangsamung.",
    },
    "en_us.json": {
        "tooltip.sporenwerk.feldscanner.3": "Right-click air: area survey; right-click a block: inspect that block.",
        "message.sporenwerk.scanner.state_on": "POWERED",
        "message.sporenwerk.scanner.state_off": "UNPOWERED",
        "message.sporenwerk.scanner.crop_phenotype": "Stored mutagen phenotype tier for this crop: %1$s/3.",
        "message.sporenwerk.scanner.device.ward": "Spore Ward emitter: %1$s.",
        "message.sporenwerk.scanner.device.dampener": "Resonance Dampener: stored counterpulses %1$s.",
        "message.sporenwerk.scanner.device.siren": "Warning siren: stored alarm signal %1$s/15.",
        "message.sporenwerk.scanner.device.relay": "Containment Relay: mode %1$s, stored comparator signal %2$s/15.",
        "message.sporenwerk.scanner.device.station": "Control Station: most recently stored hazard value %1$s/15.",
        "message.sporenwerk.scanner.survey.header": "AREA SURVEY: radius %1$s blocks, height ±%2$s. Loaded chunks only.",
        "message.sporenwerk.scanner.survey.fields": "Mutagen soil by tier — I: %1$s | II: %2$s | III: %3$s",
        "message.sporenwerk.scanner.survey.crops": "Mutated Sporenwerk crops in survey area: %1$s",
        "message.sporenwerk.scanner.survey.devices": "Powered wards: %1$s | dampeners: %2$s (charges: %3$s) | sirens: %4$s (critical: %5$s) | active relays: %6$s (max signal: %7$s) | highest station signal: %8$s",
        "message.sporenwerk.scanner.survey.threats": "Kristallpirscher nearby: %1$s",
        "message.sporenwerk.scanner.survey.loaded": "Bounded one-shot scan. Device counts do not prove full protection coverage.",
        "message.sporenwerk.scanner.survey.guidance.pirscher": "DANGER: Kristallpirscher detected. Find cover and verify resonance protection.",
        "message.sporenwerk.scanner.survey.guidance.critical": "CRITICAL: An alarm or tier-III field with insufficient detected reserve. Verify overlapping protection directly.",
        "message.sporenwerk.scanner.survey.guidance.elevated": "ELEVATED: An alarm or tier-II Mutagen field was detected. Check field edges and respiratory protection.",
        "message.sporenwerk.scanner.survey.guidance.active": "ACTIVE: Mutagen soil, mutated crops, or containment devices detected. Repeat the scan after changes.",
        "message.sporenwerk.scanner.survey.guidance.clear": "NO ACTIVE SIGNAL detected in the survey area. Only loaded chunks are inspected.",
        "message.sporenwerk.wurzelkonzentrat.cured_both": "Redroot Concentrate: healed 2 hearts and removed poison and resonance slowdown.",
        "message.sporenwerk.wurzelkonzentrat.cured_poison": "Redroot Concentrate: healed 2 hearts and removed poison.",
        "message.sporenwerk.wurzelkonzentrat.cured_slowdown": "Redroot Concentrate: healed 2 hearts and removed resonance slowdown.",
        "message.sporenwerk.wurzelkonzentrat.healed": "Redroot Concentrate: healed 2 hearts.",
        "tooltip.sporenwerk.wurzelkonzentrat.heal": "Restores 2 hearts and removes poison or resonance slowdown.",
    },
}
for locale, entries in translations.items():
    locale_path = ASSETS / "lang" / locale
    data = json.loads(locale_path.read_text(encoding="utf-8"))
    data.update(entries)
    locale_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# Bump active-version assertions while preserving historical release-note assertions.
for test_path in (ROOT / "tools").glob("test_*.py"):
    lines = test_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "Aktueller Entwicklungsstand: 1.44.0" in line:
            lines[index] = line.replace("Aktueller Entwicklungsstand: 1.44.0",
                                        "Aktueller Entwicklungsstand: 1.45.0")
            line = lines[index]
            changed = True
        if r"1\.44\.0" not in line or "version" not in line.lower():
            continue
        newer = line.replace(r"1\.44\.0", r"1\.45\.0")
        if newer != line:
            lines[index] = newer
            changed = True
        for following in range(index, min(index + 3, len(lines))):
            if "must be version 1.44.0" in lines[following] or "version must be 1.44.0" in lines[following]:
                lines[following] = lines[following].replace("1.44.0", "1.45.0")
                changed = True
    if changed:
        test_path.write_text("".join(lines), encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.45.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.45.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """## Version 1.45.0 — Multi-System-Feldanalyse, Gegenmittel und Ereignisfeedback

- **Feldscanner als Diagnosewerkzeug:** Rechtsklick auf Luft führt einen einmaligen Scan mit Radius 8 und Höhe ±4 aus. Er zählt Mutagenboden der Stufen I–III, mutierte Sporenwerk-Pflanzen, aktivierte Sporenabwehrsender, Resonanzdämpfer samt gespeicherten Ladungen, Sirenenalarme und Containment-Relais. In der Umgebung erkannte Kristallpirscher werden ebenfalls gemeldet.
- **Direkte Hardwaremessung:** Beim Rechtsklick auf Ward, Dämpfer, Sirene, Relais oder Kontrollstation zeigt der Scanner gespeicherte Zustände und Signalwerte statt bloß eine generische Feldmeldung.
- **Handlungsorientierte Rückmeldung:** Die Bereichsanalyse ordnet den Befund grob ein und nennt erkannte kritische Alarme, Stufe-III-Felder ohne ausreichend erkannte Schutzreserve oder nahe Kristallpirscher. Sie behauptet ausdrücklich nicht, dass bloß gezählte Geräte jedes Feld tatsächlich abdecken.
- **Sicherer Scan:** Der Scan läuft nur serverseitig, nur bei Spieleraktion, überspringt ungeladene Chunks und verwendet einen festen 17×9×17-Blockbereich. Kein Tick-Polling und kein erzwungenes Laden von Chunks.
- **Rotwurzel-Konzentrat:** Neben der Heilung von zwei Herzen entfernt das Konzentrat jetzt Gift und/oder Resonanzverlangsamung. Die Rückmeldung unterscheidet, welcher Effekt tatsächlich geheilt wurde; Rezept und Abklingzeit bleiben erhalten.
- **Mutagenblüte hörbar:** Eine Amethyst-Glocke ergänzt die bestehenden Partikel, Belohnungen und Abklingzeit als klares akustisches Ereignissignal. Bloom-Belohnungen und Expositionsregeln werden nicht geändert.
- **Qualitätssicherung:** Neue Regressionen prüfen Gebietslimits, Chunk-Sicherheit, Hardwaremessungen, DE/EN-Texte, Heilmittel-Gegenwehr, Bloom-Sound, Releaseversion, Forge-Build, installierbare JAR und dedizierten Serverstart.

"""
if "## Version 1.45.0 — Multi-System-Feldanalyse, Gegenmittel und Ereignisfeedback" not in readme:
    marker = "## Version 1.44.0"
    index = readme.find(marker)
    require(index >= 0, "could not locate the 1.44.0 release notes")
    readme = readme[:index] + section + readme[index:]
headline = "**Aktueller Entwicklungsstand: 1.45.0 — Multi-System-Feldanalyse, Rotwurzel-Gegenmittel und Mutagenblüten-Signal.**"
headline_lines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headline_lines:
    readme = readme.replace(headline_lines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines:
    readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.45.0", 1)
else:
    readme = readme.replace(headline, headline + "\n\n## Aktueller Schwerpunkt — 1.45.0", 1)
readme_path.write_text(readme, encoding="utf-8")

print("Sporenwerk 1.45.0 generated: multi-system field scan, localized cure feedback, and Mutagen Bloom audio cue.")
