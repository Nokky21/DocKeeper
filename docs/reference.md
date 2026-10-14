# DocKeeper reference

[← README](../README.md) · [Install](install.md) · [Architecture](architecture.md)

## Anchors

| Form | Syntax | Use it for |
|---|---|---|
| By symbol (**preferred**) | `[[src/pay.ts#validatePayment]]` | functions, classes, methods, constants |
| Symbol inside a container | `[[src/pay.ts#Payments.validate]]` | methods with the same name in different classes |
| By line | `[[src/pay.ts:147]]` | things that are not definitions (config, a single line) |
| Hidden | `<!-- dockeeper: src/pay.ts:147 src/pay.ts#validatePayment -->` | keep the rendered text clean |
| Linked, outside the text | `dockeeper link guide.md:12 src/pay.ts#validatePayment` | published docs whose code is private |
| Inside a diagram | a `%% dockeeper: src/pay.ts#validatePayment` line in a `mermaid` block | diagrams that must stay true |

Anchors inside code blocks and inline code are ignored, so docs can teach the syntax safely. The one
exception is a `%% dockeeper:` line inside a `mermaid` block: `%%` is a Mermaid comment, so Obsidian
and GitHub don't show it, and it keeps each anchor next to the nodes it describes. `audit` counts the
diagrams that have no anchors. <!-- dockeeper: dockeeper/markdown.py#analizar dockeeper/markdown.py#_fichas -->

Paths are relative to the repository root. Prefer symbols: a line number written in a document ages
when code moves. The seal file always knows the real position, but readers see the old number, and
`fix` never rewrites your documents. <!-- dockeeper: dockeeper/motor.py#arreglar -->

Definitions are recognized for Python, JavaScript/TypeScript, Go, Rust, Java, Kotlin, Scala, C#,
C/C++, Swift, PHP, Dart, Ruby, Elixir, Lua, Julia and shell. Any other text file still works with
line anchors (window blocks).

## Commands

| Command | What it does | Writes |
|---|---|---|
| `audit` | Inventory: missing base pages, docs without anchors, [packages](#monorepos-and-whole-repositories), coverage per folder, biggest undocumented definitions | nothing |
| `scan` | Seals new anchors and shows the block each one landed on; prunes anchors removed from docs. `--resellar` re-seals everything after a review | seal file |
| `check` | Verifies anchors, links and published-doc rules | nothing |
| `fix` | Relocates `MOVED`, removes orphans. `--aceptar` accepts reviewed `CHANGED` blocks as the new truth | seal file |
| `link DOC:LINE ANCHOR` | Binds a line of a document to code without touching the document. `--quitar` removes it | seal file |
| `why` | Decisions from git history (`Decision:`, `Motivo:`/`Why:`, `Alternativas:`, `ADR`) and decision entries with no written reason | nothing |
| `review` | [What a change means for the docs](#reviewing-every-change): claims it touched, new or changed code with no claim, decisions not yet written down. `--desde REF` (default `HEAD~1`) | nothing |

Every command accepts `--json` (stable, machine-readable) and `--raiz PATH` (repository root;
defaults to the nearest folder with `.dockeeper.json` or `.git`). Every command except `link` accepts
`--solo` and `--sin` ([partial scope](#partial-scope)).

## Verdicts and exit codes

| Code | Meaning | Exit | What to do |
|---|---|---|---|
| `OK` | Same block, same place | 0 | nothing |
| `MOVED` | Same block, somewhere else | 0 | `fix` relocates it |
| `CHANGED` | The block's content changed, or its symbol is gone | **1** | read the code, correct the text, then `fix --aceptar` |
| `DESAPARECIDO` | The anchored file no longer exists | **1** | rewrite or remove the claim, then `scan` |
| `SIN_SELLAR` | Anchor written but never sealed | **1** | `scan` |
| `HUERFANA` | Sealed anchor no longer in the document | 0 | `fix` (or `scan`) removes it |
| `ANCLA_MAL_ESCRITA` | Malformed anchor or a path outside the repository | **1** | fix the anchor |
| `ANCLA_INTERNA` | Anchor inside a `publico` document | **1** | use `link` instead |
| `RUTA_INTERNA` | A `publico` document mentions an internal path | **1** | remove the path |
| `CODIGO_COPIADO` | A published document copies code from the repository | **1** | describe it or write your own example |
| `VINCULO_SUELTO` | The sentence a link pointed to was rewritten | **1** | review it, then `link` again or `link --quitar` |
| `NADA_COMPROBADO` | Nothing to check in this scope | **1** | there is no "empty green" |

`scan` can also report `NO_EXISTE`, `SIN_SIMBOLO`, `FUERA_DE_RANGO` or `SIN_CONTENIDO` while sealing
(file, symbol or line not found), exit code 1. Exit code **2** always means a usage or
configuration error. <!-- dockeeper: dockeeper/motor.py#FALLOS dockeeper/motor.py#comprobar dockeeper/cli.py#main -->

## Reviewing every change

`review` compares a base with your working tree and answers three questions: which claims did this
change touch, which new or changed definitions have no claim at all, and which decisions in these
commits are not written down yet. It never fails (exit 0): `check` is still the gate.

- No options: the last commit plus anything not committed yet. That is what a `post-commit` hook
  sees.
- `--desde main`: the whole branch, counted from where it forked from `main`. Use it before opening a
  pull request.
- Only files git knows about count: untracked files join once you `git add` them.
- A new class is reported as the class, not as each of its methods; a new method in an existing
  class is reported as `Class.method`.

<!-- dockeeper: dockeeper/revision.py#revisar dockeeper/revision.py#_tocadas -->

The hook is in [Continuous integration](#continuous-integration). Your agent can install it: ask it
to "review the docs on every commit".

## Monorepos and whole repositories

`audit` lists the **packages** of a repository: every subfolder with a manifest (`package.json`,
`deno.json`, `pyproject.toml`, `setup.py`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`,
`composer.json`, `Gemfile`, `mix.exs`, `Package.swift`, `pubspec.yaml`, `*.csproj`…). For each one it
shows the name declared in the manifest, its README if it has one and how many of its definitions
have a claim. The root is the repository, not a package, and copied dependencies (`node_modules`,
`vendor`, `third_party`…) are ignored. A file belongs to the deepest package that contains it.
<!-- dockeeper: dockeeper/paquetes.py#detectar dockeeper/paquetes.py#paquete_de -->

When you ask your agent to document the whole repository, the skill works in parts: inventory, a plan
you can read, the root pages (with a map of the packages), then one package at a time with
`--solo <folder>`, and a final `check` over everything. That keeps a huge monorepo within what an
agent can read at once.

## Partial scope

- `--solo PATH` (repeatable). If the path points only at documents, it narrows the **documents**; if
  it points at code, it narrows the **code**. `--solo src/payments` checks that part against every
  document that talks about it; `--solo docs/api.md` checks that document without losing the code it
  points to.
- `--sin PATTERN` (repeatable, globs or folder prefixes) excludes documents and code. The `sin` key
  in `.dockeeper.json` excludes permanently.
- No `--solo` means no restriction; no `--sin` means nothing excluded. A `--solo` that matches
  nothing is an error. <!-- dockeeper: dockeeper/alcance.py#Alcance -->

## Published documentation

Documentation that leaves the repository is the hard case: it can't carry internal paths or copied
code, and it still has to be checkable. Declare it in `.dockeeper.json`:

```json
{
  "publico": ["docs/public/"],
  "publicado": ["README.md"]
}
```

- **`publico`**: published, and the code is **private**. No anchors, no internal paths, no copied
  code. Bind each claim with `dockeeper link`. The link is stored in the seal file, so readers never
  see a path, while `check` verifies both the code and that the sentence is still there.
- **`publicado`**: published, and the code is **public** (like the README of DocKeeper itself). Anchors are allowed
  (hidden ones are best); copying code is not.

<p align="center"><img src="../site/public/assets/published-docs.svg" alt="Published docs: the public page shows no paths; the link lives in the seal file and check verifies both the sentence and the private code" width="100%"></p>

Copied code means a code block in the document with `bloque_minimo` (default 3) or more consecutive
lines identical, spacing aside, to a file in the repository. The report names the source file.
<!-- dockeeper: dockeeper/publicado.py#IndiceCopias dockeeper/publicado.py#rutas_en_texto -->

## The "why"

`why` reads the git history looking for decision markers and checks your decision documents for
entries with no written reason. What is not in the history is never invented: the agent writes
"not documented". Mark decisions in commit messages like this:

```text
feat(seal): keep the seal outside the documents

Decision: the seal lives in its own file
Why: published pages must not show internal paths
Alternatives: HTML comments (they still leak in the page source)
```

<!-- dockeeper: dockeeper/porque.py#historial dockeeper/porque.py#entradas_sin_motivo -->

## Continuous integration

**GitHub Actions.** The repository is also an action:

```yaml
name: docs
on: [push, pull_request]
jobs:
  dockeeper:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: Nokky21/DocKeeper@v0.2.0
        # with:
        #   args: --sin vendor/
```

Inputs: `args` (extra arguments for `check`) and `working-directory` (repository root, default `.`).

**Any other CI.** Only Python and git are needed:

```bash
git clone --depth 1 https://github.com/Nokky21/DocKeeper.git /tmp/dockeeper
python3 /tmp/dockeeper/bin/dockeeper check
```

**Git hooks.** To review every commit (it never blocks), save this as `.git/hooks/post-commit` and
make it executable. Your agent can install it for you: ask it to "review the docs on every commit".

```sh
#!/bin/sh
python3 "$HOME/.claude/skills/dockeeper/bin/dockeeper" review || true
```

<!-- dockeeper: dockeeper/revision.py#revisar -->

To catch it before pushing, save this as `.git/hooks/pre-push`:

```sh
#!/bin/sh
exec python3 "$HOME/.claude/skills/dockeeper/bin/dockeeper" check
```

## Configuration

`.dockeeper.json` at the repository root. Every key is optional; unknown keys are an error, so a
typo can't silently disable a rule. <!-- dockeeper: dockeeper/config.py#cargar -->

| Key | Default | Meaning |
|---|---|---|
| `documentos` | `["*.md", "*.markdown", "*.mdx"]` | which files are documents (everything else is code) |
| `sin` | `[]` | always excluded |
| `publico` | `[]` | published docs whose code is private |
| `publicado` | `[]` | published docs whose code is public |
| `decisiones` | `["*decision*", "*adr*"]` | decision documents for `why` (case-insensitive) |
| `bloque_minimo` | `3` | consecutive lines that count as copied code |
| `ventana` | `3` | window radius when a line is not inside any definition |

## Files and paths

What DocKeeper reads and writes in **your** repository:

| Path | Written by | Commit it? |
|---|---|---|
| your documents (`*.md` by default) | you or your agent; DocKeeper never rewrites them | yes |
| `.dockeeper.json` | you (optional) | yes |
| `.dockeeper.sello.json` | `scan`, `fix`, `link` | yes: CI checks against it |

Everything is relative to the repository root, found by walking up from the current folder to the
first one with `.dockeeper.json` or `.git` (or given with `--raiz`). DocKeeper never writes outside
that root, and with git it respects `.gitignore`. <!-- dockeeper: dockeeper/config.py#buscar_raiz dockeeper/repo.py#Repo -->

## Limits

DocKeeper is honest about what it can't do:

- It compares content, not meaning: a block rewritten with the same behavior is `CHANGED`.
- It does not detect non-contiguous copies, and lets one- or two-line copies through on purpose.
- Definitions are found with patterns, not a parser. Rare constructs (C++ out-of-class methods,
  multi-line decorators) fall back to the enclosing definition or a window; `scan` shows every block
  so you can confirm it.
- It checks that documentation is still **true**, not that it is **useful**.

## FAQ

**Does my code leave my machine?** No. DocKeeper makes no network calls, and the seal file stores
hashes and positions, never code.

**Does it need an AI model?** No. The agent writes the documentation; DocKeeper's verification is
deterministic and runs without any model.

**I renamed a function. What happens?** Its symbol anchors report `CHANGED` ("symbol not found").
Update the anchor in the document, then run `scan`.

**Is the CLI in English?** Yes, by default. If your environment is in Spanish (`LC_ALL`, `LC_MESSAGES`
or `LANG` starting with `es`), messages are in Spanish. Verdict codes and the `--json` structure (keys
and codes) are the same in both languages, so scripts and agents are not affected; only the
human-readable texts, such as `detalle`, follow the language.
<!-- dockeeper: dockeeper/textos.py#espanol -->

## Repository layout and development

```text
bin/dockeeper            CLI launcher (no install needed)
dockeeper/               the engine (Python standard library only)
  cli.py                 commands and output
  motor.py               scan, check, fix, link
  markdown.py            reading anchors from documents
  bloques.py             definitions and the block behind each anchor
  huellas.py             normalization and fingerprints
  sello.py               the seal file
  alcance.py             --solo / --sin
  publicado.py           published-doc rules (copied code, internal paths)
  porque.py              the "why" from git history
  auditoria.py           audit
  paquetes.py            packages of a monorepo
  revision.py            review
  config.py, repo.py, rutas.py   configuration, file access, path patterns
templates/               page templates the skill writes from
SKILL.md                 instructions for agents
docs/                    install guide, this reference, README translations (i18n/)
action.yml               GitHub Action
site/                    website (Astro)
  src/demo/              live demo: a TypeScript port of the check + shared scenarios
tests/                   test suite
.github/workflows/       CI, website deploy, release
SPEC.md                  specification and acceptance criteria (Spanish)
```

```bash
python3 -m unittest              # the whole suite, including the self-check of this repository
cd site && yarn install && yarn dev   # the website, at http://localhost:4321/DocKeeper/
cd site && yarn test             # the live demo gives the same verdicts as the Python engine
```

The suite covers every acceptance criterion in [SPEC.md](../SPEC.md) and includes a self-check: the
README, its translations and these pages are sealed, and CI fails if they stop being true. CI runs the tests on Linux, macOS and Windows
with Python 3.10 to 3.14, and the website is built with Astro and deployed to GitHub Pages. The live
demo runs a TypeScript port of the check; `tests/test_demo.py` (real engine) and `site/scripts/check-demo.ts`
(port) run the same scenarios from `site/src/demo/scenarios.json`, so the demo can't drift from the CLI.
