"""Utilidades de prueba: repositorios temporales y ejecución de la CLI en proceso."""

import io
import json
import subprocess
import tempfile
import textwrap
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from dockeeper.cli import main


def d(texto: str) -> str:
    """Quita la sangría común y el salto inicial de un texto de prueba."""
    return textwrap.dedent(texto).lstrip("\n")


class RepoDePrueba:
    def __init__(self, ficheros: dict, config: dict = None):
        self._tmp = tempfile.TemporaryDirectory(prefix="dockeeper-")
        self.raiz = Path(self._tmp.name).resolve()
        if config is not None:
            self.escribir(".dockeeper.json", json.dumps(config))
        for ruta, texto in ficheros.items():
            self.escribir(ruta, texto)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._tmp.cleanup()

    def escribir(self, ruta: str, texto: str) -> None:
        p = self.raiz / ruta
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")

    def leer(self, ruta: str) -> str:
        return (self.raiz / ruta).read_text(encoding="utf-8")

    def leer_bytes(self, ruta: str) -> bytes:
        return (self.raiz / ruta).read_bytes()

    def borrar(self, ruta: str) -> None:
        (self.raiz / ruta).unlink()

    def sello(self) -> dict:
        return json.loads(self.leer(".dockeeper.sello.json"))

    def dk(self, *args):
        """Ejecuta la CLI → (código de salida, salida de texto)."""
        salida, errores = io.StringIO(), io.StringIO()
        with redirect_stdout(salida), redirect_stderr(errores):
            try:
                codigo = main([*args, "--raiz", str(self.raiz)])
            except SystemExit as e:
                codigo = e.code
        return codigo, salida.getvalue() + errores.getvalue()

    def dk_json(self, *args):
        """Ejecuta la CLI con --json → (código de salida, datos)."""
        codigo, salida = self.dk(*args, "--json")
        return codigo, json.loads(salida)

    def git(self, *args) -> str:
        r = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=self.raiz,
                           capture_output=True, text=True, encoding="utf-8", check=True)
        return r.stdout

    def iniciar_git(self) -> None:
        self.git("init", "-q")
        self.git("config", "user.name", "Prueba")
        self.git("config", "user.email", "prueba@example.invalid")

    def commit(self, mensaje: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", mensaje)
        return self.git("rev-parse", "HEAD").strip()


def estados(datos: dict) -> list:
    return [i["estado"] for i in datos["items"]]


def por_ancla(datos: dict) -> dict:
    return {i["ancla"]: i for i in datos["items"] if i.get("ancla")}
