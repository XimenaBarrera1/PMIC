import os
import time
import threading
from PIL import Image
from database import insertar_archivo
from config import RUTA_PROCESADAS

NUEVO_ANCHO = 800


def worker_resize(cola_resize, cola_formato, proceso_id):
    while True:
        ruta_imagen = cola_resize.get()
        inicio = time.time()
        worker_name = threading.current_thread().name

        try:
            print("Redimensionando:", ruta_imagen)
            print("Existe archivo:", os.path.exists(ruta_imagen))

            # Carpeta del proceso
            ruta_proceso = os.path.join(RUTA_PROCESADAS, proceso_id)
            os.makedirs(ruta_proceso, exist_ok=True)

            # Abrir imagen
            with Image.open(ruta_imagen) as img:
                ancho_original, alto_original = img.size

                nuevo_alto = int(alto_original * (NUEVO_ANCHO / ancho_original))
                img_redimensionada = img.resize((NUEVO_ANCHO, nuevo_alto))

                nombre_base = os.path.basename(ruta_imagen)
                nombre_sin_ext, ext = os.path.splitext(nombre_base)

                nuevo_nombre = f"{nombre_sin_ext}_redimensionado{ext}"
                ruta_salida = os.path.join(ruta_proceso, nuevo_nombre)

                img_redimensionada.save(ruta_salida)

            fin = time.time()
            tiempo_procesamiento = fin - inicio

            tamano_mb = os.path.getsize(ruta_salida) / (1024 * 1024)

            insertar_archivo((
                proceso_id,
                nuevo_nombre,
                "RESIZE",
                worker_name,
                tiempo_procesamiento,
                tamano_mb,
                time.strftime("%Y-%m-%d %H:%M:%S"),
                "COMPLETADO",
                None
            ))

            # Enviar a siguiente etapa
            cola_formato.put(ruta_salida)

        except Exception as e:
            fin = time.time()
            tiempo_procesamiento = fin - inicio

            insertar_archivo((
                proceso_id,
                os.path.basename(ruta_imagen),
                "RESIZE",
                worker_name,
                tiempo_procesamiento,
                0,
                time.strftime("%Y-%m-%d %H:%M:%S"),
                "ERROR",
                str(e)
            ))

            print(f"[ERROR RESIZE] {e}")

        finally:
            cola_resize.task_done()