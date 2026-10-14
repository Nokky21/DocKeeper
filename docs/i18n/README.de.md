<div align="center">

# DocKeeper

**Dokumentation, die nicht verrottet.**

Dein Coding-Agent schreibt die Doku, Diagramme inklusive. DocKeeper verknüpft jede Aussage und jedes Diagramm mit dem Code dahinter und meldet sich, sobald sich dieser Code ändert.

[![CI](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml/badge.svg)](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-2ea44f)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](../../LICENSE)

[Website](https://nokky21.github.io/DocKeeper/) · [Live-Demo](https://nokky21.github.io/DocKeeper/#demo) · [Installation](#install) · [Referenz](../reference.md)

<sub>[English](../../README.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · **Deutsch** · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [Türkçe](README.tr.md) · [العربية](README.ar.md) · [עברית](README.he.md) · [हिन्दी](README.hi.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md) · [ไทย](README.th.md)</sub>

</div>

---

## Warum

Ein README, das heute geschrieben wird, ist ein paar Monate später falsch, und niemand weiß, welche Seiten lügen. DocKeeper löst den Teil mit dem „niemand weiß“, kostenlos und auf deinem Rechner:

- **Jede Aussage wird geprüft.** „Zahlungen werden vor der Abbuchung validiert“ ist mit der Funktion verknüpft, die das tut. Ändert sich diese Funktion, sagt DocKeeper es dir.
- **Keine KI in der Prüfung.** Dein Agent schreibt; die Prüfung vergleicht Fingerabdrücke und liefert deshalb immer dieselbe Antwort.
- **Lokal und kostenlos.** Kein Konto, kein Server, kein Netzwerk, keine Abhängigkeiten. MIT-Lizenz.

## Was er schreibt

Einmal bitten, und dein Agent dokumentiert das ganze Repository Seite für Seite, nach den Vorlagen des Skills:

- **README**: was es ist, wie es funktioniert, wie man es startet.
- **Architektur**: Komponenten, Abläufe, Daten und Grenzen, mit Diagrammen.
- **Entscheidungen**: was entschieden wurde und warum, nur aus der Git-Historie.
- **Betriebsanleitungen**: Runbooks mit den genauen Befehlen.
- **API**: jede Operation mit Eingaben, Fehlern und Wirkungen.
- **Einarbeitung**: ein Lesepfad für den ersten Tag.

In einem Monorepo schreibt er zusätzlich ein README pro Paket. Jede Aussage zeigt auf ihren Code. Siehe [die Architektur von DocKeeper selbst](../architecture.md), geschrieben mit dem Skill.

## So funktioniert es

<p align="center"><img src="../../site/public/assets/how-it-works.svg" alt="So funktioniert DocKeeper: Eine Aussage wird an einen Codeblock verankert, der Block bekommt einen Fingerabdruck, und check meldet OK, MOVED oder CHANGED" width="100%"></p>

1. **Verankern.** Neben jede Aussage schreibt der Agent, wo sie im Code steckt: `[[src/payments.py#validate_payment]]`, oder dasselbe in einem HTML-Kommentar, damit die Seite sauber bleibt.
2. **Versiegeln.** `dockeeper scan` berechnet den Fingerabdruck des Codes hinter jedem Anker, meist die ganze Funktion. Umformatieren spielt keine Rolle; geänderte Logik schon.
   <!-- dockeeper: dockeeper/bloques.py#bloque_en dockeeper/huellas.py#huella -->
3. **Prüfen.** `dockeeper check` gibt jeder Aussage ein Urteil: `OK`; `MOVED` (der Code ist verschoben, und `dockeeper fix` zieht nach, ohne dass jemand prüfen muss); oder `CHANGED` (der Code hat sich geändert, also liest ihn ein Mensch und passt den Text an). Jedes `CHANGED` führt zu Exit-Code 1, also schlägt die CI fehl.
   <!-- dockeeper: dockeeper/motor.py#verificar_codigo dockeeper/motor.py#FALLOS -->

<p align="center"><img src="../../site/public/assets/terminal-check.svg" alt="Echte Ausgabe von dockeeper check nach einer Codeänderung: eine Aussage CHANGED, eine MOVED" width="100%"></p>

<a id="install"></a>

## Installation

Du brauchst `python3` (3.10 oder neuer) und `git`. Klone das Repository in einen Ordner, der genau `dockeeper` heißt:

```bash
# Claude Code
git clone https://github.com/Nokky21/DocKeeper.git ~/.claude/skills/dockeeper

# Codex, Gemini CLI, Cursor, GitHub Copilot
git clone https://github.com/Nokky21/DocKeeper.git ~/.agents/skills/dockeeper
```

Andere Ordner, ein einzelnes Projekt, Windows, claude.ai und die API: siehe die [Installationsanleitung](../install.md).

## Benutzung

Bitte deinen Agenten in deinen eigenen Worten:

- *„Dokumentiere dieses Repository mit dockeeper.“* Auch Monorepos, ein Paket nach dem anderen.
- *„Prüfe, ob unsere Doku noch stimmt, und korrigiere, was nicht stimmt.“*
- *„Prüfe die Doku bei jedem Commit.“* Dafür installiert er einen Git-Hook, der nie einen Commit blockiert.
- *„Schreib die Seite mit den Entscheidungen aus der Git-Historie. Erfinde keine Gründe.“*
- *„Zeichne die Architektur mit Ablaufdiagrammen.“*

Oder führe es selbst im Wurzelverzeichnis deines Projekts aus:

```bash
DK="python3 $HOME/.claude/skills/dockeeper/bin/dockeeper"
$DK audit    # was fehlt: Seiten, Pakete, undokumentierter Code
$DK scan     # neue Anker versiegeln und zeigen, auf welchen Code jeder zeigt
$DK check    # stimmt es noch? Exit 0 = ja, 1 = etwas hat sich geändert
$DK fix      # verschobenem Code folgen (ändert nur die Siegeldatei)
$DK review   # was der letzte Commit für die Doku bedeutet
```

<!-- dockeeper: dockeeper/motor.py#arreglar -->

## Bei jedem Commit

`review` schaut sich den letzten Commit an (oder einen ganzen Branch, mit `--desde main`) und listet die Aussagen, die er berührt hat, den neuen oder geänderten Code, den noch keine Aussage abdeckt, und die Entscheidungen aus diesen Commits, die noch nirgends stehen. Als `post-commit`-Hook sieht, wer committet, du oder dein Agent, diese Liste jedes Mal, und die Doku wächst mit dem Code:
<!-- dockeeper: dockeeper/revision.py#revisar -->

```sh
#!/bin/sh
python3 "$HOME/.claude/skills/dockeeper/bin/dockeeper" review || true
```

## Diagramme, die stimmen bleiben

Der Agent zeichnet Abläufe, Sequenzen, Zustände und Daten in Mermaid, das GitHub und Obsidian gleich darstellen. Jedes Diagramm trägt seine Anker in sich, in unsichtbaren `%% dockeeper:`-Zeilen, sodass `check` es meldet, wenn sich der gezeigte Code ändert. Dieses hier ist echt:

```mermaid
flowchart LR
  A["Dein Agent schreibt eine Seite"] --> B["scan versiegelt jeden Anker"]
  %% dockeeper: dockeeper/motor.py#escanear
  B --> C{"check"}
  %% dockeeper: dockeeper/motor.py#comprobar
  C -- OK --> D["Die Doku bleibt wahr"]
  C -- CHANGED --> E["Text anpassen"]
  E --> B
  %% dockeeper: dockeeper/motor.py#arreglar
```

## Monorepos

`audit` findet jedes Paket (jeden Unterordner mit `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `pom.xml` usw.) und zeigt, welche keine Doku haben. Der Agent schreibt die Seiten im Wurzelverzeichnis mit einer Karte der Pakete und dokumentiert dann ein Paket nach dem anderen. So passt auch ein riesiges Repository. <!-- dockeeper: dockeeper/paquetes.py#detectar -->

## In der CI

```yaml
- uses: actions/checkout@v6
- uses: Nokky21/DocKeeper@v0.3.0
```

Jede andere CI braucht nur Python und git: [klonen und `check` ausführen](../reference.md#continuous-integration).

## Mehr erfahren

- [Installationsanleitung](../install.md): jeder Agent, ein einzelnes Projekt, Windows, claude.ai und die API.
- [Referenz](../reference.md): Anker, Befehle, Urteile, Teilbereiche, veröffentlichte Doku, das „Warum“, Konfiguration, Grenzen und FAQ.
- [Architektur](../architecture.md): wie DocKeeper innen funktioniert, in sechs verankerten Diagrammen.
- [SKILL.md](../../SKILL.md), die Anweisungen, denen dein Agent folgt, und die [Spezifikation](../../SPEC.md) (beide auf Spanisch).

## Lizenz

[MIT](../../LICENSE).

---

<sub>Übersetzung des [englischen README](../../README.md), das bei Abweichungen maßgeblich ist. Installationsanleitung, Referenz und Architektur sind auf Englisch.</sub>
