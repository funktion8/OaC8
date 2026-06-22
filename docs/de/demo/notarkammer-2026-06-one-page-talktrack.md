# Notarkammer-Demo: 1-Seiten-Handout und Talktrack

Stand: 2026-06-22

## Ziel

Der Termin soll NaC als 100% notariat-faehigen ISV-Kandidaten positionieren.
Das konkrete Ziel ist XNP/SNP-Testzugang, klaerbare Pilotrollen und der
naechste Schritt zur ISV-Listung. Die Demo verkauft keinen Produktivzugang,
sondern zeigt einen sicheren Gespraechsrahmen fuer Freigabe, Testdaten,
Evidence-Felder, Status-Callbacks und Zertifizierungsanforderungen.

## Primaervorgang

Primaervorgang ist der Immobilienkaufvertrag. Er ist fachlich stark genug,
um Entwurf, Beurkundung, Auflassungsvormerkung, Vorkaufsrecht,
Unbedenklichkeitsbescheinigung, Loeschungsunterlagen, Kaufpreisfaelligkeit
und Vollzug in einem BPMN-Bild zu zeigen.

## BPMN-Talktrack

- NaC zeigt den Immobilienkaufvertrag als BPMN-Vorgang mit parallelen
  Vollzugspfaden, Dauerbaendern, kritischem Pfad und Evidence-Gates.
- XNP bleibt die lokale notarielle Arbeitsumgebung; XNotar steht fuer
  Grundbuch- und Registervorbereitung, Validierung, Signatur und beN-Versand.
- Kartenleser, SAK/KMC und Signatur werden nur als lokale Readiness-Grenze
  gezeigt; NaC speichert keine PINs, Kartenwerte oder Tokens.
- Register und Grundbuch erscheinen als externe Warte-, Nachweis- und
  Ruecklaufpunkte, nicht als direkte NaC-Datenquellen.
- Vollzug wird als fachliche Gate-Kette erklaert: erst wenn externe
  Nachweise vorliegen, kann der naechste BPMN-Schritt freigegeben werden.

## Klare Nicht-Claims

- keine produktive XNP-Aktion,
- keine Mandatsdaten,
- keine echten Register-/Grundbuchabfragen,
- keine OCI-Aktionen,
- keine Secrets,
- keine Live-Calls,
- keine Aussage, dass NaC XNP, XNotar, Register oder Grundbuch produktiv
  steuert.

## Abschlussfrage

Welche XNP/SNP-Testumgebung, ISV-Rolle, Evidence-Felder, Status-Callbacks,
Fehlerklassen und Zertifizierungsschritte braucht NaC, damit der
Immobilienkaufvertrag als offizieller ISV-Pilot vorbereitet werden kann?
