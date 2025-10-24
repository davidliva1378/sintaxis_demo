# Agentes del Sistema Jurídico

Este documento describe los distintos **agentes funcionales** del sistema jurídico. Cada agente representa un conjunto de tareas autónomas que pueden actuar de forma independiente o coordinada con otros módulos.

---

## 🧭 1. Agente de Extracción de Datos

**Responsabilidad:**  
Extrae expedientes, notificaciones y actuaciones desde el portal del Poder Judicial de la Nación (PJN) mediante navegación automatizada.

**Componentes relacionados:**
- `panel_pjn/web/auto_login.py`
- `panel_pjn/acciones_pjn/expedientes/`
- `panel_pjn/acciones_pjn/notificaciones/`

**Funciones destacadas:**
- Login automático al PJN
- Extracción completa o incremental
- Registro de metadatos
- Control de hash para evitar duplicados

---

## 🔔 2. Agente de Notificaciones

**Responsabilidad:**  
Monitorea cédulas electrónicas recibidas, detecta vencimientos y genera alertas.

**Componentes relacionados:**
- `panel_pjn/acciones_pjn/notificaciones/monitoreo.py`
- `datos_extraidos/monitoreo/`
- `config/config_monitor.json`

**Funciones destacadas:**
- Seguimiento de estado: atendida / pendiente
- Alerta visual y sonora
- Generación de historial y control de cambios

---

## 📁 3. Agente de Gestión de Expedientes

**Responsabilidad:**  
Administra los expedientes activos, su estructura de carpetas y metadatos asociados.

**Componentes relacionados:**
- `panel_pjn/acciones_pjn/expedientes/`
- `base_datos_simulada/`
- `datos_extraidos/actuaciones/`

**Funciones destacadas:**
- Creación de carpetas por expediente
- Carga inicial y comparación posterior
- Filtrado y selección de expedientes

---

## 🧾 4. Agente de Actuaciones

**Responsabilidad:**  
Extrae las actuaciones visibles de cada expediente, gestiona su visualización y descarga.

**Componentes relacionados:**
- `panel_pjn/acciones_pjn/actuaciones/`
- `gestion_actuaciones.py`

**Funciones destacadas:**
- Extracción por paginación
- Categorización por tipo: firma, DEO, providencia
- Descarga o vista previa de documentos adjuntos

---

## 📅 5. Agente de Agenda Jurídica

**Responsabilidad:**  
Gestiona vencimientos procesales, audiencias, tareas pendientes y recordatorios del sistema.

**Componentes relacionados:**
- `panel_pjn/agenda/` (en desarrollo)
- `config/config_monitor.json`

**Funciones destacadas:**
- Registro automático de vencimientos desde notificaciones
- Tareas manuales vinculadas a expedientes
- Vista diaria/semanal/mensual

---

## 🧠 6. Agente de IA (en desarrollo)

**Responsabilidad:**  
Aplica inteligencia artificial para análisis de jurisprudencia, predicción de sentencias o redacción automatizada de escritos.

**Componentes previstos:**
- `ia/`
- `modelos_gpt/`
- `generador_escritos.py`

**Funciones proyectadas:**
- Sugerencias inteligentes en demandas y escritos
- Análisis de tendencias judiciales por juzgado
- Clasificación automática de documentos

---

## 📊 7. Agente de Estadísticas y Resúmenes

**Responsabilidad:**  
Genera informes sobre actividad diaria, expedientes modificados, liquidaciones, y desempeño del sistema.

**Componentes relacionados:**
- `panel_pjn/resumenes_diarios/`
- `datos_extraidos/`
- `recursos/plantillas_pdf/`

**Funciones destacadas:**
- Generación automática de PDF de actividad diaria
- Reportes por actor, expediente o juzgado
- Estadísticas agregadas por período

---

## 🧩 Observaciones generales

- Todos los agentes comparten una estructura modular que permite integrarlos o ejecutar de forma independiente.
- Se recomienda que cada agente tenga un `README` propio cuando se vuelva lo suficientemente complejo.
- Se evaluará más adelante implementar una interfaz para coordinar la ejecución de múltiples agentes en forma automática o programada.