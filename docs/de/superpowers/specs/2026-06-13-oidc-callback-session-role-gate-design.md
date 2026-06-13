# OIDC Callback, Session und NaC-Rollengate

## Kontext

Der Live-Test fuer `myjur` hat den OIDC-Fluss bis zur Rueckkehr nach
`/auth/callback` bestaetigt. Passwort-Reset, Consent und Redirect funktionieren.
NaC zeigt danach bewusst nur `Anmeldung empfangen`, weil der Arbeitsbereich erst
nach serverseitiger State-, Token-, Session- und Rollenpruefung geoeffnet werden
darf.

Der aktuelle Zustand ist damit kein Identity-Provider-Fehler, sondern der
naechste Produktinkrement: Der Auth-Callback muss vom geschlossenen
Zwischenereignis zur validierten notariat8-Sitzung werden.

## Entscheidung

Ansatz A ist freigegeben: `/auth/callback` wird fachlich zur auth/stateful
Runtime gehoeren. Die Public-GET-Function bleibt fuer oeffentliche Seiten und
Login-Intent-Readiness leicht und moeglichst secretfrei. Token-Austausch,
Client-Secret-Zugriff, Session-Erzeugung und NaC-Rollengate laufen serverseitig
im geschuetzten Callback-Pfad.

## Ziele

- `state` wird serverseitig validiert und abgelaufene oder fremde Werte schlagen
  geschlossen fehl.
- Der Authorization Code wird nur serverseitig gegen Tokens getauscht.
- ID-Token werden gegen Issuer, Audience, Nonce und Signatur geprueft.
- NaC mappt Identity-Domain-Gruppen oder Claims auf eigene Rollen.
- Ein geschuetzter Arbeitsbereich wird erst nach positivem Rollengate geoeffnet.
- Callback-Werte, Tokens und Secrets erscheinen nicht in Browsertexten, Logs,
  GitHub, Git oder Chat.

## Nichtziele

- Keine Mandatsdaten in diesem Track.
- Kein generisches Benutzerverwaltungs-Frontend.
- Keine Umstellung der gesamten Public-GET-Function auf eine secretfuehrende
  Runtime.
- Keine OCI-Schreiboperation ohne eigenes Owner Apply Gate.

## Architektur

Die Login-Intent-Route bleibt public und erzeugt den signierten Redirect-Kontext.
Der Callback wird dagegen in eine stateful/auth Runtime gefuehrt. Diese Runtime
hat Zugriff auf die notwendigen Vault-Referenzen, nicht auf Klartext-Secrets in
Git oder Function-Konfiguration.

Der Callback verarbeitet nur serverseitig:

1. Query empfangen und Log-Ausgabe redigieren.
2. `state` validieren und `tenant_hint` nur als Kontext behandeln.
3. Code am Token-Endpunkt tauschen.
4. ID-Token und Nonce validieren.
5. Gruppen/Claims auf NaC-Rollen abbilden.
6. Session-Cookie mit sicheren Attributen setzen.
7. Nur bei passender Rolle in den Arbeitsbereich weiterleiten.

## Rollenmodell

Fuer den ersten Live-Test ist `nac-tenant-admin` der Rollenanker. Ein IdP-Login
allein reicht nicht. NaC akzeptiert nur eine serverseitig verifizierte
Rollenbindung, zum Beispiel die Mitgliedschaft in `nac-tenant-admin`, bevor der
Arbeitsbereich fuer `myjur` geoeffnet wird.

`tenant_hint` bleibt unverbindlich. Er hilft beim Routing und bei der Anzeige,
begruendet aber keine Berechtigung.

## Sicherheitsregeln

- Client Secrets liegen ausschliesslich in OCI Vault oder einem gleichwertigen
  Secret Store.
- Tokens werden nicht persistiert, solange keine explizite Session-Store-
  Entscheidung getroffen wurde.
- Session-Cookies sind `HttpOnly`, `Secure` und `SameSite=Lax`.
- Fehlerseiten zeigen keine Providerdetails, Codes, States, Nonces, Tokens oder
  Secret-Referenzen.
- Rollengate-Fehler sind geschlossen: kein Workspace, keine Mandatsdaten.

## Tests

Die Implementierung braucht Tests fuer:

- gueltigen Callback mit validiertem State, Token-Antwort und passender Rolle,
- ungueltigen oder abgelaufenen State,
- Token-Exchange-Fehler ohne Secret-Leak,
- ID-Token mit falschem Issuer, falscher Audience oder falscher Nonce,
- fehlende Rolle trotz erfolgreichem IdP-Login,
- Session-Cookie nur nach positivem Rollengate,
- Schutz gegen Callback-Werte in HTML und Logs.

## Auslieferung

Die Code-Aenderung erfolgt ueber geschuetzten PR. Danach folgen getrennte Gates:

1. Release Approval fuer das neue NaC-Image.
2. Resource-Manager-Plan ohne Apply fuer Route/Function-Konfiguration.
3. Owner Apply Approval fuer die Callback-Route zur auth/stateful Runtime und
   die Vault-Secret-Referenz.
4. Live-Test mit synthetischem `myjur`-Testkonto.
