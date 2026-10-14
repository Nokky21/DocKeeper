<div align="center">

# DocKeeper

**Dokumentation som inte ruttnar.**

Din kodagent skriver dokumentationen. DocKeeper knyter varje påstående till koden bakom det och säger till så fort den koden ändras.

[![CI](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml/badge.svg)](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-2ea44f)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](../../LICENSE)

[Webbplats](https://nokky21.github.io/DocKeeper/) · [Live-demo](https://nokky21.github.io/DocKeeper/#demo) · [Installera](#install) · [Referens](../reference.md)

<sub>[English](../../README.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · **Svenska** · [Русский](README.ru.md) · [Українська](README.uk.md) · [Türkçe](README.tr.md) · [العربية](README.ar.md) · [עברית](README.he.md) · [हिन्दी](README.hi.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md) · [ไทย](README.th.md)</sub>

</div>

---

## Varför

En README som skrivs i dag är fel några månader senare, och ingen vet vilka sidor som ljuger. DocKeeper löser ”ingen vet”-delen, gratis och på din egen dator:

- **Varje påstående kontrolleras.** ”Betalningar valideras innan de dras” är knutet till funktionen som gör det. När den funktionen ändras säger DocKeeper till.
- **Ingen AI i kontrollen.** Din agent skriver; kontrollen jämför fingeravtryck och ger därför alltid samma svar.
- **Lokalt och gratis.** Inget konto, ingen server, inget nätverk, inga beroenden. MIT-licens.

## Så fungerar det

<p align="center"><img src="../../site/public/assets/how-it-works.svg" alt="Så fungerar DocKeeper: ett påstående förankras i ett kodblock, blocket får ett fingeravtryck och check rapporterar OK, MOVED eller CHANGED" width="100%"></p>

1. **Förankra.** Bredvid varje påstående skriver agenten var det finns i koden: `[[src/payments.py#validate_payment]]`, eller samma sak i en HTML-kommentar så att sidan förblir ren.
2. **Försegla.** `dockeeper scan` tar fingeravtrycket av koden bakom varje ankare, oftast hela funktionen. Omformatering spelar ingen roll; ändrad logik gör det.
   <!-- dockeeper: dockeeper/bloques.py#bloque_en dockeeper/huellas.py#huella -->
3. **Kontrollera.** `dockeeper check` ger varje påstående ett utlåtande: `OK`; `MOVED` (koden har flyttats och `dockeeper fix` följer efter utan att någon behöver granska); eller `CHANGED` (koden har ändrats, så en människa läser den och uppdaterar texten). Varje `CHANGED` ger slutkod 1, så CI fallerar.
   <!-- dockeeper: dockeeper/motor.py#verificar_codigo dockeeper/motor.py#FALLOS -->

<p align="center"><img src="../../site/public/assets/terminal-check.svg" alt="Verklig utdata från dockeeper check efter en kodändring: ett påstående CHANGED, ett MOVED" width="100%"></p>

<a id="install"></a>

## Installera

Du behöver `python3` (3.10 eller senare) och `git`. Klona repot till en mapp som heter exakt `dockeeper`:

```bash
# Claude Code
git clone https://github.com/Nokky21/DocKeeper.git ~/.claude/skills/dockeeper

# Codex, Gemini CLI, Cursor, GitHub Copilot
git clone https://github.com/Nokky21/DocKeeper.git ~/.agents/skills/dockeeper
```

Andra mappar, ett enskilt projekt, Windows, claude.ai och API:t: se [installationsguiden](../install.md).

## Användning

Be din agent med egna ord:

- *”Dokumentera det här repot med dockeeper.”* Även monorepon, ett paket i taget.
- *”Kontrollera om vår dokumentation fortfarande stämmer och rätta det som inte gör det.”*
- *”Granska dokumentationen vid varje commit.”* Den installerar en git-hook som aldrig blockerar en commit.
- *”Skriv beslutssidan utifrån git-historiken. Hitta inte på skäl.”*

Eller kör det själv från projektets rotmapp:

```bash
DK="python3 $HOME/.claude/skills/dockeeper/bin/dockeeper"
$DK audit    # vad som saknas: sidor, paket, odokumenterad kod
$DK scan     # förseglar nya ankare och visar vilken kod varje ankare pekar på
$DK check    # stämmer det fortfarande? slutkod 0 = ja, 1 = något har ändrats
$DK fix      # följer kod som flyttats (rör bara sigillfilen)
$DK review   # vad den senaste committen betyder för dokumentationen
```

<!-- dockeeper: dockeeper/motor.py#arreglar -->

## Vid varje commit

`review` tittar på den senaste committen (eller en hel gren, med `--desde main`) och listar påståendena den berörde, ny eller ändrad kod som inget påstående täcker än, och besluten i de committarna som inte står skrivna någonstans. Som `post-commit`-hook ser den som committar, du eller din agent, listan varje gång, och dokumentationen växer med koden:
<!-- dockeeper: dockeeper/revision.py#revisar -->

```sh
#!/bin/sh
python3 "$HOME/.claude/skills/dockeeper/bin/dockeeper" review || true
```

## Monorepon

`audit` hittar varje paket (varje undermapp med `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `pom.xml` och så vidare) och visar vilka som saknar dokumentation. Agenten skriver rotens sidor med en karta över paketen och dokumenterar sedan ett paket i taget, så även ett enormt repo får plats. <!-- dockeeper: dockeeper/paquetes.py#detectar -->

## I CI

```yaml
- uses: actions/checkout@v6
- uses: Nokky21/DocKeeper@v0.2.0
```

All annan CI behöver bara Python och git: [klona det och kör `check`](../reference.md#continuous-integration).

## Läs mer

- [Installationsguide](../install.md): varje agent, ett enskilt projekt, Windows, claude.ai och API:t.
- [Referens](../reference.md): ankare, kommandon, utlåtanden, delomfång, publicerad dokumentation, ”varför”, konfiguration, begränsningar och vanliga frågor.
- [SKILL.md](../../SKILL.md), instruktionerna din agent följer, och [specifikationen](../../SPEC.md) (båda på spanska).

## Licens

[MIT](../../LICENSE).

---

<sub>Översättning av [README på engelska](../../README.md), som gäller vid skillnader. Installationsguiden och referensen är på engelska.</sub>
