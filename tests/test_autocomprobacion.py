"""El propio repositorio está sellado y su check en verde: si no se mantiene limpio a sí mismo, no vale."""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from dockeeper.cli import main

RAIZ = Path(__file__).resolve().parent.parent


class PruebasAutocomprobacion(unittest.TestCase):
    def test_el_repositorio_se_mantiene_limpio(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            codigo = main(["check", "--raiz", str(RAIZ), "--json"])
        datos = json.loads(salida.getvalue())
        problemas = [i for i in datos["items"] if i["estado"] != "OK"]
        self.assertEqual(problemas, [], "Tras cambiar código anclado: revisa el texto, luego dockeeper fix --aceptar")
        self.assertEqual(codigo, 0)
        documentos = {i["doc"] for i in datos["items"]}
        self.assertTrue({"README.md", "SKILL.md", "SPEC.md"} <= documentos)
        self.assertTrue(any(i["tipo"] == "vinculo" for i in datos["items"]))


if __name__ == "__main__":
    unittest.main()
