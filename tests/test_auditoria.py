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


if __name__ == "__main__":
    unittest.main()
