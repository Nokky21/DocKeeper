# API: the `--json` contract

For agents, scripts and CI steps that read DocKeeper's output instead of a person. The commands and
their options are in the [reference](reference.md); this page is the shape of what they return.

## Conventions

- **One JSON object on standard output**, indented, UTF-8, for every command run with `--json`.
  <!-- dockeeper: dockeeper/cli.py#_emitir -->
- **Keys and codes are stable and never translated.** They are Spanish words (`orden`, `codigo`,
  `items`, `estado`…) whatever the language of the environment. Only the texts meant for people
  (`detalle`, `avisos`, `error`) follow the language. The `accion` values of `fix` are codes too.
  <!-- dockeeper: tests/test_textos.py#PruebasTextos.test_codigos_y_claves_del_json_no_cambian -->
- **Every object has `orden`** (the command) **and `codigo`**, the same number as the exit code: `0`
  when everything is true or only moved, `1` when something changed or broke, `2` for a usage or
  configuration error. <!-- dockeeper: dockeeper/motor.py#FALLOS dockeeper/motor.py#Resultado -->
- **Errors** (exit `2`) come as `{"orden", "error", "codigo": 2}` and nothing else.
  <!-- dockeeper: dockeeper/cli.py#main -->

### An item

`check`, `scan`, `fix` and `link` return a list of `items`. Each one always has `estado` (a verdict
code, see the [reference](reference.md#verdicts-and-exit-codes)) and `tipo` (`ancla`, `vinculo`,
`documento` or `repo`). The other keys only appear when they have a value:

| Key | What it holds |
|---|---|
| `doc`, `linea_doc` | the document and its line |
| `ancla` | the anchor as written, for example `src/payments.py#validate_payment` |
| `detalle` | one sentence for a person, in the environment's language |
| `bloque` | where the anchor landed: `fichero`, `tipo`, `inicio`, `fin`, the `primera` and `ultima` lines, and `nombre` for a definition |
| `avisos` | warnings for a person |
| `fuente` | for copied code, the repository file it was copied from |
| `accion` | only in `fix`: `recolocada`, `aceptada` or `quitada del sello` |

<!-- dockeeper: dockeeper/motor.py#Item dockeeper/motor.py#vista -->

## Operations

### `check`

Is every claim still true? Reads, never writes. <!-- dockeeper: dockeeper/cli.py#_check -->

- **Output:** `orden`, `raiz`, `alcance` (`solo_documentos`, `solo_codigo`, `sin`), `codigo`,
  `examinados` (how many claims were checked), `fuera_de_alcance`, `resumen` (count per verdict) and
  `items`. <!-- dockeeper: dockeeper/cli.py#_json_resultado -->
- **Errors:** nothing in scope is itself a failure, `NADA_COMPROBADO` with exit `1`, so an empty
  check never passes for a clean one.

Example, written by hand:

```json
{
  "orden": "check",
  "codigo": 1,
  "examinados": 2,
  "resumen": { "OK": 1, "CHANGED": 1 },
  "items": [
    { "estado": "CHANGED", "tipo": "ancla", "doc": "docs/payments.md", "linea_doc": 3,
      "ancla": "src/payments.py#validate_payment",
      "detalle": "the content of “validate_payment” changed (src/payments.py:4-7)" }
  ]
}
```

### `scan`

Seals new anchors and prunes the ones no document uses any more. Same output as `check`; each new
anchor carries its `bloque` so you can confirm where it landed. **Effect:** writes
`.dockeeper.sello.json`. <!-- dockeeper: dockeeper/cli.py#_scan dockeeper/motor.py#escanear -->

### `fix`

Follows code that moved; with `--aceptar`, also reseals what changed after a person reviewed it.
Same output as `check` after the fix, plus `hechos`: the items it acted on, each with its `accion`.
**Effect:** writes the seal file only, never a document.
<!-- dockeeper: dockeeper/cli.py#_fix dockeeper/motor.py#arreglar -->

### `link`

Binds a sentence of a published document to code without writing anything in the document.
**Output:** `orden`, `raiz`, `codigo` and `items`. **Effect:** writes the seal file.
<!-- dockeeper: dockeeper/cli.py#_link dockeeper/motor.py#vincular -->

### `audit`

The inventory. Reads, never writes, and always exits `0`.
<!-- dockeeper: dockeeper/cli.py#_audit dockeeper/auditoria.py#auditar -->

- **Output:** `git` (`historial`, `commits`, `commits_con_decision`), `totales`, `paginas` (each base
  page and the documents that fill it), `documentos` (anchors, links, code blocks and diagrams per
  document), `paquetes` (each package with its files, definitions, anchored definitions, README and the
  documents about it), `cobertura` per top-level folder and `mayores_sin_ancla`, the largest
  definitions no claim covers.

### `why`

Decisions recorded in the git history. Reads, never writes.
<!-- dockeeper: dockeeper/cli.py#_why dockeeper/porque.py#historial -->

- **Output:** `historial` (`false` when there is no git history), `decisiones` (`commit`, `fecha`,
  `autor`, `asunto`, `decision`, `motivo`, `alternativas`, `adr`, `documentada`, `ficheros`),
  `documentos` (the decision documents) and `entradas` (each entry of those documents and whether it
  has a written reason, `con_motivo`). A `motivo` that the history doesn't record is `null`, never a
  guess.

### `review`

What a change means for the docs. Reads, never writes, and always exits `0`: it informs, the gate is
`check`. <!-- dockeeper: dockeeper/cli.py#_review dockeeper/revision.py#revisar -->

- **Output:** `desde` and `base` (the commits compared), `cambios` (`codigo` and `documentos`
  changed), `afirmaciones` (claims the change touched, as items), `sin_documentar` (`simbolo`,
  `estado` of `nueva` or `cambiada`, `inicio`, `fin`, `lineas` and the `documentos` that already talk
  about that file) and `decisiones` not written down yet.
  <!-- dockeeper: dockeeper/revision.py#SinDocumentar -->
