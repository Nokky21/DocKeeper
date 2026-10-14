"""Diagramas Mermaid: sus anclas «%% dockeeper:» se sellan y se comprueban como las demás."""

import unittest

from tests.util import RepoDePrueba, d, por_ancla

CODIGO = d('''
    def validar(pago):
        return pago > 0


    def cobrar(pago):
        return pago
''')
DOC = d('''
    # Pagos

    ```mermaid
    flowchart LR
      A[validar] --> B[cobrar]
      %% dockeeper: src/pagos.py#validar src/pagos.py#cobrar
    ```
''')


class PruebasDiagramas(unittest.TestCase):
    def test_las_anclas_de_un_diagrama_se_comprueban(self):
        with RepoDePrueba({"src/pagos.py": CODIGO, "docs/pagos.md": DOC}) as r:
            codigo, datos = r.dk_json("scan")
            self.assertEqual(codigo, 0)
            self.assertEqual(sorted(por_ancla(datos)), ["src/pagos.py#cobrar", "src/pagos.py#validar"])
            r.escribir("src/pagos.py", CODIGO.replace("pago > 0", "pago >= 0"))
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            cambio = por_ancla(datos)["src/pagos.py#validar"]
            self.assertEqual((cambio["estado"], cambio["linea_doc"]), ("CHANGED", 6))  # la línea «%%» del diagrama

    def test_fuera_de_un_diagrama_no_es_un_ancla(self):
        texto = d('''
            Así se ancla un diagrama:

            ```markdown
            %% dockeeper: src/pagos.py#no_existe
            ```

            ```text
            %% dockeeper: src/pagos.py#tampoco
            ```
        ''')
        with RepoDePrueba({"src/pagos.py": CODIGO, "docs/guia.md": texto}) as r:
            _, datos = r.dk_json("scan")
            self.assertEqual(por_ancla(datos), {})

    def test_ancla_mal_escrita_en_un_diagrama(self):
        with RepoDePrueba({"src/pagos.py": CODIGO,
                           "docs/pagos.md": "```Mermaid\nflowchart LR\n  %% dockeeper: esto-no\n```\n"}) as r:
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            self.assertIn("ANCLA_MAL_ESCRITA", [i["estado"] for i in datos["items"]])

    def test_audit_senala_diagramas_sin_anclas(self):
        sin = "```mermaid\nflowchart LR\n  A --> B\n```\n"
        with RepoDePrueba({"src/pagos.py": CODIGO, "docs/pagos.md": DOC + "\n" + sin}) as r:
            _, datos = r.dk_json("audit")
            doc = next(x for x in datos["documentos"] if x["doc"] == "docs/pagos.md")
            self.assertEqual((doc["diagramas"], doc["diagramas_sin_anclas"]), (2, 1))
            _, texto = r.dk("audit")
            self.assertIn("1 diagrama sin anclas", texto)

    def test_en_un_documento_publico_es_un_ancla_interna(self):
        with RepoDePrueba({"src/pagos.py": CODIGO, "docs/pagos.md": DOC}, config={"publico": ["docs/"]}) as r:
            _, datos = r.dk_json("check")
            estados = [i["estado"] for i in datos["items"]]
            self.assertIn("ANCLA_INTERNA", estados)
            self.assertNotIn("RUTA_INTERNA", estados)  # la misma ancla no cuenta dos veces


if __name__ == "__main__":
    unittest.main()
