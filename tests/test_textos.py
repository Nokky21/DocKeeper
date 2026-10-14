"""Idioma de los mensajes: inglés por defecto, español si el entorno lo pide; códigos y claves de --json no cambian."""

import ast
import os
import string
import unittest
from pathlib import Path
from unittest import mock

from dockeeper.textos import EN
from tests.util import RepoDePrueba, d

RAIZ = Path(__file__).resolve().parent.parent
PAGOS = d('''
    def validar_pago(pago):
        return pago > 0
''')
SIN_IDIOMA = {"LC_ALL": "", "LC_MESSAGES": "", "LANG": ""}


def con_cambio(r: RepoDePrueba) -> None:
    r.dk("scan")
    r.escribir("src/pagos.py", PAGOS.replace("> 0", ">= 0"))


class PruebasTextos(unittest.TestCase):
    def repo(self):
        return RepoDePrueba({"src/pagos.py": PAGOS, "README.md": "Valida [[src/pagos.py#validar_pago]].\n"})

    def test_ingles_por_defecto(self):
        with self.repo() as r, mock.patch.dict(os.environ, SIN_IDIOMA):
            con_cambio(r)
            codigo, texto = r.dk("check")
            self.assertEqual(codigo, 1)
            self.assertIn("1 claim checked", texto)
            self.assertIn("the content of “validar_pago” changed", texto)
            self.assertIn("Result: FAIL", texto)
            self.assertNotIn("FALLA", texto)

    def test_espanol_si_el_entorno_lo_pide(self):
        with self.repo() as r, mock.patch.dict(os.environ, {**SIN_IDIOMA, "LANG": "es_ES.UTF-8"}):
            con_cambio(r)
            _, texto = r.dk("check")
            self.assertIn("1 afirmación comprobada", texto)
            self.assertIn("Resultado: FALLA", texto)

    def test_lc_all_manda_sobre_lang(self):
        with self.repo() as r, mock.patch.dict(os.environ, {**SIN_IDIOMA, "LC_ALL": "en_US.UTF-8",
                                                            "LANG": "es_ES.UTF-8"}):
            con_cambio(r)
            _, texto = r.dk("check")
            self.assertIn("Result: FAIL", texto)

    def test_codigos_y_claves_del_json_no_cambian(self):
        with self.repo() as r:
            con_cambio(r)
            datos = {}
            for idioma in ("en_US.UTF-8", "es_ES.UTF-8"):
                with mock.patch.dict(os.environ, {**SIN_IDIOMA, "LC_ALL": idioma}):
                    _, datos[idioma] = r.dk_json("check")
            sin_detalle = [{k: v for k, v in datos[i].items() if k != "items"} for i in datos]
            self.assertEqual(sin_detalle[0], sin_detalle[1])
            self.assertEqual(*[[(x["estado"], x.get("ancla")) for x in datos[i]["items"]] for i in datos])

    def test_cada_mensaje_tiene_version_en_ingles(self):
        for p in sorted((RAIZ / "dockeeper").glob("*.py")):
            for nodo in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                funcion = getattr(nodo.func, "id", getattr(nodo.func, "attr", None)) if isinstance(nodo, ast.Call) else None
                if funcion not in ("t", "tn"):
                    continue
                pasados = {k.arg for k in nodo.keywords} | ({"n"} if funcion == "tn" else set())
                for arg in nodo.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        self.assertIn(arg.value, EN, f"{p.name}:{nodo.lineno}")
                        campos = {c for _, c, _, _ in string.Formatter().parse(arg.value) if c}
                        self.assertLessEqual(campos, pasados, f"{p.name}:{nodo.lineno}: faltan datos")
        for es, en in EN.items():
            campos = [{c for _, c, _, _ in string.Formatter().parse(x) if c} for x in (es, en)]
            self.assertEqual(campos[0], campos[1], es)


if __name__ == "__main__":
    unittest.main()
