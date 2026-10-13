"""Bloques: definición más interior, ventana recortada y símbolos, en varios lenguajes."""

import unittest

from dockeeper import huellas as H
from dockeeper.bloques import Analisis, bloque_en, bloques_de_simbolo
from tests.util import d


def bloque(ruta, texto, linea, ventana=3):
    b = bloque_en(Analisis(ruta, texto.split("\n")), linea, ventana)
    return b.tipo, b.nombre, b.inicio, b.fin


def simbolo(ruta, texto, nombre):
    return [(b.tipo, b.inicio, b.fin) for b in bloques_de_simbolo(Analisis(ruta, texto.split("\n")), nombre)]


PY = d('''
    import os

    LIMITE = {
        "diario": 10,
    }


    class Cobros:
        """Cobros.

    Texto pegado a la izquierda dentro de una cadena.
    """

        @staticmethod
        def cobrar(pago):
            total = pago["importe"]
            return total

        def anular(self):
            return None


    def suelta():
        return "def falsa(): {"
''')

TS = d('''
    import { x } from "y";

    export async function validarPago(pago: Pago): Promise<boolean> {
      const msg = "llave en texto { que no cuenta";
      if (pago.importe <= 0) {
        return false;
      }
      return true;
    }

    export class Cobros {
      private total = 0;

      cobrar(pago: Pago): void {
        this.total += pago.importe;
      }

      anular() {
        foo(bar);
      }
    }

    export const sumar = (a: number, b: number) => {
      return a + b;
    };

    export const handler = async (
      evento: Evento,
    ): Promise<void> => {
      await procesar(evento);
    };
''')


class PruebasBloques(unittest.TestCase):
    def test_python_definicion_mas_interior(self):
        self.assertEqual(bloque("a.py", PY, 16), ("definicion", "cobrar", 14, 17))
        self.assertEqual(bloque("a.py", PY, 9), ("definicion", "Cobros", 8, 20))
        self.assertEqual(bloque("a.py", PY, 18), ("definicion", "Cobros", 8, 20))
        self.assertEqual(bloque("a.py", PY, 24), ("definicion", "suelta", 23, 24))

    def test_python_cadena_pegada_a_la_izquierda_no_corta_la_clase(self):
        self.assertEqual(bloque("a.py", PY, 11)[2:], (8, 20))

    def test_ventana_recortada_si_no_hay_definicion(self):
        tipo, nombre, inicio, fin = bloque("a.py", PY, 2)
        self.assertEqual((tipo, nombre, inicio), ("ventana", None, 1))
        self.assertEqual(fin, 5)  # recortada para acabar en una línea con contenido

    def test_typescript(self):
        self.assertEqual(bloque("a.ts", TS, 5), ("definicion", "validarPago", 3, 9))
        self.assertEqual(bloque("a.ts", TS, 15), ("definicion", "cobrar", 14, 16))
        self.assertEqual(bloque("a.ts", TS, 12), ("definicion", "Cobros", 11, 21))
        self.assertEqual(bloque("a.ts", TS, 19), ("definicion", "anular", 18, 20))
        self.assertEqual(bloque("a.ts", TS, 24), ("definicion", "sumar", 23, 25))
        self.assertEqual(bloque("a.ts", TS, 30), ("definicion", "handler", 27, 31))

    def test_go_rust_ruby(self):
        go = d('''
            package pagos

            func (r *Repo) Guardar(p Pago) error {
            	if p.Importe <= 0 {
            		return errInvalido
            	}
            	return nil
            }
        ''')
        self.assertEqual(bloque("a.go", go, 5), ("definicion", "Guardar", 3, 8))
        rust = d('''
            pub fn primero<'a>(x: &'a str) -> &'a str {
                let c = '{';
                x
            }
        ''')
        self.assertEqual(bloque("a.rs", rust, 3), ("definicion", "primero", 1, 4))
        ruby = d('''
            class Cobro
              def cobrar(pago)
                pago.importe
              rescue StandardError
                nil
              end
            end
        ''')
        self.assertEqual(bloque("a.rb", ruby, 5), ("definicion", "cobrar", 2, 6))

    def test_simbolos(self):
        self.assertEqual(simbolo("a.py", PY, "cobrar"), [("definicion", 14, 17)])
        self.assertEqual(simbolo("a.py", PY, "Cobros.anular"), [("definicion", 19, 20)])
        self.assertEqual(simbolo("a.py", PY, "Otra.anular"), [])
        self.assertEqual(simbolo("a.py", PY, "LIMITE"), [("declaracion", 3, 5)])
        self.assertEqual(simbolo("a.py", PY, "falsa"), [])  # está dentro de una cadena
        self.assertEqual(simbolo("a.ts", TS, "Cobros.cobrar"), [("definicion", 14, 16)])
        self.assertEqual(simbolo("a.ts", TS, "foo"), [])  # una llamada no es una definición

    def test_fichero_sin_lenguaje_usa_ventana(self):
        yml = "a: 1\nb: 2\n\n\nc: 3\nd: 4\ne: 5\n"
        self.assertEqual(bloque("x.yml", yml, 1, ventana=2), ("ventana", None, 1, 2))


class PruebasHuellas(unittest.TestCase):
    def test_normalizar_ignora_espacios_y_lineas_vacias(self):
        a = ["def f(x):", "    return  x + 1   ", ""]
        b = ["", "def  f(x):", "", "\treturn x + 1"]
        self.assertEqual(H.huella_de(a), H.huella_de(b))

    def test_cambiar_la_logica_cambia_la_huella(self):
        self.assertNotEqual(H.huella_de(["return x + 1"]), H.huella_de(["return x - 1"]))

    def test_buscar(self):
        lineas = ["a", "", "b", "c", "b", "", "c"]
        objetivo, n = H.huella_de(["b", "c"])
        self.assertEqual(H.buscar(lineas, objetivo, n), [(3, 4), (5, 7)])


if __name__ == "__main__":
    unittest.main()
