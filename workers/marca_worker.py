import os
import time
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from database import insertar_archivo
from config import RUTA_PROCESADAS


def worker_marca(cola_marca, id_proceso):
    while True:
        ruta_imagen = cola_marca.get()

        try:
            inicio = time.time()

            ruta_proceso = os.path.join(RUTA_PROCESADAS, id_proceso)
            os.makedirs(ruta_proceso, exist_ok=True)

            with Image.open(ruta_imagen).convert("RGBA") as img:

                ancho, alto = img.size
                texto = "PMIC - ACME"

                draw = ImageDraw.Draw(img)

                #Tamaño dinámico del texto
                tamaño_fuente = int(ancho * 0.05)

                try:
                    fuente = ImageFont.truetype("arial.ttf", tamaño_fuente)
                except:
                    fuente = ImageFont.load_default()

                bbox = draw.textbbox((0, 0), texto, font=fuente)
                texto_ancho = bbox[2] - bbox[0]
                texto_alto = bbox[3] - bbox[1]

                #Posición de la marca de agua en la esquina inferior derecha con margen
                margen = 10
                posicion = (
                    ancho - texto_ancho - margen,
                    alto - texto_alto - margen
                )

                draw.text(
                    posicion,
                    texto,
                    font=fuente,
                    fill=(255, 0, 0, 180) 
                )

                nombre_base = os.path.basename(ruta_imagen)
                nombre_sin_ext, ext = os.path.splitext(nombre_base)

                nuevo_nombre = f"{nombre_sin_ext}_marca_agua{ext}"
                ruta_salida = os.path.join(ruta_proceso, nuevo_nombre)

                img.save(ruta_salida)

            fin = time.time()
            tiempo_procesamiento = fin - inicio

            tamano_mb = os.path.getsize(ruta_salida) / (1024 * 1024)

            datos = (
                id_proceso,
                nuevo_nombre,
                "MARCA",
                threading.current_thread().name,
                tiempo_procesamiento,
                tamano_mb,
                datetime.now().isoformat(),
                "COMPLETADO",
                None
            )

            insertar_archivo(datos)

        except Exception as e:

            datos = (
                id_proceso,
                os.path.basename(ruta_imagen),
                "MARCA",
                threading.current_thread().name,
                0,
                0,
                datetime.now().isoformat(),
                "ERROR",
                str(e)
            )

            insertar_archivo(datos)
            print(f"[ERROR MARCA] {ruta_imagen} -> {e}")

        finally:
            cola_marca.task_done()