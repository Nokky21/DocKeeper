# SPEC — DocKeeper

> Estado: v0.1 · 2026-10-13 · Origen: encargo «DocKeeper» (CEO, encargo de Edgar, 2026-10-12).
> Este documento manda sobre el código: si discrepan, uno de los dos está mal.

## 1. El problema

La IA ya escribe documentación; eso ya no vale nada. Lo que cuesta es que **siga siendo verdad**:
a los pocos meses el texto describe un código que ya no existe y nadie sabe qué páginas mienten.
Las herramientas que atacan esto cuestan cientos de dólares al mes. No hay una versión gratuita,
local y completa para una persona sola.

## 2. Qué es

Un **skill** (`SKILL.md` + `templates/`) y una **CLI** (`dockeeper`, paquete `dockeeper/`) que
trabajan juntos:

1. El skill escribe documentación detallada (README, arquitectura, decisiones, procedimientos, API,
   incorporación) **anclando cada afirmación a su código**.
2. La CLI **sella** cada ancla (huella del bloque de código) y **comprueba** después si sigue siendo
   cierta: `OK`, `MOVED` (se movió: se arregla sola) o `CHANGED` (cambió: lo mira una persona).
3. Funciona sobre el repositorio entero o una parte (`--solo`, `--sin`).
4. Sirve para documentación **publicada**: sin rutas internas ni código copiado, y aun así comprobable
   (vínculos guardados fuera del documento).
5. Saca el **porqué** del historial de git; lo que no consta no se inventa.

## 3. Qué NO hace (en esta fase)

- No juzga si la documentación es útil, solo si sigue siendo cierta.
- No compara significados: compara contenido normalizado. Sin modelos de IA en el motor.
- No tiene servidor, cuentas, cobros ni telemetría. No usa la red.
- No escribe fuera del repositorio sobre el que trabaja (solo `.dockeeper.sello.json` en su raíz).
- No toca la configuración de otros programas ni publica nada en ningún sitio.
- No reescribe documentos: `fix` solo toca el sello.

## 4. Diseño

### 4.1 Anclas

| Forma | Ejemplo | Uso |
|---|---|---|
| Visible por línea | `[[src/pagos.ts:147]]` | afirmaciones sobre una línea concreta |
| Visible por símbolo | `[[src/pagos.ts#validarPago]]` | **recomendada**: no envejece a la vista |
| Símbolo con contenedor | `[[src/pagos.ts#Cobros.validar]]` | desambigua métodos homónimos |
| Oculta | `<!-- dockeeper: src/pagos.ts:147 src/pagos.ts#validar -->` | no ensucia el Markdown visible |
| Vínculo (fuera del doc) | `dockeeper link doc.md:12 src/pagos.ts#validar` | documentación publicada |

- Rutas **relativas a la raíz** del repositorio. Una ruta absoluta o que sale de la raíz es un error.
- Al leer un documento se saltan los bloques de código (` ``` ` y `~~~`), el código en línea y los
  comentarios HTML que no son de dockeeper. Así un documento que *enseña* la sintaxis no se llena de
  anclas falsas (fallo del prototipo).

### 4.2 El bloque de una ancla

- Por línea: si la línea cae dentro de una función, clase o método, el bloque es **la definición más
  interior que la contiene, entera** (con sus decoradores). Si no hay definición: ventana de
  ±`ventana` líneas (3 por defecto) **recortada para empezar y acabar en líneas con contenido**.
- Por símbolo: la definición con ese nombre (si no hay, la declaración `NOMBRE = …` menos indentada).
- Las definiciones se reconocen por patrones por familia de lenguaje (indentación: Python; `end`:
  Ruby, Elixir, Lua, Julia; llaves: JS/TS, Go, Rust, Java, Kotlin, C#, C/C++, Swift, PHP, Dart,
  shell…). Antes, el contenido de cadenas y comentarios se blanquea para que una llave dentro de un
  texto no cuente.

### 4.3 Huella y veredictos

- Huella = SHA-256 (16 hex) de las líneas del bloque **normalizadas**: espacios colapsados, sin
  espacios en los extremos, sin líneas vacías. Reformatear no rompe; cambiar la lógica sí.
- Comprobación de una ancla sellada:
  1. Fichero inexistente → `DESAPARECIDO`.
  2. Se recalcula el bloque en la posición guardada (definición: se recalcula desde la línea;
     ventana: el tramo guardado; símbolo: por nombre). Huella igual y misma posición → `OK`;
     huella igual en otra posición → `MOVED`.
  3. Si no, se busca la huella antigua en todo el fichero: aparece → `MOVED`; no aparece → `CHANGED`.
- Código de salida de `check`: **0** si todo es `OK`/`MOVED` (o avisos); **1** si hay `CHANGED`,
  `DESAPARECIDO`, ancla sin sellar o mal escrita, cualquier problema de documentación publicada o
  nada que comprobar; **2** error de uso o de configuración.

### 4.4 El sello

`.dockeeper.sello.json` en la raíz, JSON estable y ordenado (diffs legibles). Por ancla: documento,
ancla tal como está escrita (clave), fichero, línea actual, tramo, tipo de bloque, nº de líneas
normalizadas y huella. **No guarda código**, solo huellas.

### 4.5 Órdenes

| Orden | Qué hace | Escribe |
|---|---|---|
| `audit` | inventario: páginas base que faltan, documentos sin anclas, cobertura por carpeta | nada |
| `scan` | sella las anclas nuevas y **enseña en qué bloque queda cada una**; poda las que ya no están | sello |
| `check` | comprueba anclas, vínculos y documentación publicada | nada |
| `fix` | recoloca los `MOVED`, quita huérfanas; con `--aceptar`, acepta los `CHANGED` revisados | sello |
| `link` | vincula una línea de un documento con código sin tocar el documento (`--quitar` deshace) | sello |
| `why` | decisiones del historial (`Decision:`, `Motivo:`, `Why:`, `ADR`…) y entradas sin motivo | nada |

Todas aceptan `--json` y `--raiz`.

### 4.6 Alcance parcial

- `--solo RUTA` (repetible): si todo lo que casa con la ruta son documentos, recorta los
  **documentos**; si casa algún fichero de código, recorta el **código** (los destinos de las anclas).
  `--solo dockeeper` comprueba esa parte con todos los documentos que hablan de ella;
  `--solo README.md` comprueba ese documento sin perder el código al que apunta.
- `--sin PATRÓN` (repetible; también `sin` en la configuración): descarta documentos y código.
- Listas vacías: `--solo` vacío = **sin restricción**; `--sin` vacío = **nada que descartar**. Son
  semánticas distintas y se prueban por separado (fallo del prototipo: todo parecía correcto porque
  no se comprobaba nada).
- Un `--solo` que no casa con nada es un error (2). Un `check` que no comprueba nada falla (1).

### 4.7 Documentación publicada

`.dockeeper.json`:

| Clase | Clave | Regla |
|---|---|---|
| Publicada, código **privado** | `publico` | ni anclas (visibles u ocultas), ni rutas internas, ni código copiado |
| Publicada, código **público** | `publicado` | puede anclar a su código, pero no copiarlo |

- `link` guarda la comprobación fuera del documento. Del lado del documento se guarda la huella de
  la línea vinculada: si la línea se mueve → `MOVED`; si se reescribe → `VINCULO_SUELTO`.
- `CODIGO_COPIADO`: un bloque de código de un documento publicado contiene `bloque_minimo` (3) o más
  líneas contiguas normalizadas idénticas a líneas contiguas de un fichero del repositorio.
- `RUTA_INTERNA` (solo `publico`): el texto menciona la ruta de un fichero o carpeta del repositorio.

## 5. Criterios de aceptación

Cada criterio tiene una prueba que lo demuestra (`python3 -m unittest`).

| # | Criterio | Prueba |
|---|---|---|
| CA-01 | Mover una función no hace fallar `check` (`MOVED`, salida 0) y `fix` la recoloca (luego `OK`). | [[tests/test_check.py#PruebasCheck.test_mover_funcion_no_falla_y_fix_la_recoloca]] |
| CA-02 | Cambiar el contenido de una función anclada hace fallar `check` (`CHANGED`, salida 1). | [[tests/test_check.py#PruebasCheck.test_cambiar_contenido_falla]] |
| CA-03 | `fix` (también con `--aceptar`) no modifica ningún documento. | [[tests/test_check.py#PruebasCheck.test_fix_no_toca_el_documento]] |
| CA-04 | Un fichero anclado que desaparece se detecta (`DESAPARECIDO`, salida 1). | [[tests/test_check.py#PruebasCheck.test_fichero_desaparecido]] |
| CA-05 | Un documento publicado con código copiado falla y dice de qué fichero sale. | [[tests/test_publicado.py#PruebasPublicado.test_codigo_copiado_falla_y_dice_de_donde]] |
| CA-06 | Un documento `publico` con anclas internas (visibles u ocultas) o rutas internas falla. | [[tests/test_publicado.py#PruebasPublicado.test_publico_con_anclas_internas_falla]] |
| CA-07 | El vínculo de un documento publicado se comprueba sin aparecer en el texto. | [[tests/test_publicado.py#PruebasPublicado.test_vinculo_se_comprueba_sin_aparecer_en_el_texto]] |
| CA-08 | `--solo` restringe a una parte (código o documentos según a qué señale). | [[tests/test_alcance.py#PruebasAlcance.test_solo_codigo_recorta_el_codigo]] |
| CA-09 | Listas vacías: sin `--solo` no hay restricción y `--sin` vacío no descarta nada. | [[tests/test_alcance.py#PruebasAlcance.test_listas_vacias]] |
| CA-10 | Reformatear (espacios, líneas vacías) no rompe una ancla. | [[tests/test_check.py#PruebasCheck.test_reformatear_no_rompe]] |
| CA-11 | Las anclas dentro de bloques de código y código en línea se ignoran. | [[tests/test_anclas.py#PruebasAnclas.test_salta_bloques_y_codigo_en_linea]] |
| CA-12 | `scan` enseña en qué bloque queda cada ancla. | [[tests/test_check.py#PruebasCheck.test_scan_ensena_el_bloque]] |
| CA-13 | `check` sin nada que comprobar falla: no existe el verde vacío. | [[tests/test_check.py#PruebasCheck.test_nada_comprobado_falla]] |
| CA-14 | `why` extrae decisiones del historial, no inventa motivos y señala entradas sin motivo. | [[tests/test_porque.py#PruebasPorque.test_decisiones_del_historial]] |
| CA-15 | Todas las órdenes aceptan `--json` y emiten JSON válido. | [[tests/test_cli.py#PruebasCli.test_todas_las_ordenes_aceptan_json]] |
| CA-16 | No escribe fuera de la raíz: solo crea `.dockeeper.sello.json`. | [[tests/test_cli.py#PruebasCli.test_solo_escribe_el_sello]] |
| CA-17 | El propio repositorio está sellado y su `check` está en verde. | [[tests/test_autocomprobacion.py#PruebasAutocomprobacion.test_el_repositorio_se_mantiene_limpio]] |

## 6. Criterios de abandono

Se para y se replantea si ocurre cualquiera de estas cosas:

1. En repositorios reales, más de **1 de cada 5** `CHANGED` es ruido (el comportamiento no cambió) de
   forma sostenida: el coste de revisar supera el valor del aviso.
2. La detección de definiciones por patrones falla en más del **10 %** de las anclas de un lenguaje
   objetivo y la previa de `scan` no basta para corregirlo a mano.
3. El valor principal empieza a necesitar IA para funcionar (regla 3 del encargo).
4. Para que la versión de pago tenga sentido habría que empeorar la gratuita (regla 2): se abandona
   el modelo, no la gratuita.

### Medición (2026-10-13)

Para el criterio 2, `audit` sobre un backend NestJS/TypeScript real (960 ficheros de código, sin
escribir nada en él): 1,4 s; 1518 métodos de clase según un oráculo aproximado por expresión
regular, 0 sin detectar. El único fallo visto en la muestra previa (tipo de retorno genérico partido
en varias líneas) se corrigió y tiene prueba.

## 7. Decisiones tomadas ante ambigüedades

| Ambigüedad | Decisión | Por qué |
|---|---|---|
| «`fix` no toca el texto del documento» | `fix` solo escribe el sello. El número visible de una ancla por línea puede quedar atrás (el sello lleva la posición real). | Es la lectura literal y la más simple. Por eso se recomienda anclar por **símbolo**, que no envejece a la vista. |
| Identidad de un ancla entre ejecuciones | Clave = (documento, ancla tal como está escrita). Misma ancla repetida en un documento = una entrada. | Editar el texto alrededor no rompe el sello; cambiar el destino a mano crea un ancla nueva. |
| Ventana frente a definición al comprobar | La definición se recalcula desde la línea; la ventana se comprueba por su tramo guardado. | Recalcular una ventana por radio tras borrar una línea vacía interna daría `MOVED` eternos. |
| Ancla por símbolo que cambia de línea | `MOVED` (salida 0) y `fix` actualiza el tramo. | Uniforme con las anclas por línea; el sello no queda desfasado. |
| `[[algo#x]]` sin `.` ni `/` en la ruta | No es ancla. | No confundir con wikilinks de Obsidian (`[[nota#encabezado]]`). |
| Bloques de Markdown indentados (4 espacios) | Se leen como texto, no como código. | Tratarlos como código haría desaparecer en silencio anclas de listas anidadas; un ancla falsa al menos da error visible. Para enseñar la sintaxis: ` ``` `. |
| Qué línea cuenta para «código copiado» | Solo líneas con algún carácter alfanumérico. | Una ristra de `}` o `)` no es copiar código y daría falsos avisos. |
| «No puede llevar rutas internas» | Además de las anclas, `RUTA_INTERNA` busca en el texto de un doc `publico` rutas de ficheros o carpetas del repo (con al menos una `/`). | El encargo habla de rutas, no solo de anclas. |
| `check` sin nada en alcance | Falla con `NADA_COMPROBADO`. | Un verde vacío es exactamente el fallo del prototipo. |
| Versión de Python | Objetivo 3.10+; el código evita lo que no existe en 3.9 y la suite pasa también en 3.9 (el `python3` del sistema en macOS). | Que funcione sin instalar nada. |
| Ancla huérfana (en el sello, ya no en el doc) | Aviso `HUERFANA` (salida 0); `scan` y `fix` la quitan. | Ya no hay afirmación que comprobar. |

## 8. Límites conocidos (no se esconden)

- Compara contenido, no significados: un bloque reescrito con el mismo sentido sale `CHANGED`.
- Normaliza espacios también dentro de cadenas: cambiar `"a  b"` por `"a b"` no se nota.
- Una copia **no contigua** (líneas reordenadas o recortadas) no se detecta.
- El umbral de 3 líneas deja pasar copias de una o dos líneas **a propósito**, para no llenar de
  avisos falsos.
- Un ancla mal puesta se sella tal cual: `scan` enseña el bloque de cada ancla precisamente para
  confirmarla al escribirla.
- Las definiciones se reconocen por patrones, no por un analizador: hay construcciones raras que no
  se detectan (métodos C++ fuera de la clase, decoradores multilínea, funciones anónimas). Entonces se
  usa la definición que la contiene o una ventana, y la previa de `scan` lo enseña.
- Si el bloque anclado aparece idéntico en dos sitios, `MOVED` elige el más cercano a la posición
  antigua.
- `RUTA_INTERNA` puede dar falsos avisos si una URL pública coincide con una carpeta interna.
- No juzga si la documentación es **útil**, solo si sigue siendo **cierta**.
