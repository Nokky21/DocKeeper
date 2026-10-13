# DocKeeper

**Documentación que no se pudre.** · *Documentation that doesn't rot.* — [English below](#english)

Escribir documentación ya no cuesta nada; que **siga siendo verdad** sí. Con los meses el texto
describe un código que ya no existe y nadie sabe qué páginas mienten. DocKeeper ancla cada
afirmación a su código y avisa cuando ese código cambia.

Gratis, local y completo: sin cuenta, sin servidor, sin red, sin límites artificiales y sin IA en el
motor. Solo Python 3.10+ y su biblioteca estándar.

## Cómo funciona

1. **Anclas.** Cada afirmación lleva su ancla al código: por símbolo (`[[src/pagos.ts#validarPago]]`),
   por línea (`[[src/pagos.ts:147]]`), oculta en un comentario (`<!-- dockeeper: src/pagos.ts:147 -->`)
   o, para documentación publicada, guardada fuera del texto con `dockeeper link`. Lo que va dentro
   de bloques de código o código en línea no cuenta como ancla, así que se puede enseñar la
   sintaxis sin crear anclas falsas. <!-- dockeeper: dockeeper/markdown.py#analizar -->
2. **Bloque.** Si la línea anclada está dentro de una función, clase o método, el bloque es esa
   definición entera; si no, una ventana alrededor recortada a líneas con contenido.
   <!-- dockeeper: dockeeper/bloques.py#bloque_en -->
3. **Huella.** Un hash del bloque normalizado (sin espacios sobrantes ni líneas vacías): reformatear
   no rompe nada; cambiar la lógica sí se nota. <!-- dockeeper: dockeeper/huellas.py#normalizar_linea dockeeper/huellas.py#huella -->
   El sello guarda posiciones y huellas, nunca código. <!-- dockeeper: dockeeper/sello.py#Entrada -->
4. **Veredicto.** `OK`; `MOVED` si la misma huella aparece en otro sitio (se arregla solo con
   `fix`); `CHANGED` si ya no aparece (lo tiene que mirar una persona); `DESAPARECIDO` si el fichero
   ya no existe. <!-- dockeeper: dockeeper/motor.py#verificar_codigo -->

## Empezar

```bash
git clone <este repositorio> dockeeper
cd tu-proyecto
python3 ../dockeeper/bin/dockeeper audit      # qué hay, qué falta, qué no está anclado
python3 ../dockeeper/bin/dockeeper scan       # sella las anclas y enseña en qué bloque queda cada una
python3 ../dockeeper/bin/dockeeper check      # ¿sigue siendo cierto? (0 sí · 1 no · 2 error de uso)
```

También funciona `python3 -m dockeeper` desde la carpeta del proyecto, y `bin/dockeeper` se puede
enlazar desde el `PATH`.

| Orden | Qué hace |
|---|---|
| `audit` | páginas base que faltan, documentos sin anclas, cobertura por carpeta |
| `scan` | sella las anclas nuevas y enseña el bloque de cada una para confirmarla |
| `check` | comprueba anclas, vínculos y documentación publicada |
| `fix` | recoloca los `MOVED`; con `--aceptar`, acepta los `CHANGED` ya revisados |
| `link` | vincula una línea de un documento con código sin tocar el documento |
| `why` | decisiones del historial de git y entradas de decisión sin motivo |

Todas aceptan `--json`. `fix` solo escribe el sello: nunca reescribe un documento.
<!-- dockeeper: dockeeper/motor.py#arreglar -->

## En CI

`check` sale con **0** si todo está `OK` o `MOVED`, y con **1** si hay `CHANGED`, ficheros
desaparecidos, anclas sin sellar o problemas de documentación publicada. Si no hay nada que
comprobar también sale con 1: no existe el verde vacío.
<!-- dockeeper: dockeeper/motor.py#FALLOS dockeeper/motor.py#comprobar -->

## Alcance parcial

`--solo RUTA` (repetible) recorta los documentos si la ruta señala documentos y el código si señala
código: `--solo src/pagos` comprueba esa parte con todos los documentos que hablan de ella;
`--solo docs/api.md` comprueba ese documento sin perder el código al que apunta. `--sin PATRÓN`
descarta. Sin `--solo` no hay restricción; sin `--sin` no se descarta nada.
<!-- dockeeper: dockeeper/alcance.py#Alcance -->

## Documentación publicada

En `.dockeeper.json` se declaran dos clases:

- `publico`: se publica y su código es privado. Nada de anclas ni rutas internas ni código copiado;
  cada afirmación se vincula con `dockeeper link guia.md:12 src/pagos.ts#validarPago`, que se
  guarda en el sello. El lector no ve ninguna ruta y `check` sigue comprobándolo todo.
- `publicado`: se publica y su código también (como este README). Puede anclar a su código, pero no
  copiarlo.

Código copiado es un bloque de código del documento con 3 o más líneas seguidas idénticas a un
fichero del repositorio; el aviso dice de qué fichero sale.
<!-- dockeeper: dockeeper/publicado.py#IndiceCopias dockeeper/publicado.py#rutas_en_texto -->

## El porqué

`why` lee el historial buscando `Decision:`, `Motivo:`, `Why:`, `Alternativas:` y `ADR`, y señala
las entradas de los documentos de decisiones que no tienen motivo escrito. Lo que no consta en el
historial no se inventa: se escribe que no consta.
<!-- dockeeper: dockeeper/porque.py#historial dockeeper/porque.py#entradas_sin_motivo -->

## Límites

- Compara contenido, no significados: un bloque reescrito con el mismo sentido sale `CHANGED`.
- No detecta copias no contiguas; deja pasar copias de una o dos líneas a propósito.
- Reconoce definiciones con patrones, no con un analizador sintáctico: `scan` enseña el bloque de
  cada ancla para confirmarla al escribirla.
- No juzga si la documentación es útil, solo si sigue siendo cierta.

Más detalle en [SPEC.md](SPEC.md). El skill para escribir la documentación está en
[SKILL.md](SKILL.md) y las plantillas en [templates/](templates/).

## Pruebas

```bash
python3 -m unittest
```

La suite incluye la autocomprobación: este README está sellado y su `check` tiene que estar en
verde.

## Licencia

MIT. Ver [LICENSE](LICENSE).

---

## English

**DocKeeper keeps documentation true.** Writing docs is cheap now; keeping them correct is not.
DocKeeper anchors every claim to the code behind it and tells you when that code changes. Free,
local and complete: no account, no server, no network, no artificial limits, no AI in the engine.
Python 3.10+ standard library only.

**How it works.** Anchor each claim by symbol (`[[src/pay.ts#validatePayment]]`), by line
(`[[src/pay.ts:147]]`), in a hidden comment (`<!-- dockeeper: src/pay.ts:147 -->`) or, for
published docs, outside the text with `dockeeper link`. Anchors inside code blocks or inline code
are ignored. The anchored block is the whole enclosing function, class or method, or a trimmed
window when there is none. Its fingerprint is a hash of the normalized block, so reformatting is
harmless and logic changes are caught. Verdicts: `OK`, `MOVED` (same fingerprint elsewhere; `fix`
relocates it), `CHANGED` (a person must look), `DESAPARECIDO` (the file is gone).
<!-- dockeeper: dockeeper/bloques.py#bloque_en dockeeper/motor.py#verificar_codigo -->

**Commands.** `audit` (what exists, what is missing, what is unanchored), `scan` (seal anchors and
show the block each one landed on), `check` (exit 0 when everything is `OK`/`MOVED`, 1 otherwise,
2 on usage errors; nothing to check also exits 1), `fix` (relocate `MOVED`; `--aceptar` accepts
reviewed `CHANGED`; it only writes the seal file), `link` (bind a document line to code without
touching the document) and `why` (decisions from git history; missing reasons are reported, never
invented). All of them accept `--json`.

**Partial scope.** `--solo PATH` (repeatable) narrows documents when the path points at documents
and narrows code when it points at code. `--sin PATTERN` excludes.

**Published docs.** In `.dockeeper.json`, `publico` marks docs whose code is private (no anchors,
no internal paths, no copied code: use `dockeeper link`), and `publicado` marks docs whose code is
public (anchors allowed, copied code is not). Copied code means 3+ consecutive lines identical to a
repository file; the report names the source file.

**Limits.** It compares content, not meaning; non-contiguous copies are not detected; definitions
are found with patterns, not a parser, which is why `scan` shows every block for confirmation. It
checks that documentation is still true, not that it is useful.

Run the tests with `python3 -m unittest`. License: MIT.
