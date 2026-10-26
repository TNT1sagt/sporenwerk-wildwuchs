#!/usr/bin/env python3
"""1.103 physical field journal + Dämmerling crop warning rings. Server-only."""
from pathlib import Path
import re,json,sys
R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
J=R/"src/main/java/de/sporenwerk"
A=R/"src/main/resources/assets/sporenwerk"
ST=J/"block/MutagenFieldControlStationBlock.java"
M=J/"entity/DaemmerlingEntity.java"
def need(x,m):
    if not x:raise SystemExit("1.103 field journal: "+m)
def patch(path,a,b,label):
    s=path.read_text(encoding="utf-8")
    need(s.count(a)==1,label+" anchor count "+str(s.count(a)))
    path.write_text(s.replace(a,b,1),encoding="utf-8")
s=ST.read_text(encoding="utf-8")
for token in ("Survey s = survey(serverLevel, pos);",
              "s.highSoil()", "s.soil()", "s.crops()", "s.spreadNodes()",
              "s.cultivatedNodes()", "Items.COMPASS"):
    need(token in s,"existing station source required: "+token)
patch(ST,
"""        Survey s = survey(serverLevel, pos);
        // Optional survival diagnostics.""",
"""        Survey s = survey(serverLevel, pos);
        // A book carries its own history between stations, worlds and chests.
        if (hand == InteractionHand.MAIN_HAND
                && player.getItemInHand(hand).is(Items.WRITABLE_BOOK)) {
            updateFieldJournal(serverLevel, pos, player, s);
            return InteractionResult.CONSUME;
        }
        // Optional survival diagnostics.""",
"read-only survey dispatch")
journal="""
    /**
     * A physical journal with its own NBT baseline. Same dimension AND
     * station are required for meaningful deltas. Neither world nor player
     * persistent data are changed and no extra survey is ever performed.
     */
    private static void updateFieldJournal(ServerLevel level, BlockPos station,
                                           Player player, Survey survey) {
        net.minecraft.world.item.ItemStack book = player.getMainHandItem();
        net.minecraft.nbt.CompoundTag stored = book.getOrCreateTag().getCompound(
                "SporenwerkFieldJournal");
        String dimension = level.dimension().location().toString();
        boolean comparable = stored.contains("Dimension", 8)
                && dimension.equals(stored.getString("Dimension"))
                && stored.getLong("Station") == station.asLong();
        if (comparable) {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.journal_diff",
                    survey.soil() - stored.getInt("Soil"),
                    survey.highSoil() - stored.getInt("HighSoil"),
                    survey.crops() - stored.getInt("Crops"),
                    survey.spreadNodes() - stored.getInt("Spread"),
                    survey.cultivatedNodes() - stored.getInt("Cultivate"))
                    .withStyle(survey.spreadNodes() > stored.getInt("Spread")
                            ? ChatFormatting.RED : ChatFormatting.AQUA), false);
        } else {
            player.displayClientMessage(Component.translatable(
                    "message.sporenwerk.fieldstation.journal_baseline",
                    survey.soil(), survey.highSoil(), survey.crops(),
                    survey.spreadNodes(), survey.cultivatedNodes())
                    .withStyle(ChatFormatting.GREEN), false);
        }
        net.minecraft.nbt.CompoundTag fresh = new net.minecraft.nbt.CompoundTag();
        fresh.putString("Dimension", dimension);
        fresh.putLong("Station", station.asLong());
        fresh.putLong("GameTick", level.getGameTime());
        fresh.putInt("Soil", survey.soil());
        fresh.putInt("HighSoil", survey.highSoil());
        fresh.putInt("Crops", survey.crops());
        fresh.putInt("Spread", survey.spreadNodes());
        fresh.putInt("Cultivate", survey.cultivatedNodes());
        book.getOrCreateTag().put("SporenwerkFieldJournal", fresh);
        player.getInventory().setChanged();
        player.displayClientMessage(Component.translatable(
                "message.sporenwerk.fieldstation.journal_hint")
                .withStyle(ChatFormatting.GRAY), false);
        level.playSound(null, station, SoundEvents.BOOK_PAGE_TURN,
                SoundSource.BLOCKS, 0.48F, comparable ? 1.16F : 0.91F);
        level.sendParticles(net.minecraft.core.particles.ParticleTypes.END_ROD,
                station.getX() + 0.5D, station.getY() + 0.92D, station.getZ() + 0.5D,
                7, 0.16D, 0.13D, 0.16D, 0.003D);
    }

"""
patch(ST,"    private static void emitCompassDiagnostic(ServerLevel level, BlockPos center, boolean threat) {",
      journal+"    private static void emitCompassDiagnostic(ServerLevel level, BlockPos center, boolean threat) {",
      "item-stored snapshot helper")

mob=M.read_text(encoding="utf-8")
need("private void emitRaidWarning(BlockPos cropPos, boolean urgent)" in mob
     and "if (chewTicks == 8 || chewTicks == 20)" in mob,
     "two existing warning frames")
patch(M,
"""            level.playSound(null, cropPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, urgent ? 0.62F : 0.36F,
                    urgent ? 0.45F : 0.67F);""",
"""            // No additional tick work: only the old bite warnings at 8/20
            // form a visibly growing border around the threatened crop.
            for (int sample = 0; sample < 12; sample++) {
                double angle = sample * Math.PI / 6.0D;
                double radius = urgent ? 1.35D : 0.72D;
                level.sendParticles(urgent ? ParticleTypes.SOUL_FIRE_FLAME
                                : ParticleTypes.WARPED_SPORE,
                        x + Math.cos(angle) * radius,
                        y + (sample % 3) * 0.09D,
                        z + Math.sin(angle) * radius,
                        1, 0.0D, 0.018D, 0.0D, 0.003D);
            }
            level.playSound(null, cropPos, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.HOSTILE, urgent ? 0.62F : 0.36F,
                    urgent ? 0.45F : 0.67F);""",
"visual bite-wave warning")

for lang,strings in (
 ("de_de.json",{
  "journal_diff":"Feldchronik seit der letzten Messung: Mutagenboden %s | Hochmutagen %s | Sporenpflanzen %s | Ausbreitungsherde %s | Anbauherde %s.",
  "journal_baseline":"Feldchronik: Mutagenboden %s | Hochmutagen %s | Sporenpflanzen %s | Ausbreitungsherde %s | Anbauherde %s.",
  "journal_hint":"Buch und Feder hat den Stationsstand gespeichert. Wieder benutzen: Vergleich. Nur geladene Chunks derselben Station/Dimension; kein weltweiter Heilungsnachweis."}),
 ("en_us.json",{
  "journal_diff":"Field journal changes: Mutagen soil %s | high-level soil %s | spore crops %s | spread nodes %s | cultivation nodes %s.",
  "journal_baseline":"Field journal: Mutagen soil %s | high-level soil %s | spore crops %s | spread nodes %s | cultivation nodes %s.",
  "journal_hint":"Book and quill saves the station reading. Use again to compare. Loaded chunks of the same station/dimension only; not proof of a world-wide cure."})
):
    p=A/"lang"/lang; d=json.loads(p.read_text(encoding="utf-8"))
    for name,value in strings.items():d["message.sporenwerk.fieldstation."+name]=value
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for p in (R/"tools").glob("test_*.py"):
    if p.name=="test_field_journal_103.py":continue
    s=p.read_text(encoding="utf-8")
    n=s.replace("Aktueller Entwicklungsstand: 1.102.0","Aktueller Entwicklungsstand: 1.103.0")
    if "build.gradle" in s:
        n=n.replace(r"1\.102\.0",r"1\.103\.0").replace("artifact must be version 1.102.0","artifact must be version 1.103.0")
    n=n.replace('"Version 1.102.0" in readme and "Version 1.101.0" in readme',
                '"Version 1.103.0" in readme and "Version 1.102.0" in readme')
    if n!=s:p.write_text(n,encoding="utf-8")
g=R/"build.gradle"
v,count=re.subn(r"(?m)^\s*version\s*=\s*['\"][^'\"]+['\"]","version = '1.103.0'",g.read_text(encoding="utf-8"),count=1)
need(count==1,"Gradle version");g.write_text(v,encoding="utf-8")
p=R/"README.md";s=p.read_text(encoding="utf-8")
head="**Aktueller Entwicklungsstand: 1.102.0 — Mutagen-Feldkompass und lebendige Dämmerling-Fraßgesten.**"
need(head in s,"previous generated README heading")
s=s.replace(head,"**Aktueller Entwicklungsstand: 1.103.0 — Buchgebundene Feldchronik und Warnkreise im Farm-Horror.**",1)
section="""## Aktueller Entwicklungsschritt — 1.103.0

- **Feldchronik im Buch:** Ein Buch und Feder in der Haupthand an der Kontrollstation rechtsklicken. Die erste Messung speichert einen Ausgangszustand als NBT in genau diesem Buch; jede folgende Messung an derselben Station zeigt echte Veränderungen in fünf Kennzahlen.
- **Fünf Kennzahlen:** Mutagenboden, stark mutierter Boden, Sporenpflanzen, aktive Ausbreitungsherde und sichere Anbauherde. Bei steigender Zahl aktiver Herde wird die Vergleichsmeldung rot.
- **Sichere Aussagegrenzen:** Messungen derselben Dimension und Stationsposition werden verglichen. An anderen Stationen wird eine neue Basis gesetzt; nur geladene Weltbereiche im bisherigen Radius fließen in die Zahlen ein. Entladene Chunks können die Messwerte verändern, daher kein weltweiter Heilungsbeweis.
- **Buch bleibt erhalten und transportierbar:** Alte NBT-Einträge und Buchseiten bleiben erhalten; keine extra Server-Ticker, Welt-Schreiboperationen, Chunk-Ladungen oder zweite Stationssuche.
- **Dämmerling mit zwei echten Horror-Warnkreisen:** Der bereits vorhandene Warnimpuls an Fraßticks 8 und 20 bildet jetzt kleine bzw. größere zwölfteilige Sporenringe um das bedrohte Beet. Kein Spawnticker und kein zusätzlicher Schaden.
- **Kompatibel:** Der normale Stationsbericht, Kupferrettung, Amethyst-Neustart, Notabschaltung, Kompass, Seelenlaterne und Leuchtbeeren bleiben erhalten.

"""
need("## Aktueller Entwicklungsschritt — 1.102.0" in s,"old section")
s=s.replace("## Aktueller Entwicklungsschritt — 1.102.0",section+"## Aktueller Entwicklungsschritt — 1.102.0",1)
release="""## Version 1.103.0 — Tragbares Mutagenfeld-Tagebuch und sichtbare Biss-Warnung

- Buch und Feder speichert einen echten Feld-Schnappschuss an der Kontrollstation und vergleicht fünf Kennzahlen bei erneuter Verwendung. Keine neuen Scans, keine Gegenstandsverluste.
- Dämmerling signalisiert die beiden alten Fraß-Warnmomente mit gestaffelten Kreisen um das Beet; alle bisherigen Abwehrwege gelten unverändert.
- Alle Quellen, Mutagen-Heilwege, Maschinen, Kopplungen und Bosskämpfe bleiben erhalten. Ein visueller Minecraft-Client-Test ist zusätzlich nötig.

"""
need("## Version 1.102.0 —" in s,"last release")
s=s.replace("## Version 1.102.0 —",release+"## Version 1.102.0 —",1)
p.write_text(s,encoding="utf-8")
print("Sporenwerk 1.103: book-bound persistent field history and two escalating raid crop rings applied.")
