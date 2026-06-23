# Notarkammer-Demo: Login-Checkliste

Status: kurze Demo-Checkliste fuer den geschuetzten Einstieg. Keine
Runtime-Aenderung, kein Infrastruktur-Apply, keine Secrets.

## Einstieg

- Start: `https://app.notariat8.de/login`
- Nur der Login-Einstieg und die geschlossene Startgrenze sind im Scope.
- Kein Zugriff auf Mandate, Akteninhalte, Urkunden, Register- oder
  Grundstuecksdaten.

## Statuspunkte

| Punkt | Zeigbar | Stopper |
| --- | --- | --- |
| Token-Austausch | Ampel- oder Textstatus ohne technische Rohwerte. | Nicht abgeschlossen, ungueltig oder nicht vorfuehrstabil. |
| Token-Prüfung | Bestaetigung, dass die Anmeldung geprueft wurde. | Pruefung offen, fehlgeschlagen oder nicht belastbar. |
| Rollengate | Demo-Rolle ist fuer den Einstieg freigegeben. | Rolle offen, unbekannt oder nicht demo-freigegeben. |
| Sitzung | Sitzung nur redaktiert: Status, Zeitfenster, Demo-Freigabe. | Sitzung offen, nicht belastbar oder mit Rohwerten sichtbar. |

## Redaktionsgrenzen

- Keine Secrets, Tokens, Claims oder technischen Rohwerte zeigen.
- Keine Callbacks, keine Parameter oder Browser-Adressdetails zeigen.
- Keine Providerdetails, Konfigurationswerte oder Anbieterdiagnosen nennen.
- Keine Konsolen, Cloud-Ansichten oder Infrastrukturaktionen im Termin.
- Keine echten Personen-, Akten-, Urkunden-, Register- oder
  Grundstuecksdaten verwenden.

## Entscheidung

- Gruen: Alle vier Statuspunkte sind abgeschlossen und redaktiert zeigbar.
- Gelb: Ein Punkt ist offen; Einstieg als fail-closed erklaeren und auf den
  vorbereiteten Prozesspfad wechseln.
- Rot: Ein Punkt ist fehlgeschlagen oder zeigt Rohwerte; Live-Pfad stoppen,
  keine Live-Fehlersuche.
