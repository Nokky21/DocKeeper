"""review: qué documentación toca un cambio y qué código nuevo o cambiado queda sin documentar."""

import shutil
import unittest

from tests.util import RepoDePrueba, d

PAGOS = d('''
    def validar(pago):
        return pago > 0


    def cobrar(pago):
        return pago


    class Caja:
        def abrir(self):
            return True
''')


def simbolos(datos: dict) -> dict:
    return {s["simbolo"]: s["estado"] for s in datos["sin_documentar"]}


@unittest.skipIf(shutil.which("git") is None, "hace falta git")
class PruebasRevision(unittest.TestCase):
    def repo(self):
        r = RepoDePrueba({"src/pagos.py": PAGOS, "docs/pagos.md": "Valida [[src/pagos.py#validar]].\n"})
        r.iniciar_git()
        r.dk("scan")
        r.commit("feat: pagos")
        return r

    def test_cambio_anclado_y_codigo_nuevo_sin_documentar(self):
        with self.repo() as r:
            r.escribir("src/pagos.py", PAGOS.replace("pago > 0", "pago >= 0").replace("return pago\n", "return -pago\n")
                       + "\n\ndef reembolsar(pago):\n    return pago\n")
            r.commit("feat: reembolsos")
            codigo, datos = r.dk_json("review")
            self.assertEqual(codigo, 0)
            self.assertEqual(datos["cambios"]["codigo"], ["src/pagos.py"])
            self.assertEqual([(i["estado"], i["ancla"]) for i in datos["afirmaciones"]],
                             [("CHANGED", "src/pagos.py#validar")])
            self.assertEqual(simbolos(datos), {"src/pagos.py#cobrar": "cambiada",
                                               "src/pagos.py#reembolsar": "nueva"})
            nueva = next(s for s in datos["sin_documentar"] if s["estado"] == "nueva")
            self.assertEqual(nueva["documentos"], ["docs/pagos.md"])  # ya hay un documento de ese fichero

            _, texto = r.dk("review")
            self.assertIn("CHANGED", texto)
            self.assertIn("nueva     src/pagos.py#reembolsar", texto)

    def test_metodo_nuevo_y_clase_nueva(self):
        with self.repo() as r:
            r.escribir("src/pagos.py", PAGOS + d('''
                    def cerrar(self):
                        return False


                class Banco:
                    def ingresar(self):
                        return 1

                    def retirar(self):
                        return 2
            '''))
            r.commit("feat: banco")
            _, datos = r.dk_json("review")
            # El método nuevo de una clase que ya existía se nombra con su contenedor; de una clase
            # nueva sale la clase, no cada método.
            self.assertEqual(simbolos(datos), {"src/pagos.py#Caja.cerrar": "nueva", "src/pagos.py#Banco": "nueva"})
            self.assertEqual(datos["afirmaciones"], [])

    def test_sin_nada_que_revisar(self):
        with self.repo() as r:
            r.escribir("LICENCIA", "MIT\n")
            r.commit("chore: licencia")
            codigo, texto = r.dk("review")
            self.assertEqual(codigo, 0)
            self.assertIn("Nada que revisar", texto)
            _, datos = r.dk_json("review")
            self.assertEqual((datos["afirmaciones"], datos["sin_documentar"], datos["decisiones"]), ([], [], []))

    def test_primer_commit_todo_es_nuevo(self):
        with RepoDePrueba({"src/a.py": "def uno():\n    return 1\n"}) as r:
            r.iniciar_git()
            r.commit("feat: inicio")
            codigo, datos = r.dk_json("review")
            self.assertEqual(codigo, 0)
            self.assertIsNone(datos["base"])
            self.assertEqual(simbolos(datos), {"src/a.py#uno": "nueva"})

    def test_desde_una_rama_cuenta_desde_la_bifurcacion(self):
        with self.repo() as r:
            principal = r.git("rev-parse", "--abbrev-ref", "HEAD").strip()
            r.git("checkout", "-q", "-b", "rama")
            r.escribir("src/extra.py", "def extra():\n    return 1\n")
            r.commit("feat: extra")
            r.escribir("src/otro.py", "def otro():\n    return 2\n")
            r.commit("feat: otro")
            _, datos = r.dk_json("review", "--desde", principal)
            self.assertEqual(simbolos(datos), {"src/extra.py#extra": "nueva", "src/otro.py#otro": "nueva"})
            _, datos = r.dk_json("review")  # por defecto, solo el último commit
            self.assertEqual(simbolos(datos), {"src/otro.py#otro": "nueva"})
            codigo, salida = r.dk("review", "--desde", "no-existe")
            self.assertEqual(codigo, 2)

    def test_fichero_borrado_y_documento_sin_sellar(self):
        with self.repo() as r:
            r.borrar("src/pagos.py")
            r.escribir("docs/nuevo.md", "Cobra [[src/cobros.py#cobrar]].\n")
            r.escribir("src/cobros.py", "def cobrar():\n    return 1\n")
            r.commit("refactor: cobros")
            _, datos = r.dk_json("review")
            self.assertEqual({(i["estado"], i["ancla"]) for i in datos["afirmaciones"]},
                             {("DESAPARECIDO", "src/pagos.py#validar"),
                              ("SIN_SELLAR", "src/cobros.py#cobrar")})
            # Lo anclado (aunque falte sellarlo) no se repite como «sin documentar».
            self.assertEqual(simbolos(datos), {})

    def test_decisiones_de_los_commits_sin_documentar(self):
        with self.repo() as r:
            r.escribir("src/a.py", "x = 1\n")
            sha = r.commit("feat: a\n\nDecision: separar a\nWhy: claridad")
            _, datos = r.dk_json("review")
            self.assertEqual([x["decision"] for x in datos["decisiones"]], ["separar a"])
            r.escribir("DECISIONES.md", f"# Decisiones\n\n## Separar a\n\n- Motivo: claridad ({sha[:7]})\n")
            _, datos = r.dk_json("review")
            self.assertEqual(datos["decisiones"], [])  # ya documentada

    def test_lineas_borradas_que_empiezan_por_guiones(self):
        # En Lua «--» es un comentario: borrar esa línea da «--- …» dentro del diff, que no es una cabecera.
        lua = "function saludo()\n-- comentario\n  return 1\nend\n\nfunction otra()\n  return 2\nend\n"
        with RepoDePrueba({"src/a.lua": lua}) as r:
            r.iniciar_git()
            r.commit("feat: lua")
            r.escribir("src/a.lua", lua.replace("-- comentario\n", "").replace("return 2", "return 3"))
            r.commit("refactor: lua")
            _, datos = r.dk_json("review")
            self.assertEqual(datos["cambios"]["codigo"], ["src/a.lua"])
            self.assertEqual(simbolos(datos), {"src/a.lua#saludo": "cambiada", "src/a.lua#otra": "cambiada"})

    def test_renombrar_un_fichero_anclado(self):
        with self.repo() as r:
            r.git("mv", "src/pagos.py", "src/cobros.py")
            r.commit("refactor: renombrar")
            _, datos = r.dk_json("review")
            self.assertEqual(datos["cambios"]["codigo"], ["src/cobros.py", "src/pagos.py"])
            self.assertEqual([(i["estado"], i["ancla"]) for i in datos["afirmaciones"]],
                             [("DESAPARECIDO", "src/pagos.py#validar")])

    def test_rutas_con_corchetes_no_son_comodines(self):
        # Rutas dinámicas de Next.js o Astro: «[id]» es parte del nombre, no un comodín.
        with RepoDePrueba({"src/pages/[id].ts": "export function cargar() {\n  return 1;\n}\n"}) as r:
            r.iniciar_git()
            r.commit("feat: ruta")
            r.escribir("src/pages/[id].ts", "export function cargar() {\n  return 2;\n}\n")
            r.commit("fix: ruta")
            codigo, datos = r.dk_json("review")
            self.assertEqual(codigo, 0, datos)
            self.assertEqual(simbolos(datos), {"src/pages/[id].ts#cargar": "cambiada"})

    def test_sin_git_es_error_de_uso(self):
        with RepoDePrueba({"src/a.py": "x = 1\n", ".dockeeper.json": "{}"}) as r:
            codigo, salida = r.dk("review")
            self.assertEqual(codigo, 2)
            self.assertIn("necesita un repositorio git", salida)


if __name__ == "__main__":
    unittest.main()
