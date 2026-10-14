"""audit: páginas base, documentos sin anclas y cobertura del código."""

import unittest

from tests.util import RepoDePrueba, d


class PruebasAuditoria(unittest.TestCase):
    def test_inventario(self):
        with RepoDePrueba({
            "README.md": "Calcula [[src/a.py#calcular]].\n",
            "docs/notas.md": "Notas sin ninguna ancla.\n",
            "docs/adr/0001.md": "# ADR\n",
            "src/a.py": d('''
                def calcular(x):
                    return x * 2


                def otra(y):
                    return y
            '''),
            "lib/b.py": "class Grande:\n    def m(self):\n        return 1\n",
        }) as r:
            r.dk("scan")
            codigo, datos = r.dk_json("audit")
            self.assertEqual(codigo, 0)
            paginas = {p["pagina"]: p["documentos"] for p in datos["paginas"]}
            self.assertEqual(paginas["README"], ["README.md"])
            self.assertEqual(paginas["DECISIONES"], ["docs/adr/0001.md"])
            self.assertEqual(paginas["ARQUITECTURA"], [])
            docs = {x["doc"]: x for x in datos["documentos"]}
            self.assertTrue(docs["docs/notas.md"]["sin_anclas"])
            self.assertEqual((docs["README.md"]["anclas"], docs["README.md"]["selladas"]), (1, 1))
            cobertura = {c["carpeta"]: (c["ancladas"], c["definiciones"]) for c in datos["cobertura"]}
            self.assertEqual(cobertura, {"lib": (0, 1), "src": (1, 2)})
            self.assertEqual([x["simbolo"] for x in datos["mayores_sin_ancla"]], ["lib/b.py#Grande", "src/a.py#otra"])
            _, texto = r.dk("audit")
            self.assertIn("✗ ARQUITECTURA", texto)
            self.assertIn("sin anclas: nada de lo que dice está comprobado", texto)


    def test_dependencias_subidas_no_son_codigo_propio(self):
        with RepoDePrueba({
            "src/a.py": "def propia():\n    return 1\n",
            "node_modules/lib/index.js": "function ajena() {\n  return 1;\n}\n",
            "node_modules/lib/README.md": "# lib\n",
            "vendor/github.com/x/y.go": "package y\n\nfunc Ajena() int {\n\treturn 1\n}\n",
            # Un paquete propio puede llamarse «vendor»: lo suyo sí cuenta, sus node_modules no.
            "packages/vendor/package.json": '{"name": "vendor"}\n',
            "packages/vendor/x.js": "function suya() {\n  return 2;\n}\n",
            "packages/vendor/README.md": "# vendor\n",
            "packages/vendor/node_modules/dep/i.js": "function ajena2() {\n  return 3;\n}\n",
        }) as r:
            r.iniciar_git()
            r.git("add", "-f", ".")  # subidas a git (-f: aunque un gitignore global ignore node_modules)
            _, datos = r.dk_json("audit")
            self.assertEqual(datos["totales"]["ficheros_de_codigo"], 3)
            self.assertEqual(datos["totales"]["documentos"], 1)
            self.assertEqual({c["carpeta"] for c in datos["cobertura"]}, {"packages", "src"})
            self.assertEqual([x["simbolo"] for x in datos["mayores_sin_ancla"]],
                             ["packages/vendor/x.js#suya", "src/a.py#propia"])
            self.assertEqual([(p["ruta"], p["ficheros"]) for p in datos["paquetes"]], [("packages/vendor", 2)])
            # Recortar el código no convierte en dependencia lo de un paquete propio que queda fuera.
            _, datos = r.dk_json("audit", "--solo", "src/")
            self.assertEqual([x["doc"] for x in datos["documentos"]], ["packages/vendor/README.md"])

if __name__ == "__main__":
    unittest.main()
