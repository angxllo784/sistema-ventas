"""Acceso a datos: una clase por agregado.

Los repositorios solo hablan con SQLite. La lógica de negocio (validar
stock, calcular totales) vive en ``servicios.py``.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from .models import Cliente, LineaVenta, Producto, Venta


class ClienteRepositorio:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def crear(self, nombre: str, documento: str = "") -> Cliente:
        cursor = self.conexion.execute(
            "INSERT INTO clientes (nombre, documento) VALUES (?, ?)",
            (nombre.strip(), documento.strip()),
        )
        return Cliente(id=cursor.lastrowid, nombre=nombre, documento=documento)

    def obtener(self, cliente_id: int) -> Optional[Cliente]:
        fila = self.conexion.execute(
            "SELECT * FROM clientes WHERE id = ?", (cliente_id,)
        ).fetchone()
        if not fila:
            return None
        return Cliente(id=fila["id"], nombre=fila["nombre"], documento=fila["documento"])

    def listar(self) -> List[Cliente]:
        filas = self.conexion.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
        return [
            Cliente(id=f["id"], nombre=f["nombre"], documento=f["documento"]) for f in filas
        ]


class ProductoRepositorio:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def crear(self, nombre: str, precio: Decimal, stock: int) -> Producto:
        cursor = self.conexion.execute(
            "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
            (nombre.strip(), float(precio), stock),
        )
        return Producto(id=cursor.lastrowid, nombre=nombre, precio=precio, stock=stock)

    def obtener(self, producto_id: int) -> Optional[Producto]:
        fila = self.conexion.execute(
            "SELECT * FROM productos WHERE id = ?", (producto_id,)
        ).fetchone()
        if not fila:
            return None
        return Producto(
            id=fila["id"],
            nombre=fila["nombre"],
            precio=Decimal(str(fila["precio"])),
            stock=fila["stock"],
        )

    def listar(self) -> List[Producto]:
        filas = self.conexion.execute("SELECT * FROM productos ORDER BY nombre").fetchall()
        return [
            Producto(
                id=f["id"],
                nombre=f["nombre"],
                precio=Decimal(str(f["precio"])),
                stock=f["stock"],
            )
            for f in filas
        ]

    def actualizar_stock(self, producto_id: int, stock: int) -> None:
        self.conexion.execute(
            "UPDATE productos SET stock = ? WHERE id = ?", (stock, producto_id)
        )


class VentaRepositorio:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def crear(self, venta: Venta) -> int:
        """Inserta la cabecera y el detalle; devuelve el id de la venta."""
        cursor = self.conexion.execute(
            "INSERT INTO ventas (cliente_id, fecha, subtotal, igv, total) VALUES (?, ?, ?, ?, ?)",
            (
                venta.cliente_id,
                venta.fecha.isoformat(timespec="seconds"),
                float(venta.subtotal),
                float(venta.igv),
                float(venta.total),
            ),
        )
        venta_id = int(cursor.lastrowid)

        self.conexion.executemany(
            """
            INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
            """,
            [
                (venta_id, linea.producto_id, linea.cantidad, float(linea.precio_unitario))
                for linea in venta.lineas
            ],
        )
        return venta_id

    def listar(self, limite: int = 50) -> List[Venta]:
        filas = self.conexion.execute(
            "SELECT * FROM ventas ORDER BY fecha DESC, id DESC LIMIT ?", (limite,)
        ).fetchall()
        if not filas:
            return []

        ids = [f["id"] for f in filas]
        marcadores = ",".join("?" * len(ids))
        detalles = self.conexion.execute(
            f"""
            SELECT d.*, p.nombre AS producto
            FROM detalle_venta d
            JOIN productos p ON p.id = d.producto_id
            WHERE d.venta_id IN ({marcadores})
            ORDER BY d.id
            """,
            ids,
        ).fetchall()

        por_venta: Dict[int, List[LineaVenta]] = {venta_id: [] for venta_id in ids}
        for detalle in detalles:
            por_venta[detalle["venta_id"]].append(
                LineaVenta(
                    producto_id=detalle["producto_id"],
                    nombre=detalle["producto"],
                    cantidad=detalle["cantidad"],
                    precio_unitario=Decimal(str(detalle["precio_unitario"])),
                )
            )

        return [
            Venta(
                id=fila["id"],
                cliente_id=fila["cliente_id"],
                fecha=datetime.fromisoformat(fila["fecha"]),
                lineas=tuple(por_venta[fila["id"]]),
            )
            for fila in filas
        ]
