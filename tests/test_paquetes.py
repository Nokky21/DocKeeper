"""Paquetes: monorepos y repositorios con varias piezas, cada una con su manifiesto."""

import json
import unittest

from tests.util import RepoDePrueba, d

MONOREPO = {
    "package.json": json.dumps({"name": "acme", "private": True, "workspaces": ["packages/*"]}),
    "packages/api/package.json": json.dumps({"name": "@acme/api"}),
    "packages/api/src/index.ts": "export function arrancar() {\n  return 1;\n}\n",
    "packages/api/README.md": "# API\n\nArranca en [[packages/api/src/index.ts#arrancar]].\n",
    "packages/api/examples/demo/package.json": json.dumps({"name": "demo"}),
    "packages/api/examples/demo/main.js": "function demo() {\n  return 2;\n}\n",
    "packages/web/package.json": "{ esto no es json",
    "packages/web/app.js": "function pintar() {\n  return 3;\n}\n",
    "services/cobros/go.mod": "module github.com/acme/cobros\n\ngo 1.22\n",
    "services/cobros/main.go": "package main\n\nfunc cobrar() int {\n\treturn 4\n}\n",
    "libs/core/pyproject.toml": d('''
        [build-system]
        name = "no-es-este"

        [project]
        name = "acme-core"
    '''),
    "libs/core/core.py": "def nucleo():\n    return 5\n",
    "crates/parser/Cargo.toml": '[package]\nname = "parser"\nversion = "0.1.0"\n',
    "crates/parser/src/lib.rs": "pub fn parse() -> i32 {\n    5\n}\n",
    "vendor/github.com/x/y/go.mod": "module github.com/x/y\n",
    "vendor/github.com/x/y/y.go": "package y\n",
    "docs/ARQUITECTURA.md": "Cobra en [[services/cobros/main.go#cobrar]].\n",
}


class PruebasPaquetes(unittest.TestCase):
    def test_monorepo(self):
        with RepoDePrueba(MONOREPO) as r:
            r.dk("scan")
            codigo, datos = r.dk_json("audit")
            self.assertEqual(codigo, 0)
            paquetes = {p["ruta"]: p for p in datos["paquetes"]}
            # La raíz no es un paquete; las dependencias copiadas (vendor/) tampoco.
            self.assertEqual(sorted(paquetes), ["crates/parser", "libs/core", "packages/api",
                                                "packages/api/examples/demo", "packages/web", "services/cobros"])
            self.assertEqual({k: p["nombre"] for k, p in paquetes.items()}, {
                "crates/parser": "parser", "libs/core": "acme-core", "packages/api": "@acme/api",
                "packages/api/examples/demo": "demo",
                "packages/web": "web",  # manifiesto ilegible: el nombre de la carpeta
                "services/cobros": "github.com/acme/cobros",
            })
            api = paquetes["packages/api"]
            self.assertEqual((api["ficheros"], api["definiciones"], api["ancladas"]), (2, 1, 1))  # el ejemplo es otro
            self.assertEqual(api["readme"], "packages/api/README.md")
            self.assertEqual(paquetes["packages/api/examples/demo"]["ficheros"], 2)
            cobros = paquetes["services/cobros"]
            self.assertIsNone(cobros["readme"])
            self.assertEqual((cobros["ancladas"], cobros["documentado_en"]), (1, ["docs/ARQUITECTURA.md"]))

            _, texto = r.dk("audit")
            self.assertIn("Paquetes (6)", texto)
            self.assertRegex(texto, r"packages/web/ +web +0/1 +definiciones · 2 ficheros · sin README  ← sin documentar")

    def test_manifiestos_raros(self):
        with RepoDePrueba({
            "a/package.json": "\ufeff" + json.dumps({"name": "@acme/con-bom"}),
            "b/Cargo.toml": '[package]  # núcleo\nversion = "1"\n\n[[bin]]\nname = "binario"\n',
            "c/Cargo.toml": '[[bin]]\nname = "binario"\n\n[package]\nname = "de-verdad"\n',
            "d/go.mod": 'module\t"github.com/acme/d"\n',
            "servicios/vendor/go.mod": "module github.com/acme/vendor\n",  # un paquete propio llamado vendor
        }) as r:
            _, datos = r.dk_json("audit")
            self.assertEqual({p["ruta"]: p["nombre"] for p in datos["paquetes"]}, {
                "a": "@acme/con-bom", "b": "b", "c": "de-verdad", "d": "github.com/acme/d",
                "servicios/vendor": "github.com/acme/vendor",
            })

    def test_alcance_de_un_paquete(self):
        with RepoDePrueba(MONOREPO) as r:
            _, datos = r.dk_json("audit", "--solo", "services/cobros")
            self.assertEqual([p["ruta"] for p in datos["paquetes"]], ["services/cobros"])

    def test_repositorio_de_una_pieza(self):
        with RepoDePrueba({"package.json": "{}", "src/a.js": "function a() {}\n"}) as r:
            _, datos = r.dk_json("audit")
            self.assertEqual(datos["paquetes"], [])
            _, texto = r.dk("audit")
            self.assertNotIn("Paquetes", texto)


if __name__ == "__main__":
    unittest.main()
