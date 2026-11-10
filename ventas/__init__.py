"""Sistema de ventas con arquitectura en capas.

Capas:
    models      -> entidades y cálculo de totales
    repositorio -> SQL
    servicios   -> reglas de negocio (stock, transacciones)
    reportes    -> PDF / CSV
    cli         -> interfaz de consola
"""

__version__ = "1.0.0"

from .models import Cliente, LineaVenta, Producto, Venta

__all__ = ["Cliente", "Producto", "LineaVenta", "Venta", "__version__"]
