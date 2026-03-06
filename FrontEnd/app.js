const API = "http://127.0.0.1:8001";

async function iniciarProceso() {
    const urlsVal = document.getElementById("urls").value.trim();
    if (!urlsVal) return alert("Ingrese URLs");

    const payload = {
        urls: urlsVal.split("\n"),
        workers_descarga: parseInt(document.getElementById("workers_descarga").value),
        workers_resize: parseInt(document.getElementById("workers_resize").value),
        workers_formato: parseInt(document.getElementById("workers_formato").value),
        workers_marca: parseInt(document.getElementById("workers_marca").value)
    };

    const response = await fetch(`${API}/procesar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await response.json();
    document.getElementById("resultado").innerText = "ID del proceso: " + data.id_proceso;
    document.getElementById("id_proceso").value = data.id_proceso;
}

async function consultarEstado() {
    const id = document.getElementById("id_proceso").value;
    if (!id) return;

    const response = await fetch(`${API}/estado/${id}`);
    const data = await response.json();
    mostrarEstado(data);
}

function mostrarEstado(data) {
    let html = "";

    // 1. INFORMACIÓN GENERAL (Todos los campos)
    html += `<h3 class="section-h3">Información General</h3>`;
    html += `
        <div class="info-card">
            <p><strong>ID:</strong> ${data.informacion_general.id_proceso}</p>
            <p><strong>Estado:</strong> ${data.informacion_general.estado}</p>
            <p><strong>Fecha Inicio:</strong> ${data.informacion_general.fecha_inicio}</p>
            <p><strong>Fecha Fin:</strong> ${data.informacion_general.fecha_fin || 'En proceso...'}</p>
            <p><strong>Tiempo Total:</strong> ${data.informacion_general.tiempo_total}</p>
        </div>
    `;

    // 2. MÉTRICAS POR ETAPA (En Tabla Dinámica)
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
        let m = data.metricas_por_etapa[etapa];
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

    // 3. RESUMEN GLOBAL (Todos los campos)
    html += `<h3 class="section-h3">Resumen Global</h3>`;
    const res = data.resumen_global;
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