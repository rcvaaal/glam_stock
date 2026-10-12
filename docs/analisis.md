# Análisis y diseño: Glam Stock

## Nombre del proyecto

Glam Stock: inventario y ventas de una tienda de maquillaje.

## Descripción del problema

Una tienda pequeña de maquillaje que vende por redes sociales suele llevar el inventario en un cuaderno o en notas del celular. Eso provoca que se ofrezcan productos que ya se agotaron, que no se sepa cuántas unidades quedan de cada tono y que los totales de las ventas se calculen a mano.

## Objetivo general

Desarrollar una aplicación web que permita registrar marcas, categorías, productos y ventas de maquillaje, descontando automáticamente las existencias en cada venta y calculando el total a cobrar.

## Principales funcionalidades

- Registrar, consultar, modificar y eliminar marcas, categorías, productos y ventas.
- Descontar del inventario las unidades vendidas y devolverlas si la venta se modifica o se elimina.
- Impedir una venta cuando no hay suficientes existencias.
- Calcular el total de cada venta desde el backend (precio × cantidad).
- Mostrar un resumen con el dinero vendido, el producto más vendido y los productos por agotarse.

## Usuarios del sistema

- **Dueña de la tienda:** administra marcas, categorías, precios y revisa el resumen.
- **Vendedora:** consulta existencias y registra las ventas.

## Diseño de la base de datos

El diagrama entidad-relación está en `docs/diagrama_er.png`.

### Descripción de las tablas

| Tabla | Qué guarda | Llave primaria | Llaves foráneas |
|---|---|---|---|
| `marca` | Marcas de maquillaje que maneja la tienda | `id` (autoincremental) | Ninguna |
| `categoria` | Tipos de producto | `id` (autoincremental) | Ninguna |
| `producto` | Productos en inventario, con precio y existencias | `id` (autoincremental) | `marca` → `marca.id`, `categoria` → `categoria.id` |
| `venta` | Ventas realizadas | `id` (autoincremental) | `producto` → `producto.id` |

### Relaciones

| Relación | Tipo | Explicación |
|---|---|---|
| marca – producto | 1 a N | Cada fila de `producto` guarda en `marca` a cuál fila de `marca` pertenece |
| categoria – producto | 1 a N | Cada fila de `producto` guarda en `categoria` a cuál fila de `categoria` pertenece |
| producto – venta | 1 a N | Cada fila de `venta` guarda en `producto` a cuál fila de `producto` pertenece |

### Reglas de integridad

- Se activan las llaves foráneas de SQLite con `PRAGMA foreign_keys = ON` en cada conexión.
- `ON DELETE RESTRICT` en `producto.marca`, `producto.categoria`, `venta.producto`: no se puede eliminar un registro que otro todavía usa.
- Restricciones `CHECK`: las cantidades y los montos no pueden ser negativos.

### Regla de negocio

total = precio del producto × cantidad. Además, cada venta resta sus unidades de `producto.existencias`.
