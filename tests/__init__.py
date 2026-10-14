"""Las pruebas asertan los textos en español, así que fijan ese idioma (test_textos prueba la elección)."""

import os

os.environ["LC_ALL"] = "es_ES.UTF-8"
