#!/usr/bin/env python3
"""Add the Luminous Crystal Core as a reusable boss relic with an interrupt pulse (1.74.0)."""
from pathlib import Path
import json
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require(condition, message):
    if not condition:
        raise SystemExit("Luminous Crystal Core 1.74: " + message)


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


# Add a real Java item, rather than a display-only icon. It is a reusable boss relic:
# right-click releases a short-range pulse, with a reliable counterplay window against the Colossus.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
import_line = "import de.sporenwerk.item.LeuchtenderKristallkernItem;"
if import_line not in items:
    anchor = "import net.minecraft.world.item.Item;"
    require(anchor in items, "ModItems import anchor missing")
    items = items.replace(anchor, import_line + "\n" + anchor, 1)
registration = '    public static final RegistryObject<Item> LEUCHTENDER_KRISTALLKERN = ITEMS.register("leuchtender_kristallkern", () -> new LeuchtenderKristallkernItem(new Item.Properties().stacksTo(1)));'
if registration not in items:
    anchor = '    public static final RegistryObject<Item> MUTAGENKOLOSS_HERZ = ITEMS.register("mutagenkoloss_herz", () -> new Item(new Item.Properties().stacksTo(1)));'
    require(anchor in items, "Mutagen Colossus heart registration missing")
    items = items.replace(anchor, anchor + "\n" + registration, 1)
items_path.write_text(items, encoding="utf-8")
require("LEUCHTENDER_KRISTALLKERN" in items_path.read_text(encoding="utf-8"),
        "item registration was not installed")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
creative_entry = "output.accept(ModItems.LEUCHTENDER_KRISTALLKERN.get());"
if creative_entry not in creative:
    anchor = "output.accept(ModItems.MUTAGENKOLOSS_HERZ.get());"
    require(anchor in creative, "Mutagen Colossus heart creative-tab anchor missing")
    creative_path.write_text(creative.replace(anchor, anchor + "\n                        " + creative_entry, 1), encoding="utf-8")

# Expose a guarded, server-authoritative counterplay method on the boss. A pulse only
# cancels an actual stomp/breath wind-up; it cannot cancel its awakening or idle state.
boss_path = SRC / "entity/MutagenkolossEntity.java"
boss = boss_path.read_text(encoding="utf-8")
method = r"""
    public boolean disruptWithResonancePulse() {
        if (this.level().isClientSide || this.attackTicksLeft <= 0) return false;
        int state = this.getAttackState();
        if (state != ATTACK_STOMP && state != ATTACK_BREATH) return false;

        this.attackTicksLeft = 0;
        this.attackCooldown = Math.max(this.attackCooldown, 80);
        this.entityData.set(ATTACK_TICKS, 0);
        this.entityData.set(ATTACK_STATE, ATTACK_IDLE);
        if (this.level() instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    this.getX(), this.getY() + this.getBbHeight() * 0.65D, this.getZ(),
                    28, 0.55D, 0.45D, 0.55D, 0.045D);
            serverLevel.sendParticles(ParticleTypes.WARPED_SPORE,
                    this.getX(), this.getY() + this.getBbHeight() * 0.45D, this.getZ(),
                    18, 0.48D, 0.4D, 0.48D, 0.02D);
            serverLevel.playSound(null, this.blockPosition(), SoundEvents.AMETHYST_BLOCK_BREAK,
                    SoundSource.HOSTILE, 1.4F, 0.62F);
        }
        return true;
    }
"""
if "public boolean disruptWithResonancePulse()" not in boss:
    anchor = "    public int getAttackState() { return this.entityData.get(ATTACK_STATE); }\n    public int getAttackTicks() { return this.entityData.get(ATTACK_TICKS); }"
    require(anchor in boss, "boss attack-state getters were not found")
    boss = boss.replace(anchor, anchor + "\n" + method, 1)
    boss_path.write_text(boss, encoding="utf-8")
require("public boolean disruptWithResonancePulse()" in boss_path.read_text(encoding="utf-8"),
        "boss counterplay method was not installed")

java = r"""
package de.sporenwerk.item;

import de.sporenwerk.entity.DaemmerlingEntity;
import de.sporenwerk.entity.KristallpirscherEntity;
import de.sporenwerk.entity.MutagenkolossEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import org.jetbrains.annotations.Nullable;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/** A reusable endgame relic. Its pulse can disrupt a telegraphed Colossus attack. */
public final class LeuchtenderKristallkernItem extends Item {
    private static final double PULSE_RADIUS = 8.0D;
    private static final int MAX_TARGETS = 4;
    private static final int COOLDOWN_TICKS = 200;

    public LeuchtenderKristallkernItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(level instanceof ServerLevel serverLevel)) return InteractionResultHolder.fail(stack);

        AABB volume = player.getBoundingBox().inflate(PULSE_RADIUS);
        List<LivingEntity> targets = new ArrayList<>();
        targets.addAll(serverLevel.getEntitiesOfClass(MutagenkolossEntity.class, volume, LivingEntity::isAlive));
        targets.addAll(serverLevel.getEntitiesOfClass(KristallpirscherEntity.class, volume, LivingEntity::isAlive));
        targets.addAll(serverLevel.getEntitiesOfClass(DaemmerlingEntity.class, volume, LivingEntity::isAlive));
        targets.removeIf(target -> player.distanceToSqr(target) > PULSE_RADIUS * PULSE_RADIUS
                || !player.hasLineOfSight(target));
        targets.sort(Comparator.comparingDouble(target -> player.distanceToSqr(target)));

        if (targets.isEmpty()) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.leuchtkern.no_target").withStyle(ChatFormatting.GRAY), true);
            return InteractionResultHolder.fail(stack);
        }

        int affected = 0;
        int interrupted = 0;
        for (LivingEntity target : targets) {
            if (affected >= MAX_TARGETS) break;
            boolean bossInterrupted = target instanceof MutagenkolossEntity boss
                    && boss.disruptWithResonancePulse();
            if (bossInterrupted) interrupted++;

            float damage = target instanceof MutagenkolossEntity
                    ? (bossInterrupted ? 14.0F : 5.0F)
                    : target instanceof KristallpirscherEntity ? 8.0F : 6.0F;
            target.hurt(player.damageSources().magic(), damage);
            target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN,
                    target instanceof MutagenkolossEntity ? 40 : 60,
                    target instanceof MutagenkolossEntity ? 0 : 1, true, true, true));
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    target.getX(), target.getY() + target.getBbHeight() * 0.55D, target.getZ(),
                    12, 0.24D, 0.28D, 0.24D, 0.025D);
            serverLevel.sendParticles(ParticleTypes.WARPED_SPORE,
                    target.getX(), target.getY() + target.getBbHeight() * 0.45D, target.getZ(),
                    8, 0.18D, 0.2D, 0.18D, 0.01D);
            affected++;
        }

        serverLevel.sendParticles(ParticleTypes.END_ROD, player.getX(), player.getY() + 1.0D,
                player.getZ(), 18, 0.45D, 0.3D, 0.45D, 0.035D);
        serverLevel.sendParticles(ParticleTypes.WARPED_SPORE, player.getX(), player.getY() + 0.8D,
                player.getZ(), 12, 0.4D, 0.22D, 0.4D, 0.018D);
        serverLevel.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME,
                SoundSource.PLAYERS, 1.0F, 0.58F + serverLevel.random.nextFloat() * 0.18F);
        player.getCooldowns().addCooldown(this, COOLDOWN_TICKS);
        player.swing(hand, true);
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.leuchtkern.used", affected, interrupted)
                .withStyle(ChatFormatting.AQUA), true);
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level,
                                List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.leuchtender_kristallkern.1")
                .withStyle(ChatFormatting.AQUA));
        tooltip.add(Component.translatable("tooltip.sporenwerk.leuchtender_kristallkern.2")
                .withStyle(ChatFormatting.GRAY));
        super.appendHoverText(stack, level, tooltip, flag);
    }
}
"""
write("src/main/java/de/sporenwerk/item/LeuchtenderKristallkernItem.java", java)

# Distinct, transparent 16x16 item pixel art: a dark angular shell, cyan crystal facets,
# and a small white-hot core. This becomes the real item sprite and QA preview input.
def make_core_icon():
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.polygon([(7, 0), (11, 2), (15, 7), (12, 12), (8, 15), (3, 12), (0, 7), (3, 3)],
                 fill=(20, 24, 44, 255))
    draw.polygon([(7, 1), (10, 3), (13, 7), (11, 11), (8, 14), (4, 11), (2, 7), (4, 4)],
                 fill=(28, 94, 142, 255))
    draw.polygon([(7, 2), (8, 6), (3, 7), (4, 4)], fill=(49, 222, 243, 255))
    draw.polygon([(8, 2), (10, 3), (13, 7), (9, 8), (8, 6)],
                 fill=(71, 244, 255, 255))
    draw.polygon([(3, 8), (8, 7), (8, 13), (4, 11)], fill=(21, 170, 205, 255))
    draw.polygon([(9, 8), (13, 7), (11, 11), (8, 14)], fill=(22, 125, 183, 255))
    draw.polygon([(6, 5), (9, 5), (11, 7), (9, 10), (6, 9), (5, 7)],
                 fill=(111, 255, 255, 255))
    draw.polygon([(7, 6), (9, 6), (10, 7), (8, 9), (6, 8)], fill=(238, 255, 255, 255))
    draw.point((4, 4), fill=(129, 255, 255, 255))
    draw.point((11, 4), fill=(174, 255, 255, 255))
    return image

core_texture = ASSETS / "textures/item/leuchtender_kristallkern.png"
core_texture.parent.mkdir(parents=True, exist_ok=True)
make_core_icon().save(core_texture, optimize=True)
write("src/main/resources/assets/sporenwerk/models/item/leuchtender_kristallkern.json", """
{
  "parent": "minecraft:item/generated",
  "textures": { "layer0": "sporenwerk:item/leuchtender_kristallkern" }
}
""")

# The Colossus always drops one core, so the relic is a real progression reward rather than a random dead end.
loot_path = RES / "data/sporenwerk/loot_tables/entities/mutagenkoloss.json"
loot = json.loads(loot_path.read_text(encoding="utf-8"))
already_drops_core = any(
    entry.get("name") == "sporenwerk:leuchtender_kristallkern"
    for pool in loot.get("pools", []) for entry in pool.get("entries", [])
)
if not already_drops_core:
    loot.setdefault("pools", []).append({
        "rolls": 1.0,
        "entries": [{"type": "minecraft:item", "name": "sporenwerk:leuchtender_kristallkern"}]
    })
loot_path.write_text(json.dumps(loot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

write("src/main/resources/data/sporenwerk/advancements/monsters/leuchtender_kristallkern.json", """
{
  "parent": "sporenwerk:monsters/mutagenkoloss",
  "display": {
    "icon": { "item": "sporenwerk:leuchtender_kristallkern" },
    "title": { "translate": "advancements.sporenwerk.leuchtkern.title" },
    "description": { "translate": "advancements.sporenwerk.leuchtkern.description" },
    "frame": "challenge",
    "show_toast": true,
    "announce_to_chat": true,
    "hidden": false
  },
  "criteria": {
    "claim_core": {
      "trigger": "minecraft:inventory_changed",
      "conditions": { "items": [{ "items": ["sporenwerk:leuchtender_kristallkern"] }] }
    }
  },
  "requirements": [["claim_core"]]
}
""")

# Both supported locales describe the active pulse and its boss counterplay.
for locale, values in {
    "de_de.json": {
        "item.sporenwerk.leuchtender_kristallkern": "Leuchtender Kristallkern",
        "tooltip.sporenwerk.leuchtender_kristallkern.1": "Ein lebender Resonanzkern aus dem Kristallkoloss.",
        "tooltip.sporenwerk.leuchtender_kristallkern.2": "Rechtsklick: Resonanzimpuls im Umkreis von 8 Blöcken. Unterbricht Stampf- und Atemaufladung des Kolosses. Abklingzeit: 10 Sekunden.",
        "message.sporenwerk.leuchtkern.no_target": "Kein Mutagengegner in Sichtweite innerhalb von 8 Blöcken.",
        "message.sporenwerk.leuchtkern.used": "Resonanzimpuls: %s Kreaturen getroffen, %s Bossangriffe unterbrochen.",
        "advancements.sporenwerk.leuchtkern.title": "Der Kern pulsiert",
        "advancements.sporenwerk.leuchtkern.description": "Nimm den Leuchtenden Kristallkern an dich."
    },
    "en_us.json": {
        "item.sporenwerk.leuchtender_kristallkern": "Luminous Crystal Core",
        "tooltip.sporenwerk.leuchtender_kristallkern.1": "A living resonance core taken from the Crystal Colossus.",
        "tooltip.sporenwerk.leuchtender_kristallkern.2": "Right-click: pulse within 8 blocks. Interrupts the Colossus's stomp and breath wind-ups. Cooldown: 10 seconds.",
        "message.sporenwerk.leuchtkern.no_target": "No Mutagen enemy in line of sight within 8 blocks.",
        "message.sporenwerk.leuchtkern.used": "Resonance pulse: hit %s creatures, interrupted %s boss attacks.",
        "advancements.sporenwerk.leuchtkern.title": "The Core Still Pulses",
        "advancements.sporenwerk.leuchtkern.description": "Claim the Luminous Crystal Core."
    }
}.items():
    path = ASSETS / "lang" / locale
    translations = json.loads(path.read_text(encoding="utf-8"))
    translations.update(values)
    path.write_text(json.dumps(translations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Include this exact item sprite in the existing generated visual QA sheet.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
if '"leuchtender_kristallkern"' not in preview:
    anchor = '"mutagenprobe", "mutagenextrakt", "mutagene_sporen", "feldscanner",'
    require(anchor in preview, "art preview item-list anchor missing")
    preview_path.write_text(preview.replace(anchor,
        '"mutagenprobe", "mutagenextrakt", "mutagene_sporen", "leuchtender_kristallkern", "feldscanner",', 1),
        encoding="utf-8")

# Every older regression suite checks that the build metadata agrees with the newest release.
for test_path in (ROOT / "tools").glob("test_*.py"):
    if test_path.name == "test_luminous_crystal_core_174.py":
        continue
    original = test_path.read_text(encoding="utf-8")
    updated = original.replace("Aktueller Entwicklungsstand: 1.73.0",
                               "Aktueller Entwicklungsstand: 1.74.0")
    updated = updated.replace(r"1\.73\.0", r"1\.74\.0")
    updated = updated.replace("artifact must be version 1.73.0",
                              "artifact must be version 1.74.0")
    updated = updated.replace(
        '"Version 1.73.0" in readme and "Version 1.72.0" in readme',
        '"Version 1.74.0" in readme and "Version 1.73.0" in readme')
    if updated != original:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.74.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Gradle artifact version")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
release = """## Version 1.74.0 — Leuchtender Kristallkern als Bossreliquie

- **Das Konzept wird zum echten Item:** Der Leuchtende Kristallkern erhält eine eigene transparente 16×16-Pixeltextur, Itemmodell, Kreativkatalog-Eintrag und deutsche/englische Lokalisierung.
- **Funktion statt reiner Dekoration:** Rechtsklick entfesselt serverseitig einen Resonanzimpuls, der bis zu vier Mutagengegner in Sichtweite innerhalb von acht Blöcken trifft. Das Artefakt ist wiederverwendbar und hat eine feste Abklingzeit von zehn Sekunden.
- **Aktive Boss-Gegenwehr:** Trifft der Impuls den Kristallkoloss während seiner angekündigten Stampf- oder Atemaufladung, unterbricht er diesen Angriff, setzt den Windup sichtbar zurück und verursacht zusätzlichen Schaden. Aufwachen und normale Phasen werden nicht abgebrochen.
- **Verdienter Endgame-Fund:** Der Kristallkoloss lässt einen Kern garantiert fallen. Ein eigenes Advancement zeichnet den Fund auf; das Bild ist außerdem in der Visual-QA-Vorschau enthalten.
- **Sicherheits- und Regressionstests:** Zielauswahl und Schaden laufen serverseitig; Reichweite, Sichtlinie, Zielobergrenze, Windup-Interruption, Loot-Tabelle, Modell, Textur, DE/EN-Texte und Versionsmetadaten werden geprüft.

"""
current = """## Aktueller Entwicklungsschritt — 1.74.0

- **Leuchtender Kristallkern:** Das Kristallkern-Bild ist als transparentes 16×16-Minecraft-Item eingebunden und wird als garantierte Endgame-Beute des Kristallkolosses vergeben.
- **Resonanzimpuls:** Rechtsklick trifft bis zu vier nahe sichtbare Mutagengegner, mit Abklingzeit und serverseitiger Zielprüfung.
- **Gegen die Boss-Angriffsfenster:** Der Impuls kann Stampf- und Atemaufladungen des Kristallkolosses beenden; außerhalb solcher Aufladungen unterbricht er keine Bossphase.
- **Visual QA und Inhalt:** Itemmodell, Tooltip, DE/EN-Texte, Fund-Advancement und JAR-Prüfung sind Bestandteil des Build-Workflows.

"""
if "## Version 1.74.0 — Leuchtender Kristallkern als Bossreliquie" not in readme:
    marker = "## Version 1.73.0 — Resonanzverdichtung überlappender Mutagenfelder"
    index = readme.find(marker)
    require(index >= 0, "could not find 1.73 release heading")
    readme = readme[:index] + release + readme[index:]
if "## Aktueller Entwicklungsschritt — 1.74.0" not in readme:
    marker = "## Aktueller Entwicklungsschritt — 1.73.0"
    index = readme.find(marker)
    require(index >= 0, "could not find current 1.73 development section")
    readme = readme[:index] + current + readme[index:]
readme = readme.replace(
    "**Aktueller Entwicklungsstand: 1.73.0 — Resonanzverdichtung überlappender Mutagenfelder.**",
    "**Aktueller Entwicklungsstand: 1.74.0 — Leuchtender Kristallkern als aktive Bossreliquie.**")
require("Aktueller Entwicklungsstand: 1.74.0" in readme,
        "README current-version headline was not updated")
readme_path.write_text(readme, encoding="utf-8")

print("Sporenwerk 1.74.0 generated: the Luminous Crystal Core is loot, a usable pulse relic, and Colossus attack counterplay.")
