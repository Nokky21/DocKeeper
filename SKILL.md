---
name: dockeeper
description: Use when writing, updating or auditing repository documentation that must stay true to the code (README, architecture, decisions, runbooks, API, onboarding) — every claim is anchored to code and checked with the local `dockeeper` CLI (OK / MOVED / CHANGED), including published docs that must not leak internal paths or copied code, and "why" sections drawn only from git history.
license: MIT
compatibility: Needs python3 (3.9+, standard library only) and git; runs locally, no network or account.
---

# DocKeeper — documentación que no se pudre

Escribir documentación ya no tiene valor; que **siga siendo verdad**, sí. Este skill escribe
documentación detallada y **ancla cada afirmación a su código**; la CLI `dockeeper` sella esas
anclas y avisa cuando el código del que hablan cambia. Todo es local: sin cuenta, sin red, sin IA en
el motor.

**Cómo se ejecuta la CLI** (sin instalar nada, Python 3.10+ y solo biblioteca estándar), desde la
raíz del repositorio que se documenta:

```bash
python3 <carpeta-de-este-skill>/bin/dockeeper <orden> [--json] [--solo RUTA]... [--sin PATRÓN]...
```

En Claude Code la carpeta del skill es `${CLAUDE_SKILL_DIR}`. En Windows, si no existe `python3`, usa
`python` (o `py`).

Órdenes: `audit`, `scan`, `check`, `fix`, `link`, `why`. Todas aceptan `--json` (úsalo para leer
resultados) y `--raiz` si no estás en la raíz. Salida: 0 bien · 1 hay problemas · 2 error de uso.
<!-- dockeeper: dockeeper/cli.py#main dockeeper/motor.py#FALLOS -->

## La regla

**Cada afirmación verificable lleva su ancla.** No «esta función valida el pago», sino «esta función
valida el pago» + ancla a la definición. Si una frase no se puede anclar (opiniones, planes,
promesas), o se convierte en algo comprobable o se marca como lo que es. Lo que no se sabe no se
inventa: se escribe «No consta».

**Idioma:** escribe la documentación en el idioma del repositorio (o en el que pida la persona). Las
plantillas de `templates/` están en español: traduce sus encabezados y textos guía; no impongas el
español a un proyecto en otro idioma. Para no consta, usa la expresión equivalente («Not documented»).

## Sintaxis de anclas

| Forma | Escritura | Cuándo |
|---|---|---|
| Por símbolo (**preferida**) | `[[ruta/fichero.ext#nombre]]` | funciones, clases, métodos, constantes |
| Símbolo con contenedor | `[[ruta/fichero.ext#Clase.metodo]]` | métodos con nombres repetidos |
| Por línea | `[[ruta/fichero.ext:147]]` | algo que no es una definición (config, una línea suelta) |
| Oculta | `<!-- dockeeper: ruta:147 ruta#nombre -->` | no ensuciar el texto visible (código público) |
| Vínculo | `dockeeper link doc.md:12 ruta#nombre` | documentación publicada con código privado |

- Rutas **relativas a la raíz** del repositorio.
- El bloque de un ancla es la **definición entera** que contiene la línea (la más interior); si no
  hay definición, una ventana de ±3 líneas. Por eso un ancla por línea dentro de una función vigila
  la función completa. <!-- dockeeper: dockeeper/bloques.py#bloque_en -->
- Prefiere símbolos: el número de línea escrito en un documento envejece a la vista cuando el código
  se mueve (el sello sabe la posición real, pero el lector ve la antigua). `fix` no reescribe
  documentos.
- Lo que va dentro de bloques de código o código en línea **no** es un ancla: así se enseña la
  sintaxis sin crear anclas falsas. <!-- dockeeper: dockeeper/markdown.py#analizar -->

## Flujo de trabajo

1. **Auditar** — `dockeeper audit --json`: páginas base que faltan, documentos sin anclas, carpetas y
   definiciones grandes sin ninguna afirmación. Lee el código de la zona antes de escribir.
   `dockeeper why --json` da las decisiones del historial.
2. **Escribir** — parte de `templates/` (README, ARQUITECTURA, DECISIONES, PROCEDIMIENTOS, API,
   INCORPORACION). Detallado y concreto; un ancla por afirmación. Nada de copiar bloques de código
   del repositorio en documentos publicados: descríbelo o escribe un ejemplo propio.
3. **Sellar** — `dockeeper scan`. **Lee la previa de cada ancla**: dice en qué bloque ha quedado
   (tipo, nombre, líneas, primera y última línea). Si el bloque no es aquello de lo que habla la
   frase, corrige el ancla y vuelve a ejecutar `scan`. Un ancla mal puesta se sella tal cual; la
   previa es la única red.
4. **Comprobar** — `dockeeper check`. En CI, el código de salida decide.
5. **Arreglar**:
   - `MOVED` → `dockeeper fix` (solo toca el sello). <!-- dockeeper: dockeeper/motor.py#arreglar -->
   - `CHANGED` → lee el código nuevo, **corrige el texto** si ya no es cierto y después
     `dockeeper fix --aceptar` (acota con `--solo` para no aceptar más de lo revisado).
   - `DESAPARECIDO` → el fichero ya no existe: reescribe la afirmación o quítala; luego `scan`.
   - `SIN_SELLAR` → `scan`. `HUERFANA` → `fix` la quita.

## Qué escribe cada página

- **README** — qué es, para quién, cómo funciona en una vuelta (un ancla por paso), cómo arrancar,
  configuración (ancla al código que lee cada variable), estado y límites.
- **ARQUITECTURA** — componentes con responsabilidad, entradas/salidas, dependencias e invariantes;
  flujos principales paso a paso incluidos los fallos; datos; fronteras de seguridad. Todo anclado.
- **DECISIONES** — una entrada por decisión: fecha, decisión, **motivo**, alternativas descartadas,
  consecuencias, fuente (commit/ADR/persona) y ancla al código. Motivo y alternativas **solo si
  constan** (historial, ADR o una persona); si no, «**Motivo:** No consta». `why` señala las
  entradas sin motivo escrito y qué decisiones del historial aún no están documentadas.
- **PROCEDIMIENTOS** — pasos ejecutables con comando exacto, ancla al script y comprobación de cada
  paso; qué hacer si falla y cómo volver atrás. Sin secretos reales.
- **API** — por operación: permisos, entrada (ancla a la validación), salida, errores, efectos e
  idempotencia; ejemplos escritos a mano.
- **INCORPORACION** — ruta de lectura anclada para el primer día, ideas clave, cómo se trabaja,
  trampas conocidas y a quién preguntar.

## Documentación publicada

Declárala en `.dockeeper.json` (en la raíz del repositorio documentado):

| Clase | Clave | Regla que comprueba `check` |
|---|---|---|
| Se publica y su código **no** es público | `publico` | sin anclas (`ANCLA_INTERNA`), sin rutas internas (`RUTA_INTERNA`), sin código copiado (`CODIGO_COPIADO`) |
| Se publica y su código **sí** es público | `publicado` | puede anclar a su código (mejor oculto), pero sin código copiado |

- Para documentos `publico`, vincula cada afirmación **fuera del texto**:
  `dockeeper link docs/guia.md:12 src/pagos.ts#validarPago`. El lector no ve ninguna ruta; `check`
  comprueba el código y también que la frase siga ahí (si se mueve: `MOVED`; si se reescribe:
  `VINCULO_SUELTO` → revisar y volver a vincular, o `link --quitar`).
- Código copiado = 3 o más líneas seguidas idénticas (espacios aparte) a un fichero del repositorio;
  el aviso dice de qué fichero sale. Umbral: `bloque_minimo`.
  <!-- dockeeper: dockeeper/publicado.py#IndiceCopias dockeeper/motor.py#_verificar_vinculo -->

Otras claves: `documentos` (qué ficheros son documentos, por defecto Markdown), `sin` (lo que se
descarta siempre), `decisiones` (qué documentos son de decisiones), `ventana` (radio de la ventana).

## Alcance parcial

- `--solo RUTA` (repetible). Si la ruta señala **solo documentos**, recorta los documentos; si
  señala **código**, recorta el código. `--solo src/pagos` comprueba esa parte con todos los
  documentos que hablan de ella; `--solo docs/api.md` comprueba ese documento sin perder el código
  al que apunta. Varias rutas se combinan.
- `--sin PATRÓN` (repetible) descarta documentos y código (`*`, `?` o prefijos de carpeta).
- Un `--solo` que no casa con nada es un error; un `check` sin nada que comprobar **falla**
  (`NADA_COMPROBADO`): no existe el verde vacío. <!-- dockeeper: dockeeper/alcance.py#Alcance dockeeper/motor.py#comprobar -->
- Úsalo para documentar una zona cada vez: `audit --solo zona` → escribir → `scan --solo zona` →
  `check --solo zona`.

## Limitaciones (dilas si vienen al caso)

- Compara contenido, no significados: un bloque reescrito con el mismo sentido sale `CHANGED`.
- Una copia **no contigua** (líneas reordenadas o recortadas) no se detecta; copias de una o dos
  líneas se dejan pasar a propósito.
- Las definiciones se reconocen por patrones (Python, JS/TS, Go, Rust, Java, Kotlin, C#, C/C++,
  Swift, PHP, Ruby, Elixir, Lua, shell…), no con un analizador: alguna construcción rara no se
  detecta y se usa la definición que la contiene o una ventana. La previa de `scan` lo enseña.
- No juzga si la documentación es útil, solo si sigue siendo cierta.
