# ATP Runtime Graph Projection

Status: owner-freier Contract-first-Slice, kein OCI-Apply.

Dieser Vertrag ergaenzt den ATP Runtime Store um eine testbare Graph-Projektion aus
`process_events`. Die Projektion erzeugt eine mandatsdatenfreie Metadatensicht fuer
Demo, Review und spaetere Oracle-Graph-Aktivierung.

## Zweck

Die Runtime-Events bleiben die Append-only-Quelle. Daraus wird eine Graph-Sicht
abgeleitet:

- Knoten fuer Prozessinstanz, Gates und externe Systeme.
- Kanten fuer Event-Gates, externe Beruehrungspunkte und Abhaengigkeiten.
- Parallelgruppen fuer fachlich gleichzeitig moegliche Schritte.
- Dauerbaender fuer Stunden, Tage, Wochen oder Monate.
- kritischer Pfad fuer Schritte, die den Vollzug voraussichtlich bestimmen.

## Guardrails

- Kein Live-OCI.
- Kein Schema-Apply.
- Keine Secrets.
- Keine Mandatsdaten.
- Keine produktive XNP/SNP-Aktion.
- Keine rohen Browser-Identifier als fachlicher Output.

Die erste Umsetzung ist bewusst eine Python-Projektion. Eine spaetere Oracle-Graph-
oder PGQL-Nutzung bleibt ein eigener Owner-Gate-Schnitt.
