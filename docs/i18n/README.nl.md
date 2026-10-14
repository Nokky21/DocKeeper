<div align="center">

# DocKeeper

**Documentatie die niet verrot.**

Je codeeragent schrijft de documentatie. DocKeeper koppelt elke bewering aan de code erachter en waarschuwt je zodra die code verandert.

[![CI](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml/badge.svg)](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-2ea44f)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](../../LICENSE)

[Website](https://nokky21.github.io/DocKeeper/) · [Live demo](https://nokky21.github.io/DocKeeper/#demo) · [Installeren](#install) · [Referentie](../reference.md)

<sub>[English](../../README.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · **Nederlands** · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [Türkçe](README.tr.md) · [العربية](README.ar.md) · [עברית](README.he.md) · [हिन्दी](README.hi.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md) · [ไทย](README.th.md)</sub>

</div>

---

## Waarom

Een README die je vandaag schrijft, klopt een paar maanden later niet meer, en niemand weet welke pagina’s liegen. DocKeeper lost het ‘niemand weet’-deel op, gratis en op je eigen machine:

- **Elke bewering wordt gecontroleerd.** ‘Betalingen worden gevalideerd voordat ze worden afgeschreven’ is gekoppeld aan de functie die dat doet. Verandert die functie, dan zegt DocKeeper het je.
- **Geen AI in de controle.** Je agent schrijft; de controle vergelijkt vingerafdrukken en geeft dus altijd hetzelfde antwoord.
- **Lokaal en gratis.** Geen account, geen server, geen netwerk, geen afhankelijkheden. MIT-licentie.

## Hoe het werkt

<p align="center"><img src="../../site/public/assets/how-it-works.svg" alt="Hoe DocKeeper werkt: een bewering wordt verankerd aan een codeblok, het blok krijgt een vingerafdruk en check meldt OK, MOVED of CHANGED" width="100%"></p>

1. **Verankeren.** Naast elke bewering schrijft de agent waar die in de code staat: `[[src/payments.py#validate_payment]]`, of hetzelfde in een HTML-commentaar zodat de pagina schoon blijft.
2. **Verzegelen.** `dockeeper scan` berekent de vingerafdruk van de code achter elk anker, meestal de hele functie. Herformatteren maakt niet uit; de logica veranderen wel.
   <!-- dockeeper: dockeeper/bloques.py#bloque_en dockeeper/huellas.py#huella -->
3. **Controleren.** `dockeeper check` geeft elke bewering een oordeel: `OK`; `MOVED` (de code is verplaatst en `dockeeper fix` volgt hem zonder dat iemand hoeft te controleren); of `CHANGED` (de code is veranderd, dus een mens leest hem en werkt de tekst bij). Elke `CHANGED` geeft exitcode 1, dus de CI faalt.
   <!-- dockeeper: dockeeper/motor.py#verificar_codigo dockeeper/motor.py#FALLOS -->

<p align="center"><img src="../../site/public/assets/terminal-check.svg" alt="Echte uitvoer van dockeeper check na het aanpassen van de code: één bewering CHANGED, één MOVED" width="100%"></p>

<a id="install"></a>

## Installeren

Je hebt `python3` (3.10 of nieuwer) en `git` nodig. Kloon de repository in een map die precies `dockeeper` heet:

```bash
# Claude Code
git clone https://github.com/Nokky21/DocKeeper.git ~/.claude/skills/dockeeper

# Codex, Gemini CLI, Cursor, GitHub Copilot
git clone https://github.com/Nokky21/DocKeeper.git ~/.agents/skills/dockeeper
```

Andere mappen, één project, Windows, claude.ai en de API: zie de [installatiegids](../install.md).

## Gebruik

Vraag het je agent in je eigen woorden:

- *‘Documenteer deze repository met dockeeper.’* Ook monorepo’s, één pakket per keer.
- *‘Controleer of onze documentatie nog klopt en verbeter wat niet klopt.’*
- *‘Controleer de documentatie bij elke commit.’* Hij installeert een git-hook die nooit een commit blokkeert.
- *‘Schrijf de beslissingenpagina op basis van de git-geschiedenis. Verzin geen redenen.’*

Of voer het zelf uit vanuit de hoofdmap van je project:

```bash
DK="python3 $HOME/.claude/skills/dockeeper/bin/dockeeper"
$DK audit    # wat ontbreekt: pagina’s, pakketten, ongedocumenteerde code
$DK scan     # verzegelt nieuwe ankers en toont naar welke code elk anker wijst
$DK check    # klopt het nog? exit 0 = ja, 1 = er is iets veranderd
$DK fix      # volgt verplaatste code (raakt alleen het zegelbestand aan)
$DK review   # wat de laatste commit betekent voor de documentatie
```

<!-- dockeeper: dockeeper/motor.py#arreglar -->

## Bij elke commit

`review` bekijkt de laatste commit (of een hele branch, met `--desde main`) en somt de beweringen op die geraakt zijn, de nieuwe of gewijzigde code die nog door geen enkele bewering gedekt wordt, en de beslissingen uit die commits die nog nergens staan. Als `post-commit`-hook ziet wie er commit, jij of je agent, die lijst elke keer, en groeit de documentatie mee met de code:
<!-- dockeeper: dockeeper/revision.py#revisar -->

```sh
#!/bin/sh
python3 "$HOME/.claude/skills/dockeeper/bin/dockeeper" review || true
```

## Monorepo’s

`audit` vindt elk pakket (elke submap met een `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `pom.xml` enzovoort) en laat zien welke geen documentatie hebben. De agent schrijft de pagina’s in de hoofdmap met een kaart van de pakketten en documenteert daarna één pakket per keer, zodat zelfs een enorme repository past. <!-- dockeeper: dockeeper/paquetes.py#detectar -->

## In CI

```yaml
- uses: actions/checkout@v6
- uses: Nokky21/DocKeeper@v0.1.0
```

Elke andere CI heeft alleen Python en git nodig: [kloon het en voer `check` uit](../reference.md#continuous-integration).

## Meer weten

- [Installatiegids](../install.md): elke agent, één project, Windows, claude.ai en de API.
- [Referentie](../reference.md): ankers, commando’s, oordelen, gedeeltelijke scope, gepubliceerde documentatie, het ‘waarom’, configuratie, grenzen en FAQ.
- [SKILL.md](../../SKILL.md), de instructies die je agent volgt, en de [specificatie](../../SPEC.md) (beide in het Spaans).

## Licentie

[MIT](../../LICENSE).

---

<sub>Vertaling van de [Engelse README](../../README.md), die bij verschillen leidend is. De installatiegids en de referentie zijn in het Engels.</sub>
