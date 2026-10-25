#!/usr/bin/env python3
"""Add a shard-powered Resonanzfokus combat tool (1.49.0)."""
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
        raise SystemExit("Resonanzfokus: " + message)


def replace_once(path, old, new, label):
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    require(old in source, "could not locate " + label)
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


# Registry and creative inventory.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
line = "import de.sporenwerk.item.ResonanzfokusItem;"
if line not in items:
    anchor = "import net.minecraft.world.item.Item;"
    require(anchor in items, "ModItems import anchor missing")
    items = items.replace(anchor, line + "\n" + anchor, 1)
shard = (
    '    public static final RegistryObject<Item> KRISTALLPIRSCHER_RESONANZSPLITTER = '
    'ITEMS.register("kristallpirscher_resonanzsplitter", () -> new Item(new Item.Properties().stacksTo(16)));'
)
registration = (
    '    public static final RegistryObject<Item> RESONANZFOKUS = '
    'ITEMS.register("resonanzfokus", () -> new ResonanzfokusItem(new Item.Properties().stacksTo(1)));'
)
if registration not in items:
    require(shard in items, "Resonanzsplitter registration missing")
    items = items.replace(shard, shard + "\n" + registration, 1)
items_path.write_text(items, encoding="utf-8")
replace_once(SRC / "registry/ModCreativeTabs.java",
    "output.accept(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get());",
    "output.accept(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get());\n"
    "                output.accept(ModItems.RESONANZFOKUS.get());",
    "creative tab entry")

# Combat behavior is server-authoritative, bounded, and uses existing mob classes and loot.
java = """
package de.sporenwerk.item;

import de.sporenwerk.entity.DaemmerlingEntity;
import de.sporenwerk.entity.KristallpirscherEntity;
import de.sporenwerk.registry.ModItems;
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
import org.jetbrains.annotations.Nullable;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public final class ResonanzfokusItem extends Item {
    private static final double PULSE_RADIUS = 5.5D;
    private static final int MAX_TARGETS = 3;
    private static final int COOLDOWN_TICKS = 80;

    public ResonanzfokusItem(Properties properties) { super(properties); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);
        if (!(level instanceof ServerLevel serverLevel)) return InteractionResultHolder.fail(stack);

        List<LivingEntity> targets = new ArrayList<>();
        targets.addAll(serverLevel.getEntitiesOfClass(DaemmerlingEntity.class,
                player.getBoundingBox().inflate(PULSE_RADIUS), entity -> entity.isAlive()));
        targets.addAll(serverLevel.getEntitiesOfClass(KristallpirscherEntity.class,
                player.getBoundingBox().inflate(PULSE_RADIUS), entity -> entity.isAlive()));
        targets.removeIf(target -> player.distanceToSqr(target) > PULSE_RADIUS * PULSE_RADIUS
                || !player.hasLineOfSight(target));
        targets.sort(Comparator.comparingDouble(target -> player.distanceToSqr(target)));

        if (targets.isEmpty()) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.resonanzfokus.no_target").withStyle(ChatFormatting.GRAY), true);
            return InteractionResultHolder.fail(stack);
        }
        if (!consumeResonanceShard(player)) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.resonanzfokus.need_shard").withStyle(ChatFormatting.RED), true);
            return InteractionResultHolder.fail(stack);
        }

        int affected = 0;
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
        }
        serverLevel.sendParticles(ParticleTypes.END_ROD, player.getX(), player.getY() + 1.0D,
                player.getZ(), 10, 0.35D, 0.25D, 0.35D, 0.02D);
        serverLevel.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME,
                SoundSource.PLAYERS, 0.9F, 0.65F + serverLevel.random.nextFloat() * 0.25F);
        player.getCooldowns().addCooldown(this, COOLDOWN_TICKS);
        player.swing(hand, true);
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.resonanzfokus.used", affected).withStyle(ChatFormatting.AQUA), true);
        return InteractionResultHolder.success(stack);
    }

    private static boolean consumeResonanceShard(Player player) {
        for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
            ItemStack candidate = player.getInventory().getItem(slot);
            if (candidate.is(ModItems.KRISTALLPIRSCHER_RESONANZSPLITTER.get())) {
                player.getInventory().removeItem(slot, 1);
                return true;
            }
        }
        return false;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level,
                                List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.sporenwerk.resonanzfokus.1").withStyle(ChatFormatting.AQUA));
        tooltip.add(Component.translatable("tooltip.sporenwerk.resonanzfokus.2").withStyle(ChatFormatting.GRAY));
        super.appendHoverText(stack, level, tooltip, flag);
    }
}
"""
java_path = SRC / "item/ResonanzfokusItem.java"
java_path.parent.mkdir(parents=True, exist_ok=True)
java_path.write_text(java.lstrip(), encoding="utf-8")

res = RES / "data/sporenwerk/recipes/resonanzfokus.json"
res.parent.mkdir(parents=True, exist_ok=True)
res.write_text(json.dumps({
    "type": "minecraft:crafting_shaped", "pattern": [" S ", "ARA", " C "],
    "key": {"S": {"item": "sporenwerk:kristallpirscher_resonanzsplitter"},
            "A": {"item": "minecraft:amethyst_shard"},
            "R": {"item": "minecraft:redstone"},
            "C": {"item": "minecraft:copper_ingot"}},
    "result": {"item": "sporenwerk:resonanzfokus", "count": 1}
}, indent=2) + "\n", encoding="utf-8")

adv = RES / "data/sporenwerk/advancements/recipes/misc/resonanzfokus.json"
adv.parent.mkdir(parents=True, exist_ok=True)
adv.write_text(json.dumps({
    "parent": "minecraft:recipes/root",
    "rewards": {"recipes": ["sporenwerk:resonanzfokus"]},
    "criteria": {
        "has_amethyst": {"trigger": "minecraft:inventory_changed",
                         "conditions": {"items": [{"items": ["minecraft:amethyst_shard"]}]}},
        "has_resonance_shard": {"trigger": "minecraft:inventory_changed",
                                "conditions": {"items": [{"items": ["sporenwerk:kristallpirscher_resonanzsplitter"]}]}},
        "has_the_recipe": {"trigger": "minecraft:recipe_unlocked",
                           "conditions": {"recipe": "sporenwerk:resonanzfokus"}}
    },
    "requirements": [["has_amethyst"], ["has_resonance_shard"], ["has_the_recipe"]]
}, indent=2) + "\n", encoding="utf-8")

model = ASSETS / "models/item/resonanzfokus.json"
model.parent.mkdir(parents=True, exist_ok=True)
model.write_text(json.dumps({"parent": "minecraft:item/generated",
                             "textures": {"layer0": "sporenwerk:item/resonanzfokus"}}, indent=2) + "\n",
                 encoding="utf-8")

# A unique 16x16 icon rather than a reused generic texture.
texture = ASSETS / "textures/item/resonanzfokus.png"
texture.parent.mkdir(parents=True, exist_ok=True)
im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.polygon([(7,0),(10,2),(13,2),(15,5),(13,7),(12,10),(8,15),(4,11),(4,8),(1,6),(3,3),(6,3)],
          fill=(34,43,54,255), outline=(13,19,26,255))
d.polygon([(7,3),(10,5),(11,8),(8,12),(5,9),(5,6)],
          fill=(110,59,181,255), outline=(211,190,246,255))
d.rectangle((7,5,9,7), fill=(255,240,190,255))
d.rectangle((2,4,3,5), fill=(204,120,75,255))
d.rectangle((12,4,13,5), fill=(204,120,75,255))
d.rectangle((6,11,7,12), fill=(63,176,177,255))
d.point((8,14), fill=(139,239,211,255))
im.save(texture, optimize=True)

preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
if '"resonanzfokus"' not in preview:
    anchor = '"sporenfiltereinsatz_mutagen"'
    require(anchor in preview, "make_art_preview item-list anchor missing")
    preview_path.write_text(preview.replace(anchor, anchor + ', "resonanzfokus"', 1), encoding="utf-8")

translations = {
 "de_de.json": {
  "item.sporenwerk.resonanzfokus": "Resonanzfokus",
  "tooltip.sporenwerk.resonanzfokus.1": "Rechtsklick: Löst einen gerichteten Resonanzimpuls aus.",
  "tooltip.sporenwerk.resonanzfokus.2": "Verbraucht 1 Resonanzsplitter; trifft bis zu 3 Sporenwerk-Gegner in 5,5 Blöcken mit Schaden, Verlangsamung und Rückstoß. Abklingzeit: 4 s.",
  "message.sporenwerk.resonanzfokus.no_target": "Keine Sporenwerk-Resonanzsignatur in Sichtweite.",
  "message.sporenwerk.resonanzfokus.need_shard": "Benötigt einen Kristallpirscher-Resonanzsplitter im Inventar.",
  "message.sporenwerk.resonanzfokus.used": "Resonanzimpuls trifft %s Gegner."
 },
 "en_us.json": {
  "item.sporenwerk.resonanzfokus": "Resonance Focus",
  "tooltip.sporenwerk.resonanzfokus.1": "Right-click to release a directed resonance pulse.",
  "tooltip.sporenwerk.resonanzfokus.2": "Consumes 1 resonance shard; hits up to 3 Sporenwerk threats within 5.5 blocks with damage, slowing and knockback. Cooldown: 4 s.",
  "message.sporenwerk.resonanzfokus.no_target": "No Sporenwerk resonance signature in line of sight.",
  "message.sporenwerk.resonanzfokus.need_shard": "A Crystal Stalker Resonance Shard is required in your inventory.",
  "message.sporenwerk.resonanzfokus.used": "Resonance pulse hits %s target(s)."
 }
}
for filename, entries in translations.items():
    path = ASSETS / "lang" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Update only active-version assertions in older tests; keep all archived release history.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.48.0",
                             "Aktueller Entwicklungsstand: 1.49.0")
    if "build.gradle" in updated:
        updated = updated.replace(r"1\.48\.0", r"1\.49\.0")
        updated = updated.replace("artifact must be version 1.48.0", "artifact must be version 1.49.0")
    updated = updated.replace('"Version 1.48.0" in readme and "Version 1.47.0" in readme',
                              '"Version 1.49.0" in readme and "Version 1.48.0" in readme')
    updated = updated.replace("release notes must add 1.48.0 while preserving 1.47.0",
                              "release notes must add 1.49.0 while preserving 1.48.0")
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.49.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not bump build.gradle")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
headline = "**Aktueller Entwicklungsstand: 1.49.0 — Resonanzfokus für taktische Gegenwehr im Nahbereich.**"
readme, count = re.subn(r"(?m)^\*\*Aktueller Entwicklungsstand:.*\*\*$", headline, readme, count=1)
if count == 0:
    readme = headline + "\n\n" + readme
focus = """## Aktueller Schwerpunkt — 1.49.0

- **Aktive Gegenwehr statt nur passiver Sicherung:** Der Resonanzfokus verwandelt Kristallpirscher-Beute in eine wiederverwendbare Nahbereichswaffe.
- **Taktischer Einsatz:** Ein erfolgreicher Impuls verbraucht genau einen Resonanzsplitter, trifft höchstens drei Sporenwerk-Gegner in 5,5 Blöcken Sichtweite und kombiniert typabhängigen Schaden mit Verlangsamung und Rückstoß.
- **Faire Fehlversuche:** Ohne passendes Ziel oder ohne Munition wird kein Splitter verbraucht und keine Abklingzeit gestartet.
- **Technische Grenzen:** Serverseitige Zielauswahl, Sichtlinienprüfung, festes Zielmaximum und vier Sekunden Abklingzeit.
- **Release-QA:** Rezept, Pixel-Art, DE/EN-Rückmeldungen, Regressionstest, Forge-Build, JAR-Inhalt und dedizierter Serverstart."""
start = readme.find("## Aktueller Schwerpunkt — ")
divider = readme.find("\n---", start) if start >= 0 else -1
if start >= 0 and divider >= 0:
    readme = readme[:start] + focus + "\n" + readme[divider + 1:]
section = """## Version 1.49.0 — Resonanzfokus und aktive Gegenwehr

- **Neues Kampfwerkzeug:** Der Resonanzfokus feuert einen sichtbaren Impuls und nutzt Kristallpirscher-Resonanzsplitter als echte Munition.
- **Zielgerichtete Wirkung:** Er trifft maximal drei Dämmerlinge oder Kristallpirscher innerhalb von 5,5 Blöcken und nur bei freier Sicht. Der Dämmerling erleidet höheren Schaden und längere Verlangsamung; der Kristallpirscher wird ebenfalls getroffen und kurz ausgebremst.
- **Ressourcenvertrag:** Ein Splitter wird erst nach erfolgreicher Zielsuche verbraucht. Fehlen Ziel oder Munition, wird keine Abklingzeit gestartet.
- **Minecraft-Integration:** Eigenes 16×16-Pixel-Artwork, Rezept, Rezeptbuch-Freischaltung, Creative-Tab-Eintrag und deutsche/englische Tooltips sowie Statusmeldungen.
- **Qualitätssicherung:** Regressionen prüfen Zielarten, Sichtlinie, Reichweite, Zielmaximum, Effekte, Splitterverbrauch, Rezept und Ressourcen. Die Pipeline baut anschließend die installierbare Forge-JAR und startet einen dedizierten Server."""
if "## Version 1.49.0 — Resonanzfokus und aktive Gegenwehr" not in readme:
    marker = "## Version 1.48.0 — Bioreaktor-Kreislauf und reaktive Sporenabwehr"
    index = readme.find(marker)
    require(index >= 0, "README 1.48.0 release-note anchor missing")
    readme = readme[:index] + section + "\n\n" + readme[index:]
readme_path.write_text(readme, encoding="utf-8")
print("Created Sporenwerk 1.49.0 Resonanzfokus patch and release metadata.")
