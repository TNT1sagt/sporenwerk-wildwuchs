# Sporenwerk: Wildwuchs

Minecraft Forge 1.20.1 mod project (Java 17).

Automated build via GitHub Actions.

## Aktueller Entwicklungsschwerpunkt: reversible Mutagenfelder

Die nächste Spielmechanik erweitert die Infektion von Spielerwirkungen zu einer räumlich kontrollierten Weltmechanik:

- **Quellgebundene Ausbreitung:** Ein platzierter Mutagenherd infiziert zusammenhängendes geeignetes Terrain innerhalb eines festen Radius von 8 Blöcken und bis zu 3 Blöcken über/unter der Quelle. Wird der Herd entfernt, stoppt die weitere Ausbreitung.
- **Ursprungszustand bleibt erhalten:** Jeder infizierte Terrainblock speichert den exakten ursprünglichen Minecraft-Blockzustand und die Position des auslösenden Herdes. Erz, Container, Maschinen, Pflanzen, Flüssigkeiten, Redstone und andere nicht freigegebene Blöcke werden nicht umgewandelt.
- **Aktive Heilzone:** Ein Mutationsanker stellt ursprüngliche Blockzustände innerhalb eines Radius von 8 Blöcken und 12 Blöcken nach oben/unten schrittweise wieder her. Der Fortschritt wird pro Dimension gespeichert.
- **Gegenmaßnahmen:** Sporenresistente Blöcke können eine physische Barriere bilden. Rezepte für Mutagenherd, Mutationsanker und Sporenresistente Blöcke erlauben die Herstellung im Survival-Modus.
- **Prüfung:** GitHub Actions kontrolliert den Wiederherstellungsvertrag, räumliche Grenzen, Ressourcen, Forge-Build, installierbares JAR und den Start des dedizierten Servers.

Die Implementierung gilt erst als verifiziert, wenn die zugehörige CI vollständig erfolgreich abgeschlossen wurde. Der Build-Workflow erzeugt die gepackte Mod-JAR als GitHub-Actions-Artefakt.
