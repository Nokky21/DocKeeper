"""Acceso al repositorio: listado de ficheros, lectura de texto y clase de cada documento."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from . import rutas as R
from .bloques import Analisis
from .config import NOMBRE_CONFIG, NOMBRE_SELLO, Config

_CARPETAS_IGNORADAS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox", ".mypy_cache",
                       ".pytest_cache", "dist", "build", ".next", "target"}
_MAX_BYTES = 2_000_000


class Repo:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.raiz = cfg.raiz
        self._raiz_real = cfg.raiz.resolve()
        self._ficheros: Optional[List[str]] = None
        self._lineas: Dict[str, Optional[List[str]]] = {}
        self._analisis: Dict[str, Optional[Analisis]] = {}

    @property
    def ficheros(self) -> List[str]:
        """Ficheros del repositorio (respeta .gitignore si hay git), sin los propios de dockeeper."""
        if self._ficheros is None:
            rutas = self._listar_git()
            if rutas is None:
                rutas = self._listar_carpeta()
            propios = {NOMBRE_CONFIG, NOMBRE_SELLO}
            self._ficheros = sorted({r for r in rutas if r not in propios and (self.raiz / r).is_file()})
        return self._ficheros

    def _listar_git(self) -> Optional[List[str]]:
        try:
            r = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                               cwd=self.raiz, capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            return None
        return [p for p in r.stdout.decode("utf-8", "surrogateescape").split("\0") if p]

    def _listar_carpeta(self) -> List[str]:
        rutas = []
        for carpeta, subcarpetas, ficheros in os.walk(self.raiz):
            subcarpetas[:] = sorted(c for c in subcarpetas if c not in _CARPETAS_IGNORADAS)
            for f in ficheros:
                rutas.append(Path(carpeta, f).relative_to(self.raiz).as_posix())
        return rutas

    def _dentro(self, p: Path) -> bool:
        try:
            p.resolve().relative_to(self._raiz_real)
            return True
        except ValueError:
            return False

    def existe(self, ruta: str) -> bool:
        p = self.raiz / ruta
        return p.is_file() and self._dentro(p)

    def lineas(self, ruta: str) -> Optional[List[str]]:
        """Líneas de un fichero de texto; None si no existe, es binario o es enorme."""
        if ruta not in self._lineas:
            self._lineas[ruta] = self._leer(ruta)
        return self._lineas[ruta]

    def _leer(self, ruta: str) -> Optional[List[str]]:
        p = self.raiz / ruta
        try:
            if not (p.is_file() and self._dentro(p)) or p.stat().st_size > _MAX_BYTES:
                return None
            datos = p.read_bytes()
        except OSError:
            return None
        if b"\0" in datos[:8192]:
            return None
        texto = datos.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
        lineas = texto.split("\n")
        if lineas and lineas[-1] == "":
            lineas.pop()
        return lineas

    def analisis(self, ruta: str) -> Optional[Analisis]:
        if ruta not in self._analisis:
            lineas = self.lineas(ruta)
            self._analisis[ruta] = None if lineas is None else Analisis(ruta, lineas)
        return self._analisis[ruta]

    def es_documento(self, ruta: str) -> bool:
        return any(R.casa(ruta, p) for p in self.cfg.documentos)

    def documentos(self) -> List[str]:
        return [f for f in self.ficheros if self.es_documento(f)]

    def clase(self, ruta: str) -> str:
        """«publico» (código privado), «publicado» (código público) o «interno»."""
        if any(R.casa(ruta, p) for p in self.cfg.publico):
            return "publico"
        if any(R.casa(ruta, p) for p in self.cfg.publicado):
            return "publicado"
        return "interno"
