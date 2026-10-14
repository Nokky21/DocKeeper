"""Textos para personas: en inglés por defecto y en español si el entorno está en español.

El código escribe cada mensaje en español, que hace de clave; ``EN`` da su versión en inglés. El
idioma sale del entorno como en gettext: la primera variable con valor entre LC_ALL, LC_MESSAGES y
LANG; si empieza por «es», español. Los códigos de veredicto (OK, CHANGED…) y las claves de --json
no se traducen: son el contrato con agentes y scripts. Sus textos para personas (detalle, avisos,
error) sí siguen el idioma.
"""

from __future__ import annotations

import os


def espanol() -> bool:
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG"):
        valor = os.environ.get(variable)
        if valor:
            return valor.lower().startswith("es")
    return False


def t(texto: str, **datos: object) -> str:
    """El mensaje en el idioma del entorno, con sus datos ({nombre})."""
    plantilla = texto if espanol() else EN.get(texto, texto)
    return plantilla.format(**datos) if datos else plantilla


def tn(singular: str, plural: str, n: int, **datos: object) -> str:
    """Como ``t``, eligiendo singular o plural según ``n`` (disponible como {n})."""
    return t(singular if n == 1 else plural, n=n, **datos)


EN = {
    # --- Configuración, sello y alcance (errores de uso) ---
    "{fichero} no se puede leer: {error}": "{fichero} can't be read: {error}",
    "{fichero} debe ser un objeto JSON": "{fichero} must be a JSON object",
    "{fichero}: clave desconocida «{clave}» (válidas: {validas})": "{fichero}: unknown key “{clave}” (valid keys: {validas})",
    "{fichero}: «{clave}» debe ser una lista de textos": "{fichero}: “{clave}” must be a list of strings",
    "{fichero}: «{clave}» debe ser un entero mayor o igual que 1": "{fichero}: “{clave}” must be an integer of 1 or more",
    "{fichero} está dañado: entrada incompleta {entrada}": "{fichero} is damaged: incomplete entry {entrada}",
    "{fichero}: versión desconocida (se espera «dockeeper»: {version})": "{fichero}: unknown version (expected “dockeeper”: {version})",
    "--solo {patron}: no casa con ningún fichero del repositorio": "--solo {patron}: matches no file in the repository",
    "{ruta} no es una carpeta": "{ruta} is not a folder",
    "review necesita un repositorio git": "review needs a git repository",
    "--desde {desde}: no es una revisión de este repositorio": "--desde {desde}: not a revision of this repository",
    # --- Anclas mal escritas ---
    "«{token}» no es un ancla (usa ruta:línea o ruta#símbolo)": "“{token}” is not an anchor (use path:line or path#symbol)",
    "«{ruta}» es absoluta o sale del repositorio": "“{ruta}” is absolute or outside the repository",
    "las líneas empiezan en 1": "lines start at 1",
    "«{simbolo}» no es un símbolo válido": "“{simbolo}” is not a valid symbol",
    "el comentario dockeeper debe cerrarse en la misma línea": "a dockeeper comment must close on the same line",
    "comentario dockeeper sin anclas": "dockeeper comment with no anchors",
    "no es un ancla (usa ruta:línea o ruta#símbolo)": "not an anchor (use path:line or path#symbol)",
    # --- Resolver un ancla ---
    "{fichero} no existe": "{fichero} does not exist",
    "{fichero} no es un fichero de texto legible": "{fichero} is not a readable text file",
    "no se reconocen definiciones en ficheros como {fichero}: ancla por línea": "definitions aren't recognized in files like {fichero}: anchor by line",
    "no se encuentra la definición de «{simbolo}» en {fichero}": "no definition of “{simbolo}” found in {fichero}",
    "«{simbolo}» aparece {n} veces; se usa la de la línea {linea}. Precisa con Contenedor.{nombre}": "“{simbolo}” appears {n} times; using the one on line {linea}. Narrow it with Container.{nombre}",
    "{fichero} tiene {n} líneas": "{fichero} has {n} lines",
    "no hay código alrededor de {fichero}:{linea}": "no code around {fichero}:{linea}",
    "ninguna definición contiene la línea: se usa una ventana de ±{n} líneas": "no definition contains the line: using a window of ±{n} lines",
    "la línea anclada está vacía": "the anchored line is empty",
    "comentario oculto": "hidden comment",
    "ancla visible": "visible anchor",
    "{forma} en un documento «publico»: usa dockeeper link (se guarda fuera del texto)": "{forma} in a “publico” document: use dockeeper link (it is stored outside the text)",
    # --- scan, check, fix ---
    "ya no está en el documento": "no longer in the document",
    "el documento ya no existe": "the document no longer exists",
    "sellada en {fichero}:{inicio}-{fin}": "sealed at {fichero}:{inicio}-{fin}",
    "ancla sin sellar: dockeeper scan": "anchor not sealed: dockeeper scan",
    "el documento ya no contiene esta ancla: fix la quita del sello": "the document no longer contains this anchor: fix removes it from the seal",
    "no hay ninguna afirmación que comprobar en este alcance": "there are no claims to check in this scope",
    "el documento ya no existe: fix quita el vínculo": "the document no longer exists: fix removes the link",
    "la frase vinculada pasó de la línea {antes} a la {ahora}": "the linked sentence moved from line {antes} to line {ahora}",
    "la frase de la línea {linea} ya no está: revísala y vuelve a vincular": "the sentence on line {linea} is gone: review it and link again",
    "{fichero} ya no existe": "{fichero} no longer exists",
    "«{simbolo}» pasó de {inicio}-{fin} a {nuevo_inicio}-{nuevo_fin}": "“{simbolo}” moved from {inicio}-{fin} to {nuevo_inicio}-{nuevo_fin}",
    "ya no se encuentra «{simbolo}» en {fichero}": "“{simbolo}” is no longer in {fichero}",
    "el contenido de «{simbolo}» cambió ({fichero}:{inicio}-{fin})": "the content of “{simbolo}” changed ({fichero}:{inicio}-{fin})",
    "el bloque pasó de {inicio}-{fin} a {nuevo_inicio}-{nuevo_fin}": "the block moved from {inicio}-{fin} to {nuevo_inicio}-{nuevo_fin}",
    "el bloque {fichero}:{inicio}-{fin} cambió": "the block {fichero}:{inicio}-{fin} changed",
    " (no se puede aceptar: {motivo})": " (can't accept it: {motivo})",
    "«{destino}» no es DOCUMENTO:LÍNEA (rutas relativas a la raíz)": "“{destino}” is not DOCUMENT:LINE (paths relative to the root)",
    "{doc} no existe o no es texto": "{doc} does not exist or is not text",
    "la línea {linea} de {doc} está vacía: vincula la frase, no el hueco": "line {linea} of {doc} is empty: link the sentence, not the gap",
    "no hay vínculos en {doc}:{linea}": "no links on {doc}:{linea}",
    "no hay vínculos en {doc}:{linea} hacia {ancla}": "no links on {doc}:{linea} to {ancla}",
    # --- Documentación publicada ---
    "el bloque de código copia {n}+ líneas seguidas de {fuente}: descríbelo o escribe un ejemplo propio": "the code block copies {n}+ consecutive lines of {fuente}: describe it or write your own example",
    "menciona la ruta interna «{ruta}» en un documento publicado": "mentions the internal path “{ruta}” in a published document",
    # --- Línea de órdenes: ayuda ---
    "Documentación anclada al código que avisa cuando deja de ser cierta.": "Documentation anchored to code that tells you when it stops being true.",
    "raíz del repositorio (por defecto, la carpeta con .dockeeper.json o .git)": "repository root (default: the nearest folder with .dockeeper.json or .git)",
    "salida en JSON": "JSON output",
    "limita a esta ruta (repetible): si es de documentos recorta documentos; si es de código recorta código": "limit to this path (repeatable): a documents path narrows documents; a code path narrows code",
    "descarta lo que case con este patrón o prefijo (repetible)": "exclude what matches this pattern or prefix (repeatable)",
    "inventario: páginas que faltan, documentos sin anclas, paquetes y código sin documentar": "inventory: missing pages, documents without anchors, packages and undocumented code",
    "sella las anclas nuevas y enseña en qué bloque queda cada una": "seal new anchors and show the block each one lands on",
    "vuelve a sellar también las ya selladas (tras revisar el texto)": "re-seal the already sealed ones too (after reviewing the text)",
    "comprueba que lo documentado sigue siendo cierto": "check that what is documented is still true",
    "recoloca los MOVED y quita huérfanas (solo toca el sello)": "relocate MOVED anchors and remove orphans (only touches the seal)",
    "acepta los CHANGED como nueva verdad (después de revisar el texto)": "accept CHANGED blocks as the new truth (after reviewing the text)",
    "vincula una línea de un documento con código sin tocar el documento": "link a line of a document to code without touching the document",
    "documento y línea de la afirmación": "document and line of the claim",
    "código que la respalda": "code that backs it",
    "quita los vínculos de esa línea (o solo el indicado)": "remove the links on that line (or just the given one)",
    "decisiones del historial (Decision:, Motivo:, Why:, ADR) y entradas sin motivo": "decisions from git history (Decision:, Motivo:, Why:, ADR) and entries with no reason",
    "qué documentación toca un cambio y qué código nuevo o cambiado queda sin documentar": "which docs a change touches and which new or changed code is left undocumented",
    "revisión desde la que comparar con el árbol de trabajo (por defecto HEAD~1: el último commit y lo que haya sin commitear); con una rama, desde donde se bifurcó": "revision to compare the working tree with (default HEAD~1: the last commit plus anything uncommitted); with a branch, from where it forked",
    "falta el ancla: dockeeper link DOC:LÍNEA RUTA:LÍNEA|RUTA#SÍMBOLO": "missing anchor: dockeeper link DOC:LINE PATH:LINE|PATH#SYMBOL",
    "orden": "command",
    "RUTA": "PATH",
    "PATRÓN": "PATTERN",
    "DOC:LÍNEA": "DOC:LINE",
    "RUTA:LÍNEA|RUTA#SÍMBOLO": "PATH:LINE|PATH#SYMBOL",
    # --- Línea de órdenes: salida común ---
    "(repositorio)": "(repository)",
    "aviso: {aviso}": "warning: {aviso}",
    "definición": "definition",
    "declaración": "declaration",
    "ventana": "window",
    "bloque: {tipo}{nombre} {fichero}:{inicio}-{fin}": "block: {tipo}{nombre} {fichero}:{inicio}-{fin}",
    " «{nombre}»": " “{nombre}”",
    "   ← línea anclada": "   ← anchored line",
    "{n} fuera de alcance": "{n} out of scope",
    "nada": "nothing",
    "Resumen: {resumen}": "Summary: {resumen}",
    "Resultado: FALLA": "Result: FAIL",
    "Resultado: en verde": "Result: green",
    "dockeeper fix las recoloca (solo toca el sello)": "dockeeper fix relocates them (it only touches the seal)",
    "revisa el código y el texto; luego dockeeper fix --aceptar": "review the code and the text, then dockeeper fix --aceptar",
    "dockeeper scan las sella": "dockeeper scan seals them",
    "dockeeper fix las quita del sello": "dockeeper fix removes them from the seal",
    "corrige o quita el ancla del documento y vuelve a ejecutar scan": "correct or remove the anchor in the document, then run scan again",
    "revisa la frase y vuelve a vincularla (dockeeper link) o quítalo (link --quitar)": "review the sentence and link it again (dockeeper link) or remove the link (link --quitar)",
    "en documentos «publico» usa dockeeper link en vez de anclas en el texto": "in “publico” documents use dockeeper link instead of anchors in the text",
    "describe el código o escribe un ejemplo propio en vez de copiarlo": "describe the code or write your own example instead of copying it",
    "quita la ruta interna del texto publicado": "remove the internal path from the published text",
    # --- scan, check, fix, link ---
    "dockeeper scan · {n} anclas en alcance": "dockeeper scan · {n} anchors in scope",
    "dockeeper scan · 1 ancla en alcance": "dockeeper scan · 1 anchor in scope",
    "dockeeper check · {n} afirmaciones comprobadas": "dockeeper check · {n} claims checked",
    "dockeeper check · 1 afirmación comprobada": "dockeeper check · 1 claim checked",
    "dockeeper fix · 1 cambio en el sello (los documentos no se tocan)": "dockeeper fix · 1 change to the seal (documents are not touched)",
    "dockeeper fix · {n} cambios en el sello (los documentos no se tocan)": "dockeeper fix · {n} changes to the seal (documents are not touched)",
    "recolocada": "relocated",
    "quitada del sello": "removed from seal",
    "aceptada": "accepted",
    "Queda pendiente:": "Still pending:",
    "Resumen tras fix: {resumen}": "Summary after fix: {resumen}",
    "El documento no se ha tocado: el vínculo vive en el sello.": "The document was not touched: the link lives in the seal.",
    # --- audit ---
    "dockeeper audit · {raiz}": "dockeeper audit · {raiz}",
    "Git: {commits} commits · {decisiones} con marcas de decisión (dockeeper why)": "Git: {commits} commits · {decisiones} with decision markers (dockeeper why)",
    "Git: sin historial (why no tendrá de dónde sacar el porqué)": "Git: no history (why has nowhere to take the reasons from)",
    "Totales: {documentos} documentos · {codigo} ficheros de código · {anclas} anclas selladas · {vinculos} vínculos": "Totals: {documentos} documents · {codigo} code files · {anclas} sealed anchors · {vinculos} links",
    "Páginas base:": "Base pages:",
    "falta (plantilla: templates/{pagina}.md)": "missing (template: templates/{pagina}.md)",
    "Documentos:": "Documents:",
    "  ← sin anclas: nada de lo que dice está comprobado": "  ← no anchors: nothing it says is checked",
    "  ← 1 diagrama sin anclas («%% dockeeper:»)": "  ← 1 diagram without anchors (“%% dockeeper:”)",
    "  ← {n} diagramas sin anclas («%% dockeeper:»)": "  ← {n} diagrams without anchors (“%% dockeeper:”)",
    "{anclas} anclas ({selladas} selladas) · {vinculos} vínculos": "{anclas} anchors ({selladas} sealed) · {vinculos} links",
    "Paquetes ({n}): documenta uno cada vez con --solo RUTA": "Packages ({n}): document one at a time with --solo PATH",
    "sin README": "no README",
    "  ← sin documentar": "  ← undocumented",
    "definiciones · {ficheros} ficheros": "definitions · {ficheros} files",
    "Cobertura (definiciones de primer nivel con alguna afirmación anclada):": "Coverage (top-level definitions with at least one anchored claim):",
    "(raíz)": "(root)",
    "Mayores definiciones sin ninguna afirmación anclada:": "Largest definitions with no anchored claim:",
    "{simbolo} ({n} líneas)": "{simbolo} ({n} lines)",
    # --- why ---
    "Sin historial de git: no hay de dónde sacar el porqué. Lo que no consta, se escribe que no consta.": "No git history: there is nowhere to take the reasons from. What is not on record is written as not on record.",
    "Decisiones en el historial ({n}):": "Decisions in the history ({n}):",
    "motivo: {motivo}": "reason: {motivo}",
    "no consta en el historial": "not in the history",
    "alternativas descartadas: {alternativas}": "rejected alternatives: {alternativas}",
    "documentada: sí": "documented: yes",
    "documentada: no": "documented: no",
    "Documentos de decisiones: {documentos} · {entradas} entradas · {sin_motivo} sin motivo escrito": "Decision documents: {documentos} · {entradas} entries · {sin_motivo} with no written reason",
    "No hay documentos de decisiones (plantilla: templates/DECISIONES.md).": "No decision documents (template: templates/DECISIONES.md).",
    # --- review ---
    "el principio": "the beginning",
    "{n} fichero de código": "{n} code file",
    "{n} ficheros de código": "{n} code files",
    "{n} documento": "{n} document",
    "{n} documentos": "{n} documents",
    "dockeeper review · cambios desde {desde} ({base}) · {codigo} · {documentos}": "dockeeper review · changes since {desde} ({base}) · {codigo} · {documentos}",
    "Nada que revisar: la documentación que toca este cambio sigue en verde y no queda código nuevo o cambiado sin documentar.": "Nothing to review: the docs this change touches are still green and no new or changed code is left undocumented.",
    "Afirmaciones que toca el cambio (revisa el texto):": "Claims this change touches (review the text):",
    "Código nuevo o cambiado sin ninguna afirmación (¿se puede añadir a la documentación?):": "New or changed code with no claim (worth adding to the docs?):",
    "nueva": "new",
    "cambiada": "changed",
    " · ya hablan de ese fichero: {documentos}": " · already about that file: {documentos}",
    "{simbolo} ({n} líneas){documentos}": "{simbolo} ({n} lines){documentos}",
    "… y {n} más (--json las da todas)": "… and {n} more (--json lists them all)",
    "Decisiones de estos commits sin documentar (dockeeper why):": "Decisions in these commits not documented yet (dockeeper why):",
    "documenta lo que haga falta con un ancla por afirmación y sella con dockeeper scan": "document what is worth it, one anchor per claim, and seal with dockeeper scan",
    "anótalas en el documento de decisiones (motivo solo si consta)": "add them to the decisions document (a reason only if it is on record)",
}
