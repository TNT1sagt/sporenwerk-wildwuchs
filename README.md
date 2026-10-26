# Sporenwerk: Wildwuchs

**Aktueller Entwicklungsstand: 1.85.0 — lebendige Horror- und Kulturfelder mit eigenem Ambiente.**

Dieses Repository enthält die Patch-Skripte und Regressionstests, mit denen der GitHub-Actions-Workflow den Minecraft-Forge-1.20.1-Mod aus dem Quellstand zusammensetzt. Die installierbare JAR wird durch den Workflow gebaut; automatisierte Prüfungen sind kein Ersatz für einen vollständigen Sichttest im Minecraft-Client.

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
