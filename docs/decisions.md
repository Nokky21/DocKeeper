# Decisions

Why DocKeeper is built the way it is, taken from the git history with `dockeeper why`. A reason
appears here only if the commit records one; nothing is guessed. The full list of design decisions,
with their reasons, is in section 7 of the [specification](../SPEC.md) (Spanish).

Most recent first.

## D-005 · `audit` skips dependencies committed to git

- **Date:** 2026-10-14
- **Decision:** `audit` does not count anything under `node_modules/`, `vendor/` and similar folders
  as your own code or documentation, unless that folder is the root of one of your packages.
- **Reason:** it is someone else's code: analysing it took 16 seconds on a real repository and filled
  the inventory with false gaps.
- **Alternatives considered:** not recorded.
- **Consequences:** `check`, `scan` and `review` still read those folders; leave them out with `sin`
  in `.dockeeper.json`. A package of your own that happens to be called `vendor` (say
  `packages/vendor/`) still counts.
- **Source:** commit `91e67a1`.
  <!-- dockeeper: dockeeper/paquetes.py#ajena dockeeper/auditoria.py#auditar -->

## D-004 · Diagrams carry their anchors inside the block

- **Date:** 2026-10-14
- **Decision:** a Mermaid diagram is anchored inside its own block, on `%% dockeeper:` lines.
- **Reason:** `%%` is a Mermaid comment, so nobody sees it, and it keeps each anchor next to the
  nodes it backs.
- **Alternatives considered:** not recorded.
- **Consequences:** it is the only exception to "code blocks hold no anchors". A `markdown` or `text`
  block that teaches the syntax still creates none.
- **Source:** commit `f7cff84`.
  <!-- dockeeper: dockeeper/markdown.py#analizar -->

## D-003 · English by default, Spanish when the environment asks

- **Date:** 2026-10-14
- **Decision:** messages are in English unless `LC_ALL`, `LC_MESSAGES` or `LANG` starts with `es`.
- **Reason:** so it works for anyone without configuring anything, without losing Spanish.
- **Alternatives considered:** not recorded.
- **Consequences:** the code writes each message in Spanish, which is also its key, and the English
  text comes from a table. Verdict codes and `--json` keys never change with the language. The test
  suite pins Spanish, so tests assert the Spanish wording.
- **Source:** commit `f5295e0`.
  <!-- dockeeper: dockeeper/textos.py#espanol dockeeper/textos.py#t tests/__init__.py:5 -->

## D-002 · A package is any subfolder with a known manifest

- **Date:** 2026-10-14
- **Decision:** a package is a subfolder holding a manifest DocKeeper knows (`package.json`, `go.mod`,
  `Cargo.toml`, `pyproject.toml`, `pom.xml` and so on).
- **Reason:** it works the same for any monorepo tool without interpreting its workspaces.
- **Alternatives considered:** not recorded.
- **Consequences:** the root is never a package, manifests inside dependency folders don't count, and
  a file belongs to the deepest package that contains it.
- **Source:** commit `b18c665`.
  <!-- dockeeper: dockeeper/paquetes.py#detectar dockeeper/paquetes.py#paquete_de -->

## D-001 · The post-commit hook is installed by the agent, never by the CLI

- **Date:** 2026-10-14
- **Decision:** the git hook that runs `dockeeper review` after each commit is written by the agent,
  when the person asks for it. The CLI never writes hooks.
- **Reason:** the CLI only writes its seal file (specification §3).
- **Alternatives considered:** not recorded.
- **Consequences:** `review` only informs and always exits with 0; the gate in CI is `check`.
- **Source:** commit `4d82dfb`.
  <!-- dockeeper: dockeeper/revision.py#revisar -->
