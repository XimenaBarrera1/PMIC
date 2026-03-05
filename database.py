import sqlite3
import threading
import os
from config import RUTA_DB

db_lock = threading.Lock()


def inicializar_db():
    # Crear carpeta data si no existe
    os.makedirs(os.path.dirname(RUTA_DB), exist_ok=True)

    conn = sqlite3.connect(RUTA_DB)
    cursor = conn.cursor()

    # Crear tabla procesos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS procesos (
        id TEXT PRIMARY KEY,
        estado TEXT NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT,
        tiempo_total REAL,
        total_archivos INTEGER NOT NULL
    );
    """)

    # Crear tabla archivos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS archivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proceso_id TEXT NOT NULL,
        nombre_archivo TEXT NOT NULL,
        etapa TEXT NOT NULL,
        worker TEXT NOT NULL,
        tiempo_procesamiento REAL,
        tamano_mb REAL,
        fecha_procesamiento TEXT NOT NULL,
        estado TEXT NOT NULL,
        error_mensaje TEXT,
        FOREIGN KEY (proceso_id) REFERENCES procesos(id)
    );
    """)

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(RUTA_DB, check_same_thread=False)


def insertar_proceso(id_proceso, fecha_inicio, total_archivos):
    conn = get_connection()
    cursor = conn.cursor()

    with db_lock:
        cursor.execute("""
            INSERT INTO procesos (id, estado, fecha_inicio, total_archivos)
            VALUES (?, 'EN_PROCESO', ?, ?)
        """, (id_proceso, fecha_inicio, total_archivos))
        conn.commit()

    conn.close()


def insertar_archivo(datos):
    conn = get_connection()
    cursor = conn.cursor()

    with db_lock:
        cursor.execute("""
            INSERT INTO archivos (
                proceso_id,
                nombre_archivo,
                etapa,
                worker,
                tiempo_procesamiento,
                tamano_mb,
                fecha_procesamiento,
                estado,
                error_mensaje
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, datos)
        conn.commit()

    conn.close()


def finalizar_proceso(id_proceso, estado_final, fecha_fin, tiempo_total):
    conn = get_connection()
    cursor = conn.cursor()

    with db_lock:
        cursor.execute("""
            UPDATE procesos
            SET estado = ?, fecha_fin = ?, tiempo_total = ?
            WHERE id = ?
        """, (estado_final, fecha_fin, tiempo_total, id_proceso))
        conn.commit()

    conn.close()