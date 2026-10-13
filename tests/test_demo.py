"""La demo de la web dice lo mismo que el motor real.

site/src/demo/scenarios.json describe los escenarios de la demo y sus veredictos esperados.
Aquí se pasan por la CLI de verdad; site/scripts/check-demo.ts los pasa por el port en
TypeScript que usa la web. Si uno de los dos cambia de comportamiento, falla su prueba.
"""

import json
import unittest
from pathlib import Path

from tests.util import RepoDePrueba

DATOS = json.loads((Path(__file__).resolve().parent.parent / "site/src/demo/scenarios.json").read_text(encoding="utf-8"))


def _texto(lineas):
    return "\n".join(lineas) + "\n"


def _documento():
    frases = [f"{c['text']} [[{c['anchor']}]]" for c in DATOS["claims"]]
    return _texto([DATOS["title"], "", *frases])


def _veredictos(datos):
    return {i["ancla"]: i["estado"] for i in datos["items"]}


class PruebasDemo(unittest.TestCase):
    def test_la_demo_de_la_web_dice_lo_mismo_que_el_motor(self):
        for escenario in DATOS["scenarios"]:
            with self.subTest(escenario=escenario["id"]):
                with RepoDePrueba({DATOS["file"]: _texto(DATOS["original"]), DATOS["doc"]: _documento()}) as r:
                    self.assertEqual(r.dk("scan")[0], 0)
                    sellado = {a["ancla"]: a["huella"] for a in r.sello()["anclas"]}
                    self.assertEqual(sellado, DATOS["sealed"])
                    r.escribir(DATOS["file"], _texto(escenario["code"] or DATOS["original"]))
                    self.assertEqual(_veredictos(r.dk_json("check")[1]), escenario["expected"])
                    if "afterFix" in escenario:
                        r.dk("fix")
                        self.assertEqual(_veredictos(r.dk_json("check")[1]), escenario["afterFix"])
                    if "afterAccept" in escenario:
                        r.dk("fix", "--aceptar")
                        self.assertEqual(_veredictos(r.dk_json("check")[1]), escenario["afterAccept"])


if __name__ == "__main__":
    unittest.main()
