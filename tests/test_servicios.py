from decimal import Decimal

import pytest

from ventas.models import LineaVenta, Venta
from ventas.repositorio import ClienteRepositorio, ProductoRepositorio
from ventas.servicios import ErrorVenta, VentaService


@pytest.fixture
def datos(conexion):
    cliente = ClienteRepositorio(conexion).crear("María Quispe", "45678912")
    productos = ProductoRepositorio(conexion)
    mouse = productos.crear("Mouse inalámbrico", Decimal("59.90"), 5)
    laptop = productos.crear("Laptop", Decimal("2499.00"), 2)
    return conexion, cliente, mouse, laptop


def test_registrar_venta_calcula_totales(datos):
    conexion, cliente, mouse, _ = datos
    servicio = VentaService(conexion)

    venta = servicio.registrar(cliente.id, [(mouse.id, 2)])

    assert venta.id is not None
    assert venta.subtotal == Decimal("119.80")
    assert venta.igv == Decimal("21.56")
    assert venta.total == Decimal("141.36")


def test_registrar_venta_descuenta_stock(datos):
    conexion, cliente, mouse, _ = datos
    VentaService(conexion).registrar(cliente.id, [(mouse.id, 3)])

    actualizado = ProductoRepositorio(conexion).obtener(mouse.id)
    assert actualizado.stock == 2


def test_stock_insuficiente_no_modifica_nada(datos):
    conexion, cliente, mouse, _ = datos
    servicio = VentaService(conexion)

    with pytest.raises(ErrorVenta, match="Stock insuficiente"):
        servicio.registrar(cliente.id, [(mouse.id, 99)])

    assert ProductoRepositorio(conexion).obtener(mouse.id).stock == 5
    assert conexion.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 0


def test_cliente_inexistente(datos):
    conexion, _, mouse, _ = datos

    with pytest.raises(ErrorVenta, match="no existe"):
        VentaService(conexion).registrar(999, [(mouse.id, 1)])


def test_cantidad_invalida(datos):
    conexion, cliente, mouse, _ = datos

    with pytest.raises(ErrorVenta, match="mayor que cero"):
        VentaService(conexion).registrar(cliente.id, [(mouse.id, 0)])


def test_venta_sin_lineas():
    with pytest.raises(ValueError):
        Venta.crear(cliente_id=1, lineas=[])


def test_igv_se_redondea_a_dos_decimales():
    venta = Venta(
        id=1,
        cliente_id=1,
        fecha=__import__("datetime").datetime(2025, 3, 12, 10, 0),
        lineas=(
            LineaVenta(producto_id=1, nombre="Producto", cantidad=3, precio_unitario=Decimal("33.33")),
        ),
    )

    assert venta.subtotal == Decimal("99.99")
    assert venta.igv == Decimal("18.00")
    assert venta.total == Decimal("117.99")
