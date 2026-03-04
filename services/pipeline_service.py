import os
import uuid
import queue
import threading
import sqlite3
from datetime import datetime

from database import insertar_proceso, finalizar_proceso
from config import RUTA_PROCESADAS

from workers.descarga_worker import worker_descarga
from workers.resize_worker import worker_resize
from workers.formato_worker import worker_formato
from workers.marca_worker import worker_marca

DATABASE = "data/pmic.db"


def iniciar_proceso(
    urls: list,
    n_descarga: int,
    n_resize: int,
    n_formato: int,
    n_marca: int,
):
    if not urls:
        raise Exception("Debe enviar al menos una URL")

    id_proceso = str(uuid.uuid4())
    fecha_inicio = datetime.now().isoformat()
    total_archivos = len(urls)

    insertar_proceso(id_proceso, fecha_inicio, total_archivos)

    # Crear carpeta del proceso
    ruta_proceso = os.path.join(RUTA_PROCESADAS, id_proceso)
    os.makedirs(ruta_proceso, exist_ok=True)

    # Crear colas
    cola_descarga = queue.Queue()
    cola_resize = queue.Queue()
    cola_formato = queue.Queue()
    cola_marca = queue.Queue()

    # Workers descarga
    for i in range(n_descarga):
        t = threading.Thread(
            target=worker_descarga,
            args=(cola_descarga, cola_resize, id_proceso),
            name=f"D{i+1}",
            daemon=True
        )
        t.start()

    # Workers resize
    for i in range(n_resize):
        t = threading.Thread(
            target=worker_resize,
            args=(cola_resize, cola_formato, id_proceso),
            name=f"R{i+1}",
            daemon=True
        )
        t.start()

    # Workers formato
    for i in range(n_formato):
        t = threading.Thread(
            target=worker_formato,
            args=(cola_formato, cola_marca, id_proceso),
            name=f"F{i+1}",
            daemon=True
        )
        t.start()

    # Workers marca
    for i in range(n_marca):
        t = threading.Thread(
            target=worker_marca,
            args=(cola_marca, id_proceso),
            name=f"M{i+1}",
            daemon=True
        )
        t.start()

    # Encolar URLs
    for url in urls:
        cola_descarga.put((url, ruta_proceso))

    # Hilo de finalización
    def esperar_finalizacion():
        cola_descarga.join()
        cola_resize.join()
        cola_formato.join()
        cola_marca.join()

        fecha_fin = datetime.now()
        tiempo_total = (
            fecha_fin - datetime.fromisoformat(fecha_inicio)
        ).total_seconds()

        # 🔥 NUEVA LÓGICA DE ESTADO FINAL
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Total errores
        cursor.execute("""
            SELECT COUNT(*) FROM archivos
            WHERE proceso_id = ? AND estado = 'ERROR'
        """, (id_proceso,))
        total_errores = cursor.fetchone()[0]

        # Total registros generados
        cursor.execute("""
            SELECT COUNT(*) FROM archivos
            WHERE proceso_id = ?
        """, (id_proceso,))
        total_registros = cursor.fetchone()[0]

        conn.close()

        if total_registros == 0:
            estado_final = "FALLIDO"
        elif total_errores == 0:
            estado_final = "COMPLETADO"
        elif total_errores == total_registros:
            estado_final = "FALLIDO"
        else:
            estado_final = "COMPLETADO_CON_ERRORES"

        finalizar_proceso(
            id_proceso,
            estado_final,
            fecha_fin.isoformat(),
            tiempo_total
        )

        print("Proceso finalizado:", id_proceso, "Estado:", estado_final)

    threading.Thread(target=esperar_finalizacion, daemon=True).start()

    return id_proceso