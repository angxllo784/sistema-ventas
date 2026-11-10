# Sistema de Gestión de Ventas

Aplicación de consola en Python para registrar ventas con cálculo de IGV,
control de stock y exportación de reportes en PDF y CSV. Está organizada en
capas para separar el cálculo del negocio, el acceso a datos y la interfaz,
de modo que cada parte se pueda probar por separado.

## Características

- **Registro de ventas** con validación de cliente, producto, cantidad y
  stock disponible *antes* de escribir en la base de datos.
- **Cálculo exacto de importes** con `Decimal`: subtotal, IGV (18 %) y total
  redondeados a dos decimales con criterio comercial.
- **Transacciones**: si algo falla a mitad de la venta, no queda una venta
  incompleta ni stock descontado.
- **Descuento automático de stock** en la misma transacción.
- **Reportes** en PDF (ReportLab, con total general) y CSV compatible con
  Excel en español (separador `;`, UTF-8 con BOM).
- **Arquitectura en capas**: `models` → `repositorio` → `servicios` →
  `reportes` → `cli`.
- **Pruebas** con `pytest` sobre reglas de negocio, repositorios y reportes.

## Stack

Python 3.12 · SQLite · ReportLab · pytest

## Estructura

```
sistema-ventas/
├── ventas/
│   ├── models.py       # Cliente, Producto, Venta y cálculo de totales
│   ├── db.py           # conexión, claves foráneas y carga del esquema
│   ├── repositorio.py  # SQL de clientes, productos y ventas
│   ├── servicios.py    # validación de stock y transacción de venta
│   ├── reportes.py     # exportación a PDF y CSV
│   └── cli.py          # comandos: seed, vender, listar, reporte
├── tests/
│   ├── test_servicios.py
│   ├── test_repositorio.py
│   └── test_reportes.py
├── schema.sql
├── requirements.txt
└── requirements-dev.txt
```

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Uso

Crear datos de ejemplo (2 clientes y 3 productos):

```bash
python -m ventas seed
```

Registrar una venta indicando `producto x cantidad`:

```bash
python -m ventas vender --cliente 1 --items "1x2,2x3"
```

```
Venta #1 registrada
  2 × Laptop Lenovo IdeaPad @ S/ 2,499.00 = S/ 4,998.00
  3 × Mouse inalámbrico @ S/ 59.90 = S/ 179.70
  Subtotal: S/ 5,177.70
  IGV (18%): S/ 931.99
  Total:    S/ 6,109.69
```

Listar ventas y generar reportes:

```bash
python -m ventas listar
python -m ventas reporte --pdf datos/ventas.pdf --csv datos/ventas.csv
```

| Comando | Descripción |
| --- | --- |
| `seed` | crea clientes y productos de ejemplo |
| `vender --cliente N --items "1x2,3x1"` | registra una venta |
| `listar --limite 20` | muestra las últimas ventas |
| `reporte --pdf/--csv` | exporta el detalle de ventas |

La base se crea sola en `datos/ventas.db`; se puede cambiar con `--db`.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Decisiones técnicas

- **`Decimal` en lugar de `float`.** Con `float`, `0.1 + 0.2` no da `0.3`;
  en un sistema que calcula IGV eso termina en diferencias de céntimos. Los
  importes se redondean con `ROUND_HALF_UP`, que es el criterio comercial.
- **Validar todo antes de insertar.** La venta se construye en memoria y solo
  se escribe si todos los ítems son válidos; así nunca hay cabeceras sin
  detalle.
- **Repositorios separados de los servicios.** El SQL vive en
  `repositorio.py` y las reglas (stock, cantidades, cliente existente) en
  `servicios.py`, lo que permite probar la lógica con una base temporal.
- **El detalle se guarda con el precio del momento.** Si el producto cambia
  de precio después, la venta histórica conserva el importe original.
- **El esquema está en `schema.sql`.** Se puede revisar y versionar sin
  buscar cadenas SQL dentro del código.

## Autor

Angello Mathias Silva Saldaña — [LinkedIn](https://www.linkedin.com/in/angello-silva-6b980436)
