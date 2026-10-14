"""El fichero de sello (.dockeeper.sello.json): huellas de cada ancla y de cada vínculo.

No guarda código, solo posiciones y huellas. JSON ordenado para que los diffs se lean bien.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import NOMBRE_SELLO, ErrorDeUso
from .textos import t

VERSION = 1


@dataclass
class Entrada:
    doc: str
    ancla: str  # tal como está escrita (forma canónica): clave junto con el documento
    fichero: str
    tipo: str  # "definicion" | "declaracion" | "ventana"
    inicio: int
    fin: int
    n: int
    huella: str
    simbolo: Optional[str] = None
    linea: Optional[int] = None  # posición real de un ancla por línea (puede diferir de la escrita)
    linea_doc: Optional[int] = None  # solo vínculos: línea del documento vinculada
    huella_doc: Optional[str] = None  # solo vínculos: huella de esa línea

    _ORDEN = ("doc", "linea_doc", "huella_doc", "ancla", "fichero", "simbolo", "linea",
              "tipo", "inicio", "fin", "n", "huella")

    def a_dict(self) -> dict:
        return {k: getattr(self, k) for k in self._ORDEN if getattr(self, k) is not None}

    @classmethod
    def desde_dict(cls, datos: dict) -> "Entrada":
        nombres = {f.name for f in fields(cls)}
        obligatorias = ("doc", "ancla", "fichero", "tipo", "inicio", "fin", "n", "huella")
        if not isinstance(datos, dict) or any(k not in datos for k in obligatorias):
            raise ErrorDeUso(t("{fichero} está dañado: entrada incompleta {entrada}", fichero=NOMBRE_SELLO, entrada=repr(datos)))
        return cls(**{k: v for k, v in datos.items() if k in nombres})


class Sello:
    def __init__(self, ruta: Path):
        self.ruta = ruta
        self.anclas: Dict[Tuple[str, str], Entrada] = {}
        self.vinculos: List[Entrada] = []

    @classmethod
    def cargar(cls, raiz: Path) -> "Sello":
        sello = cls(raiz / NOMBRE_SELLO)
        if not sello.ruta.is_file():
            return sello
        try:
            datos = json.loads(sello.ruta.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            raise ErrorDeUso(t("{fichero} no se puede leer: {error}", fichero=NOMBRE_SELLO, error=e)) from e
        if not isinstance(datos, dict) or datos.get("dockeeper") != VERSION:
            raise ErrorDeUso(t("{fichero}: versión desconocida (se espera «dockeeper»: {version})", fichero=NOMBRE_SELLO,
                                version=VERSION))
        for d in datos.get("anclas", []):
            e = Entrada.desde_dict(d)
            sello.anclas[(e.doc, e.ancla)] = e
        for d in datos.get("vinculos", []):
            sello.vinculos.append(Entrada.desde_dict(d))
        return sello

    def guardar(self) -> None:
        datos = {
            "dockeeper": VERSION,
            "anclas": [self.anclas[k].a_dict() for k in sorted(self.anclas)],
            "vinculos": [v.a_dict() for v in sorted(self.vinculos, key=lambda v: (v.doc, v.linea_doc or 0, v.ancla))],
        }
        temporal = self.ruta.with_name(self.ruta.name + ".tmp")
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporal, self.ruta)

    def todas(self) -> List[Entrada]:
        return list(self.anclas.values()) + list(self.vinculos)

    def quitar(self, entrada: Entrada) -> None:
        clave = (entrada.doc, entrada.ancla)
        if self.anclas.get(clave) is entrada:
            del self.anclas[clave]
        else:
            self.vinculos = [v for v in self.vinculos if v is not entrada]

    def poner_vinculo(self, entrada: Entrada) -> bool:
        """Añade o sustituye el vínculo (doc, línea, ancla). Devuelve True si ya existía."""
        clave = (entrada.doc, entrada.linea_doc, entrada.ancla)
        antes = len(self.vinculos)
        self.vinculos = [v for v in self.vinculos if (v.doc, v.linea_doc, v.ancla) != clave]
        existia = len(self.vinculos) != antes
        self.vinculos.append(entrada)
        return existia
