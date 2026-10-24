#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
def read(path): return (root / path).read_text(encoding="utf-8")
def require(ok, message):
    if not ok: raise SystemExit("Mutagen bloom regression: " + message)

nodes = read("src/main/java/de/sporenwerk/infection/MutationNodeData.java")
for token in ("Map<Long, Long> lastBlooms", 'entry.contains("LastBloom")',
              "claimBloom(BlockPos pos, long gameTime, long cooldownTicks)",
              'value.putLong("LastBloom"', "lastBlooms.remove(pos.asLong())"):
    require(token in nodes, "persistent per-node cooldown is missing " + token)
bloom = read("src/main/java/de/sporenwerk/infection/MutagenBloom.java")
for token in ("mutagenStrengthAt(level, origin) < 3", "claimBloom(origin, level.getGameTime(), COOLDOWN_TICKS)",
              "COOLDOWN_TICKS = 12000L", "ParticleTypes.WARPED_SPORE", "ParticleTypes.PORTAL",
              "attempt < 32 && advanced < 6", "releaseHarvestableSpores(level, origin, random)",
              "new ItemStack(ModItems.MUTAGENE_SPOREN.get(), count)", "level.addFreshEntity(new ItemEntity(level, x, y, z, spores))",
              "int count = random.nextFloat() < 0.20F ? 2 : 1",
              "releaseHarvestableSpores(ServerLevel level, BlockPos origin, RandomSource random)",
              "releaseCondensedCore(level, origin, random)", "random.nextFloat() >= 0.12F",
              "new ItemStack(ModItems.MUTAGENKERNKRISTALL.get())",
              "releaseCondensedCore(ServerLevel level, BlockPos origin, RandomSource random)",
              "MutationField.hasAnchor(level, player.blockPosition())",
              "mask.is(ModItems.SPORENFILTERMASKE.get())", "mask.hurtAndBreak(1, player",
              "InfectionState.setLevel(player, InfectionState.level(player) + 1)",
              "SporenwerkControlledExposureAt", "accelerateCrops(level, origin, random)",
              "exposeNearbyPlayers(level, origin)", "awardBloomDiscovery(player)",
              'new ResourceLocation("sporenwerk", "first_mutagen_bloom")',
              'award(discovery, "witness_bloom")'):
    require(token in bloom, "bloom behavior is missing " + token)
node = read("src/main/java/de/sporenwerk/block/MutationNodeBlock.java")
require("MutagenBloom.tryTrigger(level, pos, random)" in node,
        "scheduled active-node tick must invoke the event")
items = read("src/main/java/de/sporenwerk/registry/ModItems.java")
creative = read("src/main/java/de/sporenwerk/registry/ModCreativeTabs.java")
require("MUTAGENKERNKRISTALL" in items and 'register("mutagenkernkristall"' in items
        and "MutagenCoreCrystalItem" in items,
        "rare bloom core must be registered as a dedicated item")
require("output.accept(ModItems.MUTAGENKERNKRISTALL.get())" in creative,
        "rare bloom core must be visible in the creative catalogue")
advancement = json.loads(read("src/main/resources/data/sporenwerk/advancements/first_mutagen_bloom.json"))
require(advancement["parent"] == "sporenwerk:mutagen_laboratory"
        and advancement["criteria"]["witness_bloom"]["trigger"] == "minecraft:impossible"
        and advancement["rewards"]["loot"] == ["sporenwerk:quests/first_mutagen_bloom"],
        "first bloom must award one persistent advancement and a field-research reward")
reward_table = json.loads(read("src/main/resources/data/sporenwerk/loot_tables/quests/first_mutagen_bloom.json"))
reward_items = {entry["name"]: entry["functions"][0]["count"]
                for entry in reward_table["pools"][0]["entries"]}
require(reward_items == {"sporenwerk:feldwissen": 3, "sporenwerk:myzelkompost": 2},
        "first bloom reward must remain bounded to 3 field knowledge and 2 mycelium compost")
for locale in ("de_de.json", "en_us.json"):
    data = json.loads((root / "src/main/resources/assets/sporenwerk/lang" / locale).read_text(encoding="utf-8"))
    require(data.get("message.sporenwerk.mutagen.bloom", "").strip(),
            locale + " missing the Mutagen Bloom warning")
    require(data.get("advancements.sporenwerk.first_mutagen_bloom.title", "").strip()
            and data.get("advancements.sporenwerk.first_mutagen_bloom.description", "").strip(),
            locale + " missing the first-bloom advancement texts")
require("Version 1.15.0" in read("README.md"), "release notes missing 1.15.0")
build = read("build.gradle")
version_match = re.search(r"version\s*=\s*['\"](\d+)\.(\d+)\.(\d+)['\"]", build)
require(version_match is not None and tuple(int(part) for part in version_match.groups()) >= (1, 24, 0),
        "produced artifact must include the 1.21.0 first-bloom milestone")

entity = read("src/main/java/de/sporenwerk/entity/DaemmerlingEntity.java")
for token in ("new BloomScentGoal(this)", "private static final class BloomScentGoal extends Goal",
              "SEARCH_RADIUS = 24", "SCENT_TICKS = 2400L",
              "nearestRecentBloom(", "mob.getNavigation().createPath(bloom.above(), 0) == null",
              "outsideArrivalRange(target)", "new CropThreatGoal(this)"):
    require(token in entity, "Dämmerling bloom response is missing " + token)
require("nearestRecentBloom(BlockPos center, int radius, long gameTime, long scentTicks)" in nodes,
        "saved field registry must expose only bounded recent blooms")
require("Version 1.16.0" in read("README.md"), "release notes missing 1.16.0")

# Keep the reward bounded: one spore by default, with a second as a rare 20% outcome.
reward = bloom[bloom.index("private static void releaseHarvestableSpores"):bloom.index("private static void accelerateCrops")]
require("random.nextFloat() < 0.20F ? 2 : 1" in reward,
        "bloom reward must remain one spore with a 20% chance for a second")
require("new ItemStack(ModItems.MUTAGENE_SPOREN.get(), count)" in reward,
        "bloom reward must use the registered spore item")
require("level.addFreshEntity(new ItemEntity(level, x, y, z, spores))" in reward,
        "bloom reward must be collectible in-world")
print("Mutagen Bloom strength gate, saved cooldown, harvestable spore reward, crop boost, mask counterplay, anchor protection and locales passed.")
