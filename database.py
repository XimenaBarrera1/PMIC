import sqlite3
import threading
from config import RUTA_DB

db_lock = threading.Lock()


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