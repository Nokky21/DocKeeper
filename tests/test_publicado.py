"""Documentación publicada: sin anclas ni rutas internas, sin código copiado, con vínculos fuera del texto."""

import unittest

from tests.util import RepoDePrueba, d, estados

PAGOS = d('''
    def validar_pago(pago):
        importe = pago["importe"]
        if importe <= 0:
            raise ValueError("importe no válido")
        return True
''')
CONFIG = {"publico": ["docs/publica/"], "publicado": ["README.md"]}
GUIA = "# Guía\n\nEl pago se valida antes de cobrarlo.\n"


def repo(ficheros):
    return RepoDePrueba({"src/pagos.py": PAGOS, **ficheros}, config=CONFIG)


class PruebasPublicado(unittest.TestCase):
    def test_publico_con_anclas_internas_falla(self):
        with repo({"docs/publica/guia.md": "Se valida el pago [[src/pagos.py#validar_pago]].\n"
                                           "<!-- dockeeper: src/pagos.py:2 -->\n"}) as r:
            codigo, datos = r.dk_json("scan")
            self.assertEqual(codigo, 1)
            self.assertEqual(estados(datos), ["ANCLA_INTERNA", "ANCLA_INTERNA"])
            self.assertFalse((r.raiz / ".dockeeper.sello.json").exists())  # no se sella nada
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            self.assertEqual(estados(datos), ["ANCLA_INTERNA", "ANCLA_INTERNA"])

    def test_publico_con_rutas_internas_falla(self):
        with repo({"docs/publica/guia.md": d('''
                El fichero src/pagos.py contiene la validación.
                Código: https://git.example.com/org/repo/blob/main/src/pagos.py#L2
                La carpeta src/ a secas es demasiado genérica para avisar.
            ''')}) as r:
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            rutas = [(i["linea_doc"], i["estado"]) for i in datos["items"]]
            self.assertEqual(rutas, [(1, "RUTA_INTERNA"), (2, "RUTA_INTERNA")])

    def test_publico_limpio_pasa(self):
        with repo({"docs/publica/guia.md": GUIA}) as r:
            self.assertEqual(r.dk("check")[0], 0)

    def test_publicado_puede_anclar_a_su_codigo(self):
        with repo({"README.md": "Valida pagos <!-- dockeeper: src/pagos.py#validar_pago --> [[src/pagos.py:3]].\n"}) as r:
            self.assertEqual(r.dk("scan")[0], 0)
            codigo, datos = r.dk_json("check")
            self.assertEqual((codigo, estados(datos)), (0, ["OK", "OK"]))

    def test_codigo_copiado_falla_y_dice_de_donde(self):
        readme = d('''
            # Pagos

            ```python
            # ejemplo
            importe = pago["importe"]
            if importe <= 0:
                    raise   ValueError("importe no válido")
            ```
        ''')
        with repo({"README.md": readme}) as r:
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            copia = next(i for i in datos["items"] if i["estado"] == "CODIGO_COPIADO")
            self.assertEqual(copia["fuente"], "src/pagos.py:2")
            self.assertEqual(copia["linea_doc"], 5)
            codigo, texto = r.dk("check")
            self.assertIn("src/pagos.py:2", texto)
        with repo({"docs/publica/guia.md": readme}) as r:  # también en la clase «publico»
            self.assertIn("CODIGO_COPIADO", estados(r.dk_json("check")[1]))

    def test_umbral_de_copia(self):
        dos_lineas = "```\nimporte = pago[\"importe\"]\nif importe <= 0:\n```\n"
        with repo({"README.md": dos_lineas}) as r:
            self.assertEqual(r.dk("check")[0], 0)  # dos líneas se dejan pasar a propósito
            r.escribir(".dockeeper.json", '{"publicado": ["README.md"], "bloque_minimo": 2}')
            self.assertIn("CODIGO_COPIADO", estados(r.dk_json("check")[1]))

    def test_lineas_sin_contenido_no_hacen_copia(self):
        codigo = "def f():\n    return [\n        1,\n    ]\n    }\n    }\n    }\n"
        with RepoDePrueba({"src/a.py": codigo, "README.md": "```\n}\n}\n}\n```\n"},
                          config={"publicado": ["README.md"]}) as r:
            self.assertEqual(r.dk("check")[0], 0)

    def test_documento_interno_puede_copiar_codigo(self):
        with repo({"docs/interno.md": "```\nimporte = pago[\"importe\"]\nif importe <= 0:\n"
                                      "raise ValueError(\"importe no válido\")\n```\n[[src/pagos.py:2]]\n"}) as r:
            r.dk("scan")
            self.assertEqual(r.dk("check")[0], 0)

    def test_vinculo_se_comprueba_sin_aparecer_en_el_texto(self):
        with repo({"docs/publica/guia.md": GUIA}) as r:
            codigo, datos = r.dk_json("link", "docs/publica/guia.md:3", "src/pagos.py#validar_pago")
            self.assertEqual(codigo, 0)
            self.assertEqual(datos["items"][0]["estado"], "VINCULADO")
            self.assertEqual(r.leer("docs/publica/guia.md"), GUIA)  # el documento no se toca
            self.assertNotIn("src/", r.leer("docs/publica/guia.md"))
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 0)
            vinculo = next(i for i in datos["items"] if i["tipo"] == "vinculo")
            self.assertEqual((vinculo["estado"], vinculo["ancla"]), ("OK", "src/pagos.py#validar_pago"))
            r.escribir("src/pagos.py", PAGOS.replace("<= 0", "< 0"))
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            self.assertEqual(estados(datos), ["CHANGED"])

    def test_vinculo_frase_movida_y_reescrita(self):
        with repo({"docs/publica/guia.md": GUIA}) as r:
            r.dk("link", "docs/publica/guia.md:3", "src/pagos.py#validar_pago")
            movida = "# Guía\n\nIntroducción nueva.\n\nEl pago se valida antes de cobrarlo.\n"
            r.escribir("docs/publica/guia.md", movida)
            codigo, datos = r.dk_json("check")
            self.assertEqual((codigo, estados(datos)), (0, ["MOVED"]))
            r.dk("fix")
            self.assertEqual(r.leer("docs/publica/guia.md"), movida)
            self.assertEqual(r.sello()["vinculos"][0]["linea_doc"], 5)
            self.assertEqual(estados(r.dk_json("check")[1]), ["OK"])
            r.escribir("docs/publica/guia.md", movida.replace("antes de cobrarlo", "al final"))
            codigo, datos = r.dk_json("check")
            self.assertEqual((codigo, estados(datos)), (1, ["VINCULO_SUELTO"]))
            codigo, datos = r.dk_json("link", "docs/publica/guia.md:5", "--quitar")
            self.assertEqual(estados(datos), ["DESVINCULADO"])
            self.assertEqual(r.sello()["vinculos"], [])

    def test_errores_de_link(self):
        with repo({"docs/publica/guia.md": GUIA}) as r:
            self.assertEqual(r.dk("link", "docs/publica/guia.md:2", "src/pagos.py#validar_pago")[0], 2)  # línea vacía
            self.assertEqual(r.dk("link", "docs/publica/guia.md", "src/pagos.py#validar_pago")[0], 2)
            self.assertEqual(r.dk("link", "docs/publica/guia.md:3")[0], 2)  # falta el ancla
            self.assertEqual(r.dk("link", "docs/publica/guia.md:3", "src/pagos.py")[0], 2)
            codigo, datos = r.dk_json("link", "docs/publica/guia.md:3", "src/pagos.py#no_existe")
            self.assertEqual((codigo, estados(datos)), (1, ["SIN_SIMBOLO"]))
            self.assertEqual(r.dk("link", "docs/publica/guia.md:3", "--quitar")[0], 2)  # no hay nada que quitar


if __name__ == "__main__":
    unittest.main()
