"""Criterios del motor: MOVED, CHANGED, DESAPARECIDO, fix, scan y el verde vacío."""

import unittest

from tests.util import RepoDePrueba, d, estados, por_ancla

PAGOS = d('''
    import os


    def validar_pago(pago):
        if pago["importe"] <= 0:
            raise ValueError("importe no válido")
        return True


    def cobrar(pago):
        validar_pago(pago)
        return {"estado": "cobrado"}
''')

DOC = d('''
    # Pagos

    Antes de cobrar se valida el pago [[src/pagos.py#validar_pago]].
    El cobro devuelve su estado [[src/pagos.py:12]].
''')


def repo_base():
    return RepoDePrueba({"src/pagos.py": PAGOS, "docs/pagos.md": DOC})


class PruebasCheck(unittest.TestCase):
    def test_mover_funcion_no_falla_y_fix_la_recoloca(self):
        with repo_base() as r:
            self.assertEqual(r.dk("scan")[0], 0)
            # Se insertan líneas por encima: las dos funciones bajan de sitio.
            r.escribir("src/pagos.py", PAGOS.replace("import os\n", "import os\nimport sys\n\n\nLIMITE = 10\n"))
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 0, datos)
            self.assertEqual(sorted(estados(datos)), ["MOVED", "MOVED"])

            codigo, _ = r.dk("fix")
            self.assertEqual(codigo, 0)
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 0)
            self.assertEqual(estados(datos), ["OK", "OK"])
            ancla_linea = next(a for a in r.sello()["anclas"] if a["ancla"] == "src/pagos.py:12")
            self.assertEqual(ancla_linea["linea"], 16)  # recolocada 4 líneas más abajo
            self.assertEqual(ancla_linea["inicio"], 14)

    def test_cambiar_contenido_falla(self):
        with repo_base() as r:
            r.dk("scan")
            r.escribir("src/pagos.py", PAGOS.replace('<= 0', '< 0'))
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            items = por_ancla(datos)
            self.assertEqual(items["src/pagos.py#validar_pago"]["estado"], "CHANGED")
            self.assertEqual(items["src/pagos.py:12"]["estado"], "OK")
            codigo, texto = r.dk("check")
            self.assertIn("CHANGED", texto)
            self.assertIn("FALLA", texto)

    def test_cambio_dentro_de_una_funcion_anclada_por_linea(self):
        with repo_base() as r:
            r.dk("scan")
            # La línea 12 está dentro de «cobrar»: el bloque es la función entera.
            r.escribir("src/pagos.py", PAGOS.replace('"cobrado"', '"pendiente"'))
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            self.assertEqual(por_ancla(datos)["src/pagos.py:12"]["estado"], "CHANGED")

    def test_fix_no_toca_el_documento(self):
        with repo_base() as r:
            r.dk("scan")
            antes = r.leer_bytes("docs/pagos.md")
            r.escribir("src/pagos.py", "\n\n" + PAGOS.replace('<= 0', '< 0'))
            r.dk("fix")
            self.assertEqual(r.leer_bytes("docs/pagos.md"), antes)
            codigo, _ = r.dk("fix", "--aceptar")
            self.assertEqual(codigo, 0)
            self.assertEqual(r.leer_bytes("docs/pagos.md"), antes)
            codigo, datos = r.dk_json("check")
            self.assertEqual((codigo, estados(datos)), (0, ["OK", "OK"]))

    def test_fichero_desaparecido(self):
        with repo_base() as r:
            r.dk("scan")
            r.borrar("src/pagos.py")
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            self.assertEqual(estados(datos), ["DESAPARECIDO", "DESAPARECIDO"])

    def test_reformatear_no_rompe(self):
        with repo_base() as r:
            r.dk("scan")
            reformateado = (PAGOS.replace('    if pago["importe"] <= 0:', '    if  pago["importe"]  <=  0:   ')
                            .replace("    return True", "\n    return True\n"))
            r.escribir("src/pagos.py", reformateado)
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 0, datos)
            self.assertNotIn("CHANGED", estados(datos))

    def test_sin_sellar_falla(self):
        with repo_base() as r:
            r.dk("scan")
            r.escribir("docs/pagos.md", DOC + "Y además cobra [[src/pagos.py#cobrar]].\n")
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            self.assertEqual(por_ancla(datos)["src/pagos.py#cobrar"]["estado"], "SIN_SELLAR")

    def test_huerfana_avisa_y_fix_la_quita(self):
        with repo_base() as r:
            r.dk("scan")
            r.escribir("docs/pagos.md", DOC.replace(" [[src/pagos.py:12]]", ""))
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 0)
            self.assertIn("HUERFANA", estados(datos))
            r.dk("fix")
            self.assertEqual([a["ancla"] for a in r.sello()["anclas"]], ["src/pagos.py#validar_pago"])

    def test_scan_ensena_el_bloque(self):
        with repo_base() as r:
            codigo, datos = r.dk_json("scan")
            self.assertEqual(codigo, 0)
            items = por_ancla(datos)
            simbolo = items["src/pagos.py#validar_pago"]["bloque"]
            self.assertEqual((simbolo["tipo"], simbolo["inicio"], simbolo["fin"]), ("definicion", 4, 7))
            self.assertEqual(simbolo["primera"], "def validar_pago(pago):")
            linea = items["src/pagos.py:12"]["bloque"]
            self.assertEqual((linea["nombre"], linea["inicio"], linea["fin"]), ("cobrar", 10, 12))
            _, texto = r.dk("scan", "--resellar")
            self.assertIn("definición «cobrar» src/pagos.py:10-12", texto)
            self.assertIn("def cobrar(pago):", texto)

    def test_scan_no_resella_lo_ya_sellado(self):
        with repo_base() as r:
            r.dk("scan")
            r.escribir("src/pagos.py", PAGOS.replace('<= 0', '< 0'))
            _, datos = r.dk_json("scan")
            self.assertEqual(estados(datos), ["SELLADA", "SELLADA"])
            self.assertEqual(r.dk("check")[0], 1)

    def test_nada_comprobado_falla(self):
        with RepoDePrueba({"src/a.py": "x = 1\n", "README.md": "# Nada anclado\n"}) as r:
            codigo, datos = r.dk_json("check")
            self.assertEqual(codigo, 1)
            self.assertEqual(estados(datos), ["NADA_COMPROBADO"])

    def test_ancla_rota_al_escribirla(self):
        with RepoDePrueba({"src/a.py": "def f():\n    return 1\n",
                           "README.md": "[[src/b.py:1]] [[src/a.py#g]] [[src/a.py:9]] [[../fuera.py:1]]\n"}) as r:
            codigo, datos = r.dk_json("scan")
            self.assertEqual(codigo, 1)
            self.assertEqual(sorted(estados(datos)), ["ANCLA_MAL_ESCRITA", "FUERA_DE_RANGO", "NO_EXISTE", "SIN_SIMBOLO"])

    def test_simbolo_movido_es_moved_y_fix_lo_recoloca(self):
        with repo_base() as r:
            r.dk("scan")
            r.escribir("src/pagos.py", "# cabecera\n\n" + PAGOS)
            codigo, datos = r.dk_json("check")
            self.assertEqual(por_ancla(datos)["src/pagos.py#validar_pago"]["estado"], "MOVED")
            r.dk("fix")
            entrada = next(a for a in r.sello()["anclas"] if a["ancla"] == "src/pagos.py#validar_pago")
            self.assertEqual((entrada["inicio"], entrada["fin"]), (6, 9))


if __name__ == "__main__":
    unittest.main()
