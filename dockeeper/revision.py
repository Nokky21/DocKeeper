"""Revisión de un cambio: qué de la documentación toca y qué queda sin documentar.

Un cambio es lo que hay entre una base y el árbol de trabajo: el último commit (lo normal en un hook
post-commit), una rama entera frente a la principal o lo que aún no se ha commiteado. Responde:

- qué afirmaciones ancladas al código cambiado (o escritas en documentos cambiados) ya no están OK;
- qué definiciones nuevas o cambiadas no tienen ninguna afirmación anclada (lo que se puede añadir);
- qué decisiones de esos commits aún no están en un documento de decisiones.

Es informativa: no escribe nada. La puerta de CI sigue siendo ``check``.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from . import bloques as B
from . import motor, porque
from .config import ErrorDeUso

_ARBOL_VACIO = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # el árbol vacío de git: sin commits previos
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclass
class Cambio:
    ruta: Optional[str] = None  # ruta actual (None si se borró)
    anterior: Optional[str] = None  # ruta en la base (None si es nuevo)
    lineas: Set[int] = field(default_factory=set)  # líneas tocadas en la versión actual


@dataclass
class SinDocumentar:
    simbolo: str
    estado: str  # «nueva» | «cambiada»
    inicio: int
    fin: int
    documentos: List[str]  # documentos que ya hablan de ese fichero

    def a_dict(self) -> dict:
        return {"simbolo": self.simbolo, "estado": self.estado, "inicio": self.inicio, "fin": self.fin,
                "lineas": self.fin - self.inicio + 1, "documentos": self.documentos}


@dataclass
class Revision:
    desde: str
    base: Optional[str]  # None = árbol vacío (no hay commit anterior)
    codigo: List[str]
    documentos: List[str]
    afirmaciones: List[motor.Item]
    sin_documentar: List[SinDocumentar]
    decisiones: List[porque.Decision]

    @property
    def vacia(self) -> bool:
        return not (self.afirmaciones or self.sin_documentar or self.decisiones)


def _git(raiz: Path, *args: str) -> Optional[str]:
    try:
        r = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=raiz, capture_output=True)
    except OSError:
        return None
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def _base(raiz: Path, desde: Optional[str]) -> Optional[str]:
    """Commit base del cambio (punto de bifurcación con HEAD) o None si no hay commit anterior."""
    if _git(raiz, "rev-parse", "--git-dir") is None:
        raise ErrorDeUso("review necesita un repositorio git")
    if _git(raiz, "rev-parse", "--verify", "-q", "HEAD") is None:
        return None  # sin commits: todo es nuevo
    sha = _git(raiz, "rev-parse", "--verify", "-q", (desde or "HEAD~1") + "^{commit}")
    if sha is None:
        if desde is None:
            return None  # primer commit: no hay padre
        raise ErrorDeUso(f"--desde {desde}: no es una revisión de este repositorio")
    comun = _git(raiz, "merge-base", sha.strip(), "HEAD")
    return (comun or sha).strip()


def _ruta(texto: str, prefijo: str) -> Optional[str]:
    texto = texto.rstrip("\t")
    if texto == "/dev/null":
        return None
    if texto.startswith('"') and texto.endswith('"'):
        texto = texto[1:-1]
    return texto[len(prefijo):] if texto.startswith(prefijo) else texto


def _cambios(raiz: Path, base: Optional[str]) -> List[Cambio]:
    """Ficheros cambiados entre la base y el árbol de trabajo (los que git conoce)."""
    salida = _git(raiz, "diff", "--no-color", "--no-ext-diff", "-U0", "-M", base or _ARBOL_VACIO, "--")
    cambios: List[Cambio] = []
    actual: Optional[Cambio] = None
    cabecera = False
    for linea in (salida or "").splitlines():
        if linea.startswith("diff --git "):
            actual, cabecera = Cambio(), True
            cambios.append(actual)
            # Respaldo para renombrados puros, binarios o cambios de modo (sin líneas ---/+++).
            if " b/" in linea:
                actual.ruta = linea.rsplit(" b/", 1)[1]
                actual.anterior = linea[len("diff --git a/"):].rsplit(" b/", 1)[0]
        elif actual is None:
            continue
        elif cabecera and linea.startswith("new file mode"):
            actual.anterior = None
        elif cabecera and linea.startswith("deleted file mode"):
            actual.ruta = None
        elif cabecera and linea.startswith("rename from "):
            actual.anterior = linea[len("rename from "):]
        elif cabecera and linea.startswith("rename to "):
            actual.ruta = linea[len("rename to "):]
        elif cabecera and linea.startswith("--- "):
            actual.anterior = _ruta(linea[4:], "a/")
        elif cabecera and linea.startswith("+++ "):
            actual.ruta = _ruta(linea[4:], "b/")
        else:
            m = _HUNK.match(linea)
            if m:
                cabecera = False  # dentro de un tramo, «--- x» es una línea borrada, no una cabecera
                inicio, n = int(m.group(1)), int(m.group(2) or 1)
                if n:
                    actual.lineas.update(range(inicio, inicio + n))
                else:
                    actual.lineas.add(max(inicio, 1))  # solo se borró: la línea anterior al hueco
    return cambios


def _nombres(an: B.Analisis) -> Dict[B.Definicion, str]:
    """Nombre cualificado de cada definición (Contenedor.nombre), como en las anclas por símbolo."""
    defs = an.definiciones
    nombres = {}
    for d in defs:
        padres = [p for p in defs if p.inicio <= d.inicio and d.fin <= p.fin and (p.inicio, p.fin) != (d.inicio, d.fin)]
        padres.sort(key=lambda p: (p.inicio - p.fin, p.inicio))  # de fuera a dentro
        nombres[d] = ".".join([p.nombre for p in padres] + [d.nombre])
    return nombres


def _tocadas(an: B.Analisis, lineas: Set[int], previas: Set[str]) -> List[Tuple[B.Definicion, str, bool]]:
    """Definiciones tocadas: la más interior de cada línea; si un contenedor es nuevo, el nuevo más externo."""
    nombres = _nombres(an)
    elegidas: Dict[B.Definicion, bool] = {}
    for n in sorted(lineas):
        dentro = sorted((d for d in an.definiciones if d.inicio <= n <= d.fin),
                        key=lambda d: (d.inicio - d.fin, d.inicio))  # de fuera a dentro
        if not dentro:
            continue
        nueva = next((d for d in dentro if nombres[d] not in previas), None)
        elegida = nueva or dentro[-1]
        elegidas[elegida] = nueva is not None
    return [(d, nombres[d], es_nueva) for d, es_nueva in sorted(elegidas.items(), key=lambda x: x[0].inicio)]


def _tramos(ctx: motor.Contexto, ficheros: Set[str]) -> Tuple[Dict[str, List[Tuple[int, int]]], Dict[str, Set[str]]]:
    """Tramos que cubren hoy las afirmaciones (selladas o aún sin sellar) y documentos que hablan de cada fichero."""
    tramos: Dict[str, List[Tuple[int, int]]] = {}
    docs: Dict[str, Set[str]] = {}
    for doc in ctx.documentos():
        for a in ctx.documento(doc).anclas:
            if a.fichero not in ficheros or (doc, a.texto) in ctx.sello.anclas:
                continue
            docs.setdefault(a.fichero, set()).add(doc)
            b, error, _ = motor.resolver(ctx, a.fichero, a.linea, a.simbolo)
            if b is not None:
                tramos.setdefault(a.fichero, []).append((b.inicio, b.fin))
    for e in ctx.sello.todas():
        if e.fichero not in ficheros:
            continue
        docs.setdefault(e.fichero, set()).add(e.doc)
        estado, _, nueva, vista = motor.verificar_codigo(ctx, e)
        if nueva:
            tramo = (nueva["inicio"], nueva["fin"])
        elif vista:
            tramo = (vista["inicio"], vista["fin"])
        elif estado == "OK":
            tramo = (e.inicio, e.fin)
        else:
            continue  # desaparecido o símbolo que ya no está: no cubre nada hoy
        tramos.setdefault(e.fichero, []).append(tramo)
    return tramos, docs


def _literal(ruta: str) -> str:
    """La ruta como patrón que solo casa consigo misma (``[id].ts`` es una ruta, no un comodín)."""
    return "".join(f"[{c}]" if c in "*?[" else c for c in ruta)


def _afirmaciones(raiz: Path, codigo: List[str], documentos: List[str], sin: List[str],
                  conocidas: Set[str]) -> List[motor.Item]:
    """Lo que `check` diría de las afirmaciones que tocan el cambio (solo lo que no está OK)."""
    items: List[motor.Item] = []
    vistos = set()
    pasadas = [(codigo, ("ancla", "vinculo")), (documentos, None)]
    for rutas, tipos in pasadas:
        rutas = [_literal(r) for r in rutas if r in conocidas]
        if not rutas:
            continue
        res = motor.comprobar(motor.Contexto(raiz, rutas, sin))
        for item in res.items:
            if item.estado in ("OK", "NADA_COMPROBADO") or (tipos and item.tipo not in tipos):
                continue
            clave = (item.estado, item.doc, item.linea_doc, item.ancla)
            if clave not in vistos:
                vistos.add(clave)
                items.append(item)
    return items


def revisar(ctx: motor.Contexto, desde: Optional[str], sin: List[str]) -> Revision:
    raiz, repo, alcance = ctx.cfg.raiz, ctx.repo, ctx.alcance
    base = _base(raiz, desde)
    cambios = _cambios(raiz, base)

    codigo: List[str] = []
    documentos: List[str] = []
    for c in cambios:
        for ruta in dict.fromkeys(r for r in (c.ruta, c.anterior) if r):  # renombrado: las dos rutas
            if repo.es_documento(ruta):
                if alcance.doc_en_alcance(ruta) and ruta not in documentos:
                    documentos.append(ruta)
            elif alcance.codigo_en_alcance(ruta) and ruta not in codigo:
                codigo.append(ruta)

    conocidas = set(repo.ficheros)
    for e in ctx.sello.todas():
        conocidas.update((e.fichero, e.doc))
    afirmaciones = _afirmaciones(raiz, codigo, documentos, sin, conocidas)

    tramos, docs = _tramos(ctx, set(codigo))
    sin_documentar: List[SinDocumentar] = []
    for c in cambios:
        if not c.ruta or c.ruta not in codigo or not c.lineas:
            continue
        an = repo.analisis(c.ruta)
        if an is None or not an.familia:
            continue
        previas: Set[str] = set()
        if c.anterior and base:
            texto = _git(raiz, "show", f"{base}:{c.anterior}")
            if texto is not None:
                previas = set(_nombres(B.Analisis(c.anterior, texto.splitlines())).values())
        for d, nombre, nueva in _tocadas(an, c.lineas, previas):
            if any(ini <= d.fin and d.inicio <= fin for ini, fin in tramos.get(c.ruta, [])):
                continue  # ya hay una afirmación sobre ella: si dejó de ser cierta, sale en afirmaciones
            sin_documentar.append(SinDocumentar(f"{c.ruta}#{nombre}", "nueva" if nueva else "cambiada",
                                                d.inicio, d.fin, sorted(docs.get(c.ruta, ()))))

    decisiones = porque.historial(ctx, f"{base}..HEAD" if base else "HEAD") or []
    if decisiones:
        porque.marcar_documentadas(ctx, decisiones)
    return Revision(desde=desde or "HEAD~1", base=base, codigo=sorted(codigo), documentos=sorted(documentos),
                    afirmaciones=afirmaciones, sin_documentar=sin_documentar,
                    decisiones=[d for d in decisiones if not d.documentada])
