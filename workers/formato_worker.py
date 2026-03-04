import os
import time
import threading
from datetime import datetime
from PIL import Image

from database import insertar_archivo
from config import RUTA_PROCESADAS


def worker_formato(cola_formato, cola_marca, id_proceso):
    while True:
        ruta_imagen = cola_formato.get()

        try:
            inicio = time.time()

            ruta_proceso = os.path.join(RUTA_PROCESADAS, id_proceso)
            os.makedirs(ruta_proceso, exist_ok=True)

            nombre_base = os.path.basename(ruta_imagen)
            nombre_sin_ext, ext = os.path.splitext(nombre_base)

            ext = ext.lower()

            # 🔥 CASO 1: YA ES PNG → NO SE CONVIERTE
            if ext == ".png":

                ruta_salida = ruta_imagen  # Se deja igual
                nuevo_nombre = nombre_base

            # 🔥 CASO 2: NO ES PNG → CONVERTIR
            else:
                with Image.open(ruta_imagen) as img:

                    nuevo_nombre = f"{nombre_sin_ext}_formato_cambiado.png"
                    ruta_salida = os.path.join(ruta_proceso, nuevo_nombre)

                    img.convert("RGBA").save(ruta_salida, "PNG")

            fin = time.time()
            tiempo_procesamiento = fin - inicio

            tamano_mb = os.path.getsize(ruta_salida) / (1024 * 1024)

            datos = (
                id_proceso,
                nuevo_nombre,
                "FORMATO",
                threading.current_thread().name,
                tiempo_procesamiento,
                tamano_mb,
                datetime.now().isoformat(),
                "COMPLETADO",
                None
            )

            insertar_archivo(datos)

            # Siempre pasa a la cola de marca
            cola_marca.put(ruta_salida)

        except Exception as e:

            datos = (
                id_proceso,
                os.path.basename(ruta_imagen),
                "FORMATO",
                threading.current_thread().name,
                0,
                0,
                datetime.now().isoformat(),
                "ERROR",
                str(e)
            )

            insertar_archivo(datos)
            print(f"[ERROR FORMATO] {ruta_imagen} -> {e}")

        finally:
            cola_formato.task_done()