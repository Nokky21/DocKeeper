"""Cada lenguaje que el README declara reconoce su definición más interior."""

import unittest

from dockeeper.bloques import Analisis, bloque_en
from tests.util import d

# (fichero, código, línea anclada, (nombre, inicio, fin) esperados)
CASOS = [
    ("a.java", '''
        public class Pagos {
            @Override
            public boolean validar(Pago p) {
                if (p.importe <= 0) {
                    return false;
                }
                return true;
            }
        }
    ''', 5, ("validar", 2, 8)),
    ("a.kt", '''
        class Pagos {
            fun validar(p: Pago): Boolean {
                return p.importe > 0
            }
        }
    ''', 3, ("validar", 2, 4)),
    ("a.scala", '''
        object Pagos {
          def validar(p: Pago): Boolean = {
            p.importe > 0
          }
        }
    ''', 3, ("validar", 2, 4)),
    ("a.cs", '''
        public class Pagos
        {
            public bool Validar(Pago p)
            {
                return p.Importe > 0;
            }
        }
    ''', 5, ("Validar", 3, 6)),
    ("a.c", '''
        static int validar(const struct pago *p)
        {
            return p->importe > 0;
        }
    ''', 3, ("validar", 1, 4)),
    ("a.cpp", '''
        class Pagos {
        public:
            bool validar(const Pago& p) const {
                return p.importe > 0;
            }
        };
    ''', 4, ("validar", 3, 5)),
    ("a.swift", '''
        struct Pagos {
            func validar(_ p: Pago) -> Bool {
                return p.importe > 0
            }
        }
    ''', 3, ("validar", 2, 4)),
    ("a.php", '''
        <?php
        class Pagos {
            public function validar($p) {
                return $p->importe > 0;
            }
        }
    ''', 4, ("validar", 3, 5)),
    ("a.dart", '''
        class Pagos {
          bool validar(Pago p) {
            return p.importe > 0;
          }
        }
    ''', 3, ("validar", 2, 4)),
    ("a.sh", '''
        validar() {
          if [ "$1" -gt 0 ]; then
            echo ok
          fi
        }
    ''', 3, ("validar", 1, 5)),
    ("a.lua", '''
        local function validar(p)
          if p.importe > 0 then
            return true
          end
          return false
        end
    ''', 3, ("validar", 1, 6)),
    ("a.ex", '''
        defmodule Pagos do
          def validar(p) do
            p.importe > 0
          end
        end
    ''', 3, ("validar", 2, 4)),
    ("a.jl", '''
        function validar(p)
            return p.importe > 0
        end
    ''', 2, ("validar", 1, 3)),
]


class PruebasLenguajes(unittest.TestCase):
    def test_definicion_mas_interior_por_lenguaje(self):
        for fichero, codigo, linea, esperado in CASOS:
            with self.subTest(fichero=fichero):
                b = bloque_en(Analisis(fichero, d(codigo).split("\n")), linea, 3)
                self.assertEqual((b.tipo, b.nombre, b.inicio, b.fin), ("definicion", *esperado))


if __name__ == "__main__":
    unittest.main()
