"""Motor: sellar (scan), comprobar (check) y arreglar (fix).

Veredictos de un ancla sellada:
- OK: el bloque está donde estaba y su huella coincide.
- MOVED: la misma huella aparece en otra posición → ``fix`` la recoloca sin intervención.
- CHANGED: la huella ya no aparece en el fichero → lo tiene que mirar una persona.
- DESAPARECIDO: el fichero ya no existe.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from . import bloques as B
from . import huellas as H
from . import markdown as M
from .alcance import Alcance
from .config import cargar
from .repo import Repo
from .sello import Entrada, Sello

# Veredictos que hacen fallar la orden (código de salida 1).
FALLOS = {
    "CHANGED", "DESAPARECIDO", "SIN_SELLAR", "ANCLA_MAL_ESCRITA", "NADA_COMPROBADO",
    "NO_EXISTE", "SIN_SIMBOLO", "FUERA_DE_RANGO", "SIN_CONTENIDO",
}
_GRAVEDAD = {"OK": 0, "MOVED": 1, "VINCULO_SUELTO": 2, "CHANGED": 3, "DESAPARECIDO": 4}


@dataclass
class Item:
    estado: str
    doc: Optional[str] = None
    linea_doc: Optional[int] = None
    ancla: Optional[str] = None
    tipo: str = "ancla"  # ancla | vinculo | documento | repo
    detalle: str = ""
    bloque: Optional[dict] = None
    avisos: List[str] = field(default_factory=list)
    fuente: Optional[str] = None
    accion: Optional[str] = None
    entrada: Optional[Entrada] = field(default=None, repr=False)
    nueva: Optional[dict] = field(default=None, repr=False)

    @property
    def falla(self) -> bool:
        return self.estado in FALLOS

    def a_dict(self) -> dict:
        d = {"estado": self.estado, "tipo": self.tipo}
        for clave in ("doc", "linea_doc", "ancla", "detalle", "bloque", "avisos", "fuente", "accion"):
            valor = getattr(self, clave)
            if valor not in (None, "", []):
                d[clave] = valor
        return d


@dataclass
class Resultado:
    items: List[Item]
    examinados: int = 0
    fuera_de_alcance: int = 0

    @property
    def codigo(self) -> int:
        return 1 if any(i.falla for i in self.items) else 0

    def resumen(self) -> Dict[str, int]:
        return dict(Counter(i.estado for i in self.items))


class Contexto:
    """Todo lo que necesita una orden: configuración, repositorio, sello y alcance."""

    def __init__(self, raiz: Path, solo: Iterable[str] = (), sin: Iterable[str] = ()):
        self.cfg = cargar(raiz)
        self.repo = Repo(self.cfg)
        self.sello = Sello.cargar(raiz)
        conocidas = set(self.repo.ficheros)
        for e in self.sello.todas():
            conocidas.update((e.fichero, e.doc))
        self.alcance = Alcance(list(solo), list(self.cfg.sin) + list(sin), conocidas, self.repo.es_documento)
        self._docs: Dict[str, M.Documento] = {}

    def documento(self, ruta: str) -> M.Documento:
        if ruta not in self._docs:
            self._docs[ruta] = M.analizar(ruta, self.repo.lineas(ruta) or [])
        return self._docs[ruta]

    def documentos(self) -> List[str]:
        return [d for d in self.repo.documentos() if self.alcance.doc_en_alcance(d)]


# --- Bloques y vistas previas ------------------------------------------------------------

def vista(repo: Repo, fichero: str, b: B.Bloque, linea: Optional[int] = None) -> dict:
    """Lo que hay que enseñar para confirmar un ancla: dónde quedó y qué líneas abarca."""
    lineas = repo.lineas(fichero) or []

    def texto(n: int) -> str:
        return lineas[n - 1].rstrip()[:120] if 1 <= n <= len(lineas) else ""

    d = {"fichero": fichero, "tipo": b.tipo, "inicio": b.inicio, "fin": b.fin,
         "primera": texto(b.inicio), "ultima": texto(b.fin)}
    if b.nombre:
        d["nombre"] = b.nombre
    if linea is not None:
        d["linea"] = linea
        d["anclada"] = texto(linea)
    return d


def resolver(ctx: Contexto, fichero: str, linea: Optional[int], simbolo: Optional[str]
             ) -> Tuple[Optional[B.Bloque], Optional[Tuple[str, str]], List[str]]:
    """Calcula el bloque de un ancla → (bloque, (veredicto, motivo) si falla, avisos)."""
    if not ctx.repo.existe(fichero):
        return None, ("NO_EXISTE", f"{fichero} no existe"), []
    an = ctx.repo.analisis(fichero)
    if an is None:
        return None, ("NO_EXISTE", f"{fichero} no es un fichero de texto legible"), []
    avisos: List[str] = []
    if simbolo:
        candidatos = B.bloques_de_simbolo(an, simbolo)
        if not candidatos:
            if an.familia is None:
                return None, ("SIN_SIMBOLO", f"no se reconocen definiciones en ficheros como {fichero}: "
                                             "ancla por línea"), []
            return None, ("SIN_SIMBOLO", f"no se encuentra la definición de «{simbolo}» en {fichero}"), []
        if len(candidatos) > 1:
            avisos.append(f"«{simbolo}» aparece {len(candidatos)} veces; se usa la de la línea "
                          f"{candidatos[0].cabecera}. Precisa con Contenedor.{simbolo.split('.')[-1]}")
        return candidatos[0], None, avisos
    if linea > len(an.lineas):
        return None, ("FUERA_DE_RANGO", f"{fichero} tiene {len(an.lineas)} líneas"), []
    b = B.bloque_en(an, linea, ctx.cfg.ventana)
    if b.n == 0:
        return None, ("SIN_CONTENIDO", f"no hay código alrededor de {fichero}:{linea}"), []
    if b.tipo == "ventana":
        avisos.append(f"ninguna definición contiene la línea: se usa una ventana de ±{ctx.cfg.ventana} líneas")
    if not an.lineas[linea - 1].strip():
        avisos.append("la línea anclada está vacía")
    return b, None, avisos


def _entrada(doc: str, ancla: str, fichero: str, linea: Optional[int], simbolo: Optional[str],
             b: B.Bloque) -> Entrada:
    return Entrada(doc=doc, ancla=ancla, fichero=fichero, tipo=b.tipo, inicio=b.inicio, fin=b.fin,
                   n=b.n, huella=b.huella, simbolo=simbolo, linea=None if simbolo else linea)


def _resellar(e: Entrada, b: B.Bloque) -> None:
    e.tipo, e.inicio, e.fin, e.n, e.huella = b.tipo, b.inicio, b.fin, b.n, b.huella


def _problemas(doc: str, documento: M.Documento) -> List[Item]:
    return [Item("ANCLA_MAL_ESCRITA", doc, p.linea_doc, p.texto, detalle=p.motivo) for p in documento.problemas]


# --- scan --------------------------------------------------------------------------------

def escanear(ctx: Contexto, resellar: bool = False) -> Resultado:
    """Sella las anclas nuevas (o todas con ``resellar``), enseña su bloque y poda las que ya no están."""
    res = Resultado([])
    sello, alcance = ctx.sello, ctx.alcance
    cambios = False
    for doc in ctx.documentos():
        documento = ctx.documento(doc)
        res.items.extend(_problemas(doc, documento))
        vistas = set()
        for a in documento.anclas:
            if not alcance.codigo_en_alcance(a.fichero):
                res.fuera_de_alcance += 1
                continue
            if a.texto in vistas:
                continue
            vistas.add(a.texto)
            res.examinados += 1
            item = _sellar_ancla(ctx, doc, a, resellar)
            cambios = cambios or item.estado in ("NUEVA", "RESELLADA")
            res.items.append(item)
        for clave, e in list(sello.anclas.items()):
            if clave[0] == doc and clave[1] not in vistas and alcance.codigo_en_alcance(e.fichero):
                del sello.anclas[clave]
                cambios = True
                res.items.append(Item("PODADA", doc, None, e.ancla, detalle="ya no está en el documento"))
    for clave, e in list(sello.anclas.items()):
        if not ctx.repo.existe(e.doc) and alcance.doc_en_alcance(e.doc) and alcance.codigo_en_alcance(e.fichero):
            del sello.anclas[clave]
            cambios = True
            res.items.append(Item("PODADA", e.doc, None, e.ancla, detalle="el documento ya no existe"))
    if cambios:
        sello.guardar()
    return res


def _sellar_ancla(ctx: Contexto, doc: str, a: M.Ancla, resellar: bool) -> Item:
    previa = ctx.sello.anclas.get((doc, a.texto))
    if previa is not None and not resellar:
        return Item("SELLADA", doc, a.linea_doc, a.texto,
                    detalle=f"sellada en {previa.fichero}:{previa.inicio}-{previa.fin}")
    # Al resellar, la posición real es la del sello (fix pudo recolocarla), no la escrita.
    linea = previa.linea if previa is not None and previa.linea else a.linea
    b, error, avisos = resolver(ctx, a.fichero, linea, a.simbolo)
    if error:
        return Item(error[0], doc, a.linea_doc, a.texto, detalle=error[1])
    ctx.sello.anclas[(doc, a.texto)] = _entrada(doc, a.texto, a.fichero, linea, a.simbolo, b)
    return Item("RESELLADA" if previa else "NUEVA", doc, a.linea_doc, a.texto,
                bloque=vista(ctx.repo, a.fichero, b, linea), avisos=avisos)


# --- check -------------------------------------------------------------------------------

def comprobar(ctx: Contexto) -> Resultado:
    res = Resultado([])
    alcance, sello = ctx.alcance, ctx.sello
    comprobadas = set()
    for doc in ctx.documentos():
        documento = ctx.documento(doc)
        res.items.extend(_problemas(doc, documento))
        vistas = set()
        for a in documento.anclas:
            if not alcance.codigo_en_alcance(a.fichero):
                res.fuera_de_alcance += 1
                continue
            if a.texto in vistas:
                continue
            vistas.add(a.texto)
            res.examinados += 1
            e = sello.anclas.get((doc, a.texto))
            if e is None:
                res.items.append(Item("SIN_SELLAR", doc, a.linea_doc, a.texto,
                                      detalle="ancla sin sellar: dockeeper scan"))
                continue
            comprobadas.add((doc, a.texto))
            res.items.append(_verificar_ancla(ctx, e, a.linea_doc))
    for clave, e in sello.anclas.items():
        if clave not in comprobadas and alcance.doc_en_alcance(e.doc) and alcance.codigo_en_alcance(e.fichero):
            res.items.append(Item("HUERFANA", e.doc, None, e.ancla, entrada=e,
                                  detalle="el documento ya no contiene esta ancla: fix la quita del sello"))
    if res.examinados == 0:
        res.items.append(Item("NADA_COMPROBADO", tipo="repo",
                              detalle="no hay ninguna afirmación que comprobar en este alcance"))
    return res


def _verificar_ancla(ctx: Contexto, e: Entrada, linea_doc: Optional[int]) -> Item:
    estado, detalle, nueva, bloque = verificar_codigo(ctx, e)
    return Item(estado, e.doc, linea_doc, e.ancla, detalle=detalle, bloque=bloque, entrada=e, nueva=nueva)


def verificar_codigo(ctx: Contexto, e: Entrada) -> Tuple[str, str, Optional[dict], Optional[dict]]:
    """Compara el bloque sellado con el código actual → (veredicto, detalle, posición nueva, vista)."""
    an = ctx.repo.analisis(e.fichero) if ctx.repo.existe(e.fichero) else None
    if an is None:
        return "DESAPARECIDO", f"{e.fichero} ya no existe", None, None
    if e.simbolo:
        candidatos = B.bloques_de_simbolo(an, e.simbolo)
        for b in candidatos:
            if b.huella == e.huella:
                if (b.inicio, b.fin) == (e.inicio, e.fin):
                    return "OK", "", None, None
                return ("MOVED", f"«{e.simbolo}» pasó de {e.inicio}-{e.fin} a {b.inicio}-{b.fin}",
                        {"inicio": b.inicio, "fin": b.fin}, None)
        if not candidatos:
            return "CHANGED", f"ya no se encuentra «{e.simbolo}» en {e.fichero}", None, None
        b = candidatos[0]
        return ("CHANGED", f"el contenido de «{e.simbolo}» cambió ({e.fichero}:{b.inicio}-{b.fin})",
                None, vista(ctx.repo, e.fichero, b))
    if e.tipo == "ventana":
        b = B.bloque_tramo(an.lineas, e.inicio, e.fin)
    else:
        b = B.bloque_en(an, e.linea, ctx.cfg.ventana)
    if b.huella == e.huella and b.n == e.n:
        if (b.inicio, b.fin) == (e.inicio, e.fin):
            return "OK", "", None, None
        return ("MOVED", f"el bloque pasó de {e.inicio}-{e.fin} a {b.inicio}-{b.fin}",
                {"inicio": b.inicio, "fin": b.fin, "linea": e.linea + b.inicio - e.inicio}, None)
    tramos = H.buscar(an.lineas, e.huella, e.n)
    if tramos:
        ini, fin = min(tramos, key=lambda t: (abs(t[0] - e.inicio), t[0]))
        linea = min(max(ini + (e.linea - e.inicio), ini), fin)
        return ("MOVED", f"el bloque pasó de {e.inicio}-{e.fin} a {ini}-{fin}",
                {"inicio": ini, "fin": fin, "linea": linea}, None)
    return ("CHANGED", f"el bloque {e.fichero}:{e.inicio}-{e.fin} cambió", None,
            vista(ctx.repo, e.fichero, b, e.linea) if b.n else None)


# --- fix ---------------------------------------------------------------------------------

def arreglar(ctx: Contexto, aceptar: bool = False) -> Tuple[List[Item], Resultado]:
    """Recoloca los MOVED y quita las huérfanas; con ``aceptar``, resella los CHANGED revisados.

    Solo escribe el sello: nunca toca un documento.
    """
    hechos: List[Item] = []
    for item in comprobar(ctx).items:
        e = item.entrada
        if e is None:
            continue
        if item.estado == "MOVED" and item.nueva:
            for clave, valor in item.nueva.items():
                setattr(e, clave, valor)
            item.accion = "recolocada"
            hechos.append(item)
        elif item.estado == "HUERFANA":
            ctx.sello.quitar(e)
            item.accion = "quitada del sello"
            hechos.append(item)
        elif item.estado == "CHANGED" and aceptar:
            b, error, avisos = resolver(ctx, e.fichero, e.linea, e.simbolo)
            if error:
                item.detalle += f" (no se puede aceptar: {error[1]})"
                continue
            for clave, valor in (item.nueva or {}).items():
                if clave == "linea_doc":
                    e.linea_doc = valor
            _resellar(e, b)
            item.accion = "aceptada"
            item.bloque = vista(ctx.repo, e.fichero, b, e.linea)
            item.avisos = avisos
            hechos.append(item)
    if hechos:
        ctx.sello.guardar()
    return hechos, comprobar(ctx)
