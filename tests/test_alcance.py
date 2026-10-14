"""Alcance parcial: --solo recorta código o documentos según a qué señale; --sin descarta."""

import unittest

from dockeeper.alcance import Alcance
from dockeeper.config import ErrorDeUso
from dockeeper.rutas import casa
from tests.util import RepoDePrueba, d, estados

PAGOS = d('''
    def validar(pago):
        return pago > 0
''')
OTRO = d('''
    def informe():
        return "ok"
''')


def repo():
    r = RepoDePrueba({
        "src/pagos.py": PAGOS,
        "src/otro.py": OTRO,
        "src/sin_anclas.py": "x = 1\n",
        "src/NOTAS.md": "Notas internas de la carpeta [[src/pagos.py#validar]].\n",
        "docs/a.md": "Valida [[src/pagos.py#validar]] e informa [[src/otro.py#informe]].\n",
        "docs/b.md": "Solo valida [[src/pagos.py#validar]].\n",
    })
    r.dk("scan")
    r.escribir("src/otro.py", OTRO.replace('"ok"', '"ko"'))  # rompe solo lo que habla de otro.py
    return r


class PruebasAlcance(unittest.TestCase):
    def test_sin_restriccion_se_comprueba_todo(self):
        with repo() as r:
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            self.assertEqual(datos["examinados"], 4)
            self.assertEqual(datos["fuera_de_alcance"], 0)

    def test_solo_codigo_recorta_el_codigo(self):
        with repo() as r:
            codigo, datos = r.dk_json("check", "--solo", "src/pagos.py")
            self.assertEqual(codigo, 0, datos)
            self.assertEqual(datos["alcance"]["solo_codigo"], ["src/pagos.py"])
            self.assertEqual(datos["examinados"], 3)  # las tres anclas a pagos, desde todos los documentos
            self.assertEqual(datos["fuera_de_alcance"], 1)  # la de docs/a.md a otro.py

    def test_solo_carpeta_con_codigo_trae_todos_los_documentos_que_hablan_de_ella(self):
        with repo() as r:
            # src/ contiene código y un documento: cuenta como código, así que NO recorta documentos.
            codigo, datos = r.dk_json("check", "--solo", "src")
            self.assertEqual(datos["alcance"], {"solo_documentos": [], "solo_codigo": ["src"], "sin": []})
            self.assertEqual(codigo, 1)
            self.assertEqual(datos["examinados"], 4)

    def test_solo_documento_recorta_documentos_sin_perder_su_codigo(self):
        with repo() as r:
            codigo, datos = r.dk_json("check", "--solo", "docs/b.md")
            self.assertEqual((codigo, datos["examinados"]), (0, 1))
            self.assertEqual(datos["alcance"]["solo_documentos"], ["docs/b.md"])
            codigo, datos = r.dk_json("check", "--solo", "docs/a.md")
            self.assertEqual((codigo, datos["examinados"]), (1, 2))
            self.assertIn("CHANGED", estados(datos))

    def test_solo_carpeta_de_documentos(self):
        with repo() as r:
            codigo, datos = r.dk_json("check", "--solo", "docs")
            self.assertEqual(datos["alcance"]["solo_documentos"], ["docs"])
            self.assertEqual((codigo, datos["examinados"]), (1, 3))

    def test_solo_repetible_y_combinado(self):
        with repo() as r:
            codigo, datos = r.dk_json("check", "--solo", "docs/a.md", "--solo", "src/pagos.py")
            self.assertEqual((codigo, datos["examinados"], datos["fuera_de_alcance"]), (0, 1, 1))

    def test_sin_descarta(self):
        with repo() as r:
            codigo, datos = r.dk_json("check", "--sin", "src/otro.py")
            self.assertEqual((codigo, datos["fuera_de_alcance"]), (0, 1))
            codigo, datos = r.dk_json("check", "--sin", "docs/a*")
            self.assertEqual((codigo, datos["examinados"]), (0, 2))

    def test_sin_en_la_configuracion(self):
        with repo() as r:
            r.escribir(".dockeeper.json", '{"sin": ["src/otro.py"]}')
            self.assertEqual(r.dk("check")[0], 0)

    def test_listas_vacias(self):
        conocidas = ["src/a.py", "docs/x.md"]
        es_doc = lambda ruta: ruta.endswith(".md")
        vacio = Alcance([], [], conocidas, es_doc)
        # --solo vacío = sin restricción; --sin vacío = nada que descartar.
        for ruta in conocidas + ["cualquier/otra.go"]:
            self.assertTrue(vacio.doc_en_alcance(ruta))
            self.assertTrue(vacio.codigo_en_alcance(ruta))
        solo_codigo = Alcance(["src"], [], conocidas, es_doc)
        self.assertTrue(solo_codigo.doc_en_alcance("docs/x.md"))  # los documentos no se recortan
        self.assertFalse(solo_codigo.codigo_en_alcance("lib/b.py"))
        solo_sin = Alcance([], ["src"], conocidas, es_doc)
        self.assertFalse(solo_sin.codigo_en_alcance("src/a.py"))
        self.assertTrue(solo_sin.codigo_en_alcance("lib/b.py"))

    def test_rutas_con_corchetes_casan_literalmente(self):
        self.assertTrue(casa("app/[id]/page.tsx", "app/[id]/page.tsx"))
        self.assertTrue(casa("app/[id]/page.tsx", "app/[id]"))
        self.assertTrue(casa("app/x.tsx", "app/[xy].tsx"))  # sin ruta literal, sigue siendo glob
        with RepoDePrueba({"app/[id]/page.py": PAGOS, "docs/a.md": "Valida [[app/[id]/page.py#validar]].\n"}) as r:
            r.dk("scan")
            self.assertEqual(r.dk("check", "--solo", "app/[id]/page.py")[0], 0)

    def test_solo_que_no_casa_es_error_de_uso(self):
        with repo() as r:
            codigo, salida = r.dk("check", "--solo", "no/existe")
            self.assertEqual(codigo, 2)
            self.assertIn("no casa con ningún fichero", salida)
        with self.assertRaises(ErrorDeUso):
            Alcance(["nada"], [], ["src/a.py"], lambda _: False)

    def test_alcance_sin_anclas_no_es_un_verde_vacio(self):
        with repo() as r:
            codigo, datos = r.dk_json("check", "--solo", "src/sin_anclas.py")
            self.assertEqual(codigo, 1)
            self.assertIn("NADA_COMPROBADO", estados(datos))

    def test_scan_parcial_sella_y_poda_solo_su_parte(self):
        with RepoDePrueba({"src/pagos.py": PAGOS, "src/otro.py": OTRO,
                           "docs/a.md": "[[src/pagos.py#validar]] [[src/otro.py#informe]]\n",
                           "docs/b.md": "[[src/pagos.py#validar]]\n"}) as r:
            r.dk("scan", "--solo", "docs/b.md")
            self.assertEqual([(a["doc"], a["ancla"]) for a in r.sello()["anclas"]],
                             [("docs/b.md", "src/pagos.py#validar")])
            self.assertEqual(r.dk("check")[0], 1)  # lo de docs/a.md sigue sin sellar
            r.dk("scan")
            r.escribir("docs/a.md", "[[src/pagos.py#validar]]\n")
            r.dk("scan", "--solo", "src/pagos.py")  # no poda la de otro.py: está fuera de alcance
            self.assertIn(("docs/a.md", "src/otro.py#informe"),
                          [(a["doc"], a["ancla"]) for a in r.sello()["anclas"]])
            r.dk("scan")
            self.assertNotIn(("docs/a.md", "src/otro.py#informe"),
                             [(a["doc"], a["ancla"]) for a in r.sello()["anclas"]])


if __name__ == "__main__":
    unittest.main()
