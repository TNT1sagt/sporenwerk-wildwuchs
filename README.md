# Sporenwerk: Wildwuchs

**Aktueller Entwicklungsstand: 1.31.0 — gespeicherte Mutagen-Alarme mit Spieler-Quittierung.**

Dieses Repository enthält die Patch-Skripte und Regressionstests, mit denen der GitHub-Actions-Workflow den Minecraft-Forge-1.20.1-Mod aus dem Quellstand zusammensetzt. Die installierbare JAR wird durch den Workflow gebaut; automatisierte Prüfungen sind kein Ersatz für einen vollständigen Sichttest im Minecraft-Client.

## Aktueller Schwerpunkt — 1.31.0

- Mutagenfeld-Stufe I: dunkler Moosboden mit grünen, verzweigten Myzeladern.
- Mutagenfeld-Stufe II: violett-schwarzer Untergrund mit magenta-orangen Bruchrissen.
- Mutagenfeld-Stufe III: dunkle Kristallplatten mit cyanfarbenen Kanten, hellen Kernen und deutlich stärkerem Leuchten.
- Beleuchtung und Partikel folgen der server-synchronisierten Feldstärke; die Partikel bleiben durch ein festes Budget begrenzt.
- Ein Scan an der Mutagenfeld-Kontrollstation aktualisiert einen Comparator-Gefahrenwert von 0 bis 15, ohne Welt-Scans bei jedem Redstone-Tick auszulösen.
- Die Mutagen-Warnsirene unterscheidet Warnung, erhöhte Gefahr und kritische Belastung visuell; Warntöne eskalieren nur bei einem Wechsel in eine höhere Stufe.

---

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
