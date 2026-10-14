"""Rutas relativas a la raíz del repositorio y casado de patrones."""

from __future__ import annotations

import fnmatch
import posixpath
from typing import Optional


def normalizar_ruta(ruta: str) -> Optional[str]:
    """Ruta POSIX relativa a la raíz, o None si es absoluta o sale de la raíz."""
    ruta = ruta.replace("\\", "/").strip()
    if not ruta or ruta.startswith("/"):
        return None
    limpia = posixpath.normpath(ruta)
    if limpia in (".", "..") or limpia.startswith("../"):
        return None
    return limpia


def normalizar_patron(patron: str) -> str:
    patron = patron.replace("\\", "/").strip()
    while patron.startswith("./"):
        patron = patron[2:]
    return patron


def casa(ruta: str, patron: str, sin_mayusculas: bool = False) -> bool:
    """¿Casa la ruta con el patrón?

    - La ruta exacta o cualquier cosa por debajo de ese directorio, aunque lleve corchetes
      (rutas dinámicas como ``app/[id]/page.tsx``).
    - Con comodines (``*``, ``?``, ``[``): además, glob sobre la ruta entera y, si el patrón no
      lleva barra, también sobre el nombre del fichero.
    """
    patron = normalizar_patron(patron)
    if sin_mayusculas:
        ruta, patron = ruta.lower(), patron.lower()
    if patron in ("", "."):
        return True
    base = patron.rstrip("/")
    if ruta == base or ruta.startswith(base + "/"):
        return True
    if any(c in patron for c in "*?["):
        if fnmatch.fnmatchcase(ruta, patron):
            return True
        return "/" not in patron and fnmatch.fnmatchcase(posixpath.basename(ruta), patron)
    return False
