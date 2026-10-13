"""El bloque de código que representa un ancla.

- Si la línea anclada cae dentro de una función, clase o método, el bloque es la definición
  **más interior que la contiene, entera** (con sus decoradores).
- Si no, una ventana de ±``ventana`` líneas recortada para empezar y acabar con contenido.
- Por símbolo: la definición con ese nombre (``Clase.metodo`` desambigua); si no hay, la
  declaración ``NOMBRE = …`` menos indentada.

Las definiciones se reconocen con patrones por familia de lenguaje (sin analizadores: cero
dependencias). Antes de buscar cabeceras y llaves se «limpia» el texto: el contenido de
cadenas y comentarios pasa a espacios para que una llave dentro de un texto no cuente.
"""

from __future__ import annotations

import bisect
import posixpath
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from . import huellas as H


# --- Léxico por lenguaje -----------------------------------------------------------------

@dataclass(frozen=True)
class _Lexico:
    comentario: Tuple[str, ...] = ()  # comentarios de línea
    bloque: Optional[Tuple[str, str]] = None  # comentarios de bloque
    multilinea: Tuple[str, ...] = ()  # cadenas que pueden cruzar líneas
    simples: Tuple[str, ...] = ('"', "'")  # cadenas de una línea
    almohadilla_tras_espacio: bool = False  # shell: «#» solo comenta tras espacio o al inicio
    comilla_rust: bool = False  # Rust: «'» abre un carácter o es un lifetime, nunca una cadena


_LENGUAJES: Dict[str, Tuple[str, _Lexico]] = {}


def _registrar(extensiones: str, familia: str, lexico: _Lexico) -> None:
    for ext in extensiones.split():
        _LENGUAJES[ext] = (familia, lexico)


_registrar(".py .pyi", "indentacion", _Lexico(comentario=("#",), multilinea=('"""', "'''")))
_registrar(".rb .rake", "end", _Lexico(comentario=("#",)))
_registrar(".ex .exs .jl", "end", _Lexico(comentario=("#",), multilinea=('"""',)))
_registrar(".lua", "end", _Lexico(comentario=("--",)))
_registrar(".js .jsx .mjs .cjs .ts .tsx .mts .cts .go", "llaves",
           _Lexico(comentario=("//",), bloque=("/*", "*/"), multilinea=("`",)))
_registrar(".java .kt .kts .scala .groovy .swift .dart", "llaves",
           _Lexico(comentario=("//",), bloque=("/*", "*/"), multilinea=('"""',)))
_registrar(".c .h .cc .cpp .cxx .hpp .hh .hxx .m .mm .cs .sol .zig", "llaves",
           _Lexico(comentario=("//",), bloque=("/*", "*/")))
_registrar(".rs", "llaves", _Lexico(comentario=("//",), bloque=("/*", "*/"), comilla_rust=True))
_registrar(".php", "llaves", _Lexico(comentario=("//", "#"), bloque=("/*", "*/")))
_registrar(".sh .bash .zsh", "llaves", _Lexico(comentario=("#",), almohadilla_tras_espacio=True))


def lenguaje(ruta: str) -> Tuple[Optional[str], Optional[_Lexico]]:
    return _LENGUAJES.get(posixpath.splitext(ruta)[1].lower(), (None, None))


# --- Limpieza de cadenas y comentarios ---------------------------------------------------

_CHAR_RUST = re.compile(r"'(?:\\(?:u\{[0-9a-fA-F]+\}|.)|[^\\'\n])'")


def _en_blanco(texto: str) -> str:
    return re.sub(r"[^\n]", " ", texto)


def _fin_cadena(texto: str, j: int, delim: str, multilinea: bool) -> int:
    n = len(texto)
    while j < n:
        c = texto[j]
        if c == "\\":
            j += 2
            continue
        if texto.startswith(delim, j):
            return j + len(delim)
        if c == "\n" and not multilinea:
            return j
        j += 1
    return n


def limpiar(lineas: Sequence[str], lex: _Lexico) -> Tuple[List[str], List[bool]]:
    """Blanquea cadenas y comentarios.

    Devuelve las líneas limpias y, por línea, si empieza dentro de una cadena o comentario
    multilínea (para no cortar un bloque indentado a mitad de un texto).
    """
    texto = "\n".join(lineas)
    fichas = set(lex.comentario) | set(lex.multilinea) | set(lex.simples)
    if lex.bloque:
        fichas.add(lex.bloque[0])
    patron = re.compile("|".join(re.escape(f) for f in sorted(fichas, key=len, reverse=True)))
    salida: List[str] = []
    tramos: List[Tuple[int, int]] = []  # construcciones que pueden cruzar líneas
    i, n = 0, len(texto)
    while i < n:
        m = patron.search(texto, i)
        if not m:
            salida.append(texto[i:])
            break
        j, ficha = m.start(), m.group()
        salida.append(texto[i:j])
        if lex.bloque and ficha == lex.bloque[0]:
            k = texto.find(lex.bloque[1], j + len(ficha))
            fin = n if k < 0 else k + len(lex.bloque[1])
            tramos.append((j, fin))
        elif ficha in lex.comentario:
            if ficha == "#" and lex.almohadilla_tras_espacio and j > 0 and texto[j - 1] not in " \t\n":
                salida.append(ficha)
                i = j + 1
                continue
            k = texto.find("\n", j)
            fin = n if k < 0 else k
        elif ficha in lex.multilinea:
            fin = _fin_cadena(texto, j + len(ficha), ficha, True)
            tramos.append((j, fin))
        elif lex.comilla_rust and ficha == "'":
            mc = _CHAR_RUST.match(texto, j)
            if not mc:  # lifetime: la comilla no abre nada
                salida.append(ficha)
                i = j + 1
                continue
            fin = mc.end()
        else:
            fin = _fin_cadena(texto, j + 1, ficha, False)
        salida.append(_en_blanco(texto[j:fin]))
        i = fin
    limpias = "".join(salida).split("\n")
    inicios = [0] + [m.end() for m in re.finditer("\n", texto)]
    continuacion = [False] * len(limpias)
    for a, b in tramos:
        k = bisect.bisect_right(inicios, a)
        while k < len(inicios) and inicios[k] < b:
            continuacion[k] = True
            k += 1
    return limpias, continuacion


# --- Cabeceras de definición -------------------------------------------------------------

_ID = r"[A-Za-z_$][\w$]*"
_MODS = (r"(?:(?:export|default|declare|public|private|protected|internal|static|final|abstract|override|"
         r"virtual|async|sealed|open|suspend|inline|extern|unsafe|partial|readonly|local|const|mut|"
         r"pub(?:\([^)]*\))?)\s+)*")

_PY = re.compile(rf"^\s*(?:async\s+)?(?:def|class)\s+(?P<nombre>{_ID})")
_END = re.compile(r"^\s*(?:local\s+)?(?:def|defp|defmacro|defmodule|class|module|function|macro|struct)\s+"
                  r"(?:self\.)?(?P<nombre>[A-Za-z_][\w.:]*[?!=]?)")
_CLASE = re.compile(rf"^\s*{_MODS}(?:(?:data|case|enum|abstract|sealed|value|inner)\s+)*"
                    r"(?:class|interface|struct|enum|trait|record|object|protocol|extension|union|impl|"
                    rf"namespace|type)\s+(?:<[^>]*>\s*)?(?P<nombre>{_ID})")
_FUNCION = re.compile(rf"^\s*{_MODS}(?:function\s*\*?|func|fun|fn|def|sub|proc)\s*(?:<[^>]*>\s*)?"
                      rf"(?:\([^)]*\)\s*)?(?:{_ID}\s*\.\s*)*(?P<nombre>{_ID})\s*(?=[<({{]|$)")
_FLECHA = re.compile(rf"^\s*{_MODS}(?:(?:const|let|var)\s+)?(?P<nombre>{_ID})\s*(?::[^=]+)?=\s*(?:async\s+)?"
                     rf"(?:function\b|(?:\([^()]*\)|{_ID})\s*(?::[^=]+)?=>|(?P<abierta>\(\s*$))")
_METODO = re.compile(rf"^\s*{_MODS}(?:(?:get|set|static|async)\s+)*(?:\*\s*)?"
                     r"(?:(?P<tipo>[A-Za-z_$][\w$<>\[\],.?:*&]*(?:\s+[A-Za-z_$][\w$<>\[\],.?:*&]*)*?)\s+[*&]*)?"
                     rf"(?:{_ID}::)*(?P<nombre>~?{_ID})\s*(?:<[^<>()]*>)?\s*\(")
_DECL = re.compile(rf"^(?P<sangria>\s*){_MODS}(?:(?:let|var|val|final|static|readonly)\s+)*"
                   rf"(?:[A-Za-z_$][\w$<>\[\],.?]*\s+)?(?P<nombre>{_ID})\s*(?::[^=]+?)?\s*:?=(?![=>])")

# Palabras que parecen el nombre o el tipo de un método pero son control de flujo o llamadas.
_NO_NOMBRES = {"if", "for", "while", "switch", "catch", "return", "else", "do", "try", "with", "function",
               "func", "fn", "new", "throw", "typeof", "await", "yield", "case", "sizeof", "foreach", "elif",
               "using", "lock", "fixed", "synchronized", "super", "this", "delete", "match", "when", "loop",
               "until", "unless", "assert", "import", "require", "select", "go", "defer", "guard"}
_NO_TIPOS = {"return", "new", "else", "throw", "await", "yield", "case", "typeof", "delete", "echo", "print",
             "goto", "in", "of", "not", "and", "or", "do", "then", "go", "defer", "import", "export", "from",
             "package", "using", "raise", "assert"}

_CONTINUACION = (",", "(", "[", "=", "=>", "+", "-", "*", "/", "&&", "||", "?", ":", ".", "\\", "|", "&", "->", "<")
_MAX_CABECERA = 50


@dataclass(frozen=True)
class Definicion:
    nombre: str
    cabecera: int  # línea de la cabecera (desde 1)
    inicio: int  # incluye decoradores
    fin: int


@dataclass(frozen=True)
class Bloque:
    tipo: str  # "definicion" | "declaracion" | "ventana"
    inicio: int
    fin: int
    nombre: Optional[str]
    cabecera: Optional[int]
    huella: str
    n: int  # líneas con contenido (normalizadas)


def _sangria(texto: str) -> int:
    expandido = texto.expandtabs(8)
    return len(expandido) - len(expandido.lstrip())


_SIGUE = ("{", ">", ")", "]", ".", ":", "|", "&", "?", "=", ",")


def _siguiente_continua(limpias: Sequence[str], i: int) -> bool:
    """¿La siguiente línea con contenido continúa la cabecera? (``{`` en otra línea, ``> {`` de un genérico…)"""
    for j in range(i + 1, min(len(limpias), i + 4)):
        if limpias[j].strip():
            return limpias[j].strip().startswith(_SIGUE)
    return False


def _cerrar_llave(limpias: Sequence[str], i: int, k: int) -> int:
    prof = 0
    for j in range(i, len(limpias)):
        for c in limpias[j][k if j == i else 0:]:
            if c == "{":
                prof += 1
            elif c == "}":
                prof -= 1
                if prof == 0:
                    return j
    return len(limpias) - 1


def _ext_llaves(limpias: Sequence[str], i0: int) -> Tuple[int, bool, int]:
    """Extensión en lenguajes de llaves → (línea final, ¿tiene cuerpo {…}?, línea de la llave)."""
    par = 0
    i = i0
    while i < len(limpias) and i - i0 <= _MAX_CABECERA:
        t = limpias[i]
        for k, c in enumerate(t):
            if c in "([":
                par += 1
            elif c in ")]":
                par = max(0, par - 1)
            elif par == 0 and c == "{":
                return _cerrar_llave(limpias, i, k), True, i
            elif par == 0 and c == ";":
                return i, False, i
        s = t.strip()
        if s and par == 0 and not s.endswith(_CONTINUACION) and not _siguiente_continua(limpias, i):
            return i, False, i
        i += 1
    return i0, False, i0


def _ext_indentacion(limpias: Sequence[str], continuacion: Sequence[bool], i0: int) -> int:
    """Extensión en Python: la firma (hasta cerrar paréntesis) y las líneas más indentadas."""
    sangria = _sangria(limpias[i0])
    par = 0
    i = i0
    while i < len(limpias):
        for c in limpias[i]:
            if c in "([{":
                par += 1
            elif c in ")]}":
                par -= 1
        if par <= 0:
            break
        i += 1
    fin = min(i, len(limpias) - 1)
    for j in range(fin + 1, len(limpias)):
        if continuacion[j]:  # dentro de una cadena multilínea: sigue siendo cuerpo
            fin = j
            continue
        t = limpias[j]
        if not t.strip():
            continue
        if _sangria(t) <= sangria:
            break
        fin = j
    return fin


_UNA_LINEA_END = re.compile(r"(\bend\s*$|,\s*do:|^\s*def\s+[\w?!.]+(\([^)]*\))?\s*=[^=~])")
_MISMA_SANGRIA_END = re.compile(r"^\s*(rescue|ensure|else|elsif|when|in|catch|after)\b")


def _ext_end(limpias: Sequence[str], i0: int) -> int:
    """Extensión en lenguajes con «end»: hasta el «end» con la misma sangría."""
    if _UNA_LINEA_END.search(limpias[i0]):
        return i0
    sangria = _sangria(limpias[i0])
    ultima = i0
    for j in range(i0 + 1, len(limpias)):
        t = limpias[j]
        if not t.strip():
            continue
        s = _sangria(t)
        if s < sangria:
            return ultima
        if s == sangria:
            if re.match(r"^\s*end\b", t):
                return j
            if not _MISMA_SANGRIA_END.match(t):
                return ultima
        ultima = j
    return ultima


def _ext_sentencia(limpias: Sequence[str], i0: int) -> int:
    """Extensión de una sentencia: hasta cerrar paréntesis, corchetes y llaves."""
    par = 0
    for i in range(i0, len(limpias)):
        for c in limpias[i]:
            if c in "([{":
                par += 1
            elif c in ")]}":
                par -= 1
        if par <= 0 and not limpias[i].rstrip().endswith("\\"):
            return i
    return len(limpias) - 1


def _subir_decoradores(lineas: Sequence[str], i: int) -> int:
    while i > 0 and lineas[i - 1].strip().startswith("@"):
        i -= 1
    return i


class Analisis:
    """Definiciones de un fichero de código (se calculan una vez y se reutilizan)."""

    def __init__(self, ruta: str, lineas: List[str]):
        self.ruta = ruta
        self.lineas = lineas
        self.familia, self._lexico = lenguaje(ruta)
        self._limpias: Optional[List[str]] = None
        self._continuacion: Optional[List[bool]] = None
        self._definiciones: Optional[List[Definicion]] = None

    def _limpiar(self) -> None:
        if self._limpias is None:
            if self._lexico is None:
                self._limpias, self._continuacion = list(self.lineas), [False] * len(self.lineas)
            else:
                self._limpias, self._continuacion = limpiar(self.lineas, self._lexico)

    @property
    def limpias(self) -> List[str]:
        self._limpiar()
        return self._limpias

    @property
    def continuacion(self) -> List[bool]:
        self._limpiar()
        return self._continuacion

    @property
    def definiciones(self) -> List[Definicion]:
        if self._definiciones is None:
            self._definiciones = self._buscar_definiciones() if self.familia else []
        return self._definiciones

    def _cabecera(self, t: str) -> Optional[Tuple[str, str]]:
        if self.familia == "indentacion":
            m = _PY.match(t)
            return (m.group("nombre"), "def") if m else None
        if self.familia == "end":
            m = _END.match(t)
            return (re.split(r"[.:]+", m.group("nombre"))[-1], "def") if m else None
        for patron, tipo in ((_CLASE, "def"), (_FUNCION, "def"), (_FLECHA, "flecha"), (_METODO, "metodo")):
            m = patron.match(t)
            if not m:
                continue
            nombre = m.group("nombre")
            if tipo == "metodo":
                tipo_txt = m.group("tipo")
                if nombre.lstrip("~") in _NO_NOMBRES or (tipo_txt and tipo_txt.split()[0] in _NO_TIPOS):
                    return None
            if tipo == "flecha" and m.group("abierta"):
                tipo = "flecha_abierta"
            return nombre, tipo
        return None

    def _buscar_definiciones(self) -> List[Definicion]:
        limpias, continuacion = self.limpias, self.continuacion
        res = []
        for i, t in enumerate(limpias):
            if continuacion[i] or not t.strip():
                continue
            cabecera = self._cabecera(t)
            if cabecera is None:
                continue
            nombre, tipo = cabecera
            if self.familia == "indentacion":
                fin = _ext_indentacion(limpias, continuacion, i)
            elif self.familia == "end":
                fin = _ext_end(limpias, i)
            else:
                fin, cuerpo, llave = _ext_llaves(limpias, i)
                if tipo == "metodo" and not cuerpo:
                    continue  # una llamada o una declaración sin cuerpo, no una definición
                if tipo == "flecha_abierta" and "=>" not in " ".join(limpias[i:(llave if cuerpo else fin) + 1]):
                    continue
            inicio = _subir_decoradores(self.lineas, i)
            res.append(Definicion(nombre, i + 1, inicio + 1, fin + 1))
        return res

    def declaraciones(self, nombre: str) -> List[Definicion]:
        """Declaraciones «NOMBRE = …», de menos a más indentadas."""
        if not self.familia:
            return []
        encontradas = []
        for i, t in enumerate(self.limpias):
            if self.continuacion[i]:
                continue
            m = _DECL.match(t)
            if not m or m.group("nombre") != nombre:
                continue
            fin = _ext_llaves(self.limpias, i)[0] if self.familia == "llaves" else _ext_sentencia(self.limpias, i)
            encontradas.append((_sangria(m.group("sangria")), i, Definicion(nombre, i + 1, i + 1, fin + 1)))
        return [d for _, _, d in sorted(encontradas, key=lambda x: (x[0], x[1]))]


# --- Bloques -----------------------------------------------------------------------------

def _bloque(lineas: Sequence[str], tipo: str, inicio: int, fin: int,
            nombre: Optional[str] = None, cabecera: Optional[int] = None) -> Bloque:
    huella, n = H.huella_de(lineas[inicio - 1:fin])
    return Bloque(tipo, inicio, fin, nombre, cabecera, huella, n)


def _vacio(linea: int) -> Bloque:
    return Bloque("ventana", linea, linea - 1, None, None, H.huella([]), 0)


def bloque_en(an: Analisis, linea: int, ventana: int) -> Bloque:
    """Bloque que representa una ancla por línea."""
    total = len(an.lineas)
    if not 1 <= linea <= total:
        return _vacio(linea)
    dentro = [d for d in an.definiciones if d.inicio <= linea <= d.fin]
    if dentro:
        d = min(dentro, key=lambda d: (d.fin - d.inicio, -d.inicio))  # la más interior
        return _bloque(an.lineas, "definicion", d.inicio, d.fin, d.nombre, d.cabecera)
    a, b = max(1, linea - ventana), min(total, linea + ventana)
    while a <= b and not an.lineas[a - 1].strip():
        a += 1
    while b >= a and not an.lineas[b - 1].strip():
        b -= 1
    return _bloque(an.lineas, "ventana", a, b) if a <= b else _vacio(linea)


def bloque_tramo(lineas: Sequence[str], inicio: int, fin: int) -> Bloque:
    """El tramo guardado de una ventana, tal como está ahora."""
    fin = min(fin, len(lineas))
    if inicio < 1 or inicio > fin:
        return _vacio(inicio)
    return _bloque(lineas, "ventana", inicio, fin)


def _contenida_en(d: Definicion, padres: List[str], defs: List[Definicion]) -> bool:
    if not padres:
        return True
    for p in defs:
        if (p.nombre == padres[-1] and p.inicio <= d.inicio and d.fin <= p.fin
                and (p.inicio, p.fin) != (d.inicio, d.fin) and _contenida_en(p, padres[:-1], defs)):
            return True
    return False


def bloques_de_simbolo(an: Analisis, simbolo: str) -> List[Bloque]:
    """Bloques candidatos para un ancla por símbolo (puede haber varios homónimos)."""
    partes = simbolo.split(".")
    defs = an.definiciones
    candidatas = [d for d in defs if d.nombre == partes[-1] and _contenida_en(d, partes[:-1], defs)]
    tipo = "definicion"
    if not candidatas and len(partes) == 1:
        candidatas, tipo = an.declaraciones(partes[0]), "declaracion"
    return [_bloque(an.lineas, tipo, d.inicio, d.fin, d.nombre, d.cabecera) for d in candidatas]
