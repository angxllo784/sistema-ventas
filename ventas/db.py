"""Conexión a la base de datos y carga del esquema."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

RAIZ = Path(__file__).resolve().parent.parent
RUTA_ESQUEMA = RAIZ / "schema.sql"


def conectar(ruta: Path | str) -> sqlite3.Connection:
    """Abre la base, activa claves foráneas y crea las tablas si faltan."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.executescript(RUTA_ESQUEMA.read_text(encoding="utf-8"))
    return conexion


@contextmanager
def abrir(ruta: Path | str) -> Iterator[sqlite3.Connection]:
    """Context manager que confirma los cambios o revierte si hay error."""
    conexion = conectar(ruta)
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
