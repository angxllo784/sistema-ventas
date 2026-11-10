"""Línea de comandos del sistema de ventas."""

from __future__ import annotations

import argparse
from decimal import Decimal
from typing import List, Optional, Sequence

from . import db
from .models import Cliente
from .repositorio import ClienteRepositorio, ProductoRepositorio, VentaRepositorio
from .reportes import exportar_csv, exportar_pdf
from .servicios import ErrorVenta, VentaService

BASE_POR_DEFECTO = "datos/ventas.db"


def _items(texto: str) -> List[tuple[int, int]]:
    """Convierte ``"1x2,3x1"`` en ``[(1, 2), (3, 1)]``."""
    items: List[tuple[int, int]] = []
    for parte in texto.split(","):
        parte = parte.strip()
        if not parte:
            continue
        try:
            producto, cantidad = parte.lower().split("x")
            items.append((int(producto), int(cantidad)))
        except ValueError as error:
            raise SystemExit(
                f"Formato inválido: «{parte}». Usa producto x cantidad, por ejemplo 1x2."
            ) from error
    if not items:
        raise SystemExit("Debes indicar al menos un producto (por ejemplo 1x2).")
    return items


def _clientes_por_id(conexion) -> dict[int, str]:
    return {c.id: c.nombre for c in ClienteRepositorio(conexion).listar()}


def cmd_seed(args: argparse.Namespace) -> int:
    with db.abrir(args.db) as conexion:
        clientes = ClienteRepositorio(conexion)
        productos = ProductoRepositorio(conexion)

        if clientes.listar():
            print("La base ya tiene datos; no se agregó nada.")
            return 0

        clientes.crear("Comercial Andina S.A.C.", "20512345678")
        clientes.crear("María Quispe", "45678912")
        productos.crear("Laptop Lenovo IdeaPad", Decimal("2499.00"), 8)
        productos.crear("Mouse inalámbrico", Decimal("59.90"), 40)
        productos.crear("Monitor 24\"", Decimal("549.00"), 15)

        print("Datos de ejemplo creados: 2 clientes y 3 productos.")
    return 0


def cmd_vender(args: argparse.Namespace) -> int:
    with db.abrir(args.db) as conexion:
        servicio = VentaService(conexion)
        try:
            venta = servicio.registrar(args.cliente, _items(args.items))
        except ErrorVenta as error:
            print(f"No se pudo registrar la venta: {error}")
            return 1

        print(f"Venta #{venta.id} registrada")
        for linea in venta.lineas:
            print(
                f"  {linea.cantidad} × {linea.nombre} "
                f"@ S/ {linea.precio_unitario:,.2f} = S/ {linea.subtotal:,.2f}"
            )
        print(f"  Subtotal: S/ {venta.subtotal:,.2f}")
        print(f"  IGV (18%): S/ {venta.igv:,.2f}")
        print(f"  Total:    S/ {venta.total:,.2f}")
    return 0


def cmd_listar(args: argparse.Namespace) -> int:
    with db.abrir(args.db) as conexion:
        clientes = _clientes_por_id(conexion)
        ventas = VentaRepositorio(conexion).listar(args.limite)

        if not ventas:
            print("Aún no hay ventas registradas.")
            return 0

        print(f"{'ID':>4}  {'FECHA':<17} {'CLIENTE':<24} {'TOTAL':>12}")
        print("-" * 62)
        for venta in ventas:
            nombre = clientes.get(venta.cliente_id, f"Cliente {venta.cliente_id}")
            print(
                f"{venta.id:>4}  {venta.fecha:%d/%m/%Y %H:%M} "
                f"{nombre[:24]:<24} S/ {venta.total:>9,.2f}"
            )
    return 0


def cmd_reporte(args: argparse.Namespace) -> int:
    with db.abrir(args.db) as conexion:
        clientes = _clientes_por_id(conexion)
        ventas = VentaRepositorio(conexion).listar(limite=500)

        if not ventas:
            print("No hay ventas para exportar.")
            return 1

        if args.csv:
            print(f"CSV generado: {exportar_csv(ventas, args.csv, clientes)}")
        if args.pdf:
            print(f"PDF generado: {exportar_pdf(ventas, args.pdf, clientes)}")
        if not args.csv and not args.pdf:
            print("Indica --csv y/o --pdf.")
            return 1
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ventas", description="Sistema de ventas por consola (SQLite)."
    )
    parser.add_argument("--db", default=BASE_POR_DEFECTO, help="ruta de la base SQLite")
    sub = parser.add_subparsers(dest="comando", required=True)

    seed = sub.add_parser("seed", help="crear datos de ejemplo")
    seed.set_defaults(func=cmd_seed)

    vender = sub.add_parser("vender", help="registrar una venta")
    vender.add_argument("--cliente", type=int, required=True)
    vender.add_argument("--items", required=True, help="por ejemplo 1x2,3x1")
    vender.set_defaults(func=cmd_vender)

    listar = sub.add_parser("listar", help="listar ventas")
    listar.add_argument("--limite", type=int, default=20)
    listar.set_defaults(func=cmd_listar)

    reporte = sub.add_parser("reporte", help="exportar ventas")
    reporte.add_argument("--csv")
    reporte.add_argument("--pdf")
    reporte.set_defaults(func=cmd_reporte)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = construir_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
