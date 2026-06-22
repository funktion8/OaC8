# Notarkammer-Demo 2026-06: Fallback-Evidence-Manifest

Status: geschuetzter Demo-Nachweis fuer vorbereitete Screenshots und
Ersatzansichten. Keine produktive Einreichung, keine echten Mandatsdaten, keine
Secrets.

Dieses Manifest beschreibt, welche vorbereiteten Ansichten in der
Notarkammer-Demo verwendet werden duerfen, wenn Live-Seiten langsam sind oder
ein lokaler Arbeitsplatz nicht bereit ist. Es ersetzt keine Live-Pruefung,
sondern verhindert Ad-hoc-Debugging im Termin.

## Erlaubte vorbereitete Evidence

| Evidence | Erlaubter Inhalt | Zweck |
| --- | --- | --- |
| `notariat8.de` Startseite | Oeffentliche Startseite ohne Akten- oder Mandatsbezug. | Einstieg stabil zeigen, wenn die Seite nicht laedt. |
| `notariat8.de/prozessmodell.html` | Prozessmodell Immobilienkaufvertrag mit Dauerlogik, Parallelitaet und kritischem Pfad. | BPMN-Logik erklaeren, wenn der Viewer nicht laedt. |
| `app.notariat8.de/workspace` | Geschlossene oder metadata-only Ansicht mit fail-closed Status. | Sicherheitsgrenze zeigen, wenn Login nicht fortgesetzt wird. |
| XNP und card reader Readiness | Nur lokaler Status `ready`, `manual_review` oder `blocked`; keine Rohdaten. | XNP als lokale Arbeitsplatzgrenze erklaeren. |
| Protected PR | Pull Request, Checks und redigierte Testausgabe. | Aenderungs- und Freigabespur zeigen. |

## Nicht erlaubte Evidence

- keine echten Mandatsdaten
- keine Ausweise
- keine Urkunden
- keine Registerauszuege
- keine Grundbuchdaten
- keine Zugangsdaten
- keine PINs
- keine Tokens
- keine Schluessel
- keine produktive Einreichung
- keine produktive XNP-, Register- oder Grundbuchaktion

## Redaktionsregel

Screenshots und Nachweise duerfen nur sichtbare Produkt- oder
Prozessoberflaechen zeigen. Fenster mit Logins, Tokens, Cookies, Session-Werten,
interner Infrastruktur, Secret-Referenzen, Wallets oder echten Namen werden
nicht verwendet. Wenn ein Screenshot unsicher ist, wird er nicht gezeigt.

## Stop-Line

"Wir zeigen jetzt die vorbereitete, redigierte Evidence. Sie belegt den
geprueften Demo-Stand und enthaelt keine Mandatsdaten."
