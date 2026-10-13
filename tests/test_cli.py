"""La CLI: --json en todas las órdenes, códigos de salida y que solo escribe el sello."""

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from tests.util import RepoDePrueba, d

RAIZ = Path(__file__).resolve().parent.parent
PAGOS = d('''
    def validar_pago(pago):
        return pago > 0
''')


def instantanea(raiz: Path) -> dict:
    """Ruta → contenido de todo lo que hay bajo la raíz (salvo .git)."""
    res = {}
    for carpeta, subcarpetas, ficheros in os.walk(raiz):
        subcarpetas[:] = [c for c in subcarpetas if c != ".git"]
        for f in ficheros:
            p = Path(carpeta, f)
            res[p.relative_to(raiz).as_posix()] = p.read_bytes()
    return res


class PruebasCli(unittest.TestCase):
    def test_version(self):
        r = subprocess.run([sys.executable, "-m", "dockeeper", "--version"], cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8")
        self.assertEqual(r.returncode, 0)
        self.assertIn("dockeeper", r.stdout)

    def test_lanzador_bin(self):
        r = subprocess.run([sys.executable, str(RAIZ / "bin" / "dockeeper"), "--help"], capture_output=True, text=True,
                           encoding="utf-8")
        self.assertEqual(r.returncode, 0)
        for orden in ("audit", "scan", "check", "fix", "link", "why"):
            self.assertIn(orden, r.stdout)

    def test_todas_las_ordenes_aceptan_json(self):
        with RepoDePrueba({"src/pagos.py": PAGOS, "README.md": "Valida [[src/pagos.py#validar_pago]].\n",
                           "docs/guia.md": "Una frase que vincular.\n"}) as r:
            if shutil.which("git"):
                r.iniciar_git()
                r.commit("feat: inicio\n\nDecision: probar\nMotivo: porque sí")
            ordenes = [
                ("audit",), ("scan",), ("check",), ("fix",), ("fix", "--aceptar"),
                ("link", "docs/guia.md:1", "src/pagos.py#validar_pago"),
                ("link", "docs/guia.md:1", "--quitar"), ("why",),
            ]
            for orden in ordenes:
                codigo, salida = r.dk(*orden, "--json")
                datos = json.loads(salida)  # falla si no es JSON válido
                self.assertEqual(datos["orden"], orden[0])
                self.assertEqual(datos["codigo"], codigo)
                self.assertEqual(codigo, 0, (orden, datos))

    def test_errores_de_uso_en_json(self):
        with RepoDePrueba({"a.py": "x = 1\n"}, config={"publicos": ["docs/"]}) as r:
            codigo, salida = r.dk("check", "--json")
            self.assertEqual(codigo, 2)
            self.assertIn("clave desconocida «publicos»", json.loads(salida)["error"])

    def test_sello_danado(self):
        with RepoDePrueba({"a.py": "x = 1\n", ".dockeeper.sello.json": "{no es json"}) as r:
            self.assertEqual(r.dk("check")[0], 2)

    def test_solo_escribe_el_sello(self):
        with RepoDePrueba({"src/pagos.py": PAGOS, "README.md": "Valida [[src/pagos.py#validar_pago]].\n",
                           "docs/guia.md": "Una frase que vincular.\n"},
                          config={"publico": ["docs/"]}) as r:
            antes = instantanea(r.raiz)
            for orden in [("audit",), ("scan",), ("check",), ("link", "docs/guia.md:1", "src/pagos.py#validar_pago"),
                          ("fix", "--aceptar"), ("why",), ("check",)]:
                r.dk(*orden)
            despues = instantanea(r.raiz)
            self.assertEqual(set(despues) - set(antes), {".dockeeper.sello.json"})
            self.assertEqual({k: despues[k] for k in antes}, antes)  # nada más se ha tocado
            sello = r.leer(".dockeeper.sello.json")
            self.assertNotIn("return pago", sello)  # el sello guarda huellas, no código


if __name__ == "__main__":
    unittest.main()
