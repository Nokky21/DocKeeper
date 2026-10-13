"""Configuración del repositorio (.dockeeper.json) y localización de la raíz."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

NOMBRE_CONFIG = ".dockeeper.json"
NOMBRE_SELLO = ".dockeeper.sello.json"

_POR_DEFECTO = {
    # Qué ficheros son documentos (el resto es código).
    "documentos": ["*.md", "*.markdown", "*.mdx"],
    # Qué se descarta siempre (documentos y código).
    "sin": [],
    # Documentación publicada cuyo código NO es público: ni anclas, ni rutas internas, ni código copiado.
    "publico": [],
    # Documentación publicada cuyo código SÍ es público: puede anclar, pero no copiar código.
    "publicado": [],
    # Qué documentos son de decisiones (para `why`); sin distinguir mayúsculas.
    "decisiones": ["*decision*", "*adr*"],
    # Líneas contiguas idénticas a partir de las cuales un bloque cuenta como código copiado.
    "bloque_minimo": 3,
    # Radio de la ventana cuando la línea anclada no está dentro de ninguna definición.
    "ventana": 3,
}
_LISTAS = ("documentos", "sin", "publico", "publicado", "decisiones")
_ENTEROS = ("bloque_minimo", "ventana")


class ErrorDeUso(Exception):
    """La orden no puede ejecutarse por un error de uso o de configuración (código de salida 2)."""


@dataclass
class Config:
    raiz: Path
    documentos: List[str]
    sin: List[str]
    publico: List[str]
    publicado: List[str]
    decisiones: List[str]
    bloque_minimo: int
    ventana: int


def buscar_raiz(desde: Path) -> Path:
    """Sube desde ``desde`` hasta una carpeta con .dockeeper.json o .git; si no la hay, ``desde``."""
    actual = desde.resolve()
    for carpeta in [actual, *actual.parents]:
        if (carpeta / NOMBRE_CONFIG).is_file() or (carpeta / ".git").exists():
            return carpeta
    return actual


def cargar(raiz: Path) -> Config:
    datos = {clave: (list(v) if isinstance(v, list) else v) for clave, v in _POR_DEFECTO.items()}
    ruta = raiz / NOMBRE_CONFIG
    if ruta.is_file():
        try:
            propios = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            raise ErrorDeUso(f"{NOMBRE_CONFIG} no se puede leer: {e}") from e
        if not isinstance(propios, dict):
            raise ErrorDeUso(f"{NOMBRE_CONFIG} debe ser un objeto JSON")
        for clave, valor in propios.items():
            if clave.startswith("_"):
                continue  # claves de comentario
            if clave not in _POR_DEFECTO:
                validas = ", ".join(_POR_DEFECTO)
                raise ErrorDeUso(f"{NOMBRE_CONFIG}: clave desconocida «{clave}» (válidas: {validas})")
            if clave in _LISTAS and not (isinstance(valor, list) and all(isinstance(x, str) for x in valor)):
                raise ErrorDeUso(f"{NOMBRE_CONFIG}: «{clave}» debe ser una lista de textos")
            if clave in _ENTEROS and not (isinstance(valor, int) and not isinstance(valor, bool) and valor >= 1):
                raise ErrorDeUso(f"{NOMBRE_CONFIG}: «{clave}» debe ser un entero mayor o igual que 1")
            datos[clave] = valor
    return Config(raiz=raiz, **datos)
