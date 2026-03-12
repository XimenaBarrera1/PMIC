const API = window.location.origin;

/*
Se actualizó este archivo para:
- limpiar URLs vacías antes de enviarlas
- validar que los workers sean enteros mayores a 0
- manejar errores del backend y de red
- mostrar mensajes de estado mientras se procesa o consulta
*/

async function iniciarProceso() {
    const urlsVal = document.getElementById("urls").value.trim();

    if (!urlsVal) {
        alert("Ingrese al menos una URL.");
        return;
    }

    const urls = urlsVal
        .split("\n")
        .map(url => url.trim())
        .filter(url => url !== "");

    if (urls.length === 0) {
        alert("Ingrese al menos una URL válida.");
        return;
    }

    const workers_descarga = parseInt(document.getElementById("workers_descarga").value);
    const workers_resize = parseInt(document.getElementById("workers_resize").value);
    const workers_formato = parseInt(document.getElementById("workers_formato").value);
    const workers_marca = parseInt(document.getElementById("workers_marca").value);

    const workers = [
        workers_descarga,
        workers_resize,
        workers_formato,
        workers_marca
    ];

    const workersValidos = workers.every(w => Number.isInteger(w) && w > 0);

    if (!workersValidos) {
        alert("Todos los workers deben ser números enteros mayores a 0.");
        return;
    }

    const payload = {
        urls,
        workers_descarga,
        workers_resize,
        workers_formato,
        workers_marca
    };

    document.getElementById("resultado").innerText = "Enviando proceso...";
    document.getElementById("estado").innerHTML = `<p class="empty-state">Iniciando procesamiento...</p>`;

    try {
        const response = await fetch(`${API}/procesar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "No se pudo iniciar el proceso.");
        }

        document.getElementById("resultado").innerText = "ID del proceso: " + data.id_proceso;
        document.getElementById("id_proceso").value = data.id_proceso;
    } catch (error) {
        document.getElementById("resultado").innerText = "";
        document.getElementById("estado").innerHTML = `
            <div class="info-card">
                <p><strong>Error:</strong> ${error.message}</p>
            </div>
        `;
    }
}

async function consultarEstado() {
    const id = document.getElementById("id_proceso").value.trim();

    if (!id) {
        alert("Ingrese un ID de proceso.");
        return;
    }

    document.getElementById("estado").innerHTML = `<p class="empty-state">Consultando estado...</p>`;

    try {
        const response = await fetch(`${API}/estado/${id}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "No se pudo consultar el estado.");
        }

        mostrarEstado(data);
    } catch (error) {
        document.getElementById("estado").innerHTML = `
            <div class="info-card">
                <p><strong>Error:</strong> ${error.message}</p>
            </div>
        `;
    }
}

function mostrarEstado(data) {
    let html = "";

    html += `<h3 class="section-h3">Información General</h3>`;
    html += `
        <div class="info-card">
            <p><strong>ID:</strong> ${data.informacion_general.id_proceso}</p>
            <p><strong>Estado:</strong> ${data.informacion_general.estado}</p>
            <p><strong>Fecha Inicio:</strong> ${data.informacion_general.fecha_inicio}</p>
            <p><strong>Fecha Fin:</strong> ${data.informacion_general.fecha_fin || "En proceso..."}</p>
            <p><strong>Tiempo Total:</strong> ${data.informacion_general.tiempo_total}</p>
        </div>
    `;

    html += `<h3 class="section-h3">Métricas por Etapa</h3>`;
    html += `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Etapa</th>
                    <th>Procesados</th>
                    <th>Fallidos</th>
                    <th>T. Acumulado</th>
                    <th>T. Promedio</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const etapa in data.metricas_por_etapa) {
        const m = data.metricas_por_etapa[etapa];
        html += `
            <tr>
                <td><strong>${etapa}</strong></td>
                <td>${m.total_procesados}</td>
                <td>${m.total_fallidos}</td>
                <td>${m.tiempo_total_acumulado}</td>
                <td>${m.tiempo_promedio}</td>
            </tr>
        `;
    }

    html += `</tbody></table>`;

    const res = data.resumen_global;
    html += `<h3 class="section-h3">Resumen Global</h3>`;
    html += `
        <div class="info-card" style="border-left: 5px solid var(--dark);">
            <p><strong>Total Archivos Recibidos:</strong> ${res.total_archivos_recibidos}</p>
            <p><strong>Total con Error:</strong> ${res.total_archivos_con_error}</p>
            <p><strong>Porcentaje de Éxito:</strong> ${res.porcentaje_exito}</p>
            <p><strong>Porcentaje de Fallo:</strong> ${res.porcentaje_fallo}</p>
        </div>
    `;

    document.getElementById("estado").innerHTML = html;
}