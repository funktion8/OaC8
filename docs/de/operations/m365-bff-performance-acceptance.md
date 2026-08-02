# M365-BFF-Performance-Abnahme

Status: geplante Dokumentations- und JSON-Vertragsschicht; diese Änderung
implementiert keinen Live-Runner.

Dieser Standard definiert eine kapazitätsgebundene Abnahme-Lane für den
aktivierten M365-BFF-Read-Endpunkt. Die maschinenlesbare Quelle ist
[m365-bff-performance-acceptance.contract.json](../../../workflows/contracts/m365-bff-performance-acceptance.contract.json),
der Verification-Harness steht in
[m365-bff-performance-acceptance.verification.json](../../../workflows/verification-contracts/m365-bff-performance-acceptance.verification.json).

## Feste Route

Das fachliche Ziel ist unveränderlich:

| Feld | Exakter Wert |
| --- | --- |
| Schema | `https` |
| Host | `func-nac-bff-test-funktion8.azurewebsites.net` |
| Methode | `GET` |
| Workspace | `notary_team_01` |
| Akte | `NAC-SYN-MATTER-001` |
| Pfad | `/v1/workspaces/notary_team_01/matters/NAC-SYN-MATTER-001/workbench-snapshot` |
| Query | `purpose=view_synthetic_matter_workspace` |
| Wire-Schema | `nac.workbench.snapshot/v1` |

Redirects, alternative Ziele, Klartext-HTTP und Cache-Busting-Änderungen sind
verboten. Jede versandte Anfrage muss exakt HTTP `200` erhalten, als
`nac.workbench.snapshot/v1` validieren und darf höchstens `1 MiB` groß sein.
Bodies werden im Speicher validiert und niemals aufbewahrt.

## Kapazitäts-Preflight

Die Live-Ausführung ist `BLOCKED`, solange keine aktuelle autoritative Evidence
den SharePoint-Service-Tier des Tenants identifiziert und sowohl dessen
Anfragen-Allowance als auch dessen Resource-Unit-Allowance verifiziert.
Schätzungen, Defaults und abgeleitete Tiers sind keine autoritative Evidence.

Der Preflight misst außerdem die Baseline-Last des Tenants für Anfragen und RU
und leitet die Testallokation aus einer konservativen RU-Obergrenze pro Anfrage
ab. Baseline plus geplante Testlast müssen in jedem durch den autoritativen Tier
definierten Allowance-Zeitfenster bei höchstens `50 %` beider verifizierter
Allowances bleiben. Die niedrigere resultierende Rate begrenzt jede Phase.
Evidence, die älter als 24 Stunden, an einen anderen Tenant/Workspace gebunden
oder ohne verfügbare Allowance ist, lässt den Status auf `BLOCKED`.

Der Azure-Preflight liest Azure Monitor und verlangt:

- `AlwaysReadyUnits=0`
- prognostizierte und beobachtete Execution Units der Abnahme höchstens am
  inklusiven Cap von `120.000 GB-s`
- fortlaufende Monitor-Verfügbarkeit während und nach dem Lauf

Dies sind Read-only-Prüfungen. Sie erlauben keine Kapazitäts-, Berechtigungs-,
Konfigurations- oder Infrastrukturänderung.

## Globales Dispatch-Budget

Für alle Phasen gilt exakt ein inklusives globales Limit:

```text
maximale Target-Dispatches = 50.000
```

Dies ist eine Obergrenze, keine vorgeschriebene Anzahl. Ein erfolgreicher
sicherer Plan darf weniger Anfragen verwenden. Jeder Target-Versuch zählt,
einschließlich Versuchen mit Timeout, Authentifizierungsfehler, Redirect,
Throttling oder Abort. Vor dem Netzwerkversand wird atomar eine Sequenz
reserviert. Wenn die nächste Sequenz `50.000` überschreiten würde, wird keine
Anfrage gesendet.

Client-Retries und automatisches Folgen von Redirects sind deaktiviert. Es gibt
weder eine unbedingte Phase mit 50.000 Anfragen noch die unbedingte Vorgabe,
50.000 Anfragen innerhalb von zwei Stunden abzuschließen.

## Phasen

Der owner-gebundene Phasenplaner allokiert alle Phasenbudgets vorab. Ihre Summe
darf höchstens `50.000` betragen; jede Rate wird durch die verifizierten
50-%-Allowances für Anfragen und RU begrenzt.

| Phase | Sicherheitsgebundenes Verhalten |
| --- | --- |
| `idle_cold_start_assessment` | 20 Minuten Runner-Idle-Zeit beobachten, danach exakt eine Anfrage senden; Infrastruktur nicht neu starten. |
| `capacity_bounded_volume` | Eine dynamische owner-gebundene Allokation höchstens zwei aktive Stunden verwenden; es gibt keine unbedingte Anfragenzahl. |
| `sustained_2h` | Höchstens zwei aktive Stunden mit der niedrigeren Rate aus 4 Anfragen/Sekunde und Kapazitäts-Preflight ausführen. |
| `soak_24h` | Höchstens 24 aktive Stunden, nicht schneller als eine Anfrage/Minute und mit höchstens 1.440 Dispatches ausführen. |

Die akzeptierte Fehlerrate beträgt `0 %`. Für jede Anfrage gilt eine
Latenzobergrenze von `10.000 ms`. Volume- und Sustained-Phase verlangen p95
höchstens `1.000 ms` und p99 höchstens `2.000 ms`; für Soak gelten p95 höchstens
`1.500 ms` und p99 höchstens `3.000 ms`. Diese Metriken bleiben reine
Aggregate.

Die Phasen laufen nacheinander und verwenden keine Catch-up-Bursts. Ein
restart-sicherer Zustand persistiert die globale Sequenz, verbrauchte
Allokation sowie alle Vertrags-, Aktivierungs-, Ziel-, Kapazitäts- und
Phasenplan-Hashes. Ein Resume darf keine Zähler verringern, keine Sequenz
wiederverwenden und keine freigegebene Allokation erhöhen.

## Cold-Start-Klassifikation

Die 20-minütige Idle-Beobachtung allein weist keinen Plattform-Cold-Start nach.
`cold_start_classification` ist nur dann `VERIFIED`, wenn autoritative
Server-Telemetrie beweist, dass sich die Serverinstanz oder die Server-Start-
Epoch zwischen gebundener Baseline und gemessener Anfrage geändert hat.

Wenn diese Änderung fehlt, unverändert, nicht verfügbar oder nicht beweisbar
ist, lautet die einzig zulässige Klassifikation `INCONCLUSIVE`. Rohe Instanz-
und Start-Epoch-Werte werden niemals aufbewahrt. Die Infrastruktur wird nicht
neu gestartet, um ein Ergebnis zu erzwingen.

## Abort-Verhalten

Die Lane bricht ohne Retry ab bei:

- Authentifizierungsfehler oder Challenge
- jeder Redirect-Antwort oder jedem `Location`-Signal
- jedem Throttle-Status oder Throttle-Signal
- Drift bei Schema, Host, Port, Pfad, Query, DNS, Zertifikat oder Target-Binding
- Status ungleich `200`, Schemafehler oder Antwort über `1 MiB`
- Überschreitung der Anfrage- oder aggregierten Phasen-Latenzschwelle
- ausgeschöpftem globalem Dispatch-, verifiziertem Anfragen-/RU- oder Azure-Execution-Unit-Budget
- veralteter oder nicht verfügbarer Kapazitäts- oder Azure-Monitor-Evidence
- beschädigtem Zustand oder fehlgeschlagener Evidence-Redaktion

Ein Abort löst keinen Rollback, keine Löschung, Berechtigungs- oder
Credential-Änderung und keinen Infrastruktur-Neustart, keine Skalierung oder
Umkonfiguration aus.

## Aggregierte Evidence

Die Evidence besteht aus redigiertem JSON und semantisch entsprechendem
Markdown und enthält ausschließlich Aggregate: Phasenzähler und -metriken,
globalen Dispatch-Zähler, genutzte Anteile der verifizierten Allowances, Azure
Execution Units, Always Ready Units, Cold-Start-Klassifikation, den booleschen
Instanz-/Epoch-Wechsel, Hashbindungen und einen Abort-Reason-Code.

Die Evidence speichert keinen Einzelrequest-Datensatz, rohe Header, Bodies,
Body-Hashes, URLs, Pfade, Hosts, Queries, Tokens, Cookies, Credentials,
Tenant-IDs, Benutzer-IDs, Serverinstanz-IDs, Start-Epochen,
Provider-Antworten oder Azure-Monitor-Antworten. Unbekannte Evidence-Felder
führen zur Ablehnung des Artefakts.

## Aktivierungs- und Owner-Gate

Ein künftiger Live-Befehl bleibt an redigierte Aktivierungs-Evidence mit
finalem Status exakt `PASSED` gebunden. Die Owner-Freigabe bindet Aktivierung,
Vertrag, festes Ziel, Kapazitäts-Preflight, Phasenplan und Correlation-ID. Der
geplante Befehlsname lautet:

```text
nac m365 teams-sharepoint bff-performance-acceptance
```

Er wird durch diese Dokumentationsschicht nicht implementiert. Fehlende oder
abweichende Aktivierungs-, Owner-, Kapazitäts- oder Zielbindungen blockieren
vor jedem Target-Dispatch.
