"""Glam Stock: API REST con FastAPI + SQLite. Inventario y ventas de una tienda de maquillaje."""
from datetime import date
from pathlib import Path
import os
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from database import get_connection, initialize_database

# Crea las tablas (y los datos de ejemplo) antes de atender la primera petición.
initialize_database()

app = FastAPI(title="Glam Stock", description="Inventario y ventas de una tienda de maquillaje.", version="1.0.0")


# ==================== Modelos: validan los datos que llegan a la API ====================

class Marca(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    pais: str = Field(min_length=1, max_length=120)


class Categoria(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(min_length=1, max_length=500)


class Producto(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    marca: int
    categoria: int
    tono: str = Field(min_length=1, max_length=120)
    precio: float = Field(ge=0)
    existencias: int = Field(ge=0)


class Venta(BaseModel):
    fecha: date
    producto: int
    cantidad: int = Field(gt=0)
    cliente: str = Field(min_length=1, max_length=120)


# ==================== Reglas de negocio ====================
def regla_venta(conn, nuevo, anterior):
    """Regla de negocio: una venta mueve el inventario y calcula su total.

    anterior = la venta como estaba guardada (None si se está creando).
    nuevo    = la venta que se va a guardar (None si se está eliminando).
    """
    # Si la venta ya existía, primero se devuelven sus unidades al inventario.
    if anterior:
        conn.execute("UPDATE producto SET existencias = existencias + ? WHERE id = ?",
                     (anterior["cantidad"], anterior["producto"]))
    if nuevo:
        producto = conn.execute("SELECT precio, existencias FROM producto WHERE id = ?",
                                (nuevo["producto"],)).fetchone()
        if not producto:
            raise HTTPException(400, "El producto seleccionado no existe.")
        if nuevo["cantidad"] > producto["existencias"]:
            raise HTTPException(409, f"No alcanza el inventario: quedan {producto['existencias']} en existencia.")
        nuevo["total"] = producto["precio"] * nuevo["cantidad"]
        conn.execute("UPDATE producto SET existencias = existencias - ? WHERE id = ?",
                     (nuevo["cantidad"], nuevo["producto"]))


# ==================== Marcas ====================
# Consulta base: trae cada fila de marca.
CONSULTA_MARCA = """
SELECT t.*
FROM marca t
"""


@app.get("/api/marcas")
def listar_marcas():
    with get_connection() as conn:
        return [dict(fila) for fila in conn.execute(CONSULTA_MARCA + " ORDER BY t.nombre")]


@app.get("/api/marcas/{id}")
def obtener_marca(id: int):
    with get_connection() as conn:
        fila = conn.execute(CONSULTA_MARCA + " WHERE t.id = ?", (id,)).fetchone()
    if not fila:
        raise HTTPException(404, "No se encontró la marca.")
    return dict(fila)


@app.post("/api/marcas", status_code=201)
def crear_marca(datos: Marca):
    nuevo = datos.model_dump(mode="json")
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO marca (nombre, pais) VALUES (:nombre, :pais)", nuevo)
            nuevo["id"] = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "No se pudo guardar: revise los datos.")
    return nuevo


@app.put("/api/marcas/{id}")
def actualizar_marca(id: int, datos: Marca):
    nuevo = datos.model_dump(mode="json")
    try:
        with get_connection() as conn:
            anterior = conn.execute("SELECT * FROM marca WHERE id = ?", (id,)).fetchone()
            if not anterior:
                raise HTTPException(404, "No se encontró la marca.")
            conn.execute("UPDATE marca SET nombre = :nombre, pais = :pais WHERE id = :pk_url", {**nuevo, "pk_url": id})
    except sqlite3.IntegrityError:
        raise HTTPException(409, "No se pudo guardar: revise los datos.")
    return {"id": id, **nuevo}


@app.delete("/api/marcas/{id}", status_code=204)
def eliminar_marca(id: int):
    try:
        with get_connection() as conn:
            anterior = conn.execute("SELECT * FROM marca WHERE id = ?", (id,)).fetchone()
            if not anterior:
                raise HTTPException(404, "No se encontró la marca.")
            conn.execute("DELETE FROM marca WHERE id = ?", (id,))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "No se puede eliminar la marca: hay productos que dependen de este registro.")


# ==================== Categorías ====================
# Consulta base: trae cada fila de categoria.
CONSULTA_CATEGORIA = """
SELECT t.*
FROM categoria t
"""


@app.get("/api/categorias")
def listar_categorias():
    with get_connection() as conn:
        return [dict(fila) for fila in conn.execute(CONSULTA_CATEGORIA + " ORDER BY t.nombre")]


@app.get("/api/categorias/{id}")
def obtener_categoria(id: int):
    with get_connection() as conn:
        fila = conn.execute(CONSULTA_CATEGORIA + " WHERE t.id = ?", (id,)).fetchone()
    if not fila:
        raise HTTPException(404, "No se encontró la categoría.")
    return dict(fila)


@app.post("/api/categorias", status_code=201)
def crear_categoria(datos: Categoria):
    nuevo = datos.model_dump(mode="json")
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO categoria (nombre, descripcion) VALUES (:nombre, :descripcion)", nuevo)
            nuevo["id"] = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "No se pudo guardar: revise los datos.")
    return nuevo


@app.put("/api/categorias/{id}")
def actualizar_categoria(id: int, datos: Categoria):
    nuevo = datos.model_dump(mode="json")
    try:
        with get_connection() as conn:
            anterior = conn.execute("SELECT * FROM categoria WHERE id = ?", (id,)).fetchone()
            if not anterior:
                raise HTTPException(404, "No se encontró la categoría.")
            conn.execute("UPDATE categoria SET nombre = :nombre, descripcion = :descripcion WHERE id = :pk_url", {**nuevo, "pk_url": id})
    except sqlite3.IntegrityError:
        raise HTTPException(409, "No se pudo guardar: revise los datos.")
    return {"id": id, **nuevo}


@app.delete("/api/categorias/{id}", status_code=204)
def eliminar_categoria(id: int):
    try:
        with get_connection() as conn:
            anterior = conn.execute("SELECT * FROM categoria WHERE id = ?", (id,)).fetchone()
            if not anterior:
                raise HTTPException(404, "No se encontró la categoría.")
            conn.execute("DELETE FROM categoria WHERE id = ?", (id,))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "No se puede eliminar la categoría: hay productos que dependen de este registro.")


# ==================== Productos ====================
# Consulta base: trae cada fila de producto con el nombre de sus datos relacionados.
CONSULTA_PRODUCTO = """
SELECT t.*,
       (SELECT nombre FROM marca WHERE id = t.marca) AS marca_nombre,
       (SELECT nombre FROM categoria WHERE id = t.categoria) AS categoria_nombre
FROM producto t
"""


@app.get("/api/productos")
def listar_productos():
    with get_connection() as conn:
        return [dict(fila) for fila in conn.execute(CONSULTA_PRODUCTO + " ORDER BY t.nombre")]


@app.get("/api/productos/{id}")
def obtener_producto(id: int):
    with get_connection() as conn:
        fila = conn.execute(CONSULTA_PRODUCTO + " WHERE t.id = ?", (id,)).fetchone()
    if not fila:
        raise HTTPException(404, "No se encontró el producto.")
    return dict(fila)


@app.post("/api/productos", status_code=201)
def crear_producto(datos: Producto):
    nuevo = datos.model_dump(mode="json")
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO producto (nombre, marca, categoria, tono, precio, existencias) VALUES (:nombre, :marca, :categoria, :tono, :precio, :existencias)", nuevo)
            nuevo["id"] = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Revise los datos: alguno de los registros relacionados no existe.")
    return nuevo


@app.put("/api/productos/{id}")
def actualizar_producto(id: int, datos: Producto):
    nuevo = datos.model_dump(mode="json")
    try:
        with get_connection() as conn:
            anterior = conn.execute("SELECT * FROM producto WHERE id = ?", (id,)).fetchone()
            if not anterior:
                raise HTTPException(404, "No se encontró el producto.")
            conn.execute("UPDATE producto SET nombre = :nombre, marca = :marca, categoria = :categoria, tono = :tono, precio = :precio, existencias = :existencias WHERE id = :pk_url", {**nuevo, "pk_url": id})
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Revise los datos: alguno de los registros relacionados no existe.")
    return {"id": id, **nuevo}


@app.delete("/api/productos/{id}", status_code=204)
def eliminar_producto(id: int):
    try:
        with get_connection() as conn:
            anterior = conn.execute("SELECT * FROM producto WHERE id = ?", (id,)).fetchone()
            if not anterior:
                raise HTTPException(404, "No se encontró el producto.")
            conn.execute("DELETE FROM producto WHERE id = ?", (id,))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "No se puede eliminar el producto: hay ventas que dependen de este registro.")


# ==================== Ventas ====================
# Consulta base: trae cada fila de venta con el nombre de sus datos relacionados.
CONSULTA_VENTA = """
SELECT t.*,
       (SELECT nombre FROM producto WHERE id = t.producto) AS producto_nombre
FROM venta t
"""


@app.get("/api/ventas")
def listar_ventas():
    with get_connection() as conn:
        return [dict(fila) for fila in conn.execute(CONSULTA_VENTA + " ORDER BY t.id DESC")]


@app.get("/api/ventas/{id}")
def obtener_venta(id: int):
    with get_connection() as conn:
        fila = conn.execute(CONSULTA_VENTA + " WHERE t.id = ?", (id,)).fetchone()
    if not fila:
        raise HTTPException(404, "No se encontró la venta.")
    return dict(fila)


@app.post("/api/ventas", status_code=201)
def crear_venta(datos: Venta):
    nuevo = datos.model_dump(mode="json")
    try:
        with get_connection() as conn:
            regla_venta(conn, nuevo, None)
            cursor = conn.execute(
                "INSERT INTO venta (fecha, producto, cantidad, cliente, total) VALUES (:fecha, :producto, :cantidad, :cliente, :total)", nuevo)
            nuevo["id"] = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Revise los datos: alguno de los registros relacionados no existe.")
    return nuevo


@app.put("/api/ventas/{id}")
def actualizar_venta(id: int, datos: Venta):
    nuevo = datos.model_dump(mode="json")
    try:
        with get_connection() as conn:
            anterior = conn.execute("SELECT * FROM venta WHERE id = ?", (id,)).fetchone()
            if not anterior:
                raise HTTPException(404, "No se encontró la venta.")
            regla_venta(conn, nuevo, anterior)
            conn.execute("UPDATE venta SET fecha = :fecha, producto = :producto, cantidad = :cantidad, cliente = :cliente, total = :total WHERE id = :pk_url", {**nuevo, "pk_url": id})
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Revise los datos: alguno de los registros relacionados no existe.")
    return {"id": id, **nuevo}


@app.delete("/api/ventas/{id}", status_code=204)
def eliminar_venta(id: int):
    try:
        with get_connection() as conn:
            anterior = conn.execute("SELECT * FROM venta WHERE id = ?", (id,)).fetchone()
            if not anterior:
                raise HTTPException(404, "No se encontró la venta.")
            regla_venta(conn, None, anterior)
            conn.execute("DELETE FROM venta WHERE id = ?", (id,))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "No se puede eliminar la venta.")


# ==================== Resumen ====================
@app.get("/api/resumen")
def resumen():
    """Calcula estadísticas con consultas SQL para la pantalla de resumen."""
    with get_connection() as conn:
        vendido = conn.execute("SELECT COALESCE(SUM(total), 0), COUNT(*) FROM venta").fetchone()
        estrella = conn.execute(
            """SELECT p.nombre, SUM(v.cantidad) AS unidades FROM venta v
               JOIN producto p ON p.id = v.producto GROUP BY p.id ORDER BY unidades DESC LIMIT 1""").fetchone()
        pocos = conn.execute("SELECT nombre, existencias FROM producto WHERE existencias <= 3 ORDER BY existencias").fetchall()
        inventario = conn.execute("SELECT COALESCE(SUM(precio * existencias), 0) FROM producto").fetchone()[0]
    return [
        {"dato": "Ventas registradas", "valor": str(vendido[1])},
        {"dato": "Dinero vendido", "valor": f"₡{vendido[0]:,.0f}".replace(",", " ")},
        {"dato": "Producto más vendido", "valor": f"{estrella['nombre']} ({estrella['unidades']} unidades)" if estrella else "Aún no hay ventas"},
        {"dato": "Valor del inventario", "valor": f"₡{inventario:,.0f}".replace(",", " ")},
        {"dato": "Productos por agotarse (3 o menos)",
         "valor": ", ".join(f"{p['nombre']} ({p['existencias']})" for p in pocos) or "Ninguno"},
    ]


# El frontend vive en public/. Vercel publica esa carpeta por su cuenta,
# así que solo se monta desde FastAPI cuando el proyecto corre en la computadora.
# Va al final para que las rutas /api y /docs tengan prioridad.
if not os.environ.get("VERCEL"):
    app.mount("/", StaticFiles(directory=Path(__file__).parent / "public", html=True), name="frontend")
