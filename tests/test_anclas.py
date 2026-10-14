"""Lectura de anclas en Markdown: formas válidas y lo que se salta."""

import unittest

from dockeeper.markdown import analizar, leer_ancla
from tests.util import d


def anclas(texto):
    doc = analizar("doc.md", texto.split("\n"))
    return [(a.linea_doc, a.texto, a.oculta) for a in doc.anclas], doc


class PruebasAnclas(unittest.TestCase):
    def test_formas_visibles_y_ocultas(self):
        encontradas, doc = anclas(d('''
            Valida [[src/pagos.ts:147]] y [[src/pagos.ts#validarPago]].
            Método [[src/cobros.py#Cobros.cobrar]]. <!-- dockeeper: lib/a.go:3, lib/b.go#Run -->
            Ruta con punto inicial [[./src/x.py:1]].
        '''))
        self.assertEqual(encontradas, [
            (1, "src/pagos.ts:147", False),
            (1, "src/pagos.ts#validarPago", False),
            (2, "lib/a.go:3", True),
            (2, "lib/b.go#Run", True),
            (2, "src/cobros.py#Cobros.cobrar", False),
            (3, "src/x.py:1", False),
        ])
        self.assertEqual(doc.problemas, [])

    def test_salta_bloques_y_codigo_en_linea(self):
        encontradas, doc = anclas(d('''
            Sintaxis: `[[ruta/fichero.ext:147]]` y ``[[a.py#x `con` acento]]``.
            ```markdown
            [[ejemplo/falso.py:1]]
            <!-- dockeeper: ejemplo/falso.py:2 -->
            ```
            ~~~~
            [[otro/falso.py#f]]
            ```
            sigue dentro de la valla de tildes [[tambien/falso.py:3]]
            ~~~~
            <!-- un comentario normal con [[comentado/falso.py:4]] -->
            <!-- comentario
            de varias líneas [[comentado/falso.py:5]]
            -->
            `<!-- dockeeper: en/codigo.py:6 -->`
            Solo esta cuenta [[real/bueno.py:9]].
        '''))
        self.assertEqual(encontradas, [(16, "real/bueno.py:9", False)])
        self.assertEqual(len(doc.bloques), 2)
        self.assertEqual(doc.bloques[0].inicio, 3)
        self.assertEqual(doc.bloques[0].info, "markdown")

    def test_rutas_con_corchetes(self):
        encontradas, doc = anclas(d('''
            Ruta dinámica [[app/[id]/page.tsx#GET]] y [[src/pages/[...slug].astro:3]].
            Opcional [[app/[[...slug]]/page.tsx:2]] y con matcher [[src/routes/[page=integer]/+page.ts#load]].
            Oculta <!-- dockeeper: app/[id]/route.ts:4 --> y un wikilink [[Nota [borrador]]].
        '''))
        self.assertEqual(encontradas, [
            (1, "app/[id]/page.tsx#GET", False),
            (1, "src/pages/[...slug].astro:3", False),
            (2, "app/[[...slug]]/page.tsx:2", False),
            (2, "src/routes/[page=integer]/+page.ts#load", False),
            (3, "app/[id]/route.ts:4", True),
        ])
        self.assertEqual(doc.problemas, [])

    def test_wikilinks_no_son_anclas(self):
        encontradas, _ = anclas("Ver [[Nota]] y [[Nota#Encabezado]] y [[otra nota]].\n")
        self.assertEqual(encontradas, [])

    def test_anclas_mal_escritas(self):
        _, doc = anclas(d('''
            Fuera de la raíz [[../secreto.py:1]].
            <!-- dockeeper: no-es-ancla -->
            <!-- dockeeper: a.py:1
            -->
            Línea cero [[a.py:0]].
        '''))
        motivos = [(p.linea_doc, p.motivo) for p in doc.problemas]
        self.assertEqual([n for n, _ in motivos], [1, 2, 3, 5])
        self.assertIn("sale del repositorio", motivos[0][1])
        self.assertIn("cerrarse en la misma línea", motivos[2][1])

    def test_leer_ancla(self):
        self.assertEqual(leer_ancla("src/a.py:3"), ("src/a.py", 3, None, "src/a.py:3"))
        self.assertEqual(leer_ancla("./src/a.py#Clase.m"), ("src/a.py", None, "Clase.m", "src/a.py#Clase.m"))
        self.assertEqual(leer_ancla("app/[id]/page.tsx#GET"), ("app/[id]/page.tsx", None, "GET", "app/[id]/page.tsx#GET"))
        for malo in ("src/a.py", "/etc/passwd:1", "a.py#", "a.py#Clase.", "../a.py:1"):
            with self.assertRaises(ValueError, msg=malo):
                leer_ancla(malo)


if __name__ == "__main__":
    unittest.main()
