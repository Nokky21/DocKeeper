# DocKeeper architecture

[← README](../README.md) · [Reference](reference.md) · [Install](install.md)

> [!NOTE]
> This page was written with the DocKeeper skill, the same way it documents your repository. Every
> claim and every diagram is anchored to the code it describes, and CI fails the moment one of them
> stops being true. The diagrams are Mermaid, so they render the same on GitHub and in Obsidian.

DocKeeper has two halves. The **skill** (`SKILL.md` and `templates/`) tells your agent how to write
documentation and diagrams that point at the code. The **CLI** (`dockeeper/`, Python standard library
only) seals what those pointers cover and later says whether it is still true. Nothing here calls a
model or the network.

## Components

```mermaid
flowchart LR
  CLI["cli.py<br/>commands and output"] --> MOT["motor.py<br/>scan · check · fix · link"]
  %% dockeeper: dockeeper/cli.py#main dockeeper/motor.py#comprobar
  MOT --> MD["markdown.py<br/>anchors in documents"]
  %% dockeeper: dockeeper/markdown.py#analizar
  MOT --> BLK["bloques.py<br/>the block behind an anchor"]
  %% dockeeper: dockeeper/bloques.py#bloque_en
  BLK --> HU["huellas.py<br/>normalized fingerprints"]
  %% dockeeper: dockeeper/huellas.py#huella
  MOT --> SEAL[(".dockeeper.sello.json")]
  %% dockeeper: dockeeper/sello.py#Sello
  MOT --> PUB["publicado.py<br/>published-doc rules"]
  %% dockeeper: dockeeper/publicado.py#revisar
  CLI --> REV["revision.py<br/>review"]
  %% dockeeper: dockeeper/revision.py#revisar
  CLI --> AUD["auditoria.py<br/>audit"]
  AUD --> PKG["paquetes.py<br/>packages"]
  %% dockeeper: dockeeper/auditoria.py#auditar dockeeper/paquetes.py#detectar
  CLI --> WHY["porque.py<br/>why"]
  %% dockeeper: dockeeper/porque.py#historial
```

- **The CLI** parses the command and prints the result, as text or as `--json`.
- **The engine** (`motor.py`) seals anchors, checks them and relocates the ones that moved. It is the
  only part that writes, and it only writes the seal file.
  <!-- dockeeper: dockeeper/motor.py#escanear dockeeper/motor.py#arreglar dockeeper/sello.py#Sello -->
- **Blocks and fingerprints.** An anchor stands for a whole definition, found with per-language
  patterns rather than a parser, and its lines are normalized before hashing so reformatting doesn't
  count as a change. <!-- dockeeper: dockeeper/bloques.py#bloque_en dockeeper/huellas.py#normalizar_linea -->

## How a claim is checked

```mermaid
flowchart TD
  A["Sealed anchor"] --> X{"Does the file<br/>still exist?"}
  X -- no --> GONE["DESAPARECIDO"]
  X -- yes --> B["Recompute the block<br/>at the saved position"]
  B --> F{"Same fingerprint?"}
  F -- "yes, same place" --> OK["OK"]
  F -- "yes, elsewhere" --> MV["MOVED"]
  F -- no --> S{"Fingerprint found<br/>elsewhere in the file?"}
  S -- yes --> MV
  S -- no --> CH["CHANGED"]
  %% dockeeper: dockeeper/motor.py#verificar_codigo dockeeper/huellas.py#buscar
```

`MOVED` never needs a person: `fix` updates the seal. `CHANGED` always does, because only a person can
say whether the sentence is still true. Any `CHANGED` makes `check` exit with 1.
<!-- dockeeper: dockeeper/motor.py#FALLOS -->

## The commit loop

```mermaid
sequenceDiagram
  participant Dev as You or your agent
  participant Git
  participant Hook as post-commit hook
  participant DK as dockeeper review
  Dev->>Git: git commit
  Git->>Hook: runs after every commit
  Hook->>DK: review (never blocks)
  %% dockeeper: dockeeper/revision.py#revisar
  DK->>Git: diff from HEAD~1 to the working tree
  %% dockeeper: dockeeper/revision.py#_base dockeeper/revision.py#_cambios
  DK-->>Dev: claims touched, new code with no claim, decisions not written down
  Dev->>Dev: update the docs, then dockeeper scan
```

A new class is reported as the class, not as each of its methods, and a definition already covered
by any claim is not reported again. <!-- dockeeper: dockeeper/revision.py#_tocadas dockeeper/revision.py#_tramos -->

## Life of an anchor

```mermaid
stateDiagram-v2
  [*] --> Unsealed: written in a document
  Unsealed --> Sealed: scan
  Sealed --> Moved: the code moved
  Moved --> Sealed: fix
  Sealed --> Changed: the code changed
  Changed --> Sealed: text reviewed, fix --aceptar
  Sealed --> Orphan: removed from the document
  Orphan --> [*]: scan or fix
  %% dockeeper: dockeeper/motor.py#escanear dockeeper/motor.py#arreglar
```

## The seal file

```mermaid
erDiagram
  SEAL ||--o{ ANCHOR : anclas
  SEAL ||--o{ LINK : vinculos
  ANCHOR {
    string doc
    string ancla
    string fichero
    int inicio
    int fin
    string huella
  }
  LINK {
    string doc
    int linea_doc
    string huella_doc
    string fichero
    string huella
  }
  %% dockeeper: dockeeper/sello.py#Entrada dockeeper/sello.py#Sello
```

It stores positions and fingerprints, never code, as sorted JSON so its diffs are readable. A link
also keeps the fingerprint of the sentence it belongs to, which is how published pages are checked
without showing any path. <!-- dockeeper: dockeeper/sello.py#Entrada dockeeper/motor.py#vincular -->

## Decisions

From `dockeeper why`, which only reads what the git history says:

```mermaid
timeline
  title Decisions recorded in the git history
  v0.2 · 2026-10-14 : The post-commit hook is installed by the agent, never by the CLI
                    : A package is any subfolder with a known manifest
                    : Messages in English by default, in Spanish when the environment asks
  v0.3 · 2026-10-14 : Diagrams are anchored inside their own block
  v0.4 · 2026-10-14 : Dependencies committed to git are not your code for audit
  %% dockeeper: dockeeper/revision.py#revisar dockeeper/paquetes.py#detectar dockeeper/textos.py#espanol dockeeper/markdown.py#_fichas
  %% dockeeper: dockeeper/paquetes.py#ajena
```

> [!TIP]
> The reasons are in the commit messages (`Decision:` and `Why:` lines). Run `dockeeper why` to see
> them, and the [specification](../SPEC.md) (Spanish) for every decision taken so far.
