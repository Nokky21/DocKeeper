"""Paquetes de un repositorio: cada subcarpeta con un manifiesto (monorepos y repos con varias piezas).

Un paquete se documenta por separado (su README, con ``--solo`` sobre su carpeta) y la raíz lleva el
mapa de todos. No se interpretan los espacios de trabajo de cada herramienta: basta el manifiesto,
así sirven igual npm, pnpm, yarn, Nx, Turborepo, Go, Cargo, Maven, Gradle o una mezcla.
"""

from __future__ import annotations

import json
import posixpath
import re
from dataclasses import dataclass
from typing import Callable, List, Optional

# Ficheros que marcan la raíz de un paquete.
MANIFIESTOS = (
    "package.json", "deno.json", "deno.jsonc", "pyproject.toml", "setup.py", "Cargo.toml", "go.mod",
    "pom.xml", "build.gradle", "build.gradle.kts", "composer.json", "Gemfile", "mix.exs", "Package.swift",
    "pubspec.yaml",
)
_SUFIJOS = (".csproj", ".fsproj", ".gemspec")
# Dependencias copiadas dentro del repositorio: no son paquetes propios.
_AJENAS = {"node_modules", "vendor", "third_party", "bower_components", ".venv", "venv", "site-packages"}

_SECCION = re.compile(r"^\s*(\[\[?)\s*([^\]]+?)\s*\]")  # [tabla] o [[tabla de tablas]], con comentario detrás
_NOMBRE_TOML = re.compile(r"""^\s*name\s*=\s*["']([^"']+)["']""")
_MODULO_GO = re.compile(r"""^\s*module\s+["`]?([^"`\s]+)""")


@dataclass
class Paquete:
    ruta: str
    nombre: str
    manifiesto: str


def es_manifiesto(ruta: str) -> bool:
    nombre = posixpath.basename(ruta)
    return nombre in MANIFIESTOS or nombre.endswith(_SUFIJOS)


def _nombre(manifiesto: str, lineas: Optional[List[str]]) -> Optional[str]:
    """Nombre declarado en el manifiesto, solo en los formatos que se leen sin dependencias."""
    if not lineas:
        return None
    lineas = [lineas[0].lstrip("\ufeff"), *lineas[1:]]  # marca de orden de bytes (ficheros de Windows)
    base = posixpath.basename(manifiesto)
    if base in ("package.json", "composer.json", "deno.json"):
        try:
            datos = json.loads("\n".join(lineas))
        except ValueError:
            return None
        nombre = datos.get("name") if isinstance(datos, dict) else None
        return nombre if isinstance(nombre, str) and nombre else None
    if base in ("pyproject.toml", "Cargo.toml"):
        secciones = {"pyproject.toml": ("project", "tool.poetry"), "Cargo.toml": ("package",)}[base]
        seccion = None
        for linea in lineas:
            m = _SECCION.match(linea)
            if m:
                seccion = m.group(2) if m.group(1) == "[" else None  # [[bin]] no es la sección del paquete
                continue
            m = _NOMBRE_TOML.match(linea)
            if m and seccion in secciones:
                return m.group(1)
        return None
    if base == "go.mod":
        for linea in lineas:
            m = _MODULO_GO.match(linea)
            if m:
                return m.group(1)
        return None
    if base == "pubspec.yaml":
        for linea in lineas:
            if linea.startswith("name:"):
                return linea.split(":", 1)[1].strip().strip("'\"") or None
    return None


def detectar(ficheros: List[str], leer: Callable[[str], Optional[List[str]]]) -> List[Paquete]:
    """Paquetes de las subcarpetas (la raíz no cuenta: es el repositorio). Uno por carpeta."""
    carpetas = {}
    for f in ficheros:
        if "/" not in f or not es_manifiesto(f):
            continue
        carpeta = posixpath.dirname(f)
        if _AJENAS.intersection(carpeta.split("/")[:-1]):  # dentro de node_modules/, vendor/…; no la propia
            continue
        carpetas.setdefault(carpeta, []).append(f)
    paquetes = []
    for carpeta, manifiestos in sorted(carpetas.items()):
        # Con varios manifiestos en la misma carpeta, el primero según el orden de MANIFIESTOS.
        manifiesto = min(manifiestos, key=lambda m: (MANIFIESTOS.index(posixpath.basename(m))
                                                    if posixpath.basename(m) in MANIFIESTOS else len(MANIFIESTOS), m))
        nombre = _nombre(manifiesto, leer(manifiesto)) or posixpath.basename(carpeta)
        paquetes.append(Paquete(carpeta, nombre, manifiesto))
    return paquetes


def paquete_de(ruta: str, paquetes: List[Paquete]) -> Optional[Paquete]:
    """El paquete más profundo que contiene la ruta (None si solo la contiene la raíz)."""
    dentro = [p for p in paquetes if ruta.startswith(p.ruta + "/")]
    return max(dentro, key=lambda p: len(p.ruta)) if dentro else None
