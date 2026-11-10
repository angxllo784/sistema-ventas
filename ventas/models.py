"""Modelos de dominio del sistema de ventas.

Los importes se manejan con ``Decimal`` para evitar los errores de
redondeo típicos de ``float`` al calcular IGV y totales.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence, Tuple

IGV = Decimal("0.18")
_CENTIMOS = Decimal("0.01")


def redondear(valor: Decimal) -> Decimal:
    """Redondea a dos decimales con el criterio comercial (mitad hacia arriba)."""
    return valor.quantize(_CENTIMOS, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Cliente:
    id: int | None
    nombre: str
    documento: str = ""


@dataclass(frozen=True)
class Producto:
    id: int | None
    nombre: str
    precio: Decimal
    stock: int


@dataclass(frozen=True)
class LineaVenta:
    """Un producto dentro de una venta, con la cantidad solicitada."""

    producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: Decimal

    @property
    def subtotal(self) -> Decimal:
        return redondear(self.precio_unitario * self.cantidad)


@dataclass(frozen=True)
class Venta:
    id: int | None
    cliente_id: int
    fecha: datetime
    lineas: Tuple[LineaVenta, ...]

    @property
    def subtotal(self) -> Decimal:
        return redondear(sum((linea.subtotal for linea in self.lineas), Decimal("0")))

    @property
    def igv(self) -> Decimal:
        return redondear(self.subtotal * IGV)

    @property
    def total(self) -> Decimal:
        return redondear(self.subtotal + self.igv)

    @classmethod
    def crear(cls, cliente_id: int, lineas: Sequence[LineaVenta]) -> "Venta":
        """Construye una venta nueva (sin id) con la fecha actual."""
        if not lineas:
            raise ValueError("La venta debe tener al menos un producto.")
        return cls(id=None, cliente_id=cliente_id, fecha=datetime.now(), lineas=tuple(lineas))
