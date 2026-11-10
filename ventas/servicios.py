"""Reglas de negocio de la venta."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from typing import Iterable, List, Tuple

from .models import LineaVenta, Venta
from .repositorio import ClienteRepositorio, ProductoRepositorio, VentaRepositorio


class ErrorVenta(Exception):
    """Error de negocio mostrable al usuario (stock, cliente, etc.)."""


class VentaService:
    """Registra ventas validando cliente, stock y cantidades."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion
        self.clientes = ClienteRepositorio(conexion)
        self.productos = ProductoRepositorio(conexion)
        self.ventas = VentaRepositorio(conexion)

    def registrar(self, cliente_id: int, items: Iterable[Tuple[int, int]]) -> Venta:
        """Crea una venta a partir de pares ``(producto_id, cantidad)``.

        Valida todo antes de escribir para no dejar ventas a medias.
        """
        if not self.clientes.obtener(cliente_id):
            raise ErrorVenta(f"El cliente {cliente_id} no existe.")

        lineas: List[LineaVenta] = []
        for producto_id, cantidad in items:
            if cantidad <= 0:
                raise ErrorVenta("La cantidad debe ser mayor que cero.")

            producto = self.productos.obtener(producto_id)
            if producto is None:
                raise ErrorVenta(f"El producto {producto_id} no existe.")
            if producto.stock < cantidad:
                raise ErrorVenta(
                    f"Stock insuficiente de «{producto.nombre}»: "
                    f"disponible {producto.stock}, solicitado {cantidad}."
                )

            lineas.append(
                LineaVenta(
                    producto_id=producto.id,
                    nombre=producto.nombre,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                )
            )

        venta = Venta.crear(cliente_id, lineas)

        with self.conexion:  # transacción: todo o nada
            venta_id = self.ventas.crear(venta)
            for linea in venta.lineas:
                producto = self.productos.obtener(linea.producto_id)
                self.productos.actualizar_stock(
                    linea.producto_id, producto.stock - linea.cantidad
                )

        return replace(venta, id=venta_id)
