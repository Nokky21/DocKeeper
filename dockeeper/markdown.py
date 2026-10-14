"""Lectura de documentos Markdown: anclas, bloques de código y líneas fuera de código.

Se saltan los bloques de código (``` y ~~~), el código en línea (acentos graves) y los
comentarios HTML que no son de dockeeper. Si no, un documento que *enseña* la sintaxis se
llenaría de anclas falsas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from . import textos
from .rutas import normalizar_ruta

_VALLA = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_TROZO = r"[^\[\]\s|#:<>\"'`]"
# Rutas dinámicas de los frameworks web: app/[id]/page.tsx, [...slug].astro, [[...slug]].
_RUTA = rf"(?:{_TROZO}|\[{_TROZO}+\]|\[\[{_TROZO}+\]\])+"
_SIMBOLO = r"[A-Za-z_$][\w$.]*"
_ANCLA = re.compile(rf"\[\[({_RUTA})(?::(\d+)|#({_SIMBOLO}))\]\]")
_TOKEN = re.compile(rf"^({_RUTA})(?::(\d+)|#({_SIMBOLO}))$")
_COMENTARIO_DK = re.compile(r"^<!--\s*dockeeper\s*:(.*?)-->$", re.I | re.S)
_APERTURA_DK = re.compile(r"^<!--\s*dockeeper\s*:", re.I)
_DK_EN_LINEA = re.compile(r"<!--\s*dockeeper\s*:.*?-->", re.I)
# En un diagrama Mermaid, «%%» es un comentario: ni Obsidian ni GitHub lo enseñan.
_MERMAID_DK = re.compile(r"^\s*%%\s*dockeeper\s*:(.*)$", re.I)


@dataclass(frozen=True)
class Ancla:
    doc: str
    linea_doc: int
    texto: str  # forma canónica: «ruta:N» o «ruta#símbolo» (clave en el sello)
    fichero: str
    linea: Optional[int]
    simbolo: Optional[str]
    oculta: bool


@dataclass(frozen=True)
class Problema:
    doc: str
    linea_doc: int
    texto: str
    motivo: str


@dataclass
class BloqueCodigo:
    inicio: int  # línea del documento donde empieza el contenido (tras la valla)
    lineas: List[str] = field(default_factory=list)
    info: str = ""

    @property
    def diagrama(self) -> bool:
        return self.info.lower().split()[:1] == ["mermaid"]

    @property
    def anclado(self) -> bool:
        """Un diagrama está anclado si alguna de sus líneas es «%% dockeeper: …»."""
        return any(_MERMAID_DK.match(linea) for linea in self.lineas)


@dataclass
class Documento:
    anclas: List[Ancla]
    problemas: List[Problema]
    bloques: List[BloqueCodigo]
    en_codigo: List[bool]  # por línea: ¿está dentro de un bloque de código (vallas incluidas)?


def leer_ancla(token: str) -> Tuple[str, Optional[int], Optional[str], str]:
    """Interpreta «ruta:N» o «ruta#símbolo» → (fichero, línea, símbolo, texto canónico).

    Lanza ValueError con el motivo si no es un ancla válida.
    """
    m = _TOKEN.match(token.strip())
    if not m:
        raise ValueError(textos.t("«{token}» no es un ancla (usa ruta:línea o ruta#símbolo)", token=token))
    return _validar(m.group(1), m.group(2), m.group(3))


def _validar(ruta: str, num: Optional[str], simbolo: Optional[str]) -> Tuple[str, Optional[int], Optional[str], str]:
    fichero = normalizar_ruta(ruta)
    if fichero is None:
        raise ValueError(textos.t("«{ruta}» es absoluta o sale del repositorio", ruta=ruta))
    if num is not None:
        linea = int(num)
        if linea < 1:
            raise ValueError(textos.t("las líneas empiezan en 1"))
        return fichero, linea, None, f"{fichero}:{linea}"
    if any(not parte for parte in simbolo.split(".")):
        raise ValueError(textos.t("«{simbolo}» no es un símbolo válido", simbolo=simbolo))
    return fichero, None, simbolo, f"{fichero}#{simbolo}"


def sin_codigo_en_linea(texto: str) -> str:
    """Sustituye por espacios el código en línea (`…`, ``…``), respetando la longitud."""
    tiradas = [(m.start(), m.end()) for m in re.finditer(r"`+", texto)]
    res = list(texto)
    i = 0
    while i < len(tiradas):
        ini, fin = tiradas[i]
        largo = fin - ini
        cierre = next((j for j in range(i + 1, len(tiradas)) if tiradas[j][1] - tiradas[j][0] == largo), None)
        if cierre is None:
            i += 1
            continue
        for p in range(ini, tiradas[cierre][1]):
            res[p] = " "
        i = cierre + 1
    return "".join(res)


def sin_anclas(linea: str) -> str:
    """La línea sin anclas visibles ni comentarios dockeeper, «%%» incluidos (para buscar rutas sueltas)."""
    if _MERMAID_DK.match(linea):
        return " " * len(linea)
    return _ANCLA.sub(" ", _DK_EN_LINEA.sub(" ", linea))


def analizar(doc: str, lineas: List[str]) -> Documento:
    anclas: List[Ancla] = []
    problemas: List[Problema] = []
    bloques: List[BloqueCodigo] = []
    en_codigo: List[bool] = []
    valla: Optional[Tuple[str, int]] = None
    actual: Optional[BloqueCodigo] = None
    en_comentario = False

    for num, linea in enumerate(lineas, 1):
        if valla is not None:
            en_codigo.append(True)
            if re.match(rf"^ {{0,3}}{re.escape(valla[0])}{{{valla[1]},}}\s*$", linea):
                bloques.append(actual)
                valla, actual = None, None
            else:
                actual.lineas.append(linea)
                m = _MERMAID_DK.match(linea) if actual.diagrama else None
                if m:  # la única forma de ancla dentro de un bloque: explícita y solo en diagramas
                    _fichas(doc, num, m.group(1), linea.strip(), anclas, problemas)
            continue
        m = _VALLA.match(linea)
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            valla = (m.group(1)[0], len(m.group(1)))
            actual = BloqueCodigo(num + 1, [], m.group(2).strip())
            en_codigo.append(True)
            continue
        en_codigo.append(False)
        visible, en_comentario = _visible(doc, num, linea, en_comentario, anclas, problemas)
        for a in _ANCLA.finditer(visible):
            ruta = a.group(1)
            if "." not in ruta and "/" not in ruta:
                continue  # wikilink de Obsidian u otro uso de [[...]]: no es un ancla
            _anadir(doc, num, a.group(0), ruta, a.group(2), a.group(3), False, anclas, problemas)

    if actual is not None:  # valla sin cerrar: el bloque llega hasta el final
        bloques.append(actual)
    return Documento(anclas, problemas, bloques, en_codigo)


def _visible(doc, num, linea, en_comentario, anclas, problemas) -> Tuple[str, bool]:
    """Texto de la línea sin código en línea ni comentarios HTML; recoge las anclas ocultas."""
    texto = sin_codigo_en_linea(linea)
    trozos = []
    i = 0
    if en_comentario:
        k = texto.find("-->")
        if k < 0:
            return " " * len(texto), True
        trozos.append(" " * (k + 3))
        i = k + 3
    while True:
        k = texto.find("<!--", i)
        if k < 0:
            trozos.append(texto[i:])
            return "".join(trozos), False
        trozos.append(texto[i:k])
        fin = texto.find("-->", k + 4)
        if fin < 0:
            if _APERTURA_DK.match(texto[k:]):
                problemas.append(Problema(doc, num, texto[k:].strip(),
                                           textos.t("el comentario dockeeper debe cerrarse en la misma línea")))
            trozos.append(" " * (len(texto) - k))
            return "".join(trozos), True
        comentario = texto[k:fin + 3]
        m = _COMENTARIO_DK.match(comentario)
        if m:
            _fichas(doc, num, m.group(1), comentario, anclas, problemas)
        trozos.append(" " * len(comentario))
        i = fin + 3


def _fichas(doc, num, contenido, original, anclas, problemas) -> None:
    """Anclas ocultas de un comentario dockeeper (HTML, o «%%» en un diagrama Mermaid)."""
    fichas = [f for f in re.split(r"[\s,]+", contenido.strip()) if f]
    if not fichas:
        problemas.append(Problema(doc, num, original, textos.t("comentario dockeeper sin anclas")))
    for ficha in fichas:
        t = _TOKEN.match(ficha)
        if not t:
            problemas.append(Problema(doc, num, ficha, textos.t("no es un ancla (usa ruta:línea o ruta#símbolo)")))
            continue
        _anadir(doc, num, ficha, t.group(1), t.group(2), t.group(3), True, anclas, problemas)


def _anadir(doc, num, original, ruta, linea, simbolo, oculta, anclas, problemas) -> None:
    try:
        fichero, n, sim, texto = _validar(ruta, linea, simbolo)
    except ValueError as e:
        problemas.append(Problema(doc, num, original, str(e)))
        return
    anclas.append(Ancla(doc, num, texto, fichero, n, sim, oculta))
