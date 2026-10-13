"""Auditoría: qué documentación hay, qué falta y qué código no tiene ninguna afirmación anclada.

Es el primer paso del flujo (auditar → escribir → sellar → comprobar → arreglar).
"""

from __future__ import annotations

import posixpath
import subprocess
import unicodedata
from typing import TYPE_CHECKING, Dict, List, Tuple

from . import porque

if TYPE_CHECKING:
    from .motor import Contexto

# Páginas base y los nombres con que suelen aparecer.
PAGINAS = [
    ("README", ["readme"]),
    ("ARQUITECTURA", ["arquitectura", "architecture"]),
    ("DECISIONES", ["decisiones", "decisions", "adr"]),
    ("PROCEDIMIENTOS", ["procedimientos", "procedures", "runbook", "operaciones", "operations"]),
    ("API", ["api"]),
    ("INCORPORACION", ["incorporacion", "onboarding"]),
]


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _es_pagina(doc: str, alias: List[str]) -> bool:
    partes = [_sin_acentos(p.lower()) for p in doc.split("/")]
    nombre = posixpath.splitext(partes[-1])[0]
    return any(nombre.startswith(a) for a in alias) or any(a in partes[:-1] for a in alias)


def _commits(ctx: "Contexto") -> int:
    try:
        r = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=ctx.cfg.raiz, capture_output=True, text=True)
    except OSError:
        return 0
    return int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip().isdigit() else 0


def auditar(ctx: "Contexto") -> dict:
    repo, alcance, sello = ctx.repo, ctx.alcance, ctx.sello
    documentos = ctx.documentos()
    codigo = [f for f in repo.ficheros if not repo.es_documento(f) and alcance.codigo_en_alcance(f)]

    paginas = []
    for nombre, alias in PAGINAS:
        encontradas = [doc for doc in documentos if _es_pagina(doc, alias)]
        paginas.append({"pagina": nombre, "documentos": encontradas})

    docs = []
    for doc in documentos:
        documento = ctx.documento(doc)
        anclas = sorted({a.texto for a in documento.anclas})
        selladas = sum(1 for a in anclas if (doc, a) in sello.anclas)
        vinculos = sum(1 for v in sello.vinculos if v.doc == doc)
        docs.append({"doc": doc, "clase": repo.clase(doc), "anclas": len(anclas), "selladas": selladas,
                     "vinculos": vinculos, "bloques_de_codigo": len(documento.bloques),
                     "sin_anclas": not anclas and not vinculos})

    # Tramos anclados por fichero (posiciones del sello: ejecuta check/fix para tenerlas al día).
    tramos: Dict[str, List[Tuple[int, int]]] = {}
    for e in sello.todas():
        tramos.setdefault(e.fichero, []).append((e.inicio, e.fin))

    carpetas: Dict[str, Dict[str, int]] = {}
    sin_ancla = []
    for f in codigo:
        carpeta = f.split("/")[0] if "/" in f else "(raíz)"
        c = carpetas.setdefault(carpeta, {"ficheros": 0, "definiciones": 0, "ancladas": 0})
        c["ficheros"] += 1
        an = repo.analisis(f)
        if an is None or not an.familia:
            continue
        defs = an.definiciones
        superiores = [d for d in defs
                      if not any(o is not d and o.inicio <= d.inicio and d.fin <= o.fin
                                 and (o.inicio, o.fin) != (d.inicio, d.fin) for o in defs)]
        for d in superiores:
            c["definiciones"] += 1
            if any(ini <= d.fin and d.inicio <= fin for ini, fin in tramos.get(f, [])):
                c["ancladas"] += 1
            else:
                sin_ancla.append({"simbolo": f"{f}#{d.nombre}", "lineas": d.fin - d.inicio + 1})
    sin_ancla.sort(key=lambda x: (-x["lineas"], x["simbolo"]))

    decisiones = porque.historial(ctx)
    return {
        "orden": "audit",
        "raiz": str(ctx.cfg.raiz),
        "alcance": alcance.describir(),
        "git": {"historial": decisiones is not None, "commits": _commits(ctx),
                "commits_con_decision": len(decisiones or [])},
        "totales": {"documentos": len(documentos), "ficheros_de_codigo": len(codigo),
                    "anclas_selladas": len(sello.anclas), "vinculos": len(sello.vinculos)},
        "paginas": paginas,
        "documentos": docs,
        "cobertura": [{"carpeta": k, **v} for k, v in sorted(carpetas.items())],
        "mayores_sin_ancla": sin_ancla[:15],
    }
