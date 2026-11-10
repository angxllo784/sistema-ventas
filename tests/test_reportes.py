import csv
from datetime import datetime
from decimal import Decimal

import pytest

from ventas.models import LineaVenta, Venta
from ventas.reportes import exportar_csv, exportar_pdf


def _venta():
    return Venta(
        id=7,
        cliente_id=1,
        fecha=datetime(2025, 3, 12, 10, 30),
        lineas=(
            LineaVenta(producto_id=1, nombre="Monitor", cantidad=1, precio_unitario=Decimal("549.00")),
            LineaVenta(producto_id=2, nombre="Mouse", cantidad=2, precio_unitario=Decimal("59.90")),
        ),
    )


def test_exportar_csv(tmp_path):
    ruta = exportar_csv([_venta()], tmp_path / "ventas.csv", {1: "Comercial Andina"})

    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.reader(archivo, delimiter=";"))

    assert filas[0] == ["Venta", "Fecha", "Cliente", "Productos", "Subtotal", "IGV", "Total"]
    assert filas[1][0] == "7"
    assert filas[1][2] == "Comercial Andina"
    assert "1× Monitor" in filas[1][3]
    assert filas[1][4] == "S/ 668.80"
    assert filas[1][6] == "S/ 789.18"


def test_exportar_pdf(tmp_path):
    pytest.importorskip("reportlab", reason="ReportLab no instalado")

    ruta = exportar_pdf([_venta()], tmp_path / "ventas.pdf", {1: "Comercial Andina"})

    assert ruta.exists()
    assert ruta.stat().st_size > 1000
    assert ruta.read_bytes().startswith(b"%PDF")
