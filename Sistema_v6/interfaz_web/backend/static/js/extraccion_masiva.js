/**
 * Sistema de Extracción Masiva - Frontend JavaScript
 *
 * Maneja la lógica del dashboard de extracción masiva:
 * - Envío de configuración
 * - Conexión WebSocket para progreso en tiempo real
 * - Actualización de UI
 * - Control de extracción (pausar, reanudar, cancelar)
 * - Descarga de reportes
 */

class ExtraccionMasivaManager {
    constructor() {
        this.sessionId = null;
        this.websocket = null;
        this.estadoActual = null;

        // Elementos del DOM
        this.elementos = {
            // Panels
            panelConfig: document.getElementById('panelConfig'),
            panelProgreso: document.getElementById('panelProgreso'),
            panelResultados: document.getElementById('panelResultados'),
            panelError: document.getElementById('panelError'),

            // Formulario
            formConfig: document.getElementById('formConfig'),
            btnIniciar: document.getElementById('btnIniciar'),

            // Progreso
            statusBadge: document.getElementById('statusBadge'),
            statusText: document.getElementById('statusText'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            progressMessage: document.getElementById('progressMessage'),

            // Estadísticas
            statTotal: document.getElementById('statTotal'),
            statExitosos: document.getElementById('statExitosos'),
            statErrores: document.getElementById('statErrores'),
            statTiempo: document.getElementById('statTiempo'),
            statVelocidad: document.getElementById('statVelocidad'),
            statRestante: document.getElementById('statRestante'),

            // Fase
            phaseValue: document.getElementById('phaseValue'),

            // Botones de control
            btnPausar: document.getElementById('btnPausar'),
            btnReanudar: document.getElementById('btnReanudar'),
            btnCancelar: document.getElementById('btnCancelar'),

            // Resultados
            resultSessionId: document.getElementById('resultSessionId'),
            resultTotal: document.getElementById('resultTotal'),
            resultExitosos: document.getElementById('resultExitosos'),
            resultErrores: document.getElementById('resultErrores'),
            resultDuracion: document.getElementById('resultDuracion'),
            resultVelocidad: document.getElementById('resultVelocidad'),
            downloadGrid: document.getElementById('downloadGrid'),

            // Error
            errorMessage: document.getElementById('errorMessage'),
            btnReintentar: document.getElementById('btnReintentar'),

            // Nueva extracción
            btnNuevaExtraccion: document.getElementById('btnNuevaExtraccion'),

            // Log
            logContainer: document.getElementById('logContainer'),
        };

        this.inicializarEventos();
    }

    inicializarEventos() {
        // Evento de envío del formulario
        this.elementos.formConfig.addEventListener('submit', (e) => {
            e.preventDefault();
            this.iniciarExtraccion();
        });

        // Botones de control
        this.elementos.btnPausar.addEventListener('click', () => this.pausarExtraccion());
        this.elementos.btnReanudar.addEventListener('click', () => this.reanudarExtraccion());
        this.elementos.btnCancelar.addEventListener('click', () => this.cancelarExtraccion());

        // Botones de nueva extracción
        this.elementos.btnNuevaExtraccion.addEventListener('click', () => this.resetear());
        this.elementos.btnReintentar.addEventListener('click', () => this.resetear());
    }

    /**
     * Iniciar una nueva extracción masiva
     */
    async iniciarExtraccion() {
        try {
            // Recopilar configuración del formulario
            const config = this.recopilarConfiguracion();

            this.log('Enviando configuración de extracción...', 'info');

            // Deshabilitar botón de inicio
            this.elementos.btnIniciar.disabled = true;
            this.elementos.btnIniciar.textContent = '⏳ Iniciando...';

            // Enviar solicitud a la API
            const response = await fetch('/api/extraccion/masiva/iniciar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config),
            });

            if (!response.ok) {
                throw new Error(`Error HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.sessionId = data.session_id;

            this.log(`Extracción iniciada: ${this.sessionId}`, 'success');

            // Cambiar a panel de progreso
            this.mostrarPanel('progreso');

            // Conectar WebSocket para progreso
            this.conectarWebSocket();

            // Habilitar botones de control
            this.elementos.btnPausar.disabled = false;
            this.elementos.btnCancelar.disabled = false;

        } catch (error) {
            console.error('Error iniciando extracción:', error);
            this.mostrarError(`Error al iniciar extracción: ${error.message}`);
            this.elementos.btnIniciar.disabled = false;
            this.elementos.btnIniciar.textContent = '🚀 Iniciar Extracción';
        }
    }

    /**
     * Recopilar configuración del formulario
     */
    recopilarConfiguracion() {
        const formData = new FormData(this.elementos.formConfig);

        // Recopilar estados seleccionados
        const estados = [];
        document.querySelectorAll('input[name="estados"]:checked').forEach(cb => {
            estados.push(cb.value);
        });

        // Recopilar formatos seleccionados
        const formatos = [];
        document.querySelectorAll('input[name="formatos"]:checked').forEach(cb => {
            formatos.push(cb.value);
        });

        const config = {
            fecha_desde: formData.get('fecha_desde') || null,
            fecha_hasta: formData.get('fecha_hasta') || null,
            estados: estados.length > 0 ? estados : null,
            umbral_errores: parseInt(formData.get('umbral_errores')) || 10,
            headless: document.getElementById('headless').checked,
            exportar_formatos: formatos.length > 0 ? formatos : ['json'],
        };

        return config;
    }

    /**
     * Conectar WebSocket para recibir progreso en tiempo real
     */
    conectarWebSocket() {
        // Determinar protocolo (ws o wss)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/extraccion/masiva/ws/${this.sessionId}`;

        this.log(`Conectando WebSocket: ${wsUrl}`, 'info');

        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            this.log('WebSocket conectado', 'success');
        };

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.actualizarProgreso(data);
        };

        this.websocket.onerror = (error) => {
            console.error('Error WebSocket:', error);
            this.log('Error en conexión WebSocket', 'error');
        };

        this.websocket.onclose = () => {
            this.log('WebSocket desconectado', 'info');
        };

        // Enviar ping cada 30 segundos para mantener conexión
        this.pingInterval = setInterval(() => {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send('ping');
            }
        }, 30000);
    }

    /**
     * Actualizar UI con datos de progreso
     */
    actualizarProgreso(data) {
        this.estadoActual = data.estado;

        // Actualizar badge de estado
        this.elementos.statusBadge.className = `status-badge ${data.estado}`;
        this.elementos.statusText.textContent = this.traducirEstado(data.estado);

        // Actualizar barra de progreso
        const porcentaje = Math.round(data.porcentaje || 0);
        this.elementos.progressFill.style.width = `${porcentaje}%`;
        this.elementos.progressText.textContent = `${porcentaje}%`;
        this.elementos.progressMessage.textContent = data.mensaje || '';

        // Actualizar estadísticas
        this.elementos.statTotal.textContent = data.progreso_actual || 0;
        this.elementos.statTiempo.textContent = this.formatearTiempo(data.tiempo_transcurrido || 0);

        if (data.velocidad) {
            this.elementos.statVelocidad.textContent = `${data.velocidad.toFixed(1)}/min`;
        }

        if (data.tiempo_estimado) {
            this.elementos.statRestante.textContent = this.formatearTiempo(data.tiempo_estimado);
        }

        this.elementos.statErrores.textContent = data.errores || 0;

        // Actualizar fase
        this.elementos.phaseValue.textContent = this.traducirFase(data.fase);

        // Log de progreso
        this.log(`${data.mensaje} (${porcentaje}%)`, 'info');

        // Verificar si completó
        if (data.estado === 'completado') {
            this.extraccionCompletada();
        } else if (data.estado === 'error') {
            this.mostrarError(data.mensaje);
        } else if (data.estado === 'cancelado') {
            this.log('Extracción cancelada por el usuario', 'warning');
            this.mostrarPanel('config');
        }
    }

    /**
     * Cuando la extracción se completa
     */
    async extraccionCompletada() {
        this.log('✅ Extracción completada exitosamente', 'success');

        // Cerrar WebSocket
        if (this.websocket) {
            clearInterval(this.pingInterval);
            this.websocket.close();
        }

        // Obtener resumen final
        try {
            const response = await fetch(`/api/extraccion/masiva/resumen/${this.sessionId}`);

            if (!response.ok) {
                throw new Error('Error obteniendo resumen');
            }

            const resumen = await response.json();
            this.mostrarResultados(resumen);

        } catch (error) {
            console.error('Error obteniendo resumen:', error);
            this.log('Error obteniendo resumen final', 'error');
        }
    }

    /**
     * Mostrar panel de resultados
     */
    mostrarResultados(resumen) {
        this.elementos.resultSessionId.textContent = resumen.session_id;
        this.elementos.resultTotal.textContent = resumen.total;
        this.elementos.resultExitosos.textContent = resumen.exitosos;
        this.elementos.resultErrores.textContent = resumen.errores;
        this.elementos.resultDuracion.textContent = this.formatearTiempo(resumen.duracion_segundos);
        this.elementos.resultVelocidad.textContent = `${resumen.velocidad_promedio.toFixed(2)} exp/min`;

        // Generar botones de descarga
        this.generarBotonesDescarga();

        // Actualizar estadísticas finales en panel de progreso
        this.elementos.statExitosos.textContent = resumen.exitosos;
        this.elementos.statTotal.textContent = resumen.total;

        // Mostrar panel de resultados
        this.mostrarPanel('resultados');
    }

    /**
     * Generar botones de descarga de reportes
     */
    generarBotonesDescarga() {
        const formatos = [
            { nombre: 'JSON', icono: '📄', formato: 'json' },
            { nombre: 'Excel', icono: '📊', formato: 'excel' },
            { nombre: 'CSV', icono: '📋', formato: 'csv' },
            { nombre: 'HTML', icono: '🌐', formato: 'html' },
        ];

        this.elementos.downloadGrid.innerHTML = '';

        formatos.forEach(f => {
            const btn = document.createElement('a');
            btn.href = `/api/extraccion/masiva/descargar/${this.sessionId}/${f.formato}`;
            btn.className = 'download-btn';
            btn.textContent = `${f.icono} ${f.nombre}`;
            btn.download = `extraccion_${this.sessionId}.${f.formato}`;
            this.elementos.downloadGrid.appendChild(btn);
        });
    }

    /**
     * Pausar extracción
     */
    async pausarExtraccion() {
        try {
            const response = await fetch(`/api/extraccion/masiva/pausar/${this.sessionId}`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Error pausando extracción');
            }

            this.log('⏸️ Extracción pausada', 'warning');

            this.elementos.btnPausar.classList.add('hidden');
            this.elementos.btnReanudar.classList.remove('hidden');

        } catch (error) {
            console.error('Error pausando:', error);
            this.log('Error al pausar extracción', 'error');
        }
    }

    /**
     * Reanudar extracción
     */
    async reanudarExtraccion() {
        try {
            const response = await fetch(`/api/extraccion/masiva/reanudar/${this.sessionId}`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Error reanudando extracción');
            }

            this.log('▶️ Extracción reanudada', 'success');

            this.elementos.btnPausar.classList.remove('hidden');
            this.elementos.btnReanudar.classList.add('hidden');

        } catch (error) {
            console.error('Error reanudando:', error);
            this.log('Error al reanudar extracción', 'error');
        }
    }

    /**
     * Cancelar extracción
     */
    async cancelarExtraccion() {
        if (!confirm('¿Estás seguro de que deseas cancelar la extracción?')) {
            return;
        }

        try {
            const response = await fetch(`/api/extraccion/masiva/cancelar/${this.sessionId}`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Error cancelando extracción');
            }

            this.log('🛑 Extracción cancelada', 'warning');

            // Cerrar WebSocket
            if (this.websocket) {
                clearInterval(this.pingInterval);
                this.websocket.close();
            }

            // Volver a configuración
            setTimeout(() => this.resetear(), 2000);

        } catch (error) {
            console.error('Error cancelando:', error);
            this.log('Error al cancelar extracción', 'error');
        }
    }

    /**
     * Mostrar un panel específico
     */
    mostrarPanel(panel) {
        this.elementos.panelConfig.classList.add('hidden');
        this.elementos.panelProgreso.classList.add('hidden');
        this.elementos.panelResultados.classList.add('hidden');
        this.elementos.panelError.classList.add('hidden');

        if (panel === 'config') {
            this.elementos.panelConfig.classList.remove('hidden');
        } else if (panel === 'progreso') {
            this.elementos.panelProgreso.classList.remove('hidden');
        } else if (panel === 'resultados') {
            this.elementos.panelProgreso.classList.remove('hidden');
            this.elementos.panelResultados.classList.remove('hidden');
        } else if (panel === 'error') {
            this.elementos.panelError.classList.remove('hidden');
        }
    }

    /**
     * Mostrar error
     */
    mostrarError(mensaje) {
        this.elementos.errorMessage.textContent = mensaje;
        this.mostrarPanel('error');
        this.log(`❌ Error: ${mensaje}`, 'error');
    }

    /**
     * Resetear el sistema para nueva extracción
     */
    resetear() {
        // Cerrar WebSocket si existe
        if (this.websocket) {
            clearInterval(this.pingInterval);
            this.websocket.close();
            this.websocket = null;
        }

        // Resetear variables
        this.sessionId = null;
        this.estadoActual = null;

        // Resetear UI
        this.elementos.btnIniciar.disabled = false;
        this.elementos.btnIniciar.textContent = '🚀 Iniciar Extracción';
        this.elementos.btnPausar.classList.remove('hidden');
        this.elementos.btnReanudar.classList.add('hidden');

        // Resetear formulario
        this.elementos.formConfig.reset();

        // Limpiar log
        this.elementos.logContainer.innerHTML = '<p class="log-entry">Sistema listo para iniciar extracción...</p>';

        // Mostrar panel de configuración
        this.mostrarPanel('config');

        this.log('Sistema reiniciado', 'info');
    }

    /**
     * Agregar entrada al log
     */
    log(mensaje, tipo = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const entry = document.createElement('p');
        entry.className = `log-entry log-${tipo}`;
        entry.textContent = `[${timestamp}] ${mensaje}`;
        this.elementos.logContainer.appendChild(entry);

        // Auto-scroll al final
        this.elementos.logContainer.scrollTop = this.elementos.logContainer.scrollHeight;
    }

    /**
     * Traducir estado al español
     */
    traducirEstado(estado) {
        const traducciones = {
            'iniciando': 'Iniciando',
            'en_progreso': 'En Progreso',
            'completado': 'Completado',
            'error': 'Error',
            'pausado': 'Pausado',
            'cancelado': 'Cancelado',
        };
        return traducciones[estado] || estado;
    }

    /**
     * Traducir fase al español
     */
    traducirFase(fase) {
        const traducciones = {
            'configuracion': 'Configuración',
            'listado': 'Extrayendo Listado',
            'procesamiento': 'Procesando Expedientes',
            'exportacion': 'Generando Reportes',
            'finalizado': 'Finalizado',
        };
        return traducciones[fase] || fase;
    }

    /**
     * Formatear tiempo en segundos a formato legible
     */
    formatearTiempo(segundos) {
        if (!segundos || segundos < 0) return '0s';

        const horas = Math.floor(segundos / 3600);
        const minutos = Math.floor((segundos % 3600) / 60);
        const segs = Math.floor(segundos % 60);

        if (horas > 0) {
            return `${horas}h ${minutos}m ${segs}s`;
        } else if (minutos > 0) {
            return `${minutos}m ${segs}s`;
        } else {
            return `${segs}s`;
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.extraccionManager = new ExtraccionMasivaManager();
    console.log('Sistema de Extracción Masiva inicializado');
});
