# Onboarding

For someone about to make their first change to DocKeeper itself. If you only want to use it, the
[README](../README.md) and the [install guide](install.md) are enough.

## First day

1. Clone the repository and run `python3 -m unittest` from its root. Nothing to install: the engine
   uses the standard library only.
   - Check: the last line says `OK`.
2. Read the code in this order:
   - **The entry.** `bin/dockeeper` puts the repository on the import path, so the CLI runs without
     installing anything, and hands over to `main`, which picks the command from a table.
     <!-- dockeeper: bin/dockeeper:7 dockeeper/cli.py#main dockeeper/cli.py#_ORDENES -->
   - **The context of a run.** Configuration, file listing, partial scope and seal, loaded once per
     command. <!-- dockeeper: dockeeper/motor.py#Contexto -->
   - **Reading a document.** Anchors are found outside code blocks, inline code and foreign HTML
     comments, plus `%% dockeeper:` lines inside Mermaid diagrams.
     <!-- dockeeper: dockeeper/markdown.py#analizar -->
   - **From a line to a block.** The heart of the engine: comments and strings are blanked, then
     definitions are found by patterns for each family of languages, and an anchor gets the innermost
     definition around it or a small window.
     <!-- dockeeper: dockeeper/bloques.py#limpiar dockeeper/bloques.py#Analisis dockeeper/bloques.py#bloque_en -->
   - **The fingerprint and the seal.** Normalized lines, a SHA-256 cut to 16 characters, stored with
     positions and never with code. <!-- dockeeper: dockeeper/huellas.py#huella dockeeper/sello.py#Sello -->
   - **The verdict.** Same fingerprint in the same place, somewhere else, or nowhere.
     <!-- dockeeper: dockeeper/motor.py#verificar_codigo -->
3. Run `python3 bin/dockeeper check` and `python3 bin/dockeeper audit` on this repository: it
   documents itself, so both show the engine at work on code you are now reading.

## Mental model

- **An anchor points at a block, not at a line.** A line inside a function stands for the whole
  function, so the claim notices a change anywhere in it. <!-- dockeeper: dockeeper/bloques.py#bloque_en -->
- **Formatting doesn't count, logic does.** Spaces are collapsed and blank lines dropped before
  hashing. <!-- dockeeper: dockeeper/huellas.py#normalizar_linea dockeeper/huellas.py#normalizar -->
- **The seal is the memory.** `scan`, `fix` and `link` write it; `check` only compares against it,
  which is why CI can run `check` and nothing else. <!-- dockeeper: dockeeper/sello.py#Entrada -->
- **No AI in the engine.** The skill (`SKILL.md`) is what an agent follows to write documentation;
  the CLI only seals and checks. Both are described in [the architecture](architecture.md).

## How work is done here

- **Languages.** Code, comments, `SPEC.md` and `SKILL.md` are in Spanish; the README, `docs/` and the
  website are in English, and the README also comes in 22 translations. CLI messages are written in
  Spanish in the code and translated from a table. <!-- dockeeper: dockeeper/textos.py#t -->
- **Python.** The target is 3.10 and newer, and the code also avoids what 3.9 lacks, so it runs on
  the Python that ships with macOS.
- **Tests and CI.** Every change runs the unit tests on Linux, macOS and Windows, plus the
  repository's own GitHub Action, which checks these docs.
  <!-- dockeeper: .github/workflows/ci.yml:19 .github/workflows/ci.yml:39 -->
- **The specification decides.** `SPEC.md` (Spanish) holds the acceptance criteria and every design
  decision; if code and specification disagree, one of them is wrong. The decisions recorded in the
  git history are on [the decisions page](decisions.md).
- **Releasing and the website:** see [the procedures](procedures.md).

## Known traps

- **Changing code that the docs talk about makes the self-check fail**, sometimes 23 times over,
  because the README and its translations share anchors. Read the sentence, then reseal: see
  [the procedures](procedures.md#when-you-change-code-that-the-docs-talk-about).
  <!-- dockeeper: tests/test_autocomprobacion.py#PruebasAutocomprobacion.test_el_repositorio_se_mantiene_limpio -->
- **Tests assert Spanish messages.** The suite pins a Spanish locale, so a test reads the Spanish
  text even if your terminal is in English. <!-- dockeeper: tests/__init__.py:5 -->
- **Every new message needs its English text**, or a test fails.
  <!-- dockeeper: tests/test_textos.py#PruebasTextos.test_cada_mensaje_tiene_version_en_ingles -->
- **The website sources are documents too.** DocKeeper reads the `.astro` files of `site/src/` as
  documentation, so they can carry anchors, and a literal `[[` or three backticks in them would be
  taken as an anchor or a code fence. The [website README](../site/README.md) has the
  details.
- **The templates are left out on purpose.** `templates/` carries example anchors, so the
  configuration of this repository excludes it from every command.

## Who to ask

Open an issue on [GitHub](https://github.com/Nokky21/DocKeeper/issues). Owners by area are not recorded.
