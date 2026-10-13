"""Alcance parcial: --solo (repetible) y --sin (repetible, más «sin» de la configuración).

Ojo con las listas vacías, que significan cosas distintas (en el prototipo esta confusión
hizo que no se comprobara nada y todo pareciera correcto):

- ``--solo`` vacío = **sin restricción**: todo entra.
- ``--sin`` vacío = **nada que descartar**: no se descarta nada.

Un prefijo de ``--solo`` que señala solo a documentos recorta los documentos; uno que señala
a algún fichero de código recorta el código (los destinos de las anclas).
"""

from __future__ import annotations

from typing import Callable, Iterable, List

from .config import ErrorDeUso
from .rutas import casa, normalizar_patron


class Alcance:
    def __init__(self, solo: List[str], sin: List[str], conocidas: Iterable[str],
                 es_documento: Callable[[str], bool]):
        self.solo = [normalizar_patron(p) for p in solo]
        self.sin = [normalizar_patron(p) for p in sin]
        self.solo_docs: List[str] = []
        self.solo_codigo: List[str] = []
        conocidas = sorted(set(conocidas))
        for patron in self.solo:
            casadas = [r for r in conocidas if casa(r, patron)]
            if not casadas:
                raise ErrorDeUso(f"--solo {patron}: no casa con ningún fichero del repositorio")
            if all(es_documento(r) for r in casadas):
                self.solo_docs.append(patron)
            else:
                self.solo_codigo.append(patron)

    def _descartada(self, ruta: str) -> bool:
        return any(casa(ruta, p) for p in self.sin)  # lista vacía → no se descarta nada

    def doc_en_alcance(self, ruta: str) -> bool:
        if self._descartada(ruta):
            return False
        return not self.solo_docs or any(casa(ruta, p) for p in self.solo_docs)  # vacía → todo entra

    def codigo_en_alcance(self, ruta: str) -> bool:
        if self._descartada(ruta):
            return False
        return not self.solo_codigo or any(casa(ruta, p) for p in self.solo_codigo)  # vacía → todo entra

    def describir(self) -> dict:
        return {"solo_documentos": self.solo_docs, "solo_codigo": self.solo_codigo, "sin": self.sin}
