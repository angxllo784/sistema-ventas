from decimal import Decimal

from ventas.repositorio import ClienteRepositorio, ProductoRepositorio, VentaRepositorio
from ventas.servicios import VentaService


def test_listar_ventas_incluye_detalle(conexion):
    cliente = ClienteRepositorio(conexion).crear("Comercial Andina", "20512345678")
    producto = ProductoRepositorio(conexion).crear("Monitor", Decimal("549.00"), 10)

    VentaService(conexion).registrar(cliente.id, [(producto.id, 2)])

    ventas = VentaRepositorio(conexion).listar()

    assert len(ventas) == 1
    assert ventas[0].lineas[0].nombre == "Monitor"
    assert ventas[0].lineas[0].cantidad == 2
    assert ventas[0].total == Decimal("1295.64")


def test_listar_sin_ventas_devuelve_vacio(conexion):
    assert VentaRepositorio(conexion).listar() == []


def test_actualizar_stock(conexion):
    productos = ProductoRepositorio(conexion)
    producto = productos.crear("Teclado", Decimal("120.00"), 4)

    productos.actualizar_stock(producto.id, 1)

    assert productos.obtener(producto.id).stock == 1
