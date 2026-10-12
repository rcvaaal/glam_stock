"""Conexión, esquema y datos de ejemplo de SQLite para Glam Stock."""
from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3

BASE_DIR = Path(__file__).resolve().parent

# En Vercel el proyecto es de solo lectura: el único lugar donde se puede
# escribir es /tmp. En la computadora la base queda junto al código.
if os.environ.get("VERCEL"):
    DB_PATH = Path("/tmp/glam_stock.db")
else:
    DB_PATH = BASE_DIR / "glam_stock.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS marca (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  pais TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS categoria (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  descripcion TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS producto (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  marca INTEGER NOT NULL,
  categoria INTEGER NOT NULL,
  tono TEXT NOT NULL,
  precio REAL NOT NULL CHECK(precio >= 0),
  existencias INTEGER NOT NULL CHECK(existencias >= 0),
  FOREIGN KEY (marca) REFERENCES marca(id) ON DELETE RESTRICT,
  FOREIGN KEY (categoria) REFERENCES categoria(id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS venta (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha TEXT NOT NULL,
  producto INTEGER NOT NULL,
  cantidad INTEGER NOT NULL CHECK(cantidad > 0),
  cliente TEXT NOT NULL,
  total REAL NOT NULL CHECK(total >= 0),
  FOREIGN KEY (producto) REFERENCES producto(id) ON DELETE RESTRICT
);
"""

# Datos de ejemplo: solo se insertan la primera vez, cuando la base está vacía.
SEED = """
INSERT INTO marca (nombre, pais) VALUES
  ('Maybelline', 'Estados Unidos'), ('NYX', 'Estados Unidos'), ('Rare Beauty', 'Estados Unidos'), ('Essence', 'Alemania');
INSERT INTO categoria (nombre, descripcion) VALUES
  ('Labiales', 'Barras, tintas y brillos para labios.'),
  ('Rostro', 'Bases, correctores, rubores e iluminadores.'),
  ('Ojos', 'Sombras, delineadores y máscaras de pestañas.');
INSERT INTO producto (nombre, marca, categoria, tono, precio, existencias) VALUES
  ('Labial SuperStay Matte Ink', 1, 1, 'Pioneer', 7500, 6),
  ('Base Fit Me Matte', 1, 2, '220 Natural Beige', 8900, 3),
  ('Delineador Epic Ink', 2, 3, 'Negro', 6800, 9),
  ('Rubor líquido Soft Pinch', 3, 2, 'Happy', 19500, 2),
  ('Máscara Lash Princess', 4, 3, 'Negro', 4200, 12);
INSERT INTO venta (fecha, producto, cantidad, cliente, total) VALUES
  ('2026-09-29', 1, 2, 'Valeria Montero', 15000),
  ('2026-10-02', 5, 3, 'Camila Rojas', 12600),
  ('2026-10-04', 4, 1, 'Sofía Jiménez', 19500);
"""


@contextmanager
def get_connection():
    """Abre una conexión, guarda los cambios si todo sale bien y siempre la cierra."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row            # permite leer las filas como diccionarios
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite no revisa llaves foráneas si no se activa
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database():
    """Crea las tablas si no existen y carga los datos de ejemplo una sola vez."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        vacia = conn.execute("SELECT COUNT(*) FROM marca").fetchone()[0] == 0
        if vacia:
            conn.executescript(SEED)
