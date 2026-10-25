#!/usr/bin/env python3
"""Connect Filtermoos protection with Crystal Stalker pulse defense and timed Resonanzfokus parries (1.51.0)."""
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
        raise SystemExit("Resonance counterplay: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# 1) Mature living Filtermoos also buffers the delayed Crystal Stalker pulse.
stalker_path = SRC / "entity/KristallpirscherEntity.java"
replace_once(
    stalker_path,
    "import de.sporenwerk.block.InfestedTerrainBlock;",
    "import de.sporenwerk.block.InfestedTerrainBlock;\nimport de.sporenwerk.infection.FilterMossSymbiosis;",
    "Filtermoos helper import in Crystal Stalker"
)
pulse_target = """            if (distanceToSqr(player) <= RESONANCE_EFFECT_RADIUS_SQR) {
                player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 50, 0), this);
            }"""
pulse_buffered = """            // Living Filtermoos is a countermeasure for the released pulse, not a new per-tick scan.
            if (distanceToSqr(player) <= RESONANCE_EFFECT_RADIUS_SQR
                    && !FilterMossSymbiosis.protects(level(), player.blockPosition())) {
                player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 50, 0), this);
            }"""
replace_once(stalker_path, pulse_target, pulse_buffered, "Crystal Stalker pulse release loop")

disrupt_anchor = """    @Override
    public boolean doHurtTarget(Entity target) {"""
disrupt_method = """    /**
     * Interrupts only an active, field-enabled windup. A mistimed hit remains an ordinary attack.
     * The successful parry consumes the current windup and places the ability on its normal cooldown.
     */
    public boolean disruptResonance() {
        if (level().isClientSide || resonanceWindup <= 0 || resonanceCooldown > 0 || !isOnHighTierSoil()) {
            return false;
        }
        resonanceWindup = 0;
        resonanceCooldown = RESONANCE_COOLDOWN_TICKS;
        if (level() instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(ParticleTypes.CRIT,
                    getX(), getY() + 0.75D, getZ(), 16, 0.35D, 0.28D, 0.35D, 0.08D);
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    getX(), getY() + 0.9D, getZ(), 10, 0.28D, 0.32D, 0.28D, 0.03D);
            level().playSound(null, blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, 1.0F, 1.35F);
        }
        return true;
    }

"""
replace_once(stalker_path, disrupt_anchor, disrupt_method + disrupt_anchor,
             "Crystal Stalker counterpulse interruption method")

# 2) A correctly timed Resonanzfokus hit grants extra opening and a one-time research reward.
focus_path = SRC / "item/ResonanzfokusItem.java"
for anchor, addition, label in [
    ("import net.minecraft.ChatFormatting;",
     "import net.minecraft.advancements.Advancement;\nimport net.minecraft.ChatFormatting;", "Advancement import"),
    ("import net.minecraft.network.chat.Component;",
     "import net.minecraft.network.chat.Component;\nimport net.minecraft.resources.ResourceLocation;", "ResourceLocation import"),
    ("import net.minecraft.server.level.ServerLevel;",
     "import net.minecraft.server.level.ServerLevel;\nimport net.minecraft.server.level.ServerPlayer;", "ServerPlayer import"),
]:
    replace_once(focus_path, anchor, addition, label)

old_loop = """        int affected = 0;
        for (LivingEntity target : targets) {
            if (affected >= MAX_TARGETS) break;
            boolean stalker = target instanceof KristallpirscherEntity;
            target.hurt(player.damageSources().magic(), stalker ? 5.0F : 8.0F);
            target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN,
                    stalker ? 40 : 70, 1, true, true, true));
            target.knockback(0.9D, player.getX() - target.getX(), player.getZ() - target.getZ());
            serverLevel.sendParticles(ParticleTypes.WARPED_SPORE,
                    target.getX(), target.getY() + target.getBbHeight() * 0.5D, target.getZ(),
                    14, 0.24D, 0.24D, 0.24D, 0.01D);
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    target.getX(), target.getY() + target.getBbHeight() * 0.5D, target.getZ(),
                    5, 0.12D, 0.16D, 0.12D, 0.02D);
            affected++;
        }"""
new_loop = """        int affected = 0;
        int interruptedPulses = 0;
        for (LivingEntity target : targets) {
            if (affected >= MAX_TARGETS) break;
            boolean stalker = target instanceof KristallpirscherEntity;
            boolean interrupted = stalker && ((KristallpirscherEntity) target).disruptResonance();
            float damage = stalker ? (interrupted ? 9.0F : 5.0F) : 8.0F;
            int slowDuration = stalker ? (interrupted ? 100 : 40) : 70;
            target.hurt(player.damageSources().magic(), damage);
            target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN,
                    slowDuration, 1, true, true, true));
            target.knockback(interrupted ? 1.25D : 0.9D,
                    player.getX() - target.getX(), player.getZ() - target.getZ());
            if (interrupted) {
                interruptedPulses++;
                player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,
                        60, 0, true, true, true));
                if (player instanceof ServerPlayer serverPlayer) {
                    awardCounterpulseResearch(serverPlayer);
                }
                player.displayClientMessage(Component.translatable(
                        "message.sporenwerk.resonanzfokus.counterpulse").withStyle(ChatFormatting.GOLD), true);
            }
            serverLevel.sendParticles(ParticleTypes.WARPED_SPORE,
                    target.getX(), target.getY() + target.getBbHeight() * 0.5D, target.getZ(),
                    14, 0.24D, 0.24D, 0.24D, 0.01D);
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    target.getX(), target.getY() + target.getBbHeight() * 0.5D, target.getZ(),
                    interrupted ? 14 : 5, 0.12D, 0.16D, 0.12D, 0.02D);
            affected++;
        }"""
replace_once(focus_path, old_loop, new_loop, "Resonanzfokus target combat loop")

award_anchor = """    private static boolean consumeResonanceShard(Player player) {"""
award_helper = """    private static void awardCounterpulseResearch(ServerPlayer player) {
        var server = player.getServer();
        Advancement milestone = server == null ? null : server.getAdvancements().getAdvancement(
                new ResourceLocation("sporenwerk", "monsters/resonance_parry"));
        if (milestone != null) {
            player.getAdvancements().award(milestone, "counterpulse_interrupted");
        }
    }

"""
replace_once(focus_path, award_anchor, award_helper + award_anchor, "one-time counterpulse research award")

# Teach the timing window in the actual item tooltip.
tooltip_anchor = """        tooltip.add(Component.translatable("tooltip.sporenwerk.resonanzfokus.2").withStyle(ChatFormatting.GRAY));
        super.appendHoverText(stack, level, tooltip, flag);"""
tooltip_new = """        tooltip.add(Component.translatable("tooltip.sporenwerk.resonanzfokus.2").withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("tooltip.sporenwerk.resonanzfokus.3").withStyle(ChatFormatting.GOLD));
        super.appendHoverText(stack, level, tooltip, flag);"""
replace_once(focus_path, tooltip_anchor, tooltip_new, "timed counterpulse tooltip")

# 3) One-time field-research advancement and restrained reward; award is triggered only on a real interrupt.
advancement = {
    "parent": "sporenwerk:monsters/kristallpirscher_resonanzsplitter",
    "display": {
        "icon": {"item": "sporenwerk:kristallpirscher_resonanzsplitter"},
        "title": {"translate": "advancements.sporenwerk.resonance_parry.title"},
        "description": {"translate": "advancements.sporenwerk.resonance_parry.description"},
        "frame": "goal",
        "show_toast": True,
        "announce_to_chat": False,
        "hidden": False
    },
    "criteria": {"counterpulse_interrupted": {"trigger": "minecraft:impossible"}},
    "requirements": [["counterpulse_interrupted"]],
    "rewards": {"loot": ["sporenwerk:quests/resonance_parry"]}
}
adv_path = RES / "data/sporenwerk/advancements/monsters/resonance_parry.json"
adv_path.parent.mkdir(parents=True, exist_ok=True)
adv_path.write_text(json.dumps(advancement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

loot = {
    "type": "minecraft:generic",
    "pools": [
        {"rolls": 1.0, "entries": [{"type": "minecraft:item", "name": "sporenwerk:mutagenextrakt"}]},
        {"rolls": 1.0, "entries": [{
            "type": "minecraft:item", "name": "sporenwerk:sporenfiltereinsatz",
            "functions": [{"function": "minecraft:set_count", "count": 2}]
        }]}
    ]
}
loot_path = RES / "data/sporenwerk/loot_tables/quests/resonance_parry.json"
loot_path.parent.mkdir(parents=True, exist_ok=True)
loot_path.write_text(json.dumps(loot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

translations = {
    "de_de.json": {
        "tooltip.sporenwerk.resonanzfokus.3": "Timing: Triff den Kristallpirscher während seiner Aufladung, um den Impuls zu brechen.",
        "message.sporenwerk.resonanzfokus.counterpulse": "Resonanz gekontert! Der Kristallpirscher ist unterbrochen; kurzzeitige Resistenz aktiviert.",
        "advancements.sporenwerk.resonance_parry.title": "Echo gebrochen",
        "advancements.sporenwerk.resonance_parry.description": "Unterbrich eine aktive Kristallpirscher-Resonanzaufladung mit dem Resonanzfokus."
    },
    "en_us.json": {
        "tooltip.sporenwerk.resonanzfokus.3": "Timing: Hit the Crystal Stalker during its windup to break the pulse.",
        "message.sporenwerk.resonanzfokus.counterpulse": "Resonance countered! The Crystal Stalker is interrupted; brief resistance activated.",
        "advancements.sporenwerk.resonance_parry.title": "Echo Broken",
        "advancements.sporenwerk.resonance_parry.description": "Interrupt an active Crystal Stalker resonance windup with the Resonance Focus."
    }
}
for filename, entries in translations.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Bump test contracts that target the active release; historical release notes stay intact.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.50.0",
                             "Aktueller Entwicklungsstand: 1.51.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.50\.0", r"1\.51\.0")
        updated = updated.replace("artifact must be version 1.50.0", "artifact must be version 1.51.0")
    updated = updated.replace('"Version 1.50.0" in readme and "Version 1.49.0" in readme',
                              '"Version 1.51.0" in readme and "Version 1.50.0" in readme')
    updated = updated.replace("release notes must add 1.50.0 while preserving 1.49.0",
                              "release notes must add 1.51.0 while preserving 1.50.0")
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.51.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not set artifact version to 1.51.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
headline = "**Aktueller Entwicklungsstand: 1.51.0 — Resonanzparade, lebender Schutz und Feldforschung.**"
readme, count = re.subn(r"(?m)^\*\*Aktueller Entwicklungsstand:.*\*\*$", headline, readme, count=1)
require(count == 1, "could not update README current-version headline")

focus = """## Aktueller Schwerpunkt — 1.51.0

- **Reaktionskampf:** Der Resonanzfokus kann einen laufenden Kristallpirscher-Resonanzimpuls unterbrechen. Das Zeitfenster wird über das vorhandene Klang-/Partikel-Telegraphing angekündigt.
- **Lebende Schutzökologie:** Reifes Filtermoos der Mutagenstufe II/III puffert den tatsächlichen Resonanztreffer im kleinen Schutzradius. Die Prüfung findet nur beim Puls-Auslösen statt, nicht als zusätzliche Tick-Schleife.
- **Forschungsfortschritt:** Der erste echte Gegenimpuls schaltet eine einmalige Forschungsstufe frei und liefert Mutagenextrakt plus zwei Filtereinsätze.
- **Klares Kampf-Feedback:** Eine gelungene Parade verursacht stärkeren Schaden und längere Verlangsamung am Kristallpirscher und verleiht dem Spieler kurzzeitig Resistenz.
- **Release-QA:** Separate Regressionen prüfen Windup-Unterbrechung, Feldschutz, One-shot-Belohnung, Übersetzungen, Forge-JAR und dedizierten Serverstart."""
focus_start = readme.find("## Aktueller Schwerpunkt — ")
divider = readme.find("\n---", focus_start) if focus_start >= 0 else -1
require(focus_start >= 0 and divider >= 0, "could not locate README current-focus boundary")
readme = readme[:focus_start] + focus + "\n" + readme[divider + 1:]

section = """## Version 1.51.0 — Resonanzparade und lebender Schutz

- **Aktive Konteraktion:** Ein Resonanzfokus-Treffer während der 30-Tick-Aufladung des Kristallpirschers bricht den noch nicht freigesetzten Impuls ab und startet dessen normale Abklingzeit. Außerhalb des Zeitfensters ist der Treffer ein normaler Fokus-Angriff.
- **Fairer Timing-Bonus:** Eine erfolgreiche Parade verursacht 9 statt 5 Schaden am Kristallpirscher, verlängert die Verlangsamung, verstärkt den Rückstoß und verleiht dem Spieler kurzzeitige Resistenz. Der erfolgreiche Fokusimpuls kostet weiterhin genau einen Resonanzsplitter.
- **Filtermoos als echte Gegenwehr:** Reifes Filtermoos der Stufe II/III kann den freigesetzten Resonanzimpuls innerhalb seines vorhandenen Schutzradius abfangen. Die zusätzliche Prüfung erfolgt beim ohnehin vorhandenen Puls-Auslösen, nicht in einer neuen Tick-Schleife.
- **Einmaliger Forschungsfund:** Die erste Unterbrechung schaltet „Echo gebrochen“ frei und gibt Mutagenextrakt plus zwei Sporenfiltereinsätze. Der Advancement-Status verhindert wiederholtes Farmen der Belohnung.
- **Qualitätssicherung:** Tests prüfen Timing, Windup-Abbruch, Puls-Cooldown, Filtermoos-Schutz, einm alige Belohnung, deutsche/englische Texte, Ressourcen und JAR-Inhalt."""
section = section.replace("einm alige", "einmalige")
if "## Version 1.51.0 — Resonanzparade und lebender Schutz" not in readme:
    marker = "## Version 1.50.0 — Lebendes Filtermoos und natürliche Feldabwehr"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate 1.50.0 release-note anchor")
    readme = readme[:idx] + section + "\n\n" + readme[idx:]
readme_path.write_text(readme, encoding="utf-8")
print("Sporenwerk 1.51.0 generated: timed resonance parry, Filtermoos pulse interception, one-time research reward and regression contracts.")
