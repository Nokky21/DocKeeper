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
from dockeeper import auditoria, motor, porque, revision
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

    ordenes.add_parser("audit", parents=[comun, alcance],
                       help="inventario: páginas que faltan, documentos sin anclas y código sin documentar")
    s = ordenes.add_parser("scan", parents=[comun, alcance],
                           help="sella las anclas nuevas y enseña en qué bloque queda cada una")
    s.add_argument("--resellar", action="store_true",
                   help="vuelve a sellar también las ya selladas (tras revisar el texto)")
    ordenes.add_parser("check", parents=[comun, alcance], help="comprueba que lo documentado sigue siendo cierto")
    f = ordenes.add_parser("fix", parents=[comun, alcance],
                           help="recoloca los MOVED y quita huérfanas (solo toca el sello)")
    f.add_argument("--aceptar", action="store_true",
                   help="acepta los CHANGED como nueva verdad (después de revisar el texto)")
    v = ordenes.add_parser("link", parents=[comun],
                           help="vincula una línea de un documento con código sin tocar el documento")
    v.add_argument("destino", metavar="DOC:LÍNEA", help="documento y línea de la afirmación")
    v.add_argument("ancla", nargs="?", metavar="RUTA:LÍNEA|RUTA#SÍMBOLO", help="código que la respalda")
    v.add_argument("--quitar", action="store_true", help="quita los vínculos de esa línea (o solo el indicado)")
    ordenes.add_parser("why", parents=[comun, alcance],
                       help="decisiones del historial (Decision:, Motivo:, Why:, ADR) y entradas sin motivo")
    r = ordenes.add_parser("review", parents=[comun, alcance],
                           help="qué documentación toca un cambio y qué código nuevo o cambiado queda sin documentar")
    r.add_argument("--desde", metavar="REF",
                   help="revisión desde la que comparar con el árbol de trabajo (por defecto HEAD~1: el último "
                        "commit y lo que haya sin commitear); con una rama, desde donde se bifurcó")
    return p


def _salida_utf8() -> None:
    """En Windows la consola o un pipe pueden no ser UTF-8, y «→» o «│» romperían la salida."""
    for flujo in (sys.stdout, sys.stderr):
        codificacion = (getattr(flujo, "encoding", None) or "").lower().replace("-", "")
        if hasattr(flujo, "reconfigure") and codificacion != "utf8":
            flujo.reconfigure(encoding="utf-8", errors="replace")


def main(argv: Optional[List[str]] = None) -> int:
    _salida_utf8()
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
    "VINCULO_SUELTO": "revisa la frase y vuelve a vincularla (dockeeper link) o quítalo (link --quitar)",
    "ANCLA_INTERNA": "en documentos «publico» usa dockeeper link en vez de anclas en el texto",
    "CODIGO_COPIADO": "describe el código o escribe un ejemplo propio en vez de copiarlo",
    "RUTA_INTERNA": "quita la ruta interna del texto publicado",
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


def _link(args, raiz: Path) -> int:
    ctx = motor.Contexto(raiz)
    if args.quitar:
        items = motor.desvincular(ctx, args.destino, args.ancla)
    elif not args.ancla:
        raise ErrorDeUso("falta el ancla: dockeeper link DOC:LÍNEA RUTA:LÍNEA|RUTA#SÍMBOLO")
    else:
        items = [motor.vincular(ctx, args.destino, args.ancla)]
    codigo = 1 if any(i.falla for i in items) else 0
    if args.json:
        _emitir({"orden": "link", "raiz": str(ctx.cfg.raiz), "codigo": codigo, "items": [i.a_dict() for i in items]})
        return codigo
    for item in items:
        _linea(item)
        _bloque(item)
    if not args.quitar and not codigo:
        print("El documento no se ha tocado: el vínculo vive en el sello.")
    return codigo


def _audit(args, raiz: Path) -> int:
    ctx = motor.Contexto(raiz, args.solo, args.sin)
    datos = auditoria.auditar(ctx)
    datos["codigo"] = 0
    if args.json:
        _emitir(datos)
        return 0
    git, tot = datos["git"], datos["totales"]
    print(f"dockeeper audit · {datos['raiz']}")
    if git["historial"]:
        print(f"Git: {git['commits']} commits · {git['commits_con_decision']} con marcas de decisión (dockeeper why)")
    else:
        print("Git: sin historial (why no tendrá de dónde sacar el porqué)")
    print(f"Totales: {tot['documentos']} documentos · {tot['ficheros_de_codigo']} ficheros de código · "
          f"{tot['anclas_selladas']} anclas selladas · {tot['vinculos']} vínculos")
    print("Páginas base:")
    for p in datos["paginas"]:
        if p["documentos"]:
            print(f"  ✓ {p['pagina']:<15} {', '.join(p['documentos'])}")
        else:
            print(f"  ✗ {p['pagina']:<15} falta (plantilla: templates/{p['pagina']}.md)")
    print("Documentos:")
    for doc in datos["documentos"]:
        nota = "  ← sin anclas: nada de lo que dice está comprobado" if doc["sin_anclas"] else ""
        print(f"  {doc['doc']:<40} {doc['clase']:<10} {doc['anclas']} anclas ({doc['selladas']} selladas) · "
              f"{doc['vinculos']} vínculos{nota}")
    if datos["paquetes"]:
        print(f"Paquetes ({len(datos['paquetes'])}): documenta uno cada vez con --solo RUTA")
        for p in datos["paquetes"]:
            readme = p["readme"] or "sin README"
            nota = "  ← sin documentar" if not p["readme"] and not p["documentado_en"] else ""
            print(f"  {p['ruta'] + '/':<28} {p['nombre']:<24} {p['ancladas']:>4}/{p['definiciones']:<4} definiciones · "
                  f"{p['ficheros']} ficheros · {readme}{nota}")
    print("Cobertura (definiciones de primer nivel con alguna afirmación anclada):")
    for c in datos["cobertura"]:
        nota = "  ← sin documentar" if c["definiciones"] and not c["ancladas"] else ""
        carpeta = c["carpeta"] if c["carpeta"] == "(raíz)" else c["carpeta"] + "/"
        print(f"  {carpeta:<25} {c['ancladas']:>4}/{c['definiciones']:<4} definiciones · "
              f"{c['ficheros']} ficheros{nota}")
    if datos["mayores_sin_ancla"]:
        print("Mayores definiciones sin ninguna afirmación anclada:")
        for x in datos["mayores_sin_ancla"]:
            print(f"  {x['simbolo']} ({x['lineas']} líneas)")
    return 0


def _why(args, raiz: Path) -> int:
    ctx = motor.Contexto(raiz, args.solo, args.sin)
    decisiones = porque.historial(ctx)
    if decisiones:
        porque.marcar_documentadas(ctx, decisiones)
    entradas = porque.entradas_sin_motivo(ctx)
    if args.json:
        _emitir({"orden": "why", "raiz": str(ctx.cfg.raiz), "codigo": 0, "historial": decisiones is not None,
                 "decisiones": [d.a_dict() for d in decisiones or []],
                 "documentos": porque.documentos_de_decisiones(ctx),
                 "entradas": [e.a_dict() for e in entradas]})
        return 0
    if decisiones is None:
        print("Sin historial de git: no hay de dónde sacar el porqué. Lo que no consta, se escribe que no consta.")
    else:
        print(f"Decisiones en el historial ({len(decisiones)}):")
        for d in decisiones:
            marca = " [ADR]" if d.adr else ""
            print(f"  {d.commit} {d.fecha}  {d.decision}{marca}")
            print(f"      motivo: {d.motivo or 'no consta en el historial'}")
            if d.alternativas:
                print(f"      alternativas descartadas: {d.alternativas}")
            print(f"      documentada: {'sí' if d.documentada else 'no'}")
    documentos = porque.documentos_de_decisiones(ctx)
    if documentos:
        sin_motivo = [e for e in entradas if not e.con_motivo]
        print(f"Documentos de decisiones: {', '.join(documentos)} · {len(entradas)} entradas · "
              f"{len(sin_motivo)} sin motivo escrito")
        for e in sin_motivo:
            print(f"  SIN_MOTIVO  {e.doc}:{e.linea}  {e.titulo}")
    else:
        print("No hay documentos de decisiones (plantilla: templates/DECISIONES.md).")
    return 0


_MAX_LISTA = 20


def _review(args, raiz: Path) -> int:
    ctx = motor.Contexto(raiz, args.solo, args.sin)
    rev = revision.revisar(ctx, args.desde, args.sin)
    if args.json:
        _emitir({"orden": "review", "raiz": str(ctx.cfg.raiz), "codigo": 0, "alcance": ctx.alcance.describir(),
                 "desde": rev.desde, "base": rev.base[:10] if rev.base else None,
                 "cambios": {"codigo": rev.codigo, "documentos": rev.documentos},
                 "afirmaciones": [i.a_dict() for i in rev.afirmaciones],
                 "sin_documentar": [s.a_dict() for s in rev.sin_documentar],
                 "decisiones": [d.a_dict() for d in rev.decisiones]})
        return 0
    base = rev.base[:10] if rev.base else "el principio"
    nc, nd = len(rev.codigo), len(rev.documentos)
    print(f"dockeeper review · cambios desde {rev.desde} ({base}) · {nc} fichero{'' if nc == 1 else 's'} de código · "
          f"{nd} documento{'' if nd == 1 else 's'}")
    if rev.vacia:
        print("Nada que revisar: la documentación que toca este cambio sigue en verde y no queda código "
              "nuevo o cambiado sin documentar.")
        return 0
    if rev.afirmaciones:
        print("Afirmaciones que toca el cambio (revisa el texto):")
        for item in rev.afirmaciones:
            _linea(item)
    if rev.sin_documentar:
        print("Código nuevo o cambiado sin ninguna afirmación (¿se puede añadir a la documentación?):")
        for s in rev.sin_documentar[:_MAX_LISTA]:
            docs = f" · ya hablan de ese fichero: {', '.join(s.documentos)}" if s.documentos else ""
            print(f"  {s.estado:<9} {s.simbolo} ({s.fin - s.inicio + 1} líneas){docs}")
        if len(rev.sin_documentar) > _MAX_LISTA:
            print(f"  … y {len(rev.sin_documentar) - _MAX_LISTA} más (--json las da todas)")
    if rev.decisiones:
        print("Decisiones de estos commits sin documentar (dockeeper why):")
        for d in rev.decisiones:
            print(f"  {d.commit} {d.fecha}  {d.decision}")
    estados = {i.estado for i in rev.afirmaciones}
    for estado, pista in _PISTAS.items():
        if estado in estados:
            print(f"  → {pista}")
    if rev.sin_documentar:
        print("  → documenta lo que haga falta con un ancla por afirmación y sella con dockeeper scan")
    if rev.decisiones:
        print("  → anótalas en el documento de decisiones (motivo solo si consta)")
    return 0


_ORDENES: Dict[str, Callable[[argparse.Namespace, Path], int]] = {
    "audit": _audit,
    "why": _why,
    "scan": _scan,
    "check": _check,
    "fix": _fix,
    "link": _link,
    "review": _review,
}
