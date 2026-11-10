"""Reportes de ventas en PDF y CSV."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List

from .models import Venta


def _resumen(venta: Venta, clientes: Dict[int, str]) -> List[str]:
    productos = ", ".join(f"{l.cantidad}× {l.nombre}" for l in venta.lineas)
    return [
        str(venta.id or "—"),
        venta.fecha.strftime("%d/%m/%Y %H:%M"),
        clientes.get(venta.cliente_id, f"Cliente {venta.cliente_id}"),
        productos,
        f"S/ {venta.subtotal:,.2f}",
        f"S/ {venta.igv:,.2f}",
        f"S/ {venta.total:,.2f}",
    ]


def exportar_csv(ventas: Iterable[Venta], ruta: Path | str, clientes: Dict[int, str]) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow(
            ["Venta", "Fecha", "Cliente", "Productos", "Subtotal", "IGV", "Total"]
        )
        for venta in ventas:
            escritor.writerow(_resumen(venta, clientes))
    return ruta


def exportar_pdf(ventas: List[Venta], ruta: Path | str, clientes: Dict[int, str]) -> Path:
    """Genera un PDF con el detalle de las ventas usando ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as error:  # pragma: no cover
        raise RuntimeError(
            "ReportLab no está instalado. Ejecuta: pip install -r requirements.txt"
        ) from error

    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    estilos = getSampleStyleSheet()
    documento = SimpleDocTemplate(
        str(ruta),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Reporte de ventas",
    )

    elementos = [
        Paragraph("Reporte de ventas", estilos["Title"]),
        Paragraph(
            f"{len(ventas)} venta(s) registradas", estilos["Normal"]
        ),
        Spacer(1, 0.5 * cm),
    ]

    encabezado = ["Venta", "Fecha", "Cliente", "Productos", "Subtotal", "IGV", "Total"]
    filas = [encabezado] + [_resumen(venta, clientes) for venta in ventas]

    total_general = sum((venta.total for venta in ventas), Decimal("0"))
    filas.append(["", "", "", "", "", "Total", f"S/ {total_general:,.2f}"])

    tabla = Table(filas, repeatRows=1, colWidths=[1.4 * cm, 3 * cm, 4 * cm, 5 * cm, 2 * cm, 1.8 * cm, 2.3 * cm])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243b53")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd2d9")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f0f4f8")]),
                ("FONTNAME", (5, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    elementos.append(tabla)
    documento.build(elementos)
    return ruta
