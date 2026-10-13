"""Documentación publicada: código copiado y rutas internas.

- ``publicado`` (código público): puede anclar a su código, pero no copiarlo.
- ``publico`` (código privado): ni anclas, ni rutas internas, ni código copiado. Las anclas
  internas las detecta el motor; aquí, las rutas sueltas en el texto y el código copiado.

Código copiado = un bloque de código del documento contiene ``bloque_minimo`` o más líneas
seguidas idénticas (normalizadas) a líneas seguidas de un fichero del repositorio. Solo cuentan
las líneas con algún carácter alfanumérico: una ristra de llaves no es copiar código.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Set, Tuple

from . import huellas as H
from . import markdown as M

if TYPE_CHECKING:  # solo para anotaciones: evita el import circular con motor
    from .motor import Contexto, Item

_TOKEN_RUTA = re.compile(r"[\w.\-]+(?:/[\w.\-]+)+/?")


def lineas_utiles(lineas: Sequence[str]) -> List[Tuple[int, str]]:
    """(línea, texto normalizado) de las líneas con algún carácter alfanumérico."""
    return [(num, t) for num, t in H.indice(lineas) if any(c.isalnum() for c in t)]


class IndiceCopias:
    """Índice de todas las secuencias de ``k`` líneas útiles del código del repositorio."""

    def __init__(self, ctx: "Contexto"):
        self.k = ctx.cfg.bloque_minimo
        self._ctx = ctx
        self._mapa: Optional[Dict[Tuple[str, ...], Tuple[str, int]]] = None

    def _construir(self) -> Dict[Tuple[str, ...], Tuple[str, int]]:
        repo, alcance = self._ctx.repo, self._ctx.alcance
        mapa: Dict[Tuple[str, ...], Tuple[str, int]] = {}
        for fichero in repo.ficheros:
            if repo.es_documento(fichero) or not alcance.codigo_en_alcance(fichero):
                continue
            lineas = repo.lineas(fichero)
            if lineas is None:
                continue
            utiles = lineas_utiles(lineas)
            textos = [t for _, t in utiles]
            for i in range(len(utiles) - self.k + 1):
                mapa.setdefault(tuple(textos[i:i + self.k]), (fichero, utiles[i][0]))
        return mapa

    def buscar(self, lineas: Sequence[str]) -> Optional[Tuple[int, str, int]]:
        """Primera copia en un bloque → (línea dentro del bloque, fichero de origen, línea de origen)."""
        if self._mapa is None:
            self._mapa = self._construir()
        utiles = lineas_utiles(lineas)
        textos = [t for _, t in utiles]
        for i in range(len(utiles) - self.k + 1):
            origen = self._mapa.get(tuple(textos[i:i + self.k]))
            if origen:
                return utiles[i][0], origen[0], origen[1]
        return None


def codigo_copiado(ctx: "Contexto", doc: str, documento: M.Documento) -> List["Item"]:
    from .motor import Item

    if ctx.indice_copias is None:
        ctx.indice_copias = IndiceCopias(ctx)
    items = []
    for bloque in documento.bloques:
        copia = ctx.indice_copias.buscar(bloque.lineas)
        if copia:
            linea, fichero, origen = copia
            items.append(Item("CODIGO_COPIADO", doc, bloque.inicio + linea - 1, tipo="documento",
                              fuente=f"{fichero}:{origen}",
                              detalle=f"el bloque de código copia {ctx.cfg.bloque_minimo}+ líneas seguidas de "
                                      f"{fichero}:{origen}: descríbelo o escribe un ejemplo propio"))
    return items


def _rutas_internas(ctx: "Contexto") -> Set[str]:
    """Rutas de ficheros y carpetas del repositorio con al menos una «/», salvo documentos publicados."""
    if ctx.rutas_internas is None:
        rutas: Set[str] = set()
        for fichero in ctx.repo.ficheros:
            if ctx.repo.es_documento(fichero) and ctx.repo.clase(fichero) != "interno":
                continue
            partes = fichero.split("/")
            for i in range(2, len(partes) + 1):
                rutas.add("/".join(partes[:i]))
        ctx.rutas_internas = rutas
    return ctx.rutas_internas


def rutas_en_texto(ctx: "Contexto", doc: str, lineas: Sequence[str]) -> List["Item"]:
    from .motor import Item

    internas = _rutas_internas(ctx)
    items = []
    for num, linea in enumerate(lineas, 1):
        vistas = []
        for m in _TOKEN_RUTA.finditer(M.sin_anclas(linea)):
            token = m.group()
            while token.startswith("./"):
                token = token[2:]
            token = token.rstrip("./-")
            partes = token.split("/")
            # La ruta entera o cualquier final suyo (p. ej., dentro de una URL al repositorio privado).
            for i in range(len(partes) - 1):
                candidata = "/".join(partes[i:])
                if candidata in internas and candidata not in vistas:
                    vistas.append(candidata)
                    break
        for ruta in vistas:
            items.append(Item("RUTA_INTERNA", doc, num, tipo="documento",
                              detalle=f"menciona la ruta interna «{ruta}» en un documento publicado"))
    return items


def revisar(ctx: "Contexto", doc: str, documento: M.Documento, clase: str) -> List["Item"]:
    items = codigo_copiado(ctx, doc, documento)
    if clase == "publico":
        items.extend(rutas_en_texto(ctx, doc, ctx.repo.lineas(doc) or []))
    return items
