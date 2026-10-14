"""El porqué: decisiones del historial de git y entradas de decisión sin motivo escrito.

Lo que no está en el historial no se inventa: un commit con «Decision:» pero sin motivo sale
con el motivo vacío («no consta»), y así debe escribirse en la documentación.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

from . import rutas as R

if TYPE_CHECKING:
    from .motor import Contexto

_MARCAS = [
    ("decision", re.compile(r"^\s*[-*]?\s*(?:decisi[oó]n|decided)\s*:\s*(.*)$", re.I)),
    ("motivo", re.compile(r"^\s*[-*]?\s*(?:motivo|why|por\s*qu[eé]|porque|reason|rationale)\s*:\s*(.*)$", re.I)),
    ("alternativas", re.compile(r"^\s*[-*]?\s*(?:alternativas?(?:\s+descartadas?)?|descartad[oa]s?|"
                                r"alternatives?(?:\s+considered)?|rejected)\s*:\s*(.*)$", re.I)),
]
_ADR = re.compile(r"\bADR(?:[-\s#]?\d+)?\b")

# En los documentos de decisiones: campo o sección que contiene el motivo.
_CAMPO_MOTIVO = re.compile(r"^(?:[-*+]\s+)?(motivo|por\s*qu[eé]|porqu[eé]|why|reason|rationale|contexto|context)"
                           r"\s*:\s*(.*)$", re.I)
_SECCION_MOTIVO = re.compile(r"^(motivo|por\s*qu[eé]|porqu[eé]|why|reason|rationale|contexto|context)\b", re.I)
_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_RELLENO = {"", "?", "...", "…", "todo", "tbd", "pendiente", "-"}


@dataclass
class Decision:
    commit: str
    fecha: str
    autor: str
    asunto: str
    decision: str
    motivo: Optional[str]
    alternativas: Optional[str]
    adr: bool
    ficheros: List[str] = field(default_factory=list)
    documentada: bool = False

    def a_dict(self) -> dict:
        return {"commit": self.commit, "fecha": self.fecha, "autor": self.autor, "asunto": self.asunto,
                "decision": self.decision, "motivo": self.motivo, "alternativas": self.alternativas,
                "adr": self.adr, "documentada": self.documentada, "ficheros": self.ficheros}


@dataclass
class EntradaDecision:
    doc: str
    linea: int
    titulo: str
    con_motivo: bool

    def a_dict(self) -> dict:
        return {"doc": self.doc, "linea": self.linea, "titulo": self.titulo, "con_motivo": self.con_motivo}


def _extraer(asunto: str, cuerpo: str) -> Dict[str, str]:
    campos: Dict[str, str] = {}
    actual = None
    for linea in [asunto, *cuerpo.splitlines()]:
        for clave, patron in _MARCAS:
            m = patron.match(linea)
            if m:
                actual = clave
                campos[clave] = m.group(1).strip()
                break
        else:
            if not linea.strip():
                actual = None
            elif actual:  # continuación del campo anterior
                campos[actual] = (campos[actual] + " " + linea.strip()).strip()
    return campos


def historial(ctx: "Contexto", rango: Optional[str] = None) -> Optional[List[Decision]]:
    """Commits con marcas de decisión, del más reciente al más antiguo. None si no hay historial.

    ``rango`` (p. ej. ``base..HEAD``) limita el historial a esos commits.
    """
    formato = "%x1e%H%x1f%ad%x1f%an%x1f%s%x1f%b%x1f"
    try:
        r = subprocess.run(["git", "log", "--no-color", "--date=short", "--name-only", f"--format={formato}",
                            *([rango] if rango else []), "--"],
                           cwd=ctx.cfg.raiz, capture_output=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    decisiones = []
    for registro in r.stdout.decode("utf-8", "replace").split("\x1e")[1:]:
        partes = registro.split("\x1f")
        if len(partes) < 6:
            continue
        sha, fecha, autor, asunto, cuerpo, resto = partes[:6]
        ficheros = [f.strip() for f in resto.strip().splitlines() if f.strip()]
        campos = _extraer(asunto, cuerpo)
        adr = bool(_ADR.search(asunto + "\n" + cuerpo))
        if not campos and not adr:
            continue
        if not _en_alcance(ctx, ficheros):
            continue
        decisiones.append(Decision(
            commit=sha[:10], fecha=fecha, autor=autor, asunto=asunto.strip(),
            decision=campos.get("decision") or asunto.strip(),
            motivo=campos.get("motivo") or None, alternativas=campos.get("alternativas") or None,
            adr=adr, ficheros=ficheros))
    return decisiones


def _en_alcance(ctx: "Contexto", ficheros: List[str]) -> bool:
    """Un commit entra si toca algún fichero que case con --solo (si lo hay) y no esté descartado."""
    alcance = ctx.alcance
    if not (alcance.solo or alcance.sin):
        return True
    for f in ficheros:
        if any(R.casa(f, p) for p in alcance.sin):
            continue
        if not alcance.solo or any(R.casa(f, p) for p in alcance.solo):
            return True
    return False


def documentos_de_decisiones(ctx: "Contexto") -> List[str]:
    return [doc for doc in ctx.documentos()
            if any(R.casa(doc, p, sin_mayusculas=True) for p in ctx.cfg.decisiones)]


def _limpiar(linea: str) -> str:
    return re.sub(r"(\*\*|__)", "", linea).strip()


def _tiene_motivo(lineas: List[str]) -> bool:
    """¿Hay un campo «Motivo: …» con contenido o una sección «## Motivo» con texto?"""
    en_seccion = False
    for i, linea in enumerate(lineas):
        texto = _limpiar(linea)
        enc = _ENCABEZADO.match(texto)
        if enc:
            en_seccion = bool(_SECCION_MOTIVO.match(enc.group(2)))
            continue
        if en_seccion and texto:
            return True
        m = _CAMPO_MOTIVO.match(texto)
        if m:
            valor = m.group(2).strip()
            if valor.startswith("<") and valor.endswith(">"):
                continue  # hueco de plantilla sin rellenar
            if valor.lower().strip(".") not in _RELLENO:
                return True
            if not valor:  # el motivo puede ir en la línea siguiente
                siguiente = next((_limpiar(x) for x in lineas[i + 1:] if x.strip()), "")
                if siguiente and not _ENCABEZADO.match(siguiente) and not re.match(r"^[\w ]+:", siguiente):
                    return True
    return False


def entradas_sin_motivo(ctx: "Contexto") -> List[EntradaDecision]:
    """Entradas de los documentos de decisiones, marcando las que no tienen motivo escrito.

    Si un documento tiene una sección de motivo de nivel 2 («## Contexto», «## Motivo»…) es un ADR
    entero (una decisión por fichero); si no, cada «## …» es una entrada.
    """
    entradas = []
    for doc in documentos_de_decisiones(ctx):
        lineas = ctx.repo.lineas(doc) or []
        en_codigo = ctx.documento(doc).en_codigo
        encabezados = []
        for n, linea in enumerate(lineas, 1):
            m = _ENCABEZADO.match(linea)
            if m and not en_codigo[n - 1]:
                encabezados.append((n, len(m.group(1)), m.group(2)))
        if any(nivel == 2 and _SECCION_MOTIVO.match(titulo) for _, nivel, titulo in encabezados):
            titulo = next((t for _, nivel, t in encabezados if nivel == 1), doc)
            entradas.append(EntradaDecision(doc, 1, titulo, _tiene_motivo(_fuera_de_codigo(lineas, en_codigo))))
            continue
        nivel2 = [(n, t) for n, nivel, t in encabezados if nivel == 2]
        for i, (n, titulo) in enumerate(nivel2):
            fin = nivel2[i + 1][0] - 1 if i + 1 < len(nivel2) else len(lineas)
            cuerpo = _fuera_de_codigo(lineas[n:fin], en_codigo[n:fin])
            entradas.append(EntradaDecision(doc, n, titulo, _tiene_motivo(cuerpo)))
    return entradas


def _fuera_de_codigo(lineas: List[str], en_codigo: List[bool]) -> List[str]:
    return [linea for linea, dentro in zip(lineas, en_codigo) if not dentro]


def marcar_documentadas(ctx: "Contexto", decisiones: List[Decision]) -> None:
    """Una decisión está documentada si su commit (7+ caracteres) aparece en un documento de decisiones."""
    texto = "\n".join("\n".join(ctx.repo.lineas(doc) or []) for doc in documentos_de_decisiones(ctx))
    for d in decisiones:
        d.documentada = d.commit[:7] in texto
