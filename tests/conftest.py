import sqlite3

import pytest

from ventas import db


@pytest.fixture
def conexion(tmp_path):
    conexion = db.conectar(tmp_path / "ventas.db")
    try:
        yield conexion
    finally:
        conexion.close()
