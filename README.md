# Sporenwerk: Wildwuchs

**Aktueller Entwicklungsstand: 1.62.0 — mehrlagige Kristallkoloss-Panzerung mit cyan-violetten Leuchtkanten.**

Dieses Repository enthält die Patch-Skripte und Regressionstests, mit denen der GitHub-Actions-Workflow den Minecraft-Forge-1.20.1-Mod aus dem Quellstand zusammensetzt. Die installierbare JAR wird durch den Workflow gebaut; automatisierte Prüfungen sind kein Ersatz für einen vollständigen Sichttest im Minecraft-Client.

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
