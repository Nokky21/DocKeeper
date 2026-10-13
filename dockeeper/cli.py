"""Línea de órdenes de DocKeeper.

Códigos de salida: 0 todo bien (OK, MOVED o avisos) · 1 hay problemas · 2 error de uso.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

from dockeeper import __version__
from dockeeper import motor
from dockeeper.config import ErrorDeUso, buscar_raiz

_ANCHO = 15


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dockeeper",
                                description="Documentación anclada al código que avisa cuando deja de ser cierta.")
    p.add_argument("--version", action="version", version=f"dockeeper {__version__}")
    ordenes = p.add_subparsers(dest="orden", metavar="orden")
    ordenes.required = True

    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("--raiz", help="raíz del repositorio (por defecto, la carpeta con .dockeeper.json o .git)")
    comun.add_argument("--json", action="store_true", help="salida en JSON")
    alcance = argparse.ArgumentParser(add_help=False)
    alcance.add_argument("--solo", action="append", default=[], metavar="RUTA",
                         help="limita a esta ruta (repetible): si es de documentos recorta documentos; "
                              "si es de código recorta código")
    alcance.add_argument("--sin", action="append", default=[], metavar="PATRÓN",
                         help="descarta lo que case con este patrón o prefijo (repetible)")

    s = ordenes.add_parser("scan", parents=[comun, alcance],
                           help="sella las anclas nuevas y enseña en qué bloque queda cada una")
    s.add_argument("--resellar", action="store_true",
                   help="vuelve a sellar también las ya selladas (tras revisar el texto)")
    ordenes.add_parser("check", parents=[comun, alcance], help="comprueba que lo documentado sigue siendo cierto")
    f = ordenes.add_parser("fix", parents=[comun, alcance],
                           help="recoloca los MOVED y quita huérfanas (solo toca el sello)")
    f.add_argument("--aceptar", action="store_true",
                   help="acepta los CHANGED como nueva verdad (después de revisar el texto)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        raiz = Path(args.raiz).resolve() if args.raiz else buscar_raiz(Path.cwd())
        if not raiz.is_dir():
            raise ErrorDeUso(f"{raiz} no es una carpeta")
        return _ORDENES[args.orden](args, raiz)
    except ErrorDeUso as e:
        if getattr(args, "json", False):
            _emitir({"orden": args.orden, "error": str(e), "codigo": 2})
        else:
            print(f"dockeeper: {e}", file=sys.stderr)
        return 2


# --- Salida ------------------------------------------------------------------------------

def _emitir(datos: dict) -> None:
    print(json.dumps(datos, ensure_ascii=False, indent=2))


def _lugar(item: motor.Item) -> str:
    if item.doc is None:
        return "(repositorio)"
    return f"{item.doc}:{item.linea_doc}" if item.linea_doc else item.doc


def _linea(item: motor.Item, detalle: bool = True) -> None:
    partes = [f"{item.estado:<{_ANCHO}}", _lugar(item)]
    if item.ancla:
        partes.append(f"→ {item.ancla}")
    print("  ".join(partes))
    if detalle and item.detalle:
        print(f"{'':<{_ANCHO}}  {item.detalle}")
    for aviso in item.avisos:
        print(f"{'':<{_ANCHO}}  aviso: {aviso}")


def _bloque(item: motor.Item) -> None:
    b = item.bloque
    if not b:
        return
    tipo = {"definicion": "definición", "declaracion": "declaración", "ventana": "ventana"}.get(b["tipo"], b["tipo"])
    nombre = f" «{b['nombre']}»" if b.get("nombre") else ""
    sangria = " " * (_ANCHO + 2)
    print(f"{sangria}bloque: {tipo}{nombre} {b['fichero']}:{b['inicio']}-{b['fin']}")
    filas = [(b["inicio"], b["primera"])]
    if b.get("linea") not in (None, b["inicio"], b["fin"]):
        filas.append((b["linea"], b.get("anclada", "") + "   ← línea anclada"))
    if b["fin"] != b["inicio"]:
        filas.append((b["fin"], b["ultima"]))
    for num, texto in filas:
        print(f"{sangria}  {num:>5} │ {texto}")


def _resumen(res: motor.Resultado) -> str:
    cuenta = res.resumen()
    partes = [f"{n} {estado}" for estado, n in sorted(cuenta.items())]
    if res.fuera_de_alcance:
        partes.append(f"{res.fuera_de_alcance} fuera de alcance")
    return " · ".join(partes) if partes else "nada"


def _json_resultado(orden: str, ctx: motor.Contexto, res: motor.Resultado, extra: Optional[dict] = None) -> dict:
    datos = {"orden": orden, "raiz": str(ctx.cfg.raiz), "alcance": ctx.alcance.describir(),
             "codigo": res.codigo, "examinados": res.examinados, "fuera_de_alcance": res.fuera_de_alcance,
             "resumen": res.resumen(), "items": [i.a_dict() for i in res.items]}
    if extra:
        datos.update(extra)
    return datos


_PISTAS = {
    "MOVED": "dockeeper fix las recoloca (solo toca el sello)",
    "CHANGED": "revisa el código y el texto; luego dockeeper fix --aceptar",
    "SIN_SELLAR": "dockeeper scan las sella",
    "HUERFANA": "dockeeper fix las quita del sello",
    "DESAPARECIDO": "corrige o quita el ancla del documento y vuelve a ejecutar scan",
}


# --- Órdenes -----------------------------------------------------------------------------

def _scan(args, raiz: Path) -> int:
    ctx = motor.Contexto(raiz, args.solo, args.sin)
    res = motor.escanear(ctx, resellar=args.resellar)
    if args.json:
        _emitir(_json_resultado("scan", ctx, res))
        return res.codigo
    print(f"dockeeper scan · {res.examinados} anclas en alcance")
    for item in res.items:
        _linea(item)
        _bloque(item)
    print(f"Resumen: {_resumen(res)}")
    return res.codigo


def _check(args, raiz: Path) -> int:
    ctx = motor.Contexto(raiz, args.solo, args.sin)
    res = motor.comprobar(ctx)
    if args.json:
        _emitir(_json_resultado("check", ctx, res))
        return res.codigo
    print(f"dockeeper check · {res.examinados} afirmaciones comprobadas")
    for item in res.items:
        if item.estado != "OK":
            _linea(item)
            _bloque(item)
    print(f"Resumen: {_resumen(res)}")
    for estado, pista in _PISTAS.items():
        if estado in res.resumen():
            print(f"  → {pista}")
    print("Resultado: " + ("FALLA" if res.codigo else "en verde"))
    return res.codigo


def _fix(args, raiz: Path) -> int:
    ctx = motor.Contexto(raiz, args.solo, args.sin)
    hechos, final = motor.arreglar(ctx, aceptar=args.aceptar)
    if args.json:
        _emitir(_json_resultado("fix", ctx, final, {"hechos": [i.a_dict() for i in hechos]}))
        return final.codigo
    print(f"dockeeper fix · {len(hechos)} cambio{'' if len(hechos) == 1 else 's'} en el sello (los documentos no se tocan)")
    for item in hechos:
        print(f"{item.accion:<{_ANCHO}}  {_lugar(item)}  → {item.ancla}")
        if item.accion == "aceptada":
            _bloque(item)
    restantes = [i for i in final.items if i.estado != "OK"]
    if restantes:
        print("Queda pendiente:")
        for item in restantes:
            _linea(item)
    print(f"Resumen tras fix: {_resumen(final)}")
    print("Resultado: " + ("FALLA" if final.codigo else "en verde"))
    return final.codigo


_ORDENES: Dict[str, Callable[[argparse.Namespace, Path], int]] = {
    "scan": _scan,
    "check": _check,
    "fix": _fix,
}
