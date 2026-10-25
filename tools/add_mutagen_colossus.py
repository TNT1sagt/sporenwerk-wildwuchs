#!/usr/bin/env python3
"""Add the animated crystal colossus boss, visual assets, and a Survival summoning ritual (1.55.0)."""
from pathlib import Path
import json
import random
import re
import sys
from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SRC = ROOT / "src/main/java/de/sporenwerk"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/sporenwerk"


def require(ok, message):
    if not ok:
        raise SystemExit("Mutagen Colossus: " + message)


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def add_import(path, anchor, lines, label):
    source = path.read_text(encoding="utf-8")
    missing = [line for line in lines.splitlines() if line not in source]
    if not missing:
        return
    require(anchor in source, "could not find import anchor for " + label)
    path.write_text(source.replace(anchor, anchor + "\n" + "\n".join(missing), 1), encoding="utf-8")


def append_before_class_end(path, snippet, sentinel, label):
    source = path.read_text(encoding="utf-8")
    if sentinel in source:
        return
    idx = source.rfind("}")
    require(idx >= 0, "could not locate class end for " + label)
    path.write_text(source[:idx] + "\n" + snippet.strip() + "\n" + source[idx:], encoding="utf-8")


# Register a separate four-legged boss. It is deliberately not part of ordinary biome spawning:
# in Survival it is summoned deliberately with three core crystals on Tier-III Mutagen soil.
entities_path = SRC / "registry/ModEntities.java"
entities = entities_path.read_text(encoding="utf-8")
if "MUTAGENKOLOSS" not in entities:
    add_import(entities_path, "import de.sporenwerk.entity.KristallpirscherEntity;",
               "import de.sporenwerk.entity.MutagenkolossEntity;", "boss entity")
    entities = entities_path.read_text(encoding="utf-8")
    anchor = '                    .build("kristallpirscher"));'
    require(anchor in entities, "could not locate Kristallpirscher registration")
    entities = entities.replace(anchor, anchor + '''

    public static final RegistryObject<EntityType<MutagenkolossEntity>> MUTAGENKOLOSS =
            ENTITIES.register("mutagenkoloss", () -> EntityType.Builder
                    .of(MutagenkolossEntity::new, MobCategory.MONSTER)
                    .sized(4.8F, 4.5F)
                    .clientTrackingRange(16)
                    .fireImmune()
                    .build("mutagenkoloss"));''', 1)
    entities_path.write_text(entities, encoding="utf-8")
require("EntityType<MutagenkolossEntity>" in entities_path.read_text(encoding="utf-8"),
        "boss entity registration was not installed")

# Boss stats, renderer, and bespoke model layers are registered through standard Forge events.
events_path = SRC / "registry/ModEntityEvents.java"
events = events_path.read_text(encoding="utf-8")
if "createMutagenkolossAttributes" not in events:
    append_before_class_end(events_path, '''
    @SubscribeEvent
    public static void createMutagenkolossAttributes(EntityAttributeCreationEvent event) {
        event.put(ModEntities.MUTAGENKOLOSS.get(), Zombie.createAttributes()
                .add(Attributes.MAX_HEALTH, 260.0D)
                .add(Attributes.ATTACK_DAMAGE, 16.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.25D)
                .add(Attributes.FOLLOW_RANGE, 40.0D)
                .add(Attributes.ARMOR, 18.0D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.95D)
                .build());
    }
''', "createMutagenkolossAttributes", "boss attributes")
add_import(events_path, "import de.sporenwerk.registry.ModEntities;",
           "import net.minecraft.world.entity.ai.attributes.Attributes;\nimport net.minecraft.world.entity.monster.Zombie;\nimport net.minecraftforge.event.entity.EntityAttributeCreationEvent;",
           "boss attribute event imports")

# A functional, server-authoritative boss with synchronized animation states, a boss bar,
# a telegraphed stomp, a directional crystal breath, and a one-time phase transition.
write("src/main/java/de/sporenwerk/entity/MutagenkolossEntity.java", r"""
package de.sporenwerk.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * A towering crystal-backed Mutagen boss. Animation state is synchronized so every client
 * sees the same windups; all damage, phase changes, and hit tests are server-authoritative.
 */
public final class MutagenkolossEntity extends Monster {
    public static final int ATTACK_IDLE = 0;
    public static final int ATTACK_STOMP = 1;
    public static final int ATTACK_BREATH = 2;
    public static final int ATTACK_AWAKENING = 3;
    private static final EntityDataAccessor<Integer> ATTACK_STATE =
            SynchedEntityData.defineId(MutagenkolossEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> ATTACK_TICKS =
            SynchedEntityData.defineId(MutagenkolossEntity.class, EntityDataSerializers.INT);
    private static final int STOMP_WINDUP = 42;
    private static final int BREATH_WINDUP = 48;
    private static final int AWAKENING_WINDUP = 36;

    private final ServerBossEvent bossEvent = new ServerBossEvent(
            Component.translatable("entity.sporenwerk.mutagenkoloss"),
            BossEvent.BossBarColor.PURPLE, BossEvent.BossBarOverlay.PROGRESS);
    private int attackTicksLeft;
    private int attackCooldown = 80;
    private boolean secondPhaseTriggered;

    public MutagenkolossEntity(EntityType<? extends MutagenkolossEntity> type, Level level) {
        super(type, level);
        this.setPersistenceRequired();
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new MeleeAttackGoal(this, 1.12D, true));
        this.goalSelector.addGoal(2, new WaterAvoidingRandomStrollGoal(this, 0.62D));
        this.goalSelector.addGoal(3, new LookAtPlayerGoal(this, Player.class, 28.0F));
        this.goalSelector.addGoal(4, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ATTACK_STATE, ATTACK_IDLE);
        this.entityData.define(ATTACK_TICKS, 0);
    }

    public int getAttackState() { return this.entityData.get(ATTACK_STATE); }
    public int getAttackTicks() { return this.entityData.get(ATTACK_TICKS); }

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide) return;

        this.bossEvent.setProgress(Math.max(0.0F, Math.min(1.0F, this.getHealth() / this.getMaxHealth())));
        if (this.attackCooldown > 0) this.attackCooldown--;

        if (this.attackTicksLeft > 0) {
            this.attackTicksLeft--;
            this.entityData.set(ATTACK_TICKS, this.attackTicksLeft);
            emitWindupParticles();
            if (this.attackTicksLeft == 0) releaseAttack(this.getAttackState());
            return;
        }

        LivingEntity target = this.getTarget();
        if (target == null || !target.isAlive()) {
            this.entityData.set(ATTACK_STATE, ATTACK_IDLE);
            this.entityData.set(ATTACK_TICKS, 0);
            return;
        }
        this.getLookControl().setLookAt(target, 30.0F, 30.0F);

        if (!this.secondPhaseTriggered && this.getHealth() <= this.getMaxHealth() * 0.5F) {
            this.secondPhaseTriggered = true;
            beginAttack(ATTACK_AWAKENING, AWAKENING_WINDUP);
            return;
        }
        if (this.attackCooldown <= 0) {
            if (this.distanceToSqr(target) <= 100.0D) {
                beginAttack(ATTACK_STOMP, STOMP_WINDUP);
            } else {
                beginAttack(ATTACK_BREATH, BREATH_WINDUP);
            }
        }
    }

    private void beginAttack(int state, int duration) {
        this.entityData.set(ATTACK_STATE, state);
        this.attackTicksLeft = duration;
        this.entityData.set(ATTACK_TICKS, duration);
        float pitch = state == ATTACK_BREATH ? 0.62F : state == ATTACK_AWAKENING ? 0.48F : 0.72F;
        this.level().playSound(null, this.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME,
                SoundSource.HOSTILE, 1.5F, pitch);
        if (this.level() instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    this.getX(), this.getY() + 2.0D, this.getZ(), 18,
                    1.1D, 0.55D, 1.1D, 0.035D);
        }
    }

    private void emitWindupParticles() {
        if (!(this.level() instanceof ServerLevel serverLevel)) return;
        int state = this.getAttackState();
        if (this.attackTicksLeft % 6 != 0) return;
        if (state == ATTACK_BREATH) {
            serverLevel.sendParticles(ParticleTypes.DRAGON_BREATH,
                    this.getX(), this.getY() + 2.2D, this.getZ(), 12,
                    0.45D, 0.35D, 0.45D, 0.02D);
        } else {
            serverLevel.sendParticles(ParticleTypes.CRIT,
                    this.getX(), this.getY() + 0.4D, this.getZ(), 18,
                    1.0D, 0.16D, 1.0D, 0.08D);
        }
    }

    private void releaseAttack(int state) {
        if (state == ATTACK_STOMP || state == ATTACK_AWAKENING) {
            boolean empowered = state == ATTACK_AWAKENING;
            performStomp(empowered ? 18.0F : 14.0F, empowered ? 7.2D : 5.8D);
            if (empowered) {
                this.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 300, 0));
                this.level().playSound(null, this.blockPosition(), SoundEvents.GENERIC_EXPLODE,
                        SoundSource.HOSTILE, 2.0F, 0.56F);
            }
            this.attackCooldown = empowered ? 72 : 92;
        } else if (state == ATTACK_BREATH) {
            performCrystalBreath();
            this.attackCooldown = 128;
        }
        this.entityData.set(ATTACK_STATE, ATTACK_IDLE);
        this.entityData.set(ATTACK_TICKS, 0);
    }

    private void performStomp(float damage, double radius) {
        if (this.level() instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(ParticleTypes.EXPLOSION,
                    this.getX(), this.getY() + 0.35D, this.getZ(), 10,
                    radius * 0.55D, 0.18D, radius * 0.55D, 0.02D);
            serverLevel.sendParticles(ParticleTypes.END_ROD,
                    this.getX(), this.getY() + 0.7D, this.getZ(), 46,
                    radius * 0.72D, 0.22D, radius * 0.72D, 0.06D);
        }
        this.level().playSound(null, this.blockPosition(), SoundEvents.GENERIC_EXPLODE,
                SoundSource.HOSTILE, 1.8F, 0.72F);
        AABB area = this.getBoundingBox().inflate(radius, 2.6D, radius);
        List<LivingEntity> victims = this.level().getEntitiesOfClass(LivingEntity.class, area,
                entity -> entity != this && entity.isAlive() && !this.isAlliedTo(entity));
        for (LivingEntity victim : victims) {
            victim.hurt(this.damageSources().mobAttack(this), damage);
            victim.knockback(1.65D, this.getX() - victim.getX(), this.getZ() - victim.getZ());
            if (damage > 15.0F) victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 70, 1));
        }
    }

    private void performCrystalBreath() {
        Vec3 direction = this.getLookAngle().normalize();
        Vec3 origin = this.position().add(0.0D, 2.15D, 0.0D).add(direction.scale(1.2D));
        if (this.level() instanceof ServerLevel serverLevel) {
            for (int step = 1; step <= 16; step++) {
                Vec3 point = origin.add(direction.scale(step));
                serverLevel.sendParticles(ParticleTypes.DRAGON_BREATH,
                        point.x, point.y, point.z, 9, 0.35D, 0.28D, 0.35D, 0.012D);
                serverLevel.sendParticles(ParticleTypes.END_ROD,
                        point.x, point.y, point.z, 3, 0.2D, 0.18D, 0.2D, 0.008D);
            }
        }
        this.level().playSound(null, this.blockPosition(), SoundEvents.BEACON_ACTIVATE,
                SoundSource.HOSTILE, 1.6F, 0.58F);

        AABB nearby = this.getBoundingBox().inflate(17.0D, 5.0D, 17.0D);
        for (LivingEntity victim : this.level().getEntitiesOfClass(LivingEntity.class, nearby,
                entity -> entity != this && entity.isAlive() && !this.isAlliedTo(entity))) {
            Vec3 delta = victim.position().add(0.0D, victim.getBbHeight() * 0.45D, 0.0D).subtract(origin);
            double along = delta.dot(direction);
            if (along < 0.0D || along > 16.5D) continue;
            Vec3 lateral = delta.subtract(direction.scale(along));
            if (lateral.lengthSqr() > 3.2D) continue;
            victim.hurt(this.damageSources().mobAttack(this), 10.0F);
            victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 90, 0));
            victim.knockback(0.8D, this.getX() - victim.getX(), this.getZ() - victim.getZ());
        }
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putBoolean("SporenwerkPhaseTwo", this.secondPhaseTriggered);
        tag.putInt("SporenwerkAttackCooldown", this.attackCooldown);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.secondPhaseTriggered = tag.getBoolean("SporenwerkPhaseTwo");
        this.attackCooldown = Math.max(20, tag.getInt("SporenwerkAttackCooldown"));
        this.attackTicksLeft = 0;
        this.entityData.set(ATTACK_STATE, ATTACK_IDLE);
        this.entityData.set(ATTACK_TICKS, 0);
    }

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        this.bossEvent.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        this.bossEvent.removePlayer(player);
    }

    @Override
    public boolean isPersistenceRequired() {
        return true;
    }

    @Override
    public boolean removeWhenFarAway(double distanceToClosestPlayer) {
        return false;
    }

}
""")

# The bespoke model is made of articulated quadruped parts, crystal spines, horn plates, paws and a segmented tail.
# Animations are procedural and use entity-synchronized attack state; this needs no extra animation dependency.
write("src/main/java/de/sporenwerk/client/MutagenkolossModel.java", r"""
package de.sporenwerk.client;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.MutagenkolossEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

public final class MutagenkolossModel extends EntityModel<MutagenkolossEntity> {
    public static final ModelLayerLocation LAYER_LOCATION =
            new ModelLayerLocation(new ResourceLocation(Sporenwerk.MODID, "mutagenkoloss"), "main");
    public static final ModelLayerLocation GLOW_LAYER_LOCATION =
            new ModelLayerLocation(new ResourceLocation(Sporenwerk.MODID, "mutagenkoloss"), "glow");

    private final ModelPart root;
    private final ModelPart body;
    private final ModelPart head;
    private final ModelPart frontLeft;
    private final ModelPart frontRight;
    private final ModelPart rearLeft;
    private final ModelPart rearRight;
    private final ModelPart tail;
    private final ModelPart tailTip;
    private final ModelPart[] spines;

    public MutagenkolossModel(ModelPart root) {
        this.root = root;
        this.body = root.getChild("body");
        this.head = body.getChild("head");
        this.frontLeft = body.getChild("front_left");
        this.frontRight = body.getChild("front_right");
        this.rearLeft = body.getChild("rear_left");
        this.rearRight = body.getChild("rear_right");
        this.tail = body.getChild("tail");
        this.tailTip = tail.getChild("tail_tip");
        this.spines = new ModelPart[] {
                body.getChild("spine_0"), body.getChild("spine_1"), body.getChild("spine_2"),
                body.getChild("spine_3"), body.getChild("spine_4"), body.getChild("spine_5"),
                body.getChild("spine_6")
        };
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition body = root.addOrReplaceChild("body",
                CubeListBuilder.create().texOffs(0, 0).addBox(-20.0F, -8.0F, -26.0F, 40.0F, 20.0F, 52.0F)
                        .texOffs(0, 60).addBox(-21.0F, -7.0F, -25.0F, 42.0F, 17.0F, 24.0F)
                        .texOffs(80, 60).addBox(-19.0F, -6.0F, 3.0F, 38.0F, 15.0F, 22.0F),
                PartPose.offset(0.0F, 9.0F, 0.0F));

        body.addOrReplaceChild("neck",
                CubeListBuilder.create().texOffs(100, 0).addBox(-11.0F, -7.0F, -28.0F, 22.0F, 14.0F, 16.0F),
                PartPose.ZERO);

        PartDefinition head = body.addOrReplaceChild("head",
                CubeListBuilder.create().texOffs(100, 32).addBox(-9.0F, -7.0F, -10.0F, 18.0F, 13.0F, 16.0F)
                        .texOffs(144, 32).addBox(-7.0F, -2.0F, -17.0F, 14.0F, 7.0F, 10.0F)
                        .texOffs(144, 52).addBox(-6.0F, 3.0F, -15.0F, 12.0F, 3.0F, 10.0F),
                PartPose.offset(0.0F, -5.0F, -20.0F));
        head.addOrReplaceChild("horn_left",
                CubeListBuilder.create().texOffs(180, 0).addBox(-3.0F, -5.0F, -3.0F, 6.0F, 5.0F, 6.0F)
                        .texOffs(194, 0).addBox(-2.0F, -10.0F, -2.0F, 4.0F, 5.0F, 4.0F)
                        .texOffs(204, 0).addBox(-1.0F, -14.0F, -1.0F, 2.0F, 4.0F, 2.0F),
                PartPose.offsetAndRotation(-7.5F, -2.0F, -4.0F, -0.25F, 0.0F, -0.38F));
        head.addOrReplaceChild("horn_right",
                CubeListBuilder.create().texOffs(216, 0).addBox(-3.0F, -5.0F, -3.0F, 6.0F, 5.0F, 6.0F)
                        .texOffs(230, 0).addBox(-2.0F, -10.0F, -2.0F, 4.0F, 5.0F, 4.0F)
                        .texOffs(240, 0).addBox(-1.0F, -14.0F, -1.0F, 2.0F, 4.0F, 2.0F),
                PartPose.offsetAndRotation(7.5F, -2.0F, -4.0F, -0.25F, 0.0F, 0.38F));

        addLeg(body, "front_left", 0, 96, -17.0F, 2.0F, -16.0F, true);
        addLeg(body, "front_right", 40, 96, 17.0F, 2.0F, -16.0F, false);
        addLeg(body, "rear_left", 80, 96, -17.0F, 2.0F, 14.0F, true);
        addLeg(body, "rear_right", 120, 96, 17.0F, 2.0F, 14.0F, false);

        PartDefinition tail = body.addOrReplaceChild("tail",
                CubeListBuilder.create().texOffs(0, 140).addBox(-7.0F, -6.0F, 0.0F, 14.0F, 12.0F, 18.0F),
                PartPose.offset(0.0F, 1.0F, 18.0F));
        tail.addOrReplaceChild("tail_tip",
                CubeListBuilder.create().texOffs(64, 140).addBox(-5.0F, -4.0F, 0.0F, 10.0F, 8.0F, 17.0F)
                        .texOffs(104, 140).addBox(-3.0F, -2.0F, 14.0F, 6.0F, 4.0F, 8.0F),
                PartPose.offset(0.0F, 0.0F, 16.0F));

        addCrystal(body, "spine_0", 0, -10.0F, -16.0F, 18, -0.22F);
        addCrystal(body, "spine_1", 24, 7.0F, -13.0F, 22, 0.18F);
        addCrystal(body, "spine_2", 48, -3.0F, -7.0F, 18, -0.12F);
        addCrystal(body, "spine_3", 72, 8.0F, -1.0F, 23, 0.22F);
        addCrystal(body, "spine_4", 96, -5.0F, 5.0F, 18, -0.14F);
        addCrystal(body, "spine_5", 120, 5.0F, 11.0F, 15, 0.19F);
        addCrystal(body, "spine_6", 144, 0.0F, 17.0F, 13, 0.0F);
        body.addOrReplaceChild("shoulder_crystal_left",
                CubeListBuilder.create().texOffs(176, 100).addBox(-3.0F, -13.0F, -3.0F, 6.0F, 13.0F, 6.0F),
                PartPose.offsetAndRotation(-14.0F, -4.0F, -13.0F, 0.12F, 0.0F, -0.62F));
        body.addOrReplaceChild("shoulder_crystal_right",
                CubeListBuilder.create().texOffs(200, 100).addBox(-3.0F, -13.0F, -3.0F, 6.0F, 13.0F, 6.0F),
                PartPose.offsetAndRotation(14.0F, -4.0F, -13.0F, 0.12F, 0.0F, 0.62F));
        return LayerDefinition.create(mesh, 256, 256);
    }

    private static void addLeg(PartDefinition body, String name, int u, int v,
                               float x, float y, float z, boolean left) {
        PartDefinition leg = body.addOrReplaceChild(name,
                CubeListBuilder.create().texOffs(u, v).addBox(-7.0F, -1.0F, -6.5F, 14.0F, 13.0F, 13.0F),
                PartPose.offset(x, y, z));
        leg.addOrReplaceChild("paw",
                CubeListBuilder.create().texOffs(u, v + 32).addBox(-7.5F, 0.0F, -8.0F, 15.0F, 3.0F, 15.0F),
                PartPose.offset(0.0F, 11.0F, -1.0F));
    }

    private static void addCrystal(PartDefinition body, String name, int u,
                                   float x, float z, int height, float lean) {
        body.addOrReplaceChild(name,
                CubeListBuilder.create()
                        .texOffs(u, 176).addBox(-3.5F, -height * 0.42F, -3.8F,
                                7.0F, height * 0.42F, 7.6F)
                        .texOffs(u + 8, 176).addBox(-2.4F, -height * 0.78F, -2.8F,
                                4.8F, height * 0.36F, 5.6F)
                        .texOffs(u + 14, 176).addBox(-1.1F, -height, -1.5F,
                                2.2F, height * 0.25F, 3.0F),
                PartPose.offsetAndRotation(x, -7.0F, z, 0.0F, 0.0F, lean));
    }

    public static LayerDefinition createGlowLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create(), PartPose.offset(0.0F, 9.0F, 0.0F));
        body.addOrReplaceChild("core_glow",
                CubeListBuilder.create().texOffs(200, 0).addBox(-6.5F, -6.0F, -27.2F, 13.0F, 12.0F, 2.5F),
                PartPose.ZERO);
        PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create(), PartPose.offset(0.0F, -5.0F, -20.0F));
        head.addOrReplaceChild("eye_left",
                CubeListBuilder.create().texOffs(200, 28).addBox(-9.5F, -4.5F, -12.2F, 3.5F, 3.0F, 1.4F),
                PartPose.ZERO);
        head.addOrReplaceChild("eye_right",
                CubeListBuilder.create().texOffs(200, 28).addBox(6.0F, -4.5F, -12.2F, 3.5F, 3.0F, 1.4F),
                PartPose.ZERO);
        head.addOrReplaceChild("mouth_glow",
                CubeListBuilder.create().texOffs(200, 44).addBox(-4.0F, 2.5F, -17.8F, 8.0F, 1.2F, 1.0F),
                PartPose.ZERO);

        addGlowLeg(body, "front_left", -17.0F, 2.0F, -16.0F);
        addGlowLeg(body, "front_right", 17.0F, 2.0F, -16.0F);
        addGlowLeg(body, "rear_left", -17.0F, 2.0F, 14.0F);
        addGlowLeg(body, "rear_right", 17.0F, 2.0F, 14.0F);

        PartDefinition tail = body.addOrReplaceChild("tail", CubeListBuilder.create(), PartPose.offset(0.0F, 1.0F, 18.0F));
        tail.addOrReplaceChild("tail_tip", CubeListBuilder.create().texOffs(224, 44)
                .addBox(-1.5F, -3.0F, 1.0F, 3.0F, 6.0F, 17.0F), PartPose.offset(0.0F, 0.0F, 16.0F));

        addGlowCrystal(body, "spine_0", -10.0F, -16.0F, 16, -0.22F);
        addGlowCrystal(body, "spine_1", 7.0F, -13.0F, 20, 0.18F);
        addGlowCrystal(body, "spine_2", -3.0F, -7.0F, 16, -0.12F);
        addGlowCrystal(body, "spine_3", 8.0F, -1.0F, 21, 0.22F);
        addGlowCrystal(body, "spine_4", -5.0F, 5.0F, 16, -0.14F);
        addGlowCrystal(body, "spine_5", 5.0F, 11.0F, 13, 0.19F);
        addGlowCrystal(body, "spine_6", 0.0F, 17.0F, 11, 0.0F);
        return LayerDefinition.create(mesh, 256, 256);
    }

    private static void addGlowLeg(PartDefinition body, String name, float x, float y, float z) {
        PartDefinition leg = body.addOrReplaceChild(name, CubeListBuilder.create(), PartPose.offset(x, y, z));
        leg.addOrReplaceChild("leg_vein", CubeListBuilder.create().texOffs(208, 80)
                .addBox(-1.4F, 1.0F, -6.8F, 2.8F, 9.0F, 0.8F), PartPose.ZERO);
        leg.addOrReplaceChild("paw", CubeListBuilder.create().texOffs(208, 48)
                .addBox(-7.5F, 0.0F, -8.0F, 15.0F, 3.0F, 15.0F), PartPose.offset(0.0F, 11.0F, -1.0F));
    }

    private static void addGlowCrystal(PartDefinition body, String name, float x, float z,
                                       int height, float lean) {
        body.addOrReplaceChild(name, CubeListBuilder.create()
                .texOffs(176, 64).addBox(-3.2F, -height * 0.42F, -3.4F,
                        6.4F, height * 0.42F, 6.8F)
                .texOffs(184, 64).addBox(-2.2F, -height * 0.78F, -2.4F,
                        4.4F, height * 0.36F, 4.8F)
                .texOffs(190, 64).addBox(-1.0F, -height, -1.3F,
                        2.0F, height * 0.25F, 2.6F),
                PartPose.offsetAndRotation(x, -7.0F, z, 0.0F, 0.0F, lean));
    }

    @Override
    public void setupAnim(MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,
                          float ageInTicks, float netHeadYaw, float headPitch) {
        float gait = Mth.sin(limbSwing * 0.42F) * limbSwingAmount * 0.72F;
        this.body.xRot = Mth.sin(ageInTicks * 0.065F) * 0.018F;
        this.body.yRot = 0.0F;
        this.body.zRot = 0.0F;
        this.head.xRot = headPitch * Mth.DEG_TO_RAD * 0.42F;
        this.head.yRot = netHeadYaw * Mth.DEG_TO_RAD * 0.42F;
        this.head.zRot = 0.0F;
        this.frontLeft.xRot = gait;
        this.frontRight.xRot = -gait;
        this.rearLeft.xRot = -gait;
        this.rearRight.xRot = gait;
        this.frontLeft.yRot = this.frontRight.yRot = 0.0F;
        this.rearLeft.yRot = this.rearRight.yRot = 0.0F;
        this.frontLeft.zRot = this.frontRight.zRot = 0.0F;
        this.rearLeft.zRot = this.rearRight.zRot = 0.0F;
        this.tail.xRot = Mth.sin(ageInTicks * 0.06F) * 0.08F;
        this.tail.yRot = Mth.sin(ageInTicks * 0.045F) * 0.12F;
        this.tail.zRot = 0.0F;
        this.tailTip.xRot = Mth.sin(ageInTicks * 0.08F) * 0.09F;
        this.tailTip.yRot = Mth.sin(ageInTicks * 0.065F + 0.7F) * 0.16F;
        this.tailTip.zRot = 0.0F;
        for (int i = 0; i < this.spines.length; i++) {
            this.spines[i].zRot = Mth.sin(ageInTicks * 0.045F + i * 0.74F) * 0.035F;
        }

        int state = entity.getAttackState();
        int ticks = entity.getAttackTicks();
        if (state == MutagenkolossEntity.ATTACK_STOMP) {
            if (ticks > 13) {
                this.body.xRot = -0.14F;
                this.head.xRot -= 0.22F;
                this.frontLeft.xRot = -0.52F;
                this.frontRight.xRot = -0.52F;
            } else {
                this.body.xRot = 0.27F;
                this.head.xRot = 0.26F;
                this.frontLeft.xRot = 0.72F;
                this.frontRight.xRot = 0.72F;
            }
        } else if (state == MutagenkolossEntity.ATTACK_BREATH) {
            this.head.xRot = -0.34F + Mth.sin(ageInTicks * 0.28F) * 0.04F;
            this.head.yRot *= 0.55F;
            this.body.xRot = -0.04F;
            this.tailTip.yRot += Mth.sin(ageInTicks * 0.22F) * 0.08F;
        } else if (state == MutagenkolossEntity.ATTACK_AWAKENING) {
            float pulse = Mth.sin(ageInTicks * 0.5F) * 0.06F;
            this.body.xRot = -0.16F + pulse;
            this.head.xRot = -0.45F + pulse;
            this.frontLeft.xRot = -0.42F;
            this.frontRight.xRot = -0.42F;
            this.rearLeft.xRot = 0.24F;
            this.rearRight.xRot = 0.24F;
            for (ModelPart spine : this.spines) spine.zRot *= 1.9F;
        }
    }

    @Override
    public void renderToBuffer(PoseStack poseStack, VertexConsumer vertexConsumer, int packedLight,
                               int packedOverlay, float red, float green, float blue, float alpha) {
        this.root.render(poseStack, vertexConsumer, packedLight, packedOverlay, red, green, blue, alpha);
    }
}
""")

write("src/main/java/de/sporenwerk/client/MutagenkolossRenderer.java", r"""
package de.sporenwerk.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import de.sporenwerk.Sporenwerk;
import de.sporenwerk.entity.MutagenkolossEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;

public final class MutagenkolossRenderer extends MobRenderer<MutagenkolossEntity, MutagenkolossModel> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(Sporenwerk.MODID, "textures/entity/mutagenkoloss.png");
    private static final ResourceLocation GLOW_TEXTURE =
            new ResourceLocation(Sporenwerk.MODID, "textures/entity/mutagenkoloss_glow.png");

    public MutagenkolossRenderer(EntityRendererProvider.Context context) {
        super(context, new MutagenkolossModel(context.bakeLayer(MutagenkolossModel.LAYER_LOCATION)), 1.35F);
        this.addLayer(new GlowLayer(this, context));
    }

    @Override
    public ResourceLocation getTextureLocation(MutagenkolossEntity entity) {
        return TEXTURE;
    }

    @Override
    protected void scale(MutagenkolossEntity entity, PoseStack poseStack, float partialTick) {
        poseStack.scale(1.22F, 1.22F, 1.22F);
    }

    private static final class GlowLayer extends RenderLayer<MutagenkolossEntity, MutagenkolossModel> {
        private final MutagenkolossModel glowModel;

        private GlowLayer(MutagenkolossRenderer parent, EntityRendererProvider.Context context) {
            super(parent);
            this.glowModel = new MutagenkolossModel(context.bakeLayer(MutagenkolossModel.GLOW_LAYER_LOCATION));
        }

        @Override
        public void render(PoseStack poseStack, MultiBufferSource buffer, int packedLight,
                           MutagenkolossEntity entity, float limbSwing, float limbSwingAmount,
                           float partialTick, float ageInTicks, float netHeadYaw, float headPitch) {
            this.glowModel.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);
            VertexConsumer vertex = buffer.getBuffer(RenderType.eyes(GLOW_TEXTURE));
            this.glowModel.renderToBuffer(poseStack, vertex, 0xF000F0, OverlayTexture.NO_OVERLAY,
                    1.0F, 1.0F, 1.0F, 1.0F);
        }
    }
}
""")

# Register the renderer and both baked model layers, then add a custom, emissive-free base texture plus an eyes pass.
client_path = SRC / "client/ClientModEvents.java"
client = client_path.read_text(encoding="utf-8")
add_import(client_path, "import de.sporenwerk.client.KristallpirscherRenderer;",
           "import de.sporenwerk.client.MutagenkolossRenderer;\nimport de.sporenwerk.client.MutagenkolossModel;\nimport net.minecraftforge.client.event.EntityRenderersEvent;",
           "boss renderer/model imports")
client = client_path.read_text(encoding="utf-8")
if "ModEntities.MUTAGENKOLOSS.get(), MutagenkolossRenderer::new" not in client:
    anchor = "event.registerEntityRenderer(ModEntities.KRISTALLPIRSCHER.get(), KristallpirscherRenderer::new);"
    require(anchor in client, "could not locate Crystal Stalker renderer registration")
    client = client.replace(anchor, anchor + "\n        event.registerEntityRenderer(ModEntities.MUTAGENKOLOSS.get(), MutagenkolossRenderer::new);", 1)
client_path.write_text(client, encoding="utf-8")
append_before_class_end(client_path, '''
    @SubscribeEvent
    public static void registerMutagenkolossLayerDefinitions(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(MutagenkolossModel.LAYER_LOCATION, MutagenkolossModel::createBodyLayer);
        event.registerLayerDefinition(MutagenkolossModel.GLOW_LAYER_LOCATION, MutagenkolossModel::createGlowLayer);
    }
''', "registerMutagenkolossLayerDefinitions", "boss model layers")

# Add a boss-heart item as the guaranteed victory drop and a Survival-facing spawn egg.
items_path = SRC / "registry/ModItems.java"
items = items_path.read_text(encoding="utf-8")
if "MUTAGENKOLOSS_HERZ" not in items:
    marker = "public static final RegistryObject<Item> KRISTALLPIRSCHER_SPAWN_EGG"
    lines = items.splitlines()
    for idx, line in enumerate(lines):
        if marker in line:
            lines.insert(idx + 1, '    public static final RegistryObject<Item> MUTAGENKOLOSS_HERZ = ITEMS.register("mutagenkoloss_herz", () -> new Item(new Item.Properties().stacksTo(1)));')
            lines.insert(idx + 2, '    public static final RegistryObject<Item> MUTAGENKOLOSS_SPAWN_EGG = ITEMS.register("mutagenkoloss_spawn_egg", () -> new net.minecraftforge.common.ForgeSpawnEggItem(ModEntities.MUTAGENKOLOSS, 0x101A30, 0x39E8FF, new Item.Properties()));')
            break
    else:
        raise SystemExit("Cannot add Mutagen Colossus: Kristallpirscher spawn egg declaration was not found")
    items_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
items = items_path.read_text(encoding="utf-8")
if "MUTAGENKOLOSS_HERZ" not in items or "MUTAGENKOLOSS_SPAWN_EGG" not in items:
    raise SystemExit("Mutagen Colossus rewards/items are missing")

creative_path = SRC / "registry/ModCreativeTabs.java"
creative = creative_path.read_text(encoding="utf-8")
anchor = "output.accept(ModItems.KRISTALLPIRSCHER_SPAWN_EGG.get());"
addition = anchor + "\n                        output.accept(ModItems.MUTAGENKOLOSS_HERZ.get());\n                        output.accept(ModItems.MUTAGENKOLOSS_SPAWN_EGG.get());"
if addition not in creative:
    require(anchor in creative, "could not find Crystal Stalker creative item")
    creative_path.write_text(creative.replace(anchor, addition, 1), encoding="utf-8")

write("src/main/resources/assets/sporenwerk/models/item/mutagenkoloss_herz.json", """
{
  "parent": "minecraft:item/generated",
  "textures": { "layer0": "sporenwerk:item/mutagenkoloss_herz" }
}
""")
write("src/main/resources/assets/sporenwerk/models/item/mutagenkoloss_spawn_egg.json", """
{ "parent": "minecraft:item/template_spawn_egg" }
""")

# Intentional summon ritual: crouch-right-click Tier-III soil while holding at least three core crystals.
write("src/main/java/de/sporenwerk/entity/MutagenkolossRitual.java", r"""
package de.sporenwerk.entity;

import de.sporenwerk.Sporenwerk;
import de.sporenwerk.block.InfestedTerrainBlock;
import de.sporenwerk.registry.ModBlocks;
import de.sporenwerk.registry.ModEntities;
import de.sporenwerk.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = Sporenwerk.MODID)
public final class MutagenkolossRitual {
    private MutagenkolossRitual() {}

    @SubscribeEvent
    public static void summonOnHighMutagenSoil(PlayerInteractEvent.RightClickBlock event) {
        if (event.getLevel().isClientSide || !(event.getEntity() instanceof ServerPlayer player)
                || !player.isShiftKeyDown()) return;
        ItemStack held = player.getItemInHand(event.getHand());
        if (!held.is(ModItems.MUTAGENKERNKRISTALL.get()) || held.getCount() < 3) return;

        BlockPos pos = event.getPos();
        BlockState soil = event.getLevel().getBlockState(pos);
        if (!soil.is(ModBlocks.MUTAGEN_BODEN.get())
                || !soil.hasProperty(InfestedTerrainBlock.MUTAGEN_LEVEL)
                || soil.getValue(InfestedTerrainBlock.MUTAGEN_LEVEL) < 3) return;

        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        if (!(event.getLevel() instanceof ServerLevel level)) return;
        MutagenkolossEntity boss = ModEntities.MUTAGENKOLOSS.get().create(level);
        if (boss == null) return;
        boss.moveTo(pos.getX() + 0.5D, pos.getY() + 1.0D, pos.getZ() + 0.5D,
                player.getYRot(), 0.0F);
        if (!level.noCollision(boss)) {
            boss.discard();
            player.displayClientMessage(Component.translatable("message.sporenwerk.mutagenkoloss.blocked"), true);
            return;
        }
        if (!level.addFreshEntity(boss)) {
            boss.discard();
            return;
        }
        if (!player.getAbilities().instabuild) held.shrink(3);
        level.playSound(null, pos, SoundEvents.RESPAWN_ANCHOR_CHARGE,
                SoundSource.BLOCKS, 2.0F, 0.55F);
        level.sendParticles(ParticleTypes.DRAGON_BREATH,
                pos.getX() + 0.5D, pos.getY() + 1.3D, pos.getZ() + 0.5D,
                70, 1.8D, 1.1D, 1.8D, 0.07D);
        player.displayClientMessage(Component.translatable("message.sporenwerk.mutagenkoloss.summoned"), true);
    }
}
""")

# Pixel-art textures: deep obsidian armor, fractured violet/cyan crystal plates, orange energy nodes,
# and a separate transparent atlas for full-bright emissive features.
def make_colossus_texture():
    rng = random.Random(1550)
    image = Image.new("RGBA", (256, 256), (17, 23, 36, 255))
    draw = ImageDraw.Draw(image)
    palette = [(24, 31, 48, 255), (35, 42, 64, 255), (46, 43, 72, 255),
               (39, 55, 75, 255), (29, 39, 59, 255), (63, 43, 79, 255)]
    for y in range(0, 256, 4):
        for x in range(0, 256, 4):
            c = rng.choice(palette)
            draw.rectangle((x, y, x + 3, y + 3), fill=c)
    # Large interlocking armor scales with hard 90-degree pixels, not smooth gradients.
    for row in range(8):
        for col in range(10):
            x, y = 4 + col * 25, 4 + row * 29
            tone = rng.choice([(37, 46, 68, 255), (51, 48, 78, 255), (28, 40, 60, 255), (48, 57, 82, 255)])
            draw.polygon([(x, y + 4), (x + 7, y), (x + 21, y + 2),
                          (x + 24, y + 11), (x + 16, y + 19), (x + 3, y + 16)], fill=tone)
            draw.line([(x + 3, y + 16), (x + 9, y + 8), (x + 20, y + 11)],
                      fill=(83, 97, 139, 255), width=2)
            if (row + col) % 3 == 0:
                draw.line([(x + 16, y + 13), (x + 20, y + 18), (x + 18, y + 23)],
                          fill=(58, 146, 207, 255), width=2)
    # Cyan crystal facets concentrated across the spine and claw UV areas.
    for x, y, scale in ((8, 184, 1), (34, 190, 2), (63, 184, 1), (91, 192, 2),
                        (117, 186, 1), (145, 194, 2), (173, 188, 1), (201, 193, 2),
                        (226, 180, 1), (18, 224, 1), (75, 228, 1), (135, 224, 1),
                        (193, 229, 1), (232, 217, 1)):
        w = 6 * scale
        h = 17 * scale
        draw.polygon([(x, y + h), (x + w // 2, y), (x + w, y + h - 4),
                      (x + w - 2, y + h), (x + 2, y + h)], fill=(27, 106, 147, 255))
        draw.polygon([(x + 1, y + h - 2), (x + w // 2, y + 2),
                      (x + w // 2 + 1, y + h - 4)], fill=(71, 207, 228, 255))
        draw.line([(x + w // 2, y + 3), (x + w // 2, y + h - 5)],
                  fill=(172, 252, 255, 255), width=1)
        draw.point((x + w - 1, y + h - 5), fill=(37, 145, 197, 255))
    # Magenta-violet crystal faults break up the dark armor, matching the high-mutagen palette.
    for x, y in ((14, 61), (53, 88), (88, 63), (126, 94), (169, 79),
                 (205, 85), (232, 63), (29, 169), (80, 150), (177, 145), (224, 164)):
        draw.line([(x, y), (x + 4, y - 2), (x + 7, y + 3), (x + 4, y + 7)],
                  fill=(116, 54, 191, 255), width=2)
        draw.line([(x + 2, y), (x + 5, y + 3)], fill=(209, 91, 242, 255), width=1)
    # Bioluminescent seams and several orange, volatile nodules.
    for x, y in ((18, 35), (36, 50), (58, 29), (76, 43), (95, 31), (112, 48),
                 (141, 34), (165, 48), (184, 31), (211, 43), (236, 28),
                 (29, 115), (69, 132), (109, 112), (157, 127), (205, 112)):
        draw.line([(x, y), (x + 5, y + 4), (x + 2, y + 9), (x + 8, y + 15)],
                  fill=(38, 132, 190, 255), width=2)
        draw.line([(x + 1, y + 1), (x + 4, y + 5), (x + 3, y + 8)],
                  fill=(67, 227, 255, 255), width=1)
    for x, y in ((42, 37), (104, 52), (151, 39), (197, 62), (220, 112),
                 (49, 144), (131, 157), (216, 151)):
        draw.rectangle((x, y, x + 4, y + 4), fill=(255, 126, 35, 255))
        draw.rectangle((x + 1, y + 1, x + 3, y + 3), fill=(255, 207, 86, 255))
        draw.point((x + 2, y + 2), fill=(255, 245, 196, 255))
    # Distinct bright eyes, throat core and crystal crown marks in the UV regions used by the model.
    draw.rectangle((142, 41, 151, 48), fill=(9, 24, 48, 255))
    draw.rectangle((144, 43, 148, 46), fill=(31, 174, 238, 255))
    draw.rectangle((145, 44, 147, 45), fill=(231, 255, 255, 255))
    draw.rectangle((158, 41, 167, 48), fill=(9, 24, 48, 255))
    draw.rectangle((160, 43, 164, 46), fill=(31, 174, 238, 255))
    draw.rectangle((161, 44, 163, 45), fill=(231, 255, 255, 255))
    draw.polygon([(105, 83), (115, 57), (122, 82), (118, 91)], fill=(27, 126, 171, 255))
    draw.polygon([(108, 81), (115, 61), (116, 82)], fill=(106, 236, 255, 255))
    return image

def make_colossus_glow():
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((198, 0, 225, 21), fill=(13, 174, 255, 255))
    draw.rectangle((202, 3, 220, 18), fill=(53, 236, 255, 255))
    draw.rectangle((207, 6, 216, 15), fill=(225, 255, 255, 255))
    draw.rectangle((198, 26, 227, 41), fill=(35, 208, 255, 255))
    draw.rectangle((202, 29, 223, 38), fill=(142, 250, 255, 255))
    draw.rectangle((198, 42, 224, 52), fill=(14, 109, 255, 255))
    draw.rectangle((201, 45, 221, 49), fill=(102, 218, 255, 255))
    draw.rectangle((174, 62, 225, 100), fill=(18, 148, 221, 255))
    for y in range(64, 98, 4):
        draw.line([(177, y), (221, y + 2)], fill=(95, 233, 255, 255), width=2)
    draw.rectangle((204, 104, 226, 126), fill=(30, 168, 255, 255))
    # Brighter veins/panels deliberately cover the UV rectangles used by the tapered spine overlay.
    for idx, (x, y) in enumerate(((176, 64), (184, 68), (190, 72), (176, 82),
                                  (184, 86), (190, 90))):
        draw.polygon([(x, y + 15), (x + 3, y), (x + 6, y + 15)],
                     fill=(28, 196, 255, 255))
        draw.line([(x + 3, y + 2), (x + 3, y + 12)],
                  fill=(200, 255, 255, 255), width=1)
    draw.rectangle((208, 80, 212, 91), fill=(22, 154, 255, 255))
    draw.rectangle((209, 81, 210, 89), fill=(143, 251, 255, 255))
    draw.rectangle((208, 48, 223, 51), fill=(20, 172, 255, 255))
    draw.rectangle((208, 48, 232, 72), fill=(38, 194, 255, 255))
    draw.rectangle((224, 44, 252, 72), fill=(20, 154, 244, 255))
    draw.rectangle((228, 47, 248, 68), fill=(111, 241, 255, 255))
    return image

texture_path = ASSETS / "textures/entity/mutagenkoloss.png"
texture_path.parent.mkdir(parents=True, exist_ok=True)
make_colossus_texture().save(texture_path, optimize=True)
glow_path = ASSETS / "textures/entity/mutagenkoloss_glow.png"
make_colossus_glow().save(glow_path, optimize=True)

def make_heart_icon():
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.polygon([(2, 5), (2, 3), (5, 1), (7, 3), (9, 1), (13, 2),
                  (15, 5), (13, 9), (8, 15), (3, 9)], fill=(31, 27, 57, 255))
    draw.polygon([(3, 4), (6, 2), (8, 4), (10, 2), (13, 4), (13, 7),
                  (8, 13), (4, 8)], fill=(38, 144, 209, 255))
    draw.polygon([(5, 4), (7, 3), (8, 5), (11, 3), (12, 5), (8, 10)],
                 fill=(68, 229, 255, 255))
    draw.rectangle((6, 6, 7, 8), fill=(232, 255, 255, 255))
    draw.point((4, 5), fill=(151, 241, 255, 255))
    return image

heart_path = ASSETS / "textures/item/mutagenkoloss_herz.png"
heart_path.parent.mkdir(parents=True, exist_ok=True)
make_heart_icon().save(heart_path, optimize=True)

# Victory reward and a dedicated advancement ensure the boss has a lasting progression payoff.
write("src/main/resources/data/sporenwerk/loot_tables/entities/mutagenkoloss.json", """
{
  "type": "minecraft:entity",
  "pools": [
    {
      "rolls": 1.0,
      "entries": [
        {
          "type": "minecraft:item",
          "name": "sporenwerk:mutagenkoloss_herz"
        }
      ]
    },
    {
      "rolls": 1.0,
      "entries": [
        {
          "type": "minecraft:item",
          "name": "sporenwerk:mutagenkernkristall",
          "functions": [
            { "function": "minecraft:set_count", "count": { "min": 3.0, "max": 6.0 } }
          ]
        }
      ]
    },
    {
      "rolls": 1.0,
      "entries": [
        {
          "type": "minecraft:item",
          "name": "sporenwerk:pflanzenreste",
          "functions": [
            { "function": "minecraft:set_count", "count": { "min": 5.0, "max": 10.0 } }
          ]
        }
      ]
    }
  ]
}
""")
write("src/main/resources/data/sporenwerk/advancements/monsters/mutagenkoloss.json", """
{
  "parent": "minecraft:adventure/kill_a_mob",
  "display": {
    "icon": { "item": "sporenwerk:mutagenkoloss_herz" },
    "title": { "translate": "advancements.sporenwerk.mutagenkoloss.title" },
    "description": { "translate": "advancements.sporenwerk.mutagenkoloss.description" },
    "frame": "challenge",
    "show_toast": true,
    "announce_to_chat": true,
    "hidden": false
  },
  "criteria": {
    "defeat_mutagenkoloss": {
      "trigger": "minecraft:player_killed_entity",
      "conditions": {
        "entity": { "type": "sporenwerk:mutagenkoloss" }
      }
    }
  },
  "requirements": [["defeat_mutagenkoloss"]]
}
""")

for locale, entries in {
    "de_de.json": {
        "entity.sporenwerk.mutagenkoloss": "Kristallkoloss",
        "item.sporenwerk.mutagenkoloss_spawn_egg": "Kristallkoloss-Spawn-Ei",
        "item.sporenwerk.mutagenkoloss_herz": "Herz des Kristallkolosses",
        "message.sporenwerk.mutagenkoloss.summoned": "Der Kristallkoloss erwacht. Weiche seinen angekündigten Resonanzangriffen aus!",
        "message.sporenwerk.mutagenkoloss.blocked": "Zu wenig Platz: Der Kristallkoloss konnte nicht sicher erscheinen. Es wurde nichts verbraucht.",
        "tooltip.sporenwerk.mutagenkoloss_herz": "Ein verdichteter Mutagenkern. Sein Echo pulsiert noch.",
        "tooltip.sporenwerk.mutagenkoloss_ritual": "Geduckt mit 3 Mutagenkernkristallen auf Mutagenboden Stufe III rechtsklicken.",
        "advancements.sporenwerk.mutagenkoloss.title": "Herz des Hochmutagens",
        "advancements.sporenwerk.mutagenkoloss.description": "Besiege den Kristallkoloss und sichere seinen Kern."
    },
    "en_us.json": {
        "entity.sporenwerk.mutagenkoloss": "Crystal Colossus",
        "item.sporenwerk.mutagenkoloss_spawn_egg": "Crystal Colossus Spawn Egg",
        "item.sporenwerk.mutagenkoloss_herz": "Crystal Colossus Heart",
        "message.sporenwerk.mutagenkoloss.summoned": "The Crystal Colossus awakens. Dodge its telegraphed resonance attacks!",
        "message.sporenwerk.mutagenkoloss.blocked": "Not enough room: the Crystal Colossus could not spawn safely. Nothing was consumed.",
        "tooltip.sporenwerk.mutagenkoloss_herz": "A condensed Mutagen core. Its echo still pulses.",
        "tooltip.sporenwerk.mutagenkoloss_ritual": "Crouch-right-click Tier III Mutagen soil with 3 Mutagen Core Crystals.",
        "advancements.sporenwerk.mutagenkoloss.title": "Heart of High Mutagen",
        "advancements.sporenwerk.mutagenkoloss.description": "Defeat the Crystal Colossus and claim its core."
    }
}.items():
    lang_path = ASSETS / "lang" / locale
    lang = json.loads(lang_path.read_text(encoding="utf-8"))
    lang.update(entries)
    lang_path.write_text(json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Keep QA preview visible and make it reserve space for the 256x256 boss texture and emissive atlas.
preview_path = ROOT / "tools/make_art_preview.py"
preview = preview_path.read_text(encoding="utf-8")
if "MUTAGENKOLOSS PIXEL ART" not in preview:
    preview = preview.replace("W, H = 1400, 1360", "W, H = 1400, 1600")
    anchor = "canvas.save(out, optimize=True)"
    require(anchor in preview, "could not locate art preview output")
    preview = preview.replace(anchor, """
panel(24, 1360, 1352, 215, "MUTAGENKOLOSS PIXEL ART — ARMORED BODY AND EMISSIVE CRYSTALS")
paste_scaled(assets / "textures/entity" / "mutagenkoloss.png", 45, 1390, 190, 175, "Koloss 256x256")
paste_scaled(assets / "textures/entity" / "mutagenkoloss_glow.png", 265, 1390, 190, 175, "Glow atlas")
canvas.save(out, optimize=True)""", 1)
    preview_path.write_text(preview, encoding="utf-8")

# Update all version-sensitive regression contracts, without erasing the release history.
for test_path in (ROOT / "tools").glob("test_*.py"):
    source = test_path.read_text(encoding="utf-8")
    updated = source.replace("Aktueller Entwicklungsstand: 1.54.0",
                             "Aktueller Entwicklungsstand: 1.55.0")
    updated = updated.replace("Aktueller Entwicklungsstand: 1.55.0",
                              "Aktueller Entwicklungsstand: 1.56.0")
    if "build.gradle" in source:
        updated = updated.replace(r"1\.54\.0", r"1\.55\.0")
        updated = updated.replace(r"1\.55\.0", r"1\.56\.0")
        updated = updated.replace("artifact must be version 1.54.0",
                                  "artifact must be version 1.55.0")
        updated = updated.replace("artifact must be version 1.55.0",
                                  "artifact must be version 1.56.0")
    updated = updated.replace(
        '"Version 1.54.0" in readme and "Version 1.53.0" in readme',
        '"Version 1.55.0" in readme and "Version 1.54.0" in readme')
    updated = updated.replace(
        '"Version 1.55.0" in readme and "Version 1.54.0" in readme',
        '"Version 1.56.0" in readme and "Version 1.55.0" in readme')
    if updated != source:
        test_path.write_text(updated, encoding="utf-8")

build_path = ROOT / "build.gradle"
build, count = re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]",
                       "version = '1.56.0'", build_path.read_text(encoding="utf-8"), count=1)
require(count == 1, "could not advance Gradle artifact version to 1.56.0")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
legacy_section = """## Version 1.55.0 — Der Kristallkoloss erwacht

- **Eigener Boss statt umgefärbter Zombie:** Der Kristallkoloss verwendet ein separates vierbeiniges Modell mit massigem Panzerkörper, sieben Rückenstacheln, Hörnern, vier animierten Läufen und segmentiertem Kristallschwanz.
- **Leuchtende Kristalle:** Eine zweite, transparente Emissiv-Textur wird über einen Full-Bright-Eyes-Layer gerendert.
- **Prozedurale Animation und Kampf:** Laufbewegung, Schwanzpendel, angekündigter Stampfangriff, gerichteter Kristallatem, Bossleiste und eine zweite Phase ab 50 % Leben.
- **Survival-Beschwörung:** Geduckt mit drei Mutagenkernkristallen auf Mutagenboden Stufe III rechtsklicken. Bei blockiertem Spawn wird nichts verbraucht.
- **Sieg mit Belohnung:** Ein garantiertes Kristallkoloss-Herz, weitere Kernkristalle, Pflanzenreste und ein eigenes Challenge-Advancement.

"""
if "## Version 1.55.0 — Der Kristallkoloss erwacht" not in readme:
    legacy_marker = "## Version 1.54.0 — Blütenduft für den Kristallpirscher"
    legacy_index = readme.find(legacy_marker)
    require(legacy_index >= 0, "could not locate 1.54.0 release notes to preserve history")
    readme = readme[:legacy_index] + legacy_section + readme[legacy_index:]
section = """## Version 1.56.0 — Visuelle Überarbeitung des Kristallkolosses

- **Silhouette statt Kopf-im-Gras:** Der Panzerkörper wurde verbreitert und verlängert, die Kopfform verkleinert und die Schnauze klarer abgesetzt. Beine sind länger, weiter außen platziert und enden jetzt mit breiten, sichtbaren Klauenfüßen auf Bodenhöhe.
- **Tatsächliche Kristallspitzen:** Die sieben Rückenstacheln bestehen nun aus drei gestapelten, zunehmend schmalen Segmenten statt gleich breiten rechteckigen Säulen. Hörner laufen ebenfalls sichtbar zu.
- **Leuchten an den richtigen Stellen:** Die Full-Bright-Ebene deckt die Kristallsegmente über die passenden UV-Bereiche ab. Brustkern, Beinäder und Klauen erhalten deutlich größere, besser sichtbare Leuchtflächen.
- **Mehr Farbkontrast:** Die Rüstung behält den Obsidian-Look, bekommt aber lesbarere blaue Bruchadern, violette Kristallrisse und stärkere reflektierende Kanten.
- **Boss-Ritual und Angriffe bleiben erhalten:** Beschwörung mit drei Mutagenkernkristallen, Bossleiste, Stampfen, angekündigter Kristallatem und zweite Phase bleiben Teil desselben Bosses.
- **Zusätzliche Regressionen:** Die Tests prüfen jetzt ausdrücklich den größeren Panzerkörper, verlängerte Beine, dreistufige Kristallspitzen, Leuchtadern, JAR-Inhalt, Ressourcen und Serverstart.

Diese Änderung ist eine gezielte Modellkorrektur auf Grundlage des tatsächlichen Screenshots. Der CI-Build kann Geometrie, Ressourcen und Registrierung kontrollieren; ein erneuter manueller Client-Sichttest bleibt nötig, bevor wir das Aussehen als fertig bezeichnen.

"""
if "## Version 1.56.0 — Visuelle Überarbeitung des Kristallkolosses" not in readme:
    marker = "## Version 1.55.0 — Der Kristallkoloss erwacht"
    idx = readme.find(marker)
    require(idx >= 0, "could not locate 1.54.0 release notes to preserve history")
    readme = readme[:idx] + section + readme[idx:]
headline = "**Aktueller Entwicklungsstand: 1.56.0 — überarbeitete Kristallkoloss-Silhouette, Klauen und leuchtende Kristallspitzen.**"
headlines = [line for line in readme.splitlines() if "Aktueller Entwicklungsstand:" in line]
if headlines:
    readme = readme.replace(headlines[0], headline, 1)
else:
    readme = headline + "\n\n" + readme.lstrip()
focus_lines = [line for line in readme.splitlines() if line.startswith("## Aktueller Schwerpunkt — ")]
if focus_lines:
    readme = readme.replace(focus_lines[0], "## Aktueller Schwerpunkt — 1.56.0", 1)
else:
    readme = readme.replace(headline, headline + "\n\n## Aktueller Schwerpunkt — 1.56.0", 1)
readme_path.write_text(readme, encoding="utf-8")
print("Installed 1.56.0 Crystal Colossus visual correction: custom quadruped model, emissive crystal layer, synchronized attacks, two phases, Survival ritual and boss reward.")
