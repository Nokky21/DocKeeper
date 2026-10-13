"""El porqué: decisiones del historial (sin inventar motivos) y entradas sin motivo escrito."""

import shutil
import unittest

from tests.util import RepoDePrueba, d


@unittest.skipIf(shutil.which("git") is None, "hace falta git")
class PruebasPorque(unittest.TestCase):
    def test_decisiones_del_historial(self):
        with RepoDePrueba({"src/a.py": "x = 1\n"}) as r:
            r.iniciar_git()
            r.commit("feat: primera versión")
            r.escribir("src/a.py", "x = 2\n")
            r.commit(d('''
                refactor: huellas normalizadas

                Decision: normalizar espacios antes de calcular la huella
                Motivo: reformatear no debe romper anclas
                  ni obligar a resellar.
                Alternativas: AST por lenguaje (exige dependencias)
            '''))
            r.escribir("src/b.py", "y = 1\n")
            sello = r.commit("chore: sello aparte\n\nDecision: el sello vive fuera del documento\n")
            r.escribir("docs/x.md", "nada\n")
            r.commit("docs: ADR-007 formato de anclas")

            codigo, datos = r.dk_json("why")
            self.assertEqual(codigo, 0)
            decisiones = datos["decisiones"]
            self.assertEqual([x["decision"] for x in decisiones], [
                "docs: ADR-007 formato de anclas",
                "el sello vive fuera del documento",
                "normalizar espacios antes de calcular la huella",
            ])
            self.assertTrue(decisiones[0]["adr"])
            self.assertIsNone(decisiones[1]["motivo"])  # no consta: no se inventa
            self.assertEqual(decisiones[2]["motivo"], "reformatear no debe romper anclas ni obligar a resellar.")
            self.assertEqual(decisiones[2]["alternativas"], "AST por lenguaje (exige dependencias)")
            self.assertEqual(decisiones[1]["ficheros"], ["src/b.py"])

            _, texto = r.dk("why")
            self.assertIn("motivo: no consta en el historial", texto)

            # Alcance: solo los commits que tocan esa parte.
            _, datos = r.dk_json("why", "--solo", "src/b.py")
            self.assertEqual([x["commit"] for x in datos["decisiones"]], [sello[:10]])

    def test_entradas_sin_motivo_y_documentadas(self):
        with RepoDePrueba({"src/a.py": "x = 1\n"}) as r:
            r.iniciar_git()
            sello = r.commit("chore: sello aparte\n\nDecision: el sello vive fuera del documento\n")
            r.escribir("DECISIONES.md", d(f'''
                # Decisiones

                ## D-002 · Sello fuera del documento

                - **Decisión:** el sello vive aparte.
                - **Motivo:** No consta
                - **Fuente:** commit `{sello[:7]}`

                ## D-001 · Huellas normalizadas

                - **Decisión:** normalizar espacios.

                ## D-000 · Sin rellenar

                - **Motivo:** <por qué, o «No consta»>

                ```
                ## Esto es un ejemplo dentro de un bloque, no una entrada
                ```
            '''))
            r.escribir("docs/adr/0001-anclas.md", "# ADR 1: anclas\n\n## Contexto\n\nHacía falta comprobar.\n\n"
                                                  "## Decisión\n\nAnclar.\n")
            r.escribir("docs/adr/0002-vacio.md", "# ADR 2: vacío\n\n## Contexto\n\n## Decisión\n\nAlgo.\n")
            _, datos = r.dk_json("why")
            entradas = {(e["doc"], e["titulo"]): e["con_motivo"] for e in datos["entradas"]}
            self.assertEqual(entradas, {
                ("DECISIONES.md", "D-002 · Sello fuera del documento"): True,
                ("DECISIONES.md", "D-001 · Huellas normalizadas"): False,
                ("DECISIONES.md", "D-000 · Sin rellenar"): False,
                ("docs/adr/0001-anclas.md", "ADR 1: anclas"): True,
                ("docs/adr/0002-vacio.md", "ADR 2: vacío"): False,
            })
            self.assertTrue(datos["decisiones"][0]["documentada"])
            _, texto = r.dk("why")
            self.assertIn("SIN_MOTIVO  DECISIONES.md:9  D-001 · Huellas normalizadas", texto)

    def test_sin_historial(self):
        with RepoDePrueba({"src/a.py": "x = 1\n"}) as r:
            codigo, datos = r.dk_json("why")
            self.assertEqual((codigo, datos["historial"], datos["decisiones"]), (0, False, []))
            self.assertIn("Sin historial", r.dk("why")[1])


if __name__ == "__main__":
    unittest.main()
