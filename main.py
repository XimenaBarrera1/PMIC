from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import sqlite3

from services.pipeline_service import iniciar_proceso
from database import inicializar_db  

app = FastAPI(title="PMIC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

inicializar_db()


class ProcesoRequest(BaseModel):
    urls: List[str]
    workers_descarga: int
    workers_resize: int
    workers_formato: int
    workers_marca: int


@app.post("/procesar")
def procesar(request: ProcesoRequest):

    # Validacion de url
    if not request.urls:
        raise HTTPException(
            status_code=400,
            detail="Debe enviar al menos una URL"
        )

    if (
        request.workers_descarga <= 0 or
        request.workers_resize <= 0 or
        request.workers_formato <= 0 or
        request.workers_marca <= 0
    ):
        raise HTTPException(
            status_code=400,
            detail="La cantidad de workers debe ser mayor a 0"
        )

    try:
        id_proceso = iniciar_proceso(
            request.urls,
            request.workers_descarga,
            request.workers_resize,
            request.workers_formato,
            request.workers_marca
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al iniciar el proceso: {str(e)}"
        )

    return {
        "mensaje": "Proceso iniciado",
        "id_proceso": id_proceso
    }


DATABASE = "data/pmic.db"


@app.get("/estado/{id_proceso}")
def consultar_estado(id_proceso: str):

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM procesos WHERE id = ?",
        (id_proceso,)
    )
    proceso = cursor.fetchone()

    if not proceso:
        conn.close()
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    cursor.execute("""
        SELECT 
            etapa,
            COUNT(*) as total,
            SUM(CASE WHEN estado = 'ERROR' THEN 1 ELSE 0 END) as fallidos,
            SUM(tiempo_procesamiento) as tiempo_total
        FROM archivos
        WHERE proceso_id = ?
        GROUP BY etapa
    """, (id_proceso,))

    metricas = {}
    total_error_global = 0

    for row in cursor.fetchall():
        tiempo_total = row["tiempo_total"] or 0
        total = row["total"]
        fallidos = row["fallidos"] or 0

        tiempo_promedio = tiempo_total / total if total > 0 else 0

        metricas[row["etapa"]] = {
            "total_procesados": total,
            "total_fallidos": fallidos,
            "tiempo_total_acumulado": tiempo_total,
            "tiempo_promedio": tiempo_promedio
        }

        total_error_global += fallidos

    total_recibidos = proceso["total_archivos"]

    porcentaje_exito = (
        ((total_recibidos - total_error_global) / total_recibidos) * 100
        if total_recibidos and total_recibidos > 0 else 0
    )

    porcentaje_fallo = 100 - porcentaje_exito

    conn.close()

    return {
        "informacion_general": {
            "id_proceso": proceso["id"],
            "estado": proceso["estado"],
            "fecha_inicio": proceso["fecha_inicio"],
            "fecha_fin": proceso["fecha_fin"],
            "tiempo_total": proceso["tiempo_total"]
        },
        "metricas_por_etapa": metricas,
        "resumen_global": {
            "total_archivos_recibidos": total_recibidos,
            "total_archivos_con_error": total_error_global,
            "porcentaje_exito": porcentaje_exito,
            "porcentaje_fallo": porcentaje_fallo
        }
    }


app.mount("/", StaticFiles(directory="FrontEnd", html=True), name="index.html")