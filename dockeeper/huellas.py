"""Huellas de bloques normalizados.

Normalizar = colapsar los espacios, quitar los de los extremos y descartar las líneas vacías.
Así reformatear no cambia la huella y cambiar la lógica sí.
"""

from __future__ import annotations

import hashlib
from typing import Iterable, List, Sequence, Tuple


def normalizar_linea(linea: str) -> str:
    return " ".join(linea.split())


def normalizar(lineas: Iterable[str]) -> List[str]:
    return [t for t in (normalizar_linea(linea) for linea in lineas) if t]


def huella(normalizadas: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(normalizadas).encode("utf-8")).hexdigest()[:16]


def huella_de(lineas: Iterable[str]) -> Tuple[str, int]:
    """Huella y número de líneas con contenido de un bloque."""
    normalizadas = normalizar(lineas)
    return huella(normalizadas), len(normalizadas)


def huella_linea(linea: str) -> str:
    return huella([normalizar_linea(linea)])


def indice(lineas: Sequence[str]) -> List[Tuple[int, str]]:
    """(número de línea desde 1, texto normalizado) de cada línea con contenido."""
    res = []
    for num, linea in enumerate(lineas, 1):
        texto = normalizar_linea(linea)
        if texto:
            res.append((num, texto))
    return res


def buscar(lineas: Sequence[str], buscada: str, n: int) -> List[Tuple[int, int]]:
    """Tramos (inicio, fin) donde ``n`` líneas con contenido seguidas tienen la huella ``buscada``."""
    if n <= 0:
        return []
    idx = indice(lineas)
    textos = [t for _, t in idx]
    tramos = []
    for i in range(len(idx) - n + 1):
        if huella(textos[i:i + n]) == buscada:
            tramos.append((idx[i][0], idx[i + n - 1][0]))
    return tramos
