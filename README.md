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

# Sporenwerk: Wildwuchs

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
