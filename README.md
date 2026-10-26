# Sporenwerk: Wildwuchs

**Aktueller Entwicklungsstand: 1.108.0 — Echte Durchbrüche im Kristallrücken, Kolossmonolithen und Wurzelhänden.**

Dieses Repository enthält die Patch-Skripte und Regressionstests, mit denen der GitHub-Actions-Workflow den Minecraft-Forge-1.20.1-Mod aus dem Quellstand zusammensetzt. Die installierbare JAR wird durch den Workflow gebaut; automatisierte Prüfungen sind kein Ersatz für einen vollständigen Sichttest im Minecraft-Client.

## Aktueller Entwicklungsschritt — 1.108.0

- **Kristallpirscher: echte getrennte Rückenprismen:** Die zuvor große, kompakte 10×17×5-Voxel-Rückenplatte wurde durch drei unterschiedlich hohe schmale Rückendornen ersetzt. Die neuen Luftspalte sind echte 3D-Durchbrüche, keine bloß dunkel gefärbten Pixel. Das bereits animierte `back_crest`-Gelenk bleibt erhalten, ebenso die zusätzlichen Seitenkristalle, Rückenfinnen, Jagdklauen und der Brustresonator.
- **Kristallkoloss: aufgebrochene Basaltmonolithen:** Die beiden zuvor massiven Rückenpfeiler bestehen nun aus zwei dunklen Seitenstützen mit dazwischenliegender Lücke, einer rückwärtigen Strebe und einer oberen Kappe. Die alten beweglichen violetten `monolith_prism`-Kristalle und die schmalen glühenden Runen bleiben erhalten. Der separate normal texturierte und der selektiv leuchtende Modellbaum behalten dieselben Knochenhierarchien.
- **Dämmerling: offen geformte Wurzelhandflächen:** Die bisherigen 4,6×5,6×3,6 breiten Quader-Fäustlinge wurden durch zwei schmale Handwurzelstränge und eine kleine Verbindung bei den Fingern ersetzt. Die bestehenden langen, beweglichen Finger und die vom Server synchronisierte Fraßpose bleiben erhalten.
- **Erstmals eine aus echtem Modellcode abgeleitete QA-Grafik:** Der CI-Test liest die aktuellen `ModelPart.addBox`-Koordinaten und erstellt orthografische Querschnittszeichnungen für die drei überarbeiteten Partien. Er prüft mathematisch, ob die Lücken mindestens einen Minecraft-Modellpixel breit sind, und verhindert eine Rückkehr der alten ausgefüllten 3D-Blöcke. **Dies ist ausdrücklich kein Minecraft-Screenshot** und noch kein Referenzbild-Vergleich.
- **Originaltexturen beibehalten:** Das Modell nutzt weiterhin normale Minecraft-Pixelatlanten (128×128 für Pirscher/Dämmerling, 256×256 für Koloss), mit eigenständigen, transparenten Leuchtebenen. Keine übernommenen Texturen oder Modelle aus Belowland oder Wonderland.
- **Keine Gameplay-Regel geändert:** Mutagenausbreitung und Endgame-Heilung, Farming, Maschinen, Spawns, Bossgegner-KI, Schaden, Kollisionsboxen und Gegenstandserhalt sind unberührt.
- **Technisch bestätigt:** 120 erfolgreiche GitHub-Actions-Schritte, einschließlich aller alten und neuen Regressionen, Forge-1.20.1-Kompilierung, installierbarer Mod-JAR, eigenständigem Geometrie-Artefakt und erfolgreich gestartetem dediziertem Minecraft-Server.

### Pflichtabnahme im Minecraft-Client für 1.108.0

1. Den Kristallpirscher aus der direkten Rückansicht und aus beiden Seitenansichten betrachten. Drei deutlich getrennte Rückenprismen müssen erkennbar sein; die Zwischenräume dürfen nicht von einer darunter liegenden massiven Kristallplatte verschlossen werden.
2. Den Koloss seitlich und schräg von hinten prüfen: Beide Rückenmonolithen sollen offene Spalten zwischen dunklen Stützen haben. Die violetten leuchtenden Kristalle müssen mit den Basaltmonolithen mitbewegt werden.
3. Den Dämmerling bei Tageslicht, bei Dunkelheit und beim tatsächlichen Beetfraß ansehen. Die Hände sollen schmaler, zwischen den Wurzelsträngen offen und mit den alten beweglichen langen Fingern verbunden sein.
4. Die technischen Querschnitte im neuen Artefakt `sporenwerk-1.108.0-creature-geometry-qa` mit den tatsächlichen Minecraft-Aufnahmen vergleichen. Die technische Grafik stellt nur ausgewählte Quellenwürfel ohne vollständige Rotation/Kindhierarchie dar; sie ersetzt keine In-Game-Abnahme.
5. Screenshots in ähnlicher Perspektive wie die ursprünglichen Konzeptbilder anfertigen und Silhouette, Proportion, Glow-Verteilung und Bewegungen **direkt nebeneinander** prüfen. Was noch abweicht, gilt weiterhin als unvollständig.
6. Bewegung, Dunkelheit, Bosskampf, Feldraids sowie dedizierten Mehrspieler-Server testen. Ein erfolgreicher Server-Build beweist nicht, dass die vollständige visuelle Referenz exakt erreicht wurde.

## Aktueller Entwicklungsschritt — 1.107.0

- **Koloss: Gesichtspanzer wirklich zum 1.105-Schädel passend:** Beim Verkleinern des Kopfes waren vier ältere Stirn-/Wangenpanzer und deren zusätzliche Vollhelligkeitswürfel unverändert groß geblieben. Jetzt wurden beide Basaltbrauen, beide Wangen und ihre oberen bzw. unteren Steinkanten in der tatsächlichen Forge-Geometrie zurückgenommen. Die zwei Gesichtsseiten sind spiegelgleich und bleiben innerhalb der neuen Schädelbreite.
- **Keine großen leuchtenden Basaltplatten mehr:** Die transparenten Emissiv-Modellteile für Stirn und Wange wurden stark verschlankt. Der dunkle Stein bleibt in der regulären Haut; dünne runenähnliche Linien benutzen ausschließlich das vorhandene transparente Glow-Atlas. Die korrekt positionierten Augen aus 1.106 behalten ihre eigenständigen Leuchtteile.
- **Kristallpirscher: klares Fußprofil statt überbreiter Schienbeine:** Die frühere Kristallschiene war fast doppelt so breit wie das schlanke Bein aus 1.105. Sie wurde verkleinert; jedes der beiden echten laufenden Beine besitzt nun zusätzlich zwei unterschiedlich lange, nach vorn ausgerichtete 3D-Kristallkrallen.
- **Dämmerling: schmale Wurzelschienbeine und asymmetrische Zehen:** Die breiten Holzschienen wurden auf die schmalen Basisbeine abgestimmt. An jedem Fuß sind zwei getrennte, nach vorne wachsende Wurzelzehen hinzugekommen. Sie folgen direkt den bestehenden Lauf-/Fraßgelenken statt als schwebende Textur oder flaches Partikelsymbol zu erscheinen.
- **Keine Übernahme fremder Modellressourcen:** Die bisherigen originalen Minecraft-Pixeltexturen (128×128 für Pirscher/Dämmerling, 256×256 für den Koloss) und ihre transparenten Glow-Masken bleiben erhalten. Keine Ressourcen aus Belowland, Wonderland oder anderen Mods wurden übernommen.
- **Bewusst keine Gameplay-Änderung:** Alle Korrekturen liegen in clientseitigen Voxelboxen und ModelParts. Mutagenkontrolle, Maschinen, Farm-Horror-Gegenmaßnahmen, Koloss-Hitbox, KI, Gesundheit, Angriff und andere Weltsysteme bleiben unverändert.
- **Technisch verifiziert:** 118 erfolgreiche GitHub-Actions-Schritte. Die neuen Regressionen überprüfen gespiegelt passende Stein- und Rune-Geometrie, physisch separate Kristall- und Wurzelzehen, alte Knochenbewegungen und vollständige Pixelatlanten. Forge 1.20.1 kompiliert und die JAR wurde mitsamt dediziertem Server erfolgreich geprüft.

### Minecraft-Client-Sichttest für 1.107.0

1. **Koloss frontal:** Beide dunklen Brauen und beide Wangen müssen sich sauber an den kleineren Kopf anschließen. Die cyan-/violettleuchtenden Augen sollen erkennbar zwischen den Platten liegen; große, durchgehend leuchtende Steinwürfel oder außerhalb des Kopfes schwebende Leuchtpanzer sind nicht akzeptabel.
2. **Koloss Seitenansicht und Angriff:** Die Gesichtsplatte soll eine gestufte Basaltschicht bleiben. Kristallkrone, Unterkiefer, Kernblende, Schwanz und Attackeneffekte dürfen durch die Korrektur nicht verschoben sein.
3. **Kristallpirscher im Stand und beim Jagen:** Jeweils zwei reale Kristallkrallen pro Fuß müssen am Bein sitzen, bei Bewegung mitlaufen und deutlich vor den schmaleren Kristallschienen sichtbar sein. Beide Beine aus Vorder- und Seitenperspektive prüfen.
4. **Dämmerling bei Tag, nachts und beim Beetfraß:** Die Beine dürfen unter dem neuen Wurzelrumpf nicht wie dicke Standard-Zombiebeine aussehen. Getrennte Wurzelzehen müssen am Boden sichtbar bleiben, auch während der Kiefer und die seitlichen Rumpfwurzeln sich bewegen.
5. **Originalbild direkt vergleichen:** Aus identischen Blickrichtungen In-Game-Screenshots machen. Silhouette und Größenverhältnis von Körper, Kopf und Gliedmaßen stehen vor Farbe/Glow. Die neue Geometrie ist eine echte Verbesserung, beweist aber noch keine vollständige Bildgleichheit.

## Aktueller Entwicklungsschritt — 1.106.0

- **Koloss-Leuchtaugen an tatsächlichen Schädel angepasst:** Die seit Version 1.105 verkleinerte Kopfgeometrie war schmaler als die älteren Fullbright-Augenteile. Beide Augen liegen nun als echte symmetrische Forge-Cubes innerhalb der neuen Schädelbreite und treffen die Gesichtsebene. Die viel zu breiten emissiven Brauenplatten wurden zugleich verkleinert. Dies behebt eine konkrete Modellabweichung und verhindert frei schwebende Glow-Flächen.
- **Kristallpirscher mit dreiteiligen Schulterfacetten:** An jedem Arm wurden die alten, großen, einteiligen Kristallwülste durch drei räumlich getrennte Panzerabschnitte ersetzt. Die in 1.105 langgezogenen Gliedmaßen und die vier animierten Jagdklauen werden dadurch weniger verdeckt. Die vorhandenen Cyan-/Magenta-Pixeloberflächen, Dorsalflossen, Kopfkristalle und der pulsierende Brustresonator bleiben erhalten.
- **Dämmerling mit tatsächlichen beweglichen Wurzelfasern:** Zwei unterschiedlich lange schmale Wurzelknochen hängen jetzt seitlich am offenen Rumpf, schwingen bei der Bewegung gegeneinander und beugen sich beim echten serverseitig synchronisierten Beetfraß zusätzlich nach vorne. Vor jeder Animation werden die Gelenke absolut berechnet, damit keine schleichende Rotationsverschiebung entsteht.
- **Pixel- und Leuchtlayer unverändert:** Alle drei Kreaturen behalten ihre eigenen Minecraft-Pixel-Atlanten mit 128×128 bzw. 256×256 sowie ihre transparenten selektiven Glow-Masken. Es wurden keine Texturen oder Modelle aus Belowland, Wonderland oder anderen Referenzmods übernommen.
- **Keine Spieler- oder Weltänderungen:** Der Schritt verändert ausschließlich Geometrie und Animation. Infektionsheilung, kontrollierte Farmanlagen, Dämmerling-Abwehr, Boss-Schadenswerte, Gegenstände, KI und Trefferzonen bleiben unverändert. Keine neuen Server-Ticker oder Chunk-Abfragen.
- **Technisch verifiziert:** 117 GitHub-Actions-Schritte erfolgreich, einschließlich der neuen exakten Augenkoordinaten-Prüfung und Tests für getrennte Schultercubes, bewegliche Wurzelknochen, alte Monsteranimationen, Forge-1.20.1-Kompilierung, installierbare JAR und dedizierten Serverstart.

### In-Game-Referenzprüfung für Version 1.106.0

1. Kristallkoloss frontal und schräg von vorne betrachten: Beide Leuchtaugen müssen symmetrisch innerhalb des kleineren Schädels liegen; keine überstehenden hellen Brauenteile. Danach geöffneten Unterkiefer, Kristallatem und das Leuchten des Brustkerns kontrollieren.
2. Kristallpirscher von vorne, von der Seite und in Bewegung betrachten: Die drei getrennten Kristallpanzerstücke je Schulter müssen voneinander unterscheidbar sein. Arme, lange Klauen und durchbrochene Rippen dürfen nicht durch alte massive Würfel versteckt werden.
3. Dämmerling tagsüber, nachts, beim Gehen und während eines Beetangriffs betrachten: Zwei unterschiedliche herabhängende Wurzelfasern müssen in echter 3D-Tiefe sichtbar sein, nicht nur als Textur. Beim Fraß sollen sie sich zusammen mit dem vorhandenen Kiefer bewegen.
4. Glow und Körperhaut aller drei getrennt prüfen: Keine vollflächig leuchtenden Stein-/Wurzelpanzer und keine verschobenen Skin-/Glow-Körper.
5. Screenshots aus den gleichen Blickwinkeln wie die Originalbilder machen und Silhouette, relative Teilgrößen, Farben, Glühbereiche und Animationsform vergleichen. **Ein Build-Erfolg ist kein Nachweis exakter Bildtreue.** Restliche Abweichungen bleiben ausdrücklich offene Modellaufgaben.

## Aktueller Entwicklungsschritt — 1.105.0

**Ziel:** Keine bloße Stilähnlichkeit mit den Kreaturenreferenzen. Die tatsächliche Minecraft-3D-Geometrie muss in Silhouette, Größe, Kopfprofil, Kristallverteilung und Glow zu den Bildern passen. Dieser Schritt korrigiert reale Abweichungen im bisher erzeugten Modell; die exakte visuelle Gleichheit wird erst nach einem Client-Bildvergleich als abgeschlossen betrachtet.

- **Kristallkoloss:** Der ursprüngliche besonders breite, massive Kopfbereich wurde im echten Forge-ModelLayer durch einen kleineren Felsenschädel mit gestufter Schnauze ersetzt. Dadurch treten sein niedriger, breiter Vierbeinerkörper und die höheren Kristall-/Panzerformen stärker hervor. Alle bisherigen Unterkiefer-, Kristallkronen-, Schwanz-, Klauen-, Resonanz- und Brustblendenmodelle behalten ihre vorhandenen Gelenke.
- **Kristallpirscher:** Statt einen gewöhnlichen vollen Zombie-Körper unter die Kristallteile zu setzen, werden der eigentliche Kopf, der Brustkörper, beide Arme und beide Beine durch selbst modellierte, schmale, langgliedrige Voxelgeometrie ersetzt. Drei räumlich getrennte Brustpanzerreihen und eine schmale Wirbelsäule mit Seitenleisten erzeugen echte Zwischenräume. Cyan-violette Kristalle, Rückenzacken, Brustresonator und Klauen bleiben animiert und am neuen Körper befestigt.
- **Dämmerling:** Dieselbe grundlegende Render-Schwachstelle wurde behoben: Keine massiven Zombie-Standardwürfel mehr unter dem Horror-Design. Stattdessen besitzt er einen schmalen Wurzelkörper, schlanke Arme/Beine und einen segmentierten offenen Brustkorb. Seine asymmetrischen Hörner, Wurzelfinger, bewegliche Fraßschnauze, Augen-Glow und sämtliches Feldraid-Verhalten bleiben bestehen.
- **Texturen bleiben Minecraft-kompatibel:** Originale 128×128-Pixelatlanten für Pirscher und Dämmerling und 256×256 für den Koloss, jeweils mit bestehenden separaten Glow-Texturen. Keine 3D-/Texturressourcen aus Belowland, Wonderland oder anderen Referenzmods übernommen.
- **Technik geprüft:** 116 erfolgreiche GitHub-Actions-Schritte, einschließlich neuer Tests für tatsächliche nicht-generische Basisgeometrie, Durchbrüche im Torso, korrekt erhaltene Knochen/Animationen, alten Farm- und Mutagenmechaniken, Forge-1.20.1-Kompilierung, installierbarer JAR-Prüfung und Dedicated-Server-Smoke-Test.
- **Offene Abnahme:** Der Build belegt keine pixel- oder formgenaue Übereinstimmung mit den Ursprungsbildern. Die In-Game-Optik muss weiterhin sichtbar gegen diese Referenzen kontrolliert und bei Abweichungen korrigiert werden.

### Pflicht-Sichttest der drei Kreaturen für 1.105.0

1. Den Kristallkoloss **direkt von vorne, seitlich, von hinten und schräg** fotografieren. Prüfen, dass das Kopfprofil deutlich kleiner als der breite Rumpf wirkt und Kristallmonolithen, vier kräftige Beine, cyanfarbene Klauen, Brustkern und gebogener Skorpionschwanz dieselbe Umrissfunktion wie im ursprünglichen Referenzbild erfüllen.
2. Kristallpirscher aus 4–8 Blöcken Abstand betrachten: Die Arme sollen nicht mehr wie normale Zombiearme wirken; echte sichtbare Lücken zwischen Brustpanzerstücken und Wirbelsäulenleisten müssen sich aus der Seitenansicht zeigen.
3. Dämmerling im Dunkeln und während des echten Beetfraßes betrachten: schmaler Wurzelrumpf, unterschiedlich große Rückenwurzeln und ausgestreckte Finger, dazu ein funktionierender Fraßkiefer. Prüfen, dass es unter den Wucherungen keine große unpassende Zombie-Silhouette gibt.
4. Bei allen dreien Tag-/Nacht-Skin und Glow getrennt überprüfen. Dunkle Basalt- und Wurzelpanzer dürfen nicht großflächig leuchten. Beim Koloss müssen das normale und das emissive Modell übereinanderliegen.
5. Die tatsächlichen In-Game-Aufnahmen **neben die Originalbilder legen**. Silhouette und Proportionen zuerst abnehmen, danach Farben, Emission und Animationsqualität; verbleibende Abweichungen gelten als offene Modellaufgaben.
6. Welten neu laden, Server mit Client verbinden, alle drei Monster in Bewegung/Angriff testen. Neue Voxelboxen sind reine Rendereränderungen; Hitboxen und Farm-/Mutagenmechanik sollen unverändert bleiben.

## Aktueller Entwicklungsschritt — 1.104.0

- **Feldchronik mit verlässlichem Messbereich:** Das bisherige Buch mit Feder speichert ab jetzt auch die Anzahl und eine reproduzierbare Signatur der beim Stationsscan geladenen X/Z-Spalten. Nur bei derselben Station derselben Dimension mit demselben Abdeckungsbereich zeigt das Buch Veränderungen an Mutagenboden, Hochmutagenboden, Sporenpflanzen, ausbreitenden und kultivierenden Knoten an.
- **Keine falschen Heilungsschlüsse:** Wenn zwischen Messungen beispielsweise ein benachbarter Chunk entladen wird, meldet die Chronik eine veränderte Messabdeckung und legt einen neuen Ausgangswert an. Sie zeigt dann bewusst keine irreführenden Differenzen. Bücher aus Version 1.103 ohne die neue Signatur können weiter benutzt werden; bei der ersten erneuten Messung wird ein sicherer aktueller Basisstand gespeichert.
- **Kein zusätzlicher Stationsscan:** Die Signatur entsteht unmittelbar im bisherigen, geladenen und bereits begrenzten Stations-Scan. Kupfer-Notrettung, Feldkompass, Amethyst-Neustart, Notabschaltung, stabilisierende Maschinen und der Mutagen-Heilungsweg sind funktional unverändert.
- **Vanilla-Komposter schützt gegen Dämmerling-Fraß:** Ein vollständig gefüllter Vanilla-Komposter (Füllstand 8) im bestehenden 3-Block-Bereich um eine reife Sporenpflanze zählt als passive Schutzstelle gegen den Dämmerling. Er wird dabei nicht geleert; leere oder unvollständige Komposter schützen nicht.
- **Schon bestehende Feldschutz-KI wiederverwendet:** Dämmerlinge prüfen bei ihrer bisherigen Pflanzenauswahl weiterhin nur bereits geladene Blöcke, Filtermoos-Symbiose und Feldsammler bleiben bestehen. Der zusätzliche Komposterfall nutzt denselben Blockzustand, ohne weitere Weltabfragen oder Mob-Scans auszulösen.
- **Wichtige Einschränkung:** Der Komposter verhindert nur diesen einen Farm-Horror-Fraßangriff. Er ist keine Mutagenbarriere und heilt keine Infektion. Für Mutagen bleiben die bestehenden Block- und Maschinenwerkzeuge zuständig.
- **Technisch verifiziert:** 115 erfolgreiche GitHub-Actions-Schritte, einschließlich aller bisherigen Mutagen-, Koloss- und Farm-Horror-Regressionen, neuer Tests zu geladener Flächensignatur, altem Buch-NBT und vollem Komposter sowie Forge-1.20.1-Kompilierung, JAR-Verifikation und Dedicated-Server-Smoke-Test.

### Minecraft-Client-Abnahme für Version 1.104.0

1. Mit Buch und Feder an der Kontrollstation eine Messung speichern, dann im selben geladenen Gebiet einen Mutagenblock oder eine Sporenpflanze verändern und erneut messen. Die zugehörige Feldänderung soll korrekt erscheinen.
2. In kontrollierter Testwelt gezielt einen Teil des Stationsradius entladen (zum Beispiel durch geänderte Simulations-/Ladebedingungen im Mehrspieler-Test) und das gleiche Buch erneut benutzen. Statt vermeintlicher Heilungsfortschritte soll eine Warnung erscheinen, dass die Messabdeckung nicht vergleichbar ist.
3. Ein älteres Messbuch aus Version 1.103 verwenden. Es darf nicht fehlschlagen oder sich verlieren, sondern muss eine neue sichere Vergleichsbasis anlegen; danach erneute Messung testen.
4. Eine reife Sporenpflanze in Dunkelheit mit einem vollen Vanilla-Komposter innerhalb von drei Blöcken gegen den Dämmerling testen. Der Gegner soll diese Pflanze als geschützt behandeln.
5. Bei unveränderter Pflanze denselben Komposter leeren. Ohne Feldsammler, ausreichende Beleuchtung, Filtermoos oder Spielerschutz muss der Dämmerling wieder ein legitimes Angriffsziel finden.
6. Welt speichern, neu laden, Buch in eine Kiste legen und erneut herausnehmen; die Chronikdaten und Schutzregeln müssen erhalten bleiben. Das technische CI-Ergebnis ersetzt nicht den Minecraft-Client-Sicht- und Gameplaytest.

## Aktueller Entwicklungsschritt — 1.103.0

- **Tragbare Feldchronik:** Ein normales Buch und Feder in der Haupthand auf die Mutagen-Feldkontrollstation rechtsklicken. Bei der ersten Messung speichert das Buch fünf Kennzahlen im eigenen NBT. Eine erneute Messung an derselben Station derselben Dimension zeigt die Differenzen seit dem letzten Stand. Bücher können aufbewahrt oder unter Spielern weitergegeben werden; vorhandene Buchdaten bleiben erhalten, nichts wird verbraucht.
- **Fünf vergleichbare Kennzahlen:** Aktuell gezählter Mutagenboden, besonders stark mutierter Boden, lebende Sporenpflanzen, aktive ausbreitende Mutagenknoten und sichere Kultivierungsknoten. Steigt die Zahl aktiver Quellen, erscheint die Vergleichsmeldung rot. Die Dokumentation sagt ausdrücklich, dass die vorhandene Station nur momentan geladene Blöcke in 16 Blöcken Horizontalradius und ±8 Blöcken Höhe berücksichtigt; eine Änderung der Chunk-Ladebedingungen kann den Vergleich ebenfalls beeinflussen.
- **Station und Dimension sind Teil der Buchmessung:** Beim Gebrauch an einer anderen Station oder in einer anderen Dimension legt das Buch einen neuen Ausgangswert an, statt irreführende Felder miteinander zu vergleichen. Der gespeicherte Stand bleibt auf die jeweils letzte Messung beschränkt.
- **Dämmerling-Überfälle leichter zu erkennen:** Die bereits bestehenden frühen und späten Vorwarnungen während des echten Pflanzenfraßes erhalten einen kleinen und einen größeren Kreis aus Wurzelsporen bzw. Seelenfeuer-Partikeln direkt am Beet. Er wird ausschließlich bei den vorhandenen Fraßticks 8 und 20 erzeugt; keine Endlos-Partikel, keine zusätzlich geladenen Chunks und kein neuer Schaden.
- **Bestehendes Gameplay geschützt:** Die eingeführten Buch- und Warneffekte verändern weder Pflanzenwachstum noch die Mutagenheilung, Kupferrettung, Amethyst-Neustart, Feldkompassfunktion, Dämmerling-KI, Seelenlaterne, Leuchtbeeren, Maschinen oder Bosskämpfe.
- **Technisch verifiziert:** 114 grüne GitHub-Actions-Schritte. Sämtliche Modell-, Feldkontroll- und Farm-Horror-Regressionen bestanden, außerdem Forge-1.20.1-Kompilierung, installierbare JAR-Paketprüfung und Dedicated-Server-Smoke-Test.

### Minecraft-Client-Abnahme für Version 1.103.0

1. Buch und Feder in der Haupthand auf eine Feldkontrollstation rechtsklicken. Prüfen, dass die fünf Basiswerte angezeigt werden und das Buch danach unverbraucht im Inventar liegt.
2. Im geladenen Radius gezielt Mutagenboden, eine Sporenpflanze oder einen aktiven Knoten verändern und das gleiche Buch erneut verwenden. Die passenden Änderungswerte sollen differenziert erscheinen.
3. Dieselbe Feldchronik in eine Kiste legen, wieder entnehmen und später erneut verwenden. Der vorige Vergleichsstand muss erhalten bleiben; an einer anderen Station oder in einer anderen Dimension muss stattdessen eine neue Basis erstellt werden.
4. Ein ungeschütztes reifes Beet in Dunkelheit von einem Dämmerling angreifen lassen. Der erste Kreis soll klein sein, der zweite kurz vor dem tatsächlichen Biss größer. Warnungen sollen aufhören, wenn der Raid endet.
5. Seelenlaternen und Leuchtbeeren getrennt testen: Die Gegenmaßnahmen müssen weiterhin rechtzeitig funktionieren und die synchronisierte Dämmerling-Fraßpose beenden.
6. Die Arbeit mit dem Buch darf keine Entlastungs-, Heilungs- oder Mutagenoperation auslösen. Ein grüner Dedicated-Server-Test ersetzt nicht die visuelle Prüfung in Minecraft.

## Aktueller Entwicklungsschritt — 1.102.0

- **Neue freiwillige Feldkompass-Funktion:** Einen normalen Minecraft-Kompass in die Haupthand nehmen und die Mutagen-Feldkontrollstation rechtsklicken. Sie zeigt die relativen X-, Y- und Z-Abstände sowie die ungefähre Entfernung der nächsten tatsächlich aktiven Ausbreitungsquelle an. Der Kompass bleibt erhalten.
- **Bereits vorhandene, sichere Stationsvermessung:** Die Kompassdaten werden im selben Scan gesammelt, den die Feldkontrollstation beim normalen Rechtsklick verwendet. Der Radius bleibt auf 16 Blöcke horizontal und ±8 Blöcke vertikal begrenzt. Nicht geladene Chunks werden übersprungen. Inaktive, geheilte, kultivierende, ruhende und redstone-pausierte Quellen gelten nicht als aktive Ausbreitungsziele.
- **Drei Ausgänge – Diagnose ohne Zwang:** Bei Gefahr erscheint eine rote Lage- und Entfernungsnachricht sowie ein kleiner violetter Kreis. Ohne aktive Quelle erscheint eine grüne Meldung samt ruhigem Kreis. Ein kurzer Hinweis erklärt die Minecraft-Koordinaten (+X = Osten, +Z = Süden) und die Einschränkung auf bereits geladene Chunks. Die unverwechselbaren Texturen und sichtbaren Infektionsfelder funktionieren weiterhin ganz ohne Kompass.
- **Dämmerling mit animiertem Unterkiefer:** Sein bestehender echter 3D-Unterkiefer bekommt beim server-synchronisierten Feldfraß eine rhythmische Beißbewegung. Die selektiv roten Glow-Augen leuchten während des Fraßes etwas stärker; beim Abbruch per Seelenlaterne oder Leuchtbeeren kehren beide in ihre Ausgangslage zurück.
- **Andere Systeme geschützt:** Die schon vorhandenen Notabschaltung, Kupfer-Rettung, Amethyst-Neustart, Mutagen-Endgame-Heilung, Feldschutzmaschinen und drei Mutagenknotenmodi bleiben erhalten. Der neue Kompass ist nur eine Diagnose; er verändert keine Weltblöcke, KI oder gespeicherten Felder.
- **Technischer Abschluss:** 113 GitHub-Actions-Schritte erfolgreich. Zusätzliche Regressionen für Quellpriorität, relative Entfernung und geladene Chunks, außerdem Forge-1.20.1-Kompilierung, installierbare JAR-Prüfung und dedizierter Serverstart.

### Minecraft-Client-Abnahme für 1.102.0

1. Eine aktive, ungepauste Ausbreitungsquelle innerhalb des Kontrollstationsradius platzieren, mit Vanilla-Kompass auf die Station klicken und relative Koordinaten sowie die Entfernungsangabe vergleichen.
2. Quelle in Anbau oder Ruhe schalten und die Messung erneut auslösen: Die Quelle darf nicht mehr als aktive Ausbreitungsgefahr erscheinen. Auch bei Redstone-Pause oder dauerhaft geheilter Quelle darf sie kein falscher Alarm sein.
3. Mehrere Quellen anordnen und kontrollieren, ob tatsächlich die nächstgelegene, bereits geladene Quelle als Richtung angezeigt wird; nicht geladene Chunks bleiben außerhalb der Aussage.
4. Mit leerer Hand weiterhin den ausführlichen Bericht abrufen; geduckt mit Kupfer, Amethyst oder ohne Item müssen die bisherigen Kontrollaktionen unverändert bleiben.
5. Beim Dämmerling einen echten Fraß an reifen Pflanzen beobachten. Sein Unterkiefer und die roten Augen sollen im Rhythmus seiner Wurzelhände reagieren und nach Vertreibung wieder normal aussehen.
6. Multiplayer, Neuladen und Dunkelheit testen. Die erfolgreiche CI bestätigt technische Kompatibilität, ersetzt aber keine Sichtprüfung der tatsächlichen Minecraft-Optik.

## Aktueller Entwicklungsschritt — 1.101.0

- **Der Dämmerling frisst jetzt sichtbar:** Ein echtes, vom Server synchronisiertes visuelles Signal lässt das seit Version 1.100 eigenständige 3D-Modell nur bei einem tatsächlichen laufenden Beetangriff in eine besondere Fraßhaltung wechseln. Der Körper krümmt sich vor, die Wurzelkrallen greifen abwechselnd zu und die seitlichen Rückenwurzeln spannen sich an.
- **Sauberer Rückweg zur Normalanimation:** Sobald er das Beet verlässt, durch eine Seelenlaterne oder Leuchtbeeren abgelenkt wird, den Fraß beendet oder das KI-Ziel verliert, wird der visuelle Status über denselben Serverpfad zurückgesetzt. Andere Horror-, Kampf- und Farm-Animationen bleiben bestehen.
- **Netzwerksynchronisation mit geringer Belastung:** Ein einziges zusätzliches, nur bei Änderungen synchronisiertes Boolean-EntityData-Feld. Die vorhandene serverseitige Dämmerling-Markierung bleibt für die Feldkontrollstation maßgeblich. Keine neuen AI-Ziele, Spieler- oder Chunk-Scans, keine kontinuierliche Netzwerkübertragung.
- **Mutagenmodi jetzt unmittelbar sichtbar:** Beim bewussten Umschalten eines Infektionsherds erscheinen kurzzeitig 12 Partikelpositionen als Kreis. Aktive Ausbreitung zeigt größere, violette Portalsporen mit Seelenfeuer; sichere Kultivierung einen ruhigeren grünen Wachstumsring; der Ruhezustand einen kleineren grauen Rauchring.
- **Keine Scannerpflicht:** Die bestehenden drei in der Welt unterschiedlich texturierten Blockzustände bleiben erhalten und die Ringe zeigen den neuen Modus zusätzlich direkt am Block. Ringe entstehen ausschließlich beim manuellen Moduswechsel und nicht bei zufälligen oder geplanten Blockticks.
- **Sicherheit bewahrt:** Redstone-Pause, inaktive Knoten, Heilungsweg, geschützte Ernten, Dämmerling-Blickkontakt, Seelenlaterne, Leuchtbeeren und kontrollierte Farmanlagen behalten ihre bisherigen Regeln. Keine neuen Schaden-, Drops- oder Infektionsfolgen.
- **Technisch verifiziert:** 112 erfolgreich abgeschlossene GitHub-Actions-Schritte mit eigenen Regressionstests, Forge-1.20.1-Kompilierung, JAR-Prüfung und erfolgreichem Dedicated-Server-Smoke-Test.

### Minecraft-Client-Abnahme für Version 1.101.0

1. Dämmerling im Dunkeln zu einem reifen, unbeleuchteten und ungeschützten Beet führen und prüfen, ob er während des Knabberns deutlich gekrümmt mit beiden Wurzelhänden am Boden arbeitet.
2. Leuchtbeeren und danach eine Seelenlaterne in die Hand nehmen. Beide Abwehrmaßnahmen sollen die bestehende Feldzerstörung stoppen und die visuelle Fraßpose wieder ausschalten.
3. Fütterungsanimation und normales Gehen aus verschiedenen Perspektiven kontrollieren: Rückenwurzeln und Arme müssen am 3D-Körper bleiben, der rote Augen-Glow darf nicht den ganzen Körper leuchten lassen.
4. Mutagenknoten manuell mehrfach umschalten: Violett-großer Ausbreitungsring, grün-mittlerer Kulturkreis und kleiner grauer Ruhering müssen optisch klar unterscheidbar sein.
5. Redstone-pausierte und inaktive Knoten kontrollieren, einschließlich bestehender Texturen, Ernteschutzsysteme und Infektionsbegrenzungen. Es darf keine neue Ausbreitung durch die visuellen Effekte entstehen.
6. Multiplayer mit mindestens zwei Clients sowie Welt-Neuladen testen. Der automatische Forge-Build bestätigt die technische Integration, ersetzt aber keine Sichtprüfung der tatsächlichen Minecraft-Optik.

## Aktueller Entwicklungsschritt — 1.100.0

- **Dämmerling endlich als eigenständiges Minecraft-Monster:** Der frühere Vanilla-Zombie-Renderer wurde durch einen eigenen Forge-ModelLayer ersetzt. Ein eingefallener Torso, zwei ungleich große Rückenwurzeln, eine gekrümmte Kopfkrone, längliche Wurzelfinger und mineralisierte Schienen verändern seine tatsächliche 3D-Silhouette.
- **Lebendige Schattenanatomie:** Seine Rückenwurzeln und Krallen bewegen sich beim Gehen unterschiedlich stark. Während aggressiver Verfolgung beugt sich der Körper vor und verändert die Klauenhaltung. Die vorhandene Zombie-Bewegungsbasis und Dämmerling-KI bleiben erhalten.
- **Neuer eigener Pixel-Look:** Originaler 128×128-Minecraft-Texturatlas mit erhaltener 64×64-Grundhaut, neuen dunkelgrünen Wurzeloberflächen und einer transparenten zusätzlichen Emissiv-PNG für rote Augen und nur schmale, lebendige Wurzeladern.
- **Leuchtbeeren lenken den Pflanzenräuber ab:** Wer bei einem tatsächlichen Feldüberfall innerhalb von vier Blöcken Leuchtbeeren hält, kann den Dämmerling kurzfristig vertreiben und die bedrohte reife Pflanze schützen. Das funktioniert nur während des bestehenden langsamen Fraßversuchs, ohne den Gegenstand zu verbrauchen.
- **Seelenlaterne hat Vorrang:** Wenn ein geeigneter Laternenwächter in der Nähe ist, wird er gegenüber dem Beerenköder bevorzugt. Der alte Nachtwache-Fortschritt wird nur beim echten Laternen-Einsatz vergeben.
- **Eigene Rückmeldung:** Der Leuchtbeeren-Schutz erzeugt einen anderen Sporenimpuls, einen tieferen Amethystton und eine lokale, zeitlich gedrosselte Meldung auf Deutsch oder Englisch.
- **Leistung und Sicherheit:** Die beiden Gegenmaßnahmen verwenden gemeinsam den einen bisherigen Spieler-Scan im Fraßziel. Keine zusätzlichen Server-Ticker, Chunk-Ladungen, neuen Spielfiguren-Schäden oder Änderungen am Mutagen-Heilungsweg.
- **Technisch verifiziert:** 111 erfolgreiche GitHub-Actions-Schritte, einschließlich alter und neuer Regressionen, Forge-1.20.1-Kompilierung, installierbarer JAR-Prüfung und Dedicated-Server-Smoke-Test.

### Minecraft-Client-Sichttest für 1.100.0

1. Einen Dämmerling im Creative-Modus erzeugen und aus allen vier Seiten prüfen: beide Rückenwurzeln, Finger und Kopfwucherung müssen tatsächlich zum Körper gehören und korrekt texturiert sein.
2. In der Dunkelheit das Leuchten betrachten: Augen und einzelne Adern sollen leuchten, nicht der gesamte Körper.
3. Den Dämmerling herumwandern und einen Spieler verfolgen lassen. Rückenwurzeln und Finger müssen mit ihren eigenen Gelenken arbeiten, ohne vom Körper abzureißen.
4. Ein reifes, unbeleuchtetes und nicht zusätzlich geschütztes Beet testen. Kurz vor dem vollständigen Fressen Leuchtbeeren in der Hand halten: Das Beet soll erhalten bleiben und die eigene Köder-Meldung erscheinen.
5. Den Versuch mit einer Seelenlaterne wiederholen; diese soll weiterhin Vorrang haben und den Nachtwache-Fortschritt erlauben.
6. Mit Filtermoos und beleuchteten Feldern überprüfen, dass bereits sichere Beete auch ohne die neue Gegenmaßnahme sicher bleiben.
7. Danach Welt laden, Multiplayer und Performance kontrollieren. Eine grüne Server-CI bestätigt nicht, dass das neue 3D-Modell schon genauso hochwertig wie die Referenzbilder aussieht.

## Aktueller Entwicklungsschritt — 1.99.0

- **Kristallkoloss: Kampfschaden wird sichtbar:** Die vier vorhandenen Schulter- und Hüftpanzer öffnen sich mit abnehmender Gesundheit zunehmend. Unter 70 % HP beginnt die neue rein optische Phase; bei 25 % HP ist die Panzeröffnung am deutlichsten.
- **Vier freigelegte Kristallfugen:** Unter den Panzerungen werden originale violett-cyanfarbene Kristalladern als echte Minecraft-Modellgeometrie sichtbar. Jede der vier Fugen besitzt denselben Knochen im normalen Modell und im selektiven Leucht-Layer. Die vorhandenen UV-Texturen werden verwendet, nicht überschrieben.
- **Kristallpirscher mit optischer Verletzungsphase:** Unter 55 % Gesundheit beginnt er sich leicht asymmetrischer zu bewegen; Kopfkristall und Thoraxresonator zittern bzw. pulsieren stärker. Es werden nur Modellposen und die Stärke des schon vorhandenen Glow-Layers verändert.
- **Spielmechanik unverändert:** Weder der Koloss noch der Pirscher wird durch diese Optik stärker oder schwächer. Laufgeschwindigkeit, Bossangriffe, Hitboxen, Drops, Mutagenfelder, Schutztechnologie und der vollständige Heilungsweg bleiben gleich. Es entstehen keine zusätzlichen Server-Ticker oder Netzwerkpakete.
- **Technik verifiziert:** 110 erfolgreiche GitHub-Actions-Schritte, alle bisherigen Regressionen sowie neue Gesundheitsphasen- und Skin/Glow-Modelltests bestanden. Forge 1.20.1 wurde kompiliert, die JAR geprüft und ein dedizierter Minecraft-Server erfolgreich gestartet.

### Minecraft-Client-Test für Version 1.99.0

1. Den Kristallkoloss mit vollen Lebenspunkten aus Front- und Seitenansicht fotografieren und prüfen, ob die vier Rüstungsfugen zunächst verborgen sind.
2. Seine Gesundheit unter 70 %, 50 % und 25 % senken: Die vier Panzerungen sollten sich zunehmend öffnen und die Kristalladern freigeben, ohne an der Oberflächengeometrie zu verrutschen.
3. Im Dunkeln die schmalen Kristalladern auf selektives Leuchten prüfen. Der übrige Basaltpanzer darf nicht vollständig leuchten.
4. Den Kristallpirscher in Ruhe und bei weniger als 55 % bzw. 15 % Gesundheit beobachten: Nur die visuellen Bewegungen sollen sich ändern; Geschwindigkeit und Angriffstakte dürfen nicht beeinflusst werden.
5. Beide Kreaturen nach Speichern und Neuladen vergleichen. Ihre optischen Phasen müssen sich allein aus dem bestehenden Lebensstand korrekt wiederherstellen, ohne neue Speicherdaten.
6. Die tatsächliche In-Game-Qualität weiterhin gegen die übermittelten Referenzbilder prüfen; die technische CI ersetzt diesen Sichttest nicht.

## Aktueller Entwicklungsschritt — 1.98.0

- **13 Minecraft-Modellpixel Versatz behoben:** Ein konkreter Fehler in den vorherigen Koloss-Modellen: Der Body-Ursprung des normalen Modells befand sich bei Y = −4, der separat gebackene Leucht-Layer bei Y = +9. Beide besitzen jetzt exakt denselben Ursprung. Die Korrektur wirkt auf Kopf, Brustkern, Schwanz, Klauen, Kristallmonolithen und die sechs Resonanzrippen.
- **Kristallblende sitzt endlich vor dem Kern:** Die vier beweglichen Brustplatten aus Version 1.97 besaßen Scharniere bei Z = −28,4, während die leuchtende Vorderkante bis etwa Z = −37,1 reicht. Die Blende wurde nach vorne auf Z = −38,6 versetzt, damit sie aus der Frontansicht nicht hinter dem Kristall verschwindet.
- **Vier echte zusätzliche Einfassungen:** Rund um den Kristallkern sitzen nun vier dunkel gepanzerte Kristallhalterungen mit schmalen leuchtenden Einlagen. Die Geometrie bleibt in der Skin- und Glow-Schicht identisch an ihren Gelenken verankert, wobei dunkles Gestein nur im normalen Modell liegt.
- **Sanfte Öffnungsanimation:** Die Aufladebewegung der vier Blenden benutzt jetzt einen glatten, mathematisch begrenzten Übergang (Smoothstep). Die bestehenden synchronisierten Angriffszustände steuern weiterhin alles, ohne neue Netzwerkdaten oder Server-Ticker.
- **Bestehende Inhalte unberührt:** Keine Änderung an Infektion, Heilung, Maschinen, Pflanzen, Gegner-KI, Trefferzonen oder Boss-Schadenswerten.
- **Technische Tests:** Zusätzliche Regression für exakte Skin-/Glow-Körperwurzel, Lage der Iris relativ zur vorderen Kristallfläche, vier passende Einfassungen, aktuelle Versionsdaten und unveränderte Kampfanimationen. Forge-1.20.1-Kompilierung und JAR-Verifikation im GitHub-Workflow.
- **Visuelle Abnahme noch erforderlich:** Auch nach der Geometriekorrektur muss die tatsächliche Minecraft-Client-Darstellung überprüft werden; ein grüner Build ersetzt keine Seiten-, Front- und Kampfansichten.

### Minecraft-Client-Sichttest für Version 1.98.0

1. Kristallkoloss in der Dunkelheit aus Vorder-, Seiten- und Rückansicht prüfen. Leuchtaugen, alle Kristallspitzen und der Brustkern müssen räumlich zu den normalen Stein- und Kristallknochen passen.
2. Beim Kristallatem beobachten, ob sich die vier Blenden tatsächlich **vor** dem sichtbaren Kern öffnen und seine Farbe freigeben; kein Durchschneiden mit Kopf oder Unterkiefer.
3. Die verschiedenen Stampf- und Erwachensphasen prüfen: Öffnung und Schließen müssen sanft bleiben und ohne kumulativen Winkelversatz wieder die Ruhepose erreichen.
4. Vier Eck-Einfassungen und ihre schmalen Kristalladern im Vergleich zu dunklen Basaltplatten überprüfen. Der komplette Steinpanzer darf nicht leuchten.
5. Mit der Vorversion 1.97 vergleichen, um den korrigierten Höhenversatz und die tatsächliche Wirkung der Kristallblende sichtbar zu bestätigen.

## Aktueller Entwicklungsschritt — 1.97.0

- **Kristallkoloss: vierteilige echte 3D-Brustblende.** Vor dem bereits existierenden leuchtenden Kristallkern sitzen vier zusätzliche Basaltpanzer. Zwei seitliche und zwei vertikale Blätter können sich im Kampf synchron öffnen, wodurch die Kristallform eine deutlichere Bewegung bekommt.
- **Kampfgesten anhand echter Serverzustände.** Die Blende öffnet während der bestehenden Kristallatem-, Stampf- und Erwachensvorbereitung unterschiedlich weit. Jede Animation berechnet ihre Ausgangslage pro Frame neu und kehrt nach dem Kampf in Ruhe zurück.
- **Originale Haut- und Glow-Schichten.** Beide 256×256-Modellbäume enthalten die gleichen vier Gelenke. Die Basaltplatten erscheinen nur im normalen Modell, während die schmalen eingelegten Kristalladern die separate Leuchtschicht nutzen.
- **Kristallpirscher: einzeln bewegliche Brustsplitter.** Die zwei Kristalle am bereits vorhandenen pulsierenden Thoraxorgan besitzen jetzt eigenständige Gelenke und spreizen sich bei aggressiver Verfolgung. Im Leerlauf schließen sie sich wieder.
- **Keine neuen technischen Risiken für die Spielwelt.** Die Veränderungen betreffen ausschließlich die Client-Modellgeometrie und Animation. Boss-Hitboxen, Infektionsheilung, Feldtechnologie, Weltblöcke, Drop-Raten und Kampfschaden bleiben unangetastet.
- **Tests und Grenzen.** Neue eigene 1.97-Modellregression, Forge-Kompilierung, JAR-Verifikation und dedizierter Serverstart im GitHub-Workflow. Der echte visuelle Minecraft-Client-Test bleibt eine eigenständige Abnahme.

### Minecraft-Sichttest für Version 1.97.0

1. Den Kristallkoloss mit seiner Kristallblende direkt von vorne beobachten: vier Blätter müssen eindeutig vor dem bestehenden Brustkern sichtbar sein.
2. Kristallatem, Stampfvorbereitung und Erwachensphase auslösen, die unterschiedlichen Öffnungswinkel prüfen und darauf achten, dass die Blende nach jedem Angriff wieder schließt.
3. Im Dunkeln überprüfen, dass nur die eingelegten Kristalladern leuchten, nicht der massive dunkle Basaltpanzer.
4. Kristallpirscher aus der Nähe bei Ruhe und Verfolgung betrachten: Das pulsierende Brustorgan und seine zwei einzelnen seitlichen Splitter müssen nachvollziehbar miteinander reagieren.
5. Multiplayer, Modellbewegungen, Speicherstand und Performance im Minecraft-Client kontrollieren. Erfolgreiches Kompilieren bestätigt die technische Integration, nicht die visuelle Gleichheit mit den Vorlagen.

## Aktueller Entwicklungsschritt — 1.96.0

- **Sechs echte Seitenrippen am Kristallkoloss:** Drei Basalt-Kristall-Konstruktionen pro Körperseite erweitern die Silhouette der bestehenden vierbeinigen Boss-Entität. Jedes Bauteil hat ein eigenes animierbares Gelenk und einen schmaleren eingelegten Kristallkern.
- **Resonanz wird sichtbar:** Während der vorhandenen synchronisierten Atem-, Stampf- und Erwachensvorbereitung fächern sich die sechs seitlichen Rippen zeitversetzt auf. Im Leerlauf kehren sie zu ihrer Ausgangslage zurück.
- **Zwei passende Render-Layer:** Im normalen 256×256-Pixelatlas liegen die Basaltpanzer und violett-cyanfarbenen Kristalle; die separate Leuchtschicht übernimmt nur die schmalen leuchtenden Kernflächen. Die sechs neuen Teile sitzen an den gleichen Gelenken.
- **Neues Brustorgan des Kristallpirschers:** Ein eigener erhabener Thoraxkristall mit zwei seitlichen Splittern wird unter dem existierenden humanoiden Modellrumpf geführt. Der Brustkern pulsiert bei aggressiver Verfolgung stärker.
- **Keine Spielmechanik verfälscht:** Mutagenheilung, kontrollierte Infektionsgebiete, Maskenschutz, Boss-Drops, Bewegungsgeschwindigkeit, Gegnerhitboxen und Kampfschaden bleiben unverändert. Neue Animationen benutzen nur bestehende clientseitige Modelländerungen und synchronisierte Angriffsphasen.
- **Technische Prüfung:** 107 GitHub-Actions-Schritte erfolgreich. Eigene Modell- und PNG-Regressionen, Forge-1.20.1-Kompilierung, installierbare JAR-Prüfung und Dedicated-Server-Smoke-Test bestanden. Die tatsächliche Client-Optik muss weiterhin überprüft werden.

### Minecraft-Client-Abnahme für Version 1.96.0

1. Koloss aus der Front-, Seiten- und Rückansicht betrachten: Sind drei dunkel gefasste Kristallrippen auf jeder Seite sichtbar und ragen sie nicht absurd durch seine Vorder- oder Hinterbeine?
2. Atemangriff, Stampfen und Erwachensphase testen: Rippen müssen leicht zeitversetzt ausfächern und danach ohne Animationsdrift in die Ruhepose zurückkehren.
3. Im Dunkeln die Normal- und Leuchtschicht vergleichen: Dunkle Rippensockel dürfen nicht dauerhaft fullbright sein, die violett-cyanfarbenen Kristallkerne aber sichtbar leuchten.
4. Kristallpirscher in Ruhe und bei aggressiver Verfolgung prüfen: Brustorgan und zwei Splitter sollen mit dem Körper mitgehen und bei Verfolgung deutlich pulsieren.
5. Multiplayer-Client, Welt neu laden, Boss-Schaden, Hitboxen und Performance testen. Erst danach das Modell mit den gesendeten Referenzbildern vergleichen und verbleibende Form- und Texturabweichungen bewerten.

## Aktueller Entwicklungsschritt — 1.95.0

- **Kristallpirscher bewegt sich eigenständiger:** Bei aggressiver Verfolgung beugt er den Torso deutlich weiter vor und streckt die beiden Arme asymmetrisch aus. Vier echte Klauenknochen bewegen sich unabhängig mit versetzten Phasen. Der bestehende Rücken- und Kieferkristall bleibt eingebunden.
- **Saubere Jagd-/Ruhe-Übergänge:** Die vier Klauengelenke und die neue Jagdpose verwenden absolute statt kumulativer Bewegungswinkel. Die gewöhnliche Humanoid-Laufanimation bleibt als Basis erhalten.
- **Leuchtende Kristalladern:** Der bestehende transparente Cyan-/Magenta-Glow-Layer pulsiert sanft und leuchtet bei Aggression etwas heller, ohne den dunklen Panzer als Ganzes zu beleuchten.
- **Kristallkoloss mit Angriffs-Telegraphie:** Drei Endstachelspitzen fächern sich während des Kristallatem-Angriffs auseinander. Die beiden hohen Rückenmonolithen spreizen sich bei einem Stampf- oder Erwachens-Windup. Die zwölf echten Klauenspitzen werden während der vorbereiteten Schockwelle dezent animiert.
- **Performance und Kompatibilität:** Alle neuen animierten Gelenke werden einmalig beim Modellbau gebunden. Zwei Modellschichten benutzen dieselben vorhandenen synchronisierten Angriffsphasen; keine neuen Server-Ticker, Netzwerkpakete, Schadenserhöhungen oder geladenen Chunks.
- **Teststand:** Zusätzlicher Regressionstest für vier Stalker-Klauen, drei Stacheln, zwölf Boss-Klauen, Monolithen und synchrone Windups. Forge-Build/JAR-Prüfung bestanden. Client-Sichtabnahme folgt weiterhin separat.

### Minecraft-Client-Sichtprüfung für Version 1.95.0

1. Kristallpirscher in Ruhe und beim Verfolgen von Spielern beobachten: Der Torso soll sich nach vorne beugen, die Arme unterschiedlich weit ausgreifen und die vier Talons zurückfedern.
2. Im Dunkeln kontrollieren, dass nur die Kristalladern pulsieren, nicht die ganzen Panzerflächen.
3. Den Koloss aus Seiten- und Rückansicht beim Kristallatem beobachten: Drei Stachelspitzen am Schwanz müssen sich öffnen und nach dem Angriff wieder schließen.
4. Während des Stampf-Windups die Rückenmonolithen und zwölf Klauenspitzen beobachten; anschließend Stand und Bewegung auf Aussetzer, Textursprünge oder versetzte Glow-Ebenen prüfen.
5. Multiplayer, Weltladen und Schadenswerte testen. Eine erfolgreiche automatische Kompilierung beweist nicht die gewünschte optische Qualität im Minecraft-Client.

## Aktueller Entwicklungsschritt — 1.94.0

- **Eigenständiger Kristallpirscher-Umriss:** Zur echten Forge-3D-Kreatur kommen zwei verschieden hohe, gestufte seitliche Rückenflossen mit dunklen Mineraleinfassungen hinzu. Ein neues asymmetrisches Kieferkristallorgan gibt dem Kopf eine zusätzliche nicht-Vanilla-Form.
- **Animierte Kristallgelenke:** Die beiden Flossen sind echte Modellknochen, schwingen beim Gehen, spreizen sich in aggressiver Haltung und berechnen ihre Ausgangslage für jeden Animationsframe erneut. Auch der Kieferkristall ändert seine Pose beim Angreifen.
- **Selektiv leuchtende Textur:** Der ursprüngliche Kristallpirscher-Skin und die bisherige 128x128-UV-Struktur bleiben erhalten. Neue violett/cyanfarbene Pixelbereiche auf zuvor freien UV-Flächen werden mit einer schmalen, transparenten Emissivmaske ergänzt.
- **Zwölf facettierte Klauenspitzen für den Kristallkoloss:** Alle vier beweglichen Pfoten bekommen je drei zusätzliche, zweistufige Minecraft-ModelParts. Die Haupt- und Leuchtmodelle verwenden gleiche Gelenke, damit die neuen Klauen bei der gewichtigen Lauf- und Stampfanimation folgen.
- **Technisch geprüft:** Der Forge-1.20.1-Build wurde erfolgreich erstellt, die installierbare JAR verifiziert, die eigene Kristallanatomie-Regression zusammen mit allen bisherigen Tests bestanden und ein dedizierter Minecraft-Server erfolgreich gestartet. GitHub Actions: 105 grüne Schritte.
- **Grenze der Prüfung:** Die In-Game-Darstellung ist noch nicht per echtem Minecraft-Client-Screenshot bewertet. Technische Modellbäume und valide Texturen bedeuten nicht automatisch, dass Form, proportionierte Leuchtbereiche und Animation exakt den hochgeladenen Vorlagen entsprechen.

### Minecraft-Client-Abnahme für 1.94.0

1. Kristallpirscher mit Spawn-Ei erstellen, drei Perspektiven prüfen, vor allem ungleiche Rückenflossen und Kieferkristall.
2. Herumlaufen und Angriff provozieren: Kristalle dürfen weder starr an der alten Weltposition bleiben noch Körperteile durchschneiden; die Leuchtschicht soll nur die cyan-violetten Adern beleuchten.
3. Kristallkoloss erstellen: alle vier Pfoten und je drei facettierte neue Klauenspitzen kontrollieren.
4. Die Lauf- und Stampfanimation und die drei Phasen des Schwanzes prüfen; Texturen dürfen nicht verrutschen und die neue Glow-Geometrie soll am jeweiligen Knochen bleiben.
5. Erst anhand echter Client-Bilder mit den Referenzen entscheiden, welche Anatomie und Pixeloberflächen weiter verfeinert werden müssen.

## Aktueller Entwicklungsschritt — 1.93.0

- **Kristallpirscher jetzt als echtes 3D-Monster:** Der Renderer verwendet einen eigenen gebackenen Forge-ModelLayer. Anstelle der einfachen Vanilla-Zombie-Körperform kommen große asymmetrische Rückenwucherungen, markante Kopfkristalle, mineralische Gesichtsmaske, schwere Schulterplatten und verlängerte Cyan-Kristallklauen hinzu. Die zuverlässige Vanilla-Lauf- und Angriffsanimation wird als Basis erhalten.
- **Lebendige Wucherungen:** Eigene animierte Modellknochen bewegen Rücken, Schultern und Kopfkristalle beim Laufen. In aggressiver Haltung beugt sich der Kristallpirscher stärker vor.
- **Eigenes selektives Leuchten:** Originaler 128×128-Pixelatlas plus eine zweite transparente Emissiv-Textur, die nur Cyan-Adern, Kristalle und Augen beleuchtet, nicht die dunklen Steinflächen.
- **Bewährte Spielmechaniken:** Tier-III-Mutagenfeld-Spawn, Maskenschutz gegen Giftangriffe, Beute, Heilung auf Mutagenboden und Forschung funktionieren unverändert.
- **Qualität und Ressourcen:** Forge-Java-Kompilierung, separate Pixel-/Layer-Regressionsprüfungen, Paketprüfung der neuen Klassen und PNGs, dedizierter Serverstart sowie 104 erfolgreiche GitHub-Actions-Schritte. Ein instabiler Vanilla-Minecraft-Asset-Download wurde beim Server-Smoke-Test separat mit einem begrenzten Retry abgesichert.
- **Noch offene visuelle Abnahme:** Die tatsächliche Darstellung und Animation im Minecraft-Client muss mit den Nutzerreferenzen verglichen werden; ein erfolgreicher automatisierter Serverbuild weist die Optik nicht nach.

### Minecraft-Client-Test für 1.93.0

1. Den Kristallpirscher mit seinem Spawn-Ei erstellen und aus Vorder-, Seiten- und Rückansicht auf Kristallpanzer, Kopf- und Klauensilhouette prüfen.
2. Bewegungen und Angriffshaltung betrachten: Der Rückenkamm und die Schulterwucherungen müssen mit dem Körper mitlaufen und dürfen nicht abreißen.
3. Nachts ohne direkte Beleuchtung prüfen, ob nur Kristalladern/Augen leuchten und der dunkle Panzer nicht unnatürlich vollhell erscheint.
4. Auf Tier-III-Mutagenboden Spawns, Giftschaden, Filtermaske und Drops prüfen, anschließend Multiplayer und Weltneuladen testen.
5. Screenshots mit den eingesandten Konzeptvorlagen vergleichen, bevor die endgültige visuelle Gleichheit freigegeben wird.

## Aktueller Entwicklungsschritt — 1.92.0

- **Tatsächliche In-Game-Geometrie:** Das bereits existierende Kristallkoloss-Modell bekommt neue Würfelgeometrie, nicht nur eine Illustration oder zusätzliche Partikel.
- **Neuer Schwanz-Umriss:** Ein hochgebogener Skorpionschwanz aus den drei bestehenden animierten Schwanzgliedern und einem neuen vierten Gelenk. Am Ende sitzt eine dreizackige, magenta-violette Kristallblüte mit eigenem Bewegungsverhalten während der Kristallatem-Attacke.
- **Massive Rückenpanzer:** Zwei hohe, seitliche Obsidianmonolithen tragen große Kristallspitzen und kleine bernsteinfarbene Resonanzadern. Bereits bestehende bewegliche Kopfkrone, Brustkern, Glühklauen und Bossangriffe bleiben erhalten.
- **Getrennte Pixel- und Emissiv-Atlanten:** Originale 256×256-PNG-Texturen mit neuem violett-orangen UV-Bereich. Der dunkle Panzer bleibt unbeleuchtet; neue Kristalle und Adern besitzen eng angepasste Glow-Geometrie.
- **Animation ohne Fremdabhängigkeiten:** Beide ModelPart-Bäume besitzen deckungsgleiche Ansatzpunkte und bewegen sich über die vorhandene synchronisierte Bossanimation; keine Kopie fremder Mod-Modelle oder Texturen.
- **Build verifiziert:** 103 erfolgreiche Workflow-Schritte, eigene Modell-/Pixel-Regression, Forge-1.20.1-JAR-Prüfung sowie dedizierter Server-Smoke-Test.
- **Noch nicht bestätigt:** Das tatsächliche Aussehen im laufenden Minecraft-Client wurde nicht bildlich abgenommen. Die In-Game-Silhouette muss mit den eingesandten Referenzbildern verglichen und nötigenfalls weiter überarbeitet werden.

### Minecraft-Client-Sichttest 1.92.0

1. Den Koloss im Creative-Modus oder über das Bossritual herbeirufen und aus Front-, Seiten- und Rückansicht kontrollieren: Schwanzbogen und Kristallblüte dürfen nicht in den Körper schneiden oder unnatürlich flach bleiben.
2. Sehen, ob die hohen Rückenmonolithen bei Bewegungen stimmig wirken und die Magenta-Kristalle sowie orange Adern sichtbar sind.
3. Bei Bewegung und Kristallatem die Synchronisation von dunklem Skin und Glow-Schicht testen; besonders auf versetztes Leuchten oder transparente Texturartefakte achten.
4. Speicherstand neu laden und Spawn-/Bosskampf sowie die vorhandene Kernöffnung und Stampfphase prüfen.
5. Gegenüber dem Referenzdesign gezielt noch fehlende Anatomie, Texturdichte und Animation erfassen. Ein grüner Forge-Build ist kein visueller Gleichheitsnachweis.

## Aktueller Entwicklungsschritt — 1.91.0

- **Dreistufige Koloss-Ankunft:** Die Boss-Entität löst auf ihrem vorhandenen Server-Tick drei nicht-schädliche Resonanzwellen mit wachsenden Kristallringen, schwebenden Sporen und gestaffelten Klängen aus. Spieler in der Nähe werden einmalig gewarnt.
- **Persistente Ankunft:** Die durchlaufene Auftrittsstufe wird im Boss-NBT gesichert. Bereits vollständig gesehene Auftritte starten beim erneuten Laden des Bosses nicht neu.
- **Echte Dämmerling-Überfälle:** Bei einer tatsächlich begonnenen Fraßattacke entsteht nun eine Spielerwarnung im Umkreis von 12 Blöcken. Ein 200-Tick-Cooldown pro Spieler verhindert Textspam, wenn mehrere Dämmerlinge gleichzeitig angreifen.
- **Verbesserte Feldstation:** Der Bericht zeigt nicht nur anwesende Dämmerlinge, sondern warnt separat vor Kreaturen, die gerade tatsächlich an Pflanzen fressen. Die Zähler verwenden dieselbe einzelne manuelle Entity-Abfrage.
- **Bestehende Systeme erhalten:** Seelenlaterne, Filtermoos, Koloss-Angriffsfenster, Sprung-Ausweichen beim Stampfen, Kupfererdung, Amethystneustart, Not-Aus und die Automationssignale bleiben verfügbar.
- **Technische Prüfung:** Alle 102 GitHub-Actions-Schritte bestanden: Quellcode-Regressionen, Forge-1.20.1-Build, JAR-Verifikation, dedizierter Serverstart und Artefakt-Paketierung.

### Manueller Minecraft-Client-Test für 1.91.0

1. Den Kristallkoloss über sein Survival-Ritual herbeirufen und prüfen, ob drei getrennte Wellen und die Warnmeldung tatsächlich sichtbar und hörbar sind.
2. Die Welt nach dem vollständig abgespielten Auftritt speichern und neu laden: Die drei Ankunftswellen dürfen nicht erneut beginnen.
3. Dämmerlinge an einem dunklen, reifen Beet beobachten: Die Spielerwarnung muss beim Fraß auftreten, nicht bloß beim Herumlaufen.
4. Mit der Kontrollstation prüfen, ob laufende Fraßattacken gesondert gezählt werden, ohne den normalen Scan oder die Sicherheitsaktionen zu verändern.
5. Multiplayer-Funktion, Darstellung, Klangreichweite und Serverleistung im Minecraft-Client prüfen. Automatisierte Regressionen ersetzen diesen Sichttest nicht.

## Aktueller Entwicklungsschritt — 1.90.0

- **Dämmerling-Überfall mit Warnsignalen:** Beim Fraß an einer reifen Sporenwerk-Pflanze erscheinen vor dem bisherigen 30-Tick-Biss zwei zeitlich getrennte violette Geistersporen- und Seelenflammenimpulse mit gedämpftem Kristallklang.
- **Seelenlaterne zur aktiven Verteidigung:** Eine gehaltene Seelenlaterne in Haupt- oder Nebenhand kann innerhalb von ungefähr vier Blöcken einen bereits laufenden Fraßversuch abbrechen. Sie wird nicht verbraucht; der Dämmerling erhält 120 Ticks Pause von der Futtersuche. Seine normale Aggression gegenüber Spielern bleibt bestehen.
- **Neuer Forschungsschritt:** Für das tatsächliche Retten eines bedrohten Beets wird die Advancement „Licht gegen den Wildwuchs“ vergeben, nie für bloßes Halten einer Laterne.
- **Nachtwache im Stationsbericht:** Der normale Stationsscan meldet nun lebende Dämmerlinge in der Umgebung und erklärt die mobile Verteidigung. Copper-Rescue, Amethyst-Neustart, Not-Aus und cached Comparator bleiben unberührt.
- **Sicherheitsgrenzen:** Bereits geladene Chunks, bestehende Filtermoos-Abwehr und Beleuchtung, kein neuer Welt-Ticker oder stationärer Entity-Ticker. Spätere Wiederholungsversuche werden gedrosselt.
- **Technischer Nachweis:** Alle 101 GitHub-Actions-Schritte, Forge-Kompilierung, JAR-Dateiprüfung und dedizierter Server-Smoke-Test bestanden.

### Manueller Minecraft-Client-Test für 1.90.0

1. Nachts ein dunkles, reifes Sporenwerk-Beet mit einem Dämmerling in der Nähe beobachten; zwei Vorwarnungen vor einem möglichen Fraß prüfen.
2. Während eines Fraßversuchs eine **Seelenlaterne in der Hand** nahe beim Beet tragen; Abbruch, Partikel, Pause und den ersten Forschungsfortschritt prüfen.
3. Mit normaler Laterne, leerer Hand und größerer Entfernung vergleichen; danach ein bereits beleuchtetes oder durch Filtermoos geschütztes Beet prüfen.
4. Die Feldkontrollstation bei an- und abwesenden Dämmerlingen normal anklicken; nachprüfen, dass geduckte Kupfer-, Amethyst- und Not-Aus-Bedienung weiterhin funktionieren.
5. Multiplayer, Speichern/Neuladen und Minecraft-Dedicated-Server-Verhalten im echten Spiel prüfen. Ein erfolgreicher automatischer Serverstart ersetzt diese Sicht- und Spieltests nicht.

## Aktueller Entwicklungsschritt — 1.89.0

- **Knotenrettung statt bloßer Notabschaltung:** Geduckt mit einem Kupferbarren auf die Mutagen-Feldkontrollstation rechtsklicken, um aktive, ungepauste AUSBREITUNG-Knoten in sicheren ANBAU umzuwandeln. Der Barren bleibt erhalten.
- **Sterilisierung und Redstone bleiben geschützt:** Gespeicherte inaktive/geheilte Quellen werden nicht wieder eingeschaltet. Pausierte, bereits kultivierende oder ruhende Knoten werden nicht verändert.
- **Forschung und direkte Spielrückmeldung:** Bei der ersten tatsächlich erfolgreichen Umwandlung wird der Fortschritt „Aus Gefahr wird Wachstum“ freigeschaltet. Grüne Wachstumspartikel, dezente Kristalllichter, Klang und DE/EN-Rückmeldung begleiten die Aktion.
- **Vier Eingriffe an einer Station:** Rechtsklick = Diagnose, Schleichen = Not-Aus, Schleichen plus Amethyst = Neustart ruhender sicherer Quellen, Schleichen plus Kupfer = gezielte Rettung gefährlicher aktiver Quellen.
- **Gleiche Sicherheitsgrenzen:** Nur geladene Chunks im Radius 16 / Höhe ±8, maximal 24 betroffene Knoten mit Partikeln, kein Chunk-Forceloading und kein neuer Stations-Ticker. Beide Anbauaktionen teilen eine einzelne geplante Node-Tick-Routine.
- **Status:** Forge-1.20.1-Build, Regressionen, JAR-Prüfung und Dedicated-Server-Smoke-Test wurden in GitHub Actions erfolgreich abgeschlossen. Ein Minecraft-Client-Sichttest steht weiterhin aus.

## Aktueller Entwicklungsschritt — 1.88.0

- **Mutagen-Knotenprotokoll:** Die Feldkontrollstation zählt beim normalen Rechtsklick fünf tatsächlich unterschiedliche Betriebszustände: ungebremste AUSBREITUNG, sicherer ANBAU, RUHE, Redstone-pausierte Quellen und gespeicherte inaktive/sterilisierte Quellen.
- **Quellen statt Bodenfarben:** Der neue Bericht prüft die echte aktive Knotenregistrierung aus den gespeicherten Welt-Daten. Damit werden endgültig inaktive Quellen nicht fälschlich als aktive Gefahr angezeigt.
- **Handlungsempfehlung:** Bei aktiv ausbreitenden Knoten erscheint eine deutliche Warnung mit Notabschaltungshinweis. Sind nur kontrollierte Anbauknoten aktiv, wird dies als kontrollierter Betrieb gemeldet; sonst zeigt die Station einen Ruhehinweis.
- **Sicheres System:** Kein Neustart und keine Blockänderung beim Scan; der bestehende Comparator-Ausgang, Not-Aus per Schleichen und sicherer Neustart mit Amethystscherbe bleiben unverändert. Redstone-Pause und die globale Endspiel-Heilung werden respektiert.
- **Performance und Sicherheit:** Die fünf Zähler werden innerhalb des bereits bestehenden manuellen Stationsscans erfasst – kein zweiter Flächenscan, kein neuer Dauer-Ticker, keine Chunk-Forceloads. Nur geladene Blöcke im bekannten Radius 16 und Höhe ±8 werden untersucht.
- **Qualitätsprüfung:** Eigene Regression für alle fünf Kategorien, gespeicherte Aktivität, Warntexte, Loaded-Chunk-Grenzen, bestehende Steuerfunktionen und Versionsdaten; vollständiger Forge-Build und dedizierter Serverstart prüfen die Integration.

## Aktueller Entwicklungsschritt — 1.87.0

- **Sicherer Wiederanlauf kontrollierter Mutagenanlagen:** Geduckt mit einer Amethystscherbe in der Hand auf die Feldkontrollstation rechtsklicken: Nur bisher ruhende und noch aktive Mutagenknoten innerhalb Radius 16 / Höhe ±8 werden auf ANBAU zurückgestellt.
- **Not-Abschaltung und Diagnose bleiben intakt:** Geduckter Rechtsklick ohne Amethystscherbe legt wie in 1.84 alle Knoten still; normaler Rechtsklick erstellt weiterhin den vorhandenen Forschungsbericht.
- **Welt-Heilung wird nicht rückgängig gemacht:** Die Station prüft die gespeicherte aktive Quellenregistrierung. Inaktive beziehungsweise endgültig geheilte Quellen können durch den Neustart nicht wieder eingeschaltet werden.
- **Nie aggressive Ausbreitung:** Der Neustart setzt ausschließlich den vorhandenen Kultivierungsmodus. Bereits aktive Quellen in anderen Modi werden nicht verändert. Redstone-Pausen bleiben unverändert.
- **Gute Bedienung:** Die Amethystscherbe wird nicht verbraucht. Eine Zählmeldung, dezente grüne Partikel, Amethystklang und die Anleitung im Stationsbericht erklären den sicheren Vorgang auf Deutsch und Englisch.
- **Performance:** Ein einmaliger, kreisförmiger Loaded-Chunk-Scan ohne Dauer-Ticker und mit begrenzten Partikeln; vorhandene Anbau-Ticks werden nur bei Redstone-freien Quellen neu geplant.

## Aktueller Entwicklungsschritt — 1.86.0

- **Dämmerling reagiert auf Blickkontakt:** Wer dem Dämmerling nachts im Dunkeln direkt in die Augen sieht und sein aktuelles Angriffsziel ist, kann ihn kurzzeitig zum Stehen bringen. Der Mob verfolgt den Spieler dabei mit seinem Blick statt sich auf ihn zuzubewegen.
- **Echte Gefahr nach dem Stillstand:** Spätestens nach 30 Ticks (1,5 Sekunden) endet die Starre; anschließend verhindern 100 Ticks Abklingzeit eine endlose Stilllegung durch ständigen Blickkontakt. Wegschauen beendet die Starre sofort.
- **Kein unfairer Fernstopp:** Nur Spieler im Abstand von höchstens 12 Blöcken mit echter Sichtlinie und Blickrichtung auf den Mob lösen die Reaktion aus. Kreativ- und Zuschauermodus werden ignoriert.
- **Horror-Feedback:** Ein kurzer violetter Partikelimpuls, ein tiefes Kristallklirren und eine spielerbezogen gedrosselte Aktionsleistenmeldung machen die Begegnung verständlich, ohne den Bildschirm permanent mit Text zu füllen.
- **Farm- und Kampfregeln bleiben:** Normales Zombie-Targeting, schwache Dämmerling-Schadenswerte, langsame dunkle Pflanzenangriffe, beleuchtete oder abgeschirmte Beete, Mutagenblüten und Sporenabwehr bleiben unverändert.
- **Performance und Sicherheit:** Ein priorisiertes Standard-Zombie-KI-Ziel statt eines zusätzlichen Entity-Tickers. Sichttests sind auf den aktuellen Angriffsspieler, 12 Blöcke, 5-Tick-Prüfintervalle und eine kurze Ereignisdauer begrenzt.
- **Qualität:** Regression prüft KI-Prioritäten, Dot-Product-Sichtprüfung, Zielprüfung, Timeouts, Erhaltung bestehender Ziele und DE/EN-Texte. Der vollständige Forge-Build und dedizierte Serverstart prüfen die Integration.

## Aktueller Entwicklungsschritt — 1.85.0

- **Lebendige Horror-Mutagenfelder:** Mutagenknoten im SPREAD-Modus können nachts selten einen flüsternden Feldimpuls abgeben. Aufsteigende Sporen, spiralig gesetzte Seelenflammen und rückwärts strömende Portalpartikel erzeugen ein unheimliches Umgebungsbild mit tiefem Resonanzton.
- **Feldwirtschaft behält ihre Identität:** CULTIVATION erzeugt stattdessen sanfte grüne Partikel, Sporen und leises Kristallklingen, ohne Spieler zu gefährden oder die sicheren Mutagen-Farmregeln zu umgehen.
- **Echte Ruhe bleibt ruhig:** DORMANT und durch Redstone pausierte Knoten bleiben vollständig still, weil die Effekte nur im bestehenden aktiven, geplanten Server-Tick auftreten.
- **Multiplayer und Leistung:** Ein gespeicherter Cooldown pro Spieler begrenzt wiederholte Impulse aus dicht nebeneinander stehenden Knoten. Der Knoten prüft die Anwesenheit von Spielern nur nach seltener Zufallsauswahl; es gibt keine zusätzliche Hintergrundtick-Logik und keine Chunk-Forceloads.
- **Integrierte Atmosphäre:** Die Effekte ergänzen die bereits unterschiedlichen Minecraft-Blockmodelle, Mutagenblüten und Feldwarngeräte. Bestehende Ausbreitungs-, Mutations-, Ernte- und Heilungsmechaniken bleiben unverändert.
- **Qualitätsprüfung:** Separate Regression prüft die aktiven Knotenmodi, Nachtbedingung, Partikel, Sounds, Multiplayer-Cooldown, Inaktivität und alte Sicherheitsregeln; kompletter Forge-Build und dedizierter Serverstart prüfen die technische Integration.

## Aktueller Entwicklungsschritt — 1.84.0

- **Notabschaltung an der Kontrollstation:** Geduckter Rechtsklick versetzt sämtliche geladenen Mutagenknoten im bestehenden Scanradius 16 (Höhe ±8) in den RUHE-Modus. Ein normaler Rechtsklick liefert weiterhin den gewohnten Diagnosebericht.
- **Kein versehentlicher Neustart:** Der RUHE-Modus ist ein bereits vorhandener persistenter Blockzustand. Die vorhandene Spread- und Cultivation-Logik respektiert diesen Zustand sowohl bei geplanten als auch zufälligen Ticks. Die zuvor gewählten Modi werden nur durch manuelles Bedienen einzelner Knoten wieder verändert.
- **Bestehende Feldinfrastruktur bleibt:** Abschalten ist kein globaler Sterilisierungsprozess. Stabilisatoren, Sporenabwehrsender, Forschungsrelais und kontrollierte Anbauflächen bleiben erhalten; Knotenregistrierung und Redstone-Status bleiben unverändert.
- **Klare Rückmeldung:** Die Station meldet die tatsächlich stillgelegte Knotenzahl, zeigt begrenzte Rauchpartikel und warnt ausdrücklich vor ungeladenen Chunks. Das normale Stationsprotokoll erklärt die neue Bedienung.
- **Sicherheit und Performance:** Ein einmaliger, kreisförmiger, höhenbegrenzter Scan mit vorheriger Loaded-Chunk-Prüfung, maximal 24 visuellen Knotenrückmeldungen und keinen neuen Tick-Schleifen. Eigene Regression und vollständiger Forge-Build prüfen die Integration.

## Aktueller Entwicklungsschritt — 1.83.0

- **Bodenerschütterung mit Vorwarnung:** Der Kristallkoloss erzeugt beim Stampfen drei deutlich sichtbare, ringförmige Warnpulse aus Partikeln. Der normale Radius beträgt 5,8 Blöcke, beim Erwachen 7,2 Blöcke.
- **Ring entspricht Trefferbereich:** Eine runde Distanzprüfung ersetzt das alte rechteckige Treffergebiet. Wer außerhalb des sichtbaren Warnkreises steht, wird vom Stampfen nicht getroffen.
- **Ausweichmechanik:** Wer rechtzeitig springt und bei der Auslösung nicht am Boden steht, kann die bodengebundene Erschütterung vermeiden. Schaden und Rückstoß für getroffene Ziele bleiben unverändert.
- **Aufprall mit zwei Leuchtwellen:** Beim Stampfstoß laufen ein innerer und ein äußerer Kristall-Partikelring über den Boden. Die Umgebung wird nicht abgebaut oder beschädigt.
- **Technische Qualität:** Nur vorhandene Bossangriffs-Ticks und standardmäßige Minecraft-Partikel; keine Blockänderungen, Chunk-Forceloads oder zusätzlichen Dauer-Ticker. Regression prüft Treffergeometrie, Ausweichmechanik, Warnzeitpunkte und unveränderte Kampfwerte; der Forge-Build und Serverstart prüfen die Integration.

## Aktueller Entwicklungsschritt — 1.82.0

- **Schwere vierbeinige Fortbewegung:** Diagonale Beinpaare des Kristallkolosses laufen in gegenläufigen Phasen; Oberschenkel, Unterschenkel und Tatzen besitzen eigene Bewegungsmuster.
- **Stand und Schwung statt Pendelgang:** Im Schwung wird eine Tatze leicht angehoben und nach vorn geführt. Während der Standphase bleibt sie näher am Boden. Die bisherigen starren Beinpendel sind ersetzt.
- **Körpergefühl:** Subtiles seitliches Schulterwiegen, Gegenrotation von Kopf und Kristallkrone sowie zeitversetzte Gegenschwünge in allen drei Schwanzsegmenten.
- **Kampf bleibt unterscheidbar:** Während des Stampfangriffs werden die Vorderpfoten unabhängig vom Laufschritt stabilisiert. Die bestehenden Biss-, Atem- und Erwachensanimationen sowie die Schadenswerte bleiben erhalten.
- **Technische Sicherheit:** Haut- und Glow-Modelle teilen sich die vorhandene Beinkette. Kein neuer Mob-Ticker, keine externen Animationsdateien und kein Chunk-Loading. Regressionen und vollständiger Forge-Build prüfen die Integration; ein Sichttest im Client steht aus.

## Aktueller Entwicklungsschritt — 1.81.0

- **Beweglicher Unterkiefer:** Der Kristallkoloss erhält ein echtes Kiefergelenk statt einer fest am Schädel liegenden Unterkieferfläche. Die bisherigen Gesteinsplatten wurden an den beweglichen Teil gebunden.
- **Leuchtende Kristallzähne:** Kleine fangartige Kristalle und das Maulleuchten bewegen sich in einem deckungsgleichen Emissiv-Modell mit dem echten Kiefer.
- **Erkennbarer Kristallatem:** Über die bestehende, synchronisierte 48-Tick-Angriffsphase öffnet der Boss sein Maul zunehmend. Die bisherigen Atem-Partikel entstehen jetzt vor seiner Schnauze und verdichten sich während des Aufladens, statt im Rumpf zu erscheinen.
- **Zusätzliche Phasenanimation:** Bei der Verwandlung reißt der Koloss das Maul stoßweise weiter auf; bei Stampfangriffen spannt sich der Kiefer.
- **Sicherer Ausbau:** Forge-ModelParts ohne zusätzliche Animationsbibliothek, bestehende Schadens- und Reichweitenlogik unverändert, keine neuen Chunkzugriffe, DE/EN-Texturassets beibehalten. Regressionen, Forge-Build und Server-Smoke-Test prüfen die Integration.

## Aktueller Entwicklungsschritt — 1.80.0

- **Kristallkoloss: mehr als nur eine Textur:** Zwei weit ausgreifende, dreistufige Kristallkronen flankieren jetzt den Kopf. Dunkle Wangenpanzer verbinden sie sichtbar mit Schädel und Hals.
- **Getrennte, deckungsgleiche Leuchtschicht:** Die neuen Kristalle besitzen innere Emissiv-Geometrie, während ihre dunklen Gesteinsfassungen unbeleuchtet bleiben. Haupt- und Glow-Layer verwenden dieselben Knochenpositionen.
- **Bewegte Anatomie:** Beide Kristallflügel atmen subtil im Leerlauf, fächern bei Atemangriffen auf und entfalten sich stärker beim Erwachen. Jede Animation setzt ihre Drehungen neu und wird auf Client und Glow-Layer identisch berechnet.
- **Eigene Gestaltung:** Die Forge-ModelParts und Bewegungen sind neu für Sporenwerk erstellt. Die beiden hochgeladenen Fremdmods wurden nur hinsichtlich technischer Struktur, Animationsumfang und Texturdichte untersucht; ihre Ressourcen werden nicht übernommen.
- **Qualität:** Eine eigene Regression prüft beide Modellbäume, Animation, Angriffsphasen, Versionsstand und Ressourcen. Der Forge-Build und der Serverstart sichern die technische Integration; die tatsächliche Bildwirkung muss im Minecraft-Client geprüft werden.

## Aktueller Entwicklungsschritt — 1.79.0

- **Automatisierte Verwertung von Pflanzenresten:** Der Biomasse-Bioreaktor wandelt vier Pflanzenreste für 60 FE in eine Biomasse um. Das erweitert die bestehende Verarbeitung von Biomasse zu zwei Myzelkompost für 80 FE.
- **Geschlossener Farmkreislauf:** Der Feldsammler liefert bei reifen Kulturen gelegentlich Pflanzenreste; der Bioreaktor macht daraus Biomasse und anschließend Dünger. Das ergänzt die Handwerksrezeptur, ohne sie zu entfernen.
- **Saubere Transaktion:** Weniger als vier Reste, ein voller Ausgabepuffer oder fehlende Energie verbrauchen keine Eingabe. Das Produkt wird eingefügt, bevor die Reste aus dem Eingabestapel entfernt werden.
- **Erklärtes Item:** Pflanzenreste haben einen deutschen und englischen Tooltip, der Menge, Energiepreis und nächsten Verarbeitungsschritt nennt.
- **Qualität:** Regression prüft beide Bioreaktor-Stufen, Reihenfolge der Transaktion, Übersetzungen, Itemregistrierung und Release-Metadaten; Forge-Build und dedizierter Serverstart laufen im Workflow.

## Aktueller Entwicklungsschritt — 1.78.0

- **Zweite Schutzroute:** Eine aktive Sporenabwehr schützt nicht nur vor dem Blütenimpuls, sondern dokumentiert den tatsächlichen Abfang als eigenständigen Forschungsfortschritt.
- **Forschungsbelohnung nur bei Erfolg:** Die neue Advancement wird ausschließlich dann vergeben, wenn eine Mutagenblüte ausgelöst wurde und die Sporenabwehr den Impuls für diesen Spieler tatsächlich abfängt. Reines Platzieren oder Einschalten reicht nicht.
- **Neue Fortschrittsverzweigung:** „Leise Wurzeln“ gewährt einmalig zwei Feldwissen und einen Myzelkompost. Die bestehende Route „Stiller Ausbruch“ für den ladungsverbrauchenden Resonanzdämpfer bleibt getrennt.
- **Ökologie + Containment:** Der Belohnungspfad verbindet den Blüten-Event, die echte Ward-Reichweite, den Forschungsbaum und die bestehende Farm-/Kompostproduktion.
- **Sicherer Ablauf:** Serverseitige Vergabe, vorhandener Blüten-Cooldown und bestehende Chunk-Grenzen bleiben erhalten; kein zusätzlicher Tick-Loop.
- **Qualität:** Advancement-Schema, Loot-Tabelle, deutsche/englische Texte, bestehende Dämpfer- und Ward-Regressionen, Forge-JAR und dedizierter Serverstart werden geprüft.

## Aktueller Entwicklungsschritt — 1.77.0

- **Symbiose als Redstone-Signal:** Das Containment-Relais erhält Modus 8 für die Zahl reifer Erntezentren, die drei Sporenwerk-Arten in unmittelbarer Nähe und ein aktives Mutagenfeld der Stufe II/III besitzen.
- **Direkte Farm-Automation:** Der Comparator gibt 0 aus, wenn keine passenden Erntezentren bereit sind, und 1–15 entsprechend der Zahl erkannter reifer Zentren (bei 15 gedeckelt). So können Sortierer, Lampen, Trichter-Taktung oder Farm-Stoppschaltungen reagieren.
- **Echte Laufzeitbedingungen:** Die Prüfung verwendet die vier registrierten Sporenwerk-Arten und die aktuelle Feldstärke, nicht bloß eine gespeicherte Feldfarbe oder globale Pflanzenzahl.
- **Ereignisgesteuert:** Pflanzen, reife Ernte und Pflanzenentfernung aktualisieren nahe Relais, ohne neue Dauer-Ticker einzubauen. Der Scan bleibt auf geladene Chunks begrenzt.
- **Qualitätssicherung:** Alle 144 Relais-Blockzustände, DE/EN-Beschriftung, Wachstums-/Pflanzenänderungsereignisse, Chunk-Sicherheit und Release-Metadaten werden geprüft.

## Aktueller Entwicklungsschritt — 1.76.0

- **Bessere Feldkontrolle:** Die Kontrollstation meldet jetzt Kulturvielfalt und reife Pflanzen, nicht nur die Zahl mutagenaktiver Pflanzen.
- **Symbiose-Diagnose:** Reife Erntezentren werden gegen die echte lokale Artenvielfalt und aktuelle Feldstärke II/III geprüft.
- **Direkte Lernhilfe:** Die Station erklärt, wie aus einer passenden Kultur Symbiosemyzel und danach Resonanzsporen-Kapseln gewonnen werden können.
- **Containment bleibt bounded:** Bestehender Scanradius, geladene Chunks, Stabilisatornetz, Sporenabwehr und Dämpferbericht bleiben erhalten.

## Aktueller Entwicklungsschritt — 1.75.0

- **Sporenpflege:** Die neue Resonanzsporen-Kapsel beschleunigt kontrolliert das Wachstum unreifer Sporenwerk-Pflanzen.
- **Containment-Wartung:** Dieselbe Kapsel lädt Resonanzdämpfer um eine Stufe nach, ohne bei vollem Gerät verbraucht zu werden. Verbundene Relais erhalten ein Update.
- **Kreislauf:** Seltenes Symbiosemyzel und mutagene Sporen aus der Feldernte werden zu einer handlichen Ressource für Farmen und Sicherheitsanlagen.
- **Qualität:** Eigene Itemtextur, Crafting-Rezept, Übersetzungen, Advancement, Regressionen, Forge-JAR- und Serverstartprüfung.

## Aktueller Entwicklungsschritt — 1.74.0

- **Leuchtender Kristallkern:** Das Kristallkern-Bild ist als transparentes 16×16-Minecraft-Item eingebunden und wird als garantierte Endgame-Beute des Kristallkolosses vergeben.
- **Resonanzimpuls:** Rechtsklick trifft bis zu vier nahe sichtbare Mutagengegner, mit Abklingzeit und serverseitiger Zielprüfung.
- **Gegen die Boss-Angriffsfenster:** Der Impuls kann Stampf- und Atemaufladungen des Kristallkolosses beenden; außerhalb solcher Aufladungen unterbricht er keine Bossphase.
- **Visual QA und Inhalt:** Itemmodell, Tooltip, DE/EN-Texte, Fund-Advancement und JAR-Prüfung sind Bestandteil des Build-Workflows.

## Aktueller Entwicklungsschritt — 1.73.0

- **Resonanzverdichtung:** Die Stärke an einer Position wird aus allen dort wirksamen, tatsächlich aktiven Quellen ermittelt. Ab zwei überlappenden Quellen kommt eine Stufe hinzu, gedeckelt auf III.
- **Ökologie und Darstellung verbunden:** Stärkestufen fließen in die vorhandenen Pflanzenphänotypen, den Feldscanner, Ernte und Mutagenblüten ein.
- **Keine Geisterquellen:** Ruhende und Redstone-gesperrte Herde werden bei der Ermittlung ausgeschlossen; nicht geladene Quell-Chunks werden nicht geladen.
- **Regressionen getrennt nach Verantwortung:** Die alten Dufttests prüfen nur die gespeicherten Duftabfragen, während die neuen Feldtests tatsächliche Betriebszustände und Überlappung prüfen.

## Aktueller Entwicklungsschritt — 1.72.0

- **Sichere Mutagenstufen:** Kulturmodus hält sichtbare Mutagen-Phänotypen und stufenabhängige Ernteboni aktiv, ohne Gelände auszubreiten, Spieler zu exponieren oder Mutagenblüten auszulösen.
- **Ruhend ist wirklich inaktiv:** Ruhender und Redstone-gesperrter Herd liefern Feldstärke 0, obwohl Herd und persistente Registrierung erhalten bleiben.
- **Gemeinsame Laufzeitabfrage:** Pflanzenvisualisierung, stufenabhängige Ernte und Feldanalyse verwenden dieselbe Prüfung des real platzierten Herdes und seines Betriebsmodus.
- **Chunk-sicher:** Die Feldstärkeabfrage liest nur bereits geladene Quell-Chunks.

## Aktueller Entwicklungsschritt — 1.71.0

- **Drei Betriebsmodi:** Rechtsklick schaltet zwischen Ausbreitung, sicherem Kulturmodus und Ruhend um.
- **Redstone-Sperre:** Strom pausiert unabhängig vom gewählten Modus jede Feldwirkung und bleibt im Weltzustand sichtbar.
- **Sichtbare Zustände:** Die drei Betriebsmodi und der elektrische Sperrzustand verwenden unterschiedliche Pixeltexturen.

## Aktueller Entwicklungsschritt — 1.70.0

- **Redstone-Kontrolle:** Der Mutagenherd lässt sich elektrisch anhalten und wieder starten. Ein pausierter Herd bleibt als solcher platziert und wird nicht als sterilisiert oder gelöscht missverstanden.
- **Saubere Stoppgrenze:** Auch bereits befallener Mutagenboden darf nicht weiterwachsen, solange die zugehörige Quelle Redstone-Strom erhält.
- **Minecraft-lesbarer Zustand:** Aktiv und pausiert besitzen unterschiedliche Blockmodelle/Texturen. Ton, Partikel und nahe Spieler erhalten beim Umschalten Feedback.
- **Kein neuer globaler Tick-Loop:** Die vorhandene begrenzte Quellen-Ticklogik wird weiterverwendet; beim Wiederanschalten wird genau ein neuer Tick geplant.

## Aktueller Entwicklungsschritt — 1.69.0

- **Dämpfer als Gegenangriff:** Ein geladener Resonanzdämpfer, der den Kristallatem abfängt, legt den Kern für 60 Ticks frei. Die Gegenmaßnahme bleibt an den tatsächlichen Verbrauch einer Dämpferladung gebunden.
- **Gemeinsamer Kernöffnungs-Effekt:** Resonanzfokus und Dämpfer nutzen denselben serverseitigen Effekt für Partikel, Klang und Redstone-Relais-Refresh.
- **Live-Redstone-Rückmeldung:** Relais erkennen nach der abgefangenen Atemattacke den freigelegten Kern, sobald der Angriffszustand zurückgesetzt wurde.
- **Keine zusätzlichen Dauerabfragen:** Der bestehende begrenzte Scan und die Ereignisverteilung werden weiterverwendet; es gibt keinen neuen Tick-Loop und keine erzwungenen Chunk-Ladevorgänge.

## Aktueller Entwicklungsschritt — 1.68.0

- **Boss-Reaktionssignal:** Das Containment-Relais erhält Modus 7. Der Comparator zeigt 15 für den aufgeladenen Kristallatem, 10 für andere Boss-Aufladeangriffe, 6 für einen freigelegten Kern und 0 ohne aktive Reaktion.
- **Ereignisgesteuerte Aktualisierung:** Angriffsbeginn/-abschluss, erfolgreiche Fokus-Parade und Ende des Kernfensters aktualisieren die lokalen Relais innerhalb der bestehenden 32-Relais-Grenze.
- **Zuverlässiger Resonanzfokus:** Der Koloss wird innerhalb der bisherigen Reichweite vor normalen Gegnern priorisiert, wenn sein Kristallatem abfangbar ist.
- **Leistungsgrenzen:** Keine dauerhafte Tick-Schleife, begrenzte Entity-Abfrage und keine erzwungenen Chunk-Ladevorgänge.
- **Qualitätssicherung:** Acht Modi mit 128 Blockstates, Ereignis-Refresh, Zielpriorität und DE/EN-Texte werden geprüft.

## Aktueller Entwicklungsschritt — 1.67.0

- **Resonanzfokus als aktive Boss-Abwehr:** Während der Kristallatem-Aufladung kann der Fokus den Koloss aus 5,5 Blöcken Reichweite unterbrechen, wenn noch mindestens acht Wind-up-Ticks verbleiben.
- **Preis und Risiko:** Der Einsatz verbraucht einen Kristallpirscher-Resonanzsplitter und startet die bestehende viersekündige Abklingzeit.
- **Fenster für den Gegenschlag:** Das erfolgreiche Parieren legt den Kern 60 Ticks frei und löst sichtbare Resonanzpartikel und Klangfeedback aus.
- **Alternative Taktik bleibt erhalten:** Ein platzierter, geladener Resonanzdämpfer kann den Atem weiterhin automatisch abfangen.
- **Qualitätssicherung:** Neue Regressionen sichern Serverseitigkeit, Target-Filter, Splitterverbrauch, Kernfenster, Übersetzungen und vollständigen Forge-Build.

## Aktueller Entwicklungsschritt — 1.66.0

- **Boss-Abwehr:** Ein geladener Resonanzdämpfer direkt an der Kristallatem-Bahn fängt den Atem ab und verbraucht genau eine Ladung.
- **Rückmeldung:** Der Dämpfer zeigt den erfolgreichen Eingriff mit Partikeln und Klang; Spieler in der Nähe erhalten eine Meldung. Die Ladung wird als Blockzustand aktualisiert und das nahe Containment-Relaisnetz sofort neu ausgewertet.
- **Sicherheitsfarbe korrigiert:** Relaismodus 6 nutzt die inverse Farbskala für Sicherheit: Rot bei niedriger Reserve, Gelb im Mittelbereich und Grün bei hoher Reserve.
- **Begrenzte Weltabfrage:** Die Atembahn wird mit einem festen kleinen Suchvolumen untersucht. Ungeladene Chunks bleiben unangetastet; es gibt keine permanente Prüfschleife.
- **Regressionen:** Ein neuer Test überprüft Abfangen, Ladungsverbrauch, Relais-Refresh, Chunk-Sicherheit, Übersetzungen und Farblogik.

## Aktueller Entwicklungsschritt — 1.65.0

- **Kristallkoloss – Gegenangriffsfenster:** Nach dem Kristallatem ist der Kern 90 Ticks überladen. Der Boss kündigt das Zeitfenster per Actionbar und End-Rod-Partikeln an; Spieler- und Projektiltreffer verursachen 30 % mehr Schaden.
- **Sichtbare Reaktion:** Brustkern und Rückenstacheln pulsieren während der Überladung deutlich stärker. Das endet automatisch, ohne permanent laufende Zusatzlogik.
- **Containment-Relais – Sicherheitsreserve:** Der siebte Modus liefert einen Comparator-Wert von 0–15. 15 heißt, dass keine Gefahr erkannt wurde; bei aktiver Gefahr verbessern zusätzliche Schutzressourcen den Wert.
- **Sichere Diagnose:** Das Relais bleibt bei begrenztem Umkreis, prüft nur bereits geladene Chunks und erzeugt keine permanente Tick-Abfrage.
- **Tests und Build:** Beide Systeme haben eigene Regressionstests; die bestehende Forge-JAR, der Ressourcencheck und der dedizierte Serverstart bleiben Teil der Pipeline.

## Aktueller Entwicklungsschritt — 1.64.0

- **Kristallkoloss:** Kantige Brauen- und Wangenpanzer verstärken die Kopfsilhouette; eine separate Glow-Textur setzt kontrollierte cyan-violette Risse.
- **Containment-Relais:** Der sechste Modus berechnet eine geschätzte Restgefahr aus Mutagenfeldstärke, Warnsignalen und vorhandenen Schutzressourcen.
- **Redstone-Steuerung:** Die Restgefahr wird als Comparator-Signal ausgegeben, damit Anlagen auf die kombinierte Situation reagieren können.
- **Qualitätssicherung:** Neue Regressionen prüfen die Modellschichten, Textur-UVs, 96 Relaiszustände, Chunk-Sicherheit und den vollständigen Forge-Starttest.


## Aktueller Entwicklungsschritt — 1.63.0

- **Direktes Feldstärke-Signal:** Das Containment-Relais erhält einen fünften Modus, der Mutagenboden und mutagenaktive Pflanzen selbst abtastet und als Comparator-Wert ausgibt.
- **Redstone-Automation:** Nach einem Relais-Scan können Lampen, Türen oder Filtermaschinen auf lokale Feldstärke reagieren, ohne erst einen Kontrollstations-Scan zu benötigen.
- **Sicherheit bleibt erhalten:** Der begrenzte Radius und der Schutz vor Chunk-Loads bleiben erhalten; der Modus fügt keine permanente Abfrageschleife hinzu.
- **Build-QA:** Alle fünf Modi und 80 Blockstate-Kombinationen werden geprüft, bevor die Forge-JAR gebaut wird.


## Aktueller Entwicklungsschritt — 1.62.0

- **Mehr Volumen:** Mehrlagige, kantige Schulter- und Hinterhandplatten verleihen dem Kristallkoloss eine schwerere Rüstungssilhouette.
- **Gezielte Leuchtkanten:** Die neue Full-Bright-Textur zeichnet cyanfarbene Kanten und violette Risse, während der Großteil der Platten dunkel bleibt.
- **Bewegliche Rüstung:** Die Platten reagieren dezent auf die Idle-Animation. Kampfwerte und Beschwörung wurden nicht verändert.
- **Qualitätssicherung:** Der Workflow prüft Modellgeometrie, UV-Farbflächen, Glow-Transparenz und baut die installierbare Forge-JAR.

Der nächste Schritt bleibt die Prüfung eines echten Client-Screenshots gegen das festgelegte Referenzbild; CI-Erfolg allein belegt keine perfekte Bildübereinstimmung.

## Version 1.108.0 — Echte 3D-Zwischenräume und sourcebasierte Silhouettenkontrolle

- Drei getrennte hohe Kristallrücken beim Kristallpirscher statt großer massiver Rückenplatte. Bestehende ModelPart-Animation und kristalline Jagdanatomie bleiben erhalten.
- Koloss mit zwei durchbrochenen Basaltmonolithen und korrekt erhaltener Normal-/Glow-Hierarchie statt vollständig geschlossener Rückentürme.
- Dämmerling mit schlanken, offenen Wurzelhandflächen und intakten, beweglichen Wurzelfingern für Beifraß und Jagd.
- Neues automatisch erzeugtes QA-PNG aus tatsächlichen Java-`addBox`-Koordinaten. **Eine technische Querschnittsansicht, nicht ein Minecraft-Screenshot.**
- 120 GitHub-Actions-Schritte erfolgreich: neue Silhouetten-Regressionen, alter Forge-Quellstand, JAR, dedizierter Server sowie QA-Artefakte. Exakte Bildtreue bedarf noch eines Client-Tests.

## Version 1.107.0 — Gesichts- und Fußsilhouetten des echten Minecraft-Modells

- Kristallkoloss: 1.105-Schädel und 1.106-Augenkorrektur jetzt auch mit angepassten alten opaken Stirn-/Wangenpanzern und deutlich dünneren, selektiv leuchtenden Linien statt massiven Fullbright-Gesichtsplatten.
- Kristallpirscher: zu breite Schienbeinplatten verengt, pro beweglichem Bein zwei geometrisch getrennte Kristall-Fußkrallen ergänzt.
- Dämmerling: überbreite Holzbeine verschlankt, je Fuß zwei eigene Wurzelzehen ergänzt; alle vorherigen Wurzelfasern, Fraß- und Jagdbewegungen bleiben erhalten.
- 118 GitHub-Actions-Schritte erfolgreich: bisherige und neue Modell-/Gameplaytests, Forge 1.20.1, installierbare JAR sowie dedizierter Serverstart. Tatsächlicher Bildvergleich im Minecraft-Client bleibt offen.

## Version 1.106.0 — Konkrete Reparaturen an der visuellen Referenztreue

- Koloss: Ursprüngliche, nach der Kopfverkleinerung außerhalb des Schädels liegende Leuchtaugen und zu breite emissive Brauen im echten Forge-3D-Modell korrigiert.
- Kristallpirscher: Massive Kristallschultern durch jeweils drei getrennte Facettenstücke ersetzt, um die langgliedrige und durchbrochene Silhouette besser lesbar zu machen.
- Dämmerling: Zwei eigene, unterschiedlich lange animierte Wurzelfasern am Körper, mit eigener Bewegung beim Gehen und serverseitig bestätigten Beetfraß.
- 117 grüne GitHub-Actions-Schritte: Modell- und Gameplayregressionen, Forge-1.20.1-Kompilierung, JAR-Prüfung und Dedicated Server. Minecraft-Client-Bildvergleich muss noch erfolgen.

## Version 1.105.0 — Referenzgebundene echte Kreaturensilhouetten

- Kristallkoloss: verkleinerter, gestufter Schädel statt eines übergroßen rechteckigen Kopfes; gesamte bestehende kristalline Vierbeiner-Anatomie und Bossanimationen bleiben verbunden.
- Kristallpirscher: echte schmale Langgliedmaßen und räumlich segmentierter Körper ersetzen generische Zombiegrundwürfel. Kristallfächer, Jagdklauen und Brustresonanz bleiben erhalten.
- Dämmerling: eigenständige schmale Wurzelgrundform und offener Brustkorb statt gefülltem Zombie-Unterkörper, ohne Eingriff in Feldangriff, Leuchtbeeren oder Laternen.
- 116 grüne GitHub-Actions-Schritte: Regressionstests, Forge 1.20.1, JAR und Serverstart. Bildgenaue Minecraft-Client-Sichtabnahme ist noch offen.

## Version 1.104.0 — Verlässliche Feldmessungen und Komposter-Farmwache

- Tragbares Mutagenfeldtagebuch vergleicht fünf bestehende Kennzahlen nur bei exakt übereinstimmender Messabdeckung derselben Station und Dimension. Ändert sich die Abdeckung geladener Chunks oder stammt das Buch aus einem älteren Format, wird eine neue Basis gespeichert.
- Vollständig befüllte Vanilla-Komposter können reife Sporenpflanzen im bestehenden Farmwachenradius vor Dämmerling-Fraß schützen; ohne Verbrauch und ohne weiteren Tick oder Welt-Scan. Kein Schutz gegen Mutagenausbreitung.
- 115 GitHub-Actions-Schritte erfolgreich: alte und neue Regressionen, Forge-1.20.1-Kompilierung, JAR-Verifikation und Dedicated-Server-Start. Minecraft-Client-Test und visuelle Prüfung bleiben offen.

## Version 1.103.0 — Tragbare Feldchronik und bedrohlichere Fraßwarnungen

- Wiederverwendbares Buch und Feder mit NBT-gebundener Feldchronik: fünf Kennzahlen beim Stationsscan speichern und Änderungen später am selben Ort vergleichen. Keine neuen automatischen Weltabfragen, kein Itemverbrauch und keine globalen Heilungsbehauptungen.
- Die bereits vorhandenen zwei Dämmerling-Vorwarnungen beim tatsächlichen Pflanzenfraß erhalten zwei gestaffelte, sichtbare 12-Punkte-Ringe mit unterschiedlichem Radius und Partikelstil.
- Kupfer-, Amethyst-, Redstone-, Mutagen- und Farm-Sicherheit bleibt unverändert; Regressionen plus Forge-/JAR-/Serverprüfung mit 114 erfolgreichen GitHub-Actions-Schritten bestätigt. Client-Sichttest bleibt erforderlich.

## Version 1.102.0 — Mutagen-Quellen finden, echten Horror sehen

- Die bestehende Kontrollstation bietet eine neue Kompassdiagnose für den nächsten wirklich aktiven, ungepausten Mutagen-Ausbreitungsherd: relative X/Y/Z-Lage und ungefähre Entfernung, ohne neue Scan-Schleife, ohne Chunk-Nachladen, ohne Kompassverbrauch.
- Der eigenständige Dämmerling bekommt eine echte, server-synchronisierte Kieferbewegung und bei anhaltendem Pflanzenfraß stärker pulsierende rote Glow-Augen.
- Infektionsfelder bleiben weiterhin ohne Scanner eindeutig sichtbar; alle bisherigen Schutz-, Heilungs-, Farm- und Bossmechaniken bleiben erhalten.
- 113 erfolgreiche GitHub-Actions-Schritte: Modell- und Feldkompass-Regressionen, Forge 1.20.1, installierbare JAR und dedizierter Server. Minecraft-Client-Sichtprüfung steht aus.

## Version 1.101.0 — Lebendiger Feldhorror und scannerfreie Modusanzeigen

- Neues serverseitig synchronisiertes Dämmerling-Fraßsignal: animierte gekrümmte Beethaltung und abwechselnde Wurzelkrallen nur bei einem tatsächlichen, ungestoppten Feldangriff.
- Drei unterschiedliche kreisförmige Partikeleffekte beim manuellen Umschalten des Infektionsherds: große Bedrohung, grüne sichere Kultivierung oder kleine ruhende Signatur.
- Unverändert: KI- und Crop-Schutzregeln, Laternen- und Beerenabwehr, Redstone, Bosskämpfe, Infektionsheilung und Spielerwerte. Keine zusätzlichen Dauer-Ticker oder Scanner.
- 112 GitHub-Actions-Schritte erfolgreich: Regression, Forge 1.20.1, Mod-JAR, Dedicated Server. Minecraft-Client-Sichttest bleibt noch nötig.

## Version 1.100.0 — Dämmerling wird eine eigenständige Kreatur

- Neuer echter animierter Forge-Körper statt des generischen Minecraft-Zombiemodells, einschließlich asymmetrischer Wurzelhorn-Anatomie, Finger, Bauchpanzerung, original 128×128-Textur und selektiv leuchtenden Augen.
- Neuer alternativer Leuchtbeeren-Köder schützt bei einer tatsächlichen langsamen Pflanzenattacke kurzzeitig reife Feldfrüchte. Seelenlaterne bleibt bevorzugte Schutzmaßnahme und exklusiv für Nachtwache-Fortschritt.
- Keine neuen Welt- oder KI-Ticker, keine neue Scannerpflicht, kein Verbrauch der Verteidigungsitems und keine Änderung an Mutagenheilung, Bosskampf oder Farmwirtschaft.
- 111 GitHub-Actions-Schritte erfolgreich – Forge 1.20.1, Modell- und Gameplayregressionen, JAR-Paketprüfung sowie Dedicated Server. Minecraft-Client-Sichttest für die endgültige Optik bleibt erforderlich.

## Version 1.99.0 — Sichtbarer Kristallverschleiß

- Vier animierte Koloss-Schulter-/Hüftpanzer öffnen sich abhängig von seinen bestehenden Lebenspunkten. Darunter kommen schmale, passend mitbewegte und selektiv leuchtende Kristalladern zum Vorschein.
- Verletzte Kristallpirscher bekommen einen sichtbar unruhigeren Gang, leichtes Zittern der Kopfkristalle und verstärkte Brustkern-Pulsation, ohne Gameplay-Änderungen.
- Keine fremden Modell-/Texturdaten übernommen, keine Änderungen an Schadenswerten, Hitboxen, Maschinen, Infektion, Heilung oder Drops.
- 110 GitHub-Actions-Schritte erfolgreich: neue Regressionen, Forge-Build, JAR-Prüfung, dedizierter Server. In-Game-Optik weiterhin gesondert zu bestätigen.

## Version 1.98.0 — Koloss-Leuchtlayer ausgerichtet und Kristallblende freigelegt

- Fix des historischen 13-Modellpixel-Höhenversatzes zwischen Haut- und Leuchtmodell.
- Bereits vorhandene vierteilige Blende vor den herausragenden Brustkristall verlegt; geglättete, phasenabhängige Öffnungsanimation.
- Vier neue ringförmig angeordnete Basaltfassungen mit schmalen selektiv leuchtenden Kristalleinlagen, alle als echte Forge-ModelParts.
- Zusätzliche strukturelle Regression und Forge-/JAR-/Server-Prüfungen. Kein neuer Boss-Schaden, keine Änderungen am Mutagen-Endgame. Manuelle visuelle Client-Abnahme noch offen.

## Version 1.97.0 — Koloss-Kristallblende und lebendige Brustkerne

- Vier neue, separat bewegliche 3D-Kristallblenden vor dem Koloss-Brustkern, mit deckungsgleichen Haut-/Emissivknochen und bewegungsabhängiger Öffnung bei den drei bestehenden Bossangriffszuständen.
- Zwei einzeln animierte Brustkristallsplitter beim Kristallpirscher, die mit dem bisherigen pulsierenden Thoraxorgan zusammenarbeiten.
- Existierende UV-Flächen werden wiederverwendet statt weitläufig überschrieben; keine Textur- oder 3D-Daten aus fremden Referenzmods kopiert.
- Keine Änderungen an Kampfwerten, Mutagenfeldern, KI oder Endgame-Heilung. Eigene Regressionen sowie Forge-/JAR-/Server-Prüfung sind im Workflow; der tatsächliche Minecraft-Client-Sichttest muss folgen.

## Version 1.96.0 — Kristallresonanz als sichtbare Anatomie

- Kristallkoloss: sechs original modellierte, gestaffelte seitliche Kristallrippen aus Basalt und violett-cyanfarbenen Lichtkernen, für alle drei bestehenden Angriffsphasen animiert und in beiden Modellschichten korrekt gebunden.
- Kristallpirscher: neues eigenständiges Thoraxorgan mit zwei angehefteten Kristallen und aggressionsabhängigem Pulsieren.
- Originale Minecraft-Pixeltexturen, kein Kopieren fremder JAR-Modelle und keine Änderungen an der Infektion oder dem Bosskampf.
- Automatische Regression, Forge-Build, JAR-Validierung und dedizierter Server erfolgreich (107 Prüfschritte); visueller Minecraft-Client-Test steht noch aus.

## Version 1.95.0 — Kristalljagd und pulsierender Koloss

- Der Kristallpirscher bekommt eine neue Verfolgungshaltung, vier unabhängige Klauenbewegungen und eine dezente Aggressionspulsation der selektiven Glow-Schicht.
- Der Kristallkoloss animiert beide Rückenmonolithen, alle zwölf facettierten Klauenspitzen und drei Schwanz-Kristallblätter synchron mit seinen bestehenden Atem-, Stampf- und Erwachensphasen.
- Vorhandene Spielmechaniken, Boss-Belohnungen, Farm-Horror, Mutagen-Steuerung und sichere Heilpfade bleiben unangetastet.
- Separater Regressionstest, Forge-1.20.1-Build, installierbare JAR und dedizierter Server-Smoke-Test gehören zur Build-Pipeline; In-Game-Optik bleibt gesondert abzunehmen.

## Version 1.94.0 — Zwei Kreaturen, mehr echte 3D-Kristalldetails

- Kristallpirscher: zwei gestufte, unterschiedlich lange Rückenflossen mit eigener Animation, beweglicher Kieferkristall, neue original bemalte Pixeltextur für die selektive cyan-violette Leuchtschicht.
- Kristallkoloss: zwölf zusätzliche facettierte Kristallklauen an vier bereits animierten Pfoten, mit passender Haut- und Glow-Geometrie.
- Unverändert: Forschungsfortschritte, Mutagen-Heilung, Gegner-KI, Spawn-Bedingungen, Verarbeitungs- und Schutzmaschinen sowie Bossangriffe.
- Prüfung: 105 erfolgreiche GitHub-Actions-Schritte, Forge-Kompilierung, JAR-Verifikation und Dedicated-Server-Smoke-Test. Sicht- und Bewegungsprüfung im laufenden Minecraft-Client bleibt offen.

## Version 1.93.0 — Kristallpirscher: eigenständige Minecraft-Anatomie

- Eigener 128×128-Modelllayer und Forge-Renderer mit schweren ungleichen Rückenkristallen, scharfkantigem Kopfschmuck, Schulter- und Beinkristallen, verlängerten Klauen und kampfabhängiger Eigenanimation.
- Neue transparente Glow-PNG für Cyan-Risse, Augen und violette Kristalle. Altes UV-Grundlayout im vergrößerten Atlas erhalten; keine Ressourcen aus fremden Referenzmods kopiert.
- Bestehende Spawnregeln, Kampf, Filtermasken-Gegenwehr und Gegenstandsbelohnungen bleiben unverändert. Eigenständige Regressionen, Forge-Build, Ressourcen-Paketprüfung und Dedicated-Server-Smoke-Test sind grün.
- Vollständige Sichtprüfung und weitere Annäherung an die Originalvorlagen im Minecraft-Client bleiben erforderlich.

## Version 1.92.0 — 3D-Schwanzstachel, Rückenmonolithen und Originaltexturen

- Neues echtes Modellmaterial: viergliedriger, hochgebogener Skorpionschwanz mit dreizackigem Kristallende, zwei gepanzerte Rückenmonolithen und überarbeitete violett/bernsteinfarbene Pixeloberflächen.
- Haut und Leucht-Layer mit identischen Gelenken, Boss-Animationen weiterverwendet, keine zusätzlichen Chunk-Ladungen oder Server-Ticker.
- Forge-Build, JAR-Verifikation, 103 automatisierte Schritte und Dedicated-Server-Smoke-Test erfolgreich; manuelle Client-Optik noch offen.

## Version 1.91.0 — Kristallkoloss-Auftritt und echte Nachtwache

- Drei sichtbare und hörbare Kristallring-Wellen für die Ankunft des Bosses, ohne zusätzlichen Schaden, Chunk-Loading oder Kamerazwang.
- Persistenter NBT-Auftrittsfortschritt und eine einmalige lokale Warnmeldung.
- Lokale Vorwarnung bei echten Dämmerling-Fraßversuchen; die Feldstation unterscheidet nun anwesende Kreaturen von aktiven Überfällen.
- Eigenständige Regressionen, Forge-Build und Dedicated-Server-Smoke-Test erfolgreich. Sichttest im Minecraft-Client weiterhin offen.

## Version 1.90.0 — Dämmerling-Nachtwache und bewachte Felder

- **Warnung:** Zweistufige audiovisuelle Fraßvorwarnung, echte Prüfung der Pflanze vor der Zerstörung und Schutz vor Chunk-Entladung.
- **Gegenwehr:** Eine tragbare Seelenlaterne verhindert unmittelbar bevorstehenden Schaden an reifen Beeten und löst 120 Ticks Abklingzeit der Futtersuche aus, ohne Gegenstandskosten.
- **Fortschritt:** Der einmalige Forschungsfortschritt „Licht gegen den Wildwuchs“ belohnt erfolgreiche Rettung; der Stationsbericht kann nahe Dämmerlinge anzeigen.
- **Qualität:** Quellenpatch und Regressionen, Minecraft-Farbtexturen und bestehende Filtermoos-/Ward-Mechaniken im Code erhalten. Automatischer Forge-Build und dedizierter Server erfolgreich; vollständige Client-Optik noch nicht manuell abgenommen.

## Version 1.89.0 — Kupfererdung und Mutagen-Knotenrettung

- Kupferbarren + geduckter Rechtsklick wandelt nur tatsächlich aktive, unpausierte Ausbreitungsquellen auf ANBAU um.
- Vorhandene Forschung, Kulturen, Redstone-Pausen, Welt-Heilung und manuelle Nothalt-/Neustartwege bleiben intakt. Es gibt keine Itemkosten oder Charakter-Nachteile.
- Erfolgsgebundener Advancement-Fortschritt „Aus Gefahr wird Wachstum“ sowie sichtbares und akustisches Feedback.
- Eigene Regression für die Quellregistrierung, geladenen Chunks, Forschungsbelohnung, Sprachtexte, Tick-Sicherheit und alte Stationsfunktionen; vollständiger Forge-Build, JAR und Serverstart erfolgreich.

## Version 1.88.0 — Live-Knotenprotokoll der Mutagen-Kontrollstation

- **Fünf Betriebszustände:** Die Kontrollstation unterscheidet beim normalen Scan AUSBREITUNG, ANBAU, RUHE, Redstone-Pause und endgültig inaktive Quellen. Die Ergebnisse stammen aus echten Blockzuständen und gespeicherter Quellregistrierung.
- **Verständlicher Alarm:** Nur tatsächlich aktive, nicht pausierte Ausbreitungsquellen lösen die rote Warnung aus. Anlagen mit ausschließlich sicheren Kulturen bekommen eine grüne Betriebsrückmeldung, stillgelegte Anlagen eine ruhige Diagnose.
- **Endspiel bleibt geschützt:** Sterilisierte Quellen erscheinen als inaktiv. Diagnose und Anzeige ändern weder gespeicherte Registrierung noch Blockzustände, Stabilisatoren, Ernte oder Sicherheitsmechaniken.
- **Bereits vorhandener Scan:** Die Auswertung nutzt exakt denselben geladenen 16-Blöcke-Radius/±8-Höhen-Bereich wie Forschung, Biodiversität und Notabschaltung. Ein Comparator löst weiterhin keinen zusätzlichen Scan aus.
- **Nachvollziehbar auf DE/EN:** Übersetzte Quellenzählung und konkrete Handlungsanweisungen. Notabschaltung (Schleichen) und sicherer Wiederanlauf (Schleichen plus Amethyst) bleiben erhalten.
- **Regression und Build:** Tests für Kategorisierung, Aktivitätsprüfung, Loaded-Chunk-Guards, Quellenzählung, Warnung, alte Steuermodi und Textressourcen; vollständige Forge-Kompilierung, JAR- und Dedicated-Server-Prüfung.

## Version 1.87.0 — Wiederanlauf sicherer Mutagenfarmen

- **Drei Betriebswege an derselben Station:** Normaler Rechtsklick untersucht die Anlage, geduckter Rechtsklick stellt sie still, geduckter Rechtsklick mit Amethystscherbe aktiviert ausschließlich sichere Kultivierung.
- **Kein unkontrolliertes Wiederausbrechen:** Aktive, registrierte und bereits ruhende Knoten können wieder in den Anbaumodus wechseln; niemals in den Ausbreitungsmodus. Knoten aus geheilten Welten bleiben inaktiv.
- **Technisch schonend:** Unveränderte Redstone-Pausen, keine Itemkosten, nur geladene Chunks, begrenzte Rückmeldungen und kein zusätzliches Hintergrundsystem.
- **Prüfung:** Neue Regression für Interaktion, Schutzschranken, sichere Feldmodi, Übersetzungen und bestehenden Not-Aus-Pfad, kompletter Forge-Build und dedizierter Serverstart.

## Version 1.86.0 — Dämmerling: Starr vor Angst oder auf der Lauer?

- **Eigenständiges Monsterverhalten:** Der Dämmerling bricht seine Jagd kurz ab, wenn sein aktuelles Ziel ihn im Dunkeln direkt anschaut. Sobald der Spieler den Blick abwendet, setzt die Verfolgung wieder ein.
- **Begrenzte Ausweichmechanik:** Maximal 30 Ticks Starre, dann 100 Ticks Immunität gegen den Effekt. Keine ständige Unterbrechung durch Spieler, die die Kreatur ununterbrochen fixieren.
- **Faire Sichtprüfung:** Zwölf Blöcke Reichweite, echte Sichtlinie, normiertes Blickrichtungs-Skalarprodukt größer als 0,93, lebende Survival-Spieler und niedrige Umgebungshelligkeit.
- **Unheimliches Feedback:** Ein Partikelimpuls, gedämpftes Amethystgeräusch und selten eingeblendeter Aktionstext vermitteln, dass die Kreatur den Blick wahrnimmt.
- **Bestehende Systeme intakt:** Das vorherige CropThreatGoal bleibt auf Priorität 5, Zombie-Angriff und vorhandene Ernte-/Schutzlogik bleiben im Code. Keine neuen Spawnregeln, Chunk-Forceloads oder dauerhaft laufenden Umweltabfragen.
- **Qualitätsnachweis:** Eigenständige Regression zu Blickkontakt, Cooldown, KI-Interaktion, vorhandenen Pflanzenregeln und Übersetzungen sowie Forge-Kompilierung und dedizierter Serverstart. Eine visuelle Client-Kontrolle steht weiterhin aus.

## Version 1.85.0 — Lebendige Mutagenfelder bei Nacht

- **Atmosphärische Mutagenquelle:** SPREAD-Knoten können nachts ein kurzes, hörbares und sichtbares Horror-Ereignis auslösen: wirbelnde Sporen, Seelenflammen-Tendrils, Portal-Partikel und ein tiefes Summen.
- **Sanfter Kulturmodus:** CULTIVATION verwendet stattdessen freundliche Wachstums-Partikel und ein gedämpftes Amethystklingen. Die funktionale Abgrenzung von kontrollierter Farm und gefährlichem Wildfeld ist weiter auch ohne Scanner sichtbar.
- **Redstone- und Notabschaltung respektiert:** Der vorhandene aktive Knoten-Tick entscheidet über die Effekte. DORMANT-, Redstone- und inaktive Knoten lösen keine Atmosphäre aus.
- **Vorsichtige Begrenzung:** Seltene serverseitige Trigger, nur bei Spielern in unmittelbarer Nähe, pro Spieler bis zu 22/35 Sekunden Abstand und ein einziger ausgelöster Impuls pro Knotentick. Keine Spawns, Exposition, Terrainveränderung, Scannerpflicht oder zusätzlichen Chunkzugriffe.
- **Qualitätssicherung:** Neue Regression für Modusverhalten, Nachtfilter, Cooldown, Partikel und Sound, unveränderte Ausbreitung/Kultivierung und Versionsstand sowie vollständiger Forge-Build und dedizierter Serverstart. Die optische Wirkung benötigt zusätzlich einen Minecraft-Client-Sichttest.

## Version 1.84.0 — Mutagen-Notabschaltung der Feldkontrollstation

- **Neue Anlagenfunktion:** Geduckter Rechtsklick auf eine Feldkontrollstation stellt alle geladenen Mutagenknoten im Radius 16 / Höhe ±8 von SPREAD bzw. CULTIVATION auf DORMANT. Die normale Diagnose bleibt verfügbar.
- **Unveränderter Schutzpfad:** Mutagenknoten behalten ihre Registrierung und ihren Redstone-Zustand. Der bestehende Mode-2-Zweig verhindert sowohl Ausbreitung als auch Kultivierung, bis ein einzelner Knoten gezielt umgestellt wird.
- **Sicherheit beim Eingriff:** Bereits ruhende Knoten werden nicht verändert. Der Scan überspringt ungeladene Chunks, verwendet nur bestehende Blockzustände und führt keinen dauerhaften Hintergrundticker ein.
- **Messbare Rückmeldung:** Spieler erhalten eine serverseitige Knotenzahl und einen Hinweis auf die Scanbegrenzung. Maximal 24 betroffene Knoten erzeugen Rauchpartikel; eine stationäre Klangrückmeldung bestätigt die Betätigung.
- **Kontrollierte Experimente bleiben möglich:** So lassen sich aktivierte Mutagenanlagen gezielt stilllegen, ohne eine Weltheilung auszulösen oder die spätere Wiedernutzung von Infektionsfeldern zu verhindern.
- **Qualitätskontrolle:** Regressionen für Eingabe, Radius, Loaded-Chunk-Guard, Spielerhinweise, Zustandserhalt, ursprüngliche Knotenticks, Metadaten und Übersetzungen sowie Forge-Kompilierung und dedizierter Serverstart.

## Version 1.83.0 — Kristallkoloss: seismischer Warnring und Sprung-Kontermöglichkeit

- **Telegraphierter Stampfangriff:** Drei Bodenkreise während der 42-Tick-Stampf- oder 36-Tick-Erwachensvorbereitung zeigen die gefährdete Zone. Ein zusätzlicher Klang warnt kurz vor dem Aufprall.
- **Klarer Trefferkreis:** Die vorhandene AABB dient nur als grobe Vorauswahl; eine genaue horizontale Kreisprüfung sichert den Radius von 5,8 bzw. 7,2 Blöcken.
- **Faire Kontermöglichkeit:** Hochspringen kann den Bodenschock abwehren, wenn das Ziel beim Impact nicht auf dem Boden steht. Die Angriffsstärke, Rückstoß- und Verlangsamungswerte bleiben erhalten.
- **Doppelter Aufprallring:** Zeitgleiche innere und äußere Kristallpartikel erzeugen einen gut sichtbaren Einschlag, ohne Blöcke abzubauen, zu ersetzen oder Chunks zu laden.
- **Performance:** Warnpulse nur dreimal pro Attacke, begrenzte Partikelanzahl pro Ring und keine dauerhaften Zusatzprüfungen.
- **Qualitätssicherung:** Neue Regression für Countdown, Partikel, realen Hit-Radius, Sprung-Ausweichen, unveränderte Angriffe, vorhandene Texturen und Version; Forge-Build und dedizierter Serverstart. Auf unebenem Gelände ist ein Minecraft-Client-Sichttest weiter nötig.

## Version 1.82.0 — Kristallkoloss: Gewicht in jedem Schritt

- **Neue Laufkinematik:** Vier individuelle Beinpfade mit gegenläufigen Diagonalphasen und differenziertem Schwung für Vorder- und Hinterbeine.
- **Bewegliche Tatzen:** Knie und Fußwinkel reagieren auf die Schrittphase; eine begrenzte vertikale und horizontale Tatzenkorrektur erzeugt erkennbare Stand-/Schwungphasen.
- **Verzögerte Masse:** Körperrollbewegung, korrigierende Kopfneigung und dreifach verzögerte Schwanzbewegung geben dem Kristallkoloss mehr körperliche Trägheit.
- **Saubere Boss-Posen:** Während des gehaltenen Stampfangriffs behalten die Vorderpfoten ihre aufgesetzte Position, statt ungewollt weiterzulaufen. Bestehende Angriffs- und Emissiv-Logik bleibt erhalten.
- **Prüfung:** Gesonderte Regression für Phasen, bewegte Tatzen, Schwanz, Stampfangriff, ModelPart-Hierarchie und Version; Forge-JAR und dedizierter Serverstart. Die tatsächliche visuelle Qualität erfordert weiterhin Client-Screenshots.

## Version 1.81.0 — Beweglicher Kristallkiefer und gerichtete Atemladung

- **Neues Gelenk:** Die untere Schnauzengeometrie des Kristallkolosses ist nicht länger fest in den Schädel eingebaut. Bestehender Kieferpanzer und neue Kristallzähne bewegen sich gemeinsam.
- **Synchronisierte Leuchtgeometrie:** Maulleuchten und Zähne folgen dem Kiefer auf dem Full-Bright-Layer, während Wangenpanzer und die Kristallkrone an ihren alten Positionen erhalten bleiben.
- **Angriffe mit Vorwarnung:** Während der bestehenden 48 Ticks Kristallatem wächst der Maulwinkel von leichter Spannung zur breiten Öffnung. Die Warnpartikel laden sichtbar an der Schnauze auf, bevor der unveränderte Strahl ausgelöst wird.
- **Weitere Ausdrucksformen:** Ruhige Atembewegung, verstärktes Aufreißen beim Erwachen, angespanntes Maul beim Stampfen.
- **Technische Prüfung:** Eigene neue Regression für Geometrie, Phasenanimation, Ladungsformel, getrennte Modell-Layer, Assets und Metadaten plus Forge-JAR und dedizierter Serverstart. Eine tatsächliche Client-Bildkontrolle ist weiterhin erforderlich.

## Version 1.80.0 — Kristallkoloss: lebendige Kristallkrone

- **Neue Silhouette:** Spiegelbildliche, jeweils dreistufige Kristallklingen ragen aus der Kopfpartie und werden durch dunkle Wangenpanzer verankert.
- **Echte Gelenke:** Beide Kristallkronen besitzen eigene ModelParts und bewegen sich unabhängig vom Kopf. Der bestehende Leucht-Layer ist geometrisch ausgerichtet und beleuchtet nur die inneren Kristallflächen.
- **Kampfbezogene Animation:** Eine sanfte Idle-Atmung geht bei Kristallatem in ein sichtbares Auffächern und beim Erwachen in eine deutlich größere Kristallresonanz über.
- **Leistungsbewusst:** Die Animation basiert auf der vorhandenen synchronisierten Boss-Zustandsvariable; es gibt keinen neuen Tick-Loop, kein Shader-Framework und keine zusätzlich erzwungenen Chunks.
- **Visuelle Referenz:** Belowland und The Wonderland dienten ausschließlich als Analysemaßstab für hochwertige Modelldichte und Animationsstruktur. Keine fremden Modelle, Texturen oder Animationen sind im Mod enthalten.
- **Prüfung:** Regressionen, Forge-JAR, unabhängige Emissiv-Layer und dedizierter Serverstart; manuelle Sicht- und Kampfprüfung im Client weiterhin erforderlich.

## Version 1.79.0 — Automatischer Pflanzenreste-Kreislauf

- **Neue Bioreaktor-Stufe:** Vier Pflanzenreste werden mit 60 FE zu einer Biomasse veredelt.
- **Weiter zur Düngung:** Die bestehende Biomasse-Verarbeitung erzeugt zwei Myzelkompost für 80 FE. Beide Schritte lassen sich mit dem Feldsammler zu einer automatisierten Rückführung verbinden.
- **Keine Teilverluste:** Zu kleine Stapel, fehlender Ausgabepuffer oder unzureichende Energie verbrauchen keinen Eingabestapel. Das Ergebnis wird erst eingefügt, bevor vier Reste entfernt werden.
- **Entdeckbarkeit:** Der Pflanzenreste-Tooltip erklärt den neuen Verarbeitungspfad auf Deutsch und Englisch.
- **Qualitätssicherung:** Neue Regression prüft das Eingabebündel, Energie, Ausgabereihenfolge, die bestehende Kompoststufe, beide Übersetzungen sowie den vollständigen Forge-Build und Serverstart.

## Version 1.78.0 — Forschungszweig für abgefangene Mutagenblüten

- **Neue Feldforschungs-Advancement „Leise Wurzeln“:** Eine aktive Sporenabwehr meldet den Spielerfortschritt erst, wenn sie einen realen Mutagenblüten-Expositionsimpuls abfängt.
- **Einmalige Belohnung:** Zwei Feldwissen und ein Myzelkompost verbinden die sichere Verteidigungsstrategie mit weiterer Forschung und der ökologischen Produktionskette.
- **Getrennter Schutzpfad:** Die bisherige Dämpfer-Advancement „Stiller Ausbruch“ bleibt an den tatsächlichen Verbrauch einer endlichen Resonanzdämpfer-Ladung gekoppelt.
- **Keine Gratisbelohnung beim Aufstellen:** Der Trigger sitzt im serverseitigen Schutz-Zweig der echten Blüten-Expositionsroutine; Einschalten, Platzieren oder bloßes Beobachten reicht nicht.
- **Qualitätssicherung:** Tests verifizieren Advancement-Kriterium, Loot-Inhalte, Sprachdateien, Dämpfer-Gegenpfad und vollständigen Forge-Serverstart.

## Version 1.77.0 — Symbiose-Ernte als Redstone-Signal

- **Neuer Containment-Relais-Modus 8:** Das Relais zählt bis zu 15 reife Sporenwerk-Erntezentren, die lokal mindestens drei verschiedene Kulturen und eine echte Feldstärke II/III besitzen.
- **Farmen lassen sich steuern:** Der Comparator-Wert kann als Erntereife-Signal für Sortierung, Lagerung, Beleuchtung, Farmstopp oder weitere Redstone-Schaltungen genutzt werden.
- **Aktualisierung bei relevanten Ereignissen:** Eine platzierte dritte Kulturart, der Reifeschritt einer passenden Pflanze und das Entfernen von Kulturen stoßen eine begrenzte Relais-Aktualisierung an. Es kommt kein globaler oder per-Block-Ticker hinzu.
- **Sicherheit und Lesbarkeit:** Der bestehende Relay-Scan bleibt geladen-chunk-basiert, das Blockmodell bleibt Minecraft-Pixelart, alle 9×16 Zustandskombinationen besitzen Modellzuordnungen und die neue Betriebsart ist auf Deutsch/Englisch beschriftet.

## Version 1.76.0 — Biodiversitätsdiagnose der Mutagen-Kontrollstation

- **Artenzahl statt bloßer Pflanzenmenge:** Die manuelle Stationserhebung zählt die vier Sporenwerk-Kulturarten sowie reife Pflanzen innerhalb des bestehenden Scanbereichs.
- **Tatsächliche Symbiose-Gelegenheit:** Der Bericht prüft das bekannte 7×3×7-Nachbarschaftsmuster, mindestens drei verschiedene Arten, eine reife Erntepflanze und ein aktuell wirksames Mutagenfeld der Stärke II/III. Er schätzt nicht anhand bloßer Bodenzahlen.
- **Konkrete Handlungsempfehlung:** Bei geeigneten Erntezentren erklärt die Station, wie durch Ernte Symbiosemyzel für Resonanzsporen-Kapseln gewonnen werden kann. Andernfalls nennt sie die fehlenden Voraussetzungen.
- **Einmaliger, sicherer Scan:** Biodiversitätsnachbarschaften werden aus dem bereits erfassten Speicherbild gezählt; nur passende reife Kandidaten erhalten eine aktuelle Feldstärkeabfrage. Nicht geladene Chunks werden übersprungen und kein Ticker wird ergänzt.
- **Qualitätssicherung:** Tests decken Arten-Bitmaske, lokale Nachbarschaft, Reifegrad, live Feldstärke, DE/EN-Empfehlungen, Versionsmetadaten und die unveränderte Containment-Erhebung ab.

## Version 1.75.0 — Resonanzsporen-Kapsel für Kultur und Containment

- **Ökologie wird zur Wartungsressource:** Symbiosemyzel und mutagene Sporen lassen sich mit Knochenmehl und Redstone zu zwei Resonanzsporen-Kapseln verarbeiten.
- **Gezielte Pflanzenpflege:** Rechtsklick auf eine unreife Sporenwerk-Pflanze erhöht ihr Wachstum um bis zu zwei Stufen. Die operative Mutagenfeldstärke wird bei Bedarf sofort im sichtbaren Phänotyp berücksichtigt; Terrain-Ausbreitung wird nicht ausgelöst.
- **Reparatur statt Einweg-Sonderfall:** Rechtsklick auf einen Resonanzdämpfer stellt genau eine Ladung wieder her und aktualisiert gekoppelte Containment-Relais. Bei voller Ladung wird keine Kapsel verbraucht.
- **Spielklare Darstellung:** Eigenes 16×16-Item-Artwork, Modell, Tooltip, DE/EN-Meldungen und Rezept-Advancement sind enthalten und werden im visuellen QA-Bogen geprüft.
- **Regressionen:** Tests sichern Eingabekosten, Wachstumskappung, Mutagen-Phänotyp, Dämpfer-Ladung, Comparator-/Relay-Aktualisierung, volle Zustände, Rezept und Versionsmetadaten.

## Version 1.74.0 — Leuchtender Kristallkern als Bossreliquie

- **Das Konzept wird zum echten Item:** Der Leuchtende Kristallkern erhält eine eigene transparente 16×16-Pixeltextur, Itemmodell, Kreativkatalog-Eintrag und deutsche/englische Lokalisierung.
- **Funktion statt reiner Dekoration:** Rechtsklick entfesselt serverseitig einen Resonanzimpuls, der bis zu vier Mutagengegner in Sichtweite innerhalb von acht Blöcken trifft. Das Artefakt ist wiederverwendbar und hat eine feste Abklingzeit von zehn Sekunden.
- **Aktive Boss-Gegenwehr:** Trifft der Impuls den Kristallkoloss während seiner angekündigten Stampf- oder Atemaufladung, unterbricht er diesen Angriff, setzt den Windup sichtbar zurück und verursacht zusätzlichen Schaden. Aufwachen und normale Phasen werden nicht abgebrochen.
- **Verdienter Endgame-Fund:** Der Kristallkoloss lässt einen Kern garantiert fallen. Ein eigenes Advancement zeichnet den Fund auf; das Bild ist außerdem in der Visual-QA-Vorschau enthalten.
- **Sicherheits- und Regressionstests:** Zielauswahl und Schaden laufen serverseitig; Reichweite, Sichtlinie, Zielobergrenze, Windup-Interruption, Loot-Tabelle, Modell, Textur, DE/EN-Texte und Versionsmetadaten werden geprüft.

## Version 1.73.0 — Resonanzverdichtung überlappender Mutagenfelder

- **Feldüberlappung hat einen Gameplay-Effekt:** Wenn mindestens zwei aktive Quellen denselben Ort innerhalb ihrer Reichweite erreichen, steigt dessen effektive Mutagenstärke um eine Stufe, höchstens bis Stufe III.
- **Mehr als ein visueller Trick:** Pflanzenphänotypen, Ernteboni, Feldscanner und Mutagenblüten lesen weiterhin dieselbe operative Stärke. In Überschneidungszonen können deshalb sichtbare Hochstufen und seltene Blüten entstehen, ohne dass ein zusätzlicher Block-Ticker nötig ist.
- **Die Betriebsmodi bleiben maßgeblich:** Ruhende, entfernte, nicht registrierte oder per Redstone gesperrte Quellen tragen nichts zur Feldverdichtung bei. Kulturquellen zählen dagegen weiter als sichere Pflanzungsfelder, nicht als Terrain-Ausbreitung.
- **Chunk-sicher:** Quellen werden nur dann abgefragt, wenn ihr Chunk bereits geladen ist; die vorhandene Feldreichweite und vertikale Grenze bleiben unverändert.
- **Qualitätssicherung:** Tests sichern Quellenüberlappung, Stärke-Obergrenze, Modus-/Redstone-Gates, Chunk-Grenze, historische Duft-Abfragen und die aktiven Versionsmetadaten.

## Version 1.72.0 — Mutagenstärke folgt dem Betriebsmodus

- **Kulturmodus mit Phänotypen:** Sporenwerk-Pflanzen können Mutagenstufen und vorhandene stufenabhängige Ernteboni erhalten, ohne dass der Herd Terraininfektion, Exposition oder Mutagenblüten auslöst.
- **Keine Geisterfelder:** Ruhend und Redstone-gesperrt liefern Feldstärke 0, auch wenn die Quelle für einen späteren Neustart registriert bleibt.
- **Einheitliche Intensität:** Pflanzenvisualisierung, Ernte und Feldanalyse verwenden dieselbe serverseitige, quellspezifische Stärkenabfrage.
- **Chunk-Grenzen:** Die neue Abfrage überspringt ungeladene Quellen-Chunks und erzwingt keine Ladevorgänge.

## Version 1.71.0 — Drei Betriebsmodi für den Mutagenherd

- Rechtsklick schaltet Ausbreitung, Kulturmodus und Ruhend um; der Modus wird im Blockzustand gespeichert.
- Kulturmodus beschleunigt nur geeignete Sporenwerk-Pflanzen, erzeugt aber keine neuen befallenen Bodenblöcke und keine Spielerexposition.
- Der Redstone-Sperrzustand hat Vorrang und verwendet weiterhin die auffällige rote Pixeltextur.
- Alle sechs Blockstate-Kombinationen, Bloom-Integration, Übersetzungen und Texturkontrast werden geprüft.

## Version 1.70.0 — Redstone-Sperre für kontrollierte Mutagenherde

- **Feld auf Knopfdruck anhalten:** Ein Redstone-Signal pausiert den Mutagenherd, ohne ihn zu zerstören oder seinen persistenten Aktivierungsstatus zu verlieren. Wird das Signal entfernt, wird die Ausbreitung automatisch fortgesetzt.
- **Bereits befallener Boden stoppt mit:** Mutagenboden prüft weiterhin seine ursprüngliche Quelle. Solange diese Quelle mit Redstone gesperrt ist, entstehen keine neuen befallenen Nachbarblöcke.
- **Im Spiel deutlich sichtbar:** Der gesperrte Herd erhält ein eigenes dunkelmetallisches Pixelmuster mit rotem Sperrbalken, statt dass man einen Scanner zum Erkennen benötigt.
- **Rückmeldung und Grenzen:** Signalwechsel erzeugen Ton, Partikel und eine lokale Nachricht. Die 8-Block-Horizontalreichweite, die vertikale Begrenzung, Heilanker, immune Baublöcke und die Endgame-Sterilisierung bleiben erhalten.
- **Qualitätssicherung:** Regressionen prüfen beide Spread-Pfade, gespeicherten Herdstatus, Blockstate-Modellzuordnung, 16×16-Texturkontrast und deutsche/englische Meldungen.

## Version 1.69.0 — Dämpfer-Parade öffnet den Kristallkern

- **Mehr als Schadensvermeidung:** Fängt ein geladener Resonanzdämpfer den Kristallatem ab, wird der Kristallkern 60 Ticks lang verwundbar. Schutzanlagen erzeugen so ein Gegenangriffsfenster, statt nur Schaden zu verhindern.
- **Gemeinsame Gegenmaßnahme:** Resonanzfokus und platzierter Dämpfer verwenden denselben serverseitigen Effekt für Kernöffnung, Kristallpartikel, Klang und Relais-Aktualisierung.
- **Redstone reagiert sofort:** Der Boss-Reaktionsmodus wird nach dem Abfangen erneut ausgewertet und wechselt von der Atemwarnung zur Kernöffnung.
- **Spielerfeedback:** Nahe Spieler erhalten die Bestätigung, dass der Atem abgefangen und der Kern freigelegt wurde.
- **Qualitätssicherung:** Tests prüfen Dämpferladung, 60-Tick-Fenster, Ereignis-Refresh und DE/EN-Texte.

## Version 1.68.0 — Boss-Reaktionssignal für Redstone und Fokus-Priorität

- **Achter Relaismodus:** „Kristallkoloss-Reaktion“ gibt einen Comparator-Wert für aktive Bossphasen aus: 15 während der Atem-Aufladung, 10 bei anderen Aufladeangriffen, 6 bei freigelegtem Kern und 0 ohne aktive Reaktion.
- **Ereignisgesteuert:** Angriffsbeginn, Angriffsabschluss, Fokus-Parade und Ablauf des Kernfensters aktualisieren bis zu 32 nahe Relais. Kein neuer Tick-Loop und keine erzwungenen Chunk-Loads.
- **Priorisierter Fokus:** Ein unterbrechbarer Kristallkoloss wird vor normalen Zielen ausgewählt, damit andere Gegner den bezahlten Parier-Einsatz nicht verdrängen.
- **Farbfeedback:** Atem-Aufladung rot, andere Aufladeangriffe gelb, freigelegter Kern cyan, keine aktive Reaktion grün.
- **Qualitätssicherung:** Regressionen prüfen 128 Blockstates, Bossphasen, Event-Refresh, Fokus-Priorität und DE/EN-Übersetzungen.

## Version 1.67.0 — Resonanzfokus kann den Kristallatem parieren

- **Aktive Gegenmaßnahme:** Der Resonanzfokus erkennt den telegraphierten Kristallatem des Kristallkolosses im Nahbereich und unterbricht ihn, solange mindestens acht Wind-up-Ticks verbleiben.
- **Bezahlte Parieraktion:** Der erfolgreiche Einsatz verbraucht einen Resonanzsplitter und startet die reguläre Fokus-Abklingzeit.
- **Konterfenster:** Nach der Unterbrechung wird der Kern 60 Ticks freigelegt, begleitet von Resonanzpartikeln und Klangfeedback.
- **Mehrere Taktiken:** Der Kristallatem lässt sich weiterhin über einen platzierten, geladenen Dämpfer abfangen; der Fokus eröffnet einen aktiven Timing-Gegenschlag.
- **Regressionen:** Neue Prüfungen sichern Wind-up-Grenze, Synchro-Zustand, Splitterverbrauch, Kernfenster und DE/EN-Rückmeldung.

## Version 1.66.0 — Kristallatem abfangen und Sicherheitsreserve richtig markieren

- **Taktische Boss-Abwehr:** Ein geladener Resonanzdämpfer direkt an der Kristallatem-Bahn kann den Angriff abfangen und verbraucht dafür genau eine Ladung.
- **Rückmeldung und Automation:** Blockzustand, Comparator und nahe Containment-Relais werden nach dem Abfangen aktualisiert; Partikel, Klang und eine DE/EN-Meldung bestätigen den Eingriff.
- **Sicherheitsdiagnose:** Relaismodus 6 verwendet jetzt Rot für geringe, Gelb für mittlere und Grün für hohe Sicherheitsreserven. Die Warnfarben der Gefahrenmodi bleiben erhalten.
- **Leistungsgrenzen:** Der Atembahnen-Scan ist räumlich begrenzt, überspringt ungeladene Chunks und fügt keine permanente Tick-Abfrage hinzu.

## Version 1.65.0 — Überladener Kristallkern und Containment-Sicherheitspuffer

- **Boss-Gegenmaßnahme:** Nach dem Kristallatem ist der Kristallkern 90 Ticks überladen. Die Actionbar und Partikel machen das Zeitfenster sichtbar; Spieler- und Projektiltreffer verursachen 30 % mehr Schaden.
- **Visuelles Feedback:** Brustkern und Rückenstacheln pulsieren während der Überladung stärker. Der Bonus endet automatisch.
- **Redstone-Diagnose:** Der siebte Relaismodus liefert einen Comparator-Wert von 0–15 für die geschätzte Sicherheitsreserve; 15 bedeutet, dass keine Gefahr erkannt wurde.
- **Qualitätssicherung:** Regressionen prüfen Zeitfenster, Schadensbonus, Übersetzungen, Modellreaktion, 112 Relaiszustände und Chunk-Sicherheit.

## Version 1.64.0 — Kopfpanzer des Kristallkolosses und Restgefahr-Signal

- **Kristallkoloss:** Vier kantige Brauen- und Wangenplatten verstärken die Kopfsilhouette und folgen der Kopfanimation. Die Glow-Textur zeigt gezielte cyan-violette Risse.
- **Containment-Relais:** Modus 5 berechnet eine geschätzte Restgefahr aus Feldstärke, Warnsignalen und aktiven Schutzressourcen.
- **Redstone-Automation:** Der geschätzte Restwert kann als Comparator-Signal von weiteren Anlagen ausgewertet werden.
- **Qualitätssicherung:** Modellschichten, UV-Farbflächen, sechs Modi, 96 Blockstate-Kombinationen und Chunk-Sicherheit werden geprüft.

## Historischer Schwerpunkt — 1.53.0

- **Reaktionskampf:** Der Resonanzfokus kann einen laufenden Kristallpirscher-Resonanzimpuls unterbrechen. Das Zeitfenster wird über das vorhandene Klang-/Partikel-Telegraphing angekündigt.
- **Lebende Schutzökologie:** Reifes Filtermoos der Mutagenstufe II/III puffert den tatsächlichen Resonanztreffer im kleinen Schutzradius. Die Prüfung findet nur beim Puls-Auslösen statt, nicht als zusätzliche Tick-Schleife.
- **Forschungsfortschritt:** Der erste echte Gegenimpuls schaltet eine einmalige Forschungsstufe frei und liefert Mutagenextrakt plus zwei Filtereinsätze.
- **Klares Kampf-Feedback:** Eine gelungene Parade verursacht stärkeren Schaden und längere Verlangsamung am Kristallpirscher und verleiht dem Spieler kurzzeitig Resistenz.
- **Release-QA:** Separate Regressionen prüfen Windup-Unterbrechung, Feldschutz, One-shot-Belohnung, Übersetzungen, Forge-JAR und dedizierten Serverstart.
---

## Version 1.53.0 — Mutagenblüten melden sich im Containment-Netz

- **Ereignis löst Alarm aus:** Eine echte Mutagenblüte der höchsten Feldstufe erhöht bis zu vier nahe Warnsirenen direkt auf die kritische Alarmstufe.
- **Die Sirene bleibt ehrlich:** Das Ereignis setzt einen Alarm-Latch, verändert aber keinen physischen Redstone-Eingang. Rechtsklick quittiert wie bisher und synchronisiert den gespeicherten Spitzenwert zurück auf das echte Redstone-Signal.
- **Relais folgen dem Ereignis:** Jede neu erhöhte Sirene aktualisiert ihr nahes Containment-Relaisnetz; der Comparator-Ausgang stellt den gespeicherten Alarmwert bereit.
- **Leistungsgrenzen:** Die Suche läuft nur nach einem tatsächlich ausgelösten, cooldown-geschützten Blütenereignis, überspringt ungeladene Chunks und verarbeitet höchstens vier Sirenen. Kein neuer Block-Ticker.

## Version 1.52.0 — Mutagenblüte, Resonanzdämpfer und Containment-Netz

- **Mehrstufiger Schutz:** Ein eingeschalteter Sporenabwehrsender fängt den Blütenimpuls zuerst ab. Fehlt er, kann ein geladener Resonanzdämpfer innerhalb seines vorhandenen Schutzradius einen Spielerimpuls auffangen.
- **Echte endliche Ladung:** Jeder abgefangene Spielerimpuls verbraucht genau eine Dämpferladung. Leere Dämpfer schützen nicht weiter.
- **Relais und Redstone:** Der tatsächliche Ladungsverbrauch aktualisiert das nahe Containment-Netz. Neue Partikel, Ton und eine einmalige Forschungsstufe bestätigen die Abwehr.
- **Sicherheitsgrenzen:** Die Suche überspringt ungeladene Chunks und läuft nur beim seltenen Mutagenblüten-Ereignis.

## Version 1.51.0 — Resonanzparade und lebender Schutz

- **Aktive Konteraktion:** Ein Resonanzfokus-Treffer während der 30-Tick-Aufladung des Kristallpirschers bricht den noch nicht freigesetzten Impuls ab und startet dessen normale Abklingzeit. Außerhalb des Zeitfensters ist der Treffer ein normaler Fokus-Angriff.
- **Fairer Timing-Bonus:** Eine erfolgreiche Parade verursacht 9 statt 5 Schaden am Kristallpirscher, verlängert die Verlangsamung, verstärkt den Rückstoß und verleiht dem Spieler kurzzeitige Resistenz. Der erfolgreiche Fokusimpuls kostet weiterhin genau einen Resonanzsplitter.
- **Filtermoos als echte Gegenwehr:** Reifes Filtermoos der Stufe II/III kann den freigesetzten Resonanzimpuls innerhalb seines vorhandenen Schutzradius abfangen. Die zusätzliche Prüfung erfolgt beim ohnehin vorhandenen Puls-Auslösen, nicht in einer neuen Tick-Schleife.
- **Einmaliger Forschungsfund:** Die erste Unterbrechung schaltet „Echo gebrochen“ frei und gibt Mutagenextrakt plus zwei Sporenfiltereinsätze. Der Advancement-Status verhindert wiederholtes Farmen der Belohnung.
- **Qualitätssicherung:** Tests prüfen Timing, Windup-Abbruch, Puls-Cooldown, Filtermoos-Schutz, einmalige Belohnung, deutsche/englische Texte, Ressourcen und JAR-Inhalt.

## Version 1.50.0 — Lebendes Filtermoos und natürliche Feldabwehr

- **Ökologische Begleitpflanze:** Ausgewachsenes Filtermoos mit Mutagenstufe II/III bildet einen begrenzten Schutzradius von drei Blöcken horizontal und einem vertikal. Innerhalb dieses Radius schützt es reife Sporenwerk-Pflanzen vor dem Dämmerling.
- **Überlebenshilfe im Feld:** Derselbe Filtermoos-Cluster fängt einen fälligen Mutagen-Expositionsimpuls ab, wenn ein Spieler nahe genug steht. Das verbraucht keine Haltbarkeit der Filtermaske; eine lokale Meldung und Sporenpartikel bestätigen den Schutz.
- **Nachvollziehbare Entdeckung:** Die erste tatsächlich abgefangene Exposition löst den Forschungsfortschritt „Ein lebender Filter“ aus und belohnt zwei gewöhnliche Filtereinsätze.
- **Scanner statt Rätselraten:** Der begrenzte Feldbericht zählt reife Filtermoos-Pflanzen der Stufe II/III im Messgebiet. Dieser Bereichsgesamtwert behauptet nicht, dass jede gezählte Pflanze den Spieler oder ein Ziel gerade schützt.
- **Ressourcen- und Balancegrenzen:** Filtermoos-Prüfungen überspringen ungeladene Chunks; die Spielerprüfung läuft nur zu ohnehin fälligen Expositionszeitpunkten. Keine neue Tick-Schleife und kein erzwungenes Chunk-Laden.
- **Qualitätssicherung:** Regressionen prüfen Mutagenstufen, Pflanzenreife, Schutzradius, Maskenhaltbarkeit, Forschungsbelohnung, Scannerbericht, DE/EN-Texte, Forge-Build und Serverstart.

## Version 1.49.0 — Resonanzfokus und aktive Gegenwehr

- **Neues Kampfwerkzeug:** Der Resonanzfokus feuert einen sichtbaren Impuls und nutzt Kristallpirscher-Resonanzsplitter als echte Munition.
- **Zielgerichtete Wirkung:** Er trifft maximal drei Dämmerlinge oder Kristallpirscher innerhalb von 5,5 Blöcken und nur bei freier Sicht. Der Dämmerling erleidet höheren Schaden und längere Verlangsamung; der Kristallpirscher wird ebenfalls getroffen und kurz ausgebremst.
- **Ressourcenvertrag:** Ein Splitter wird erst nach erfolgreicher Zielsuche verbraucht. Fehlen Ziel oder Munition, wird keine Abklingzeit gestartet.
- **Minecraft-Integration:** Eigenes 16×16-Pixel-Artwork, Rezept, Rezeptbuch-Freischaltung, Creative-Tab-Eintrag und deutsche/englische Tooltips sowie Statusmeldungen.
- **Qualitätssicherung:** Regressionen prüfen Zielarten, Sichtlinie, Reichweite, Zielmaximum, Effekte, Splitterverbrauch, Rezept und Ressourcen. Die Pipeline baut anschließend die installierbare Forge-JAR und startet einen dedizierten Server.

## Version 1.48.0 — Bioreaktor-Kreislauf und reaktive Sporenabwehr

- **Neue Produktionsoption:** Ein Symbiosemyzel wird im Biomasse-Bioreaktor mit 180 FE zu einem Mutagenextrakt veredelt. Der Bioreaktor prüft Ausgabepuffer und Energie vor dem Verbrauch des Eingangs; das Myzel wird erst nach erfolgreicher Ausgabe entfernt.
- **Gegenwehr mit Sichtbarkeit:** Wenn ein powered Sporenabwehrsender einen Dämmerling erstmals abwehrt, erscheinen einmalig Sporenpartikel. Der periodische Refresh verlängert den Schutz, ohne bei jedem Refresh erneut Partikel zu erzeugen.
- **Lokaler Cluster statt bloßer Gesamtzahl:** Der Feldscanner bestätigt einen Symbiose-Cluster nur, wenn drei Pflanzenarten innerhalb derselben begrenzten Nachbarschaft einer reifen Mutagenpflanze der Stufe II/III vorkommen. Die Prüfung nutzt die bereits erfassten Scan-Daten, ohne zusätzliche Weltblöcke zu lesen.
- **Leistungsgrenzen:** Das Scannergebiet bleibt auf Radius 8 und Höhe ±4 begrenzt. Clusterzentren müssen vollständig innerhalb des Messbereichs liegen; ungeladene Chunks werden übersprungen.
- **Qualitätssicherung:** Neue Regressionen prüfen die Bioreaktor-Transaktion, einmaliges Ward-Feedback, lokale Clustererkennung und DE/EN-Texte. Forge-Build, installierbare JAR und dedizierter Serverstart bleiben Pflicht.

## Version 1.47.0 — Symbiose-Forschung und Filter-Endstufe

- **Ökologie wird zur Ausrüstungsprogression:** Der mutagene Filtereinsatz der höchsten Stufe benötigt Symbiosemyzel zusätzlich zu verstärktem Einsatz, Mutagenextrakt und Amethystsplitter.
- **Echte Forschungsfreigabe:** Das Rezept wird erst freigeschaltet, nachdem sowohl Mutagenextrakt als auch Symbiosemyzel entdeckt wurden. Tooltipps erklären die drei Einsatzzwecke des Myzels.
- **Scanner mit Biodiversitätsdiagnose:** Der Umgebungsbericht zählt die vier Sporenwerk-Pflanzenarten im gesamten Messbereich. Er weist ausdrücklich darauf hin, dass drei verschiedene Arten dicht beieinander in Feldstufe II/III wachsen müssen.
- **Bestehende Balance bleibt erhalten:** Haltbarkeit, serverseitige Forschungsprüfung und übrige Komponenten der Upgrade-Kette bleiben erhalten; ergänzt wird nur die ökologische Zutat für die Endstufe.
- **Qualitätssicherung:** Regressionen prüfen Zutaten, Freigabelogik, Scannerzählung, Chunk-Sicherheit und DE/EN-Texte; Forge-Build, JAR-Prüfung und Serverstart bleiben Pflicht.

## Version 1.46.0 — Mutagen-Symbiose und nachhaltige Resonanzpflege

- **Artenreiche Felder werden belohnt:** Bei der Ernte im aktiven Mutagenfeld der Stufe II oder III kann selten Symbiosemyzel entstehen, wenn in der begrenzten Nachbarschaft mindestens drei verschiedene Sporenwerk-Pflanzenarten wachsen.
- **Ein gemeinsamer Erntevertrag:** Manuelle Ernte und Feldsammler verwenden dieselbe serverseitige Biodiversitätsprüfung und dieselbe stufenabhängige Chance. Der Feldsammler reserviert Symbiosemyzel zusammen mit Produkt, Pflanzenresten und mutagenen Sporen, bevor er Energie verbraucht oder die Pflanze verändert.
- **Nützlich für die Abwehr:** Symbiosemyzel stellt bei einem Rechtsklick auf einen Resonanzdämpfer genau eine Ladung wieder her. Ein Kristallpirscher-Resonanzsplitter bleibt der schnellere Weg zur vollständigen Aufladung. Bei vollem Dämpfer wird kein Symbiosemyzel verbraucht.
- **Rückmeldung und Forschung:** Eigenes 16×16-Item-Artwork, Tooltip, deutsche/englische Texte und ein Forschungsfortschritt dokumentieren den Fund. Die visuelle QA-Vorschau zeigt das neue Item.
- **Ressourcengrenzen:** Die Biodiversitätsabfrage ist auf Radius 3 und Höhe ±1 begrenzt, überspringt ungeladene Chunks und läuft nur im Erntevorgang. Kein Block-Ticker und kein erzwungenes Chunk-Laden.
- **Qualitätssicherung:** Regressionen prüfen die Artenzählung, Chancen nach Feldstärke, identische manuelle/automatisierte Ernte, atomare Maschinenpufferreservierung, Dämpferladung, Relay-Aktualisierung, Texte und Ressourcen.

## Version 1.45.0 — Multi-System-Feldanalyse, Gegenmittel und Ereignisfeedback

- **Feldscanner als Diagnosewerkzeug:** Rechtsklick auf Luft führt einen Einmalscan mit Radius 8 und Höhe ±4 aus. Er zählt Mutagenboden der Stufen I–III, mutierte Pflanzen, aktivierte Sporenabwehrsender, Dämpfer samt gespeicherten Ladungen, Sirenenalarme und Containment-Relais; nahe Kristallpirscher werden ebenfalls gemeldet.
- **Einzelmessung von Geräten:** Rechtsklick auf Sporenabwehr, Dämpfer, Warnsirene, Relais oder Kontrollstation zeigt gespeicherte Zustände und Signalwerte.
- **Bessere Überlebensoption:** Rotwurzel-Konzentrat heilt zwei Herzen und entfernt Gift und/oder Verlangsamung. Auch bei vollen Herzen lässt es sich verwenden, wenn ein solcher Effekt aktiv ist.
- **Ereignisfeedback:** Die Mutagenblüte erhält ein akustisches Signal zusätzlich zu bestehenden Partikeln, Belohnungen und Abklingzeit.
- **Sicherheits- und QA-Grenzen:** Der Scanner arbeitet nur auf dem Server, überspringt ungeladene Chunks und läuft nicht im Tick-Loop. Die Tests prüfen außerdem DE/EN-Texte, Forge-Build, JAR und Server-Smoke-Test.

## Version 1.44.0 — Ereignisgesteuerte Containment-Signalverteilung

- Zustandsänderungen an Kontrollstation, Warnsirene, Sporenabwehr oder Resonanzdämpfer aktualisieren nahe Relais.
- Die Verteilung verarbeitet höchstens 32 Relais pro Ereignis, priorisiert nähere Relais und lädt keine Chunks nach.
- Die Station und die Sirenen bleiben die Quelle ihrer gespeicherten Signalwerte; Relais aktualisieren nur ihren eigenen Ausgang.

## Version 1.35.0 — Rückmeldung und Abklingzeit für den Resonanzdämpfer

- **Sichtbar abgewehrt:** Blockiert ein Dämpfer einen Resonanzimpuls, steigen sichtbare Partikel am Gerät auf und ein kurzer Amethystton bestätigt die Abwehr.
- **Keine Scan-Schleife:** Ein bereits gedämpfter Angriffsversuch verbraucht sofort die normale 200-Tick-Abklingzeit. Damit wird der Schutzbereich nicht in jedem Tick erneut vollständig durchsucht.
- **Reaktiv platzierbar:** Wird ein Dämpfer während der 30-Tick-Aufladung platziert, bricht er den Impuls beim Auslösen ab, gibt Feedback und startet die Abklingzeit.
- **Chunk-sicher:** Nur geladene Blöcke werden abgefragt. Die Suche läuft ausschließlich beim Beginn/Ende eines Impulses und nie als kontinuierliche Block-Tick-Schleife.

## Version 1.34.0 — Mutagen-Resonanzdämpfer: technische Gegenwehr

- **Baubare Schutzzone:** Der herstellbare Resonanzdämpfer erzeugt Licht und markiert einen Bereich, in dem der Kristallpirscher seinen Resonanzimpuls nicht beginnen oder freisetzen kann.
- **Knappe, sichere Abfragen:** Der Gegner prüft den kleinen Schutzbereich nur beim Start und am Ende der Warnphase. Nicht geladene Chunks werden übersprungen; das Gerät erzwingt keine Chunk-Ladung und benötigt keinen tickenden Block-Entity-Prozess.
- **Reaktive Gegenwehr:** Wird der Dämpfer während der 30-Tick-Aufladung aufgestellt, bricht er den Impuls beim Auslösen ab. Spieler können also auf die Warnung reagieren, statt schon beim Windup festgelegt zu sein.
- **Survival-Fortschritt:** Das Rezept verlangt Eisen, Redstone, einen Amethystblock und einen Mutagenkernkristall. Eigene Blocktexturen, Modell, Loot-Tabelle, Fortschrittsfreigabe, DE/EN-Namen und Regressionstests sind enthalten.

## Version 1.33.0 — Kristallpirscher: Resonanzimpuls mit Gegenwehr

- Auf Stufe-III-Mutagenboden lädt der Kristallpirscher einen Resonanzimpuls 30 Ticks lang auf. Amethystklang und sichtbare Partikel kündigen die Attacke an.
- Erst nach der Aufladephase löst der Impuls aus; ungeschützte Spieler erhalten in begrenzter Reichweite kurz Verlangsamung. Maske, Ausweichen und ein Dämpfer bieten Gegenwehr.
- Die Fähigkeit hat eine Abklingzeit von 200 Ticks und wird serverseitig mit erneut geprüfter Reichweite und Ausrüstung verarbeitet.

## Version 1.32.0 — Kristallpirscher, Jäger der Hochmutagenfelder

- Eigenständiger Gegner mit eigener Registrierung, 64×64-Pixeltextur, Renderer, Attributen, Spawn-Ei, Loot-Tabelle und Fortschrittsziel.
- Natürliches Spawnen ist auf dunkle Positionen direkt über Mutagenboden der Stufe III begrenzt.
- Ungefilterte Treffer verursachen kurz Gift; die Sporenfiltermaske blockt den Effekt und nutzt dabei Filterhaltbarkeit ab.
- Langsame Regeneration auf Hochmutagenboden, seltene Mutagenkernkristalle und kleine Mengen Pflanzenreste.

## Version 1.31.0 — Quittierbare, gespeicherte Sirenenalarme

- **Spitzenwert bleibt sichtbar:** Die Sirene speichert den höchsten empfangenen Redstone-Wert. Fällt das Signal von kritisch auf einen niedrigeren Wert oder verschwindet es ganz, verschwindet der Alarm nicht unbemerkt.
- **Spieler-Quittierung:** Rechtsklick quittiert den gespeicherten Spitzenwert und synchronisiert die Anzeige mit der aktuell anliegenden Redstone-Stärke. Liegt weiterhin Gefahr an, bleibt sie sichtbar; liegt kein Signal an, wird die Sirene zurückgesetzt.
- **Keine zusätzliche Audio-Last:** Glockentöne werden nur beim Wechsel in eine höhere Gefahrenstufe abgespielt. Das Fallen des Signals und normale Updates bleiben stumm.
- **Qualitätssicherung:** Regressionstests prüfen Latch-Verhalten, manuelle Quittierung, alle 16 Blockstates, Texturen, Übersetzungen und den vollständigen Forge-Build samt Server-Smoke-Test.

## Version 1.30.0 — Eskalierende Mutagen-Warnsirene

- **Vier eindeutig sichtbare Zustände:** AUS, Warnung (Comparator-Signal 1–4), erhöht (5–10) und kritisch (11–15). Die Sirene speichert die empfangene Redstone-Stärke und bildet alle 16 Werte auf passende Blockmodelle ab.
- **Akustische Eskalation:** Beim Wechsel in eine höhere Gefahrenstufe ertönt ein Glockenton mit tieferer Tonhöhe für höhere Gefahr. Der Ton wird nur bei Aktivierung oder Eskalation abgespielt, nicht bei jedem Redstone-Update.
- **Direkt mit dem Comparator kombinierbar:** Der Ausgang der Mutagenfeld-Kontrollstation kann direkt in die Sirene geführt werden. Eine erneute Stationsmessung aktualisiert die Signalstärke und die Sirenenstufe.
- **Qualitätssicherung:** Regressionstests decken Grenzwerte, alle 16 Blockstates, Texturen, Blockmodelle, Rezept, Übersetzungen und Forge-JAR ab.

Automatische Tests ersetzen keinen manuellen Funktionstest des Comparator-/Sirenenaufbaus im Minecraft-Client.

## Version 1.29.0 — Redstone-Warnsirene

- Die craftbare Mutagen-Warnsirene reagiert auf Redstone und zeigt ihren Alarmzustand mit einer eigenen Pixeltextur.
- Der Übergang von AUS auf AN spielt einen kurzen Warnton; ein dauerhaftes Eingangssignal erzeugt keinen Audio-Spam.
- Rezept, Fortschrittsfreigabe, deutsche/englische Namen und Regressionstests sind enthalten.

## Version 1.28.0 — Redstone-Gefahrenausgang der Kontrollstation

- Rechtsklick auf die Mutagenfeld-Kontrollstation aktualisiert einen Comparator-Ausgang zwischen 0 und 15.
- Signal 0: kein erfasster Befall. Signal 3: mutagenaktive Pflanzen ohne erfassten Mutagenboden. Signale 4–10: normaler Mutagenboden abhängig von der gemessenen Menge. Signale 11–15: Stärke-III-Hotspots abhängig von ihrer Anzahl.
- Comparator-Abfragen lesen nur den gespeicherten Wert. Der begrenzte Scan findet ausschließlich beim Stations-Scan statt und wird nicht bei jedem Redstone-Tick wiederholt.
- Deutsche und englische Statusmeldungen und Regressionstests sind enthalten. Nach Feldänderungen erneut scannen, um den Ausgang zu aktualisieren.

## Version 1.27.0 — Mutagenfelder mit eindeutigen Stufensignaturen

- Stufe I: dunkler Moosboden mit grünen Myzeladern.
- Stufe II: violett-schwarzer Untergrund mit magenta-orangen Bruchrissen.
- Stufe III: dunkle Kristallplatten mit cyanfarbenen Kanten und hellen Kernen.
- Beleuchtung und Partikeleffekte folgen der server-synchronisierten Feldstärke.

## Version 1.17.0 — Feldscanner mit Mutagen-Risikoprofil

- Der Luftscan zeigt zusätzlich die Menge aktiven Mutagenbodens, mutierte Pflanzen getrennt nach Stufe I/II/III und Heilanker im erfassten Bereich.
- Die Risikozeile hilft, eine Farm als Ertragszone, Hochrisikofeld oder eingedämmte Versuchsfläche einzuschätzen. Der Scan bleibt auf 12 Blöcke Radius und ±4 Blöcke Höhe begrenzt.
- Die Diagnose läuft serverseitig; der Scanner verwendet keine clientseitig geschätzten Feldwerte. Deutsche und englische Texte sowie die Zählung aller drei Pflanzenstufen werden durch Regressionstests abgesichert.

## Version 1.14.0 — Sporenfilter und Expositionsschutz

- **Sporenfiltermaske:** Herstellbarer Helm mit eigener Pixeltextur, Rüstungs-Layer, deutscher und englischer Lokalisierung und Reparatur mit Leder.
- **Aktiver Feldschutz:** Eine getragene Maske fängt Expositionsimpulse in einem Mutagenfeld ab und verbraucht dabei Haltbarkeit. Ohne Maske bleibt die normale Feldgefahr bestehen.
- **Serverautorität:** Der Filter greift direkt in dieselbe serverseitige Expositionslogik ein und verlängert den gespeicherten Expositions-Cooldown.
- **Qualitätssicherung:** Neue Tests prüfen Helmregistrierung, Rezept, Texturen, Übersetzungen und tatsächliche Schutzlogik; CI validiert anschließend Ressourcen, Forge-Build, JAR und dedizierten Serverstart.

Automatische CI-Tests ersetzen keinen manuellen Sichttest im Minecraft-Client.

## Version 1.13.0 — Sichtbare Mutagenfelder und Feldanalyse

- **Sichtbarer Befall:** Infizierter Boden gibt schwaches Licht ab und wirbelt türkis-violette Sporenpartikel auf; mutierte Pflanzen bekommen zusätzliche Sporenmotes. Die Effekte hängen an synchronisierten Blockzuständen.
- **Scanner mit zwei Modi:** Rechtsklick auf einen Block liest Details; Rechtsklick in die Luft zählt im 12-Block-Radius aktive/inaktive Herde, befallenen Boden und mutierte Pflanzen. Die Spitzenstärke stammt aus Serverdaten.
- **Release-Prüfung:** Partikel- und Scannervertragstests, Ressourcenvalidierung, Forge-Build, JAR-Prüfung und Serverstart.

Automatische CI-Tests ersetzen keinen manuellen Sichttest im Minecraft-Client.

## Mod- und Build-Hinweise

Minecraft Forge 1.20.1 mod project (Java 17).

Automated build via GitHub Actions.

## Version 1.12.0 — Feldscanner und Feldanalyse

- **Feldscanner:** Neues craftbares Survival-Werkzeug mit eigener 16×16-Pixeltextur.
- **Aussagekräftige Messungen:** Rechtsklick auf Blöcke meldet aktive oder inaktive Mutagenherde, Feldstärke, Heilanker, resistente Barrieren sowie frisch befallenen oder bereits abklingenden Boden.
- **Serverautorität:** Der Scanner liest denselben gespeicherten Quellstatus und dieselbe Feldstärke, die Pflanzenmutation und Terrain-Ausbreitung steuern; er erfindet keine clientseitigen Werte.
- **Spielintegration:** Rezept aus Kupfer, Redstone, Glasscheibe, Eisen und Mutagenextrakt, Eintrag im Kreativkatalog und vollständige deutsche/englische Texte.
- **Release-QA:** Eigener Feldscanner-Vertragstest, Prüfung von Modell/Textur/Rezept/Übersetzungen, Forge-Build, JAR-Inhalt und dedizierter Serverstart.

Wie bei den vorherigen Versionen ersetzt der automatisierte Server-Smoke-Test keinen vollständigen manuellen Sicht- und Funktionstest im Minecraft-Client.

## Version 1.7.0 — Mutagenforschung und kontrollierte Produktion

Die nächste Spielmechanik erweitert die Infektion von Spielerwirkungen zu einer räumlich kontrollierten Weltmechanik:

- **Quellgebundene Ausbreitung:** Ein platzierter Mutagenherd infiziert zusammenhängendes geeignetes Terrain innerhalb eines festen Radius von 8 Blöcken und bis zu 3 Blöcken über/unter der Quelle. Wird der Herd entfernt, stoppt die weitere Ausbreitung.
- **Ursprungszustand bleibt erhalten:** Jeder infizierte Terrainblock speichert den exakten ursprünglichen Minecraft-Blockzustand und die Position des auslösenden Herdes. Erz, Container, Maschinen, Pflanzen, Flüssigkeiten, Redstone und andere nicht freigegebene Blöcke werden nicht umgewandelt.
- **Aktive Heilzone:** Ein Mutationsanker stellt ursprüngliche Blockzustände innerhalb eines Radius von 8 Blöcken und 12 Blöcken nach oben/unten schrittweise wieder her. Der Fortschritt wird pro Dimension gespeichert.
- **Gegenmaßnahmen:** Sporenresistente Blöcke können eine physische Barriere bilden. Rezepte für Mutagenherd, Mutationsanker und Sporenresistente Blöcke erlauben die Herstellung im Survival-Modus.
- **Prüfung:** GitHub Actions kontrolliert den Wiederherstellungsvertrag, räumliche Grenzen, Ressourcen, Forge-Build, installierbares JAR und den Start des dedizierten Servers.

Die Implementierung gilt erst als verifiziert, wenn die zugehörige CI vollständig erfolgreich abgeschlossen wurde. Der Build-Workflow erzeugt die gepackte Mod-JAR als GitHub-Actions-Artefakt.


## 1.6.0 — Endgame: Wildwuchs stoppen, Mutagen kontrolliert zurückbringen

- Der **Sterile Kern** deaktiviert gespeicherte Mutagenherde in allen geladenen Dimensionen.
- Bereits befallene Terrainblöcke prüfen ihre Quelle und stellen nach Deaktivierung den gespeicherten Originalzustand wieder her.
- Der Sterile Kern beendet die automatische Feld-Exposition, deaktiviert aber nicht die Vorteile kontrollierter Mutation dauerhaft.
- Ein nach dem Endgame bewusst platzierter Mutagenherd wird neu aktiviert und bleibt trotzdem an sein begrenztes Feld gebunden. So kann der Spieler nach dem großen Weltabschluss gezielt eine Versuchsfläche für Maschinen und mutierte Pflanzen anlegen.
- Bestehende oder alte Herde werden nach dem globalen Stopp nicht automatisch reaktiviert. Für eine neue Anlage ist bewusstes Platzieren erforderlich.

Diese Version ist nur dann als technisch geprüft markiert, wenn die CI die neue Endgame-Regression, den Forge-Build, das JAR und den dedizierten Serverstart erfolgreich beendet hat. Ein automatisierter Server-Smoke-Test ersetzt keinen vollständigen manuellen Test im Minecraft-Client.


## 1.7.0 — Forschungs- und Produktionskette

- **Mutagenprobe:** Im Werkbank-Rezept aus Myzelkompost, Rotwurzel, Amethyst und einer Glasflasche herstellbar.
- **Mutagenextrakt:** Der Biomasse-Bioreaktor verarbeitet eine Probe zu einem Extrakt. Der Zyklus benötigt 120 FE, verbraucht die Probe erst bei erfolgreicher Ausgabe und gewährt 25 Feldwissen.
- **Verknüpfte Geräte-Rezepte:** Mutagenherd, Mutationsanker und Steriler Kern benötigen jetzt Mutagenextrakt. Damit hängen Infektionskontrolle, Heilung und Endgame an derselben Produktionskette.
- **Erster Fund:** Beim erstmaligen Erhalt des Extrakts löst das Spiel pro Spieler einmalig eine kurze Entdeckungssequenz mit Titel, Feldprotokoll und Klang aus. Das ist eine In-Game-Story-Sequenz, keine freie Kamerafahrt.
- **Forschungsfortschritt:** Das vanilla Advancement „Die Probe lebt“ wird ohne Pflichtabhängigkeit von FTB Quests freigeschaltet.

## Versionsstand und Testgrenzen

Die GitHub-Actions-Prüfung für Version 1.7.0 ist erfolgreich durchgelaufen: Regressionstests, JSON-/Texture-/Model-Validierung, Forge-Compile, JAR-Prüfung und dedizierter Serverstart ohne optionale Mods. Der Server-Smoke-Test bestätigt den Start, ersetzt aber keinen vollständigen manuellen Test der Produktionsrezepte, räumlichen Infektion und Story-Sequenz im Minecraft-Client.

Der Build erzeugt build/libs/sporenwerk-1.7.0.jar als GitHub-Actions-Artefakt.


## 1.8.0 — Mutagene Ernte und Ressourcen-Recycling

- Reife Sporenwerk-Pflanzen können innerhalb eines aktiven Mutagenfeldes mit 22 % Chance zusätzlich mutagene Sporen liefern; Heilanker und deaktivierte Quellen unterdrücken diesen Bonus.
- Der Feldsammler nutzt dieselbe Chance. Er reserviert vor dem Verbrauch von Energie, Saatgut oder Ernte die Ausgabeplätze für Ertrag, Pflanzenreste und mögliche mutagene Sporen.
- Drei mutagene Sporen können im Biomasse-Bioreaktor bei 150 FE zu zwei stabilisierten Mutagenextrakten verarbeitet werden und geben 30 Feldwissen.
- Die erste Sporen-Ernte schaltet ein weiteres vanilla Advancement frei. FTB Quests bleibt optional.

Die Sporenproduktion wird vom gespeicherten Status eines aktiven Mutagenherds und dem Heilfeld geprüft, nicht allein von der sichtbaren Blocktextur.


## 1.9.0 — Mutagenfeld-Stärke und Pflanzen-Phänotypen

- Aktive Mutagenherde besitzen drei räumliche Stärkestufen. Der gespeicherte Aktivstatus ist maßgeblich; geheilte Zonen und deaktivierte Quellen geben keine Mutationsboni.
- Mit zunehmender Feldstärke wachsen Sporenwerk-Pflanzen häufiger schneller. Die Ernte-Eigenschaften unterscheiden sich nach Pflanze: Faserrohr liefert zusätzliche Fasern, Rotwurzel kann zusätzliche Wurzelknollen bilden, Bernsteinkappe kann bei höchster Stärke Mehrertrag bilden und Filtermoos liefert öfter Pflanzenreste.
- Die Chance auf mutagene Sporen skaliert mit der Stärke: 12 %, 22 % beziehungsweise 35 %. Handernte und Feldsammler verwenden dieselben Stufen; der Feldsammler reserviert mögliche Ausgaben weiterhin atomar vor Energie- oder Pflanzenverbrauch.
- GitHub Actions prüft Stufengrenzen, Unterdrückung durch Heilanker, Pflanzenboni, Ausgabepuffer, Forge-Build, JAR-Inhalt und dedizierten Serverstart.


## 1.10.0 — Minecraft-Texturen und sichtbare Pflanzen

- **Ursache der fehlerhaften Blockgrafik behoben:** Vollblock-Modelle verwendeten teilweise transparente Item-Sprites als Flächentexturen. Dadurch waren Flächen unsichtbar oder sahen nicht wie Minecraft-Blöcke aus.
- Vollblöcke und Maschinenflächen werden nun als **vollständig deckende 16×16-Pixeltexturen** mit getrennten Ober-, Seiten- und Unterseiten erzeugt. Die Modelle nutzen Minecrafts Cube-Textur-Slots.
- Die vier transparenten Pflanzen-Texturen erhalten explizit den Forge-Render-Layer `cutout`. Das verhindert, dass transparente Pflanzenteile falsch dargestellt werden.
- Die neue Texture-QA-Vorschau zeigt echte Blockflächen und markiert Spawn-Eier nicht mehr fälschlich als fehlende PNG-Texturen.
- Die CI prüft Texturabmessungen, Alpha-Kanal, Modellreferenzen, Crop-Cutout-Rendering, Forge-Build, JAR und dedizierten Serverstart.

Die visuelle Korrektur wird erst als bestanden markiert, wenn die Textur-Regressionen und der Forge-Build erfolgreich sind. Der Servertest bestätigt Ressourcensammlung und Start, ersetzt aber keinen vollständigen manuellen Test im Minecraft-Client.


## 1.11.0 — Sichtbare Mutagen-Phänotypen

- Alle vier Sporenwerk-Pflanzen zeigen jetzt neben ihrem Wachstumsstadium auch eine echte Mutagen-Stufe von 0 bis 3.
- Der Server aktualisiert den Blockzustand anhand der Stärke des aktiven Mutagenfeldes. Die Modelle wählen dazu eigene 16×16-Sprites mit erkennbar veränderter Farbpalette und Mutagen-Adern.
- Wenn das Feld nicht mehr aktiv ist oder ein Heilanker den Standort neutralisiert, fällt die Pflanze bei ihrer nächsten Aktualisierung auf die normale Textur zurück. Das funktioniert auch bei reifen Pflanzen.
- Die Textur- und Blockstate-Tests prüfen für jede Pflanze alle 8 Wachstumsalter × 4 Mutagen-Stufen, alle zugehörigen Modelle und PNGs, deckende Maschinen-/Blockflächen und den Cutout-Render-Layer.
- Der neue Forge-Build wird zusätzlich als JAR geprüft und muss den dedizierten Serverstart ohne optionale Mods bestehen.

Version 1.10.0 enthält die separate Korrektur für deckende Minecraft-Blocktexturen und Pflanzen-Cutout-Rendering; 1.11.0 baut darauf mit sichtbaren, feldabhängigen Pflanzenvarianten auf.
