import os
import time
import threading
import requests
from datetime import datetime
from urllib.parse import urlparse

from database import insertar_archivo


def worker_descarga(cola_descarga, cola_resize, id_proceso):

    while True:
        url, ruta_proceso = cola_descarga.get()

        try:
            inicio = time.time()

            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            print("Descargando:", url)

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            print("Tamaño descargado:", len(response.content))

            # Obtener nombre del archivo desde la URL
            nombre_archivo = os.path.basename(urlparse(url).path)

            if not nombre_archivo:
                nombre_archivo = f"imagen_{int(time.time())}.jpg"

            ruta_destino = os.path.join(ruta_proceso, nombre_archivo)

            with open(ruta_destino, "wb") as f:
                f.write(response.content)

            print("Guardado en:", ruta_destino)

            fin = time.time()
            tiempo_procesamiento = fin - inicio

            tamaño_bytes = os.path.getsize(ruta_destino)
            tamano_mb = tamaño_bytes / (1024 * 1024)

            datos = (
                id_proceso,
                nombre_archivo,
                "DESCARGA",
                threading.current_thread().name,
                tiempo_procesamiento,
                tamano_mb,
                datetime.now().isoformat(),
                "COMPLETADO",
                None
            )

            insertar_archivo(datos)

            # Enviar archivo descargado a resize
            cola_resize.put(ruta_destino)

        except Exception as e:

            datos = (
                id_proceso,
                url,
                "DESCARGA",
                threading.current_thread().name,
                0,
                0,
                datetime.now().isoformat(),
                "ERROR",
                str(e)
            )

            insertar_archivo(datos)

            print(f"[ERROR DESCARGA] {url} -> {e}")

        finally:
            cola_descarga.task_done()